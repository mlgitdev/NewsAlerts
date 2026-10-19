# Installation & Setup Guide

NewsAlerts is an institutional-grade financial momentum terminal. It can be run immediately via our **Universal `make` Developer CLI**, as a **pre-compiled portable executable** (Windows), or installed natively across macOS and Linux.

---

## 1. Universal Developer Workflow (`make`) &mdash; Recommended

NewsAlerts includes a unified, cross-platform `Makefile` providing identical developer commands across Windows, macOS, and Linux:

| Target | Description | Windows Execution | Unix Execution (macOS / Linux) |
|:---|:---|:---|:---|
| `make run` | Launch the desktop terminal application | `powershell -File ./build.ps1 -Task run` | `./run.sh` |
| `make build` | Build standalone binary or install deps | `powershell -File ./build.ps1 -Task build` | `python3 -m pip install -r requirements.txt` |
| `make test` | Run full automated unit test suite | `.venv\Scripts\python.exe -m unittest discover` | `python3 -m unittest discover` |
| `make verify` | Run Package Verification Gate | `powershell -File ./build.ps1 -Task verify-packages` | `python3 scripts/verify-packages.py` |
| `make check` | Scan local/staged files for leaked secrets | `powershell -File ./build.ps1 -Task check` | `git diff --staged` secret scan |
| `make clean` | Remove `build/`, `dist/`, `.venv/`, caches | `powershell -File ./build.ps1 -Task clean` | `rm -rf build/ dist/ .venv/` |
| `make worktree-list` | List active git worktrees | `powershell -File ./build.ps1 -Task worktree-list` | `./scripts/worktree.sh list` |
| `make worktree-new BRANCH=feat/<name>` | Create a new isolated git worktree | `powershell -File ./build.ps1 -Task worktree-new` | `./scripts/worktree.sh new` |
| `make help` | Display targets & detected platform | Formatted CLI help table | Formatted CLI help table |

### Windows Prerequisite for `make`:
Windows does not include GNU `make` by default. Install it in seconds using either package manager:

**Option A: Windows Package Manager (`winget`)**
```powershell
winget install ezwinports.make
```

**Option B: Chocolatey**
```powershell
choco install make -y
```

> **Tip**: If `make` is not recognized immediately after running `winget`, copy `make.exe` to your `PATH` (e.g. `copy "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\ezwinports.make*\bin\make.exe" "$HOME\bin\"`) or simply use the zero-install `.\make.bat <target>` wrapper included in the repository.

---

## 2. Windows x64 Step-by-Step

### Option A: Portable Standalone Executable (For Traders & Non-Developers)
1. Download `NewsAlerts-Windows-x64.zip` from the latest [GitHub Release](https://github.com/mlgitdev/NewsAlerts/releases).
2. Extract the archive to any folder (e.g. `C:\Tools\NewsAlerts` or Desktop).
3. Double-click `NewsAlerts.exe` to run.
4. *No installation, Python runtime, or administrator rights required.*

### Option B: Run from Source
```powershell
# Clone the repository
git clone https://github.com/mlgitdev/NewsAlerts.git
cd NewsAlerts

# Run using the Universal Makefile
make run

# (Or using native PowerShell directly)
.\build.ps1 -Task run
```

### Option C: Recompile Standalone Executable
```powershell
make build
# (Or: .\build.ps1 -Task build)
```

---

## 3. macOS (Apple Silicon arm64 / Intel) Step-by-Step

### Option A: Universal Makefile / Quick Launcher
```bash
git clone https://github.com/mlgitdev/NewsAlerts.git
cd NewsAlerts
make run
# (Or: ./run.sh)
```

### Option B: System-Wide Installer
```bash
chmod +x install.sh
./install.sh
```
This configures a dedicated virtual environment and installs a `newsalerts` command in `~/.local/bin/`.

---

## 4. Linux (Ubuntu, Debian, Fedora, Arch) Step-by-Step

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

### Running & Installation
```bash
git clone https://github.com/mlgitdev/NewsAlerts.git
cd NewsAlerts

# Launch immediately
make run

# Or install system desktop launcher and application icon
./install.sh
```

---

## 5. Verification & First Run

Once launched, verify your configuration:
1. Open **Settings** (gear icon in the top right).
2. Enter your TradingView `sessionid` cookie in **General & TV Login** for real-time data.
3. (Optional) In **Short Borrow**, enter your Alpaca API credentials.
4. (Optional) In **Sound Alerts**, configure Telegram Bot Token and Chat ID.
5. Click **Save Settings**.
