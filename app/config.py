"""Config persistence (%APPDATA%\\NewsAlerts\\config.json) and defaults."""
from __future__ import annotations

import copy
import json
import os
import sys
import threading
from pathlib import Path

def get_app_dir() -> Path:
    """Resolve and ensure the application data directory exists across all operating systems.

    Resolution Priority:
    1. NEWSALERTS_DIR or NEWSALERTS_HOME environment variable (explicit override).
    2. $HOME/.newsalerts (if it already exists or is configured).
    3. OS Standard Defaults:
       - Windows: %APPDATA%\\NewsAlerts (fallback: ~/.newsalerts)
       - macOS: ~/Library/Application Support/NewsAlerts (fallback: ~/.newsalerts)
       - Linux / Unix: $XDG_CONFIG_HOME/NewsAlerts or ~/.config/NewsAlerts (fallback: ~/.newsalerts)

    Automatically creates the target directory with mkdir(parents=True, exist_ok=True).
    """
    # 1. Explicit environment override
    env_dir = os.environ.get("NEWSALERTS_DIR") or os.environ.get("NEWSALERTS_HOME")
    if env_dir:
        target = Path(os.path.expandvars(env_dir)).expanduser().resolve()
        try:
            target.mkdir(parents=True, exist_ok=True)
            return target
        except Exception:
            pass

    # 2. Check if dotfolder ~/.newsalerts already exists
    dot_dir = Path.home() / ".newsalerts"
    if dot_dir.is_dir():
        return dot_dir

    # 3. Standard OS-specific locations
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        target = base / "NewsAlerts"
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
        target = base / "NewsAlerts"
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME")
        if xdg:
            target = Path(os.path.expandvars(xdg)).expanduser() / "NewsAlerts"
        else:
            target = Path.home() / ".config" / "NewsAlerts"

    # Automatically create the directory, falling back to ~/.newsalerts if system path fails
    try:
        target.mkdir(parents=True, exist_ok=True)
        return target
    except Exception:
        try:
            dot_dir.mkdir(parents=True, exist_ok=True)
            return dot_dir
        except Exception:
            return target


APP_DIR = get_app_dir()
CONFIG_PATH = APP_DIR / "config.json"
MEDIA = (
    r"C:\Windows\Media"
    if sys.platform == "win32"
    else "/System/Library/Sounds"
    if sys.platform == "darwin"
    else "/usr/share/sounds"
)


def find_secrets_file() -> Path | None:
    """Find keys.toml / secrets.toml in standard locations:
    1. %APPDATA%\\NewsAlerts\\keys.toml or secrets.toml
    2. Next to the running executable (if frozen)
    3. Project root secrets/keys.toml or secrets/secrets.toml (for dev)
    """
    candidates = [
        APP_DIR / "keys.toml",
        APP_DIR / "secrets.toml",
    ]
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        candidates.extend([exe_dir / "keys.toml", exe_dir / "secrets.toml"])
    else:
        root = Path(__file__).resolve().parent.parent
        candidates.extend([
            root / "secrets" / "keys.toml",
            root / "secrets" / "secrets.toml",
            root / "keys.toml",
        ])
    for p in candidates:
        if p.is_file():
            return p
    return None

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
    {"name": "Large Cap / High Float - Momentum Squeeze", "family": "large", "trigger": "squeeze",
     "float_min": 100e6, "up_pct": 5, "window_min": 5},
    {"name": "Large Cap / High Float - High Rel Vol - Price $20+", "family": "large", "trigger": "hod",
     "float_min": 100e6, "relvol_min": 2, "price_min": 20},
    {"name": "Squeeze Alert - 52wk Breakout", "family": "squeeze", "trigger": "52w"},
    {"name": "Squeeze Alert - Up 10% in 5min", "family": "squeeze", "trigger": "squeeze",
     "up_pct": 10, "window_min": 5},
    {"name": "Squeeze Alert - Up 10% in 10min", "family": "squeeze", "trigger": "squeeze",
     "up_pct": 10, "window_min": 10},
    {"name": "Squeeze Alert - Up 5% in 5min", "family": "squeeze", "trigger": "squeeze",
     "up_pct": 5, "window_min": 5},
]

