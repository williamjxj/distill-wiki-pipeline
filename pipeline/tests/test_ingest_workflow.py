from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from pipeline.api.jobs import JobState, store
from pipeline.api.main import create_app
from pipeline.wiki_core.fs import read_markdown
from pipeline.wiki_core.paths import WikiPaths

FIXTURES = Path(__file__).parent / "fixtures" / "minimal-wiki"
RAW_PATH = "raw/llm/2026-05-25-claude-test.md"

DRAFT_JSON = {
    "source_md": (
        "---\n"
        "type: source-summary\n"
        "raw: raw/llm/2026-05-25-claude-test.md\n"
        "source: claude\n"
        "date: 2026-05-25\n"
        "---\n\n"
        "# Test Source\n\n"
        "## Key Claims\n"
        "- Example claim\n"
    ),
    "concept_updates": {
        "test-concept": (
            "---\n"
            "type: concept\n"
            "sources: [2026-05-25-claude-test]\n"
            "last_updated: 2026-05-25\n"
            "---\n\n"
            "# Test Concept\n\n"
            "## Consensus\n"
            "- Agreed point\n"
        ),
    },
    "thesis_delta": "## Current Understanding\n- Thesis updated from ingest test.",
    "index_lines": [
        "- [[2026-05-25-claude-test]] — test source summary",
        "- [[test-concept]] — concept from ingest test",
    ],
    "log_entry": (
        "## [2026-05-25] ingest | 2026-05-25-claude-test\n"
        "Processed raw/llm/2026-05-25-claude-test.md in workflow test."
    ),
}


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
        "# Evolving Thesis\n\n## Current Understanding\n- Initial.\n",
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
        if "Approved analysis" in user:
            return f"```json\n{json.dumps(DRAFT_JSON)}\n```"
        return "Analysis: key claims and concept slugs for operator review."

    monkeypatch.setattr(
        "pipeline.llm.workflows.ingest.complete_ollama",
        fake_complete,
    )


@pytest.fixture
def client(
    wiki_paths: WikiPaths,
    mock_ollama: None,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        "pipeline.llm.workflows.ingest.resolve_paths",
        lambda: wiki_paths,
    )
    return TestClient(create_app())


def test_ingest_workflow_state_transitions(client: TestClient, wiki_paths: WikiPaths):
    resp = client.post("/api/jobs/ingest", json={"raw_path": RAW_PATH})
    assert resp.status_code == 200
    job = resp.json()
    assert job["state"] == JobState.ANALYSIS_DONE.value
    assert job["analysis"]
    job_id = job["id"]

    resp = client.post(f"/api/jobs/ingest/{job_id}/approve-analysis")
    assert resp.status_code == 200
    job = resp.json()
    assert job["state"] == JobState.DRAFT_DONE.value
    assert job["draft_payload"]["source_md"]

    resp = client.post(f"/api/jobs/ingest/{job_id}/approve-draft")
    assert resp.status_code == 200
    assert resp.json()["state"] == JobState.AWAITING_FINAL_CONFIRM.value

    resp = client.post(f"/api/jobs/ingest/{job_id}/confirm")
    assert resp.status_code == 200
    assert resp.json()["state"] == JobState.COMPLETED.value

    raw_file = wiki_paths.wiki_root / RAW_PATH
    meta, body = read_markdown(raw_file)
    assert meta["status"] == "ingested"
    assert body.strip() == "Body content here."

    source = wiki_paths.sources / "2026-05-25-claude-test.md"
    assert source.is_file()
    assert "Key Claims" in source.read_text(encoding="utf-8")

    concept = wiki_paths.concepts / "test-concept.md"
    assert concept.is_file()

    thesis = wiki_paths.evolving_thesis.read_text(encoding="utf-8")
    assert "Thesis updated from ingest test" in thesis

    index = wiki_paths.index.read_text(encoding="utf-8")
    assert "[[2026-05-25-claude-test]]" in index
    assert "[[test-concept]]" in index

    log = wiki_paths.log.read_text(encoding="utf-8")
    assert "ingest | 2026-05-25-claude-test" in log


def test_only_one_active_ingest(client: TestClient, mock_ollama):
    first = client.post("/api/jobs/ingest", json={"raw_path": RAW_PATH})
    assert first.status_code == 200
    second = client.post("/api/jobs/ingest", json={"raw_path": RAW_PATH})
    assert second.status_code == 409


def test_extract_json_strips_markdown_fence():
    from pipeline.llm.workflows.ingest import extract_json

    payload = extract_json(f"```json\n{json.dumps(DRAFT_JSON)}\n```")
    assert payload["source_md"].startswith("---")
