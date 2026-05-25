from __future__ import annotations

import json
import re
from datetime import date, datetime
from pathlib import Path

from pipeline.api.jobs import IngestJob, JobState, JobStore
from pipeline.llm.prompts.ingest import INGEST_ANALYSIS_SYSTEM, INGEST_WRITE_SYSTEM
from pipeline.llm.router import complete_ollama
from pipeline.wiki_core.fs import parse_frontmatter, read_markdown, write_frontmatter_field, write_markdown
from pipeline.wiki_core.paths import WikiPaths, resolve_paths

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*\n?(.*?)\n?```", re.DOTALL | re.IGNORECASE)


def extract_json(text: str) -> dict:
    cleaned = text.strip()
    fence = _JSON_FENCE_RE.search(cleaned)
    if fence:
        cleaned = fence.group(1).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in LLM response")
    return json.loads(cleaned[start : end + 1])


def slug_from_raw_path(raw_path: str) -> str:
    return Path(raw_path).stem


def normalize_draft_payload(payload: dict, raw_path: str, raw_meta: dict) -> dict:
    """Coerce common LLM draft shapes into the schema apply_writes expects."""
    slug = slug_from_raw_path(raw_path)
    normalized = dict(payload)

    source_md = normalized.get("source_md")
    if isinstance(source_md, dict):
        fm = source_md
        normalized["source_md"] = (
            "---\n"
            f"type: source-summary\n"
            f"raw: {raw_path}\n"
            f"source: {fm.get('source', raw_meta.get('source', 'claude'))}\n"
            f"date: {fm.get('date', raw_meta.get('date', ''))}\n"
            "---\n\n"
            f"# {fm.get('topic', slug)}\n\n"
            "## Key Claims\n\n"
            "(See raw source — draft normalization applied.)\n"
        )
    elif not isinstance(source_md, str) or not source_md.strip():
        normalized["source_md"] = (
            "---\n"
            f"type: source-summary\n"
            f"raw: {raw_path}\n"
            f"source: {raw_meta.get('source', 'claude')}\n"
            f"date: {raw_meta.get('date', '')}\n"
            "---\n\n"
            f"# {raw_meta.get('topic', slug)}\n"
        )

    log_entry = normalized.get("log_entry")
    if isinstance(log_entry, dict):
        date_str = log_entry.get("date", raw_meta.get("date", ""))
        slug_ref = log_entry.get("slug", slug)
        summary = log_entry.get("summary", "Ingest completed.")
        normalized["log_entry"] = f"## [{date_str}] ingest | {slug_ref}\n\n{summary}"

    concept_updates = normalized.get("concept_updates")
    if isinstance(concept_updates, dict):
        fixed: dict[str, str] = {}
        for key, value in concept_updates.items():
            if isinstance(value, str):
                fixed[key] = value
            elif isinstance(value, dict):
                title = value.get("title", key.replace("-", " ").title())
                body = value.get("body", json.dumps(value, indent=2))
                fixed[key] = f"# {title}\n\n{body}"
        normalized["concept_updates"] = fixed

    return normalized


def _json_prompt(data: dict) -> str:
    def _default(value: object) -> str:
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")

    return json.dumps(data, indent=2, default=_default)


def validate_raw(raw_path: str, paths: WikiPaths | None = None) -> tuple[Path, dict, str]:
    wiki_paths = paths or resolve_paths()
    raw_file = (wiki_paths.wiki_root / raw_path).resolve()
    if not str(raw_file).startswith(str(wiki_paths.wiki_root.resolve())):
        raise ValueError("invalid raw path")
    if not raw_file.is_file():
        raise FileNotFoundError(f"raw file not found: {raw_path}")
    meta, body = read_markdown(raw_file)
    if meta.get("status") != "pending":
        raise ValueError(f"raw file status is {meta.get('status')!r}, expected pending")
    return raw_file, meta, body


async def run_analysis(job: IngestJob, paths: WikiPaths | None = None) -> None:
    wiki_paths = paths or resolve_paths()
    raw_file, meta, body = validate_raw(job.raw_path, wiki_paths)
    job.raw_meta = meta
    job.raw_body = body
    prompt = (
        f"Raw path: {job.raw_path}\n"
        f"Frontmatter:\n{_json_prompt(meta)}\n\n"
        f"Body:\n{body}"
    )
    job.analysis = await complete_ollama(INGEST_ANALYSIS_SYSTEM, prompt, task="ingest")
    job.state = JobState.ANALYSIS_DONE


async def run_draft(job: IngestJob, paths: WikiPaths | None = None) -> None:
    if job.state != JobState.ANALYSIS_DONE:
        raise ValueError(f"job state is {job.state.value}, expected analysis_done")
    wiki_paths = paths or resolve_paths()
    slug = slug_from_raw_path(job.raw_path)
    prompt = (
        f"Raw path: {job.raw_path}\n"
        f"Source slug: {slug}\n"
        f"Frontmatter:\n{_json_prompt(job.raw_meta)}\n\n"
        f"Raw body:\n{job.raw_body}\n\n"
        f"Approved analysis:\n{job.analysis}"
    )
    job.draft = await complete_ollama(INGEST_WRITE_SYSTEM, prompt, task="ingest")
    job.draft_payload = normalize_draft_payload(extract_json(job.draft), job.raw_path, job.raw_meta or {})
    job.state = JobState.DRAFT_DONE


def _write_source(paths: WikiPaths, slug: str, source_md: str) -> None:
    dest = paths.sources / f"{slug}.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(source_md.strip() + "\n", encoding="utf-8")


def _merge_concept(paths: WikiPaths, slug: str, content: str) -> None:
    dest = paths.concepts / f"{slug}.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file():
        existing = dest.read_text(encoding="utf-8")
        new_meta, new_body = parse_frontmatter(content)
        _, old_body = parse_frontmatter(existing)
        merged_body = old_body.rstrip() + "\n\n" + new_body.lstrip()
        write_markdown(dest, new_meta or {}, merged_body)
    else:
        dest.write_text(content.strip() + "\n", encoding="utf-8")


def _append_text(path: Path, fragment: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        current = path.read_text(encoding="utf-8").rstrip()
        path.write_text(current + "\n\n" + fragment.strip() + "\n", encoding="utf-8")
    else:
        path.write_text(fragment.strip() + "\n", encoding="utf-8")


def _append_index_lines(paths: WikiPaths, lines: list) -> None:
    if not lines:
        return
    text = paths.index.read_text(encoding="utf-8") if paths.index.is_file() else "# Wiki Index\n"
    block = "\n".join(str(line).strip() for line in lines if str(line).strip())
    paths.index.write_text(text.rstrip() + "\n" + block + "\n", encoding="utf-8")


def apply_writes(job: IngestJob, payload: dict, paths: WikiPaths | None = None) -> None:
    wiki_paths = paths or resolve_paths()
    slug = slug_from_raw_path(job.raw_path)
    source_md = payload.get("source_md")
    if not source_md:
        raise ValueError("draft payload missing source_md")
    _write_source(wiki_paths, slug, source_md)
    for concept_slug, content in (payload.get("concept_updates") or {}).items():
        _merge_concept(wiki_paths, concept_slug, content)
    thesis_delta = payload.get("thesis_delta")
    if thesis_delta:
        _append_text(wiki_paths.evolving_thesis, thesis_delta)
    _append_index_lines(wiki_paths, payload.get("index_lines") or [])
    log_entry = payload.get("log_entry")
    if log_entry:
        _append_text(wiki_paths.log, log_entry)


def finalize_ingest(job: IngestJob, paths: WikiPaths | None = None) -> None:
    wiki_paths = paths or resolve_paths()
    raw_file = (wiki_paths.wiki_root / job.raw_path).resolve()
    write_frontmatter_field(raw_file, "status", "ingested")
    job.state = JobState.COMPLETED


async def start_ingest_job(
    store: JobStore,
    raw_path: str,
    paths: WikiPaths | None = None,
) -> IngestJob:
    job = store.create_ingest(raw_path)
    try:
        await run_analysis(job, paths)
    except Exception as exc:
        store.mark_failed(job, str(exc))
        raise
    return job


async def approve_analysis(store: JobStore, job_id: str, paths: WikiPaths | None = None) -> IngestJob:
    job = store.get(job_id)
    if job is None:
        raise KeyError("job not found")
    if job.state != JobState.ANALYSIS_DONE:
        raise ValueError(f"job state is {job.state.value}, expected analysis_done")
    try:
        await run_draft(job, paths)
    except Exception as exc:
        store.mark_failed(job, str(exc))
        raise
    return job


def approve_draft(
    store: JobStore,
    job_id: str,
    edits: dict | None = None,
) -> IngestJob:
    job = store.get(job_id)
    if job is None:
        raise KeyError("job not found")
    if job.state != JobState.DRAFT_DONE:
        raise ValueError(f"job state is {job.state.value}, expected draft_done")
    payload = dict(job.draft_payload or {})
    if edits:
        payload.update(edits)
    job.draft_payload = payload
    job.state = JobState.AWAITING_FINAL_CONFIRM
    return job


def confirm_ingest(
    store: JobStore,
    job_id: str,
    paths: WikiPaths | None = None,
) -> IngestJob:
    job = store.get(job_id)
    if job is None:
        raise KeyError("job not found")
    if job.state != JobState.AWAITING_FINAL_CONFIRM:
        raise ValueError(f"job state is {job.state.value}, expected awaiting_final_confirm")
    if not job.draft_payload:
        raise ValueError("job has no draft payload")
    try:
        apply_writes(job, job.draft_payload, paths)
        finalize_ingest(job, paths)
    except Exception as exc:
        store.mark_failed(job, str(exc))
        raise
    return job
