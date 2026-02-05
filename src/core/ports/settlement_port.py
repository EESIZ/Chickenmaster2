from dataclasses import dataclass
from abc import ABC, abstractmethod

from core.domain.player import Player
from core.domain.value_objects import Money


@dataclass(frozen=True)
class SettlementResult:
    """정산 결과 데이터"""
    revenue: int  # 매출

    # 비용 상세
    rent_cost: int  # 임대료
    ingredient_cost: int  # 재료비
    labor_cost: int  # 인건비 (알바 + 점장)
    maintenance_cost: int  # 유지관리비

    total_cost: int  # 총 비용
    net_profit: int  # 순이익 (매출 - 비용)

    updated_player: Player  # 정산 후 플레이어 상태 (자금 등 반영)


class SettlementPort(ABC):
    """정산 처리 포트 인터페이스"""

    @abstractmethod
    def calculate_settlement(self, player: Player, revenue: int) -> SettlementResult:
        """
        플레이어의 매출과 비용을 정산합니다.
        """
        pass
