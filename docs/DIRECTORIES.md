# Directory Layout & File Storage Specification

NewsAlerts is engineered to be **100% portable and isolated**. The executable binary contains zero user secrets, and all state is preserved in standard operating system user application directories.

---

## 1. Operating System Application Directories & Resolution Priority

NewsAlerts automatically resolves, creates, and provisions the data root across all platforms following this priority order:

1. **Explicit Environment Variable Override**:
   If `NEWSALERTS_DIR` or `NEWSALERTS_HOME` is set (e.g. `export NEWSALERTS_DIR=$HOME/.newsalerts`), the application expands the path, creates the folder automatically, and stores all user data there.
2. **Dotfolder Precedence**:
   If `$HOME/.newsalerts` exists on the system, NewsAlerts seamlessly uses it across Windows, macOS, and Linux.
3. **Platform Standards**:

| Operating System | Default Application Data Root (`APP_DIR`) | Fallback Location |
|:---|:---|:---|
| **Windows** | `%APPDATA%\NewsAlerts\` (e.g. `C:\Users\<User>\AppData\Roaming\NewsAlerts\`) | `$HOME/.newsalerts\` |
| **macOS** | `~/Library/Application Support/NewsAlerts/` | `$HOME/.newsalerts/` |
| **Linux / BSD** | `$XDG_CONFIG_HOME/NewsAlerts/` (default `~/.config/NewsAlerts/`) | `$HOME/.newsalerts/` |

---

## 2. Automated Directory & File Provisioning

NewsAlerts features self-healing automated provisioning:
- **Zero Manual Folder Creation**: On first launch, `get_app_dir()` automatically invokes `mkdir(parents=True, exist_ok=True)` to create the directory hierarchy.
- **Initial File Provisioning**:
  - `config.json` is automatically generated on first launch populated with complete default screening criteria, strategy definitions, and polling intervals if no configuration file exists.
  - `tape_history.json` is initialized and maintained as a rolling 4-day buffer.
  - `app.log` is initialized for structured diagnostic logging.
- **Fail-Safe Fallback**: If system directory creation fails (e.g., restricted container or permission constraints), NewsAlerts automatically falls back to creating `$HOME/.newsalerts/`.

---

## 3. File Organization within `APP_DIR`

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

---

## 4. Git Worktrees Directory (`.worktrees/`)

To preserve the clean state of the primary repository root on `main` and support concurrent feature development, development worktrees reside in `.worktrees/` at the repository root:

```
<REPO_ROOT>/
├── .worktrees/
│   ├── feat-vwap-filter/      # Isolated worktree for feat/vwap-filter
│   ├── fix-tape-timestamp/    # Isolated worktree for fix/tape-timestamp
│   └── sub-vwap-tests/        # Isolated sub-task worktree
├── app/                       # Pristine main branch codebase
├── assets/
└── web/
```

- **Strictly Git-Ignored**: `.worktrees/` is permanently excluded via `.gitignore` so worktrees never leak into git commits or release bundles.
- **Shared Python Environment**: Worktrees automatically inherit the shared `.venv` from the repository root with zero setup time.
- **Isolated Lifecycle**: Worktrees can be safely created, merged, and removed via `.\build.ps1 -Task worktree-new` / `worktree-remove` without dirtying or switching branches on `main`.
