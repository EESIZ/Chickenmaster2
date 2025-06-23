"""
재고 도메인 모델

게임 내 재고 시스템을 나타내는 불변 엔티티입니다.
"""

from dataclasses import dataclass
from uuid import UUID

from .value_objects import Money


@dataclass(frozen=True)
class Inventory:
    """재고 엔티티"""
    
    id: UUID
    name: str
    quantity: int
    quality: int  # 0-100
    purchase_price: Money
    
    def __post_init__(self):
        """생성 후 유효성 검사"""
        if not self.name.strip():
            raise ValueError("재고 이름은 비어있을 수 없습니다")
        
        if self.quantity < 0:
            raise ValueError("재고 수량은 음수일 수 없습니다")
        
        if not 0 <= self.quality <= 100:
            raise ValueError("재고 품질은 0-100 사이여야 합니다")
        
        if self.purchase_price.is_negative():
            raise ValueError("구매 가격은 음수일 수 없습니다")
    
    def add(self, quantity: int, quality: int, purchase_price: Money) -> 'Inventory':
        """재고 추가"""
        if quantity <= 0:
            raise ValueError("추가할 수량은 양수여야 합니다")
        
        if not 0 <= quality <= 100:
            raise ValueError("품질은 0-100 사이여야 합니다")
        
        if purchase_price.is_negative():
            raise ValueError("구매 가격은 음수일 수 없습니다")
        
        # 평균 품질 계산
        total_quality = (self.quality * self.quantity) + (quality * quantity)
        new_quantity = self.quantity + quantity
        new_quality = total_quality // new_quantity
        
        # 평균 구매 가격 계산
        total_price = (self.purchase_price * self.quantity) + (purchase_price * quantity)
        new_purchase_price = total_price // new_quantity
        
        return self._replace(
            quantity=new_quantity,
            quality=new_quality,
            purchase_price=new_purchase_price
        )
    
    def remove(self, quantity: int) -> 'Inventory':
        """재고 제거"""
        if quantity <= 0:
            raise ValueError("제거할 수량은 양수여야 합니다")
        
        if quantity > self.quantity:
            raise ValueError("제거할 수량이 현재 재고보다 많습니다")
        
        return self._replace(quantity=self.quantity - quantity)
    
    def _replace(self, **changes) -> 'Inventory':
        """dataclass replace 메서드 래퍼"""
        from dataclasses import replace
        return replace(self, **changes) 