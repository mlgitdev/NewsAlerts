"""News providers, caching and story rendering."""
from __future__ import annotations

from datetime import datetime
import html
import logging
import threading
import time
from abc import ABC, abstractmethod

import requests

from .tv_client import TVClient

log = logging.getLogger(__name__)

TV_BASE = "https://www.tradingview.com"


class NewsProvider(ABC):
    """Interface for news providers."""

    @abstractmethod
    def headlines(self, ticker: str) -> list[dict]: ...

    @abstractmethod
    def story(self, story_id: str) -> dict: ...


class TradingViewNews(NewsProvider):
    def __init__(self, client: TVClient) -> None:
        self.c = client

    def headlines(self, ticker: str) -> list[dict]:
        out = []
        for it in self.c.headlines(ticker):
            link = it.get("link") or (TV_BASE + it["storyPath"] if it.get("storyPath") else "")
            out.append({
                "id": it.get("id"),
                "title": it.get("title", ""),
                "provider": it.get("provider", ""),
                "source": it.get("source", ""),
                "published": it.get("published", 0),
                "link": link,
                "symbols": [s.get("symbol") for s in it.get("relatedSymbols", [])][:6],
                "summary": "",
            })
        out.sort(key=lambda x: x["published"], reverse=True)
        return out

    def story(self, story_id: str) -> dict:
        d = self.c.story(story_id)
        body = ast_to_html(d.get("astDescription")) if d.get("astDescription") else ""
        if not body and d.get("shortDescription"):
            body = f"<p>{html.escape(d['shortDescription'])}</p>"
        return {"html": body, "source_url": d.get("sourceUrl", "")}


class AlpacaNews(NewsProvider):
    """Fetches real-time Benzinga headlines and stories via Alpaca News API."""

    def __init__(self, key_id: str = "", secret_key: str = "") -> None:
        self.key_id = key_id.strip()
        self.secret_key = secret_key.strip()
        self._stories: dict[str, dict] = {}
        self._lock = threading.Lock()

    def update_credentials(self, key_id: str, secret_key: str) -> None:
        with self._lock:
            self.key_id = key_id.strip()
            self.secret_key = secret_key.strip()

    def headlines(self, ticker: str) -> list[dict]:
        with self._lock:
            kid = self.key_id
            sec = self.secret_key
        if not (kid and sec):
            return []
        sym = ticker.split(":")[-1].upper().strip()
        url = f"https://data.alpaca.markets/v1beta1/news?symbols={sym}&limit=25"
        headers = {
            "APCA-API-KEY-ID": kid,
            "APCA-API-SECRET-KEY": sec,
        }
        try:
            r = requests.get(url, headers=headers, timeout=6)
            if r.status_code != 200:
                return []
            news = r.json().get("news", [])
            out = []
            for it in news:
                sid = f"alp_{it.get('id')}"
                created_str = it.get("created_at", "")
                try:
                    dt = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                    ts = dt.timestamp()
                except Exception:
                    ts = time.time()

                headline = it.get("headline", "")
                summary = it.get("summary", "")
                content = it.get("content", "")
                link = it.get("url", "")
                source = str(it.get("source", "benzinga")).lower()

                body_html = f"<h4>{html.escape(headline)}</h4>"
                if summary:
                    body_html += f"<p>{html.escape(summary)}</p>"
                if content and content != summary:
                    body_html += f"<div>{html.escape(content)}</div>"

                with self._lock:
                    self._stories[sid] = {"html": body_html, "source_url": link}

                out.append({
                    "id": sid,
                    "title": headline,
                    "provider": "benzinga" if "benzinga" in source else source,
                    "source": source,
                    "published": ts,
                    "link": link,
                    "symbols": it.get("symbols", [sym])[:6],
                    "summary": summary[:220] if summary else "",
                })
            out.sort(key=lambda x: x["published"], reverse=True)
            return out
        except Exception as e:
            log.warning("Alpaca news error for %s: %s", ticker, e)
            return []

    def story(self, story_id: str) -> dict:
        with self._lock:
            return self._stories.get(story_id, {"html": "", "source_url": ""})


