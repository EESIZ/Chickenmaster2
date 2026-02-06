import sys
import os
from datetime import date
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "."))

from core.ports.repository_port import RepositoryPort
from core.domain.player import Player
from core.domain.turn import Turn
from core.domain.store import Store
from core.domain.product import Product
from core.domain.competitor import Competitor
from core.domain.research import Research
from core.domain.value_objects import Money, Progress
from application.game_loop_service import GameLoopService
from application.sales_service import SalesService
from application.event_service import EventService
from application.settlement_service import SettlementService
from application.action_service import ActionService
from application.ai_service_optimized import AIService
from adapters.repository.csv_event_loader import CSVEventLoader

class MockRepository(RepositoryPort):
    """메모리 기반 모의 저장소"""

    def __init__(self):
        self.players: Dict[UUID, Player] = {}
        self.competitors: Dict[UUID, Competitor] = {}
        self.turns: Dict[int, Turn] = {}
        self.stores: Dict[UUID, Store] = {}
        self.products: Dict[UUID, Product] = {}
        self.research_data: Dict[UUID, Research] = {}
        self.analysis_data: Dict[UUID, Dict[str, Any]] = {}
        self.current_turn: Optional[Turn] = None
        self.game_data: Dict[str, Any] = {}

    # --- Player ---
    def save_player(self, player: Player) -> None:
        self.players[player.id] = player

    def get_player(self, player_id: UUID) -> Optional[Player]:
        return self.players.get(player_id)

    def get_all_players(self) -> List[Player]:
        return list(self.players.values())

    # --- Competitor ---
    def save_competitor(self, competitor: Competitor) -> None:
        self.competitors[competitor.id] = competitor

    def get_all_competitors(self) -> List[Competitor]:
        return list(self.competitors.values())

    # --- Turn ---
    def save_turn(self, turn: Turn) -> None:
        print(f"[Repo] 턴 저장: {turn.turn_number} - {turn.get_phase_name()}")
        self.turns[turn.turn_number] = turn
        self.current_turn = turn

    def load_game(self, save_name: str) -> Optional[Dict[str, Any]]:
        return self.game_data

    def load_current_turn(self) -> Optional[Turn]:
        return self.current_turn

    # --- Store ---
    def save_store(self, store: Store) -> None:
        self.stores[store.id] = store

    def get_store(self, store_id: UUID) -> Optional[Store]:
        return self.stores.get(store_id)

    # --- Product ---
    def save_product(self, product: Product) -> None: # Helper for mock setup
        self.products[product.id] = product

    def get_product(self, product_id: UUID) -> Optional[Product]:
        return self.products.get(product_id)

    # --- Research ---
    def save_research(self, research: Research) -> None:
        self.research_data[research.id] = research

    def get_research(self, research_id: UUID) -> Optional[Research]:
        return self.research_data.get(research_id)

    # --- Analysis ---
    def save_player_analysis(self, player_id: UUID, analysis: Dict[str, Any]) -> None:
        self.analysis_data[player_id] = analysis

    def load_player_analysis(self, player_id: UUID) -> Optional[Dict[str, Any]]:
        return self.analysis_data.get(player_id)

    def load_turn_analysis_history(self, player_id: UUID, limit: int) -> List[Dict[str, Any]]:
        return [] # Mock history

def main():
    print("=== 치킨마스터2 통합 엔진 테스트 시작 ===")

    # 1. 저장소 초기화
    repository = MockRepository()

    # 2. 서비스 초기화
    event_loader = CSVEventLoader("data/events.csv") # 실제 파일 경로 확인 필요

    action_service = ActionService(repository)
    ai_service = AIService(repository)
    event_service = EventService(repository, event_loader)
    sales_service = SalesService(repository)
    settlement_service = SettlementService(repository)

    game_service = GameLoopService(
        repository=repository,
        action_service=action_service,
        ai_service=ai_service,
        event_service=event_service,
        sales_service=sales_service,
        settlement_service=settlement_service
    )

    # 3. 데이터 셋업 (플레이어, 매장, 제품)
    print("\n>>> 데이터 초기화 중...")

    # 제품 생성
    recipe_id = uuid4()
    ingredient_id = uuid4()

    # 재료 (Mock Inventory for Product creation, though Product uses Inventory object directly in list)
    from core.domain.inventory import Inventory
    ingredient = Inventory(
        id=ingredient_id,
        name="닭고기",
        quantity=100,
        quality=80,
        purchase_price=Money(5000)
    )

    product_id = uuid4()
    product = Product(
        id=product_id,
        recipe_id=recipe_id,
        name="황금 올리브 치킨",
        selling_price=Money(20000),
        research_progress=Progress(0),
        ingredients=[ingredient],
        awareness=10
    )
    repository.save_product(product)

    # 매장 생성
    store_id = uuid4()
    store = Store(
        id=store_id,
        owner_id=uuid4(), # Will receive player id later
        name="본점",
        monthly_rent=Money(1500000),
        product_ids=(product_id,),
        inventory_item_ids=(),
        parttime_worker_ids=(),
        is_first_store=True
    )
    repository.save_store(store)

    # 플레이어 생성 (매장 연결)
    # Player.create_new는 store_id를 새로 생성하므로, 우리가 만든 store_id로 교체해야 함
    player = Player.create_new(name="김치킨", initial_money=2000000)
    # create_new가 랜덤 store_id를 만들었으므로 교체
    player = player._replace(store_ids=(store_id,))
    # store owner_id도 업데이트
    store = store._replace(owner_id=player.id)
    repository.save_store(store)

    print(f"플레이어: {player.name}, 자금: {player.money.format_korean()}")
    print(f"매장: {store.name}, 제품: {product.name} ({product.selling_price.format_korean()})")

    # 4. 새 게임 시작
    print("\n>>> 게임 시작...")
    current_turn = game_service.start_new_game(player)

    # 5. 턴 진행
    print("\n>>> 턴 진행 시뮬레이션 (1일차)...")

    status = game_service.get_game_status()
    print(f"현재 상태: {status['current_date']} - {status['current_phase']}")

    while True:
        # 페이즈 실행
        result = game_service.execute_turn_phase()

        # 결과 요약 출력
        if status['current_phase'] == "SALES":
            print(f"[판매 결과] 매출: {result.get('total_sales')}, 고객: {result.get('customer_count')}")
            # 피드백이 있다면 출력
            # (SalesService 로직 상 GameLoopService가 상세 result를 반환하도록 수정했다면 가능)
        elif status['current_phase'] == "SETTLEMENT":
            print(f"[정산 결과] 이익: {result.get('profit')}, 비용: {result.get('costs')}")
        else:
            print(f"[{status['current_phase']}] 완료")

        # 다음 페이즈로 이동
        next_turn = game_service.advance_phase()

        if next_turn.turn_number > 1:
            print(f"\n>>> 2일차 시작! 플레이어 자금: {repository.get_player(player.id).money.format_korean()}")
            break

        status = game_service.get_game_status()

    print("\n=== 테스트 성공적 완료 ===")

if __name__ == "__main__":
    main()
