"""Windows system sounds: discovery and throttled async playback."""
from __future__ import annotations

import os
import threading
import time
from pathlib import Path

try:
    import winsound
except ImportError:  # non-Windows dev box
    winsound = None

MEDIA_DIR = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Media"


def list_sounds() -> list[dict]:
    out = []
    if MEDIA_DIR.exists():
        for p in sorted(MEDIA_DIR.rglob("*.wav")):
            rel = p.relative_to(MEDIA_DIR)
            out.append({"name": str(rel.with_suffix("")), "path": str(p)})
    return out


class SoundPlayer:
    def __init__(self, min_gap: float = 1.5) -> None:
        self.min_gap = min_gap
        self._last = 0.0
        self._lock = threading.Lock()
        self.muted = False
        self.suppressed = False  # e.g. window focused + quiet_when_focused

    def play(self, path: str, force: bool = False) -> bool:
        if winsound is None or not path:
            return False
        with self._lock:
            if not force:
                if self.muted or self.suppressed:
                    return False
                now = time.time()
                if now - self._last < self.min_gap:
                    return False
                self._last = now
        try:
            if os.path.isfile(path):
                winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC
                                   | winsound.SND_NODEFAULT)
            else:
                winsound.MessageBeep()
            return True
        except Exception:
            return False
