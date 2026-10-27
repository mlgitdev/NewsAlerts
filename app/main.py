"""Entry point: python -m app.main"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import webview

try:
    from .api import Api, Bus
    from .bamsec import BamSECService
    from .borrow import BorrowService
    from .config import APP_DIR, Config
    from .news import AlpacaNews, CombinedNews, NewsService, TradingViewNews
    from .screener import ScreenerWorker
    from .server import start_server
    from .sounds import SoundPlayer
    from .tape import TapeWorker
    from .telegram import TelegramService
    from .tv_client import TVClient
    from .version import get_version
except ImportError:
    from app.api import Api, Bus
    from app.bamsec import BamSECService
    from app.borrow import BorrowService
    from app.config import APP_DIR, Config
    from app.news import AlpacaNews, CombinedNews, NewsService, TradingViewNews
    from app.screener import ScreenerWorker
    from app.server import start_server
    from app.sounds import SoundPlayer
    from app.tape import TapeWorker
    from app.telegram import TelegramService
    from app.tv_client import TVClient
    from app.version import get_version

if getattr(sys, "frozen", False):
    exe_dir = Path(sys.executable).resolve().parent
    meipass = getattr(sys, "_MEIPASS", None)
    candidates = []
    if meipass:
        candidates.append(Path(meipass) / "web")
        candidates.append(Path(meipass) / "_internal" / "web")
    candidates.append(exe_dir / "web")
    candidates.append(exe_dir / "_internal" / "web")
    WEB = next((p for p in candidates if p.exists()), exe_dir / "web")
    BASE_DIR = WEB.parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent
    WEB = BASE_DIR / "web"



class App:
    def __init__(self) -> None:
        self.cfg = Config()
        c = self.cfg.get()
        self.bus = Bus()
        self.client = TVClient(
            c["tv"]["sessionid"],
            c["tv"]["sessionid_sign"],
            on_auth_change=lambda info: self.bus.emit("tv_auth", info)
        )
        bc = c.get("borrow", {})
        self.borrow = BorrowService(bc.get("alpaca_key_id", ""), bc.get("alpaca_secret_key", ""), bc.get("mode", "auto"))
        tv_news = TradingViewNews(self.client)
        self.alp_news = AlpacaNews(self.borrow.key_id, self.borrow.secret_key)
        self.news = NewsService(CombinedNews([self.alp_news, tv_news]))
        self.bamsec = BamSECService()
        ac = c.get("alerts", {})
        is_paused = bool(ac.get("mute", False))
        self.telegram = TelegramService(
            bot_token=ac.get("telegram_bot_token", ""),
            chat_id=ac.get("telegram_chat_id", ""),
            enabled=bool(ac.get("telegram_enabled", True)),
            paused=is_paused
        )
        self.sounds = SoundPlayer(volume=int(ac.get("volume", 80)))
        self.sounds.muted = is_paused
        self.screener = ScreenerWorker(self.cfg, self.client, self.news, self.sounds, self.bus.emit, self.borrow, self.telegram)
        self.tape = TapeWorker(self.cfg, self.client, self.sounds, self.bus.emit, self.borrow, self.telegram)
        self.api = Api(self)
        self.server_url, self.http_server = start_server(self.api, WEB)
        self.main_window = None
        self.tape_window = None

    def open_tape_window(self) -> None:
        if self.tape_window is not None:
            return
        w = webview.create_window(
            "Tape — Small Cap High of Day Momentum",
            f"{self.server_url}/tape.html",
            width=1100, height=700, background_color="#0b0e14"
        )
        self.tape_window = w

        def on_closed():
            self.tape_window = None
            self.bus.emit("tape_popped", False)

        w.events.closed += on_closed
        self.bus.emit("tape_popped", True)

    def run(self) -> None:
        c = self.cfg.get()
        self.main_window = webview.create_window(
            f"NewsAlerts v{get_version()} — Momentum Screener",
            f"{self.server_url}/index.html",
            width=1600, height=950, min_size=(1000, 600), background_color="#0b0e14",
            on_top=bool(c["ui"]["always_on_top"])
        )

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
