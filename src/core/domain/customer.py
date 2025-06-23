"""
고객 AI 도메인 모델

게임 내 고객 AI 시스템을 나타내는 불변 엔티티입니다.
10% AI 고객과 90% 수치 계산 고객으로 구성됩니다.
"""

from dataclasses import dataclass
from uuid import UUID
from typing import Optional

from .value_objects import Money, Percentage


@dataclass(frozen=True)
class CustomerAI:
    """AI 고객 엔티티 (전체 고객의 10%)"""
    
    id: UUID
    name: str
    
    # 고객 특성
    price_sensitivity: float  # 가격 민감도 (0.0 ~ 1.0)
    quality_preference: float  # 품질 선호도 (0.0 ~ 1.0)
    brand_loyalty: float  # 브랜드 충성도 (0.0 ~ 1.0)
    desire: Percentage  # 욕구 (0~100)
    
    # 현재 상태
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
    
    def record_purchase(self, store_id: UUID) -> 'CustomerAI':
        """구매 기록 업데이트 및 욕구 초기화"""
        return self._replace(
            last_purchase_store_id=store_id,
            desire=Percentage(0)
        )
    
    def update_daily_desire(self, dice_value: int) -> 'CustomerAI':
        """매일 욕구 업데이트 (Calldice의 값/10 만큼 증가)"""
        desire_increase = Percentage(dice_value / 10)
        new_desire = self.desire + desire_increase
        return self._replace(desire=new_desire)
    
    def get_purchase_probability(self, market_share: Percentage) -> float:
        """구매 확률 계산 ([욕구]% * [점유율]%)"""
        return self.desire.as_ratio() * market_share.as_ratio()
    
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