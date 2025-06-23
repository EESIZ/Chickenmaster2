"""
제품 도메인 모델

게임 내 제품을 나타내는 불변 엔티티입니다.
제품의 품질은 [요리]스탯과 [제품]의 [연구도], 재료의 [품질]의 평균으로 계산됩니다.
"""

from dataclasses import dataclass
from enum import Enum, auto
from uuid import UUID
from typing import List

from .value_objects import Money, Percentage, Progress
from .inventory import Inventory


class ProductCategory(Enum):
    """제품 카테고리"""
    
    FRIED_CHICKEN = auto()  # 후라이드 치킨
    SEASONED_CHICKEN = auto()  # 양념 치킨
    CRISPY_CHICKEN = auto()  # 크리스피 치킨
    COMBO = auto()  # 콤보 세트
    SIDE_DISH = auto()  # 사이드 메뉴


@dataclass(frozen=True)
class Product:
    """제품 엔티티"""
    
    id: UUID
    name: str
    recipe_id: UUID
    selling_price: Money
    research_progress: Progress  # 연구도 (0~100)
    ingredients: List[Inventory]  # 재료 목록
    awareness: int  # 인지도
    
    def __post_init__(self):
        """생성 후 유효성 검사"""
        if not self.name.strip():
            raise ValueError("제품 이름은 비어있을 수 없습니다")
        
        if self.selling_price.is_negative():
            raise ValueError("판매 가격은 음수일 수 없습니다")
        
        if not self.ingredients:
            raise ValueError("재료 목록은 비어있을 수 없습니다")
        
        if self.awareness < 0:
            raise ValueError("인지도는 음수일 수 없습니다")
    
    def calculate_quality(self, cooking_stat: int) -> int:
        """제품 품질 계산 ([요리]스탯과 [제품]의 [연구도], 재료의 [품질]의 평균)"""
        # 재료 품질 평균 계산
        total_ingredient_quality = sum(ingredient.quality for ingredient in self.ingredients)
        avg_ingredient_quality = total_ingredient_quality // len(self.ingredients)
        
        # 전체 품질 평균 계산
        total_quality = cooking_stat + self.research_progress.value + avg_ingredient_quality
        return total_quality // 3
    
    def calculate_cost(self) -> Money:
        """제품 원가 계산 (재료비 합계)"""
        total_cost = Money(0)
        for ingredient in self.ingredients:
            total_cost += ingredient.purchase_price
        return total_cost
    
    def calculate_profit_margin(self) -> float:
        """수익률 계산 ((판매가 - 원가) / 원가)"""
        cost = self.calculate_cost()
        if cost.is_zero():
            return 0.0
        return (self.selling_price.amount - cost.amount) / cost.amount
    
    def update_research_progress(self, progress: Progress) -> 'Product':
        """연구도 업데이트"""
        return self._replace(research_progress=progress)
    
    def update_selling_price(self, price: Money) -> 'Product':
        """판매 가격 업데이트"""
        if price.is_negative():
            raise ValueError("판매 가격은 음수일 수 없습니다")
        return self._replace(selling_price=price)
    
    def increase_awareness_by_sale(self) -> 'Product':
        """판매로 인한 인지도 증가 (3 증가)"""
        return self._replace(awareness=self.awareness + 3)
    
    def decrease_awareness_daily(self) -> 'Product':
        """매일 인지도 감소 (1 감소)"""
        new_awareness = max(0, self.awareness - 1)
        return self._replace(awareness=new_awareness)
    
    def increase_awareness_by_market_share(self, market_share_percentage: float) -> 'Product':
        """시장 점유율에 따른 인지도 증가 (점유율 * 10)"""
        increase = int(market_share_percentage * 10)
        return self._replace(awareness=self.awareness + increase)
    
    def increase_awareness_by_advertising(self, my_ad_cost: Money, competitor_max_ad_cost: Money) -> 'Product':
        """광고로 인한 인지도 증가
        - 경쟁자들의 광고비용보다 높으면 매일 현재 광고비만큼 증가
        - 낮으면 매일 1씩 증가
        """
        if my_ad_cost > competitor_max_ad_cost:
            increase = my_ad_cost.amount // 10000  # 1만원당 1씩 증가
        else:
            increase = 1
        return self._replace(awareness=self.awareness + increase)
    
    def calculate_price_score(self, market_average_price: Money) -> float:
        """가격 점수 계산 (시장 평균 대비)"""
        if market_average_price.is_zero():
            return 100.0
        return (self.selling_price.amount / market_average_price.amount) * 100
    
    def calculate_quality_score(self, market_average_quality: float) -> float:
        """품질 점수 계산 (시장 평균 대비)"""
        if market_average_quality == 0:
            return 100.0
        return (self.calculate_quality(0) / market_average_quality) * 100  # 요리 스탯은 별도로 전달
    
    def calculate_awareness_score(self, market_average_awareness: float) -> float:
        """인지도 점수 계산 (시장 평균 대비)"""
        if market_average_awareness == 0:
            return 100.0
        return (self.awareness / market_average_awareness) * 100
    
    def calculate_comprehensive_score(self, market_averages: 'MarketAverages') -> float:
        """종합 점수 계산 (가격/품질/인지도 점수의 합)"""
        price_score = self.calculate_price_score(market_averages.average_price)
        quality_score = self.calculate_quality_score(market_averages.average_quality)
        awareness_score = self.calculate_awareness_score(market_averages.average_awareness)
        
        return price_score + quality_score + awareness_score
    
    def is_same_category(self, other: 'Product') -> bool:
        """같은 카테고리인지 확인"""
        return self.recipe_id == other.recipe_id
    
    def get_display_info(self) -> str:
        """제품 정보 문자열 반환"""
        return f"{self.name} - {self.selling_price.format_korean()} (품질: {self.calculate_quality(0)}, 인지도: {self.awareness})"
    
    def _replace(self, **changes) -> 'Product':
        """dataclass replace 메서드 래퍼"""
        from dataclasses import replace
        return replace(self, **changes)


@dataclass(frozen=True)
class MarketAverages:
    """시장 평균 데이터"""
    
    average_price: Money
    average_quality: float
    average_awareness: float 