# Wiki Pipeline Operator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local wiki pipeline operator — Python `wiki_core` library, CLI, FastAPI + React UI with Ollama-backed ingest/export workflows, and an MCP sidecar — so the LLM-Wiki ETL pipeline runs independently of Cursor.

**Architecture:** Single `wiki_core` library owns all deterministic markdown/git operations. FastAPI exposes HTTP/SSE for the React UI and orchestrates staged LLM jobs via Ollama. MCP wraps the same library for external agents. Human approval gates pause jobs before writing ingested status or promoting briefs to `current`.

**Tech Stack:** Python 3.11+, FastAPI, uvicorn, PyYAML, httpx (Ollama), pytest; Vite + React + TypeScript; MCP Python SDK

**Spec:** `docs/superpowers/specs/2026-05-25-wiki-pipeline-operator-design.md`

---

## File Map

| File | Responsibility |
|------|----------------|
| `pipeline/pyproject.toml` | Python package metadata and dependencies |
| `pipeline/config.yaml` | Wiki paths, Ollama URL/model, server port |
| `pipeline/wiki_core/paths.py` | Resolve repo root, wiki submodule paths |
| `pipeline/wiki_core/fs.py` | Read/write markdown, parse/update YAML frontmatter |
| `pipeline/wiki_core/status.py` | Aggregate pipeline health for dashboard/CLI/MCP |
| `pipeline/wiki_core/lint.py` | Deterministic lint rules (7 checks from wiki-lint skill) |
| `pipeline/wiki_core/sync.py` | Wrap `scripts/sync-wiki-docs.sh` |
| `pipeline/wiki_core/models.py` | Shared dataclasses: LintFinding, PipelineStatus, RawFile |
| `pipeline/cli/main.py` | Click/Typer CLI: status, lint, sync, serve, mcp, watch |
| `pipeline/api/main.py` | FastAPI app factory |
| `pipeline/api/routes/status.py` | GET /api/status |
| `pipeline/api/routes/lint.py` | GET /api/lint |
| `pipeline/api/routes/sync.py` | POST /api/sync |
| `pipeline/api/routes/raw.py` | GET /api/raw/pending, GET /api/raw/{path} |
| `pipeline/api/routes/jobs.py` | Job CRUD + SSE streaming for ingest/export |
| `pipeline/api/jobs.py` | In-memory job store, one active ingest constraint |
| `pipeline/llm/router.py` | Route tasks to Ollama (httpx streaming) |
| `pipeline/llm/prompts/ingest.py` | System prompts ported from AGENTS.md + wiki-ingest skill |
| `pipeline/llm/prompts/export.py` | System prompts ported from wiki-export-brief skill |
| `pipeline/llm/workflows/ingest.py` | Two-stage ingest with pause checkpoints |
| `pipeline/llm/workflows/export.py` | Lint gate → brief draft → approval writes |
| `pipeline/mcp/server.py` | MCP stdio server exposing wiki_core tools |
| `pipeline/ui/` | Vite + React SPA (dashboard, ingest wizard, export, sync) |
| `scripts/wiki-pipeline` | Shell wrapper → `python -m pipeline.cli.main` |
| `pipeline/tests/fixtures/` | Minimal wiki tree for unit tests |
| `pipeline/tests/test_fs.py` | Frontmatter parse/write tests |
| `pipeline/tests/test_lint.py` | Golden lint tests |
| `pipeline/tests/test_status.py` | Status aggregation tests |
| `pipeline/tests/test_api.py` | FastAPI integration tests (mock Ollama) |

---

### Task 1: Python Package Scaffold

**Files:**
- Create: `pipeline/pyproject.toml`, `pipeline/config.yaml`, `pipeline/__init__.py`, `pipeline/wiki_core/__init__.py`, `pipeline/cli/__init__.py`, `pipeline/cli/main.py` (stub)
- Modify: `.gitignore`
- Create: `scripts/wiki-pipeline`

- [ ] **Step 1: Create pyproject.toml**

Create `pipeline/pyproject.toml`:

```toml
[project]
name = "wiki-pipeline"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "pyyaml>=6.0",
  "httpx>=0.27",
  "typer>=0.12",
  "fastapi>=0.115",
  "uvicorn[standard]>=0.32",
  "mcp>=1.0",
  "python-multipart>=0.0.9",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-asyncio>=0.24"]

[project.scripts]
wiki-pipeline = "pipeline.cli.main:app"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

- [ ] **Step 2: Create config.yaml**

Create `pipeline/config.yaml`:

```yaml
wiki_root: ../wiki
parent_root: ..
llm:
  default: ollama
  ollama_base_url: http://localhost:11434
  models:
    ollama: qwen2.5:7b-instruct
  overrides:
    export_brief: ollama
server:
  host: 127.0.0.1
  port: 8787
