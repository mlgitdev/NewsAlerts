# NewsAlerts — Momentum Screener, Tape & News

<p align="center">
  <img src="assets/hero.jpg" alt="NewsAlerts Hero Banner" width="100%" style="border-radius:12px; border:1px solid #2a3347; box-shadow:0 12px 36px rgba(0,0,0,0.55);" />
</p>

<p align="center">
  <img src="assets/app_icon_transparent.png" alt="NewsAlerts Logo" width="80" height="80" style="vertical-align:middle; margin-right:12px;" />
  <br>
  <b>Institutional-grade, real-time US small-cap momentum screener, high-of-day tape, and news intelligence terminal.</b>
</p>

---

## Key Features

- 🚨 **Instant Audio & Telegram Alerts**: Fires on newly discovered momentum symbols matching user-defined screen criteria.
- 🔔 **Unified Alert Control (The Bell)**: One-click master toggle that both mutes audio chimes and pauses Telegram alert dispatching.
- 🔊 **Visual Rising Triangle Volume Control**: Smoothly scrub chime volume from 0% to 100% with real-time per-process Windows WinMM audio scaling.
- 🌊 **Real-Time Running Tape**: Warrior-Trading style High of Day (HOD) and Squeeze Breakout momentum tape with 4-day local disk persistence for off-hours and weekend review.
- 🩳 **Short Borrow Locates**: Real-time `HTB` (Hard to Borrow), `ETB` (Easy to Borrow), and `NO BORROW` indicators powered by live Alpaca API and TradingView market feeds.
- 📰 **Recent News Intelligence**: Direct Benzinga and financial wire headlines with configurable recency windows (1h, 2h, 4h, 8h, 12h, 24h, 3d, 7d).
- 📦 **100% Portable Executable**: Runs anywhere on 64-bit Windows without installing Python or Node.js. All data persists to `%APPDATA%\NewsAlerts\`.

---

## Portable Build & Run

### Quick Run
```powershell
.\build.ps1 -Task run
```

### Recompile Standalone Portable Executable
```powershell
.\build.ps1 -Task build
```
The output executable will be created at `dist\NewsAlerts.exe` (~13 MB) bundled with the new custom application icon.
