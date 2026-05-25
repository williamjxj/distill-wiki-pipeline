from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from pipeline.api.jobs import ExportJobState, store
from pipeline.api.main import create_app
from pipeline.wiki_core.fs import read_markdown
from pipeline.wiki_core.paths import WikiPaths

FIXTURES = Path(__file__).parent / "fixtures" / "minimal-wiki"

DRAFT_BODY = """# Project Brief: Test Project

## Problem
Research needs a repeatable export path.

## Current Understanding
- Wiki distillation produces signal from synthetic LLM sources.

## Chosen Approach
- Use export-brief workflow with human approval gates.

## Constraints
- Local Ollama default; cloud override optional.

## Non-Goals
- Fully unattended export.

## Rejected Alternatives
- Dumping full wiki to coding agents.

## Open Questions
- When to evaluate cloud LLM for export quality?
"""


def make_paths(root: Path) -> WikiPaths:
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


@pytest.fixture
def wiki_tree(tmp_path: Path) -> Path:
    root = tmp_path / "wiki-env"
    shutil.copytree(FIXTURES, root)
    synthesis = root / "wiki" / "synthesis"
    synthesis.mkdir(parents=True, exist_ok=True)
    (synthesis / "evolving-thesis.md").write_text(
        "# Evolving Thesis\n\n## Current Understanding\n- Initial thesis for export test.\n",
        encoding="utf-8",
    )
    (root / "wiki" / "log.md").write_text("# Wiki Log\n", encoding="utf-8")
    (root / "wiki" / "sources").mkdir(exist_ok=True)
    return root


@pytest.fixture
def wiki_paths(wiki_tree: Path) -> WikiPaths:
    return make_paths(wiki_tree)


@pytest.fixture(autouse=True)
def reset_store():
    store.clear()
    yield
    store.clear()


@pytest.fixture
def mock_ollama(monkeypatch: pytest.MonkeyPatch):
    async def fake_complete(system: str, user: str, task: str = "ingest") -> str:
        return DRAFT_BODY

    monkeypatch.setattr(
        "pipeline.llm.workflows.export.complete_ollama",
        fake_complete,
    )


@pytest.fixture
def client(
    wiki_paths: WikiPaths,
    mock_ollama: None,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        "pipeline.llm.workflows.export.resolve_paths",
        lambda: wiki_paths,
    )
    return TestClient(create_app())


def test_export_blocked_by_lint_errors(client: TestClient):
    resp = client.post("/api/jobs/export", json={"force": False})
    assert resp.status_code == 200
    job = resp.json()
    assert job["state"] == ExportJobState.LINT_BLOCKED.value
    assert job["lint_findings"]
    assert all(f["severity"] == "error" for f in job["lint_findings"])


def test_export_approve_flow_with_force(client: TestClient, wiki_paths: WikiPaths):
    start = client.post("/api/jobs/export", json={"force": True})
    assert start.status_code == 200
    job = start.json()
    assert job["state"] == ExportJobState.DRAFT_DONE.value
    assert job["draft_body"].startswith("# Project Brief")
    job_id = job["id"]

    meta, body = read_markdown(wiki_paths.project_brief)
    assert meta["status"] == "draft"
    assert meta["export_cycle"] == 1
    assert "Research needs a repeatable export path" in body

    approve = client.post(f"/api/jobs/export/{job_id}/approve")
    assert approve.status_code == 200
    approved = approve.json()
    assert approved["state"] == ExportJobState.COMPLETED.value

    meta, body = read_markdown(wiki_paths.project_brief)
    assert meta["status"] == "current"
    assert meta["export_cycle"] == 1

    log = wiki_paths.log.read_text(encoding="utf-8")
    assert "export | project-brief cycle 1" in log


def test_export_supersedes_prior_current_brief(client: TestClient, wiki_paths: WikiPaths):
    from pipeline.wiki_core.fs import write_markdown

    write_markdown(
        wiki_paths.project_brief,
        {
            "type": "project-brief",
            "status": "current",
            "date": "2026-05-24",
            "export_cycle": 1,
            "sources_ingested": 0,
        },
        "# Project Brief: Old\n\n## Problem\nOld brief.\n",
    )

    start = client.post("/api/jobs/export", json={"force": True})
    assert start.status_code == 200
    job = start.json()
    assert job["prior_brief_status"] == "current"
    assert job["export_cycle"] == 2

    meta, _ = read_markdown(wiki_paths.project_brief)
    assert meta["status"] == "draft"
    assert meta["export_cycle"] == 2

    approve = client.post(f"/api/jobs/export/{job['id']}/approve")
    assert approve.status_code == 200

    meta, body = read_markdown(wiki_paths.project_brief)
    assert meta["status"] == "current"
    assert meta["export_cycle"] == 2
    assert "Test Project" in body

    log = wiki_paths.log.read_text(encoding="utf-8")
    assert "project-brief cycle 2" in log
