"""
Interface layer: CLI, REPL, and event adapters.
"""

import typer
from core import repl, summarizer
from codechat.events.event_bus import bus
from codechat.events import types
from codechat.domain.conversation import Message, Conversation
from codechat.data.session_repository import SessionRepository
from core.user_config import save_system_prompt, clear_model_choice
from rich.console import Console
from rich.text import Text
import toml
import os

app = typer.Typer()

@app.command("explain")
def explain(path: str, function: str = None):
    """
    Generates and displays an explanation for a file or a specific function within a file.
    
    Parameters:
        path (str): Path to the file to be explained.
        function (str, optional): Name of the function to explain. If not provided, explains the entire file.
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
    """
    Launches an interactive REPL session for asking questions about code.
    """
    repl.run()

def main():
    app()

if __name__ == "__main__":
    main()