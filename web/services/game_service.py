"""DB 기반 게임 서비스 — 4구간 하루 시스템 (PREP → BUSINESS → NIGHT → SLEEP)"""

import io
import json
import os
import random
import sys
from contextlib import contextmanager
from datetime import date
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4

from web.config import DB_PATH, EVENTS_CSV
from web.services.balance import (
    INITIAL_MONEY, INITIAL_INGREDIENT_QTY, INITIAL_INGREDIENT_QUALITY,
    INGREDIENT_PURCHASE_PRICE, INITIAL_SELLING_PRICE, INITIAL_AWARENESS, MONTHLY_RENT,
    INITIAL_REPUTATION, INITIAL_STATS,
    DEFAULT_TIME, TIME_RANGES,
    PREPARE_GAIN, PREPARE_INGREDIENT_COST, ORDER_INGREDIENT_GAIN,
    REPUTATION_MIN, REPUTATION_MAX,
    BUSINESS_DECISIONS,
    FATIGUE_RECOVERY_PER_HOUR,
    PRICE_STEP, PRICE_MIN, PRICE_MAX,
    INITIAL_FRESHNESS, FRESHNESS_MIN, FRESHNESS_MAX,
    ORDER_INGREDIENT_FRESHNESS,
    FRESHNESS_BASE_DECAY, FRESHNESS_QTY_DIVISOR, FRESHNESS_HOARDING_PENALTY,
    FRESHNESS_REPUTATION_THRESHOLD, FRESHNESS_REPUTATION_PENALTY,
    TURNAWAY_REP_DIVISOR, TURNAWAY_REP_MAX_PENALTY,
)
from web.services.engines.sales_engine import calculate_sales, generate_hourly_forecast
from web.services.engines.decision_engine import generate_decisions, apply_decision_effects


@contextmanager
def suppress_stdout():
    old = sys.stdout
    sys.stdout = io.StringIO()
    try:
        yield sys.stdout
    finally:
        sys.stdout = old


# ── 구간별 행동 분류 ──

from common.enums.action_type import (
    ActionType, CookingAction, AdvertisingAction,
    OperationAction, ResearchAction, PersonalAction, RestAction,
)
from application.action_service import ActionService

PREP_ACTIONS = [
    {
        "key": "COOKING", "name": "조리 준비", "icon": "🍳",
        "type": ActionType.COOKING,
        "actions": [
            {"enum": CookingAction.PREPARE_INGREDIENTS, "name": "재료 준비", "hours": 1, "cost": 0},
            {"enum": CookingAction.INSPECT_INGREDIENTS, "name": "재료 점검", "hours": 1, "cost": 0},
        ],
    },
    {
        "key": "OPERATION", "name": "운영", "icon": "🔧",
        "type": ActionType.OPERATION,
        "actions": [
            {"enum": OperationAction.CLEAN, "name": "매장 청소", "hours": 2, "cost": 0},
            {"enum": OperationAction.EQUIPMENT_CHECK, "name": "장비 점검", "hours": 1, "cost": 0},
        ],
    },
    {
        "key": "REST", "name": "휴식", "icon": "☕",
        "type": ActionType.REST,
        "actions": [
            {"enum": RestAction.SLEEP, "name": "휴식", "hours": 0.5, "cost": 0},
        ],
    },
]

NIGHT_ACTIONS = [
    {
        "key": "RESEARCH", "name": "연구", "icon": "🔬",
        "type": ActionType.RESEARCH,
        "actions": [
            {"enum": ResearchAction.RECIPE, "name": "레시피 연구", "hours": 3, "cost": 0},
            {"enum": ResearchAction.MANAGEMENT, "name": "경영 연구", "hours": 3, "cost": 0},
            {"enum": ResearchAction.ADVERTISING_RESEARCH, "name": "광고 연구", "hours": 3, "cost": 0},
            {"enum": ResearchAction.SERVICE, "name": "서비스 연구", "hours": 3, "cost": 0},
        ],
    },
    {
        "key": "PERSONAL", "name": "개인", "icon": "🧑",
        "type": ActionType.PERSONAL,
        "actions": [
            {"enum": PersonalAction.STUDY, "name": "학습", "hours": 2, "cost": 0},
            {"enum": PersonalAction.EXERCISE, "name": "운동", "hours": 2, "cost": 0},
        ],
    },
    {
        "key": "ADVERTISING", "name": "광고", "icon": "📢",
        "type": ActionType.ADVERTISING,
        "actions": [
            {"enum": AdvertisingAction.FLYER, "name": "전단지 배포", "hours": 2, "cost": 50000},
            {"enum": AdvertisingAction.ONLINE_AD, "name": "온라인 광고", "hours": 1, "cost": 100000},
            {"enum": AdvertisingAction.DELIVERY_APP, "name": "배달앱 등록", "hours": 1, "cost": 30000},
        ],
    },
    {
        "key": "OPERATION", "name": "운영", "icon": "🔧",
        "type": ActionType.OPERATION,
        "actions": [
            {"enum": OperationAction.ORDER_INGREDIENTS, "name": "재료 주문", "hours": 1, "cost": 200000},
            {"enum": OperationAction.HIRE_PARTTIME, "name": "알바 고용", "hours": 2, "cost": 80000},
        ],
    },
    {
        "key": "REST", "name": "휴식", "icon": "☕",
        "type": ActionType.REST,
        "actions": [
            {"enum": RestAction.SLEEP, "name": "휴식", "hours": 0.5, "cost": 0},
        ],
    },
]

STOCK_EFFECTS = {
    "PREPARE_INGREDIENTS": {"ingredient_cost": PREPARE_INGREDIENT_COST, "prepared_gain": PREPARE_GAIN},
    "ORDER_INGREDIENTS": {"ingredient_cost": 0, "ingredient_gain": ORDER_INGREDIENT_GAIN},
}

