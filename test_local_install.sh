#!/bin/bash
# test_local_install.sh - Test local install of codez-cli
set -e

PACKAGE_NAME="codez-cli"

# Uninstall if already installed
pip uninstall -y $PACKAGE_NAME || true

# Install from local dist
LATEST_WHL=$(ls dist/*.whl | sort | tail -n 1)
echo "[+] Installing $LATEST_WHL locally..."
pip install "$LATEST_WHL"

echo "[+] Installed $PACKAGE_NAME from local build."

# Test import
python3 -c "import codechat; print('Import successful!')"
