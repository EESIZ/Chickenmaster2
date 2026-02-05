from dataclasses import dataclass
from typing import Dict, List, Any
from abc import ABC, abstractmethod
from uuid import UUID

from core.domain.player import Player
from core.domain.competitor import Competitor
from core.domain.product import Product


@dataclass(frozen=True)
class CustomerFeedback:
    """고객 피드백 (롤러코스터 타이쿤 스타일)"""
    customer_name: str
    message: str
    sentiment: str  # 'POSITIVE', 'NEGATIVE', 'NEUTRAL'
    product_name: str


@dataclass(frozen=True)
class SalesResult:
    """판매 결과 데이터"""
    total_revenue: int
    total_customers: int
    sold_products: Dict[UUID, int]  # ProductID -> 판매량
    feedbacks: List[CustomerFeedback]
    market_share: float  # 시장 점유율 (0.0 ~ 1.0)


class SalesPort(ABC):
    """판매 처리 포트 인터페이스"""

    @abstractmethod
    def calculate_daily_sales(self, players: List[Player], competitors: List[Competitor]) -> Dict[UUID, SalesResult]:
        """
        모든 참여자(플레이어 및 경쟁자)의 일일 판매량을 계산합니다.
        Returns:
            Dict[UUID, SalesResult]: 참여자 ID별 판매 결과
        """
        pass
