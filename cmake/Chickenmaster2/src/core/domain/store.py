"""
매장 도메인 모델

플레이어나 경쟁자가 운영하는 매장을 나타내는 불변 엔티티입니다.
제품, 재고, 직원 등을 관리합니다.
"""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID
from datetime import date

from .value_objects import Money, Percentage


@dataclass(frozen=True)
class Store:
    """매장 엔티티"""
    
    id: UUID
    owner_id: UUID  # 플레이어 또는 경쟁자 ID
    name: str
    is_first_store: bool  # 첫 번째 매장 여부
    
    # 매장 정보
    monthly_rent: Money  # 월 임대료
    
    # 제품들 (ID 참조)
    product_ids: tuple[UUID, ...]
    
    # 재고 항목들 (ID 참조)
    inventory_item_ids: tuple[UUID, ...]
    
    # 직원들 (알바 ID 참조)
    parttime_worker_ids: tuple[UUID, ...]
    
    # 기본값이 있는 필드들
    awareness: Percentage = Percentage(0.0)  # 인지도 (0~100%)
    manager_id: Optional[UUID] = None  # 점장 (2번째 이후 매장용, 선택적)
    
    def __post_init__(self):
        """생성 후 유효성 검사"""
        if not self.name.strip():
            raise ValueError("매장 이름은 비어있을 수 없습니다")
        
        if self.monthly_rent.amount <= 0:
            raise ValueError("임대료는 0원보다 커야 합니다")
    
    def add_product(self, product_id: UUID) -> 'Store':
        """제품 추가 후 새로운 Store 반환"""
        if product_id in self.product_ids:
            raise ValueError(f"이미 존재하는 제품입니다: {product_id}")
        
        new_product_ids = self.product_ids + (product_id,)
        return self._replace(product_ids=new_product_ids)
    
    def remove_product(self, product_id: UUID) -> 'Store':
        """제품 제거 후 새로운 Store 반환"""
        if product_id not in self.product_ids:
            raise ValueError(f"존재하지 않는 제품입니다: {product_id}")
        
        new_product_ids = tuple(pid for pid in self.product_ids if pid != product_id)
        return self._replace(product_ids=new_product_ids)
    
    def add_inventory_item(self, item_id: UUID) -> 'Store':
        """재고 아이템 추가 후 새로운 Store 반환"""
        new_inventory_ids = self.inventory_item_ids + (item_id,)
        return self._replace(inventory_item_ids=new_inventory_ids)
    
    def remove_inventory_item(self, item_id: UUID) -> 'Store':
        """재고 아이템 제거 후 새로운 Store 반환"""
        if item_id not in self.inventory_item_ids:
            raise ValueError(f"존재하지 않는 재고 아이템입니다: {item_id}")
        
        new_inventory_ids = tuple(iid for iid in self.inventory_item_ids if iid != item_id)
        return self._replace(inventory_item_ids=new_inventory_ids)
    
    def hire_parttime_worker(self, worker_id: UUID) -> 'Store':
        """알바 고용 후 새로운 Store 반환"""
        if worker_id in self.parttime_worker_ids:
            raise ValueError(f"이미 고용된 알바입니다: {worker_id}")
        
        new_worker_ids = self.parttime_worker_ids + (worker_id,)
        return self._replace(parttime_worker_ids=new_worker_ids)
    
    def fire_parttime_worker(self, worker_id: UUID) -> 'Store':
        """알바 해고 후 새로운 Store 반환"""
        if worker_id not in self.parttime_worker_ids:
            raise ValueError(f"존재하지 않는 알바입니다: {worker_id}")
        
        new_worker_ids = tuple(wid for wid in self.parttime_worker_ids if wid != worker_id)
        return self._replace(parttime_worker_ids=new_worker_ids)
    
    def assign_manager(self, manager_id: UUID) -> 'Store':
        """점장 배치 후 새로운 Store 반환"""
        if self.is_first_store:
            raise ValueError("첫 번째 매장에는 점장을 배치할 수 없습니다")
        return self._replace(manager_id=manager_id)
    
    def remove_manager(self) -> 'Store':
        """점장 제거 후 새로운 Store 반환"""
        return self._replace(manager_id=None)
    
    def has_manager(self) -> bool:
        """점장이 있는지 확인"""
        return self.manager_id is not None
    
    def can_operate(self) -> bool:
        """매장 운영이 가능한지 확인 (첫 번째 매장이거나 점장이 있는 경우)"""
        return self.is_first_store or self.has_manager()
    
    def get_daily_rent(self) -> Money:
        """일일 임대료 계산"""
        return self.monthly_rent / 30
    
    def has_products(self) -> bool:
        """판매할 제품이 있는지 확인"""
        return len(self.product_ids) > 0
    
    def has_inventory(self) -> bool:
        """재고가 있는지 확인"""
        return len(self.inventory_item_ids) > 0
    
    def get_parttime_worker_count(self) -> int:
        """알바 직원 수 조회"""
        return len(self.parttime_worker_ids)
    
    def add_awareness(self, awareness_increase: float) -> 'Store':
        """인지도 증가 후 새로운 Store 반환"""
        new_awareness = self.awareness + awareness_increase
        return self._replace(awareness=new_awareness)
    
    def _replace(self, **changes) -> 'Store':
        """dataclass replace 메서드 래퍼"""
        from dataclasses import replace
        return replace(self, **changes)
    
    @classmethod
    def create_new(cls, name: str, owner_id: UUID, is_first_store: bool = True, monthly_rent: int = 500000) -> 'Store':
        """새 매장 생성 팩토리 메서드"""
        from uuid import uuid4
        
        return cls(
            id=uuid4(),
            owner_id=owner_id,
            name=name,
            is_first_store=is_first_store,
            monthly_rent=Money(monthly_rent),
            product_ids=(),
            inventory_item_ids=(),
            parttime_worker_ids=()
        )


@dataclass(frozen=True)
class ParttimeWorker:
    """알바 직원 엔티티"""
    
    id: UUID
    name: str  # 랜덤 한국인 이름
    monthly_salary: Money  # 월급
    fatigue_reduction_ratio: float  # 피로도 감소 비율 (20% ~ 50%)
    
    def __post_init__(self):
        """생성 후 유효성 검사"""
        if not self.name.strip():
            raise ValueError("알바 이름은 비어있을 수 없습니다")
        
        if self.monthly_salary.amount <= 0:
            raise ValueError("월급은 0원보다 커야 합니다")
        
        if not 0.2 <= self.fatigue_reduction_ratio <= 0.5:
            raise ValueError("피로도 감소 비율은 20%~50% 사이여야 합니다")
    
    def get_daily_salary(self) -> Money:
        """일일 급여 계산"""
        return self.monthly_salary / 30
    
    def apply_fatigue_reduction(self, base_fatigue: float) -> float:
        """피로도 감소 적용"""
        return base_fatigue * (1 - self.fatigue_reduction_ratio) 