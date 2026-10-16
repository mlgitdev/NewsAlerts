"""Short borrow status service (Easy-to-borrow, Hard-to-borrow, No-borrow, N/A).

Determines borrowability for shorters with user-specified color coding:
- Easy to borrow (ETB)  -> RED ("easy is read")
- Hard to borrow (HTB)  -> YELLOW ("hard yellow")
- No borrow available   -> GREEN ("no borrow is green")
- Data unavailable (NA) -> ORANGE ("na data orange")

Supports Alpaca Broker Assets API (live real-time ETB/HTB/shortable flags)
with an intelligent float-based heuristic fallback when no API key is set.
"""
from __future__ import annotations

import logging
import queue
import threading
import time
from pathlib import Path
from typing import Callable

import requests

try:
    import tomllib
except ImportError:  # pragma: no cover
    import tomli as tomllib  # type: ignore

log = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent
SECRETS_PATH = ROOT_DIR / "secrets" / "keys.toml"

STATUS_EASY = "easy"       # Easy to borrow -> Red
STATUS_HARD = "hard"       # Hard to borrow -> Yellow
STATUS_NONE = "none"       # No borrow      -> Green
STATUS_NA = "na"           # NA data        -> Orange

LABEL_MAP = {
    STATUS_EASY: "ETB",
    STATUS_HARD: "HTB",
    STATUS_NONE: "NO BORROW",
    STATUS_NA: "N/A",
}


def load_alpaca_secrets() -> tuple[str, str]:
    if SECRETS_PATH.exists():
        try:
            with open(SECRETS_PATH, "rb") as f:
                data = tomllib.load(f)
                alp = data.get("alpaca", {})
                k = alp.get("tradingApi_key") or alp.get("brockerApi_sandbox1_api_key") or ""
                s = alp.get("tradingApi_secret") or alp.get("brockerApi_sandbox1_api_secret") or ""
                return str(k).strip(), str(s).strip()
        except Exception:
            pass
    return "", ""


