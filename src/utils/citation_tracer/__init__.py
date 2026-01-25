"""Citation Tracer - 학술 논문 인용 계보 추적 도구.

이 패키지는 Semantic Scholar API를 활용하여 학술 논문의 인용 관계를
분석하고 시각화하는 도구를 제공합니다.

주요 기능:
    - 논문 메타데이터 및 참조/인용 정보 비동기 수집
    - 인용 그래프 구성 및 DFS 기반 계보 탐색
    - 관련성 점수 계산 및 Foundation candidate 식별
    - JSON/Markdown 형식의 Lineage 리포트 생성

Modules:
    fetcher: 논문 메타데이터 및 참조/인용 정보 수집
    graph: 인용 그래프 자료 구조 (CitationGraph, CitationNode, CitationEdge)
    traverser: DFS 기반 계보 탐색 (CitationTraverser, TraversalConfig)
    reporter: 리포트 생성 (JSON, Markdown)

Example:
    >>> import asyncio
    >>> from citation_tracer import (
    ...     fetch_paper_metadata,
    ...     CitationGraph,
    ...     CitationTraverser,
    ...     TraversalConfig,
    ...     generate_markdown_report,
    ... )
    >>> 
    >>> async def main():
    ...     # 시드 논문 메타데이터 수집
    ...     seed = await fetch_paper_metadata("arxiv:1706.03762")
    ...     
    ...     # 그래프 탐색 설정
    ...     config = TraversalConfig(max_depth=3, max_nodes=100)
    ...     traverser = CitationTraverser(config)
    ...     
    ...     # 계보 탐색
    ...     graph = await traverser.traverse(seed)
    ...     
    ...     # 리포트 생성
    ...     generate_markdown_report(graph, seed, "lineage.md")
    >>> 
    >>> asyncio.run(main())

Author: citation-tracer agent
Created: 2026-01-15
"""

from __future__ import annotations

# =============================================================================
# Version
# =============================================================================

__version__ = "1.0.0"

# =============================================================================
# Fetcher 모듈 (API 통신)
# =============================================================================

from src.utils.citation_tracer.fetcher import (
    RateLimiter,
    canonicalize_paper_id,
    close_http_client,
    fetch_citations,
    fetch_paper_metadata,
    fetch_references,
    get_rate_limiter,
    reset_global_rate_limiter,
)

# =============================================================================
# Reporter 모듈 (리포트 생성)
# =============================================================================

from src.utils.citation_tracer.reporter import (
    generate_json_report,
    generate_markdown_report,
    generate_reports,
)

# =============================================================================
# Graph 모듈 (자료 구조) - 향후 구현 시 import 추가
# =============================================================================

# from src.utils.citation_tracer.graph import (
#     CitationGraph,
#     CitationNode,
#     CitationEdge,
#     Paper,
# )

# =============================================================================
# Traverser 모듈 (탐색 엔진) - 향후 구현 시 import 추가
# =============================================================================

# from src.utils.citation_tracer.traverser import (
#     CitationTraverser,
#     TraversalConfig,
# )

# =============================================================================
# Public API
# =============================================================================

__all__ = [
    # Version
    "__version__",
    # Fetcher
    "RateLimiter",
    "canonicalize_paper_id",
    "close_http_client",
    "fetch_citations",
    "fetch_paper_metadata",
    "fetch_references",
    "get_rate_limiter",
    "reset_global_rate_limiter",
    # Reporter
    "generate_json_report",
    "generate_markdown_report",
    "generate_reports",
    # Graph (향후 추가)
    # "CitationGraph",
    # "CitationNode",
    # "CitationEdge",
    # "Paper",
    # Traverser (향후 추가)
    # "CitationTraverser",
    # "TraversalConfig",
]
