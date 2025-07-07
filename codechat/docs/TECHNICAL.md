# Technical Documentation: CodeZ CLI 🧑‍💻

## Overview

CodeZ CLI is a terminal-based conversational AI assistant designed for developers. It leverages local Large Language Models (LLMs) via Ollama to provide a private and offline-capable coding companion. The tool features a Rich-enhanced terminal interface, context-aware conversations, session management, file reading capabilities, and specialized code parsing for certain languages.

---

## Core Architecture 🏗️

The application is structured around a modular design. Understanding the entry points and CLI components is key:

*   **Entry Points & Execution Flow**:
    *   **Development (Recommended for REPL):** The `run_codez.sh` script is provided for easily running the interactive chat REPL. It activates a virtual environment (if present) and executes `python cli.py chat`.
    *   **Direct Script Execution:**
        *   `python cli.py [command]`: The root `cli.py` uses `Typer` to define commands (e.g., `chat`, `explain`). `python cli.py chat` launches the interactive REPL.
        *   `python __main__.py`: The root `__main__.py` script also executes the root `cli.py`.
    *   **Packaged Application (`codez` command):** `setup.py` and `pyproject.toml` define `codez = codechat.__main__:main` as the console script entry point. **Note:** Currently, `codechat/__main__.py` does not exist, so the installed `codez` command will not function as specified by these configurations without further changes.
*   **CLI Components**:
    *   **Root `cli.py` (Typer App):** This is the primary command-line interface handler when running from source via `run_codez.sh` or `python cli.py`. It uses `Typer` to parse arguments and dispatch commands. For the `chat` command, it invokes `core.repl.run()`.
    *   **`core.repl.py` (Rich REPL Engine):** Contains the detailed logic for the interactive REPL session, including input handling with `prompt_toolkit`, command processing (slash commands, shell commands), display formatting with `Rich`, and orchestrating calls to the LLM.
    *   **`codechat.interface.cli.CLI`:** This class exists within the `codechat` package. Its `run()` method provides a basic input loop. Its exact role in the current primary application flow initiated by `run_codez.sh` or the root `cli.py` is less direct and might be part of a different or evolving architectural layer.
*   **LLM Interaction (`core.model`)**: Handles communication with the Ollama service.
*   **Code Parsing (`core.parser`)**: Uses `tree-sitter` for advanced parsing (Swift, C/Objective-C) via `ios_lang.so`.
*   **Session Management (`codechat.data.session_repository`, `core.sqlite_memory`)**: Manages conversation history and context.
*   **Rich Terminal Output**: `rich` library is used throughout `core.repl.py` and other components for UI.
*   **Configuration (`core.user_config`)**: Manages user preferences.

---

## Key Technical Features ⚙️

*   **Local LLM Integration**: All AI processing happens locally via Ollama, ensuring code and data privacy.
*   **Contextual Conversations**: Maintains conversation history (token-limited) to provide relevant follow-up responses.
*   **Tree-sitter Based Parsing**: For languages like Swift and C, `core.parser.py` uses `tree-sitter` to parse code into Abstract Syntax Trees (ASTs). This can be used for more precise context extraction or code analysis features.
    *   The shared library `build/ios_lang.so` is loaded by `core.parser.py`. This library is compiled by `build_language_lib.py` using grammars from `vendor/tree-sitter-swift` and `vendor/tree-sitter-c`.
*   **Dynamic Command System**: The CLI supports various slash (`/`) commands and `!` for shell execution.
*   **Session Persistence**: Conversations can be saved and reloaded, allowing users to continue their work across multiple sessions.

---

## Main Components Deep Dive 🔍

### 1. Root `cli.py` (Typer Application)
*   **Location:** Project root (`./cli.py`)
*   **Role:** Defines the command-line structure using `Typer`. It handles initial command parsing (e.g., `chat`, `explain <path>`) and sets up the application environment.
*   For the `chat` command, it calls `core.repl.run()` to start the interactive session.
*   This is the script executed by `run_codez.sh` and when running `python cli.py ...`.

### 2. `core.repl.py` (Rich REPL Engine)
*   **Location:** `./core/repl.py`
*   **Role:** The heart of the interactive chat.
    *   Manages the `prompt_toolkit` session for user input, history, and autocompletion.
    *   Implements the main REPL loop.
    *   Parses and handles slash commands (e.g., `/read`, `/helpme`, `/models`), shell commands (`!cmd`), and multiline code input.
    *   Orchestrates calls to `core.model` for LLM interaction.
    *   Uses `rich` extensively for displaying formatted output, panels, syntax highlighting, etc.
    *   Manages session state and context (partially, with `LLMInteractiveSession`).

