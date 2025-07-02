"""
게임 루프 응용 서비스

게임의 메인 루프를 관리하고 턴 진행을 담당합니다.
1턴 = 1일이며 6개 페이즈로 구성됩니다.
"""

from datetime import date, timedelta
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4

from core.domain.turn import Turn, GamePhase, TurnResult, GameCalendar
from core.domain.player import Player
from core.ports.repository_port import RepositoryPort


class GameLoopService:
    """게임 루프 응용 서비스"""
    
    def __init__(self, repository: RepositoryPort):
        """
        Args:
            repository: 게임 데이터 저장소
        """
        self._repository = repository
        self._current_turn: Optional[Turn] = None
        self._game_calendar: Optional[GameCalendar] = None
        self._is_running = False
    
    def start_new_game(self, player: Player, start_date: date = None) -> Turn:
        """새 게임을 시작합니다.
        
        Args:
            player: 게임을 시작할 플레이어
            start_date: 게임 시작 날짜 (기본값: 오늘)
            
        Returns:
            Turn: 첫 번째 턴
        """
        if start_date is None:
            start_date = date.today()
        
        # 첫 번째 턴 생성
        first_turn = Turn(
            turn_number=1,
            game_date=start_date,
            current_phase=GamePhase.PLAYER_ACTION,
            is_complete=False
        )
        
        # 게임 달력 초기화
        self._game_calendar = GameCalendar(
            start_date=start_date,
            current_turn=first_turn
        )
        
        self._current_turn = first_turn
        self._is_running = True
        
        # 플레이어와 턴 정보 저장
        self._repository.save_player(player)
        self._repository.save_turn(first_turn)
        
        print(f"🎮 새 게임 시작: {player.name}")
        print(f"📅 시작 날짜: {start_date}")
        print(f"🔄 첫 번째 턴: {first_turn.get_display_info()}")
        
        return first_turn
    
    def load_game(self, save_name: str) -> Optional[Turn]:
        """저장된 게임을 불러옵니다.
        
        Args:
            save_name: 불러올 저장 파일명
            
        Returns:
            Optional[Turn]: 현재 턴 또는 None (불러오기 실패)
        """
        game_data = self._repository.load_game(save_name)
        if not game_data:
            return None
        
        # 턴 정보 복원
        current_turn = self._repository.load_current_turn()
        if not current_turn:
            return None
        
        self._current_turn = current_turn
        self._is_running = True
        
        # 게임 달력 복원 (간단한 구현)
        start_date = game_data.get('start_date', current_turn.game_date)
        if isinstance(start_date, str):
            start_date = date.fromisoformat(start_date)
        
        self._game_calendar = GameCalendar(
            start_date=start_date,
            current_turn=current_turn
        )
        
        print(f"📂 게임 불러오기 성공: {save_name}")
        print(f"🔄 현재 턴: {current_turn.get_display_info()}")
        
        return current_turn
    
    def get_current_turn(self) -> Optional[Turn]:
        """현재 턴 정보를 반환합니다."""
        return self._current_turn
    
    def get_current_phase(self) -> Optional[GamePhase]:
        """현재 게임 페이즈를 반환합니다."""
        return self._current_turn.current_phase if self._current_turn else None
    
    def is_game_running(self) -> bool:
        """게임이 실행 중인지 확인합니다."""
        return self._is_running
    
    def advance_phase(self) -> Optional[Turn]:
        """다음 페이즈로 진행합니다.
        
        Returns:
            Optional[Turn]: 업데이트된 턴 또는 None (게임 종료)
        """
        if not self._current_turn or not self._is_running:
            return None
        
        print(f"⏭️  페이즈 진행: {self._current_turn.get_phase_name()} → ", end="")
        
        # 다음 페이즈로 진행
        next_turn = self._current_turn.advance_phase()
        
        if next_turn.is_complete:
            # 턴 완료 - 다음 턴으로 이동
            self._current_turn = next_turn  # 완료된 턴으로 먼저 업데이트
            next_turn = self._start_next_turn()
            print("다음 턴")
        else:
            print(f"{next_turn.get_phase_name()}")
        
        self._current_turn = next_turn
        self._repository.save_turn(next_turn)
        
        return next_turn
    
    def execute_turn_phase(self, phase_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """현재 페이즈를 실행합니다.
        
        Args:
            phase_data: 페이즈 실행에 필요한 데이터
            
        Returns:
            Dict[str, Any]: 페이즈 실행 결과
        """
        if not self._current_turn or not self._is_running:
            return {"error": "게임이 실행 중이 아닙니다"}
        
        current_phase = self._current_turn.current_phase
        result = {"phase": current_phase.name, "success": True}
        
        try:
            if current_phase == GamePhase.PLAYER_ACTION:
                result.update(self._execute_player_action_phase(phase_data))
            elif current_phase == GamePhase.AI_ACTION:
                result.update(self._execute_ai_action_phase(phase_data))
            elif current_phase == GamePhase.EVENT:
                result.update(self._execute_event_phase(phase_data))
            elif current_phase == GamePhase.SALES:
                result.update(self._execute_sales_phase(phase_data))
            elif current_phase == GamePhase.SETTLEMENT:
                result.update(self._execute_settlement_phase(phase_data))
            elif current_phase == GamePhase.CLEANUP:
                result.update(self._execute_cleanup_phase(phase_data))
            
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
            print(f"❌ 페이즈 실행 실패: {e}")
        
        return result
    
    def _start_next_turn(self) -> Turn:
        """다음 턴을 시작합니다."""
        if not self._current_turn:
            raise ValueError("현재 턴이 없습니다")
        
        if not self._current_turn.is_complete:
            raise ValueError("현재 턴이 완료되지 않았습니다")
        
        next_turn = self._current_turn.get_next_turn()
        
        # 게임 달력 업데이트 (완료된 턴으로 먼저 설정)
        if self._game_calendar:
            # 완료된 턴으로 게임 달력 업데이트
            updated_calendar = self._game_calendar._replace(current_turn=self._current_turn)
            self._game_calendar = updated_calendar.advance_turn()
        
        print(f"📅 새로운 턴 시작: {next_turn.get_display_info()}")
        
        return next_turn
    
    def _execute_player_action_phase(self, phase_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """플레이어 행동 페이즈 실행"""
        print("🎮 플레이어 행동 페이즈")
        
        # 플레이어 행동 처리 (기본 구현)
        actions = phase_data.get("actions", []) if phase_data else []
        
        result = {
            "actions_executed": len(actions),
            "actions": actions,
            "time_remaining": 12  # 기본 12시간
        }
        
        print(f"   - 실행된 행동 수: {len(actions)}")
        
        return result
    
    def _execute_ai_action_phase(self, phase_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """AI 행동 페이즈 실행"""
        print("🤖 AI 행동 페이즈")
        
        # AI 행동 처리 (기본 구현)
        ai_actions = ["경쟁자 AI 행동 처리"]
        
        result = {
            "ai_actions": ai_actions,
            "competitors_processed": 0  # 현재 경쟁자 없음
        }
        
        print(f"   - 처리된 AI 행동: {len(ai_actions)}")
        
        return result
    
    def _execute_event_phase(self, phase_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """이벤트 페이즈 실행"""
        print("🎲 이벤트 페이즈")
        
        # 이벤트 처리 (기본 구현)
        event_occurred = False  # 임시로 이벤트 없음
        
        result = {
            "event_occurred": event_occurred,
            "event_id": None,
            "event_result": None
        }
        
        if event_occurred:
            print("   - 이벤트 발생!")
        else:
            print("   - 이벤트 없음")
        
        return result
    
    def _execute_sales_phase(self, phase_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """판매 페이즈 실행"""
        print("💰 판매 페이즈")
        
        # 판매 처리 (기본 구현)
        total_sales = 0
        customer_count = 0
        
        result = {
            "total_sales": total_sales,
            "customer_count": customer_count,
            "products_sold": {}
        }
        
        print(f"   - 총 매출: ₩{total_sales:,}")
        print(f"   - 고객 수: {customer_count}명")
        
        return result
    
    def _execute_settlement_phase(self, phase_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """정산 페이즈 실행"""
        print("📊 정산 페이즈")
        
        # 정산 처리 (기본 구현)
        revenue = 0
        costs = 0
        profit = revenue - costs
        
        result = {
            "revenue": revenue,
            "costs": costs,
            "profit": profit,
            "is_profitable": profit > 0
        }
        
        print(f"   - 매출: ₩{revenue:,}")
        print(f"   - 비용: ₩{costs:,}")
        print(f"   - 순이익: ₩{profit:,}")
        
        return result
    
    def _execute_cleanup_phase(self, phase_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """마무리 페이즈 실행"""
        print("🧹 마무리 페이즈")
        
        # 마무리 처리 (기본 구현)
        result = {
            "cleanup_completed": True,
            "turn_complete": True
        }
        
        print("   - 턴 마무리 완료")
        
        return result
    
    def get_game_status(self) -> Dict[str, Any]:
        """게임 상태 정보를 반환합니다."""
        if not self._current_turn or not self._game_calendar:
            return {"status": "게임이 시작되지 않음"}
        
        return {
            "is_running": self._is_running,
            "current_turn": self._current_turn.turn_number,
            "current_date": self._current_turn.game_date.isoformat(),
            "current_phase": self._current_turn.get_phase_name(),
            "progress": self._current_turn.get_progress_percentage(),
            "days_elapsed": self._game_calendar.get_days_elapsed(),
            "is_weekend": self._game_calendar.is_weekend(),
            "is_month_end": self._game_calendar.is_month_end()
        }
    
    def stop_game(self) -> bool:
        """게임을 중지합니다."""
        self._is_running = False
        print("⏹️  게임 중지")
        return True 