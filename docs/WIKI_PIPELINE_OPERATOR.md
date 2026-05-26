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

The CLI entrypoint is installed as `wiki-pipeline` in the venv (defined by `[project.scripts]` in `pyproject.toml`). You can also invoke it directly:

```bash
# Via installed entrypoint (after pip install -e .):
wiki-pipeline serve

# Or directly with python:
python -m pipeline.cli.main serve
```

## Running

Start the API server (FastAPI on port 8787 by default):

```bash
# Activate venv first
source pipeline/venv/bin/activate
wiki-pipeline serve
```

In a second terminal, start the UI dev server:

```bash
cd pipeline/ui
npm run dev
```

Open the URL printed by Vite (typically `http://localhost:5173`). The UI proxies API requests to the backend.

### Optional: MCP sidecar

For external agents (Cursor, Claude Desktop, OpenCode):

```bash
wiki-pipeline mcp
# Or directly:
python -m pipeline.mcp.server
```

Register in your MCP config (see below). MCP exposes **read-heavy** tools over `wiki_core`; LLM ingest/export still require the web UI approval flows.

**What MCP CAN do:** list pending files, read pages, search content, check pipeline status, run lint, sync brief.

**What MCP CANNOT do:** run ingest or export workflows — those require multi-stage human approval in the web UI.

### Optional: Watch for pending raw files

Poll pipeline status and notify when new pending raw files appear:

```bash
wiki-pipeline watch              # default: 60s interval
wiki-pipeline watch --interval 30
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

Examples (from `pipeline/` directory, venv active):

```bash
wiki-pipeline status
wiki-pipeline lint
wiki-pipeline lint --json
wiki-pipeline sync
wiki-pipeline sync --brief-only
wiki-pipeline serve --port 8787
wiki-pipeline watch --interval 120
```

Without activating the venv, use the full path:

```bash
pipeline/venv/bin/wiki-pipeline status
```

Or via `python -m` from the `pipeline/` directory:

```bash
python -m pipeline.cli.main status
python -m pipeline.cli.main lint --json
python -m pipeline.cli.main serve
```

## MCP registration

### Cursor

Already configured in `.cursor/mcp.json` at the repo root (relative paths work because Cursor sets `cwd`):

```json
{
  "mcpServers": {
    "wiki-pipeline": {
      "command": "./pipeline/venv/bin/python",
      "args": ["-m", "pipeline.mcp.server"],
      "cwd": "./pipeline"
    }
  }
}
```

### Claude Desktop

Add to `claude_desktop_config.json` (use absolute paths):

```json
{
  "mcpServers": {
    "wiki-pipeline": {
      "command": "/absolute/path/to/pipeline/venv/bin/python",
      "args": ["-m", "pipeline.mcp.server"]
    }
  }
}
```

### OpenCode

OpenCode does not have native MCP support. If you want to use the MCP tools from within an OpenCode session, run the server in a separate terminal:

```bash
# Terminal 1: start MCP sidecar
cd /path/to/pipeline && venv/bin/python -m pipeline.mcp.server
```

Then in your OpenCode session, use a tool like `webfetch` or a script to interact with it, or integrate via a custom tool/resource if your OpenCode setup supports MCP client connections.

### If not using a venv

Use your system `python3` and ensure `wiki-pipeline` is installed:

```bash
cd pipeline
pip install -e ".[dev]"
which wiki-pipeline          # should show something in your PATH
```

### MCP tools

| Tool | Description |
|------|-------------|
| `wiki_list_pending` | Raw files with `status: pending` |
| `wiki_read_page` | Read wiki page by slug or path |
| `wiki_search` | Search wiki content |
| `wiki_get_status` | Pipeline health summary |
| `wiki_run_lint` | Structured lint report |
| `wiki_sync_brief` | Sync brief to parent `docs/` (with draft warnings) |

The MCP server is intentionally **read-heavy**. Ingest and export require human approval in the web UI and are not exposed as MCP tools. Use the dashboard at `http://localhost:5173` for those workflows.

## Scheduled tasks (cron)

Cron runs with a minimal `PATH` — always use absolute paths to the venv Python or the installed entrypoint.

### Lint on a schedule

Append JSON results to a log file daily:

```cron
0 9 * * * /path/to/pipeline/venv/bin/wiki-pipeline lint --json >> /tmp/wiki-lint.log 2>&1
```

### Watch for pending files as a daemon

On reboot, start the watch loop (sends macOS notifications on new pending items):

```cron
@reboot /path/to/pipeline/venv/bin/wiki-pipeline watch >> /tmp/wiki-watch.log 2>&1
```

### Periodic sync

Synchronize the brief to parent `docs/` every 6 hours:

```cron
0 */6 * * * /path/to/pipeline/venv/bin/wiki-pipeline sync --brief-only >> /tmp/wiki-sync.log 2>&1
```

### Combined pattern (shell script for multiple steps)

For multi-step cron jobs, create a wrapper script:

```bash
#!/usr/bin/env bash
# /path/to/pipeline/cron/wiki-daily.sh
set -euo pipefail
LOG=/tmp/wiki-daily.log

echo "=== $(date) ===" >> "$LOG"
/path/to/pipeline/venv/bin/wiki-pipeline lint --json >> "$LOG" 2>&1
/path/to/pipeline/venv/bin/wiki-pipeline status >> "$LOG" 2>&1
```

Then in crontab:

```cron
30 8 * * * /path/to/pipeline/cron/wiki-daily.sh
```

**Constraints for cron:**
- Ollama must be running (`ollama serve`) for any LLM-dependent operation
- Ingest and export workflows require the web UI (human approval gates) — cron cannot automate those
- All paths must be absolute — cron has no knowledge of your project structure

## Configuration

Edit `pipeline/config.yaml` for wiki paths, Ollama URL, model names, and server host/port. Defaults assume the wiki submodule at `../wiki` relative to `pipeline/`.

Default model is `qwen2.5:7b-instruct` (local). Override at runtime via environment variable:

```bash
PIPELINE_OLLAMA_MODEL=deepseek-v4-flash:cloud wiki-pipeline serve
```

## Related docs

| Document | Purpose |
|----------|---------|
| [Design spec](superpowers/specs/2026-05-25-wiki-pipeline-operator-design.md) | Architecture, data flows, MCP, testing |
| [Implementation plan](superpowers/plans/2026-05-25-wiki-pipeline-operator.md) | Task-by-task build order |
| [wiki/AGENTS.md](../wiki/AGENTS.md) | Wiki schema and workflow authority |
| [README.md](../README.md) | Repo overview and research loop |
