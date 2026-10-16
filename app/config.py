"""Config persistence (%APPDATA%\\NewsAlerts\\config.json) and defaults."""
from __future__ import annotations

import copy
import json
import os
import threading
from pathlib import Path

APP_DIR = Path(os.environ.get("APPDATA", Path.home())) / "NewsAlerts"
CONFIG_PATH = APP_DIR / "config.json"
MEDIA = r"C:\Windows\Media"

DEFAULT_STRATEGIES = [
    {"name": "Low Float - Former Momo Stock", "family": "low", "trigger": "hod",
     "float_max": 20e6, "relvol_min": 1.5, "hi52_ratio_min": 2.0},
    {"name": "Low Float - High Rel Vol", "family": "low", "trigger": "hod",
     "float_max": 20e6, "relvol_min": 5},
    {"name": "Low Float - High Rel Vol - Price $20+", "family": "low", "trigger": "hod",
     "float_max": 20e6, "relvol_min": 5, "price_min": 20},
    {"name": "Low Float - Med Rel Vol", "family": "low", "trigger": "hod",
     "float_max": 20e6, "relvol_min": 2, "relvol_max": 5},
    {"name": "Medium Float - High Rel Vol - Price $20+", "family": "medium", "trigger": "hod",
     "float_min": 20e6, "float_max": 100e6, "relvol_min": 5, "price_min": 20},
    {"name": "Medium Float - High Rel Vol - Price under $20", "family": "medium", "trigger": "hod",
     "float_min": 20e6, "float_max": 100e6, "relvol_min": 5, "price_max": 20},
    {"name": "Medium Float - Med Rel Vol - Price $20+", "family": "medium", "trigger": "hod",
     "float_min": 20e6, "float_max": 100e6, "relvol_min": 2, "relvol_max": 5, "price_min": 20},
    {"name": "Squeeze Alert - 52wk Breakout", "family": "squeeze", "trigger": "52w"},
    {"name": "Squeeze Alert - Up 10% in 10min", "family": "squeeze", "trigger": "squeeze",
     "up_pct": 10, "window_min": 10},
    {"name": "Squeeze Alert - Up 5% in 5min", "family": "squeeze", "trigger": "squeeze",
     "up_pct": 5, "window_min": 5},
]

DEFAULT_CONFIG = {
    "tv": {"sessionid": "", "sessionid_sign": ""},
    "borrow": {"alpaca_key_id": "", "alpaca_secret_key": "", "mode": "auto"},
    "poll": {"screener_sec": 3, "tape_sec": 2, "news_sec": 30},
    "alerts": {
        "reentry_min": 15,
        "mute": False,
        "quiet_when_focused": False,
        "sound_new_symbol": MEDIA + r"\Windows Notify System Generic.wav",
        "news_sound_enabled": True,
        "sound_news": MEDIA + r"\Windows Ding.wav",
        "tape_sound_enabled": False,
        "sound_tape": MEDIA + r"\Windows Navigation Start.wav",
    },
    "news": {"recency_hours": 12, "benzinga_only": False},
    "screens": [
        {
            "id": "s1",
            "name": "2-10 small floats",
            "session": "auto",
            "alert": True,
            "filters": [
                {"field": "float", "min": 300e3, "max": 25e6},
                {"field": "price", "min": 1, "max": 20},
                {"field": "chg", "min": 10, "max": None},
                {"field": "vol", "min": 50e3, "max": None},
                {"field": "relvol", "min": None, "max": None},
            ],
            "sort": {"field": "sc", "dir": "desc"},
        }
    ],
    "active_screen": "s1",
    "tape": {
        "universe": {"price_min": 1, "price_max": 50, "chg_min": 3, "vol_min": 20e3, "limit": 300},
        "cooldown_sec": 30,
        "max_events": 1000,
        "enabled": [s["name"] for s in DEFAULT_STRATEGIES],
        "strategies": DEFAULT_STRATEGIES,
    },
    "ui": {"always_on_top": False, "font_size": 13, "news_width": 420, "tape_height": 300},
}


def _merge(base: dict, override: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


class Config:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.data = self._load()

    def _load(self) -> dict:
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return _merge(DEFAULT_CONFIG, json.load(f))
        except FileNotFoundError:
            return copy.deepcopy(DEFAULT_CONFIG)
        except Exception:
            # Corrupt file: keep a backup, start fresh
            try:
                CONFIG_PATH.replace(CONFIG_PATH.with_suffix(".bad.json"))
            except Exception:
                pass
            return copy.deepcopy(DEFAULT_CONFIG)

    def save(self) -> None:
        with self._lock:
            APP_DIR.mkdir(parents=True, exist_ok=True)
            tmp = CONFIG_PATH.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
            tmp.replace(CONFIG_PATH)

    def get(self) -> dict:
        with self._lock:
            return copy.deepcopy(self.data)

    def update(self, new: dict) -> None:
        with self._lock:
            self.data = _merge(DEFAULT_CONFIG, new)
            self.save()

    def __getitem__(self, key):
        with self._lock:
            return self.data[key]
