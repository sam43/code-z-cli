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
pip install codez-cli
```

If you are on macOS and see an error about an externally managed environment, use a virtual environment:

```bash
python3 -m venv ~/codez-venv
source ~/codez-venv/bin/activate
pip install codez-cli
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
python -m codechat
```

Or, you can also run directly:

```bash
python __main__.py
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

## Session Context & Configuration
- Previous sessions are automatically loaded as context for better answers.
- Session files are stored in the `sessions/` directory in your project root.
- Config is stored using [platformdirs](https://pypi.org/project/platformdirs/):
  - macOS/Linux: `~/.config/codez/config.json`
  - Windows: `%APPDATA%\codez\config.json`

---

## Contextual Memory & Token-Aware History
- Remembers as much chat history as fits within a configurable token budget (default: 3000 tokens).
- Oldest turns are truncated automatically if needed.
- Set token budget via `CODEZ_MAX_TOKEN_BUDGET` env var or config.
- Session memory is stored in a lightweight SQLite DB in `sessions/`.
- Stateless mode: `codez --no-memory`
- With memory (default): `codez --with-memory`

---

## Requirements
- Python 3.8+
- [Ollama](https://ollama.com/) (for local LLM)
- `rich`, `prompt_toolkit`, `platformdirs` (installed automatically)

---

## Project Structure

```
code-z-cli/
├── codechat/
│   ├── __main__.py
│   ├── ...
├── core/
│   ├── model.py
│   ├── parser.py
│   ├── repl.py
│   └── ...
├── build/
├── sessions/
├── vendor/
├── docs/
├── setup.py
├── pyproject.toml
├── requirements.txt
├── README.md
└── LICENSE
```
- Do NOT include `venv/` in the distributed package.
- Only keep `tree-sitter-*` and `vendor/` if you need them at runtime.
- `sessions/` and `build/` are for runtime and should not be packaged for PyPI.

---

## Testing
To run all unit tests (requires pytest):
```bash
pip install pytest
pytest
or
PYTHONPATH=. pytest
or specific test file
PYTHONPATH=. pytest -s tests/test_llm_interactive.py
```

---

## Contributing
Pull requests and issues are welcome! See `docs/TECHNICAL.md` for more details.

---

## License
Apache 2.0
