# Installation & Setup Guide

NewsAlerts is available as a **pre-compiled standalone portable executable** or can be run directly from source across Windows, macOS, and Linux.

---

## 1. Windows x64

### Option A: Portable Standalone Executable (Recommended)
1. Download `NewsAlerts-Windows-x64.zip` from the latest [GitHub Release](https://github.com/mlgitdev/NewsAlerts/releases).
2. Extract the archive to any folder on your computer (e.g. `C:\Tools\NewsAlerts` or Desktop).
3. Double-click `NewsAlerts.exe` to run.
4. *No installation, Python, or administrator rights required.*

### Option B: Run from Source
```powershell
# Clone the repository
git clone https://github.com/mlgitdev/NewsAlerts.git
cd NewsAlerts

# Run using the automated PowerShell runner
.\build.ps1 -Task run

# Or recompile the standalone executable yourself
.\build.ps1 -Task build
```

---

## 2. macOS (Apple Silicon arm64 / Intel)

### Option A: One-Line Shell Installer
```bash
git clone https://github.com/mlgitdev/NewsAlerts.git
cd NewsAlerts
chmod +x install.sh
./install.sh
```
This sets up a local virtual environment and installs a `newsalerts` command in `~/.local/bin/`.

### Option B: Quick Launcher
```bash
chmod +x run.sh
./run.sh
```

---

## 3. Linux (Ubuntu, Debian, Fedora, Arch)

### Prerequisites
NewsAlerts uses `pywebview`, which interfaces with the system's WebKit2GTK engine.

**Ubuntu / Debian / Mint:**
```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip libgirepository1.0-dev libcairo2-dev gir1.2-webkit2-4.1
```

**Fedora / RHEL:**
```bash
sudo dnf install python3 python3-pip webkit2gtk4.1
```

**Arch Linux:**
```bash
sudo pacman -S python webkit2gtk-4.1
```

### Installation
```bash
git clone https://github.com/mlgitdev/NewsAlerts.git
cd NewsAlerts
chmod +x install.sh
./install.sh
```
The installer automatically registers the `NewsAlerts.desktop` launcher and application icon in your desktop application menu!

---

## 4. Universal Makefile & Developer CLI (Windows, macOS, Linux)

NewsAlerts provides a unified, cross-platform `Makefile` enabling identical developer commands across Windows, macOS, and Linux:

| Target | Description |
|:---|:---|
| `make run` | Launch the desktop terminal application |
| `make build` | Build standalone executable (`NewsAlerts.exe` on Windows) or install dependencies (Unix) |
| `make test` | Run full automated unit test suite (`tests/test_*.py`) |
| `make verify` | Execute the Deterministic Package Verification Gate |
| `make check` | Scan local/staged files for leaked API keys or credentials |
| `make clean` | Remove `build/`, `dist/`, `.venv/`, and Python caches |
| `make worktree-list` | List active git worktrees under `.worktrees/` |
| `make worktree-new BRANCH=feat/<name>` | Create a new isolated git worktree |
| `make help` | Display available targets and detected platform |

### Windows Prerequisite for `make`:
Windows does not include GNU `make` by default. You can install it with a single command:

**Option 1: Windows Package Manager (`winget`)**
```powershell
winget install ezwinports.make
```

**Option 2: Chocolatey**
```powershell
choco install make -y
```

*Note: Restart your terminal or reload environment variables after installation. Alternatively, you can use the zero-install `.\make.bat <target>` wrapper or `.\build.ps1 -Task <target>` without installing third-party tools.*

---

## 5. Verification & First Run

Once launched, verify your configuration:
1. Open **Settings** (gear icon in the top right).
2. Enter your TradingView `sessionid` cookie in **General & TV Login** for real-time data.
3. (Optional) In **Short Borrow**, enter your Alpaca API credentials.
4. (Optional) In **Sound Alerts**, configure Telegram Bot Token and Chat ID.
5. Click **Save Settings**.

