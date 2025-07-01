"""
플레이어 도메인 이벤트들
"""

from dataclasses import dataclass
from uuid import UUID
from datetime import datetime

from .base_event import PlayerEvent
from ..value_objects import Money, StatValue


@dataclass(frozen=True)
class PlayerCreatedEvent(PlayerEvent):
    """플레이어 생성 이벤트"""
    
    player_name: str
    initial_money: Money


@dataclass(frozen=True)
class PlayerMoneyChangedEvent(PlayerEvent):
    """플레이어 자금 변경 이벤트"""
    
    previous_amount: Money
    new_amount: Money
    change_reason: str  # "purchase", "sale", "event" 등


@dataclass(frozen=True)
class PlayerStatImprovedEvent(PlayerEvent):
    """플레이어 스탯 향상 이벤트"""
    
    stat_name: str  # "cooking", "management" 등
    previous_stat: StatValue
    new_stat: StatValue


@dataclass(frozen=True)
class PlayerFatigueChangedEvent(PlayerEvent):
    """플레이어 피로도 변경 이벤트"""
    
    previous_fatigue: int
    new_fatigue: int
    is_critical: bool  # 위험 수준 도달 여부


@dataclass(frozen=True)
class PlayerStoreAddedEvent(PlayerEvent):
    """플레이어 매장 추가 이벤트"""
    
    store_id: UUID
    store_name: str


@dataclass(frozen=True)
class PlayerResearchStartedEvent(PlayerEvent):
    """플레이어 연구 시작 이벤트"""
    
    research_id: UUID
    research_name: str 