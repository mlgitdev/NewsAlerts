"""Unit tests for running tape momentum strategies, large-cap support, and surge detection."""
import unittest

from app.config import DEFAULT_STRATEGIES
from app.tape import TapeWorker, _match


class TestTapeStrategies(unittest.TestCase):
    def test_default_strategies_include_large_cap_and_fast_squeeze(self):
        names = {s["name"]: s for s in DEFAULT_STRATEGIES}
        self.assertIn("Large Cap / High Float - Momentum Squeeze", names)
        self.assertIn("Large Cap / High Float - High Rel Vol - Price $20+", names)
        self.assertIn("Squeeze Alert - Up 10% in 5min", names)

        large_squeeze = names["Large Cap / High Float - Momentum Squeeze"]
        self.assertEqual(large_squeeze["family"], "large")
        self.assertEqual(large_squeeze["trigger"], "squeeze")
        self.assertEqual(large_squeeze["float_min"], 100e6)
        self.assertNotIn("float_max", large_squeeze)

    def test_match_large_cap_ticker_like_smci(self):
        # SMCI: float ~574M, price $35.73, relvol 2.5
        v_smci = {"price": 35.73, "float": 574e6, "relvol": 2.5, "hi52": 54.53}

        names = {s["name"]: s for s in DEFAULT_STRATEGIES}

        # Low float strategies must reject SMCI
        self.assertFalse(_match(names["Low Float - Former Momo Stock"], v_smci))
        self.assertFalse(_match(names["Low Float - High Rel Vol"], v_smci))
        self.assertFalse(_match(names["Medium Float - High Rel Vol - Price $20+"], v_smci))

        # Large cap strategies must match SMCI
        self.assertTrue(_match(names["Large Cap / High Float - Momentum Squeeze"], v_smci))
        self.assertTrue(_match(names["Large Cap / High Float - High Rel Vol - Price $20+"], v_smci))
        self.assertTrue(_match(names["Squeeze Alert - Up 10% in 5min"], v_smci))

    def test_squeeze_trigger_on_new_entry_session_surge(self):
        worker = TapeWorker.__new__(TapeWorker)
        worker.state = {}
        worker.borrow = None

        r_smci = {
            "ticker": "NASDAQ:SMCI",
            "name": "SMCI",
            "close": 32.47,
            "change": 1.15,
            "postmarket_close": 35.73,
            "postmarket_change": 10.04,
            "float_shares_outstanding": 574e6,
            "volume": 40e6,
            "relative_volume_10d_calc": 2.5,
        }

        strat = {
            "name": "Squeeze Alert - Up 10% in 5min",
            "family": "squeeze",
            "trigger": "squeeze",
            "up_pct": 10,
            "window_min": 5,
        }

        # Process SMCI in post-market session
        events = worker._process(r_smci, "post", now=1700000000.0, strategies=[strat], cooldown=30)
        self.assertEqual(len(events), 1)
        ev = events[0]
        self.assertEqual(ev["ticker"], "NASDAQ:SMCI")
        self.assertEqual(ev["strategy"], "Squeeze Alert - Up 10% in 5min")
        self.assertEqual(ev["price"], 35.73)

    def test_squeeze_trigger_via_change5_server_velocity(self):
        worker = TapeWorker.__new__(TapeWorker)
        worker.state = {}
        worker.borrow = None

        r = {
            "ticker": "NASDAQ:TSLA",
            "name": "TSLA",
            "close": 220.0,
            "change": 2.0,
            "change|5": 10.5,
            "float_shares_outstanding": 2.6e9,
            "volume": 50e6,
            "relative_volume_10d_calc": 1.8,
        }

        strat = {
            "name": "Large Cap / High Float - Momentum Squeeze",
            "family": "large",
            "trigger": "squeeze",
            "float_min": 100e6,
            "up_pct": 5,
            "window_min": 5,
        }

        events = worker._process(r, "regular", now=1700000000.0, strategies=[strat], cooldown=30)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["ticker"], "NASDAQ:TSLA")
        self.assertEqual(events[0]["strategy"], "Large Cap / High Float - Momentum Squeeze")
        self.assertEqual(events[0]["family"], "large")

    def test_squeeze_rejects_declining_and_flat_stocks_like_stak(self):
        worker = TapeWorker.__new__(TapeWorker)
        worker.state = {}
        worker.borrow = None

        strat5 = {
            "name": "Squeeze Alert - Up 5% in 5min",
            "family": "squeeze",
            "trigger": "squeeze",
            "up_pct": 5,
            "window_min": 5,
        }
        strat10 = {
            "name": "Squeeze Alert - Up 10% in 10min",
            "family": "squeeze",
            "trigger": "squeeze",
            "up_pct": 10,
            "window_min": 10,
        }
        strats = [strat5, strat10]

        # STAK in premarket: peaked earlier at $2.13, now consolidating around $1.85
        # (37 bars / 37 minutes between 1.81 and 1.88, down -13% from peak)
        t0 = 1700000000.0
        st = worker.state.setdefault("NASDAQ:STAK", worker.state.get("NASDAQ:STAK") or type("SymState", (), {"hist": None, "high": None, "price": None, "day": None, "last_fire": {}, "last_fire_price": {}})())
        import collections
        st.hist = collections.deque([
            (t0 - 240, 1.82, 4.4e6),
            (t0 - 180, 1.84, 4.45e6),
            (t0 - 120, 1.86, 4.5e6),
            (t0 - 60, 1.83, 4.55e6),
            (t0 - 10, 1.85, 4.6e6),
        ])

        r_stak = {
            "ticker": "NASDAQ:STAK",
            "name": "STAK",
            "close": 1.67,
            "change": 67.0,
            "premarket_close": 1.85,
            "premarket_change": 9.58,
            "premarket_high": 2.13,
            "premarket_low": 1.74,
            "volume": 80e6,
            "premarket_volume": 4.66e6,
            "relative_volume_10d_calc": 32.39,
            "change|5": 9.6875,   # Static/invalid TV premarket value
            "change|15": 11.4285, # Static/invalid TV premarket value
        }

        # Must reject: STAK has only moved between 1.82 and 1.86 in window (under 5%),
        # and current price $1.85 is well below premarket high $2.13
        events = worker._process(r_stak, "pre", now=t0, strategies=strats, cooldown=30)
        self.assertEqual(len(events), 0, "Flat/declining stock STAK must not trigger false squeeze alerts")

    def test_squeeze_dynamic_upward_surge_and_progression(self):
        worker = TapeWorker.__new__(TapeWorker)
        worker.state = {}
        worker.borrow = None

        strat = {
            "name": "Squeeze Alert - Up 5% in 5min",
            "family": "squeeze",
            "trigger": "squeeze",
            "up_pct": 5,
            "window_min": 5,
        }

        t0 = 1700000000.0
        # Simulating active surge from $2.00 to $2.12 (+6%) over 3 minutes
        import collections
        st = worker.state.setdefault("NASDAQ:SURG", type("SymState", (), {"hist": None, "high": None, "price": None, "day": None, "last_fire": {}, "last_fire_price": {}})())
        st.hist = collections.deque([
            (t0 - 180, 2.00, 1.0e6),
            (t0 - 120, 2.05, 1.2e6),
            (t0 - 60, 2.08, 1.4e6),
        ])

        r = {
            "ticker": "NASDAQ:SURG",
            "name": "SURG",
            "close": 2.00,
            "premarket_close": 2.12,
            "premarket_high": 2.12,
            "premarket_low": 2.00,
            "volume": 5e6,
            "premarket_volume": 1.5e6,
            "relative_volume_10d_calc": 3.0,
        }

        # 1. Initial surge fires
        ev1 = worker._process(r, "pre", now=t0, strategies=[strat], cooldown=30)
        self.assertEqual(len(ev1), 1)
        self.assertEqual(ev1[0]["price"], 2.12)
        self.assertEqual(ev1[0]["strategy"], "Squeeze Alert - Up 5% in 5min")

        # 2. Tick 30s later with minor noise ($2.121): must NOT re-fire (requires >= 1% advance)
        r_noise = dict(r, premarket_close=2.121)
        ev2 = worker._process(r_noise, "pre", now=t0 + 35, strategies=[strat], cooldown=30)
        self.assertEqual(len(ev2), 0)

        # 3. Advancement to $2.16 (+1.8% above $2.12): fires second progression alert
        r_higher = dict(r, premarket_close=2.16, premarket_high=2.16)
        ev3 = worker._process(r_higher, "pre", now=t0 + 40, strategies=[strat], cooldown=30)
        self.assertEqual(len(ev3), 1)
        self.assertEqual(ev3[0]["price"], 2.16)

        # 4. Pullback to $2.05: must NOT fire while falling back from crest
        r_pullback = dict(r, premarket_close=2.05, premarket_high=2.16)
        ev4 = worker._process(r_pullback, "pre", now=t0 + 80, strategies=[strat], cooldown=30)
        self.assertEqual(len(ev4), 0)


if __name__ == "__main__":
    unittest.main()
