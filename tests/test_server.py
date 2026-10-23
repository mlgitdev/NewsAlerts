"""Unit tests for Bottle server static file routing (app/server.py)."""
import io
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from app.server import make_app


class TestServerStaticRoutes(unittest.TestCase):
    def setUp(self):
        self.web_dir = Path(__file__).resolve().parent.parent / "web"
        self.api = MagicMock()
        self.app = make_app(self.api, self.web_dir)

    def test_routes_exist(self):
        routes = [r.rule for r in self.app.routes]
        self.assertIn("/img/<filepath:path>", routes)
        self.assertIn("/assets/<filepath:path>", routes)
        self.assertIn("/favicon.ico", routes)
        self.assertIn("/icon.png", routes)
        self.assertIn("/css/<filepath:path>", routes)
        self.assertIn("/js/<filepath:path>", routes)
        self.assertIn("/", routes)

    def test_img_route_resolves_hero(self):
        status_line = []
        headers_list = []

        def start_response(status, headers, exc_info=None):
            status_line.append(status)
            headers_list.extend(headers)

        environ = {
            "REQUEST_METHOD": "GET",
            "PATH_INFO": "/img/hero.jpg",
            "wsgi.input": io.BytesIO(),
            "wsgi.errors": io.StringIO(),
            "wsgi.version": (1, 0),
            "wsgi.multithread": False,
            "wsgi.multiprocess": False,
            "wsgi.run_once": False,
            "wsgi.url_scheme": "http",
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "8080",
        }
        res = self.app(environ, start_response)
        self.assertTrue(status_line and status_line[0].startswith("200"))
        # Check Content-Type header
        ct = dict(headers_list).get("Content-Type", "")
        self.assertTrue(ct.startswith("image/jpeg"))
        if hasattr(res, "close"):
            res.close()

    def test_icon_route_resolves(self):
        status_line = []
        headers_list = []

        def start_response(status, headers, exc_info=None):
            status_line.append(status)
            headers_list.extend(headers)

        environ = {
            "REQUEST_METHOD": "GET",
            "PATH_INFO": "/icon.png",
            "wsgi.input": io.BytesIO(),
            "wsgi.errors": io.StringIO(),
            "wsgi.version": (1, 0),
            "wsgi.multithread": False,
            "wsgi.multiprocess": False,
            "wsgi.run_once": False,
            "wsgi.url_scheme": "http",
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "8080",
        }
        res = self.app(environ, start_response)
        self.assertTrue(status_line and status_line[0].startswith("200"))
        ct = dict(headers_list).get("Content-Type", "")
        self.assertTrue(ct.startswith("image/png"))
        if hasattr(res, "close"):
            res.close()

    def test_refresh_route(self):
        self.api.refresh.return_value = True
        status_line = []
        headers_list = []

        def start_response(status, headers, exc_info=None):
            status_line.append(status)
            headers_list.extend(headers)

        environ = {
            "REQUEST_METHOD": "POST",
            "PATH_INFO": "/api/refresh",
            "wsgi.input": io.BytesIO(),
            "wsgi.errors": io.StringIO(),
            "wsgi.version": (1, 0),
            "wsgi.multithread": False,
            "wsgi.multiprocess": False,
            "wsgi.run_once": False,
            "wsgi.url_scheme": "http",
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "8080",
        }
        res = self.app(environ, start_response)
        self.assertTrue(status_line and status_line[0].startswith("200"))
        self.api.refresh.assert_called_once()
        if hasattr(res, "close"):
            res.close()

    def test_test_telegram_route_with_payload(self):
        import json
        self.api.send_telegram_test.return_value = {"ok": True, "message": "Sent!"}
        payload = json.dumps({"bot_token": "token123", "chat_id": "chat456"}).encode("utf-8")
        status_line = []
        headers_list = []

        def start_response(status, headers, exc_info=None):
            status_line.append(status)
            headers_list.extend(headers)

        environ = {
            "REQUEST_METHOD": "POST",
            "PATH_INFO": "/api/test_telegram",
            "CONTENT_TYPE": "application/json",
            "CONTENT_LENGTH": str(len(payload)),
            "wsgi.input": io.BytesIO(payload),
            "wsgi.errors": io.StringIO(),
            "wsgi.version": (1, 0),
            "wsgi.multithread": False,
            "wsgi.multiprocess": False,
            "wsgi.run_once": False,
            "wsgi.url_scheme": "http",
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "8080",
        }
        res = self.app(environ, start_response)
        self.assertTrue(status_line and status_line[0].startswith("200"))
        self.api.send_telegram_test.assert_called_once_with(bot_token="token123", chat_id="chat456")
        if hasattr(res, "close"):
            res.close()

    def test_test_alpaca_route_with_payload(self):
        import json
        self.api.test_alpaca.return_value = {"ok": True, "message": "Connected!"}
        payload = json.dumps({"key_id": "key_abc", "secret_key": "sec_xyz"}).encode("utf-8")
        status_line = []
        headers_list = []

        def start_response(status, headers, exc_info=None):
            status_line.append(status)
            headers_list.extend(headers)

        environ = {
            "REQUEST_METHOD": "POST",
            "PATH_INFO": "/api/test_alpaca",
            "CONTENT_TYPE": "application/json",
            "CONTENT_LENGTH": str(len(payload)),
            "wsgi.input": io.BytesIO(payload),
            "wsgi.errors": io.StringIO(),
            "wsgi.version": (1, 0),
            "wsgi.multithread": False,
            "wsgi.multiprocess": False,
            "wsgi.run_once": False,
            "wsgi.url_scheme": "http",
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "8080",
        }
        res = self.app(environ, start_response)
        self.assertTrue(status_line and status_line[0].startswith("200"))
        self.api.test_alpaca.assert_called_once_with(key_id="key_abc", secret_key="sec_xyz")
        if hasattr(res, "close"):
            res.close()

    def test_tv_watchlists_route(self):
        self.api.get_watchlists.return_value = {"ok": True, "watchlists": [{"id": "1", "title": "Test"}]}
        status_line = []
        headers_list = []

        def start_response(status, headers, exc_info=None):
            status_line.append(status)
            headers_list.extend(headers)

        environ = {
            "REQUEST_METHOD": "GET",
            "PATH_INFO": "/api/tv_watchlists",
            "wsgi.input": io.BytesIO(),
            "wsgi.errors": io.StringIO(),
            "wsgi.version": (1, 0),
            "wsgi.multithread": False,
            "wsgi.multiprocess": False,
            "wsgi.run_once": False,
            "wsgi.url_scheme": "http",
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "8080",
        }
        res = self.app(environ, start_response)
        self.assertTrue(status_line and status_line[0].startswith("200"))
        self.api.get_watchlists.assert_called_once()
        if hasattr(res, "close"):
            res.close()

    def test_tv_watchlist_select_route(self):
        import json
        self.api.select_watchlist.return_value = {"ok": True, "active_id": "123", "active_title": "Day Trades"}
        payload = json.dumps({"list_id": "123", "title": "Day Trades"}).encode("utf-8")
        status_line = []
        headers_list = []

        def start_response(status, headers, exc_info=None):
            status_line.append(status)
            headers_list.extend(headers)

        environ = {
            "REQUEST_METHOD": "POST",
            "PATH_INFO": "/api/tv_watchlist/select",
            "CONTENT_TYPE": "application/json",
            "CONTENT_LENGTH": str(len(payload)),
            "wsgi.input": io.BytesIO(payload),
            "wsgi.errors": io.StringIO(),
            "wsgi.version": (1, 0),
            "wsgi.multithread": False,
            "wsgi.multiprocess": False,
            "wsgi.run_once": False,
            "wsgi.url_scheme": "http",
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "8080",
        }
        res = self.app(environ, start_response)
        self.assertTrue(status_line and status_line[0].startswith("200"))
        self.api.select_watchlist.assert_called_once_with(list_id="123", title="Day Trades")
        if hasattr(res, "close"):
            res.close()

    def test_tv_watchlist_add_route(self):
        import json
        self.api.add_to_watchlist.return_value = {"ok": True, "symbol": "NASDAQ:AAPL", "list_id": "123"}
        payload = json.dumps({"list_id": "123", "symbol": "AAPL"}).encode("utf-8")
        status_line = []
        headers_list = []

        def start_response(status, headers, exc_info=None):
            status_line.append(status)
            headers_list.extend(headers)

        environ = {
            "REQUEST_METHOD": "POST",
            "PATH_INFO": "/api/tv_watchlist/add",
            "CONTENT_TYPE": "application/json",
            "CONTENT_LENGTH": str(len(payload)),
            "wsgi.input": io.BytesIO(payload),
            "wsgi.errors": io.StringIO(),
            "wsgi.version": (1, 0),
            "wsgi.multithread": False,
            "wsgi.multiprocess": False,
            "wsgi.run_once": False,
            "wsgi.url_scheme": "http",
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "8080",
        }
        res = self.app(environ, start_response)
        self.assertTrue(status_line and status_line[0].startswith("200"))
        self.api.add_to_watchlist.assert_called_once_with(list_id="123", symbol="AAPL")
        if hasattr(res, "close"):
            res.close()

    def test_ban_symbol_route(self):
        import json
        self.api.ban_symbol.return_value = {"ok": True, "banned_symbols": ["AIOK"], "symbol": "AIOK"}
        payload = json.dumps({"symbol": "AIOK"}).encode("utf-8")
        status_line = []
        headers_list = []

        def start_response(status, headers, exc_info=None):
            status_line.append(status)
            headers_list.extend(headers)

        environ = {
            "REQUEST_METHOD": "POST",
            "PATH_INFO": "/api/ban_symbol",
            "CONTENT_TYPE": "application/json",
            "CONTENT_LENGTH": str(len(payload)),
            "wsgi.input": io.BytesIO(payload),
            "wsgi.errors": io.StringIO(),
            "wsgi.version": (1, 0),
            "wsgi.multithread": False,
            "wsgi.multiprocess": False,
            "wsgi.run_once": False,
            "wsgi.url_scheme": "http",
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "8080",
        }
        res = self.app(environ, start_response)
        self.assertTrue(status_line and status_line[0].startswith("200"))
        self.api.ban_symbol.assert_called_once_with("AIOK")
        if hasattr(res, "close"):
            res.close()

    def test_unban_symbol_route(self):
        import json
        self.api.unban_symbol.return_value = {"ok": True, "banned_symbols": [], "symbol": "AIOK"}
        payload = json.dumps({"symbol": "AIOK"}).encode("utf-8")
        status_line = []
        headers_list = []

        def start_response(status, headers, exc_info=None):
            status_line.append(status)
            headers_list.extend(headers)

        environ = {
            "REQUEST_METHOD": "POST",
            "PATH_INFO": "/api/unban_symbol",
            "CONTENT_TYPE": "application/json",
            "CONTENT_LENGTH": str(len(payload)),
            "wsgi.input": io.BytesIO(payload),
            "wsgi.errors": io.StringIO(),
            "wsgi.version": (1, 0),
            "wsgi.multithread": False,
            "wsgi.multiprocess": False,
            "wsgi.run_once": False,
            "wsgi.url_scheme": "http",
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "8080",
        }
        res = self.app(environ, start_response)
        self.assertTrue(status_line and status_line[0].startswith("200"))
        self.api.unban_symbol.assert_called_once_with("AIOK")
        if hasattr(res, "close"):
            res.close()

    def test_toggle_filter_banned_route(self):
        import json
        self.api.toggle_filter_banned.return_value = {"ok": True, "filter_banned": True}
        payload = json.dumps({"enabled": True}).encode("utf-8")
        status_line = []
        headers_list = []

        def start_response(status, headers, exc_info=None):
            status_line.append(status)
            headers_list.extend(headers)

        environ = {
            "REQUEST_METHOD": "POST",
            "PATH_INFO": "/api/toggle_filter_banned",
            "CONTENT_TYPE": "application/json",
            "CONTENT_LENGTH": str(len(payload)),
            "wsgi.input": io.BytesIO(payload),
            "wsgi.errors": io.StringIO(),
            "wsgi.version": (1, 0),
            "wsgi.multithread": False,
            "wsgi.multiprocess": False,
            "wsgi.run_once": False,
            "wsgi.url_scheme": "http",
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "8080",
        }
        res = self.app(environ, start_response)
        self.assertTrue(status_line and status_line[0].startswith("200"))
        self.api.toggle_filter_banned.assert_called_once_with(True)
        if hasattr(res, "close"):
            res.close()


if __name__ == "__main__":
    unittest.main()

