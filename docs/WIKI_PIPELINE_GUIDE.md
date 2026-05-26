# Wiki Pipeline — CLI, Automation, and MCP Guide

This document summarizes how to operate the wiki pipeline from the command line, schedule automated syncs, and use the MCP interface. It also records recent UI changes (Sync page) and how to test the Graph endpoint.

## Quick CLI reference

All commands below run from the repository root. The helper script `scripts/wiki-pipeline` sets the working directory and invokes the Python CLI.

- Run status

```bash
./scripts/wiki-pipeline status
```

- Run lint (human readable)

```bash
./scripts/wiki-pipeline lint
```

- Run sync (copy wiki/wiki/synthesis → docs/)

```bash
# brief-only sync
./scripts/wiki-pipeline sync --brief-only

# full sync (brief + thesis)
./scripts/wiki-pipeline sync
```

- Start the API server

```bash
./scripts/wiki-pipeline serve --host 0.0.0.0 --port 8787
```

- Start the MCP server (programmatic tool interface)

```bash
./scripts/wiki-pipeline mcp
```

- Run watch loop (long-running polling)

```bash
./scripts/wiki-pipeline watch --interval 60
```

If you use a Python virtualenv, `source ./venv/bin/activate` first.

## What `sync` does

- The top-level `scripts/sync-wiki-docs.sh` copies the wiki exports from `wiki/wiki/synthesis/` into `docs/` in the parent project. It overwrites the target files (not append):

  - `wiki/wiki/synthesis/project-brief.md` → `docs/PROJECT_BRIEF.md`
  - `wiki/wiki/synthesis/evolving-thesis.md` → `docs/RESEARCH_THESIS.md`

- The script warns when the brief has `status: draft`.

If you need history/audit copies, wrap `sync` in a script that produces timestamped archives or commit the copied files to git automatically (examples below).

## Scheduling

1) Cron (simple)

Edit your crontab (`crontab -e`):

```cron
# run brief-only sync at minute 5 of every hour
5 * * * * cd /path/to/experimental-app && /path/to/experimental-app/scripts/wiki-pipeline sync --brief-only >> /var/log/wiki-pipeline/sync.log 2>&1
```

Notes:

- Use absolute paths for script and repo.
- Make sure the environment (virtualenv) is set if required, or call the script with a wrapper that activates the venv.

2) systemd timer (recommended on Linux)

Service unit (`/etc/systemd/system/wiki-pipeline-sync.service`):

```
[Unit]
Description=Wiki Pipeline sync

[Service]
Type=oneshot
WorkingDirectory=/path/to/experimental-app
ExecStart=/path/to/experimental-app/scripts/wiki-pipeline sync --brief-only
```

Timer unit (`/etc/systemd/system/wiki-pipeline-sync.timer`):

```
[Unit]
Description=Run wiki-pipeline sync hourly

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now wiki-pipeline-sync.timer
```

3) Kubernetes CronJob

If you run workloads in k8s, create a CronJob that runs a container image with the repo and executes the `scripts/wiki-pipeline sync` command. Keep logs in stdout/stderr for k8s logging.

## auto-commit wrapper (example)

If you want the sync to be committed and pushed automatically, use a wrapper script (example):

```bash
#!/usr/bin/env bash
set -euo pipefail
cd /path/to/experimental-app
./scripts/wiki-pipeline sync --brief-only > /tmp/wiki-sync.out 2>&1
git add docs/PROJECT_BRIEF.md docs/RESEARCH_THESIS.md
git commit -m "Automated sync: $(date --iso-8601=seconds)" || true
git push origin main || true
```

Adjust behavior for your policies (e.g., fail on push errors, use a deploy key, or open a PR instead of direct push).

## MCP (programmatic) interface

- Start the MCP server:

```bash
./scripts/wiki-pipeline mcp
```

- What it exposes:

  - `wiki_list_pending()` — list raw markdown files with `status: pending`
  - `wiki_read_page(slug_or_path)` — read a page by slug/path
  - `wiki_search(query)` — search wiki content
  - `wiki_get_status()` — pipeline health/status
  - `wiki_run_lint()` — run lint and return structured findings
  - `wiki_sync_brief()` — run a brief-only sync and return stdout/warnings

- Typical usage: register the MCP command in your MCP client config (example for local Claude Code):

`~/.claude/mcp_servers.json` example:

```json
{
  "wiki-pipeline": {
    "cmd": "/full/path/to/experimental-app/scripts/wiki-pipeline mcp",
    "cwd": "/full/path/to/experimental-app",
    "env": {}
  }
}
```

The MCP client will start the process and call the tools via stdio. Use MCP when integrating with an agent or LLM that supports MCP; otherwise use the CLI for scheduled automation.

## UI and Graph notes

- The `/api/graph` endpoint returns a JSON structure { nodes: [{id,label}], edges: [{source,target}] } produced by scanning `wiki/wiki/{sources,concepts,synthesis}` for `[[wikilinks]]`. Example test:

```bash
curl -sS http://127.0.0.1:8787/api/graph | python3 -m json.tool
```

- UI changes made during this session:

  - Added a `Sync` page component that centralizes the `sync` action: `pipeline/ui/src/pages/SyncView.tsx` (uses `postSync` API). The Dashboard `Run Sync` button now navigates to this page rather than executing the sync directly.
  - Removed the `Sync` menu item from the main navigation to avoid duplication; the route `/sync` remains accessible.

Files changed (UI): `pipeline/ui/src/App.tsx`, `pipeline/ui/src/pages/SyncView.tsx`, `pipeline/ui/src/pages/SyncView.module.css`, `pipeline/ui/src/pages/Dashboard.tsx`.

## Recommendations

- For unattended automation use `systemd` timers or containerized CronJob.
- Use `mcp` when you want programmatic integration with an agent/LLM environment (e.g., Claude Code). For simple scheduled runs, use the `sync` CLI.
- If you want a persistent history of exports, add an archive step or wrap `sync` to create timestamped copies and commit them.

## Next steps I can implement

- Add a `--git-commit` flag to the `sync` CLI to optionally `git commit` the sync result.
- Add timestamped archive behavior to `scripts/sync-wiki-docs.sh`.
- Provide a tiny MCP test client script (spawn server, call `wiki_sync_brief`, print result).

If you want any of these implemented, tell me which and I will add it.
