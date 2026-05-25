from pathlib import Path

from pipeline.mcp.server import handle_get_status, handle_list_pending, handle_read_page, handle_search
from pipeline.wiki_core.paths import resolve_paths

FIXTURES = Path(__file__).parent / "fixtures"
FIXTURE_CONFIG = FIXTURES / "minimal-wiki-config.yaml"


def fixture_paths():
    return resolve_paths(FIXTURE_CONFIG)


def test_wiki_list_pending_returns_items_shape():
    result = handle_list_pending(fixture_paths())
    assert "items" in result
    assert isinstance(result["items"], list)
    assert len(result["items"]) >= 1
    item = result["items"][0]
    assert "path" in item
    assert "meta" in item
    assert item["meta"]["status"] == "pending"


def test_wiki_get_status_returns_expected_shape():
    result = handle_get_status(fixture_paths())
    assert isinstance(result["pending_raw_count"], int)
    assert result["pending_raw_count"] >= 1
    assert isinstance(result["pending_raw_files"], list)
    assert isinstance(result["lint_error_count"], int)
    assert isinstance(result["lint_warning_count"], int)
    assert "export_cycle" in result
    assert "brief_status" in result
    assert "last_log_entry" in result


def test_wiki_read_page_by_slug():
    result = handle_read_page(fixture_paths(), "orphan-concept")
    assert "error" not in result
    assert result["path"] == "concepts/orphan-concept.md"
    assert result["meta"]["type"] == "concept"
    assert "Orphan Concept" in result["body"]


def test_wiki_search_finds_content():
    result = handle_search(fixture_paths(), "Orphan")
    assert result["query"] == "Orphan"
    assert len(result["matches"]) >= 1
    assert any("Orphan Concept" in match["text"] for match in result["matches"])
