"""Citation Tracer - 리포트 생성 모듈.

이 모듈은 인용 그래프 분석 결과를 다양한 형식으로 출력합니다:
- JSON 형식: 기계 가독성, 후처리 용이
- Markdown 형식: 사람이 읽기 쉬운 리포트, 시각화 포함

Example:
    >>> from citation_tracer.reporter import generate_markdown_report
    >>> from citation_tracer.graph import CitationGraph
    >>> 
    >>> graph = CitationGraph()
    >>> # ... 그래프 구성 ...
    >>> generate_markdown_report(graph, seed_info, "lineage_report.md")

Author: citation-tracer agent
Created: 2026-01-15
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Sequence, Union

logger = logging.getLogger(__name__)


# =============================================================================
# 타입 정의 (Protocol을 사용한 덕 타이핑)
# =============================================================================


class PaperLike(Protocol):
    """논문 정보 프로토콜.
    
    CitationGraph의 노드에서 논문 정보를 추출할 때 사용합니다.
    """
    
    paper_id: str
    title: str
    authors: List[str]
    year: Optional[int]
    citation_count: int
    influential_citation_count: int
    abstract: str
    external_ids: Dict[str, str]


class CitationNodeLike(Protocol):
    """인용 노드 프로토콜.
    
    CitationGraph의 노드 타입 힌트에 사용합니다.
    """
    
    canonical_id: str
    paper: PaperLike
    depth: int
    relevance_score: float
    is_foundation: bool


class CitationEdgeLike(Protocol):
    """인용 엣지 프로토콜.
    
    CitationGraph의 엣지 타입 힌트에 사용합니다.
    """
    
    source_id: str
    target_id: str
    edge_type: str


class CitationGraphLike(Protocol):
    """인용 그래프 프로토콜.
    
    리포터 함수에서 받는 그래프 객체의 최소 인터페이스입니다.
    """
    
    nodes: Dict[str, CitationNodeLike]
    edges: List[CitationEdgeLike]
    
    def get_foundation_candidates(self, min_depth: int = 2) -> List[CitationNodeLike]:
        """Foundation candidate 노드를 반환합니다."""
        ...
    
    def to_dict(self) -> Dict[str, Any]:
        """그래프를 딕셔너리로 직렬화합니다."""
        ...


# =============================================================================
# JSON 리포트 생성
# =============================================================================


def generate_json_report(
    graph: CitationGraphLike,
    output_path: Union[str, Path],
    *,
    indent: int = 2,
    include_abstracts: bool = False,
    metadata: Optional[Dict[str, Any]] = None,
) -> Path:
    """인용 그래프를 JSON 형식으로 저장합니다.
    
    그래프 구조를 JSON 파일로 직렬화하여 저장합니다.
    후속 분석이나 시각화 도구에서 활용할 수 있습니다.
    
    Args:
        graph: 저장할 인용 그래프 객체.
        output_path: 출력 파일 경로 (문자열 또는 Path 객체).
        indent: JSON 들여쓰기 크기 (기본값: 2).
        include_abstracts: 초록 포함 여부 (기본값: False, 파일 크기 절감).
        metadata: 추가 메타데이터 딕셔너리 (선택).
    
    Returns:
        저장된 파일의 Path 객체.
    
    Raises:
        OSError: 파일 쓰기 실패 시.
        TypeError: 직렬화 불가능한 데이터 포함 시.
    
    Example:
        >>> graph = CitationGraph()
        >>> # ... 그래프 구성 ...
        >>> path = generate_json_report(graph, "results/lineage.json")
        >>> print(f"저장 완료: {path}")
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 기본 그래프 데이터
    data = graph.to_dict()
    
    # 상세 노드 정보 추가
    detailed_nodes: List[Dict[str, Any]] = []
    for node in graph.nodes.values():
        node_data: Dict[str, Any] = {
            "canonical_id": node.canonical_id,
            "paper_id": node.paper.paper_id,
            "title": node.paper.title,
            "authors": [
                author if isinstance(author, str) else getattr(author, "name", str(author))
                for author in node.paper.authors
            ],
            "year": node.paper.year,
            "citation_count": node.paper.citation_count,
            "influential_citation_count": node.paper.influential_citation_count,
            "external_ids": node.paper.external_ids,
            "depth": node.depth,
            "relevance_score": round(node.relevance_score, 4),
            "is_foundation": node.is_foundation,
        }
        
        if include_abstracts and node.paper.abstract:
            node_data["abstract"] = node.paper.abstract
            
        detailed_nodes.append(node_data)
    
    # 관련성 점수 기준 정렬
    detailed_nodes.sort(key=lambda n: (-n["relevance_score"], n["depth"]))
    
    # 최종 출력 데이터 구성
    output_data: Dict[str, Any] = {
        "version": "1.0.0",
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_nodes": len(graph.nodes),
            "total_edges": len(graph.edges),
            "max_depth": max((n.depth for n in graph.nodes.values()), default=0),
            "foundation_candidates": len(graph.get_foundation_candidates()),
        },
        "nodes": detailed_nodes,
        "edges": [
            {
                "source": edge.source_id,
                "target": edge.target_id,
                "type": edge.edge_type,
            }
            for edge in graph.edges
        ],
    }
    
    # 사용자 메타데이터 추가
    if metadata:
        output_data["metadata"] = metadata
    
    # JSON 파일 저장
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=indent)
    
    logger.info(f"JSON 리포트 저장 완료: {output_path} ({len(graph.nodes)}개 노드)")
    
    return output_path


