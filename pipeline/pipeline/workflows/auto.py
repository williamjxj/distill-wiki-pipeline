from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from datetime import date
from pathlib import Path
from uuid import uuid4

from pipeline.api.jobs import ExportJob, ExportJobState, IngestJob, JobState
from pipeline.llm.workflows import export as export_workflow
from pipeline.llm.workflows import ingest as ingest_workflow
from pipeline.wiki_core.fs import list_raw_files, read_markdown, write_markdown
from pipeline.wiki_core.graph import build_graph
from pipeline.wiki_core.lint import run_lint
from pipeline.wiki_core.paths import WikiPaths, resolve_paths
from pipeline.wiki_core.sync import run_sync


# ── helpers ──────────────────────────────────────────────────────────────


def _pending_raw_paths(paths: WikiPaths) -> list[tuple]:
    """Return (absolute_path, meta) for every raw file that needs processing.

    This includes files with ``status: pending`` **and** files that lack
    frontmatter entirely — the latter will get frontmatter injected
    right before ingest by :func:`_ensure_frontmatter`.
    """
    items: list[tuple] = []
    for raw_path in list_raw_files([paths.raw_llm, paths.raw_web]):
        meta, _ = read_markdown(raw_path)
        status = meta.get("status")
        if status == "pending" or status is None:
            items.append((raw_path, meta))
    return items


def _rel_to_root(paths: WikiPaths, absolute: object) -> str:
    """Convert an absolute raw-file path to the wiki-root-relative string
    that ``start_ingest_job`` and ``validate_raw`` expect."""
    return str(absolute).replace(str(paths.wiki_root), "").lstrip("/")


def _ensure_frontmatter(raw_path: Path, wiki_paths: WikiPaths) -> None:
    """Analyse a raw file and add any missing frontmatter fields.

    Files dumped into ``raw/`` often lack YAML frontmatter entirely.  This
    function examines what exists and fills in sensible defaults so the
    subsequent ``validate_raw`` step won't reject them.
    """
    meta, body = read_markdown(raw_path)
    if meta.get("status") is not None:
        return  # already has frontmatter — nothing to do

    # Determine location-based defaults
    rel = str(raw_path.relative_to(wiki_paths.wiki_root))
    is_llm = "/llm/" in rel

    meta.setdefault("type", "llm-chat" if is_llm else "web-clip")
    meta.setdefault("source", "llm" if is_llm else "web")
    meta.setdefault("date", date.today().isoformat())

    # Derive topic from the first H1 heading, or fall back to the filename
    first_line = body.strip().split("\n")[0] if body else ""
    if first_line.startswith("# ") and not first_line.startswith("##"):
        topic = first_line.lstrip("# ").strip()
    else:
        topic = raw_path.stem.replace("-", " ").replace("_", " ").title()
    meta.setdefault("topic", topic)

    meta.setdefault("status", "pending")

    write_markdown(raw_path, meta, body)


# ── automated ingest ─────────────────────────────────────────────────────


async def auto_ingest(
    raw_rel_path: str,
    paths: WikiPaths | None = None,
) -> IngestJob:
    """Run the full ingest for *one* raw file with pre-approval — no human
    gates, no ``JobStore`` dependency.

    ``raw_rel_path`` is relative to ``wiki_root`` (e.g. ``raw/llm/chat.md``).
    """
    wiki_paths = paths or resolve_paths()

    # 0  Ensure frontmatter  ── inject missing fields so validate_raw passes
    raw_abs = (wiki_paths.wiki_root / raw_rel_path).resolve()
    _ensure_frontmatter(raw_abs, wiki_paths)

    job = IngestJob(id=str(uuid4()), raw_path=raw_rel_path)

    # 1  Analysis (LLM pass 1)  ── sets  state → ANALYSIS_DONE
    try:
        await ingest_workflow.run_analysis(job, wiki_paths)
    except Exception as exc:
        job.state = JobState.FAILED
        job.error = str(exc)
        return job

    # 2  Draft (LLM pass 2)     ── reads state ANALYSIS_DONE → DRAFT_DONE
    try:
        await ingest_workflow.run_draft(job, wiki_paths)
    except Exception as exc:
        job.state = JobState.FAILED
        job.error = str(exc)
        return job

    # 3  Auto-approve draft   ── replaces the UI "approve_draft" step
    job.state = JobState.AWAITING_FINAL_CONFIRM

    # 4  Confirm & write       ── replaces "confirm_ingest"
    ingest_workflow.apply_writes(job, job.draft_payload, wiki_paths)
    ingest_workflow.finalize_ingest(job, wiki_paths)

    return job


# ── automated export ─────────────────────────────────────────────────────


