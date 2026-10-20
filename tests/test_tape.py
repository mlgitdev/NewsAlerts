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


if __name__ == "__main__":
    unittest.main()
