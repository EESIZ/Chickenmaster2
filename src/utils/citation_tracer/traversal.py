"""Citation Tracer - 인용 그래프 탐색 모듈.

BFS(Breadth-First Search) 기반으로 논문 인용 관계를 탐색하고,
관련성 점수 기반 가지치기를 통해 효율적인 그래프 구축을 수행한다.

Example:
    >>> import asyncio
    >>> from citation_tracer.traversal import CitationTraverser, TraversalConfig
    >>>
    >>> async def main():
    ...     config = TraversalConfig(max_depth=3, branching_factor=5)
    ...     traverser = CitationTraverser(config)
    ...     graph = await traverser.traverse("arxiv:2401.12345", "transformer attention")
    ...     print(f"탐색된 논문 수: {len(graph)}")
    >>>
    >>> asyncio.run(main())

Author: citation-tracer agent
Created: 2026-01-15
"""

from __future__ import annotations

import asyncio
import logging
import math
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from .fetcher import (
    RateLimiter,
    canonicalize_paper_id,
    fetch_paper_metadata,
    fetch_references,
    get_rate_limiter,
)
from .graph import CitationGraph, PaperNode

logger = logging.getLogger(__name__)


@dataclass
class TraversalConfig:
    """인용 그래프 탐색 설정.

    탐색의 깊이, 너비, 관련성 임계값 등을 제어하여
    효율적인 그래프 구축을 지원한다.

    Attributes:
        max_depth: 최대 탐색 깊이. seed 논문이 깊이 0, seed가 인용한 논문이 깊이 1.
            값이 클수록 더 오래된 기반 논문까지 탐색 (기본값: 4).
        branching_factor: 각 노드에서 탐색할 최대 참조 문헌 수.
            관련성 점수 상위 N개 논문만 확장 (기본값: 3).
        min_relevance_score: 탐색을 계속할 최소 관련성 점수 (0.0~1.0).
            이 점수 미만인 논문은 탐색하지 않음 (기본값: 0.35).
        max_nodes: 그래프에 포함할 최대 노드 수.
            메모리 및 API 호출 제한용 (기본값: 121).
        scoring_weights: 관련성 점수 계산에 사용할 가중치.
            - similarity: 쿼리와의 의미적 유사도 (기본값: 0.5)
            - influence: 영향력 기반 점수 (기본값: 0.3)
            - foundation: 기반 논문 가능성 점수 (기본값: 0.2)

    Example:
        >>> config = TraversalConfig(
        ...     max_depth=3,
        ...     branching_factor=5,
        ...     min_relevance_score=0.4
        ... )
    """

    max_depth: int = 4
    branching_factor: int = 3
    min_relevance_score: float = 0.35
    max_nodes: int = 121
    scoring_weights: Dict[str, float] = field(
        default_factory=lambda: {"similarity": 0.5, "influence": 0.3, "foundation": 0.2}
    )

    def __post_init__(self) -> None:
        """설정 값 유효성 검증."""
        if self.max_depth < 1:
            raise ValueError(f"max_depth는 1 이상이어야 합니다: {self.max_depth}")
        if self.branching_factor < 1:
            raise ValueError(f"branching_factor는 1 이상이어야 합니다: {self.branching_factor}")
        if not 0.0 <= self.min_relevance_score <= 1.0:
            raise ValueError(
                f"min_relevance_score는 0.0~1.0 범위여야 합니다: {self.min_relevance_score}"
            )
        if self.max_nodes < 1:
            raise ValueError(f"max_nodes는 1 이상이어야 합니다: {self.max_nodes}")

        # scoring_weights 합계 검증
        weight_sum = sum(self.scoring_weights.values())
        if not math.isclose(weight_sum, 1.0, rel_tol=1e-5):
            logger.warning(
                f"scoring_weights 합계가 1.0이 아닙니다 ({weight_sum:.3f}). "
                "점수 계산 결과가 예상과 다를 수 있습니다."
            )


