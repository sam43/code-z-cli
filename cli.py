"""
Interface layer: CLI, REPL, and event adapters.
"""

import typer
from core import repl, summarizer

app = typer.Typer()

@app.command("explain")
def explain(path: str, function: str = None):
    """
    Explain the content of a file or a specific function within that file.

    Args:
        path (str): The file path to explain.
        function (str, optional): The specific function name to explain. If None, explain the whole file.

    This function calls the summarizer to generate a detailed explanation,
    handles errors gracefully, and outputs the result to the CLI.
    """
    try:
        result = summarizer.explain(path, function)
        if not result:
            typer.echo("No explanation could be generated. Please check the file path and function name.")
        else:
            typer.echo(result)
    except FileNotFoundError:
        typer.echo(f"Error: File not found at path '{path}'. Please provide a valid file path.")
    except Exception as e:
        typer.echo(f"An unexpected error occurred: {e}")

@app.command("chat")
def chat():
    """Interactive REPL to ask questions about code"""
    repl.run()

def main():
    app()

if __name__ == "__main__":
    main()