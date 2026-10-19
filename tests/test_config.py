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
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_newsalerts_dir_env_override(self):
        custom = Path(self.temp_dir) / "custom_data_dir"
        with patch.dict(os.environ, {"NEWSALERTS_DIR": str(custom)}):
            resolved = get_app_dir()
            self.assertEqual(resolved, custom)
            self.assertTrue(resolved.is_dir())

    def test_newsalerts_home_env_override(self):
        custom = Path(self.temp_dir) / "home_override"
        with patch.dict(os.environ, {"NEWSALERTS_HOME": str(custom)}, clear=False):
            if "NEWSALERTS_DIR" in os.environ:
                del os.environ["NEWSALERTS_DIR"]
            resolved = get_app_dir()
            self.assertEqual(resolved, custom)
            self.assertTrue(resolved.is_dir())

    def test_dotfolder_preference_when_exists(self):
        fake_home = Path(self.temp_dir) / "fake_home"
        fake_dot = fake_home / ".newsalerts"
        fake_dot.mkdir(parents=True)
        with patch.object(Path, "home", return_value=fake_home):
            with patch.dict(os.environ, {}, clear=True):
                resolved = get_app_dir()
                self.assertEqual(resolved, fake_dot)
                self.assertTrue(resolved.is_dir())

    def test_ensure_app_dir_initialized_provisions_defaults(self):
        custom = Path(self.temp_dir) / "provision_test"
        with patch.dict(os.environ, {"NEWSALERTS_DIR": str(custom)}):
            with patch("app.config.APP_DIR", custom):
                with patch("app.config.CONFIG_PATH", custom / "config.json"):
                    d = ensure_app_dir_initialized()
                    self.assertTrue(d.is_dir())
                    cfg_file = custom / "config.json"
                    self.assertTrue(cfg_file.is_file())
                    with open(cfg_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self.assertIn("ui", data)
                    self.assertIn("poll", data)


if __name__ == "__main__":
    unittest.main()
