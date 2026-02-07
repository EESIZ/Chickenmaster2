from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from uuid import UUID

from core.domain.player import Player
from core.domain.competitor import Competitor
from core.domain.turn import Turn
from core.domain.store import Store
from core.domain.product import Product
from core.domain.research import Research


class RepositoryPort(ABC):
    """
    게임 데이터 저장 및 로드를 위한 포트 인터페이스
    """

    # --- Player ---
    @abstractmethod
    def save_player(self, player: Player) -> None:
        """플레이어 데이터를 저장합니다."""
        pass

    @abstractmethod
    def get_player(self, player_id: UUID) -> Optional[Player]:
        """플레이어 데이터를 조회합니다."""
        pass

    @abstractmethod
    def get_all_players(self) -> List[Player]:
        """모든 플레이어 목록을 조회합니다."""
        pass

    # --- Competitor ---
    @abstractmethod
    def save_competitor(self, competitor: Competitor) -> None:
        pass

    @abstractmethod
    def get_all_competitors(self) -> List[Competitor]:
        """모든 경쟁자 목록을 조회합니다."""
        pass

    # --- Turn ---
    @abstractmethod
    def save_turn(self, turn: Turn) -> None:
        """턴 데이터를 저장합니다."""
        pass

    @abstractmethod
    def load_game(self, save_name: str) -> Optional[Dict[str, Any]]:
        """저장된 게임 데이터를 로드합니다."""
        pass

    @abstractmethod
    def load_current_turn(self) -> Optional[Turn]:
        """현재 턴 정보를 로드합니다."""
        pass

    # --- Store ---
    @abstractmethod
    def save_store(self, store: Store) -> None:
        pass

    @abstractmethod
    def get_store(self, store_id: UUID) -> Optional[Store]:
        pass

    # --- Product ---
    @abstractmethod
    def save_product(self, product: Product) -> None:
        """제품 데이터를 저장합니다."""
        pass

    @abstractmethod
    def get_product(self, product_id: UUID) -> Optional[Product]:
        pass

    # --- Research ---
    @abstractmethod
    def save_research(self, research: Research) -> None:
        pass

    @abstractmethod
    def get_research(self, research_id: UUID) -> Optional[Research]:
        pass

    # --- Analysis (AIService용) ---
    @abstractmethod
    def save_player_analysis(self, player_id: UUID, analysis: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def load_player_analysis(self, player_id: UUID) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def load_turn_analysis_history(self, player_id: UUID, limit: int) -> List[Dict[str, Any]]:
        pass
