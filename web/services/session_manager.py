"""게임 세션 관리 — interactive_main.init_game() 패턴 재사용"""

import io
import sys
import threading
from contextlib import contextmanager
from typing import Dict, Optional
from uuid import UUID, uuid4


@contextmanager
def suppress_stdout():
    """게임 엔진의 emoji print 출력을 억제 (Windows cp949 대응)"""
    old = sys.stdout
    sys.stdout = io.StringIO()
    try:
        yield sys.stdout
    finally:
        sys.stdout = old

from core.domain.player import Player
from core.domain.store import Store
from core.domain.product import Product
from core.domain.inventory import Inventory
from core.domain.value_objects import Money, Progress, StatValue, Experience, Percentage
from core.ports.repository_port import RepositoryPort
from application.game_loop_service import GameLoopService
from application.sales_service import SalesService
from application.event_service import EventService
from application.settlement_service import SettlementService
from application.action_service import ActionService, ActionRequest as DomainActionRequest
from application.ai_service_optimized import AIService
from adapters.repository.csv_event_loader import CSVEventLoader
from common.enums.action_type import ActionType

from web.config import EVENTS_CSV


# ── interactive_main.py에서 가져온 MockRepository ──

class MockRepository(RepositoryPort):
    def __init__(self):
        self.players: Dict[UUID, Player] = {}
        self.competitors = {}
        self.turns = {}
        self.stores: Dict[UUID, Store] = {}
        self.products: Dict[UUID, Product] = {}
        self.research_data = {}
        self.analysis_data = {}
        self.current_turn = None
        self.game_data = {}

    def save_player(self, player): self.players[player.id] = player
    def get_player(self, pid): return self.players.get(pid)
    def get_all_players(self): return list(self.players.values())
    def save_competitor(self, c): self.competitors[c.id] = c
    def get_all_competitors(self): return list(self.competitors.values())
    def save_turn(self, t):
        self.turns[t.turn_number] = t
        self.current_turn = t
    def load_game(self, name): return self.game_data
    def load_current_turn(self): return self.current_turn
    def save_store(self, s): self.stores[s.id] = s
    def get_store(self, sid): return self.stores.get(sid)
    def save_product(self, p): self.products[p.id] = p
    def get_product(self, pid): return self.products.get(pid)
    def save_research(self, r): self.research_data[r.id] = r
    def get_research(self, rid): return self.research_data.get(rid)
    def save_player_analysis(self, pid, a): self.analysis_data[pid] = a
    def load_player_analysis(self, pid): return self.analysis_data.get(pid)
    def load_turn_analysis_history(self, pid, limit): return []


    # 행동별 재고 효과
STOCK_EFFECTS = {
    "COOK": {"ingredient_cost": 10, "stock_gain": 10},
    "PREPARE_INGREDIENTS": {"ingredient_cost": 5, "stock_gain": 5},
    "ORDER_INGREDIENTS": {"ingredient_cost": 0, "stock_gain": 0, "ingredient_gain": 50},
}


class GameSession:
    """하나의 게임 세션"""

    def __init__(self, session_id: str, player_name: str):
        self.session_id = session_id
        self.remaining_hours = 12

        # 재고 시스템
        self.ingredient_qty = 100  # 원재료 (닭고기 수량)
        self.stock = 20            # 완성품 (판매 가능 치킨 수)

        # 저장소 + 서비스 (interactive_main.init_game 패턴)
        self.repository = MockRepository()
        event_loader = CSVEventLoader(EVENTS_CSV)
        self.action_service = ActionService(self.repository)
        ai_service = AIService(self.repository)
        event_service = EventService(self.repository, event_loader)
        sales_service = SalesService(self.repository)
        settlement_service = SettlementService(self.repository)

        self.game_service = GameLoopService(
            repository=self.repository,
            action_service=self.action_service,
            ai_service=ai_service,
            event_service=event_service,
            sales_service=sales_service,
            settlement_service=settlement_service,
        )

        # 제품 생성
        ingredient = Inventory(
            id=uuid4(), name="닭고기", quantity=100,
            quality=80, purchase_price=Money(5000),
        )
        self.product_id = uuid4()
        self.product = Product(
            id=self.product_id, recipe_id=uuid4(),
            name="황금 올리브 치킨", selling_price=Money(20000),
            research_progress=Progress(0), ingredients=[ingredient],
            awareness=10,
        )
        self.repository.save_product(self.product)

        # 매장 생성
        self.store_id = uuid4()
        self.store = Store(
            id=self.store_id, owner_id=uuid4(), name="본점",
            monthly_rent=Money(1500000), product_ids=(self.product_id,),
            inventory_item_ids=(), parttime_worker_ids=(),
            is_first_store=True,
        )
        self.repository.save_store(self.store)

        # 플레이어 생성
        base_exp = Experience(0)
        self.player = Player.create_new(name=player_name, initial_money=2000000)
        self.player = self.player._replace(
            store_ids=(self.store_id,),
            cooking=StatValue(10, base_exp),
            management=StatValue(8, base_exp),
            service=StatValue(8, base_exp),
            tech=StatValue(5, base_exp),
            stamina=StatValue(50, base_exp),
        )
        self.store = self.store._replace(owner_id=self.player.id)
        self.repository.save_store(self.store)

        # 게임 시작
        with suppress_stdout():
            self.game_service.start_new_game(self.player)

    # ── 헬퍼 ──

    def get_player(self) -> Player:
        return self.repository.get_player(self.player.id) or self.player

    def get_product(self) -> Product:
        return self.repository.get_product(self.product_id) or self.product

    def get_store(self) -> Store:
        return self.repository.get_store(self.store_id) or self.store


class SessionManager:
    """전체 세션 관리"""

    def __init__(self):
        self._sessions: Dict[str, GameSession] = {}
        self._lock = threading.Lock()

    def create_session(self, player_name: str) -> GameSession:
        session_id = uuid4().hex[:12]
        session = GameSession(session_id, player_name)
        with self._lock:
            self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[GameSession]:
        return self._sessions.get(session_id)

    def delete_session(self, session_id: str) -> bool:
        with self._lock:
            return self._sessions.pop(session_id, None) is not None
