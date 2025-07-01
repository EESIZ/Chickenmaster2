"""
게임 데이터 저장/로드 포트 인터페이스

모든 도메인 엔티티의 영속성을 담당하는 추상 인터페이스입니다.
JSON, 데이터베이스 등 다양한 저장소 구현체가 이 인터페이스를 구현합니다.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import date

from core.domain.player import Player
from core.domain.store import Store, ParttimeWorker
from core.domain.product import Product
from core.domain.recipe import Recipe
from core.domain.inventory import Inventory
from core.domain.research import Research
from core.domain.competitor import Competitor
from core.domain.customer import CustomerAI
from core.domain.turn import Turn


class RepositoryPort(ABC):
    """게임 데이터 저장소 포트 인터페이스"""
    
    # ==================== 게임 세션 관리 ====================
    
    @abstractmethod
    def save_game(self, save_name: str, game_data: Dict[str, Any]) -> bool:
        """게임 전체 상태를 저장합니다.
        
        Args:
            save_name: 저장 파일명
            game_data: 저장할 게임 데이터 (플레이어, 매장, 턴 등 모든 정보)
            
        Returns:
            bool: 저장 성공 여부
        """
        pass
    
    @abstractmethod
    def load_game(self, save_name: str) -> Optional[Dict[str, Any]]:
        """저장된 게임을 불러옵니다.
        
        Args:
            save_name: 불러올 저장 파일명
            
        Returns:
            Optional[Dict[str, Any]]: 게임 데이터 또는 None (파일 없음)
        """
        pass
    
    @abstractmethod
    def list_saved_games(self) -> List[str]:
        """저장된 게임 목록을 반환합니다.
        
        Returns:
            List[str]: 저장 파일명 목록
        """
        pass
    
    @abstractmethod
    def delete_saved_game(self, save_name: str) -> bool:
        """저장된 게임을 삭제합니다.
        
        Args:
            save_name: 삭제할 저장 파일명
            
        Returns:
            bool: 삭제 성공 여부
        """
        pass
    
    # ==================== 플레이어 관리 ====================
    
    @abstractmethod
    def save_player(self, player: Player) -> bool:
        """플레이어 정보를 저장합니다."""
        pass
    
    @abstractmethod
    def load_player(self, player_id: UUID) -> Optional[Player]:
        """플레이어 정보를 불러옵니다."""
        pass
    
    # ==================== 매장 관리 ====================
    
    @abstractmethod
    def save_store(self, store: Store) -> bool:
        """매장 정보를 저장합니다."""
        pass
    
    @abstractmethod
    def load_store(self, store_id: UUID) -> Optional[Store]:
        """매장 정보를 불러옵니다."""
        pass
    
    @abstractmethod
    def load_stores_by_owner(self, owner_id: UUID) -> List[Store]:
        """특정 소유자의 모든 매장을 불러옵니다."""
        pass
    
    # ==================== 제품 관리 ====================
    
    @abstractmethod
    def save_product(self, product: Product) -> bool:
        """제품 정보를 저장합니다."""
        pass
    
    @abstractmethod
    def load_product(self, product_id: UUID) -> Optional[Product]:
        """제품 정보를 불러옵니다."""
        pass
    
    @abstractmethod
    def load_products_by_store(self, store_id: UUID) -> List[Product]:
        """특정 매장의 모든 제품을 불러옵니다."""
        pass
    
    # ==================== 레시피 관리 ====================
    
    @abstractmethod
    def save_recipe(self, recipe: Recipe) -> bool:
        """레시피 정보를 저장합니다."""
        pass
    
    @abstractmethod
    def load_recipe(self, recipe_id: UUID) -> Optional[Recipe]:
        """레시피 정보를 불러옵니다."""
        pass
    
    @abstractmethod
    def load_all_recipes(self) -> List[Recipe]:
        """모든 레시피를 불러옵니다."""
        pass
    
    # ==================== 재고 관리 ====================
    
    @abstractmethod
    def save_inventory_item(self, item: Inventory) -> bool:
        """재고 아이템을 저장합니다."""
        pass
    
    @abstractmethod
    def load_inventory_item(self, item_id: UUID) -> Optional[Inventory]:
        """재고 아이템을 불러옵니다."""
        pass
    
    @abstractmethod
    def load_inventory_by_store(self, store_id: UUID) -> List[Inventory]:
        """특정 매장의 모든 재고를 불러옵니다."""
        pass
    
    # ==================== 연구 관리 ====================
    
    @abstractmethod
    def save_research(self, research: Research) -> bool:
        """연구 정보를 저장합니다."""
        pass
    
    @abstractmethod
    def load_research(self, research_id: UUID) -> Optional[Research]:
        """연구 정보를 불러옵니다."""
        pass
    
    @abstractmethod
    def load_research_by_player(self, player_id: UUID) -> List[Research]:
        """특정 플레이어의 모든 연구를 불러옵니다."""
        pass
    
    # ==================== 경쟁자 AI 관리 ====================
    
    @abstractmethod
    def save_competitor(self, competitor: Competitor) -> bool:
        """경쟁자 AI 정보를 저장합니다."""
        pass
    
    @abstractmethod
    def load_competitor(self, competitor_id: UUID) -> Optional[Competitor]:
        """경쟁자 AI 정보를 불러옵니다."""
        pass
    
    @abstractmethod
    def load_all_competitors(self) -> List[Competitor]:
        """모든 경쟁자 AI를 불러옵니다."""
        pass
    
    # ==================== 고객 AI 관리 ====================
    
    @abstractmethod
    def save_customer(self, customer: CustomerAI) -> bool:
        """고객 AI 정보를 저장합니다."""
        pass
    
    @abstractmethod
    def load_customer(self, customer_id: UUID) -> Optional[CustomerAI]:
        """고객 AI 정보를 불러옵니다."""
        pass
    
    @abstractmethod
    def load_all_customers(self) -> List[CustomerAI]:
        """모든 고객 AI를 불러옵니다."""
        pass
    
    # ==================== 직원 관리 ====================
    
    @abstractmethod
    def save_parttime_worker(self, worker: ParttimeWorker) -> bool:
        """알바 직원 정보를 저장합니다."""
        pass
    
    @abstractmethod
    def load_parttime_worker(self, worker_id: UUID) -> Optional[ParttimeWorker]:
        """알바 직원 정보를 불러옵니다."""
        pass
    
    @abstractmethod
    def load_workers_by_store(self, store_id: UUID) -> List[ParttimeWorker]:
        """특정 매장의 모든 알바 직원을 불러옵니다."""
        pass
    
    # ==================== 턴 관리 ====================
    
    @abstractmethod
    def save_turn(self, turn: Turn) -> bool:
        """턴 정보를 저장합니다."""
        pass
    
    @abstractmethod
    def load_current_turn(self) -> Optional[Turn]:
        """현재 턴 정보를 불러옵니다."""
        pass
    
    # ==================== 통계 및 조회 ====================
    
    @abstractmethod
    def get_total_entities_count(self) -> Dict[str, int]:
        """각 엔티티별 총 개수를 반환합니다.
        
        Returns:
            Dict[str, int]: 엔티티명과 개수의 딕셔너리
        """
        pass
    
    @abstractmethod
    def cleanup_orphaned_entities(self) -> int:
        """참조되지 않는 고아 엔티티들을 정리합니다.
        
        Returns:
            int: 정리된 엔티티 개수
        """
        pass
    
    # ==================== AI 분석 데이터 관리 ====================
    
    @abstractmethod
    def save_player_analysis(self, player_id: UUID, analysis_data: Dict[str, Any]) -> bool:
        """플레이어 분석 결과를 저장합니다.
        
        Args:
            player_id: 분석 대상 플레이어 ID
            analysis_data: 분석 결과 데이터 (패턴, 성향, 전략 등)
            
        Returns:
            bool: 저장 성공 여부
        """
        pass
    
    @abstractmethod
    def load_player_analysis(self, player_id: UUID) -> Optional[Dict[str, Any]]:
        """플레이어 분석 결과를 불러옵니다.
        
        Args:
            player_id: 분석 대상 플레이어 ID
            
        Returns:
            Optional[Dict[str, Any]]: 분석 결과 데이터 또는 None
        """
        pass
    
    @abstractmethod
    def save_turn_analysis(self, turn_number: int, analysis_data: Dict[str, Any]) -> bool:
        """턴별 분석 데이터를 저장합니다.
        
        Args:
            turn_number: 턴 번호
            analysis_data: 턴 분석 데이터 (행동 패턴, 경쟁 상황 등)
            
        Returns:
            bool: 저장 성공 여부
        """
        pass
    
    @abstractmethod
    def load_turn_analysis_history(self, player_id: UUID, recent_turns: int = 10) -> List[Dict[str, Any]]:
        """플레이어의 최근 턴 분석 히스토리를 불러옵니다.
        
        Args:
            player_id: 플레이어 ID
            recent_turns: 불러올 최근 턴 수
            
        Returns:
            List[Dict[str, Any]]: 턴별 분석 데이터 리스트
        """
        pass
    
    @abstractmethod
    def update_competitive_situation(self, situation_data: Dict[str, Any]) -> bool:
        """경쟁 상황 데이터를 업데이트합니다.
        
        Args:
            situation_data: 시장 상황, 경쟁자 현황 등
            
        Returns:
            bool: 업데이트 성공 여부
        """
        pass
    
    @abstractmethod
    def get_competitive_situation(self) -> Dict[str, Any]:
        """현재 경쟁 상황 데이터를 반환합니다.
        
        Returns:
            Dict[str, Any]: 경쟁 상황 데이터
        """
        pass 