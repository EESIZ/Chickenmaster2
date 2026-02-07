"""v2 API Pydantic 모델 — 4구간 하루 시스템"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any, Literal


# ── 요청 ──

class CreateGameRequest(BaseModel):
    player_name: str = Field(default="김치킨", min_length=1, max_length=20)


class QueueActionRequest(BaseModel):
    action_type: str   # COOKING, ADVERTISING, ...
    specific_action: str  # PREPARE_INGREDIENTS, FLYER, ...


class PriceChangeRequest(BaseModel):
    new_price: int = Field(ge=5000, le=100000)


class TimeConfigRequest(BaseModel):
    wake_time: int = Field(ge=5, le=8)
    open_time: int = Field(ge=9, le=12)
    close_time: int = Field(ge=18, le=23)
    sleep_time: int = Field(ge=22, le=26)


class DecisionChoiceRequest(BaseModel):
    choice: Literal["A", "B"]


# ── 응답 ──

class GameStateResponse(BaseModel):
    game_id: str
    player: Optional[Dict[str, Any]] = None
    store: Optional[Dict[str, Any]] = None
    turn: Optional[Dict[str, Any]] = None
    is_running: bool
    stock: int
    ingredient_qty: int
    prepared_qty: int = 0
    reputation: int = 50
    current_segment: str = "PREP"
    current_phase: str = "PREP"  # backwards compat
    time_config: Optional[Dict[str, int]] = None
    segment_hours: Optional[Dict[str, int]] = None


class QueuedActionItem(BaseModel):
    slot_order: int
    action_type: str
    specific_action: str
    name: str
    hours: float
    cost: int
    status: str


class QueueResponse(BaseModel):
    queue: List[QueuedActionItem]
    total_hours: float
    segment_hours: float = 0
    remaining_hours: float = 0  # backwards compat
    available_hours: float


class ConfirmResponse(BaseModel):
    success: bool
    action_results: List[Dict[str, Any]]
    stock: Optional[int] = None
    ingredient_qty: Optional[int] = None
    prepared_qty: Optional[int] = None
    current_segment: str


class BusinessStartResponse(BaseModel):
    business_hours: int
    prepared_qty: int
    stock: int
    ingredient_qty: int
    decisions: List[Dict[str, Any]]
    current_segment: str


class DecisionResponse(BaseModel):
    decision_id: int
    choice: str
    effect: Dict[str, Any]
    label: str


class BusinessSummaryResponse(BaseModel):
    summary: Dict[str, Any]
    stock: int
    prepared_qty: int
    ingredient_qty: int
    current_segment: str
    player: Optional[Dict[str, Any]] = None
    ai_result: Optional[Dict[str, Any]] = None
    event_result: Optional[Dict[str, Any]] = None
    settlement_result: Optional[Dict[str, Any]] = None


class SleepResponse(BaseModel):
    sleep_hours: int
    fatigue_recovered: int
    new_fatigue: float
    turn_number: int
    game_date: str
    current_segment: str


class TimeConfigResponse(BaseModel):
    time_config: Dict[str, int]
    segment_hours: Dict[str, int]


class GameListItem(BaseModel):
    id: str
    player_name: str
    created_at: Optional[str] = None
    remaining_hours: Optional[int] = None
    stock: Optional[int] = None
    ingredient_qty: Optional[int] = None
