from __future__ import annotations

from datetime import date

from pipeline.api.jobs import ExportJob, ExportJobState, JobStore
from pipeline.llm.prompts.export import EXPORT_BRIEF_SYSTEM
from pipeline.llm.router import complete_ollama
from pipeline.wiki_core.fs import read_markdown, write_markdown
from pipeline.wiki_core.lint import run_lint
from pipeline.wiki_core.models import Severity
from pipeline.wiki_core.paths import WikiPaths, resolve_paths


def _count_sources(paths: WikiPaths) -> int:
    if not paths.sources.is_dir():
        return 0
    return sum(1 for path in paths.sources.glob("*.md") if path.is_file())


def _next_export_cycle(paths: WikiPaths) -> int:
    if paths.project_brief.is_file():
        meta, _ = read_markdown(paths.project_brief)
        current = meta.get("export_cycle")
        if isinstance(current, int):
            return current + 1
        if isinstance(current, str) and current.isdigit():
            return int(current) + 1
    return 1


def _read_prior_brief(paths: WikiPaths) -> tuple[dict, str] | None:
    if not paths.project_brief.is_file():
        return None
    meta, body = read_markdown(paths.project_brief)
    return meta, body


def _collect_concept_pages(paths: WikiPaths) -> str:
    blocks: list[str] = []
    if not paths.concepts.is_dir():
        return ""
    for path in sorted(paths.concepts.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        blocks.append(f"### {path.name}\n\n{text.strip()}\n")
    return "\n".join(blocks)


def _strip_code_fence(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if len(lines) >= 2 and lines[0].startswith("```"):
            end = len(lines) - 1 if lines[-1].strip() == "```" else len(lines)
            cleaned = "\n".join(lines[1:end]).strip()
    return cleaned


def lint_blocks_export(paths: WikiPaths, force: bool) -> list[dict]:
    findings = run_lint(paths)
    errors = [f for f in findings if f.severity == Severity.ERROR]
    if errors and not force:
        return [
            {
                "severity": f.severity.value,
                "code": f.code,
                "message": f.message,
                "path": f.path,
            }
            for f in errors
        ]
    return []


async def run_draft(job: ExportJob, paths: WikiPaths | None = None) -> None:
    wiki_paths = paths or resolve_paths()

    if not wiki_paths.evolving_thesis.is_file():
        raise ValueError("evolving-thesis.md not found")

    prior = _read_prior_brief(wiki_paths)
    if prior:
        prior_meta, prior_body = prior
        job.prior_brief_status = prior_meta.get("status")
        job.prior_brief = prior_body.strip()
        job.prior_export_cycle = prior_meta.get("export_cycle")

    thesis_text = wiki_paths.evolving_thesis.read_text(encoding="utf-8")
    concepts_text = _collect_concept_pages(wiki_paths)
    sources_ingested = _count_sources(wiki_paths)
    export_cycle = _next_export_cycle(wiki_paths)

    prompt = (
        f"Export cycle: {export_cycle}\n"
        f"Sources ingested: {sources_ingested}\n\n"
        f"## evolving-thesis.md\n\n{thesis_text.strip()}\n\n"
        f"## Concept pages\n\n{concepts_text or '(none)'}"
    )

    body = _strip_code_fence(
        await complete_ollama(EXPORT_BRIEF_SYSTEM, prompt, task="export_brief")
    )
    if not body.startswith("# Project Brief"):
        raise ValueError("LLM response missing required Project Brief heading")

    meta = {
        "type": "project-brief",
        "status": "draft",
        "date": date.today().isoformat(),
        "export_cycle": export_cycle,
        "sources_ingested": sources_ingested,
    }

    write_markdown(wiki_paths.project_brief, meta, body)
    job.export_cycle = export_cycle
    job.sources_ingested = sources_ingested
    job.draft_body = body
    job.draft_meta = meta
    job.state = ExportJobState.DRAFT_DONE


async def start_export(
    store: JobStore,
    force: bool = False,
    paths: WikiPaths | None = None,
) -> ExportJob:
    wiki_paths = paths or resolve_paths()
    job = store.create_export(force=force)

    blockers = lint_blocks_export(wiki_paths, force)
    job.lint_findings = blockers
    if blockers:
        job.state = ExportJobState.LINT_BLOCKED
        return job

    try:
        await run_draft(job, wiki_paths)
    except Exception as exc:
        store.mark_export_failed(job, str(exc))
        raise
    return job


def approve_export(
    store: JobStore,
    job_id: str,
    paths: WikiPaths | None = None,
) -> ExportJob:
    wiki_paths = paths or resolve_paths()
    job = store.get_export(job_id)
    if job is None:
        raise KeyError("job not found")
    if job.state != ExportJobState.DRAFT_DONE:
        raise ValueError(f"job state is {job.state.value}, expected draft_done")
    if not wiki_paths.project_brief.is_file():
        raise ValueError("project-brief.md not found")

    meta, body = read_markdown(wiki_paths.project_brief)
    if meta.get("status") != "draft":
        raise ValueError("project-brief.md is not status: draft")

    export_cycle = meta.get("export_cycle") or job.export_cycle
    if job.prior_brief_status == "current":
        # Prior current brief was superseded by this export cycle.
        pass

    meta["status"] = "current"
    meta["date"] = date.today().isoformat()
    meta["sources_ingested"] = job.sources_ingested or _count_sources(wiki_paths)
    write_markdown(wiki_paths.project_brief, meta, body)

    log_entry = (
        f"## [{date.today().isoformat()}] export | project-brief cycle {export_cycle}\n"
        "Approved project brief export."
    )
    log_path = wiki_paths.log
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if log_path.is_file():
        current = log_path.read_text(encoding="utf-8").rstrip()
        log_path.write_text(current + "\n\n" + log_entry + "\n", encoding="utf-8")
    else:
        log_path.write_text(log_entry + "\n", encoding="utf-8")

    job.draft_meta = meta
    job.state = ExportJobState.COMPLETED
    return job
