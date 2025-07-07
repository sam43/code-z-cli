#!/bin/bash
# update_submodules.sh - Pull and update all git submodules to their designated directories
# Run from the project root.

set -e

echo "Initializing and updating all submodules..."
git submodule sync
# This will initialize, clone, and update all submodules recursively
# and ensure they are in the correct directories as per .gitmodules
git submodule update --init --recursive --remote

echo "All submodules pulled and updated to their designated directories."
