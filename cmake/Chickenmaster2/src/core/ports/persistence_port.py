"""
영속성 포트 인터페이스

게임 상태의 저장, 불러오기, 백업 관리를 담당하는 인터페이스입니다.
PersistenceService가 이 인터페이스를 구현합니다.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime


class SaveGameInfo:
    """저장된 게임 정보 DTO"""
    def __init__(self, save_name: str, save_time: datetime, player_name: str, 
                 current_day: int, total_money: int, file_size: int):
        self.save_name = save_name
        self.save_time = save_time
        self.player_name = player_name
        self.current_day = current_day
        self.total_money = total_money
        self.file_size = file_size


class SaveResult:
    """저장 결과 DTO"""
    def __init__(self, success: bool, message: str, save_path: str = "", 
                 file_size: int = 0):
        self.success = success
        self.message = message
        self.save_path = save_path
        self.file_size = file_size


class LoadResult:
    """불러오기 결과 DTO"""
    def __init__(self, success: bool, message: str, game_data: Optional[Dict[str, Any]] = None):
        self.success = success
        self.message = message
        self.game_data = game_data


class PersistencePort(ABC):
    """영속성 포트 인터페이스"""
    
    @abstractmethod
    def save_game(self, save_name: str, game_data: Dict[str, Any], 
                  create_backup: bool = True) -> SaveResult:
        """게임 상태를 저장합니다.
        
        Args:
            save_name: 저장 파일명
            game_data: 저장할 게임 데이터
            create_backup: 백업 생성 여부
            
        Returns:
            SaveResult: 저장 결과
        """
        pass
    
    @abstractmethod
    def load_game(self, save_name: str) -> LoadResult:
        """저장된 게임을 불러옵니다.
        
        Args:
            save_name: 불러올 저장 파일명
            
        Returns:
            LoadResult: 불러오기 결과
        """
        pass
    
    @abstractmethod
    def list_saved_games(self) -> List[SaveGameInfo]:
        """저장된 게임 목록을 반환합니다.
        
        Returns:
            List[SaveGameInfo]: 저장된 게임 정보 목록
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
    
    @abstractmethod
    def create_backup(self, save_name: str) -> bool:
        """저장 파일의 백업을 생성합니다.
        
        Args:
            save_name: 백업할 저장 파일명
            
        Returns:
            bool: 백업 생성 성공 여부
        """
        pass
    
    @abstractmethod
    def restore_from_backup(self, save_name: str, backup_timestamp: str) -> LoadResult:
        """백업에서 게임을 복원합니다.
        
        Args:
            save_name: 복원할 저장 파일명
            backup_timestamp: 백업 타임스탬프
            
        Returns:
            LoadResult: 복원 결과
        """
        pass
    
    @abstractmethod
    def list_backups(self, save_name: str) -> List[str]:
        """특정 저장 파일의 백업 목록을 반환합니다.
        
        Args:
            save_name: 저장 파일명
            
        Returns:
            List[str]: 백업 타임스탬프 목록
        """
        pass
    
    @abstractmethod
    def cleanup_old_backups(self, max_backups: int = 5) -> int:
        """오래된 백업을 정리합니다.
        
        Args:
            max_backups: 유지할 최대 백업 수
            
        Returns:
            int: 삭제된 백업 수
        """
        pass
    
    @abstractmethod
    def export_save_data(self, save_name: str, export_format: str = "json") -> SaveResult:
        """저장 데이터를 외부 형식으로 내보냅니다.
        
        Args:
            save_name: 내보낼 저장 파일명
            export_format: 내보낼 형식 ("json", "csv" 등)
            
        Returns:
            SaveResult: 내보내기 결과
        """
        pass
    
    @abstractmethod
    def import_save_data(self, import_path: str, save_name: str) -> LoadResult:
        """외부에서 저장 데이터를 가져옵니다.
        
        Args:
            import_path: 가져올 파일 경로
            save_name: 저장할 파일명
            
        Returns:
            LoadResult: 가져오기 결과
        """
        pass
    
    @abstractmethod
    def validate_save_file(self, save_name: str) -> tuple[bool, str]:
        """저장 파일의 유효성을 검사합니다.
        
        Args:
            save_name: 검사할 저장 파일명
            
        Returns:
            tuple[bool, str]: (유효성 여부, 메시지)
        """
        pass
    
    @abstractmethod
    def get_save_file_info(self, save_name: str) -> Optional[SaveGameInfo]:
        """저장 파일의 상세 정보를 반환합니다.
        
        Args:
            save_name: 조회할 저장 파일명
            
        Returns:
            Optional[SaveGameInfo]: 저장 파일 정보 (없으면 None)
        """
        pass
    
    @abstractmethod
    def compress_save_file(self, save_name: str) -> bool:
        """저장 파일을 압축합니다.
        
        Args:
            save_name: 압축할 저장 파일명
            
        Returns:
            bool: 압축 성공 여부
        """
        pass
    
    @abstractmethod
    def get_storage_usage(self) -> Dict[str, Any]:
        """저장소 사용량 정보를 반환합니다.
        
        Returns:
            Dict[str, Any]: 저장소 사용량 정보
        """
        pass 