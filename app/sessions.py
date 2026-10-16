"""US market session detection and session-aware TradingView field mapping."""
from __future__ import annotations

from datetime import datetime, time
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")

PRE, REG, POST = "pre", "regular", "post"

# logical field -> TradingView column per session
SESSION_FIELDS = {
    PRE: {
        "price": "premarket_close",
        "chg": "premarket_change",
        "vol": "premarket_volume",
        "chg_open": "premarket_change_from_open",
        "gap": "premarket_gap",
        "high": "premarket_high",
        "low": "premarket_low",
    },
    REG: {
        "price": "close",
        "chg": "change",
        "vol": "volume",
        "chg_open": "change_from_open",
        "gap": "gap",
        "high": "high",
        "low": "low",
    },
    POST: {
        "price": "postmarket_close",
        "chg": "postmarket_change",
        "vol": "postmarket_volume",
        "chg_open": "postmarket_change",
        "gap": "gap",
        "high": "postmarket_high",
        "low": "postmarket_low",
    },
}

STATIC_FIELDS = {
    "float": "float_shares_outstanding",
    "mcap": "market_cap_basic",
    "relvol": "relative_volume_10d_calc",
    "relvol_t": "relative_volume_intraday|5",
    "sector": "sector",
    "exchange": "exchange",
}

# Every column we ever ask for (one request returns data for all sessions).
COLUMNS = [
    "name", "description", "logoid", "exchange", "sector", "type",
    "close", "change", "volume", "change_from_open", "gap", "high", "low", "open",
    "premarket_close", "premarket_change", "premarket_volume", "premarket_change_from_open",
    "premarket_gap", "premarket_high", "premarket_low",
    "postmarket_close", "postmarket_change", "postmarket_volume",
    "postmarket_high", "postmarket_low",
    "float_shares_outstanding", "market_cap_basic",
    "relative_volume_10d_calc", "relative_volume_intraday|5",
    "average_volume_10d_calc", "price_52_week_high", "price_52_week_low", "ATR",
    "update_mode",
]


def now_et() -> datetime:
    return datetime.now(ET)


def current_session(dt: datetime | None = None) -> str:
    """Auto session from the ET clock. Closed hours map to the most recent session."""
    dt = dt or now_et()
    if dt.weekday() >= 5:
        return POST
    t = dt.time()
    if time(4, 0) <= t < time(9, 30):
        return PRE
    if time(9, 30) <= t < time(16, 0):
        return REG
    return POST


def market_state(dt: datetime | None = None) -> str:
    dt = dt or now_et()
    if dt.weekday() >= 5:
        return "closed"
    t = dt.time()
    if time(4, 0) <= t < time(9, 30):
        return PRE
    if time(9, 30) <= t < time(16, 0):
        return REG
    if time(16, 0) <= t < time(20, 0):
        return POST
    return "closed"


def resolve(session: str) -> str:
    return current_session() if session in (None, "", "auto") else session


def tv_field(logical: str, session: str) -> str | None:
    if logical in STATIC_FIELDS:
        return STATIC_FIELDS[logical]
    return SESSION_FIELDS[session].get(logical)


def logical_row(raw: dict, session: str) -> dict:
    """Project a raw TradingView row onto session-aware logical fields."""
    out = {k: raw.get(v) for k, v in STATIC_FIELDS.items()}
    for k, v in SESSION_FIELDS[session].items():
        out[k] = raw.get(v)
    if out["price"] is None:  # e.g. no post-market prints yet
        out["price"] = raw.get("close")
    return out
