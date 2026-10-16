"""Telegram Bot Alert Service.

Sends push notifications when a new symbol pops up on the screener table.
Reads bot_token and admin_chat_id from secrets/keys.toml (or app config).
Runs asynchronously in a background queue.
"""
from __future__ import annotations

import html
import logging
from pathlib import Path
import queue
import threading
import time

import requests

try:
    import tomllib
except ImportError:  # pragma: no cover
    import tomli as tomllib  # type: ignore

log = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent
SECRETS_PATH = ROOT_DIR / "secrets" / "keys.toml"

BORROW_EMOJI = {
    "easy": "🔴 ETB (Easy to borrow)",
    "hard": "🟡 HTB (Hard to borrow)",
    "none": "🟢 NO BORROW",
    "na": "🟠 N/A",
}


def load_secrets() -> dict:
    if SECRETS_PATH.exists():
        try:
            with open(SECRETS_PATH, "rb") as f:
                data = tomllib.load(f)
                return data.get("telegram", {})
        except Exception as e:
            log.warning("Failed to parse %s: %s", SECRETS_PATH, e)
    return {}


class TelegramService:
    def __init__(self, bot_token: str = "", chat_id: str = "", enabled: bool = True) -> None:
        self._lock = threading.Lock()
        secrets = load_secrets()
        self.bot_token = (bot_token or secrets.get("bot_token") or "").strip()
        self.chat_id = str(chat_id or secrets.get("admin_chat_id") or "").strip()
        self.enabled = enabled and bool(self.bot_token and self.chat_id)
        self._queue: "queue.Queue[str]" = queue.Queue()
        self._thread = threading.Thread(target=self._worker, daemon=True, name="tg-alerts")
        self._thread.start()

    def update(self, bot_token: str = "", chat_id: str = "", enabled: bool = True) -> None:
        with self._lock:
            secrets = load_secrets()
            self.bot_token = (bot_token or secrets.get("bot_token") or "").strip()
            self.chat_id = str(chat_id or secrets.get("admin_chat_id") or "").strip()
            self.enabled = enabled and bool(self.bot_token and self.chat_id)

    def is_configured(self) -> bool:
        with self._lock:
            return bool(self.bot_token and self.chat_id)

    def send_raw(self, text: str) -> None:
        if not self.enabled:
            return
        self._queue.put(text)

    def send_test_message(self) -> tuple[bool, str]:
        with self._lock:
            token = self.bot_token
            cid = self.chat_id
        if not (token and cid):
            return False, "Telegram bot_token or admin_chat_id not found in secrets/keys.toml"
        msg = (
            "🔔 <b>NewsAlerts Test Notification</b>\n\n"
            "Your Telegram alert bot is configured and connected successfully!\n"
            "You will receive push notifications here whenever a new momentum symbol pops up."
        )
        try:
            r = requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": cid, "text": msg, "parse_mode": "HTML", "disable_web_page_preview": True},
                timeout=8,
            )
            d = r.json()
            if d.get("ok"):
                return True, "Test alert sent to Telegram successfully!"
            return False, f"Telegram error: {d.get('description', r.text)}"
        except Exception as e:
            return False, f"Request failed: {e}"

    def send_new_symbol_alert(self, screen_name: str, session: str, row: dict, latest_news: str = "") -> None:
        if not self.enabled:
            return

        sym = html.escape(str(row.get("symbol") or row.get("ticker", "")))
        desc = html.escape(str(row.get("desc") or ""))
        sp = row.get("sp")
        sc = row.get("sc")
        vol = row.get("sv") or row.get("volume")
        flt = row.get("float")
        relvol = row.get("relvol")
        sector = html.escape(str(row.get("sector") or "—"))

        # Format helpers
        price_str = f"${sp:.2f}" if sp is not None else "—"
        chg_sign = "+" if (sc or 0) > 0 else ""
        chg_str = f"{chg_sign}{sc:.2f}%" if sc is not None else "—"

        def fmt_big(v):
            if not v:
                return "—"
            if v >= 1e9:
                return f"{v / 1e9:.2f}B"
            if v >= 1e6:
                return f"{v / 1e6:.2f}M"
            if v >= 1e3:
                return f"{v / 1e3:.2f}K"
            return str(v)

        borrow = row.get("borrow") or {}
        bst = borrow.get("status", "na")
        borrow_str = BORROW_EMOJI.get(bst, f"🟠 {borrow.get('label', 'N/A')}")

        sess_label = {"pre": "Pre-Market", "regular": "Regular Hours", "post": "Post-Market"}.get(session, session.upper())
        ticker = row.get("ticker", sym)

        lines = [
            f"🚨 <b>New Symbol Alert: {sym}</b> ({sess_label})",
            f"Screen: <i>{html.escape(screen_name)}</i>",
            f"Company: <b>{desc}</b>",
            "",
            f"💵 <b>Price:</b> {price_str} ({chg_str})",
            f"📊 <b>Volume:</b> {fmt_big(vol)}",
            f"🌊 <b>Float:</b> {fmt_big(flt)}",
            f"⚡ <b>Rel Vol:</b> {f'{relvol:.2f}' if relvol else '—'}",
            f"🩳 <b>Borrow:</b> {borrow_str}",
            f"🏢 <b>Sector:</b> {sector}",
        ]

        if latest_news:
            lines.append(f"\n📰 <b>News:</b> {html.escape(latest_news)}")

        chart_url = f"https://www.tradingview.com/chart/?symbol={ticker}"
        lines.append(f"\n🔗 <a href=\"{chart_url}\">Open TradingView Chart</a>")

        self.send_raw("\n".join(lines))

    def _worker(self) -> None:
        while True:
            text = self._queue.get()
            with self._lock:
                token = self.bot_token
                cid = self.chat_id
            if token and cid:
                try:
                    requests.post(
                        f"https://api.telegram.org/bot{token}/sendMessage",
                        json={"chat_id": cid, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True},
                        timeout=8,
                    )
                except Exception as e:
                    log.warning("Telegram send failed: %s", e)
            time.sleep(0.3)
