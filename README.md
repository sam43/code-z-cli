# CodeZ CLI – Your Offline Code Companion

A conversational code assistant for your terminal, powered by local LLMs and enhanced with Rich terminal visuals.

---

## Features
- Conversational REPL with context-aware responses
- Instant interruption (ESC) and responsive UI
- Auto-completion for commands and file paths
- Session management: Save and resume conversations
- File reading: Display code/files with syntax highlighting
- Rich terminal output: Beautiful markdown, code, and panels
- Shell command execution with '!'
- Optional websearch tool

---

## Installation

### 1. Install from PyPI (Recommended)

```bash
pip install codez
```

If you are on macOS and see an error about an externally managed environment, use a virtual environment:

```bash
python3 -m venv ~/codez-venv
source ~/codez-venv/bin/activate
pip install codez
```

### 2. Install Ollama (for local LLM)

Follow instructions at https://ollama.com/download to install Ollama for your platform.

---

## Usage

### Start the CLI

```bash
codez
```

Or, if you prefer to run as a Python module from the project root:

```bash
python -m core.repl
```

### Common Commands
- Ask questions: Type your question and press Enter
- Read a file: `/read <filepath>`
- End session: `/endit` (saves conversation to `/sessions/`)
- Clear screen: `/clear` or `clr`
- List or change model: `/models` or `/model -u <current> <new>`
- Enable/disable tools: `/tools`
- Run shell command: `!ls`, `!pwd`, etc.
- Show help: `/helpme`

### Example
```bash
>>> How do I write a Swift function?
>>> /read ./core/model.py
>>> /endit
```

---

## Session Context
- Previous sessions are automatically loaded as context for better answers.
- Session files are stored in the `sessions/` directory in your project root.

---

## Configuration File Location

CodeZ CLI stores its configuration in a user-specific directory using the [platformdirs](https://pypi.org/project/platformdirs/) standard. The config file is typically located at:

- **macOS/Linux:** `~/.config/codez/config.json`
- **Windows:** `%APPDATA%\codez\config.json`

You do not need to manually create or edit this file; it is managed automatically when you select or change models.

---

## Contextual Memory & Token-Aware History

CodeZ CLI supports robust, token-aware context memory for LLM interactions. The assistant remembers as much of your chat history as fits within a configurable token budget (default: 3000 tokens). This ensures the model answers based on prior conversation, without exceeding the LLM's input limit.

- **Token Budget:** The context window is managed by a token budget, not just a fixed number of turns. Oldest turns are truncated automatically if needed.
- **Configurable:** You can set the token budget via the `CODEZ_MAX_TOKEN_BUDGET` environment variable or by editing the config.
- **Persistence:** By default, session memory is stored in a lightweight SQLite database in the `sessions/` directory. You can disable memory (stateless mode) with a CLI flag.
- **CLI Flags:**
  - `--with-memory` (default): Enable contextual replies (session memory)
  - `--no-memory`: Disable contextual replies (stateless, no chat history)

### Example usage

```bash
codez --no-memory   # Run in stateless mode (no chat history)
codez --with-memory # (default) Use contextual memory for better answers
```

---

## Requirements
- Python 3.8+
- [Ollama](https://ollama.com/) (for local LLM)
- `rich`, `prompt_toolkit`, `platformdirs` (installed automatically)

---

## Contributing
Pull requests and issues are welcome! Please see `docs/TECHNICAL.md` for more details.

---

## License
Apache 2.0

---

## Project Structure

Your project root should look like this:

```
code-z-cli/
├── core/
│   ├── model.py
│   ├── parser.py
│   ├── repl.py
│   ├── stream_utils.py
│   ├── summarizer.py
│   ├── user_config.py
│   └── ...
├── build/
│   └── ios_lang.so
├── sessions/
│   └── session_*.json
├── vendor/
│   ├── tree-sitter-c/
│   └── tree-sitter-swift/
├── docs/
│   └── TECHNICAL.md
├── setup.py
├── pyproject.toml
├── requirements.txt
├── README.md
└── LICENSE
```

- Do NOT include `venv/` in the distributed package.
- Only keep `tree-sitter-*` and `vendor/` if you need them at runtime.
- `sessions/` and `build/` are for runtime and should not be packaged for PyPI.
