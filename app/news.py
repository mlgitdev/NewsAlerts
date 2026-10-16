"""News providers, caching and story rendering."""
from __future__ import annotations

import html
import threading
import time
from abc import ABC, abstractmethod

from .tv_client import TVClient

TV_BASE = "https://www.tradingview.com"


class NewsProvider(ABC):
    """Interface so an official Benzinga API provider can be plugged in later."""

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
            })
        out.sort(key=lambda x: x["published"], reverse=True)
        return out

    def story(self, story_id: str) -> dict:
        d = self.c.story(story_id)
        body = ast_to_html(d.get("astDescription")) if d.get("astDescription") else ""
        if not body and d.get("shortDescription"):
            body = f"<p>{html.escape(d['shortDescription'])}</p>"
        return {"html": body, "source_url": d.get("sourceUrl", "")}


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
