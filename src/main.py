"""
새로운 아키텍처를 적용한 메인 게임 루프

의존성 주입과 계층 분리를 적용한 게임 진입점입니다.
"""

from application.services.player_service import PlayerService
from adapters.services.store_service_impl import StoreServiceImpl
from core.ports.research_service import IResearchService
from ui.controllers.game_controller import GameController


class MockResearchService(IResearchService):
    """임시 연구 서비스 구현체"""
    
    def __init__(self):
        self._research = {}
    
    def get_research_by_id(self, research_id):
        return self._research.get(str(research_id))
    
    def get_research_by_player(self, player_id):
        return []
    
    def start_research(self, player_id, research_type):
        from uuid import uuid4
        from core.domain.research import Research
        from core.domain.value_objects import Progress
        
        research = Research(
            id=uuid4(),
            research_type=research_type,
            name=f"{research_type.name} 연구",
            description="테스트 연구",
            progress=Progress(0),
            difficulty=1,
            required_stat="cooking",
            min_stat_required=10
        )
        self._research[str(research.id)] = research
        return research
    
    def advance_research(self, research_id, progress_amount):
        research = self._research.get(str(research_id))
        if research:
            new_research = research.advance_progress(progress_amount)
            self._research[str(research_id)] = new_research
            return new_research
        return None
    
    def complete_research(self, research_id):
        return self.advance_research(research_id, 100)


def create_dependencies():
    """의존성 객체들을 생성하고 주입"""
    # 서비스 구현체들 생성
    store_service = StoreServiceImpl()
    research_service = MockResearchService()
    
    # 응용 서비스 생성
    player_service = PlayerService(
        store_service=store_service,
        research_service=research_service
    )
    
    # 컨트롤러 생성
    game_controller = GameController(player_service)
    
    return game_controller


def main_menu(game_controller: GameController):
    """메인 메뉴"""
    while True:
        print("\n===== 치킨마스터2 =====")
        print("1. 새 게임")
        print("2. 플레이어 상태 확인")
        print("3. 행동 실행")
        print("4. 불러오기 (미구현)")
        print("0. 종료")
        
        choice = input("선택: ").strip()
        
        if choice == "1":
            game_controller.start_new_game()
        elif choice == "2":
            game_controller.show_player_status()
        elif choice == "3":
            game_controller.execute_action()
        elif choice == "4":
            print("아직 구현되지 않은 기능입니다.")
        elif choice == "0":
            print("게임을 종료합니다.")
            break
        else:
            print("잘못된 선택입니다.")


def main():
    """새로운 아키텍처를 적용한 메인 진입점"""
    print("치킨마스터2 (새 아키텍처)에 오신 것을 환영합니다!")
    
    # 의존성 주입
    game_controller = create_dependencies()
    
    # 메인 게임 루프
    main_menu(game_controller)


if __name__ == "__main__":
    main() 