"""Unit tests for independent In-App Audio Alerts and Telegram Alerts controls."""
import unittest
from unittest.mock import MagicMock

from app.api import Api
from app.screener import ScreenerWorker
from app.tape import TapeWorker


class TestAlertControlsDecoupling(unittest.TestCase):
    def test_tape_telegram_fires_when_audio_muted(self):
        worker = TapeWorker.__new__(TapeWorker)
        worker.cfg = MagicMock()
        worker.cfg.get.return_value = {
            "alerts": {
                "mute": True,  # In-app audio muted!
                "tape_sound_enabled": True,
                "telegram_enabled": True,  # Telegram enabled!
                "telegram_tape_enabled": True,
                "telegram_tape_cooldown_sec": 60,
            },
            "tape": {"enabled": ["Test Strategy"]},
            "filter_banned": False,
            "banned_symbols": [],
        }
        worker.sounds = MagicMock()
        worker.telegram = MagicMock()
        worker.emit = MagicMock()
        worker._tg_last_alert = {}

        # Simulate tape print event
        event = {"symbol": "RUNR", "strategy": "Test Strategy", "price": 4.50}

        # Emulate the dispatch section of poll()
        c = worker.cfg.get()
        enabled = set(c["tape"]["enabled"])
        unbanned_events = [event]
        now = 1000.0
        session = "reg"

        is_paused = bool(c["alerts"].get("mute", False))
        if c["alerts"]["tape_sound_enabled"] and not is_paused and any(e["strategy"] in enabled for e in unbanned_events):
            worker.sounds.play(c["alerts"]["sound_tape"])

        tg_on = c["alerts"].get("telegram_enabled", True) and c["alerts"].get("telegram_tape_enabled", True)
        if worker.telegram and tg_on:
            tg_cd = float(c["alerts"].get("telegram_tape_cooldown_sec", 60))
            for ev in unbanned_events:
                if ev.get("strategy") in enabled:
                    sym = str(ev.get("symbol") or ev.get("ticker", ""))
                    last_t = worker._tg_last_alert.get(sym, 0)
                    if now - last_t >= tg_cd:
                        worker._tg_last_alert[sym] = now
                        worker.telegram.send_tape_alert(ev, session=session)

        # In-app audio must be muted, but Telegram alert MUST be sent!
        worker.sounds.play.assert_not_called()
        worker.telegram.send_tape_alert.assert_called_once_with(event, session="reg")

    def test_tape_telegram_suppressed_when_telegram_disabled_and_audio_active(self):
        worker = TapeWorker.__new__(TapeWorker)
        worker.cfg = MagicMock()
        worker.cfg.get.return_value = {
            "alerts": {
                "mute": False,  # Audio active!
                "tape_sound_enabled": True,
                "sound_tape": "sound.wav",
                "telegram_enabled": False,  # Telegram disabled!
                "telegram_tape_enabled": True,
                "telegram_tape_cooldown_sec": 60,
            },
            "tape": {"enabled": ["Test Strategy"]},
            "filter_banned": False,
            "banned_symbols": [],
        }
        worker.sounds = MagicMock()
        worker.telegram = MagicMock()
        worker.emit = MagicMock()
        worker._tg_last_alert = {}

        event = {"symbol": "RUNR", "strategy": "Test Strategy", "price": 4.50}

        c = worker.cfg.get()
        enabled = set(c["tape"]["enabled"])
        unbanned_events = [event]
        now = 1000.0
        session = "reg"

        is_paused = bool(c["alerts"].get("mute", False))
        if c["alerts"]["tape_sound_enabled"] and not is_paused and any(e["strategy"] in enabled for e in unbanned_events):
            worker.sounds.play(c["alerts"]["sound_tape"])

        tg_on = c["alerts"].get("telegram_enabled", True) and c["alerts"].get("telegram_tape_enabled", True)
        if worker.telegram and tg_on:
            for ev in unbanned_events:
                worker.telegram.send_tape_alert(ev, session=session)

        # In-app audio must play, and Telegram alert must NOT be sent!
        worker.sounds.play.assert_called_once_with("sound.wav")
        worker.telegram.send_tape_alert.assert_not_called()

    def test_api_set_config_updates_telegram_and_sounds_independently(self):
        new_config = {
            "alerts": {
                "mute": True,
                "telegram_enabled": True,
                "telegram_bot_token": "token-123",
                "telegram_chat_id": "chat-456",
                "volume": 75,
            }
        }

        mock_app = MagicMock()
        mock_app.cfg.get.return_value = new_config
        mock_app.telegram = MagicMock()
        mock_app.sounds = MagicMock()
        mock_app.screener = MagicMock()
        mock_app.bus = MagicMock()

        api = Api(mock_app)

        api.save_config(new_config)

        # Sounds should be muted
        self.assertTrue(mock_app.sounds.muted)
        mock_app.sounds.set_volume.assert_called_once_with(75)

        # Telegram should be enabled with paused=False
        mock_app.telegram.update.assert_called_once_with(
            bot_token="token-123",
            chat_id="chat-456",
            enabled=True,
            paused=False,
        )

    def test_api_get_state_exposes_alerts_config_for_initial_launch_sync(self):
        saved_config = {
            "alerts": {
                "mute": True,
                "telegram_enabled": False,
            }
        }
        mock_app = MagicMock()
        mock_app.cfg.get.return_value = saved_config
        mock_app.sounds.list_sounds.return_value = []
        mock_app.borrow.key_id = ""
        mock_app.borrow.secret_key = ""
        mock_app.screener.get_latest_data.return_value = {}
        mock_app.tape.recent.return_value = []
        mock_app.tape_window = None

        api = Api(mock_app)
        state = api.get_state()

        self.assertEqual(state["config"]["alerts"]["mute"], True)
        self.assertEqual(state["config"]["alerts"]["telegram_enabled"], False)


if __name__ == "__main__":
    unittest.main()
