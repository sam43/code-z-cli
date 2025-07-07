#!/bin/bash
# build_grammars.sh - Build all tree-sitter language .so files into build/
# Run from the project root.

set -e

BUILD_DIR="$(cd "$(dirname "$0")" && pwd)/build"
mkdir -p "$BUILD_DIR"
ORIG_DIR="$(pwd)"

# Dynamically build the LANGS array from .gitmodules
LANGS=()
while IFS= read -r line; do
    if [[ $line == *"path = vendor/"* ]]; then
        path=$(echo "$line" | awk '{print $3}')
        name=$(basename "$path" | sed 's/tree-sitter-//' | tr '-' '_')
        LANGS+=("$path ${name}_lang.so")
    fi
done < ".gitmodules"

for entry in "${LANGS[@]}"; do
    read -r lang_path so_name <<< "$entry"
    echo "Building $so_name from $lang_path"
    
    cd "$lang_path"
    if [ ! -f "src/parser.c" ]; then
        echo "src/parser.c not found in $lang_path. Skipping..."
        cd "$ORIG_DIR"
        continue
    fi

    if [ "$lang_path" == "vendor/tree-sitter-swift" ]; then
        echo "Skipping $lang_path as it requires npm installation"
        cd "$ORIG_DIR"
        continue
    fi

    if [ -f "Makefile" ]; then
        make
    fi

    gcc -c -I./src -I. src/parser.c
    gcc -shared -o "$BUILD_DIR/$so_name" parser.o
    rm parser.o
    cd "$ORIG_DIR"
    echo "Built $so_name successfully."
done
echo "All grammars built successfully."

# Build grammar.js for all tree-sitter grammars in vendor/
VENDOR_DIR="vendor"

for dir in "$VENDOR_DIR"/*; do
  # Only process if directory exists and is a grammar (has package.json and src/)
  if [ -d "$dir" ] && [ -f "$dir/package.json" ] && [ -d "$dir/src" ]; then
    echo "Building grammar.js in $dir"
    (cd "$dir" && npm install && npx tree-sitter generate)
    if [ -f "$dir/grammar.js" ]; then
      echo "[OK] $dir/grammar.js built."
    else
      echo "[WARN] $dir/grammar.js not found after build!"
    fi
  else
    echo "[SKIP] $dir is not a tree-sitter grammar (missing src/ or package.json)."
  fi
done

echo "All available grammars processed."
