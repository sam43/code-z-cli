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
from datetime import datetime
from rich.text import Text
from pyfiglet import Figlet

console = Console()

def print_error(message: str, title: str = "Error"):
    """Prints a Rich Panel formatted error message."""
    console.print(Panel(Markdown(message), title=f"[bold red]{title}[/bold red]", border_style="red", expand=False))

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

def list_sessions(session_dir=SESSION_DIR):
    session_files = sorted(glob.glob(os.path.join(session_dir, "session_*.json")), reverse=True)
    return session_files

def select_session(session_files):
    table = Table(title="[bold sky_blue1]Available Sessions[/bold sky_blue1]", border_style="sky_blue1", show_lines=True)
    table.add_column("Index", justify="right", style="cyan", no_wrap=True)
    table.add_column("File Path", style="magenta", no_wrap=False) # Allow wrap for long paths
    table.add_column("Last Modified", style="yellow", no_wrap=True)

    for idx, filepath_str in enumerate(session_files):
        try:
            mtime = os.path.getmtime(filepath_str)
            last_modified_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            last_modified_str = "N/A"
        table.add_row(str(idx), filepath_str, last_modified_str)

    console.print(Panel(table, expand=False, title="[dim]Load Session[/dim]"))

    idx = Prompt.ask(
        "[bold blue]Enter session index to load[/bold blue]",
        choices=[str(i) for i in range(len(session_files))],
        default="0"
    )
    return session_files[int(idx)]

def load_session_file(filepath):
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except Exception as e:
        print_error(f"Failed to load session from `{filepath}`: {e}", title="Session Load Error")
        return []

def ensure_session_dir():
    if not os.path.exists(SESSION_DIR):
        os.makedirs(SESSION_DIR)

def show_tools():
    instruction = "[cyan]Type tool name to toggle, or Enter to exit.[/cyan]"
    table = Table(title="[bold sky_blue1]Tool Configuration[/bold sky_blue1]", caption=instruction, caption_style="dim", border_style="sky_blue1")
    table.add_column("Tool", justify="left", style="magenta")
    table.add_column("Status", justify="center")

    for tool, enabled in TOOLS.items():
        status_text = "[bold green]Enabled[/bold green]" if enabled else "[red]Disabled[/red]"
        table.add_row(tool, status_text)

    console.print(Panel(table, expand=False)) # Wrap table in a simple panel for padding

    while True:
        # Using Rich's Prompt for consistency if possible, or styled console.input
        choice = Prompt.ask("[bold blue]Toggle tool (or Enter to exit)[/bold blue]", default="").strip().lower()

        if not choice:
            break
        if choice in TOOLS:
            TOOLS[choice] = not TOOLS[choice]
            console.print(f"🛠️ [yellow]{choice} is now {'[bold green]enabled[/bold green]' if TOOLS[choice] else '[red]disabled[/red]'}.[/yellow]")
            show_tools() # Recursive call to show updated table
            break
        else:
            console.print("[yellow]Unknown tool. Please try again.[/yellow]")

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
    instruction_text = Markdown("""\
Enter your code snippet below.
- Type ` ``` ` on a new line to **start** the block.
- Paste or type your code.
- Use **Shift+Enter** for new lines within the block if using the default console input.
- Type ` ``` ` on a new line again to **finish** the block.
""")
    console.print(Panel(instruction_text, title="[bold cyan]Multiline Code Input[/bold cyan]", border_style="cyan", expand=False))

    lines = []
    in_block = False

    # Use a consistent prompt style
    input_prompt_style = "[bold sky_blue1]>>> (code)[/bold sky_blue1] " if prompt_session else "[bold sky_blue1]> (code)[/bold sky_blue1] "

    while True:
        if prompt_session:
            # Prompt toolkit's prompt doesn't directly take Rich ConsoleMarkup for the prompt string
            # For simplicity, keeping the prompt session's default prompt look here
            line = prompt_session.prompt(">>> (code) ", multiline=True) # Simple text prompt
        else:
            line = console.input(input_prompt_style)

        if line.strip() == "```":
            if in_block:
                break
            else:
                in_block = True
                continue
        if in_block:
            lines.append(line)
    return "\n".join(lines)

import random