ACTION_EXP_INFO = {
    CookingAction.PREPARE_INGREDIENTS: "요리+4",
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
    PersonalAction.STUDY: "기술+15, 경영+5",
    PersonalAction.EXERCISE: "체력+20",
    RestAction.SLEEP: "",
}

FATIGUE_INFO = ActionService.ACTION_FATIGUE_COSTS

ACTION_TYPE_MAP = {at.name: at for at in ActionType}

# ── 영업 미니 의사결정 (balance.py에서 로드) ──

BUSINESS_DECISION_TEMPLATES = [
    {
        "decision_key": d["key"],
        "title": d["title"],
        "description": d["desc"],
        "choice_a_label": d["a_label"],
        "choice_b_label": d["b_label"],
        "choice_a_effect": d["a_effect"],
        "choice_b_effect": d["b_effect"],
    }
    for d in BUSINESS_DECISIONS
]


def _find_action_meta(action_type_str: str, specific_action: str, segment: str = None):
    """구간별 ACTION 카테고리에서 행동 메타 검색"""
    cats = PREP_ACTIONS if segment == "PREP" else NIGHT_ACTIONS if segment == "NIGHT" else PREP_ACTIONS + NIGHT_ACTIONS
    for cat in cats:
        if cat["key"] == action_type_str:
            for a in cat["actions"]:
                if a["enum"].name == specific_action:
                    return cat, a
    return None, None


