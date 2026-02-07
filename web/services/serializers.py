"""도메인 모델 -> dict 변환"""

from core.domain.player import Player
from core.domain.store import Store
from core.domain.product import Product
from core.domain.turn import Turn


def serialize_player(player: Player) -> dict:
    stats = player.get_effective_stats()
    return {
        "name": player.name,
        "money": player.money.amount,
        "money_formatted": player.money.format_korean(),
        "fatigue": round(player.fatigue.value, 1),
        "happiness": round(player.happiness.value, 1),
        "stats": {
            "cooking": stats.cooking.base_value,
            "management": stats.management.base_value,
            "service": stats.service.base_value,
            "tech": stats.tech.base_value,
            "stamina": stats.stamina.base_value,
        },
        "is_fatigued": player.is_fatigued(),
        "is_critically_fatigued": player.is_critically_fatigued(),
        "is_exhausted": player.is_completely_exhausted(),
    }


def serialize_store(store: Store, product: Product) -> dict:
    return {
        "name": store.name,
        "monthly_rent": store.monthly_rent.amount,
        "product_name": product.name,
        "selling_price": product.selling_price.amount,
        "selling_price_formatted": product.selling_price.format_korean(),
    }


def serialize_turn(turn: Turn, remaining_hours: int) -> dict:
    return {
        "turn_number": turn.turn_number,
        "game_date": turn.game_date.isoformat(),
        "current_phase": turn.get_phase_name(),
        "remaining_hours": remaining_hours,
    }
