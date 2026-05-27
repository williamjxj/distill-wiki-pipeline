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
│   ├── workflows/           # auto pipeline orchestration (pre-approved)
│   ├── api/                 # FastAPI HTTP + job orchestration
│   ├── mcp/                 # MCP stdio sidecar (same wiki_core)
│   └── cli/                 # Typer CLI
├── ui/                      # Vite + React operator dashboard
└── tests/
```

**Principle:** `wiki_core` is the single source of truth. CLI, API, MCP, and LLM workflows all call into it.

## Workflows

### Manual (step-by-step)

```mermaid
flowchart TD
    subgraph Collect
        A1[Drop .md into raw/llm/ or raw/web/] --> A2[File has YAML frontmatter?]
        A2 -- yes --> A3[Validate status: pending]
        A2 -- no --> A4[Inject frontmatter] --> A3
    end

    subgraph Ingest[Ingest — 2 LLM passes, 2 human gates]
        direction LR
        B1[Analyze<br>LLM structural analysis<br>no writes] --> B2{Approve?}
        B2 -- operator approves --> B3[Draft<br>LLM generates source + concepts + thesis]
        B3 --> B4{Approve?}
        B4 -- operator approves<br>optional edits --> B5[Write wiki files<br>Set raw status: ingested]
        B2 -- reject --> B1
        B4 -- reject --> B3
    end

    subgraph Lint
        C[Deterministic checks<br>missing wikilinks, orphans, index sync]
    end

    subgraph Export[Export — 1 LLM pass, 1 human gate]
        direction LR
        D1[LLM drafts project-brief.md] --> D2{Approve?}
        D2 -- operator approves --> D3[Promote status to current]
        D2 -- reject --> D1
    end

    subgraph Sync
        E[Copy synthesis → docs/]
    end

    A3 --> B1
    B5 --> C --> D1
    D3 --> E
```

### Auto pipeline (pre-approved)

```mermaid
flowchart TD
    subgraph AutoCollect[Collect]
        F1[Drop .md into raw/llm/ or raw/web/] --> F2[Auto-inject frontmatter<br>source/type from directory<br>topic from H1<br>date from today]
    end

    subgraph AutoIngest[Ingest — 2 LLM passes, no human gates]
        direction LR
        G1[Analyze<br>LLM structural analysis] --> G2[Draft<br>LLM generates content]
        G2 --> G3[Auto-approve draft] --> G4[Write wiki files]
    end

    subgraph AutoLint1[Lint]
        H[Deterministic checks]
    end

    subgraph AutoExport[Export — deferred until all files ingested]
        direction LR
        I1[LLM drafts project-brief.md] --> I2[Auto-approve<br>Promote to current]
    end

    subgraph AutoLint2[Lint]
        J[Deterministic checks]
    end

    subgraph AutoGraph[Graph]
        K[Build wikilink knowledge graph<br>nodes + edges]
    end

    subgraph AutoSync[Sync]
        L[Copy synthesis → docs/]
    end

    F2 --> G1
    G4 --> H --> I1
    I2 --> J --> K --> L
