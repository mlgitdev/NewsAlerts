"""Unit tests for Api methods: get_quote, reset_config, get_default_config."""
import unittest
from unittest.mock import MagicMock, patch

from app.api import Api


class TestApiMethods(unittest.TestCase):
    def setUp(self):
        self.mock_app = MagicMock()
        self.api = Api(self.mock_app)

    def test_get_default_config_structure(self):
        cfg = self.api.get_default_config()
        self.assertIsInstance(cfg, dict)
        self.assertIn("news", cfg)
        self.assertIn("custom_symbols", cfg["news"])
        self.assertIn("tape", cfg)
        self.assertIn("strategies", cfg["tape"])
        self.assertIn("alerts", cfg)
        self.assertIn("hotkeys", cfg)

    def test_get_quote_resolves_symbol(self):
        mock_row = {
            "ticker": "NASDAQ:SMCI",
            "name": "SMCI",
            "description": "Super Micro Computer, Inc.",
            "close": 35.73,
            "change": 10.04,
            "volume": 50e6,
            "relative_volume_10d_calc": 3.0,
            "float_shares_outstanding": 574e6,
            "logoid": "smci-logo",
        }
        self.mock_app.client.scan.return_value = [mock_row]
        self.mock_app.borrow.get_status.return_value = {"status": "easy", "label": "ETB"}
        self.mock_app.borrow.get_details.return_value = {"marginable": True}
        self.mock_app.borrow.get_snapshot.return_value = {"bid": 35.70, "ask": 35.75}

        # Query using bare symbol
        res = self.api.get_quote("SMCI")
        self.assertIsNotNone(res)
        self.assertEqual(res["ticker"], "NASDAQ:SMCI")
        self.assertEqual(res["symbol"], "SMCI")
        self.assertEqual(res["desc"], "Super Micro Computer, Inc.")
        self.assertEqual(res["borrow"]["status"], "easy")

        # Query using exchange-qualified symbol
        res2 = self.api.get_quote("NASDAQ:SMCI")
        self.assertIsNotNone(res2)
        self.assertEqual(res2["ticker"], "NASDAQ:SMCI")

    def test_get_quote_returns_none_for_missing_or_empty(self):
        self.assertIsNone(self.api.get_quote(""))
        self.assertIsNone(self.api.get_quote("   "))

        self.mock_app.client.scan.return_value = []
        self.assertIsNone(self.api.get_quote("UNKNOWN123"))

    def test_reset_config_invokes_cfg_reset_and_save(self):
        default_cfg = {"news": {"custom_symbols": []}, "tape": {"strategies": []}}
        self.mock_app.cfg.reset.return_value = default_cfg
        self.mock_app.cfg.get.return_value = default_cfg
        self.mock_app.bus = MagicMock()
        self.mock_app.screener = MagicMock()
        self.mock_app.sounds = MagicMock()
        self.mock_app.telegram = MagicMock()
        self.mock_app.borrow = MagicMock()
        self.mock_app.client = MagicMock()

        res = self.api.reset_config()
        self.mock_app.cfg.reset.assert_called_once()
        self.assertEqual(res, default_cfg)

    def test_send_telegram_test_forwards_credentials(self):
        self.mock_app.telegram.send_test_message.return_value = (True, "Test alert sent to Telegram successfully!")
        res = self.api.send_telegram_test(bot_token="123456:ABC-DEF", chat_id="987654321")
        self.mock_app.telegram.send_test_message.assert_called_once_with(
            bot_token="123456:ABC-DEF", chat_id="987654321"
        )
        self.assertTrue(res["ok"])
        self.assertEqual(res["message"], "Test alert sent to Telegram successfully!")

    @patch("requests.get")
    def test_test_alpaca_uses_provided_credentials(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"id": "acc-123", "buying_power": "50000.00", "status": "ACTIVE"}
        mock_get.return_value = mock_resp

        res = self.api.test_alpaca(key_id="CUSTOM_KEY", secret_key="CUSTOM_SECRET")
        self.assertTrue(res["ok"])
        self.assertIn("ACTIVE", res["message"])
        self.assertIn("$50,000.00", res["message"])

        # Verify headers used custom keys
        mock_get.assert_called_once()
        _, kwargs = mock_get.call_args
        self.assertEqual(kwargs["headers"]["APCA-API-KEY-ID"], "CUSTOM_KEY")
        self.assertEqual(kwargs["headers"]["APCA-API-SECRET-KEY"], "CUSTOM_SECRET")

    def test_get_watchlists_tradingview_cloud(self):
        self.mock_app.cfg.get.return_value = {
            "watchlist": {"active_id": "tv_1", "active_title": "Day Trades", "custom_lists": []}
        }
        self.mock_app.client.get_watchlists.return_value = {
            "ok": True,
            "watchlists": [{"id": "tv_1", "title": "Day Trades", "count": 12}],
        }
        res = self.api.get_watchlists()
        self.assertTrue(res["ok"])
        self.assertTrue(res["connected"])
        self.assertEqual(res["source"], "tradingview")
        self.assertEqual(len(res["watchlists"]), 1)
        self.assertEqual(res["active_id"], "tv_1")

    def test_get_watchlists_local_fallback(self):
        self.mock_app.cfg.get.return_value = {
            "watchlist": {
                "active_id": "local_default",
                "active_title": "Momentum Watchlist",
                "custom_lists": [{"id": "local_default", "title": "Momentum Watchlist", "symbols": ["AAPL"]}],
            }
        }
        self.mock_app.client.get_watchlists.return_value = {
            "ok": False,
            "message": "Session unauthenticated",
            "watchlists": [],
        }
        res = self.api.get_watchlists()
        self.assertTrue(res["ok"])
        self.assertFalse(res["connected"])
        self.assertEqual(res["source"], "local")
        self.assertEqual(res["active_id"], "local_default")

    def test_select_watchlist(self):
        cfg = {"watchlist": {"active_id": "tv_1", "active_title": "Old"}}
        self.mock_app.cfg.get.return_value = cfg
        res = self.api.select_watchlist("tv_2", "New Watchlist")
        self.assertTrue(res["ok"])
        self.assertEqual(res["active_id"], "tv_2")
        self.assertEqual(res["active_title"], "New Watchlist")
        self.mock_app.cfg.update.assert_called_once()

    def test_add_to_watchlist_tradingview(self):
        self.mock_app.client.sessionid = "active_tv_session"
        cfg = {
            "watchlist": {
                "active_id": "12345",
                "active_title": "Momentum",
                "custom_lists": [],
            }
        }
        self.mock_app.cfg.get.return_value = cfg
        self.mock_app.client.add_to_watchlist.return_value = {
            "ok": True,
            "message": "Symbol added to TradingView watchlist",
            "symbol": "NASDAQ:TSLA",
            "list_id": "12345",
        }

        # Mock quote lookup for exchange qualification
        mock_row = {"ticker": "NASDAQ:TSLA", "name": "TSLA", "description": "Tesla", "close": 200.0, "change": 5.0, "volume": 10e6, "relative_volume_10d_calc": 1.0, "float_shares_outstanding": 3e9}
        self.mock_app.client.scan.return_value = [mock_row]
        self.mock_app.borrow.get_status.return_value = {"status": "easy", "label": "ETB"}
        self.mock_app.borrow.get_details.return_value = {}
        self.mock_app.borrow.get_snapshot.return_value = {}

        res = self.api.add_to_watchlist("12345", "TSLA")
        self.assertTrue(res["ok"])
        self.mock_app.client.add_to_watchlist.assert_called_once_with("12345", "NASDAQ:TSLA")

    def test_add_to_watchlist_local(self):
        self.mock_app.client.sessionid = ""
        cfg = {
            "watchlist": {
                "active_id": "local_default",
                "active_title": "Momentum Watchlist",
                "custom_lists": [{"id": "local_default", "title": "Momentum Watchlist", "symbols": []}],
            }
        }
        self.mock_app.cfg.get.return_value = cfg

        res = self.api.add_to_watchlist("local_default", "NVDA")
        self.assertTrue(res["ok"])
        self.assertEqual(res["source"], "local")
        self.mock_app.cfg.update.assert_called_once()

    def test_set_on_top_guard(self):
        mock_window = MagicMock()
        self.mock_app.main_window = mock_window

        # Initial call sets state and invokes window logic
        self.assertTrue(self.api.set_on_top(True))
        self.assertEqual(getattr(mock_window, "_on_top_state", None), True)

        # Calling again with identical state skips redundant updates
        self.assertTrue(self.api.set_on_top(True))
        self.assertEqual(getattr(mock_window, "_on_top_state", None), True)

        # Calling with False updates state
        self.assertTrue(self.api.set_on_top(False))
        self.assertEqual(getattr(mock_window, "_on_top_state", None), False)

    def test_get_state_includes_storage_metadata(self):
        self.mock_app.borrow.key_id = "PKTEST123456"
        self.mock_app.borrow.secret_key = "SECRET123"
        self.mock_app.client.get_auth_status.return_value = {"connected": True, "username": "pro_trader"}
        self.mock_app.screener.status_payload.return_value = {}
        self.mock_app.screener.last_rows = []
        self.mock_app.tape.snapshot.return_value = []
        self.mock_app.tape_window = None
        self.mock_app.bus.latest_id.return_value = 42

        state = self.api.get_state()
        self.assertIn("app_dir", state)
        self.assertIn("secrets_file", state)
        self.assertIn("has_keys_toml", state)
        self.assertIsInstance(state["app_dir"], str)
        self.assertTrue(len(state["app_dir"]) > 0)
        self.assertIsInstance(state["has_keys_toml"], bool)

    @patch("os.startfile", create=True)
    def test_open_app_dir_windows(self, mock_startfile):
        with patch("sys.platform", "win32"):
            res = self.api.open_app_dir()
            self.assertTrue(res["ok"])
            mock_startfile.assert_called_once()

    @patch("subprocess.Popen")
    def test_open_app_dir_unix(self, mock_popen):
        with patch("sys.platform", "darwin"):
            res = self.api.open_app_dir()
            self.assertTrue(res["ok"])
            mock_popen.assert_called_once()


if __name__ == "__main__":
    unittest.main()
