#!/usr/bin/env bash
# ============================================================
#  System Configuration Comparison Tool - Linux/macOS launcher
#  ./run.sh  - sets up a virtual environment and starts the app
# ============================================================
set -e
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
    echo "Python 3 is required. Install it first (e.g. sudo apt install python3 python3-venv python3-tk)."
    exit 1
fi

if [ ! -x ".venv/bin/python" ]; then
    echo "First run - setting up a virtual environment..."
    python3 -m venv .venv
    ./.venv/bin/pip install --upgrade pip >/dev/null
    echo "Installing dependencies (psutil, customtkinter)..."
    ./.venv/bin/pip install -r requirements.txt
    echo "Setup complete."
fi

exec ./.venv/bin/python main.py
