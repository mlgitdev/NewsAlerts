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

## 4. Verification & First Run

Once launched, verify your configuration:
1. Open **Settings** (gear icon in the top right).
2. Enter your TradingView `sessionid` cookie in **General & TV Login** for real-time data.
3. (Optional) In **Short Borrow**, enter your Alpaca API credentials.
4. (Optional) In **Sound Alerts**, configure Telegram Bot Token and Chat ID.
5. Click **Save Settings**.
