"""
플레이어 DTO 정의
"""

from dataclasses import dataclass
from typing import List
from uuid import UUID


@dataclass(frozen=True)
class CreatePlayerRequest:
    """플레이어 생성 요청 DTO"""
    
    name: str
    character_preset: str  # "chef", "businessman", "service_expert"
    initial_money: int = 1000000


@dataclass(frozen=True)
class PlayerStatsDto:
    """플레이어 스탯 DTO"""
    
    cooking: int
    management: int
    service: int
    tech: int
    stamina: int


@dataclass(frozen=True)
class PlayerStatusDto:
    """플레이어 상태 DTO"""
    
    id: str
    name: str
    stats: PlayerStatsDto
    fatigue: float
    money: int
    store_count: int
    research_count: int


@dataclass(frozen=True)
class PlayerActionRequest:
    """플레이어 행동 요청 DTO"""
    
    player_id: str
    action_type: str  # "cook", "manage", "research" 등
    target_id: str = None  # 대상 ID (매장, 연구 등)
    parameters: dict = None  # 추가 매개변수 