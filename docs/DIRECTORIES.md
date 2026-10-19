# Directory Layout & File Storage Specification

NewsAlerts is engineered to be **100% portable and isolated**. The executable binary contains zero user secrets, and all state is preserved in standard operating system user application directories.

---

## 1. Operating System Application Directories

| Operating System | Application Data Root (`APP_DIR`) |
|:---|:---|
| **Windows** | `%APPDATA%\NewsAlerts\` (e.g. `C:\Users\<User>\AppData\Roaming\NewsAlerts\`) |
| **macOS** | `~/Library/Application Support/NewsAlerts/` |
| **Linux** | `~/.config/NewsAlerts/` (or `$XDG_CONFIG_HOME/NewsAlerts/`) |

---

## 2. File Organization within `APP_DIR`

```
<APP_DIR>/
├── config.json          # User settings, screener filter definitions, sound choices
├── tape_history.json    # 4-day rolling tape events (persisted across restarts)
├── app.log              # Detailed diagnostic runtime logs & API trace information
├── keys.toml            # Optional user credentials file (alternative to Settings UI)
└── webview/             # WebView2 / WebKit cache, cookies, and local profile storage
```

### Detailed Breakdown

### `config.json`
Stores the active UI configuration:
- Screener column ordering, sort direction, and custom user filters.
- Active polling intervals (`screener_sec`, `tape_sec`, `news_sec`).
- Sound settings (chime volume, individual sound paths, mute/pause state).
- TradingView session cookies (`sessionid`, `sessionid_sign`).
- Alpaca API keys for short borrow locates.
- Telegram push alert preferences and credentials.

### `tape_history.json`
Maintains a rolling 4-day buffer of momentum tape prints:
- Retains up to 5,000 recent alerts.
- Enables off-hours, weekend, and after-hours market momentum review.
- Automatically prunes events older than 4 days upon each tape poll.

### `keys.toml` (Optional)
If you prefer managing API credentials outside the UI, you can place a `keys.toml` file in `APP_DIR` or next to the executable:
```toml
[tradingview]
sessionid = "your_tradingview_sessionid"
sessionid_sign = "your_tradingview_sessionid_sign"

[alpaca]
key_id = "your_alpaca_key_id"
secret_key = "your_alpaca_secret_key"
mode = "auto"

[telegram]
bot_token = "your_bot_token"
admin_chat_id = "your_chat_id"
```

### `app.log`
Rotated execution logs capturing scanner events, network reconnection attempts, borrow locates, and worker activity.

---

## 3. Temporary & Scratch Files
Temporary files and build caches (`build/`, `dist/`, `__pycache__`) are kept exclusively in the build working directory and are never pushed to Git or packaged into release distributions.
