"""
연구 유형 정의

README.md에 명시된 연구 분야들을 enum으로 정의합니다.
"""

from enum import Enum, auto


class ResearchType(Enum):
    """연구 분야"""
    
    RECIPE = auto()  # 레시피: 새로운 제품 개발
    MANAGEMENT = auto()  # 경영: 운영 효율성 향상
    ADVERTISING = auto()  # 광고: 마케팅 효과 증대
    SERVICE = auto()  # 서비스: 고객 만족도 향상 