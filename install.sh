#!/usr/bin/env bash
# NewsAlerts Installation Script (Linux & macOS)
set -e

echo "======================================================="
echo " Installing NewsAlerts Terminal & Screener"
echo " OS: $(uname -s) | Architecture: $(uname -m)"
echo "======================================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${HOME}/.local/bin"
APP_DIR="${HOME}/.local/share/newsalerts"
DESKTOP_DIR="${HOME}/.local/share/applications"
ICON_DIR="${HOME}/.local/share/icons/hicolor/256x256/apps"

mkdir -p "$BIN_DIR"

# 1. Detect Python
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "[-] Error: Python 3.10+ is required. Please install Python 3 and re-run." >&2
    exit 1
fi

PY_VER=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "[+] Detected Python $PY_VER ($PYTHON_CMD)"

# 2. Check OS-specific dependencies
OS_TYPE="$(uname -s)"
if [ "$OS_TYPE" = "Linux" ]; then
    echo "[+] Checking Linux graphical environment..."
    if ! command -v pkg-config &>/dev/null && [ ! -d "/usr/include/webkit2gtk-4.0" ] && [ ! -d "/usr/include/webkit2gtk-4.1" ]; then
        echo "[i] Note: pywebview on Linux requires WebKit2GTK."
        echo "    If not already installed, run: sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.1"
    fi
elif [ "$OS_TYPE" = "Darwin" ]; then
    echo "[+] macOS detected. Using native WebKit & Cocoa."
fi

# 3. Create Virtualenv and install requirements
echo "[+] Setting up environment..."
if [ ! -d "$SCRIPT_DIR/.venv" ]; then
    "$PYTHON_CMD" -m venv "$SCRIPT_DIR/.venv"
fi

"$SCRIPT_DIR/.venv/bin/pip" install --upgrade pip
"$SCRIPT_DIR/.venv/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"

# 4. Create launcher in ~/.local/bin/newsalerts
cat << 'EOF' > "$BIN_DIR/newsalerts"
#!/usr/bin/env bash
TARGET_DIR="INSTALL_PATH_PLACEHOLDER"
cd "$TARGET_DIR"
exec "$TARGET_DIR/.venv/bin/python" "$TARGET_DIR/run_app.py" "$@"
EOF

sed -i.bak "s|INSTALL_PATH_PLACEHOLDER|$SCRIPT_DIR|g" "$BIN_DIR/newsalerts" 2>/dev/null || sed -i "" "s|INSTALL_PATH_PLACEHOLDER|$SCRIPT_DIR|g" "$BIN_DIR/newsalerts"
rm -f "$BIN_DIR/newsalerts.bak"
chmod +x "$BIN_DIR/newsalerts"
echo "[+] Created executable command at: $BIN_DIR/newsalerts"

# 5. Linux Desktop Launcher Integration
if [ "$OS_TYPE" = "Linux" ]; then
    mkdir -p "$DESKTOP_DIR" "$ICON_DIR"
    if [ -f "$SCRIPT_DIR/assets/app_icon_transparent.png" ]; then
        cp "$SCRIPT_DIR/assets/app_icon_transparent.png" "$ICON_DIR/newsalerts.png"
    fi

    if [ -f "$SCRIPT_DIR/assets/NewsAlerts.desktop" ]; then
        cp "$SCRIPT_DIR/assets/NewsAlerts.desktop" "$DESKTOP_DIR/NewsAlerts.desktop"
        chmod +x "$DESKTOP_DIR/NewsAlerts.desktop"
        echo "[+] Installed desktop entry to: $DESKTOP_DIR/NewsAlerts.desktop"
    fi
fi

echo ""
echo "======================================================="
echo "[OK] NewsAlerts installed successfully!"
echo "     Run command: newsalerts (or ./run.sh)"
echo "     Config location:"
if [ "$OS_TYPE" = "Darwin" ]; then
    echo "       ~/Library/Application Support/NewsAlerts/"
else
    echo "       ~/.config/NewsAlerts/"
fi
echo "======================================================="
