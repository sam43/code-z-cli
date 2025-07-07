# core/parser.py
import os
from tree_sitter import Language, Parser
import os

# Determine the project root directory from the location of parser.py
# parser.py is in core/, so project_root is one level up.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BUILD_DIR = os.path.join(PROJECT_ROOT, 'build')

# Build .so paths dynamically
IOS_LANG_SO_PATH = os.path.join(BUILD_DIR, 'ios_lang.so')
JAVA_LANG_SO_PATH = os.path.join(BUILD_DIR, 'java_lang.so')
KOTLIN_LANG_SO_PATH = os.path.join(BUILD_DIR, 'kotlin_lang.so')
PYTHON_LANG_SO_PATH = os.path.join(BUILD_DIR, 'python_lang.so')
JAVASCRIPT_LANG_SO_PATH = os.path.join(BUILD_DIR, 'javascript_lang.so')
TYPESCRIPT_LANG_SO_PATH = os.path.join(BUILD_DIR, 'typescript_lang.so')
GO_LANG_SO_PATH = os.path.join(BUILD_DIR, 'go_lang.so')

# Map language names to their .so grammar files and tree-sitter language names
LANGUAGES = {
    "swift":  (IOS_LANG_SO_PATH, "swift"),
    "objc":   (IOS_LANG_SO_PATH, "objc"),
    "java":   (JAVA_LANG_SO_PATH, "java"),
    "kt":     (KOTLIN_LANG_SO_PATH, "kotlin"),
    "kotlin": (KOTLIN_LANG_SO_PATH, "kotlin"),
    "py":     (PYTHON_LANG_SO_PATH, "python"),
    "python": (PYTHON_LANG_SO_PATH, "python"),
    "js":     (JAVASCRIPT_LANG_SO_PATH, "javascript"),
    "javascript": (JAVASCRIPT_LANG_SO_PATH, "javascript"),
    "ts":     (TYPESCRIPT_LANG_SO_PATH, "typescript"),
    "typescript": (TYPESCRIPT_LANG_SO_PATH, "typescript"),
    "go":     (GO_LANG_SO_PATH, "go"),
}

# Node types for function definitions in each language
FUNCTION_NODE_TYPES = {
    "swift": ["function_declaration"],
    "objc": ["function_definition", "method_definition"],
    "java": ["method_declaration"],
    "kotlin": ["function_declaration"],
    "python": ["function_definition"],
    "javascript": ["function_declaration", "method_definition"],
    "typescript": ["function_declaration", "method_signature"],
    "go": ["function_declaration", "method_declaration"],
}

def detect_language_from_filename(filename: str) -> str:
    """
    Guess the programming language from the file extension.
    """
    ext = os.path.splitext(filename)[1].lower()
    ext_map = {
        ".swift": "swift",
        ".m": "objc",
        ".mm": "objc",
        ".java": "java",
        ".kt": "kotlin",
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
    }
    return ext_map.get(ext, "swift")  # Default to swift if unknown

def load_parser(language: str):
    lang_key = language.lower()
    if lang_key not in LANGUAGES:
        raise ValueError(f"Unsupported language: {language}")
    so_path, ts_lang = LANGUAGES[lang_key]
    if not os.path.exists(so_path):
        raise FileNotFoundError(f"Grammar file not found: {so_path}")
    parser = Parser()
    parser.set_language(Language(so_path, ts_lang))
    return parser

def extract_functions(code: str, language: str = "swift"):
    """
    Extract function definitions from code using tree-sitter.
    Supported languages: swift, objc, java, kotlin, python, javascript, typescript
    """
    lang_key = language.lower()
    parser = load_parser(lang_key)
    tree = parser.parse(bytes(code, "utf8"))
    root = tree.root_node
    node_types = FUNCTION_NODE_TYPES.get(lang_key, ["function_declaration"])
    functions = []

    def walk(node):
        if node.type in node_types:
            start = node.start_byte
            end = node.end_byte
            functions.append(code[start:end])
        for child in node.children:
            walk(child)

    walk(root)
    return functions

def get_missing_grammars():
    """
    Returns a list of submodule directories (from LANGUAGES) that are missing grammar.js.
    """
    missing = []
    for lang, (so_path, ts_lang) in LANGUAGES.items():
        # Guess submodule dir from so_path (assumes vendor/<submodule>)
        parts = os.path.relpath(so_path, PROJECT_ROOT).split(os.sep)
        if len(parts) < 2:
            continue
        submodule_dir = os.path.join(PROJECT_ROOT, 'vendor', f'tree-sitter-{lang}')
        grammar_js = os.path.join(submodule_dir, 'grammar.js')
        if not os.path.exists(grammar_js):
            missing.append((lang, submodule_dir))
    return missing

if __name__ == "__main__":
    missing = get_missing_grammars()
    if missing:
        print("The following grammars are missing grammar.js:")
        for lang, subdir in missing:
            print(f"  - {lang}: {subdir}")
    else:
        print("All required grammar.js files are present.")
