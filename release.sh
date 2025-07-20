#!/bin/bash
# release.sh - Automate PyPI release for codez-cli
set -e

get_version() {
  version=$(awk '
    /^\[project\]/ { in_project=1; next }
    /^\[/ && in_project { exit }
    in_project && /^version *=/ {
      gsub(/version *= *"/, "")
      gsub(/"/, "")
      print
      exit
    }
  ' pyproject.toml)
  echo "$version"
}

VERSION=$(get_version)

# 1. Update version (manual step)
echo "[!] Make sure you updated version to $VERSION in pyproject.toml!"
read -p "Press Enter to continue if done, or Ctrl+C to abort..."

# 2. Clean previous builds
echo "[+] Cleaning old builds..."
rm -rf dist/ build/ *.egg-info/

# 3. Install build tools
echo "[+] Installing/upgrading build tools..."
pip install --upgrade build twine

# 4. Build distribution
echo "[+] Building package..."
python -m build

# 5. Check distribution
echo "[+] Checking distribution..."
twine check dist/*

# 6. Test installation
echo "[+] Testing package installation..."
python -m venv test_env
source test_env/bin/activate
pip install dist/*.whl --force-reinstall
echo "[+] Installed package contents:"
pip show -f codez-cli
echo "[+] Package location:"
python -c "import codechat; print(codechat.__file__)"
echo "[+] Testing CLI:"
codez --help
deactivate
rm -rf test_env

# 7. Prompt for PyPI upload
read -p "Do you want to upload to PyPI? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "[+] Uploading to PyPI..."
    twine upload dist/*
else
    echo "[!] Skipping PyPI upload."
fi

# 8. Git tag
echo "[+] Creating git tag..."
git tag "v$VERSION"
git push origin "v$VERSION"

echo "[+] Release script complete!"
echo "[!] Next steps:"
echo "    1. Update CHANGELOG.md"
echo "    2. Create a GitHub release"
echo "    3. Update documentation if needed"