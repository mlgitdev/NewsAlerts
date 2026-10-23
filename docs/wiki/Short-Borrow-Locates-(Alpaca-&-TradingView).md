# Short Borrow Locates (Alpaca & TradingView)

Shortability status is a primary variable in active momentum trading. When an aggressive runner has zero borrow availability or hard-to-borrow status, short sellers cannot easily short the stock, creating conditions for violent short squeezes.

---

## 🏷️ Borrow Status Indicators

NewsAlerts provides clear, color-coded badges directly on the screener, tape, and ticker header:

| Badge | Label | Meaning & Trading Edge |
| :---: | :---: | :--- |
| <span style="background:#166534;color:#4ade80;padding:2px 8px;border-radius:4px;font-weight:700">ETB</span> | **Easy to Borrow** | Plentiful shares available to short. Low locate fees. Less prone to severe borrow-induced squeeze traps. |
| <span style="background:#854d0e;color:#fde047;padding:2px 8px;border-radius:4px;font-weight:700">HTB</span> | **Hard to Borrow** | Broker locate required; high borrow interest rates. High squeeze risk when volume surges. |
| <span style="background:#991b1b;color:#f87171;padding:2px 8px;border-radius:4px;font-weight:700">NO BORROW</span> | **No Locate Available** | Broker has zero short inventory. Maximum short-squeeze vulnerability; any short covering creates vertical price expansion. |

---

## 🔌 Connecting Alpaca Brokerage API

NewsAlerts queries real-time shortability availability via the **Alpaca Brokerage Market API**:

1. Log into your [Alpaca Account](https://alpaca.markets) (Live or Paper trading).
2. Generate an **API Key ID** and **Secret Key**.
3. In NewsAlerts, open **Settings** (`S`) &rarr; **Short Borrow**.
4. Enter your `key_id` and `secret_key` (fields are password-masked).
5. Click **▶ Test Alpaca Connection** to verify your account status and buying power in real time.
6. Click **Save Settings**. Borrow locate indicators will update automatically on every scan cycle.

### Credential Storage & Precedence:
- **GUI Saved (`config.json`)**: Stored under `"borrow": { "alpaca_key_id": "...", "alpaca_secret_key": "...", "mode": "auto" }` in your central application directory (`%APPDATA%\NewsAlerts\` on Windows, `~/Library/Application Support/NewsAlerts/` on macOS, `~/.config/NewsAlerts/` on Linux).
- **Standalone Secrets (`keys.toml`)**: Alternatively, place keys in `<APP_DIR>/keys.toml` under `[alpaca]` for isolated management.
- For complete details, see the [[Configuration & Secrets Guide|Configuration-&-Secrets-Guide]].
