"""Local HTTP API and static file server for NewsAlerts UI."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from socketserver import ThreadingMixIn
import threading
from wsgiref.simple_server import WSGIServer, make_server

from bottle import Bottle, request, response, static_file

log = logging.getLogger(__name__)


class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True
    allow_reuse_address = False


def make_app(api, web_dir: Path) -> Bottle:
    app = Bottle()

    def json_resp(data):
        response.content_type = "application/json; charset=utf-8"
        return json.dumps(data)

    @app.hook("after_request")
    def no_cache():
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

    # ------------------------------------------------------------- Static Files
    @app.route("/")
    @app.route("/index.html")
    def index():
        return static_file("index.html", root=str(web_dir))

    @app.route("/tape.html")
    def tape():
        return static_file("tape.html", root=str(web_dir))

    @app.route("/css/<filepath:path>")
    def css(filepath):
        return static_file(filepath, root=str(web_dir / "css"))

    @app.route("/js/<filepath:path>")
    def js(filepath):
        return static_file(filepath, root=str(web_dir / "js"))

    @app.route("/img/<filepath:path>")
    def img(filepath):
        if (web_dir / "img" / filepath).exists():
            return static_file(filepath, root=str(web_dir / "img"))
        if (web_dir.parent / "assets" / filepath).exists():
            return static_file(filepath, root=str(web_dir.parent / "assets"))
        return static_file(filepath, root=str(web_dir / "img"))

    @app.route("/assets/<filepath:path>")
    def assets(filepath):
        if (web_dir.parent / "assets" / filepath).exists():
            return static_file(filepath, root=str(web_dir.parent / "assets"))
        return static_file(filepath, root=str(web_dir / "img"))

    @app.route("/favicon.ico")
    def favicon():
        return static_file("favicon.ico", root=str(web_dir))

    @app.route("/icon.png")
    def icon():
        return static_file("icon.png", root=str(web_dir))

    @app.route("/<filename:re:[a-zA-Z0-9_\\-\\.]+\\.(png|ico|jpg|jpeg|svg|webp)>")
    def static_image(filename):
        if (web_dir / filename).exists():
            return static_file(filename, root=str(web_dir))
        if (web_dir / "img" / filename).exists():
            return static_file(filename, root=str(web_dir / "img"))
        if (web_dir.parent / "assets" / filename).exists():
            return static_file(filename, root=str(web_dir.parent / "assets"))
        return static_file(filename, root=str(web_dir))

    # ---------------------------------------------------------------- API Routes
    @app.route("/api/state", method=["GET"])
    def get_state():
        try:
            return json_resp(api.get_state())
        except Exception as e:
            log.exception("Error in /api/state: %s", e)
            return json_resp({"error": str(e)})

    @app.route("/api/events", method=["GET"])
    def get_events():
        try:
            after = request.query.get("after", 0)
            try:
                after_id = int(after)
            except ValueError:
                after_id = 0
            return json_resp(api.poll_events(after_id))
        except Exception as e:
            log.exception("Error in /api/events: %s", e)
            return json_resp([])

    @app.route("/api/config", method=["POST"])
    def save_config():
        try:
            data = request.json or {}
            ok = api.save_config(data)
            return json_resp({"ok": ok})
        except Exception as e:
            log.exception("Error in /api/config: %s", e)
            return json_resp({"ok": False, "error": str(e)})

    @app.route("/api/test_telegram", method=["POST"])
    def test_telegram():
        try:
            data = request.json if request.json and isinstance(request.json, dict) else {}
            bot_token = data.get("bot_token", "")
            chat_id = data.get("chat_id", "")
            return json_resp(api.send_telegram_test(bot_token=bot_token, chat_id=chat_id))
        except Exception as e:
            log.exception("Error in /api/test_telegram: %s", e)
            return json_resp({"ok": False, "message": str(e)})

    @app.route("/api/test_alpaca", method=["POST"])
    def test_alpaca():
        try:
            data = request.json if request.json and isinstance(request.json, dict) else {}
            key_id = data.get("key_id", "")
            secret_key = data.get("secret_key", "")
            return json_resp(api.test_alpaca(key_id=key_id, secret_key=secret_key))
        except Exception as e:
            log.exception("Error in /api/test_alpaca: %s", e)
            return json_resp({"ok": False, "message": str(e)})

    @app.route("/api/tv_watchlists", method=["GET"])
    def get_tv_watchlists():
        try:
            return json_resp(api.get_watchlists())
        except Exception as e:
            log.exception("Error in /api/tv_watchlists: %s", e)
            return json_resp({"ok": False, "message": str(e), "watchlists": []})

    @app.route("/api/tv_watchlist/select", method=["POST"])
    def select_tv_watchlist():
        try:
            data = request.json if request.json and isinstance(request.json, dict) else {}
            list_id = data.get("list_id", "")
            title = data.get("title", "")
            return json_resp(api.select_watchlist(list_id=list_id, title=title))
        except Exception as e:
            log.exception("Error in /api/tv_watchlist/select: %s", e)
            return json_resp({"ok": False, "message": str(e)})

    @app.route("/api/tv_watchlist/add", method=["POST"])
    def add_to_tv_watchlist():
        try:
            data = request.json if request.json and isinstance(request.json, dict) else {}
            list_id = data.get("list_id", "")
            symbol = data.get("symbol", "")
            return json_resp(api.add_to_watchlist(list_id=list_id, symbol=symbol))
        except Exception as e:
            log.exception("Error in /api/tv_watchlist/add: %s", e)
            return json_resp({"ok": False, "message": str(e)})

    @app.route("/api/set_volume", method=["POST"])
    def set_volume():
        try:
            data = request.json or {}
            vol = int(data.get("volume", 80))
            return json_resp(api.set_volume(vol))
        except Exception as e:
            log.exception("Error in /api/set_volume: %s", e)
            return json_resp({"ok": False, "error": str(e)})

    @app.route("/api/set_focused", method=["POST"])
    def set_focused():
        try:
            data = request.json or {}
            focused = bool(data.get("focused", False))
            api.set_focused(focused)
            return json_resp({"ok": True})
        except Exception as e:
            log.exception("Error in /api/set_focused: %s", e)
            return json_resp({"ok": False})

    @app.route("/api/news", method=["GET"])
    def get_news():
        ticker = request.query.get("ticker", "")
        force = request.query.get("force", "0") in ("1", "true", "True")
        try:
            return json_resp(api.get_news(ticker, force=force))
        except Exception as e:
            log.exception("Error in /api/news: %s", e)
            return json_resp({"ticker": ticker, "items": [], "total": 0, "error": str(e)})

    @app.route("/api/story", method=["GET"])
    def get_story():
        story_id = request.query.get("id", "")
        try:
            return json_resp(api.get_story(story_id))
        except Exception as e:
            log.exception("Error in /api/story: %s", e)
            return json_resp({"id": story_id, "title": "", "body": f"Error: {e}"})

    @app.route("/api/quote", method=["GET"])
    def get_quote():
        ticker = request.query.get("ticker", "")
        try:
            return json_resp(api.get_quote(ticker))
        except Exception as e:
            log.exception("Error in /api/quote: %s", e)
            return json_resp(None)

    @app.route("/api/play_sound", method=["POST"])
    def play_sound():
        try:
            data = request.json or {}
            path = data.get("path", "")
            return json_resp({"ok": api.play_sound(path)})
        except Exception as e:
            log.exception("Error in /api/play_sound: %s", e)
            return json_resp({"ok": False})

    @app.route("/api/play_alert", method=["POST"])
    def play_alert():
        try:
            data = request.json or {}
            kind = data.get("kind", "")
            return json_resp({"ok": api.play_alert(kind)})
        except Exception as e:
            log.exception("Error in /api/play_alert: %s", e)
            return json_resp({"ok": False})

    @app.route("/api/open_url", method=["POST"])
    def open_url():
        try:
            data = request.json or {}
            url = data.get("url", "")
            return json_resp({"ok": api.open_url(url)})
        except Exception as e:
            log.exception("Error in /api/open_url: %s", e)
            return json_resp({"ok": False})

    @app.route("/api/open_chart", method=["POST"])
    def open_chart():
        try:
            data = request.json or {}
            ticker = data.get("ticker", "")
            return json_resp({"ok": api.open_chart(ticker)})
        except Exception as e:
            log.exception("Error in /api/open_chart: %s", e)
            return json_resp({"ok": False})

    @app.route("/api/pop_tape", method=["POST"])
    def pop_tape():
        try:
            return json_resp({"ok": api.pop_tape()})
        except Exception as e:
            log.exception("Error in /api/pop_tape: %s", e)
            return json_resp({"ok": False})

    @app.route("/api/refresh", method=["POST"])
    def refresh():
        try:
            return json_resp({"ok": api.refresh()})
        except Exception as e:
            log.exception("Error in /api/refresh: %s", e)
            return json_resp({"ok": False})

    @app.route("/api/clear_tape", method=["POST"])
    def clear_tape():
        try:
            return json_resp({"ok": api.clear_tape()})
        except Exception as e:
            log.exception("Error in /api/clear_tape: %s", e)
            return json_resp({"ok": False})

    @app.route("/api/select_symbol", method=["POST"])
    def select_symbol():
        try:
            data = request.json or {}
            ticker = data.get("ticker", "")
            return json_resp({"ok": api.select_symbol(ticker)})
        except Exception as e:
            log.exception("Error in /api/select_symbol: %s", e)
            return json_resp({"ok": False})

    @app.route("/api/set_on_top", method=["POST"])
    def set_on_top():
        try:
            data = request.json or {}
            on = bool(data.get("on", False))
            return json_resp({"ok": api.set_on_top(on)})
        except Exception as e:
            log.exception("Error in /api/set_on_top: %s", e)
            return json_resp({"ok": False})

    @app.route("/api/ban_symbol", method=["POST"])
    def ban_symbol():
        try:
            data = request.json or {}
            symbol = data.get("symbol", "")
            return json_resp(api.ban_symbol(symbol))
        except Exception as e:
            log.exception("Error in /api/ban_symbol: %s", e)
            return json_resp({"ok": False, "error": str(e)})

    @app.route("/api/unban_symbol", method=["POST"])
    def unban_symbol():
        try:
            data = request.json or {}
            symbol = data.get("symbol", "")
            return json_resp(api.unban_symbol(symbol))
        except Exception as e:
            log.exception("Error in /api/unban_symbol: %s", e)
            return json_resp({"ok": False, "error": str(e)})

    @app.route("/api/toggle_filter_banned", method=["POST"])
    def toggle_filter_banned():
        try:
            data = request.json or {}
            enabled = data.get("enabled", None)
            return json_resp(api.toggle_filter_banned(enabled))
        except Exception as e:
            log.exception("Error in /api/toggle_filter_banned: %s", e)
            return json_resp({"ok": False, "error": str(e)})

    return app



def start_server(api, web_dir: Path, port: int = 49281) -> tuple[str, ThreadingWSGIServer]:
    """Finds an open port starting from `port` and starts ThreadingWSGIServer in a daemon thread."""
    app = make_app(api, web_dir)
    cur_port = port
    server = None
    for attempt in range(25):
        try:
            server = make_server("127.0.0.1", cur_port, app, server_class=ThreadingWSGIServer)
            break
        except OSError:
            cur_port += 1

    if server is None:
        raise RuntimeError("Could not find an available port for local server")

    url = f"http://127.0.0.1:{cur_port}"
    th = threading.Thread(target=server.serve_forever, daemon=True, name="HttpServerThread")
    th.start()
    log.info("Local HTTP server running at %s", url)
    return url, server
