#!/bin/bash
# release.sh - Automate PyPI release for codez-cli
set -e

VERSION="0.2.0"

# 1. Update version (manual step)
echo "[!] Make sure you updated version to $VERSION in setup.py and pyproject.toml!"
read -p "Press Enter to continue if done, or Ctrl+C to abort..."

# 2. Clean previous builds
echo "[+] Cleaning old builds..."
rm -rf dist/ build/ *.egg-info/

# 3. Build distribution
echo "[+] Installing build tools..."
pip install --upgrade build twine

echo "[+] Building package..."
python3 -m build

# 4. Check distribution
echo "[+] Checking distribution..."
twine check dist/*

# 5. Upload to PyPI
echo "[+] Uploading to PyPI..."
twine upload dist/*

echo "[+] Release script complete!"
echo "[!] Remember to tag the release in git:"
echo "    git tag v$VERSION && git push --tags"
