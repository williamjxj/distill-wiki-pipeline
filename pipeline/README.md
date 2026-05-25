# Wiki Pipeline Operator

Local operator for the LLM-Wiki ETL loop: **collect → ingest → lint → export → sync**. Runs independently of Cursor via CLI, web UI, and MCP.

Full setup and CLI reference: [`docs/WIKI_PIPELINE_OPERATOR.md`](../docs/WIKI_PIPELINE_OPERATOR.md)

## Architecture

```
pipeline/
├── config.yaml              # wiki paths, Ollama model, server port
├── pipeline/
│   ├── wiki_core/           # shared library — paths, fs, lint, status, sync, graph
│   ├── llm/                 # Ollama router + ingest/export workflows
│   ├── api/                 # FastAPI HTTP + job orchestration
│   ├── mcp/                 # MCP stdio sidecar (same wiki_core)
│   └── cli/                 # Typer CLI
├── ui/                      # Vite + React operator dashboard
└── tests/
```

**Principle:** `wiki_core` is the single source of truth. CLI, API, MCP, and LLM workflows all call into it.

## Workflow

```mermaid
flowchart LR
    A[raw/ pending] --> B[Ingest wizard]
    B --> C[wiki/sources + concepts + thesis]
    C --> D[Lint]
    D --> E[Export brief]
    E --> F[Sync to docs/]
    F --> G[Build in parent repo]
    G --> A
```

### 1. Collect

Add LLM chat exports to `wiki/raw/llm/` (or web clips to `wiki/raw/web/`) with AGENTS.md frontmatter and `status: pending`.

Upload via the UI **Raw Queue** form or paste files manually.

### 2. Ingest (human gates)

One raw file per job, two LLM passes with approval between stages:

| Stage | What happens |
|-------|----------------|
| Analyze | Ollama structural analysis (no writes) |
| Review | Operator approves analysis in UI |
| Draft | Ollama generates source page, concept updates, thesis delta |
| Review | Operator approves draft (optional edits) |
| Confirm | Writes wiki files; sets raw `status: ingested` |

**CLI:** `./scripts/wiki-pipeline serve` + UI at `/ingest`

**API:** `POST /api/jobs/ingest` → approve-analysis → approve-draft → confirm

### 3. Lint

Deterministic checks (no LLM): pending raw, missing wikilinks, orphan pages, index sync.

```bash
./scripts/wiki-pipeline lint
./scripts/wiki-pipeline lint --json
```

UI: **Lint** page (`/lint`)

### 4. Export brief

Lint gate → Ollama draft of `wiki/synthesis/project-brief.md` → operator approval → promote to `status: current`.

UI: **Export** page (`/export`)

### 5. Sync to parent

Copy synthesis into parent `docs/`:

```bash
./scripts/wiki-pipeline sync
./scripts/wiki-pipeline sync --brief-only
```

Warns if brief is still `status: draft`.

### 6. MCP (optional)

Expose read-heavy tools to Cursor / Claude Desktop without opening the UI:

```bash
./scripts/wiki-pipeline mcp
```

Tools: `wiki_list_pending`, `wiki_read_page`, `wiki_search`, `wiki_get_status`, `wiki_run_lint`, `wiki_sync_brief`

## Quick start

```bash
# Setup (once)
cd pipeline
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cd ui && npm install && cd ../..

# Ensure Ollama is running with the configured model
ollama pull deepseek-v4-flash:cloud

# Run
./scripts/wiki-pipeline serve          # API :8787
cd pipeline/ui && npm run dev          # UI :5173
```

## Configuration

Edit `config.yaml`:

| Key | Default | Purpose |
|-----|---------|---------|
| `wiki_root` | `../wiki` | Wiki submodule path |
| `llm.models.ollama` | `deepseek-v4-flash:cloud` | Model for ingest/export (requires Ollama cloud access) |
| `llm.ollama_base_url` | `http://localhost:11434` | Ollama API |
| `server.port` | `8787` | FastAPI bind port |

## CLI commands

| Command | Description |
|---------|-------------|
| `status` | Pipeline health summary |
| `lint [--json]` | Deterministic lint report |
| `sync [--brief-only]` | Sync wiki synthesis → `docs/` |
| `serve` | Start FastAPI server |
| `mcp` | Start MCP stdio server |
| `watch [--interval N]` | Notify when pending raw files exist |

Entry point from repo root: `./scripts/wiki-pipeline`