async def auto_export(paths: WikiPaths | None = None) -> ExportJob:
    """Run the full export with pre-approval — no human gate, no
    ``JobStore`` dependency."""
    wiki_paths = paths or resolve_paths()
    job = ExportJob(id=str(uuid4()))

    # 1  Draft  ── writes  project-brief.md  with  status: draft
    await export_workflow.run_draft(job, wiki_paths)

    # 2  Auto-approve (promote status draft → current)
    meta, body = read_markdown(wiki_paths.project_brief)
    export_cycle = meta.get("export_cycle") or job.export_cycle
    sources_ingested = (
        job.sources_ingested
        or (len(list(wiki_paths.sources.glob("*.md"))) if wiki_paths.sources.is_dir() else 0)
    )
    meta["status"] = "current"
    meta["date"] = date.today().isoformat()
    meta["sources_ingested"] = sources_ingested
    write_markdown(wiki_paths.project_brief, meta, body)

    # log entry
    log_entry = (
        f"## [{date.today().isoformat()}] export | project-brief cycle {export_cycle}\n"
        "Approved project brief export (auto-pipeline)."
    )
    wiki_paths.log.parent.mkdir(parents=True, exist_ok=True)
    if wiki_paths.log.is_file():
        current = wiki_paths.log.read_text(encoding="utf-8").rstrip()
        wiki_paths.log.write_text(current + "\n\n" + log_entry + "\n", encoding="utf-8")
    else:
        wiki_paths.log.write_text(log_entry + "\n", encoding="utf-8")

    job.state = ExportJobState.COMPLETED
    job.export_cycle = export_cycle
    job.sources_ingested = sources_ingested

    return job


# ── streaming pipeline (single source of truth) ─────────────────────────


def _yield_step(event_type: str, step: str, status: str, message: str) -> dict:
    return {"event": event_type, "step": step, "status": status, "message": message}


def _yield_log(line: str) -> dict:
    return {"event": "log", "line": line}


async def stream_auto_pipeline(
    file_spec: str,
    paths: WikiPaths | None = None,
) -> AsyncGenerator[dict, None]:
    """Async generator that yields event dicts for the full pipeline.

    ``file_spec`` is either ``"all"`` (process all pending) or a wiki-root-relative
    path to a single raw file.

    Each yielded dict has ``{"event": "step"|"log"|"result", ...}``.
    """
    wiki_paths = paths or resolve_paths()
    total_errors = 0
    total_warnings = 0
    files_processed = 0

    if file_spec == "all":
        items = _pending_raw_paths(wiki_paths)
        if not items:
            yield _yield_log("No pending raw files to process")
            yield {"event": "result", "status": "completed",
                   "summary": {"files_processed": 0, "errors": 0, "warnings": 0}}
            return
        file_list = items
        yield _yield_log(f"Found {len(file_list)} pending file(s)")
    else:
        raw_abs = (wiki_paths.wiki_root / file_spec).resolve()
        file_list = [(raw_abs, {})]
        yield _yield_log(f"Processing: {file_spec}")

    for abs_path, _meta in file_list:
        rel = _rel_to_root(wiki_paths, abs_path)
        slug = rel.rsplit("/", 1)[-1].replace(".md", "")
        files_processed += 1

        # ── 1  Frontmatter ───────────────────────────────────────────────
        yield _yield_step("step", "frontmatter", "running", f"Injecting frontmatter for {rel}")
        _ensure_frontmatter(abs_path, wiki_paths)
        yield _yield_step("step", "frontmatter", "done", "✓ Frontmatter injected")

        # ── 2  Ingest ─────────────────────────────────────────────────────
        yield _yield_step("step", "ingest", "running", f"Ingesting {rel}...")
        yield _yield_log(f"  auto  | ingest  {rel}")
        try:
            ingest_job = await auto_ingest(rel, wiki_paths)
        except Exception as exc:
            yield _yield_step("step", "ingest", "failed", f"✗ Ingest failed: {exc}")
            yield _yield_log(f"         └ FAILED  {exc}")
            total_errors += 1
            continue
        if ingest_job.state == JobState.FAILED:
            yield _yield_step("step", "ingest", "failed", f"✗ Ingest failed: {ingest_job.error}")
            yield _yield_log(f"         └ FAILED  {ingest_job.error}")
            total_errors += 1
            continue
        yield _yield_step("step", "ingest", "done", "✓ Ingest complete")
        yield _yield_log(f"         └ {ingest_job.state.value}")

        # ── 3  Lint (post-ingest) ────────────────────────────────────────
        yield _yield_step("step", "lint", "running", "Running lint...")
        lint_results = run_lint(wiki_paths)
        errs = sum(1 for f in lint_results if f.severity.name == "ERROR")
        warns = sum(1 for f in lint_results if f.severity.name == "WARNING")
        total_errors += errs
        total_warnings += warns
        yield _yield_step("step", "lint", "done", f"✓ Lint: {errs} errors, {warns} warnings")
        yield _yield_log(f"  auto  | lint     {errs} errors, {warns} warnings")

    # ── 4  Export (only when no more pending files remain) ────────────────
    remaining = _pending_raw_paths(wiki_paths)
    if remaining:
        yield _yield_step("step", "export", "skipped",
                          f"→ Skipped: {len(remaining)} pending file(s) remain")
        yield _yield_log(f"  auto  | {len(remaining)} pending file(s) remain — skipping export")
    else:
        yield _yield_step("step", "export", "running", "Exporting project brief...")
        yield _yield_log("  auto  | export   project brief")
        try:
            export_job = await auto_export(wiki_paths)
        except Exception as exc:
            yield _yield_step("step", "export", "failed", f"✗ Export failed: {exc}")
            yield _yield_log(f"         └ FAILED  {exc}")
            total_errors += 1
            yield {"event": "result", "status": "failed",
                   "summary": {"files_processed": files_processed, "errors": total_errors, "warnings": total_warnings}}
            return
        yield _yield_step("step", "export", "done",
                          f"✓ Export cycle {export_job.export_cycle}")
        yield _yield_log(f"         └ cycle {export_job.export_cycle}")

        # ── 5  Lint (post-export) ────────────────────────────────────────
        yield _yield_step("step", "lint2", "running", "Running post-export lint...")
        lint2 = run_lint(wiki_paths)
        errs2 = sum(1 for f in lint2 if f.severity.name == "ERROR")
        warns2 = sum(1 for f in lint2 if f.severity.name == "WARNING")
        total_errors += errs2
        total_warnings += warns2
        yield _yield_step("step", "lint2", "done", f"✓ Lint: {errs2} errors, {warns2} warnings")
        yield _yield_log(f"  auto  | lint     {errs2} errors, {warns2} warnings")

        # ── 6  Graph ─────────────────────────────────────────────────────
        yield _yield_step("step", "graph", "running", "Building knowledge graph...")
        graph_data = build_graph(wiki_paths)
        graph_msg = f"{len(graph_data['nodes'])} nodes, {len(graph_data['edges'])} edges"
        yield _yield_step("step", "graph", "done", f"✓ Graph: {graph_msg}")
        yield _yield_log(f"  auto  | graph    {graph_msg}")

        # ── 7  Sync ──────────────────────────────────────────────────────
        yield _yield_step("step", "sync", "running", "Syncing to docs/...")
        try:
            sync_result = run_sync(wiki_paths)
        except Exception as exc:
            yield _yield_step("step", "sync", "failed", f"✗ Sync failed: {exc}")
            yield _yield_log(f"         └ FAILED  {exc}")
            total_errors += 1
            yield {"event": "result", "status": "failed",
                   "summary": {"files_processed": files_processed, "errors": total_errors, "warnings": total_warnings}}
            return
        yield _yield_step("step", "sync", "done", "✓ Sync completed")
        yield _yield_log("  auto  | sync     completed")

    yield {"event": "result", "status": "completed",
           "summary": {"files_processed": files_processed, "errors": total_errors, "warnings": total_warnings}}


