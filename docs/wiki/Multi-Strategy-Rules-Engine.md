# Multi-Strategy Rules Engine

NewsAlerts includes a modular **Rules Engine** that categorizes and tags momentum prints based on predefined trading strategies.

---

## 🎯 Supported In-App Strategies

1. **Low Float Momo (`low_float_momo`)**:
   - **Float**: < 10,000,000 shares.
   - **Price**: $1.00 – $20.00.
   - **Change**: >= +10.0%.
   - **Objective**: Identify explosive low-float micro-caps prone to massive percentage surges.

2. **Squeeze 52-Week Breakout (`squeeze_52w`)**:
   - **Criteria**: Stock breaching 52-week highs with heavy volume and `HTB` or `NO BORROW` status.
   - **Objective**: Target aggressive short squeeze cascades where short sellers are trapped.

3. **Velocity Surges (5% / 10%)**:
   - **5% Velocity Surge**: Rapid 5% price movement within a rolling 5-minute window.
   - **10% Velocity Surge**: Exceptional 10% vertical price expansion signaling breaking news or halts.

---

## ⚙️ Strategy Selection & Tuning

- Open **Settings** (`S` or gear icon) and switch to the **Strategies** tab.
- Toggle individual strategies on or off with a single click.
- Each strategy features distinct color badges on the tape and dedicated sound triggers.
- Inactive strategies are suppressed from triggering audio chimes or Telegram notifications.
