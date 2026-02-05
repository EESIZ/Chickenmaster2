from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from core.domain.player import Player
from core.domain.turn import Turn

class RepositoryPort(ABC):
    """
    게임 데이터 저장 및 로드를 위한 포트 인터페이스
    """

    @abstractmethod
    def save_player(self, player: Player) -> None:
        """플레이어 데이터를 저장합니다."""
        pass

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
