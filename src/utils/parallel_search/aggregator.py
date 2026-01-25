"""검색 결과 집계 및 중복 제거 모듈.

이 모듈은 여러 검색 제공자로부터 받은 결과를 통합하고,
중복을 제거하며, 다양한 전략으로 결과를 정렬하는 기능을 제공합니다.

Example:
    >>> from src.utils.parallel_search.aggregator import (
    ...     deduplicate_results,
    ...     rank_results,
    ...     merge_provider_results,
    ... )
    >>> 
    >>> # 여러 provider 결과 병합
    >>> provider_results = {
    ...     "arxiv": arxiv_results,
    ...     "semantic_scholar": ss_results,
    ... }
    >>> merged = merge_provider_results(provider_results)
    >>> 
    >>> # 중복 제거 및 정렬
    >>> unique = deduplicate_results(merged)
    >>> ranked = rank_results(unique, strategy="score_desc")
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime
from typing import TypeVar

from src.utils.parallel_search.base import SearchResult

logger = logging.getLogger(__name__)

T = TypeVar("T")


def _get_canonical_id(result: SearchResult, priority: list[str]) -> str | None:
    """결과에서 우선순위에 따라 정규 ID를 추출합니다.

    Args:
        result: 검색 결과.
        priority: ID 우선순위 리스트 (예: ["doi", "arxiv_id", "corpus_id"]).

    Returns:
        찾은 첫 번째 ID 또는 None.
    """
    for id_type in priority:
        if id_type in result.ids and result.ids[id_type]:
            return f"{id_type}:{result.ids[id_type]}"
    return None


def deduplicate_results(
    results: list[SearchResult],
    priority: list[str] | None = None,
) -> list[SearchResult]:
    """검색 결과에서 중복을 제거합니다.

    정규 ID(DOI, arXiv ID 등)를 기준으로 중복을 판별하며,
    동일한 ID를 가진 결과 중 점수가 높은 것을 유지합니다.

    Args:
        results: 검색 결과 리스트.
        priority: ID 우선순위 리스트 (기본값: ["doi", "arxiv_id", "corpus_id"]).
            리스트 앞쪽의 ID 타입이 더 높은 우선순위를 가집니다.
            여러 ID를 가진 결과의 경우 첫 번째로 일치하는 ID를 사용합니다.

    Returns:
        중복이 제거된 결과 리스트.
        원본 순서를 최대한 유지하며, 중복된 결과 중 점수가
        가장 높은 것만 포함됩니다.

    Example:
        >>> results = [
        ...     SearchResult(provider="arxiv", title="Paper A", 
        ...                  ids={"arxiv_id": "2401.12345"}, score=0.9, ...),
        ...     SearchResult(provider="semantic_scholar", title="Paper A",
        ...                  ids={"arxiv_id": "2401.12345"}, score=0.8, ...),
        ... ]
        >>> unique = deduplicate_results(results)
        >>> len(unique)  # 1 (점수가 높은 arxiv 결과만 유지)
        1
    """
    if priority is None:
        priority = ["doi", "arxiv_id", "corpus_id", "pmid", "pmcid"]

    seen: dict[str, SearchResult] = {}
    results_without_id: list[SearchResult] = []

    for result in results:
        canonical_id = _get_canonical_id(result, priority)

        if canonical_id is None:
            # ID가 없는 결과는 URL로 중복 체크
            url_key = f"url:{result.url}"
            if url_key not in seen:
                seen[url_key] = result
                results_without_id.append(result)
            elif result.score > seen[url_key].score:
                # URL로 매칭된 결과 중 점수가 높은 것으로 교체
                old_result = seen[url_key]
                idx = results_without_id.index(old_result)
                results_without_id[idx] = result
                seen[url_key] = result
        elif canonical_id not in seen:
            seen[canonical_id] = result
        elif result.score > seen[canonical_id].score:
            # 더 높은 점수의 결과로 교체
            seen[canonical_id] = result

    # ID가 있는 결과들 (원본 순서 유지)
    id_results: list[SearchResult] = []
    seen_ids: set[str] = set()
    for result in results:
        canonical_id = _get_canonical_id(result, priority)
        if canonical_id and canonical_id not in seen_ids:
            if canonical_id in seen:
                id_results.append(seen[canonical_id])
                seen_ids.add(canonical_id)

    # ID가 있는 결과를 먼저, 없는 결과를 나중에
    deduplicated = id_results + results_without_id

    logger.debug(
        "중복 제거: %d -> %d개 결과",
        len(results),
        len(deduplicated),
    )

    return deduplicated


def rank_results(
    results: list[SearchResult],
    strategy: str = "score_desc",
    provider_priority: list[str] | None = None,
) -> list[SearchResult]:
    """검색 결과를 지정된 전략에 따라 정렬합니다.

    Args:
        results: 검색 결과 리스트.
        strategy: 정렬 전략. 다음 중 하나:
            - "score_desc": 점수 내림차순 (기본값).
            - "score_asc": 점수 오름차순.
            - "timestamp_desc": 최신순.
            - "timestamp_asc": 오래된 순.
            - "provider": 제공자 우선순위에 따라 정렬.
            - "combined": 점수와 제공자 우선순위 조합.
        provider_priority: 제공자 우선순위 리스트 (strategy="provider" 또는
            "combined"일 때 사용). 기본값: ["semantic_scholar", "arxiv", "web"].

    Returns:
        정렬된 결과 리스트 (새 리스트, 원본 불변).

    Raises:
        ValueError: 알 수 없는 전략이 지정된 경우.

    Example:
        >>> ranked = rank_results(results, strategy="score_desc")
        >>> ranked[0].score >= ranked[1].score
        True
    """
    if provider_priority is None:
        provider_priority = ["semantic_scholar", "arxiv", "web", "google"]

    # 제공자 우선순위 맵 (낮을수록 높은 우선순위)
    provider_rank = {p: i for i, p in enumerate(provider_priority)}
    default_rank = len(provider_priority)  # 알 수 없는 제공자는 맨 뒤

    # 정렬 키 함수 정의
    sort_keys: dict[str, Callable[[SearchResult], tuple]] = {
        "score_desc": lambda r: (-r.score, r.provider),
        "score_asc": lambda r: (r.score, r.provider),
        "timestamp_desc": lambda r: (-r.fetched_at.timestamp(), r.provider),
        "timestamp_asc": lambda r: (r.fetched_at.timestamp(), r.provider),
        "provider": lambda r: (
            provider_rank.get(r.provider, default_rank),
            -r.score,
        ),
        "combined": lambda r: (
            -r.score * 0.7 - (1 - provider_rank.get(r.provider, default_rank) / (default_rank + 1)) * 0.3,
            r.provider,
        ),
    }

    if strategy not in sort_keys:
        raise ValueError(
            f"알 수 없는 정렬 전략입니다: {strategy}. "
            f"가능한 전략: {list(sort_keys.keys())}"
        )

    ranked = sorted(results, key=sort_keys[strategy])

    logger.debug("결과 정렬 완료: strategy=%s, count=%d", strategy, len(ranked))

    return ranked


def merge_provider_results(
    provider_results: dict[str, list[SearchResult]],
    deduplicate: bool = True,
    rank_strategy: str = "combined",
    priority: list[str] | None = None,
) -> list[SearchResult]:
    """여러 제공자의 검색 결과를 통합합니다.

    각 제공자의 결과를 하나의 리스트로 병합하고,
    선택적으로 중복 제거와 정렬을 수행합니다.

    Args:
        provider_results: 제공자별 검색 결과 딕셔너리.
            키는 제공자 이름, 값은 해당 제공자의 결과 리스트입니다.
        deduplicate: 중복 제거 수행 여부 (기본값: True).
        rank_strategy: 정렬 전략 (기본값: "combined").
            rank_results 함수의 strategy 파라미터 참조.
        priority: 중복 제거 시 ID 우선순위 리스트.
            deduplicate_results 함수의 priority 파라미터 참조.

    Returns:
        통합된 검색 결과 리스트.

    Example:
        >>> provider_results = {
        ...     "arxiv": [SearchResult(...), SearchResult(...)],
        ...     "semantic_scholar": [SearchResult(...)],
        ...     "web": [SearchResult(...), SearchResult(...)],
        ... }
        >>> merged = merge_provider_results(provider_results)
        >>> len(merged)  # 중복 제거 후 개수
        4
    """
    # 모든 결과를 하나의 리스트로 병합
    all_results: list[SearchResult] = []
    for provider_name, results in provider_results.items():
        logger.debug("제공자 %s: %d개 결과", provider_name, len(results))
        all_results.extend(results)

    logger.info("총 %d개 결과 병합 중", len(all_results))

    # 중복 제거
    if deduplicate:
        all_results = deduplicate_results(all_results, priority=priority)

    # 정렬
    if rank_strategy:
        provider_priority = list(provider_results.keys())
        all_results = rank_results(
            all_results,
            strategy=rank_strategy,
            provider_priority=provider_priority,
        )

    return all_results


def filter_results(
    results: list[SearchResult],
    *,
    min_score: float | None = None,
    max_age_days: int | None = None,
    providers: list[str] | None = None,
    require_ids: list[str] | None = None,
) -> list[SearchResult]:
    """지정된 조건에 따라 검색 결과를 필터링합니다.

    Args:
        results: 검색 결과 리스트.
        min_score: 최소 점수 (이상). None이면 필터링하지 않습니다.
        max_age_days: 최대 결과 나이 (일). None이면 필터링하지 않습니다.
        providers: 포함할 제공자 리스트. None이면 모든 제공자 포함.
        require_ids: 필수 ID 타입 리스트. 지정된 ID 중 하나라도
            있어야 포함됩니다. None이면 ID 필터링하지 않습니다.

    Returns:
        필터링된 결과 리스트.

    Example:
        >>> filtered = filter_results(
        ...     results,
        ...     min_score=0.5,
        ...     providers=["arxiv", "semantic_scholar"],
        ...     require_ids=["doi", "arxiv_id"],
        ... )
    """
    filtered: list[SearchResult] = []
    now = datetime.utcnow()

    for result in results:
        # 점수 필터
        if min_score is not None and result.score < min_score:
            continue

        # 나이 필터
        if max_age_days is not None:
            age_days = (now - result.fetched_at).days
            if age_days > max_age_days:
                continue

        # 제공자 필터
        if providers is not None and result.provider not in providers:
            continue

        # ID 필터
        if require_ids is not None:
            has_required_id = any(
                id_type in result.ids and result.ids[id_type]
                for id_type in require_ids
            )
            if not has_required_id:
                continue

        filtered.append(result)

    logger.debug(
        "결과 필터링: %d -> %d개",
        len(results),
        len(filtered),
    )

    return filtered


def group_by_query(
    results: list[SearchResult],
) -> dict[str, list[SearchResult]]:
    """검색 결과를 쿼리별로 그룹화합니다.

    Args:
        results: 검색 결과 리스트.

    Returns:
        쿼리를 키로, 해당 쿼리의 결과 리스트를 값으로 하는 딕셔너리.

    Example:
        >>> grouped = group_by_query(results)
        >>> grouped["transformer attention"]
        [SearchResult(...), SearchResult(...)]
    """
    grouped: dict[str, list[SearchResult]] = {}

    for result in results:
        if result.query not in grouped:
            grouped[result.query] = []
        grouped[result.query].append(result)

    return grouped


def get_statistics(results: list[SearchResult]) -> dict:
    """검색 결과의 통계 정보를 계산합니다.

    Args:
        results: 검색 결과 리스트.

    Returns:
        통계 정보 딕셔너리:
        - total: 총 결과 수
        - by_provider: 제공자별 결과 수
        - avg_score: 평균 점수
        - score_range: (최소 점수, 최대 점수)
        - with_doi: DOI가 있는 결과 수
        - with_arxiv_id: arXiv ID가 있는 결과 수

    Example:
        >>> stats = get_statistics(results)
        >>> print(f"총 {stats['total']}개 결과, 평균 점수: {stats['avg_score']:.2f}")
    """
    if not results:
        return {
            "total": 0,
            "by_provider": {},
            "avg_score": 0.0,
            "score_range": (0.0, 0.0),
            "with_doi": 0,
            "with_arxiv_id": 0,
        }

    by_provider: dict[str, int] = {}
    scores: list[float] = []
    with_doi = 0
    with_arxiv_id = 0

    for result in results:
        by_provider[result.provider] = by_provider.get(result.provider, 0) + 1
        scores.append(result.score)

        if "doi" in result.ids and result.ids["doi"]:
            with_doi += 1
        if "arxiv_id" in result.ids and result.ids["arxiv_id"]:
            with_arxiv_id += 1

    return {
        "total": len(results),
        "by_provider": by_provider,
        "avg_score": sum(scores) / len(scores),
        "score_range": (min(scores), max(scores)),
        "with_doi": with_doi,
        "with_arxiv_id": with_arxiv_id,
    }


__all__ = [
    "deduplicate_results",
    "filter_results",
    "get_statistics",
    "group_by_query",
    "merge_provider_results",
    "rank_results",
]
