# core/repl.py

import json
import os
import difflib
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
from core.licensing import is_pro_license_active, activate_pro_license, deactivate_pro_license, get_license_status_message # Updated imports
from core.model import fetch_webpage
import time
from datetime import datetime
from rich.text import Text
from pyfiglet import Figlet
import subprocess

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
- [bold blue]/pull_model <model_name>[/bold blue]: Download a model via Ollama (e.g., /pull_model llama3)
- [bold blue]/debug_code [filepath][/bold blue]: Debug a code snippet or file, with an optional error message.
- [bold blue]/gen_doc [filepath][/bold blue]: Generate a docstring for a code snippet or file.
- [bold blue]/suggest_refactor [filepath] (Pro)[/bold blue]: Get suggestions for refactoring a code snippet or file.
- [bold blue]/analyze_performance [filepath][/bold blue]: Static analysis for performance issues in code/file.
- [bold blue]/gen_tests [filepath] (Pro)[/bold blue]: Generate example test cases for a code snippet or file.
- [bold blue]/apply_patch <filepath>[/bold blue]: Interactively apply new content to a file, showing a diff.
- [bold blue]/activate_license <key>[/bold blue]: Activate your Pro license key.
- [bold blue]/deactivate_license[/bold blue]: Deactivate the current Pro license.
- [bold blue]/license_status[/bold blue]: Check the current Pro license status.
- [bold blue]/index_project [path][/bold blue]: Perform a basic scan of a project directory (lists files).
- [bold blue]/execute_code_suggestion (Conceptual)[/bold blue]: Simulate LLM-suggested code execution.
- [bold blue]'!'[/bold blue]: Run shell commands starting with '!' (e.g., !ls, !pwd)
'''

read_file_cache = {}
SESSIONS_PROJECT_INDEX = None # Will store {"path": str, "summary": str}

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
    models_details, err = model_mod.get_ollama_models()
    saved_model = load_model_choice()
    selected_model = None
    available_model_names = []

    if err:
        print_error(err, title="Ollama Error")
        # Allow to proceed if ollama is not installed, user might want to use /pull_model or only non-LLM features
        console.print("[yellow]Ollama is not available. Some features will be limited. You can try `/pull_model` if Ollama is installed but was not running.[/yellow]")

    if models_details: # Check if models_details is not None and not empty
        available_model_names = [m.get("name") for m in models_details if m.get("name")]

    if not available_model_names and not err: # No models, but ollama command worked
        default_suggestion = "llama3" # A common, good default model
        print_error(
            f"No models found locally via Ollama. You can download models using the `/pull_model <model_name>` command.\n"
            f"For example, try: `/pull_model {default_suggestion}`",
            title="Ollama - No Models Found"
        )
        # No return here, allow user to use /pull_model

    if available_model_names: # Only proceed with selection if models are available
        if saved_model and saved_model in available_model_names:
            selected_model = saved_model
            console.print(f"✅ [green]Using saved model:[/green] {selected_model}")
        else:
            console.print("[cyan]Available models:[/cyan]\n - " + "\n - ".join(available_model_names))
            # Create choices for Prompt.ask from available_model_names
            prompt_choices = available_model_names if available_model_names else []
            default_choice = "deepseek-r1:latest" if "deepseek-r1:latest" in available_model_names else (prompt_choices[0] if prompt_choices else None)

            if not default_choice and not prompt_choices: # No models to choose from
                 print_error(f"No models available to select. Please use `/pull_model <model_name>`.", title="Model Selection Error")
                 # selected_model remains None
            elif default_choice: # Only ask if there are choices
                selected_model = Prompt.ask(
                    "[bold blue]Enter model name[/bold blue]",
                    choices=prompt_choices,
                    default=default_choice
                ).strip()

                if not selected_model and default_choice: # User just pressed Enter
                    selected_model = default_choice

                if selected_model and selected_model not in available_model_names: # Should not happen with Prompt.ask choices
                    print_error(f"Selected model [bold]'{selected_model}'[/bold] is not available. Please choose from the list.", title="Model Not Found")
                    return # Critical error, cannot proceed without a valid model if user tried to select one.

            if selected_model: # If a model was successfully selected
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

    if not selected_model and available_model_names: # User had choices but didn't finalize one (e.g. error in prompt logic)
        print_error("No model was ultimately selected. Please try again.", "Model Selection Error")
        return
    elif not selected_model and not available_model_names and not err: # No models were available and Ollama was running
        # Error already printed about no models found and to use /pull_model
        # We can let them proceed to the REPL to use /pull_model
        console.print("\n[yellow]Continuing without a selected LLM. Some features will be disabled.[/yellow]")
        console.print("Use `/pull_model <model_name>` to download a model, then restart or use `/models`.")
    elif not selected_model and err: # Ollama itself had an issue
        # Error already printed by initial Ollama check
        console.print("\n[yellow]Continuing without a selected LLM due to Ollama issues. Some features will be disabled.[/yellow]")
        # User might still want to use REPL for non-Ollama commands if any were added.

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
    session_agent = None
    if selected_model:
        session_agent = LLMInteractiveSession(
            model_name=selected_model,
            persist=with_memory
        )
    else:
        console.print("[dim]LLM session memory disabled as no model is selected.[/dim]")


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
        # Detect code block start for multiline input
        if query.strip() == '```':
            # Call the improved multiline_code_input which expects ``` to start and end
            code = multiline_code_input(prompt_session)
            console.print("✅ [green]Code block captured.[/green]")

            # Ask for follow-up question regarding the code
            followup_prompt_text = "What would you like to ask about this code? (Press Enter to just send the code)"
            followup = prompt_session.prompt(f'{followup_prompt_text}\n>>> ', multiline=False, enable_history_search=True)

            if followup.strip():
                query = f"Here is my code:\n```\n{code}\n```\n\n{followup.strip()}"
            else:
                query = f"Here is my code:\n```\n{code}\n```"
        # Handle shell commands starting with '!'
        if query.strip().startswith("!"):
            # import subprocess # Moved to top-level
            shell_cmd_str = query.strip()[1:]
            if not shell_cmd_str:
                print_error("No shell command provided after '!'", title="Shell Command Error")
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
                    models_details, err = model_mod.get_ollama_models()
                    if err:
                        print_error(err, title="Ollama Error")
                        continue

                    available_model_names = [m.get("name") for m in models_details if m.get("name")]
                    if new_model not in available_model_names:
                        print_error(f"Model [bold]'{new_model}'[/bold] not found locally. Please ensure it's pulled via `ollama pull {new_model}` or use `/pull_model {new_model}`.", title="Model Not Found")
                        continue
                    save_model_choice(new_model)
                    console.print(f"✅ [green]Model updated from '{current_model}' to '{new_model}'.[/green]")
                    selected_model = new_model
                else:
                    # Show current and available models
                    models_details, err = model_mod.get_ollama_models()
                    if err:
                        print_error(err, title="Ollama Error")
                        continue

                    console.print(f"\n[cyan]Current model:[/cyan] [bold white]{selected_model}[/bold white]\n")

                    if not models_details:
                        console.print("[yellow]No models found locally via Ollama.[/yellow]")
                        console.print("You can download models using: /pull_model <model_name>")
                    else:
                        table = Table(title="[bold sky_blue1]Available Ollama Models[/bold sky_blue1]", border_style="sky_blue1", show_lines=True)
                        table.add_column("Name", style="magenta", no_wrap=True)
                        table.add_column("ID", style="cyan", no_wrap=True)
                        table.add_column("Size", style="green", no_wrap=True)
                        table.add_column("Modified", style="yellow", no_wrap=True)

                        for model_info in models_details:
                            table.add_row(
                                model_info.get("name", "N/A"),
                                model_info.get("id", "N/A"),
                                model_info.get("size", "N/A"),
                                model_info.get("modified", "N/A")
                            )
                        console.print(table)
                        console.print("\nTo change model, use `/models -u <current_model_name> <new_model_name>` or restart.")
                        console.print("To download a new model, use `/pull_model <model_name>`.")
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
            if cmd[0] == "/pull_model":
                if len(cmd) > 1:
                    model_to_pull = cmd[1]
                    console.print(f"[cyan]Attempting to pull model '{model_to_pull}' via Ollama. This may take a while...[/cyan]")
                    try:
                        # Using subprocess.Popen to stream output might be better for long pulls,
                        # but for simplicity and immediate feedback, run and wait.
                        # Rich's console.status can be used if we make this threaded.
                        # For now, a simple blocking call with clear messages.
                        process = subprocess.Popen(["ollama", "pull", model_to_pull], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

                        # Stream stdout
                        if process.stdout:
                            for line in iter(process.stdout.readline, ''):
                                console.print(line, end='')
                        process.stdout.close()

                        # Check stderr after stdout is exhausted
                        stderr_output = ""
                        if process.stderr:
                            stderr_output = process.stderr.read()
                            process.stderr.close()

                        return_code = process.wait()

                        if return_code == 0:
                            console.print(f"\n✅ [bold green]Successfully pulled model '{model_to_pull}'.[/bold green]")
                            console.print(f"You can now select it using the `/models` command or by restarting the application.")
                        else:
                            print_error(f"Failed to pull model '{model_to_pull}'. Ollama exit code: {return_code}\n{stderr_output}", title="Model Pull Error")
                    except FileNotFoundError:
                        print_error("Ollama command not found. Please ensure Ollama is installed and in your PATH.", title="Ollama Error")
                    except Exception as e:
                        print_error(f"An error occurred while trying to pull the model: {e}", title="Model Pull Error")
                else:
                    print_error("Usage: `/pull_model <model_name>` (e.g., `/pull_model llama3`)", title="Command Error")
                continue
            # Add more tool commands here as needed
            if cmd[0] == "/debug_code": # Now accepts optional filepath
                if not selected_model:
                    print_error("No LLM model selected. This tool requires a model.", "Tool Error")
                    continue

                code_to_debug = ""
                input_source_description = ""

                if len(cmd) > 1: # Filepath provided
                    filepath_str = cmd[1]
                    filepath = Path(filepath_str).expanduser().resolve()
                    if filepath.exists() and filepath.is_file():
                        try:
                            code_to_debug = filepath.read_text(encoding='utf-8')
                            console.print(f"✅ [green]Using content from file for debugging:[/green] {filepath}")
                            input_source_description = f"file: {filepath}"
                        except Exception as e:
                            print_error(f"Error reading file {filepath}: {e}", "File Read Error")
                            continue
                    else:
                        print_error(f"File not found or is not a regular file: {filepath}", "File Error")
                        continue

                if not code_to_debug: # No filepath or read failed, fallback to snippet
                    console.print("[cyan]Enter the code snippet you want to debug (or type '/cancel_tool'):[/cyan]")
                    code_to_debug = multiline_code_input(prompt_session)
                    if code_to_debug.strip().lower() == "/cancel_tool":
                        console.print("[yellow]Debug tool cancelled.[/yellow]")
                        continue
                    if not code_to_debug.strip():
                        console.print("[yellow]No code provided. Debug tool cancelled.[/yellow]")
                        continue
                    input_source_description = "pasted snippet"

                error_message = Prompt.ask("[cyan]Optional: Enter the error message (or press Enter to skip)[/cyan]", default="").strip()

                system_prompt_debug = (
                    "You are a debugging assistant. Analyze the provided code snippet and error message (if any). "
                    "Explain the error in simple terms, identify the likely cause in the code, and suggest specific fixes or debugging steps. "
                    "Provide corrected code snippets if possible."
                )

                user_content = f"Code to debug:\n```\n{code_to_debug}\n```"
                if error_message:
                    user_content += f"\n\nError message:\n```\n{error_message}\n```"

                full_prompt = f"{system_prompt_debug}\n\n{user_content}"

                with console.status("[bold cyan]Debugger is analyzing your code...[/bold cyan]", spinner="dots8") as status:
                    # Simplified Ollama call for tool, no complex stage cycling here for now
                    debug_response = None
                    try:
                        debug_response = model.query_ollama(full_prompt, selected_model)
                    except Exception as e:
                        print_error(f"Ollama query failed for debug tool: {e}", "Tool Error")
                        continue # to next REPL iteration

                    if debug_response is None: # Should be caught by exception, but as a safeguard
                        print_error("Debugger received no response from the model.", "Tool Error")
                        continue

                console.print("[bold magenta]Debugger Analysis:[/bold magenta]")
                print_llm_response_with_snippets(debug_response)
                session.append({"user": f"/debug_code with content:\n{user_content}", "response": debug_response})
                if session_agent:
                    session_agent.memory.add_turn(f"User (debug tool): {user_content}", debug_response)
                continue

            if cmd[0] == "/gen_doc": # Now accepts optional filepath
                if not selected_model:
                    print_error("No LLM model selected. This tool requires a model.", "Tool Error")
                    continue

                code_for_docstring = ""
                input_source_description = ""

                if len(cmd) > 1: # Filepath provided
                    filepath_str = cmd[1]
                    filepath = Path(filepath_str).expanduser().resolve()
                    if filepath.exists() and filepath.is_file():
                        try:
                            # For docstrings, often a specific function/class is targeted.
                            # Reading the whole file might be too much.
                            # For now, let's keep it simple: if file, use whole content.
                            # Future: allow specifying function/class name within the file.
                            code_for_docstring = filepath.read_text(encoding='utf-8')
                            console.print(f"✅ [green]Using content from file for docstring generation:[/green] {filepath}")
                            input_source_description = f"file: {filepath}"
                        except Exception as e:
                            print_error(f"Error reading file {filepath}: {e}", "File Read Error")
                            continue
                    else:
                        print_error(f"File not found or is not a regular file: {filepath}", "File Error")
                        continue

                if not code_for_docstring: # No filepath or read failed, fallback to snippet
                    console.print("[cyan]Enter the code snippet (e.g., a function or method) for which to generate a docstring (or type '/cancel_tool'):[/cyan]")
                    code_for_docstring = multiline_code_input(prompt_session)
                    if code_for_docstring.strip().lower() == "/cancel_tool":
                        console.print("[yellow]Docstring generator cancelled.[/yellow]")
                        continue
                    if not code_for_docstring.strip():
                        console.print("[yellow]No code provided. Docstring generator cancelled.[/yellow]")
                        continue
                    input_source_description = "pasted snippet"

                # Ask user for docstring format preference (e.g. reStructuredText, Google, NumPy)
                docstring_formats = ["google", "numpy", "reStructuredText (reST)", "epytext", "plaintext"]
                selected_format = Prompt.ask(
                    "[cyan]Choose a docstring format (or type one)[/cyan]",
                    choices=docstring_formats,
                    default="google"
                ).strip()


                system_prompt_docstring = (
                    f"You are a helpful assistant that generates docstrings for code. "
                    f"Analyze the provided code snippet and generate a clear, concise, and accurate docstring for it. "
                    f"The preferred docstring format is: {selected_format}. "
                    f"Ensure the docstring explains the function's purpose, arguments, and what it returns, if applicable."
                )

                user_content = f"Code for docstring generation (format: {selected_format}):\n```\n{code_for_docstring}\n```"
                full_prompt = f"{system_prompt_docstring}\n\n{user_content}"

                with console.status("[bold cyan]Generating docstring...[/bold cyan]", spinner="dots8") as status:
                    docstring_response = None
                    try:
                        docstring_response = model.query_ollama(full_prompt, selected_model)
                    except Exception as e:
                        print_error(f"Ollama query failed for docstring generator: {e}", "Tool Error")
                        continue

                    if docstring_response is None:
                        print_error("Docstring generator received no response from the model.", "Tool Error")
                        continue

                console.print(f"[bold magenta]Generated Docstring ({selected_format}):[/bold magenta]")
                # The response might be just the docstring, or include ```.
                # For now, print as is, assuming LLM provides it well-formatted.
                # We can add stripping of ``` if LLM consistently wraps it.
                print_llm_response_with_snippets(docstring_response)
                session.append({"user": f"/gen_doc with content:\n{user_content}", "response": docstring_response})
                if session_agent:
                    session_agent.memory.add_turn(f"User (docstring tool): {user_content}", docstring_response)
                continue

            if cmd[0] == "/suggest_refactor": # Now accepts optional filepath
                if not is_pro_license_active():
                    print_error(
                        "The `/suggest_refactor` command is a Pro feature. "
                        "Please activate a Pro license to use this tool.\n"
                        "To simulate activation for testing, try the command: `/activate_license CODEZPRO-TEST-DUMY-VALD-PROK`",
                        title="Pro Feature"
                    )
                    continue

                if not selected_model:
                    print_error("No LLM model selected. This tool requires a model.", "Tool Error")
                    continue

                code_to_refactor = ""
                input_source_description = ""

                if len(cmd) > 1: # Filepath provided
                    filepath_str = cmd[1]
                    filepath = Path(filepath_str).expanduser().resolve()
                    if filepath.exists() and filepath.is_file():
                        try:
                            code_to_refactor = filepath.read_text(encoding='utf-8')
                            console.print(f"✅ [green]Using content from file:[/green] {filepath}")
                            input_source_description = f"file: {filepath}"
                        except Exception as e:
                            print_error(f"Error reading file {filepath}: {e}", "File Read Error")
                            continue
                    else:
                        print_error(f"File not found or is not a regular file: {filepath}", "File Error")
                        continue

                if not code_to_refactor: # No filepath provided or file read failed, fallback to snippet
                    console.print("[cyan]Enter the code snippet you want refactoring suggestions for (or type '/cancel_tool'):[/cyan]")
                    code_to_refactor = multiline_code_input(prompt_session)
                    if code_to_refactor.strip().lower() == "/cancel_tool":
                        console.print("[yellow]Refactor suggestion tool cancelled.[/yellow]")
                        continue
                    if not code_to_refactor.strip():
                        console.print("[yellow]No code provided. Refactor suggestion tool cancelled.[/yellow]")
                        continue
                    input_source_description = "pasted snippet"

                # Optional: Ask for focus areas for refactoring
                refactor_focus_options = ["readability", "maintainability", "performance", "general best practices", "custom..."]
                focus_area = Prompt.ask(
                    "[cyan]Any specific focus for refactoring? (e.g., readability, performance, or custom focus)[/cyan]",
                    choices=refactor_focus_options,
                    default="general best practices"
                ).strip()
                if focus_area.lower() == "custom...":
                    focus_area = Prompt.ask("[cyan]Describe your custom refactoring focus:[/cyan]").strip()


                system_prompt_refactor = (
                    "You are an expert code reviewer specializing in refactoring. "
                    "Analyze the provided code snippet. Identify areas for improvement based on the focus: '{focus}'. "
                    "For each suggestion, explain the rationale and provide the refactored code snippet if applicable. "
                    "Prioritize actionable and clear advice."
                ).format(focus=focus_area)

                user_content = f"Code to refactor (focus: {focus_area}):\n```\n{code_to_refactor}\n```"
                full_prompt = f"{system_prompt_refactor}\n\n{user_content}"

                with console.status("[bold cyan]Analyzing code for refactoring opportunities...[/bold cyan]", spinner="dots8") as status:
                    refactor_response = None
                    try:
                        refactor_response = model.query_ollama(full_prompt, selected_model)
                    except Exception as e:
                        print_error(f"Ollama query failed for refactor tool: {e}", "Tool Error")
                        continue

                    if refactor_response is None:
                        print_error("Refactor tool received no response from the model.", "Tool Error")
                        continue

                console.print(f"[bold magenta]Refactoring Suggestions (Focus: {focus_area}):[/bold magenta]")
                print_llm_response_with_snippets(refactor_response)
                session.append({"user": f"/suggest_refactor with content:\n{user_content}", "response": refactor_response})
                if session_agent:
                    session_agent.memory.add_turn(f"User (refactor tool): {user_content}", refactor_response)
                continue

            if cmd[0] == "/execute_code_suggestion": # Placeholder for LLM-suggested execution
                console.print("[bold red]⚠️ WARNING: This is a conceptual placeholder for Interactive Code Execution. ⚠️[/bold red]")
                console.print("[cyan]In a real implementation, code suggested by an LLM would be shown here for approval before safe, sandboxed execution.[/cyan]")
                console.print("[bold yellow]No code will actually be executed by this stub command.[/bold yellow]")

                # This feature would likely be PRO if fully implemented
                # if not is_pro_license_active():
                #      print_error("Interactive code execution would be a Pro feature.", "Pro Feature")
                #      continue

                simulated_llm_code_suggestion = "print(f'Current value of x: {x}')\n# result = my_complex_function(y)"
                console.print(f"\nImagine the LLM suggested executing this Python code to help:\n```python\n{simulated_llm_code_suggestion}\n```")

                if Prompt.ask(f"[bold blue]If this were a real feature, would you approve execution of the above code? (y/n)[/bold blue]", choices=["y", "n"], default="n") == "y":
                    console.print("[green]You approved (simulated).[/green]")
                    console.print("[dim]In a real system, the code would now run in a secure sandbox, and its output (or error) would be captured and could be sent back to the LLM for further analysis.[/dim]")
                else:
                    console.print("[yellow]Execution (simulated) cancelled by user.[/yellow]")
                continue

            if cmd[0] == "/index_project":
                project_path_str = "." # Default to current directory
                if len(cmd) > 1:
                    project_path_str = cmd[1]

                project_path = Path(project_path_str).expanduser().resolve()

                if not project_path.exists() or not project_path.is_dir():
                    print_error(f"Directory not found: {project_path}", title="Project Indexing Error")
                    continue

                console.print(f"[cyan]Starting basic indexing of project at: {project_path}[/cyan]")

                file_list = []
                try:
                    # Recursive scan for this version of the stub
                    with console.status("[yellow]Scanning directory recursively...[/yellow]"):
                        for item_path in project_path.rglob('*'): # rglob for recursive
                            if item_path.is_file():
                                relative_path = item_path.relative_to(project_path)
                                file_list.append(f" (F) {relative_path}")
                            elif item_path.is_dir():
                                relative_path = item_path.relative_to(project_path)
                                file_list.append(f" (D) {relative_path}/") # Add trailing slash for dirs

                    if file_list:
                        # Limit displayed files to avoid flooding console for large projects
                        max_display_files = 50
                        display_list = file_list[:max_display_files]
                        summary_text = f"[bold green]Project Index (Basic File List for {project_path}):[/bold green]\n" + "\n".join(display_list)
                        if len(file_list) > max_display_files:
                            summary_text += f"\n... and {len(file_list) - max_display_files} more items."

                        console.print(Panel(summary_text, title="Project Index Summary", border_style="blue", expand=False))

                        global SESSIONS_PROJECT_INDEX # Defined at top of file for session state
                        SESSIONS_PROJECT_INDEX = {"path": str(project_path), "summary": "\n".join(file_list)} # Store full list
                        console.print("[dim]Basic project index (file list) stored for this session.[/dim]")
                        console.print("[dim]Future: Use `/ask_project <question>` to query using this index.[/dim]")
                    else:
                        console.print(f"[yellow]No files or subdirectories found in {project_path}.[/yellow]")

                except Exception as e:
                    print_error(f"Error during basic project indexing: {e}", title="Project Indexing Error")
                continue

            if cmd[0] == "/execute_code_suggestion": # Placeholder for LLM-suggested execution
                console.print("[bold red]⚠️ WARNING: This is a highly experimental and UNSAFE placeholder. ⚠️[/bold red]")
                console.print("[bold red]It uses `eval()` and should NOT be used with untrusted code.[/bold red]")
                console.print("[cyan]This command simulates executing code that an LLM might suggest.[/cyan]")

                if not is_pro_license_active(): # Potentially a Pro feature
                     print_error("Interactive code execution is a Pro feature. Please activate a license.", "Pro Feature")
                     continue

                code_to_execute = Prompt.ask("[cyan]Enter Python code to execute (UNSAFE!):[/cyan]").strip()
                if not code_to_execute:
                    console.print("[yellow]No code provided.[/yellow]")
                    continue

                if Prompt.ask(f"[bold yellow]Really execute (UNSAFE!):[/bold yellow]\n```python\n{code_to_execute}\n```\nExecute? (y/n)", choices=["y", "n"], default="n") == "y":
                    try:
                        # UNSAFE - FOR DEMONSTRATION OF FLOW ONLY
                        # A real implementation requires a secure sandbox (e.g., Docker, restricted environment)
                        result = eval(code_to_execute, {"__builtins__": {}}, {}) # Extremely restricted eval
                        console.print("[bold green]Execution Result:[/bold green]")
                        console.print(result)
                        # In a real flow, this result would be sent back to the LLM.
                        # session.append({"user": f"/execute_code_suggestion: {code_to_execute}", "response": str(result)})
                        # if session_agent: session_agent.memory.add_turn(...)
                    except Exception as e:
                        print_error(f"Error during execution: {e}", "Execution Error")
                else:
                    console.print("[yellow]Execution cancelled.[/yellow]")
                continue

            if cmd[0] == "/activate_license":
                if len(cmd) > 1:
                    key = cmd[1]
                    success, message = activate_pro_license(key) # From core.licensing
                    if success:
                        console.print(f"✅ [green]{message}[/green]")
                    else:
                        print_error(message, title="License Activation Failed")
                else:
                    print_error("Usage: `/activate_license <license_key>`", title="Command Error")
                continue

            if cmd[0] == "/deactivate_license":
                success, message = deactivate_pro_license()
                if success:
                    console.print(f"✅ [green]{message}[/green]")
                else:
                    print_error(message, title="License Deactivation") # Or just console.print for info
                continue

            if cmd[0] == "/license_status":
                status_message = get_license_status_message()
                console.print(Panel(Markdown(status_message), title="[bold cyan]License Status[/bold cyan]", border_style="cyan", expand=False))
                continue

            if cmd[0] == "/analyze_performance": # Now accepts optional filepath
                if not selected_model:
                    print_error("No LLM model selected. This tool requires a model.", "Tool Error")
                    continue

                code_to_analyze = ""
                input_source_description = ""

                if len(cmd) > 1: # Filepath provided
                    filepath_str = cmd[1]
                    filepath = Path(filepath_str).expanduser().resolve()
                    if filepath.exists() and filepath.is_file():
                        try:
                            code_to_analyze = filepath.read_text(encoding='utf-8')
                            console.print(f"✅ [green]Using content from file for performance analysis:[/green] {filepath}")
                            input_source_description = f"file: {filepath}"
                        except Exception as e:
                            print_error(f"Error reading file {filepath}: {e}", "File Read Error")
                            continue
                    else:
                        print_error(f"File not found or is not a regular file: {filepath}", "File Error")
                        continue

                if not code_to_analyze: # No filepath or read failed, fallback to snippet
                    console.print("[cyan]Enter the code snippet for performance analysis (static analysis based, or type '/cancel_tool'):[/cyan]")
                    code_to_analyze = multiline_code_input(prompt_session)
                    if code_to_analyze.strip().lower() == "/cancel_tool":
                        console.print("[yellow]Performance analysis cancelled.[/yellow]")
                        continue
                    if not code_to_analyze.strip():
                        console.print("[yellow]No code provided. Performance analysis cancelled.[/yellow]")
                        continue
                    input_source_description = "pasted snippet"

                system_prompt_performance = (
                    "You are a code performance analyst. Based on static analysis of the provided code snippet, "
                    "identify potential performance bottlenecks or anti-patterns (e.g., inefficient loops, excessive object creation in loops, "
                    "suboptimal algorithm choice if discernible). Explain why these might be problematic and suggest general optimizations or areas to investigate further. "
                    "Acknowledge that this is static analysis and true performance requires profiling."
                )

                user_content = f"Code for performance analysis:\n```\n{code_to_analyze}\n```"
                full_prompt = f"{system_prompt_performance}\n\n{user_content}"

                with console.status("[bold cyan]Analyzing code for potential performance issues...[/bold cyan]", spinner="dots8") as status:
                    performance_response = None
                    try:
                        performance_response = model.query_ollama(full_prompt, selected_model)
                    except Exception as e:
                        print_error(f"Ollama query failed for performance analysis tool: {e}", "Tool Error")
                        continue

                    if performance_response is None:
                        print_error("Performance analysis tool received no response from the model.", "Tool Error")
                        continue

                console.print("[bold magenta]Performance Analysis (Static):[/bold magenta]")
                print_llm_response_with_snippets(performance_response)
                session.append({"user": f"/analyze_performance with content:\n{user_content}", "response": performance_response})
                if session_agent:
                    session_agent.memory.add_turn(f"User (performance tool): {user_content}", performance_response)
                continue

            if cmd[0] == "/gen_tests": # Now accepts optional filepath
                if not is_pro_license_active():
                    print_error(
                        "The `/gen_tests` command is a Pro feature. "
                        "Please activate a Pro license to use this tool.\n"
                        "To simulate activation for testing, try the command: `/activate_license CODEZPRO-TEST-DUMY-VALD-PROK`",
                        title="Pro Feature"
                    )
                    continue

                if not selected_model:
                    print_error("No LLM model selected. This tool requires a model.", "Tool Error")
                    continue

                code_for_tests = ""
                input_source_description = ""

                if len(cmd) > 1: # Filepath provided
                    filepath_str = cmd[1]
                    filepath = Path(filepath_str).expanduser().resolve()
                    if filepath.exists() and filepath.is_file():
                        try:
                            code_for_tests = filepath.read_text(encoding='utf-8')
                            console.print(f"✅ [green]Using content from file for test generation:[/green] {filepath}")
                            input_source_description = f"file: {filepath}"
                        except Exception as e:
                            print_error(f"Error reading file {filepath}: {e}", "File Read Error")
                            continue
                    else:
                        print_error(f"File not found or is not a regular file: {filepath}", "File Error")
                        continue

                if not code_for_tests: # No filepath or read failed, fallback to snippet
                    console.print("[cyan]Enter the code snippet (e.g., a function) for which to generate test cases (or type '/cancel_tool'):[/cyan]")
                    code_for_tests = multiline_code_input(prompt_session)
                    if code_for_tests.strip().lower() == "/cancel_tool":
                        console.print("[yellow]Test case generator cancelled.[/yellow]")
                        continue
                    if not code_for_tests.strip():
                        console.print("[yellow]No code provided. Test case generator cancelled.[/yellow]")
                        continue
                    input_source_description = "pasted snippet"

                test_frameworks = ["pytest", "unittest", "text description", "custom..."]
                framework_choice = Prompt.ask(
                    "[cyan]Preferred test framework/style?[/cyan]",
                    choices=test_frameworks,
                    default="pytest"
                ).strip()
                if framework_choice.lower() == "custom...":
                    framework_choice = Prompt.ask("[cyan]Describe your custom test style/framework:[/cyan]").strip()

                system_prompt_tests = (
                    f"You are a test case generation assistant. For the provided code snippet, generate a few example test cases. "
                    f"Cover common scenarios, edge cases, and error conditions if applicable. "
                    f"Format the tests in a style suitable for: {framework_choice}."
                )

                user_content = f"Code for test case generation (framework: {framework_choice}):\n```\n{code_for_tests}\n```"
                full_prompt = f"{system_prompt_tests}\n\n{user_content}"

                with console.status("[bold cyan]Generating test cases...[/bold cyan]", spinner="dots8") as status:
                    tests_response = None
                    try:
                        tests_response = model.query_ollama(full_prompt, selected_model)
                    except Exception as e:
                        print_error(f"Ollama query failed for test case generator: {e}", "Tool Error")
                        continue

                    if tests_response is None:
                        print_error("Test case generator received no response from the model.", "Tool Error")
                        continue

                console.print(f"[bold magenta]Generated Test Cases ({framework_choice}):[/bold magenta]")
                print_llm_response_with_snippets(tests_response) # LLM might return code blocks for tests
                session.append({"user": f"/gen_tests with content:\n{user_content}", "response": tests_response})
                if session_agent:
                    session_agent.memory.add_turn(f"User (test gen tool): {user_content}", tests_response)
                continue

            if cmd[0] == "/apply_patch":
                if len(cmd) < 2:
                    print_error("Usage: `/apply_patch <filepath>`", title="Command Error")
                    continue

                target_filepath_str = cmd[1]
                target_filepath = Path(target_filepath_str).expanduser().resolve()

                if not target_filepath.exists() or not target_filepath.is_file():
                    print_error(f"File not found or is not a regular file: {target_filepath}", title="File Error")
                    continue

                try:
                    original_content = target_filepath.read_text(encoding='utf-8')
                except Exception as e:
                    print_error(f"Error reading file {target_filepath}: {e}", title="File Read Error")
                    continue

                console.print(f"[cyan]Current content of {target_filepath} will be used as the original.[/cyan]")
                console.print("[cyan]Now, please provide the new content for the file below:[/cyan]")
                new_content = multiline_code_input(prompt_session)

                if not new_content.strip() and not original_content.strip(): # Both empty
                    console.print("[yellow]Both original and new content are empty. No changes to apply.[/yellow]")
                    continue
                if new_content.strip() == original_content.strip(): # Content is identical
                    console.print("[yellow]New content is identical to the original. No changes to apply.[/yellow]")
                    continue


                if prompt_for_code_application(console, original_content, new_content, str(target_filepath)):
                    try:
                        # Simple backup
                        backup_filepath = target_filepath.with_suffix(target_filepath.suffix + ".bak")
                        target_filepath.rename(backup_filepath)
                        console.print(f"[dim]Original file backed up to: {backup_filepath}[/dim]")

                        target_filepath.write_text(new_content, encoding='utf-8')
                        console.print(f"✅ [bold green]Changes applied successfully to {target_filepath}.[/bold green]")
                        # Invalidate read_file_cache for this file if it was cached
                        if str(target_filepath) in read_file_cache:
                            del read_file_cache[str(target_filepath)]
                    except Exception as e:
                        print_error(f"Error writing changes to {target_filepath}: {e}", title="File Write Error")
                        # Attempt to restore backup if it exists
                        if backup_filepath.exists():
                            try:
                                backup_filepath.rename(target_filepath)
                                console.print(f"[yellow]Attempted to restore original from backup: {target_filepath}[/yellow]")
                            except Exception as rb_err:
                                print_error(f"Critical error: Could not restore backup for {target_filepath}. Backup is at {backup_filepath}. Error: {rb_err}", "Backup Restore Error")
                # else: Changes were discarded by the user (handled in prompt_for_code_application)
                continue


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
            # import subprocess # Moved to top-level
            if not shell_cmd_str:
                print_error("No shell command provided after '!'", title="Shell Command Error")
                continue
            try:
                shell_cmd_list = shlex.split(shell_cmd_str)
                if not shell_cmd_list: # Handle empty string after shlex.split
                    print_error("No valid shell command provided after '!'", title="Shell Command Error")
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

        if not selected_model: # If no model is selected, skip LLM query part
            console.print("[yellow]No LLM model selected. Cannot process query.[/yellow]")
            console.print("Use `/pull_model <name>`, `/models`, or restart if you have models.")
            continue

        # Build context string from session memory (token-aware, not just last 20 turns)
        context_str = ""
        if session_agent:
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
        if session_agent:
            session_agent.memory.add_turn(query, response)  # Add the turn to memory

# import difflib # Moved to top

# Place this near the top with other function definitions
def filter_thinking_block(response: str) -> str:
    """Remove the <think>...</think> block from the LLM response if present."""
    import re
    pattern = r"(?s)<think>.*?</think>"
    return re.sub(pattern, '', response).strip()

def prompt_for_code_application(console: Console, original_content: str, new_content: str, filepath: str) -> bool:
    """
    Shows a diff of changes and prompts the user for approval to apply them.
    Returns True if approved, False otherwise.
    """
    diff = list(difflib.unified_diff(
        original_content.splitlines(keepends=True),
        new_content.splitlines(keepends=True),
        fromfile=f"a/{filepath}",
        tofile=f"b/{filepath}",
        lineterm=""
    ))

    if not diff:
        console.print("[yellow]No changes detected.[/yellow]")
        return False

    console.print(f"[bold underline]Proposed changes for {filepath}:[/bold underline]")
    for line in diff:
        if line.startswith('+'):
            console.print(f"[green]{line}[/green]", end="")
        elif line.startswith('-'):
            console.print(f"[red]{line}[/red]", end="")
        elif line.startswith('@@'):
            console.print(f"[cyan]{line}[/cyan]", end="")
        else:
            console.print(line, end="")
    console.print() # Newline after diff

    while True:
        choice = Prompt.ask(
            "[bold blue]Apply these changes? (y/n/d/e) [Yes/No/Diff(again)/Edit manually][/bold blue]",
            choices=["y", "n", "d", "e"],
            default="y"
        ).lower()

        if choice == 'y':
            return True
        elif choice == 'n':
            console.print("[yellow]Changes discarded.[/yellow]")
            return False
        elif choice == 'd':
            # Reprint diff
            console.print(f"[bold underline]Proposed changes for {filepath}:[/bold underline]")
            for line_d in diff: # Renamed variable to avoid conflict
                if line_d.startswith('+'):
                    console.print(f"[green]{line_d}[/green]", end="")
                elif line_d.startswith('-'):
                    console.print(f"[red]{line_d}[/red]", end="")
                elif line_d.startswith('@@'):
                    console.print(f"[cyan]{line_d}[/cyan]", end="")
                else:
                    console.print(line_d, end="")
            console.print()
        elif choice == 'e':
            console.print("[yellow]Manual edit not implemented in this version. Discarding changes.[/yellow]")
            # In a future version, this could open new_content in an editor or allow line-by-line edits.
            return False

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
