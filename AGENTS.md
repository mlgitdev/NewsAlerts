# AGENTS.md — AI Agent Operating Guidelines & Repository Protocol

Welcome, Agent. This document defines the mandatory operating guidelines, architectural constraints, security rules, and workflow protocols for any automated AI agent (Antigravity, Claude, Copilot, Cursor, etc.) contributing to **NewsAlerts**.

---

## 1. Core Mission & Philosophy

NewsAlerts is a lightweight, ultra-responsive financial momentum terminal designed for active day traders.
- **Aesthetic Excellence**: High-precision, dark-mode institutional trading terminal aesthetic (Bloomberg / TradingView Pro). **Strictly zero AI-slop** (no blurry mockups, no cartoonish illustrations, no fake marketing cards).
- **Zero Bloat**: No Node.js / Electron overhead in runtime. Native `pywebview` window with pure Vanilla JS/HTML/CSS.
- **Cross-Platform Parity**: Windows x64, macOS (Apple Silicon arm64), and Linux must all be supported with clean platform abstraction.
- **Rock-Solid Isolation**: Secrets must never touch the codebase, Git commits, or release bundles.

---

## 2. Strict Security & Secret Protection

### Absolute Rules:
1. **Never Commit Secrets**: Any file named `keys.toml`, `secrets.toml`, `.env`, or containing live API keys, session cookies, or bot tokens must be rejected.
2. **AppData Isolation**: User credentials belong exclusively in `%APPDATA%\NewsAlerts\` (Windows), `~/Library/Application Support/NewsAlerts/` (macOS), or `~/.config/NewsAlerts/` (Linux).
3. **Auditing Verification**: Before submitting a PR or triggering a build, audit your staged files:
   ```bash
   git diff --staged --name-only | grep -E "keys|secret|token|\.env"
   ```

---

## 3. Multi-OS Architecture & Compatibility

When writing or modifying code, adhere strictly to cross-platform compatibility:

### File Paths & Storage
- Always use `Path` from `pathlib` and the centralized `APP_DIR` in [`app/config.py`](file:///app/config.py).
- Never hardcode Windows-only backslashes (`\`) in code logic or URLs.

### Sound & Audio Playback
- Audio playback logic resides in [`app/sounds.py`](file:///app/sounds.py).
- Windows uses `winsound` and WinMM `waveOutSetVolume`.
- macOS uses `afplay` with `-v` volume scaling.
- Linux uses `paplay` / `aplay` / `canberra-gtk-play`.
- All audio calls must be throttled and non-blocking (async threads).

### Executable Icons
- Windows executables require standard Win32 DIB format `.ico` with sizes 16, 24, 32, 48, 64, 128, 256 (`assets/icon.ico`).
- macOS bundles require native Apple `.icns` (`assets/icon.icns`).
- Linux requires 256x256 / 512x512 transparent PNG (`assets/app_icon_transparent.png`) paired with `assets/NewsAlerts.desktop`.

---

## 4. Branch & Pull Request Protocol

### 1. Branch Naming Conventions
- Features: `feat/<short-descriptor>` (e.g. `feat/vwap-filter`)
- Bug Fixes: `fix/<short-descriptor>` (e.g. `fix/tape-timestamp`)
- Documentation: `docs/<short-descriptor>`
- Performance: `perf/<short-descriptor>`

### 2. Conventional Commits
All commit messages must follow Conventional Commits format:
```
<type>(<scope>): <concise present-tense description>

[optional detailed body]
```
Allowed types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`.

### 3. Pull Request Requirements
When an Agent creates a PR:
- **Title**: Must be a valid Conventional Commit string.
- **Body**: Must strictly adhere to `.github/pull_request_template.md` with all required sections filled out:
  - `## Summary`
  - `## Motivation / Context`
  - `## Changes`
  - `## Verification & Testing`
  - `## Checklist`
- **Never bypass checks**: Do not attempt to merge directly to `main`. Only the repository owner (`@mlgitdev`) can approve and merge.

---

## 5. Local Verification Gate Before PR Creation

Agents MUST execute the following verification steps prior to opening a PR:

1. **Python Syntax & Type Cleanliness**:
   ```powershell
   .venv\Scripts\python.exe -m py_compile app/*.py run_app.py
   ```
2. **Execute Unit Tests**:
   Run all test scripts in `scratch/` or `tests/`:
   ```powershell
   .venv\Scripts\python.exe -c "import sys; sys.path.insert(0, '.'); import app.main; print('Import check passed')"
   ```
3. **Audit Executable Build (if packaging changes made)**:
   ```powershell
   .\build.ps1 -Task build
   ```
   Verify that `dist\NewsAlerts.exe` passes the automated secret audit.

---

## 6. Frontend Coding Standards

- **Core**: Vanilla HTML5 and Vanilla modern ES6+ JavaScript. **No React, Vue, or Angular**.
- **CSS**: Pure Vanilla CSS using design system tokens defined in [`web/css/app.css`](file:///web/css/app.css). Avoid ad-hoc styling.
- **Responsiveness**: Resizable panes, splitters, and dynamic tabular data must remain fluid and memory-leak free.
- **Browser Compatibility**: Edge WebView2 (Chromium) on Windows, Safari WebKit on macOS, WebKit2GTK on Linux.