class CombinedNews(NewsProvider):
    """Combines multiple news feeds (Alpaca Benzinga + TradingView), deduplicating by title."""

    def __init__(self, providers: list[NewsProvider]) -> None:
        self.providers = providers

    def headlines(self, ticker: str) -> list[dict]:
        combined = []
        seen_titles = set()
        for p in self.providers:
            try:
                items = p.headlines(ticker)
                for it in items:
                    norm_title = it.get("title", "").strip().lower()
                    if norm_title and norm_title in seen_titles:
                        continue
                    if norm_title:
                        seen_titles.add(norm_title)
                    combined.append(it)
            except Exception as e:
                log.warning("Error fetching headlines from %s: %s", p.__class__.__name__, e)
        combined.sort(key=lambda x: x["published"], reverse=True)
        return combined

    def story(self, story_id: str) -> dict:
        for p in self.providers:
            try:
                s = p.story(story_id)
                if s and (s.get("html") or s.get("source_url")):
                    return s
            except Exception:
                pass
        return {"html": "", "source_url": ""}


_TAGS = {"p": "p", "b": "b", "strong": "b", "i": "i", "em": "i", "ul": "ul", "ol": "ol",
         "li": "li", "h1": "h4", "h2": "h4", "h3": "h5", "h4": "h5", "table": "table",
         "tr": "tr", "td": "td", "th": "th", "tbody": "tbody", "thead": "thead",
         "blockquote": "blockquote", "br": "br"}


def ast_to_html(node) -> str:
    if node is None:
        return ""
    if isinstance(node, str):
        return html.escape(node)
    if isinstance(node, list):
        return "".join(ast_to_html(n) for n in node)
    t = node.get("type")
    params = node.get("params") or {}
    inner = ast_to_html(node.get("children", []))
    if t == "root":
        return inner
    if t == "url":
        url = html.escape(params.get("url", ""), quote=True)
        text = html.escape(params.get("linkText") or params.get("url", ""))
        return f'<a href="{url}" data-ext="1">{text}</a>'
    if t == "symbol":
        sym = html.escape(params.get("symbol", ""))
        return f'<span class="sym" data-sym="{sym}">{html.escape(params.get("text", sym))}</span>'
    if t == "image":
        return ""
    if t == "br":
        return "<br>"
    tag = _TAGS.get(t)
    return f"<{tag}>{inner}</{tag}>" if tag else inner


class NewsService:
    """Caches headlines per ticker (TTL) and answers 'has fresh news?' queries."""

    def __init__(self, provider: NewsProvider, ttl: float = 45.0) -> None:
        self.p = provider
        self.ttl = ttl
        self._cache: dict[str, tuple[float, list[dict]]] = {}
        self._stories: dict[str, dict] = {}
        self._lock = threading.Lock()

    def get(self, ticker: str, force: bool = False) -> list[dict]:
        with self._lock:
            hit = self._cache.get(ticker)
        if hit and not force and time.time() - hit[0] < self.ttl:
            return hit[1]
        items = self.p.headlines(ticker)
        with self._lock:
            self._cache[ticker] = (time.time(), items)
        return items

    def cached(self, ticker: str) -> list[dict] | None:
        with self._lock:
            hit = self._cache.get(ticker)
        return hit[1] if hit else None

    def story(self, story_id: str) -> dict:
        with self._lock:
            if story_id in self._stories:
                return self._stories[story_id]
        s = self.p.story(story_id)
        with self._lock:
            self._stories[story_id] = s
        return s

    @staticmethod
    def recent(items: list[dict], hours: float, benzinga_only: bool = False) -> list[dict]:
        cutoff = time.time() - hours * 3600
        return [i for i in items
                if i["published"] >= cutoff and (not benzinga_only or i["provider"] == "benzinga")]
