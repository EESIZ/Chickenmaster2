"""병렬 검색 유틸리티 패키지.

다양한 검색 제공자를 통합하여 병렬로 검색을 수행하는 유틸리티를 제공합니다.

주요 기능:
- 비동기 병렬 실행 (세마포어 기반 동시성 제어)
- 다중 검색 제공자 지원 (arXiv, Semantic Scholar, 웹 검색)
- 결과 집계 및 중복 제거
- Rate limiting 및 지수 백오프 재시도

Example:
    >>> import asyncio
    >>> from src.utils.parallel_search import (
    ...     ArxivProvider,
    ...     SemanticScholarProvider,
    ...     run_parallel,
    ...     merge_provider_results,
    ... )
    >>> 
    >>> async def search_papers(query: str):
    ...     providers = [ArxivProvider(), SemanticScholarProvider()]
    ...     factories = [
    ...         lambda p=provider: p.search(query)
    ...         for provider in providers
    ...     ]
    ...     results = await run_parallel(
    ...         factories,
    ...         max_concurrency=3,
    ...         timeout_s=30.0,
    ...     )
    ...     
    ...     provider_results = {}
    ...     for provider, result in zip(providers, results):
    ...         if result.success:
    ...             provider_results[provider.name] = result.data
    ...     
    ...     return merge_provider_results(provider_results)
    >>> 
    >>> merged = asyncio.run(search_papers("transformer attention"))
"""

# Base classes and data structures
from src.utils.parallel_search.base import SearchProvider, SearchResult, TaskResult

# Executor functions
from src.utils.parallel_search.executor import run_parallel, run_parallel_with_retry

# Aggregation utilities
from src.utils.parallel_search.aggregator import (
    deduplicate_results,
    filter_results,
    get_statistics,
    group_by_query,
    merge_provider_results,
    rank_results,
)

# Provider implementations
from src.utils.parallel_search.providers import (
    ArxivProvider,
    SemanticScholarProvider,
    WebProvider,
)

__all__ = [
    # Base classes
    "SearchProvider",
    "SearchResult",
    "TaskResult",
    # Executor
    "run_parallel",
    "run_parallel_with_retry",
    # Aggregator
    "deduplicate_results",
    "filter_results",
    "get_statistics",
    "group_by_query",
    "merge_provider_results",
    "rank_results",
    # Providers
    "ArxivProvider",
    "SemanticScholarProvider",
    "WebProvider",
]
