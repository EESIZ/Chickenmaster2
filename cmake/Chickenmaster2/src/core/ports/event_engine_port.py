"""
이벤트 엔진 포트 인터페이스

게임 이벤트의 발생 조건 확인, 발동, 쿨다운 관리를 담당하는 인터페이스입니다.
EventService가 이 인터페이스를 구현합니다.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from uuid import UUID

from core.domain.event import Event, EventChoice
from core.domain.player import Player
from core.domain.turn import Turn


class EventTriggerResult:
    """이벤트 발동 결과 DTO"""
    def __init__(self, event: Event, triggered: bool, reason: str = ""):
        self.event = event
        self.triggered = triggered
        self.reason = reason


class EventExecutionResult:
    """이벤트 실행 결과 DTO"""
    def __init__(self, success: bool, message: str, effects_applied: Dict[str, Any], 
                 updated_player: Optional[Player] = None):
        self.success = success
        self.message = message
        self.effects_applied = effects_applied
        self.updated_player = updated_player


class EventEnginePort(ABC):
    """이벤트 엔진 포트 인터페이스"""
    
    @abstractmethod
    def check_event_conditions(self, event: Event, player: Player, 
                              current_turn: Turn) -> bool:
        """이벤트 발생 조건을 확인합니다.
        
        Args:
            event: 확인할 이벤트
            player: 현재 플레이어 상태
            current_turn: 현재 턴 정보
            
        Returns:
            bool: 조건 만족 여부
        """
        pass
    
    @abstractmethod
    def trigger_daily_event(self, player: Player, current_turn: Turn) -> Optional[EventTriggerResult]:
        """일일 이벤트를 발동합니다.
        
        README.md 규칙: 1턴에 1개 이벤트만 발생, Calldice로 선택
        
        Args:
            player: 현재 플레이어 상태
            current_turn: 현재 턴 정보
            
        Returns:
            Optional[EventTriggerResult]: 발동된 이벤트 (없으면 None)
        """
        pass
    
    @abstractmethod
    def execute_event_choice(self, event: Event, choice: EventChoice, 
                           player: Player) -> EventExecutionResult:
        """플레이어의 이벤트 선택을 실행합니다.
        
        Args:
            event: 실행할 이벤트
            choice: 플레이어가 선택한 선택지
            player: 현재 플레이어 상태
            
        Returns:
            EventExecutionResult: 실행 결과
        """
        pass
    
    @abstractmethod
    def check_reserved_events(self, current_turn: Turn) -> List[Event]:
        """예약된 이벤트들을 확인합니다.
        
        Args:
            current_turn: 현재 턴 정보
            
        Returns:
            List[Event]: 현재 턴에 발동될 예약 이벤트 목록
        """
        pass
    
    @abstractmethod
    def add_event_cooldown(self, event_id: str, cooldown_turns: int) -> bool:
        """이벤트에 쿨다운을 추가합니다.
        
        Args:
            event_id: 이벤트 ID
            cooldown_turns: 쿨다운 턴 수
            
        Returns:
            bool: 추가 성공 여부
        """
        pass
    
    @abstractmethod
    def is_event_on_cooldown(self, event_id: str, current_turn: int) -> bool:
        """이벤트가 쿨다운 중인지 확인합니다.
        
        Args:
            event_id: 이벤트 ID
            current_turn: 현재 턴 번호
            
        Returns:
            bool: 쿨다운 중 여부
        """
        pass
    
    @abstractmethod
    def get_available_events(self, player: Player, current_turn: Turn) -> List[Event]:
        """현재 발생 가능한 이벤트 목록을 반환합니다.
        
        조건을 만족하고 쿨다운이 아닌 이벤트들을 필터링합니다.
        
        Args:
            player: 현재 플레이어 상태
            current_turn: 현재 턴 정보
            
        Returns:
            List[Event]: 발생 가능한 이벤트 목록
        """
        pass
    
    @abstractmethod
    def reserve_event(self, event: Event, trigger_turn: int) -> bool:
        """이벤트를 특정 턴에 예약합니다.
        
        Args:
            event: 예약할 이벤트
            trigger_turn: 발동할 턴 번호
            
        Returns:
            bool: 예약 성공 여부
        """
        pass
    
    @abstractmethod
    def calculate_event_probability(self, event: Event, player: Player) -> float:
        """이벤트 발생 확률을 계산합니다.
        
        Args:
            event: 확률을 계산할 이벤트
            player: 현재 플레이어 상태
            
        Returns:
            float: 발생 확률 (0.0 ~ 1.0)
        """
        pass
    
    @abstractmethod
    def get_event_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """최근 발생한 이벤트 기록을 반환합니다.
        
        Args:
            limit: 반환할 최대 기록 수
            
        Returns:
            List[Dict]: 이벤트 기록 목록
        """
        pass 