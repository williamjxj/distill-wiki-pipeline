import typer

app = typer.Typer(name="wiki-pipeline", help="LLM-Wiki pipeline operator")

@app.callback()
def main():
    """LLM-Wiki pipeline operator"""

@app.command()
def status():
    typer.echo("wiki-pipeline: not yet implemented")

if __name__ == "__main__":
    app()
