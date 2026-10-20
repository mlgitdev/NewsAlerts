# Release Governance & Versioning Policy

NewsAlerts adheres strictly to [Semantic Versioning (SemVer 2.0.0)](https://semver.org/):
`v<MAJOR>.<MINOR>.<PATCH>`

- **MAJOR**: Incompatible architectural changes, database schema breaking changes, or major UI overhauls.
- **MINOR**: New trading strategies, platform providers, UI panels, or backwards-compatible features.
- **PATCH**: Bug fixes, reliability updates, performance optimizations, or small documentation corrections.

---

## Single Source of Truth (`VERSION`)

Application version metadata is centrally registered in the root [`VERSION`](../VERSION) plain-text file:
- **Root `VERSION` File**: Contains the plain SemVer string (e.g., `2.4.5`).
- **Automatic Runtime Propagation**: [`app/version.py`](../app/version.py) dynamically reads `VERSION` at launch (and inside frozen PyInstaller executables via `sys._MEIPASS`), automatically calculating `__version__`, `VERSION_INFO = (major, minor, patch)`, and git tag representation.
- **Dynamic Frontend Display**: The frontend terminal queries `App.api().get_state()` and dynamically renders version badges without requiring hardcoded strings in HTML or JavaScript:
  1. The **topbar brand header** (`#brand-version`).
  2. The **bottom-right corner badge** of the terminal window (`#corner-version-badge`). Clicking this badge opens the system and release dialog.
  3. The **popout tape window corner** (`web/tape.html`).
  4. The **Settings -> About tab**, dynamically detailing SemVer component breakdown (`Major`, `Minor`, `Patch`).

---

## Release Pipeline & Automation

All official releases are produced deterministically through GitHub Actions:
1. Every release tag (`v*.*.*`) or merged release PR triggers `.github/workflows/release.yml`.
2. Clean virtual environments build multi-platform release artifacts:
   - **Windows x64**: PyInstaller standalone single-file `.exe` with embedded Win32 standard DIB icon and bundled `VERSION` file.
   - **macOS arm64**: Standalone Apple Silicon app bundle and launcher with native `.icns`.
   - **Linux x64**: Standalone binary, `.desktop` launcher, and `install.sh`.
3. An automated security audit verifies that `keys.toml`, `.env`, and secret directories are 100% absent from all bundles.
4. Release notes are extracted from `docs/releases/<version>.md` and published directly to GitHub Releases.

---

## Release History

- [v2.7.0 Release Notes](releases/v2.7.0.md) — Custom US equity symbol search in News wire (AMEX, NASDAQ, NYSE), interactive Strategy Builder with trigger types and deletion in Settings, and Backup / Import & Export JSON synchronization.
- [v2.6.0 Release Notes](releases/v2.6.0.md) — Large-Cap & High-Float Momentum Squeeze strategies, high-velocity 5-min surge alerts (Up 10% in 5min), TradingView change|5 velocity, and expanded universe boundaries ($1–$500).
- [v2.5.0 Release Notes](releases/v2.5.0.md) — Customizable Keyboard Shortcuts & Hotkey Configuration tab in Settings with interactive key capture, institutional defaults, and multi-OS config persistence.
- [v2.4.5 Release Notes](releases/v2.4.5.md) — Single Source of Truth (SSOT) architecture via root `VERSION` file, dynamic runtime propagation, and complete decoupling of static version strings.
- [v2.4.4 Release Notes](releases/v2.4.4.md) — Fix and activate terminal-wide keyboard shortcuts and hotkeys (M, T, Space, S, R, Esc, 1-5, Enter), toast feedback, and input guards.
- [v2.4.3 Release Notes](releases/v2.4.3.md) — Multi-OS data directory resolution, $HOME/.newsalerts and env overrides, auto-provisioning, and test coverage.
- [v2.4.2 Release Notes](releases/v2.4.2.md) — About pane GitHub & Wiki links, README social preview hero, TradingView chart popout docs, and comprehensive Wiki suite.
- [v2.4.1 Release Notes](releases/v2.4.1.md) — Runtime asset routing, Settings grid alignment fix, brand navigation, and social preview card.
- [v2.4.0 Release Notes](releases/v2.4.0.md) — Unified alert pause, triangle volume control, brand identity, multi-OS support, and GitHub CI/CD automation.
