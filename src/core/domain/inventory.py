"""
재고 도메인 모델

매장에서 사용하는 재고를 나타내는 불변 엔티티입니다.
단순한 수량과 품질만 관리합니다.
"""

from dataclasses import dataclass
from uuid import UUID

from .value_objects import Money


@dataclass(frozen=True)
class InventoryItem:
    """재고 아이템 엔티티"""
    
    id: UUID
    name: str
    
    # 재고 정보
    quantity: int  # 수량
    quality: int  # 품질 (1~100)
    purchase_price: Money  # 구매 가격
    
    def __post_init__(self):
        """생성 후 유효성 검사"""
        if not self.name.strip():
            raise ValueError("재고 아이템 이름은 비어있을 수 없습니다")
        
        if self.quantity < 0:
            raise ValueError("수량은 음수일 수 없습니다")
        
        if not 1 <= self.quality <= 100:
            raise ValueError("품질은 1~100 사이여야 합니다")
        
        if self.purchase_price.amount < 0:
            raise ValueError("구매 가격은 음수일 수 없습니다")
    
    def use_quantity(self, amount: int) -> 'InventoryItem':
        """수량 사용 후 새로운 InventoryItem 반환"""
        if amount < 0:
            raise ValueError("사용량은 음수일 수 없습니다")
        
        if self.quantity < amount:
            raise ValueError(f"재고 부족. 보유: {self.quantity}, 필요: {amount}")
        
        new_quantity = self.quantity - amount
        return self._replace(quantity=new_quantity)
    
    def add_quantity(self, amount: int) -> 'InventoryItem':
        """수량 추가 후 새로운 InventoryItem 반환"""
        if amount < 0:
            raise ValueError("추가량은 음수일 수 없습니다")
        
        new_quantity = self.quantity + amount
        return self._replace(quantity=new_quantity)
    
    def is_running_low(self) -> bool:
        """재고 부족 상태인지 확인"""
        from ...constants import INVENTORY_LOW_THRESHOLD
        return self.quantity <= INVENTORY_LOW_THRESHOLD
    
    def is_out_of_stock(self) -> bool:
        """재고 소진 상태인지 확인"""
        return self.quantity == 0
    
    def calculate_total_value(self) -> Money:
        """총 재고 가치 계산"""
        return self.purchase_price * self.quantity
    
    def get_quality_grade(self) -> str:
        """품질 등급 문자열 반환"""
        if self.quality >= 90:
            return "최상급"
        elif self.quality >= 80:
            return "상급"
        elif self.quality >= 70:
            return "중급"
        elif self.quality >= 60:
            return "하급"
        else:
            return "불량"
    
    def get_display_info(self) -> str:
        """재고 정보 문자열 반환"""
        return f"{self.name} - {self.quantity}개, 품질: {self.get_quality_grade()}"
    
    def _replace(self, **changes) -> 'InventoryItem':
        """dataclass replace 메서드 래퍼"""
        from dataclasses import replace
        return replace(self, **changes) 