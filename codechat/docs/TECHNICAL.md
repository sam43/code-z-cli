# Technical Documentation: CodeZ CLI 🧑‍💻

## Overview

CodeZ CLI is a terminal-based conversational AI assistant designed for developers. It leverages local Large Language Models (LLMs) via Ollama to provide a private and offline-capable coding companion. The tool features a Rich-enhanced terminal interface, context-aware conversations, session management, file reading capabilities, and specialized code parsing for certain languages.

---

## Core Architecture 🏗️

The application is structured around a modular design:

*   **Entry Point (`codechat.__main__`)**: Initializes and runs the command-line interface.
*   **CLI Interface (`codechat.interface.cli.CLI`)**: Manages the main REPL loop, user interactions, command dispatching, and orchestrates calls to various services. This is the primary interaction hub.
*   **LLM Interaction (`core.model`)**: Handles communication with the Ollama service, sending prompts and receiving responses from the local LLM.
*   **Code Parsing (`core.parser`)**:
    *   Utilizes the `tree-sitter` library for advanced parsing of specific languages (currently Swift and C/Objective-C).
    *   Depends on a compiled shared library (`ios_lang.so`) which is built from language grammars located in the `vendor/` directory.
*   **Session Management (`codechat.data.session_repository`, `core.sqlite_memory`)**:
    *   Persists conversation history to enable context carry-over between sessions.
    *   Older versions used JSON files in `sessions/`; newer implementations use an SQLite database for more robust session and memory management.
*   **Rich Terminal Output**: Employs the `rich` library extensively for styled text, syntax highlighting, markdown rendering, and interactive prompts, ensuring a user-friendly terminal experience.
*   **Configuration (`core.user_config`)**: Manages user preferences, such as the selected Ollama model, using `platformdirs` to store configuration files in standard user-specific locations.

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

### 1. `codechat.interface.cli.CLI`
*   The modern entry point for user interaction.
*   Manages the `prompt_toolkit` session for input.
*   Parses user input into commands or LLM queries.
*   Delegates to other components for specific tasks (LLM queries, file reading, etc.).

### 2. `core.model`
*   Abstracts Ollama API calls.
*   Fetches available models, sends queries, and processes responses.

### 3. `core.parser`
*   Responsible for loading `tree-sitter` grammars (via `build/ios_lang.so`).
*   Provides functions to parse code strings into ASTs and extract relevant information (e.g., function definitions).
*   Crucial for features that require deep code understanding.

### 4. `core.repl.py` (Legacy & Core Logic)
*   While `codechat.interface.cli.CLI` is the main interface, `core.repl.py` contains significant logic for the REPL behavior, command handling, and interaction flows that are utilized by or were foundational to the current CLI. Many helper functions for session management, output formatting, and command execution reside here.

### 5. `build_language_lib.py` & `vendor/`
*   **`build_language_lib.py`**: A utility script that uses `tree-sitter` to compile language grammars into a shared library (`.so` or `.dylib` or `.dll` depending on OS). Currently, it builds `build/ios_lang.so` from grammars in `vendor/tree-sitter-swift` and `vendor/tree-sitter-c`.
*   **`vendor/`**: Contains the `tree-sitter` grammar repositories for languages CodeZ CLI aims to parse with `tree-sitter`. These are essential for running `build_language_lib.py`.

### 6. `sessions/` and `core.sqlite_memory.py`
*   **`sessions/`**: Historically used for storing session data as JSON files. May still be used or referenced for legacy session data.
*   **`core.sqlite_memory.py`**: Implements session and long-term memory storage using an SQLite database, offering more structured and efficient context management.

---

## Development & Contribution Guide 🛠️

### Building `ios_lang.so`
To enable or test features relying on Swift/C parsing:
1.  Ensure you have a C compiler installed on your system.
2.  Run the build script from the project root:
    ```bash
    python build_language_lib.py
    ```
    This will generate `build/ios_lang.so`. The application expects this file to be present at `./build/ios_lang.so` relative to the location of `core/parser.py` (which effectively means `project_root/build/ios_lang.so` when running from the project root).

### Running Tests
Use `pytest`:
```bash
pytest
```
Or, for specific files with more output:
```bash
PYTHONPATH=. pytest -s tests/core/test_llm_interactive.py
```

### Adding New Commands or Features
1.  **CLI Commands**: Modify `codechat.interface.cli.CLI` to recognize new commands. Implement the command's logic, potentially by adding new methods to `CLI` or new functions in relevant `core` modules.
2.  **Parsing Other Languages**:
    *   Add the `tree-sitter` grammar for the new language to the `vendor/` directory.
    *   Update `build_language_lib.py` to include the new grammar in the compilation process.
    *   Extend `core.parser.py` to load and use the new language grammar.

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
