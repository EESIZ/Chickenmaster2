"""
게임 컨트롤러

게임 플레이 관련 사용자 입력을 처리합니다.
"""

from typing import Optional

from application.services.player_service import PlayerService
from application.dtos.player_dto import CreatePlayerRequest, PlayerActionRequest


class GameController:
    """게임 컨트롤러"""
    
    def __init__(self, player_service: PlayerService):
        self._player_service = player_service
        self._current_player_id: Optional[str] = None
    
    def start_new_game(self) -> str:
        """새 게임 시작"""
        print("\n===== 새 게임 시작 =====")
        
        # 플레이어 이름 입력
        player_name = input("플레이어 이름을 입력하세요: ").strip()
        if not player_name:
            player_name = "치킨마스터"
        
        # 캐릭터 선택
        character_preset = self._select_character()
        
        # 플레이어 생성 요청
        request = CreatePlayerRequest(
            name=player_name,
            character_preset=character_preset
        )
        
        # 플레이어 생성
        player_status = self._player_service.create_player(request)
        self._current_player_id = player_status.id
        
        print(f"\n{player_status.name}님, 환영합니다!")
        self._display_player_status(player_status)
        
        return player_status.id
    
    def _select_character(self) -> str:
        """캐릭터 선택"""
        print("\n캐릭터를 선택하세요:")
        print("1. 요리사 (요리 특화)")
        print("2. 경영자 (경영 특화)")
        print("3. 서비스 전문가 (서비스 특화)")
        print("0. 테스트맨 (모든 스탯 최고)")
        
        while True:
            choice = input("선택 (1-3, 0): ").strip()
            
            if choice == "1":
                return "chef"
            elif choice == "2":
                return "businessman"
            elif choice == "3":
                return "service_expert"
            elif choice == "0":
                return "testman"
            else:
                print("잘못된 선택입니다. 다시 입력해주세요.")
    
    def show_player_status(self) -> None:
        """현재 플레이어 상태 표시"""
        if not self._current_player_id:
            print("현재 플레이어가 없습니다.")
            return
        
        player_status = self._player_service.get_player_status(self._current_player_id)
        if not player_status:
            print("플레이어 정보를 찾을 수 없습니다.")
            return
        
        self._display_player_status(player_status)
    
    def execute_action(self) -> None:
        """플레이어 행동 실행"""
        if not self._current_player_id:
            print("현재 플레이어가 없습니다.")
            return
        
        print("\n===== 행동 선택 =====")
        print("1. 휴식 (피로도 감소)")
        print("2. 작업 (피로도 증가)")
        print("3. 상태 확인")
        print("0. 돌아가기")
        
        choice = input("선택: ").strip()
        
        if choice == "1":
            self._execute_rest()
        elif choice == "2":
            self._execute_work()
        elif choice == "3":
            self.show_player_status()
        elif choice == "0":
            return
        else:
            print("잘못된 선택입니다.")
    
    def _execute_rest(self) -> None:
        """휴식 실행"""
        request = PlayerActionRequest(
            player_id=self._current_player_id,
            action_type="rest"
        )
        
        player_status = self._player_service.execute_player_action(request)
        print("\n휴식을 취했습니다. 피로도가 감소했습니다.")
        self._display_player_status(player_status)
    
    def _execute_work(self) -> None:
        """작업 실행"""
        request = PlayerActionRequest(
            player_id=self._current_player_id,
            action_type="work"
        )
        
        player_status = self._player_service.execute_player_action(request)
        print("\n열심히 일했습니다. 피로도가 증가했습니다.")
        self._display_player_status(player_status)
    
    def _display_player_status(self, player_status) -> None:
        """플레이어 상태 표시"""
        print(f"\n===== {player_status.name}의 상태 =====")
        print(f"자금: ₩{player_status.money:,}")
        print(f"피로도: {player_status.fatigue:.1f}%")
        print(f"매장 수: {player_status.store_count}")
        print(f"연구 수: {player_status.research_count}")
        print("\n--- 스탯 ---")
        print(f"요리: {player_status.stats.cooking}")
        print(f"경영: {player_status.stats.management}")
        print(f"서비스: {player_status.stats.service}")
        print(f"기술: {player_status.stats.tech}")
        print(f"체력: {player_status.stats.stamina}")
        print("=" * 30) 