import sys
import os
from datetime import date
from typing import Dict, Any, Optional
from uuid import UUID

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "."))

from core.ports.repository_port import RepositoryPort
from core.domain.player import Player
from core.domain.turn import Turn
from application.game_loop_service import GameLoopService

class MockRepository(RepositoryPort):
    """메모리 기반 모의 저장소"""

    def __init__(self):
        self.players: Dict[UUID, Player] = {}
        self.turns: Dict[int, Turn] = {}
        self.current_turn: Optional[Turn] = None
        self.game_data: Dict[str, Any] = {}

    def save_player(self, player: Player) -> None:
        print(f"[Repo] 플레이어 저장: {player.name}")
        self.players[player.id] = player

    def save_turn(self, turn: Turn) -> None:
        print(f"[Repo] 턴 저장: {turn.turn_number} - {turn.get_phase_name()}")
        self.turns[turn.turn_number] = turn
        self.current_turn = turn

    def load_game(self, save_name: str) -> Optional[Dict[str, Any]]:
        print(f"[Repo] 게임 데이터 로드: {save_name}")
        return self.game_data

    def load_current_turn(self) -> Optional[Turn]:
        return self.current_turn

def main():
    print("=== 치킨마스터2 엔진 테스트 시작 ===")

    # 1. 저장소 및 서비스 초기화
    repository = MockRepository()
    game_service = GameLoopService(repository)

    # 2. 플레이어 생성
    print("\n>>> 플레이어 생성 중...")
    player = Player.create_new(name="김치킨", initial_money=1000000)
    print(f"플레이어 생성 완료: {player.name}, 자금: {player.money.format_korean()}")

    # 3. 새 게임 시작
    print("\n>>> 게임 시작...")
    current_turn = game_service.start_new_game(player)

    # 4. 턴 페이즈 진행 시뮬레이션
    print("\n>>> 턴 진행 시뮬레이션 (1일차)...")

    # 현재 상태 확인
    status = game_service.get_game_status()
    print(f"현재 상태: {status['current_date']} - {status['current_phase']}")

    # 페이즈 진행 반복
    while True:
        # 페이즈 실행
        result = game_service.execute_turn_phase()
        print(f"[{status['current_phase']}] 결과: {result}")

        # 다음 페이즈로 이동
        next_turn = game_service.advance_phase()

        if next_turn.turn_number > 1:
            print("\n>>> 2일차 시작! 테스트를 종료합니다.")
            break

        status = game_service.get_game_status()

    print("\n=== 테스트 성공적 완료 ===")

if __name__ == "__main__":
    main()
