"""
포트 계층 패키지

헥사고날 아키텍처의 포트 인터페이스들을 정의합니다.
애플리케이션 계층이 이 인터페이스들을 사용하고, 어댑터 계층이 구현합니다.
"""

from .repository_port import RepositoryPort
from .action_port import ActionPort, ActionRequest, ActionResult
from .ai_engine_port import AIEnginePort, AIDecision
from .event_engine_port import EventEnginePort, EventTriggerResult, EventExecutionResult
from .sales_engine_port import SalesEnginePort, SalesResult, CustomerDecision
from .persistence_port import PersistencePort, SaveGameInfo, SaveResult, LoadResult
from .notification_port import (
    NotificationPort, 
    Notification, 
    NotificationLevel, 
    NotificationType
)

__all__ = [
    # Repository
    "RepositoryPort",
    
    # Action
    "ActionPort",
    "ActionRequest", 
    "ActionResult",
    
    # AI Engine
    "AIEnginePort",
    "AIDecision",
    
    # Event Engine
    "EventEnginePort",
    "EventTriggerResult",
    "EventExecutionResult",
    
    # Sales Engine
    "SalesEnginePort",
    "SalesResult",
    "CustomerDecision",
    
    # Persistence
    "PersistencePort",
    "SaveGameInfo",
    "SaveResult",
    "LoadResult",
    
    # Notification
    "NotificationPort",
    "Notification",
    "NotificationLevel",
    "NotificationType",
] 