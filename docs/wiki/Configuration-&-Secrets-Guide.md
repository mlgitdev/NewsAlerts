# Configuration & Secrets Guide

NewsAlerts enforces strict security and environment separation to protect your sensitive API keys, session cookies, and bot tokens.

---

## 🔒 Directory Isolation & Multi-OS Resolution Policy

Under no circumstances are secrets, tokens, or configuration files committed to git repositories or included in build artifacts.

All settings and secrets reside strictly in the operating system's standard user application storage, automatically created and provisioned on first launch:

| Operating System | Central Application Directory (`APP_DIR`) | Fallback Location |
| :--- | :--- | :--- |
| **Windows** | `%APPDATA%\NewsAlerts\` (`C:\Users\<user>\AppData\Roaming\NewsAlerts\`) | `$HOME/.newsalerts\` |
| **macOS** | `~/Library/Application Support/NewsAlerts/` | `$HOME/.newsalerts/` |
| **Linux / BSD** | `$XDG_CONFIG_HOME/NewsAlerts/` (default `~/.config/NewsAlerts/`) | `$HOME/.newsalerts/` |

### Custom Location Override & Dotfolder Support:
- **Environment Variable**: Set `NEWSALERTS_DIR` or `NEWSALERTS_HOME` (e.g. `export NEWSALERTS_DIR=$HOME/.newsalerts`) to explicitly direct all data storage to any custom folder.
- **Dotfolder Detection**: If `$HOME/.newsalerts` exists on disk, NewsAlerts automatically prioritizes and uses it across all platforms.
- **Automated Provisioning**: Zero manual directory setup is required. The terminal automatically invokes `mkdir(parents=True, exist_ok=True)` and creates `config.json` with default settings upon first launch.

---

## 📄 File Manifest in `APP_DIR`

- **`config.json`**: Primary runtime settings (scan filters, strategy toggles, audio preferences, Telegram credentials, TradingView session cookies).
- **`keys.toml`** *(Optional)*: Standalone secret storage file for headless environments or manual editing.
- **`tape_history.json`**: Rolling 4-day tape history cache (up to 5,000 prints).
- **`app.log`**: Rolling terminal diagnostics and connection logs.

## 🛡️ Best Practices

1. Never commit `.env`, `keys.toml`, or `config.json` to any git branch.
2. In-app settings are automatically validated and written atomically with file locks.
3. Automated pre-commit and CI workflows scan for credential patterns on every build.

---

## 💾 Backup & Sync Center

Use the **Backup & Sync** tab in Settings to safeguard your configuration:
- **Full Application Backup**: Click `💾 Export Full Backup (.json)` to generate a complete snapshot of all screeners, audio alerts, and strategies. Use `📂 Import Backup File` to restore or migrate to another machine.
- **Strategy Sync**: Click `💾 Export Strategies (.json)` to share momentum strategies with trading partners, or import community presets via `📂 Import Strategies`.
- **Factory Reset**: Click `↺ Restore Factory Defaults` to reset terminal settings back to fresh defaults while safely preserving `keys.toml`.

