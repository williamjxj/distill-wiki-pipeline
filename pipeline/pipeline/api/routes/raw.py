from fastapi import APIRouter, HTTPException
from pipeline.wiki_core.fs import list_raw_files, read_markdown
from pipeline.wiki_core.paths import resolve_paths

router = APIRouter(tags=["raw"])


@router.get("/raw/pending")
def list_pending():
    paths = resolve_paths()
    items = []
    for raw_path in list_raw_files([paths.raw_llm, paths.raw_web]):
        meta, _ = read_markdown(raw_path)
        if meta.get("status") == "pending":
            items.append({
                "path": str(raw_path.relative_to(paths.wiki_root)),
                "meta": meta,
            })
    return {"items": items}


@router.get("/raw/{file_path:path}")
def get_raw(file_path: str):
    paths = resolve_paths()
    raw_path = (paths.wiki_root / file_path).resolve()
    if not str(raw_path).startswith(str(paths.wiki_root.resolve())):
        raise HTTPException(status_code=400, detail="invalid path")
    if not raw_path.is_file():
        raise HTTPException(status_code=404, detail="not found")
    meta, body = read_markdown(raw_path)
    return {"path": file_path, "meta": meta, "body": body}
