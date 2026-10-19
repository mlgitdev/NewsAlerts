# Release Governance & Versioning Policy

NewsAlerts adheres strictly to [Semantic Versioning (SemVer 2.0.0)](https://semver.org/):
`v<MAJOR>.<MINOR>.<PATCH>`

- **MAJOR**: Incompatible architectural changes, database schema breaking changes, or major UI overhauls.
- **MINOR**: New trading strategies, platform providers, UI panels, or backwards-compatible features.
- **PATCH**: Bug fixes, reliability updates, performance optimizations, or small documentation corrections.

---

## Release Pipeline & Automation

All official releases are produced deterministically through GitHub Actions:
1. Every release tag (`v*.*.*`) or merged release PR triggers `.github/workflows/release.yml`.
2. Clean virtual environments build multi-platform release artifacts:
   - **Windows x64**: PyInstaller standalone single-file `.exe` with embedded Win32 standard DIB icon.
   - **macOS arm64**: Standalone Apple Silicon app bundle and launcher with native `.icns`.
   - **Linux x64**: Standalone binary, `.desktop` launcher, and `install.sh`.
3. An automated security audit verifies that `keys.toml`, `.env`, and secret directories are 100% absent from all bundles.
4. Release notes are extracted from `docs/releases/<version>.md` and published directly to GitHub Releases.

---

## Release History

- [v2.4.0 Release Notes](releases/v2.4.0.md) — Unified alert pause, triangle volume control, brand identity, multi-OS support, and GitHub CI/CD automation.
