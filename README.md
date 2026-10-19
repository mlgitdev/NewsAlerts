# NewsAlerts — Momentum Screener, Tape & News Terminal

<p align="center">
  <img src="assets/hero.jpg" alt="NewsAlerts Hero Banner" width="100%" style="border-radius:12px; border:1px solid #2a3347; box-shadow:0 12px 36px rgba(0,0,0,0.55);" />
</p>

<p align="center">
  <img src="assets/app_icon_transparent.png" alt="NewsAlerts Logo" width="80" height="80" style="vertical-align:middle; margin-right:12px;" />
  <br>
  <b>Institutional-grade, real-time US small-cap momentum screener, high-of-day tape, and news intelligence terminal.</b>
</p>

<p align="center">
  <a href="https://github.com/mlgitdev/NewsAlerts/actions/workflows/ci.yml"><img src="https://github.com/mlgitdev/NewsAlerts/actions/workflows/ci.yml/badge.svg" alt="CI Status" /></a>
  <a href="https://github.com/mlgitdev/NewsAlerts/actions/workflows/secret-scan.yml"><img src="https://github.com/mlgitdev/NewsAlerts/actions/workflows/secret-scan.yml/badge.svg" alt="Secret Scanning" /></a>
  <a href="https://github.com/mlgitdev/NewsAlerts/releases"><img src="https://img.shields.io/github/v/release/mlgitdev/NewsAlerts?color=10b981&label=SemVer%20Release&logo=semver" alt="Latest SemVer Release" /></a>
  <img src="https://img.shields.io/badge/Platform-Windows%20x64%20%7C%20macOS%20arm64%20%7C%20Linux-blue" alt="Supported Platforms" />
  <img src="https://img.shields.io/badge/Package%20Gate-Verified-purple" alt="Package Verification Gate" />
</p>

---

## 🎯 The Problem & Why NewsAlerts

Active momentum day trading requires spotting low-float runners the split second volume arrives. Existing platforms make this harder than it should be:

- **Interactive Brokers (TWS & IBKR Desktop)**: Notoriously bloated, complex, and cumbersome to configure for fast intraday momentum screening.
- **TradingView**: Offers powerful scanning data but completely lacks native real-time audio bells and instant alert dispatching when new symbols break into momentum criteria.

**NewsAlerts bridges this gap with a focused, zero-bloat institutional trading terminal designed for pure execution speed:**

- ⚡ **Zero-Latency Inbound Alerts**: Plays an instant audio chime (with interactive volume control & one-click pause) and sends Telegram push notifications the exact second a ticker breaches your screening criteria.
- 🌊 **Running Momentum Tape**: Warrior-Trading style High of Day (HOD) and Squeeze Breakout prints with 4-day local disk persistence for weekend and off-hours trade review.
- 📰 **Instant Catalyst Confirmation**: Integrated Benzinga-first news wire showing headlines from the last 1 hour to 7 days, allowing immediate verification of what catalyst is driving the move.
- 🩳 **Real-Time Borrow Locates**: Live `HTB` (Hard to Borrow), `ETB` (Easy to Borrow), and `NO BORROW` badges right on the tape and screener to identify short squeeze potential instantly.
- 🪶 **Zero Electron / Node.js Overhead**: Native Edge WebView2 execution compiled to a lightweight ~14 MB standalone binary with sub-second launch times.

---

## ⚡ Quick Start & Universal Makefile Workflow

NewsAlerts includes a **Universal Cross-Platform `Makefile`** providing identical developer and build commands across **Windows, macOS, and Linux**:

```bash
make run                             # Launch desktop application
make build                           # Build standalone executable (Windows) or install dependencies (Unix)
make test                            # Run full automated unit test suite
make verify                          # Run Deterministic Package Verification Gate
make check                           # Audit for credential leaks
make clean                           # Remove build artifacts and caches
make worktree-list                   # List active git worktrees
make worktree-new BRANCH=feat/<name> # Create new isolated git worktree
make help                            # Display usage guide and detected platform
```

