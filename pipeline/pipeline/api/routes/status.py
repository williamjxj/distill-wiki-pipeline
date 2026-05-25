from fastapi import APIRouter
from pipeline.wiki_core.paths import resolve_paths
from pipeline.wiki_core.status import get_pipeline_status

router = APIRouter(tags=["status"])


@router.get("/status")
def get_status():
    s = get_pipeline_status(resolve_paths())
    return {
        "pending_raw_count": s.pending_raw_count,
        "pending_raw_files": [f.__dict__ for f in s.pending_raw_files],
        "lint_error_count": s.lint_error_count,
        "lint_warning_count": s.lint_warning_count,
        "export_cycle": s.export_cycle,
        "brief_status": s.brief_status,
        "last_log_entry": s.last_log_entry,
    }
