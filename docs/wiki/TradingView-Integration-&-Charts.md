# TradingView Integration & One-Click Charting

NewsAlerts integrates with **TradingView** to power both real-time streaming scanner updates and seamless one-click chart charting directly from the terminal.

---

## 📈 One-Click Chart Launching (News Pane Header)

When active momentum tickers trigger alerts or appear on the scanner, speed of execution is critical. Manually typing tickers into external chart windows wastes precious seconds.

NewsAlerts provides an **instant one-click chart launcher** docked directly within the **News Catalyst Banner / Pane Header**:

```
+------------------------------------------------------------------------------------+
| [LOGO] WORX $4.20 (+94.20%)  [HTB]  Float 1.2M · VWAP: $3.95     [CHART 📈] [REFRESH 🔄] |
+------------------------------------------------------------------------------------+
```

### How to Open a Chart in TradingView:
1. Click any row in the **Momentum Screener** or any print in the **Running Tape**. The ticker is immediately focused and its catalyst headlines load in the right-hand News pane.
2. In the top-right corner of the **News Pane Header**, locate the **Chart Icon** (`#news-chart`).
3. Click the **Chart Icon** (or press the chart shortcut).
4. The terminal automatically launches your default operating system browser and opens the live interactive chart for that exact ticker:
   ```
   https://www.tradingview.com/chart/?symbol=<TICKER>
   ```
5. Your customized TradingView indicators, moving averages, volume profile, and drawing templates are loaded immediately without any manual symbol entry.

---

## ⚡ Real-Time TradingView Session Authentication

By default, unauthenticated TradingView connections receive delayed data (~15-minute delay). Entering your TradingView session cookie enables sub-second real-time streaming:

### Step-by-Step Session Setup:
1. Open your browser and log into [tradingview.com](https://www.tradingview.com).
2. Press `F12` (or right-click &rarr; *Inspect*) to open Developer Tools.
3. Navigate to the **Application** tab (Chrome / Edge / Brave) or **Storage** tab (Firefox).
4. Under the **Cookies** section in the left sidebar, click `https://www.tradingview.com`.
5. Locate the cookie named `sessionid` and double-click to copy its value.
6. In **NewsAlerts**, click the top-right **Gear Icon (Settings)** or press `S`.
7. Paste the cookie into the **TradingView Session ID** input field.
8. Click **Save Settings**. The status indicator in the top header will transition to **TradingView — Connected (Real-Time)**.

---

## 🛡️ Security & Token Isolation

- Your session cookies are stored exclusively in your local user configuration directory (`%APPDATA%\NewsAlerts\config.json` on Windows or `~/Library/Application Support/NewsAlerts/` on macOS).
- Cookies are **strictly isolated** from git repositories and release packages.
- The terminal communicates directly with TradingView servers via encrypted HTTPS WebSockets.
