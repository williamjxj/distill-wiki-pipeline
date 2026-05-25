from __future__ import annotations

import asyncio
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from pipeline.wiki_core.fs import list_raw_files, read_markdown
from pipeline.wiki_core.lint import run_lint
from pipeline.wiki_core.models import LintFinding
from pipeline.wiki_core.paths import WikiPaths, resolve_paths
from pipeline.wiki_core.status import get_pipeline_status
from pipeline.wiki_core.sync import run_sync

mcp = FastMCP("wiki-pipeline")


def _finding_to_dict(finding: LintFinding) -> dict:
    data = finding.__dict__.copy()
    data["severity"] = finding.severity.value
    return data


def _resolve_wiki_page(paths: WikiPaths, slug_or_path: str) -> Path:
    value = slug_or_path.strip().strip("/")
    if value.startswith("wiki/"):
        value = value[5:]

    if "/" in value or value.endswith(".md"):
        page_path = (paths.wiki_inner / value).resolve()
    else:
        candidates = [
            paths.sources / f"{value}.md",
            paths.concepts / f"{value}.md",
            paths.synthesis / f"{value}.md",
        ]
        matches = [candidate for candidate in candidates if candidate.is_file()]
        if not matches:
            raise ValueError(f"Page not found: {slug_or_path}")
        page_path = matches[0].resolve()

    wiki_inner = paths.wiki_inner.resolve()
    if not str(page_path).startswith(str(wiki_inner)):
        raise ValueError("invalid path")
    if not page_path.is_file():
        raise ValueError(f"Page not found: {slug_or_path}")
    return page_path


def _wiki_page_paths(paths: WikiPaths) -> list[Path]:
    pages: list[Path] = []
    for directory in (paths.sources, paths.concepts, paths.synthesis):
        if directory.is_dir():
            pages.extend(sorted(directory.glob("*.md")))
    for extra in (paths.index, paths.log):
        if extra.is_file():
            pages.append(extra)
    return pages


def handle_list_pending(paths: WikiPaths | None = None) -> dict:
    paths = paths or resolve_paths()
    items = []
    for raw_path in list_raw_files([paths.raw_llm, paths.raw_web]):
        meta, _ = read_markdown(raw_path)
        if meta.get("status") == "pending":
            items.append({
                "path": str(raw_path.relative_to(paths.wiki_root)),
                "meta": meta,
            })
    return {"items": items}


def handle_read_page(paths: WikiPaths, slug_or_path: str) -> dict:
    try:
        page_path = _resolve_wiki_page(paths, slug_or_path)
    except ValueError as exc:
        return {"error": str(exc)}

    meta, body = read_markdown(page_path)
    return {
        "path": str(page_path.relative_to(paths.wiki_inner)),
        "meta": meta,
        "body": body,
    }


def handle_search(paths: WikiPaths, query: str) -> dict:
    query = query.strip()
    if not query:
        return {"query": query, "matches": [], "error": "query is required"}

    needle = query.lower()
    matches = []
    for page in _wiki_page_paths(paths):
        for line_no, line in enumerate(page.read_text(encoding="utf-8").splitlines(), 1):
            if needle in line.lower():
                matches.append({
                    "path": str(page.relative_to(paths.wiki_inner)),
                    "line": line_no,
                    "text": line.strip(),
                })

    return {"query": query, "matches": matches}


def handle_get_status(paths: WikiPaths | None = None) -> dict:
    paths = paths or resolve_paths()
    status = get_pipeline_status(paths)
    return {
        "pending_raw_count": status.pending_raw_count,
        "pending_raw_files": [f.__dict__ for f in status.pending_raw_files],
        "lint_error_count": status.lint_error_count,
        "lint_warning_count": status.lint_warning_count,
        "export_cycle": status.export_cycle,
        "brief_status": status.brief_status,
        "last_log_entry": status.last_log_entry,
    }


def handle_run_lint(paths: WikiPaths | None = None) -> dict:
    paths = paths or resolve_paths()
    findings = run_lint(paths)
    return {"findings": [_finding_to_dict(finding) for finding in findings]}


def handle_sync_brief(paths: WikiPaths | None = None) -> dict:
    paths = paths or resolve_paths()
    try:
        result = run_sync(paths, brief_only=True)
    except RuntimeError as exc:
        return {"error": str(exc)}
    return {"stdout": result.stdout, "warnings": result.warnings}


@mcp.tool()
def wiki_list_pending() -> dict:
    """List raw markdown files with status: pending."""
    return handle_list_pending()


@mcp.tool()
def wiki_read_page(slug_or_path: str) -> dict:
    """Read a wiki page by slug or relative path under wiki/."""
    return handle_read_page(resolve_paths(), slug_or_path)


@mcp.tool()
def wiki_search(query: str) -> dict:
    """Search wiki page content for a query string."""
    return handle_search(resolve_paths(), query)


@mcp.tool()
def wiki_get_status() -> dict:
    """Return pipeline health summary."""
    return handle_get_status()


@mcp.tool()
def wiki_run_lint() -> dict:
    """Run deterministic wiki lint and return a structured report."""
    return handle_run_lint()


@mcp.tool()
def wiki_sync_brief() -> dict:
    """Run brief sync script and return any warnings."""
    return handle_sync_brief()


def main() -> None:
    asyncio.run(mcp.run_stdio_async())


if __name__ == "__main__":
    main()
