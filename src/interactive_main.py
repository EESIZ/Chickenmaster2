# -*- coding: utf-8 -*-
"""
치킨마스터2 인터랙티브 모드

CLI 기반으로 플레이어가 직접 행동을 선택하고 게임을 진행합니다.
실행: python -X utf8 src/interactive_main.py
"""

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
from core.domain.inventory import Inventory
from core.domain.value_objects import Money, Progress, Percentage
from application.game_loop_service import GameLoopService
from application.sales_service import SalesService
from application.event_service import EventService
from application.settlement_service import SettlementService
from application.action_service import ActionService, ActionRequest, ActionResult
from application.ai_service_optimized import AIService
from adapters.repository.csv_event_loader import CSVEventLoader
from common.enums.action_type import (
    ActionType, CookingAction, AdvertisingAction,
    OperationAction, ResearchAction, PersonalAction, RestAction,
)


# ─── MockRepository (simple_main.py에서 가져옴) ───

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

    def save_player(self, player: Player) -> None:
        self.players[player.id] = player

    def get_player(self, player_id: UUID) -> Optional[Player]:
        return self.players.get(player_id)

    def get_all_players(self) -> List[Player]:
        return list(self.players.values())

    def save_competitor(self, competitor: Competitor) -> None:
        self.competitors[competitor.id] = competitor

    def get_all_competitors(self) -> List[Competitor]:
        return list(self.competitors.values())

    def save_turn(self, turn: Turn) -> None:
        self.turns[turn.turn_number] = turn
        self.current_turn = turn

    def load_game(self, save_name: str) -> Optional[Dict[str, Any]]:
        return self.game_data

    def load_current_turn(self) -> Optional[Turn]:
        return self.current_turn

    def save_store(self, store: Store) -> None:
        self.stores[store.id] = store

    def get_store(self, store_id: UUID) -> Optional[Store]:
        return self.stores.get(store_id)

    def save_product(self, product: Product) -> None:
        self.products[product.id] = product

    def get_product(self, product_id: UUID) -> Optional[Product]:
        return self.products.get(product_id)

    def save_research(self, research: Research) -> None:
        self.research_data[research.id] = research

    def get_research(self, research_id: UUID) -> Optional[Research]:
        return self.research_data.get(research_id)

    def save_player_analysis(self, player_id: UUID, analysis: Dict[str, Any]) -> None:
        self.analysis_data[player_id] = analysis

    def load_player_analysis(self, player_id: UUID) -> Optional[Dict[str, Any]]:
        return self.analysis_data.get(player_id)

    def load_turn_analysis_history(self, player_id: UUID, limit: int) -> List[Dict[str, Any]]:
        return []


# ─── 행동 정보 테이블 ───

