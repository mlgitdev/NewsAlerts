"""HTTP client for the TradingView scanner and news endpoints."""
from __future__ import annotations

import logging
import threading
import time

import requests

from .sessions import COLUMNS

log = logging.getLogger(__name__)

SCAN_URL = "https://scanner.tradingview.com/america/scan"
HEADLINES_URL = "https://news-headlines.tradingview.com/v2/headlines"
STORY_URL = "https://news-headlines.tradingview.com/v2/story"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0 Safari/537.36")

BASE_FILTERS = [
    {"left": "country", "operation": "equal", "right": "United States"},
    {"left": "type", "operation": "equal", "right": "stock"},
    {"left": "exchange", "operation": "in_range", "right": ["AMEX", "NASDAQ", "NYSE"]},
    {"left": "is_primary", "operation": "equal", "right": True},
]


class TVError(Exception):
    pass


class TVClient:
    def __init__(self, sessionid: str = "", sessionid_sign: str = "") -> None:
        self._lock = threading.Lock()
        self._s = requests.Session()
        self._s.headers.update({
            "User-Agent": UA,
            "Origin": "https://www.tradingview.com",
            "Referer": "https://www.tradingview.com/",
            "Accept": "application/json",
        })
        self._backoff_until = 0.0
        self.set_cookies(sessionid, sessionid_sign)

    def set_cookies(self, sessionid: str, sessionid_sign: str = "") -> None:
        with self._lock:
            self._s.cookies.clear()
            if sessionid:
                self._s.cookies.set("sessionid", sessionid.strip(), domain=".tradingview.com")
            if sessionid_sign:
                self._s.cookies.set("sessionid_sign", sessionid_sign.strip(), domain=".tradingview.com")

    # ---------------------------------------------------------------- scanner
    def scan(self, filters: list, sort_by: str, sort_desc: bool = True, limit: int = 150,
             columns: list | None = None) -> list[dict]:
        if time.time() < self._backoff_until:
            raise TVError("backing off after rate limit")
        cols = columns or COLUMNS
        body = {
            "markets": ["america"],
            "symbols": {"query": {"types": []}, "tickers": []},
            "options": {"lang": "en"},
            "columns": cols,
            "filter": BASE_FILTERS + filters,
            "sort": {"sortBy": sort_by, "sortOrder": "desc" if sort_desc else "asc",
                     "nullsFirst": False},
            "range": [0, limit],
        }
        try:
            r = self._s.post(SCAN_URL, json=body, timeout=10)
        except requests.RequestException as e:
            raise TVError(f"network: {e}") from e
        if r.status_code == 429 or r.status_code >= 500:
            self._backoff_until = time.time() + 15
            raise TVError(f"HTTP {r.status_code}")
        if r.status_code != 200:
            raise TVError(f"HTTP {r.status_code}: {r.text[:200]}")
        out = []
        for item in r.json().get("data", []):
            row = dict(zip(cols, item["d"]))
            row["ticker"] = item["s"]
            out.append(row)
        return out

    # ------------------------------------------------------------------- news
    def headlines(self, ticker: str) -> list[dict]:
        params = {"client": "web", "lang": "en", "streaming": "false", "symbol": ticker}
        try:
            r = self._s.get(HEADLINES_URL, params=params, timeout=10)
            r.raise_for_status()
            return r.json().get("items", [])
        except Exception as e:
            log.warning("headlines %s failed: %s", ticker, e)
            return []

    def story(self, story_id: str) -> dict:
        try:
            r = self._s.get(STORY_URL, params={"id": story_id, "lang": "en"}, timeout=10)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            log.warning("story %s failed: %s", story_id, e)
            return {}
