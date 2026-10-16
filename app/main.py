"""Entry point: python -m app.main"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import webview

from .api import Api, Bus
from .borrow import BorrowService
from .config import APP_DIR, Config
from .news import NewsService, TradingViewNews
from .screener import ScreenerWorker
from .sounds import SoundPlayer
from .tape import TapeWorker
from .telegram import TelegramService
from .tv_client import TVClient

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"


class App:
    def __init__(self) -> None:
        self.cfg = Config()
        c = self.cfg.get()
        self.bus = Bus()
        self.client = TVClient(c["tv"]["sessionid"], c["tv"]["sessionid_sign"])
        self.news = NewsService(TradingViewNews(self.client))
        bc = c.get("borrow", {})
        self.borrow = BorrowService(bc.get("alpaca_key_id", ""), bc.get("alpaca_secret_key", ""), bc.get("mode", "auto"))
        self.telegram = TelegramService(enabled=bool(c["alerts"].get("telegram_enabled", True)))
        self.sounds = SoundPlayer()
        self.sounds.muted = bool(c["alerts"]["mute"])
        self.screener = ScreenerWorker(self.cfg, self.client, self.news, self.sounds, self.bus.emit, self.borrow, self.telegram)
        self.tape = TapeWorker(self.cfg, self.client, self.sounds, self.bus.emit, self.borrow)
        self.api = Api(self)
        self.main_window = None
        self.tape_window = None

    def open_tape_window(self) -> None:
        if self.tape_window is not None:
            return
        w = webview.create_window("Tape — Small Cap High of Day Momentum",
                                  str(WEB / "tape.html"), js_api=self.api,
                                  width=1100, height=700, background_color="#0b0e14")
        self.tape_window = w

        def on_closed():
            self.bus.remove(w)
            self.tape_window = None
            self.bus.emit("tape_popped", False)

        w.events.loaded += lambda: self.bus.add(w)
        w.events.closed += on_closed
        self.bus.emit("tape_popped", True)

    def run(self) -> None:
        c = self.cfg.get()
        self.main_window = webview.create_window(
            "NewsAlerts — Momentum Screener", str(WEB / "index.html"), js_api=self.api,
            width=1600, height=950, min_size=(1000, 600), background_color="#0b0e14",
            on_top=bool(c["ui"]["always_on_top"]))
        self.main_window.events.loaded += lambda: self.bus.add(self.main_window)

        def start_workers():
            self.screener.start()
            self.tape.start()

        webview.start(start_workers, debug="--debug" in sys.argv, private_mode=False,
                      storage_path=str(APP_DIR / "webview"))


def main() -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.FileHandler(APP_DIR / "app.log", encoding="utf-8"),
                  logging.StreamHandler()] if sys.stdout else
                 [logging.FileHandler(APP_DIR / "app.log", encoding="utf-8")])
    App().run()


if __name__ == "__main__":
    main()
