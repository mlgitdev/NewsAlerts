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


if __name__ == "__main__":
    unittest.main()
