"""arXiv API 검색 제공자 모듈.

arXiv API를 사용하여 학술 논문을 검색하는 SearchProvider 구현체입니다.
arXiv API의 rate limit(최소 3초 지연)을 준수합니다.

Example:
    >>> from src.utils.parallel_search.providers.arxiv_provider import ArxivProvider
    >>> 
    >>> provider = ArxivProvider()
    >>> results = await provider.search("transformer attention mechanism")
    >>> for result in results:
    ...     print(f"{result.title}: {result.url}")
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
from datetime import datetime
from typing import Any
from xml.etree import ElementTree

import httpx

from src.utils.parallel_search.base import SearchProvider, SearchResult

logger = logging.getLogger(__name__)

# arXiv API 상수
ARXIV_API_BASE_URL = "http://export.arxiv.org/api/query"
ARXIV_NAMESPACE = {"atom": "http://www.w3.org/2005/Atom"}


class ArxivProvider(SearchProvider):
    """arXiv API를 사용한 검색 제공자.

    arXiv의 공식 API를 사용하여 학술 논문을 검색합니다.
    API rate limit을 준수하기 위해 요청 간 최소 3초의 지연을 적용합니다.

    Attributes:
        name: "arxiv"
        max_concurrency: 최대 동시 요청 수 (기본값: 2, arXiv 권장)
        timeout_s: 요청 타임아웃 (기본값: 10초)
        min_delay_s: 요청 간 최소 지연 (기본값: 3초, arXiv 필수)

    Reference:
        - arXiv API 문서: https://arxiv.org/help/api/
        - Rate limit: 최소 3초 간격, burst 요청 금지

    Example:
        >>> provider = ArxivProvider(max_results=10)
        >>> results = await provider.search("neural network")
        >>> print(f"Found {len(results)} papers")
    """

    def __init__(
        self,
        *,
        max_concurrency: int = 2,
        timeout_s: float = 10.0,
        min_delay_s: float = 3.0,
        max_results: int = 10,
        sort_by: str = "relevance",
        sort_order: str = "descending",
    ) -> None:
        """ArxivProvider를 초기화합니다.

        Args:
            max_concurrency: 최대 동시 요청 수 (기본값: 2).
                arXiv는 높은 동시성을 권장하지 않습니다.
            timeout_s: 요청 타임아웃 초 (기본값: 10.0).
            min_delay_s: 요청 간 최소 지연 초 (기본값: 3.0).
                arXiv API 정책상 최소 3초 필요합니다.
            max_results: 최대 결과 수 (기본값: 10, 최대: 100).
            sort_by: 정렬 기준. "relevance", "lastUpdatedDate",
                "submittedDate" 중 하나 (기본값: "relevance").
            sort_order: 정렬 순서. "ascending", "descending" 중 하나
                (기본값: "descending").

        Raises:
            ValueError: 유효하지 않은 인자가 전달된 경우.
        """
        super().__init__(max_concurrency=max_concurrency, timeout_s=timeout_s)

        if min_delay_s < 3.0:
            logger.warning(
                "arXiv API는 최소 3초 지연을 요구합니다. "
                "min_delay_s를 3.0으로 조정합니다."
            )
            min_delay_s = 3.0

        if max_results < 1 or max_results > 100:
            raise ValueError(f"max_results는 1~100 사이여야 합니다: {max_results}")

        valid_sort_by = ["relevance", "lastUpdatedDate", "submittedDate"]
        if sort_by not in valid_sort_by:
            raise ValueError(f"sort_by는 {valid_sort_by} 중 하나여야 합니다: {sort_by}")

        valid_sort_order = ["ascending", "descending"]
        if sort_order not in valid_sort_order:
            raise ValueError(
                f"sort_order는 {valid_sort_order} 중 하나여야 합니다: {sort_order}"
            )

        self._min_delay_s = min_delay_s
        self._max_results = max_results
        self._sort_by = sort_by
        self._sort_order = sort_order
        self._last_request_time: float = 0.0
        self._lock = asyncio.Lock()

        # Connection pooling을 위한 클라이언트 설정
        self._client: httpx.AsyncClient | None = None

    @property
    def name(self) -> str:
        """제공자 이름을 반환합니다."""
        return "arxiv"

    @property
    def min_delay_s(self) -> float:
        """요청 간 최소 지연 시간(초)을 반환합니다."""
        return self._min_delay_s

    async def _get_client(self) -> httpx.AsyncClient:
        """HTTP 클라이언트를 반환합니다 (lazy initialization).

        Connection pooling을 위해 단일 클라이언트 인스턴스를 재사용합니다.

        Returns:
            httpx.AsyncClient 인스턴스.
        """
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout_s, connect=5.0),
                limits=httpx.Limits(
                    max_connections=self.max_concurrency,
                    max_keepalive_connections=self.max_concurrency,
                ),
                headers={"User-Agent": "ParallelSearch/1.0 (research tool)"},
            )
        return self._client

    async def _enforce_rate_limit(self) -> None:
        """rate limit을 준수하기 위해 필요한 만큼 대기합니다.

        arXiv API는 최소 3초 간격의 요청을 요구합니다.
        여러 코루틴이 동시에 요청할 때도 안전하게 처리합니다.
        """
        async with self._lock:
            now = time.time()
            elapsed = now - self._last_request_time
            if elapsed < self._min_delay_s:
                wait_time = self._min_delay_s - elapsed
                logger.debug("Rate limit 대기: %.2f초", wait_time)
                await asyncio.sleep(wait_time)
            self._last_request_time = time.time()

    def _build_query(self, query: str) -> str:
        """검색 쿼리를 arXiv API 형식으로 변환합니다.

        Args:
            query: 검색 쿼리 문자열.

        Returns:
            arXiv API용 쿼리 문자열.
        """
        # 기본적으로 all: (모든 필드) 검색 사용
        # 특수 접두사가 있으면 그대로 사용
        if any(
            query.startswith(prefix)
            for prefix in ["ti:", "au:", "abs:", "cat:", "id:", "all:"]
        ):
            return query
        return f"all:{query}"

    def _parse_entry(self, entry: ElementTree.Element, query: str) -> SearchResult:
        """단일 arXiv 항목을 SearchResult로 파싱합니다.

        Args:
            entry: XML 항목 요소.
            query: 원본 검색 쿼리.

        Returns:
            파싱된 SearchResult.
        """
        # 네임스페이스 처리
        ns = ARXIV_NAMESPACE

        def find_text(tag: str, default: str = "") -> str:
            elem = entry.find(f"atom:{tag}", ns)
            return elem.text.strip() if elem is not None and elem.text else default

        # 기본 필드 추출
        title = find_text("title").replace("\n", " ")
        abstract = find_text("summary").replace("\n", " ")

        # ID 추출 (예: http://arxiv.org/abs/2401.12345v1)
        arxiv_url = find_text("id")
        arxiv_id_match = re.search(r"arxiv\.org/abs/(\d+\.\d+)", arxiv_url)
        arxiv_id = arxiv_id_match.group(1) if arxiv_id_match else ""

        # PDF URL
        pdf_link = entry.find("atom:link[@title='pdf']", ns)
        pdf_url = pdf_link.get("href", "") if pdf_link is not None else ""

        # DOI 추출 (있는 경우)
        doi_elem = entry.find("atom:link[@title='doi']", ns)
        doi = ""
        if doi_elem is not None:
            doi_href = doi_elem.get("href", "")
            doi_match = re.search(r"doi\.org/(10\.\d+/[^\s]+)", doi_href)
            doi = doi_match.group(1) if doi_match else ""

        # 저자 목록
        authors = [
            author.find("atom:name", ns).text  # type: ignore[union-attr]
            for author in entry.findall("atom:author", ns)
            if author.find("atom:name", ns) is not None
        ]
        authors_str = ", ".join(authors[:3])
        if len(authors) > 3:
            authors_str += f" 외 {len(authors) - 3}명"

        # 카테고리
        categories = [
            cat.get("term", "")
            for cat in entry.findall("atom:category", ns)
        ]
        primary_category = categories[0] if categories else ""

        # 발행일
        published = find_text("published")

        # IDs 딕셔너리 구성
        ids: dict[str, str] = {}
        if arxiv_id:
            ids["arxiv_id"] = arxiv_id
        if doi:
            ids["doi"] = doi
        if primary_category:
            ids["category"] = primary_category

        # snippet 구성
        snippet = f"{authors_str}. "
        if abstract:
            snippet += abstract[:300]
            if len(abstract) > 300:
                snippet += "..."

        return SearchResult(
            provider=self.name,
            query=query,
            title=title,
            url=pdf_url or arxiv_url,
            ids=ids,
            snippet=snippet,
            score=0.8,  # arXiv 결과는 관련성이 높은 편
            fetched_at=datetime.utcnow(),
        )

    async def _handle_rate_limit_error(
        self,
        response: httpx.Response,
        retry_count: int,
        max_retries: int = 3,
    ) -> bool:
        """429 에러 처리 및 재시도 결정.

        Args:
            response: HTTP 응답.
            retry_count: 현재 재시도 횟수.
            max_retries: 최대 재시도 횟수.

        Returns:
            재시도 여부.
        """
        if retry_count >= max_retries:
            logger.error("최대 재시도 횟수 초과: %d", max_retries)
            return False

        # Retry-After 헤더 확인
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                wait_time = int(retry_after)
            except ValueError:
                wait_time = 60  # 기본 1분 대기
        else:
            # 지수 백오프
            wait_time = min(60, (2**retry_count) * self._min_delay_s)

        logger.warning(
            "Rate limit 초과 (429). %d초 후 재시도 (%d/%d)",
            wait_time,
            retry_count + 1,
            max_retries,
        )
        await asyncio.sleep(wait_time)
        return True

    async def search(self, query: str) -> list[SearchResult]:
        """arXiv API를 사용하여 검색을 수행합니다.

        Args:
            query: 검색 쿼리 문자열.
                기본적으로 모든 필드에서 검색합니다.
                특수 접두사 사용 가능:
                - ti: 제목 검색 (예: "ti:attention")
                - au: 저자 검색 (예: "au:vaswani")
                - abs: 초록 검색
                - cat: 카테고리 검색 (예: "cat:cs.LG")

        Returns:
            검색 결과 리스트. 에러 발생 시 빈 리스트 반환.

        Example:
            >>> provider = ArxivProvider()
            >>> results = await provider.search("transformer attention")
            >>> for r in results:
            ...     print(f"{r.title} ({r.ids.get('arxiv_id', 'N/A')})")
        """
        await self._enforce_rate_limit()

        client = await self._get_client()
        formatted_query = self._build_query(query)

        params = {
            "search_query": formatted_query,
            "start": 0,
            "max_results": self._max_results,
            "sortBy": self._sort_by,
            "sortOrder": self._sort_order,
        }

        retry_count = 0
        max_retries = 3

        while True:
            try:
                logger.debug("arXiv API 요청: %s", formatted_query)
                response = await client.get(ARXIV_API_BASE_URL, params=params)

                if response.status_code == 429:
                    should_retry = await self._handle_rate_limit_error(
                        response, retry_count, max_retries
                    )
                    if should_retry:
                        retry_count += 1
                        await self._enforce_rate_limit()
                        continue
                    return []

                response.raise_for_status()
                break

            except httpx.TimeoutException as e:
                logger.error("arXiv API 타임아웃: %s", str(e))
                return []

            except httpx.HTTPStatusError as e:
                logger.error("arXiv API HTTP 에러: %s", str(e))
                return []

            except httpx.RequestError as e:
                logger.error("arXiv API 요청 에러: %s", str(e))
                return []

        # XML 파싱
        try:
            root = ElementTree.fromstring(response.text)
            entries = root.findall("atom:entry", ARXIV_NAMESPACE)

            results = []
            for entry in entries:
                try:
                    result = self._parse_entry(entry, query)
                    results.append(result)
                except Exception as e:
                    logger.warning("항목 파싱 실패: %s", str(e))
                    continue

            logger.info("arXiv 검색 완료: query=%r, results=%d", query, len(results))
            return results

        except ElementTree.ParseError as e:
            logger.error("XML 파싱 에러: %s", str(e))
            return []

    async def close(self) -> None:
        """HTTP 클라이언트를 닫습니다."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> ArxivProvider:
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


__all__ = ["ArxivProvider"]
