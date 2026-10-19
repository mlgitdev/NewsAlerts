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
6. In **NewsAlerts**, open **Settings** (`S`) &rarr; **Telegram Alerts**.
7. Enter your **Bot Token** and **Chat ID**.
8. Click **Test Telegram Alert** to send an instant verification message.
9. Check **Enable Telegram Dispatching** and click **Save Settings**.
