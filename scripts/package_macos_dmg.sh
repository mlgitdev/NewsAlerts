#!/usr/bin/env bash
# Package macOS NewsAlerts.app bundle and Apple Disk Image (DMG) installer
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

APP_VER="2.9.0"
if [ -f "VERSION" ]; then
    APP_VER="$(cat VERSION | tr -d '[:space:]')"
fi

echo "======================================================="
echo " Packaging macOS DMG Installer for NewsAlerts v${APP_VER}"
echo "======================================================="

STAGING_DIR="dmg-staging"
APP_DIR="${STAGING_DIR}/NewsAlerts.app"

rm -rf "$STAGING_DIR" NewsAlerts-macOS-arm64.dmg
mkdir -p "${APP_DIR}/Contents/MacOS"
mkdir -p "${APP_DIR}/Contents/Resources"

# Copy assets and runtime dependencies
if [ -f "assets/icon.icns" ]; then
    cp assets/icon.icns "${APP_DIR}/Contents/Resources/icon.icns"
fi
cp -r app web assets requirements.txt run_app.py "${APP_DIR}/Contents/Resources/"

# Generate Info.plist
cat << EOF > "${APP_DIR}/Contents/Info.plist"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>NewsAlerts</string>
    <key>CFBundleDisplayName</key>
    <string>NewsAlerts</string>
    <key>CFBundleIdentifier</key>
    <string>com.mlgitdev.newsalerts</string>
    <key>CFBundleVersion</key>
    <string>${APP_VER}</string>
    <key>CFBundleShortVersionString</key>
    <string>${APP_VER}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleExecutable</key>
    <string>NewsAlerts</string>
    <key>CFBundleIconFile</key>
    <string>icon.icns</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

# Generate executable binary launcher script
cat << 'EOF' > "${APP_DIR}/Contents/MacOS/NewsAlerts"
#!/usr/bin/env bash
DIR="$(cd "$(dirname "$0")/../Resources" && pwd)"
cd "$DIR"
exec python3 "$DIR/run_app.py" "$@"
EOF
chmod +x "${APP_DIR}/Contents/MacOS/NewsAlerts"

# Symlink /Applications for drag-and-drop installer
ln -s /Applications "${STAGING_DIR}/Applications"

# Compile Apple Disk Image
echo "[+] Compiling UDZO DMG via hdiutil..."
hdiutil create -volname "NewsAlerts" -srcfolder "$STAGING_DIR" -ov -format UDZO NewsAlerts-macOS-arm64.dmg

echo "[OK] Successfully created NewsAlerts-macOS-arm64.dmg"
