# Wiki Pipeline Operator Design Spec

**Date:** 2026-05-25  
**Status:** Approved  
**Repo:** `experimental-app` (parent) + `project-wiki` submodule at `wiki/`  
**Builds on:** [2026-05-24-project-wiki-design.md](../../../wiki/docs/superpowers/specs/2026-05-24-project-wiki-design.md)

## Summary

A local web application that operates the LLM-Wiki ETL pipeline independently of Cursor. A shared Python library (`wiki_core`) implements file operations, lint rules, and sync; a FastAPI server exposes HTTP/SSE for a React UI; Ollama runs LLM workflow stages with explicit human approval gates; an optional MCP server exposes read-heavy tools to external agents. Cursor skills and `AGENTS.md` remain the workflow specification — not the runtime.

## Goals

1. Operate ingest → lint → export → sync without opening Cursor
2. Preserve human approval gates before marking raw sources ingested and before promoting briefs to `current`
3. Provide rich UI affordances: queue, diffs, graph, lint checklist, pipeline timeline
4. Use Ollama locally by default; allow cloud LLM override for export synthesis
5. Share pipeline logic across web UI, CLI scripts, and MCP via a single `wiki_core` library
6. Keep markdown + git as the source of truth — no database-backed wiki content

## Non-Goals

- Multi-user auth or team deployment
- Remote/hosted access (Tailscale, reverse proxy, Docker production)
- Replacing Obsidian as optional knowledge viewer
- Repurposing Open WebUI or AnythingLLM as the pipeline operator
- Fully unattended LLM ingest/export (human gates remain mandatory)
- Embedding/RAG search infrastructure
- Replacing or modifying raw body content (only frontmatter `status` may change in `raw/`)

## Context & Constraints

| Constraint | Detail |
|------------|--------|
| Deployment | Localhost only, single user, same machine as Ollama |
| Wiki location | Git submodule at `wiki/`; reads/writes on disk |
| Human gates | Confirm before `status: ingested`; approve before brief `status: current` |
| Existing automation | `scripts/sync-wiki-docs.sh` wrapped, not replaced |
| LLM default | Ollama at `http://localhost:11434` |
| Cursor skills | Remain valid workflow spec; optional for users who prefer Cursor |

## Architecture

```
experimental-app/
├── wiki/                          # git submodule (source of truth)
├── docs/                          # synced exports (unchanged)
├── scripts/
│   ├── sync-wiki-docs.sh          # existing; called by wiki_core.sync
│   └── wiki-pipeline              # CLI entrypoint → pipeline package
└── pipeline/
    ├── wiki_core/                 # shared library (single source of pipeline logic)
    │   ├── fs.py                  # markdown read/write, YAML frontmatter
    │   ├── lint.py                # deterministic lint rules
    │   ├── status.py              # pipeline health aggregation
    │   ├── sync.py                # wraps sync-wiki-docs.sh
    │   └── paths.py               # repo root, wiki paths resolution
    ├── llm/
    │   ├── router.py              # Ollama vs cloud model routing
    │   ├── prompts/               # ported from AGENTS.md + Cursor skills
    │   └── workflows/
    │       ├── ingest.py          # two-stage ingest with pause points
    │       └── export.py          # lint gate → brief draft → approval
    ├── api/                       # FastAPI HTTP server
    │   ├── main.py
    │   ├── routes/                # REST + SSE streaming endpoints
    │   └── jobs.py                # in-memory job queue (one ingest at a time)
    ├── mcp/                       # MCP stdio server wrapping wiki_core
    ├── ui/                        # Vite + React SPA
    └── config.yaml                # Ollama model, paths, LLM overrides
```

### Component Responsibilities

| Component | Responsibility | Consumers |
|-----------|----------------|-----------|
| `wiki_core` | All deterministic file/git/wiki rules | API, CLI, MCP, LLM workflows |
| `llm/` | Staged LLM jobs with approval checkpoints | API only |
| `api/` | HTTP/SSE for UI; job orchestration | React UI |
| `ui/` | Operator dashboard, wizards, diffs, graph | Browser at localhost |
| `mcp/` | Agent-facing tools over `wiki_core` | Claude Desktop, Cursor, scripts |
| `scripts/wiki-pipeline` | CLI for status, lint, sync, serve, mcp, watch | Terminal, cron |

