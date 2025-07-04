# core/parser.py
from tree_sitter import Language, Parser
import os

# Map language names to their .so grammar files and tree-sitter language names
LANGUAGES = {
    "swift":  ("./build/ios_lang.so", "swift"),
    "objc":   ("./build/ios_lang.so", "objc"),
    "java":   ("./build/java_lang.so", "java"),
    "kt":     ("./build/kotlin_lang.so", "kotlin"),
    "kotlin": ("./build/kotlin_lang.so", "kotlin"),
    "py":     ("./build/python_lang.so", "python"),
    "python": ("./build/python_lang.so", "python"),
    "js":     ("./build/javascript_lang.so", "javascript"),
    "javascript": ("./build/javascript_lang.so", "javascript"),
    "ts":     ("./build/typescript_lang.so", "typescript"),
    "typescript": ("./build/typescript_lang.so", "typescript"),
    "go":     ("./build/go_lang.so", "go"),
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
        parts = so_path.split('/')
        if len(parts) < 3:
            continue
        submodule_dir = '/'.join(parts[:2])
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
