# core/repl.py
from pathlib import Path

tips = [
    "[bold blue]/read <filepath>[/bold blue] — Load a file's content into the conversation.",
    "[bold blue]!ls[/bold blue] or any shell command — Run directly in the prompt!",
    "[bold blue]/models[/bold blue] — See available LLMs or switch to a different one.",
    "[bold blue]/forget_session[/bold blue] — Clear your conversation history/context.",
    "[bold blue]```[/bold blue] — Enter code blocks by typing triple backticks, then paste/type code, then triple backticks again.",
    "[bold blue]/helpme or /? [/bold blue] — Access help anytime.",
    "[bold blue]/tools[/bold blue] — Toggle features like web search (if available).",
    "[bold blue]/mode <ask|build>[/bold blue] — Instantly switch between Q&A and code editing modes.",
    "[bold blue]/load_session[/bold blue] — Resume or load previous sessions.",
    "[bold blue]/clear[/bold blue] or [bold blue]clr[/bold blue] — Clear the terminal for more space.",
    "All output is rendered with beautiful markdown, code highlighting, and panels.",
    "Paste or type multiline code blocks easily using triple backticks.",
    "Your code never leaves your machine—100% privacy with local LLMs.",
    "Analyze code in Python, Swift, C, Java, JS, and more (tree-sitter powered)."
]

import json
import os
from core import model
from core.mode_manager import ModeManager, FileChange
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
from codechat.version_utils import get_version
from core.system_prompts import system_prompt_agent, system_prompt_ask

console = Console()

def print_error(message: str, title: str = "Error"):
    """Prints a Rich Panel formatted error message."""
    console.print(Panel(Markdown(message), title=f"[bold red]{title}[/bold red]", border_style="red", expand=False))

def get_system_prompt_for_mode(mode: str) -> str:
    """Returns the appropriate system prompt based on the selected mode."""
    if mode.lower() == "ask":
        return system_prompt_ask
    elif mode.lower() == "build":
        return system_prompt_agent
    else:
        # Default to build mode if an invalid mode is somehow set
        return system_prompt_agent

# TOOLS update for /process
TOOLS = {
    "websearch": False,
    "process": False
}

