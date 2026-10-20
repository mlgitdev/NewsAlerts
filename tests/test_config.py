"""Unit tests for multi-OS application directory resolution and file provisioning."""
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.config import get_app_dir, ensure_app_dir_initialized, Config, DEFAULT_CONFIG


class TestAppDirResolution(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp()).resolve()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_newsalerts_dir_env_override(self):
        custom = (self.temp_dir / "custom_data_dir").resolve()
        with patch.dict(os.environ, {"NEWSALERTS_DIR": str(custom)}):
            resolved = get_app_dir()
            self.assertEqual(resolved.resolve(), custom.resolve())
            self.assertTrue(resolved.is_dir())

    def test_newsalerts_home_env_override(self):
        custom = (self.temp_dir / "home_override").resolve()
        with patch.dict(os.environ, {"NEWSALERTS_HOME": str(custom)}, clear=False):
            if "NEWSALERTS_DIR" in os.environ:
                del os.environ["NEWSALERTS_DIR"]
            resolved = get_app_dir()
            self.assertEqual(resolved.resolve(), custom.resolve())
            self.assertTrue(resolved.is_dir())

    def test_dotfolder_preference_when_exists(self):
        fake_home = (self.temp_dir / "fake_home").resolve()
        fake_dot = (fake_home / ".newsalerts").resolve()
        fake_dot.mkdir(parents=True)
        with patch.object(Path, "home", return_value=fake_home):
            with patch.dict(os.environ, {}, clear=True):
                resolved = get_app_dir()
                self.assertEqual(resolved.resolve(), fake_dot.resolve())
                self.assertTrue(resolved.is_dir())

    def test_ensure_app_dir_initialized_provisions_defaults(self):
        custom = (self.temp_dir / "provision_test").resolve()
        with patch.dict(os.environ, {"NEWSALERTS_DIR": str(custom)}):
            with patch("app.config.APP_DIR", custom):
                with patch("app.config.CONFIG_PATH", custom / "config.json"):
                    d = ensure_app_dir_initialized()
                    self.assertEqual(d.resolve(), custom.resolve())
                    self.assertTrue(d.is_dir())
                    cfg_file = custom / "config.json"
                    self.assertTrue(cfg_file.is_file())
                    with open(cfg_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self.assertIn("ui", data)
                    self.assertIn("poll", data)
                    self.assertIn("hotkeys", data)
                    self.assertEqual(data["hotkeys"]["mute"], "m")
                    self.assertEqual(data["hotkeys"]["popout_tape"], "t")
                    self.assertEqual(data["hotkeys"]["pause_tape"], "Space")

    def test_hotkeys_configuration_customization_and_save(self):
        custom = (self.temp_dir / "hotkeys_test").resolve()
        with patch.dict(os.environ, {"NEWSALERTS_DIR": str(custom)}):
            with patch("app.config.APP_DIR", custom):
                cfg_path = custom / "config.json"
                with patch("app.config.CONFIG_PATH", cfg_path):
                    config = Config()
                    self.assertIn("hotkeys", config.data)
                    self.assertEqual(config.data["hotkeys"]["mute"], "m")
                    self.assertEqual(config.data["hotkeys"]["refresh"], "r")

                    # Customize hotkeys
                    custom_hotkeys = dict(config.data["hotkeys"])
                    custom_hotkeys["mute"] = "x"
                    custom_hotkeys["refresh"] = "f5"
                    config.update({"hotkeys": custom_hotkeys})

                    # Reload and verify persistence
                    reloaded = Config()
                    self.assertEqual(reloaded.data["hotkeys"]["mute"], "x")
                    self.assertEqual(reloaded.data["hotkeys"]["refresh"], "f5")
                    # Untouched default remains intact
                    self.assertEqual(reloaded.data["hotkeys"]["popout_tape"], "t")

    def test_news_custom_symbols_persistence(self):
        custom = (self.temp_dir / "custom_news_syms").resolve()
        with patch.dict(os.environ, {"NEWSALERTS_DIR": str(custom)}):
            with patch("app.config.APP_DIR", custom):
                cfg_path = custom / "config.json"
                with patch("app.config.CONFIG_PATH", cfg_path):
                    config = Config()
                    self.assertIn("news", config.data)
                    self.assertIn("custom_symbols", config.data["news"])
                    self.assertEqual(config.data["news"]["custom_symbols"], [])

                    # Add custom symbols
                    config.update({"news": {"custom_symbols": ["SMCI", "NVDA", "AAPL"]}})
                    reloaded = Config()
                    self.assertEqual(reloaded.data["news"]["custom_symbols"], ["SMCI", "NVDA", "AAPL"])

    def test_strategies_customization_and_deletion_persistence(self):
        custom = (self.temp_dir / "strategies_test").resolve()
        with patch.dict(os.environ, {"NEWSALERTS_DIR": str(custom)}):
            with patch("app.config.APP_DIR", custom):
                cfg_path = custom / "config.json"
                with patch("app.config.CONFIG_PATH", cfg_path):
                    config = Config()
                    orig_count = len(config.data["tape"]["strategies"])
                    self.assertGreater(orig_count, 0)

                    # Add custom strategy
                    custom_strat = {
                        "name": "Custom Micro Float Momentum",
                        "family": "custom",
                        "trigger": "hod",
                        "float_max": 5e6,
                        "relvol_min": 3.0,
                    }
                    new_strategies = list(config.data["tape"]["strategies"]) + [custom_strat]
                    new_enabled = list(config.data["tape"]["enabled"]) + [custom_strat["name"]]
                    config.update({"tape": {"strategies": new_strategies, "enabled": new_enabled}})

                    reloaded = Config()
                    self.assertEqual(len(reloaded.data["tape"]["strategies"]), orig_count + 1)
                    self.assertIn("Custom Micro Float Momentum", [s["name"] for s in reloaded.data["tape"]["strategies"]])

                    # Delete a strategy and verify deleted_strategies prevents resurrection
                    del_name = "Low Float - Former Momo Stock"
                    filtered_strategies = [s for s in reloaded.data["tape"]["strategies"] if s["name"] != del_name]
                    filtered_enabled = [n for n in reloaded.data["tape"]["enabled"] if n != del_name]
                    config.update({
                        "tape": {
                            "strategies": filtered_strategies,
                            "enabled": filtered_enabled,
                            "deleted_strategies": [del_name],
                        }
                    })

                    reloaded2 = Config()
                    strat_names = [s["name"] for s in reloaded2.data["tape"]["strategies"]]
                    self.assertNotIn(del_name, strat_names)
                    self.assertIn("Custom Micro Float Momentum", strat_names)

    def test_factory_reset_restores_defaults(self):
        custom = (self.temp_dir / "reset_test").resolve()
        with patch.dict(os.environ, {"NEWSALERTS_DIR": str(custom)}):
            with patch("app.config.APP_DIR", custom):
                cfg_path = custom / "config.json"
                with patch("app.config.CONFIG_PATH", cfg_path):
                    config = Config()
                    config.update({
                        "alerts": {"volume": 25},
                        "news": {"custom_symbols": ["TSLA"]},
                    })
                    self.assertEqual(config.data["alerts"]["volume"], 25)
                    self.assertEqual(config.data["news"]["custom_symbols"], ["TSLA"])

                    # Reset to factory defaults
                    fresh = config.reset()
                    self.assertEqual(fresh["alerts"]["volume"], 80)
                    self.assertEqual(fresh["news"]["custom_symbols"], [])

                    reloaded = Config()
                    self.assertEqual(reloaded.data["alerts"]["volume"], 80)
                    self.assertEqual(reloaded.data["news"]["custom_symbols"], [])


if __name__ == "__main__":
    unittest.main()


