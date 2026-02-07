"""Pydantic 요청/응답 모델"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any


# ── 요청 ──

class CreateGameRequest(BaseModel):
    player_name: str = Field(default="김치킨", min_length=1, max_length=20)


class ActionRequest(BaseModel):
    action_type: str  # COOKING, ADVERTISING, OPERATION, RESEARCH, PERSONAL, REST
    specific_action: str  # e.g. PREPARE_INGREDIENTS, FLYER, ...
    time_hours: Optional[int] = None  # 휴식 시 시간 지정


class PriceChangeRequest(BaseModel):
    new_price: int = Field(ge=5000, le=100000)


# ── 응답 ──

class StatInfo(BaseModel):
    cooking: int
    management: int
    service: int
    tech: int
    stamina: int


class PlayerInfo(BaseModel):
    name: str
    money: int
    money_formatted: str
    fatigue: float
    happiness: float
    stats: StatInfo
    is_fatigued: bool
    is_critically_fatigued: bool
    is_exhausted: bool


class StoreInfo(BaseModel):
    name: str
    monthly_rent: int
    product_name: str
    selling_price: int
    selling_price_formatted: str


class TurnInfo(BaseModel):
    turn_number: int
    game_date: str
    current_phase: str
    remaining_hours: int


class GameStateResponse(BaseModel):
    session_id: str
    player: PlayerInfo
    store: StoreInfo
    turn: TurnInfo
    is_running: bool
    stock: int
    ingredient_qty: int


class ActionInfo(BaseModel):
    category: str
    category_name: str
    specific_action: str
    name: str
    hours: int
    cost: int
    fatigue_per_hour: float
    exp_info: str
    can_do: bool


class AvailableActionsResponse(BaseModel):
    remaining_hours: int
    categories: List[Dict[str, Any]]


class ActionResultResponse(BaseModel):
    success: bool
    message: str
    time_consumed: int
    fatigue_change: float
    money_change: int
    experience_gains: Dict[str, int]
    stock: Optional[int] = None
    ingredient_qty: Optional[int] = None


class AdvanceResultResponse(BaseModel):
    success: bool
    phases: List[Dict[str, Any]]
    settlement: Optional[Dict[str, Any]] = None
    stock: Optional[int] = None
    ingredient_qty: Optional[int] = None


class ErrorResponse(BaseModel):
    detail: str
