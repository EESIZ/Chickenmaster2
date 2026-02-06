"""
도메인 값 객체 정의

게임에서 사용되는 불변 값 객체들을 정의합니다.
모든 값 객체는 불변이며, 유효성 검사와 도메인 메서드를 포함합니다.
"""

from dataclasses import dataclass
from typing import Union
import math


@dataclass(frozen=True)
class Money:
    """원화 단위 값 객체"""
    
    amount: int
    
    def __add__(self, other: Union['Money', int]) -> 'Money':
        if isinstance(other, Money):
            return Money(self.amount + other.amount)
        return Money(self.amount + other)
    
    def __sub__(self, other: Union['Money', int]) -> 'Money':
        if isinstance(other, Money):
            return Money(self.amount - other.amount)
        return Money(self.amount - other)
    
    def __mul__(self, multiplier: Union[int, float]) -> 'Money':
        return Money(int(self.amount * multiplier))
    
    def __truediv__(self, divisor: Union[int, float]) -> 'Money':
        return Money(int(self.amount / divisor))

    def __floordiv__(self, divisor: Union[int, float]) -> 'Money':
        return Money(int(self.amount // divisor))
    
    def __lt__(self, other: Union['Money', int]) -> bool:
        if isinstance(other, Money):
            return self.amount < other.amount
        return self.amount < other
    
    def __le__(self, other: Union['Money', int]) -> bool:
        if isinstance(other, Money):
            return self.amount <= other.amount
        return self.amount <= other
    
    def __gt__(self, other: Union['Money', int]) -> bool:
        if isinstance(other, Money):
            return self.amount > other.amount
        return self.amount > other
    
    def __ge__(self, other: Union['Money', int]) -> bool:
        if isinstance(other, Money):
            return self.amount >= other.amount
        return self.amount >= other
    
    def is_zero(self) -> bool:
        """금액이 0원인지 확인"""
        return self.amount == 0

    def is_positive(self) -> bool:
        """금액이 양수인지 확인"""
        return self.amount > 0

    def is_negative(self) -> bool:
        """금액이 음수인지 확인"""
        return self.amount < 0
    
    def format_korean(self) -> str:
        """한국식 원화 표기로 포맷"""
        return f"₩{self.amount:,}"


@dataclass(frozen=True)
class Percentage:
    """퍼센트 값 객체 (0~100)"""
    
    value: float
    
    def __post_init__(self):
        if self.value < 0:
            raise ValueError(f"퍼센트 값은 음수일 수 없습니다: {self.value}")
    
    def __add__(self, other: Union['Percentage', float]) -> 'Percentage':
        if isinstance(other, Percentage):
            return Percentage(self.value + other.value)
        return Percentage(self.value + other)
    
    def __sub__(self, other: Union['Percentage', float]) -> 'Percentage':
        if isinstance(other, Percentage):
            return Percentage(max(0, self.value - other.value))
        return Percentage(max(0, self.value - other))
    
    def __mul__(self, multiplier: Union[int, float]) -> 'Percentage':
        return Percentage(self.value * multiplier)

    def __lt__(self, other: Union['Percentage', float]) -> bool:
        if isinstance(other, Percentage):
            return self.value < other.value
        return self.value < other

    def __le__(self, other: Union['Percentage', float]) -> bool:
        if isinstance(other, Percentage):
            return self.value <= other.value
        return self.value <= other

    def __gt__(self, other: Union['Percentage', float]) -> bool:
        if isinstance(other, Percentage):
            return self.value > other.value
        return self.value > other

    def __ge__(self, other: Union['Percentage', float]) -> bool:
        if isinstance(other, Percentage):
            return self.value >= other.value
        return self.value >= other
    
    def as_ratio(self) -> float:
        """0.0~1.0 비율로 변환"""
        return self.value / 100.0
    
    def is_critical(self, threshold: 'Percentage') -> bool:
        """임계값을 넘었는지 확인"""
        return self.value >= threshold.value
    
    def format(self) -> str:
        """퍼센트 문자열로 포맷"""
        return f"{self.value:.1f}%"


@dataclass(frozen=True)
class Hours:
    """시간 값 객체 (0~24)"""
    
    value: int
    
    def __post_init__(self):
        if not 0 <= self.value <= 24:
            raise ValueError(f"시간 값은 0~24 사이여야 합니다: {self.value}")
    
    def __add__(self, other: Union['Hours', int]) -> 'Hours':
        if isinstance(other, Hours):
            return Hours(min(24, self.value + other.value))
        return Hours(min(24, self.value + other))
    
    def __sub__(self, other: Union['Hours', int]) -> 'Hours':
        if isinstance(other, Hours):
            return Hours(max(0, self.value - other.value))
        return Hours(max(0, self.value - other))
    
    def is_exhausted(self) -> bool:
        """시간이 모두 소진되었는지 확인"""
        return self.value == 0
    
    def has_enough(self, required: Union['Hours', int]) -> bool:
        """필요한 시간이 충분한지 확인"""
        if isinstance(required, Hours):
            return self.value >= required.value
        return self.value >= required


@dataclass(frozen=True)
class Progress:
    """진행도 값 객체 (0~100)"""
    
    value: int
    
    def __post_init__(self):
        if not 0 <= self.value <= 100:
            raise ValueError(f"진행도는 0~100 사이여야 합니다: {self.value}")
    
    def __add__(self, other: Union['Progress', int]) -> 'Progress':
        if isinstance(other, Progress):
            return Progress(min(100, self.value + other.value))
        return Progress(min(100, self.value + other))
    
    def is_complete(self) -> bool:
        """완료되었는지 확인"""
        return self.value >= 100
    
    def completion_ratio(self) -> float:
        """완료 비율 (0.0~1.0)"""
        return self.value / 100.0


@dataclass(frozen=True)
class Experience:
    """경험치 값 객체 (0~100, 100 도달 시 레벨업)"""
    
    value: int
    
    def __post_init__(self):
        if not 0 <= self.value <= 100:
            raise ValueError(f"경험치는 0~100 사이여야 합니다: {self.value}")
    
    def __add__(self, other: Union['Experience', int]) -> tuple['Experience', int]:
        """경험치 추가 후 (새 경험치, 레벨업 횟수) 반환"""
        if isinstance(other, Experience):
            total = self.value + other.value
        else:
            total = self.value + other
        
        level_ups = total // 100
        remaining_exp = total % 100
        
        return Experience(remaining_exp), level_ups
    
    def is_ready_for_levelup(self) -> bool:
        """레벨업 준비가 되었는지 확인"""
        return self.value >= 100


@dataclass(frozen=True)
class StatValue:
    """스탯 값 객체"""
    
    base_value: int  # 기본 스탯값
    experience: Experience = Experience(0) # 경험치
    
    def __post_init__(self):
        if self.base_value < 0:
            raise ValueError(f"스탯 값은 음수일 수 없습니다: {self.base_value}")
    
    def apply_fatigue_penalty(self, fatigue_level: int) -> 'StatValue':
        """피로도에 따른 페널티 적용 후 새로운 StatValue 반환"""
        # 피로도 10당 스탯 1 감소
        penalty = fatigue_level // 10
        new_base = max(0, self.base_value - penalty)
        return StatValue(base_value=new_base)
    
    def get_dice_bonus(self) -> int:
        """주사위 굴림 보너스 계산 (스탯 10당 +1)"""
        return self.base_value // 10