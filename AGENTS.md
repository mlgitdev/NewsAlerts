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

## 4. Git Worktree Protocol & Task Isolation (Mandatory)

The repository root checkout on `main` is considered **immutable and read-only for active development**. Agents must strictly adhere to the following task isolation workflow:

### 1. Mandatory Worktree for New Work
- Never edit or dirty the root checkout on `main`.
- Always spawn a dedicated git worktree under `.worktrees/`:
  ```powershell
  # Windows
  .\build.ps1 -Task worktree-new -Branch feat/<descriptor> -Base main
  ```
  ```bash
  # Linux / macOS
  ./scripts/worktree.sh new feat/<descriptor> main
  ```
  *(Or native git: `git worktree add -b feat/<descriptor> .worktrees/<sanitized-name> main`)*

### 2. Sub-Task Worktrees & Merge-Back Protocol
- For multi-phase features or parallel experiments, branch sub-worktrees from the parent `feat/` branch:
  ```powershell
  .\build.ps1 -Task worktree-new -Branch sub/<feature>/<subtask> -Base feat/<feature>
  ```
- Once validated, merge the sub-task back into the primary feature branch before PR creation:
  ```powershell
  .\build.ps1 -Task worktree-merge -Branch sub/<feature>/<subtask> -Base feat/<feature>
  ```
- Safely remove the sub-task worktree:
  ```powershell
  .\build.ps1 -Task worktree-remove -Branch sub/<feature>/<subtask>
  ```

### 3. Cleanup After PR Merge
- Once the Pull Request is reviewed, approved, and merged into `main` by `@mlgitdev`, the worktree must be removed:
  ```powershell
  .\build.ps1 -Task worktree-remove -Branch feat/<descriptor>
  ```

---

## 5. Branch & Pull Request Protocol

### 1. Branch Naming Conventions
- Features: `feat/<short-descriptor>` (e.g. `feat/vwap-filter`)
- Major Epics: `major/<short-descriptor>` (e.g. `major/v3-architecture`)
- Bug Fixes: `fix/<short-descriptor>` (e.g. `fix/tape-timestamp`)
- Documentation: `docs/<short-descriptor>`
- Performance: `perf/<short-descriptor>`
- Sub-tasks: `sub/<feature>/<task>`

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
- **Code Ownership**: Component modifications are subject to [`.github/CODEOWNERS`](.github/CODEOWNERS). Review requests are automatically routed to designated code owner `@mlgitdev`.

---

## 6. Local Verification Gate Before PR Creation

Agents MUST execute the following verification steps prior to opening a PR:

1. **Python Syntax Compilation**:
   ```powershell
   .venv\Scripts\python.exe -m compileall app run_app.py
   ```
2. **Execute Full Unit Test Suite**:
   ```powershell
   .venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
   ```
3. **Audit Executable Build (if packaging changes made)**:
   ```powershell
   .\build.ps1 -Task build
   ```
   Verify that `dist\NewsAlerts.exe` passes the automated secret audit.
4. **Package Verification Gate**:
   ```powershell
   .\build.ps1 -Task verify-packages
   ```
   Verify standalone binary integrity, PE magic headers, and absence of secret files.

---

## 7. Package Verification & Automated Fail-Safe Rollback

All build and release pipelines enforce the **Deterministic Package Verification Gate**:
- **In-PR Gate**: If package verification fails, the PR check turns RED and merge is strictly blocked (PR is aborted).
- **Post-PR Release Gate**: If verification fails post-merge on `main`:
  1. The release artifact is NOT published.
  2. The remote git tag is deleted.
  3. The `main` branch is automatically reverted to the last known good commit.
  4. A critical incident GitHub issue is automatically opened and assigned to `@mlgitdev`.

---

## 8. Frontend Coding Standards

- **Core**: Vanilla HTML5 and Vanilla modern ES6+ JavaScript. **No React, Vue, or Angular**.
- **CSS**: Pure Vanilla CSS using design system tokens defined in [`web/css/app.css`](file:///web/css/app.css). Avoid ad-hoc styling.
- **Responsiveness**: Resizable panes, splitters, and dynamic tabular data must remain fluid and memory-leak free.
- **Browser Compatibility**: Edge WebView2 (Chromium) on Windows, Safari WebKit on macOS, WebKit2GTK on Linux.