class CitationTraverser:
    """인용 그래프 탐색기.

    BFS(너비 우선 탐색)를 사용하여 seed 논문에서 시작하여
    참조 문헌을 따라 탐색하고, 관련성 점수를 기반으로 가지치기를 수행한다.

    Attributes:
        config: 탐색 설정 (TraversalConfig).
        _rate_limiter: API 호출 빈도 제한기.
        _seed_query: 현재 탐색의 seed 쿼리 (유사도 계산용).
        _visited: 이미 방문한 논문 ID 집합.

    Example:
        >>> traverser = CitationTraverser(TraversalConfig())
        >>> graph = await traverser.traverse("arxiv:2401.12345", "attention mechanism")
        >>> print(f"노드 수: {len(graph)}")
        >>> for candidate in graph.get_foundation_candidates()[:5]:
        ...     print(f"  - {candidate.title}")
    """

    def __init__(
        self,
        config: Optional[TraversalConfig] = None,
        rate_limiter: Optional[RateLimiter] = None,
    ) -> None:
        """탐색기 초기화.

        Args:
            config: 탐색 설정. None이면 기본값 사용.
            rate_limiter: API 호출 빈도 제한기. None이면 새로 생성.
        """
        self.config = config or TraversalConfig()
        self._rate_limiter = rate_limiter or get_rate_limiter(min_delay_s=3.0)
        self._seed_query: str = ""
        self._visited: Set[str] = set()

    async def traverse(self, seed_paper_id: str, seed_query: str) -> CitationGraph:
        """seed 논문에서 시작하여 인용 그래프를 구축한다.

        BFS로 참조 문헌을 탐색하면서 관련성 점수가 높은 논문만 선택적으로 확장한다.
        max_depth, max_nodes 제한에 도달하거나 더 이상 확장할 노드가 없으면 종료한다.

        Args:
            seed_paper_id: 탐색 시작 논문 ID.
                지원 형식: "arxiv:xxxx", "doi:xxxx", "corpus_id:xxxx"
            seed_query: 관련성 계산에 사용할 쿼리 문자열.
                논문 제목/초록과의 유사도 계산에 활용.

        Returns:
            구축된 CitationGraph. 노드와 인용 관계 엣지를 포함.

        Raises:
            httpx.HTTPStatusError: API 요청 실패.
            ValueError: 유효하지 않은 seed_paper_id.

        Example:
            >>> graph = await traverser.traverse(
            ...     "arxiv:1706.03762",
            ...     "transformer self-attention mechanism"
            ... )
            >>> print(f"탐색 완료: {len(graph)} 논문")
        """
        logger.info(f"인용 그래프 탐색 시작: {seed_paper_id}, 쿼리: '{seed_query[:50]}...'")

        # 상태 초기화
        self._seed_query = seed_query.lower()
        self._visited.clear()

        graph = CitationGraph()

        # BFS 큐: (paper_id, depth, parent_id)
        queue: deque[tuple[str, int, Optional[str]]] = deque()

        # Seed 논문 처리
        try:
            seed_metadata = await fetch_paper_metadata(
                seed_paper_id, rate_limiter=self._rate_limiter
            )
            seed_canonical_id = canonicalize_paper_id(seed_metadata)
        except Exception as e:
            logger.error(f"Seed 논문 메타데이터 수집 실패: {seed_paper_id} - {e}")
            raise

        # Seed 노드 생성 및 추가
        seed_node = self._create_paper_node(seed_metadata, depth=0, parent_id=None)
        seed_node.score = 1.0  # Seed 논문은 최대 점수
        graph.add_node(seed_node)
        self._visited.add(seed_canonical_id)

        # BFS 시작
        queue.append((seed_canonical_id, 0, None))

        while queue and len(graph) < self.config.max_nodes:
            current_id, current_depth, parent_id = queue.popleft()

            # 최대 깊이 도달 시 탐색 중단
            if current_depth >= self.config.max_depth:
                continue

            # 현재 노드의 참조 문헌 수집
            try:
                references = await fetch_references(
                    current_id,
                    rate_limiter=self._rate_limiter,
                    limit=self.config.branching_factor * 3,  # 여유 있게 수집 후 필터링
                )
            except Exception as e:
                logger.warning(f"참조 문헌 수집 실패: {current_id} - {e}")
                continue

            # 관련성 점수 계산 및 정렬
            scored_refs: List[tuple[Dict[str, Any], float]] = []
            for ref in references:
                try:
                    ref_id = canonicalize_paper_id(ref)
                    if ref_id in self._visited:
                        continue

                    score = self._calculate_relevance_score(ref, current_depth + 1)
                    if score >= self.config.min_relevance_score:
                        scored_refs.append((ref, score))
                except (ValueError, KeyError) as e:
                    logger.debug(f"참조 문헌 처리 스킵: {e}")
                    continue

            # 점수 기준 내림차순 정렬
            scored_refs.sort(key=lambda x: x[1], reverse=True)

            # branching_factor만큼 선택하여 그래프에 추가
            selected_count = 0
            for ref, score in scored_refs:
                if selected_count >= self.config.branching_factor:
                    break
                if len(graph) >= self.config.max_nodes:
                    break

                ref_id = canonicalize_paper_id(ref)

                # 이미 방문한 노드는 엣지만 추가
                if ref_id in self._visited:
                    graph.add_edge(current_id, ref_id)
                    continue

                # 새 노드 생성
                ref_node = self._create_paper_node(
                    ref, depth=current_depth + 1, parent_id=current_id
                )
                ref_node.score = score

                graph.add_node(ref_node)
                graph.add_edge(current_id, ref_id)
                self._visited.add(ref_id)

                # 다음 탐색을 위해 큐에 추가
                queue.append((ref_id, current_depth + 1, current_id))
                selected_count += 1

            logger.debug(
                f"깊이 {current_depth}: {current_id[:30]}... -> "
                f"{selected_count}/{len(references)} 참조 문헌 선택"
            )

        logger.info(
            f"인용 그래프 탐색 완료: {len(graph)} 노드, {len(graph.edges)} 엣지, "
            f"기반 논문 후보: {len(graph.get_foundation_candidates())}개"
        )

        return graph

    def _calculate_relevance_score(self, paper: Dict[str, Any], depth: int) -> float:
        """논문의 관련성 점수를 계산한다.

        세 가지 요소를 가중합하여 최종 점수를 산출:
        1. similarity: seed 쿼리와의 텍스트 유사도
        2. influence: 인용 수 기반 영향력
        3. foundation: 깊이 기반 기반 논문 가능성

        Args:
            paper: 논문 메타데이터 딕셔너리.
                필수 필드: title, citationCount
                선택 필드: abstract, influentialCitationCount
            depth: 현재 탐색 깊이 (1 이상).

        Returns:
            0.0~1.0 범위의 관련성 점수.

        Example:
            >>> score = traverser._calculate_relevance_score(
            ...     {"title": "Attention Is All You Need", "citationCount": 50000},
            ...     depth=1
            ... )
            >>> print(f"관련성 점수: {score:.3f}")
        """
        weights = self.config.scoring_weights

        # 1. 텍스트 유사도 계산 (간단한 키워드 매칭)
        similarity_score = self._compute_text_similarity(paper)

        # 2. 영향력 점수 계산
        influence_score = self._compute_influence_score(paper)

        # 3. 기반 논문 가능성 점수 (깊이가 깊을수록 기반 논문일 가능성)
        foundation_score = self._compute_foundation_score(paper, depth)

        # 가중합 계산
        total_score = (
            weights.get("similarity", 0.5) * similarity_score
            + weights.get("influence", 0.3) * influence_score
            + weights.get("foundation", 0.2) * foundation_score
        )

        return min(max(total_score, 0.0), 1.0)

    def _compute_text_similarity(self, paper: Dict[str, Any]) -> float:
        """쿼리와 논문 텍스트 간의 유사도를 계산한다.

        간단한 키워드 매칭 기반으로 유사도를 추정한다.
        제목과 초록에서 쿼리 키워드 출현 빈도를 계산.

        Args:
            paper: 논문 메타데이터.

        Returns:
            0.0~1.0 범위의 유사도 점수.
        """
        if not self._seed_query:
            return 0.5  # 쿼리 없으면 중립 점수

        # 논문 텍스트 결합 (제목 + 초록)
        title = (paper.get("title") or "").lower()
        abstract = (paper.get("abstract") or "").lower()
        paper_text = f"{title} {abstract}"

        if not paper_text.strip():
            return 0.0

        # 쿼리 토큰화 (간단한 공백 분리)
        query_tokens = set(self._seed_query.split())
        if not query_tokens:
            return 0.5

        # 매칭된 토큰 비율 계산
        matched_tokens = sum(1 for token in query_tokens if token in paper_text)
        match_ratio = matched_tokens / len(query_tokens)

        # 제목 매칭에 가중치 부여
        title_matches = sum(1 for token in query_tokens if token in title)
        title_bonus = 0.2 * (title_matches / len(query_tokens))

        return min(match_ratio + title_bonus, 1.0)

    def _compute_influence_score(self, paper: Dict[str, Any]) -> float:
        """논문의 영향력 점수를 계산한다.

        인용 수와 영향력 있는 인용 수를 기반으로 점수를 산출.
        로그 스케일을 사용하여 극단적인 인용 수 차이를 완화.

        Args:
            paper: 논문 메타데이터.

        Returns:
            0.0~1.0 범위의 영향력 점수.
        """
        citation_count = paper.get("citationCount") or 0
        influential_count = paper.get("influentialCitationCount") or 0

        # 로그 스케일 정규화 (citation_count가 10,000이면 ~1.0)
        # log10(1 + count) / log10(10001) ≈ count=10000일 때 1.0
        if citation_count > 0:
            citation_score = math.log10(1 + citation_count) / 4.0  # log10(10001) ≈ 4
            citation_score = min(citation_score, 1.0)
        else:
            citation_score = 0.0

        # 영향력 있는 인용 비율 보너스
        if citation_count > 0 and influential_count > 0:
            influential_ratio = influential_count / citation_count
            influential_bonus = 0.2 * influential_ratio
        else:
            influential_bonus = 0.0

        # isInfluential 플래그 보너스
        if paper.get("isInfluential"):
            influential_bonus += 0.1

        return min(citation_score + influential_bonus, 1.0)

    def _compute_foundation_score(self, paper: Dict[str, Any], depth: int) -> float:
        """기반 논문 가능성 점수를 계산한다.

        깊이가 깊고 출판 연도가 오래될수록 기반 논문일 가능성이 높다.

        Args:
            paper: 논문 메타데이터.
            depth: 현재 탐색 깊이.

        Returns:
            0.0~1.0 범위의 기반 논문 가능성 점수.
        """
        # 깊이 기반 점수 (깊이 4에서 최대)
        depth_score = min(depth / self.config.max_depth, 1.0)

        # 연도 기반 점수 (오래될수록 높음)
        year = paper.get("year")
        if year and isinstance(year, int):
            # 2026년 기준, 10년 이상 된 논문은 만점
            current_year = 2026
            age = current_year - year
            age_score = min(age / 10.0, 1.0)
        else:
            age_score = 0.3  # 연도 정보 없으면 중간값

        # 깊이와 연도 점수의 평균
        return (depth_score + age_score) / 2.0

    def _create_paper_node(
        self, paper: Dict[str, Any], depth: int, parent_id: Optional[str]
    ) -> PaperNode:
        """논문 메타데이터에서 PaperNode를 생성한다.

        Args:
            paper: Semantic Scholar API에서 받은 논문 메타데이터.
            depth: 탐색 깊이.
            parent_id: 부모 노드의 canonical ID.

        Returns:
            생성된 PaperNode 객체.
        """
        canonical_id = canonicalize_paper_id(paper)

        # 저자 이름 추출
        authors_data = paper.get("authors") or []
        authors = [
            a.get("name", "Unknown") for a in authors_data if isinstance(a, dict)
        ]

        # URL 생성
        external_ids = paper.get("externalIds") or {}
        if "DOI" in external_ids and external_ids["DOI"]:
            url = f"https://doi.org/{external_ids['DOI']}"
        elif "ArXiv" in external_ids and external_ids["ArXiv"]:
            url = f"https://arxiv.org/abs/{external_ids['ArXiv']}"
        else:
            paper_id = paper.get("paperId", "")
            url = f"https://www.semanticscholar.org/paper/{paper_id}" if paper_id else ""

        return PaperNode(
            canonical_id=canonical_id,
            title=paper.get("title") or "Unknown",
            year=paper.get("year"),
            authors=authors,
            citation_count=paper.get("citationCount") or 0,
            url=url,
            depth=depth,
            score=0.0,  # 이후 설정됨
            parent_id=parent_id,
        )


