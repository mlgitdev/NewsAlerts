import collections
import json
import logging
import threading
import webbrowser

from . import sessions as S
from .news import NewsService
from .sounds import list_sounds

log = logging.getLogger(__name__)


class Bus:
    """Thread-safe event journal for reliable UI streaming without COM thread deadlocks."""

    def __init__(self, maxlen: int = 1000) -> None:
        self._lock = threading.Lock()
        self._seq = 0
        self._events: collections.deque = collections.deque(maxlen=maxlen)

    def add(self, w) -> None:
        pass

    def remove(self, w) -> None:
        pass

    def emit(self, event: str, payload) -> None:
        with self._lock:
            self._seq += 1
            self._events.append({
                "id": self._seq,
                "event": event,
                "payload": payload,
            })

    def latest_id(self) -> int:
        with self._lock:
            return self._seq

    def poll(self, after_id: int = 0) -> list[dict]:
        with self._lock:
            if not self._events:
                return []
            if after_id <= 0:
                return list(self._events)
            return [e for e in self._events if e["id"] > after_id]


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
            "last_event_id": a.bus.latest_id(),
        }

    def poll_events(self, after_id: int = 0):
        return self._app.bus.poll(int(after_id))

    def save_config(self, cfg: dict):
        a = self._app
        a.cfg.update(cfg)
        c = a.cfg.get()
        a.client.set_cookies(c["tv"]["sessionid"], c["tv"]["sessionid_sign"])
        bc = c.get("borrow", {})
        a.borrow.update_credentials(bc.get("alpaca_key_id", ""), bc.get("alpaca_secret_key", ""), bc.get("mode", "auto"))
        a.telegram.update(enabled=bool(c["alerts"].get("telegram_enabled", True)))
        a.sounds.muted = bool(c["alerts"]["mute"])
        a.screener.poke()
        a.bus.emit("config", c)
        return True

    def send_telegram_test(self):
        ok, msg = self._app.telegram.send_test_message()
        return {"ok": ok, "message": msg}

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
