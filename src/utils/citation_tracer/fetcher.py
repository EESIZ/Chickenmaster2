"""Citation Tracer - 논문 메타데이터 및 참조 정보 수집 모듈.

이 모듈은 Semantic Scholar API를 통해 논문 정보를 비동기적으로 수집합니다.
Rate limiting과 연결 풀링을 통해 효율적인 API 호출을 지원합니다.

Example:
    >>> import asyncio
    >>> from citation_tracer.fetcher import fetch_paper_metadata
    >>> 
    >>> async def main():
    ...     metadata = await fetch_paper_metadata("arxiv:2401.12345")
    ...     print(metadata["title"])
    >>> 
    >>> asyncio.run(main())

Author: citation-tracer agent
Created: 2026-01-15
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, List, Literal, Optional, Union

import httpx

logger = logging.getLogger(__name__)

# Semantic Scholar API 기본 설정
SEMANTIC_SCHOLAR_BASE_URL = "https://api.semanticscholar.org/graph/v1"
DEFAULT_FIELDS = [
    "paperId",
    "title",
    "authors",
    "year",
    "citationCount",
    "influentialCitationCount",
    "abstract",
    "externalIds",
]

# 지원되는 API 제공자 타입
ProviderType = Literal["semantic_scholar", "crossref"]


class RateLimiter:
    """API 요청 간 최소 딜레이를 보장하는 Rate Limiter.

    비동기 환경에서 API 호출 빈도를 제한하여 rate limit 초과를 방지합니다.
    마지막 요청 시간을 추적하고, 필요 시 대기 시간을 강제합니다.

    Attributes:
        min_delay_s: 요청 간 최소 딜레이 (초).
        _last_request_time: 마지막 요청 완료 시간 (monotonic clock).
        _lock: 동시 접근 방지를 위한 asyncio Lock.

    Example:
        >>> limiter = RateLimiter(min_delay_s=3.0)
        >>> async def make_request():
        ...     await limiter.acquire()
        ...     # API 호출 수행
        ...     response = await client.get(url)
    """

    def __init__(self, min_delay_s: float = 3.0) -> None:
        """Rate Limiter 초기화.

        Args:
            min_delay_s: 연속 요청 간 최소 대기 시간 (초). 기본값 3.0초.
        """
        self.min_delay_s = min_delay_s
        self._last_request_time: Optional[float] = None
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """다음 요청을 위한 슬롯 획득.

        마지막 요청 이후 min_delay_s가 경과하지 않았으면 대기합니다.
        동시에 여러 코루틴이 호출해도 순차적으로 처리됩니다.

        Note:
            이 메서드는 반드시 API 호출 직전에 호출해야 합니다.
        """
        async with self._lock:
            if self._last_request_time is not None:
                elapsed = time.monotonic() - self._last_request_time
                if elapsed < self.min_delay_s:
                    wait_time = self.min_delay_s - elapsed
                    logger.debug(f"Rate limiter: {wait_time:.2f}초 대기 중...")
                    await asyncio.sleep(wait_time)

            self._last_request_time = time.monotonic()

    def reset(self) -> None:
        """마지막 요청 시간 초기화.

        테스트 또는 새로운 세션 시작 시 사용합니다.
        """
        self._last_request_time = None


# 전역 Rate Limiter 인스턴스 (모듈 레벨에서 공유)
_global_rate_limiter = RateLimiter(min_delay_s=3.0)

# 전역 HTTP 클라이언트 (연결 풀링)
_http_client: Optional[httpx.AsyncClient] = None


async def _get_http_client() -> httpx.AsyncClient:
    """전역 HTTP 클라이언트 반환 (lazy initialization).

    연결 풀링을 위해 단일 클라이언트를 재사용합니다.

    Returns:
        httpx.AsyncClient: 설정된 HTTP 클라이언트.
    """
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0, connect=5.0),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            headers={
                "User-Agent": "CitationTracer/1.0 (Research Tool)",
            },
        )
    return _http_client


async def close_http_client() -> None:
    """전역 HTTP 클라이언트 종료.

    애플리케이션 종료 시 리소스 정리를 위해 호출합니다.
    """
    global _http_client
    if _http_client is not None and not _http_client.is_closed:
        await _http_client.aclose()
        _http_client = None


def canonicalize_paper_id(paper: Union[str, Dict[str, Any]]) -> str:
    """논문 ID를 표준 형식으로 변환.

    우선순위: DOI > arXiv ID > Semantic Scholar corpus_id
    반환 형식: "doi:10.xxx", "arxiv:2401.xxx", "corpus_id:12345"

    Args:
        paper: 논문 ID 문자열 또는 externalIds를 포함한 논문 메타데이터 dict.
            - 문자열인 경우: 이미 표준화된 ID로 간주하거나 paperId로 처리.
            - dict인 경우: externalIds 필드에서 ID 추출.

    Returns:
        표준화된 논문 ID 문자열.

    Examples:
        >>> canonicalize_paper_id({"externalIds": {"DOI": "10.1234/example"}})
        'doi:10.1234/example'

        >>> canonicalize_paper_id({"externalIds": {"ArXiv": "2401.12345"}})
        'arxiv:2401.12345'

        >>> canonicalize_paper_id({"paperId": "abc123"})
        'corpus_id:abc123'

        >>> canonicalize_paper_id("arxiv:2401.12345")
        'arxiv:2401.12345'
    """
    # 이미 문자열인 경우
    if isinstance(paper, str):
        # 이미 표준 형식인지 확인
        if paper.startswith(("doi:", "arxiv:", "corpus_id:")):
            return paper
        # Semantic Scholar paperId 형식으로 간주
        return f"corpus_id:{paper}"

    # dict에서 ID 추출
    external_ids: Dict[str, Any] = paper.get("externalIds", {}) or {}
    paper_id: Optional[str] = paper.get("paperId")

    # 우선순위 1: DOI
    if "DOI" in external_ids and external_ids["DOI"]:
        return f"doi:{external_ids['DOI']}"

    # 우선순위 2: arXiv ID
    if "ArXiv" in external_ids and external_ids["ArXiv"]:
        return f"arxiv:{external_ids['ArXiv']}"

    # 우선순위 3: Semantic Scholar corpus_id (paperId)
    if paper_id:
        return f"corpus_id:{paper_id}"

    # CorpusId 필드가 별도로 있는 경우
    if "CorpusId" in external_ids and external_ids["CorpusId"]:
        return f"corpus_id:{external_ids['CorpusId']}"

    # ID를 찾을 수 없는 경우
    raise ValueError(f"논문 ID를 찾을 수 없습니다: {paper}")


def _extract_paper_id_for_api(paper_id: str) -> str:
    """API 호출용 논문 ID 추출.

    표준화된 ID에서 API 호출에 사용할 형식으로 변환합니다.

    Args:
        paper_id: canonicalize_paper_id()로 표준화된 ID.

    Returns:
        Semantic Scholar API에서 사용 가능한 ID 형식.
    """
    if paper_id.startswith("doi:"):
        return paper_id  # Semantic Scholar는 "doi:xxx" 형식 지원
    elif paper_id.startswith("arxiv:"):
        # "arxiv:2401.12345" -> "ARXIV:2401.12345"
        return f"ARXIV:{paper_id[6:]}"
    elif paper_id.startswith("corpus_id:"):
        return paper_id[10:]  # corpus_id 접두사 제거
    else:
        return paper_id


async def fetch_paper_metadata(
    paper_id: str,
    provider: ProviderType = "semantic_scholar",
    rate_limiter: Optional[RateLimiter] = None,
) -> Dict[str, Any]:
    """논문 메타데이터를 API에서 비동기로 수집.

    Semantic Scholar API를 통해 논문의 제목, 초록, 저자, 출판연도,
    인용 수 등의 메타데이터를 수집합니다.

    Args:
        paper_id: 논문 식별자. 다음 형식을 지원:
            - "doi:10.1234/example"
            - "arxiv:2401.12345"
            - "corpus_id:abc123"
            - 또는 직접 Semantic Scholar paperId
        provider: API 제공자. 현재 "semantic_scholar"만 지원.
        rate_limiter: 사용할 RateLimiter 인스턴스. None이면 전역 인스턴스 사용.

    Returns:
        논문 메타데이터 dictionary:
            - paperId: Semantic Scholar 내부 ID
            - title: 논문 제목
            - abstract: 초록 (없으면 None)
            - authors: 저자 목록 [{"name": "...", "authorId": "..."}]
            - year: 출판 연도
            - citationCount: 인용 수
            - influentialCitationCount: 영향력 있는 인용 수
            - externalIds: 외부 ID (DOI, ArXiv 등)
            - canonicalId: 표준화된 ID

    Raises:
        httpx.HTTPStatusError: API 요청 실패 (4xx, 5xx).
        httpx.RequestError: 네트워크 오류.
        ValueError: 지원하지 않는 provider.

    Example:
        >>> metadata = await fetch_paper_metadata("arxiv:2401.12345")
        >>> print(f"제목: {metadata['title']}")
        >>> print(f"인용 수: {metadata['citationCount']}")
    """
    if provider != "semantic_scholar":
        raise ValueError(f"지원하지 않는 provider: {provider}. 현재 'semantic_scholar'만 지원합니다.")

    # Rate limiting
    limiter = rate_limiter or _global_rate_limiter
    await limiter.acquire()

    # API용 ID 추출
    api_id = _extract_paper_id_for_api(paper_id)
    fields = ",".join(DEFAULT_FIELDS)
    url = f"{SEMANTIC_SCHOLAR_BASE_URL}/paper/{api_id}?fields={fields}"

    logger.debug(f"Fetching paper metadata: {paper_id} -> {url}")

    client = await _get_http_client()

    try:
        response = await client.get(url)
        response.raise_for_status()
        data: Dict[str, Any] = response.json()

        # 표준화된 ID 추가
        data["canonicalId"] = canonicalize_paper_id(data)

        logger.info(
            f"논문 메타데이터 수집 완료: {data.get('title', 'Unknown')[:50]}... "
            f"(인용 수: {data.get('citationCount', 0)})"
        )

        return data

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.warning(f"논문을 찾을 수 없습니다: {paper_id}")
            raise
        elif e.response.status_code == 429:
            logger.error(f"Rate limit 초과: {paper_id}. 잠시 후 다시 시도하세요.")
            raise
        else:
            logger.error(f"API 오류 ({e.response.status_code}): {paper_id}")
            raise

    except httpx.RequestError as e:
        logger.error(f"네트워크 오류: {paper_id} - {e}")
        raise


async def fetch_references(
    paper_id: str,
    provider: ProviderType = "semantic_scholar",
    rate_limiter: Optional[RateLimiter] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """논문의 참조 문헌 목록을 비동기로 수집.

    지정된 논문이 인용한 다른 논문들의 메타데이터를 수집합니다.
    각 참조 문헌에 대해 표준화된 ID가 추가됩니다.

    Args:
        paper_id: 논문 식별자 (fetch_paper_metadata와 동일한 형식 지원).
        provider: API 제공자. 현재 "semantic_scholar"만 지원.
        rate_limiter: 사용할 RateLimiter 인스턴스. None이면 전역 인스턴스 사용.
        limit: 최대 수집할 참조 문헌 수 (기본값 100, 최대 1000).
        offset: 페이지네이션 오프셋.

    Returns:
        참조 문헌 메타데이터 리스트. 각 항목은 fetch_paper_metadata 반환값과
        동일한 구조를 가지며, 추가로 다음 필드 포함:
            - isInfluential: 영향력 있는 인용 여부 (bool)
            - canonicalId: 표준화된 ID

    Raises:
        httpx.HTTPStatusError: API 요청 실패.
        httpx.RequestError: 네트워크 오류.
        ValueError: 지원하지 않는 provider.

    Example:
        >>> references = await fetch_references("arxiv:2401.12345")
        >>> for ref in references[:5]:
        ...     print(f"- {ref['title']} ({ref['year']})")
    """
    if provider != "semantic_scholar":
        raise ValueError(f"지원하지 않는 provider: {provider}. 현재 'semantic_scholar'만 지원합니다.")

    # Rate limiting
    limiter = rate_limiter or _global_rate_limiter
    await limiter.acquire()

    # API용 ID 추출
    api_id = _extract_paper_id_for_api(paper_id)
    fields = ",".join([f"citedPaper.{f}" for f in DEFAULT_FIELDS] + ["isInfluential"])

    url = (
        f"{SEMANTIC_SCHOLAR_BASE_URL}/paper/{api_id}/references"
        f"?fields={fields}&limit={min(limit, 1000)}&offset={offset}"
    )

    logger.debug(f"Fetching references: {paper_id} -> {url}")

    client = await _get_http_client()

    try:
        response = await client.get(url)
        response.raise_for_status()
        data: Dict[str, Any] = response.json()

        references: List[Dict[str, Any]] = []
        for item in data.get("data", []):
            cited_paper = item.get("citedPaper")
            if cited_paper and cited_paper.get("paperId"):
                # isInfluential 플래그 추가
                cited_paper["isInfluential"] = item.get("isInfluential", False)
                # 표준화된 ID 추가
                try:
                    cited_paper["canonicalId"] = canonicalize_paper_id(cited_paper)
                except ValueError:
                    # ID 표준화 실패 시 paperId 사용
                    cited_paper["canonicalId"] = f"corpus_id:{cited_paper['paperId']}"
                references.append(cited_paper)

        logger.info(f"참조 문헌 {len(references)}개 수집 완료 (paper_id: {paper_id})")

        return references

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.warning(f"논문을 찾을 수 없습니다: {paper_id}")
            return []
        elif e.response.status_code == 429:
            logger.error(f"Rate limit 초과: {paper_id}. 잠시 후 다시 시도하세요.")
            raise
        else:
            logger.error(f"API 오류 ({e.response.status_code}): {paper_id}")
            raise

    except httpx.RequestError as e:
        logger.error(f"네트워크 오류: {paper_id} - {e}")
        raise


async def fetch_citations(
    paper_id: str,
    provider: ProviderType = "semantic_scholar",
    rate_limiter: Optional[RateLimiter] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """논문을 인용한 다른 논문 목록을 비동기로 수집.

    지정된 논문을 인용한 후속 논문들의 메타데이터를 수집합니다.
    (순방향 인용 추적에 사용)

    Args:
        paper_id: 논문 식별자.
        provider: API 제공자. 현재 "semantic_scholar"만 지원.
        rate_limiter: 사용할 RateLimiter 인스턴스.
        limit: 최대 수집할 인용 논문 수 (기본값 100, 최대 1000).
        offset: 페이지네이션 오프셋.

    Returns:
        인용 논문 메타데이터 리스트. 각 항목 구조는 fetch_references와 동일.

    Raises:
        httpx.HTTPStatusError: API 요청 실패.
        httpx.RequestError: 네트워크 오류.
        ValueError: 지원하지 않는 provider.

    Example:
        >>> citations = await fetch_citations("arxiv:1706.03762")  # Attention paper
        >>> print(f"이 논문을 인용한 논문 수: {len(citations)}")
    """
    if provider != "semantic_scholar":
        raise ValueError(f"지원하지 않는 provider: {provider}. 현재 'semantic_scholar'만 지원합니다.")

    # Rate limiting
    limiter = rate_limiter or _global_rate_limiter
    await limiter.acquire()

    # API용 ID 추출
    api_id = _extract_paper_id_for_api(paper_id)
    fields = ",".join([f"citingPaper.{f}" for f in DEFAULT_FIELDS] + ["isInfluential"])

    url = (
        f"{SEMANTIC_SCHOLAR_BASE_URL}/paper/{api_id}/citations"
        f"?fields={fields}&limit={min(limit, 1000)}&offset={offset}"
    )

    logger.debug(f"Fetching citations: {paper_id} -> {url}")

    client = await _get_http_client()

    try:
        response = await client.get(url)
        response.raise_for_status()
        data: Dict[str, Any] = response.json()

        citations: List[Dict[str, Any]] = []
        for item in data.get("data", []):
            citing_paper = item.get("citingPaper")
            if citing_paper and citing_paper.get("paperId"):
                citing_paper["isInfluential"] = item.get("isInfluential", False)
                try:
                    citing_paper["canonicalId"] = canonicalize_paper_id(citing_paper)
                except ValueError:
                    citing_paper["canonicalId"] = f"corpus_id:{citing_paper['paperId']}"
                citations.append(citing_paper)

        logger.info(f"인용 논문 {len(citations)}개 수집 완료 (paper_id: {paper_id})")

        return citations

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.warning(f"논문을 찾을 수 없습니다: {paper_id}")
            return []
        elif e.response.status_code == 429:
            logger.error(f"Rate limit 초과: {paper_id}. 잠시 후 다시 시도하세요.")
            raise
        else:
            logger.error(f"API 오류 ({e.response.status_code}): {paper_id}")
            raise

    except httpx.RequestError as e:
        logger.error(f"네트워크 오류: {paper_id} - {e}")
        raise


# ============================================================================
# 유틸리티 함수
# ============================================================================


def get_rate_limiter(min_delay_s: float = 3.0) -> RateLimiter:
    """새로운 RateLimiter 인스턴스 생성.

    Args:
        min_delay_s: 최소 딜레이 (초).

    Returns:
        새로운 RateLimiter 인스턴스.
    """
    return RateLimiter(min_delay_s=min_delay_s)


def reset_global_rate_limiter() -> None:
    """전역 Rate Limiter 초기화.

    테스트 또는 새로운 세션 시작 시 사용합니다.
    """
    _global_rate_limiter.reset()


# ============================================================================
# 테스트용 코드
# ============================================================================

if __name__ == "__main__":
    # 간단한 테스트
    async def _test() -> None:
        """모듈 기능 테스트."""
        logging.basicConfig(level=logging.DEBUG)

        # 1. canonicalize_paper_id 테스트
        print("=== canonicalize_paper_id 테스트 ===")
        test_cases = [
            {"externalIds": {"DOI": "10.1234/test"}, "paperId": "abc"},
            {"externalIds": {"ArXiv": "2401.12345"}, "paperId": "def"},
            {"externalIds": {}, "paperId": "ghi123"},
            "arxiv:2401.00001",
            "corpus_id:12345",
        ]
        for tc in test_cases:
            result = canonicalize_paper_id(tc)
            print(f"  {tc} -> {result}")

        # 2. fetch_paper_metadata 테스트 (실제 API 호출)
        print("\n=== fetch_paper_metadata 테스트 ===")
        try:
            # "Attention Is All You Need" 논문
            metadata = await fetch_paper_metadata("arxiv:1706.03762")
            print(f"  제목: {metadata.get('title')}")
            print(f"  연도: {metadata.get('year')}")
            print(f"  인용 수: {metadata.get('citationCount')}")
            print(f"  표준 ID: {metadata.get('canonicalId')}")
        except Exception as e:
            print(f"  오류: {e}")

        # 3. fetch_references 테스트
        print("\n=== fetch_references 테스트 ===")
        try:
            refs = await fetch_references("arxiv:1706.03762", limit=5)
            print(f"  수집된 참조 문헌: {len(refs)}개")
            for ref in refs[:3]:
                print(f"    - {ref.get('title', 'Unknown')[:60]}...")
        except Exception as e:
            print(f"  오류: {e}")

        # 클라이언트 정리
        await close_http_client()

    asyncio.run(_test())