HELP_TEXT = """[bold cyan]🚀 CodeZ CLI — Command Reference[/bold cyan]

[bold green]General:[/bold green]
  [bold blue]/helpme or '/?'[/bold blue]         Show this help message
  [bold blue]'exit' or 'bye' [/bold blue]          End the session and save conversation
  [bold blue]/clear[/bold blue], [bold blue]clr[/bold blue]  Clear the terminal screen
  [bold blue]exit[/bold blue], [bold blue]'bye'[/bold blue]   Exit the REPL

[bold green]Session & Context:[/bold green]
  [bold blue]/load_session[/bold blue]   List and load a previous session as context
  [bold blue]/forget_session[/bold blue] Forget the currently loaded session context

[bold green]AI & Tools:[/bold green]
  [bold blue]/mode <ask|build>[/bold blue]   Switch between 'ask' (Q&A) and 'build' (code editing/debug) modes
  [bold blue]/models[/bold blue]            Show or update the selected model
  [bold blue]/tools[/bold blue]             Enable or disable optional tools (e.g., websearch)
  [bold blue]/summarize[/bold blue]         Analyze the project and generate a markdown summary report

[bold green]Code & Files:[/bold green]
  [bold blue]/read <filepath>[/bold blue]   Read and display a file with syntax highlighting
  [bold blue]```[/bold blue]                Start multiline code input (type ``` again to finish)

[bold green]Shell:[/bold green]
  [bold blue]!<command>[/bold blue]         Run shell commands directly (e.g., !ls, !pwd)

[dim]Tip: Type /helpme or '/?' at any time to see this list. For more features, see the welcome message or documentation.[/dim]
"""

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
        __version__ = get_version()
    except Exception:
        __version__ = "unknown"
    try:
        f = Figlet(font='standard')  # 'slant' or 'standard' are good choices
        ascii_art_title = f.renderText("CodeZ CLI")

        # Use full bold bright magenta for the ASCII + center it
        console.print(Text(ascii_art_title, style="bold bright_magenta"), justify="center")

        # Tagline and version info
        tagline = Text("CodeZ CLI – When AI Takes a Break, We Don’t!", style="bold green")
        version = Text(f"v{__version__}", style="bold cyan")

        console.print(tagline, justify="center")
        console.print(version, justify="center")

    except Exception as e:
        # Fallback text if Figlet fails
        console.print("[bold bright_magenta]CodeZ CLI[/bold bright_magenta]", justify="center", style="italic")
        console.print("[bold yellow]When AI Takes a Break, We Don’t![/bold yellow]", justify="center")
        console.print(f"[cyan]v{__version__}[/cyan]", justify="center")
        print_error(f"Could not render Figlet title: {e}", "Display Warning")

    # Show welcome message (features) directly after tagline and version
    selected_tip = random.choice(tips)
    key_features = [
        "🗣️ [bold]Conversational AI REPL[/bold]: Chat with your code and get instant, context-aware answers.",
        "🌈 [bold]Rich Terminal UI[/bold]: Beautiful markdown, code highlighting, and interactive panels.",
        "💾 [bold]Session Memory[/bold]: Save, resume, and manage your coding conversations.",
        "⚡ [bold]Shell Power[/bold]: Run shell commands directly in your chat (just start with `!`).",
        "📄 [bold]File Explorer[/bold]: Instantly read and display code with syntax highlighting using `/read <filepath>`.",
        "🤖 [bold]Local LLMs[/bold]: 100% privacy—your code never leaves your machine.",
        "🧠 [bold]Code Analysis[/bold]: Deep code understanding for Python, Swift, C, Java, JS, and more (tree-sitter powered).",
        "🔄 [bold]Mode Switching[/bold]: Instantly toggle between 'Ask' (Q&A) and 'Build' (code editing/debug) modes with `/mode <ask|build>`.",
        "🛠️ [bold]Tool Toggling[/bold]: Enable/disable features like web search on demand with `/tools`.",
        "📝 [bold]Multiline Code Input[/bold]: Paste or type code blocks easily with triple backticks.",
        "📂 [bold]Session Management[/bold]: Load, forget, or clear session context with `/load_session`, `/forget_session`, `/clear`.",
        "✨ [bold]Extensible & Open Source[/bold]: Built for privacy, hackability, and your workflow.",
    ]
    if len(key_features) > 5:
        features_display = '\n'.join(f"*   {f}" for f in key_features[:7]) + "\n*   [dim]see more... (type '/helpme' or '/?')[/dim]"
    else:
        features_display = '\n'.join(f"*   {f}" for f in key_features)

    welcome_message = f"""🧠 [bold green]Welcome - We care about your privacy, you are in control here![/bold green]\n\n[bold cyan]Key Features:[/bold cyan]\n{features_display}\n\n💡 [bold yellow]Tip of the session:[/bold yellow] {selected_tip}\n\nType `/helpme` or `/?` for a full list of commands."""
    welcome_renderable = Text.from_markup(welcome_message)
    console.print(Panel(welcome_renderable, title="[dim]Your AI Coding Assistant[/dim]", border_style="blue", expand=False, padding=(1,2)))
    console.print() # Add a newline after the panel
    # (Removed duplicate tips definition here)
