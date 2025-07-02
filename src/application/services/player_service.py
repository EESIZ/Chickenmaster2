"""
플레이어 응용 서비스

플레이어 관련 유스케이스를 구현합니다.
"""

from typing import List, Optional
from uuid import UUID, uuid4

from ..dtos.player_dto import (
    CreatePlayerRequest, 
    PlayerStatusDto, 
    PlayerStatsDto,
    PlayerActionRequest
)
from core.domain.player import Player
from core.domain.value_objects import Money, StatValue, Percentage
from core.domain.events.player_events import (
    PlayerCreatedEvent,
    PlayerMoneyChangedEvent,
    PlayerStoreAddedEvent
)
from core.ports.store_service import IStoreService
from core.ports.research_service import IResearchService


class PlayerService:
    """플레이어 응용 서비스"""
    
    def __init__(
        self,
        store_service: IStoreService,
        research_service: IResearchService,
        event_publisher=None  # 이벤트 발행자 (추후 구현)
    ):
        self._store_service = store_service
        self._research_service = research_service
        self._event_publisher = event_publisher
        self._players = {}  # 임시 저장소 (추후 Repository로 대체)
    
    def create_player(self, request: CreatePlayerRequest) -> PlayerStatusDto:
        """새 플레이어 생성"""
        # 캐릭터 프리셋에 따른 스탯 설정
        preset_stats = self._get_character_preset_stats(request.character_preset)
        
        # 플레이어 생성
        player = Player(
            id=uuid4(),
            name=request.name,
            cooking=StatValue(base_value=preset_stats["cooking"]),
            management=StatValue(base_value=preset_stats["management"]),
            service=StatValue(base_value=preset_stats["service"]),
            tech=StatValue(base_value=preset_stats["tech"]),
            stamina=StatValue(base_value=preset_stats["stamina"]),
            fatigue=Percentage(0),
            money=Money(request.initial_money),
            store_ids=(),  # 초기에는 매장 없음
            research_ids=()  # 초기에는 연구 없음
        )
        
        # 첫 번째 매장 생성
        store = self._store_service.create_store(
            owner_id=player.id,
            name=f"{player.name}의 치킨집",
            initial_money=Money(100000)
        )
        
        # 플레이어에 매장 추가
        player = player.add_store(store.id)
        
        # 저장
        self._players[str(player.id)] = player
        
        # 이벤트 발행
        if self._event_publisher:
            self._event_publisher.publish(
                PlayerCreatedEvent(
                    event_id=uuid4(),
                    occurred_at=None,
                    aggregate_id=player.id,
                    player_id=player.id,
                    player_name=player.name,
                    initial_money=player.money
                )
            )
            
            self._event_publisher.publish(
                PlayerStoreAddedEvent(
                    event_id=uuid4(),
                    occurred_at=None,
                    aggregate_id=player.id,
                    player_id=player.id,
                    store_id=store.id,
                    store_name=store.name
                )
            )
        
        return self._convert_to_status_dto(player)
    
    def get_player_status(self, player_id: str) -> Optional[PlayerStatusDto]:
        """플레이어 상태 조회"""
        player = self._players.get(player_id)
        if not player:
            return None
        
        return self._convert_to_status_dto(player)
    
    def execute_player_action(self, request: PlayerActionRequest) -> PlayerStatusDto:
        """플레이어 행동 실행"""
        player = self._players.get(request.player_id)
        if not player:
            raise ValueError(f"플레이어를 찾을 수 없습니다: {request.player_id}")
        
        # 행동 유형에 따른 처리
        if request.action_type == "rest":
            # 휴식 - 피로도 감소
            new_fatigue = Percentage(max(0, player.fatigue.value - 10))
            player = player._replace(fatigue=new_fatigue)
        
        elif request.action_type == "work":
            # 작업 - 피로도 증가, 경험치 획득
            new_fatigue = Percentage(min(100, player.fatigue.value + 5))
            player = player._replace(fatigue=new_fatigue)
        
        # 저장
        self._players[request.player_id] = player
        
        return self._convert_to_status_dto(player)
    
    def _get_character_preset_stats(self, preset: str) -> dict:
        """캐릭터 프리셋 스탯 반환"""
        presets = {
            "chef": {
                "cooking": 16,
                "management": 8,
                "service": 12,
                "stamina": 10,
                "tech": 14
            },
            "businessman": {
                "cooking": 8,
                "management": 16,
                "service": 12,
                "stamina": 14,
                "tech": 10
            },
            "service_expert": {
                "cooking": 10,
                "management": 12,
                "service": 16,
                "stamina": 12,
                "tech": 8
            },
            "testman": {
                "cooking": 20,
                "management": 20,
                "service": 20,
                "stamina": 20,
                "tech": 20
            }
        }
        
        return presets.get(preset, presets["chef"])
    
    def _convert_to_status_dto(self, player: Player) -> PlayerStatusDto:
        """Player 도메인 객체를 DTO로 변환"""
        return PlayerStatusDto(
            id=str(player.id),
            name=player.name,
            stats=PlayerStatsDto(
                cooking=player.cooking.base_value,
                management=player.management.base_value,
                service=player.service.base_value,
                tech=player.tech.base_value,
                stamina=player.stamina.base_value
            ),
            fatigue=player.fatigue.value,
            money=player.money.amount,
            store_count=len(player.store_ids),
            research_count=len(player.research_ids)
        ) 