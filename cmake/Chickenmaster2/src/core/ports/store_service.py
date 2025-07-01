"""
스토어 서비스 포트 인터페이스
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..domain.store import Store
from ..domain.value_objects import Money


class IStoreService(ABC):
    """스토어 관리 서비스 인터페이스"""
    
    @abstractmethod
    def get_store_by_id(self, store_id: UUID) -> Optional[Store]:
        """ID로 스토어 조회"""
        pass
    
    @abstractmethod
    def get_stores_by_owner(self, owner_id: UUID) -> List[Store]:
        """소유자 ID로 스토어 목록 조회"""
        pass
    
    @abstractmethod
    def create_store(self, owner_id: UUID, name: str, initial_money: Money) -> Store:
        """새 스토어 생성"""
        pass
    
    @abstractmethod
    def update_store(self, store: Store) -> Store:
        """스토어 정보 업데이트"""
        pass
    
    @abstractmethod
    def delete_store(self, store_id: UUID) -> bool:
        """스토어 삭제"""
        pass 