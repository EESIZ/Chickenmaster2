"""영업 판매량/매출 계산 — 순수 함수, DB 접근 없음"""

from typing import Dict, Any, List

from web.services.balance import (
    CUSTOMERS_PER_HOUR, REPUTATION_BASE,
    MARGIN_MULT_FLOOR, SALES_MULT_FLOOR,
    FRESHNESS_SALES_BASE, FRESHNESS_SALES_FLOOR, FRESHNESS_SALES_CEILING,
)


def calculate_sales(
    business_hours: int,
    reputation: int,
    prepared_qty: int,
    ingredient_freshness: float,
    decisions: List[Dict[str, Any]],
    price: int,
) -> Dict[str, Any]:
    """
    영업 결과를 순수 계산으로 산출합니다.

    Args:
        business_hours: 영업 시간
        reputation: 현재 평판 (0~100)
        prepared_qty: 준비된 수량
        ingredient_freshness: 재료 신선도 (0~100)
        decisions: 의사결정 결과 목록 (player_choice, effect_json 포함)
        price: 상품 판매가

    Returns:
        base_customers, freshness_mult, total_customers, actual_served,
        used_prepared, remaining_prepared,
        effective_price, total_sales, stock_cost_from_decisions
    """
    # Freshness multiplier: clamp(freshness / 80, 0.5, 1.2)
    freshness_mult = max(
        FRESHNESS_SALES_FLOOR,
        min(FRESHNESS_SALES_CEILING, ingredient_freshness / FRESHNESS_SALES_BASE),
    )

    # Base customers formula (with freshness multiplier)
    base_customers = int(
        business_hours * CUSTOMERS_PER_HOUR * (reputation / REPUTATION_BASE) * freshness_mult
    )

    # Aggregate decision effects
    customer_bonus = 0
    customer_bonus_pct = 0
    margin_penalty_pct = 0
    sales_penalty_pct = 0
    stock_cost_from_decisions = 0

    for d in decisions:
        if d["player_choice"]:
            eff = d["effect_json"]
            customer_bonus += eff.get("customer_bonus", 0)
            customer_bonus_pct += eff.get("customer_bonus_pct", 0)
            margin_penalty_pct += eff.get("margin_penalty_pct", 0)
            sales_penalty_pct += eff.get("sales_penalty_pct", 0)
            stock_cost_from_decisions += eff.get("stock_cost", 0)

    total_customers = base_customers + customer_bonus
    total_customers = int(total_customers * (1 + customer_bonus_pct / 100))

    # Can only serve up to prepared_qty
    available_servings = prepared_qty
    actual_served = min(total_customers, available_servings)
    turned_away = max(0, total_customers - actual_served)

    used_prepared = min(actual_served, prepared_qty)
    remaining_prepared = max(0, prepared_qty - used_prepared)

    # Revenue
    margin_mult = max(MARGIN_MULT_FLOOR, 1.0 - margin_penalty_pct / 100)
    sales_mult = max(SALES_MULT_FLOOR, 1.0 - sales_penalty_pct / 100)
    effective_price = int(price * margin_mult * sales_mult)

    total_sales = actual_served * effective_price

    return {
        "base_customers": base_customers,
        "freshness_mult": round(freshness_mult, 2),
        "total_customers": total_customers,
        "actual_served": actual_served,
        "turned_away": turned_away,
        "used_prepared": used_prepared,
        "remaining_prepared": remaining_prepared,
        "effective_price": effective_price,
        "total_sales": total_sales,
        "stock_cost_from_decisions": stock_cost_from_decisions,
    }
