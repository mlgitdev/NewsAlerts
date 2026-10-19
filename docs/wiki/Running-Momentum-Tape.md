# Running Momentum Tape & 4-Day Persistence

The **Running Momentum Tape** provides a high-velocity stream of High of Day (HOD) and Squeeze Breakout prints inspired by professional Ross Cameron / Warrior-Trading style momentum desks.

---

## 🌊 Real-Time Tape Mechanics

- **High-Velocity Prints**:
  Every time a monitored stock hits a new High of Day or triggers a surge condition, a color-coded print is pushed to the tape.
- **5-Minute Relative Volume Acceleration**:
  Prints display real-time 5-minute relative volume surges (e.g. `+42,900% 5m rVol`), signaling institutional block buying or aggressive retail retail crowding.
- **Pop-Out Detached Window**:
  Press `T` on your keyboard or click the Pop-Out icon in the Tape header to launch a dedicated, borderless floating tape window. Position the detached tape on a secondary monitor while keeping the main screener and news reader on your primary display.

---

## 💾 4-Day Local Disk Persistence

Unlike web-based scanners that erase your tape history the moment you refresh or close the browser, NewsAlerts features automated local disk persistence:

- **Storage File**: `tape_history.json` located in `%APPDATA%\NewsAlerts\` (Windows) or `~/Library/Application Support/NewsAlerts/` (macOS).
- **Capacity**: Retains up to 5,000 historical momentum prints.
- **Automatic Pruning**: Automatically purges prints older than 4 days (96 hours).
- **Off-Hours & Weekend Review**: Re-open NewsAlerts on Saturday or Sunday to study historical breakout prints, volume surges, and catalyst timings from the entire previous trading week.
