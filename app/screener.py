"""Screener poller: builds TradingView queries from screens, diffs results, raises new-symbol alerts."""
from __future__ import annotations

import json
import logging
import queue
import threading
import time
from typing import Callable

from . import sessions as S
from .borrow import BorrowService
from .config import Config
from .news import NewsService
from .sounds import SoundPlayer
from .telegram import TelegramService
from .tv_client import TVClient, TVError

log = logging.getLogger(__name__)

NEW_BADGE_SEC = 60

# UI row key -> logical field (for sorting on the server side)
SORT_KEYS = {"close": "close", "change": "change", "volume": "volume",
             "sp": "price", "sc": "chg", "sv": "vol",
             "float": "float", "relvol": "relvol", "relvol_t": "relvol_t", "mcap": "mcap"}


def build_filters(screen: dict, session: str) -> list:
    out = []
    for f in screen.get("filters", []):
        field = f.get("field")
        if field in ("sector", "exchange"):
            vals = f.get("values") or []
            if vals:
                out.append({"left": S.tv_field(field, session), "operation": "in_range", "right": vals})
            continue
        col = S.tv_field(field, session)
        if not col:
            continue
        lo, hi = f.get("min"), f.get("max")
        if lo is not None and hi is not None:
            out.append({"left": col, "operation": "in_range", "right": [lo, hi]})
        elif lo is not None:
            out.append({"left": col, "operation": "egreater", "right": lo})
        elif hi is not None:
            out.append({"left": col, "operation": "eless", "right": hi})
    return out


def sort_column(screen: dict, session: str) -> tuple[str, bool]:
    s = screen.get("sort") or {}
    key = SORT_KEYS.get(s.get("field"), "chg")
    col = key if key in ("close", "change", "volume") else S.tv_field(key, session)
    return col or S.tv_field("chg", session), s.get("dir", "desc") == "desc"


class _ScreenState:
    def __init__(self, sig: str) -> None:
        self.sig = sig
        self.seeded = False
        self.prev: set[str] = set()
        self.last_seen: dict[str, float] = {}
        self.first_seen: dict[str, float] = {}
        self.new_at: dict[str, float] = {}


class NewsPrefetcher(threading.Thread):
    """Background fetch of headlines so rows can show a 📰 flag."""

    def __init__(self, news: NewsService, ttl: float = 120.0) -> None:
        super().__init__(daemon=True, name="news-prefetch")
        self.news = news
        self.ttl = ttl
        self.q: "queue.Queue[tuple[str, Callable | None]]" = queue.Queue()
        self._fetched: dict[str, float] = {}

    def want(self, ticker: str, cb: Callable | None = None, priority: bool = False) -> None:
        if priority or time.time() - self._fetched.get(ticker, 0) > self.ttl:
            self._fetched[ticker] = time.time()
            self.q.put((ticker, cb))

    def run(self) -> None:
        while True:
            ticker, cb = self.q.get()
            try:
                items = self.news.get(ticker, force=True)
                if cb:
                    cb(ticker, items)
            except Exception:
                log.exception("prefetch %s", ticker)
            time.sleep(0.25)


