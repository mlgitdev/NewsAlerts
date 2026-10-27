"""Unit tests for BamSEC filings parser, service, and API routes."""
from __future__ import annotations

import io
import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.bamsec import BamSECService, form_group
from app.server import make_app


SAMPLE_BAMSEC_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>AI OKTO CORP. – Filings and Transcripts – BamSEC</title>
</head>
<body>
    <h1 class="company-name">AI OKTO CORP.</h1>
    <div class="content">
        <h2>Prospectuses and Registrations <small class="pull-right"></small></h2>
        <div class="list-group default-results filings">
            <a data-filing-id="1" class="list-group-item" href="/filing/114036126040189?cik=2095591">
                <span class="label-left" title="F-3">F-3</span>
                <div class="label-center">Shelf registration</div>
                <div class="label-right">10/20/26</div>
            </a>
            <a data-filing-id="2" class="list-group-item" href="/filing/114036126032987?cik=2095591">
                <span class="label-left" title="DRS/A">DRS/A</span>
                <div class="label-center">Draft registration statement &ndash; amended</div>
                <div class="label-right">08/14/26</div>
            </a>
        </div>

        <h2>Ownership <small class="pull-right"></small></h2>
        <div class="list-group default-results filings">
            <a data-filing-id="3" class="list-group-item" href="/filing/114036126040105?cik=2095591">
                <span class="label-left" title="3">3</span>
                <div class="label-center">Oikonomopoulos Konstantinos</div>
                <div class="label-right">10/19/26</div>
            </a>
            <a data-filing-id="4" class="list-group-item" href="/filing/95015726001107?cik=2095591">
                <span class="label-left" title="SC 13D">SC 13D</span>
                <div class="label-center">Pani Corp.</div>
                <div class="label-right">10/16/26</div>
            </a>
        </div>

        <h2>News <small class="pull-right"></small></h2>
        <div class="list-group default-results filings">
            <a data-filing-id="5" class="list-group-item" href="/filing/114036126040608?cik=2095591">
                <span class="label-left" title="6-K">6-K</span>
                <div class="label-center">Declares Special Dividend of $3.50 Per Share</div>
                <div class="label-right">10/23/26</div>
            </a>
        </div>

        <h2>Financials </h2>
        <div class="empty-results-message">No filings in this category.</div>
    </div>