def print_welcome():
    # Generate ASCII art title
    try:
        f = Figlet(font='slant') # 'slant' or 'standard' are good choices
        # For very wide terminals, other fonts like 'banner' might be too wide
        # Default figlet font is 'standard' if 'slant' is not available, though it usually is.
        ascii_art_title = f.renderText("CodeZ CLI")
        console.print(f"[bold bright_magenta]{ascii_art_title}[/bold bright_magenta]", justify="center")
    except Exception as e:
        # Fallback if figlet fails for any reason (e.g. font not found, though unlikely for standard ones)
        console.print("[bold bright_magenta]CodeZ CLI[/bold bright_magenta]", justify="center", style="italic")
        print_error(f"Could not render Figlet title: {e}", "Display Warning")


    tips = [
        "Use `/read <filepath>` to load a file's content into the conversation.",
        "Type `!ls` or any other shell command directly into the prompt!",
        "Use `/models` to see available LLMs or switch to a different one.",
        "Your conversation history provides context to the LLM. Use `/forget_session` to clear it.",
        "Code blocks can be entered by typing ```, pasting your code, then ``` on a new line.",
        "Access help anytime with the `/helpme` command.",
        "Use `/tools` to toggle features like web search (if available)."
    ]
    selected_tip = random.choice(tips)

    # Adjusted message slightly as main title is now ASCII art
    welcome_message = f"""\
🧠 [bold green]Welcome – Your Offline Code Companion[/bold green]

Key Features:
*   📂 Analyze code ([bold]Swift, Obj-C[/bold] via tree-sitter, other languages generally)
*   🧾 Ask natural language questions about your code
*   🧱 Interactive code input using triple backticks (```)
*   셸 Run shell commands with an exclamation mark prefix (e.g., [bold cyan]!ls[/bold cyan])
*   🚪 Type [bold]'exit', '/endit',[/bold] or [bold]'quit'[/bold] to end the session

💡 [bold yellow]Tip of the session:[/bold yellow] {selected_tip}

Type `/helpme` for a full list of commands.
"""
    # Using Text.from_markup directly to ensure Rich tags are parsed.
    # This will render Rich tags but not Markdown syntax like lists.
    # from rich.text import Text # Already imported at top level
    welcome_renderable = Text.from_markup(welcome_message)
    # Changed panel title to be more subtle as main title is now ASCII art
    console.print(Panel(welcome_renderable, title="[dim]Your AI Coding Assistant[/dim]", border_style="blue", expand=False, padding=(1,2)))
    console.print() # Add a newline after the panel


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
        print_error(err, title="Ollama Error")
        return
    if models:
        if saved_model and saved_model in models:
            selected_model = saved_model
            console.print(f"✅ [green]Using saved model:[/green] {selected_model}")
        else:
            console.print("[cyan]Available models:[/cyan]\n - " + "\n - ".join(models))
            selected_model = Prompt.ask("[bold blue]Enter model name[/bold blue]", default="deepseek-r1:latest").strip()
            if not selected_model: # Should be handled by Prompt.ask default, but as a safeguard
                selected_model = "deepseek-r1:latest"
            if selected_model not in models:
                print_error(f"Model [bold]'{selected_model}'[/bold] not found locally. Please ensure it's pulled via `ollama pull {selected_model}` and then restart.", title="Model Not Found")
                return
            # Ask to save model
            save = Prompt.ask("[bold blue]Save this model for future sessions? (y/n)[/bold blue]", choices=["y", "n"], default="y").lower()
            if save in ["y", "yes"]:
                save_model_choice(selected_model)
                console.print(f"[green]Model '{selected_model}' saved for future sessions.[/green]")
    else:
        print_error("No models found in Ollama. Please add a model using `ollama pull <model_name>` and then restart.", title="Ollama Model Error")
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
            query = prompt_session.prompt(">> ", multiline=False, enable_history_search=True)
        # Detect code block start for multiline input
        if query.strip() == '```':
            # Call the improved multiline_code_input which expects ``` to start and end
            code = multiline_code_input(prompt_session)
            console.print("✅ [green]Code block captured.[/green]")

            # Ask for follow-up question regarding the code
            followup_prompt_text = "What would you like to ask about this code? (Press Enter to just send the code)"
            followup = prompt_session.prompt(f'{followup_prompt_text}\n >>> ', multiline=False, enable_history_search=True)

            if followup.strip():
                query = f"Here is my code:\n```\n{code}\n```\n\n{followup.strip()}"
            else:
                query = f"Here is my code:\n```\n{code}\n```"
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
                    # Using print_error for stderr from shell, but maybe too much if it's just a warning
                    # Keep as is for now, can be refined if too verbose.
                    print_error(result.stderr, title=f"Shell Command Error ({shell_cmd_list[0]})")
            except FileNotFoundError:
                print_error(f"Command not found: `{shell_cmd_list[0]}`", title="Shell Command Error")
            except Exception as e:
                print_error(f"Failed to execute shell command: {e}", title="Shell Command Error")
            continue
        # Handle all tool commands starting with '/'
        if query.strip().startswith("/"):
            # Use regex to robustly match /read <filepath> (with or without quotes, and with spaces)
            import re as _re
            read_match = _re.match(r"^/read\s+(['\"]?)(.+?)\1\s*$", query.strip())
            if read_match:
                filepath = read_match.group(2)
                if not filepath:
                    print_error("No file path provided for `/read` command.", title="Command Error")
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
                console.print(Panel(Markdown(HELP_TEXT), title="[bold cyan]Help & Commands[/bold cyan]", border_style="cyan", expand=False))
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
                        print_error(err, title="Ollama Error")
                        continue
                    if new_model not in models:
                        print_error(f"Model [bold]'{new_model}'[/bold] not found. Please add it using `ollama pull {new_model}` and try again.", title="Model Not Found")
                        continue
                    save_model_choice(new_model)
                    console.print(f"✅ [green]Model updated from '{current_model}' to '{new_model}'.[/green]")
                    selected_model = new_model
                else:
                    # Show current and available models
                    models, err = model_mod.get_ollama_models()
                    if err:
                        print_error(err, title="Ollama Error")
                        continue
                    console.print(f"[cyan]Current model:[/cyan] {selected_model}")
                    console.print("[cyan]Available models:[/cyan]\n - " + "\n - ".join(models))
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
            print_error(f"Unknown tool command: `{cmd[0]}`\nType `/helpme` to see available commands.", title="Command Error")
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
                    print_error(result.stderr.strip(), title=f"Shell Command Error ({shell_cmd_list[0]})")
            except FileNotFoundError:
                 print_error(f"Command not found: `{shell_cmd_list[0]}`", title="Shell Command Error")
            except Exception as e:
                print_error(f"Failed to execute shell command: {e}", title="Shell Command Error")
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
                print_error("No file path provided for `/read` command.", title="Command Error")
                continue
            read_file_content(filepath)
            console.print(f"✅ [yellow]Finished reading {filepath}. Do you need any assistance with this file? (yes/no)[/yellow]")
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
                    last_thinking = summarize_response(response) # response is str
                except Exception as e:
                    print_error(f"Ollama model query failed: {e}\nPlease ensure Ollama is running and the model (`{selected_model}`) is available.", title="Ollama Query Error")
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
                console.print("[yellow]No previous session files found in `sessions/` directory.[/yellow]") # Info, not error
                continue
            selected = select_session(session_files)
            prev_context = load_session_file(selected) # Errors handled in load_session_file
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
        stages = [
            "[bold cyan]Sending query to model...[/bold cyan]",
            "[bold cyan]Model is processing your request...[/bold cyan]",
            "[bold cyan]Compiling thoughts and insights...[/bold cyan]",
            "[bold cyan]Almost there, fetching results...[/bold cyan]"
        ]
        stage_idx = 0
        last_stage_update_time = time.time()

        with console.status(stages[stage_idx], spinner="dots8") as status: # Using a different spinner
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
                current_time = time.time()
                # Cycle through stages every 2.5 seconds
                if current_time - last_stage_update_time > 2.5:
                    stage_idx = (stage_idx + 1) % len(stages)
                    status.update(stages[stage_idx])
                    last_stage_update_time = current_time
                time.sleep(0.1) # Short sleep to keep loop responsive
            t.join()

            if isinstance(response, Exception):
                print_error(f"Ollama model query failed: {response}\nPlease ensure Ollama is running and the model (`{selected_model}`) is available.", title="Ollama Query Error")
                session.append({"user": query, "response": f"Error: {response}"})
                # Not adding to session_agent.memory here as it expects successful model response string
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
