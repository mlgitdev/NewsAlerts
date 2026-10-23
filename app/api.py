import collections
import json
import logging
import threading
import webbrowser

from . import sessions as S
from .news import NewsService
from .sounds import list_sounds
from .version import get_version, get_version_info

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
        kid = a.borrow.key_id
        tv_auth = a.client.get_auth_status() if hasattr(a.client, "get_auth_status") else {}
        from .config import APP_DIR, find_secrets_file
        sec_file = find_secrets_file()
        return {
            "version": get_version(),
            "semver": get_version_info(),
            "config": a.cfg.get(),
            "sounds": list_sounds(),
            "status": a.screener.status_payload(),
            "screener": a.screener.last_rows,
            "tape": a.tape.snapshot(),
            "tape_popped": a.tape_window is not None,
            "last_event_id": a.bus.latest_id(),
            "alpaca_active": bool(kid and a.borrow.secret_key),
            "alpaca_key_masked": (kid[:6] + "..." + kid[-4:]) if kid else "",
            "tv_connected": tv_auth.get("connected", False),
            "tv_username": tv_auth.get("username", ""),
            "tv_pro_plan": tv_auth.get("pro_plan", ""),
            "tv_error": tv_auth.get("error", ""),
            "app_dir": str(APP_DIR),
            "secrets_file": str(sec_file) if sec_file else "",
            "has_keys_toml": bool(sec_file and sec_file.is_file()),
        }

    def get_version(self) -> dict:
        """Return Semantic Version metadata to frontend callers."""
        return get_version_info()

    def poll_events(self, after_id: int = 0):
        return self._app.bus.poll(int(after_id))

    def save_config(self, cfg: dict):
        a = self._app
        a.cfg.update(cfg)
        c = a.cfg.get()
        tv = c.get("tv", {})
        a.client.set_cookies(tv.get("sessionid", ""), tv.get("sessionid_sign", ""))
        bc = c.get("borrow", {})
        a.borrow.update_credentials(bc.get("alpaca_key_id", ""), bc.get("alpaca_secret_key", ""), bc.get("mode", "auto"))
        if hasattr(a, "alp_news"):
            a.alp_news.update_credentials(a.borrow.key_id, a.borrow.secret_key)
        ac = c.get("alerts", {})
        is_paused = bool(ac.get("mute", False))
        a.telegram.update(
            bot_token=ac.get("telegram_bot_token", ""),
            chat_id=ac.get("telegram_chat_id", ""),
            enabled=bool(ac.get("telegram_enabled", True)),
            paused=is_paused
        )
        a.sounds.muted = is_paused
        if "volume" in ac:
            a.sounds.set_volume(int(ac["volume"]))
        a.screener.poke()
        a.bus.emit("config", c)
        return True

    def set_volume(self, volume: int):
        a = self._app
        vol = max(0, min(100, int(volume)))
        a.sounds.set_volume(vol)
        cfg = a.cfg.get()
        cfg.setdefault("alerts", {})["volume"] = vol
        a.cfg.update(cfg)
        a.bus.emit("config", cfg)
        return {"ok": True, "volume": vol}

    def send_telegram_test(self, bot_token: str = "", chat_id: str = ""):
        ok, msg = self._app.telegram.send_test_message(bot_token=bot_token, chat_id=chat_id)
        return {"ok": ok, "message": msg}

    def test_alpaca(self, key_id: str = "", secret_key: str = ""):
        a = self._app
        kid = (key_id or "").strip() or a.borrow.key_id
        sec = (secret_key or "").strip() or a.borrow.secret_key
        if not (kid and sec):
            return {"ok": False, "message": "No Alpaca keys found in secrets/keys.toml or settings."}
        try:
            import requests
            headers = {"APCA-API-KEY-ID": kid, "APCA-API-SECRET-KEY": sec}
            r = requests.get("https://paper-api.alpaca.markets/v2/account", headers=headers, timeout=6)
            if r.status_code == 200:
                acc = r.json()
                bp = acc.get("buying_power", "0")
                status = acc.get("status", "ACTIVE")
                return {
                    "ok": True,
                    "message": f"Connected! Account {status} · Buying Power: ${float(bp):,.2f}",
                    "account_id": acc.get("id"),
                }
            return {"ok": False, "message": f"Alpaca error {r.status_code}: {r.text}"}
        except Exception as e:
            return {"ok": False, "message": str(e)}

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

    def reset_config(self):
        """Restore all application configurations back to factory defaults."""
        c = self._app.cfg.reset()
        self.save_config(c)
        return c

    def get_default_config(self):
        """Return fresh copy of DEFAULT_CONFIG for inspection or schema reference."""
        from .config import get_default_config
        return get_default_config()

    def get_quote(self, ticker: str):
        """Snapshot for the news header when a tape symbol is clicked or custom symbol entered."""
        try:
            sym = str(ticker).split(":")[-1].strip().upper()
            if not sym:
                return None
            rows = self._app.client.scan([{"left": "name", "operation": "equal",
                                           "right": sym}], "volume", True, 5)
            # Find exact match by name or ticker
            row = next((r for r in rows if r["name"].upper() == sym or r["ticker"].upper() == ticker.upper()), rows[0] if rows else None)
            if not row:
                return None
            lg = S.logical_row(row, S.current_session())
            borrow_info = self._app.borrow.get_status(row["ticker"], lg["float"])
            details = self._app.borrow.get_details(row["ticker"])
            snapshot = self._app.borrow.get_snapshot(row["ticker"])
            return {"ticker": row["ticker"], "symbol": row["name"], "desc": row["description"],
                    "logoid": row.get("logoid"), "sp": lg["price"], "sc": lg["chg"],
                    "float": lg["float"], "sector": lg["sector"], "borrow": borrow_info,
                    "details": details, "snapshot": snapshot}
        except Exception as e:
            log.warning("get_quote %s failed: %s", ticker, e)
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

    def open_app_dir(self):
        """Open the central application directory in the native OS file explorer."""
        from .config import APP_DIR
        import os
        import sys
        import subprocess
        try:
            APP_DIR.mkdir(parents=True, exist_ok=True)
            if sys.platform == "win32":
                os.startfile(str(APP_DIR))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(APP_DIR)])
            else:
                subprocess.Popen(["xdg-open", str(APP_DIR)])
            return {"ok": True, "path": str(APP_DIR)}
        except Exception as e:
            log.warning("open_app_dir failed: %s", e)
            return {"ok": False, "error": str(e)}

    def pop_tape(self):
        self._app.open_tape_window()
        return True

    def refresh(self):
        """Trigger an immediate screener re-scan."""
        self._app.screener.poke()
        return True

    def select_symbol(self, ticker: str):
        self._app.bus.emit("select", ticker)
        return True

    def set_on_top(self, on: bool):
        try:
            w = self._app.main_window
            if w is None:
                return True
            target = bool(on)
            if getattr(w, "_on_top_state", None) == target:
                return True
            w._on_top_state = target

            import sys
            if sys.platform == "win32":
                import ctypes
                hwnd = None
                try:
                    from webview.platforms import winforms
                    form = winforms.BrowserView.instances.get(w.uid)
                    if form is not None and hasattr(form, "Handle"):
                        hwnd = form.Handle.ToInt64()
                except Exception:
                    pass
                if hwnd:
                    HWND_TOPMOST = -1 if target else -2
                    SWP_FLAGS = 0x0002 | 0x0001 | 0x0010  # SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE
                    ctypes.windll.user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_FLAGS)
                    return True

            w.on_top = target
        except Exception:
            pass
        return True

    def clear_tape(self):
        self._app.tape.clear()
        self._app.bus.emit("tape_cleared", {})
        return True

    # ------------------------------------------------------------- watchlists
    def get_watchlists(self) -> dict:
        a = self._app
        cfg = a.cfg.get()
        wl_cfg = cfg.setdefault("watchlist", {
            "active_id": "",
            "active_title": "Default",
            "custom_lists": [{"id": "local_default", "title": "Momentum Watchlist", "symbols": []}],
        })

        # Query TradingView if session is available
        res = a.client.get_watchlists()
        if res.get("ok") and res.get("watchlists"):
            tv_lists = res["watchlists"]
            # Ensure an active_id is set
            active_id = wl_cfg.get("active_id")
            if not active_id or not any(x["id"] == active_id for x in tv_lists):
                wl_cfg["active_id"] = tv_lists[0]["id"]
                wl_cfg["active_title"] = tv_lists[0]["title"]
                a.cfg.update(cfg)
            return {
                "ok": True,
                "source": "tradingview",
                "connected": True,
                "authenticated": True,
                "active_id": wl_cfg.get("active_id", ""),
                "active_title": wl_cfg.get("active_title", ""),
                "watchlists": tv_lists,
            }

        # Fallback to local watchlists
        local_lists = wl_cfg.get("custom_lists", [{"id": "local_default", "title": "Momentum Watchlist", "symbols": []}])
        active_id = wl_cfg.get("active_id")
        if not active_id or not any(x["id"] == active_id for x in local_lists):
            wl_cfg["active_id"] = local_lists[0]["id"]
            wl_cfg["active_title"] = local_lists[0]["title"]
            a.cfg.update(cfg)
        return {
            "ok": True,
            "source": "local",
            "connected": False,
            "authenticated": False,
            "message": res.get("message") or "TradingView session not connected. Using local watchlists.",
            "active_id": wl_cfg.get("active_id", ""),
            "active_title": wl_cfg.get("active_title", ""),
            "watchlists": local_lists,
        }

    def select_watchlist(self, list_id: str, title: str = "") -> dict:
        a = self._app
        cfg = a.cfg.get()
        wl_cfg = cfg.setdefault("watchlist", {})
        wl_cfg["active_id"] = str(list_id or "").strip()
        if title:
            wl_cfg["active_title"] = str(title).strip()
        a.cfg.update(cfg)
        return {"ok": True, "active_id": wl_cfg["active_id"], "active_title": wl_cfg.get("active_title", "")}

    def add_to_watchlist(self, list_id: str, symbol: str) -> dict:
        a = self._app
        sym = str(symbol or "").strip().upper()
        if not sym:
            return {"ok": False, "message": "Symbol is required."}

        # Resolve full exchange prefix if missing (e.g. SMCI -> NASDAQ:SMCI)
        full_ticker = sym
        if ":" not in full_ticker:
            q = self.get_quote(sym)
            if q and q.get("ticker"):
                full_ticker = q["ticker"]
            else:
                full_ticker = f"NASDAQ:{sym}"

        # If list_id starts with local_ or no list_id provided, store locally
        cfg = a.cfg.get()
        wl_cfg = cfg.setdefault("watchlist", {})
        target_id = str(list_id or wl_cfg.get("active_id") or "local_default").strip()

        if target_id.startswith("local_") or not a.client.sessionid:
            lists = wl_cfg.setdefault("custom_lists", [{"id": "local_default", "title": "Momentum Watchlist", "symbols": []}])
            target = next((x for x in lists if x["id"] == target_id), None)
            if not target:
                target = {"id": target_id, "title": "Momentum Watchlist", "symbols": []}
                lists.append(target)
            if full_ticker not in target["symbols"] and sym not in target["symbols"]:
                target["symbols"].append(full_ticker)
                a.cfg.update(cfg)
                return {"ok": True, "source": "local", "message": f"Added {full_ticker} to local watchlist", "symbol": full_ticker, "list_id": target_id}
            return {"ok": True, "already_exists": True, "source": "local", "message": f"{full_ticker} already in watchlist", "symbol": full_ticker, "list_id": target_id}

        # Target is a TradingView list
        res = a.client.add_to_watchlist(target_id, full_ticker)
        if res.get("ok"):
            # Mirror in local custom_lists
            lists = wl_cfg.setdefault("custom_lists", [])
            target = next((x for x in lists if x["id"] == target_id), None)
            if not target:
                target = {"id": target_id, "title": wl_cfg.get("active_title", "TradingView Watchlist"), "symbols": []}
                lists.append(target)
            if full_ticker not in target["symbols"]:
                target["symbols"].append(full_ticker)
                a.cfg.update(cfg)
        return res
