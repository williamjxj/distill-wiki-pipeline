from __future__ import annotations

import re
from pathlib import Path

from pipeline.wiki_core.fs import read_markdown
from pipeline.wiki_core.paths import WikiPaths

_WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")


def _wiki_page_paths(paths: WikiPaths) -> list[Path]:
    pages: list[Path] = []
    for directory in (paths.sources, paths.concepts, paths.synthesis):
        if directory.is_dir():
            pages.extend(directory.glob("*.md"))
    return pages


def _slug_for(path: Path) -> str:
    return path.stem


def _collect_wikilinks(text: str) -> set[str]:
    return set(_WIKILINK_RE.findall(text))


def build_graph(paths: WikiPaths) -> dict:
    """Return { nodes: [{id, label}], edges: [{source, target}] }."""
    pages = _wiki_page_paths(paths)
    slug_to_path = {_slug_for(page): page for page in pages}
    node_ids = set(slug_to_path.keys())
    edges: list[dict[str, str]] = []
    seen_edges: set[tuple[str, str]] = set()

    for page in pages:
        source = _slug_for(page)
        _, body = read_markdown(page)
        for target in sorted(_collect_wikilinks(body)):
            if target == source:
                continue
            node_ids.add(target)
            edge = (source, target)
            if edge not in seen_edges:
                seen_edges.add(edge)
                edges.append({"source": source, "target": target})

    nodes = [{"id": node_id, "label": node_id} for node_id in sorted(node_ids)]
    return {"nodes": nodes, "edges": edges}
