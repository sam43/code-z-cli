# core/parser.py
import os
from tree_sitter import Language, Parser

# Determine the project root directory from the location of parser.py
# parser.py is in core/, so project_root is one level up.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
IOS_LANG_SO_PATH = os.path.join(PROJECT_ROOT, 'build', 'ios_lang.so')

LANGUAGES = {
    "swift": IOS_LANG_SO_PATH,
    "objc": IOS_LANG_SO_PATH,
}

def load_parser(language: str):
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

    functions = []
    for node in root.walk():
        if node.type in ["function_declaration", "function_definition"]:
            start = node.start_byte
            end = node.end_byte
            functions.append(code[start:end])
    return functions
