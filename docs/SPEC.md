# NewsAlerts — Momentum Screener, Tape & News (Windows desktop)

## 1. Goal
A lightweight Windows desktop app that replicates the TradingView stock screener workflow
(small-float momentum), and adds what TradingView lacks:

1. **A bell** when a new symbol enters the screener table.
2. **A news pane** (Benzinga-first) showing *very recent* news for the clicked symbol.
3. **A running tape** (Warrior-Trading style "Small Cap – High of Day Momentum") driven by
   predefined, toggleable strategies.

## 2. Tech stack
| Layer | Choice | Why |
|---|---|---|
| Backend | Python 3.11 (native Windows, no container) | Already installed, simple |
| Window | `pywebview` (WebView2 / Edge) | Native window, ~no footprint, no Node/Electron |
| Frontend | Vanilla HTML/CSS/JS | No build step |
| HTTP | `requests` | Scanner + news calls |
| Sounds | `winsound` + `C:\Windows\Media\*.wav` | Native Windows sounds, zero deps |
| Time | `zoneinfo` + `tzdata` | Session detection in America/New_York |
| Config | JSON in `%APPDATA%\NewsAlerts\config.json` | Persist screens, filters, sounds, cookie |

Run: `run.bat` → creates venv on first run → `python -m app.main`.

## 3. Data sources
### 3.1 Screener — TradingView scanner (US Market Only)
- `POST https://scanner.tradingview.com/america/scan` (the endpoint the TV web screener uses).
- **US Only**: Hard-filtered to US common equities:
  `country = "United States"`, `type = "stock"`, `exchange in ["AMEX", "NASDAQ", "NYSE"]`, `is_primary = true`.
  Excludes ADRs, foreign shares, OTC, and funds.
- Auth: user pastes `sessionid` (+ optional `sessionid_sign`) cookie from tradingview.com in
  Settings → real-time data for subscribers. Without it data is 15-min delayed.
- **TradingView Connection Status Badge**: Positioned in the main window top-right corner directly to the left of the session & market status pill:
  - `[▲ TradingView — Connected]` (🟢 **Green**): Session cookies are active and verified against TradingView; displays verified username and subscription tier on hover.
  - `[▲ TradingView — Disconnected]` (🔴 **Red**): Session cookies are missing, invalid, or expired. Clicking opens Settings directly to the TradingView credentials tab.
- The app reads the `update_mode` field and shows a **REALTIME / DELAYED** badge in the status bar.
- Default poll interval: **3 s** (configurable 1–30 s). Backoff on HTTP 429/5xx.

### 3.2 News — TradingView news feed (includes Benzinga)
- Headlines: `GET https://news-headlines.tradingview.com/v2/headlines?symbol=EXCH:TICKER&lang=en`
- Story body: `GET https://news-headlines.tradingview.com/v2/story?id=<id>&lang=en`
  (AST → rendered HTML in-app; "Open in browser" button for the original link).
- Provider filter: **Benzinga only** / All providers (default: All, Benzinga highlighted).
- Recency filter: default **last 12 h** (options: 1 h, 4 h, 12 h, since prev close, 24 h).
- Pluggable `NewsProvider` interface so an official Benzinga API key can be added later.

### 3.3 Short Borrow Availability Indicator (Easy / Hard / No Borrow / NA)
Displays a color-coded status badge directly next to each symbol in both the Screener and the Tape:
- **Easy to Borrow (ETB)**: 🔴 **Red** (`easy is read`) — Easy for shorters to dump / high supply
- **Hard to Borrow (HTB)**: 🟡 **Yellow** (`hard yellow`) — Limited supply / locate fee required
- **No Borrow Available**: 🟢 **Green** (`no borrow is green`) — No shares available to short / highest squeeze potential
- **N/A / Unknown**: 🟠 **Orange** (`na data orange`) — Data unavailable or symbol unlisted for locate
- **Data Source**: Integrated with Alpaca Broker API (free paper account keys in Settings / secrets) for real-time broker locates (`borrow_status: hard_to_borrow` -> HTB Yellow, `easy_to_borrow` -> ETB Red), with an intelligent float-based heuristic fallback (float < 500K = No Borrow, 500K–50M = HTB, > 50M = ETB).

## 4. Market sessions
Session selector: **Auto | Pre-market | Regular | Post-market** (Auto uses ET clock:
Pre 04:00–09:30, Regular 09:30–16:00, Post 16:00–20:00, otherwise "Closed" → last session).