</body>
</html>
"""


class TestBamSECFormGroup(unittest.TestCase):
    def test_news_forms(self):
        self.assertEqual(form_group("8-K"), "news")
        self.assertEqual(form_group("6-K"), "news")
        self.assertEqual(form_group("8-K/A"), "news")

    def test_offering_forms(self):
        self.assertEqual(form_group("S-1"), "offering")
        self.assertEqual(form_group("S-3"), "offering")
        self.assertEqual(form_group("F-3"), "offering")
        self.assertEqual(form_group("424B5"), "offering")
        self.assertEqual(form_group("DRS"), "offering")
        self.assertEqual(form_group("RW"), "offering")

    def test_ownership_forms(self):
        self.assertEqual(form_group("3"), "ownership")
        self.assertEqual(form_group("4"), "ownership")
        self.assertEqual(form_group("SC 13D"), "ownership")
        self.assertEqual(form_group("SC 13G"), "ownership")

    def test_financial_forms(self):
        self.assertEqual(form_group("10-K"), "financial")
        self.assertEqual(form_group("10-Q"), "financial")
        self.assertEqual(form_group("20-F"), "financial")

    def test_other_forms(self):
        self.assertEqual(form_group("CERT"), "other")
        self.assertEqual(form_group("DEF 14A"), "other")


class TestBamSECService(unittest.TestCase):
    def setUp(self):
        self.service = BamSECService(ttl=60.0)

    def test_parse_html(self):
        parsed = BamSECService.parse_html("AIOK", SAMPLE_BAMSEC_HTML, "https://www.bamsec.com/companies/2095591/ai-okto-corp")
        self.assertEqual(parsed["ticker"], "AIOK")
        self.assertEqual(parsed["company"], "AI OKTO CORP.")
        self.assertEqual(parsed["total"], 5)
        self.assertIn("Prospectuses and Registrations", parsed["categories"])
        self.assertIn("Ownership", parsed["categories"])
        self.assertIn("News", parsed["categories"])

        # Check News item
        news_items = parsed["categories"]["News"]
        self.assertEqual(len(news_items), 1)
        self.assertEqual(news_items[0]["form"], "6-K")
        self.assertEqual(news_items[0]["group"], "news")
        self.assertEqual(news_items[0]["title"], "Declares Special Dividend of $3.50 Per Share")
        self.assertEqual(news_items[0]["date"], "10/23/26")
        self.assertEqual(news_items[0]["url"], "https://www.bamsec.com/filing/114036126040608?cik=2095591")

        # Check Prospectus item
        prosp_items = parsed["categories"]["Prospectuses and Registrations"]
        self.assertEqual(len(prosp_items), 2)
        self.assertEqual(prosp_items[0]["form"], "F-3")
        self.assertEqual(prosp_items[0]["group"], "offering")

        # Check Ownership item
        own_items = parsed["categories"]["Ownership"]
        self.assertEqual(len(own_items), 2)
        self.assertEqual(own_items[1]["form"], "SC 13D")
        self.assertEqual(own_items[1]["group"], "ownership")

    def test_parse_html_not_found(self):
        html_empty = "<html><body><h1>No search results</h1></body></html>"
        parsed = BamSECService.parse_html("UNKNOWN", html_empty, "https://www.bamsec.com/search?q=UNKNOWN")
        self.assertEqual(parsed["total"], 0)
        self.assertIn("error", parsed)

    @patch("requests.get")
    def test_get_filings_caching(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = SAMPLE_BAMSEC_HTML
        mock_resp.url = "https://www.bamsec.com/companies/2095591/ai-okto-corp"
        mock_get.return_value = mock_resp

        # First call fetches via network
        res1 = self.service.get_filings("AIOK")
        self.assertEqual(res1["total"], 5)
        self.assertEqual(mock_get.call_count, 1)

        # Second call returns cached result without network request
        res2 = self.service.get_filings("AIOK")
        self.assertEqual(res2["total"], 5)
        self.assertEqual(mock_get.call_count, 1)

        # Force refresh bypasses cache
        res3 = self.service.get_filings("AIOK", force=True)
        self.assertEqual(res3["total"], 5)
        self.assertEqual(mock_get.call_count, 2)


class TestBamSECServerRoute(unittest.TestCase):
    def setUp(self):
        self.web_dir = Path(__file__).resolve().parent.parent / "web"
        self.api = MagicMock()
        self.api.get_bamsec.return_value = {
            "ticker": "AIOK",
            "company": "AI OKTO CORP.",
            "bamsec_url": "https://www.bamsec.com/companies/2095591/ai-okto-corp",
            "categories": {},
            "all_filings": [],
            "total": 0,
        }
        self.app = make_app(self.api, self.web_dir)

    def test_api_bamsec_route_exists(self):
        routes = [r.rule for r in self.app.routes]
        self.assertIn("/api/bamsec", routes)

    def test_api_bamsec_calls_api(self):
        status_line = []
        headers_list = []

        def start_response(status, headers, exc_info=None):
            status_line.append(status)
            headers_list.extend(headers)

        environ = {
            "REQUEST_METHOD": "GET",
            "PATH_INFO": "/api/bamsec",
            "QUERY_STRING": "ticker=AIOK&force=1",
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
        data = json.loads(b"".join(res).decode("utf-8"))
        self.assertEqual(data["ticker"], "AIOK")
        self.api.get_bamsec.assert_called_with("AIOK", force=True)


class TestBamSECApiOptOut(unittest.TestCase):
    def test_default_config_opt_in(self):
        from app.config import DEFAULT_CONFIG
        self.assertIn("news", DEFAULT_CONFIG)
        self.assertTrue(DEFAULT_CONFIG["news"].get("bamsec_enabled", False))

    def test_api_get_bamsec_when_enabled(self):
        from app.api import Api
        mock_app = MagicMock()
        mock_app.config = {"news": {"bamsec_enabled": True}}
        mock_app.bamsec = MagicMock()
        mock_app.bamsec.get_filings.return_value = {
            "ticker": "AIOK",
            "total": 3,
            "all_filings": [{"form": "8-K"}]
        }
        api = Api(mock_app)
        res = api.get_bamsec("AIOK", force=True)
        self.assertEqual(res["ticker"], "AIOK")
        self.assertEqual(res["total"], 3)
        self.assertNotIn("disabled", res)
        mock_app.bamsec.get_filings.assert_called_once_with("AIOK", force=True)

    def test_api_get_bamsec_when_disabled_opt_out(self):
        from app.api import Api
        mock_app = MagicMock()
        mock_app.config = {"news": {"bamsec_enabled": False}}
        mock_app.bamsec = MagicMock()
        api = Api(mock_app)
        res = api.get_bamsec("AIOK", force=True)
        self.assertEqual(res["ticker"], "AIOK")
        self.assertEqual(res["total"], 0)
        self.assertTrue(res.get("disabled"))
        mock_app.bamsec.get_filings.assert_not_called()


if __name__ == "__main__":
    unittest.main()
