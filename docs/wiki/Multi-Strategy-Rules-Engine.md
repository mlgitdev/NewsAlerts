# Multi-Strategy Rules Engine

NewsAlerts includes a modular **Rules Engine** that categorizes, filters, and tags momentum prints in real time based on user-defined and institutional trading strategies.

---

## 🎯 Supported Built-In Strategies (13 Active Rules)

NewsAlerts ships with 13 finely tuned strategies covering micro-cap runners, short-squeeze breakouts, and institutional momentum movers:

| Strategy Name | Trigger | Family | Default Criteria | Objective |
| :--- | :---: | :---: | :--- | :--- |
| **Low Float – Former Momo Stock** | `New HOD` | `Low Float` | Float < 20M, RelVol ≥ 1.5, 52w high ≥ 2× price | Spot explosive low-float former runners breaking out |
| **Low Float – High Rel Vol** | `New HOD` | `Low Float` | Float < 20M, RelVol ≥ 5.0 | Catch intense volume expansion in micro-caps |
| **Low Float – High Rel Vol – Price $20+** | `New HOD` | `Low Float` | Float < 20M, RelVol ≥ 5.0, Price ≥ $20 | High-dollar micro-cap runners with massive intraday range |
| **Low Float – Med Rel Vol** | `New HOD` | `Low Float` | Float < 20M, 2.0 ≤ RelVol < 5.0 | Early volume buildup in low-float setups |
| **Medium Float – High Rel Vol – Price $20+** | `New HOD` | `Med Float` | 20M ≤ Float < 100M, RelVol ≥ 5.0, Price ≥ $20 | Heavy institutional volume in mid-cap leaders |
| **Medium Float – High Rel Vol – Price under $20** | `New HOD` | `Med Float` | 20M ≤ Float < 100M, RelVol ≥ 5.0, Price < $20 | Fast mid-cap runners under $20 |
| **Medium Float – Med Rel Vol – Price $20+** | `New HOD` | `Med Float` | 20M ≤ Float < 100M, 2.0 ≤ RelVol < 5.0, Price ≥ $20 | Steady mid-cap continuation setups |
| **Large Cap / High Float – Momentum Squeeze** | `Up X% in N min` | `Large Cap` | Float ≥ 100M, 5% gain in 5 min (or change\|5 ≥ 5%) | Catch high-dollar institutional squeezes (e.g. SMCI, NVDA, TSLA) |
| **Large Cap / High Float – High Rel Vol – Price $20+** | `New HOD` | `Large Cap` | Float ≥ 100M, RelVol ≥ 2.0, Price ≥ $20 | Unusual volume flow in large-cap liquidity leaders |
| **Squeeze Alert – 52wk Breakout** | `52w Breakout` | `Squeeze` | Price ≥ 52-week High cross | Catch all-time and 52-week high short-squeeze breakouts |
| **Squeeze Alert – Up 10% in 5min** | `Up X% in N min` | `Squeeze` | 10% vertical price surge in 5 min | Extreme velocity halts and breaking catalyst surges |
| **Squeeze Alert – Up 10% in 10min** | `Up X% in N min` | `Squeeze` | 10% gain in 10 min (monotonic progression) | Sustained trend breakouts |
| **Squeeze Alert – Up 5% in 5min** | `Up X% in N min` | `Squeeze` | 5% gain in 5 min (monotonic progression) | Early velocity inflection before broader retail awareness |

---

## 🔔 Tape Header Quick-Filter Popout

Active day traders cannot afford to open full configuration modals during intense trading hours. NewsAlerts provides an instant floating **Strategy Popout Menu** docked right on the running tape header:

<p align="center">
  <a href="https://raw.githubusercontent.com/mlgitdev/NewsAlerts/main/docs/img/tape_strategies_menu.png">
    <img src="https://raw.githubusercontent.com/mlgitdev/NewsAlerts/main/docs/img/tape_strategies_menu.png" alt="Tape Strategies Quick-Filter Menu" width="380" style="border-radius:8px; border:1px solid #2a3347; box-shadow:0 8px 24px rgba(0,0,0,0.45);" />
  </a>
  <br>
  <small><em>Tape header quick-toggle dropdown: One-click strategy toggles with matching color bullets and master select/unselect.</em></small>
</p>

