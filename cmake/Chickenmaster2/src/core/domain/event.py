"""
이벤트 도메인 모델

게임 내 이벤트 시스템을 나타내는 불변 엔티티입니다.
5가지 이벤트 분류와 다양한 효과를 관리합니다.
이벤트 데이터는 CSV 파일에서 불러옵니다.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, Dict, Any
from uuid import UUID
import json

from common.enums.event_type import EventType
from .value_objects import Money


class EventEffect(Enum):
    """이벤트 효과 유형"""
    
    NO_EFFECT = auto()  # 아무 효과 없음
    MONEY_GAIN = auto()  # 자금 획득
    MONEY_LOSS = auto()  # 자금 손실
    STAT_GAIN = auto()  # 스탯 증가
    STAT_LOSS = auto()  # 스탯 감소
    HAPPINESS_GAIN = auto()  # 행복도 증가
    HAPPINESS_LOSS = auto()  # 행복도 감소
    FATIGUE_GAIN = auto()  # 피로도 증가
    FATIGUE_LOSS = auto()  # 피로도 감소 (휴식 효과)
    RECIPE_GAIN = auto()  # 레시피 획득
    CUSTOMER_GAIN = auto()  # 고객 증가
    CUSTOMER_LOSS = auto()  # 고객 감소
    INVENTORY_GAIN = auto()  # 재고 획득
    INVENTORY_LOSS = auto()  # 재고 손실
    COMPETITOR_EFFECT = auto()  # 경쟁자 영향
    RESEARCH_PROGRESS = auto()  # 연구 진행도 증가
    STORE_UPGRADE = auto()  # 매장 업그레이드
    REPUTATION_GAIN = auto()  # 평판 증가
    REPUTATION_LOSS = auto()  # 평판 감소


@dataclass(frozen=True)
class EventChoice:
    """이벤트 선택지"""
    
    id: str
    description: str
    effects: tuple[Dict[str, Any], ...]  # 효과 데이터
    requirements: Optional[Dict[str, Any]] = None  # 선택 조건
    
    def __post_init__(self):
        """생성 후 유효성 검사"""
        if not self.description.strip():
            raise ValueError("선택지 설명은 비어있을 수 없습니다")
        
        # 빈 효과 배열 허용 (아무 효과 없는 선택지를 위해)
    
    def can_choose(self, player_stats: Dict[str, Any]) -> bool:
        """선택 가능한지 확인"""
        if self.requirements is None:
            return True
        
        # 요구사항 검사 로직 (예: 최소 스탯, 자금 등)
        for req_type, req_value in self.requirements.items():
            if req_type in player_stats:
                if player_stats[req_type] < req_value:
                    return False
        
        return True


@dataclass(frozen=True)
class Event:
    """이벤트 엔티티"""
    
    id: UUID
    csv_id: str  # CSV 파일의 ID
    name: str
    description: str
    event_type: EventType
    
    # 이벤트 속성
    is_chain_event: bool = False  # 연쇄 이벤트 여부
    chain_next_event_id: Optional[UUID] = None  # 다음 연쇄 이벤트 ID
    probability_weight: int = 100  # 발생 확률 가중치
    
    # 선택지 (선택형 이벤트용)
    choices: tuple[EventChoice, ...] = ()
    
    # 자동 효과 (일상/기회/위기 이벤트용)
    auto_effects: tuple[Dict[str, Any], ...] = ()
    
    def __post_init__(self):
        """생성 후 유효성 검사"""
        if not self.name.strip():
            raise ValueError("이벤트 이름은 비어있을 수 없습니다")
        
        if not self.description.strip():
            raise ValueError("이벤트 설명은 비어있을 수 없습니다")
        
        if self.probability_weight <= 0:
            raise ValueError("확률 가중치는 0보다 커야 합니다")
        
        # 선택형 이벤트는 선택지가 있어야 함
        if self.event_type == EventType.CHOICE and len(self.choices) == 0:
            raise ValueError("선택형 이벤트는 최소 1개의 선택지가 있어야 합니다")
        
        # 자동 이벤트는 자동 효과가 있어야 함
        if self.event_type in [EventType.DAILY, EventType.OPPORTUNITY, EventType.CRISIS] and len(self.auto_effects) == 0:
            raise ValueError("자동 이벤트는 최소 1개의 자동 효과가 있어야 합니다")
    
    def is_choice_event(self) -> bool:
        """선택형 이벤트인지 확인"""
        return self.event_type == EventType.CHOICE
    
    def is_auto_event(self) -> bool:
        """자동 이벤트인지 확인"""
        return self.event_type in [EventType.DAILY, EventType.OPPORTUNITY, EventType.CRISIS]
    
    def has_next_chain_event(self) -> bool:
        """다음 연쇄 이벤트가 있는지 확인"""
        return self.is_chain_event and self.chain_next_event_id is not None
    
    def get_available_choices(self, player_stats: Dict[str, Any]) -> list[EventChoice]:
        """플레이어가 선택 가능한 선택지 반환"""
        return [choice for choice in self.choices if choice.can_choose(player_stats)]
    
    def get_choice_by_id(self, choice_id: str) -> Optional[EventChoice]:
        """ID로 선택지 조회"""
        for choice in self.choices:
            if choice.id == choice_id:
                return choice
        return None
    
    def create_chain_event(self, next_event_id: UUID) -> 'Event':
        """연쇄 이벤트 설정 후 새로운 Event 반환"""
        return self._replace(
            is_chain_event=True,
            chain_next_event_id=next_event_id
        )
    
    def _replace(self, **changes) -> 'Event':
        """dataclass replace 메서드 래퍼"""
        from dataclasses import replace
        return replace(self, **changes)


@dataclass(frozen=True)
class EventTemplate:
    """이벤트 템플릿 (CSV에서 로드용)"""
    
    csv_id: str  # CSV 파일의 ID
    name: str
    description: str
    event_type: EventType
    probability_weight: int
    choices: tuple[EventChoice, ...] = ()
    auto_effects: tuple[Dict[str, Any], ...] = ()
    
    def create_event(self, event_id: UUID) -> Event:
        """실제 Event 인스턴스 생성"""
        return Event(
            id=event_id,
            csv_id=self.csv_id,
            name=self.name,
            description=self.description,
            event_type=self.event_type,
            probability_weight=self.probability_weight,
            choices=self.choices,
            auto_effects=self.auto_effects,
        )
    
    @staticmethod
    def from_csv_row(csv_row: Dict[str, str]) -> 'EventTemplate':
        """CSV 행에서 EventTemplate 생성"""
        # JSON 문자열을 파이썬 객체로 변환
        auto_effects_json = csv_row.get('auto_effects', '[]')
        choices_json = csv_row.get('choices', '[]')
        
        try:
            auto_effects_data = json.loads(auto_effects_json) if auto_effects_json.strip() != '[]' else []
            choices_data = json.loads(choices_json) if choices_json.strip() != '[]' else []
        except json.JSONDecodeError as e:
            raise ValueError(f"CSV 데이터 파싱 오류 (ID: {csv_row.get('id', 'unknown')}): {e}")
        
        # EventChoice 객체들 생성
        choices = tuple(
            EventChoice(
                id=choice_data['id'],
                description=choice_data['description'],
                effects=tuple(choice_data.get('effects', [])),
                requirements=choice_data.get('requirements'),
            )
            for choice_data in choices_data
        )
        
        # EventType 변환
        event_type_str = csv_row['event_type'].upper()
        event_type = EventType[event_type_str]
        
        return EventTemplate(
            csv_id=csv_row['id'],
            name=csv_row['name'],
            description=csv_row['description'],
            event_type=event_type,
            probability_weight=int(csv_row['probability_weight']),
            choices=choices,
            auto_effects=tuple(auto_effects_data),
        ) 