# Welcome to the NewsAlerts Wiki

**NewsAlerts** is an institutional-grade, zero-bloat financial momentum terminal engineered specifically for active US small-cap day traders.

Built on a native, ultra-responsive architecture (`pywebview` + Vanilla ES6+/CSS with zero Node.js / Electron overhead), NewsAlerts bridges the critical execution gap between bloated broker platforms (Interactive Brokers TWS / Desktop) and charting platforms (TradingView) where news catalysts often lag by 5 to 15 minutes.

<p align="center">
  <a href="https://raw.githubusercontent.com/mlgitdev/NewsAlerts/main/docs/img/terminal.png">
    <img src="https://raw.githubusercontent.com/mlgitdev/NewsAlerts/main/docs/img/terminal.png" alt="NewsAlerts Real-Time Momentum Terminal" width="100%" style="border-radius:10px; border:1px solid #2a3347; box-shadow:0 10px 30px rgba(0,0,0,0.5);" />
  </a>
  <br>
  <small><em>Live institutional terminal capture (v2.7.0): Real-time screener, high-of-day momentum tape with large-cap & small-cap squeeze prints, custom symbol search bar, and catalyst news wire.</em></small>
</p>

---

## ⚡ Quick Navigation

| Topic | Description |
| :--- | :--- |
| **[TradingView Integration & Charts](TradingView-Integration-&-Charts)** | Real-time session feeds, **Cloud Watchlist Sync**, and **One-Click Chart Popout** |
| **[Real-Time Momentum Screener](Real-Time-Momentum-Screener)** | Sub-second low-float screener, live `NEW` badges, dynamic criteria filtering |
| **[Running Momentum Tape](Running-Momentum-Tape)** | Warrior-Trading style HOD & squeeze breakout prints with 4-day persistence & quick-filter dropdown |
| **[Multi-Strategy Rules Engine](Multi-Strategy-Rules-Engine)** | Interactive Strategy Builder (`+ Add Strategy`), 13 built-in rules, trigger types, and Backup & Sync |
| **[Catalyst News Wire & Benzinga](Catalyst-News-Wire-&-Benzinga)** | Zero-lag wire PRs, custom US equity ticker search bar (`#news-sym-input`), and watchlist chips |
| **[Short Borrow Locates](Short-Borrow-Locates-(Alpaca-&-TradingView))** | Live broker-grade `ETB`, `HTB`, and `NO BORROW` badges for short squeeze edge |
| **[Audio Alerts & Volume Control](Audio-Alerts-&-Volume-Controls)** | Instant audio chimes, visual rising triangle scrubber, master bell mute |
| **[Telegram Push Notifications](Telegram-Push-Notifications)** | Sub-second asynchronous push alerts with full stats and one-click chart links |
| **[Configuration & Secrets Guide](Configuration-&-Secrets-Guide)** | Managing `keys.toml`, Alpaca API keys, Telegram tokens, and AppData isolation |
| **[Keyboard Shortcuts & Hotkeys](Keyboard-Shortcuts-&-Hotkeys)** | Full hotkey guide for rapid keyboard navigation (`M`, `T`, `Space`, `S`, `Esc`) |
| **[Building & Packaging From Source](Building-&-Packaging-From-Source)** | PyInstaller compilation, cross-platform Makefile, and verification gate |

---

## 🎯 Core Trading Edge

1. **Zero-Lag Catalyst Discovery**:
   Retail charting platforms like TradingView frequently experience 5 to 15-minute news feed delays. In fast momentum runners, a 15-minute delay is the difference between catching a breakout at the base or buying the top into institutional profit taking. NewsAlerts connects directly to live wire catalysts (Benzinga, GlobeNewswire, PR Newswire) the split second they cross.

2. **One-Click Chart Launching**:
   No need to manually type ticker symbols into separate charting windows. The News pane features a dedicated **Chart Icon** (`#news-chart`) in the symbol header that immediately pops open the full TradingView interactive chart for the active ticker in your browser.

3. **Multi-Strategy Inbound Audio Chimes & Quick-Filter**:
   Active traders cannot watch multiple screens continuously. NewsAlerts rings an instant auditory chime the exact second a ticker enters your strategy criteria. Traders can toggle strategies directly on the tape header (`Strategies 11/13`) without entering settings.

4. **Interactive Strategy Builder & Preset Sharing**:
   Full in-terminal Strategy Builder (`+ Add Strategy`) in Settings with trigger selection (`New HOD`, `52w Breakout`, `Up X% in N min`), family tagging, and inline portable JSON import/export.

5. **Institutional Short Locates**:
   Direct integration with Alpaca Brokerage locate APIs surfaces real-time `ETB` (Easy to Borrow), `HTB` (Hard to Borrow), and `NO BORROW` badges on every screener row and tape print, exposing high-probability short-squeeze opportunities instantly.

6. **Full State Backup & Disaster Recovery**:
   The Backup & Sync Center allows traders to export full application backups, synchronize tactical strategies independently, or execute clean factory resets while securely preserving user API keys.
