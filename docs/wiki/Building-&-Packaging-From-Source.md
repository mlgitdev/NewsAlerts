# Building & Packaging From Source

NewsAlerts compiles into a lightweight, standalone native binary (~14 MB) embedding all HTML/CSS/JS assets, custom icons, and audio files.

---

## 🛠️ Cross-Platform Build Workflow

The repository includes a **Universal Cross-Platform `Makefile`** compatible with Windows, macOS, and Linux:

```bash
# Clone the repository
git clone https://github.com/mlgitdev/NewsAlerts.git
cd NewsAlerts

# Create virtual environment and install dependencies
make build

# Launch the desktop terminal
make run

# Run full automated unit tests
make test

# Execute Deterministic Package Verification Gate
make verify

# Audit for accidental secret or credential leaks
make check
```

---

## 📦 Standalone Binaries (PyInstaller)

- **Windows**: Bundled using `NewsAlerts.spec` into `dist\NewsAlerts.exe` with bundled Win32 icon (`assets/icon.ico`).
- **macOS**: Built with native Apple Silicon arm64 compatibility and ICNS icon (`assets/icon.icns`).
- **Linux**: Bundled with WebKit2GTK support and Desktop entry (`assets/NewsAlerts.desktop`).

---

## 🛡️ Package Verification Gate

Before any release artifact is accepted or published:
1. Binary PE magic headers are validated.
2. File size thresholds are checked (must remain under 25 MB).
3. Secrets and private key patterns are verified absent from the compiled archive.
4. Python byte-compilation check passes cleanly with zero syntax errors.
