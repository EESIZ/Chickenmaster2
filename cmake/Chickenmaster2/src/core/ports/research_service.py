"""
연구 서비스 포트 인터페이스
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..domain.research import Research
from common.enums.research_type import ResearchType


class IResearchService(ABC):
    """연구 관리 서비스 인터페이스"""
    
    @abstractmethod
    def get_research_by_id(self, research_id: UUID) -> Optional[Research]:
        """ID로 연구 조회"""
        pass
    
    @abstractmethod
    def get_research_by_player(self, player_id: UUID) -> List[Research]:
        """플레이어 ID로 연구 목록 조회"""
        pass
    
    @abstractmethod
    def start_research(self, player_id: UUID, research_type: ResearchType) -> Research:
        """새 연구 시작"""
        pass
    
    @abstractmethod
    def advance_research(self, research_id: UUID, progress_amount: int) -> Research:
        """연구 진행"""
        pass
    
    @abstractmethod
    def complete_research(self, research_id: UUID) -> Research:
        """연구 완료"""
        pass 