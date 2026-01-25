"""Citation Graph 데이터 구조 모듈.

논문 인용 관계를 그래프로 표현하기 위한 자료구조를 정의한다.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class PaperNode:
    """논문 노드를 나타내는 데이터 클래스.

    Attributes:
        canonical_id: 논문의 고유 식별자 (DOI, Semantic Scholar ID 등)
        title: 논문 제목
        year: 출판 연도 (알 수 없는 경우 None)
        authors: 저자 목록
        citation_count: 피인용 횟수
        url: 논문 URL
        depth: 탐색 깊이 (seed 논문 = 0)
        score: 중요도 점수 (0.0 ~ 1.0)
        parent_id: 이 논문을 인용한 상위 논문의 ID (seed인 경우 None)
    """

    canonical_id: str
    title: str
    year: int | None = None
    authors: list[str] = field(default_factory=list)
    citation_count: int = 0
    url: str = ""
    depth: int = 0
    score: float = 0.0
    parent_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """노드를 딕셔너리로 변환한다."""
        return asdict(self)


class CitationGraph:
    """인용 관계를 표현하는 그래프 자료구조.

    논문 노드와 인용 관계 엣지를 관리한다.

    Attributes:
        nodes: 노드 ID를 키로 하는 PaperNode 딕셔너리
        edges: (인용하는 논문 ID, 인용되는 논문 ID) 튜플 리스트
    """

    def __init__(self) -> None:
        """빈 그래프를 초기화한다."""
        self.nodes: dict[str, PaperNode] = {}
        self.edges: list[tuple[str, str]] = []

    def add_node(self, node: PaperNode) -> None:
        """그래프에 노드를 추가한다.

        이미 존재하는 노드는 덮어쓴다.

        Args:
            node: 추가할 PaperNode 객체
        """
        self.nodes[node.canonical_id] = node

    def add_edge(self, from_id: str, to_id: str) -> None:
        """인용 관계 엣지를 추가한다.

        from_id 논문이 to_id 논문을 인용하는 관계를 나타낸다.

        Args:
            from_id: 인용하는 논문의 ID
            to_id: 인용되는 논문의 ID
        """
        edge = (from_id, to_id)
        if edge not in self.edges:
            self.edges.append(edge)

    def get_foundation_candidates(self) -> list[PaperNode]:
        """기반 논문 후보를 반환한다.

        깊이가 2 이상인 논문들을 기반 논문 후보로 간주한다.
        이는 여러 경로에서 반복적으로 인용되는 핵심 논문일 가능성이 높다.

        Returns:
            깊이가 2 이상인 PaperNode 리스트 (score 내림차순 정렬)
        """
        candidates = [node for node in self.nodes.values() if node.depth >= 2]
        return sorted(candidates, key=lambda n: n.score, reverse=True)

    def to_dict(self) -> dict[str, Any]:
        """그래프를 JSON 직렬화 가능한 딕셔너리로 변환한다.

        Returns:
            nodes와 edges를 포함하는 딕셔너리
        """
        return {
            "nodes": {nid: node.to_dict() for nid, node in self.nodes.items()},
            "edges": self.edges,
        }

    def __len__(self) -> int:
        """그래프의 노드 수를 반환한다."""
        return len(self.nodes)

    def __contains__(self, node_id: str) -> bool:
        """노드 ID가 그래프에 존재하는지 확인한다."""
        return node_id in self.nodes