**Principle:** Implement wiki logic once in `wiki_core`. HTTP API, CLI, and MCP are thin adapters.

## Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Core + API + MCP + LLM | Python 3.11+ | Ollama client, MCP SDK, file/YAML tooling |
| HTTP | FastAPI + SSE | Streaming LLM output to UI |
| UI | Vite + React + TypeScript | Rich diffs, graph, interactive approval flows |
| Job state | In-memory (+ optional SQLite for job history) | Local single-user; no external DB |
| LLM | Ollama default; Anthropic/OpenAI optional override | Local privacy; cloud for export if needed |

Rejected alternatives:
- **Next.js full-stack** — splits core logic across TS/Python; MCP still needs Python sidecar
- **Open WebUI / AnythingLLM** — chat-first UIs; wrong abstraction for stateful file pipeline
- **MCP as primary UI backend** — MCP is for LLM clients, not browser HTTP

## Data Flow

### Ingest (one raw file per job)

```
UI: select pending raw file
  → [deterministic] validate frontmatter, abort if status: ingested
  → [Ollama] Pass 1: structural analysis (stream via SSE)
  → [PAUSE] user reviews analysis in UI
  → [Ollama] Pass 2: generate source page, concept updates, thesis delta
  → [PAUSE] user reviews diffs; optional inline edits
  → [deterministic] write approved files; update index.md, log.md
  → [PAUSE] user confirms
  → [deterministic] set raw frontmatter status: ingested
```

### Export brief

```
UI: trigger export
  → [deterministic] run lint; block or require override if issues remain
  → [Ollama or cloud] generate project-brief.md draft from thesis + concepts
  → [PAUSE] user reviews brief diff vs previous cycle
  → [deterministic] write brief with status: draft; increment export_cycle
  → [PAUSE] user approves
  → [deterministic] mark prior brief superseded; set new brief status: current; append log
  → [deterministic] offer sync to parent docs/
```

### Sync to parent

```
UI or CLI: sync
  → [deterministic] run scripts/sync-wiki-docs.sh
  → warn prominently if project-brief.md is still status: draft
  → copy to docs/PROJECT_BRIEF.md and optionally docs/RESEARCH_THESIS.md
```

## LLM Configuration

`pipeline/config.yaml`:

```yaml
wiki_root: ../wiki          # relative to pipeline/ or absolute
parent_root: ..             # experimental-app root

llm:
  default: ollama
  ollama_base_url: http://localhost:11434
  models:
    ollama: qwen2.5:7b-instruct   # user-configurable
  overrides:
    export_brief: ollama    # set to anthropic/openai if local quality insufficient

server:
  host: 127.0.0.1
  port: 8787
```

Prompts in `pipeline/llm/prompts/` are ported from `wiki/AGENTS.md` and the four Cursor skills (`wiki-ingest`, `wiki-lint`, `wiki-export-brief`, `wiki-query`). Query workflow is UI-driven in Phase 2+.

## Web UI — Phased Features

### Phase 1: Operator MVP

- **Dashboard:** pending raw count, last ingest date, export cycle, lint warning count
- **Raw queue:** list files in `raw/` with `status: pending`; preview content
- **Ingest wizard:** two-pass flow with approval gates (see Data Flow)
- **Sync panel:** one-click sync; draft-status warning
- **Log viewer:** rendered timeline from `wiki/log.md`

### Phase 2: Rich Features

- Side-by-side diff: raw vs generated source page; thesis before/after
- Wikilink graph: parse `[[links]]` across wiki pages (optionally ingest Obsidian `graph.json` layout hints)
- Lint dashboard: actionable checklist; approve or dismiss per finding
- Export wizard: lint gate → draft → diff → approve → current
- Drag-drop upload to `raw/llm/` or `raw/web/` with frontmatter form helper

### Phase 3: Automation Hooks