# =============================================================================
# Markdown 리포트 생성
# =============================================================================


def _format_authors(authors: Sequence[Any], max_authors: int = 3) -> str:
    """저자 목록을 문자열로 포맷팅합니다.
    
    Args:
        authors: 저자 목록 (문자열 또는 name 속성을 가진 객체).
        max_authors: 표시할 최대 저자 수.
    
    Returns:
        포맷된 저자 문자열.
    """
    if not authors:
        return "Unknown"
    
    author_names: List[str] = []
    for author in authors[:max_authors]:
        if isinstance(author, str):
            author_names.append(author)
        elif hasattr(author, "name"):
            author_names.append(author.name)
        else:
            author_names.append(str(author))
    
    result = ", ".join(author_names)
    if len(authors) > max_authors:
        result += f" et al. (+{len(authors) - max_authors}명)"
    
    return result


def _format_external_link(canonical_id: str, external_ids: Dict[str, str]) -> str:
    """외부 링크를 Markdown 형식으로 생성합니다.
    
    Args:
        canonical_id: 정규 ID.
        external_ids: 외부 ID 딕셔너리.
    
    Returns:
        Markdown 링크 문자열.
    """
    # DOI 링크
    doi = external_ids.get("DOI") or external_ids.get("doi")
    if doi:
        return f"[DOI](https://doi.org/{doi})"
    
    # arXiv 링크
    arxiv = external_ids.get("ArXiv") or external_ids.get("arxiv")
    if arxiv:
        return f"[arXiv](https://arxiv.org/abs/{arxiv})"
    
    # Semantic Scholar 링크
    paper_id = external_ids.get("CorpusId") or external_ids.get("corpus_id")
    if paper_id:
        return f"[S2](https://www.semanticscholar.org/paper/{paper_id})"
    
    # canonical_id에서 추출 시도
    if canonical_id.startswith("doi:"):
        return f"[DOI](https://doi.org/{canonical_id[4:]})"
    elif canonical_id.startswith("arxiv:"):
        return f"[arXiv](https://arxiv.org/abs/{canonical_id[6:]})"
    elif canonical_id.startswith("corpus_id:"):
        return f"[S2](https://www.semanticscholar.org/paper/{canonical_id[10:]})"
    
    return ""