```

- [ ] **Step 3: Update .gitignore**

Append to `.gitignore`:

```
# Python pipeline
pipeline/venv/
pipeline/__pycache__/
pipeline/**/__pycache__/
pipeline/.pytest_cache/
pipeline/ui/node_modules/
pipeline/ui/dist/
*.egg-info/
```

- [ ] **Step 4: Create CLI stub and shell wrapper**

Create `pipeline/cli/main.py`:

```python
import typer

app = typer.Typer(name="wiki-pipeline", help="LLM-Wiki pipeline operator")

@app.command()
def status():
    typer.echo("wiki-pipeline: not yet implemented")

if __name__ == "__main__":
    app()
```

Create `scripts/wiki-pipeline`:

```bash
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/pipeline"
exec python -m pipeline.cli.main "$@"
```

Run: `chmod +x scripts/wiki-pipeline`

- [ ] **Step 5: Install and verify**

```bash
cd pipeline
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
cd ..
./scripts/wiki-pipeline status
```

Expected: `wiki-pipeline: not yet implemented`

- [ ] **Step 6: Commit**

```bash
git add pipeline/ scripts/wiki-pipeline .gitignore
git commit -m "$(cat <<'EOF'
feat: scaffold wiki-pipeline Python package and CLI stub

EOF
)"
```

---

### Task 2: wiki_core — Paths and File I/O

**Files:**
- Create: `pipeline/wiki_core/paths.py`, `pipeline/wiki_core/fs.py`, `pipeline/wiki_core/models.py`
- Create: `pipeline/tests/fixtures/minimal-wiki/…`, `pipeline/tests/test_fs.py`
- Modify: `pipeline/cli/main.py` (no change yet — tests only)

- [ ] **Step 1: Write failing test for frontmatter parsing**

Create `pipeline/tests/fixtures/minimal-wiki/raw/llm/2026-05-25-claude-test.md`:

```markdown
---
type: llm-chat
source: claude
topic: "test topic"
date: 2026-05-25
status: pending
question: "test question"
---

Body content here.
```

Create `pipeline/tests/test_fs.py`:

```python
from pathlib import Path
import pytest
from wiki_core.fs import parse_frontmatter, read_markdown, write_frontmatter_field

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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd pipeline && source venv/bin/activate
pytest tests/test_fs.py -v
```

Expected: FAIL — `ModuleNotFoundError: wiki_core`

- [ ] **Step 3: Implement paths.py and fs.py**

Create `pipeline/wiki_core/paths.py`:

```python
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
    pipeline_dir = Path(__file__).resolve().parent.parent
    path = config_path or (pipeline_dir / _CONFIG_NAME)
    with path.open() as f:
        return yaml.safe_load(f)

def resolve_paths(config_path: Path | None = None) -> WikiPaths:
    pipeline_dir = Path(__file__).resolve().parent.parent
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
```

Create `pipeline/wiki_core/fs.py`:

```python
from __future__ import annotations
import re
from pathlib import Path
import yaml

_FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n?", re.DOTALL)

def parse_frontmatter(text: str) -> tuple[dict, str]:
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    meta = yaml.safe_load(match.group(1)) or {}
    body = text[match.end():]
    return meta, body

def read_markdown(path: Path) -> tuple[dict, str]:
    return parse_frontmatter(path.read_text(encoding="utf-8"))

def render_markdown(meta: dict, body: str) -> str:
    header = yaml.safe_dump(meta, sort_keys=False).strip()
    body = body.lstrip("\n")
    return f"---\n{header}\n---\n\n{body}"

def write_markdown(path: Path, meta: dict, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(meta, body), encoding="utf-8")

def write_frontmatter_field(path: Path, field: str, value) -> None:
    meta, body = read_markdown(path)
    meta[field] = value
    write_markdown(path, meta, body)

def list_raw_files(raw_dirs: list[Path]) -> list[Path]:
    files: list[Path] = []
    for directory in raw_dirs:
        if directory.is_dir():
            files.extend(sorted(directory.glob("*.md")))
    return files
```

Create `pipeline/wiki_core/models.py`:

```python
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum

class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

@dataclass
class LintFinding:
    severity: Severity
    code: str
    message: str
    path: str | None = None

@dataclass
class RawFile:
    path: str
    status: str
    topic: str | None
    source: str | None
    date: str | None

@dataclass
class PipelineStatus:
    pending_raw_count: int
    pending_raw_files: list[RawFile]
    lint_error_count: int
    lint_warning_count: int
    export_cycle: int | None
    brief_status: str | None
    last_log_entry: str | None
```

- [ ] **Step 4: Run tests**

```bash
cd pipeline && pytest tests/test_fs.py -v
```

Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add pipeline/wiki_core/ pipeline/tests/
git commit -m "$(cat <<'EOF'
feat: add wiki_core paths and markdown frontmatter I/O

EOF
)"
```

---

### Task 3: wiki_core — Lint Engine

