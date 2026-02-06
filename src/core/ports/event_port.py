from dataclasses import dataclass
from typing import Optional, List
from abc import ABC, abstractmethod
from uuid import UUID

from core.domain.turn import Turn
from core.domain.player import Player
from core.domain.event import Event


@dataclass(frozen=True)
class EventResult:
    """이벤트 처리 결과"""
    occurred: bool
    event: Optional[Event] = None
    message: str = ""
    effects_applied: List[str] = None  # 적용된 효과 설명 목록


class EventPort(ABC):
    """이벤트 처리 포트 인터페이스"""

    @abstractmethod
    def process_daily_events(self, turn: Turn, player: Player) -> EventResult:
        """
        턴과 플레이어 상태에 따라 오늘의 이벤트를 처리합니다.
        """
        pass

    @abstractmethod
    def handle_event_choice(self, event_id: UUID, choice_index: int, player: Player) -> EventResult:
        """
        이벤트 선택지에 따른 결과를 처리합니다.
        """
        pass
