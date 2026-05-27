from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from pipeline.api.main import create_app
from pipeline.wiki_core.paths import WikiPaths


def _make_empty_paths(root: Path) -> WikiPaths:
    wiki_inner = root / "wiki"
    return WikiPaths(
        repo_root=root,
        wiki_root=root,
        raw_llm=root / "raw" / "llm",
        raw_web=root / "raw" / "web",
        wiki_inner=wiki_inner,
        sources=wiki_inner / "sources",
        concepts=wiki_inner / "concepts",
        synthesis=wiki_inner / "synthesis",
        index=wiki_inner / "index.md",
        log=wiki_inner / "log.md",
        evolving_thesis=wiki_inner / "synthesis" / "evolving-thesis.md",
        project_brief=wiki_inner / "synthesis" / "project-brief.md",
        docs_dir=root / "docs",
        sync_script=root / "scripts" / "sync-wiki-docs.sh",
    )


def test_auto_endpoint_returns_stream(tmp_path, monkeypatch):
    empty_paths = _make_empty_paths(tmp_path)
    monkeypatch.setattr(
        "pipeline.api.routes.auto.resolve_paths",
        lambda: empty_paths,
    )

    client = TestClient(create_app())
    resp = client.post("/api/auto", json={"file": "all"})
    assert resp.status_code == 200
    assert resp.headers.get("content-type", "").startswith("text/event-stream")
    assert resp.headers.get("cache-control") == "no-cache"


def test_auto_endpoint_events_have_expected_structure(tmp_path, monkeypatch):
    empty_paths = _make_empty_paths(tmp_path)
    monkeypatch.setattr(
        "pipeline.api.routes.auto.resolve_paths",
        lambda: empty_paths,
    )

    client = TestClient(create_app())
    resp = client.post("/api/auto", json={"file": "all"})
    assert resp.status_code == 200

    body = resp.text
    events = body.strip().split("\n\n")

    assert len(events) >= 1
    last_event = events[-1]
    assert "event: result" in last_event
    assert '"status"' in last_event
    assert '"summary"' in last_event
