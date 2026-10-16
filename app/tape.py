"""Running tape: polls a momentum universe, keeps rolling history, emits strategy events."""
from __future__ import annotations

import collections
import logging
import threading
import time
from typing import Callable

from . import sessions as S
from .borrow import BorrowService
from .config import Config
from .sounds import SoundPlayer
from .tv_client import TVClient, TVError

log = logging.getLogger(__name__)

HISTORY_SEC = 30 * 60
BARS_PER_DAY = 78  # 5-min bars in a regular session


class _SymState:
    __slots__ = ("hist", "high", "price", "day", "last_fire")

    def __init__(self) -> None:
        self.hist: collections.deque = collections.deque()  # (ts, price, volume)
        self.high = None
        self.price = None
        self.day = None
        self.last_fire: dict[str, float] = {}


def _match(strat: dict, v: dict) -> bool:
    def rng(val, lo_key, hi_key):
        lo, hi = strat.get(lo_key), strat.get(hi_key)
        if lo is None and hi is None:
            return True
        if val is None:
            return False
        if lo is not None and val < lo:
            return False
        if hi is not None and val >= hi:
            return False
        return True

    if not (rng(v["float"], "float_min", "float_max") and rng(v["relvol"], "relvol_min", "relvol_max")
            and rng(v["price"], "price_min", "price_max")):
        return False
    ratio = strat.get("hi52_ratio_min")
    if ratio:
        if not v["hi52"] or not v["price"] or v["hi52"] < ratio * v["price"]:
            return False
    return True


class TapeWorker(threading.Thread):
    def __init__(self, cfg: Config, client: TVClient, sounds: SoundPlayer,
                 emit: Callable[[str, object], None], borrow: BorrowService | None = None) -> None:
        super().__init__(daemon=True, name="tape")
        self.cfg = cfg
        self.client = client
        self.sounds = sounds
        self.emit = emit
        self.borrow = borrow
        self.state: dict[str, _SymState] = {}
        self.events: collections.deque = collections.deque(maxlen=2000)
        self._session = None

    def snapshot(self) -> list[dict]:
        return list(self.events)

    def run(self) -> None:
        while True:
            t0 = time.time()
            try:
                self.tick()
            except TVError as e:
                log.info("tape: %s", e)
            except Exception:
                log.exception("tape tick")
            interval = max(1.0, float(self.cfg["poll"]["tape_sec"]))
            time.sleep(max(0.2, interval - (time.time() - t0)))

    def tick(self) -> None:
        c = self.cfg.get()
        tc = c["tape"]
        u = tc["universe"]
        session = S.current_session()
        if session != self._session:  # new session: reset HOD tracking
            self.state.clear()
            self._session = session
        if S.market_state() == "closed":
            return
        f = lambda k: S.tv_field(k, session)  # noqa: E731
        filters = [
            {"left": f("price"), "operation": "in_range", "right": [u["price_min"], u["price_max"]]},
            {"left": f("chg"), "operation": "egreater", "right": u["chg_min"]},
            {"left": f("vol"), "operation": "egreater", "right": u["vol_min"]},
        ]
        rows = self.client.scan(filters, f("chg"), True, limit=int(u["limit"]))
        now = time.time()
        enabled = set(tc["enabled"])
        cooldown = float(tc["cooldown_sec"])
        new_events = []
        for r in rows:
            ev = self._process(r, session, now, tc["strategies"], cooldown)
            new_events.extend(ev)
        if new_events:
            self.events.extendleft(new_events)
            while len(self.events) > int(tc["max_events"]):
                self.events.pop()
            self.emit("tape", new_events)
            if c["alerts"]["tape_sound_enabled"] and any(e["strategy"] in enabled for e in new_events):
                self.sounds.play(c["alerts"]["sound_tape"])

    def _process(self, r: dict, session: str, now: float, strategies: list, cooldown: float) -> list:
        lg = S.logical_row(r, session)
        price, vol = lg["price"], lg["vol"]
        if price is None:
            return []
        st = self.state.setdefault(r["ticker"], _SymState())
        high = lg["high"] if lg["high"] is not None else price
        high = max(high, price)

        # 5-min relative volume (%) from our own history vs average 5-min volume
        relvol5 = None
        avg = r.get("average_volume_10d_calc")
        if st.hist and vol is not None and avg:
            past = next((h for h in st.hist if h[0] >= now - 300), st.hist[0])
            span = max(now - past[0], 30)
            dv = max(0, vol - (past[2] or 0))
            relvol5 = dv / (avg / BARS_PER_DAY) * (300 / span) * 100

        hi52, lo52 = r.get("price_52_week_high"), r.get("price_52_week_low")
        low = lg["low"]
        atr = r.get("ATR")
        v = {
            "price": price, "float": lg["float"], "relvol": lg["relvol"], "hi52": hi52,
        }
        prev_price, prev_high = st.price, st.high
        triggers = []
        if prev_high is not None and high > prev_high and price >= high * 0.999:
            triggers.append("hod")
        if hi52 and prev_price is not None and prev_price < hi52 <= price:
            triggers.append("52w")

        events = []
        for strat in strategies:
            trig = strat.get("trigger", "hod")
            name = strat["name"]
            fired = False
            if trig in ("hod", "52w"):
                fired = trig in triggers and _match(strat, v)
            elif trig == "squeeze" and st.hist:
                win = now - float(strat.get("window_min", 5)) * 60
                lows = [h[1] for h in st.hist if h[0] >= win and h[1]]
                if lows and now - st.hist[0][0] >= 30:
                    fired = price >= min(lows) * (1 + float(strat.get("up_pct", 5)) / 100) \
                        and _match(strat, v)
            if fired and now - st.last_fire.get(name, 0) >= cooldown:
                st.last_fire[name] = now
                borrow_info = self.borrow.get_status(r["ticker"], lg["float"]) if self.borrow else {"status": "na", "label": "N/A"}
                events.append({
                    "ts": now, "ticker": r["ticker"], "symbol": r.get("name"),
                    "price": price, "volume": vol, "float": lg["float"],
                    "relvol": lg["relvol"], "relvol5": relvol5, "chg": lg["chg"],
                    "gap": lg["gap"],
                    "borrow": borrow_info,
                    "pos52": ((price - lo52) / (hi52 - lo52) * 100) if hi52 and lo52 is not None
                    and hi52 > lo52 else None,
                    "range": ((high - low) / atr * 100) if atr and low is not None else None,
                    "strategy": name, "family": strat.get("family", "low"),
                })

        st.price, st.high = price, high
        st.hist.append((now, price, vol))
        while st.hist and st.hist[0][0] < now - HISTORY_SEC:
            st.hist.popleft()
        return events