def _generate_timeline_section(
    nodes: Sequence[CitationNodeLike],
) -> str:
    """연도별 타임라인 섹션을 생성합니다.
    
    Args:
        nodes: 노드 목록.
    
    Returns:
        Markdown 형식의 타임라인 섹션.
    """
    # 연도별 그룹화
    by_year: Dict[int, List[CitationNodeLike]] = defaultdict(list)
    unknown_year: List[CitationNodeLike] = []
    
    for node in nodes:
        year = node.paper.year
        if year is not None:
            by_year[year].append(node)
        else:
            unknown_year.append(node)
    
    if not by_year and not unknown_year:
        return "타임라인 정보가 없습니다.\n"
    
    lines: List[str] = []
    
    # 연도순 정렬 (오래된 것부터)
    for year in sorted(by_year.keys()):
        year_nodes = sorted(by_year[year], key=lambda n: -n.relevance_score)
        lines.append(f"\n### {year}년\n")
        
        for node in year_nodes[:5]:  # 연도당 최대 5개
            link = _format_external_link(node.canonical_id, node.paper.external_ids)
            foundation_badge = " 🏛️" if node.is_foundation else ""
            score = f"[{node.relevance_score:.2f}]"
            
            lines.append(
                f"- **{node.paper.title}**{foundation_badge} {score}\n"
                f"  - {_format_authors(node.paper.authors)} | "
                f"인용: {node.paper.citation_count:,} {link}\n"
            )
        
        if len(year_nodes) > 5:
            lines.append(f"  - ... +{len(year_nodes) - 5}개 논문\n")
    
    # 연도 미상
    if unknown_year:
        lines.append("\n### 연도 미상\n")
        for node in unknown_year[:3]:
            lines.append(f"- {node.paper.title}\n")
    
    return "".join(lines)


def _generate_contributions_section(
    nodes: Sequence[CitationNodeLike],
    top_k: int = 10,
) -> str:
    """주요 기여 논문 섹션을 생성합니다.
    
    Args:
        nodes: 노드 목록.
        top_k: 표시할 상위 논문 수.
    
    Returns:
        Markdown 형식의 주요 기여 섹션.
    """
    # 관련성 점수 기준 상위 논문
    sorted_nodes = sorted(nodes, key=lambda n: -n.relevance_score)[:top_k]
    
    if not sorted_nodes:
        return "주요 기여 논문 정보가 없습니다.\n"
    
    lines: List[str] = []
    
    for i, node in enumerate(sorted_nodes, 1):
        paper = node.paper
        link = _format_external_link(node.canonical_id, paper.external_ids)
        foundation_badge = " 🏛️" if node.is_foundation else ""
        
        lines.append(f"\n#### {i}. {paper.title}{foundation_badge}\n")
        lines.append(f"- **저자**: {_format_authors(paper.authors)}\n")
        lines.append(f"- **연도**: {paper.year or 'N/A'}\n")
        lines.append(f"- **인용 수**: {paper.citation_count:,}")
        
        if paper.influential_citation_count > 0:
            lines.append(f" (영향력 있는 인용: {paper.influential_citation_count:,})")
        
        lines.append(f"\n- **관련성 점수**: {node.relevance_score:.4f}\n")
        lines.append(f"- **탐색 깊이**: {node.depth}\n")
        
        if link:
            lines.append(f"- **링크**: {link}\n")
        
        # 초록 (있는 경우, 처음 200자)
        if paper.abstract:
            abstract_preview = paper.abstract[:200]
            if len(paper.abstract) > 200:
                abstract_preview += "..."
            lines.append(f"\n  > {abstract_preview}\n")
    
    return "".join(lines)


