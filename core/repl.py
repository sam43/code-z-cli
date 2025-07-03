# core/repl.py

import json
import os
from core import model
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.table import Table
from pathlib import Path
import glob
import shlex
import re
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

console = Console()

TOOLS = {
    "websearch": False
}

HELP_TEXT = '''\
[bold cyan]Available Commands:[/bold cyan]
- [bold blue]/read <filepath>[/bold blue]: Read and display a file with syntax highlighting
- [bold blue]/load_session[/bold blue]: List and load a previous session as context
- [bold blue]/forget_session[/bold blue]: Forget the currently loaded session context
- [bold blue]/clear[/bold blue] or [bold blue]clr[/bold blue]: Clear the terminal screen for more space
- [bold blue]/endit[/bold blue]: End the session and save conversation
- [bold blue]/helpme[/bold blue]: Show this help message
- [bold blue]/tools[/bold blue]: Enable or disable optional tools (e.g., websearch)
'''

read_file_cache = {}

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SESSION_DIR = os.path.join(PROJECT_ROOT, 'sessions')

def summarize_response(response: str, max_lines: int = None) -> str:
    """Return the full response unless max_lines is set and exceeded."""
    lines = response.strip().split('\n')
    if max_lines is not None and len(lines) > max_lines:
        return '\n'.join(lines[:max_lines]) + '\n... (truncated)'
    return response

def format_code_blocks(text: str) -> str:
    """Format code blocks for terminal display using triple backticks."""
    # Replace markdown code blocks with triple backticks (if not already)
    return re.sub(r'```([a-zA-Z]*)\n', '```\n', text)

def read_file_content(filepath: str, cache_context=True):
    try:
        path = Path(filepath).expanduser().resolve()
        if not path.exists():
            console.print(f"[red]Error: File not found: {path}[/red]")
            return
        if not path.is_file():
            console.print(f"[red]Error: Not a file: {path}[/red]")
            return
        content = path.read_text(encoding='utf-8')
        ext = path.suffix.lstrip('.')
        syntax = Syntax(content, ext, theme="monokai", line_numbers=True)
        console.print(Panel(syntax, title=str(path)))
        if cache_context:
            read_file_cache[str(path)] = content
    except Exception as e:
        console.print(f"[red]Error reading file:[/red] {e}")

def load_previous_session(session_dir=SESSION_DIR):
    session_files = sorted(glob.glob(os.path.join(session_dir, "session_*.json")), reverse=True)
    if not session_files:
        return []
    latest_session = session_files[0]
    try:
        with open(latest_session, "r") as f:
            return json.load(f)
    except Exception as e:
        console.print(f"[red]Failed to load previous session:[/red] {e}")
        return []

def list_sessions(session_dir=SESSION_DIR):
    session_files = sorted(glob.glob(os.path.join(session_dir, "session_*.json")), reverse=True)
    return session_files

def select_session(session_files):
    table = Table(title="Available Sessions")
    table.add_column("Index", justify="right")
    table.add_column("Filename", justify="left")
    for idx, fname in enumerate(session_files):
        table.add_row(str(idx), fname)
    console.print(table)
    idx = Prompt.ask("Enter session index to load", choices=[str(i) for i in range(len(session_files))], default="0")
    return session_files[int(idx)]

def load_session_file(filepath):
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except Exception as e:
        console.print(f"[red]Failed to load session:[/red] {e}")
        return []

def ensure_session_dir():
    if not os.path.exists(SESSION_DIR):
        os.makedirs(SESSION_DIR)

def show_tools():
    table = Table(title="Available Tools")
    table.add_column("Tool", justify="left")
    table.add_column("Enabled", justify="center")
    for tool, enabled in TOOLS.items():
        table.add_row(tool, "[green]Yes[/green]" if enabled else "[red]No[/red]")
    console.print(table)
    console.print("[cyan]Type the tool name to toggle (enable/disable) it, or press Enter to exit.[/cyan]")
    while True:
        choice = console.input("[bold blue]>>>  [/bold blue]").strip().lower()
        if not choice:
            break
        if choice in TOOLS:
            TOOLS[choice] = not TOOLS[choice]
            console.print(f"[yellow]{choice} is now {'enabled' if TOOLS[choice] else 'disabled'}.[/yellow]")
            show_tools()
            break
        else:
            console.print("[red]Unknown tool. Try again or press Enter to exit.[/red]")

