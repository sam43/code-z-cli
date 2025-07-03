# CodeChat CLI

A conversational code assistant for your terminal, powered by local LLMs and enhanced with Rich terminal visuals.

---

## Features
- **Conversational REPL** with context-aware responses
- **Session management**: Save and resume conversations
- **File reading**: Display code/files with syntax highlighting
- **Rich terminal output**: Beautiful markdown, code, and panels

---

## Installation

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd code-chat-cli
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
# Or, manually:
pip install rich
```

### 3. Install Ollama (for local LLM)
Follow instructions at https://ollama.com/download to install Ollama for your platform.

---

## Usage

### Start the CLI
```bash
python -m codechat.core.repl
```

### Commands
- **Ask questions**: Type your question and press Enter.
- **Read a file**: `/read <filepath>`
- **End session**: `/endit` (saves conversation to `/user-sessions/`)
- **/clear** or **clr**: Clear the terminal screen for more space

### Example
```bash
>>> How do I write a Python function?
>>> /read ./core/model.py
>>> /endit
```

---

## Standalone Usage

After installing, you can launch CodeChat CLI from anywhere:

```bash
codechat
```

Or, if you prefer to run as a Python module:

```bash
python -m codechat
```

## Installation (as a package)

Clone the repository and install with pip:

```bash
git clone <your-repo-url>
cd code-chat-cli
pip install .
```

This will install all dependencies and add the `codechat` command to your PATH.

---

## Session Context
- Previous sessions are automatically loaded as context for better answers.
- Session files are stored in `/user-sessions/`.

---

## Requirements
- Python 3.8+
- [Ollama](https://ollama.com/) (for local LLM)
- `rich` Python package

---

## Contributing
Pull requests and issues are welcome!

---

## License
MIT
