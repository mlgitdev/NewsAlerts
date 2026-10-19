#!/usr/bin/env bash
# NewsAlerts cross-platform launcher (Linux & macOS)
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo "[-] Error: Python 3.10+ is required but not installed or not in PATH." >&2
    exit 1
fi

if [ ! -d ".venv" ]; then
    echo "[+] Creating local virtual environment (.venv)..."
    "$PYTHON" -m venv .venv
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r requirements.txt
fi

exec .venv/bin/python run_app.py "$@"
