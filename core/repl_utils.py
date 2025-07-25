"""
Utility functions for the CodeZ CLI REPL.
"""
import os
import re
import json
import glob
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

def print_error(message: str, title: str = "Error", console=None):
    """Prints a Rich Panel formatted error message."""
    if console is None:
        console = Console()
    console.print(Panel(Markdown(message), title=f"[bold red]{title}[/bold red]", border_style="red", expand=False))

def summarize_response(response: str, max_lines: int = None) -> str:
    """Return the full response unless max_lines is set and exceeded."""
    lines = response.strip().split('\n')
    if max_lines is not None and len(lines) > max_lines:
        return '\n'.join(lines[:max_lines]) + '\n... (truncated)'
    return response

def format_code_blocks(text: str) -> str:
    """Format code blocks for terminal display using triple backticks."""
    return re.sub(r'```([a-zA-Z]*)\n', '```\n', text)

def filter_thinking_block(response: str) -> str:
    """Remove the <think>...</think> block from the LLM response if present."""
    pattern = r"(?s)<think>.*?</think>"
    return re.sub(pattern, '', response).strip()

def list_sessions(session_dir):
    session_files = sorted(glob.glob(os.path.join(session_dir, "session_*.json")), reverse=True)
    return session_files

def load_session_file(filepath):
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except Exception as e:
        print_error(f"Failed to load session from `{filepath}`: {e}", title="Session Load Error")
        return []

def select_session(session_files, console=None):
    if console is None:
        console = Console()
    table = Table(title="[bold sky_blue1]Available Sessions[/bold sky_blue1]", border_style="sky_blue1", show_lines=True)
    table.add_column("Index", justify="right", style="cyan", no_wrap=True)
    table.add_column("File Path", style="magenta", no_wrap=False)
    table.add_column("Last Modified", style="yellow", no_wrap=True)
    for idx, filepath_str in enumerate(session_files):
        try:
            mtime = os.path.getmtime(filepath_str)
            last_modified_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            last_modified_str = "N/A"
        table.add_row(str(idx), filepath_str, last_modified_str)
    console.print(Panel(table, expand=False, title="[dim]Load Session[/dim]"))
    from rich.prompt import Prompt
    idx = Prompt.ask(
        "[bold blue]Enter session index to load[/bold blue]",
        choices=[str(i) for i in range(len(session_files))],
        default="0"
    )
    return session_files[int(idx)]
