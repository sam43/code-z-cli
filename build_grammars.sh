#!/bin/bash
# build_grammars.sh - Build all tree-sitter language .so files into build/
# Run from the project root.

set -e

BUILD_DIR="$(cd "$(dirname "$0")" && pwd)/build"
mkdir -p "$BUILD_DIR"
ORIG_DIR="$(pwd)"

# List of submodule paths and their output .so names
LANGS=(
  "vendor/tree-sitter-swift ios_lang.so"
  "vendor/py-tree-sitter python_lang.so"
  "vendor/java-tree-sitter java_lang.so"
  "vendor/kotlin-tree-sitter kotlin_lang.so"
  "vendor/tree-sitter-javascript javascript_lang.so"
  "vendor/tree-sitter-typescript/typescript typescript_lang.so"
  "vendor/tree-sitter-go go_lang.so"
  "vendor/tree-sitter-c c_lang.so"
  "vendor/tree-sitter-php php_lang.so"
  "vendor/tree-sitter-rust rust_lang.so"
)

for entry in "${LANGS[@]}"; do
  set -- $entry
  DIR=$1
  OUT=$2
  echo "Building $OUT from $DIR..."
  cd "$ORIG_DIR/$DIR"
  # Build grammar.js if missing and package.json exists
  if [ ! -f grammar.js ] && [ -f package.json ]; then
    echo "[INFO] grammar.js missing in $DIR, running npm install && npx tree-sitter generate"
    npm install && npx tree-sitter generate
  fi
  # Always try to generate parser.c
  tree-sitter generate || { echo "tree-sitter generate failed in $DIR"; cd "$ORIG_DIR"; continue; }
  if [ -f src/scanner.c ]; then
    gcc -shared -o "$BUILD_DIR/$OUT" -fPIC src/parser.c src/scanner.c
  else
    gcc -shared -o "$BUILD_DIR/$OUT" -fPIC src/parser.c
  fi
  cd "$ORIG_DIR" > /dev/null
  echo "Built $BUILD_DIR/$OUT"
done

echo "All grammars built successfully."
