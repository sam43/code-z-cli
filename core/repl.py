# core/repl.py

import json
import os
from core import model
from core.stream_utils import stream_response
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
from core.user_config import save_model_choice, load_model_choice, clear_model_choice
from core.model import fetch_webpage
import time

console = Console()

# TOOLS update for /process
TOOLS = {
    "websearch": False,
    "process": False
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
- [bold blue]/models[/bold blue]: Show or update the selected model
- [bold blue]'!'[/bold blue]: Run shell commands starting with '!' (e.g., !ls, !pwd)
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
            line = prompt_session.prompt(">", multiline=True)
        else:
            line = console.input(">")
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
    console.print("\n")
    console.print("🧠 [bold green]Welcome to CodeZ CLI – Your Offline Code Companion[/bold green]")
    console.print("═══════════════════════════════════════════════════════")
    console.print("📂 [bold green]Analyze code files and directories in Swift, Obj-C[/bold green]")
    console.print("🧾 [bold green]Ask natural language questions about functions or files[/bold green]")
    console.print("🧱 [bold green]Use triple backticks ``` to enter code blocks interactively[/bold green]")
    console.print("🚪 [bold green]Type 'exit', '/endit', or 'quit' anytime to leave[/bold green]")
    console.print("[!] [bold cyan]To run a shell command - just add '!' before your shell command i.e: '!ls', '!pwd' etc.[/bold cyan]")
    console.print("═══════════════════════════════════════════════════════\n")


def run(with_memory=True):
    """
    Main REPL loop. If with_memory is True, use contextual replies (session memory), else stateless mode.
    """
    from core import model as model_mod
    from core.llm_interactive import LLMInteractiveSession
    # Model selection at the start
    models, err = model_mod.get_ollama_models()
    saved_model = load_model_choice()
    selected_model = None
    if err:
        console.print(f"[red]{err}[/red]")
        return
    if models:
        if saved_model and saved_model in models:
            selected_model = saved_model
            console.print(f"[green]Using saved model:[/green] {selected_model}")
        else:
            console.print("[cyan]Available models:[/cyan] " + ", ".join(models))
            selected_model = console.input("[bold blue]Enter model name (default: deepseek-r1:latest): [/bold blue]").strip()
            if not selected_model:
                selected_model = "deepseek-r1:latest"
            if selected_model not in models:
                console.print(f"[red]Model '{selected_model}' not found. Please add it using 'ollama pull {selected_model}' and restart.")
                return
            # Ask to save model
            save = console.input("[bold blue]Save this model for future sessions? (y/n): [/bold blue]").strip().lower()
            if save in ["y", "yes"]:
                save_model_choice(selected_model)
                console.print(f"[green]Model '{selected_model}' saved for future sessions.[/green]")
    else:
        console.print("[red]No models found in ollama. Please add a model using 'ollama pull <model>' and restart.")
        return

    # console.print("[bold green]Welcome to CodeZ CLI. Type '/endit' to end session.[/bold green]")
    print_welcome()
    ensure_session_dir()
    session = []
    session_file = os.path.join(SESSION_DIR, f"session_{os.getpid()}.json")
    prev_context = load_previous_session()
    # Load all previous session turns for context
    all_session_turns = load_all_sessions()
    if prev_context:
        console.print("[yellow]Loaded previous session context.[/yellow]")
    websearch_prompted = False
    prompt_session = PromptSession()
    last_thinking = None  # Store last thinking process

    # Session memory setup
    session_agent = LLMInteractiveSession(
        model_name=selected_model,
        persist=with_memory
    )

    # Add: Paste code snippet interactively
    def paste_code_snippet():
        console.print("[cyan]Paste your code snippet below. Type 'END' on a new line to finish.[/cyan]")
        lines = []
        while True:
            line = input()
            if line.strip() == 'END':
                break
            lines.append(line)
        code = '\n'.join(lines)
        return code

    import re
    def clean_code_snippet(code: str) -> str:
        """Remove line numbers from pasted code."""
        lines = code.splitlines()
        cleaned = []
        for line in lines:
            # Remove leading line numbers (e.g., ' 1 |', '12 ', '003:')
            cleaned.append(re.sub(r"^\s*\d+[:|\s]", "", line))
        return "\n".join(cleaned)

    # New paste mode for code blocks
    def paste_code_snippet_block():
        console.print("[cyan]Paste your code below. Type 'END' on a new line to finish.[/cyan]")
        lines = []
        while True:
            line = input()
            if line.strip() == 'END':
                break
            lines.append(line)
        code = '\n'.join(lines)
        return clean_code_snippet(code)

    while True:
        with patch_stdout():
            query = prompt_session.prompt('>>> ', multiline=False, enable_history_search=True)
        # Detect code block start
        if query.strip() == '```':
            code = paste_code_snippet_block()
            console.print("[green]Code block pasted. Continue typing your question or press Enter to send.[/green]")
            followup = prompt_session.prompt('>>> ', multiline=False, enable_history_search=True)
            if followup.strip():
                query = f"Here is my code:\n{code}\n{followup.strip()}"
            else:
                query = f"Here is my code:\n{code}"
        # Handle shell commands starting with '!'
        if query.strip().startswith("!"):
            import subprocess
            shell_cmd_str = query.strip()[1:]
            if not shell_cmd_str:
                console.print("[red]No shell command provided after '!'.[/red]")
                continue
            try:
                # Split the command string into a list for shell=False
                shell_cmd_list = shlex.split(shell_cmd_str)
                if not shell_cmd_list: # Handle empty string after shlex.split
                    console.print("[red]No valid shell command provided after '!'.[/red]")
                    continue

                result = subprocess.run(shell_cmd_list, shell=False, capture_output=True, text=True)
                if result.stdout:
                    console.print(f"[green]{result.stdout}[/green]", end="")
                if result.stderr:
                    console.print(f"[red]{result.stderr}[/red]", end="")
            except FileNotFoundError:
                console.print(f"[red]Error: Command not found: {shell_cmd_list[0]}[/red]")
            except Exception as e:
                console.print(f"[red]Shell command error:[/red] {e}")
            continue
        # Handle all tool commands starting with '/'
        if query.strip().startswith("/"):
            # Use regex to robustly match /read <filepath> (with or without quotes, and with spaces)
            import re as _re
            read_match = _re.match(r"^/read\s+(['\"]?)(.+?)\1\s*$", query.strip())
            if read_match:
                filepath = read_match.group(2)
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
                        response = model.query_ollama(full_prompt, selected_model)
                        last_thinking = summarize_response(response)
                    # Stream the model response
                    console.print("[bold magenta]CodeZ:[/bold magenta]", end=" ")
                    # Stream the model response character by character
                    from core.stream_utils import stream_response
                    stream_response(last_thinking, console=console, delay=0.01)
                    # Optionally, for code snippets, you can still use print_llm_response_with_snippets if needed
                    # print_llm_response_with_snippets(last_thinking)
                    session.append({"user": user_q, "response": response, "file": str(Path(filepath).expanduser().resolve())})
                continue
            # Only split for other tool commands if not /read
            cmd = shlex.split(query.strip())
            if cmd[0] == "/helpme":
                console.print(HELP_TEXT)
                continue
            if cmd[0] == "/tools":
                show_tools()
                continue
            if cmd[0] == "/models" or cmd[0] == "/model": # Allow both /models and /model
                # /models -u <current_model> <new_model>
                if len(cmd) >= 4 and cmd[1] in ["-u", "--update"]:
                    current_model = cmd[2]
                    new_model = cmd[3]
                    models, err = model_mod.get_ollama_models()
                    if err:
                        console.print(f"[red]{err}[/red]")
                        continue
                    if new_model not in models:
                        console.print(f"[red]Model '{new_model}' not found. Please add it using 'ollama pull {new_model}' and try again.")
                        continue
                    save_model_choice(new_model)
                    console.print(f"[green]Model updated from '{current_model}' to '{new_model}'.[/green]")
                    selected_model = new_model
                else:
                    # Show current and available models
                    models, err = model_mod.get_ollama_models()
                    if err:
                        console.print(f"[red]{err}[/red]")
                        continue
                    console.print(f"[cyan]Current model:[/cyan] {selected_model}")
                    console.print("[cyan]Available models:[/cyan] " + ", ".join(models))
                continue
            if cmd[0] == "/process":
                if last_thinking:
                    console.print("[bold blue]--- Thought Process ---[/bold blue]")
                    from core.stream_utils import stream_thinking
                    stream_thinking(last_thinking, console)
                    console.print("[bold blue]----------------------[/bold blue]")
                else:
                    console.print("[yellow]No thought process available for the last response.[/yellow]")
                continue
            # Add more tool commands here as needed
            if cmd[0] == "/forget_session":
                prev_context = []
                console.print("[yellow]Previous session context forgotten. You are now starting fresh.[/yellow]")
                continue
            # Unknown tool command
            console.print(f"[red]Unknown tool command: {cmd[0]}")
            continue
        # Handle shell commands starting with '!'
        if query.strip().startswith("!"):
            shell_cmd_str = query.strip()[1:]
            import subprocess
            if not shell_cmd_str:
                console.print("[red]No shell command provided after '!'.[/red]")
                continue
            try:
                shell_cmd_list = shlex.split(shell_cmd_str)
                if not shell_cmd_list: # Handle empty string after shlex.split
                    console.print("[red]No valid shell command provided after '!'.[/red]")
                    continue
                result = subprocess.run(shell_cmd_list, shell=False, capture_output=True, text=True)
                if result.stdout:
                    console.print(f"[green]{result.stdout.strip()}[/green]")
                if result.stderr:
                    console.print(f"[red]{result.stderr.strip()}[/red]")
            except Exception as e:
                console.print(f"[red]Shell command failed: {e}[/red]")
            continue
        # All non-tool commands below here
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
        if query.strip().lower() == "clear": # Make 'clear' also clear the screen
            console.clear()
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
                response = None
                try:
                    with console.status("[bold cyan]Thinking deeply about the file and your question..."):
                        # This is not in a separate thread, so direct try-except is fine
                        response = model.query_ollama(full_prompt, selected_model)
                    last_thinking = summarize_response(response)
                except Exception as e:
                    console.print(f"\n[red]Error querying Ollama model: {e}[/red]")
                    console.print("[yellow]Please ensure Ollama is running and the model is available.[/yellow]")
                    session.append({"user": user_q, "response": f"Error: {e}", "file": str(Path(filepath).expanduser().resolve())})
                    continue # Skip response processing

                # Stream the model response
                console.print("[bold magenta]CodeZ:[/bold magenta]", end=" ")
                # Stream the model response character by character
                from core.stream_utils import stream_response
                stream_response(last_thinking, console=console, delay=0.01)
                # Optionally, for code snippets, you can still use print_llm_response_with_snippets if needed
                # print_llm_response_with_snippets(last_thinking)
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
        # Build context string from session memory (token-aware, not just last 20 turns)
        context_str = session_agent.memory.get_context_prompt()
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
                "You are a precise and honest code assistant who uses reasoning to respond to user queries. "
                "Read the provided resource carefully and answer only based on the given context. "
                "If you do not know, say so. Do not hallucinate or invent details. "
                "Align your answer strictly with the resource and question. "
                "If you need more information, you are allowed to use the websearch tool to search the web for relevant content. "
                "Use the websearch tool only if it is enabled by the user."
            )
            full_prompt = f"{system_prompt}\n\n{context_str}\nWeb search result: {web_content}\nUser: {query}\nModel:"
        else:
            # Update system prompt to be more coding-focused
            system_prompt = (
                "You are a precise and honest code assistant who uses reasoning to respond to user queries. "
                "Focus on providing direct, practical coding solutions, code snippets, reasoning, and implementation details. "
                "Avoid lengthy theoretical explanations unless specifically asked. "
                "If you do not know, say so. Do not hallucinate or invent details. "
                "Align your answer strictly with the resource, context, and question. "
            )
            full_prompt = f"{system_prompt}\n\n{context_str}\nUser: {query}\nModel:"
        with console.status("[bold cyan]Preparing context...") as status:
            # Simulate progress percentage while querying model
            percent = 0
            done = False
            response = None
            def run_model():
                nonlocal response, done
                try:
                    response = model.query_ollama(full_prompt, selected_model)
                except Exception as e:
                    # Capture exception to be handled in the main thread
                    response = e
                finally:
                    done = True
            import threading
            t = threading.Thread(target=run_model)
            t.start()
            while not done:
                percent = min(percent + 7, 99)  # Simulate progress
                status.update(f"[bold cyan]Querying model... {percent}% (Press CTRL+C to stop)[/bold cyan]")
                time.sleep(0.15)
            t.join()

            if isinstance(response, Exception):
                console.print(f"\n[red]Error querying Ollama model: {response}[/red]")
                console.print("[yellow]Please ensure Ollama is running and the model is available.[/yellow]")
                # Optionally, log the error or take other actions
                session.append({"user": query, "response": f"Error: {response}"}) # Log error to session
                # session_agent.memory.add_turn(query, f"Error: {response}") # Also log error to persistent memory
                continue # Skip response processing and restart loop

            status.update("[bold cyan]Querying model... 100%")
            last_thinking = summarize_response(response) # response here is str

        # Stream the model response
        console.print("[bold magenta]CodeZ:[/bold magenta]", end=" ")
        if TOOLS.get("process"):
            print_llm_response_with_snippets(last_thinking)
        else:
            filtered = filter_thinking_block(last_thinking)
            print_llm_response_with_snippets(filtered)
        session.append({"user": query, "response": response}) # response is str
        session_agent.memory.add_turn(query, response)  # Add the turn to memory

# Place this near the top with other function definitions
def filter_thinking_block(response: str) -> str:
    """Remove the <think>...</think> block from the LLM response if present."""
    import re
    pattern = r"(?s)<think>.*?</think>"
    return re.sub(pattern, '', response).strip()

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

def print_llm_response_with_snippets(response: str):
    """
    Print LLM response, rendering code snippets in a styled TUI panel.
    Code blocks (```lang\n...\n```) are rendered with syntax highlighting and a border.
    """
    import re
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.markdown import Markdown
    code_block_pattern = re.compile(r"```([a-zA-Z0-9]*)\n(.*?)```", re.DOTALL)
    last_end = 0
    for match in code_block_pattern.finditer(response):
        # Print any text before the code block
        if match.start() > last_end:
            text = response[last_end:match.start()].strip()
            if text:
                console.print(Markdown(text))
        lang = match.group(1) or "text"
        code = match.group(2).strip()
        syntax = Syntax(code, lang, theme="monokai", line_numbers=True, word_wrap=True)
        console.print(Panel(syntax, title=f"Code Snippet ({lang})", border_style="bold green"))
        last_end = match.end()
    # Print any text after the last code block
    if last_end < len(response):
        text = response[last_end:].strip()
        if text:
            console.print(Markdown(text))
