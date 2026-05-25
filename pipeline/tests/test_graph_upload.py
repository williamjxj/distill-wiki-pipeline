from pathlib import Path

from fastapi.testclient import TestClient
from pipeline.api.main import create_app
from pipeline.wiki_core.graph import build_graph
from pipeline.wiki_core.paths import WikiPaths
from test_lint import make_paths

FIXTURES = Path(__file__).parent / "fixtures" / "minimal-wiki"


def test_build_graph_returns_nodes_and_edges():
    graph = build_graph(make_paths())
    assert "nodes" in graph
    assert "edges" in graph
    assert isinstance(graph["nodes"], list)
    assert isinstance(graph["edges"], list)
    for node in graph["nodes"]:
        assert "id" in node
        assert "label" in node
    for edge in graph["edges"]:
        assert "source" in edge
        assert "target" in edge


def test_graph_endpoint():
    client = TestClient(create_app())
    resp = client.get("/api/graph")
    assert resp.status_code == 200
    data = resp.json()
    assert "nodes" in data
    assert "edges" in data


def test_upload_llm_raw(tmp_path, monkeypatch):
    wiki_root = tmp_path / "wiki"
    raw_llm = wiki_root / "raw" / "llm"
    raw_web = wiki_root / "raw" / "web"
    raw_llm.mkdir(parents=True)
    raw_web.mkdir(parents=True)

    paths = WikiPaths(
        repo_root=tmp_path,
        wiki_root=wiki_root,
        raw_llm=raw_llm,
        raw_web=raw_web,
        wiki_inner=wiki_root / "wiki",
        sources=wiki_root / "wiki" / "sources",
        concepts=wiki_root / "wiki" / "concepts",
        synthesis=wiki_root / "wiki" / "synthesis",
        index=wiki_root / "wiki" / "index.md",
        log=wiki_root / "wiki" / "log.md",
        evolving_thesis=wiki_root / "wiki" / "synthesis" / "evolving-thesis.md",
        project_brief=wiki_root / "wiki" / "synthesis" / "project-brief.md",
        docs_dir=tmp_path / "docs",
        sync_script=tmp_path / "scripts" / "sync-wiki-docs.sh",
    )

    monkeypatch.setattr(
        "pipeline.api.routes.upload.resolve_paths",
        lambda config_path=None: paths,
    )

    client = TestClient(create_app())
    resp = client.post(
        "/api/raw/upload",
        data={
            "type": "llm-chat",
            "source": "claude",
            "topic": "auth patterns",
            "date": "2026-05-25",
            "question": "How should we handle auth?",
        },
        files={"file": ("chat.md", b"Assistant: use JWT.\n", "text/markdown")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["path"] == "raw/llm/2026-05-25-claude-auth-patterns.md"
    assert data["meta"]["status"] == "pending"
    assert data["meta"]["question"] == "How should we handle auth?"

    written = raw_llm / "2026-05-25-claude-auth-patterns.md"
    assert written.is_file()
    assert "Assistant: use JWT." in written.read_text(encoding="utf-8")


def test_upload_web_requires_url(tmp_path, monkeypatch):
    wiki_root = tmp_path / "wiki"
    raw_llm = wiki_root / "raw" / "llm"
    raw_web = wiki_root / "raw" / "web"
    raw_llm.mkdir(parents=True)
    raw_web.mkdir(parents=True)

    paths = WikiPaths(
        repo_root=tmp_path,
        wiki_root=wiki_root,
        raw_llm=raw_llm,
        raw_web=raw_web,
        wiki_inner=wiki_root / "wiki",
        sources=wiki_root / "wiki" / "sources",
        concepts=wiki_root / "wiki" / "concepts",
        synthesis=wiki_root / "wiki" / "synthesis",
        index=wiki_root / "wiki" / "index.md",
        log=wiki_root / "wiki" / "log.md",
        evolving_thesis=wiki_root / "wiki" / "synthesis" / "evolving-thesis.md",
        project_brief=wiki_root / "wiki" / "synthesis" / "project-brief.md",
        docs_dir=tmp_path / "docs",
        sync_script=tmp_path / "scripts" / "sync-wiki-docs.sh",
    )

    monkeypatch.setattr(
        "pipeline.api.routes.upload.resolve_paths",
        lambda config_path=None: paths,
    )

    client = TestClient(create_app())
    resp = client.post(
        "/api/raw/upload",
        data={
            "type": "web-article",
            "source": "web",
            "topic": "Next.js docs",
            "date": "2026-05-25",
        },
        files={"file": ("nextjs-app-router-docs.md", b"Article body.\n", "text/markdown")},
    )
    assert resp.status_code == 400
    assert "url" in resp.json()["detail"]
