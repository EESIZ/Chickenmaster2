import random
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID

from core.ports.event_port import EventPort, EventResult
from core.ports.repository_port import RepositoryPort
from core.domain.event_loader import EventLoaderPort
from core.domain.turn import Turn
from core.domain.player import Player
from core.domain.event import Event
from core.domain.value_objects import Money


class EventService(EventPort):
    """이벤트 서비스 구현체"""

    def __init__(self, repository: RepositoryPort, event_loader: EventLoaderPort):
        self._repository = repository
        self._event_loader = event_loader

    def process_daily_events(self, turn: Turn, player: Player) -> EventResult:
        """일일 이벤트 처리"""

        # 이벤트 로더가 load_all_events 메서드를 가지고 있다고 가정 (CSVEventLoader 확장)
        if hasattr(self._event_loader, 'load_all_events'):
            events = self._event_loader.load_all_events()
        else:
            # Fallback
            events = []

        # 3. 조건에 맞는 이벤트 필터링
        available_events = [
            e for e in events
            if self._check_event_condition(e, turn, player)
        ]

        if not available_events:
            return EventResult(occurred=False, message="평화로운 하루입니다.")

        # 4. 확률적 발생 (30%)
        if random.random() > 0.3:
             return EventResult(occurred=False, message="특별한 사건 없이 하루가 지나갑니다.")

        # 5. 이벤트 선택
        selected_event = random.choice(available_events)

        # 자동 효과 적용
        effects_msg = []
        updated_player = player
        for effect in selected_event.auto_effects:
            result = self._apply_effect(effect, updated_player)
            updated_player = result[0]
            effects_msg.append(result[1])

        self._repository.save_player(updated_player)

        return EventResult(
            occurred=True,
            event=selected_event,
            message=f"[{selected_event.name}] {selected_event.description}",
            effects_applied=effects_msg
        )

    def handle_event_choice(self, event_id: UUID, choice_index: int, player: Player) -> EventResult:
        # csv_id로 조회해야 함. event_id가 UUID라면 매핑 필요.
        # 여기서는 단순화를 위해 생략
        return EventResult(occurred=False, message="선택지 처리는 아직 지원되지 않습니다.")

    def _check_event_condition(self, event: Event, turn: Turn, player: Player) -> bool:
        return True

    def _apply_effect(self, effect: Dict[str, Any], player: Player) -> Tuple[Player, str]:
        """이벤트 효과 적용"""

        effect_type = effect.get('effect_type')
        value = effect.get('value')

        if effect_type == "MONEY_CHANGE":
             amount = int(value)
             if amount > 0:
                 return player.earn_money(Money(amount)), f"자금 {amount}원 획득"
             else:
                 loss = abs(amount)
                 # 자금 부족 시 처리 (0원으로 만듦)
                 if player.money.amount < loss:
                     return player.spend_money(player.money), f"자금 {player.money.amount}원 손실 (파산 위기)"
                 return player.spend_money(Money(loss)), f"자금 {loss}원 감소"

        return player, "효과 적용됨"
