"""
이벤트 유형 정의

README.md에 명시된 5가지 이벤트 분류를 enum으로 정의합니다.
"""

from enum import Enum, auto


class EventType(Enum):
    """이벤트 분류"""
    
    DAILY = auto()  # 일상: 특별한 조건 없이 랜덤 발생
    OPPORTUNITY = auto()  # 기회: 특정 조건 달성 시 발생
    CHOICE = auto()  # 선택: 트레이드오프 결과를 가지는 선택지
    CHAIN = auto()  # 연쇄: 다른 이벤트에 의해 연쇄적으로 발생
    CRISIS = auto()  # 위기: 일정 턴 후 발생하는 난이도 조절용 이벤트 