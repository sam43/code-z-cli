# 🤖 CodeZ CLI – Your Supercharged Offline Coding Buddy! 🚀

Ever wished you had a coding assistant right in your terminal, one that respects your privacy and works offline? Meet **CodeZ CLI**! 🎉 It's a friendly, conversational code companion powered by local Large Language Models (LLMs) through Ollama, all jazzed up with slick Rich terminal visuals.

Whether you're learning a new language, need a quick code snippet, or want to understand complex code, CodeZ is here to help you out, right from your command line!

---

## ✨ Awesome Features ✨

*   🗣️ **Conversational REPL:** Chat with your code and get context-aware responses.
*   ⚡ **Lightning Fast:** Instant interruption (ESC) and a super responsive UI.
*   ✍️ **Smart Autocompletion:** For commands and file paths, making typing a breeze.
*   💾 **Session Savvy:** Save your chats and resume them later. Never lose a brilliant thought!
*   📄 **File Explorer:** Read and display code or any file with beautiful syntax highlighting.
*   🌈 **Rich & Beautiful:** Enjoy gorgeous markdown, code rendering, and panels in your terminal.
*   셸 **Shell Power:** Run shell commands directly with `!` (e.g., `!ls -la`).
*   🌐 **Web-Savvy (Optional):** Enable a web search tool to pull in external knowledge.
*   🧐 **Code Analysis (Swift/C):** Uses `tree-sitter` for deeper insights into Swift and C codebases (requires a small helper library).

---

## 🚀 Getting Started: Your First Chat in Minutes! 🚀

Ready to team up with CodeZ? Here’s how:

### Step 1: Get Your Local LLM Brain 🧠 (Install Ollama)