class ScreenerWorker(threading.Thread):
    def __init__(self, cfg: Config, client: TVClient, news: NewsService, sounds: SoundPlayer,
                 emit: Callable[[str, object], None], borrow: BorrowService | None = None,
                 telegram: TelegramService | None = None) -> None:
        super().__init__(daemon=True, name="screener")
        self.cfg = cfg
        self.client = client
        self.news = news
        self.sounds = sounds
        self.emit = emit
        self.borrow = borrow
        self.telegram = telegram
        self.prefetch = NewsPrefetcher(news)
        self._states: dict[str, _ScreenState] = {}
        self._wake = threading.Event()
        self.last_rows: dict = {}
        self.status = {"ok": False, "error": "", "realtime": None, "last": 0}

    def poke(self) -> None:
        self._wake.set()

    # --------------------------------------------------------------- main loop
    def run(self) -> None:
        self.prefetch.start()
        while True:
            t0 = time.time()
            try:
                self.tick()
            except Exception as e:
                log.exception("screener tick")
                self.status.update(ok=False, error=str(e))
                self.emit("status", self.status_payload())
            interval = max(1.0, float(self.cfg["poll"]["screener_sec"]))
            self._wake.wait(max(0.2, interval - (time.time() - t0)))
            self._wake.clear()

    def status_payload(self) -> dict:
        auth = self.client.get_auth_status() if hasattr(self.client, "get_auth_status") else {}
        return {
            **self.status,
            "market": S.market_state(),
            "auto_session": S.current_session(),
            "et": S.now_et().strftime("%H:%M:%S"),
            "tv_connected": auth.get("connected", False),
            "tv_username": auth.get("username", ""),
            "tv_pro_plan": auth.get("pro_plan", ""),
            "tv_error": auth.get("error", ""),
        }

    def tick(self) -> None:
        c = self.cfg.get()
        active_id = c.get("active_screen")
        screens = [s for s in c["screens"] if s.get("alert") or s["id"] == active_id]
        for screen in screens:
            self._poll_screen(screen, c, screen["id"] == active_id)
        self.emit("status", self.status_payload())

    def _poll_screen(self, screen: dict, c: dict, active: bool) -> None:
        session = S.resolve(screen.get("session", "auto"))
        filters = build_filters(screen, session)
        sig = json.dumps([session, filters], sort_keys=True)
        st = self._states.get(screen["id"])
        if st is None or st.sig != sig:
            st = self._states[screen["id"]] = _ScreenState(sig)

        col, desc = sort_column(screen, session)
        try:
            raw = self.client.scan(filters, col, desc, limit=int(screen.get("limit", 150)))
        except TVError as e:
            self.status.update(ok=False, error=str(e))
            return
        self.status.update(ok=True, error="", last=time.time())
        if raw:
            self.status["realtime"] = not str(raw[0].get("update_mode", "")).startswith("delayed")

        now = time.time()
        reentry = float(c["alerts"]["reentry_min"]) * 60
        current = {r["ticker"] for r in raw}
        new_syms = []
        for t in current:
            gone_for = now - st.last_seen.get(t, 0)
            if t not in st.prev and gone_for > reentry:
                st.first_seen[t] = now
                if st.seeded:
                    new_syms.append(t)
                    st.new_at[t] = now
            st.first_seen.setdefault(t, now)
            st.last_seen[t] = now
        st.prev = current
        was_seeded = st.seeded
        st.seeded = True

        rows = [self._row(r, session, st, c, now) for r in raw]
        for r in rows:
            self.prefetch.want(r["ticker"])

        if active:
            self.last_rows = {"screen_id": screen["id"], "session": session, "rows": rows,
                              "seeded": was_seeded}
            self.emit("screener", self.last_rows)

        if new_syms and screen.get("alert") and was_seeded:
            by_t = {r["ticker"]: r for r in rows}
            payload = {"screen_id": screen["id"], "screen_name": screen["name"], "ts": now,
                       "symbols": [by_t[t] for t in new_syms]}
            self.emit("new_symbols", payload)
            is_paused = bool(c["alerts"].get("mute", False))
            if not is_paused:
                self.sounds.play(c["alerts"]["sound_new_symbol"])
            for t in new_syms:
                row_data = by_t[t]
                if self.telegram and c["alerts"].get("telegram_enabled", True) and not is_paused:
                    cached = self.news.cached(t)
                    fresh = NewsService.recent(cached, c["news"]["recency_hours"]) if cached else []
                    latest_title = fresh[0]["title"] if fresh else ""
                    self.telegram.send_new_symbol_alert(screen["name"], session, row_data, latest_title)
                self.prefetch.want(t, self._on_new_symbol_news, priority=True)

    def _on_new_symbol_news(self, ticker: str, items: list[dict]) -> None:
        c = self.cfg.get()
        fresh = NewsService.recent(items, c["news"]["recency_hours"], c["news"]["benzinga_only"])
        if fresh:
            self.emit("symbol_news", {"ticker": ticker, "count": len(fresh),
                                      "latest": fresh[0]})
            if c["alerts"]["news_sound_enabled"] and not c["alerts"].get("mute", False):
                self.sounds.play(c["alerts"]["sound_news"])

    def _row(self, r: dict, session: str, st: _ScreenState, c: dict, now: float) -> dict:
        lg = S.logical_row(r, session)
        cached = self.news.cached(r["ticker"])
        fresh = NewsService.recent(cached, c["news"]["recency_hours"],
                                   c["news"]["benzinga_only"]) if cached else []
        fs = st.first_seen.get(r["ticker"], now)
        borrow_info = self.borrow.get_status(r["ticker"], lg["float"]) if self.borrow else {"status": "na", "label": "N/A"}
        return {
            "ticker": r["ticker"], "symbol": r.get("name"), "desc": r.get("description"),
            "logoid": r.get("logoid"),
            "close": r.get("close"), "change": r.get("change"), "volume": r.get("volume"),
            "sp": lg["price"], "sc": lg["chg"], "sv": lg["vol"], "chg_open": lg["chg_open"],
            "gap": lg["gap"],
            "float": lg["float"], "relvol": lg["relvol"], "relvol_t": lg["relvol_t"],
            "mcap": lg["mcap"], "sector": lg["sector"], "exchange": lg["exchange"],
            "borrow": borrow_info,
            "news": len(fresh), "news_ts": fresh[0]["published"] if fresh else None,
            "news_bz": any(i["provider"] == "benzinga" for i in fresh),
            "first_seen": fs, "is_new": now - st.new_at.get(r["ticker"], 0) < NEW_BADGE_SEC,
        }
