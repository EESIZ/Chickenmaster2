"""Semantic Scholar API 검색 제공자 모듈.

Semantic Scholar API를 사용하여 학술 논문을 검색하는 SearchProvider 구현체입니다.
배치 검색 및 Paper Details API를 지원합니다.

Example:
    >>> from src.utils.parallel_search.providers.semantic_scholar_provider import (
    ...     SemanticScholarProvider,
    ... )
    >>> 
    >>> provider = SemanticScholarProvider(api_key="your_api_key")
    >>> results = await provider.search("transformer attention mechanism")
    >>> for result in results:
    ...     print(f"{result.title}: {result.ids.get('corpus_id', 'N/A')}")
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from datetime import datetime
from typing import Any

import httpx

from src.utils.parallel_search.base import SearchProvider, SearchResult

logger = logging.getLogger(__name__)

# Semantic Scholar API 상수
SS_API_BASE_URL = "https://api.semanticscholar.org/graph/v1"
SS_PARTNER_API_URL = "https://partner.semanticscholar.org/graph/v1"

# 기본 필드 (API 요청 시 포함)
DEFAULT_FIELDS = [
    "paperId",
    "corpusId",
    "title",
    "abstract",
    "url",
    "year",
    "authors",
    "citationCount",
    "influentialCitationCount",
    "externalIds",
    "publicationTypes",
]


class SemanticScholarProvider(SearchProvider):
    """Semantic Scholar API를 사용한 검색 제공자.

    Semantic Scholar의 공식 API를 사용하여 학술 논문을 검색합니다.
    API 키 없이도 사용 가능하지만, 키가 있으면 더 높은 rate limit을 적용받습니다.

    Attributes:
        name: "semantic_scholar"
        max_concurrency: 최대 동시 요청 수 (기본값: 5)
        timeout_s: 요청 타임아웃 (기본값: 10초)

    Rate Limits:
        - 인증 없음: 100 requests/5min (~0.33 rps)
        - API 키: 1 request/second (1 rps)
        - Partner API: 10 requests/second (10 rps)

    Reference:
        - API 문서: https://api.semanticscholar.org/api-docs/
        - Rate limits: https://www.semanticscholar.org/product/api#api-key

    Example:
        >>> async with SemanticScholarProvider() as provider:
        ...     results = await provider.search("neural network")
        ...     print(f"Found {len(results)} papers")
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        max_concurrency: int = 5,
        timeout_s: float = 10.0,
        max_results: int = 10,
        use_partner_api: bool = False,
    ) -> None:
        """SemanticScholarProvider를 초기화합니다.

        Args:
            api_key: Semantic Scholar API 키 (선택).
                환경변수 SEMANTIC_SCHOLAR_API_KEY에서도 읽어옵니다.
            max_concurrency: 최대 동시 요청 수 (기본값: 5).
            timeout_s: 요청 타임아웃 초 (기본값: 10.0).
            max_results: 검색당 최대 결과 수 (기본값: 10, 최대: 100).
            use_partner_api: Partner API 사용 여부 (기본값: False).
                Partner API는 더 높은 rate limit을 제공합니다.
        """
        super().__init__(max_concurrency=max_concurrency, timeout_s=timeout_s)

        # API 키 설정 (환경변수 폴백)
        self._api_key = api_key or os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
        self._use_partner_api = use_partner_api and self._api_key is not None
        self._max_results = min(max_results, 100)

        # Rate limiting 설정
        if self._use_partner_api:
            self._requests_per_second = 10.0
        elif self._api_key:
            self._requests_per_second = 1.0
        else:
            self._requests_per_second = 0.33  # 100 requests / 5 min

        self._min_interval = 1.0 / self._requests_per_second
        self._last_request_time: float = 0.0
        self._lock = asyncio.Lock()

        # HTTP 클라이언트
        self._client: httpx.AsyncClient | None = None

        logger.info(
            "SemanticScholarProvider 초기화: api_key=%s, rps=%.2f",
            "있음" if self._api_key else "없음",
            self._requests_per_second,
        )

    @property
    def name(self) -> str:
        """제공자 이름을 반환합니다."""
        return "semantic_scholar"

    def _get_base_url(self) -> str:
        """API 기본 URL을 반환합니다."""
        return SS_PARTNER_API_URL if self._use_partner_api else SS_API_BASE_URL

    async def _get_client(self) -> httpx.AsyncClient:
        """HTTP 클라이언트를 반환합니다 (lazy initialization).

        Returns:
            httpx.AsyncClient 인스턴스.
        """
        if self._client is None or self._client.is_closed:
            headers = {"User-Agent": "ParallelSearch/1.0 (research tool)"}
            if self._api_key:
                headers["x-api-key"] = self._api_key

            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout_s, connect=5.0),
                limits=httpx.Limits(
                    max_connections=self.max_concurrency * 2,
                    max_keepalive_connections=self.max_concurrency,
                ),
                headers=headers,
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

    async def _handle_rate_limit_error(
        self,
        response: httpx.Response,
        retry_count: int,
        max_retries: int = 3,
    ) -> bool:
        """429 에러 처리 및 지수 백오프 재시도.

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
                wait_time = float(retry_after)
            except ValueError:
                wait_time = 30.0
        else:
            # 지수 백오프: 1, 2, 4, 8... 초
            wait_time = min(60, (2**retry_count) * 1.0)

        logger.warning(
            "Rate limit 초과 (429). %.1f초 후 재시도 (%d/%d)",
            wait_time,
            retry_count + 1,
            max_retries,
        )
        await asyncio.sleep(wait_time)
        return True

    def _parse_paper(self, paper: dict[str, Any], query: str) -> SearchResult | None:
        """Semantic Scholar 논문 데이터를 SearchResult로 변환합니다.

        Args:
            paper: API 응답의 논문 데이터.
            query: 원본 검색 쿼리.

        Returns:
            SearchResult 또는 파싱 실패 시 None.
        """
        try:
            # 기본 필드
            paper_id = paper.get("paperId", "")
            corpus_id = paper.get("corpusId")
            title = paper.get("title", "제목 없음")
            abstract = paper.get("abstract", "")
            url = paper.get("url", "")

            # 외부 ID 추출
            external_ids = paper.get("externalIds", {}) or {}
            ids: dict[str, str] = {}

            if corpus_id:
                ids["corpus_id"] = str(corpus_id)
            if paper_id:
                ids["paper_id"] = paper_id

            # DOI, arXiv ID 등
            for key in ["DOI", "ArXiv", "PubMed", "PMID"]:
                if key in external_ids and external_ids[key]:
                    ids[key.lower()] = str(external_ids[key])

            # URL 구성
            if not url and paper_id:
                url = f"https://www.semanticscholar.org/paper/{paper_id}"

            # 저자 정보
            authors = paper.get("authors", []) or []
            author_names = [a.get("name", "") for a in authors[:3] if a.get("name")]
            authors_str = ", ".join(author_names)
            if len(authors) > 3:
                authors_str += f" 외 {len(authors) - 3}명"

            # 인용 수로 점수 계산 (정규화)
            citation_count = paper.get("citationCount", 0) or 0
            influential_count = paper.get("influentialCitationCount", 0) or 0

            # 점수: 인용 수 기반 (로그 스케일, 0.5~1.0 범위)
            import math

            base_score = 0.5
            if citation_count > 0:
                # log10(citations + 1) / 4로 정규화 (최대 ~0.5 추가)
                citation_bonus = min(0.4, math.log10(citation_count + 1) / 10)
                base_score += citation_bonus
            if influential_count > 0:
                influential_bonus = min(0.1, math.log10(influential_count + 1) / 20)
                base_score += influential_bonus

            score = min(1.0, base_score)

            # Snippet 구성
            year = paper.get("year")
            snippet_parts = []
            if authors_str:
                snippet_parts.append(authors_str)
            if year:
                snippet_parts.append(f"({year})")
            if abstract:
                abstract_preview = abstract[:250]
                if len(abstract) > 250:
                    abstract_preview += "..."
                snippet_parts.append(abstract_preview)

            snippet = " ".join(snippet_parts)

            return SearchResult(
                provider=self.name,
                query=query,
                title=title,
                url=url,
                ids=ids,
                snippet=snippet,
                score=score,
                fetched_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.warning("논문 파싱 실패: %s", str(e))
            return None

    async def search(self, query: str) -> list[SearchResult]:
        """Semantic Scholar API를 사용하여 검색을 수행합니다.

        Args:
            query: 검색 쿼리 문자열.

        Returns:
            검색 결과 리스트. 에러 발생 시 빈 리스트 반환.

        Example:
            >>> provider = SemanticScholarProvider()
            >>> results = await provider.search("attention mechanism")
            >>> for r in results:
            ...     print(f"{r.title} (citations: {r.ids.get('citation_count', 'N/A')})")
        """
        await self._enforce_rate_limit()

        client = await self._get_client()
        base_url = self._get_base_url()
        endpoint = f"{base_url}/paper/search"

        params = {
            "query": query,
            "limit": self._max_results,
            "fields": ",".join(DEFAULT_FIELDS),
        }

        retry_count = 0
        max_retries = 3

        while True:
            try:
                logger.debug("Semantic Scholar API 요청: %s", query)
                response = await client.get(endpoint, params=params)

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
                logger.error("Semantic Scholar API 타임아웃: %s", str(e))
                return []

            except httpx.HTTPStatusError as e:
                logger.error("Semantic Scholar API HTTP 에러: %s", str(e))
                return []

            except httpx.RequestError as e:
                logger.error("Semantic Scholar API 요청 에러: %s", str(e))
                return []

        # JSON 파싱
        try:
            data = response.json()
            papers = data.get("data", [])

            results = []
            for paper in papers:
                result = self._parse_paper(paper, query)
                if result:
                    results.append(result)

            logger.info(
                "Semantic Scholar 검색 완료: query=%r, results=%d",
                query,
                len(results),
            )
            return results

        except (ValueError, KeyError) as e:
            logger.error("JSON 파싱 에러: %s", str(e))
            return []

    async def batch_search(
        self,
        queries: list[str],
        batch_size: int = 500,
    ) -> dict[str, list[SearchResult]]:
        """여러 쿼리를 배치로 검색합니다.

        Semantic Scholar API의 batch endpoint를 사용하여
        여러 쿼리를 효율적으로 처리합니다.

        Note:
            현재 Semantic Scholar API는 batch paper lookup만 지원하고
            batch search는 지원하지 않습니다. 따라서 이 메서드는
            순차적으로 개별 검색을 수행합니다.

        Args:
            queries: 검색 쿼리 리스트.
            batch_size: 한 번에 처리할 쿼리 수 (현재 미사용).

        Returns:
            쿼리를 키로, 결과 리스트를 값으로 하는 딕셔너리.

        Example:
            >>> queries = ["attention mechanism", "transformer model", "BERT"]
            >>> results = await provider.batch_search(queries)
            >>> for query, papers in results.items():
            ...     print(f"{query}: {len(papers)} results")
        """
        results: dict[str, list[SearchResult]] = {}

        for query in queries:
            try:
                search_results = await self.search(query)
                results[query] = search_results
            except Exception as e:
                logger.error("배치 검색 실패 (query=%r): %s", query, str(e))
                results[query] = []

        logger.info(
            "배치 검색 완료: %d queries, %d total results",
            len(queries),
            sum(len(r) for r in results.values()),
        )
        return results

    async def get_paper_details(
        self,
        paper_id: str,
        fields: list[str] | None = None,
    ) -> SearchResult | None:
        """특정 논문의 상세 정보를 가져옵니다.

        Args:
            paper_id: Semantic Scholar Paper ID, DOI, arXiv ID 등.
                예: "649def34f8be52c8b66281af98ae884c09aef38b"
                또는 "DOI:10.18653/v1/N18-3011"
                또는 "ARXIV:2106.09685"
            fields: 요청할 필드 리스트 (기본값: DEFAULT_FIELDS).

        Returns:
            논문 정보 SearchResult 또는 찾지 못한 경우 None.

        Example:
            >>> paper = await provider.get_paper_details("ARXIV:1706.03762")
            >>> if paper:
            ...     print(f"{paper.title}")
        """
        await self._enforce_rate_limit()

        client = await self._get_client()
        base_url = self._get_base_url()
        endpoint = f"{base_url}/paper/{paper_id}"

        if fields is None:
            fields = DEFAULT_FIELDS

        params = {"fields": ",".join(fields)}

        try:
            logger.debug("Paper details 요청: %s", paper_id)
            response = await client.get(endpoint, params=params)

            if response.status_code == 404:
                logger.warning("논문을 찾을 수 없음: %s", paper_id)
                return None

            response.raise_for_status()
            paper = response.json()

            return self._parse_paper(paper, f"paper:{paper_id}")

        except httpx.HTTPStatusError as e:
            logger.error("Paper details HTTP 에러: %s", str(e))
            return None

        except httpx.RequestError as e:
            logger.error("Paper details 요청 에러: %s", str(e))
            return None

    async def close(self) -> None:
        """HTTP 클라이언트를 닫습니다."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> SemanticScholarProvider:
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


__all__ = ["SemanticScholarProvider"]
