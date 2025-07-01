"""
알림 포트 인터페이스

UI 알림과 메시지 전달을 담당하는 인터페이스입니다.
NotificationService가 이 인터페이스를 구현합니다.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class NotificationLevel(Enum):
    """알림 레벨"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    CRITICAL = "critical"


class NotificationType(Enum):
    """알림 타입"""
    GAME_EVENT = "game_event"
    PLAYER_ACTION = "player_action"
    SYSTEM_MESSAGE = "system_message"
    ACHIEVEMENT = "achievement"
    WARNING = "warning"
    ERROR = "error"


class Notification:
    """알림 DTO"""
    def __init__(self, id: str, title: str, message: str, level: NotificationLevel,
                 notification_type: NotificationType, timestamp: datetime,
                 data: Optional[Dict[str, Any]] = None, auto_dismiss: bool = False,
                 dismiss_after_seconds: int = 0):
        self.id = id
        self.title = title
        self.message = message
        self.level = level
        self.notification_type = notification_type
        self.timestamp = timestamp
        self.data = data or {}
        self.auto_dismiss = auto_dismiss
        self.dismiss_after_seconds = dismiss_after_seconds


class NotificationPort(ABC):
    """알림 포트 인터페이스"""
    
    @abstractmethod
    def show_notification(self, notification: Notification) -> bool:
        """알림을 표시합니다.
        
        Args:
            notification: 표시할 알림
            
        Returns:
            bool: 표시 성공 여부
        """
        pass
    
    @abstractmethod
    def show_info(self, title: str, message: str, data: Optional[Dict[str, Any]] = None) -> bool:
        """정보 알림을 표시합니다.
        
        Args:
            title: 알림 제목
            message: 알림 메시지
            data: 추가 데이터
            
        Returns:
            bool: 표시 성공 여부
        """
        pass
    
    @abstractmethod
    def show_warning(self, title: str, message: str, data: Optional[Dict[str, Any]] = None) -> bool:
        """경고 알림을 표시합니다.
        
        Args:
            title: 알림 제목
            message: 알림 메시지
            data: 추가 데이터
            
        Returns:
            bool: 표시 성공 여부
        """
        pass
    
    @abstractmethod
    def show_error(self, title: str, message: str, data: Optional[Dict[str, Any]] = None) -> bool:
        """오류 알림을 표시합니다.
        
        Args:
            title: 알림 제목
            message: 알림 메시지
            data: 추가 데이터
            
        Returns:
            bool: 표시 성공 여부
        """
        pass
    
    @abstractmethod
    def show_success(self, title: str, message: str, data: Optional[Dict[str, Any]] = None) -> bool:
        """성공 알림을 표시합니다.
        
        Args:
            title: 알림 제목
            message: 알림 메시지
            data: 추가 데이터
            
        Returns:
            bool: 표시 성공 여부
        """
        pass
    
    @abstractmethod
    def show_achievement(self, title: str, description: str, 
                        achievement_data: Dict[str, Any]) -> bool:
        """업적 달성 알림을 표시합니다.
        
        Args:
            title: 업적 제목
            description: 업적 설명
            achievement_data: 업적 데이터
            
        Returns:
            bool: 표시 성공 여부
        """
        pass
    
    @abstractmethod
    def dismiss_notification(self, notification_id: str) -> bool:
        """특정 알림을 제거합니다.
        
        Args:
            notification_id: 제거할 알림 ID
            
        Returns:
            bool: 제거 성공 여부
        """
        pass
    
    @abstractmethod
    def dismiss_all_notifications(self) -> int:
        """모든 알림을 제거합니다.
        
        Returns:
            int: 제거된 알림 수
        """
        pass
    
    @abstractmethod
    def get_active_notifications(self) -> List[Notification]:
        """현재 활성 알림 목록을 반환합니다.
        
        Returns:
            List[Notification]: 활성 알림 목록
        """
        pass
    
    @abstractmethod
    def get_notification_history(self, limit: int = 50) -> List[Notification]:
        """알림 기록을 반환합니다.
        
        Args:
            limit: 반환할 최대 기록 수
            
        Returns:
            List[Notification]: 알림 기록 목록
        """
        pass
    
    @abstractmethod
    def set_notification_settings(self, settings: Dict[str, Any]) -> bool:
        """알림 설정을 변경합니다.
        
        Args:
            settings: 알림 설정 딕셔너리
            
        Returns:
            bool: 설정 변경 성공 여부
        """
        pass
    
    @abstractmethod
    def is_notification_enabled(self, notification_type: NotificationType) -> bool:
        """특정 타입의 알림이 활성화되어 있는지 확인합니다.
        
        Args:
            notification_type: 확인할 알림 타입
            
        Returns:
            bool: 활성화 여부
        """
        pass
    
    @abstractmethod
    def show_game_event_notification(self, event_title: str, event_description: str,
                                   choices: List[str]) -> bool:
        """게임 이벤트 알림을 표시합니다.
        
        Args:
            event_title: 이벤트 제목
            event_description: 이벤트 설명
            choices: 선택지 목록
            
        Returns:
            bool: 표시 성공 여부
        """
        pass
    
    @abstractmethod
    def show_turn_summary(self, turn_data: Dict[str, Any]) -> bool:
        """턴 요약 알림을 표시합니다.
        
        Args:
            turn_data: 턴 요약 데이터
            
        Returns:
            bool: 표시 성공 여부
        """
        pass
    
    @abstractmethod
    def show_progress_notification(self, title: str, current: int, total: int,
                                 message: str = "") -> bool:
        """진행률 알림을 표시합니다.
        
        Args:
            title: 알림 제목
            current: 현재 진행량
            total: 전체 진행량
            message: 추가 메시지
            
        Returns:
            bool: 표시 성공 여부
        """
        pass 