class BorrowService:
    def __init__(self, key_id: str = "", secret_key: str = "", mode: str = "auto") -> None:
        if not (key_id and secret_key):
            k, s = load_alpaca_secrets()
            key_id = key_id or k
            secret_key = secret_key or s
        self.key_id = key_id.strip()
        self.secret_key = secret_key.strip()
        self.mode = mode  # "auto", "alpaca", "heuristic"
        self._cache: dict[str, dict] = {}
        self._details: dict[str, dict] = {}
        self._lock = threading.RLock()
        self.q: "queue.Queue[tuple[str, float | None, Callable | None]]" = queue.Queue()
        self._worker_thread = threading.Thread(target=self._worker, daemon=True, name="borrow-fetch")
        self._worker_thread.start()
        if self.key_id and self.secret_key and self.mode in ("auto", "alpaca"):
            self._sync_thread = threading.Thread(target=self._sync_bulk_assets, daemon=True, name="alpaca-bulk-assets")
            self._sync_thread.start()

    def update_credentials(self, key_id: str, secret_key: str, mode: str = "auto") -> None:
        with self._lock:
            if not (key_id and secret_key):
                k, s = load_alpaca_secrets()
                key_id = key_id or k
                secret_key = secret_key or s
            self.key_id = (key_id or "").strip()
            self.secret_key = (secret_key or "").strip()
            self.mode = mode
            if self.key_id and self.secret_key and self.mode in ("auto", "alpaca"):
                threading.Thread(target=self._sync_bulk_assets, daemon=True, name="alpaca-bulk-assets").start()

    def _sync_bulk_assets(self) -> None:
        """Fetch all active US equity assets from Alpaca to pre-populate locate data in memory."""
        try:
            url = "https://paper-api.alpaca.markets/v2/assets?status=active&asset_class=us_equity"
            headers = {
                "APCA-API-KEY-ID": self.key_id,
                "APCA-API-SECRET-KEY": self.secret_key,
            }
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200:
                assets = r.json()
                with self._lock:
                    for a in assets:
                        sym = str(a.get("symbol", "")).upper()
                        etb = bool(a.get("easy_to_borrow", False))
                        shortable = bool(a.get("shortable", False))
                        if etb:
                            st = STATUS_EASY
                        elif shortable:
                            st = STATUS_HARD
                        else:
                            st = STATUS_NONE
                        self._cache[sym] = {"status": st, "label": LABEL_MAP[st], "source": "alpaca"}
                        self._details[sym] = {
                            "exchange": a.get("exchange", ""),
                            "marginable": a.get("marginable", False),
                            "fractionable": a.get("fractionable", False),
                            "etb": etb,
                            "shortable": shortable,
                        }
                log.info("Synced %d active US equities from Alpaca for instant locate resolution", len(assets))
        except Exception as e:
            log.warning("Bulk asset sync from Alpaca failed: %s", e)

    def get_status(self, symbol: str, float_shares: float | None = None) -> dict:
        """Returns cached status immediately or returns best estimate and enqueues lookup."""
        sym = symbol.split(":")[-1].upper().strip()
        with self._lock:
            if sym in self._cache:
                return self._cache[sym]

        # Immediate estimate
        est = self._estimate(sym, float_shares)
        with self._lock:
            self._cache[sym] = est

        # Request background live resolution if Alpaca API credentials available
        if self.key_id and self.secret_key and self.mode in ("auto", "alpaca"):
            self.q.put((sym, float_shares, None))

        return est

    def get_details(self, symbol: str) -> dict:
        sym = symbol.split(":")[-1].upper().strip()
        with self._lock:
            return self._details.get(sym, {})

    def get_snapshot(self, symbol: str) -> dict | None:
        """Fetches real-time snapshot (Bid, Ask, Sizes, VWAP, last trade) from Alpaca."""
        if not (self.key_id and self.secret_key):
            return None
        sym = symbol.split(":")[-1].upper().strip()
        url = f"https://data.alpaca.markets/v2/stocks/snapshots?symbols={sym}"
        headers = {
            "APCA-API-KEY-ID": self.key_id,
            "APCA-API-SECRET-KEY": self.secret_key,
        }
        try:
            r = requests.get(url, headers=headers, timeout=5)
            if r.status_code == 200:
                data = r.json().get(sym)
                if not data:
                    return None
                q = data.get("latestQuote") or {}
                t = data.get("latestTrade") or {}
                m = data.get("minuteBar") or {}
                d = data.get("dailyBar") or {}
                pd = data.get("prevDailyBar") or {}
                return {
                    "bid": q.get("bp"),
                    "ask": q.get("ap"),
                    "bid_size": q.get("bs"),
                    "ask_size": q.get("as"),
                    "last_trade_price": t.get("p"),
                    "last_trade_size": t.get("s"),
                    "vwap": m.get("vw") or d.get("vw"),
                    "prev_close": pd.get("c"),
                    "daily_volume": d.get("v"),
                }
        except Exception as e:
            log.warning("Alpaca snapshot query for %s failed: %s", sym, e)
        return None

    def enqueue(self, symbol: str, float_shares: float | None = None, cb: Callable | None = None) -> None:
        sym = symbol.split(":")[-1].upper().strip()
        self.q.put((sym, float_shares, cb))

    def _estimate(self, sym: str, float_shares: float | None) -> dict:
        if float_shares is None or float_shares <= 0:
            return {"status": STATUS_NA, "label": LABEL_MAP[STATUS_NA], "source": "na"}
        # Typical broker short locate boundaries for US momentum stocks:
        if float_shares < 15_000_000:
            # Low float: shares are heavily constrained / threshold security
            return {"status": STATUS_NONE, "label": LABEL_MAP[STATUS_NONE], "source": "heuristic"}
        if float_shares <= 50_000_000:
            # Mid float: locate required / Hard to borrow
            return {"status": STATUS_HARD, "label": LABEL_MAP[STATUS_HARD], "source": "heuristic"}
        # High float (>50M): ample institutional inventory
        return {"status": STATUS_EASY, "label": LABEL_MAP[STATUS_EASY], "source": "heuristic"}

    def _query_alpaca(self, sym: str) -> dict | None:
        if not (self.key_id and self.secret_key):
            return None
        url = f"https://paper-api.alpaca.markets/v2/assets/{sym}"
        headers = {
            "APCA-API-KEY-ID": self.key_id,
            "APCA-API-SECRET-KEY": self.secret_key,
        }
        try:
            r = requests.get(url, headers=headers, timeout=5)
            if r.status_code == 200:
                d = r.json()
                shortable = d.get("shortable", False)
                etb = d.get("easy_to_borrow", False)
                if etb:
                    st = STATUS_EASY
                elif shortable:
                    st = STATUS_HARD
                else:
                    st = STATUS_NONE
                res = {"status": st, "label": LABEL_MAP[st], "source": "alpaca"}
                with self._lock:
                    self._details[sym] = {
                        "exchange": d.get("exchange", ""),
                        "marginable": d.get("marginable", False),
                        "fractionable": d.get("fractionable", False),
                        "etb": etb,
                        "shortable": shortable,
                    }
                return res
            elif r.status_code == 404:
                return {"status": STATUS_NONE, "label": LABEL_MAP[STATUS_NONE], "source": "alpaca"}
        except Exception as e:
            log.warning("alpaca borrow query for %s failed: %s", sym, e)
        return None

    def _worker(self) -> None:
        while True:
            sym, float_shares, cb = self.q.get()
            try:
                result = None
                if self.key_id and self.secret_key and self.mode in ("auto", "alpaca"):
                    result = self._query_alpaca(sym)
                if not result:
                    result = self._estimate(sym, float_shares)

                with self._lock:
                    self._cache[sym] = result

                if cb:
                    cb(sym, result)
            except Exception:
                log.exception("borrow worker error on %s", sym)
            time.sleep(0.15)
