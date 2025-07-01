"""
기본 도메인 이벤트
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4
from abc import ABC


@dataclass(frozen=True)
class DomainEvent(ABC):
    """도메인 이벤트 기본 클래스"""
    
    event_id: UUID
    occurred_at: datetime
    aggregate_id: UUID  # 이벤트가 발생한 애그리거트 ID
    
    def __post_init__(self):
        if not self.event_id:
            object.__setattr__(self, 'event_id', uuid4())
        if not self.occurred_at:
            object.__setattr__(self, 'occurred_at', datetime.now())


@dataclass(frozen=True)
class PlayerEvent(DomainEvent):
    """플레이어 관련 이벤트 기본 클래스"""
    
    player_id: UUID
    
    def __post_init__(self):
        super().__post_init__()
        object.__setattr__(self, 'aggregate_id', self.player_id) 