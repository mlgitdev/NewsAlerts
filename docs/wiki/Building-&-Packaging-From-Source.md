# Building & Packaging From Source

NewsAlerts compiles into a lightweight, standalone native binary (~14 MB) embedding all HTML/CSS/JS assets, custom icons, and audio files.

---

## 🛠️ Cross-Platform Build Workflow

The repository includes a **Universal Cross-Platform `Makefile`** compatible with Windows, macOS, and Linux:

```bash
# Clone the repository
git clone https://github.com/mlgitdev/NewsAlerts.git
cd NewsAlerts

# Auto-detect OS & prepare virtual environment with all dependencies
make env

# Or explicit platform-specific setup:
# make env-win    # Windows
# make env-linux  # Linux
# make env-mac    # macOS

# Compile dual build (portable .exe + unpacked app folder)
make build

# Launch the portable standalone binary
make run

# Launch the unpacked app directory (instant sub-300ms startup)
make run-app

# Install to %LOCALAPPDATA%\Programs\NewsAlerts with Start Menu & Desktop shortcuts
make install-local

# Compile Inno Setup Windows installer (NewsAlerts-Setup-v*.exe)
make installer

# Run full automated unit tests
make test

# Execute Deterministic Package Verification Gate
make verify

# Audit for accidental secret or credential leaks
make check

# List open GitHub issues (Issue-First Protocol)
make issue-list

# Inspect specific issue details and discussion
make issue-view ISSUE=<number>
```

---

## 📦 Dual Distribution Model (PyInstaller & Inno Setup)

NewsAlerts provides two distinct distribution formats:
1. **Portable Standalone Executable (`dist\NewsAlerts.exe`)**: Single-file archive (~15 MB) for USB drives or drop-in use.
2. **Unpacked Application Directory (`dist\NewsAlerts-App\`)**: Pre-extracted folder (~29.6 MB) bypassing `%TEMP%` extraction and real-time antivirus scans for sub-300ms instant terminal startup.
3. **Inno Setup Windows Installer (`NewsAlerts-Setup-vX.Y.Z.exe`)**: Modern LZMA2 installer (~13.5 MB) deploying directly to `%LOCALAPPDATA%\Programs\NewsAlerts` without requiring Administrator privileges.


---

## 🛡️ Package Verification Gate

Before any release artifact is accepted or published:
1. Binary PE magic headers are validated.
2. File size thresholds are checked (must remain under 25 MB).
3. Secrets and private key patterns are verified absent from the compiled archive.
4. Python byte-compilation check passes cleanly with zero syntax errors.
