from fastapi import APIRouter

from pipeline.wiki_core.graph import build_graph
from pipeline.wiki_core.paths import resolve_paths

router = APIRouter(tags=["graph"])


@router.get("/graph")
def get_graph():
    return build_graph(resolve_paths())