def print_tips():
    """Display all tips in a styled Rich panel."""
    tips_display = '\n'.join(f"[green]•[/green] {tip}" for tip in tips)
    panel = Panel(
        tips_display,
        title="[bold cyan]💡 CodeZ CLI Tips[/bold cyan]",
        border_style="green",
        expand=False,
        padding=(1,2)
    )
    console.print(panel)

    selected_tip = random.choice(tips)

    # Key features (<=5 lines, expandable with 'see more...')
    key_features = [
        "🗣️ [bold]Conversational AI REPL[/bold]: Chat with your code and get instant, context-aware answers.",
        "🌈 [bold]Rich Terminal UI[/bold]: Beautiful markdown, code highlighting, and interactive panels.",
        "💾 [bold]Session Memory[/bold]: Save, resume, and manage your coding conversations.",
        "⚡ [bold]Shell Power[/bold]: Run shell commands directly in your chat (just start with `!`).",
        "📄 [bold]File Explorer[/bold]: Instantly read and display code with syntax highlighting using `/read <filepath>`.",
        "🤖 [bold]Local LLMs[/bold]: 100% privacy—your code never leaves your machine.",
        "🧠 [bold]Code Analysis[/bold]: Deep code understanding for Python, Swift, C, Java, JS, and more (tree-sitter powered).",
        "🔄 [bold]Mode Switching[/bold]: Instantly toggle between 'Ask' (Q&A) and 'Build' (code editing/debug) modes with `/mode <ask|build>`.",
        "🛠️ [bold]Tool Toggling[/bold]: Enable/disable features like web search on demand with `/tools`.",
        "📝 [bold]Multiline Code Input[/bold]: Paste or type code blocks easily with triple backticks.",
        "📂 [bold]Session Management[/bold]: Load, forget, or clear session context with `/load_session`, `/forget_session`, `/clear`.",
        "✨ [bold]Extensible & Open Source[/bold]: Built for privacy, hackability, and your workflow.",
    ]
    # Show only the first 7, then a 'see more...' if needed
    if len(key_features) > 5:
        features_display = '\n'.join(f"*   {f}" for f in key_features[:7]) + "\n*   [dim]see more... (type '/helpme' or '/?')[/dim]"
    else:
        features_display = '\n'.join(f"*   {f}" for f in key_features)

    welcome_message = f"""🧠 [bold green]Welcome - We care about your privacy, you are in control here![/bold green]

    [bold cyan]Key Features:[/bold cyan]
    {features_display}

    💡 [bold yellow]Tip of the session:[/bold yellow] {selected_tip}

    Type `/helpme` or `/?` for a full list of commands.
    """
    # Using Text.from_markup directly to ensure Rich tags are parsed.
    # This will render Rich tags but not Markdown syntax like lists.
    # from rich.text import Text # Already imported at top level
    welcome_renderable = Text.from_markup(welcome_message)
    # Changed panel title to be more subtle as main title is now ASCII art
    console.print(Panel(welcome_renderable, title="[dim]Your AI Coding Assistant[/dim]", border_style="blue", expand=False, padding=(1,2)))
    console.print() # Add a newline after the panel


