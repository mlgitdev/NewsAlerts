# Configuration & Secrets Guide

NewsAlerts enforces strict security and environment separation to protect your sensitive API keys, session cookies, and bot tokens.

---

## 🔒 Directory Isolation Policy

Under no circumstances are secrets, tokens, or configuration files committed to git repositories or included in build artifacts.

All settings and secrets reside strictly in the operating system's standard user application storage:

| Operating System | Central Application Directory (`APP_DIR`) |
| :--- | :--- |
| **Windows** | `%APPDATA%\NewsAlerts\` (`C:\Users\<user>\AppData\Roaming\NewsAlerts\`) |
| **macOS** | `~/Library/Application Support/NewsAlerts/` |
| **Linux** | `~/.config/NewsAlerts/` or `$XDG_CONFIG_HOME/NewsAlerts/` |

---

## 📄 File Manifest in `APP_DIR`

- **`config.json`**: Primary runtime settings (scan filters, strategy toggles, audio preferences, Telegram credentials, TradingView session cookies).
- **`keys.toml`** *(Optional)*: Standalone secret storage file for headless environments or manual editing.
- **`tape_history.json`**: Rolling 4-day tape history cache (up to 5,000 prints).
- **`app.log`**: Rolling terminal diagnostics and connection logs.

---

## 🛡️ Best Practices

1. Never commit `.env`, `keys.toml`, or `config.json` to any git branch.
2. In-app settings are automatically validated and written atomically with file locks.
3. Automated pre-commit and CI workflows scan for credential patterns on every build.
