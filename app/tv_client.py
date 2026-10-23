"""HTTP client for the TradingView scanner and news endpoints."""
from __future__ import annotations

import logging
import re
import threading
import time

from typing import Callable

import requests

from .sessions import COLUMNS

log = logging.getLogger(__name__)

SCAN_URL = "https://scanner.tradingview.com/america/scan"
HEADLINES_URL = "https://news-headlines.tradingview.com/v2/headlines"
STORY_URL = "https://news-headlines.tradingview.com/v2/story"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0 Safari/537.36")

BASE_FILTERS = [
    {"left": "type", "operation": "equal", "right": "stock"},
    {"left": "exchange", "operation": "in_range", "right": ["AMEX", "NASDAQ", "NYSE"]},
    {"left": "is_primary", "operation": "equal", "right": True},
]


class TVError(Exception):
    pass


class TVClient:
    def __init__(self, sessionid: str = "", sessionid_sign: str = "",
                 on_auth_change: Callable[[dict], None] | None = None) -> None:
        self._lock = threading.Lock()
        self.on_auth_change = on_auth_change
        self._s = requests.Session()
        self._s.headers.update({
            "User-Agent": UA,
            "Origin": "https://www.tradingview.com",
            "Referer": "https://www.tradingview.com/",
            "Accept": "application/json",
        })
        self._backoff_until = 0.0
        self.sessionid = ""
        self.sessionid_sign = ""
        self.auth_info = {
            "connected": False,
            "authenticated": False,
            "username": "",
            "pro_plan": "",
            "error": "",
        }
        self.set_cookies(sessionid, sessionid_sign)

    def set_cookies(self, sessionid: str, sessionid_sign: str = "") -> None:
        s_id = (sessionid or "").strip()
        s_sign = (sessionid_sign or "").strip()
        with self._lock:
            if s_id == self.sessionid and s_sign == self.sessionid_sign and self.auth_info.get("connected"):
                return
            self.sessionid = s_id
            self.sessionid_sign = s_sign
            self._s.cookies.clear()
            if self.sessionid:
                self._s.cookies.set("sessionid", self.sessionid, domain=".tradingview.com")
            if self.sessionid_sign:
                self._s.cookies.set("sessionid_sign", self.sessionid_sign, domain=".tradingview.com")
        threading.Thread(target=self.check_auth, daemon=True, name="tv-auth-check").start()

    def _set_auth_info(self, info: dict) -> dict:
        with self._lock:
            self.auth_info = info
        if self.on_auth_change:
            try:
                self.on_auth_change(info)
            except Exception:
                pass
        return info

    def check_auth(self) -> dict:
        """Validates sessionid and sessionid_sign cookies against TradingView."""
        with self._lock:
            has_cookies = bool(self.sessionid)
        if not has_cookies:
            return self._set_auth_info({
                "connected": False,
                "authenticated": False,
                "username": "",
                "pro_plan": "",
                "error": "No cookies configured",
            })
        try:
            r = self._s.get("https://www.tradingview.com/", timeout=6)
            if r.status_code == 200:
                auth = "is-authenticated" in r.text
                username = ""
                pro_plan = ""
                m_u = re.search(r'"username"\s*:\s*"([^"]+)"', r.text)
                if m_u:
                    username = m_u.group(1)
                m_p = re.search(r'"pro_plan"\s*:\s*"([^"]+)"', r.text)
                if m_p:
                    pro_plan = m_p.group(1)
                return self._set_auth_info({
                    "connected": auth,
                    "authenticated": auth,
                    "username": username,
                    "pro_plan": pro_plan,
                    "error": "" if auth else "Session expired or invalid",
                })
        except Exception as e:
            log.warning("TradingView auth check error: %s", e)
            return self._set_auth_info({
                "connected": False,
                "authenticated": False,
                "username": "",
                "pro_plan": "",
                "error": str(e),
            })
        return self._set_auth_info({
            "connected": False,
            "authenticated": False,
            "username": "",
            "pro_plan": "",
            "error": "Verification failed",
        })

    def get_auth_status(self) -> dict:
        with self._lock:
            return dict(self.auth_info)

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

    # ------------------------------------------------------------- watchlists
    def get_watchlists(self) -> dict:
        """Fetch user custom watchlists from TradingView using session cookies."""
        with self._lock:
            sessionid = self.sessionid
        if not sessionid:
            return {"ok": False, "authenticated": False, "message": "TradingView sessionid not configured", "watchlists": []}
        try:
            r = self._s.get("https://www.tradingview.com/api/v1/symbols_list/custom/", timeout=8)
            if r.status_code == 200:
                data = r.json()
                lists = data if isinstance(data, list) else data.get("data", [])
                watchlists = []
                for item in lists:
                    if isinstance(item, dict) and "id" in item:
                        watchlists.append({
                            "id": str(item["id"]),
                            "title": str(item.get("title") or item.get("name") or f"Watchlist {item['id']}"),
                            "symbols": list(item.get("symbols") or []),
                            "count": len(item.get("symbols") or []),
                        })
                return {"ok": True, "authenticated": True, "watchlists": watchlists}
            if r.status_code in (401, 403):
                return {"ok": False, "authenticated": False, "message": "TradingView session expired or unauthorized", "watchlists": []}
            return {"ok": False, "authenticated": False, "message": f"TradingView returned status {r.status_code}", "watchlists": []}
        except Exception as e:
            log.warning("get_watchlists error: %s", e)
            return {"ok": False, "authenticated": False, "message": str(e), "watchlists": []}

    def add_to_watchlist(self, list_id: str, symbol: str) -> dict:
        """Add a ticker symbol to a TradingView custom watchlist."""
        with self._lock:
            sessionid = self.sessionid
        if not sessionid:
            return {"ok": False, "message": "TradingView sessionid not configured. Enter it in Settings."}
        list_id = str(list_id or "").strip()
        sym = str(symbol or "").strip().upper()
        if not list_id or not sym:
            return {"ok": False, "message": "Watchlist ID and symbol are required."}

        try:
            # 1. Check if symbol already exists in watchlist
            get_url = f"https://www.tradingview.com/api/v1/symbols_list/custom/{list_id}/"
            gr = self._s.get(get_url, timeout=8)
            if gr.status_code == 200:
                ldata = gr.json()
                cur_syms = list(ldata.get("symbols") or []) if isinstance(ldata, dict) else []
                bare_sym = sym.split(":")[-1]
                if any(s == sym or s.split(":")[-1] == bare_sym for s in cur_syms):
                    return {"ok": True, "already_exists": True, "message": f"{sym} already in watchlist", "symbol": sym, "list_id": list_id}

            # 2. Append endpoint expects a JSON list of symbol strings: ["EXCHANGE:TICKER"]
            append_url = f"https://www.tradingview.com/api/v1/symbols_list/custom/{list_id}/append/"
            r = self._s.post(append_url, json=[sym], timeout=8)
            if r.status_code in (200, 201, 204):
                return {"ok": True, "message": f"Added {sym} to TradingView watchlist", "symbol": sym, "list_id": list_id}
            if r.status_code == 400 and ("already" in r.text.lower() or "exist" in r.text.lower()):
                return {"ok": True, "already_exists": True, "message": f"{sym} already in watchlist", "symbol": sym, "list_id": list_id}

            return {"ok": False, "message": f"TradingView error (HTTP {r.status_code}): {r.text[:120]}"}
        except Exception as e:
            log.warning("add_to_watchlist error for %s in %s: %s", sym, list_id, e)
            return {"ok": False, "message": str(e)}
