# core/parser.py
import os
from tree_sitter import Language, Parser
import os

# Map language names to their .so grammar files and tree-sitter language names
LANGUAGES = {
#     "swift": IOS_LANG_SO_PATH,
#     "objc": IOS_LANG_SO_PATH,
# }
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
    lang_so_path = LANGUAGES.get(language)
    if not lang_so_path:
        # This case should ideally not be hit if LANGUAGES dict is correct
        # and language is validated before calling.
        print(f"Error: Language '{language}' not configured for parsing.")
        return None

    if not os.path.exists(lang_so_path):
        print(f"Error: Tree-sitter library not found at {lang_so_path}.")
        print(f"Please build it using: python build_language_lib.py")
        return None

    try:
        parser.set_language(Language(lang_so_path, language))
        return parser
    except OSError as e:
        print(f"Error loading tree-sitter library for {language} from {lang_so_path}: {e}")
        print(f"Ensure the library is compiled for your current OS/architecture.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while loading parser for {language}: {e}")
        return None
    parser.set_language(Language(so_path, ts_lang))
    return parser

def extract_functions(code: str, language: str = "swift"):
    parser = load_parser(language)
    if parser is None:
        print(f"Could not initialize parser for language '{language}'. Aborting function extraction.")
        return [] # Return empty list or handle error as appropriate

    try:
        tree = parser.parse(bytes(code, "utf8"))
        root = tree.root_node
    except Exception as e:
        print(f"Error during parsing or walking the tree for language '{language}': {e}")
        return []
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
