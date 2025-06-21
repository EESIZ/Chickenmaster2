"""
고객 AI 도메인 모델

게임 내 고객 AI 시스템을 나타내는 불변 엔티티입니다.
10% AI 고객과 90% 수치 계산 고객으로 구성됩니다.
"""

from dataclasses import dataclass
from enum import Enum, auto
from uuid import UUID
from typing import Optional

from .value_objects import Money, Percentage


class CustomerType(Enum):
    """고객 유형"""
    
    BUDGET_CONSCIOUS = auto()  # 가격 민감형
    QUALITY_SEEKER = auto()  # 품질 추구형
    BRAND_LOYAL = auto()  # 브랜드 충성형
    TRENDY = auto()  # 트렌드 민감형


class CustomerMood(Enum):
    """고객 기분 상태"""
    
    VERY_HAPPY = auto()  # 매우 만족
    HAPPY = auto()  # 만족
    NEUTRAL = auto()  # 보통
    UNHAPPY = auto()  # 불만족
    VERY_UNHAPPY = auto()  # 매우 불만족


@dataclass(frozen=True)
class CustomerAI:
    """AI 고객 엔티티 (전체 고객의 10%)"""
    
    id: UUID
    name: str
    customer_type: CustomerType
    
    # 고객 특성
    price_sensitivity: float  # 가격 민감도 (0.0 ~ 1.0)
    quality_preference: float  # 품질 선호도 (0.0 ~ 1.0)
    brand_loyalty: float  # 브랜드 충성도 (0.0 ~ 1.0)
    
    # 현재 상태
    mood: CustomerMood = CustomerMood.NEUTRAL
    last_purchase_store_id: Optional[UUID] = None
    
    def __post_init__(self):
        """생성 후 유효성 검사"""
        if not self.name.strip():
            raise ValueError("고객 이름은 비어있을 수 없습니다")
        
        if not 0.0 <= self.price_sensitivity <= 1.0:
            raise ValueError("가격 민감도는 0.0~1.0 사이여야 합니다")
        
        if not 0.0 <= self.quality_preference <= 1.0:
            raise ValueError("품질 선호도는 0.0~1.0 사이여야 합니다")
        
        if not 0.0 <= self.brand_loyalty <= 1.0:
            raise ValueError("브랜드 충성도는 0.0~1.0 사이여야 합니다")
    
    def evaluate_product(self, price: Money, quality: int, awareness: int, market_averages: 'MarketAverages') -> float:
        """제품 평가 점수 계산"""
        # 가격 점수 (낮을수록 좋음)
        price_score = self._calculate_price_score(price, market_averages.average_price)
        
        # 품질 점수 (높을수록 좋음)
        quality_score = self._calculate_quality_score(quality, market_averages.average_quality)
        
        # 인지도 점수 (높을수록 좋음)
        awareness_score = self._calculate_awareness_score(awareness, market_averages.average_awareness)
        
        # 가중 평균 계산
        weighted_score = (
            price_score * self.price_sensitivity +
            quality_score * self.quality_preference +
            awareness_score * (1 - self.brand_loyalty)
        )
        
        return weighted_score
    
    def _calculate_price_score(self, price: Money, market_average: Money) -> float:
        """가격 점수 계산 (시장 평균 대비)"""
        if market_average.is_zero():
            return 50.0
        
        # 가격이 낮을수록 높은 점수
        ratio = price.amount / market_average.amount
        return max(0, 100 - (ratio * 50))
    
    def _calculate_quality_score(self, quality: int, market_average: float) -> float:
        """품질 점수 계산 (시장 평균 대비)"""
        if market_average == 0:
            return 50.0
        
        # 품질이 높을수록 높은 점수
        ratio = quality / market_average
        return min(100, ratio * 50)
    
    def _calculate_awareness_score(self, awareness: int, market_average: float) -> float:
        """인지도 점수 계산 (시장 평균 대비)"""
        if market_average == 0:
            return 50.0
        
        # 인지도가 높을수록 높은 점수
        ratio = awareness / market_average
        return min(100, ratio * 50)
    
    def update_mood_after_purchase(self, satisfaction_level: float) -> 'CustomerAI':
        """구매 후 기분 상태 업데이트"""
        if satisfaction_level >= 90:
            new_mood = CustomerMood.VERY_HAPPY
        elif satisfaction_level >= 70:
            new_mood = CustomerMood.HAPPY
        elif satisfaction_level >= 50:
            new_mood = CustomerMood.NEUTRAL
        elif satisfaction_level >= 30:
            new_mood = CustomerMood.UNHAPPY
        else:
            new_mood = CustomerMood.VERY_UNHAPPY
        
        return self._replace(mood=new_mood)
    
    def record_purchase(self, store_id: UUID) -> 'CustomerAI':
        """구매 기록 업데이트"""
        return self._replace(last_purchase_store_id=store_id)
    
    def get_loyalty_bonus(self, store_id: UUID) -> float:
        """브랜드 충성도 보너스 계산"""
        if self.last_purchase_store_id == store_id:
            return self.brand_loyalty * 20  # 최대 20점 보너스
        return 0.0
    
    def get_mood_modifier(self) -> float:
        """기분 상태에 따른 구매 확률 보정치"""
        mood_modifiers = {
            CustomerMood.VERY_HAPPY: 1.2,
            CustomerMood.HAPPY: 1.1,
            CustomerMood.NEUTRAL: 1.0,
            CustomerMood.UNHAPPY: 0.9,
            CustomerMood.VERY_UNHAPPY: 0.8,
        }
        return mood_modifiers.get(self.mood, 1.0)
    
    def _replace(self, **changes) -> 'CustomerAI':
        """dataclass replace 메서드 래퍼"""
        from dataclasses import replace
        return replace(self, **changes)


@dataclass(frozen=True)
class MarketAverages:
    """시장 평균 데이터 (고객 평가용)"""
    
    average_price: Money
    average_quality: float
    average_awareness: float


@dataclass(frozen=True)
class CustomerDemand:
    """고객 수요 데이터 (수치적 고객 90% 처리용)"""
    
    total_customers: int  # 총 고객 수
    ai_customers: int  # AI 고객 수 (10%)
    numerical_customers: int  # 수치적 고객 수 (90%)
    
    def __post_init__(self):
        """생성 후 유효성 검사"""
        if self.total_customers != self.ai_customers + self.numerical_customers:
            raise ValueError("총 고객 수가 AI 고객 수 + 수치적 고객 수와 일치하지 않습니다")
        
        expected_ai_ratio = self.ai_customers / self.total_customers
        if not 0.09 <= expected_ai_ratio <= 0.11:  # 10% ± 1% 허용
            raise ValueError("AI 고객 비율이 10% 근처가 아닙니다")
    
    def calculate_numerical_demand(self, market_share_percentage: Percentage) -> int:
        """수치적 고객 수요 계산"""
        return int(self.numerical_customers * market_share_percentage.as_ratio())
    
    def get_ai_customer_ratio(self) -> float:
        """AI 고객 비율 반환"""
        return self.ai_customers / self.total_customers if self.total_customers > 0 else 0.0 