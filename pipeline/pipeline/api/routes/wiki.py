from fastapi import APIRouter

from pipeline.wiki_core.fs import read_markdown
from pipeline.wiki_core.paths import resolve_paths

router = APIRouter(tags=["wiki"])


@router.get("/wiki/evolving-thesis")
def get_evolving_thesis():
    paths = resolve_paths()
    if not paths.evolving_thesis.is_file():
        return {"content": ""}
    _, body = read_markdown(paths.evolving_thesis)
    return {"content": body}