**Files:**
- Create: `pipeline/wiki_core/lint.py`, `pipeline/tests/test_lint.py`
- Modify: `pipeline/tests/fixtures/minimal-wiki/` (add wiki pages for lint cases)

- [ ] **Step 1: Write failing lint tests**

Create fixture `pipeline/tests/fixtures/minimal-wiki/wiki/index.md`:

```markdown
# Wiki Index

## Sources

## Concepts

- [[orphan-concept]] — listed but page missing body cross-links
```

Create `pipeline/tests/fixtures/minimal-wiki/wiki/concepts/orphan-concept.md`:

```markdown
---
type: concept
sources: []
last_updated: 2026-05-25
---

# Orphan Concept

No inbound links from other pages.
```

Create `pipeline/tests/test_lint.py`:

```python
from pathlib import Path
import pytest
from wiki_core.lint import run_lint
from wiki_core.paths import WikiPaths
from wiki_core.models import Severity

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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd pipeline && pytest tests/test_lint.py -v
```

Expected: FAIL — `run_lint` not defined

- [ ] **Step 3: Implement lint.py**

Create `pipeline/wiki_core/lint.py`:

```python
from __future__ import annotations
import re
from pathlib import Path
from wiki_core.fs import list_raw_files, parse_frontmatter, read_markdown
from wiki_core.models import LintFinding, Severity
from wiki_core.paths import WikiPaths

_WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")
_INDEX_ENTRY_RE = re.compile(r"^\s*-\s*\[\[([^\]|]+)")

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

def _index_slugs(index_text: str) -> set[str]:
    return set(_INDEX_ENTRY_RE.findall(index_text))

def run_lint(paths: WikiPaths) -> list[LintFinding]:
    findings: list[LintFinding] = []

    # Pending raw files
    for raw_path in list_raw_files([paths.raw_llm, paths.raw_web]):
        meta, _ = read_markdown(raw_path)
        if meta.get("status") == "pending":
            findings.append(LintFinding(
                severity=Severity.INFO,
                code="pending_raw",
                message=f"Pending ingest: {raw_path.relative_to(paths.wiki_root)}",
                path=str(raw_path.relative_to(paths.wiki_root)),
            ))

    pages = _wiki_page_paths(paths)
    slug_to_path = {_slug_for(p): p for p in pages}
    all_slugs = set(slug_to_path.keys())

    inbound: dict[str, int] = {slug: 0 for slug in all_slugs}
    all_links: set[str] = set()

    for page in pages:
        _, body = read_markdown(page)
        links = _collect_wikilinks(body)
        all_links.update(links)
        for link in links:
            if link in inbound:
                inbound[link] += 1

    # Missing wikilink targets
    for link in sorted(all_links):
        if link not in all_slugs and link not in {"index"}:
            findings.append(LintFinding(
                severity=Severity.ERROR,
                code="missing_page",
                message=f"Wikilink [[{link}]] has no matching page",
            ))

    # Orphan pages (no inbound links; exclude synthesis index staples)
    exempt = {"evolving-thesis", "project-brief", "index"}
    for slug, count in inbound.items():
        if count == 0 and slug not in exempt:
            findings.append(LintFinding(
                severity=Severity.WARNING,
                code="orphan_page",
                message=f"Page [[{slug}]] has no inbound wikilinks",
                path=f"wiki/{slug_to_path[slug].relative_to(paths.wiki_inner)}",
            ))

    # Index sync — pages on disk but not listed in index.md
    if paths.index.is_file():
        _, index_body = read_markdown(paths.index)
        indexed = _index_slugs(index_body)
        for slug in all_slugs:
            if slug not in indexed and slug not in exempt:
                findings.append(LintFinding(
                    severity=Severity.WARNING,
                    code="index_out_of_sync",
                    message=f"Page [[{slug}]] exists on disk but missing from index.md",
                    path=f"wiki/{slug}.md",
                ))

    return findings
```

- [ ] **Step 4: Run tests**

```bash
cd pipeline && pytest tests/test_lint.py -v
```

Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add pipeline/wiki_core/lint.py pipeline/tests/
git commit -m "$(cat <<'EOF'
feat: add deterministic wiki lint engine

EOF
)"
```

---

### Task 4: wiki_core — Status, Sync, and CLI Commands

**Files:**
- Create: `pipeline/wiki_core/status.py`, `pipeline/wiki_core/sync.py`, `pipeline/tests/test_status.py`
- Modify: `pipeline/cli/main.py`

- [ ] **Step 1: Write failing status test**

Create `pipeline/tests/test_status.py`:

```python
from wiki_core.status import get_pipeline_status
from test_lint import make_paths

def test_status_counts_pending_raw():
    status = get_pipeline_status(make_paths())
    assert status.pending_raw_count >= 1
    assert status.last_log_entry is None or isinstance(status.last_log_entry, str)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd pipeline && pytest tests/test_status.py -v
