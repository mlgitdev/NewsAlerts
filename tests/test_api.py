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


if __name__ == "__main__":
    unittest.main()
