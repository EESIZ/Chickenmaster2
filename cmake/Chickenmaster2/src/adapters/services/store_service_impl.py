"""
스토어 서비스 구현체
"""

from typing import List, Optional
from uuid import UUID, uuid4

from core.ports.store_service import IStoreService
from core.domain.store import Store
from core.domain.value_objects import Money


class StoreServiceImpl(IStoreService):
    """스토어 서비스 구현체"""
    
    def __init__(self):
        self._stores = {}  # 임시 저장소 (추후 실제 DB로 대체)
    
    def get_store_by_id(self, store_id: UUID) -> Optional[Store]:
        """ID로 스토어 조회"""
        return self._stores.get(str(store_id))
    
    def get_stores_by_owner(self, owner_id: UUID) -> List[Store]:
        """소유자 ID로 스토어 목록 조회"""
        return [
            store for store in self._stores.values()
            if hasattr(store, 'owner_id') and store.owner_id == owner_id
        ]
    
    def create_store(self, owner_id: UUID, name: str, initial_money: Money) -> Store:
        """새 스토어 생성"""
        store_id = uuid4()
        
        # 기본 매장 생성 (임시 구현)
        store = Store(
            id=store_id,
            name=name,
            money=initial_money,
            manager_hired=False,
            manager_salary=Money(0),
            product_ids=(),
            inventory_ids=()
        )
        
        # owner_id 정보 추가 (임시로 속성 추가)
        # 실제로는 Store 도메인 모델에 owner_id 필드가 있어야 함
        object.__setattr__(store, 'owner_id', owner_id)
        
        self._stores[str(store_id)] = store
        return store
    
    def update_store(self, store: Store) -> Store:
        """스토어 정보 업데이트"""
        self._stores[str(store.id)] = store
        return store
    
    def delete_store(self, store_id: UUID) -> bool:
        """스토어 삭제"""
        if str(store_id) in self._stores:
            del self._stores[str(store_id)]
            return True
        return False 