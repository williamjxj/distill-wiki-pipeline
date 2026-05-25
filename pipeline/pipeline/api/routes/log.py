from fastapi import APIRouter
from pipeline.wiki_core.paths import resolve_paths

router = APIRouter(tags=["log"])


@router.get("/log")
def get_log():
    paths = resolve_paths()
    if not paths.log.is_file():
        return {"content": ""}
    return {"content": paths.log.read_text(encoding="utf-8")}