Every session-aware filter/column maps to a different TradingView field:

| Logical field | Pre-market | Regular | Post-market |
|---|---|---|---|
| Price | `premarket_close` | `close` | `postmarket_close` |
| Chg % | `premarket_change` | `change` | `postmarket_change` |
| Volume | `premarket_volume` | `volume` | `postmarket_volume` |
| Chg from open % | `premarket_change_from_open` | `change_from_open` | `postmarket_change` |
| Gap % | `premarket_gap` | `gap` | `gap` |
| High | `premarket_high` | `high` | `postmarket_high` |

Non-session fields: `float_shares_outstanding`, `market_cap_basic`, `sector`,
`relative_volume_10d_calc` (Rel vol), `relative_volume_intraday|5` (Rel vol at time),
`price_52_week_high/low`, `change|5`, `change|15`, `average_volume_10d_calc`.

## 5. Window layout
```
┌──────────────────────────────────────────────────────────────────────────┐
│ [Screen tabs: 2-10 small floats ▾ | + ]   Session [Auto▾]  🔔  ⚙  ● RT  │
│ Filter chips: [Float 300K–25M ×] [Price 1–20 ×] [Chg% >10 ×] [Vol >50K ×]│
│              [Rel vol ≥ … ×] [+ add filter]                               │
├───────────────────────────────────────────────┬──────────────────────────┤
│ SCREENER TABLE                                │ NEWS  (symbol: TCRT)      │
│ Sym | Name | Price | Chg% | S.Price | S.Chg% |│ [Benzinga only ☐] [12h▾]  │
│ Float | S.Vol | Vol | RelVol@t | RelVol |     │ • 08:14  Benzinga  Why is │
│ MktCap | Sector | 📰 | First seen             │   … expandable story      │
├───────────────────────────────────────────────┴──────────────────────────┤
│ TAPE — Small Cap High of Day Momentum   [Strategies ▾] [⏸] [⧉ pop-out]   │
│ Time | Sym | Price | Vol | Float | RelVol | RelVol5m% | Chg% | Gap |...   │
└──────────────────────────────────────────────────────────────────────────┘
```
- Panes are resizable (drag splitters); sizes persisted.
- Tape can pop out into its own window (second pywebview window).
- Dark theme matching TradingView look.

## 6. Screener
### 6.1 Screens (presets)
- Multiple named screens (tabs); each has its own filters, sort, session, columns and alert settings.
- Shipped default: **"2-10 small floats"** = Float 300K–25M, Price 1–20, Chg% > 10, Vol > 50K
  (session-aware). Rename / duplicate / delete supported.

### 6.2 Filters (all editable)
Each filter is a chip; click to edit min/max, × to remove, "+" to add.

| Filter | Type | Session-aware |
|---|---|---|
| Price | range | ✓ |
| Chg % | range | ✓ |
| Volume | range | ✓ |
| Chg from open % | range | ✓ |
| Gap % | range | ✓ |
| Float | range | |
| Market cap | range | |
| Rel vol | range (always visible, quick edit) | |
| Rel vol at time | range | |
| Sector | multi-select | |
| Exchange | multi-select (NASDAQ/NYSE/AMEX), OTC excluded by default | |

Values accept suffixes `K`, `M`, `B` (e.g. `300K`, `25M`).

### 6.3 Columns (default order)
Symbol · Name · Price · Chg % · *Session* price · *Session* chg % · Float · *Session* vol · Vol ·
Rel vol at time · Rel vol · Mkt cap · Sector · 📰 (recent-news flag) · First seen.

In Regular session the "Session" columns are hidden (they duplicate Price/Chg/Vol).
Click header to sort; sort persisted per screen. Positive values green, negative red.

### 6.4 New-symbol alert (the bell)
- Each poll diffs the symbol set against the previous poll.
- **New symbol** = not in table in the last *N* minutes (re-entry window, default 15 min).
- On new symbol: play selected sound, row flashes (yellow pulse 3 s), "NEW" badge for 60 s,
  window title shows count, entry added to an alert log.
- First load of a screen (or after filter edits) does **not** alert (seeds silently).
- Per-screen 🔔 toggle; global mute; quiet when the window is focused (optional).
- Background fetch of headlines for new symbols → 📰 flag if news within recency window.
  Optional separate sound for "new symbol has fresh news".

### 6.5 Click → news
Clicking a row selects it and loads news in the right pane (§7).

