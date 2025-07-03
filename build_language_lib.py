# build_language_lib.py
from tree_sitter import Language

Language.build_library(
    'build/ios_lang.so',
    [
        'vendor/tree-sitter-swift',
        'vendor/tree-sitter-c',
    ]
)

print("Language library built successfully at 'build/ios_lang.so'.")