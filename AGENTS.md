# Distill-Wiki-Pipeline — AGENTS.md

## What this repo is

Multi-LLM research-to-wiki pipeline. Collects LLM chat exports and web clips, ingests them into a structured wiki, lints for broken links/orphans, exports project briefs, builds wikilink knowledge graphs, and syncs synthesis to `docs/`.

## Repo topology

```
pipeline/              # Python package — CLI, FastAPI, MCP, React UI
  pipeline/
    wiki_core/         # SHARED LIBRARY — paths, fs, lint, status, sync, graph
    cli/main.py        # Typer CLI entrypoint
    api/               # FastAPI server + job store + routes
    mcp/server.py      # MCP stdio server
    workflows/auto.py  # Pre-approved auto pipeline orchestration
    llm/workflows/     # Ingest/export workflow functions
  ui/                  # Vite + React operator dashboard
  tests/               # pytest — uses tests/fixtures/minimal-wiki/
  config.yaml          # wiki_root, Ollama model, server port
wiki/                  # GIT SUBMODULE (https://github.com/williamjxj/project-wiki.git)
  raw/llm/             # LLM chat exports (status: pending = unprocessed)
  raw/web/             # Web article clips
  wiki/                # sources/, concepts/, synthesis/, index.md, log.md
  AGENTS.md            # Wiki submodule's own agent schema — NOT repo root
docs/                  # Synced exports (PROJECT_BRIEF.md, RESEARCH_THESIS.md)
scripts/
  wiki-pipeline        # Shell shortcut: cd pipeline && python -m pipeline.cli.main "$@"
  sync-wiki-docs.sh    # Copy wiki synthesis → docs/
opencode.jsonc         # MCP server config for wiki-pipeline
```

## Architecture invariant

**`wiki_core/` is the single source of truth.** CLI, API, MCP, and LLM workflows all call into it. Never add business logic in API routes or MCP handlers that bypasses wiki_core.

## CLI commands

All from `pipeline/` with venv active. Alternatives: `pip/venv/bin/wiki-pipeline`, `python -m pipeline.cli.main`, or `./scripts/wiki-pipeline`.

| Command | Purpose |
|---------|---------|
| `wiki-pipeline status` | Pipeline health summary |
| `wiki-pipeline lint` | Lint checks (missing_page, orphan_page, pending_raw, index_out_of_sync) |
| `wiki-pipeline lint --json` | Machine-readable lint output |
| `wiki-pipeline sync` | Copy synthesis → parent `docs/` |
| `wiki-pipeline sync --brief-only` | Only project brief (skip thesis) |
| `wiki-pipeline serve` | Start FastAPI backend on :8787 |
| `wiki-pipeline mcp` | MCP stdio sidecar |
| `wiki-pipeline watch [--interval N]` | Poll for pending files, notify |
| `wiki-pipeline auto --file <path>` | Ingest→lint→export→lint→graph→sync (no human gates) |
| `wiki-pipeline auto --all` | Process all pending |
| `wiki-pipeline auto --watch` | Watch + auto-process |

## Testing

Run from `pipeline/` with venv active:

```bash
pytest                          # all tests
pytest tests/test_lint.py       # single file
pytest -x                       # fail fast
```

Test fixture wiki at `pipeline/tests/fixtures/minimal-wiki/`. Tests use `pytest-asyncio`. Config in `pyproject.toml`: `testpaths = ["tests"]`, `pythonpath = ["."]`.

## Development setup

```bash
# Clone with submodule
git clone --recurse-submodules <repo-url>
git submodule update --init --recursive  # if already cloned

# Python
cd pipeline
python3 -m venv venv && source venv/bin/activate
pip install -e ".[dev]"

# UI
cd ui && npm install && cd ../..

# Ollama (required for ingest/export)
ollama serve
ollama pull qwen2.5:7b-instruct  # default model in config.yaml
```

## Running locally (two terminals)

```
Terminal 1: source pipeline/venv/bin/activate && wiki-pipeline serve   # :8787
Terminal 2: cd pipeline/ui && npm run dev                                # :5173
```

## Important gotchas

- **`wiki/` is a git submodule**, not a regular directory. Never add `wiki/` to `.gitignore` — that breaks submodule tracking. It's tracked via `.gitmodules` plus a pinned commit SHA.
- **MCP is read-only.** It can list pending, read pages, search, check status, run lint, sync brief. It cannot run ingest or export workflows — those require multi-stage human approval in the web UI.
- **Frontmatter auto-injection**: The auto pipeline handles files without YAML frontmatter. `source`/`type` derived from directory (`raw/llm/` vs `raw/web/`), `topic` from first `# H1`, `date` from today.
- **Lint severities**: `missing_page` = ERROR (broken wikilink), `orphan_page` = WARNING (no inbound links), `pending_raw` = INFO, `index_out_of_sync` = ERROR.
- **Export is deferred** in auto pipeline — runs only after all pending files are processed.
- **LLM call failures** are non-fatal in auto pipeline: that file is skipped and the batch continues.

## Existing instruction files

| File | Scope | Always applied? |
|------|-------|-----------------|
| `wiki/AGENTS.md` | Wiki submodule conventions (naming, structures, lifecycle) | No — only when editing wiki content |
| `.github/instructions/wiki-pipeline.md` | Copilot instructions (registered in `.vscode/settings.json`) | In VSCode/Copilot |
| `.cursor/rules/karpathy-guidelines.mdc` | Behavioral guidelines (think-before-code, simplicity, surgical changes) | Yes — `alwaysApply: true` |
| `opencode.jsonc` | OpenCode MCP server config | Platform-specific |
| `.vscode/mcp.json` | VSCode MCP config | Platform-specific |
| `.cursor/mcp.json` | Cursor MCP config | Platform-specific |
