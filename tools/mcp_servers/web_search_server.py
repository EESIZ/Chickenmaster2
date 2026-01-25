#!/usr/bin/env python3
"""Web Search MCP 서버.

MCP stdio transport 위에서 동작하는, 가벼운(표준 라이브러리만 사용) 웹 검색 + 페이지 fetch 기능을 제공한다.

검색 백엔드:
- DuckDuckGo HTML endpoint (best-effort; 외부 서비스/마크업 변경에 따라 동작이 바뀔 수 있음)

Usage:
    uv run python -m tools.mcp_servers.web_search_server

MCP Tools:
    - web_search: 웹 검색 결과(title/url/snippet) 목록 반환
    - fetch_web_page: URL을 가져와 본문 텍스트(best-effort) 추출
    - search_and_fetch: 검색 후 상위 결과를 즉시 fetch/추출
"""

from __future__ import annotations

import asyncio
import html
import html.parser
import json
import re
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Optional

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import TextContent, Tool
except ImportError:
    print("Error: MCP SDK not installed. Run: uv sync", file=sys.stderr)
    raise


server = Server("web-search")


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    snippet: str


class _DuckDuckGoHTMLParser(html.parser.HTMLParser):
    """DuckDuckGo HTML 검색 결과를 파싱하는 최소 파서."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._results: list[SearchResult] = []
        self._current_title: Optional[str] = None
        self._current_url: Optional[str] = None
        self._current_snippet: Optional[str] = None

        self._in_result_title = False
        self._in_result_snippet = False

    @property
    def results(self) -> list[SearchResult]:
        return self._results

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        if tag != "a":
            return

        attr_map = {k: (v or "") for k, v in attrs}
        classes = set((attr_map.get("class") or "").split())
        href = (attr_map.get("href") or "").strip()

        if "result__a" in classes:
            self._in_result_title = True
            self._current_title = ""
            self._current_url = href
            return

        if "result__snippet" in classes:
            self._in_result_snippet = True
            self._current_snippet = ""

    def handle_endtag(self, tag: str) -> None:
        if tag != "a":
            return

        if self._in_result_title:
            self._in_result_title = False
            # Title anchor ended; wait for snippet before finalizing.
            return

        if self._in_result_snippet:
            self._in_result_snippet = False
            # Snippet ended; finalize a result if we have both title+url.
            if self._current_title and self._current_url:
                url = _normalize_ddg_redirect(self._current_url)
                snippet = (self._current_snippet or "").strip()
                self._results.append(
                    SearchResult(
                        title=self._current_title.strip(),
                        url=url,
                        snippet=snippet,
                    )
                )
            self._current_title = None
            self._current_url = None
            self._current_snippet = None

    def handle_data(self, data: str) -> None:
        if self._in_result_title and self._current_title is not None:
            self._current_title += data
        elif self._in_result_snippet and self._current_snippet is not None:
            self._current_snippet += data


class _HTMLToTextParser(html.parser.HTMLParser):
    """HTML을 plain text로 변환하는 간단 파서(기본 블록 태그 줄바꿈 처리)."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._chunks: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip_depth += 1
            return
        if tag in {"p", "br", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self._chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"}:
            if self._skip_depth > 0:
                self._skip_depth -= 1
            return
        if tag in {"p", "div", "li"}:
            self._chunks.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth > 0:
            return
        text = data.strip()
        if not text:
            return
        self._chunks.append(text + " ")

    def get_text(self) -> str:
        text = "".join(self._chunks)
        # Normalize whitespace while keeping newlines.
        text = re.sub(r"[ \t\f\v]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


def _normalize_ddg_redirect(href: str) -> str:
    """DuckDuckGo 리다이렉트 URL을 가능한 경우 원본 URL로 정규화한다."""
    href = href.strip()
    if href.startswith("//"):
        href = "https:" + href

    parsed = urllib.parse.urlparse(href)
    if parsed.netloc.endswith("duckduckgo.com") and parsed.path.startswith("/l/"):
        qs = urllib.parse.parse_qs(parsed.query)
        uddg = qs.get("uddg", [""])[0]
        if uddg:
            return urllib.parse.unquote(uddg)

    return href


async def _http_get(url: str, timeout_s: int = 15, max_bytes: int = 2_000_000) -> tuple[str, dict[str, str]]:
    """URL을 가져와 (body, headers)를 반환한다.

    Notes:
        표준 라이브러리 urllib 기반이며, 인코딩은 best-effort로 처리한다.
    """

    def _do_request() -> tuple[bytes, dict[str, str]]:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            headers = {k.lower(): v for k, v in resp.headers.items()}
            data = resp.read(max_bytes + 1)
            if len(data) > max_bytes:
                data = data[:max_bytes]
            return data, headers

    data, headers = await asyncio.to_thread(_do_request)

    # Decode using charset if present.
    content_type = headers.get("content-type", "")
    charset = "utf-8"
    m = re.search(r"charset=([^;\s]+)", content_type, flags=re.IGNORECASE)
    if m:
        charset = m.group(1).strip("\"'")

    try:
        text = data.decode(charset, errors="replace")
    except LookupError:
        text = data.decode("utf-8", errors="replace")

    return text, headers


async def ddg_search(query: str, max_results: int = 5, timeout_s: int = 15) -> list[SearchResult]:
    """DuckDuckGo(HTML endpoint)로 웹 검색을 수행하고 결과를 파싱한다."""
    q = query.strip()
    if not q:
        return []

    url = "https://duckduckgo.com/html/?" + urllib.parse.urlencode({"q": q})
    body, _headers = await _http_get(url, timeout_s=timeout_s, max_bytes=1_500_000)

    parser = _DuckDuckGoHTMLParser()
    parser.feed(body)
    results = parser.results

    # De-duplicate by URL (preserve order).
    seen: set[str] = set()
    deduped: list[SearchResult] = []
    for r in results:
        if not r.url or r.url in seen:
            continue
        seen.add(r.url)
        deduped.append(r)
        if len(deduped) >= max_results:
            break

    return deduped


async def fetch_and_extract_text(url: str, max_chars: int = 20_000, timeout_s: int = 15) -> dict[str, Any]:
    """URL을 fetch하고 본문 텍스트를 추출한다(best-effort)."""
    text, headers = await _http_get(url, timeout_s=timeout_s)
    content_type = headers.get("content-type", "")

    # If HTML, extract text; otherwise return raw text (still truncated).
    extracted = text
    if "text/html" in content_type.lower() or "<html" in text.lower():
        parser = _HTMLToTextParser()
        parser.feed(text)
        extracted = parser.get_text()

    extracted = html.unescape(extracted)
    if len(extracted) > max_chars:
        extracted = extracted[: max_chars - 1] + "…"

    return {
        "url": url,
        "content_type": content_type,
        "extracted_text": extracted,
        "truncated": len(extracted) >= max_chars,
    }


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="web_search",
            description="Search the web (DuckDuckGo HTML) and return a list of results (title/url/snippet).",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (1-10)",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 10,
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "HTTP timeout in seconds",
                        "default": 15,
                        "minimum": 1,
                        "maximum": 60,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="fetch_web_page",
            description="Fetch a web page and extract plain text content (best-effort).",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to fetch"},
                    "max_chars": {
                        "type": "integer",
                        "description": "Maximum number of characters to return",
                        "default": 20000,
                        "minimum": 1000,
                        "maximum": 200000,
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "HTTP timeout in seconds",
                        "default": 15,
                        "minimum": 1,
                        "maximum": 60,
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="search_and_fetch",
            description="Search the web and fetch/extract text for the top results.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "max_results": {
                        "type": "integer",
                        "description": "Number of results/pages to fetch (1-5)",
                        "default": 3,
                        "minimum": 1,
                        "maximum": 5,
                    },
                    "max_chars": {
                        "type": "integer",
                        "description": "Max chars per page",
                        "default": 10000,
                        "minimum": 1000,
                        "maximum": 200000,
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "HTTP timeout in seconds",
                        "default": 15,
                        "minimum": 1,
                        "maximum": 60,
                    },
                },
                "required": ["query"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    try:
        if name == "web_search":
            query = str(arguments.get("query", ""))
            max_results = int(arguments.get("max_results", 5))
            timeout = int(arguments.get("timeout", 15))
            results = await ddg_search(query, max_results=max_results, timeout_s=timeout)
            payload = {
                "status": "success",
                "query": query,
                "engine": "duckduckgo_html",
                "results": [
                    {"title": r.title, "url": r.url, "snippet": r.snippet}
                    for r in results
                ],
            }
            return [TextContent(type="text", text=json.dumps(payload, indent=2))]

        if name == "fetch_web_page":
            url = str(arguments.get("url", "")).strip()
            max_chars = int(arguments.get("max_chars", 20000))
            timeout = int(arguments.get("timeout", 15))
            if not url:
                return [TextContent(type="text", text=json.dumps({"status": "error", "error": "url is required"}, indent=2))]
            payload = await fetch_and_extract_text(url, max_chars=max_chars, timeout_s=timeout)
            payload["status"] = "success"
            return [TextContent(type="text", text=json.dumps(payload, indent=2))]

        if name == "search_and_fetch":
            query = str(arguments.get("query", ""))
            max_results = int(arguments.get("max_results", 3))
            max_chars = int(arguments.get("max_chars", 10000))
            timeout = int(arguments.get("timeout", 15))

            results = await ddg_search(query, max_results=max_results, timeout_s=timeout)
            pages: list[dict[str, Any]] = []
            for r in results:
                try:
                    pages.append(await fetch_and_extract_text(r.url, max_chars=max_chars, timeout_s=timeout))
                except Exception as e:  # noqa: BLE001
                    pages.append({"url": r.url, "status": "error", "error": str(e)})

            payload = {
                "status": "success",
                "query": query,
                "engine": "duckduckgo_html",
                "results": [
                    {"title": r.title, "url": r.url, "snippet": r.snippet}
                    for r in results
                ],
                "pages": pages,
            }
            return [TextContent(type="text", text=json.dumps(payload, indent=2))]

        return [TextContent(type="text", text=json.dumps({"status": "error", "error": f"Unknown tool: {name}"}, indent=2))]

    except Exception as e:  # noqa: BLE001
        return [TextContent(type="text", text=json.dumps({"status": "error", "error": str(e)}, indent=2))]


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