def _generate_foundation_section(
    graph: CitationGraphLike,
    min_depth: int = 2,
) -> str:
    """Foundation candidate 섹션을 생성합니다.
    
    Args:
        graph: 인용 그래프.
        min_depth: 최소 깊이 기준.
    
    Returns:
        Markdown 형식의 Foundation 섹션.
    """
    candidates = graph.get_foundation_candidates(min_depth=min_depth)
    
    if not candidates:
        return (
            "현재 탐색 깊이에서 Foundation candidate가 발견되지 않았습니다.\n"
            "`max_depth`를 늘려 더 깊은 계보를 탐색해 보세요.\n"
        )
    
    lines: List[str] = [
        f"총 **{len(candidates)}개**의 Foundation candidate를 발견했습니다.\n\n"
    ]
    
    # 상위 10개만 표시
    for i, node in enumerate(candidates[:10], 1):
        paper = node.paper
        link = _format_external_link(node.canonical_id, paper.external_ids)
        
        lines.append(
            f"{i}. **{paper.title}** ({paper.year or 'N/A'})\n"
            f"   - 저자: {_format_authors(paper.authors, max_authors=2)}\n"
            f"   - 인용 수: {paper.citation_count:,} | 깊이: {node.depth} | "
            f"점수: {node.relevance_score:.3f} {link}\n"
        )
    
    if len(candidates) > 10:
        lines.append(f"\n... +{len(candidates) - 10}개 추가 Foundation candidates\n")
    
    return "".join(lines)


def _generate_citation_paths_section(
    graph: CitationGraphLike,
    max_paths: int = 5,
) -> str:
    """인용 경로 시각화 섹션을 생성합니다.
    
    Args:
        graph: 인용 그래프.
        max_paths: 표시할 최대 경로 수.
    
    Returns:
        Markdown 형식의 경로 시각화 섹션.
    """
    if not graph.edges:
        return "인용 경로 정보가 없습니다.\n"
    
    # 깊이별 노드 그룹화
    by_depth: Dict[int, List[CitationNodeLike]] = defaultdict(list)
    for node in graph.nodes.values():
        by_depth[node.depth].append(node)
    
    if not by_depth:
        return "경로 시각화를 위한 노드가 없습니다.\n"
    
    lines: List[str] = []
    
    # 트리 구조 시각화 (Mermaid 다이어그램)
    lines.append("```mermaid\ngraph TD\n")
    
    # 샘플 경로 추출 (상위 관련성 점수 기준)
    path_count = 0
    displayed_nodes: set[str] = set()
    
    for edge in graph.edges:
        if path_count >= max_paths * 3:  # 경로당 평균 3개 엣지 가정
            break
        
        source = graph.nodes.get(edge.source_id)
        target = graph.nodes.get(edge.target_id)
        
        if source and target:
            # 노드 ID 정리 (Mermaid 호환)
            source_id = source.canonical_id.replace(":", "_").replace(".", "_")[:20]
            target_id = target.canonical_id.replace(":", "_").replace(".", "_")[:20]
            
            # 노드 라벨 (짧은 제목)
            source_label = source.paper.title[:30].replace('"', "'")
            target_label = target.paper.title[:30].replace('"', "'")
            
            if source.canonical_id not in displayed_nodes:
                lines.append(f'    {source_id}["{source_label}..."]\n')
                displayed_nodes.add(source.canonical_id)
            
            if target.canonical_id not in displayed_nodes:
                lines.append(f'    {target_id}["{target_label}..."]\n')
                displayed_nodes.add(target.canonical_id)
            
            arrow = "-->" if edge.edge_type == "cites" else "-.->|cited by|"
            lines.append(f"    {source_id} {arrow} {target_id}\n")
            path_count += 1
    
    lines.append("```\n")
    
    # 텍스트 기반 경로 요약
    lines.append("\n**주요 인용 체인:**\n\n")
    
    # 깊이별 대표 논문으로 경로 구성
    max_depth = max(by_depth.keys()) if by_depth else 0
    
    for depth in range(min(max_depth + 1, 4)):  # 최대 깊이 4까지
        if depth in by_depth:
            top_node = max(by_depth[depth], key=lambda n: n.relevance_score)
            prefix = "  " * depth
            arrow = "└─" if depth > 0 else "●"
            year_str = f"({top_node.paper.year})" if top_node.paper.year else ""
            
            lines.append(
                f"{prefix}{arrow} **{top_node.paper.title[:50]}...** {year_str}\n"
            )
    
    return "".join(lines)


