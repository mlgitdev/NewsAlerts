# Telegram Push Notifications

NewsAlerts includes a dedicated **Asynchronous Telegram Worker Queue** that dispatches sub-second push notifications directly to your phone, tablet, or desktop Telegram messenger.

---

## 📲 Alert Payload Anatomy

Every Telegram alert dispatched by NewsAlerts is formatted for immediate trading comprehension:

```
🚨 NEW MOMENTUM ALERT: WORX
Strategy: Low Float Momo Breakout
Price: $4.20 (+94.20%)
Volume: 3,420,000 | Float: 1.2M
Borrow Status: HTB (Hard to Borrow)
5m Relative Volume: +64,906%
🔗 Open Chart: https://www.tradingview.com/chart/?symbol=WORX
```

Clicking the chart link in your Telegram app on mobile or desktop instantly opens the ticker in TradingView for immediate analysis.

---

## 🤖 Telegram Bot Setup Guide

1. Open Telegram and search for `@BotFather`.
2. Send `/newbot` and follow the prompts to choose a bot name and username.
3. BotFather will provide an **HTTP API Token** (e.g. `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`).
4. Start a direct message with your newly created bot and click **Start**.
5. To find your personal `chat_id`, search for `@userinfobot` in Telegram, click Start, and note your numeric ID.
6. In **NewsAlerts**, open **Settings** (`S`) &rarr; **Sound Alerts**.
7. Enter your **Bot Token** (password-masked) and **Chat ID**.
8. Click **✈️ Send Test Message** to send an instant verification message to your Telegram chat.
9. Check **Enable Telegram Dispatching** and click **Save Settings**.

### Credential Storage & Precedence:
- **GUI Saved (`config.json`)**: Stored under `"alerts": { "telegram_bot_token": "...", "telegram_chat_id": "..." }` in your central application directory (`%APPDATA%\NewsAlerts\` on Windows, `~/Library/Application Support/NewsAlerts/` on macOS, `~/.config/NewsAlerts/` on Linux).
- **Standalone Secrets (`keys.toml`)**: Alternatively, place keys in `<APP_DIR>/keys.toml` under `[telegram]` (`bot_token` and `admin_chat_id`).
- For complete details, see the [[Configuration & Secrets Guide|Configuration-&-Secrets-Guide]].
