# Welcome to the NewsAlerts Wiki

**NewsAlerts** is an institutional-grade, zero-bloat financial momentum terminal engineered specifically for active US small-cap day traders.

Built on a native, ultra-responsive architecture (`pywebview` + Vanilla ES6+/CSS with zero Node.js / Electron overhead), NewsAlerts bridges the critical execution gap between bloated broker platforms (Interactive Brokers TWS / Desktop) and charting platforms (TradingView) where news catalysts often lag by 5 to 15 minutes.

---

## ⚡ Quick Navigation

| Topic | Description |
| :--- | :--- |
| **[TradingView Integration & Charts](TradingView-Integration-&-Charts)** | Real-time session feeds & **One-Click Chart Popout** via the news pane icon |
| **[Real-Time Momentum Screener](Real-Time-Momentum-Screener)** | Sub-second low-float screener, live `NEW` badges, dynamic criteria filtering |
| **[Running Momentum Tape](Running-Momentum-Tape)** | Warrior-Trading style HOD & squeeze breakout prints with 4-day disk persistence |
| **[Multi-Strategy Rules Engine](Multi-Strategy-Rules-Engine)** | Granular strategy selection (Low Float Momo, Squeeze 52wk, velocity surges) |
| **[Catalyst News Wire & Benzinga](Catalyst-News-Wire-&-Benzinga)** | Zero-lag wire PRs (beating the 15-minute retail delay) and story reader |
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

3. **Multi-Strategy Inbound Audio Chimes**:
   Active traders cannot watch multiple screens continuously. NewsAlerts rings an instant auditory chime the exact second a ticker enters your strategy criteria, alerting you before volume cascades onto retail scanners.

4. **Institutional Short Locates**:
   Direct integration with Alpaca Brokerage locate APIs surfaces real-time `ETB` (Easy to Borrow), `HTB` (Hard to Borrow), and `NO BORROW` badges on every screener row and tape print, exposing high-probability short-squeeze opportunities instantly.