## 7. News pane
- Header: symbol, name, price/chg.
- List of headlines within recency window, newest first: time (ET, + "12m ago"), provider badge
  (Benzinga highlighted orange), title.
- Click headline → expands inline story text; "Open" opens original URL in default browser.
- Auto-refresh every 30 s while symbol selected; new headline → subtle highlight (+ optional sound).
- Empty state: "No news in last 12h".

## 8. Tape (running momentum events)
### 8.1 Universe & engine
- Separate scanner query (every 2 s): US stocks, price 1–50, session chg% > 3, session vol > 20K,
  top 300 by chg%. (Editable in Settings.)
- Engine keeps a rolling in-memory history per symbol: `(ts, price, volume, high)` for 30 min.
- **Event** = a symbol matching ≥1 enabled strategy AND one of:
  - makes a **new high of day** (session-aware high) vs the previous poll, or
  - triggers a squeeze condition (§8.2), with per-symbol/per-strategy cooldown (default 30 s). **Monotonic Window Progression**: During an active time window (e.g. 5 min / 10 min), subsequent triggers for the same symbol & strategy require strictly higher prices (`price > last_alert_price`). If the price falls or is flat vs the previous trigger, alerts are suppressed; once the time window resets (`now - last_alert_time >= window_min * 60`), a new squeeze cycle can begin.
- **Persistent Storage & Off-Hours Review**: Tape alerts are automatically saved to `%APPDATA%\NewsAlerts\tape_history.json` and retained for at least 4 days (configurable). When the app restarts, reloads, or opens during off-hours / weekends, all historical alerts are immediately loaded into the tape for retrospective review.
- **Timestamp Formatting**: Displays `H:MM:SS am/pm` for alerts triggered today, and `MMM DD H:MM am/pm` for older alerts, with full ET date/time and relative age tooltips.
- Newest events on top; up to 3,000 scrollable rows; ⏸ pause freezes scrolling and shows "New events ↑"; 🗑️ clear button removes history.

### 8.2 Predefined strategies (toggle list like the Warrior screenshot)
| Strategy | Rule (defaults, all editable in Settings) |
|---|---|
| Low Float – Former Momo Stock | float < 20M, 52w high ≥ 2× price, rel vol ≥ 1.5 |
| Low Float – High Rel Vol | float < 20M, rel vol ≥ 5 |
| Low Float – High Rel Vol – Price $20+ | float < 20M, rel vol ≥ 5, price ≥ 20 |
| Low Float – Med Rel Vol | float < 20M, 2 ≤ rel vol < 5 |
| Medium Float – High Rel Vol – Price $20+ | 20M ≤ float < 100M, rel vol ≥ 5, price ≥ 20 |
| Medium Float – High Rel Vol – Price under $20 | 20M ≤ float < 100M, rel vol ≥ 5, price < 20 |
| Medium Float – Med Rel Vol – Price $20+ | 20M ≤ float < 100M, 2 ≤ rel vol < 5, price ≥ 20 |
| Squeeze Alert – 52wk Breakout | price ≥ 52w high (fires on cross) |
| Squeeze Alert – Up 10% in 10min | price ≥ 1.10 × lowest price in last 10 min (up-only within active 10m window) |
| Squeeze Alert – Up 5% in 5min | price ≥ 1.05 × lowest price in last 5 min (up-only within active 5m window) |

### 8.3 Tape columns
Time · Symbol (click → news) · Price · Volume · Float · Rel Vol (daily) · Rel Vol 5m % ·
Chg % · Gap % · Pos in 52w range % · Range today % · Strategy name.

### 8.4 Colors
Row background per strategy family (Low Float = mint, Medium Float = sand, Squeeze = cyan),
volume cell darker the larger the volume, float cell green when < 20M.
Optional tape sound (default off — the tape is noisy).

### 8.5 Telegram Push Alerts for Tape Momentum
- **Real-Time Push Notifications**: When momentum tickers print on the Tape (e.g. `NCPL` popping up on HOD / low-float runner), an instant Telegram push alert is dispatched to the user's configured chat.
- **Rich Message Format**: Includes Symbol, Strategy name, Session, Price, Change %, Volume, Float, Relative Volume (daily + 5m%), Short Borrow Status (`HTB` / `ETB` / `NO BORROW` / `N/A`), 52w range position, and a direct TradingView chart link.
- **Per-Symbol Cooldown**: A per-ticker cooldown (default 60s, configurable in Settings) prevents rapid duplicate push notifications when a runner repeatedly prints new HODs in seconds.

