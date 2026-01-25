"""웹 검색 제공자 모듈.

기존 MCP 웹 검색 도구를 래핑하여 SearchProvider 인터페이스로 제공합니다.
직접 검색 엔진 API를 호출하지 않고 MCP 서버를 통해 검색을 수행합니다.

Example:
    >>> from src.utils.parallel_search.providers.web_provider import WebProvider
    >>> 
    >>> provider = WebProvider()
    >>> results = await provider.search("python async programming best practices")
    >>> for result in results:
    ...     print(f"{result.title}: {result.url}")
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import re
import time
from datetime import datetime
from typing import Any

import httpx

from src.utils.parallel_search.base import SearchProvider, SearchResult

logger = logging.getLogger(__name__)

# 웹 검색 API 상수
DEFAULT_SEARCH_API_URL = "https://api.search.brave.com/res/v1/web/search"


class WebProvider(SearchProvider):
    """웹 검색 제공자.

    일반 웹 검색을 수행하여 다양한 소스의 결과를 제공합니다.
    MCP 웹 검색 서버가 있으면 사용하고, 없으면 직접 검색 API를 호출합니다.

    Attributes:
        name: "web"
        max_concurrency: 최대 동시 요청 수 (기본값: 3)
        timeout_s: 요청 타임아웃 (기본값: 15초)

    Example:
        >>> async with WebProvider() as provider:
        ...     results = await provider.search("machine learning tutorial")
        ...     for r in results:
        ...         print(f"{r.title}: {r.url}")
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        search_api_url: str | None = None,
        max_concurrency: int = 3,
        timeout_s: float = 15.0,
        max_results: int = 10,
        mcp_server_url: str | None = None,
    ) -> None:
        """WebProvider를 초기화합니다.

        Args:
            api_key: 검색 API 키 (선택).
                환경변수 BRAVE_SEARCH_API_KEY 또는 SEARCH_API_KEY에서도 읽어옵니다.
            search_api_url: 검색 API URL (기본값: Brave Search API).
            max_concurrency: 최대 동시 요청 수 (기본값: 3).
            timeout_s: 요청 타임아웃 초 (기본값: 15.0).
            max_results: 최대 결과 수 (기본값: 10).
            mcp_server_url: MCP 웹 검색 서버 URL (선택).
                설정되면 MCP 서버를 통해 검색합니다.
        """
        super().__init__(max_concurrency=max_concurrency, timeout_s=timeout_s)

        # API 키 설정 (환경변수 폴백)
        self._api_key = (
            api_key
            or os.environ.get("BRAVE_SEARCH_API_KEY")
            or os.environ.get("SEARCH_API_KEY")
        )
        self._search_api_url = search_api_url or DEFAULT_SEARCH_API_URL
        self._max_results = max_results
        self._mcp_server_url = mcp_server_url

        # Rate limiting (보수적 설정)
        self._min_interval = 0.5  # 2 rps 제한
        self._last_request_time: float = 0.0
        self._lock = asyncio.Lock()

        # HTTP 클라이언트
        self._client: httpx.AsyncClient | None = None

        logger.info(
            "WebProvider 초기화: api_key=%s, mcp=%s",
            "있음" if self._api_key else "없음",
            "있음" if self._mcp_server_url else "없음",
        )

    @property
    def name(self) -> str:
        """제공자 이름을 반환합니다."""
        return "web"

    async def _get_client(self) -> httpx.AsyncClient:
        """HTTP 클라이언트를 반환합니다 (lazy initialization).

        Returns:
            httpx.AsyncClient 인스턴스.
        """
        if self._client is None or self._client.is_closed:
            headers = {"User-Agent": "ParallelSearch/1.0 (research tool)"}
            if self._api_key:
                headers["X-Subscription-Token"] = self._api_key

            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout_s, connect=5.0),
                limits=httpx.Limits(
                    max_connections=self.max_concurrency * 2,
                    max_keepalive_connections=self.max_concurrency,
                ),
                headers=headers,
                follow_redirects=True,
            )
        return self._client

    async def _enforce_rate_limit(self) -> None:
        """rate limit을 준수하기 위해 필요한 만큼 대기합니다."""
        async with self._lock:
            now = time.time()
            elapsed = now - self._last_request_time
            if elapsed < self._min_interval:
                wait_time = self._min_interval - elapsed
                logger.debug("Rate limit 대기: %.3f초", wait_time)
                await asyncio.sleep(wait_time)
            self._last_request_time = time.time()

    def _generate_result_id(self, url: str) -> str:
        """URL로부터 고유 결과 ID를 생성합니다.

        Args:
            url: 결과 URL.

        Returns:
            URL 기반 해시 ID.
        """
        return hashlib.md5(url.encode()).hexdigest()[:12]

    def _extract_domain(self, url: str) -> str:
        """URL에서 도메인을 추출합니다.

        Args:
            url: 전체 URL.

        Returns:
            도메인 문자열.
        """
        match = re.search(r"https?://([^/]+)", url)
        return match.group(1) if match else ""

    def _calculate_score(
        self,
        position: int,
        total: int,
        domain: str,
    ) -> float:
        """검색 결과 점수를 계산합니다.

        순위와 도메인 신뢰도를 기반으로 점수를 계산합니다.

        Args:
            position: 검색 결과 내 순위 (0-indexed).
            total: 총 결과 수.
            domain: 결과 도메인.

        Returns:
            0.0~1.0 범위의 점수.
        """
        # 순위 기반 점수 (1위: 0.9, 10위: 0.45)
        rank_score = max(0.3, 0.9 - (position / total) * 0.5)

        # 도메인 신뢰도 보너스
        trusted_domains = {
            "arxiv.org": 0.1,
            "github.com": 0.08,
            "stackoverflow.com": 0.05,
            "medium.com": 0.03,
            "wikipedia.org": 0.05,
            "docs.python.org": 0.08,
            "pytorch.org": 0.08,
            "tensorflow.org": 0.08,
            "huggingface.co": 0.08,
        }

        domain_bonus = 0.0
        for trusted, bonus in trusted_domains.items():
            if trusted in domain:
                domain_bonus = bonus
                break

        return min(1.0, rank_score + domain_bonus)

    def _parse_brave_result(
        self,
        result: dict[str, Any],
        query: str,
        position: int,
        total: int,
    ) -> SearchResult | None:
        """Brave Search API 결과를 SearchResult로 변환합니다.

        Args:
            result: API 응답의 단일 결과.
            query: 원본 검색 쿼리.
            position: 결과 순위.
            total: 총 결과 수.

        Returns:
            SearchResult 또는 파싱 실패 시 None.
        """
        try:
            title = result.get("title", "")
            url = result.get("url", "")
            description = result.get("description", "")

            if not title or not url:
                return None

            domain = self._extract_domain(url)
            result_id = self._generate_result_id(url)
            score = self._calculate_score(position, total, domain)

            return SearchResult(
                provider=self.name,
                query=query,
                title=title,
                url=url,
                ids={"web_id": result_id, "domain": domain},
                snippet=description,
                score=score,
                fetched_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.warning("웹 결과 파싱 실패: %s", str(e))
            return None

    async def _search_via_api(self, query: str) -> list[SearchResult]:
        """검색 API를 직접 호출하여 검색합니다.

        Args:
            query: 검색 쿼리.

        Returns:
            검색 결과 리스트.
        """
        if not self._api_key:
            logger.warning("검색 API 키가 설정되지 않았습니다")
            return []

        client = await self._get_client()

        params = {
            "q": query,
            "count": self._max_results,
            "safesearch": "moderate",
        }

        try:
            response = await client.get(self._search_api_url, params=params)
            response.raise_for_status()

            data = response.json()
            web_results = data.get("web", {}).get("results", [])

            results = []
            total = len(web_results)
            for i, result in enumerate(web_results):
                parsed = self._parse_brave_result(result, query, i, total)
                if parsed:
                    results.append(parsed)

            return results

        except httpx.HTTPStatusError as e:
            logger.error("검색 API HTTP 에러: %s", str(e))
            return []

        except httpx.RequestError as e:
            logger.error("검색 API 요청 에러: %s", str(e))
            return []

    async def _search_via_mcp(self, query: str) -> list[SearchResult]:
        """MCP 서버를 통해 검색합니다.

        Args:
            query: 검색 쿼리.

        Returns:
            검색 결과 리스트.
        """
        if not self._mcp_server_url:
            return []

        client = await self._get_client()

        try:
            # MCP 프로토콜에 따른 요청
            response = await client.post(
                self._mcp_server_url,
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "web_search",
                        "arguments": {"query": query, "max_results": self._max_results},
                    },
                    "id": 1,
                },
            )
            response.raise_for_status()

            data = response.json()
            if "error" in data:
                logger.error("MCP 에러: %s", data["error"])
                return []

            # MCP 응답 파싱 (서버 구현에 따라 다름)
            mcp_results = data.get("result", {}).get("content", [])
            results = []

            for i, item in enumerate(mcp_results):
                if item.get("type") == "text":
                    # 텍스트 형식 결과 파싱
                    text = item.get("text", "")
                    # 간단한 파싱 (서버 출력 형식에 따라 조정 필요)
                    lines = text.strip().split("\n")
                    for line in lines:
                        if line.startswith("- "):
                            # "- [title](url): description" 형식 가정
                            match = re.match(
                                r"- \[(.+?)\]\((.+?)\)(?:: (.*))?", line
                            )
                            if match:
                                title, url, desc = match.groups()
                                domain = self._extract_domain(url)
                                score = self._calculate_score(
                                    len(results), self._max_results, domain
                                )
                                results.append(
                                    SearchResult(
                                        provider=self.name,
                                        query=query,
                                        title=title,
                                        url=url,
                                        ids={
                                            "web_id": self._generate_result_id(url),
                                            "domain": domain,
                                        },
                                        snippet=desc or "",
                                        score=score,
                                        fetched_at=datetime.utcnow(),
                                    )
                                )

            return results

        except httpx.RequestError as e:
            logger.error("MCP 요청 에러: %s", str(e))
            return []

    async def search(self, query: str) -> list[SearchResult]:
        """웹 검색을 수행합니다.

        MCP 서버가 설정되어 있으면 MCP를 통해, 아니면 직접 API를 호출합니다.

        Args:
            query: 검색 쿼리 문자열.

        Returns:
            검색 결과 리스트. 에러 발생 시 빈 리스트 반환.

        Example:
            >>> provider = WebProvider(api_key="your_key")
            >>> results = await provider.search("python async tutorial")
            >>> for r in results:
            ...     print(f"{r.title}: {r.url}")
        """
        await self._enforce_rate_limit()

        logger.debug("웹 검색 시작: %s", query)

        # MCP 서버 우선, 없으면 직접 API 호출
        if self._mcp_server_url:
            results = await self._search_via_mcp(query)
            if results:
                logger.info("MCP 웹 검색 완료: query=%r, results=%d", query, len(results))
                return results
            logger.warning("MCP 검색 실패, API 폴백 시도")

        results = await self._search_via_api(query)
        logger.info("API 웹 검색 완료: query=%r, results=%d", query, len(results))
        return results

    async def close(self) -> None:
        """HTTP 클라이언트를 닫습니다."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> WebProvider:
        """비동기 컨텍스트 매니저 진입."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """비동기 컨텍스트 매니저 종료."""
        await self.close()


__all__ = ["WebProvider"]