### Key Quick-Filter Capabilities:
1. **One-Click Toggles**: Click `🔔 Strategies 11/13` in the tape header to instantly enable or disable any strategy stream.
2. **Select / Unselect All**: Rapidly mute all strategies to focus on a single setup, or turn all on with one click.
3. **Color-Coded Bullets**: Every checkbox is paired with a distinct colored bullet matching tape row highlights:
   - 🟢 **Mint**: `Low Float`
   - 🟡 **Sand**: `Med Float`
   - 🟣 **Violet**: `Large Cap`
   - 🔵 **Cyan**: `Squeeze`
4. **Live Header Badge**: The button updates dynamically to reflect the active rule count (e.g. `Strategies 11/13`).
5. **Instant Client-Side Filtering**: Toggling strategies immediately hides or reveals historical rows on the tape without requiring a reload.

---

## ⚙️ Interactive Strategy Builder (Settings)

Traders can construct completely custom strategies using the dynamic **Strategy Builder** inside Settings → **Tape Strategies**:

<p align="center">
  <a href="https://raw.githubusercontent.com/mlgitdev/NewsAlerts/main/docs/img/strategy_builder.png">
    <img src="https://raw.githubusercontent.com/mlgitdev/NewsAlerts/main/docs/img/strategy_builder.png" alt="Interactive Strategy Builder" width="100%" style="border-radius:10px; border:1px solid #2a3347; box-shadow:0 8px 24px rgba(0,0,0,0.45);" />
  </a>
  <br>
  <small><em>Settings → Tape Strategies: Rule definition table, trigger selectors, family tags, inline export/import, and universe thresholds.</em></small>
</p>

### Strategy Builder Parameters:
- **`+ Add Strategy`**: Append a new strategy row with custom parameters.
- **Trigger Type**:
  - `New HOD`: Triggers when matching stock prints a new session high.
  - `52w Breakout`: Triggers when the price crosses the 52-week high threshold.
  - `Up X% in N min`: Evaluates rolling window price velocity.
- **Family Badges**: Categorize rules into `Low Float`, `Med Float`, `Large Cap`, `Squeeze`, or `Custom`.
- **Threshold Filters**:
  - `Float ≥` and `Float <` (e.g. `20M`, `100M`)
  - `RelVol ≥` and `RelVol <` (e.g. `1.5`, `5.0`)
  - `Price ≥` and `Price <` (e.g. `$1.00`, `$20.00`, `$50.00`)
  - `52w High Ratio ≥` (e.g. `2.0` for 52w high at least double current price)
- **Delete Strategy (`🗑️`)**: Remove unwanted strategies with one click; deletions are tracked in `deleted_strategies` so defaults never resurrect upon application restart.
- **Inline Import & Export**: One-click `💾 Export` and `📂 Import` buttons directly above the strategies table for rapid preset sharing.

---

## 📦 Backup & Sync Center

Preserve terminal configurations or share tactical momentum setups via Settings → **Backup & Sync**:

<p align="center">
  <a href="https://raw.githubusercontent.com/mlgitdev/NewsAlerts/main/docs/img/backup_sync.png">
    <img src="https://raw.githubusercontent.com/mlgitdev/NewsAlerts/main/docs/img/backup_sync.png" alt="Backup & Sync Center" width="100%" style="border-radius:10px; border:1px solid #2a3347; box-shadow:0 8px 24px rgba(0,0,0,0.45);" />
  </a>
  <br>
  <small><em>Settings → Backup & Sync: Full application backup, strategy definition sync, and destructive factory reset.</em></small>
</p>

1. **Full Application Backup (`Complete State`)**:
   - `💾 Export Full Backup (.json)`: Exports all screener presets, sound chimes, volume levels, tape universe, hotkeys, and strategies into a single JSON file.
   - `📂 Import Backup File`: Restores the complete terminal state on another machine or after a clean reinstall.
2. **Tape Strategies Only (`N Active`)**:
   - `💾 Export Strategies (.json)`: Saves only the strategy definitions to share with trading communities.
   - `📂 Import Strategies`: Imports custom strategies without altering screener filters or secret keys.
3. **Factory Reset (`Destructive`)**:
   - `↺ Restore Factory Defaults`: Restores all presets and strategies back to original factory defaults while securely preserving secrets in `keys.toml`.


