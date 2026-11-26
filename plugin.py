from __future__ import annotations

import asyncio
import html
import json
import re
import time
from types import SimpleNamespace
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from maibot_sdk import API, MaiBotPlugin, Tool

from .config_models import Config


def fetch_url(url, timeout):
    request = Request(url, headers={"User-Agent": "zeyr-better-search/0.1"})
    with urlopen(request, timeout=timeout) as response:
        return (
            response.read(),
            response.headers.get_content_charset() or "utf-8",
            response.headers.get_content_type(),
        )


def clean_text(raw):
    text = re.sub(r"(?is)<(script|style|nav|footer|header|aside|noscript).*?>.*?</\1>", " ", raw)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


class Plugin(MaiBotPlugin):
    config_model = Config

    def __init__(self):
        super().__init__()
        self.cache = {}

    async def on_load(self):
        self.ctx.logger.info("更好的搜索已加载")

    async def on_unload(self):
        self.cache.clear()

    async def on_config_update(self, scope, config_data, version):
        self.cache.clear()

    def sources(self):
        configured = [source for source in self.config.sources if source.enabled and source.endpoint]
        return configured or [SimpleNamespace(name="duckduckgo", kind="duckduckgo", endpoint="", domains=[])]

    def parse_html_results(self, body):
        text = body.decode("utf-8", "ignore")
        rows = []
        for match in re.finditer(
            r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', text, re.I | re.S
        ):
            url, title = match.groups()
            rows.append(
                {"title": clean_text(title), "url": html.unescape(url), "snippet": "", "source": "duckduckgo"}
            )
        return rows

    def parse_json_results(self, body, source):
        payload = json.loads(body.decode("utf-8"))
        values = payload.get("results", payload if isinstance(payload, list) else [])
        return [
            {
                "title": str(row.get("title", "")),
                "url": str(row.get("url", "")),
                "snippet": str(row.get("snippet", row.get("description", ""))),
                "source": source.name,
            }
            for row in values
            if row.get("url")
        ]

    async def search(self, query, scope="web"):
        if not self.config.enabled or not query.strip():
            return {"query": query, "scope": scope, "results": [], "degraded": False}
        key = (query.strip(), scope)
        cached = self.cache.get(key)
        if cached and time.monotonic() - cached["at"] < self.config.cache_minutes * 60:
            return cached["value"]
        errors, rows = [], []
        for source in self.sources():
            try:
                url = (
                    source.endpoint.format(query=quote(query), scope=quote(scope))
                    if source.endpoint
                    else f"https://html.duckduckgo.com/html/?q={quote(query)}"
                )
                body, _, _ = await asyncio.to_thread(fetch_url, url, self.config.timeout_seconds)
                rows = (
                    self.parse_html_results(body)
                    if source.kind == "duckduckgo"
                    else self.parse_json_results(body, source)
                )
                if rows:
                    break
            except Exception as exc:
                errors.append(f"{source.name}: {type(exc).__name__}")
        for row in rows:
            host = urlparse(row["url"]).netloc.casefold()
            row["preferred"] = any(domain.casefold() in host for domain in self.config.preferred_domains)
        rows.sort(key=lambda row: not row.get("preferred", False))
        value = {
            "query": query,
            "scope": scope,
            "results": rows[: self.config.max_results],
            "degraded": bool(errors),
            "errors": errors,
        }
        self.cache[key] = {"at": time.monotonic(), "value": value}
        return value

    async def fetch(self, url):
        if not re.match(r"^https?://", url):
            return {"url": url, "success": False, "error": "仅支持 http/https"}
        try:
            body, charset, content_type = await asyncio.to_thread(fetch_url, url, self.config.timeout_seconds)
            text = clean_text(body.decode(charset, "replace"))[: self.config.max_body_chars]
            return {
                "url": url,
                "success": True,
                "content_type": content_type,
                "text": text,
                "truncated": len(text) >= self.config.max_body_chars,
            }
        except Exception as exc:
            return {"url": url, "success": False, "error": f"{type(exc).__name__}: {exc}"}

    @Tool(
        "smart_search",
        description="使用配置的搜索源查询网页，失败时自动降级。",
        parameters={"query": {"type": "string"}, "scope": {"type": "string", "default": "web"}},
        visibility="visible",
    )
    async def tool_search(self, query, scope="web", **kwargs):
        return await self.search(query, scope)

    @Tool(
        "smart_fetch",
        description="抓取网页并去除脚本、导航和样式噪声。",
        parameters={"url": {"type": "string"}},
        visibility="visible",
    )
    async def tool_fetch(self, url, **kwargs):
        return await self.fetch(url)

    @API("query", public=True, version="1")
    async def api_query(self, q, scope="web", **kwargs):
        return {"schema_version": 1, "success": True, "data": await self.search(q, scope), "error": ""}

    @API("fetch", public=True, version="1")
    async def api_fetch(self, url, **kwargs):
        value = await self.fetch(url)
        return {
            "schema_version": 1,
            "success": bool(value.get("success")),
            "data": value,
            "error": value.get("error", ""),
        }


def create_plugin():
    return Plugin()
