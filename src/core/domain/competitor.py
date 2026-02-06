"""
경쟁자 도메인 모델

AI가 조종하는 경쟁 치킨집을 나타내는 불변 엔티티입니다.
플레이어와 경쟁하며 지연 행동 시스템을 가집니다.
"""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID
from datetime import date
from enum import Enum, auto

from .value_objects import Money


class CompetitorStrategy(Enum):
    """경쟁자 전략 유형"""
    
    AGGRESSIVE = auto()  # 공격적 전략 (가격 인하, 마케팅 강화)
    DEFENSIVE = auto()  # 방어적 전략 (품질 유지, 비용 절감)
    PRICE_AGGRESSIVE = auto() # 가격 경쟁 중심
    BALANCED = auto() # 균형 잡힌 전략


@dataclass(frozen=True)
class DelayedAction:
    """지연 실행 행동"""
    
    id: UUID
    action_type: str  # 행동 유형 (가격 변경, 마케팅 등)
    target_turn: int  # 실행될 턴
    parameters: dict  # 행동 매개변수
    
    def is_ready_to_execute(self, current_turn: int) -> bool:
        """실행 준비가 되었는지 확인"""
        return current_turn >= self.target_turn


@dataclass(frozen=True)
class Competitor:
    """경쟁자 엔티티"""
    
    id: UUID
    name: str
    strategy: CompetitorStrategy
    
    # 재정 상태
    money: Money
    
    # 소유 매장들 (ID 참조)
    store_ids: tuple[UUID, ...]
    
    # 지연 행동 큐
    delayed_actions: tuple[DelayedAction, ...]
    
    # 파산 관련
    bankrupt_since: Optional[date] = None  # 파산 시작일
    
    def __post_init__(self):
        """생성 후 유효성 검사"""
        if not self.name.strip():
            raise ValueError("경쟁자 이름은 비어있을 수 없습니다")
        
        if len(self.store_ids) == 0:
            raise ValueError("경쟁자는 최소 1개의 매장을 가져야 합니다")
    
    def spend_money(self, amount: Money) -> 'Competitor':
        """자금 사용 후 새로운 Competitor 반환"""
        new_money = self.money - amount
        return self._replace(money=new_money)
    
    def earn_money(self, amount: Money) -> 'Competitor':
        """자금 획득 후 새로운 Competitor 반환"""
        new_money = self.money + amount
        return self._replace(money=new_money)
    
    def add_delayed_action(self, action: DelayedAction) -> 'Competitor':
        """지연 행동 추가 후 새로운 Competitor 반환"""
        new_actions = self.delayed_actions + (action,)
        return self._replace(delayed_actions=new_actions)
    
    def remove_delayed_action(self, action_id: UUID) -> 'Competitor':
        """지연 행동 제거 후 새로운 Competitor 반환"""
        new_actions = tuple(
            action for action in self.delayed_actions 
            if action.id != action_id
        )
        return self._replace(delayed_actions=new_actions)
    
    def get_ready_actions(self, current_turn: int) -> list[DelayedAction]:
        """현재 턴에 실행 가능한 행동들 반환"""
        return [
            action for action in self.delayed_actions
            if action.is_ready_to_execute(current_turn)
        ]
    
    def execute_ready_actions(self, current_turn: int) -> 'Competitor':
        """실행 가능한 행동들 제거 후 새로운 Competitor 반환"""
        remaining_actions = tuple(
            action for action in self.delayed_actions
            if not action.is_ready_to_execute(current_turn)
        )
        return self._replace(delayed_actions=remaining_actions)
    
    def is_bankrupt(self) -> bool:
        """파산 상태인지 확인 (자금 0원)"""
        return self.money.is_zero()
    
    def mark_bankrupt(self, bankruptcy_date: date) -> 'Competitor':
        """파산 표시 후 새로운 Competitor 반환"""
        return self._replace(bankrupt_since=bankruptcy_date)
    
    def clear_bankruptcy(self) -> 'Competitor':
        """파산 상태 해제 후 새로운 Competitor 반환"""
        return self._replace(bankrupt_since=None)
    
    def get_bankruptcy_duration_days(self, current_date: date) -> int:
        """파산 지속 일수 계산"""
        if self.bankrupt_since is None:
            return 0
        
        return (current_date - self.bankrupt_since).days
    
    def should_be_eliminated(self, current_date: date) -> bool:
        """제거되어야 하는지 확인 (30일 파산 지속)"""
        from constants import AI_BANKRUPTCY_DAYS
        
        if self.bankrupt_since is None:
            return False
        
        return self.get_bankruptcy_duration_days(current_date) >= AI_BANKRUPTCY_DAYS
    
    def add_store(self, store_id: UUID) -> 'Competitor':
        """매장 추가 후 새로운 Competitor 반환"""
        new_store_ids = self.store_ids + (store_id,)
        return self._replace(store_ids=new_store_ids)
    
    def get_strategy_description(self) -> str:
        """전략 설명 반환"""
        strategy_descriptions = {
            CompetitorStrategy.AGGRESSIVE: "공격적 전략 - 가격 인하와 마케팅 강화로 시장 점유율 확대",
            CompetitorStrategy.DEFENSIVE: "방어적 전략 - 품질 유지와 비용 절감으로 안정적 운영"
        }
        return strategy_descriptions.get(self.strategy, "알 수 없는 전략")
    
    def _replace(self, **changes) -> 'Competitor':
        """dataclass replace 메서드 래퍼"""
        from dataclasses import replace
        return replace(self, **changes) 