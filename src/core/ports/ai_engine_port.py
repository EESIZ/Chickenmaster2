from dataclasses import dataclass
from typing import Optional
from abc import ABC, abstractmethod
from uuid import UUID

from common.enums.action_type import ActionType
from core.domain.competitor import Competitor


@dataclass(frozen=True)
class AIDecision:
    """AI 의사결정 결과"""
    action_type: ActionType
    target_amount: int  # 투자 금액 또는 목표 수치
    reasoning: str  # 결정 사유 (디버깅/로그용)


class AIEnginePort(ABC):
    """AI 엔진 포트 인터페이스"""

    @abstractmethod
    def get_ai_decision_based_on_analysis(self, competitor: Competitor, player_id: UUID) -> Optional[AIDecision]:
        """분석에 기반한 AI 의사결정을 반환합니다."""
        pass
