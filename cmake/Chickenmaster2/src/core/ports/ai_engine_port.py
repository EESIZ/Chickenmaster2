"""
경쟁자 AI 엔진 포트 인터페이스

경쟁자 AI의 의사결정과 행동 큐 관리를 담당하는 인터페이스입니다.
AIService가 이 인터페이스를 구현합니다.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from uuid import UUID

from core.domain.competitor import Competitor
from core.domain.player import Player
from common.enums.action_type import ActionType


class AIDecision:
    """AI 의사결정 결과 DTO"""
    def __init__(self, competitor_id: UUID, action_type: ActionType, 
                 specific_action: str, delay_turns: int, target_id: Optional[UUID] = None):
        self.competitor_id = competitor_id
        self.action_type = action_type
        self.specific_action = specific_action
        self.delay_turns = delay_turns  # 3~10턴 지연
        self.target_id = target_id


class AIEnginePort(ABC):
    """경쟁자 AI 엔진 포트 인터페이스"""
    
    @abstractmethod
    def make_decision(self, competitor: Competitor, game_state: Dict[str, Any]) -> AIDecision:
        """경쟁자 AI의 다음 행동을 결정합니다.
        
        Args:
            competitor: 의사결정을 할 경쟁자 AI
            game_state: 현재 게임 상태 정보
            
        Returns:
            AIDecision: AI 의사결정 결과 (지연 행동 포함)
        """
        pass
    
    @abstractmethod
    def execute_delayed_actions(self, current_turn: int) -> List[Dict[str, Any]]:
        """현재 턴에 실행할 지연된 행동들을 처리합니다.
        
        Args:
            current_turn: 현재 턴 번호
            
        Returns:
            List[Dict]: 실행된 행동 결과 목록
        """
        pass
    
    @abstractmethod
    def add_delayed_action(self, decision: AIDecision, execution_turn: int) -> bool:
        """지연 행동을 큐에 추가합니다.
        
        Args:
            decision: AI 의사결정 결과
            execution_turn: 실행될 턴 번호
            
        Returns:
            bool: 추가 성공 여부
        """
        pass
    
    @abstractmethod
    def check_bankruptcy(self, competitor: Competitor) -> bool:
        """경쟁자의 파산 조건을 확인합니다.
        
        README.md 규칙: 자금 0원 상태가 30일 지속되면 파산
        
        Args:
            competitor: 확인할 경쟁자
            
        Returns:
            bool: 파산 여부
        """
        pass
    
    @abstractmethod
    def get_competitor_strategy(self, competitor: Competitor, player: Player) -> str:
        """경쟁자의 현재 전략을 분석합니다.
        
        Args:
            competitor: 분석할 경쟁자
            player: 플레이어 정보 (비교용)
            
        Returns:
            str: 전략 설명 ("공격적", "수비적", "균형적" 등)
        """
        pass
    
    @abstractmethod
    def simulate_competitor_turn(self, competitor: Competitor, 
                                game_state: Dict[str, Any]) -> Competitor:
        """경쟁자의 턴을 시뮬레이션합니다.
        
        Args:
            competitor: 시뮬레이션할 경쟁자
            game_state: 현재 게임 상태
            
        Returns:
            Competitor: 업데이트된 경쟁자 상태
        """
        pass
    
    @abstractmethod
    def get_delayed_actions_count(self, competitor_id: UUID) -> int:
        """특정 경쟁자의 대기 중인 지연 행동 수를 반환합니다.
        
        Args:
            competitor_id: 경쟁자 ID
            
        Returns:
            int: 대기 중인 행동 수
        """
        pass
    
    @abstractmethod
    def clear_competitor_actions(self, competitor_id: UUID) -> bool:
        """경쟁자의 모든 지연 행동을 제거합니다. (파산 시 사용)
        
        Args:
            competitor_id: 경쟁자 ID
            
        Returns:
            bool: 제거 성공 여부
        """
        pass 