ACTION_CATEGORIES = [
    {
        "name": "조리",
        "icon": "[조리]",
        "type": ActionType.COOKING,
        "actions": [
            {"enum": CookingAction.PREPARE_INGREDIENTS, "name": "재료 준비", "hours": 2, "cost": 0},
            {"enum": CookingAction.COOK, "name": "조리", "hours": 3, "cost": 0},
            {"enum": CookingAction.INSPECT_INGREDIENTS, "name": "재료 점검", "hours": 1, "cost": 0},
        ],
    },
    {
        "name": "광고",
        "icon": "[광고]",
        "type": ActionType.ADVERTISING,
        "actions": [
            {"enum": AdvertisingAction.FLYER, "name": "전단지 배포", "hours": 2, "cost": 50000},
            {"enum": AdvertisingAction.ONLINE_AD, "name": "온라인 광고", "hours": 1, "cost": 100000},
            {"enum": AdvertisingAction.DELIVERY_APP, "name": "배달앱 등록", "hours": 1, "cost": 30000},
        ],
    },
    {
        "name": "운영",
        "icon": "[운영]",
        "type": ActionType.OPERATION,
        "actions": [
            {"enum": OperationAction.ORDER_INGREDIENTS, "name": "재료 주문", "hours": 1, "cost": 200000},
            {"enum": OperationAction.CLEAN, "name": "매장 청소", "hours": 2, "cost": 0},
            {"enum": OperationAction.EQUIPMENT_CHECK, "name": "장비 점검", "hours": 1, "cost": 0},
            {"enum": OperationAction.HIRE_PARTTIME, "name": "알바 고용", "hours": 2, "cost": 80000},
        ],
    },
    {
        "name": "연구",
        "icon": "[연구]",
        "type": ActionType.RESEARCH,
        "actions": [
            {"enum": ResearchAction.RECIPE, "name": "레시피 연구", "hours": 3, "cost": 0},
            {"enum": ResearchAction.MANAGEMENT, "name": "경영 연구", "hours": 3, "cost": 0},
            {"enum": ResearchAction.ADVERTISING_RESEARCH, "name": "광고 연구", "hours": 3, "cost": 0},
            {"enum": ResearchAction.SERVICE, "name": "서비스 연구", "hours": 3, "cost": 0},
        ],
    },
    {
        "name": "개인",
        "icon": "[개인]",
        "type": ActionType.PERSONAL,
        "actions": [
            {"enum": PersonalAction.VACATION, "name": "휴가", "hours": 4, "cost": 150000},
            {"enum": PersonalAction.STUDY, "name": "학습", "hours": 2, "cost": 0},
            {"enum": PersonalAction.EXERCISE, "name": "운동", "hours": 2, "cost": 0},
        ],
    },
    {
        "name": "휴식",
        "icon": "[휴식]",
        "type": ActionType.REST,
        "actions": [
            {"enum": RestAction.SLEEP, "name": "수면", "hours": 1, "cost": 0},
        ],
    },
]

# 경험치 정보 (ActionService에서 가져옴)
ACTION_EXP_INFO = {
    CookingAction.PREPARE_INGREDIENTS: "요리+8",
    CookingAction.COOK: "요리+12",
    CookingAction.INSPECT_INGREDIENTS: "요리+4, 경영+2",
    AdvertisingAction.FLYER: "경영+6",
    AdvertisingAction.ONLINE_AD: "경영+8, 기술+4",
    AdvertisingAction.DELIVERY_APP: "경영+6, 기술+6",
    OperationAction.ORDER_INGREDIENTS: "경영+8",
    OperationAction.CLEAN: "서비스+10",
    OperationAction.EQUIPMENT_CHECK: "기술+8, 경영+4",
    OperationAction.HIRE_PARTTIME: "경영+10, 서비스+4",
    ResearchAction.RECIPE: "요리+15",
    ResearchAction.MANAGEMENT: "경영+15",
    ResearchAction.ADVERTISING_RESEARCH: "경영+12, 기술+8",
    ResearchAction.SERVICE: "서비스+15",
    PersonalAction.VACATION: "체력+12, 피로-8/h",
    PersonalAction.STUDY: "기술+15, 경영+5",
    PersonalAction.EXERCISE: "체력+20",
    RestAction.SLEEP: "체력+8, 피로-16/h",
}

FATIGUE_INFO = ActionService.ACTION_FATIGUE_COSTS


# ─── UI 함수들 ───

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def prompt(msg: str, default: str = "") -> str:
    """사용자 입력을 받습니다."""
    if default:
        raw = input(f"{msg} [{default}]: ").strip()
        return raw if raw else default
    return input(f"{msg}: ").strip()


def prompt_int(msg: str, low: int, high: int) -> int:
    """정수 입력을 받습니다."""
    while True:
        raw = input(f"{msg} ({low}-{high}): ").strip()
        if raw.lower() == "q":
            return -1
        try:
            val = int(raw)
            if low <= val <= high:
                return val
            print(f"  {low}~{high} 사이의 숫자를 입력하세요.")
        except ValueError:
            print("  숫자를 입력하세요.")


def show_title():
    print()
    print("=" * 50)
    print("       치킨마스터 2 - 인터랙티브 모드")
    print("=" * 50)
    print()
    print("  치킨집 사장이 되어 최고의 치킨 제국을 만드세요!")
    print("  매일 12시간 안에 행동을 선택하고,")
    print("  매출을 올리고, 경쟁자를 이기세요!")
    print()
    print("  [q] 를 입력하면 언제든 게임을 종료합니다.")
    print()