### Windows Prerequisite for `make`:
Windows does not include GNU `make` by default. Install it in seconds:
```powershell
winget install ezwinports.make
# Or via Chocolatey: choco install make -y
```
> *Zero-install alternative: You can also run `.\make.bat <target>` or `.\build.ps1 -Task <target>` in Windows PowerShell / CMD without installing any extra software.*

---

## 📖 Operational Procedures & Documentation Index

All technical procedures are documented in detail within the [`docs/`](docs/) directory. Below is an executive summary of each procedure with direct links:

### 🚀 1. Installation & Launch Procedure &mdash; [docs/INSTALLATION.md](docs/INSTALLATION.md)
*Universal `make` workflow, standalone binaries, and OS-specific setup:*
- **Universal Developer CLI (`make`)**: Primary cross-platform interface for building, testing, verifying, and running NewsAlerts.
- **Windows x64**: Zero-install portable standalone executable (`dist\NewsAlerts.exe`) with bundled custom icon, or source launch via `make run` / `.\build.ps1 -Task run`.
- **macOS (Apple Silicon arm64)**: Native Cocoa/WebKit window via `make run` / `./run.sh` or automated system-wide installer `./install.sh`.
- **Linux x86_64**: WebKit2GTK runtime setup, automated `./install.sh`, and desktop application launcher (`assets/NewsAlerts.desktop`).
&rarr; *Read the complete [Installation Guide](docs/INSTALLATION.md)*

### ⚙️ 2. Configuration & Credentials Procedure &mdash; [docs/CONFIGURATION.md](docs/CONFIGURATION.md)
*Configuration guidelines for live market data feeds, borrow locates, and alert notifications:*
- **In-App Settings UI**: Configure feeds, audio volume, and Telegram directly within the UI via the topbar gear icon.
- **TradingView Real-Time Data**: Enter session cookies (`sessionid`, `sessionid_sign`) for sub-second unthrottled screener updates.
- **Alpaca Short Borrow Locates**: Connect Alpaca API keys (`key_id`, `secret_key`) for live `HTB`, `ETB`, and `NO BORROW` badges.
- **Telegram Bot Notifications**: Dispatch instant push alerts for newly discovered breakout symbols.
- **Isolated `keys.toml` Storage**: Optional manual credential management strictly preserved in user `APP_DIR` (never in git).
&rarr; *Read the complete [Configuration Guide](docs/CONFIGURATION.md)*

