"""
플레이어 행동 처리 포트 인터페이스

플레이어의 행동 실행과 관련된 유스케이스 인터페이스를 정의합니다.
ActionService가 이 인터페이스를 구현합니다.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from uuid import UUID

from core.domain.player import Player
from common.enums.action_type import ActionType


class ActionRequest:
    """행동 요청 DTO"""
    def __init__(self, player_id: UUID, action_type: ActionType, specific_action: str, 
                 time_hours: int, target_id: Optional[UUID] = None):
        self.player_id = player_id
        self.action_type = action_type
        self.specific_action = specific_action
        self.time_hours = time_hours
        self.target_id = target_id


class ActionResult:
    """행동 결과 DTO"""
    def __init__(self, success: bool, message: str, time_consumed: int, 
                 fatigue_change: float, money_change: int, 
                 experience_gains: Dict[str, int], updated_player: Player):
        self.success = success
        self.message = message
        self.time_consumed = time_consumed
        self.fatigue_change = fatigue_change
        self.money_change = money_change
        self.experience_gains = experience_gains
        self.updated_player = updated_player


class ActionPort(ABC):
    """플레이어 행동 처리 포트 인터페이스"""
    
    @abstractmethod
    def execute_action(self, request: ActionRequest) -> ActionResult:
        """플레이어 행동을 실행합니다.
        
        Args:
            request: 행동 요청 정보
            
        Returns:
            ActionResult: 행동 실행 결과
        """
        pass
    
    @abstractmethod
    def get_available_actions(self, player_id: UUID, remaining_time: int) -> List[Dict[str, any]]:
        """플레이어가 수행 가능한 행동 목록을 반환합니다.
        
        Args:
            player_id: 플레이어 ID
            remaining_time: 남은 시간 (시간 단위)
            
        Returns:
            List[Dict]: 수행 가능한 행동 목록
        """
        pass
    
    @abstractmethod
    def validate_action(self, player_id: UUID, action_type: ActionType, 
                       specific_action: str, time_hours: int) -> tuple[bool, str]:
        """행동 유효성을 검사합니다.
        
        Args:
            player_id: 플레이어 ID
            action_type: 행동 카테고리
            specific_action: 구체적인 행동
            time_hours: 소모할 시간
            
        Returns:
            tuple[bool, str]: (유효성 여부, 메시지)
        """
        pass
    
    @abstractmethod
    def get_action_cost(self, action_type: ActionType, specific_action: str) -> int:
        """행동에 필요한 자금을 반환합니다.
        
        Args:
            action_type: 행동 카테고리
            specific_action: 구체적인 행동
            
        Returns:
            int: 필요한 자금 (원 단위)
        """
        pass
    
    @abstractmethod
    def get_action_time_cost(self, action_type: ActionType, specific_action: str) -> int:
        """행동에 필요한 시간을 반환합니다.
        
        Args:
            action_type: 행동 카테고리
            specific_action: 구체적인 행동
            
        Returns:
            int: 필요한 시간 (시간 단위)
        """
        pass 