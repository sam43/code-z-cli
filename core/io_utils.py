"""
Input/output utilities for CodeZ CLI REPL.
"""
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from rich.markdown import Markdown
from rich.text import Text

def print_code_snippet(snippet: str, language: str = ""):
    """Print code or text as a formatted snippet in the terminal using Rich."""
    console = Console()
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
    console = Console()
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
