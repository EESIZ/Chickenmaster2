"""
턴 도메인 모델

게임의 턴 시스템을 나타내는 불변 엔티티입니다.
1턴 = 1일이며 6개 게임 페이즈로 구성됩니다.
"""

from dataclasses import dataclass
from enum import Enum, auto
from datetime import date
from typing import Optional
from uuid import UUID


class GamePhase(Enum):
    """게임 페이즈"""
    
    PLAYER_ACTION = auto()  # 1. 플레이어 행동
    AI_ACTION = auto()  # 2. AI 행동 (경쟁자)
    EVENT = auto()  # 3. 이벤트
    SALES = auto()  # 4. 판매
    SETTLEMENT = auto()  # 5. 정산
    CLEANUP = auto()  # 6. 마무리


@dataclass(frozen=True)
class Turn:
    """턴 엔티티"""
    
    turn_number: int  # 턴 번호 (1부터 시작)
    game_date: date  # 게임 내 날짜
    current_phase: GamePhase  # 현재 페이즈
    
    # 턴 진행 상태
    is_complete: bool = False  # 턴 완료 여부
    active_event_id: Optional[UUID] = None  # 활성 이벤트 ID
    
    def __post_init__(self):
        """생성 후 유효성 검사"""
        if self.turn_number <= 0:
            raise ValueError("턴 번호는 1 이상이어야 합니다")
    
    def advance_phase(self) -> 'Turn':
        """다음 페이즈로 진행 후 새로운 Turn 반환"""
        if self.is_complete:
            raise ValueError("이미 완료된 턴입니다")
        
        phase_order = list(GamePhase)
        current_index = phase_order.index(self.current_phase)
        
        if current_index >= len(phase_order) - 1:
            # 마지막 페이즈에서 턴 완료
            return self._replace(is_complete=True)
        else:
            # 다음 페이즈로 진행
            next_phase = phase_order[current_index + 1]
            return self._replace(current_phase=next_phase)
    
    def set_active_event(self, event_id: UUID) -> 'Turn':
        """활성 이벤트 설정 후 새로운 Turn 반환"""
        return self._replace(active_event_id=event_id)
    
    def clear_active_event(self) -> 'Turn':
        """활성 이벤트 해제 후 새로운 Turn 반환"""
        return self._replace(active_event_id=None)
    
    def is_player_action_phase(self) -> bool:
        """플레이어 행동 페이즈인지 확인"""
        return self.current_phase == GamePhase.PLAYER_ACTION
    
    def is_ai_action_phase(self) -> bool:
        """AI 행동 페이즈인지 확인"""
        return self.current_phase == GamePhase.AI_ACTION
    
    def is_event_phase(self) -> bool:
        """이벤트 페이즈인지 확인"""
        return self.current_phase == GamePhase.EVENT
    
    def is_sales_phase(self) -> bool:
        """판매 페이즈인지 확인"""
        return self.current_phase == GamePhase.SALES
    
    def is_settlement_phase(self) -> bool:
        """정산 페이즈인지 확인"""
        return self.current_phase == GamePhase.SETTLEMENT
    
    def is_cleanup_phase(self) -> bool:
        """마무리 페이즈인지 확인"""
        return self.current_phase == GamePhase.CLEANUP
    
    def has_active_event(self) -> bool:
        """활성 이벤트가 있는지 확인"""
        return self.active_event_id is not None
    
    def get_phase_name(self) -> str:
        """현재 페이즈 이름 반환"""
        phase_names = {
            GamePhase.PLAYER_ACTION: "플레이어 행동",
            GamePhase.AI_ACTION: "AI 행동",
            GamePhase.EVENT: "이벤트",
            GamePhase.SALES: "판매",
            GamePhase.SETTLEMENT: "정산",
            GamePhase.CLEANUP: "마무리",
        }
        return phase_names.get(self.current_phase, "알 수 없음")
    
    def get_progress_percentage(self) -> float:
        """턴 진행률 계산 (0~100%)"""
        if self.is_complete:
            return 100.0
        
        phase_order = list(GamePhase)
        current_index = phase_order.index(self.current_phase)
        return (current_index / len(phase_order)) * 100
    
    def get_next_turn(self) -> 'Turn':
        """다음 턴 생성"""
        if not self.is_complete:
            raise ValueError("현재 턴이 완료되지 않았습니다")
        
        from datetime import timedelta
        next_date = self.game_date + timedelta(days=1)
        
        return Turn(
            turn_number=self.turn_number + 1,
            game_date=next_date,
            current_phase=GamePhase.PLAYER_ACTION,  # 첫 페이즈부터 시작
            is_complete=False,
        )
    
    def get_display_info(self) -> str:
        """턴 정보 문자열 반환"""
        status = "완료" if self.is_complete else self.get_phase_name()
        return f"턴 {self.turn_number} ({self.game_date}) - {status}"
    
    def _replace(self, **changes) -> 'Turn':
        """dataclass replace 메서드 래퍼"""
        from dataclasses import replace
        return replace(self, **changes)


@dataclass(frozen=True)
class TurnResult:
    """턴 결과 데이터"""
    
    turn: Turn
    
    # 페이즈별 결과
    player_actions: list[str]  # 플레이어가 수행한 행동들
    ai_actions: list[str]  # AI가 수행한 행동들
    event_result: Optional[str]  # 이벤트 결과
    sales_result: dict  # 판매 결과 (매출, 고객 수 등)
    settlement_result: dict  # 정산 결과 (수익, 비용 등)
    
    def get_total_revenue(self) -> int:
        """총 매출 반환"""
        return self.sales_result.get("total_revenue", 0)
    
    def get_total_cost(self) -> int:
        """총 비용 반환"""
        return self.settlement_result.get("total_cost", 0)
    
    def get_net_profit(self) -> int:
        """순수익 계산"""
        return self.get_total_revenue() - self.get_total_cost()
    
    def was_profitable(self) -> bool:
        """수익이 발생했는지 확인"""
        return self.get_net_profit() > 0


@dataclass(frozen=True)
class GameCalendar:
    """게임 달력 (턴 관리 도우미)"""
    
    start_date: date
    current_turn: Turn
    
    def __post_init__(self):
        """생성 후 유효성 검사"""
        if self.current_turn.game_date < self.start_date:
            raise ValueError("현재 게임 날짜가 시작 날짜보다 이전입니다")
    
    def get_days_elapsed(self) -> int:
        """게임 시작부터 경과한 일수"""
        return (self.current_turn.game_date - self.start_date).days
    
    def is_weekend(self) -> bool:
        """현재 날짜가 주말인지 확인 (토요일=5, 일요일=6)"""
        return self.current_turn.game_date.weekday() >= 5
    
    def is_month_end(self) -> bool:
        """현재 날짜가 월말인지 확인"""
        next_day = self.current_turn.game_date + timedelta(days=1)
        return next_day.month != self.current_turn.game_date.month
    
    def advance_turn(self) -> 'GameCalendar':
        """다음 턴으로 진행"""
        next_turn = self.current_turn.get_next_turn()
        return self._replace(current_turn=next_turn)
    
    def _replace(self, **changes) -> 'GameCalendar':
        """dataclass replace 메서드 래퍼"""
        from dataclasses import replace
        return replace(self, **changes) 