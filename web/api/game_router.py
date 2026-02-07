"""게임 API 엔드포인트"""

from fastapi import APIRouter, HTTPException

from common.enums.action_type import (
    ActionType, CookingAction, AdvertisingAction,
    OperationAction, ResearchAction, PersonalAction, RestAction,
)
from application.action_service import ActionRequest as DomainActionRequest, ActionService
from core.domain.value_objects import Money
from core.ports.sales_port import SalesResult

from web.api.schemas import (
    CreateGameRequest, ActionRequest, PriceChangeRequest,
    GameStateResponse, AvailableActionsResponse, ActionResultResponse,
    AdvanceResultResponse,
)
from web.services.serializers import serialize_player, serialize_store, serialize_turn
from web.services.session_manager import SessionManager, suppress_stdout, STOCK_EFFECTS

router = APIRouter(prefix="/games", tags=["games"])

session_manager = SessionManager()


# ── 행동 메타 정보 (interactive_main.py에서 포팅) ──

ACTION_CATEGORIES = [
    {
        "key": "COOKING", "name": "조리", "icon": "🍳",
        "type": ActionType.COOKING,
        "actions": [
            {"enum": CookingAction.PREPARE_INGREDIENTS, "name": "재료 준비", "hours": 2, "cost": 0},
            {"enum": CookingAction.COOK, "name": "조리", "hours": 3, "cost": 0},
            {"enum": CookingAction.INSPECT_INGREDIENTS, "name": "재료 점검", "hours": 1, "cost": 0},
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
            {"enum": OperationAction.CLEAN, "name": "매장 청소", "hours": 2, "cost": 0},
            {"enum": OperationAction.EQUIPMENT_CHECK, "name": "장비 점검", "hours": 1, "cost": 0},
            {"enum": OperationAction.HIRE_PARTTIME, "name": "알바 고용", "hours": 2, "cost": 80000},
        ],
    },
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
            {"enum": PersonalAction.VACATION, "name": "휴가", "hours": 4, "cost": 150000},
            {"enum": PersonalAction.STUDY, "name": "학습", "hours": 2, "cost": 0},
            {"enum": PersonalAction.EXERCISE, "name": "운동", "hours": 2, "cost": 0},
        ],
    },
    {
        "key": "REST", "name": "휴식", "icon": "😴",
        "type": ActionType.REST,
        "actions": [
            {"enum": RestAction.SLEEP, "name": "수면", "hours": 1, "cost": 0},
        ],
    },
]

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

# 매핑: action_type 문자열 -> ActionType enum
ACTION_TYPE_MAP = {at.name: at for at in ActionType}


def _get_session(session_id: str):
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
    return session


def _build_game_state(session) -> dict:
    player = session.get_player()
    store = session.get_store()
    product = session.get_product()
    turn = session.game_service.get_current_turn()
    return {
        "session_id": session.session_id,
        "player": serialize_player(player),
        "store": serialize_store(store, product),
        "turn": serialize_turn(turn, session.remaining_hours),
        "is_running": session.game_service.is_game_running(),
        "stock": session.stock,
        "ingredient_qty": session.ingredient_qty,
    }


# ── 엔드포인트 ──

@router.post("", response_model=GameStateResponse)
def create_game(req: CreateGameRequest):
    session = session_manager.create_session(req.player_name)
    return _build_game_state(session)


@router.get("/{session_id}", response_model=GameStateResponse)
def get_game(session_id: str):
    return _build_game_state(_get_session(session_id))


@router.get("/{session_id}/actions/available")
def get_available_actions(session_id: str):
    session = _get_session(session_id)
    player = session.get_player()
    remaining = session.remaining_hours

    categories = []
    for cat in ACTION_CATEGORIES:
        actions = []
        for a in cat["actions"]:
            hours = a["hours"]
            cost = a["cost"]
            fatigue = FATIGUE_INFO.get(a["enum"], 0)
            # 재고 조건 추가
            effect = STOCK_EFFECTS.get(a["enum"].name, {})
            needs_ingredients = effect.get("ingredient_cost", 0)

            if cat["key"] == "REST":
                can_do = remaining >= 1
            else:
                can_do = (hours <= remaining
                          and cost <= player.money.amount
                          and session.ingredient_qty >= needs_ingredients)
            actions.append({
                "specific_action": a["enum"].name,
                "name": a["name"],
                "hours": hours,
                "cost": cost,
                "fatigue_per_hour": fatigue,
                "exp_info": ACTION_EXP_INFO.get(a["enum"], ""),
                "can_do": can_do,
                "ingredient_cost": needs_ingredients,
                "stock_gain": effect.get("stock_gain", 0),
                "ingredient_gain": effect.get("ingredient_gain", 0),
            })
        categories.append({
            "key": cat["key"],
            "name": cat["name"],
            "icon": cat["icon"],
            "actions": actions,
        })

    return {"remaining_hours": remaining, "categories": categories}


