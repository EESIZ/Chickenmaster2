"""
치킨마스터2 — 밸런스 설정 모듈

모든 게임 밸런스 수치를 한 곳에서 관리합니다.
game_service.py 및 기타 서비스에서 이 모듈을 import하여 사용합니다.
"""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. 초기 게임 상태
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INITIAL_MONEY = 2_000_000          # 시작 자금 (원)
INITIAL_INGREDIENT_QTY = 100       # 시작 재료
INITIAL_INGREDIENT_QUALITY = 80    # 시작 재료 품질
INGREDIENT_PURCHASE_PRICE = 5_000  # 재료 단가

INITIAL_SELLING_PRICE = 20_000     # 상품 초기 판매가
INITIAL_AWARENESS = 10             # 초기 인지도
MONTHLY_RENT = 1_500_000           # 월 임대료

INITIAL_REPUTATION = 50            # 초기 평판 (0~100)

# 초기 스탯
INITIAL_STATS = {
    "cooking": 10,
    "management": 8,
    "service": 8,
    "tech": 5,
    "stamina": 50,
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. 시간 설정
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DEFAULT_TIME = {
    "wake": 7,     # 기상 시각
    "open": 10,    # 오픈 시각
    "close": 21,   # 마감 시각
    "sleep": 24,   # 취침 시각 (24 = 자정, 26 = 새벽2시)
}

TIME_RANGES = {
    "wake":  (5, 8),
    "open":  (9, 12),
    "close": (18, 23),
    "sleep": (22, 26),
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. 행동(카드) 밸런스
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 준비 구간 (PREP) 행동
PREP_ACTION_DEFS = {
    # key: (시간, 비용, 피로/시간)
    "PREPARE_INGREDIENTS": {"hours": 1, "cost": 0},
    "INSPECT_INGREDIENTS": {"hours": 1, "cost": 0},
    "CLEAN":              {"hours": 2, "cost": 0},
    "EQUIPMENT_CHECK":    {"hours": 1, "cost": 0},
    "SLEEP":              {"hours": 0.5, "cost": 0},
}

# 야간 구간 (NIGHT) 행동
NIGHT_ACTION_DEFS = {
    "RECIPE":               {"hours": 3, "cost": 0},
    "MANAGEMENT":           {"hours": 3, "cost": 0},
    "ADVERTISING_RESEARCH": {"hours": 3, "cost": 0},
    "SERVICE":              {"hours": 3, "cost": 0},
    "STUDY":                {"hours": 2, "cost": 0},
    "EXERCISE":             {"hours": 2, "cost": 0},
    "FLYER":                {"hours": 2, "cost": 50_000},
    "ONLINE_AD":            {"hours": 1, "cost": 100_000},
    "DELIVERY_APP":         {"hours": 1, "cost": 30_000},
    "ORDER_INGREDIENTS":    {"hours": 1, "cost": 200_000},
    "HIRE_PARTTIME":        {"hours": 2, "cost": 80_000},
    "SLEEP":                {"hours": 0.5, "cost": 0},
}

# 재고/재료 효과
PREPARE_GAIN = 5                 # 재료 준비 1회(1h) → +5 prepared_qty
PREPARE_INGREDIENT_COST = 3      # 재료 준비 시 소모하는 재료량
ORDER_INGREDIENT_GAIN = 50       # 재료 주문 시 획득 재료량


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. 경험치 보상
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# {행동명: "표시문자열"} — UI 표시용 + 실제 적용은 ActionService에서
EXP_REWARDS = {
    "PREPARE_INGREDIENTS":  "요리+4",
    "INSPECT_INGREDIENTS":  "요리+4, 경영+2",
    "FLYER":                "경영+6",
    "ONLINE_AD":            "경영+8, 기술+4",
    "DELIVERY_APP":         "경영+6, 기술+6",
    "ORDER_INGREDIENTS":    "경영+8",
    "CLEAN":                "서비스+10",
    "EQUIPMENT_CHECK":      "기술+8, 경영+4",
    "HIRE_PARTTIME":        "경영+10, 서비스+4",
    "RECIPE":               "요리+15",
    "MANAGEMENT":           "경영+15",
    "ADVERTISING_RESEARCH": "경영+12, 기술+8",
    "SERVICE":              "서비스+15",
    "STUDY":                "기술+15, 경영+5",
    "EXERCISE":             "체력+20",
    "SLEEP":                "",
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. 영업 (BUSINESS) 밸런스
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 기본 고객수 공식: business_hours * CUSTOMERS_PER_HOUR * (reputation / REPUTATION_BASE)
CUSTOMERS_PER_HOUR = 3
REPUTATION_BASE = 50             # 평판 기준값 (50이면 보정 1.0)

# 가격/판매 보정 하한
MARGIN_MULT_FLOOR = 0.5          # 할인 최대 50%까지만
SALES_MULT_FLOOR = 0.3           # 판매 패널티 최대 70%까지만

# 평판 범위
REPUTATION_MIN = 0
REPUTATION_MAX = 100


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. 영업 의사결정 템플릿
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BUSINESS_DECISIONS = [
    {
        "key": "lunch_rush",
        "title": "점심 러시! 할인할까요?",
        "desc": "점심시간에 손님이 몰리고 있습니다.",
        "a_label": "할인 실시",   "b_label": "정가 유지",
        "a_effect": {"customer_bonus_pct": 30, "margin_penalty_pct": 20},
        "b_effect": {},
    },
    {
        "key": "group_reservation",
        "title": "단체 예약 15명",
        "desc": "근처 회사에서 단체 주문이 들어왔습니다.",
        "a_label": "수락",        "b_label": "거절",
        "a_effect": {"customer_bonus": 15, "stock_cost": 15},
        "b_effect": {},
    },
    {
        "key": "ingredient_shortage",
        "title": "재료 부족! 긴급 주문?",
        "desc": "영업 중 재료가 떨어질 위기입니다.",
        "a_label": "긴급 주문 (-10만원)", "b_label": "무시",
        "a_effect": {"money_cost": 100_000, "ingredient_gain": 30},
        "b_effect": {"sales_penalty_pct": 30},
    },
    {
        "key": "complaint",
        "title": "서비스 컴플레인",
        "desc": "손님이 서비스에 불만을 표시하고 있습니다.",
        "a_label": "정중 대응",   "b_label": "무시",
        "a_effect": {"reputation_change": 5},
        "b_effect": {"reputation_change": -5},
    },
    {
        "key": "special_order",
        "title": "특별 주문",
        "desc": "VIP 손님이 특별 메뉴를 요청합니다.",
        "a_label": "수락 (+3만원)", "b_label": "거절",
        "a_effect": {"money_bonus": 30_000, "fatigue_change": 5},
        "b_effect": {},
    },
    {
        "key": "delivery_rush",
        "title": "배달 폭주",
        "desc": "배달 주문이 한꺼번에 몰리고 있습니다.",
        "a_label": "전부 수락",   "b_label": "제한 수락",
        "a_effect": {"customer_bonus": 10, "fatigue_change": 8},
        "b_effect": {"customer_bonus": 3},
    },
]

# 영업 중 의사결정 발생 수
DECISIONS_PER_BUSINESS = 2


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 7. 수면 & 피로
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FATIGUE_RECOVERY_PER_HOUR = 16   # 수면 시간당 피로 회복량


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 8. 가격 제한
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PRICE_STEP = 1_000               # 가격 조절 단위
PRICE_MIN = 5_000                # 최소 판매가
PRICE_MAX = 100_000              # 최대 판매가


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 9. 신선도 시스템
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INITIAL_FRESHNESS = 90
FRESHNESS_MIN = 0
FRESHNESS_MAX = 100
ORDER_INGREDIENT_FRESHNESS = 100     # 새 주문 재료 신선도

# 일일 감쇄: decay = BASE + (qty // DIVISOR) * PENALTY
FRESHNESS_BASE_DECAY = 3
FRESHNESS_QTY_DIVISOR = 50
FRESHNESS_HOARDING_PENALTY = 2

# 영업 보정: mult = clamp(freshness / BASE, FLOOR, CEILING)
FRESHNESS_SALES_BASE = 80           # 80 = 1.0x
FRESHNESS_SALES_FLOOR = 0.5
FRESHNESS_SALES_CEILING = 1.2

# 평판 페널티
FRESHNESS_REPUTATION_THRESHOLD = 40
FRESHNESS_REPUTATION_PENALTY = -2

# 10. 돌아간 고객 평판 페널티
# penalty = min(turned_away // DIVISOR, MAX)
TURNAWAY_REP_DIVISOR = 5            # 5명당 -1 평판
TURNAWAY_REP_MAX_PENALTY = 10       # 최대 -10