class GameService:
    """DB 기반 게임 오케스트레이터 — 4구간 하루 시스템"""

    def __init__(self, db_path: str = None):
        self._db_path = db_path or DB_PATH
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)

    def _repo(self, game_id: str = None):
        from adapters.repository.sqlite_repository import SQLiteRepository
        return SQLiteRepository(self._db_path, game_id)

    def _build_engine(self, repo):
        from adapters.repository.csv_event_loader import CSVEventLoader
        from application.game_loop_service import GameLoopService
        from application.sales_service import SalesService
        from application.event_service import EventService
        from application.settlement_service import SettlementService
        from application.ai_service_optimized import AIService

        action_service = ActionService(repo)
        ai_service = AIService(repo)
        event_loader = CSVEventLoader(EVENTS_CSV)
        event_service = EventService(repo, event_loader)
        sales_service = SalesService(repo)
        settlement_service = SettlementService(repo)

        game_loop = GameLoopService(
            repository=repo,
            action_service=action_service,
            ai_service=ai_service,
            event_service=event_service,
            sales_service=sales_service,
            settlement_service=settlement_service,
        )
        return game_loop, action_service

    # ── 시간 계산 유틸 ──

    @staticmethod
    def _calc_segment_hours(wake: int, open_t: int, close: int, sleep: int) -> Dict[str, int]:
        """4구간 시간 계산. sleep은 24를 넘을 수 있음 (새벽=25,26)"""
        return {
            "PREP": max(0, open_t - wake),
            "BUSINESS": max(0, close - open_t),
            "NIGHT": max(0, sleep - close),
            "SLEEP": max(0, (wake + 24) - sleep),  # 다음날 기상까지
        }

    def _get_segment_hours(self, game_id: str) -> Dict[str, int]:
        gs = self._repo(game_id).get_game_state(game_id)
        if not gs:
            return {"PREP": 3, "BUSINESS": 11, "NIGHT": 3, "SLEEP": 7}
        return self._calc_segment_hours(
            gs["wake_time"], gs["open_time"], gs["close_time"], gs["sleep_time"]
        )

    def _auto_fill_rest(self, repo, game_id: str, turn_number: int, segment: str):
        """남는 시간을 0.5h 휴식으로 자동 채우기"""
        seg_hours = self._get_segment_hours(game_id)
        total = seg_hours.get(segment, 0)
        used = repo.get_total_queued_hours(game_id, turn_number, segment)
        remaining = total - used

        if remaining <= 0:
            return

        queued = repo.get_queued_actions(game_id, turn_number, segment)
        next_slot = max((q["slot_order"] for q in queued), default=-1) + 1

        rest_unit = 0.5
        while remaining >= rest_unit:
            repo.queue_action(
                game_id, turn_number, next_slot,
                action_type="REST", specific_action="SLEEP",
                hours=rest_unit, cost=0, segment=segment,
            )
            next_slot += 1
            remaining -= rest_unit

    # ── 신선도 유틸 ──

    @staticmethod
    def _calc_freshness_decay(ingredient_qty):
        return FRESHNESS_BASE_DECAY + (ingredient_qty // FRESHNESS_QTY_DIVISOR) * FRESHNESS_HOARDING_PENALTY

    @staticmethod
    def _weighted_freshness(old_qty, old_freshness, new_qty, new_freshness=ORDER_INGREDIENT_FRESHNESS):
        total = old_qty + new_qty
        if total <= 0:
            return new_freshness
        return (old_qty * old_freshness + new_qty * new_freshness) / total

    # ── Game lifecycle ──

    def create_game(self, player_name: str) -> Dict[str, Any]:
        game_id = uuid4().hex[:12]
        repo = self._repo(game_id)
        repo.create_game(game_id, player_name)

        game_loop, _ = self._build_engine(repo)

        from core.domain.player import Player
        from core.domain.store import Store
        from core.domain.product import Product
        from core.domain.inventory import Inventory
        from core.domain.value_objects import Money, Progress, StatValue, Experience

        base_exp = Experience(0)
        player = Player.create_new(name=player_name, initial_money=INITIAL_MONEY)

        product_id = uuid4()
        ingredient = Inventory(
            id=uuid4(), name="닭고기", quantity=INITIAL_INGREDIENT_QTY,
            quality=INITIAL_INGREDIENT_QUALITY, purchase_price=Money(INGREDIENT_PURCHASE_PRICE),
        )
        product = Product(
            id=product_id, recipe_id=uuid4(),
            name="황금 올리브 치킨", selling_price=Money(INITIAL_SELLING_PRICE),
            research_progress=Progress(0), ingredients=[ingredient],
            awareness=INITIAL_AWARENESS,
        )
        repo.save_product(product)

        store_id = uuid4()
        store = Store(
            id=store_id, owner_id=uuid4(), name="본점",
            monthly_rent=Money(MONTHLY_RENT), product_ids=(product_id,),
            inventory_item_ids=(), parttime_worker_ids=(),
            is_first_store=True,
        )
        repo.save_store(store)

        player = player._replace(
            store_ids=(store_id,),
            cooking=StatValue(INITIAL_STATS["cooking"], base_exp),
            management=StatValue(INITIAL_STATS["management"], base_exp),
            service=StatValue(INITIAL_STATS["service"], base_exp),
            tech=StatValue(INITIAL_STATS["tech"], base_exp),
            stamina=StatValue(INITIAL_STATS["stamina"], base_exp),
        )
        store = store._replace(owner_id=player.id)
        repo.save_store(store)

        with suppress_stdout():
            game_loop.start_new_game(player)

        # Initialize segment to PREP
        repo.update_game_state(game_id, current_segment="PREP", segment_hours_used=0,
                               prepared_qty=0, reputation=INITIAL_REPUTATION,
                               ingredient_freshness=INITIAL_FRESHNESS)

        return self.get_state(game_id)

    def get_state(self, game_id: str) -> Dict[str, Any]:
        repo = self._repo(game_id)
        game = repo.get_game(game_id)
        if not game:
            return None

        player = repo.get_player_by_game(game_id)
        store = repo.get_store_by_game(game_id)
        product = repo.get_product_by_game(game_id)
        turn = repo.load_current_turn()
        gs = repo.get_game_state(game_id)

        from web.services.serializers import serialize_player, serialize_store, serialize_turn

        segment_hours = self._get_segment_hours(game_id)
        current_segment = gs["current_segment"] if gs else "PREP"

        return {
            "game_id": game_id,
            "player": serialize_player(player) if player else None,
            "store": serialize_store(store, product) if store and product else None,
            "turn": serialize_turn(turn, segment_hours.get(current_segment, 0)) if turn else None,
            "is_running": bool(game.get("is_active")),
            "ingredient_qty": gs["ingredient_qty"] if gs else INITIAL_INGREDIENT_QTY,
            "prepared_qty": gs["prepared_qty"] if gs else 0,
            "ingredient_freshness": gs["ingredient_freshness"] if gs else INITIAL_FRESHNESS,
            "reputation": gs["reputation"] if gs else INITIAL_REPUTATION,
            "current_segment": current_segment,
            "current_phase": current_segment,  # backwards compat for frontend
            "time_config": {
                "wake_time": gs["wake_time"] if gs else DEFAULT_TIME["wake"],
                "open_time": gs["open_time"] if gs else DEFAULT_TIME["open"],
                "close_time": gs["close_time"] if gs else DEFAULT_TIME["close"],
                "sleep_time": gs["sleep_time"] if gs else DEFAULT_TIME["sleep"],
            },
            "segment_hours": segment_hours,
        }

    def list_games(self) -> List[Dict[str, Any]]:
        repo = self._repo()
        return repo.list_active_games()

    def delete_game(self, game_id: str):
        repo = self._repo(game_id)
        repo.deactivate_game(game_id)

    # ── Time config ──

    def update_time_config(self, game_id: str, wake: int, open_t: int, close: int, sleep: int) -> Dict[str, Any]:
        # Validate ranges (from balance.py)
        wake = max(TIME_RANGES["wake"][0], min(TIME_RANGES["wake"][1], wake))
        open_t = max(TIME_RANGES["open"][0], min(TIME_RANGES["open"][1], open_t))
        close = max(TIME_RANGES["close"][0], min(TIME_RANGES["close"][1], close))
        sleep = max(TIME_RANGES["sleep"][0], min(TIME_RANGES["sleep"][1], sleep))
        if open_t <= wake:
            open_t = wake + 1
        if close <= open_t:
            close = open_t + 1
        if sleep <= close:
            sleep = close + 1

        repo = self._repo(game_id)
        repo.update_game_state(game_id,
            wake_time=wake, open_time=open_t,
            close_time=close, sleep_time=sleep,
        )
        return {
            "time_config": {"wake_time": wake, "open_time": open_t, "close_time": close, "sleep_time": sleep},
            "segment_hours": self._calc_segment_hours(wake, open_t, close, sleep),
        }

    # ── Available actions (segment-aware) ──

    def get_available_actions(self, game_id: str) -> Dict[str, Any]:
        repo = self._repo(game_id)
        player = repo.get_player_by_game(game_id)
        gs = repo.get_game_state(game_id)
        turn = repo.load_current_turn()
        if not player or not gs:
            return {"segment_hours": 0, "categories": []}

        current_segment = gs["current_segment"]
        segment_hours = self._get_segment_hours(game_id)
        total_hours = segment_hours.get(current_segment, 0)

        queued_hours = repo.get_total_queued_hours(game_id, turn.turn_number, current_segment) if turn else 0
        queued_cost = repo.get_total_queued_cost(game_id, turn.turn_number, current_segment) if turn else 0
        available_hours = total_hours - queued_hours
        available_money = player.money.amount - queued_cost

        # Pick the right action set
        if current_segment == "PREP":
            action_cats = PREP_ACTIONS
        elif current_segment == "NIGHT":
            action_cats = NIGHT_ACTIONS
        else:
            action_cats = []

        categories = []
        for cat in action_cats:
            actions = []
            for a in cat["actions"]:
                hours = a["hours"]
                cost = a["cost"]
                fatigue = FATIGUE_INFO.get(a["enum"], 0)
                effect = STOCK_EFFECTS.get(a["enum"].name, {})
                needs_ingredients = effect.get("ingredient_cost", 0)

                can_do = (hours <= available_hours
                          and cost <= available_money
                          and gs["ingredient_qty"] >= needs_ingredients)
                actions.append({
                    "action_type": cat["key"],
                    "specific_action": a["enum"].name,
                    "name": a["name"],
                    "hours": hours,
                    "cost": cost,
                    "fatigue_per_hour": fatigue,
                    "exp_info": ACTION_EXP_INFO.get(a["enum"], ""),
                    "can_do": can_do,
                    "ingredient_cost": needs_ingredients,
                    "prepared_gain": effect.get("prepared_gain", 0),
                    "ingredient_gain": effect.get("ingredient_gain", 0),
                })
            categories.append({
                "key": cat["key"],
                "name": cat["name"],
                "icon": cat["icon"],
                "actions": actions,
            })

        return {
            "current_segment": current_segment,
            "segment_hours": total_hours,
            "available_hours": available_hours,
            "categories": categories,
        }

    # ── Queue management (segment-aware) ──

    def queue_action(self, game_id: str, action_type: str, specific_action: str) -> Dict[str, Any]:
        repo = self._repo(game_id)
        player = repo.get_player_by_game(game_id)
        gs = repo.get_game_state(game_id)
        turn = repo.load_current_turn()
        if not player or not gs or not turn:
            raise ValueError("게임을 찾을 수 없습니다")

        current_segment = gs["current_segment"]
        if current_segment not in ("PREP", "NIGHT"):
            raise ValueError(f"현재 구간({current_segment})에서는 행동을 큐잉할 수 없습니다")

        cat_meta, action_meta = _find_action_meta(action_type, specific_action, current_segment)
        if not action_meta:
            raise ValueError(f"잘못된 행동: {action_type}/{specific_action}")

        hours = action_meta["hours"]
        cost = action_meta["cost"]
        segment_hours = self._get_segment_hours(game_id)
        total_hours = segment_hours.get(current_segment, 0)
        queued_hours = repo.get_total_queued_hours(game_id, turn.turn_number, current_segment)
        queued_cost = repo.get_total_queued_cost(game_id, turn.turn_number, current_segment)

        if queued_hours + hours > total_hours:
            raise ValueError("시간이 부족합니다")
        if player.money.amount < queued_cost + cost:
            raise ValueError("자금이 부족합니다")

        effect = STOCK_EFFECTS.get(specific_action, {})
        needs_ingredients = effect.get("ingredient_cost", 0)
        if needs_ingredients > 0 and gs["ingredient_qty"] < needs_ingredients:
            raise ValueError("원재료가 부족합니다")

        existing = repo.get_queued_actions(game_id, turn.turn_number, current_segment)
        slot_order = len(existing)

        repo.queue_action(game_id, turn.turn_number, slot_order,
                          action_type, specific_action, hours, cost, current_segment)

        return self.get_queue(game_id)

    def remove_from_queue(self, game_id: str, slot_order: int) -> Dict[str, Any]:
        repo = self._repo(game_id)
        turn = repo.load_current_turn()
        if not turn:
            raise ValueError("게임을 찾을 수 없습니다")
        repo.remove_queued_action(game_id, turn.turn_number, slot_order)
        return self.get_queue(game_id)

    def get_queue(self, game_id: str) -> Dict[str, Any]:
        repo = self._repo(game_id)
        turn = repo.load_current_turn()
        gs = repo.get_game_state(game_id)
        if not turn or not gs:
            return {"queue": [], "total_hours": 0, "segment_hours": 0, "available_hours": 0}

        current_segment = gs["current_segment"]
        actions = repo.get_queued_actions(game_id, turn.turn_number, current_segment)
        total_hours = sum(a["hours"] for a in actions)
        segment_hours = self._get_segment_hours(game_id).get(current_segment, 0)

        enriched = []
        for a in actions:
            _, meta = _find_action_meta(a["action_type"], a["specific_action"], current_segment)
            enriched.append({
                "slot_order": a["slot_order"],
                "action_type": a["action_type"],
                "specific_action": a["specific_action"],
                "name": meta["name"] if meta else a["specific_action"],
                "hours": a["hours"],
                "cost": a["cost"],
                "status": a["status"],
            })

        return {
            "queue": enriched,
            "total_hours": total_hours,
            "segment_hours": segment_hours,
            "remaining_hours": segment_hours,  # backwards compat
            "available_hours": segment_hours - total_hours,
        }

    # ── Prep confirm → BUSINESS ──

    def confirm_prep_actions(self, game_id: str) -> Dict[str, Any]:
        repo = self._repo(game_id)
        player = repo.get_player_by_game(game_id)
        gs = repo.get_game_state(game_id)
        turn = repo.load_current_turn()
        store = repo.get_store_by_game(game_id)
        if not player or not gs or not turn or not store:
            raise ValueError("게임을 찾을 수 없습니다")

        if gs["current_segment"] != "PREP":
            raise ValueError("준비 구간이 아닙니다")

        # 남는 시간을 자동 휴식으로 채우기
        self._auto_fill_rest(repo, game_id, turn.turn_number, "PREP")

        queued = repo.get_queued_actions(game_id, turn.turn_number, "PREP")
        action_service = ActionService(repo)
        results = []

        from application.action_service import ActionRequest as DomainActionRequest

        ingredient_qty = gs["ingredient_qty"]
        prepared_qty = gs["prepared_qty"]

        # 스탯 읽기 (d100 주사위 보정용)
        stats = {
            "cooking": player.cooking.base_value,
            "management": player.management.base_value,
            "service": player.service.base_value,
            "tech": player.tech.base_value,
            "stamina": player.stamina.base_value,
        }

        # 행동별 관련 스탯 매핑
        ACTION_STAT = {
            "PREPARE_INGREDIENTS": "cooking",
            "INSPECT_INGREDIENTS": "cooking",
            "CLEAN": "service",
            "EQUIPMENT_CHECK": "tech",
        }

        for qa in queued:
            at = ACTION_TYPE_MAP.get(qa["action_type"])
            if not at:
                results.append({"success": False, "message": f"잘못된 행동: {qa['action_type']}"})
                continue

            # D100 주사위 + 스탯 기반 보정
            dice_roll = random.randint(1, 100)
            stat_key = ACTION_STAT.get(qa["specific_action"], "cooking")
            stat_value = stats.get(stat_key, 10)
            dice_factor = max(0.5, (stat_value + dice_roll) / 100)  # 스탯+주사위 합산 %

            domain_req = DomainActionRequest(
                player_id=player.id,
                action_type=at,
                specific_action=qa["specific_action"],
                time_hours=qa["hours"],
                target_id=store.id,
            )

            with suppress_stdout():
                result = action_service.execute_action(domain_req)

            if result.success:
                effect = STOCK_EFFECTS.get(qa["specific_action"], {})
                ingredient_qty -= effect.get("ingredient_cost", 0)
                ingredient_qty += effect.get("ingredient_gain", 0)

                # Dice affects prepared_qty gain
                base_prepared = effect.get("prepared_gain", 0)
                if base_prepared > 0:
                    prepared_qty += max(1, int(base_prepared * dice_factor))
                else:
                    prepared_qty += base_prepared

            player = repo.get_player_by_game(game_id)

            # D100 quality label
            dice_quality = "CRITICAL!" if dice_roll >= 95 else "GREAT" if dice_roll >= 75 else "GOOD" if dice_roll >= 40 else "MISS" if dice_roll <= 5 else "normal"

            results.append({
                "success": result.success,
                "message": result.message,
                "time_consumed": result.time_consumed,
                "fatigue_change": result.fatigue_change,
                "money_change": result.money_change,
                "experience_gains": result.experience_gains,
                "dice_roll": dice_roll,
                "dice_factor": round(dice_factor, 2),
                "dice_quality": dice_quality,
            })

        # Update state → transition to BUSINESS
        repo.update_game_state(game_id,
            ingredient_qty=ingredient_qty,
            prepared_qty=prepared_qty, current_segment="BUSINESS",
            segment_hours_used=0,
        )

        repo.save_phase_result(game_id, turn.turn_number, "PREP", {"actions": results})
        repo.clear_queued_actions(game_id, turn.turn_number)

        return {
            "success": True,
            "action_results": results,
            "ingredient_qty": ingredient_qty,
            "prepared_qty": prepared_qty,
            "ingredient_freshness": gs["ingredient_freshness"],
            "current_segment": "BUSINESS",
        }

    # ── Business start (generate decisions) ──

    def start_business(self, game_id: str) -> Dict[str, Any]:
        repo = self._repo(game_id)
        gs = repo.get_game_state(game_id)
        turn = repo.load_current_turn()
        if not gs or not turn:
            raise ValueError("게임을 찾을 수 없습니다")

        if gs["current_segment"] != "BUSINESS":
            raise ValueError("영업 구간이 아닙니다")

        segment_hours = self._get_segment_hours(game_id)
        business_hours = segment_hours.get("BUSINESS", 11)

        # Clear old decisions
        repo.clear_business_decisions(game_id, turn.turn_number)

        # Generate random decisions via engine
        generated = generate_decisions(business_hours, BUSINESS_DECISION_TEMPLATES)

        decisions = []
        for decision in generated:
            dec_id = repo.save_business_decision(game_id, turn.turn_number, decision)
            decisions.append({
                "id": dec_id,
                **decision,
            })

        # Generate hourly forecast for client timelapse
        product = repo.get_product_by_game(game_id)
        price = product.selling_price.amount if product else INITIAL_SELLING_PRICE
        hourly_forecast = generate_hourly_forecast(
            business_hours=business_hours,
            reputation=gs["reputation"],
            prepared_qty=gs["prepared_qty"],
            ingredient_freshness=gs["ingredient_freshness"],
            price=price,
        )

        return {
            "business_hours": business_hours,
            "prepared_qty": gs["prepared_qty"],
            "ingredient_qty": gs["ingredient_qty"],
            "ingredient_freshness": gs["ingredient_freshness"],
            "decisions": decisions,
            "hourly_forecast": hourly_forecast,
            "price": price,
            "current_segment": "BUSINESS",
            "balance": {
                "prepare_gain": PREPARE_GAIN,
                "prepare_cost": PREPARE_INGREDIENT_COST,
                "rest_fatigue_recovery": 16,
            },
        }

    # ── Submit decision ──

    def submit_decision(self, game_id: str, decision_id: int, choice: str) -> Dict[str, Any]:
        repo = self._repo(game_id)
        gs = repo.get_game_state(game_id)
        turn = repo.load_current_turn()
        player = repo.get_player_by_game(game_id)
        if not gs or not turn or not player:
            raise ValueError("게임을 찾을 수 없습니다")

        decisions = repo.get_business_decisions(game_id, turn.turn_number)
        target = None
        for d in decisions:
            if d["id"] == decision_id:
                target = d
                break
        if not target:
            raise ValueError("의사결정을 찾을 수 없습니다")

        if choice not in ("A", "B"):
            raise ValueError("선택은 A 또는 B여야 합니다")

        effect = target["choice_a_effect"] if choice == "A" else target["choice_b_effect"]

        # Apply immediate effects via engine
        applied = apply_decision_effects(
            effect,
            ingredient_qty=gs["ingredient_qty"],
            reputation=gs["reputation"],
            money=player.money.amount,
            fatigue=player.fatigue.value,
        )

        from core.domain.value_objects import Money, Percentage

        if applied["new_money"] != player.money.amount:
            player = player._replace(money=Money(applied["new_money"]))
            repo.save_player(player)

        if applied["new_fatigue"] != player.fatigue.value:
            player = player._replace(fatigue=Percentage(applied["new_fatigue"]))
            repo.save_player(player)

        # 재료 획득 시 가중 평균 신선도 적용
        ingredient_gain = effect.get("ingredient_gain", 0)
        update_kwargs = {
            "ingredient_qty": applied["new_ingredient_qty"],
            "reputation": applied["new_reputation"],
        }
        if ingredient_gain > 0:
            old_qty = gs["ingredient_qty"]
            old_freshness = gs["ingredient_freshness"]
            new_freshness = self._weighted_freshness(
                old_qty, old_freshness, ingredient_gain, ORDER_INGREDIENT_FRESHNESS,
            )
            update_kwargs["ingredient_freshness"] = round(new_freshness, 1)

        repo.update_game_state(game_id, **update_kwargs)
        repo.update_business_decision(decision_id, choice, effect)

        # Re-read state after updates for accurate response
        gs_after = repo.get_game_state(game_id)

        return {
            "decision_id": decision_id,
            "choice": choice,
            "effect": effect,
            "label": target["choice_a_label"] if choice == "A" else target["choice_b_label"],
            # 클라이언트 상태 동기화용 — SSOT
            "prepared_qty": gs_after["prepared_qty"],
            "ingredient_qty": gs_after["ingredient_qty"],
            "ingredient_freshness": gs_after["ingredient_freshness"],
            "reputation": gs_after["reputation"],
            "money": player.money.amount,
            "fatigue": player.fatigue.value,
        }

    # ── Complete business → NIGHT ──

    def complete_business(self, game_id: str) -> Dict[str, Any]:
        repo = self._repo(game_id)
        gs = repo.get_game_state(game_id)
        turn = repo.load_current_turn()
        player = repo.get_player_by_game(game_id)
        store = repo.get_store_by_game(game_id)
        product = repo.get_product_by_game(game_id)
        if not gs or not turn or not player or not store or not product:
            raise ValueError("게임을 찾을 수 없습니다")

        if gs["current_segment"] != "BUSINESS":
            raise ValueError("영업 구간이 아닙니다")

        segment_hours = self._get_segment_hours(game_id)
        business_hours = segment_hours.get("BUSINESS", 11)

        # Calculate sales via engine
        prepared_qty = gs["prepared_qty"]
        ingredient_qty = gs["ingredient_qty"]
        ingredient_freshness = gs["ingredient_freshness"]

        decisions = repo.get_business_decisions(game_id, turn.turn_number)
        price = product.selling_price.amount

        sales = calculate_sales(
            business_hours=business_hours,
            reputation=gs["reputation"],
            prepared_qty=prepared_qty,
            ingredient_freshness=ingredient_freshness,
            decisions=decisions,
            price=price,
        )

        base_customers = sales["base_customers"]
        freshness_mult = sales["freshness_mult"]
        total_customers = sales["total_customers"]
        actual_served = sales["actual_served"]
        turned_away = sales["turned_away"]
        used_prepared = sales["used_prepared"]
        remaining_prepared = sales["remaining_prepared"]
        effective_price = sales["effective_price"]
        total_sales = sales["total_sales"]
        total_revenue = total_sales

        # Apply revenue to player
        from core.domain.value_objects import Money
        new_money = player.money.amount + total_revenue
        player = player._replace(money=Money(new_money))
        repo.save_player(player)

        # 돌아간 고객 → 평판 페널티
        turnaway_rep_penalty = 0
        if turned_away > 0:
            turnaway_rep_penalty = min(turned_away // TURNAWAY_REP_DIVISOR, TURNAWAY_REP_MAX_PENALTY)
            if turnaway_rep_penalty > 0:
                new_rep = max(REPUTATION_MIN, gs["reputation"] - turnaway_rep_penalty)
                repo.update_game_state(game_id, reputation=new_rep)

        # Run engine's auto phases (AI, EVENT, SETTLEMENT) in background
        game_loop, _ = self._build_engine(repo)
        game_loop._current_turn = turn
        game_loop._is_running = True
        game_loop._current_player_id = player.id

        ai_result = {}
        event_result = {}
        settlement_result = {}

        with suppress_stdout():
            # AI_ACTION
            try:
                ai_result = dict(game_loop.execute_turn_phase())
            except Exception:
                ai_result = {}
            game_loop.advance_phase()

            # EVENT
            try:
                event_result = dict(game_loop.execute_turn_phase())
            except Exception:
                event_result = {}
            game_loop.advance_phase()

            # SALES — we handle manually, just advance
            from core.ports.sales_port import SalesResult
            game_loop._current_sales_results[player.id] = SalesResult(
                total_revenue=total_revenue,
                total_customers=actual_served,
                sold_products={},
                feedbacks=[],
                market_share=0.0,
            )
            try:
                game_loop.execute_turn_phase()
            except Exception:
                pass
            game_loop.advance_phase()

            # SETTLEMENT
            try:
                settlement_result = dict(game_loop.execute_turn_phase())
            except Exception:
                settlement_result = {}
            game_loop.advance_phase()

            # CLEANUP
            try:
                game_loop.execute_turn_phase()
            except Exception:
                pass
            # Don't advance past cleanup yet — we stay in this turn

        # Update game state → NIGHT
        repo.update_game_state(game_id,
            prepared_qty=remaining_prepared,
            current_segment="NIGHT", segment_hours_used=0,
        )

        # Save results
        business_summary = {
            "business_hours": business_hours,
            "base_customers": base_customers,
            "freshness_mult": freshness_mult,
            "total_customers": total_customers,
            "actual_served": actual_served,
            "turned_away": turned_away,
            "turnaway_rep_penalty": turnaway_rep_penalty,
            "total_sales": total_sales,
            "effective_price": effective_price,
            "prepared_used": used_prepared,
            "decisions": [
                {
                    "title": d["title"],
                    "choice": d["player_choice"],
                    "effect": d["effect_json"],
                }
                for d in decisions if d["player_choice"]
            ],
        }
        repo.save_phase_result(game_id, turn.turn_number, "BUSINESS", business_summary)

        # Refresh player after engine
        player = repo.get_player_by_game(game_id)
        from web.services.serializers import serialize_player

        return {
            "summary": business_summary,
            "prepared_qty": remaining_prepared,
            "ingredient_qty": ingredient_qty,
            "ingredient_freshness": ingredient_freshness,
            "current_segment": "NIGHT",
            "player": serialize_player(player) if player else None,
            "ai_result": ai_result,
            "event_result": event_result,
            "settlement_result": settlement_result,
        }

    # ── Business mid-action (PREPARE or REST during business) ──

    def business_action(self, game_id: str, action: str) -> Dict[str, Any]:
        """영업 중 재료 준비 또는 휴식 (1시간 소모)"""
        repo = self._repo(game_id)
        gs = repo.get_game_state(game_id)
        player = repo.get_player_by_game(game_id)
        if not gs or not player:
            raise ValueError("게임을 찾을 수 없습니다")
        if gs["current_segment"] != "BUSINESS":
            raise ValueError("영업 구간이 아닙니다")

        from core.domain.value_objects import Money, Percentage

        ingredient_qty = gs["ingredient_qty"]
        prepared_qty = gs["prepared_qty"]
        fatigue = player.fatigue.value
        message = ""

        if action == "PREPARE":
            if ingredient_qty < PREPARE_INGREDIENT_COST:
                raise ValueError("원재료가 부족합니다")
            ingredient_qty -= PREPARE_INGREDIENT_COST
            prepared_qty += PREPARE_GAIN
            fatigue = min(200, fatigue + 3)  # cooking fatigue per hour
            player = player.gain_stat_experience("cooking", 8)
            message = f"재료 준비 완료! 준비량 +{PREPARE_GAIN}"
        elif action == "REST":
            fatigue = max(0, fatigue - 16)  # rest recovery per hour
            player = player.gain_stat_experience("stamina", 8)
            message = "휴식 완료! 피로 회복"
        else:
            raise ValueError(f"잘못된 행동: {action}")

        # Update player fatigue + exp
        player = player._replace(fatigue=Percentage(fatigue))
        repo.save_player(player)

        # Update game state
        hours_used = gs.get("segment_hours_used", 0) + 1
        repo.update_game_state(game_id,
            ingredient_qty=ingredient_qty,
            prepared_qty=prepared_qty,
            segment_hours_used=hours_used,
        )

        from web.services.serializers import serialize_player

        return {
            "action": action,
            "prepared_qty": prepared_qty,
            "ingredient_qty": ingredient_qty,
            "fatigue": round(fatigue, 1),
            "hours_used": hours_used,
            "message": message,
            "player": serialize_player(player),
        }

    # ── Night confirm → SLEEP ──

    def confirm_night_actions(self, game_id: str) -> Dict[str, Any]:
        repo = self._repo(game_id)
        player = repo.get_player_by_game(game_id)
        gs = repo.get_game_state(game_id)
        turn = repo.load_current_turn()
        store = repo.get_store_by_game(game_id)
        if not player or not gs or not turn or not store:
            raise ValueError("게임을 찾을 수 없습니다")

        if gs["current_segment"] != "NIGHT":
            raise ValueError("야간 구간이 아닙니다")

        # 남는 시간을 자동 휴식으로 채우기
        self._auto_fill_rest(repo, game_id, turn.turn_number, "NIGHT")

        queued = repo.get_queued_actions(game_id, turn.turn_number, "NIGHT")
        action_service = ActionService(repo)
        results = []

        from application.action_service import ActionRequest as DomainActionRequest

        ingredient_qty = gs["ingredient_qty"]
        ingredient_freshness = gs["ingredient_freshness"]

        # 스탯 읽기 (d100 주사위 보정용)
        stats = {
            "cooking": player.stats.get("cooking", {}).get("level", 10) if hasattr(player, 'stats') and isinstance(player.stats, dict) else 10,
            "management": player.stats.get("management", {}).get("level", 8) if hasattr(player, 'stats') and isinstance(player.stats, dict) else 8,
            "service": player.stats.get("service", {}).get("level", 8) if hasattr(player, 'stats') and isinstance(player.stats, dict) else 8,
            "tech": player.stats.get("tech", {}).get("level", 5) if hasattr(player, 'stats') and isinstance(player.stats, dict) else 5,
            "stamina": player.stats.get("stamina", {}).get("level", 50) if hasattr(player, 'stats') and isinstance(player.stats, dict) else 50,
        }

        # 야간 행동별 관련 스탯 매핑
        ACTION_STAT = {
            "RECIPE": "cooking",
            "MANAGEMENT": "management",
            "ADVERTISING_RESEARCH": "management",
            "SERVICE": "service",
            "STUDY": "tech",
            "EXERCISE": "stamina",
            "FLYER": "management",
            "ONLINE_AD": "tech",
            "DELIVERY_APP": "tech",
            "ORDER_INGREDIENTS": "management",
            "HIRE_PARTTIME": "management",
        }

        for qa in queued:
            at = ACTION_TYPE_MAP.get(qa["action_type"])
            if not at:
                results.append({"success": False, "message": f"잘못된 행동: {qa['action_type']}"})
                continue

            # D100 주사위 + 스탯 기반 보정
            dice_roll = random.randint(1, 100)
            stat_key = ACTION_STAT.get(qa["specific_action"], "management")
            stat_value = stats.get(stat_key, 10)
            dice_factor = max(0.5, (stat_value + dice_roll) / 100)

            domain_req = DomainActionRequest(
                player_id=player.id,
                action_type=at,
                specific_action=qa["specific_action"],
                time_hours=qa["hours"],
                target_id=store.id,
            )

            with suppress_stdout():
                result = action_service.execute_action(domain_req)

            if result.success:
                effect = STOCK_EFFECTS.get(qa["specific_action"], {})
                gain = effect.get("ingredient_gain", 0)
                if gain > 0:
                    # 재료 주문 시 가중 평균 신선도
                    old_qty = ingredient_qty
                    ingredient_qty += gain
                    ingredient_freshness = self._weighted_freshness(
                        old_qty, ingredient_freshness,
                        gain, ORDER_INGREDIENT_FRESHNESS,
                    )

            player = repo.get_player_by_game(game_id)

            dice_quality = "CRITICAL!" if dice_roll >= 95 else "GREAT" if dice_roll >= 75 else "GOOD" if dice_roll >= 40 else "MISS" if dice_roll <= 5 else "normal"

            results.append({
                "success": result.success,
                "message": result.message,
                "time_consumed": result.time_consumed,
                "fatigue_change": result.fatigue_change,
                "money_change": result.money_change,
                "experience_gains": result.experience_gains,
                "dice_roll": dice_roll,
                "dice_factor": round(dice_factor, 2),
                "dice_quality": dice_quality,
            })

        repo.update_game_state(game_id,
            ingredient_qty=ingredient_qty,
            ingredient_freshness=round(ingredient_freshness, 1),
            current_segment="SLEEP", segment_hours_used=0,
        )

        repo.save_phase_result(game_id, turn.turn_number, "NIGHT", {"actions": results})
        repo.clear_queued_actions(game_id, turn.turn_number)

        return {
            "success": True,
            "action_results": results,
            "ingredient_qty": ingredient_qty,
            "ingredient_freshness": round(ingredient_freshness, 1),
            "current_segment": "SLEEP",
        }

    # ── Sleep → next turn ──

    def execute_sleep(self, game_id: str) -> Dict[str, Any]:
        repo = self._repo(game_id)
        player = repo.get_player_by_game(game_id)
        gs = repo.get_game_state(game_id)
        turn = repo.load_current_turn()
        if not player or not gs or not turn:
            raise ValueError("게임을 찾을 수 없습니다")

        if gs["current_segment"] != "SLEEP":
            raise ValueError("수면 구간이 아닙니다")

        segment_hours = self._get_segment_hours(game_id)
        sleep_hours = segment_hours.get("SLEEP", 7)

        # Fatigue recovery (from balance.py)
        fatigue_recovered = sleep_hours * FATIGUE_RECOVERY_PER_HOUR
        from core.domain.value_objects import Percentage
        new_fatigue = max(0.0, player.fatigue.value - fatigue_recovered)
        player = player._replace(fatigue=Percentage(new_fatigue))
        repo.save_player(player)

        # 신선도 감쇄
        ingredient_qty = gs["ingredient_qty"]
        ingredient_freshness = gs["ingredient_freshness"]
        decay = self._calc_freshness_decay(ingredient_qty)
        ingredient_freshness = max(FRESHNESS_MIN, ingredient_freshness - decay)

        # 신선도가 너무 낮으면 평판 페널티
        if ingredient_freshness < FRESHNESS_REPUTATION_THRESHOLD:
            new_rep = max(REPUTATION_MIN, gs["reputation"] + FRESHNESS_REPUTATION_PENALTY)
            repo.update_game_state(game_id, reputation=new_rep)

        repo.update_game_state(game_id, ingredient_freshness=round(ingredient_freshness, 1))

        # Mark current turn as complete and create next turn
        completed_turn = turn._replace(is_complete=True)
        repo.save_turn(completed_turn)

        from datetime import timedelta
        next_turn_number = turn.turn_number + 1
        next_date = turn.game_date + timedelta(days=1)

        from core.domain.turn import Turn, GamePhase
        new_turn = Turn(
            turn_number=next_turn_number,
            game_date=next_date,
            current_phase=GamePhase.PLAYER_ACTION,
            is_complete=False,
        )
        repo.save_turn(new_turn)

        # Reset segment to PREP, reset prepared_qty for new day
        repo.update_game_state(game_id,
            current_segment="PREP", segment_hours_used=0, prepared_qty=0,
        )

        repo.save_phase_result(game_id, turn.turn_number, "SLEEP", {
            "sleep_hours": sleep_hours,
            "fatigue_recovered": fatigue_recovered,
        })

        return {
            "sleep_hours": sleep_hours,
            "fatigue_recovered": fatigue_recovered,
            "new_fatigue": round(new_fatigue, 1),
            "ingredient_freshness": round(ingredient_freshness, 1),
            "turn_number": next_turn_number,
            "game_date": next_date.isoformat(),
            "current_segment": "PREP",
        }

    # ── Price change ──

    def change_price(self, game_id: str, new_price: int) -> Dict[str, Any]:
        from core.domain.value_objects import Money
        repo = self._repo(game_id)
        product = repo.get_product_by_game(game_id)
        if not product:
            raise ValueError("제품을 찾을 수 없습니다")

        new_price = (new_price // PRICE_STEP) * PRICE_STEP
        new_price = max(PRICE_MIN, min(PRICE_MAX, new_price))

        product = product.update_selling_price(Money(new_price))
        repo.save_product(product)

        return {
            "success": True,
            "new_price": new_price,
            "new_price_formatted": Money(new_price).format_korean(),
        }