@router.post("/{session_id}/actions", response_model=ActionResultResponse)
def execute_action(session_id: str, req: ActionRequest):
    session = _get_session(session_id)
    player = session.get_player()
    store = session.get_store()

    action_type = ACTION_TYPE_MAP.get(req.action_type)
    if not action_type:
        raise HTTPException(status_code=400, detail=f"잘못된 행동 유형: {req.action_type}")

    # 시간 결정 — 휴식은 클라이언트가 지정, 나머지는 고정
    if action_type == ActionType.REST and req.time_hours:
        hours = max(1, min(req.time_hours, session.remaining_hours))
    else:
        # ACTION_CATEGORIES에서 시간 찾기
        hours = None
        for cat in ACTION_CATEGORIES:
            if cat["type"] == action_type:
                for a in cat["actions"]:
                    if a["enum"].name == req.specific_action:
                        hours = a["hours"]
                        break
                break
        if hours is None:
            raise HTTPException(status_code=400, detail=f"잘못된 세부 행동: {req.specific_action}")

    if hours > session.remaining_hours:
        raise HTTPException(status_code=400, detail="남은 시간이 부족합니다")

    domain_req = DomainActionRequest(
        player_id=player.id,
        action_type=action_type,
        specific_action=req.specific_action,
        time_hours=hours,
        target_id=store.id,
    )

    # 재고 사전 검사
    effect = STOCK_EFFECTS.get(req.specific_action, {})
    needs_ingredients = effect.get("ingredient_cost", 0)
    if needs_ingredients > 0 and session.ingredient_qty < needs_ingredients:
        raise HTTPException(status_code=400, detail=f"원재료가 부족합니다 (보유: {session.ingredient_qty}, 필요: {needs_ingredients})")

    result = session.action_service.execute_action(domain_req)

    if result.success:
        session.remaining_hours -= result.time_consumed

        # 재고 효과 적용
        if needs_ingredients > 0:
            session.ingredient_qty -= needs_ingredients
        session.ingredient_qty += effect.get("ingredient_gain", 0)
        session.stock += effect.get("stock_gain", 0)

    return {
        "success": result.success,
        "message": result.message,
        "time_consumed": result.time_consumed,
        "fatigue_change": result.fatigue_change,
        "money_change": result.money_change,
        "experience_gains": result.experience_gains,
        "stock": session.stock,
        "ingredient_qty": session.ingredient_qty,
    }


@router.post("/{session_id}/advance", response_model=AdvanceResultResponse)
def advance_turn(session_id: str):
    """플레이어 행동 페이즈 종료 후 나머지 자동 페이즈 실행 (AI->이벤트->판매->정산->마무리)"""
    session = _get_session(session_id)
    gs = session.game_service

    player = session.get_player()

    with suppress_stdout():
        # 플레이어 행동 페이즈 완료 처리
        gs.execute_turn_phase()
        gs.advance_phase()

        phases = []

        # AI 행동
        ai_result = gs.execute_turn_phase()
        gs.advance_phase()
        phases.append({"phase": "AI_ACTION", **ai_result})

        # 이벤트
        event_result = gs.execute_turn_phase()
        gs.advance_phase()
        phases.append({"phase": "EVENT", **event_result})

        # 판매
        sales_result = gs.execute_turn_phase()
        gs.advance_phase()

        # ── 재고로 판매량 제한 ──
        raw_customers = sales_result.get("customer_count", 0)
        actual_sold = min(raw_customers, session.stock)
        if raw_customers > 0:
            ratio = actual_sold / raw_customers
        else:
            ratio = 0
        capped_revenue = int(sales_result.get("total_sales", 0) * ratio)
        session.stock -= actual_sold

        # 엔진 내부 SalesResult도 보정 (정산이 이 값을 읽음)
        if player.id in gs._current_sales_results:
            old_sr = gs._current_sales_results[player.id]
            gs._current_sales_results[player.id] = SalesResult(
                total_revenue=capped_revenue,
                total_customers=actual_sold,
                sold_products=old_sr.sold_products,
                feedbacks=old_sr.feedbacks,
                market_share=old_sr.market_share,
            )

        phases.append({
            "phase": "SALES",
            "total_sales": capped_revenue,
            "customer_count": actual_sold,
            "stock_used": actual_sold,
            "stock_remaining": session.stock,
        })

        # 정산 (보정된 매출로 계산됨)
        settlement_result = gs.execute_turn_phase()
        gs.advance_phase()
        phases.append({"phase": "SETTLEMENT", **settlement_result})

        # 마무리
        cleanup_result = gs.execute_turn_phase()
        gs.advance_phase()
        phases.append({"phase": "CLEANUP", **cleanup_result})

    # 다음 턴 시작: 남은 시간 리셋
    session.remaining_hours = 12

    return {
        "success": True,
        "phases": phases,
        "settlement": settlement_result,
        "stock": session.stock,
        "ingredient_qty": session.ingredient_qty,
    }


@router.post("/{session_id}/price")
def change_price(session_id: str, req: PriceChangeRequest):
    session = _get_session(session_id)
    new_price = (req.new_price // 1000) * 1000  # 1000원 단위
    new_price = max(5000, min(100000, new_price))

    product = session.get_product()
    product = product.update_selling_price(Money(new_price))
    session.repository.save_product(product)

    return {
        "success": True,
        "new_price": new_price,
        "new_price_formatted": Money(new_price).format_korean(),
    }


@router.delete("/{session_id}")
def delete_game(session_id: str):
    if not session_manager.delete_session(session_id):
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
    return {"success": True}
