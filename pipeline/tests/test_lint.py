from pathlib import Path
from pipeline.wiki_core.lint import run_lint
from pipeline.wiki_core.paths import WikiPaths

FIXTURES = Path(__file__).parent / "fixtures" / "minimal-wiki"


def make_paths() -> WikiPaths:
    root = FIXTURES
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


def test_lint_reports_pending_raw():
    findings = run_lint(make_paths())
    codes = {f.code for f in findings}
    assert "pending_raw" in codes


def test_lint_reports_orphan_pages():
    findings = run_lint(make_paths())
    assert any(f.code == "orphan_page" for f in findings)


def test_lint_reports_missing_wikilink_targets():
    findings = run_lint(make_paths())
    assert any(f.code == "missing_page" for f in findings)