# ── CLI wrappers ────────────────────────────────────────────────────────


async def run_pipeline(
    raw_rel_path: str,
    paths: WikiPaths | None = None,
) -> dict:
    """Run the full pre-approved pipeline for one raw file::

        ingest → lint → export → lint → graph → sync

    Legacy CLI wrapper around :func:`stream_auto_pipeline`.
    """
    summary = {}
    async for event in stream_auto_pipeline(raw_rel_path, paths):
        if event["event"] == "log":
            print(event["line"])
        elif event["event"] == "step":
            if event["step"] not in summary:
                summary[event["step"]] = event["status"]
            if event["status"] in ("failed", "done", "skipped"):
                print(f"         └ {event['message']}")
        elif event["event"] == "result":
            return event["summary"]
    return summary


async def process_all_pending(paths: WikiPaths | None = None) -> list[dict]:
    """Process every pending raw file through the full pipeline.

    Legacy CLI wrapper around :func:`stream_auto_pipeline`.
    """
    results: list[dict] = []
    async for event in stream_auto_pipeline("all", paths):
        if event["event"] == "log":
            print(event["line"])
        elif event["event"] == "step":
            if event["status"] in ("failed", "done", "skipped"):
                print(f"         └ {event['message']}")
        elif event["event"] == "result":
            results.append(event["summary"])
    return results


async def watch_loop(paths: WikiPaths | None = None, interval: int = 60) -> None:
    """Poll for new pending raw files and auto-process them as they appear."""
    wiki_paths = paths or resolve_paths()
    known = {abs_path for abs_path, _meta in _pending_raw_paths(wiki_paths)}
    print(f"  auto  | watch     polling every {interval}s (Ctrl+C to stop)")

    while True:
        await asyncio.sleep(interval)
        current = {abs_path for abs_path, _meta in _pending_raw_paths(wiki_paths)}
        new_files = sorted(current - known)
        if new_files:
            for abs_path in new_files:
                rel = _rel_to_root(wiki_paths, abs_path)
                print()
                try:
                    await run_pipeline(rel, wiki_paths)
                except Exception as exc:
                    print(f"  auto  | FAILED   {rel} — {exc}")
        known = current
