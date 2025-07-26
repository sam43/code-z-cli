"""
Interface layer: CLI, REPL, and event adapters.
"""

import typer
from core import repl

app = typer.Typer()


@app.command("chat")
def chat():
    """Interactive REPL to ask questions about code"""
    repl.run()

def main():
    app()

if __name__ == "__main__":
    main()