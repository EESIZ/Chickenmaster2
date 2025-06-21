"""
도메인 레이어 - 핵심 비즈니스 엔티티들

헥사고날 아키텍처의 핵심 도메인 레이어입니다.
모든 도메인 엔티티는 불변(immutable) 객체로 구성됩니다.
"""

# 값 객체
from .value_objects import (
    Money,
    Percentage,
    Hours,
    Progress,
    Experience,
    StatValue,
)

# 도메인 엔티티
from .player import Player, PlayerEffectiveStats
from .store import Store, ParttimeWorker
from .product import Product, ProductCategory
from .recipe import Recipe, DefaultRecipes
from .competitor import Competitor, CompetitorStrategy, DelayedAction
from .research import Research, ResearchTemplate, DefaultResearchTemplates
from .inventory import InventoryItem
from .customer import CustomerAI, CustomerType, CustomerMood, MarketAverages, CustomerDemand
from .event import Event, EventChoice, EventEffect, EventTemplate
from .event_loader import EventLoaderPort
from .turn import Turn, GamePhase, TurnResult, GameCalendar

__all__ = [
    # 값 객체
    "Money",
    "Percentage", 
    "Hours",
    "Progress",
    "Experience",
    "StatValue",
    
    # 플레이어 관련
    "Player",
    "PlayerEffectiveStats",
    
    # 매장 관련
    "Store",
    "ParttimeWorker",
    
    # 제품 관련
    "Product",
    "ProductCategory",
    
    # 레시피 관련
    "Recipe",
    "DefaultRecipes",
    
    # 경쟁자 관련
    "Competitor",
    "CompetitorStrategy",
    "DelayedAction",
    
    # 연구 관련
    "Research",
    "ResearchTemplate",
    "DefaultResearchTemplates",
    
    # 재고 관련
    "InventoryItem",
    
    # 고객 관련
    "CustomerAI",
    "CustomerType",
    "CustomerMood",
    "MarketAverages",
    "CustomerDemand",
    
    # 이벤트 관련
    "Event",
    "EventChoice",
    "EventEffect",
    "EventTemplate",
    "EventLoaderPort",
    
    # 턴 관련
    "Turn",
    "GamePhase",
    "TurnResult",
    "GameCalendar",
] 