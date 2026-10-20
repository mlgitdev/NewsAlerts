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

## ⚙️ Strategy Selection & Tuning

- Open **Settings** (`S` or gear icon) and switch to the **Strategies** tab.
- Toggle individual strategies on or off with a single click.
- Each strategy features distinct color badges on the tape (Low Float = mint, Medium Float = sand, Squeeze = cyan, Large Cap = violet/purple) and dedicated sound triggers.
- Inactive strategies are suppressed from triggering audio chimes or Telegram notifications.

