"""
플레이어 행동 유형 정의

README.md에 명시된 6가지 행동 카테고리와 세부 행동들을 enum으로 정의합니다.
"""

from enum import Enum, auto


class ActionType(Enum):
    """주요 행동 카테고리"""
    
    COOKING = auto()  # 조리
    ADVERTISING = auto()  # 광고
    OPERATION = auto()  # 운영
    RESEARCH = auto()  # 연구
    PERSONAL = auto()  # 개인
    REST = auto()  # 휴식


class CookingAction(Enum):
    """조리 관련 세부 행동"""
    
    PREPARE_INGREDIENTS = auto()  # 재료준비
    COOK = auto()  # 조리
    INSPECT_INGREDIENTS = auto()  # 재료점검


class AdvertisingAction(Enum):
    """광고 관련 세부 행동"""
    
    FLYER = auto()  # 전단지
    ONLINE_AD = auto()  # 온라인광고
    DELIVERY_APP = auto()  # 배달앱


class OperationAction(Enum):
    """운영 관련 세부 행동"""
    
    ORDER_INGREDIENTS = auto()  # 재료주문
    CLEAN = auto()  # 청소
    EQUIPMENT_CHECK = auto()  # 장비점검
    HIRE_PARTTIME = auto()  # 알바고용


class ResearchAction(Enum):
    """연구 관련 세부 행동"""
    
    RECIPE = auto()  # 레시피
    MANAGEMENT = auto()  # 경영
    ADVERTISING_RESEARCH = auto()  # 광고
    SERVICE = auto()  # 서비스


class PersonalAction(Enum):
    """개인 관련 세부 행동"""
    
    VACATION = auto()  # 휴가
    STUDY = auto()  # 학습
    EXERCISE = auto()  # 운동


class RestAction(Enum):
    """휴식 관련 행동"""
    
    SLEEP = auto()  # 수면 