def run(with_memory=True):
    # --- ModeManager integration ---
    mode_manager = ModeManager()
    # Try to load persistent permissions and pending changes
    import pickle
    PERSIST_PATH = os.path.join(SESSION_DIR, 'mode_manager_state.pkl')
    if os.path.exists(PERSIST_PATH):
        try:
            with open(PERSIST_PATH, 'rb') as f:
                state = pickle.load(f)
                mode_manager.permissions = state.get('permissions', {})
                mode_manager.global_permission = state.get('global_permission', None)
                mode_manager.pending_changes = state.get('pending_changes', [])
        except Exception as e:
            print_error(f"Failed to load ModeManager state: {e}", title="ModeManager Load Error")

    def persist_mode_manager():
        try:
            with open(PERSIST_PATH, 'wb') as f:
                pickle.dump({
                    'permissions': mode_manager.permissions,
                    'global_permission': mode_manager.global_permission,
                    'pending_changes': mode_manager.pending_changes,
                }, f)
        except Exception as e:
            print_error(f"Failed to save ModeManager state: {e}", title="ModeManager Save Error")
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

    # console.print("[bold green]Welcome to CodeZ CLI. Type 'exit' or 'bye' to end session.[/bold green]")
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
    current_mode = "build"  # Default mode

    # Session memory setup
    session_agent = LLMInteractiveSession(
        model_name=selected_model,
        persist=with_memory
    )


    esc_stop = False  # Flag to indicate ESC was pressed to stop all processing
    model_thread = None  # Track the model generation thread
    model_stop_event = None  # Event to signal thread cancellation
    undo_stack = []
    redo_stack = []
    while True:
        try:
            with patch_stdout():
                query = prompt_session.prompt(
                    ">> ",
                    multiline=False,
                    enable_history_search=True,
                    key_bindings=None
                )
        except KeyboardInterrupt:
            # CTRL+C pressed: trigger end/quit command
            console.print("[yellow]Session ended by CTRL+C. Saving context...[/yellow]")
            ensure_session_dir()
            with open(session_file, "w") as f:
                json.dump(session, f, indent=2)
            break
        except EOFError:
            # ESC pressed: stop all processing, clear session state, and return to prompt
            esc_stop = True
            console.print("[cyan]ESC pressed. Stopping all processing and clearing session state. Ready for next command.[/cyan]")
            # Optionally clear session memory/context if desired:
            prev_context = []
            last_thinking = None
            # If a model thread is running, signal it to stop and join
            if model_thread is not None and model_thread.is_alive():
                if model_stop_event is not None:
                    model_stop_event.set()
                model_thread.join(timeout=2)
                model_thread = None
                model_stop_event = None
            continue
        if esc_stop:
            # If ESC was pressed, skip any further processing and reset flag
            esc_stop = False
            continue
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
            if cmd[0] in ("/helpme", "/?"):
                console.print(Panel(HELP_TEXT, title="[bold cyan]Help & Commands[/bold cyan]", border_style="cyan", expand=False))
                continue
            if cmd[0] == "/tips":
                print_tips()
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
            elif cmd[0] == "/mode":
                if len(cmd) < 2:
                    print_error("Usage: /mode <ask|build>", title="Command Error")
                    continue
                new_mode = cmd[1].lower()
                msg = mode_manager.set_mode(new_mode)
                current_mode = new_mode
                persist_mode_manager()
                console.print(msg)
                continue
            elif cmd[0] in ("/fix", "/add", "/remove"):
                if not mode_manager.is_build_mode():
                    console.print("[yellow]Not in build mode. Use /mode build first.[/yellow]")
                    continue
                if len(cmd) < 3:
                    console.print(f"Usage: {cmd[0]} <file> <your request>")
                    continue
                file_path = cmd[1]
                user_request = " ".join(cmd[2:])
                try:
                    orig = open(file_path, encoding="utf-8").read()
                except Exception:
                    orig = ""
                # --- Real LLM-driven code change ---
                # LLM prompt: ask for only the changed code, not markdown or code blocks
                llm_prompt = (
                    f"You are an expert code editor. User request: {user_request}\n"
                    f"Current file content:\n{orig}\n"
                    "Respond with the new file content only, as plain text. Do NOT use markdown or code block formatting."
                )
                try:
                    from core import model as model_mod
                    selected_model = load_model_choice() or "deepseek-r1:latest"
                    new_content = model_mod.query_ollama(llm_prompt, selected_model)
                    # Remove accidental code block markers if present
                    if new_content.strip().startswith("```"):
                        new_content = new_content.strip().lstrip("`python").strip("`").strip()
                except Exception as e:
                    console.print(f"[red]LLM error: {e}. Using fallback stub.[/red]")
                    if cmd[0] == "/fix":
                        new_content = orig + f"\n# FIX REQUEST: {user_request}\n"
                    elif cmd[0] == "/add":
                        new_content = orig + f"\n# ADD REQUEST: {user_request}\n"
                    elif cmd[0] == "/remove":
                        new_content = orig + f"\n# REMOVE REQUEST: {user_request}\n"
                change = FileChange(file_path, orig, new_content, cmd[0][1:])
                mode_manager.add_pending_change(change)
                # Enhanced diff preview with rich
                from rich.syntax import Syntax
                from rich.panel import Panel
                diff = change.get_diff()
                syntax = Syntax(diff, "diff", theme="monokai", line_numbers=False, word_wrap=True)
                console.print(Panel(syntax, title="Diff Preview", border_style="cyan"))
                # --- Inline terminal permission menu ---
                options = [
                    ("accept once", "Accept once"),
                    ("accept all", "Accept all for this file"),
                    ("accept global", "Accept all for all files"),
                    ("reject", "Reject this change"),
                    ("show full", "Show full diff")
                ]
                selected = 0
                while True:
                    console.print("\n[bold cyan]BUILD MODE: Permission Required[/bold cyan]")
                    console.print(f"File: [bold]{file_path}[/bold]  Operation: [bold]{cmd[0][1:]}[/bold]")
                    for idx, (val, label) in enumerate(options):
                        style = "bold cyan" if idx == selected else ""
                        prefix = "→ " if idx == selected else "  "
                        console.print(f"{prefix}[{val}] ", style=style, end="")
                        console.print(label, style=style)
                    console.print("\nUse [bold]up/down[/bold] arrows then [bold]Enter[/bold] to select.")
                    key = console.input("Select option (u/d/Enter): ").strip().lower()
                    if key in ("u", "up") and selected > 0:
                        selected -= 1
                    elif key in ("d", "down") and selected < len(options) - 1:
                        selected += 1
                    elif key == "" or key == "enter":
                        break
                # Hide permission block by clearing screen section
                console.clear()  # Optionally, use console.clear() or print blank lines
                result = options[selected][0]
                allowed, msg = mode_manager.handle_permission_response(result, file_path)
                # --- Logging/audit trail ---
                import datetime
                with open(os.path.join(SESSION_DIR, "edit_audit.log"), "a") as logf:
                    logf.write(f"[{datetime.datetime.now()}] {cmd[0][1:].upper()} {file_path} | {user_request} | {result} | {msg}\n")
                console.print(msg)
                # Autonomous file/folder creation for test tasks
                import re
                def is_test_task(request):
                    return bool(re.search(r"unit test|test case|write test|add test", request, re.I))
                def get_test_file_path(src_path):
                    p = Path(src_path)
                    if p.name.startswith("test_"):
                        return str(p)
                    return str(p.parent / ("test_" + p.name))
                if allowed:
                    # If the user request is for a test, create a test file/folder as needed
                    if is_test_task(user_request):
                        test_file = get_test_file_path(file_path)
                        test_dir = os.path.dirname(test_file)
                        if not os.path.exists(test_dir):
                            os.makedirs(test_dir, exist_ok=True)
                        with open(test_file, "w", encoding="utf-8") as f:
                            f.write(new_content)
                        undo_stack.append(change)
                        persist_mode_manager()
                        console.print(f"[green]New test file created: {test_file}.[/green]")
                        with open(os.path.join(SESSION_DIR, "edit_audit.log"), "a") as logf:
                            logf.write(f"[{datetime.datetime.now()}] CREATED {test_file}\n")
                    elif not os.path.exists(file_path):
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(new_content)
                        undo_stack.append(change)
                        persist_mode_manager()
                        console.print(f"[green]New file created: {file_path}.[/green]")
                        with open(os.path.join(SESSION_DIR, "edit_audit.log"), "a") as logf:
                            logf.write(f"[{datetime.datetime.now()}] CREATED {file_path}\n")
                    elif mode_manager.apply_change(change):
                        undo_stack.append(change)
                        persist_mode_manager()
                        console.print(f"[green]Change applied to {file_path}.[/green]")
                        with open(os.path.join(SESSION_DIR, "edit_audit.log"), "a") as logf:
                            logf.write(f"[{datetime.datetime.now()}] APPLIED {file_path}\n")
                    else:
                        console.print("[red]Permission denied or error applying change.[/red]")
                else:
                    console.print("[yellow]Change not applied.[/yellow]")
                # LLM clarification: if the LLM output contains a special marker, prompt user for more info
                if "[NEED_USER_INPUT]" in new_content:
                    clarification = console.input("[bold yellow]LLM needs more info: Please clarify your request: [/bold yellow]")
                    # Re-run the command with the clarification
                    cmd.append(clarification)
                    continue
                continue
            elif cmd[0] == "/review_changes":
                # List all pending changes
                changes = mode_manager.list_pending_changes()
                if not changes:
                    console.print("[yellow]No pending changes.[/yellow]")
                for idx, ch in enumerate(changes):
                    status = "[green]applied[/green]" if ch.applied else "[red]pending[/red]"
                    console.print(f"[cyan]{idx}.[/cyan] {ch.file_path} [{status}]")
                    diff = ch.get_diff()
                    console.print(Panel(diff[:1000] + ("..." if len(diff) > 1000 else ""), title="Diff Preview"))
                continue
            elif cmd[0] == "/apply_change":
                # /apply_change <idx>
                changes = mode_manager.list_pending_changes()
                if len(cmd) < 2 or not cmd[1].isdigit():
                    console.print("Usage: /apply_change <index>")
                    continue
                idx = int(cmd[1])
                if idx < 0 or idx >= len(changes):
                    console.print("Invalid change index.")
                    continue
                ch = changes[idx]
                if mode_manager.apply_change(ch):
                    undo_stack.append(ch)
                    persist_mode_manager()
                    console.print(f"[green]Change applied to {ch.file_path}.[/green]")
                else:
                    console.print("[red]Change not applied (permission denied or error).[/red]")
                continue
            elif cmd[0] == "/undo_change":
                if not undo_stack:
                    console.print("[yellow]Nothing to undo.[/yellow]")
                    continue
                ch = undo_stack.pop()
                if mode_manager.revert_change(ch):
                    redo_stack.append(ch)
                    persist_mode_manager()
                    console.print(f"[green]Change reverted for {ch.file_path}.[/green]")
                else:
                    console.print("[red]Failed to revert change.[/red]")
                continue
            elif cmd[0] == "/redo_change":
                if not redo_stack:
                    console.print("[yellow]Nothing to redo.[/yellow]")
                    continue
                ch = redo_stack.pop()
                if mode_manager.apply_change(ch):
                    undo_stack.append(ch)
                    persist_mode_manager()
                    console.print(f"[green]Change re-applied to {ch.file_path}.[/green]")
                else:
                    console.print("[red]Failed to re-apply change.[/red]")
                continue
            elif cmd[0] == "/accept_all_changes":
                changes = mode_manager.list_pending_changes()
                for ch in changes:
                    if not ch.applied:
                        mode_manager.apply_change(ch)
                        undo_stack.append(ch)
                persist_mode_manager()
                console.print("[green]All pending changes applied.[/green]")
                continue
            elif cmd[0] == "/summarize":
                try:
                    from core.project_analyzer import ProjectAnalyzer
                    # Support optional directory argument
                    if len(cmd) > 1:
                        target_dir = cmd[1]
                    else:
                        target_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                    target_dir = os.path.abspath(os.path.expanduser(target_dir))
                    if not os.path.isdir(target_dir):
                        print_error(f"Directory not found: {target_dir}", title="Summarize Error")
                        continue
                    project_name = os.path.basename(os.path.normpath(target_dir))
                    reports_dir = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')), 'reports')
                    Path(reports_dir).mkdir(parents=True, exist_ok=True)
                    out_path = os.path.join(reports_dir, f'SUMMARY_{project_name}.md')
                    console.print(f"[cyan]Analyzing project: {target_dir}, please wait...[/cyan]")
                    analyzer = ProjectAnalyzer()
                    summary = analyzer.analyze_directory(target_dir)
                    report = analyzer.generate_summary_report(summary)
                    with open(out_path, 'w', encoding='utf-8') as f:
                        f.write(report)
                    console.print(f"[green]Project summary generated at [bold]{out_path}[/bold].[/green]")
                except Exception as e:
                    print_error(f"Failed to generate project summary: {e}", title="Summarize Error")
                continue
            # Add more tool commands here as needed
            if cmd[0] == "/forget_session":
                prev_context = []
                console.print("[yellow]Previous session context forgotten. You are now starting fresh.[/yellow]")
                continue
            # Unknown tool command
            print_error(f"Unknown tool command: `{cmd[0]}`\nType `/helpme` or `/?` to see available commands.", title="Command Error")
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
        if query.strip().lower() in ["exit", "bye"]:
            persist_mode_manager()
            console.print("[yellow]Session ended. Saving context...[/yellow]")
            ensure_session_dir()
            with open(session_file, "w") as f:
                json.dump(session, f, indent=2)
            break
        if query.strip().startswith("/helpme" or query.strip() == "/?"):
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

            # Get base system prompt based on current mode
            base_system_prompt = get_system_prompt_for_mode(current_mode)

            # Combine base system prompt with websearch instructions
            final_system_prompt = (
                f"{base_system_prompt}\n"
                "If you need more information, you are allowed to use the websearch tool to search the web for relevant content. "
                "Use the websearch tool only if it is enabled by the user."
            )
            full_prompt = f"{final_system_prompt}\n\n{context_str}\nWeb search result: {web_content}\nUser: {query}\nModel:"
        else:
            # Use the base system prompt for the selected mode
            final_system_prompt = get_system_prompt_for_mode(current_mode)
            full_prompt = f"{final_system_prompt}\n\n{context_str}\nUser: {query}\nModel:"
        stages = [
            "[bold cyan]Sending query to model...[/bold cyan]",
            "[bold cyan]Model is processing your request...[/bold cyan]",
            "[bold cyan]Compiling thoughts and insights...[/bold cyan]",
            "[bold cyan]Almost there, fetching results...[/bold cyan]"
        ]
        stage_idx = 0
        last_stage_update_time = time.time()

        import threading
        with console.status(stages[stage_idx], spinner="dots8") as status: # Using a different spinner
            done = False
            response = None
            model_stop_event = threading.Event()  # Event to signal thread cancellation
            def run_model_with_stop():
                nonlocal response, done
                try:
                    # Pass stop_event to model.query_ollama if supported, else check in a loop
                    # Here, we simulate cooperative cancellation by checking the event periodically
                    # If model.query_ollama supports a stop_event, pass it; else, wrap in a loop
                    # For now, we assume model.query_ollama does NOT support stop_event, so we use a workaround
                    # (If model.query_ollama is blocking, true cancellation may require more invasive changes)
                    # This is a best-effort approach
                    def query_with_cancel():
                        # If model.query_ollama is long-running and blocking, this won't interrupt it
                        # If it supports a stop_event, pass it here
                        return model.query_ollama(full_prompt, selected_model)
                    response = query_with_cancel()
                except Exception as e:
                    response = e
                finally:
                    done = True
            model_thread = threading.Thread(target=run_model_with_stop)
            model_thread.start()
            while not done:
                current_time = time.time()
                # Cycle through stages every 2.5 seconds
                if current_time - last_stage_update_time > 2.5:
                    stage_idx = (stage_idx + 1) % len(stages)
                    status.update(stages[stage_idx])
                    last_stage_update_time = current_time
                # If ESC was pressed, signal the thread to stop
                if esc_stop:
                    if model_stop_event is not None:
                        model_stop_event.set()
                    break
                time.sleep(0.1) # Short sleep to keep loop responsive
            # Wait for thread to finish (or timeout if cancelled)
            if model_thread.is_alive():
                model_thread.join(timeout=2)
            model_thread = None
            # If cancelled, skip further processing
            if esc_stop:
                esc_stop = False
                continue
            if isinstance(response, Exception):
                print_error(f"Ollama model query failed: {response}\nPlease ensure Ollama is running and the model (`{selected_model}`) is available.", title="Ollama Query Error")
                session.append({"user": query, "response": f"Error: {response}"})
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
