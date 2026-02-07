"""v2 게임 API — 4구간 하루 시스템 (PREP → BUSINESS → NIGHT → SLEEP)"""

from fastapi import APIRouter, HTTPException

from web.api.schemas_v2 import (
    CreateGameRequest, QueueActionRequest, PriceChangeRequest,
    TimeConfigRequest, DecisionChoiceRequest,
    GameStateResponse, QueueResponse, ConfirmResponse,
    BusinessStartResponse, DecisionResponse, BusinessSummaryResponse,
    SleepResponse, TimeConfigResponse, GameListItem,
)
from web.services.game_service import GameService

router = APIRouter(prefix="/v2/games", tags=["v2-games"])

_service = GameService()


def _svc() -> GameService:
    return _service


# ── 게임 수명주기 ──

@router.get("", response_model=list[GameListItem])
def list_games():
    """활성 게임 목록"""
    return _svc().list_games()


@router.post("", response_model=GameStateResponse)
def create_game(req: CreateGameRequest):
    """새 게임 생성"""
    state = _svc().create_game(req.player_name)
    if not state:
        raise HTTPException(500, "게임 생성 실패")
    return state


@router.get("/{game_id}", response_model=GameStateResponse)
def get_game(game_id: str):
    """전체 상태 조회 (재접속용)"""
    state = _svc().get_state(game_id)
    if not state:
        raise HTTPException(404, "게임을 찾을 수 없습니다")
    return state


@router.delete("/{game_id}")
def delete_game(game_id: str):
    """게임 종료"""
    _svc().delete_game(game_id)
    return {"success": True}


# ── 시간 설정 ──

@router.put("/{game_id}/time-config", response_model=TimeConfigResponse)
def update_time_config(game_id: str, req: TimeConfigRequest):
    """하루 시간 설정 변경"""
    try:
        return _svc().update_time_config(game_id, req.wake_time, req.open_time, req.close_time, req.sleep_time)
    except ValueError as e:
        raise HTTPException(400, str(e))


# ── 카드 큐 (구간 공통) ──

@router.get("/{game_id}/actions/available")
def get_available_actions(game_id: str):
    """현 구간에서 사용 가능한 카드 목록"""
    return _svc().get_available_actions(game_id)


@router.post("/{game_id}/actions/queue", response_model=QueueResponse)
def add_to_queue(game_id: str, req: QueueActionRequest):
    """시간표에 카드 추가"""
    try:
        return _svc().queue_action(game_id, req.action_type, req.specific_action)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.delete("/{game_id}/actions/queue/{slot_order}", response_model=QueueResponse)
def remove_from_queue(game_id: str, slot_order: int):
    """시간표에서 카드 제거"""
    try:
        return _svc().remove_from_queue(game_id, slot_order)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/{game_id}/actions/queue", response_model=QueueResponse)
def get_queue(game_id: str):
    """현재 시간표 조회"""
    return _svc().get_queue(game_id)


# ── 구간 진행 ──

@router.post("/{game_id}/segments/prep/confirm", response_model=ConfirmResponse)
def confirm_prep(game_id: str):
    """준비 행동 확정 → 영업으로"""
    try:
        return _svc().confirm_prep_actions(game_id)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/{game_id}/business/start", response_model=BusinessStartResponse)
def start_business(game_id: str):
    """영업 시작 (타임랩스 설정 + 의사결정 생성)"""
    try:
        return _svc().start_business(game_id)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/{game_id}/business/decisions/{decision_id}", response_model=DecisionResponse)
def submit_decision(game_id: str, decision_id: int, req: DecisionChoiceRequest):
    """영업 의사결정 제출"""
    try:
        return _svc().submit_decision(game_id, decision_id, req.choice)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/{game_id}/business/complete", response_model=BusinessSummaryResponse)
def complete_business(game_id: str):
    """영업 종료 → 요약 + 야간으로"""
    try:
        return _svc().complete_business(game_id)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/{game_id}/segments/night/confirm", response_model=ConfirmResponse)
def confirm_night(game_id: str):
    """야간 행동 확정 → 수면으로"""
    try:
        return _svc().confirm_night_actions(game_id)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/{game_id}/sleep/execute", response_model=SleepResponse)
def execute_sleep(game_id: str):
    """수면 실행 → 다음 날"""
    try:
        return _svc().execute_sleep(game_id)
    except ValueError as e:
        raise HTTPException(400, str(e))


# ── 유틸 ──

@router.post("/{game_id}/price")
def change_price(game_id: str, req: PriceChangeRequest):
    """가격 변경"""
    try:
        return _svc().change_price(game_id, req.new_price)
    except ValueError as e:
        raise HTTPException(400, str(e))
