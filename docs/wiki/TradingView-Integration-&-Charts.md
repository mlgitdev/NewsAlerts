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

## 📋 Cloud Watchlist Synchronization & Quick-Add (`+`)

*(New in v2.8.0)*

<p align="center">
  <a href="https://raw.githubusercontent.com/mlgitdev/NewsAlerts/main/docs/img/watchlist_sync.png">
    <img src="https://raw.githubusercontent.com/mlgitdev/NewsAlerts/main/docs/img/watchlist_sync.png" alt="TradingView Cloud Watchlist Synchronization & Quick-Add" width="100%" style="border-radius:10px; border:1px solid #2a3347; box-shadow:0 8px 24px rgba(0,0,0,0.45);" />
  </a>
  <br>
  <small><em>Live Watchlist Synchronization (v2.8.0): Clicking the <code>+</code> button next to NCPL triggers a 3-second green flickering glow (<code>✓</code>) and instantly appends the symbol to the active TradingView cloud watchlist (shown live in TradingView Desktop on the right).</em></small>
</p>

```
+------------------------------------------------------------------------------------+
| 📋 WATCHLIST: [ MomentumTrading (3)  ▾ ]  [🔄]                       [TV CLOUD]   |
+------------------------------------------------------------------------------------+
```

### 1. Watchlist Selector Bar
- **Location**: Positioned directly above the News pane (`#news-pane`).
- **Dynamic Watchlist Dropdown**: Displays all custom watchlists registered to your authenticated TradingView account, along with their current symbol count.
- **On-Demand Cloud Sync (`🔄`)**: Click the refresh button to pull any newly added watchlists or external edits without restarting the application.
- **Connection Badge**: Shows `[TV Cloud]` when authenticated with TradingView, or `[Local]` when operating in offline/fallback mode.

### 2. 1-Click Quick-Add (`+`) Buttons
Every stock symbol throughout the terminal is equipped with a high-visibility `+` quick-add button:
- **Momentum Screener Table**: Beside each symbol badge in the main scanner view.
- **Running Momentum Tape**: Directly next to the symbol in each momentum print.
- **News Header**: Next to the active inspected ticker in the catalyst wire.

### 3. Visual Flickering Feedback
To maximize trader focus and prevent workflow interruption:
- **🟢 Silent Green Flickering (3 seconds)**: When a symbol is added (or if it is already present in the target watchlist), the `+` button pulses with a vibrant institutional green glow animation and turns into `✓` for 3 seconds. No disruptive modal popups or confirmation dialogs occur.
- **🔴 Red Flickering & Toast (3 seconds)**: If session credentials expire or a network error occurs, the button pulses red (`✕`) for 3 seconds and an alert toast displays the exact diagnostic failure.

---

## 🛡️ Security & Token Isolation

- Your session cookies are stored exclusively in your local user configuration directory (`%APPDATA%\NewsAlerts\config.json` on Windows or `~/Library/Application Support/NewsAlerts/` on macOS).
- Cookies are **strictly isolated** from git repositories and release packages.
- The terminal communicates directly with TradingView servers via encrypted HTTPS WebSockets.