```

### Comparison

| Step | Manual (step-by-step) | Auto pipeline |
|------|-----------------------|---------------|
| **Frontmatter** | Injected on upload (UI form) | Auto-injected from directory, H1, today's date |
| **Ingest: Analyze** | LLM pass — structural analysis | Same LLM pass |
| **Gate** | Human approves/edits analysis | Skipped — auto-approves |
| **Ingest: Draft** | LLM pass — generates content | Same LLM pass |
| **Gate** | Human approves/edits draft | Skipped — auto-approves |
| **Ingest: Write** | Writes source + concepts + thesis | Same write step |
| **Lint** | Post-ingest, deterministic | Post-ingest **and** post-export |
| **Export** | 1 LLM pass + human approval gate | 1 LLM pass + auto-approve (deferred until all files ingested) |
| **Knowledge graph** | Not built | Built after export |
| **Sync** | Manual `wiki-pipeline sync` | Automatically copies to `docs/` |
| **Failure handling** | Stops at each gate — operator decides | Marks file failed, continues batch |

### 1. Collect

Drop markdown files into `wiki/raw/llm/` or `wiki/raw/web/`. The auto pipeline will inject missing frontmatter (status, source, topic, date) automatically — no YAML required.

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

**CLI:** `wiki-pipeline serve` (from `pipeline/` with venv active) + UI at `/ingest`

**API:** `POST /api/jobs/ingest` → approve-analysis → approve-draft → confirm

**Auto (pre-approved):** `wiki-pipeline auto --file <path>` — see [auto pipeline](#auto-pipeline-pre-approved) below

### 3. Lint

Deterministic checks (no LLM): pending raw, missing wikilinks, orphan pages, index sync.

```bash
wiki-pipeline lint
wiki-pipeline lint --json
```

UI: **Lint** page (`/lint`)

### 4. Export brief

Lint gate → Ollama draft of `wiki/synthesis/project-brief.md` → operator approval → promote to `status: current`.

UI: **Export** page (`/export`)

### 5. Sync to parent

Copy synthesis into parent `docs/`:

```bash
wiki-pipeline sync
wiki-pipeline sync --brief-only
```

Warns if brief is still `status: draft`.

### 6. MCP (optional)

Expose read-heavy tools to Cursor / Claude Desktop without opening the UI:

```bash
wiki-pipeline mcp
```

Tools: `wiki_list_pending`, `wiki_read_page`, `wiki_search`, `wiki_get_status`, `wiki_run_lint`, `wiki_sync_brief`

MCP is **read-heavy** — ingest and export still require the web UI or the [auto pipeline](#7-auto-pipeline-pre-approved).

### 7. Auto pipeline (pre-approved)

Run the full pipeline without any human gates — drop a file and walk away:

```bash
# Process one file
wiki-pipeline auto --file wiki/raw/llm/chat-export.md

# Process all pending files
wiki-pipeline auto --all

# Watch for new files and process them as they appear
wiki-pipeline auto --watch
```

The auto pipeline chains: **ingest → lint → export → lint → graph → sync**.

**Key features:**

- **Zero frontmatter required** — files dumped into `raw/` without YAML frontmatter get it auto-injected. The pipeline derives `source`/`type` from the directory (`raw/llm/` vs `raw/web/`), `topic` from the first H1 heading, and `date` from today.
- **Error resilient** — if an LLM call fails (e.g. Ollama returns bad JSON), that file is marked failed and the batch continues to the next file. The pipeline doesn't crash on a single bad response.
- **Export deferred** — export runs only after all pending raw files are ingested, so the project brief captures the complete picture.

See [`docs/WIKI_PIPELINE_OPERATOR.md`](../docs/WIKI_PIPELINE_OPERATOR.md) for full details.

## Quick start

```bash
# Setup (once)
cd pipeline
python3 -m venv venv && source venv/bin/activate
pip install -e ".[dev]"
cd ui && npm install && cd ../..

# Ensure Ollama is running with the configured model
ollama pull qwen2.5:7b-instruct

# Run (venv active)
wiki-pipeline serve                    # API :8787
cd pipeline/ui && npm run dev          # UI :5173

# Or auto-pipeline (no UI needed)
wiki-pipeline auto --all               # process everything pending
```

## Configuration

Edit `config.yaml`:

| Key | Default | Purpose |
|-----|---------|---------|
| `wiki_root` | `../wiki` | Wiki submodule path |
| `llm.models.ollama` | `qwen2.5:7b-instruct` | Model for ingest/export (local Qwen 2.5 7B) |
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
| `auto --file PATH \| --all \| --watch` | Run full pipeline with pre-approval |

Entry point: `wiki-pipeline` (installed via `pip install -e .` in venv).
