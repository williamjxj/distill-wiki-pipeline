from pathlib import Path
from pipeline.wiki_core.fs import parse_frontmatter, write_frontmatter_field

FIXTURES = Path(__file__).parent / "fixtures" / "minimal-wiki"


def test_parse_frontmatter_extracts_status():
    path = FIXTURES / "raw/llm/2026-05-25-claude-test.md"
    meta, body = parse_frontmatter(path.read_text())
    assert meta["status"] == "pending"
    assert "Body content" in body


def test_write_frontmatter_field_updates_status(tmp_path):
    src = FIXTURES / "raw/llm/2026-05-25-claude-test.md"
    dest = tmp_path / "test.md"
    dest.write_text(src.read_text())
    write_frontmatter_field(dest, "status", "ingested")
    meta, _ = parse_frontmatter(dest.read_text())
    assert meta["status"] == "ingested"