## 9. Sounds
- Settings lists all `.wav` in `C:\Windows\Media` (Windows Notify, Ding, chimes, Alarm01–10, …).
- Separate pickers: **New screener symbol**, **New news**, **Tape event**; ▶ test button each.
- Played async via `winsound.PlaySound(path, SND_FILENAME | SND_ASYNC)`; throttled to 1 per 1.5 s.

## 10. Settings & Integrations
TradingView `sessionid`/`sessionid_sign` & real-time connection status · poll intervals · re-entry window · news recency & provider · sounds · tape universe & strategy thresholds · Alpaca keys for short borrow locates · Telegram Bot Token, Chat ID, and independent toggles for Screener alerts and Tape momentum alerts (with per-symbol cooldown) · always-on-top · font size.

## 11. Architecture
```
app/
  main.py        – starts pywebview windows, wires API + workers
  api.py         – JS↔Python bridge (pywebview js_api)
  config.py      – load/save %APPDATA%\NewsAlerts\config.json, defaults
  sessions.py    – ET clock, session detection, field mapping
  tv_client.py   – scanner + news HTTP client (cookie, retries, backoff)
  screener.py    – screen poller, query builder, diff / new-symbol detection
  tape.py        – tape universe poller, rolling history, strategy engine, telegram push
  news.py        – NewsProvider interface, TradingView provider, Alpaca provider, cache, AST→HTML
  borrow.py      – short borrow locate service (Alpaca + TV + heuristics fallback)
  telegram.py    – Telegram Bot API integration for Screener & Tape push notifications
  sounds.py      – list Windows sounds, throttled async playback
web/
  index.html, tape.html
  css/app.css
  js/app.js, screener.js, news.js, tape.js, settings.js, util.js
```
- Workers are daemon threads; they push updates to the UI with
  `window.evaluate_js("App.onScreener(<json>)")` etc.
- UI calls Python through `window.pywebview.api.*` (get/save config, select symbol, test sound…).

## 12. Portable Executable & Build Automation
### 12.1 Standalone Portable Executable (`dist\NewsAlerts.exe`)
- **Self-Contained**: Single `.exe` (~13 MB) bundling Python 3.11, pywebview (WebView2 Edge Chromium), bottle, requests, zoneinfo/tzdata, and frontend HTML/CSS/JS assets (`web/`).
- **Zero Installation Required**: Runs on any 64-bit Windows machine without requiring Python, Git, or Node.js.
- **AppData Persistence**: All user state and collected data are stored in `%APPDATA%\NewsAlerts\`:
  - `config.json` — User screen filters, column order, session cookies, Alpaca keys, Telegram settings.
  - `tape_history.json` — 4-day rolling tape alerts log for off-hours and weekend review.
  - `app.log` — Application logs and diagnostic traces.
  - `webview/` — Edge WebView2 profile, local storage, and cookies.
- **Strict Secrets Isolation**: Zero development keys or credentials are baked into the executable. `secrets/` is explicitly excluded during packaging. Users configure credentials via:
  - The in-app **Settings modal** (saved securely to `%APPDATA%\NewsAlerts\config.json`).
  - Or by placing an optional `keys.toml` in `%APPDATA%\NewsAlerts\` or alongside `NewsAlerts.exe`.

### 12.2 Build Automation (`build.ps1`, `Makefile`, `build.bat`)
- **PowerShell Script (`build.ps1`)**:
  - `.\build.ps1 -Task build` — Builds `dist\NewsAlerts.exe` via PyInstaller using `NewsAlerts.spec`.
  - `.\build.ps1 -Task clean` — Purges `build/`, `dist/`, and Python cache artifacts.
  - `.\build.ps1 -Task run` — Launches the compiled `dist\NewsAlerts.exe`.
  - `.\build.ps1 -Task check` — Audits the build archive to guarantee no secrets were bundled.
- **Makefile**: Provides standard `make build`, `make clean`, `make run`, and `make check` commands.
- **Batch Script (`build.bat`)**: Double-clickable command wrapper for native Windows cmd.

## 13. Non-goals (v1)
Order entry, charts, historical backtests, non-US markets, Docker packaging.

## 14. Future
Official Benzinga API provider · Windows toast notifications · mini chart on symbol click · per-symbol notes / watchlist.

