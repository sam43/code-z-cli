#!/bin/bash
# update_submodules.sh - Pull and update all git submodules to their designated directories

set -e

GITMODULES_FILE=".gitmodules"

# Parse .gitmodules for all submodule paths and URLs
while IFS= read -r line; do
    if [[ $line == *"path = "* ]]; then
        path=$(echo "$line" | awk '{print $3}')
    elif [[ $line == *"url = "* ]]; then
        url=$(echo "$line" | awk '{print $3}')
        if [ ! -d "$path" ]; then
            echo "Cloning $url into $path"
            git clone "$url" "$path"
        else
            echo "Updating $path"
            (cd "$path" && git pull origin main)
        fi
    fi
done < "$GITMODULES_FILE"

echo "Syncing and updating all submodules..."
git submodule sync
git submodule update --init --recursive --remote

echo "All submodules pulled and updated to their designated directories."