from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import yaml

_CONFIG_NAME = "config.yaml"


@dataclass(frozen=True)
class WikiPaths:
    repo_root: Path
    wiki_root: Path
    raw_llm: Path
    raw_web: Path
    wiki_inner: Path
    sources: Path
    concepts: Path
    synthesis: Path
    index: Path
    log: Path
    evolving_thesis: Path
    project_brief: Path
    docs_dir: Path
    sync_script: Path


def load_config(config_path: Path | None = None) -> dict:
    pipeline_dir = Path(__file__).resolve().parent.parent.parent
    path = config_path or (pipeline_dir / _CONFIG_NAME)
    with path.open() as f:
        return yaml.safe_load(f)


def resolve_paths(config_path: Path | None = None) -> WikiPaths:
    pipeline_dir = Path(__file__).resolve().parent.parent.parent
    cfg = load_config(config_path)
    repo_root = (pipeline_dir / cfg["parent_root"]).resolve()
    wiki_root = (pipeline_dir / cfg["wiki_root"]).resolve()
    wiki_inner = wiki_root / "wiki"
    return WikiPaths(
        repo_root=repo_root,
        wiki_root=wiki_root,
        raw_llm=wiki_root / "raw" / "llm",
        raw_web=wiki_root / "raw" / "web",
        wiki_inner=wiki_inner,
        sources=wiki_inner / "sources",
        concepts=wiki_inner / "concepts",
        synthesis=wiki_inner / "synthesis",
        index=wiki_inner / "index.md",
        log=wiki_inner / "log.md",
        evolving_thesis=wiki_inner / "synthesis" / "evolving-thesis.md",
        project_brief=wiki_inner / "synthesis" / "project-brief.md",
        docs_dir=repo_root / "docs",
        sync_script=repo_root / "scripts" / "sync-wiki-docs.sh",
    )