```

Expected: FAIL

- [ ] **Step 3: Implement status.py and sync.py**

Create `pipeline/wiki_core/status.py`:

```python
from __future__ import annotations
import re
from wiki_core.fs import list_raw_files, read_markdown
from wiki_core.lint import run_lint
from wiki_core.models import PipelineStatus, RawFile, Severity
from wiki_core.paths import WikiPaths

_LOG_ENTRY_RE = re.compile(r"^## \[([^\]]+)\] (.+)$", re.MULTILINE)

def get_pipeline_status(paths: WikiPaths) -> PipelineStatus:
    pending_files: list[RawFile] = []
    for raw_path in list_raw_files([paths.raw_llm, paths.raw_web]):
        meta, _ = read_markdown(raw_path)
        if meta.get("status") == "pending":
            pending_files.append(RawFile(
                path=str(raw_path.relative_to(paths.wiki_root)),
                status=meta.get("status", "unknown"),
                topic=meta.get("topic"),
                source=meta.get("source"),
                date=str(meta.get("date")) if meta.get("date") else None,
            ))

    findings = run_lint(paths)
    errors = sum(1 for f in findings if f.severity == Severity.ERROR)
    warnings = sum(1 for f in findings if f.severity == Severity.WARNING)

    export_cycle = None
    brief_status = None
    if paths.project_brief.is_file():
        meta, _ = read_markdown(paths.project_brief)
        brief_status = meta.get("status")
        export_cycle = meta.get("export_cycle")

    last_log_entry = None
    if paths.log.is_file():
        text = paths.log.read_text(encoding="utf-8")
        matches = _LOG_ENTRY_RE.findall(text)
        if matches:
            date, rest = matches[-1]
            last_log_entry = f"[{date}] {rest}"

    return PipelineStatus(
        pending_raw_count=len(pending_files),
        pending_raw_files=pending_files,
        lint_error_count=errors,
        lint_warning_count=warnings,
        export_cycle=export_cycle,
        brief_status=brief_status,
        last_log_entry=last_log_entry,
    )
```

Create `pipeline/wiki_core/sync.py`:

```python
from __future__ import annotations
import subprocess
from dataclasses import dataclass
from wiki_core.fs import read_markdown
from wiki_core.paths import WikiPaths

@dataclass
class SyncResult:
    stdout: str
    warnings: list[str]

def run_sync(paths: WikiPaths, brief_only: bool = False) -> SyncResult:
    warnings: list[str] = []
    if paths.project_brief.is_file():
        meta, _ = read_markdown(paths.project_brief)
        if meta.get("status") == "draft":
            warnings.append("project-brief.md is still status: draft")

    cmd = [str(paths.sync_script)]
    if brief_only:
        cmd.append("--brief-only")

    proc = subprocess.run(cmd, capture_output=True, text=True, check=False, cwd=paths.repo_root)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout or "sync failed")

    return SyncResult(stdout=proc.stdout.strip(), warnings=warnings)
```

- [ ] **Step 4: Wire CLI commands**

Replace `pipeline/cli/main.py` with:

```python
from __future__ import annotations
import json
import typer
from wiki_core.lint import run_lint
from wiki_core.paths import resolve_paths
from wiki_core.status import get_pipeline_status
from wiki_core.sync import run_sync

app = typer.Typer(name="wiki-pipeline", help="LLM-Wiki pipeline operator")

@app.command()
def status():
    paths = resolve_paths()
    s = get_pipeline_status(paths)
    typer.echo(f"Pending raw: {s.pending_raw_count}")
    typer.echo(f"Lint errors/warnings: {s.lint_error_count}/{s.lint_warning_count}")
    typer.echo(f"Brief status: {s.brief_status or 'none'}")
    typer.echo(f"Export cycle: {s.export_cycle or 'none'}")
    if s.last_log_entry:
        typer.echo(f"Last log: {s.last_log_entry}")

@app.command()
def lint(json_output: bool = typer.Option(False, "--json")):
    paths = resolve_paths()
    findings = run_lint(paths)
    if json_output:
        typer.echo(json.dumps([f.__dict__ for f in findings], default=str))
    else:
        for f in findings:
            typer.echo(f"[{f.severity.value}] {f.code}: {f.message}")

@app.command()
def sync(brief_only: bool = typer.Option(False, "--brief-only")):
    paths = resolve_paths()
    result = run_sync(paths, brief_only=brief_only)
    typer.echo(result.stdout)
    for w in result.warnings:
        typer.echo(f"WARNING: {w}")

if __name__ == "__main__":
    app()
```

- [ ] **Step 5: Run tests and manual CLI check**

```bash
cd pipeline && pytest tests/ -v
cd .. && ./scripts/wiki-pipeline status
./scripts/wiki-pipeline lint | head
```

Expected: tests PASS; status shows pending count against real wiki submodule

- [ ] **Step 6: Commit**

```bash
git add pipeline/
git commit -m "$(cat <<'EOF'
feat: add pipeline status, sync wrapper, and CLI commands

