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

VENV_DIR="$SCRIPT_DIR/.venv"
if [ ! -d "$VENV_DIR" ] && [ -d "$SCRIPT_DIR/../../.venv" ]; then
    echo "[+] Inherited shared virtual environment from repository root..."
    VENV_DIR="$SCRIPT_DIR/../../.venv"
elif [ ! -d "$VENV_DIR" ]; then
    echo "[+] Creating local virtual environment (.venv)..."
    "$PYTHON" -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install --upgrade pip
    "$VENV_DIR/bin/pip" install -r requirements.txt
fi

exec "$VENV_DIR/bin/python" run_app.py "$@"
