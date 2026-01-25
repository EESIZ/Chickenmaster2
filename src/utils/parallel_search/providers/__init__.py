"""검색 제공자 패키지.

다양한 학술 검색 API 및 웹 검색 서비스를 래핑하는
SearchProvider 구현체들을 제공합니다.

Example:
    >>> from src.utils.parallel_search.providers import (
    ...     ArxivProvider,
    ...     SemanticScholarProvider,
    ...     WebProvider,
    ... )
    >>> 
    >>> # 개별 provider 사용
    >>> arxiv = ArxivProvider()
    >>> results = await arxiv.search("transformer attention")
    >>> 
    >>> # 여러 provider 병렬 실행
    >>> from src.utils.parallel_search import run_parallel
    >>> providers = [ArxivProvider(), SemanticScholarProvider()]
    >>> factories = [
    ...     lambda p=provider: p.search("transformer attention")
    ...     for provider in providers
    ... ]
    >>> results = await run_parallel(factories, max_concurrency=3, timeout_s=30.0)
"""

from src.utils.parallel_search.providers.arxiv_provider import ArxivProvider
from src.utils.parallel_search.providers.semantic_scholar_provider import (
    SemanticScholarProvider,
)
from src.utils.parallel_search.providers.web_provider import WebProvider

__all__ = [
    "ArxivProvider",
    "SemanticScholarProvider",
    "WebProvider",
]