CodeZ CLI uses [Ollama](https://ollama.com) to run powerful language models locally on your machine. This means your code and conversations stay private!

*   Head over to [ollama.com/download](https://ollama.com/download) and install it for your operating system (macOS, Linux, Windows).
*   Once installed, pull your favorite model. We recommend starting with one like `llama3` or `mistral`:
    ```bash
    ollama pull llama3
    ```
    (Make sure Ollama is running after installation!)

### Step 2: Install CodeZ CLI 💻

This is as easy as pie! 🥧

```bash
pip install codez-cli
```

*   **For macOS users:** If you see an error about an "externally managed environment," it's best to use a virtual environment:
    ```bash
    python3 -m venv ~/codez-venv
    source ~/codez-venv/bin/activate
    pip install codez-cli
    ```

*   **What about `tree-sitter` and `ios_lang.so`?**
    *   The `pip install` command automatically installs `tree-sitter`, a cool library CodeZ uses for advanced code parsing.
    *   For enhanced understanding of **Swift and C code**, CodeZ uses a special helper library (`ios_lang.so`).
        *   **For most users:** The core features of CodeZ work perfectly without this. If this specific library isn't pre-built for your system yet, you'll still have a fantastic experience! We're working on making this seamless.
        *   **For developers:** If you want to enable this or contribute, you can build it easily! (See the "For Developers 🤓" section below).

---

## 💬 Let's Chat! - Using CodeZ CLI 💬

You're all set! Time to start your first conversation:

### Launch CodeZ:

Just type this in your terminal:

```bash
codez
```

You should see a friendly welcome message! Now, just type your questions or commands.

### Essential Commands (Your Chat Toolkit):

*   **Ask anything:** Just type your question and press Enter.
    ```
    >>> How do I write a "Hello, World!" in Python?
    ```
*   **Read a file:** Get CodeZ to read a file for you.
    ```
    >>> /read path/to/your/file.py
    ```
*   **End your chat:** Ready to wrap up?
    ```
    >>> /endit
    ```
    (This saves your conversation to the `sessions/` directory in your project root – how cool is that?!)
*   **Clear the screen:** Need a fresh slate?
    ```
    >>> /clear  # or just 'clr'
    ```
*   **Choose your LLM:** See available models or switch to a new one.
    ```
    >>> /models
    >>> /model -u current_model new_model
    ```
*   **Toggle tools:** Enable or disable features like web search.
    ```
    >>> /tools
    ```
*   **Run shell commands:** Access your system shell.
    ```
    >>> !ls -l
    >>> !git status
    ```
*   **Need help?** A handy reminder of commands.
    ```
    >>> /helpme
    ```

### Quick Example:

```
>>> What's the syntax for a for-loop in JavaScript?
🤖 CodeZ: [Provides a clear explanation and example]
>>> /read ./my_script.js
🤖 CodeZ: [Displays your script with syntax highlighting] Okay, I've read my_script.js. What would you like to do with it?
>>> Can you explain the main function in this script?
🤖 CodeZ: [Analyzes and explains]
>>> /endit
```

---

## 💪 Superpowers (Advanced Features) 💪

*   🧠 **Contextual Memory:** CodeZ remembers your conversation (within a configurable token budget) to give you smarter, more relevant answers over time. Oldest parts of the chat are gracefully trimmed if needed.
    *   Set your token budget via the `CODEZ_MAX_TOKEN_BUDGET` environment variable or in the config.
    *   Stateless mode is also available: `codez --no-memory`
*   🗂️ **Session Management:** Your conversations are automatically saved! You can even load previous sessions to pick up where you left off or provide more context.
    *   Session files live in the `sessions/` directory (usually in your project's root, or where you run `codez`).
*   ⚙️ **Configuration:** CodeZ stores its settings (like your preferred model) in a user-friendly location:
    *   **macOS/Linux:** `~/.config/codez/config.json`
    *   **Windows:** `%APPDATA%\codez\config.json`
    (Thanks to the [platformdirs](https://pypi.org/project/platformdirs/) library!)

---

## ✅ Requirements Checklist ✅

*   Python 3.8 or newer
*   [Ollama](https://ollama.com/) installed and running with at least one model (e.g., `ollama pull llama3`)
*   The Python packages `rich`, `prompt_toolkit`, `platformdirs`, and `tree-sitter` (these are installed automatically when you `pip install codez-cli`).

---

## 🤓 For Developers & Contributors 🤓

Want to peek under the hood, add new features, or fix a bug? Awesome!

### Setting Up Your Dev Environment:

1.  **Clone the repo:**
    ```bash
    git clone https://github.com/sam43/code-z-cli.git
    cd code-z-cli
    ```
2.  **Create a virtual environment (recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies (including dev tools):**
    ```bash
    pip install -r requirements.txt
    # For editable mode, if you plan to make changes to CodeZ itself:
    pip install -e .
    ```
4.  **Build the `ios_lang.so` (for Swift/C parsing):**
    This step is needed if you want to work on or test the Swift/C advanced parsing features. It requires a C compiler.
    ```bash
    python build_language_lib.py
    ```
    This will create `build/ios_lang.so`. The app looks for it at `./build/ios_lang.so` relative to where `core/parser.py` is.

### Running from Source:

After setup, you can run CodeZ directly:
```bash
python -m codechat
# or
python __main__.py
```

### Running Tests:

We use `pytest` for testing.
```bash
# Install pytest if you haven't already (it's in requirements.txt)
# pip install pytest
pytest
# or for more verbose output / specific tests:
PYTHONPATH=. pytest -s tests/core/test_llm_interactive.py
```

### Project Structure Overview:

```
code-z-cli/
├── codechat/             # Main application package
│   ├── __main__.py       # Main entry point for `python -m codechat`
│   ├── interface/        # CLI interface logic
│   ├── domain/           # Core domain models (e.g., conversation)
│   ├── data/             # Data handling (e.g., session repository)
│   └── docs/             # Contains TECHNICAL.md
├── core/                 # Core logic (LLM interaction, parsing, REPL)
│   ├── model.py          # LLM interaction via Ollama
│   ├── parser.py         # Code parsing (uses tree-sitter)
│   ├── repl.py           # REPL implementation (though CLI() is now the entry)
│   └── ...
├── build/                # Output for compiled libraries like ios_lang.so
├── sessions/             # Stores user conversation sessions (created at runtime)
├── vendor/               # tree-sitter language grammars (used by build_language_lib.py)
├── tests/                # Unit tests
├── build_language_lib.py # Script to build the tree-sitter language library
├── setup.py              # Packaging script
├── pyproject.toml        # Modern Python packaging configuration
├── requirements.txt      # Development dependencies
├── README.md             # This awesome file!
└── LICENSE               # Apache 2.0 License
```
*   **Note on packaging:** `venv/`, `sessions/`, and `build/` directories should not be included in the distributed PyPI package. `vendor/` is needed to build `ios_lang.so` but isn't strictly a runtime dependency for the app *if* `ios_lang.so` is pre-built.

### Want to dive deeper?
Check out the [Technical Documentation](codechat/docs/TECHNICAL.md) for more architectural insights!

---

## 🤝 Join the Adventure! (Contributing) 🤝

CodeZ CLI is an open-source project, and we welcome contributions of all kinds! Whether it's reporting a bug, suggesting a feature, improving documentation, or writing code, your help is appreciated.

*   **Issues:** Found a bug or have an idea? Open an issue!
*   **Pull Requests:** Got a fix or a new feature? Submit a Pull Request!

Let's make CodeZ CLI even more amazing together!

---

## 📜 License 📜

CodeZ CLI is licensed under the Apache 2.0 License. See the [LICENSE](LICENSE) file for details.

---

Happy Coding with your new AI buddy! If you love CodeZ, don't forget to ⭐ the repo!
```
