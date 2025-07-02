"""
이벤트 로더 인터페이스

CSV 파일에서 이벤트 데이터를 로드하기 위한 인터페이스입니다.
실제 구현은 infrastructure/adapter 계층에서 담당합니다.
"""

from abc import ABC, abstractmethod
from typing import List
from .event import EventTemplate


class EventLoaderPort(ABC):
    """이벤트 로더 포트 인터페이스"""
    
    @abstractmethod
    def load_event_templates(self, csv_file_path: str) -> List[EventTemplate]:
        """CSV 파일에서 이벤트 템플릿들을 로드합니다.
        
        Args:
            csv_file_path: CSV 파일 경로
            
        Returns:
            EventTemplate 객체들의 리스트
            
        Raises:
            FileNotFoundError: CSV 파일을 찾을 수 없을 때
            ValueError: CSV 데이터 형식이 잘못되었을 때
        """
        pass
    
    @abstractmethod
    def get_event_template_by_id(self, csv_id: str) -> EventTemplate:
        """CSV ID로 특정 이벤트 템플릿을 조회합니다.
        
        Args:
            csv_id: CSV 파일의 이벤트 ID
            
        Returns:
            EventTemplate 객체
            
        Raises:
            ValueError: 해당 ID의 이벤트를 찾을 수 없을 때
        """
        pass
    
    @abstractmethod
    def validate_csv_format(self, csv_file_path: str) -> bool:
        """CSV 파일 형식이 올바른지 검증합니다.
        
        Args:
            csv_file_path: CSV 파일 경로
            
        Returns:
            검증 성공 여부
        """
        pass 