DEFAULT_HOTKEYS = {
    "mute": "m",
    "popout_tape": "t",
    "pause_tape": "Space",
    "settings": "s",
    "refresh": "r",
    "close_modal": "Escape",
    "focus_story": "Enter",
    "preset_1": "1",
    "preset_2": "2",
    "preset_3": "3",
    "preset_4": "4",
    "preset_5": "5",
}

DEFAULT_CONFIG = {
    "tv": {"sessionid": "", "sessionid_sign": ""},
    "borrow": {"alpaca_key_id": "", "alpaca_secret_key": "", "mode": "auto"},
    "poll": {"screener_sec": 3, "tape_sec": 2, "news_sec": 30},
    "alerts": {
        "reentry_min": 15,
        "mute": False,
        "volume": 80,
        "quiet_when_focused": False,
        "sound_new_symbol": MEDIA + r"\Windows Notify System Generic.wav",
        "news_sound_enabled": True,
        "sound_news": MEDIA + r"\Windows Ding.wav",
        "tape_sound_enabled": False,
        "sound_tape": MEDIA + r"\Windows Navigation Start.wav",
        "telegram_enabled": True,
        "telegram_tape_enabled": True,
        "telegram_tape_cooldown_sec": 60,
        "telegram_bot_token": "",
        "telegram_chat_id": "",
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
        "universe": {"price_min": 1, "price_max": 500, "chg_min": 1, "vol_min": 20e3, "limit": 400},
        "cooldown_sec": 30,
        "max_events": 5000,
        "retention_days": 4,
        "enabled": [s["name"] for s in DEFAULT_STRATEGIES],
        "strategies": DEFAULT_STRATEGIES,
    },
    "hotkeys": copy.deepcopy(DEFAULT_HOTKEYS),
    "ui": {"always_on_top": False, "font_size": 13, "news_width": 420, "tape_height": 300},
}


def _merge(base: dict, override: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    # Ensure any new default tape strategies are added to existing configs
    if "tape" in out and isinstance(out["tape"], dict) and "strategies" in out["tape"]:
        existing_names = {s.get("name") for s in out["tape"]["strategies"] if isinstance(s, dict)}
        for default_s in DEFAULT_STRATEGIES:
            if default_s["name"] not in existing_names:
                out["tape"]["strategies"].append(copy.deepcopy(default_s))
                if "enabled" in out["tape"] and isinstance(out["tape"]["enabled"], list):
                    out["tape"]["enabled"].append(default_s["name"])
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
            # First launch: persist initial default config.json immediately
            cfg = copy.deepcopy(DEFAULT_CONFIG)
            try:
                APP_DIR.mkdir(parents=True, exist_ok=True)
                tmp = CONFIG_PATH.with_suffix(".tmp")
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(cfg, f, indent=2)
                tmp.replace(CONFIG_PATH)
            except Exception:
                pass
            return cfg
        except Exception:
            # Corrupt file: keep a backup, start fresh with defaults
            try:
                CONFIG_PATH.replace(CONFIG_PATH.with_suffix(".bad.json"))
            except Exception:
                pass
            cfg = copy.deepcopy(DEFAULT_CONFIG)
            try:
                APP_DIR.mkdir(parents=True, exist_ok=True)
                tmp = CONFIG_PATH.with_suffix(".tmp")
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(cfg, f, indent=2)
                tmp.replace(CONFIG_PATH)
            except Exception:
                pass
            return cfg


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


def ensure_app_dir_initialized() -> Path:
    """Ensure APP_DIR exists and initial configuration files are provisioned."""
    d = get_app_dir()
    d.mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.is_file():
        try:
            tmp = CONFIG_PATH.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_CONFIG, f, indent=2)
            tmp.replace(CONFIG_PATH)
        except Exception:
            pass
    return d