def show_dashboard(player: Player, turn_number: int, game_date: date, store: Store, product: Product):
    """상태 대시보드를 표시합니다."""
    stats = player.get_effective_stats()
    print()
    print("=" * 50)
    print(f"  {turn_number}일차 ({game_date})  |  {player.money.format_korean()}")
    print("-" * 50)

    # 피로도 바
    fatigue_val = player.fatigue.value
    fatigue_bar_len = int(fatigue_val / 5)  # max 200 -> 40칸
    fatigue_bar = "#" * min(fatigue_bar_len, 20) + "." * max(0, 20 - fatigue_bar_len)
    fatigue_status = ""
    if player.is_completely_exhausted():
        fatigue_status = " !! 탈진 !!"
    elif player.is_knocked_out():
        fatigue_status = " ! 기절 !"
    elif player.is_critically_fatigued():
        fatigue_status = " ! 위험 !"
    elif player.is_fatigued():
        fatigue_status = " 주의"
    print(f"  피로도: [{fatigue_bar}] {fatigue_val:.0f}%{fatigue_status}")
    print(f"  행복도: {player.happiness.value:.0f}%")
    print()
    print(f"  요리: {stats.cooking.base_value:>3d}  |  경영: {stats.management.base_value:>3d}  |  서비스: {stats.service.base_value:>3d}")
    print(f"  기술: {stats.tech.base_value:>3d}  |  체력: {stats.stamina.base_value:>3d}")
    print("-" * 50)
    print(f"  매장: {store.name}  |  메뉴: {product.name} ({product.selling_price.format_korean()})")
    print("=" * 50)


def show_action_menu(remaining_hours: int, player_money: int):
    """행동 선택 메뉴를 표시합니다."""
    print()
    print(f"  남은 시간: {remaining_hours}시간")
    print()
    for i, cat in enumerate(ACTION_CATEGORIES, 1):
        sub_names = ", ".join(a["name"] for a in cat["actions"])
        print(f"  {i}. {cat['icon']} {cat['name']:4s}  ({sub_names})")
    print(f"  7. [가격] 가격 변경")
    print(f"  8. [상태] 현재 상태 보기")
    print(f"  0. [종료] 턴 종료 (나머지 시간 건너뛰기)")
    print()


def show_sub_actions(category: dict, remaining_hours: int, player_money: int):
    """세부 행동 목록을 표시합니다."""
    print()
    print(f"  === {category['icon']} {category['name']} ===")
    print()
    available = []
    for i, action in enumerate(category["actions"], 1):
        hours = action["hours"]
        cost = action["cost"]
        exp_info = ACTION_EXP_INFO.get(action["enum"], "")
        fatigue = FATIGUE_INFO.get(action["enum"], 0)

        # 가능 여부 확인
        can_do = hours <= remaining_hours and cost <= player_money
        marker = "  " if can_do else "X "

        cost_str = f"  {Money(cost).format_korean()}" if cost > 0 else ""
        fatigue_str = f"  피로{fatigue:+.0f}/h" if fatigue != 0 else ""

        print(f"  {marker}{i}. {action['name']:8s}  {hours}시간{cost_str}{fatigue_str}  ({exp_info})")
        available.append(can_do)

    print(f"  0. 뒤로")
    print()
    return available


def show_phase_result(phase_name: str, result: Dict[str, Any]):
    """페이즈 결과를 표시합니다."""
    # GameLoopService가 이미 print하므로 여기서는 간단한 구분선만
    pass


def show_turn_summary(sales_result: Dict, settlement_result: Dict, player: Player):
    """턴 종료 요약을 표시합니다."""
    print()
    print("-" * 50)
    print("  === 일일 결산 ===")
    revenue = settlement_result.get("revenue", 0)
    costs = settlement_result.get("costs", 0)
    profit = settlement_result.get("profit", 0)
    print(f"  매출:   {Money(revenue).format_korean()}")
    print(f"  비용:   {Money(costs).format_korean()}")
    if profit >= 0:
        print(f"  순이익: {Money(profit).format_korean()}")
    else:
        print(f"  순손실: {Money(abs(profit)).format_korean()}")
    print(f"  보유자금: {player.money.format_korean()}")
    print("-" * 50)


