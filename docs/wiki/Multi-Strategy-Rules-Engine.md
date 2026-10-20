# Multi-Strategy Rules Engine

NewsAlerts includes a modular **Rules Engine** that categorizes and tags momentum prints based on predefined trading strategies.

---

## 🎯 Supported In-App Strategies

1. **Low Float Momo (`low_float_momo`)**:
   - **Float**: < 10,000,000 shares.
   - **Price**: $1.00 – $20.00.
   - **Change**: >= +10.0%.
   - **Objective**: Identify explosive low-float micro-caps prone to massive percentage surges.

2. **Large-Cap / High-Float Momo (`large_cap_momo`)**:
   - **Float**: ≥ 100,000,000 shares.
   - **Price**: $20.00 – $500.00+.
   - **Relative Volume**: ≥ 2.0x.
   - **Objective**: Capture institutional momentum in high-profile runners like SMCI, NVDA, TSLA, and AMD when catalyst news breaks.

3. **Squeeze 52-Week Breakout (`squeeze_52w`)**:
   - **Criteria**: Stock breaching 52-week highs with heavy volume and `HTB` or `NO BORROW` status.
   - **Objective**: Target aggressive short squeeze cascades where short sellers are trapped.

4. **Velocity Surges (5% / 10% in 5 min & 10 min)**:
   - **Squeeze Alert – Up 5% in 5min**: Rapid 5% price movement within a rolling 5-minute window or TradingView `change|5 ≥ 5%`.
   - **Squeeze Alert – Up 10% in 5min**: High-velocity 10% vertical price expansion in 5 minutes signaling breaking earnings or explosive catalyst halts.
   - **Squeeze Alert – Up 10% in 10min**: Sustained 10% vertical momentum expansion over a 10-minute window.

---

## ⚙️ Interactive Strategy Builder & Customization

NewsAlerts includes a dynamic **Strategy Builder** inside Settings → **Tape Strategies**:
- **Add Custom Strategy (`+ Add Strategy`)**: Add unlimited personalized momentum strategies with custom float ranges, relative volume thresholds, price filters, 52-week breakout ratios, and surge velocity windows.
- **Trigger Type Selection**:
  - `New HOD`: Triggers when matching stock prints a new session high.
  - `52w Breakout`: Triggers on 52-week high cross.
  - `Up X% in N min`: Evaluates percent surge over rolling window.
- **Family Badges**: Categorize as `Low Float` (mint), `Med Float` (sand), `Large Cap` (violet), `Squeeze` (cyan), or `Custom` (blue).
- **Delete Strategy (`🗑️`)**: Remove unwanted strategies with one click; deletions are tracked in `deleted_strategies` so factory defaults do not resurrect.
- **Portable JSON Sync**: Export strategies (`💾 Export`) to share with other traders or import community strategy presets (`📂 Import`).

---

## 📦 Backup & Sync Center

Access the dedicated **Backup & Sync** tab in Settings for full state preservation:
- **Full Configuration Backup (`.json`)**: Export screeners, audio alerts, volume levels, hotkeys, and strategies into a portable backup file for disaster recovery or machine migration.
- **Strategy Preset Import/Export**: Share or import trading strategies independently.
- **Factory Reset Safeguard**: Revert settings back to factory defaults at any time with one click.