# ============================================================================
# 테스트용 코드
# ============================================================================

if __name__ == "__main__":
    async def _test() -> None:
        """모듈 기능 테스트."""
        logging.basicConfig(level=logging.INFO)

        print("=== TraversalConfig 테스트 ===")
        config = TraversalConfig(max_depth=2, branching_factor=2, max_nodes=10)
        print(f"  max_depth: {config.max_depth}")
        print(f"  branching_factor: {config.branching_factor}")
        print(f"  max_nodes: {config.max_nodes}")

        print("\n=== CitationTraverser 테스트 ===")
        traverser = CitationTraverser(config)

        # "Attention Is All You Need" 논문으로 테스트
        print("탐색 시작: arxiv:1706.03762 (Attention Is All You Need)")
        try:
            graph = await traverser.traverse(
                "arxiv:1706.03762",
                "transformer attention mechanism neural network"
            )
            print(f"\n탐색 결과:")
            print(f"  노드 수: {len(graph)}")
            print(f"  엣지 수: {len(graph.edges)}")

            print(f"\n  기반 논문 후보:")
            for node in graph.get_foundation_candidates()[:3]:
                print(f"    - [{node.year}] {node.title[:50]}... (점수: {node.score:.3f})")

        except Exception as e:
            print(f"테스트 실패: {e}")

        # HTTP 클라이언트 정리
        from .fetcher import close_http_client
        await close_http_client()

    asyncio.run(_test())