- `wiki-pipeline watch`: desktop notification when pending raw files exist
- Cron-friendly docs for scheduled lint-check
- Optional git commit helper (stage submodule + parent docs changes)
- Cloud LLM toggle in UI for export step only

## MCP Server

MCP is a **read-heavy sidecar** over `wiki_core`. It does not replace the HTTP API. LLM ingest/export workflows require the approval UI and are not exposed as MCP tools.

### Tools

| Tool | Type | Description |
|------|------|-------------|
| `wiki_list_pending` | read | List raw files with `status: pending` |
| `wiki_read_page` | read | Read wiki page by slug or path |
| `wiki_search` | read | Search wiki content and wikilinks |
| `wiki_get_status` | read | Pipeline health: pending count, export cycle, last log entry |
| `wiki_run_lint` | read | Run deterministic lint; return structured report |
| `wiki_sync_brief` | write | Execute sync script; return warnings if brief is draft |

Run: `python -m pipeline.mcp` (stdio). Register in Claude Desktop or Cursor MCP config when external agent access is needed.

## CLI

```bash
./scripts/wiki-pipeline status           # pipeline summary
./scripts/wiki-pipeline lint             # deterministic lint report (JSON or text)
./scripts/wiki-pipeline sync [--brief-only]
./scripts/wiki-pipeline serve            # FastAPI + UI on localhost:8787
./scripts/wiki-pipeline mcp              # MCP stdio server
./scripts/wiki-pipeline watch            # notify on new pending raw files
```

LLM workflows are invoked via the web UI (or future `--interactive` CLI with pauses). No fully unattended ingest/export.

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Raw file already `ingested` | Block job; show error in UI |
| Ollama unreachable | Fail LLM stage with retry button; deterministic ops unaffected |
| Lint failures at export | Block by default; allow override with explicit user acknowledgment |
| Brief `status: draft` at sync | Sync proceeds with prominent warning (matches existing script behavior) |
| Concurrent ingest attempts | Job queue allows one active ingest job at a time |
| Missing synthesis files at sync | Fail with message pointing to export workflow |
| Invalid raw frontmatter | Block ingest; show validation errors |

## Testing Strategy

| Layer | Approach |
|-------|----------|
| `wiki_core` | Unit tests with fixture markdown tree (no LLM) |
| `lint.py` | Golden-file tests against sample wiki states |
| `api/` | Integration tests with TestClient; mock Ollama |
| `llm/workflows` | Snapshot tests for prompt assembly; manual QA for output quality |
| UI | Component tests for diff/queue views; manual E2E for ingest wizard |

## Build Order

| Step | Deliverable | Verification |
|------|-------------|--------------|
| 1 | `wiki_core` + CLI (`status`, `lint`, `sync`) | CLI matches manual checks against current wiki |
| 2 | FastAPI skeleton + Phase 1 dashboard UI | `serve` loads; dashboard shows pending count |
| 3 | Ingest workflow (Ollama + approval gates) | End-to-end ingest of one raw file via UI |
| 4 | Export workflow + sync panel | Export cycle completes; sync updates `docs/` |
| 5 | Phase 2 rich UI (diffs, graph, lint checklist) | Visual review of ingest/export diffs |
| 6 | MCP server | Tools callable from Claude Desktop |
| 7 | `watch` + cron documentation | Notification fires on new pending raw file |

## Relationship to Existing Artifacts

| Artifact | Relationship |
|----------|--------------|
| `wiki/AGENTS.md` | Schema authority; prompts ported to `pipeline/llm/prompts/` |
| Cursor skills in `wiki/.cursor/skills/` | Workflow spec; optional parallel path for Cursor users |
| `scripts/sync-wiki-docs.sh` | Called by `wiki_core.sync`; behavior unchanged |
| Obsidian | Remains optional viewer; Web Clipper still feeds `raw/web/` |
| `docs/PROJECT_BRIEF.md` | Still the dev handoff artifact; synced by operator |

## Open Questions (Deferred)

- Exact Ollama model selection per machine — user configures in `config.yaml`
- Whether export brief requires cloud LLM — evaluate after Phase 3 ingest quality on local model
- SQLite job history — add only if in-memory queue proves insufficient across browser refreshes
