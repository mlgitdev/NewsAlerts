"""JS <-> Python bridge exposed to the web UI via pywebview."""
from __future__ import annotations

import json
import logging
import threading
import webbrowser

from . import sessions as S
from .news import NewsService
from .sounds import list_sounds

log = logging.getLogger(__name__)


class Bus:
    """Pushes events to every open window: App.on(event, payload)."""

    def __init__(self) -> None:
        self._windows = []
        self._lock = threading.Lock()

    def add(self, w) -> None:
        with self._lock:
            self._windows.append(w)

    def remove(self, w) -> None:
        with self._lock:
            if w in self._windows:
                self._windows.remove(w)

    def emit(self, event: str, payload) -> None:
        js = f"window.App && App.on({json.dumps(event)}, {json.dumps(payload, default=str)})"
        with self._lock:
            wins = list(self._windows)
        for w in wins:
            try:
                (getattr(w, "run_js", None) or w.evaluate_js)(js)
            except Exception as e:
                log.debug("emit to window failed: %s", e)


class Api:
    # Attributes prefixed with "_" are not exposed to JS by pywebview.
    def __init__(self, app) -> None:
        self._app = app

    # ----------------------------------------------------------------- state
    def get_state(self):
        a = self._app
        return {
            "config": a.cfg.get(),
            "sounds": list_sounds(),
            "status": a.screener.status_payload(),
            "screener": a.screener.last_rows,
            "tape": a.tape.snapshot(),
            "tape_popped": a.tape_window is not None,
        }

    def save_config(self, cfg: dict):
        a = self._app
        a.cfg.update(cfg)
        c = a.cfg.get()
        a.client.set_cookies(c["tv"]["sessionid"], c["tv"]["sessionid_sign"])
        bc = c.get("borrow", {})
        a.borrow.update_credentials(bc.get("alpaca_key_id", ""), bc.get("alpaca_secret_key", ""), bc.get("mode", "auto"))
        a.sounds.muted = bool(c["alerts"]["mute"])
        a.screener.poke()
        a.bus.emit("config", c)
        return True

    def set_focused(self, focused: bool):
        a = self._app
        a.sounds.suppressed = bool(focused) and bool(a.cfg["alerts"]["quiet_when_focused"])
        return True

    # ------------------------------------------------------------------ news
    def get_news(self, ticker: str, force: bool = False):
        a = self._app
        c = a.cfg.get()
        items = a.news.get(ticker, force=force)
        return {
            "ticker": ticker,
            "items": NewsService.recent(items, c["news"]["recency_hours"], c["news"]["benzinga_only"]),
            "total": len(items),
        }

    def get_story(self, story_id: str):
        return self._app.news.story(story_id)

    def get_quote(self, ticker: str):
        """Snapshot for the news header when a tape symbol is clicked."""
        try:
            rows = self._app.client.scan([{"left": "name", "operation": "equal",
                                           "right": ticker.split(":")[-1]}], "volume", True, 5)
            row = next((r for r in rows if r["ticker"] == ticker), rows[0] if rows else None)
            if not row:
                return None
            lg = S.logical_row(row, S.current_session())
            borrow_info = self._app.borrow.get_status(row["ticker"], lg["float"])
            return {"ticker": row["ticker"], "symbol": row["name"], "desc": row["description"],
                    "logoid": row.get("logoid"), "sp": lg["price"], "sc": lg["chg"],
                    "float": lg["float"], "sector": lg["sector"], "borrow": borrow_info}
        except Exception:
            return None

    # ---------------------------------------------------------------- misc
    def play_sound(self, path: str):
        return self._app.sounds.play(path, force=True)

    def play_alert(self, kind: str):
        c = self._app.cfg["alerts"]
        if kind == "news" and c["news_sound_enabled"]:
            return self._app.sounds.play(c["sound_news"])
        return False

    def open_url(self, url: str):
        if url.startswith("http"):
            webbrowser.open(url)
        return True

    def open_chart(self, ticker: str):
        webbrowser.open(f"https://www.tradingview.com/chart/?symbol={ticker}")
        return True

    def pop_tape(self):
        self._app.open_tape_window()
        return True

    def select_symbol(self, ticker: str):
        self._app.bus.emit("select", ticker)
        return True

    def set_on_top(self, on: bool):
        try:
            self._app.main_window.on_top = bool(on)
        except Exception:
            pass
        return True
