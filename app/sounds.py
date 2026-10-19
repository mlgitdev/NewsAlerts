"""Windows system sounds: discovery and throttled async playback."""
from __future__ import annotations

import os
import threading
import time
from pathlib import Path

import shutil
import subprocess
import sys

try:
    import winsound
except ImportError:  # non-Windows (macOS, Linux)
    winsound = None

if sys.platform == "win32":
    MEDIA_DIR = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Media"
    SOUND_EXTS = ("*.wav",)
elif sys.platform == "darwin":
    MEDIA_DIR = Path("/System/Library/Sounds")
    SOUND_EXTS = ("*.aiff", "*.wav", "*.caf")
else:
    MEDIA_DIR = Path("/usr/share/sounds")
    SOUND_EXTS = ("*.wav", "*.ogg")


def list_sounds() -> list[dict]:
    out = []
    if MEDIA_DIR.exists():
        for pat in SOUND_EXTS:
            for p in sorted(MEDIA_DIR.rglob(pat)):
                rel = p.relative_to(MEDIA_DIR)
                out.append({"name": str(rel.with_suffix("")), "path": str(p)})
    return out


class SoundPlayer:
    def __init__(self, min_gap: float = 1.5, volume: int = 80) -> None:
        self.min_gap = min_gap
        self._last = 0.0
        self._lock = threading.Lock()
        self.muted = False
        self.suppressed = False  # e.g. window focused + quiet_when_focused
        self.volume = 80
        self.set_volume(volume)

    def set_volume(self, volume: int) -> None:
        self.volume = max(0, min(100, int(volume)))
        if sys.platform == "win32":
            try:
                import ctypes
                v = int((self.volume / 100.0) * 0xFFFF)
                dw_volume = (v & 0xFFFF) | ((v & 0xFFFF) << 16)
                ctypes.windll.winmm.waveOutSetVolume(0, dw_volume)
                ctypes.windll.winmm.waveOutSetVolume(-1, dw_volume)
            except Exception:
                pass

    def play(self, path: str, force: bool = False) -> bool:
        if not path:
            return False
        with self._lock:
            if not force:
                if self.muted or self.suppressed or self.volume <= 0:
                    return False
                now = time.time()
                if now - self._last < self.min_gap:
                    return False
                self._last = now
        try:
            if sys.platform == "win32" and winsound is not None:
                if os.path.isfile(path):
                    winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC
                                       | winsound.SND_NODEFAULT)
                else:
                    winsound.MessageBeep()
                return True
            elif sys.platform == "darwin":
                if os.path.isfile(path) and shutil.which("afplay"):
                    subprocess.Popen(["afplay", "-v", str(self.volume / 100.0), path],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return True
            elif sys.platform.startswith("linux"):
                player = shutil.which("paplay") or shutil.which("aplay") or shutil.which("canberra-gtk-play")
                if os.path.isfile(path) and player:
                    cmd = [player, path] if "canberra" not in player else [player, "-f", path]
                    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return True
            # Fallback beep
            sys.stdout.write("\a")
            sys.stdout.flush()
            return True
        except Exception:
            return False