EOF
)"
```

---

### Task 5: FastAPI Skeleton + Status/Lint/Sync/Raw Routes

**Files:**
- Create: `pipeline/api/__init__.py`, `pipeline/api/main.py`, `pipeline/api/routes/status.py`, `pipeline/api/routes/lint.py`, `pipeline/api/routes/sync.py`, `pipeline/api/routes/raw.py`
- Create: `pipeline/tests/test_api.py`
- Modify: `pipeline/cli/main.py` (add `serve` command)

- [ ] **Step 1: Write failing API test**

Create `pipeline/tests/test_api.py`:

```python
from fastapi.testclient import TestClient
from api.main import create_app

def test_status_endpoint():
    client = TestClient(create_app())
    resp = client.get("/api/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "pending_raw_count" in data
    assert "lint_error_count" in data
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd pipeline && pytest tests/test_api.py -v
```

Expected: FAIL

- [ ] **Step 3: Implement FastAPI app**

Create `pipeline/api/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import lint, raw, status, sync

def create_app() -> FastAPI:
    app = FastAPI(title="Wiki Pipeline Operator")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(status.router, prefix="/api")
    app.include_router(lint.router, prefix="/api")
    app.include_router(sync.router, prefix="/api")
    app.include_router(raw.router, prefix="/api")
    return app

app = create_app()
```

Create `pipeline/api/routes/status.py`:

```python
from fastapi import APIRouter
from wiki_core.paths import resolve_paths
from wiki_core.status import get_pipeline_status

router = APIRouter(tags=["status"])

@router.get("/status")
def get_status():
    s = get_pipeline_status(resolve_paths())
    return {
        "pending_raw_count": s.pending_raw_count,
        "pending_raw_files": [f.__dict__ for f in s.pending_raw_files],
        "lint_error_count": s.lint_error_count,
        "lint_warning_count": s.lint_warning_count,
        "export_cycle": s.export_cycle,
        "brief_status": s.brief_status,
        "last_log_entry": s.last_log_entry,
    }
```

Create `pipeline/api/routes/lint.py`:

```python
from fastapi import APIRouter
from wiki_core.lint import run_lint
from wiki_core.paths import resolve_paths

router = APIRouter(tags=["lint"])

@router.get("/lint")
def get_lint():
    findings = run_lint(resolve_paths())
    return {"findings": [f.__dict__ for f in findings]}
```

Create `pipeline/api/routes/sync.py`:

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from wiki_core.paths import resolve_paths
from wiki_core.sync import run_sync

router = APIRouter(tags=["sync"])

class SyncRequest(BaseModel):
    brief_only: bool = False

@router.post("/sync")
def post_sync(body: SyncRequest):
    try:
        result = run_sync(resolve_paths(), brief_only=body.brief_only)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"stdout": result.stdout, "warnings": result.warnings}
```

Create `pipeline/api/routes/raw.py`:

```python
from fastapi import APIRouter, HTTPException
from wiki_core.fs import list_raw_files, read_markdown
from wiki_core.paths import resolve_paths

router = APIRouter(tags=["raw"])

@router.get("/raw/pending")
def list_pending():
    paths = resolve_paths()
    items = []
    for raw_path in list_raw_files([paths.raw_llm, paths.raw_web]):
        meta, _ = read_markdown(raw_path)
        if meta.get("status") == "pending":
            items.append({
                "path": str(raw_path.relative_to(paths.wiki_root)),
                "meta": meta,
            })
    return {"items": items}

@router.get("/raw/{file_path:path}")
def get_raw(file_path: str):
    paths = resolve_paths()
    raw_path = (paths.wiki_root / file_path).resolve()
    if not str(raw_path).startswith(str(paths.wiki_root.resolve())):
        raise HTTPException(status_code=400, detail="invalid path")
    if not raw_path.is_file():
        raise HTTPException(status_code=404, detail="not found")
    meta, body = read_markdown(raw_path)
    return {"path": file_path, "meta": meta, "body": body}
```

Add to `pipeline/cli/main.py`:

```python
@app.command()
def serve(host: str = "127.0.0.1", port: int = 8787):
    import uvicorn
    uvicorn.run("api.main:app", host=host, port=port, reload=True)
```

- [ ] **Step 4: Run tests**

```bash
cd pipeline && pytest tests/test_api.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pipeline/api/ pipeline/cli/main.py pipeline/tests/test_api.py
git commit -m "$(cat <<'EOF'
feat: add FastAPI skeleton with status, lint, sync, and raw routes

EOF
)"
```

---

### Task 6: React UI — Phase 1 Dashboard MVP

**Files:**
- Create: `pipeline/ui/package.json`, `pipeline/ui/vite.config.ts`, `pipeline/ui/index.html`, `pipeline/ui/src/main.tsx`, `pipeline/ui/src/App.tsx`, `pipeline/ui/src/api.ts`, `pipeline/ui/src/pages/Dashboard.tsx`, `pipeline/ui/src/pages/RawQueue.tsx`, `pipeline/ui/src/pages/LogViewer.tsx`
- Modify: `pipeline/api/main.py` (optional static file mount in later step)

- [ ] **Step 1: Scaffold Vite React app**

```bash
cd pipeline
npm create vite@latest ui -- --template react-ts
cd ui && npm install
```

- [ ] **Step 2: Create API client**

Create `pipeline/ui/src/api.ts`:

```typescript
const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8787";

export async function fetchStatus() {
  const res = await fetch(`${API_BASE}/api/status`);
  if (!res.ok) throw new Error("status fetch failed");
  return res.json();
}

export async function fetchPendingRaw() {
  const res = await fetch(`${API_BASE}/api/raw/pending`);
  if (!res.ok) throw new Error("raw fetch failed");
  return res.json();
}

export async function postSync(briefOnly = false) {
  const res = await fetch(`${API_BASE}/api/sync`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ brief_only: briefOnly }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
```

- [ ] **Step 3: Build Dashboard page**

Create `pipeline/ui/src/pages/Dashboard.tsx` showing:
- pending raw count
- lint error/warning counts
- brief status + export cycle
- last log entry
- Sync button calling `postSync()`

Wire routes in `App.tsx`: `/`, `/raw`, `/log` (LogViewer reads `/api/log` — add route in Task 6 follow-up or read file via new endpoint).

Add `pipeline/api/routes/log.py`:

```python
from fastapi import APIRouter
from wiki_core.paths import resolve_paths

router = APIRouter(tags=["log"])

@router.get("/log")
def get_log():
    paths = resolve_paths()
    if not paths.log.is_file():
        return {"content": ""}
    return {"content": paths.log.read_text(encoding="utf-8")}
```

Register router in `api/main.py`.

- [ ] **Step 4: Manual verification**

Terminal 1:
```bash
./scripts/wiki-pipeline serve
```

Terminal 2:
```bash
cd pipeline/ui && npm run dev
```

Open `http://localhost:5173` — dashboard shows live pending count from wiki submodule; Sync button works when `project-brief.md` exists.

- [ ] **Step 5: Commit**

```bash
git add pipeline/ui/ pipeline/api/
git commit -m "$(cat <<'EOF'
feat: add Phase 1 React dashboard for pipeline status and sync

EOF
)"
```

---

### Task 7: LLM Router and Ingest Workflow Backend

**Files:**
- Create: `pipeline/llm/router.py`, `pipeline/llm/prompts/ingest.py`, `pipeline/llm/workflows/ingest.py`, `pipeline/api/jobs.py`, `pipeline/api/routes/jobs.py`
- Create: `pipeline/tests/test_ingest_workflow.py` (mock httpx)

- [ ] **Step 1: Implement Ollama router**

Create `pipeline/llm/router.py`:

```python
from __future__ import annotations
import httpx
from wiki_core.paths import load_config

async def stream_ollama(prompt: str, system: str, task: str = "ingest") -> str:
    cfg = load_config()
    base = cfg["llm"]["ollama_base_url"].rstrip("/")
    model = cfg["llm"]["models"]["ollama"]
    override = cfg["llm"].get("overrides", {}).get(task)
    if override and override != "ollama":
        raise NotImplementedError(f"Provider {override} not implemented yet")
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
    }
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(f"{base}/api/chat", json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["message"]["content"]
```

- [ ] **Step 2: Port ingest prompts**

Create `pipeline/llm/prompts/ingest.py` — copy workflow rules from `wiki/AGENTS.md` Ingest section and `wiki/.cursor/skills/wiki-ingest/SKILL.md` into two constants:

```python
INGEST_ANALYSIS_SYSTEM = """You are a wiki maintainer. Perform structural analysis only.
Do NOT write files. Summarize key claims, unique insights, contradictions, and affected concept slugs.
Follow AGENTS.md ingest rules exactly."""

INGEST_WRITE_SYSTEM = """You are a wiki maintainer. Generate markdown content for:
1) wiki/sources/<slug>.md
2) updates to wiki/concepts/ pages
3) delta for wiki/synthesis/evolving-thesis.md
4) index.md additions
5) log.md append entry
Return JSON with keys: source_md, concept_updates (dict slug->md), thesis_delta, index_lines, log_entry."""
```

- [ ] **Step 3: Implement job store and ingest workflow**

Create `pipeline/api/jobs.py` with:
- `JobState` enum: `created`, `analysis_done`, `draft_done`, `awaiting_final_confirm`, `completed`, `failed`
- `IngestJob` dataclass holding `raw_path`, `analysis`, `draft`, `state`
- `JobStore` singleton — max one active ingest

Create `pipeline/llm/workflows/ingest.py`:
- `start_analysis(job)` → calls Ollama with raw content
- `generate_draft(job)` → calls Ollama with analysis
- `apply_approved_writes(job, approved_payload)` → writes files via `wiki_core.fs`
- `mark_ingested(job)` → updates raw frontmatter status

Create `pipeline/api/routes/jobs.py` endpoints:
- `POST /api/jobs/ingest` `{ "raw_path": "raw/llm/..." }`
- `POST /api/jobs/ingest/{id}/approve-analysis`
- `POST /api/jobs/ingest/{id}/approve-draft` `{ "edits": {...} }`
- `POST /api/jobs/ingest/{id}/confirm`
- `GET /api/jobs/ingest/{id}`

- [ ] **Step 4: Write test with mocked Ollama**

Use `pytest-httpx` or monkeypatch `stream_ollama` to return fixed JSON; verify state transitions without real Ollama.

- [ ] **Step 5: Commit**

```bash
git add pipeline/llm/ pipeline/api/jobs.py pipeline/api/routes/jobs.py pipeline/tests/
git commit -m "$(cat <<'EOF'
feat: add Ollama router and staged ingest job workflow

EOF
)"
```

---

### Task 8: Ingest Wizard UI

**Files:**
- Create: `pipeline/ui/src/pages/IngestWizard.tsx`
- Modify: `pipeline/ui/src/App.tsx`, `pipeline/ui/src/api.ts`

- [ ] **Step 1: Add job API helpers in api.ts**

Functions: `startIngest(rawPath)`, `approveAnalysis(id)`, `approveDraft(id, edits)`, `confirmIngest(id)`, `getJob(id)`

- [ ] **Step 2: Build 4-step wizard UI**

Steps:
1. Select pending raw file (from RawQueue)
2. Show streaming/fetched analysis → Approve button
3. Show proposed markdown diffs (source, concepts, thesis) → Approve / edit
4. Final confirm → marks ingested

- [ ] **Step 3: Manual E2E with Ollama running**

```bash
ollama pull qwen2.5:7b-instruct   # default in pipeline/config.yaml
./scripts/wiki-pipeline serve
cd pipeline/ui && npm run dev
```

Ingest one pending raw file end-to-end; verify new source page and log entry on disk.

- [ ] **Step 4: Commit**

```bash
git add pipeline/ui/
git commit -m "$(cat <<'EOF'
feat: add ingest wizard UI with approval gates

EOF
)"
```

---

### Task 9: Export Workflow Backend + UI

**Files:**
- Create: `pipeline/llm/prompts/export.py`, `pipeline/llm/workflows/export.py`
- Modify: `pipeline/api/routes/jobs.py`, `pipeline/ui/src/pages/ExportWizard.tsx`

- [ ] **Step 1: Implement export workflow**

Stages:
1. Run lint — return blockers unless `force=true`
2. Ollama generates `project-brief.md` body from thesis + concepts
3. Pause — UI shows diff vs existing brief
4. On approve — write brief as `draft`, then promote to `current`, supersede prior, append log

- [ ] **Step 2: Add API routes**

- `POST /api/jobs/export`
- `POST /api/jobs/export/{id}/approve`
- `GET /api/jobs/export/{id}`

- [ ] **Step 3: Build ExportWizard page**

Lint summary at top; draft brief preview; approve button; post-approve sync offer.

- [ ] **Step 4: Manual verification**

Export cycle increments; sync updates `docs/PROJECT_BRIEF.md`.

- [ ] **Step 5: Commit**

```bash
git add pipeline/
git commit -m "$(cat <<'EOF'
feat: add export brief workflow with lint gate and approval UI

EOF
)"
```

---

### Task 10: Phase 2 Rich UI — Diffs, Graph, Lint Dashboard

**Files:**
- Create: `pipeline/wiki_core/graph.py`, `pipeline/api/routes/graph.py`
- Create: `pipeline/ui/src/pages/LintDashboard.tsx`, `pipeline/ui/src/pages/GraphView.tsx`, `pipeline/ui/src/components/DiffView.tsx`
- Modify: `pipeline/ui/src/pages/RawQueue.tsx` (drag-drop upload endpoint)

- [ ] **Step 1: Add wikilink graph builder**

Create `pipeline/wiki_core/graph.py`:

```python
def build_graph(paths: WikiPaths) -> dict:
    """Return { nodes: [{id, label}], edges: [{source, target}] }"""
```

Parse all wiki pages; nodes = slugs; edges = wikilink references.

- [ ] **Step 2: Add GET /api/graph and POST /api/raw/upload**

Upload endpoint writes new raw file with frontmatter form fields; validates required keys per AGENTS.md.

- [ ] **Step 3: Build DiffView component**

Use `diff` library or simple line diff for raw vs source and brief vs previous cycle.

- [ ] **Step 4: Build LintDashboard**

Fetch `/api/lint`; group by severity; dismiss/ack actions stored in local UI state only (lint fixes still manual or future task).

- [ ] **Step 5: Build GraphView**

Render graph with `react-force-graph` or Cytoscape; link nodes to wiki page preview modal.

- [ ] **Step 6: Commit**

```bash
git add pipeline/
git commit -m "$(cat <<'EOF'
feat: add diff views, wikilink graph, lint dashboard, and raw upload

EOF
)"
```

---

### Task 11: MCP Server

**Files:**
- Create: `pipeline/mcp/__init__.py`, `pipeline/mcp/server.py`
- Modify: `pipeline/cli/main.py` (add `mcp` command)

- [ ] **Step 1: Implement MCP tools over wiki_core**

Create `pipeline/mcp/server.py` registering:
- `wiki_list_pending`
- `wiki_read_page`
- `wiki_search`
- `wiki_get_status`
- `wiki_run_lint`
- `wiki_sync_brief`

Each tool calls existing `wiki_core` functions — no duplicated logic.

- [ ] **Step 2: Add CLI command**

```python
@app.command()
def mcp():
    import asyncio
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.server import server as mcp_server_module
    # run server from pipeline/mcp/server.py
```

- [ ] **Step 3: Manual verification with Claude Desktop or Cursor MCP config**

Add to MCP config:

```json
{
  "mcpServers": {
    "wiki-pipeline": {
      "command": "/path/to/experimental-app/scripts/wiki-pipeline",
      "args": ["mcp"]
    }
  }
}
```

Call `wiki_list_pending` and `wiki_get_status` from agent — verify JSON matches CLI output.

- [ ] **Step 4: Commit**

```bash
git add pipeline/mcp/ pipeline/cli/main.py
git commit -m "$(cat <<'EOF'
feat: add MCP sidecar exposing wiki_core read and sync tools

EOF
)"
```

---

### Task 12: Watch Command and Operator Docs

**Files:**
- Create: `pipeline/cli/watch.py`, `docs/WIKI_PIPELINE_OPERATOR.md`
- Modify: `pipeline/cli/main.py`, `README.md`

- [ ] **Step 1: Implement watch command**

Create `pipeline/cli/watch.py`:

```python
import time
import subprocess
from wiki_core.paths import resolve_paths
from wiki_core.status import get_pipeline_status

def watch_loop(interval: int = 60):
    seen = 0
    while True:
        count = get_pipeline_status(resolve_paths()).pending_raw_count
        if count > 0 and count != seen:
            subprocess.run([
                "osascript", "-e",
                f'display notification "{count} pending raw file(s)" with title "Wiki Pipeline"'
            ], check=False)
            seen = count
        time.sleep(interval)
```

Wire `watch` command in CLI (macOS notification via osascript; document Linux alternative in docs).

- [ ] **Step 2: Write operator docs**

Create `docs/WIKI_PIPELINE_OPERATOR.md` covering:
- Prerequisites: Python 3.11, Ollama, Node 20+
- Setup: `cd pipeline && python -m venv venv && pip install -e ".[dev]" && cd ui && npm install`
- Start: `./scripts/wiki-pipeline serve` + `cd pipeline/ui && npm run dev`
- CLI reference
- MCP registration
- Cron example: `0 9 * * * /path/to/scripts/wiki-pipeline lint --json >> /tmp/wiki-lint.log`

- [ ] **Step 3: Update root README.md**

Add section linking to operator docs and spec.

- [ ] **Step 4: Commit**

```bash
git add pipeline/cli/ docs/ README.md
git commit -m "$(cat <<'EOF'
docs: add wiki pipeline operator guide and watch notification command

EOF
)"
```

---

## Spec Coverage Self-Review

| Spec requirement | Task |
|------------------|------|
| wiki_core shared library | Tasks 2–4 |
| CLI status/lint/sync/serve/mcp/watch | Tasks 1, 4, 5, 11, 12 |
| FastAPI + React UI Phase 1 | Tasks 5–6 |
| Ollama ingest with approval gates | Tasks 7–8 |
| Export workflow + sync panel | Task 9 |
| Phase 2 rich UI | Task 10 |
| MCP read-heavy sidecar | Task 11 |
| Human gates preserved | Tasks 7–9 (explicit approve endpoints) |
| sync-wiki-docs.sh wrapped | Task 4 |
| Localhost only, no auth | Tasks 5–6 (CORS localhost only) |
| Cloud LLM override deferred | router raises NotImplementedError for non-ollama until needed |

## Execution Notes

- Run `./scripts/wiki-pipeline lint` against the live wiki submodule after Task 4 to validate real-world lint output.
- Ollama model quality varies — if export brief is weak on local model, add Anthropic provider in `llm/router.py` as follow-up (spec open question).
- Keep Cursor skills unchanged; optionally add a note in `wiki/README.md` pointing to the operator app.
