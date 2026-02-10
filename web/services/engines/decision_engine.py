"""영업 의사결정 생성 및 효과 적용 — 순수 함수, DB 접근 없음"""

import random
from typing import Dict, Any, List

from web.services.balance import DECISIONS_PER_BUSINESS, REPUTATION_MIN, REPUTATION_MAX


def generate_decisions(
    business_hours: int,
    templates: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    영업 의사결정을 랜덤 생성합니다.

    Args:
        business_hours: 영업 시간 (trigger_hour 범위 결정)
        templates: BUSINESS_DECISION_TEMPLATES 리스트

    Returns:
        trigger_hour가 추가된 의사결정 리스트 (trigger_hour 오름차순 정렬)
    """
    num_decisions = random.randint(1, DECISIONS_PER_BUSINESS)
    selected = random.sample(templates, min(num_decisions, len(templates)))

    decisions = []
    for tmpl in selected:
        trigger_hour = random.randint(1, max(1, business_hours - 1))
        decisions.append({**tmpl, "trigger_hour": trigger_hour})

    decisions.sort(key=lambda d: d["trigger_hour"])
    return decisions


def apply_decision_effects(
    effect: Dict[str, Any],
    ingredient_qty: int,
    reputation: int,
    money: int,
    fatigue: float,
) -> Dict[str, Any]:
    """
    의사결정 효과를 현재 상태에 적용합니다.

    Args:
        effect: 선택한 효과 딕셔너리
        ingredient_qty: 현재 재료량
        reputation: 현재 평판
        money: 현재 자금
        fatigue: 현재 피로도

    Returns:
        new_ingredient_qty, new_reputation, new_money, new_fatigue
    """
    money_cost = effect.get("money_cost", 0)
    money_bonus = effect.get("money_bonus", 0)
    ingredient_gain = effect.get("ingredient_gain", 0)
    rep_change = effect.get("reputation_change", 0)
    fatigue_change = effect.get("fatigue_change", 0)

    new_ingredient_qty = ingredient_qty + ingredient_gain
    new_reputation = max(REPUTATION_MIN, min(REPUTATION_MAX, reputation + rep_change))

    new_money = money
    if money_cost > 0:
        new_money = max(0, money - money_cost)
    if money_bonus > 0:
        new_money = money + money_bonus

    new_fatigue = max(0.0, min(100.0, fatigue + fatigue_change))

    return {
        "new_ingredient_qty": new_ingredient_qty,
        "new_reputation": new_reputation,
        "new_money": new_money,
        "new_fatigue": new_fatigue,
    }
