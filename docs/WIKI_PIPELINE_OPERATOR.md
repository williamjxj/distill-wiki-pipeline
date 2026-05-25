# Wiki Pipeline Operator

Local web app and CLI for operating the LLM-Wiki ETL pipeline without Cursor. Ingest, lint, export, and sync research from the wiki submodule into `docs/` with human approval gates preserved.

See the [design spec](superpowers/specs/2026-05-25-wiki-pipeline-operator-design.md) for architecture, data flows, and build order.

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.11+ | Core library, API, MCP, CLI |
| Node.js | 20+ | React UI (`pipeline/ui/`) |
| Ollama | latest | Local LLM for ingest/export workflows |
| Git submodule | initialized | Wiki at `wiki/` |

Ensure Ollama is running before using ingest or export in the UI:

```bash
ollama serve
ollama pull qwen2.5:7b-instruct   # default model in pipeline/config.yaml
```

## Setup

From the repo root:

```bash
cd pipeline
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -e ".[dev]"

cd ui
npm install
cd ../..
```

The CLI entrypoint is `./scripts/wiki-pipeline` (runs `python -m pipeline.cli.main` from `pipeline/`).

## Running

Start the API server (FastAPI on port 8787 by default):

```bash
./scripts/wiki-pipeline serve
```

In a second terminal, start the UI dev server:

```bash
cd pipeline/ui
npm run dev
```

Open the URL printed by Vite (typically `http://localhost:5173`). The UI proxies API requests to the backend.

### Optional: MCP sidecar

For external agents (Cursor, Claude Desktop):

```bash
./scripts/wiki-pipeline mcp
```

Register in your MCP config (see below). MCP exposes read-heavy tools over `wiki_core`; LLM ingest/export still require the web UI approval flows.

### Optional: Watch for pending raw files

Poll pipeline status and notify when new pending raw files appear:

```bash
./scripts/wiki-pipeline watch              # default: 60s interval
./scripts/wiki-pipeline watch --interval 30
```

On macOS, notifications use `osascript`. On Linux and other platforms, messages print to stdout.

## CLI reference

| Command | Description |
|---------|-------------|
| `status` | Pipeline summary: pending raw count, lint counts, brief status, export cycle, last log entry |
| `lint [--json]` | Run deterministic lint rules; `--json` for machine-readable output |
| `sync [--brief-only]` | Run `scripts/sync-wiki-docs.sh`; warns if brief is still `draft` |
| `serve [--host HOST] [--port PORT]` | Start FastAPI + hot reload (default `127.0.0.1:8787`) |
| `mcp` | Start MCP stdio server |
| `watch [--interval SECONDS]` | Poll for pending raw files; notify on change (min interval 1s) |

Examples:

```bash
./scripts/wiki-pipeline status
./scripts/wiki-pipeline lint
./scripts/wiki-pipeline lint --json
./scripts/wiki-pipeline sync
./scripts/wiki-pipeline sync --brief-only
./scripts/wiki-pipeline serve --port 8787
./scripts/wiki-pipeline watch --interval 120
```

## MCP registration

Add to Cursor (`.cursor/mcp.json`) or Claude Desktop config. Adjust paths to your checkout:

```json
{
  "mcpServers": {
    "wiki-pipeline": {
      "command": "/path/to/distill-wiki-pipeline/pipeline/venv/bin/python",
      "args": ["-m", "pipeline.mcp.server"],
      "cwd": "/path/to/distill-wiki-pipeline/pipeline"
    }
  }
}
```

If not using a venv, use your system `python3` and ensure `wiki-pipeline` is installed (`pip install -e ".[dev]"` from `pipeline/`).

### MCP tools

| Tool | Description |
|------|-------------|
| `wiki_list_pending` | Raw files with `status: pending` |
| `wiki_read_page` | Read wiki page by slug or path |
| `wiki_search` | Search wiki content |
| `wiki_get_status` | Pipeline health summary |
| `wiki_run_lint` | Structured lint report |
| `wiki_sync_brief` | Sync brief to parent `docs/` (with draft warnings) |

## Scheduled lint (cron)

Run lint on a schedule and append JSON results to a log:

```cron
0 9 * * * /path/to/distill-wiki-pipeline/scripts/wiki-pipeline lint --json >> /tmp/wiki-lint.log 2>&1
```

Use absolute paths in cron. Activate is not required if the shebang script invokes the venv Python, or point cron at `pipeline/venv/bin/python -m pipeline.cli.main lint --json`.

## Configuration

Edit `pipeline/config.yaml` for wiki paths, Ollama URL, model names, and server host/port. Defaults assume the wiki submodule at `../wiki` relative to `pipeline/`.

Default model is `qwen2.5:7b-instruct` (local). Override at runtime via environment variable:

```bash
PIPELINE_OLLAMA_MODEL=deepseek-v4-flash:cloud ./scripts/wiki-pipeline serve
```

## Related docs

| Document | Purpose |
|----------|---------|
| [Design spec](superpowers/specs/2026-05-25-wiki-pipeline-operator-design.md) | Architecture, data flows, MCP, testing |
| [Implementation plan](superpowers/plans/2026-05-25-wiki-pipeline-operator.md) | Task-by-task build order |
| [wiki/AGENTS.md](../wiki/AGENTS.md) | Wiki schema and workflow authority |
| [README.md](../README.md) | Repo overview and research loop |
