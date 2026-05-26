---
name: wiki-pipeline
description: LLM-Wiki ETL pipeline — ingest, lint, export, graph, sync (CLI + auto-pipeline + MCP tools)
trigger: /wiki-pipeline
---

# Wiki Pipeline

This project contains an LLM-Wiki ETL pipeline in `pipeline/`. It ingests research from raw markdown files into a structured wiki, lints for broken links and orphans, exports a project brief, builds a knowledge graph, and syncs to `docs/`.

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
│   └── venv/                 # Python virtual environment
├── wiki/                     # wiki content (git submodule)
│   ├── raw/llm/              # LLM chat exports
│   ├── raw/web/              # Web clips
│   └── wiki/                 # sources/, concepts/, synthesis/, index.md, log.md
├── docs/
│   └── WIKI_PIPELINE_OPERATOR.md   # full CLI/cron/MCP reference
├── opencode.jsonc            # MCP server config for OpenCode
├── .opencode/skills/wiki-pipeline/SKILL.md  # this skill
├── .vscode/mcp.json          # MCP server config for VSCode
├── .cursor/mcp.json          # MCP server config for Cursor
├── .vscode/settings.json     # Copilot instructions registration
└── .github/instructions/wiki-pipeline.md   # Copilot instructions file
```

## CLI commands

All commands run from `pipeline/` with venv active (`source pipeline/venv/bin/activate`):

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

Without venv: `pipeline/venv/bin/wiki-pipeline <command>`.

## Auto pipeline (pre-approved)

The `auto` command runs: **ingest → lint → export → lint → graph → sync** with no human gates.

- **Frontmatter auto-injection** — files without YAML frontmatter get it added automatically. `source`/`type` derived from directory (`raw/llm/` vs `raw/web/`), `topic` from first `# H1`, `date` from today.
- **Error resilience** — if an LLM call fails, that file is skipped and the batch continues.
- **Export deferred** — runs only after all pending files are processed.

## MCP tools

The MCP server (`wiki-pipeline mcp`) exposes these tools for AI agents:

| Tool | Description |
|------|-------------|
| `wiki_list_pending` | List raw files with `status: pending` |
| `wiki_read_page` | Read a wiki page by slug or relative path |
| `wiki_search` | Search wiki page content for a query string |
| `wiki_get_status` | Pipeline health summary |
| `wiki_run_lint` | Run deterministic wiki lint |
| `wiki_sync_brief` | Run brief sync and return warnings |

These tools are registered as MCP tools in:
- **OpenCode**: via `opencode.jsonc` → `mcp.wiki-pipeline`
- **VSCode**: via `.vscode/mcp.json` → `servers.wiki-pipeline`
- **Cursor**: via `.cursor/mcp.json` → `mcpServers.wiki-pipeline`

## Lint findings

The lint command reports:
- `missing_page` — wikilink `[[page]]` with no matching `.md` file
- `orphan_page` — page with no inbound wikilinks
- `index_out_of_sync` — page on disk but missing from `index.md`

## Config

Key settings in `pipeline/config.yaml`:
- `wiki_root: ../wiki` — paths relative to wiki submodule
- `model: qwen2.5:7b-instruct` — default Ollama model
- `server.port: 8787` — FastAPI backend port

## Ollama

The pipeline requires Ollama running locally. The default model is `qwen2.5:7b-instruct`. Start with `ollama serve`.
