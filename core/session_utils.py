"""
Session and file utilities for CodeZ CLI.
"""
import os
import json
import glob
from pathlib import Path
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from core.repl_utils import print_error

console = Console()

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SESSION_DIR = os.path.join(PROJECT_ROOT, 'sessions')
read_file_cache = {}

def read_file_content(filepath: str, cache_context=True):
    try:
        path = Path(filepath).expanduser().resolve()
        if not path.exists():
            print_error(f"File not found: `{filepath}`")
            return
        if not path.is_file():
            print_error(f"`{filepath}` is not a file.")
            return
        content = path.read_text(encoding='utf-8')
        ext = path.suffix.lstrip('.')
        syntax = Syntax(content, ext, theme="monokai", line_numbers=True, word_wrap=True)
        console.print(Panel(syntax, title=f"[bold sky_blue1]File: {path.name}[/bold sky_blue1]\n[dim]{path}[/dim]", border_style="sky_blue1", expand=False))
        if cache_context:
            read_file_cache[str(path)] = content
    except Exception as e:
        print_error(f"Could not read file `{filepath}`: {e}", title="File Read Error")

def load_previous_session(session_dir=SESSION_DIR):
    session_files = sorted(glob.glob(os.path.join(session_dir, "session_*.json")), reverse=True)
    if not session_files:
        return []
    latest_session = session_files[0]
    try:
        with open(latest_session, "r") as f:
            return json.load(f)
    except Exception as e:
        print_error(f"Failed to load previous session: {e}", title="Session Load Error")
        return []

def ensure_session_dir(session_dir=SESSION_DIR):
    if not os.path.exists(session_dir):
        os.makedirs(session_dir)

def load_all_sessions(session_dir=SESSION_DIR):
    session_files = sorted(glob.glob(os.path.join(session_dir, "session_*.json")), reverse=True)
    all_turns = []
    for fname in session_files:
        try:
            with open(fname, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    all_turns.extend(data)
        except Exception:
            continue
    return all_turns
