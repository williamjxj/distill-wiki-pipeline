from __future__ import annotations
import re
from pathlib import Path
from pipeline.wiki_core.fs import list_raw_files, read_markdown
from pipeline.wiki_core.models import LintFinding, Severity
from pipeline.wiki_core.paths import WikiPaths

_WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")
_INDEX_ENTRY_RE = re.compile(r"^\s*-\s*\[\[([^\]|]+)", re.MULTILINE)


def _wiki_page_paths(paths: WikiPaths) -> list[Path]:
    pages: list[Path] = []
    for directory in (paths.sources, paths.concepts, paths.synthesis):
        if directory.is_dir():
            pages.extend(directory.glob("*.md"))
    return pages


def _slug_for(path: Path) -> str:
    return path.stem


def _collect_wikilinks(text: str) -> set[str]:
    return set(_WIKILINK_RE.findall(text))


def _index_slugs(index_text: str) -> set[str]:
    return set(_INDEX_ENTRY_RE.findall(index_text))


def run_lint(paths: WikiPaths) -> list[LintFinding]:
    findings: list[LintFinding] = []

    for raw_path in list_raw_files([paths.raw_llm, paths.raw_web]):
        meta, _ = read_markdown(raw_path)
        if meta.get("status") == "pending":
            findings.append(LintFinding(
                severity=Severity.INFO,
                code="pending_raw",
                message=f"Pending ingest: {raw_path.relative_to(paths.wiki_root)}",
                path=str(raw_path.relative_to(paths.wiki_root)),
            ))

    pages = _wiki_page_paths(paths)
    slug_to_path = {_slug_for(p): p for p in pages}
    all_slugs = set(slug_to_path.keys())

    inbound: dict[str, int] = {slug: 0 for slug in all_slugs}
    all_links: set[str] = set()

    for page in pages:
        _, body = read_markdown(page)
        links = _collect_wikilinks(body)
        all_links.update(links)
        for link in links:
            if link in inbound:
                inbound[link] += 1

    for link in sorted(all_links):
        if link not in all_slugs and link not in {"index"}:
            findings.append(LintFinding(
                severity=Severity.ERROR,
                code="missing_page",
                message=f"Wikilink [[{link}]] has no matching page",
            ))

    exempt = {"evolving-thesis", "project-brief", "project-details", "index"}
    for slug, count in inbound.items():
        if count == 0 and slug not in exempt:
            findings.append(LintFinding(
                severity=Severity.WARNING,
                code="orphan_page",
                message=f"Page [[{slug}]] has no inbound wikilinks",
                path=f"wiki/{slug_to_path[slug].relative_to(paths.wiki_inner)}",
            ))

    if paths.index.is_file():
        _, index_body = read_markdown(paths.index)
        indexed = _index_slugs(index_body)
        for slug in all_slugs:
            if slug not in indexed and slug not in exempt:
                findings.append(LintFinding(
                    severity=Severity.WARNING,
                    code="index_out_of_sync",
                    message=f"Page [[{slug}]] exists on disk but missing from index.md",
                    path=f"wiki/{slug}.md",
                ))

    return findings