def generate_markdown_report(
    graph: CitationGraphLike,
    seed_info: Dict[str, Any],
    output_path: Union[str, Path],
    *,
    include_mermaid: bool = True,
    top_contributions: int = 10,
    foundation_min_depth: int = 2,
) -> Path:
    """인용 그래프를 Markdown 리포트로 생성합니다.
    
    사람이 읽기 쉬운 형식의 Lineage 리포트를 생성합니다.
    타임라인, 주요 기여, Foundation candidates, 인용 경로 시각화를 포함합니다.
    
    Args:
        graph: 분석된 인용 그래프 객체.
        seed_info: 시드 논문 정보 딕셔너리. 필수 키:
            - title: 논문 제목
            - authors: 저자 목록
            - year: 출판 연도
            선택 키:
            - abstract: 초록
            - canonical_id: 정규 ID
            - external_ids: 외부 ID 딕셔너리
        output_path: 출력 파일 경로.
        include_mermaid: Mermaid 다이어그램 포함 여부 (기본값: True).
        top_contributions: 주요 기여 섹션에 표시할 논문 수 (기본값: 10).
        foundation_min_depth: Foundation candidate 최소 깊이 (기본값: 2).
    
    Returns:
        저장된 파일의 Path 객체.
    
    Raises:
        OSError: 파일 쓰기 실패 시.
        KeyError: seed_info에 필수 키가 없을 때.
    
    Example:
        >>> seed_info = {
        ...     "title": "Attention Is All You Need",
        ...     "authors": ["Vaswani et al."],
        ...     "year": 2017,
        ... }
        >>> path = generate_markdown_report(graph, seed_info, "lineage.md")
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 노드 리스트 추출
    nodes = list(graph.nodes.values())
    
    # 시드 정보 추출
    seed_title = seed_info.get("title", "Unknown Paper")
    seed_authors = seed_info.get("authors", [])
    seed_year = seed_info.get("year")
    seed_abstract = seed_info.get("abstract", "")
    seed_external_ids = seed_info.get("external_ids", {})
    seed_canonical_id = seed_info.get("canonical_id", "")
    
    # 통계 계산
    years = [n.paper.year for n in nodes if n.paper.year is not None]
    min_year = min(years) if years else None
    max_year = max(years) if years else None
    total_citations = sum(n.paper.citation_count for n in nodes)
    avg_relevance = sum(n.relevance_score for n in nodes) / len(nodes) if nodes else 0
    
    # 리포트 구성
    report_lines: List[str] = []
    
    # 헤더
    report_lines.append(f"# Citation Lineage Report: {seed_title}\n\n")
    report_lines.append(f"**생성일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    # 시드 논문 정보
    report_lines.append("## 📄 시드 논문 정보\n\n")
    report_lines.append(f"- **제목**: {seed_title}\n")
    report_lines.append(f"- **저자**: {_format_authors(seed_authors)}\n")
    report_lines.append(f"- **출판연도**: {seed_year or 'N/A'}\n")
    
    seed_link = _format_external_link(seed_canonical_id, seed_external_ids)
    if seed_link:
        report_lines.append(f"- **링크**: {seed_link}\n")
    
    if seed_abstract:
        report_lines.append(f"\n> {seed_abstract[:300]}{'...' if len(seed_abstract) > 300 else ''}\n")
    
    report_lines.append("\n---\n\n")
    
    # 요약 통계
    report_lines.append("## 📊 분석 요약\n\n")
    report_lines.append("| 항목 | 값 |\n")
    report_lines.append("|------|----|\n")
    report_lines.append(f"| 총 논문 수 | {len(nodes):,} |\n")
    report_lines.append(f"| 총 인용 관계 | {len(graph.edges):,} |\n")
    report_lines.append(f"| 최대 탐색 깊이 | {max((n.depth for n in nodes), default=0)} |\n")
    report_lines.append(f"| Foundation Candidates | {len(graph.get_foundation_candidates(foundation_min_depth))} |\n")
    report_lines.append(f"| 연도 범위 | {min_year or 'N/A'} ~ {max_year or 'N/A'} |\n")
    report_lines.append(f"| 총 인용 수 합계 | {total_citations:,} |\n")
    report_lines.append(f"| 평균 관련성 점수 | {avg_relevance:.4f} |\n")
    report_lines.append("\n---\n\n")
    
    # 타임라인 섹션
    report_lines.append("## 📅 타임라인 (연도별 논문)\n")
    report_lines.append(_generate_timeline_section(nodes))
    report_lines.append("\n---\n\n")
    
    # 주요 기여 섹션
    report_lines.append("## 🏆 주요 기여 논문\n")
    report_lines.append(
        f"관련성 점수 기준 상위 {top_contributions}개 논문입니다.\n"
    )
    report_lines.append(_generate_contributions_section(nodes, top_k=top_contributions))
    report_lines.append("\n---\n\n")
    
    # Foundation Candidates 섹션
    report_lines.append("## 🏛️ Foundation Candidates\n\n")
    report_lines.append(
        "Foundation candidate는 현재 연구의 근본적인 기반이 되는 논문입니다.\n"
        f"깊이 {foundation_min_depth} 이상에서 발견된 영향력 있는 논문들입니다.\n\n"
    )
    report_lines.append(_generate_foundation_section(graph, min_depth=foundation_min_depth))
    report_lines.append("\n---\n\n")
    
    # 인용 경로 시각화 섹션
    report_lines.append("## 🔗 인용 경로 시각화\n\n")
    if include_mermaid:
        report_lines.append(_generate_citation_paths_section(graph))
    else:
        report_lines.append("(Mermaid 다이어그램 비활성화됨)\n")
    
    report_lines.append("\n---\n\n")
    
    # 푸터
    report_lines.append("## 📝 노트\n\n")
    report_lines.append("- 🏛️ 아이콘은 Foundation candidate를 나타냅니다.\n")
    report_lines.append("- 관련성 점수는 의미적 유사도, 인용 영향력, 기초 가중치의 조합입니다.\n")
    report_lines.append("- 이 리포트는 Citation Tracer v1.0.0으로 생성되었습니다.\n")
    
    # 파일 저장
    report_content = "".join(report_lines)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    
    logger.info(
        f"Markdown 리포트 저장 완료: {output_path} "
        f"({len(nodes)}개 노드, {len(report_content):,} 바이트)"
    )
    
    return output_path


# =============================================================================
# 편의 함수
# =============================================================================


def generate_reports(
    graph: CitationGraphLike,
    seed_info: Dict[str, Any],
    output_dir: Union[str, Path],
    base_name: str = "lineage",
) -> Dict[str, Path]:
    """JSON과 Markdown 리포트를 동시에 생성합니다.
    
    Args:
        graph: 분석된 인용 그래프.
        seed_info: 시드 논문 정보.
        output_dir: 출력 디렉토리.
        base_name: 기본 파일명 (확장자 제외).
    
    Returns:
        생성된 파일 경로 딕셔너리 {"json": Path, "markdown": Path}.
    
    Example:
        >>> paths = generate_reports(graph, seed_info, "results/")
        >>> print(f"JSON: {paths['json']}")
        >>> print(f"Markdown: {paths['markdown']}")
    """
    output_dir = Path(output_dir)
    
    json_path = generate_json_report(
        graph,
        output_dir / f"{base_name}.json",
        metadata={"seed": seed_info},
    )
    
    md_path = generate_markdown_report(
        graph,
        seed_info,
        output_dir / f"{base_name}.md",
    )
    
    return {
        "json": json_path,
        "markdown": md_path,
    }
