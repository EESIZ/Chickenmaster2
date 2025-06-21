"""
제품 도메인 모델

매장에서 판매하는 제품을 나타내는 불변 엔티티입니다.
가격, 품질, 인지도 등의 시장 경쟁 요소를 관리합니다.
"""

from dataclasses import dataclass
from enum import Enum, auto
from uuid import UUID

from .value_objects import Money, Percentage, Progress


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
    recipe_id: UUID  # 기반 레시피 ID
    name: str
    category: ProductCategory
    
    # 시장 경쟁 요소
    price: Money  # 판매 가격
    quality: int  # 품질 (요리 스탯 + 연구도 + 재료 품질 평균)
    awareness: int  # 인지도 (판매량, 광고, 점유율에 따라 변동)
    
    def __post_init__(self):
        """생성 후 유효성 검사"""
        if not self.name.strip():
            raise ValueError("제품 이름은 비어있을 수 없습니다")
        
        if self.price.amount <= 0:
            raise ValueError("제품 가격은 0원보다 커야 합니다")
        
        if self.quality < 0:
            raise ValueError("품질은 음수일 수 없습니다")
        
        if self.awareness < 0:
            raise ValueError("인지도는 음수일 수 없습니다")
    
    def set_price(self, new_price: Money) -> 'Product':
        """가격 설정 후 새로운 Product 반환"""
        from ...constants import PRICE_MIN, PRICE_MAX
        
        if not PRICE_MIN <= new_price.amount <= PRICE_MAX:
            raise ValueError(f"가격은 {PRICE_MIN:,}원 ~ {PRICE_MAX:,}원 사이여야 합니다")
        
        return self._replace(price=new_price)
    
    def increase_awareness(self, amount: int) -> 'Product':
        """인지도 증가 후 새로운 Product 반환"""
        new_awareness = max(0, self.awareness + amount)
        return self._replace(awareness=new_awareness)
    
    def decrease_awareness(self, amount: int) -> 'Product':
        """인지도 감소 후 새로운 Product 반환"""
        new_awareness = max(0, self.awareness - amount)
        return self._replace(awareness=new_awareness)
    
    def apply_daily_awareness_decay(self) -> 'Product':
        """일일 인지도 감소 적용 후 새로운 Product 반환"""
        from ...constants import AWARENESS_DAILY_DECAY
        return self.decrease_awareness(AWARENESS_DAILY_DECAY)
    
    def apply_sale_awareness_gain(self) -> 'Product':
        """판매 시 인지도 증가 적용 후 새로운 Product 반환"""
        from ...constants import AWARENESS_GAIN_PER_SALE
        return self.increase_awareness(AWARENESS_GAIN_PER_SALE)
    
    def update_quality(self, new_quality: int) -> 'Product':
        """품질 업데이트 후 새로운 Product 반환"""
        if new_quality < 0:
            raise ValueError("품질은 음수일 수 없습니다")
        
        return self._replace(quality=new_quality)
    
    def calculate_price_score(self, market_average_price: Money) -> float:
        """가격 점수 계산 (시장 평균 대비)"""
        if market_average_price.amount == 0:
            return 100.0
        
        return (self.price.amount / market_average_price.amount) * 100
    
    def calculate_quality_score(self, market_average_quality: float) -> float:
        """품질 점수 계산 (시장 평균 대비)"""
        if market_average_quality == 0:
            return 100.0
        
        return (self.quality / market_average_quality) * 100
    
    def calculate_awareness_score(self, market_average_awareness: float) -> float:
        """인지도 점수 계산 (시장 평균 대비)"""
        if market_average_awareness == 0:
            return 100.0
        
        return (self.awareness / market_average_awareness) * 100
    
    def calculate_comprehensive_score(
        self, 
        market_average_price: Money, 
        market_average_quality: float, 
        market_average_awareness: float
    ) -> float:
        """종합 점수 계산 (가격 + 품질 + 인지도)"""
        price_score = self.calculate_price_score(market_average_price)
        quality_score = self.calculate_quality_score(market_average_quality)
        awareness_score = self.calculate_awareness_score(market_average_awareness)
        
        return price_score + quality_score + awareness_score
    
    def is_same_category(self, other: 'Product') -> bool:
        """같은 카테고리인지 확인"""
        return self.category == other.category
    
    def get_display_info(self) -> str:
        """제품 정보 문자열 반환"""
        return f"{self.name} - {self.price.format_korean()} (품질: {self.quality}, 인지도: {self.awareness})"
    
    def _replace(self, **changes) -> 'Product':
        """dataclass replace 메서드 래퍼"""
        from dataclasses import replace
        return replace(self, **changes) 