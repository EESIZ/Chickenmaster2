"""
게임 전역 상수 정의

README.md의 게임 규칙에서 추출한 고정값들을 모아둡니다.
매직 넘버를 제거하고 단일 진실 소스를 유지하기 위함입니다.
"""

# 턴 시스템
TURN_HOURS = 12  # 1턴당 시간 자원 (09:00~21:00)
TURN_START_HOUR = 9  # 영업 시작 시간
TURN_END_HOUR = 21  # 영업 종료 시간

# 다이스 시스템 Calldice 모듈 사용

# 고객 시스템
MAX_CUSTOMER_AI_RATIO = 0.10  # 개별 AI 고객 비율 (10%)
CUSTOMER_BULK_RATIO = 0.90  # 수치 고객 비율 (90%)

# 이벤트 시스템
EVENT_MAX_PER_TURN = 1  # 턴당 최대 이벤트 수
EVENT_DAILY_THRESHOLD = 20  # 일상 이벤트 발생 임계값 (Calldice > 20)

# 피로도 시스템
FATIGUE_WARN_RATIO = 0.5  # 체력 대비 50% 경고
FATIGUE_CRITICAL_RATIO = 0.9  # 체력 대비 90% 위험 경고
FATIGUE_SHUTDOWN_RATIO = 1.0  # 체력 초과 시 스탯 1/2 감소
FATIGUE_KNOCKOUT_RATIO = 2.0  # 체력 2배 초과 시 행동 불가

# 연구 시스템
RESEARCH_MIN_PROGRESS = 0  # 연구 진행도 최소값
RESEARCH_MAX_PROGRESS = 100  # 연구 진행도 최대값

# 스탯 시스템
STAT_EXP_MIN = 0  # 스탯 경험치 최소값
STAT_EXP_MAX = 100  # 스탯 경험치 최대값
STAT_EXP_GAIN_SUCCESS = 10  # 성공 시 경험치 획득량
INITIAL_STAT_VALUE = 50  # 플레이어 초기 스탯값

# 경쟁자 AI 시스템
AI_REACTION_MIN_DELAY = 3  # AI 반응 최소 지연 턴
AI_REACTION_MAX_DELAY = 10  # AI 반응 최대 지연 턴
AI_BANKRUPTCY_DAYS = 30  # 자금 0원 지속 시 패배까지 일수
AI_RESPAWN_MIN_DAYS = 30  # 새 경쟁자 투입 최소 일수
AI_RESPAWN_MAX_DAYS = 120  # 새 경쟁자 투입 최대 일수

# 재고 시스템
INVENTORY_DANGER_DAYS = 30  # 위험 재고 판정 일수

# 인지도 시스템
AWARENESS_GAIN_PER_SALE = 3  # 판매당 인지도 증가
AWARENESS_DAILY_DECAY = 1  # 매일 인지도 감소

# 행복도 시스템 (f(x) = 50 ± A√(|x-50|/k))
HAPPINESS_BASELINE = 50  # 행복도 기준값
HAPPINESS_MIN = 0  # 행복도 최소값
HAPPINESS_MAX = 100  # 행복도 최대값
HAPPINESS_CURVE_A = 50  # 행복도 곡선 계수 A
HAPPINESS_CURVE_K = 1  # 행복도 곡선 계수 k

# 가격 시스템
PRICE_MIN = 0  # 최소 가격
PRICE_MAX = 1_000_000  # 최대 가격 (100만원)
PRICE_UNIT = 1_000  # 가격 조정 단위 (1,000원)

# 파일 경로
PATH_BGM_DIR = "bgm/"  # 배경음악 디렉토리
PATH_SAVE_DIR = "saves/"  # 세이브 파일 디렉토리
PATH_ASSETS_DIR = "assets/"  # 에셋 디렉토리 