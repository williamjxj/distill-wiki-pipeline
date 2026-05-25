from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pipeline.wiki_core.paths import resolve_paths
from pipeline.wiki_core.sync import run_sync

router = APIRouter(tags=["sync"])


class SyncRequest(BaseModel):
    brief_only: bool = False


@router.post("/sync")
def post_sync(body: SyncRequest):
    try:
        result = run_sync(resolve_paths(), brief_only=body.brief_only)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"stdout": result.stdout, "warnings": result.warnings}
