#!/bin/bash
# update_submodules.sh - Pull and update all git submodules to their designated directories
# Ensures all submodule directories exist as per .gitmodules
# Run from the project root.

set -e

GITMODULES_FILE=".gitmodules"

# Parse .gitmodules for all submodule paths
SUBMODULE_PATHS=$(grep 'path = ' "$GITMODULES_FILE" | awk -F' = ' '{print $2}')

# Create each submodule directory if it doesn't exist
for path in $SUBMODULE_PATHS; do
  if [ ! -d "$path" ]; then
    echo "Creating directory: $path"
    mkdir -p "$path"
  fi
  # Optionally, clean the directory if you want a fresh clone (uncomment below)
  # rm -rf "$path"/*
done

echo "Syncing and updating all submodules..."
git submodule sync
# This will initialize, clone, and update all submodules recursively
# and ensure they are in the correct directories as per .gitmodules
git submodule update --init --recursive --remote

echo "All submodules pulled and updated to their designated directories."
