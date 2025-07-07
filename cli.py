import typer
from core import repl, summarizer

app = typer.Typer()

@app.command()
def explain(path: str, function: str = None):
    """Explain a file or specific function"""
    result = summarizer.explain(path, function)
    typer.echo(result)

@app.command()
def chat():
    """Interactive REPL to ask questions about code"""
    repl.run()

def main():
    app()

if __name__ == "__main__":
    main()