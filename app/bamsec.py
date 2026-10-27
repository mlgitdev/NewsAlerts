"""BamSEC SEC filings provider, parser, and caching service."""
from __future__ import annotations

import html
import logging
import re
import threading
import time
from typing import Any

import requests

log = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# Categorization for form badges
OFFERING_FORMS = {"S-1", "S-1/A", "S-3", "S-3/A", "F-1", "F-1/A", "F-3", "F-3/A",
                  "424B1", "424B2", "424B3", "424B4", "424B5", "424B7", "424B8",
                  "DRS", "DRS/A", "RW", "POS AM", "POS EX", "20FR12B"}
NEWS_FORMS = {"8-K", "8-K/A", "6-K", "6-K/A"}
OWNERSHIP_FORMS = {"3", "4", "5", "SC 13D", "SC 13D/A", "SC 13G", "SC 13G/A", "144"}
FINANCIAL_FORMS = {"10-K", "10-K/A", "10-Q", "10-Q/A", "20-F", "20-F/A", "40-F"}


def form_group(form: str) -> str:
    """Return semantic group for a SEC filing form."""
    norm = form.strip().upper()
    if norm in NEWS_FORMS:
        return "news"
    if norm in OFFERING_FORMS:
        return "offering"
    if norm in OWNERSHIP_FORMS:
        return "ownership"
    if norm in FINANCIAL_FORMS:
        return "financial"
    return "other"


class BamSECService:
    """Fetches, parses, and caches SEC filings directly from BamSEC."""

    def __init__(self, ttl: float = 120.0, timeout: float = 7.0) -> None:
        self.ttl = ttl
        self.timeout = timeout
        self._cache: dict[str, tuple[float, dict[str, Any]]] = {}
        self._lock = threading.Lock()

    def get_filings(self, ticker: str, force: bool = False) -> dict[str, Any]:
        """Fetch categorized filings for ticker. Returns cached result if within TTL."""
        sym = ticker.split(":")[-1].strip().upper()
        if not sym:
            return {
                "ticker": "",
                "company": "",
                "bamsec_url": "",
                "categories": {},
                "all_filings": [],
                "total": 0,
                "error": "Empty symbol",
            }

        now = time.time()
        with self._lock:
            hit = self._cache.get(sym)
            if hit and not force and (now - hit[0] < self.ttl):
                return hit[1]

        url = f"https://www.bamsec.com/search?q={sym}"
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        try:
            r = requests.get(url, headers=headers, timeout=self.timeout, allow_redirects=True)
            if r.status_code != 200:
                res = {
                    "ticker": sym,
                    "company": sym,
                    "bamsec_url": r.url or url,
                    "categories": {},
                    "all_filings": [],
                    "total": 0,
                    "error": f"BamSEC returned HTTP {r.status_code}",
                }
                with self._lock:
                    self._cache[sym] = (now, res)
                return res

            parsed = self.parse_html(sym, r.text, r.url)
            with self._lock:
                self._cache[sym] = (now, parsed)
            return parsed

        except Exception as e:
            log.warning("BamSEC request failed for %s: %s", sym, e)
            return {
                "ticker": sym,
                "company": sym,
                "bamsec_url": url,
                "categories": {},
                "all_filings": [],
                "total": 0,
                "error": str(e),
            }

    @staticmethod
    def parse_html(sym: str, raw_html: str, final_url: str) -> dict[str, Any]:
        """Parse BamSEC HTML into structured categorized filings."""
        # Check if BamSEC redirected to entity search or no results
        if "/companies/" not in final_url and "filing" not in raw_html:
            return {
                "ticker": sym,
                "company": sym,
                "bamsec_url": final_url,
                "categories": {},
                "all_filings": [],
                "total": 0,
                "error": "No company page found on BamSEC",
            }

        # Parse company name
        comp_match = re.search(r'<h1[^>]*class="[^"]*company-name[^"]*"[^>]*>([\s\S]*?)</h1>', raw_html)
        if comp_match:
            comp_name = re.sub(r'<[^>]+>', '', comp_match.group(1)).strip()
        else:
            title_match = re.search(r'<title>([\s\S]*?)</title>', raw_html)
            if title_match:
                raw_t = title_match.group(1)
                # e.g. "AI OKTO CORP. – Filings and Transcripts – BamSEC"
                clean_t = html.unescape(raw_t).replace("&ndash;", "-").split("–")[0].split("-")[0].strip()
                comp_name = re.sub(r'\s+', ' ', clean_t)
            else:
                comp_name = sym

        # Regex to match individual filing anchor items in BamSEC
        filing_pattern = re.compile(
            r'<a\s+[^>]*href="(/filing/[^"]+)"[^>]*>'
            r'[\s\S]*?<span class="label-left"[^>]*>\s*([^<]+?)\s*</span>'
            r'[\s\S]*?<div class="label-center[^"]*">\s*([\s\S]*?)\s*</div>'
            r'[\s\S]*?<div class="label-right">\s*([^<]+?)\s*</div>',
            re.DOTALL
        )

        # Split by category headers: <h2>Category Name ...</h2>
        # Typically: Financials, Prospectuses and Registrations, Ownership, News, Proxies, Other
        cat_splits = re.split(r'<h2[^>]*>\s*([A-Za-z0-9 &/\-]+?)\s*(?:<small[\s\S]*?)?</h2>', raw_html)

        categories: dict[str, list[dict[str, Any]]] = {}
        all_filings: list[dict[str, Any]] = []

        if len(cat_splits) > 1:
            for i in range(1, len(cat_splits), 2):
                cat_name = cat_splits[i].strip()
                cat_html = cat_splits[i + 1]
                cat_items = []
                for href, form_raw, title_raw, date_raw in filing_pattern.findall(cat_html):
                    form = form_raw.strip()
                    # Clean title: strip inner HTML like <span class="float-right"> ended 06/27/26 </span>
                    clean_t = re.sub(r'<[^>]+>', ' ', title_raw)
                    clean_t = re.sub(r'\s+', ' ', html.unescape(clean_t)).strip()
                    if not clean_t or set(clean_t).issubset({'#', ' '}):
                        clean_t = f"{form} Filing"

                    link = f"https://www.bamsec.com{href.strip()}"
                    date = date_raw.strip()
                    group = form_group(form)

                    item = {
                        "category": cat_name,
                        "form": form,
                        "group": group,
                        "title": clean_t,
                        "date": date,
                        "url": link,
                    }
                    cat_items.append(item)
                    all_filings.append(item)
                categories[cat_name] = cat_items
        else:
            # Fallback when sections are not split by H2
            for href, form_raw, title_raw, date_raw in filing_pattern.findall(raw_html):
                form = form_raw.strip()
                clean_t = re.sub(r'<[^>]+>', ' ', title_raw)
                clean_t = re.sub(r'\s+', ' ', html.unescape(clean_t)).strip()
                if not clean_t or set(clean_t).issubset({'#', ' '}):
                    clean_t = f"{form} Filing"
                link = f"https://www.bamsec.com{href.strip()}"
                date = date_raw.strip()
                group = form_group(form)
                item = {
                    "category": "Filings",
                    "form": form,
                    "group": group,
                    "title": clean_t,
                    "date": date,
                    "url": link,
                }
                all_filings.append(item)
            categories["Filings"] = all_filings

        return {
            "ticker": sym,
            "company": comp_name,
            "bamsec_url": final_url,
            "categories": categories,
            "all_filings": all_filings,
            "total": len(all_filings),
            "timestamp": time.time(),
        }