### 📂 3. Directory Layouts & Persistence Procedure &mdash; [docs/DIRECTORIES.md](docs/DIRECTORIES.md)
*Cross-platform directory specifications, rolling tape persistence, and worktree layouts:*
- **User Application Roots (`APP_DIR`)**: Windows (`%APPDATA%\NewsAlerts\`), macOS (`~/Library/Application Support/NewsAlerts/`), Linux (`~/.config/NewsAlerts/`).
- **4-Day Rolling Tape Persistence**: `tape_history.json` retains up to 5,000 historical momentum prints for off-hours and weekend analysis.
- **Task-Isolated Git Worktrees (`.worktrees/`)**: Dedicated ignored directory hosting parallel feature branches without touching `main`.
&rarr; *Read the complete [Directory Layout Specification](docs/DIRECTORIES.md)*

### 📦 4. Release Governance & Versioning Procedure &mdash; [docs/RELEASES.md](docs/RELEASES.md)
*Release engineering policy, SemVer 2.0.0 compliance, and multi-OS artifact bundles:*
- **Semantic Versioning 2.0.0**: Strict `MAJOR.MINOR.PATCH` progression governed by `app/version.py`.
- **Multi-OS Release Bundles**: Automated generation of `NewsAlerts-Windows-x64.zip`, `NewsAlerts-macOS-arm64.tar.gz`, and `NewsAlerts-Linux-x64.tar.gz`.
- **Release Changelog Catalog**: Archived release documentation cataloged under `docs/releases/`.
&rarr; *Read the complete [Release Governance Guide](docs/RELEASES.md)*

### 🤝 5. Development & Git Worktree Workflow &mdash; [CONTRIBUTING.md](CONTRIBUTING.md)
*Guidelines for human developers and open source contributions:*
- **Isolated Worktree Model**: Never dirty `main`. Spawn dedicated feature worktrees via `make worktree-new BRANCH=feat/<name>`.
- **Conventional Commits**: Enforced commit structure: `type(scope): description`.
- **Pull Request & Code Ownership**: Mandatory PR template with automated bot validation and explicit code ownership via [`.github/CODEOWNERS`](.github/CODEOWNERS).
&rarr; *Read the complete [Contributing Guide](CONTRIBUTING.md)*

### 🤖 6. AI Agent Operating Protocol &mdash; [AGENTS.md](AGENTS.md)
*Authoritative rules of engagement for automated AI coding agents (Antigravity, Claude, Copilot):*
- **Absolute Security**: Strict zero-leak rule for keys, secrets, tokens, or credentials.
- **Git Worktree Mandatory Rule**: Root checkout on `main` is immutable; all modifications must occur in `.worktrees/`.
- **Local Verification Gate**: Mandatory Python syntax compilation, unit tests, and build check before submitting PRs.
&rarr; *Read the complete [AI Agent Operating Guidelines](AGENTS.md)*

---

## 🛡️ Package Verification & Fail-Safe Rollback Policy

NewsAlerts enforces a **deterministic Package Verification Gate** to ensure that broken, unverified, or incomplete binaries are never merged or distributed:

```
[ Build Artifacts ] ──> [ scripts/verify-packages.py ] 
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
     [ PASS (Code 0) ]                    [ FAIL (Code 1) ]
            │                                     │
    • PR Check Green                       • PR Aborted & Blocked
    • Publish GitHub Release               • DO NOT Publish Release
    • Distribute Multi-OS Bundles          • Delete Remote Git Tag
                                           • Revert 'main' to Last Good Commit
                                           • Auto-Open Critical GitHub Issue
```

### 1. In-PR Verification Gate
- Every Pull Request triggers multi-OS builds across Windows, macOS, and Linux.
- The package verifier audits archive structure, PE headers, executable sizes (>5MB), required launch scripts, and scans for secret file leakage.
- If any check fails, the PR check turns red and **merging is blocked**.

### 2. Post-Merge / Release Fail-Safe Rollback
If package verification fails during a release run on `main`:
1. **Release Blocked**: The package is **not published** to GitHub Releases or package registries.
2. **Git Tag Deleted**: The remote tag (e.g. `v2.4.1`) is deleted via `git push --delete origin <tag>`.
3. **Automated Branch Rollback**: The `main` branch is automatically reverted to the last known good commit (`git revert HEAD`).
4. **Critical Incident Issue**: An automated GitHub issue is opened with full logs, commit SHA, and assigned to `@mlgitdev`.

---

## ✨ Key Terminal Features

- 🚨 **Instant Audio & Telegram Alerts**: Fires on newly discovered momentum symbols matching user-defined screen criteria.
- 🔔 **Unified Alert Control (The Bell)**: One-click master toggle that both mutes audio chimes and pauses Telegram alert dispatching.
- 🔊 **Visual Rising Triangle Volume Control**: Smoothly scrub chime volume from 0% to 100% with real-time per-process Windows WinMM audio scaling.
- 🌊 **Real-Time Running Tape**: Warrior-Trading style High of Day (HOD) and Squeeze Breakout momentum tape with 4-day local disk persistence for off-hours and weekend review.
- 🩳 **Short Borrow Locates**: Real-time `HTB` (Hard to Borrow), `ETB` (Easy to Borrow), and `NO BORROW` indicators powered by live Alpaca API and TradingView market feeds.
- 📰 **Recent News Intelligence**: Direct Benzinga and financial wire headlines with configurable recency windows (1h, 2h, 4h, 8h, 12h, 24h, 3d, 7d).
- 🏷️ **Interactive Corner Version Badge**: Live SemVer 2.0.0 version indicator docked in the bottom-right corner of the terminal with click-to-open system diagnostic details.
- 📦 **100% Portable Executable**: Standalone single `.exe` (~14 MB) embedding the custom icon and running without external Python or Node.js runtimes.

---

## 📄 License
This project is proprietary and maintained by [@mlgitdev](https://github.com/mlgitdev). All rights reserved.
