# build_language_lib.py
import os
import configparser

def get_submodules():
    config = configparser.ConfigParser()
    config.read('.gitmodules')
    return [section.split('"')[1] for section in config.sections()]

LANG_MODULES = get_submodules()
VENDOR_DIR = 'vendor'
BUILD_DIR = 'build'
os.makedirs(BUILD_DIR, exist_ok=True)

missing_grammars = []
built_grammars = []

for lang in LANG_MODULES:
    lang_path = os.path.join(VENDOR_DIR, lang.split('/')[-1])
    parser_c = os.path.join(lang_path, 'src', 'parser.c')
    if not os.path.exists(parser_c):
        print(f"[WARN] Skipping {lang}: missing {parser_c}")
        missing_grammars.append(lang)
        continue
    so_name = f"{lang.split('/')[-1].replace('tree-sitter-', '').replace('-', '_')}.so"
    out_path = os.path.join(BUILD_DIR, so_name)
    print(f"Building {lang} -> {out_path}")
    Language.build_library(
        out_path,
        [lang_path]
    )
    print(f"Built {out_path}")
    built_grammars.append(lang)

print("\nBuild summary:")
print(f"  Built grammars:   {', '.join(built_grammars) if built_grammars else 'None'}")
print(f"  Missing grammars: {', '.join(missing_grammars) if missing_grammars else 'None'}")
print("All available language libraries built successfully in 'build/'.")