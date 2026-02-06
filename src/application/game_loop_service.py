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

# Services
from application.action_service import ActionService
from application.ai_service_optimized import AIService
from application.event_service import EventService
from application.sales_service import SalesService
from application.settlement_service import SettlementService
from core.ports.sales_port import SalesResult


class GameLoopService:
    """게임 루프 응용 서비스"""
    
    def __init__(self,
                 repository: RepositoryPort,
                 action_service: Optional[ActionService] = None,
                 ai_service: Optional[AIService] = None,
                 event_service: Optional[EventService] = None,
                 sales_service: Optional[SalesService] = None,
                 settlement_service: Optional[SettlementService] = None):

        self._repository = repository

        # Services
        self._action_service = action_service
        self._ai_service = ai_service
        self._event_service = event_service
        self._sales_service = sales_service
        self._settlement_service = settlement_service

        # State
        self._current_turn: Optional[Turn] = None
        self._game_calendar: Optional[GameCalendar] = None
        self._is_running = False
        self._current_player_id: Optional[UUID] = None

        # Temporary storage for phase results
        self._current_sales_results: Dict[UUID, SalesResult] = {}
    
    def start_new_game(self, player: Player, start_date: date = None) -> Turn:
        """새 게임을 시작합니다."""
        if start_date is None:
            start_date = date.today()
        
        first_turn = Turn(
            turn_number=1,
            game_date=start_date,
            current_phase=GamePhase.PLAYER_ACTION,
            is_complete=False
        )
        
        self._game_calendar = GameCalendar(
            start_date=start_date,
            current_turn=first_turn
        )
        
        self._current_turn = first_turn
        self._is_running = True
        self._current_player_id = player.id
        
        self._repository.save_player(player)
        self._repository.save_turn(first_turn)
        
        print(f"🎮 새 게임 시작: {player.name}")
        print(f"📅 시작 날짜: {start_date}")
        print(f"🔄 첫 번째 턴: {first_turn.get_display_info()}")
        
        return first_turn
    
    def advance_phase(self) -> Optional[Turn]:
        """다음 페이즈로 진행합니다."""
        if not self._current_turn or not self._is_running:
            return None
        
        print(f"⏭️  페이즈 진행: {self._current_turn.get_phase_name()} → ", end="")
        
        next_turn = self._current_turn.advance_phase()
        
        if next_turn.is_complete:
            self._current_turn = next_turn
            next_turn = self._start_next_turn()
            print("다음 턴")
        else:
            print(f"{next_turn.get_phase_name()}")
        
        self._current_turn = next_turn
        self._repository.save_turn(next_turn)
        
        return next_turn
    
    def execute_turn_phase(self, phase_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """현재 페이즈를 실행합니다."""
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
            import traceback
            traceback.print_exc()
            result["success"] = False
            result["error"] = str(e)
            print(f"❌ 페이즈 실행 실패: {e}")
        
        return result
    
    def _start_next_turn(self) -> Turn:
        """다음 턴을 시작합니다."""
        if not self._current_turn:
            raise ValueError("현재 턴이 없습니다")
        
        next_turn = self._current_turn.get_next_turn()
        self._current_sales_results = {}
        
        if self._game_calendar:
            updated_calendar = self._game_calendar._replace(current_turn=self._current_turn)
            self._game_calendar = updated_calendar.advance_turn()
        
        print(f"📅 새로운 턴 시작: {next_turn.get_display_info()}")
        
        return next_turn
    
    def _execute_player_action_phase(self, phase_data: Dict[str, Any] = None) -> Dict[str, Any]:
        print("🎮 플레이어 행동 페이즈")
        # TODO: UI 연동 시 실제 ActionService 호출
        return {"actions_executed": 0, "message": "행동 대기 중"}
    
    def _execute_ai_action_phase(self, phase_data: Dict[str, Any] = None) -> Dict[str, Any]:
        print("🤖 AI 행동 페이즈")
        processed = 0
        if self._ai_service:
            competitors = self._repository.get_all_competitors()
            # AI 로직 실행 (생략 가능)
            processed = len(competitors)
        return {"competitors_processed": processed}
    
    def _execute_event_phase(self, phase_data: Dict[str, Any] = None) -> Dict[str, Any]:
        print("🎲 이벤트 페이즈")
        
        if self._event_service and self._current_player_id:
            player = self._repository.get_player(self._current_player_id)
            if player:
                event_result = self._event_service.process_daily_events(self._current_turn, player)
                if event_result.occurred:
                    print(f"   [이벤트] {event_result.message}")
                return {"event_occurred": event_result.occurred, "message": event_result.message}

        return {"event_occurred": False, "message": "이벤트 없음"}
    
    def _execute_sales_phase(self, phase_data: Dict[str, Any] = None) -> Dict[str, Any]:
        print("💰 판매 페이즈")
        
        total_sales = 0
        customer_count = 0
        
        if self._sales_service:
            players = self._repository.get_all_players()
            competitors = self._repository.get_all_competitors()

            self._current_sales_results = self._sales_service.calculate_daily_sales(players, competitors)

            # 현재 플레이어의 결과 추출
            if self._current_player_id and self._current_player_id in self._current_sales_results:
                my_result = self._current_sales_results[self._current_player_id]
                total_sales = my_result.total_revenue
                customer_count = my_result.total_customers

                print(f"   - 매출: ₩{total_sales:,}")
                print(f"   - 고객: {customer_count}명")
                for feedback in my_result.feedbacks:
                    print(f"   💬 [{feedback.customer_name}] {feedback.message}")

        return {
            "total_sales": total_sales,
            "customer_count": customer_count
        }
    
    def _execute_settlement_phase(self, phase_data: Dict[str, Any] = None) -> Dict[str, Any]:
        print("📊 정산 페이즈")
        
        revenue = 0
        costs = 0
        profit = 0
        
        if self._settlement_service and self._current_player_id:
            player = self._repository.get_player(self._current_player_id)

            # 매출 정보 가져오기
            sales_result = self._current_sales_results.get(self._current_player_id)
            current_revenue = sales_result.total_revenue if sales_result else 0

            if player:
                result = self._settlement_service.calculate_settlement(player, current_revenue)
                revenue = result.revenue
                costs = result.total_cost
                profit = result.net_profit

                print(f"   - 매출: ₩{revenue:,}")
                print(f"   - 비용: ₩{costs:,} (임대료 {result.rent_cost}, 재료비 {result.ingredient_cost})")
                print(f"   - 순이익: ₩{profit:,}")

        return {
            "revenue": revenue,
            "costs": costs,
            "profit": profit
        }
    
    def _execute_cleanup_phase(self, phase_data: Dict[str, Any] = None) -> Dict[str, Any]:
        print("🧹 마무리 페이즈")
        return {"cleanup_completed": True}

    # ... (나머지 메서드는 동일)

    def load_game(self, save_name: str) -> Optional[Turn]:
        """저장된 게임을 불러옵니다."""
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
        return self._current_turn

    def get_current_phase(self) -> Optional[GamePhase]:
        return self._current_turn.current_phase if self._current_turn else None

    def is_game_running(self) -> bool:
        return self._is_running
    
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