def print_code_snippet(snippet: str, language: str = ""):
    """Print code or text as a formatted snippet in the terminal using Rich."""
    if not language:
        language = "text"
    try:
        syntax = Syntax(snippet, language, theme="monokai", line_numbers=False, word_wrap=True)
        console.print(Panel(syntax, title="Code Snippet"))
    except Exception:
        # Fallback to plain panel if syntax highlighting fails
        console.print(Panel(snippet, title="Snippet"))

def multiline_code_input(prompt_session=None):
    console.print("[cyan]Enter your code snippet. Type ``` on a new line to start and end the block. Use Shift+Enter for new lines inside the block.[/cyan]")
    lines = []
    in_block = False
    while True:
        if prompt_session:
            line = prompt_session.prompt("[bold blue]... [/bold blue]", multiline=True)
        else:
            line = console.input("[bold blue]... [/bold blue]")
        if line.strip() == "```":
            if in_block:
                break
            else:
                in_block = True
                continue
        if in_block:
            lines.append(line)
    return "\n".join(lines)

def print_welcome():
    print("\n")
    print("🧠 Welcome to CodeZ CLI – Your Offline Code Companion")
    print("═══════════════════════════════════════════════════════")
    print("📂 Analyze code files and directories in Swift, Obj-C")
    print("🧾 Ask natural language questions about functions or files")
    print("🧱 Use triple backticks ``` to enter code blocks interactively")
    print("🚪 Type 'exit', '/endit', or 'quit' anytime to leave")
    print("═══════════════════════════════════════════════════════\n")


