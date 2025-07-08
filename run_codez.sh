#!/bin/bash
# run_codez.sh - Make sure the script is executable, activate venv, and run the CLI
if [ ! -d "venv" ]; then
  python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt
# ...existing code...
set -e

# Ensure this script is executable (optional if you want to fix other scripts)
chmod +x ./run_codez.sh

# Activate the virtual environment
source ./venv/bin/activate

# Run the main Python script with arguments passed to this script
python cli.py chat