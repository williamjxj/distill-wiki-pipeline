from __future__ import annotations
import json
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

    uvicorn.run("pipeline.api.main:app", host=host, port=port, reload=True)


@app.command()
def mcp():
    from pipeline.mcp.server import main

    main()


if __name__ == "__main__":
    app()
