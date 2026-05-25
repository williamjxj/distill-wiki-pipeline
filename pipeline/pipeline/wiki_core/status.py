from __future__ import annotations
import re
from pipeline.wiki_core.fs import list_raw_files, read_markdown
from pipeline.wiki_core.lint import run_lint
from pipeline.wiki_core.models import PipelineStatus, RawFile, Severity
from pipeline.wiki_core.paths import WikiPaths

_LOG_ENTRY_RE = re.compile(r"^## \[([^\]]+)\] (.+)$", re.MULTILINE)


def get_pipeline_status(paths: WikiPaths) -> PipelineStatus:
    pending_files: list[RawFile] = []
    for raw_path in list_raw_files([paths.raw_llm, paths.raw_web]):
        meta, _ = read_markdown(raw_path)
        if meta.get("status") == "pending":
            pending_files.append(RawFile(
                path=str(raw_path.relative_to(paths.wiki_root)),
                status=meta.get("status", "unknown"),
                topic=meta.get("topic"),
                source=meta.get("source"),
                date=str(meta.get("date")) if meta.get("date") else None,
            ))

    findings = run_lint(paths)
    errors = sum(1 for f in findings if f.severity == Severity.ERROR)
    warnings = sum(1 for f in findings if f.severity == Severity.WARNING)

    export_cycle = None
    brief_status = None
    if paths.project_brief.is_file():
        meta, _ = read_markdown(paths.project_brief)
        brief_status = meta.get("status")
        export_cycle = meta.get("export_cycle")

    last_log_entry = None
    if paths.log.is_file():
        text = paths.log.read_text(encoding="utf-8")
        matches = _LOG_ENTRY_RE.findall(text)
        if matches:
            date, rest = matches[-1]
            last_log_entry = f"[{date}] {rest}"

    return PipelineStatus(
        pending_raw_count=len(pending_files),
        pending_raw_files=pending_files,
        lint_error_count=errors,
        lint_warning_count=warnings,
        export_cycle=export_cycle,
        brief_status=brief_status,
        last_log_entry=last_log_entry,
    )