# ─── 게임 로직 ───

def init_game() -> tuple:
    """게임을 초기화합니다."""
    show_title()

    name = prompt("  사장님 이름을 입력하세요", "김치킨")
    print()

    # 저장소 + 서비스 초기화
    repository = MockRepository()
    event_loader = CSVEventLoader("data/events.csv")

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
        settlement_service=settlement_service,
    )

    # 제품 생성
    ingredient = Inventory(
        id=uuid4(),
        name="닭고기",
        quantity=100,
        quality=80,
        purchase_price=Money(5000),
    )
    product_id = uuid4()
    product = Product(
        id=product_id,
        recipe_id=uuid4(),
        name="황금 올리브 치킨",
        selling_price=Money(20000),
        research_progress=Progress(0),
        ingredients=[ingredient],
        awareness=10,
    )
    repository.save_product(product)

    # 매장 생성
    store_id = uuid4()
    store = Store(
        id=store_id,
        owner_id=uuid4(),
        name="본점",
        monthly_rent=Money(1500000),
        product_ids=(product_id,),
        inventory_item_ids=(),
        parttime_worker_ids=(),
        is_first_store=True,
    )
    repository.save_store(store)

    # 플레이어 생성 (초기 스탯을 게임 플레이에 적합한 값으로 설정)
    player = Player.create_new(name=name, initial_money=2000000)
    from core.domain.value_objects import StatValue, Experience
    base_exp = Experience(0)
    player = player._replace(
        store_ids=(store_id,),
        cooking=StatValue(10, base_exp),
        management=StatValue(8, base_exp),
        service=StatValue(8, base_exp),
        tech=StatValue(5, base_exp),
        stamina=StatValue(50, base_exp),  # 체력 50이면 피로도 100까지 버팀
    )
    store = store._replace(owner_id=player.id)
    repository.save_store(store)

    return repository, game_service, action_service, player, store, product


