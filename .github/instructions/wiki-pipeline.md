# Wiki Pipeline — Copilot Instructions

This project contains an LLM-Wiki ETL pipeline in the `pipeline/` directory. It ingests research from raw markdown files into a structured wiki, lints, exports a project brief, builds a knowledge graph, and syncs to `docs/`.

## Where everything lives

```
experimental-app/
├── pipeline/                  # pipeline code
│   ├── pipeline/
│   │   ├── wiki_core/        # shared library (paths, fs, lint, status, sync, graph)
│   │   ├── llm/workflows/    # ingest/export workflow functions
│   │   ├── workflows/        # auto.py — pre-approved orchestration
│   │   ├── api/              # FastAPI server + job store
│   │   ├── mcp/              # MCP stdio server
│   │   └── cli/main.py       # Typer CLI entrypoint
│   ├── config.yaml           # wiki paths, Ollama model, server port
│   └── venv/                 # Python virtual environment (Python 3.11+)
├── wiki/                     # wiki content (git submodule)
│   ├── raw/llm/              # LLM chat exports
│   ├── raw/web/              # Web clips
│   └── wiki/                 # sources/, concepts/, synthesis/, index.md, log.md
└── docs/
    └── WIKI_PIPELINE_OPERATOR.md   # full reference
```

## CLI commands

All commands run from `pipeline/` with the venv active (`source venv/bin/activate`):

| Command | Purpose |
|---------|---------|
| `wiki-pipeline status` | Pipeline health summary |
| `wiki-pipeline lint` | Deterministic lint checks |
| `wiki-pipeline sync` | Copy synthesis → parent `docs/` |
| `wiki-pipeline serve` | Start FastAPI backend on :8787 |
| `wiki-pipeline mcp` | Start MCP stdio server |
| `wiki-pipeline watch` | Poll for pending files, notify |
| `wiki-pipeline auto --file <path>` | Full pipeline (one file) |
| `wiki-pipeline auto --all` | Full pipeline (all pending) |
| `wiki-pipeline auto --watch` | Watch + auto-process |

Without venv activation: `pipeline/venv/bin/wiki-pipeline <command>`.

## Auto pipeline (pre-approved)

The `auto` command runs: **ingest → lint → export → lint → graph → sync** with no human gates.

- **Frontmatter auto-injection** — files without YAML frontmatter get it added automatically. `source`/`type` derived from directory (`raw/llm/` vs `raw/web/`), `topic` from first `# H1`, `date` from today.
- **Error resilience** — if an LLM call fails, that file is skipped and the batch continues.
- **Export deferred** — runs only after all pending files are processed.

## MCP tools

The MCP server (`wiki-pipeline mcp`) exposes read-heavy tools for AI agents:

- `wiki_list_pending` — list raw files with `status: pending`
- `wiki_read_page` — read a wiki page by slug
- `wiki_search` — search wiki content
- `wiki_get_status` — pipeline health summary
- `wiki_run_lint` — structured lint report
- `wiki_sync_brief` — sync brief to parent docs

Registered in `.cursor/mcp.json` for Cursor and `.vscode/mcp.json` for VSCode (natively supported since 1.97). For Claude Desktop, add to `claude_desktop_config.json`.

## Key conventions

- Raw files need `status: pending` frontmatter for the UI, but the auto pipeline injects it if missing.
- The `JobStore` is in-memory (dict). The auto pipeline creates ephemeral jobs outside the store.
- Ollama must be running (`ollama serve`) for any LLM operation.