def run():
    console.print("[bold green]Welcome to CodeZ CLI. Type '/endit' to end session.[/bold green]")
    ensure_session_dir()
    session = []
    session_file = os.path.join(SESSION_DIR, f"session_{os.getpid()}.json")
    prev_context = load_previous_session()
    if prev_context:
        console.print("[yellow]Loaded previous session context.[/yellow]")
    websearch_prompted = False
    prompt_session = PromptSession()
    while True:
        with patch_stdout():
            query = prompt_session.prompt('>>> ', multiline=False, enable_history_search=True)
        if query.strip() == "```":
            code = multiline_code_input(prompt_session)
            print_code_snippet(code)
            continue
        if not query.strip():
            continue
        if query.strip().lower() in ["exit", "quit", "/endit"]:
            console.print("[yellow]Session ended. Saving context...[/yellow]")
            ensure_session_dir()
            with open(session_file, "w") as f:
                json.dump(session, f, indent=2)
            break
        if query.strip().startswith("/helpme"):
            console.print(HELP_TEXT)
            continue
        if query.strip().startswith("/tools"):
            show_tools()
            continue
        if query.strip().startswith("/forget_session"):
            prev_context = []
            console.print("[yellow]Previous session context forgotten. You are now starting fresh.[/yellow]")
            continue
        if query.strip().lower() in ["clr", "/clear"]:
            console.clear()
            continue
        if query.strip().lower() == "clear":
            console.print("[yellow]To clear the console, type 'clr' or '/clear'.[/yellow]")
            continue
        if query.strip().startswith("/read "):
            arg = query.strip()[6:].strip()
            try:
                parts = shlex.split(arg)
                filepath = parts[0] if parts else ''
            except Exception:
                filepath = arg.split(' ')[0]
            if not filepath:
                console.print("[red]No file path provided.[/red]")
                continue
            read_file_content(filepath)
            console.print(f"[yellow]Finished reading {filepath}. Do you need any assistance with this file? (yes/no)[/yellow]")
            followup = console.input("[bold blue]>>> [/bold blue]").strip().lower()
            if followup in ["yes", "y"]:
                file_content = read_file_cache.get(str(Path(filepath).expanduser().resolve()), "")
                console.print("[green]You can now ask questions about this file. Your next question will use its content as context.[/green]")
                user_q = console.input("[bold blue]>>> [/bold blue]")
                system_prompt = (
                    "You are a precise and honest code assistant. "
                    "Read the provided resource carefully and answer only based on the given context. "
                    "If you do not know, say so. Do not hallucinate or invent details. "
                    "Align your answer strictly with the resource and question. "
                )
                if TOOLS.get("websearch"):
                    system_prompt += (
                        " If you need more information, you are allowed to use the websearch tool to search the web for relevant content. "
                        "Use the websearch tool only if it is enabled by the user."
                    )
                full_prompt = f"{system_prompt}\n\nFile content:\n{file_content}\n\nUser question: {user_q}"
                with console.status("[bold cyan]Thinking deeply about the file and your question..."):
                    response = model.query_ollama(full_prompt)
                    concise = summarize_response(response)
                console.print(Markdown(concise))
                session.append({"user": user_q, "response": response, "file": str(Path(filepath).expanduser().resolve())})
            continue
        if query.strip().startswith("/load_session"):
            session_files = list_sessions()
            if not session_files:
                console.print("[red]No session files found.[/red]")
                continue
            selected = select_session(session_files)
            prev_context = load_session_file(selected)
            console.print(f"[green]Loaded session: {selected}[/green]")
            continue
        if query.strip().startswith("/forget_session"):
            prev_context = []
            console.print("[yellow]Previous session context forgotten. You are now starting fresh.[/yellow]")
            continue
        if not websearch_prompted:
            console.print("[cyan]Optional: Enable websearch tool for this session? (yes/no)[/cyan]")
            enable_web = console.input("[bold blue]>>>  [/bold blue]").strip().lower()
            if enable_web in ["yes", "y"]:
                TOOLS["websearch"] = True
                console.print("[green]Websearch tool enabled for this session.[/green]")
            websearch_prompted = True
        if TOOLS["websearch"]:
            console.print("[cyan]Websearch tool is enabled. Searching online for your answer...[/cyan]")
            try:
                if "fetch_webpage" in globals():
                    web_result = fetch_webpage(query, ["https://www.google.com/search?q=" + query.replace(' ', '+')])
                else:
                    web_result = {"content": f"[Web search not available in this environment. Simulated result for: {query}]"}
                web_content = web_result["content"] if isinstance(web_result, dict) and "content" in web_result else str(web_result)
            except Exception as e:
                web_content = f"[Web search failed: {e}]"
            context_str = "\n".join([f"User: {item['user']}\nModel: {item['response']}" for item in prev_context])
            system_prompt = (
                "You are a precise and honest code assistant. "
                "Read the provided resource carefully and answer only based on the given context. "
                "If you do not know, say so. Do not hallucinate or invent details. "
                "Align your answer strictly with the resource and question. "
                "If you need more information, you are allowed to use the websearch tool to search the web for relevant content. "
                "Use the websearch tool only if it is enabled by the user."
            )
            full_prompt = f"{system_prompt}\n\n{context_str}\nWeb search result: {web_content}\nUser: {query}\nModel:"
        else:
            system_prompt = (
                "You are a precise and honest code assistant. "
                "Read the provided resource carefully and answer only based on the given context. "
                "If you do not know, say so. Do not hallucinate or invent details. "
                "Align your answer strictly with the resource and question. "
            )
            context_str = "\n".join([f"User: {item['user']}\nModel: {item['response']}" for item in prev_context])
            full_prompt = f"{system_prompt}\n\n{context_str}\nUser: {query}\nModel:"
        with console.status("[bold cyan]Preparing context...") as status:
            status.update("[bold cyan]Querying model...")
            response = model.query_ollama(full_prompt)
            status.update("[bold cyan]Formatting output...")
            concise = summarize_response(response)
        console.print("[bold magenta]CodeZ:[/bold magenta]", end=" ")
        console.print(Markdown(concise))
        session.append({"user": query, "response": response})