### 3. `codechat.interface.cli.CLI`
*   **Location:** `./codechat/interface/cli.py`
*   **Role:** This class provides a simpler CLI loop. It appears to be part of an event-driven architecture (`bus.subscribe`, `bus.publish`) within the `codechat` package.
*   Its direct usage in the primary REPL flow (started by `run_codez.sh` or root `cli.py`) is not immediately apparent and might be intended for a different operational mode or is a remnant of prior architectural iterations. It does not use `Typer` or the extensive `Rich` features seen in `core.repl.py`.

### 4. `core.model`
*   Abstracts Ollama API calls.
*   Fetches available models, sends queries, and processes responses.

### 5. `core.parser`
*   Responsible for loading `tree-sitter` grammars (via `build/ios_lang.so`).
*   Provides functions to parse code strings into ASTs and extract relevant information.

### 6. `run_codez.sh`
*   **Location:** Project root (`./run_codez.sh`)
*   **Role:** A developer convenience script.
    *   Ensures it's executable.
    *   Activates the Python virtual environment (expected at `./venv`).
    *   Runs `python cli.py chat` to start the interactive REPL.

### 7. `build_language_lib.py` & `vendor/`
*   **`build_language_lib.py`**: Utility script to compile `tree-sitter` language grammars from `vendor/` into `build/ios_lang.so`.
*   **`vendor/`**: Contains `tree-sitter` grammar repositories.

### 8. `sessions/` and `core.sqlite_memory.py`
*   **`sessions/`**: Historically used for JSON-based session storage.
*   **`core.sqlite_memory.py`**: Implements more robust session/memory storage using SQLite.

---

## Development & Contribution Guide 🛠️

### Running the Application from Source (Interactive REPL)
The recommended way to run the interactive REPL for development is:
```bash
./run_codez.sh
```
Alternatively, you can directly run:
```bash
python cli.py chat
```
Ensure your virtual environment is activated and dependencies from `requirements.txt` are installed.

### Building `ios_lang.so`
(As previously described)
1.  Ensure C compiler installed.
2.  Run `python build_language_lib.py`.

### Running Tests
(As previously described)
```bash
pytest
```
Or:
```bash
PYTHONPATH=. pytest -s tests/core/test_llm_interactive.py
```

### Adding New Commands or Features
*   **For new REPL slash commands (e.g., `/mynewcommand`):**
    *   Modify `core.repl.py`. Add a new condition to the main input parsing logic to detect your command.
    *   Implement the function/method that executes the command's logic. This might involve adding new helper functions in `core.repl.py` or other `core` modules.
*   **For new top-level Typer commands (e.g., `codez newop`):**
    *   Modify the root `cli.py`. Add a new `@app.command()` decorated function.
*   **Parsing Other Languages**:
    *   (As previously described: Add grammar to `vendor/`, update `build_language_lib.py`, extend `core.parser.py`).

---

## Packaging & Distribution Notes 📦

*   **Dependencies**: `tree-sitter` is a key Python dependency.
*   **`ios_lang.so`**: This compiled library is platform-specific. For widespread, easy distribution on PyPI, platform-specific wheels (e.g., built with `cibuildwheel`) that bundle the correct `.so` file would be necessary. Currently, users or developers might need to build this manually as described above if a pre-built version for their platform is not included or found.
*   **Excluded from Package**: Directories like `venv/`, `.pytest_cache/`, `build/` (if intermediate), and `sessions/` (runtime data) should not be part of the source distribution or wheel, unless `build/ios_lang.so` is being explicitly packaged.

---

## Troubleshooting for Developers 🔩

*   **`ios_lang.so` not found**: Ensure you've run `python build_language_lib.py` and the file exists at the expected path. Check `core/parser.py` for the exact load path.
*   **Tree-sitter errors**: Verify that the `tree-sitter` Python package is installed and that the C compiler is working correctly if building `ios_lang.so`.
*   **Ollama Issues**: Confirm that the Ollama service is running and the desired models are pulled (`ollama list`).

---

For further questions or contributions, please open an issue or pull request on the project repository. Happy Hacking!
```