def handle_price_change(repository, player: Player, product: Product) -> Product:
    """가격 변경을 처리합니다."""
    print()
    print(f"  현재 가격: {product.selling_price.format_korean()}")
    print(f"  (1,000원 단위, 범위: 5,000 ~ 100,000)")
    raw = prompt("  새 가격 (원)", str(product.selling_price.amount))
    try:
        new_price = int(raw)
        new_price = max(5000, min(100000, new_price))
        new_price = (new_price // 1000) * 1000  # 1000원 단위로 반올림
        product = product.update_selling_price(Money(new_price))
        repository.save_product(product)
        print(f"  -> 가격이 {Money(new_price).format_korean()}(으)로 변경되었습니다.")
    except ValueError:
        print("  잘못된 입력입니다.")
    return product


def handle_player_action_phase(repository, action_service: ActionService, player: Player, store: Store, product: Product) -> Player:
    """플레이어 행동 페이즈를 처리합니다."""
    remaining_hours = 12

    while remaining_hours > 0:
        show_action_menu(remaining_hours, player.money.amount)
        choice = prompt_int("  행동 선택", 0, 8)

        if choice == -1:  # q
            return None  # 게임 종료 신호

        if choice == 0:  # 턴 종료
            if remaining_hours > 0:
                print(f"\n  {remaining_hours}시간을 남기고 턴을 종료합니다.")
            break

        if choice == 8:  # 상태 보기
            status = game_service.get_game_status() if 'game_service' in dir() else {}
            print(f"\n  보유자금: {player.money.format_korean()}")
            print(f"  피로도: {player.fatigue.value:.0f}%")
            print(f"  행복도: {player.happiness.value:.0f}%")
            stats = player.get_effective_stats()
            print(f"  요리: {stats.cooking.base_value}  경영: {stats.management.base_value}  서비스: {stats.service.base_value}")
            print(f"  기술: {stats.tech.base_value}  체력: {stats.stamina.base_value}")
            continue

        if choice == 7:  # 가격 변경
            product = handle_price_change(repository, player, product)
            continue

        if choice < 1 or choice > 6:
            print("  잘못된 선택입니다.")
            continue

        category = ACTION_CATEGORIES[choice - 1]
        available = show_sub_actions(category, remaining_hours, player.money.amount)

        sub_choice = prompt_int("  세부 행동 선택", 0, len(category["actions"]))
        if sub_choice == -1:
            return None
        if sub_choice == 0:
            continue

        action_info = category["actions"][sub_choice - 1]

        if not available[sub_choice - 1]:
            print("  시간 또는 자금이 부족합니다!")
            continue

        # 휴식은 시간 선택 가능
        hours = action_info["hours"]
        if category["type"] == ActionType.REST:
            max_sleep = min(remaining_hours, 12)
            hours = prompt_int(f"  몇 시간 수면할까요?", 1, max_sleep)
            if hours == -1:
                return None

        # 행동 실행
        request = ActionRequest(
            player_id=player.id,
            action_type=category["type"],
            specific_action=action_info["enum"].name,
            time_hours=hours,
            target_id=store.id,
        )

        result = action_service.execute_action(request)

        if result.success:
            print(f"\n  >> {result.message}")
            player = result.updated_player
            repository.save_player(player)
            remaining_hours -= result.time_consumed
        else:
            print(f"\n  !! {result.message}")

    return player


def main():
    """메인 게임 루프"""
    repository, game_service, action_service, player, store, product = init_game()

    # 게임 시작
    print(f"\n  {player.name} 사장님, 치킨집 창업을 축하합니다!")
    print(f"  초기 자금: {player.money.format_korean()}")
    print(f"  매장: {store.name} | 메뉴: {product.name}")
    print()
    input("  [Enter] 를 눌러 게임을 시작하세요...")

    current_turn = game_service.start_new_game(player)
    turn_count = 0

    while game_service.is_game_running():
        turn_count += 1
        status = game_service.get_game_status()

        # 최신 플레이어 상태 가져오기
        player = repository.get_player(player.id)
        if not player:
            break

        # 대시보드 표시
        show_dashboard(
            player,
            status["current_turn"],
            date.fromisoformat(status["current_date"]),
            store,
            product,
        )

        # 파산 체크
        if player.money.amount <= 0:
            print()
            print("  !! 자금이 바닥났습니다... 파산입니다 !!")
            print(f"  {turn_count}일 동안 운영하셨습니다.")
            break

        # === 1. 플레이어 행동 페이즈 ===
        print("\n  --- 플레이어 행동 페이즈 ---")
        player = handle_player_action_phase(repository, action_service, player, store, product)
        if player is None:
            print("\n  게임을 종료합니다. 수고하셨습니다!")
            break

        # GameLoopService의 player_action 페이즈 완료 처리
        game_service.execute_turn_phase()
        game_service.advance_phase()

        # === 2~6. 자동 페이즈 ===
        print()
        sales_result = {}
        settlement_result = {}

        # AI 행동
        ai_result = game_service.execute_turn_phase()
        game_service.advance_phase()

        # 이벤트
        event_result = game_service.execute_turn_phase()
        game_service.advance_phase()

        # 판매
        sales_result = game_service.execute_turn_phase()
        game_service.advance_phase()

        # 정산
        settlement_result = game_service.execute_turn_phase()
        game_service.advance_phase()

        # 마무리
        game_service.execute_turn_phase()
        game_service.advance_phase()  # 다음 턴으로

        # 최신 플레이어 상태 갱신
        player = repository.get_player(player.id)

        # 턴 요약
        show_turn_summary(sales_result, settlement_result, player)

        # 다음 턴 계속?
        print()
        cont = prompt("  다음 날로 진행할까요? (Enter=계속 / q=종료)", "y")
        if cont.lower() == "q":
            print(f"\n  {turn_count}일 동안 운영하셨습니다.")
            print(f"  최종 자금: {player.money.format_korean()}")
            print("  수고하셨습니다!")
            break

    print()
    print("=" * 50)
    print("       게임 종료 - 치킨마스터 2")
    print("=" * 50)


if __name__ == "__main__":
    main()
