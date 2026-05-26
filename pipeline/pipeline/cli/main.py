from __future__ import annotations

import asyncio
import json
from pathlib import Path

import typer

from pipeline.wiki_core.lint import run_lint
from pipeline.wiki_core.paths import resolve_paths
from pipeline.wiki_core.status import get_pipeline_status
from pipeline.wiki_core.sync import run_sync

app = typer.Typer(name="wiki-pipeline", help="LLM-Wiki pipeline operator")


@app.callback()
def main():
    """LLM-Wiki pipeline operator"""


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


@app.command()
def serve(host: str = "127.0.0.1", port: int = 8787):
    import uvicorn

    uvicorn.run("pipeline.api.main:app", host=host, port=port, reload=False)


@app.command()
def mcp():
    from pipeline.mcp.server import main

    main()


@app.command()
def watch(interval: int = typer.Option(60, "--interval", min=1)):
    from pipeline.cli.watch import watch_loop

    watch_loop(interval=interval)


@app.command()
def auto(
    file_path: str | None = typer.Option(None, "--file", "-f", help="Process a specific raw file (relative to wiki root)"),
    all_pending: bool = typer.Option(False, "--all", "-a", help="Process all pending raw files"),
    watch: bool = typer.Option(False, "--watch", "-w", help="Watch for new pending files and process automatically"),
    interval: int = typer.Option(60, "--interval", "-i", min=1, help="Poll interval in seconds (--watch only)"),
):
    """Run the full pipeline (ingest → lint → export → lint → graph → sync)
    with pre-approval — no human gates, no web UI required."""
    from pipeline.workflows.auto import process_all_pending, run_pipeline, watch_loop

    if watch:
        asyncio.run(watch_loop(interval=interval))
    elif file_path:
        rel = _resolve_raw_arg(file_path)
        asyncio.run(run_pipeline(rel))
    elif all_pending:
        asyncio.run(process_all_pending())
    else:
        typer.echo("Specify --file, --all, or --watch. See --help for details.")
        raise typer.Exit(code=1)


def _resolve_raw_arg(raw_arg: str) -> str:
    """Normalise a user-supplied ``--file`` value to a wiki-root-relative path.

    The ``scripts/wiki-pipeline`` wrapper chdirs to ``pipeline/`` before
    invoking Python, so a path that was correct at the shell  (e.g.
    ``./wiki/raw/llm/chat.md`` from the repo root) won't resolve from the new
    CWD.  This function tries the path as-is first, then prepends ``../``,
    then raises.
    """
    from pipeline.wiki_core.paths import resolve_paths

    paths = resolve_paths()
    wiki_root = paths.wiki_root.resolve()

    for candidate in (Path(raw_arg), Path("..") / raw_arg):
        abs_path = candidate.resolve()
        if abs_path.is_file():
            try:
                return str(abs_path.relative_to(wiki_root))
            except ValueError:
                typer.echo(
                    f"Error: {raw_arg} resolves to {abs_path} which is outside"
                    f" wiki root ({wiki_root})",
                    err=True,
                )
                raise typer.Exit(code=1)

    typer.echo(f"Error: file not found: {raw_arg}", err=True)
    raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
