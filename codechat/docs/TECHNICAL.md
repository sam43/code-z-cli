# Technical Documentation: CodeZ CLI

## Overview
CodeZ CLI is a terminal-based conversational assistant for code and text, supporting context-aware responses, session management, and file reading. It leverages local LLMs (via Ollama) and provides a visually rich terminal experience using the Rich library.

---

## Architecture

- **REPL Loop**: Handles user input, command parsing, and output formatting.
- **Model Integration**: Uses `ollama` to run local LLMs for generating responses.
- **Session Management**: Stores each session as a JSON file in `/sessions/` and loads previous session data as context.
- **File Reading**: Supports `/read <filepath>` command to display file contents with syntax highlighting.
- **Rich Integration**: All output (including code, markdown, and panels) is rendered using the Rich library for enhanced readability.

---

## Key Features

- **Concise Responses**: Model output is summarized for brevity.
- **Session Context**: Previous session data is loaded and used as context for new queries.
- **Session End**: Typing `/endit` saves the session and exits.
- **File Reading**: `/read <filepath>` displays file content with syntax highlighting.
- **Terminal Formatting**: Code blocks and markdown are rendered using Rich.

---

## Main Components

### 1. `core/repl.py`
- Main REPL loop, session management, Rich output, and command parsing.
- Loads previous session context from `/sessions/`.
- Handles `/read` command and session saving.

### 2. `core/model.py`
- Wraps calls to the local LLM via `ollama`.
- Optionally strips markdown headers for concise output.

### 3. `sessions/`
- Stores session JSON files, each containing a list of user/model exchanges.
- Used for context in future sessions.

### 4. Rich Integration
- Uses `Console`, `Markdown`, `Syntax`, and `Panel` from Rich for all output.

---

## Extending/Customizing
- Adjust summarization logic in `summarize_response` for more/less detail.
- Change session context loading to use a specific file or more history.
- Add more commands by extending the REPL loop.

---

## Security & Privacy
- All session data is stored locally.
- No data is sent to external servers except via the local LLM backend.

---

## Troubleshooting
- If Rich output is not displayed, ensure the `rich` package is installed in your Python environment.
- If session context is not loaded, check the `/sessions/` directory for valid JSON files.

---

## Contact
For questions or contributions, please open an issue or pull request on the project repository.
