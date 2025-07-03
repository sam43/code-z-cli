# core/parser.py
from tree_sitter import Language, Parser

LANGUAGES = {
    "swift": "./build/ios_lang.so",
    "objc": "./build/ios_lang.so",
}

def load_parser(language: str):
    parser = Parser()
    parser.set_language(Language(LANGUAGES[language], language))
    return parser

def extract_functions(code: str, language: str = "swift"):
    parser = load_parser(language)
    tree = parser.parse(bytes(code, "utf8"))
    root = tree.root_node

    functions = []
    for node in root.walk():
        if node.type in ["function_declaration", "function_definition"]:
            start = node.start_byte
            end = node.end_byte
            functions.append(code[start:end])
    return functions
