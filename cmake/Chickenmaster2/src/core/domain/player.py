"""
플레이어 도메인 모델

게임의 주인공인 플레이어를 나타내는 불변 엔티티입니다.
스탯, 피로도, 행복도, 자금 등의 상태를 관리합니다.
"""

from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

from .value_objects import Money, Percentage, StatValue, Experience
from common.enums.action_type import ActionType


@dataclass(frozen=True)
class Player:
    """플레이어 엔티티"""
    
    id: UUID
    name: str
    
    # 5가지 기본 스탯 (README 규칙)
    cooking: StatValue  # 요리
    management: StatValue  # 경영
    service: StatValue  # 서비스
    tech: StatValue  # 기술
    stamina: StatValue  # 체력
    
    # 변동 상태
    fatigue: Percentage  # 피로도
    happiness: Percentage  # 행복도
    money: Money  # 자금
    
    # 소유 매장들 (ID 참조)
    store_ids: tuple[UUID, ...]
    
    # 진행 중인 연구들 (ID 참조)
    research_ids: tuple[UUID, ...]
    
    def __post_init__(self):
        """생성 후 유효성 검사"""
        if not self.name.strip():
            raise ValueError("플레이어 이름은 비어있을 수 없습니다")
        
        if len(self.store_ids) == 0:
            raise ValueError("플레이어는 최소 1개의 매장을 가져야 합니다")
    
    def apply_fatigue(self, fatigue_delta: Percentage) -> 'Player':
        """피로도 적용 후 새로운 Player 반환"""
        new_fatigue = self.fatigue + fatigue_delta
        return self._replace(fatigue=new_fatigue)
    
    def apply_happiness(self, happiness_delta: Percentage) -> 'Player':
        """행복도 적용 후 새로운 Player 반환"""
        new_happiness = self.happiness + happiness_delta
        return self._replace(happiness=new_happiness)
    
    def spend_money(self, amount: Money) -> 'Player':
        """자금 사용 후 새로운 Player 반환"""
        if self.money < amount:
            raise ValueError(f"자금이 부족합니다. 보유: {self.money.format_korean()}, 필요: {amount.format_korean()}")
        
        new_money = self.money - amount
        return self._replace(money=new_money)
    
    def earn_money(self, amount: Money) -> 'Player':
        """자금 획득 후 새로운 Player 반환"""
        new_money = self.money + amount
        return self._replace(money=new_money)
    
    def gain_stat_experience(self, stat_type: str, exp_amount: int) -> 'Player':
        """스탯 경험치 획득 후 새로운 Player 반환"""
        current_stat = getattr(self, stat_type)
        new_stat = current_stat.add_experience(exp_amount)
        
        return self._replace(**{stat_type: new_stat})
    
    def add_store(self, store_id: UUID) -> 'Player':
        """매장 추가 후 새로운 Player 반환"""
        new_store_ids = self.store_ids + (store_id,)
        return self._replace(store_ids=new_store_ids)
    
    def add_research(self, research_id: UUID) -> 'Player':
        """연구 추가 후 새로운 Player 반환"""
        new_research_ids = self.research_ids + (research_id,)
        return self._replace(research_ids=new_research_ids)
    
    def is_fatigued(self) -> bool:
        """피로도 경고 상태인지 확인 (체력의 50% 이상)"""
        threshold = Percentage(self.stamina.base_value * 0.5)  # 50%
        return self.fatigue >= threshold
    
    def is_critically_fatigued(self) -> bool:
        """피로도 위험 상태인지 확인 (체력의 90% 이상)"""
        threshold = Percentage(self.stamina.base_value * 0.9)  # 90%
        return self.fatigue >= threshold
    
    def is_knocked_out(self) -> bool:
        """피로도 기절 상태인지 확인 (체력의 100% 이상)"""
        threshold = Percentage(self.stamina.base_value)  # 100%
        return self.fatigue >= threshold
    
    def is_completely_exhausted(self) -> bool:
        """완전 탈진 상태인지 확인 (체력의 200% 이상, 행동 불가)"""
        threshold = Percentage(self.stamina.base_value * 2)  # 200%
        return self.fatigue >= threshold
    
    def get_effective_stats(self) -> 'PlayerEffectiveStats':
        """피로도를 반영한 실제 스탯 반환"""
        if self.is_knocked_out():
            # 체력 초과 시 모든 스탯 1/2
            penalty_ratio = 0.5
            return PlayerEffectiveStats(
                cooking=self.cooking.apply_fatigue_penalty(penalty_ratio),
                management=self.management.apply_fatigue_penalty(penalty_ratio),
                service=self.service.apply_fatigue_penalty(penalty_ratio),
                tech=self.tech.apply_fatigue_penalty(penalty_ratio),
                stamina=self.stamina.apply_fatigue_penalty(penalty_ratio),
            )
        else:
            # 정상 상태
            return PlayerEffectiveStats(
                cooking=self.cooking,
                management=self.management,
                service=self.service,
                tech=self.tech,
                stamina=self.stamina,
            )
    
    def calculate_happiness_change(self, profit_amount: Money, is_profit: bool, fatigue_ratio: float) -> float:
        """행복도 변화량 계산 (README.md 공식 적용)
        
        Args:
            profit_amount: 수익/손실의 절댓값 (항상 양수)
            is_profit: True면 흑자, False면 적자
            fatigue_ratio: 피로도 비율 (0.0~1.0)
        
        README.md 규칙:
        - 피로도가 50% 이상인채 턴을 종료하면 감소
        - 적자가 발생하면 감소  
        - 흑자가 발생하면 증가
        - 피로도가 50% 미만인채 턴을 종료하면 증가
        - f(x) = 50 ± A√(|x-50|/k) (A=50, k=1) 공식은 변화량 크기 조정용
        """
        # README.md 공식 상수 (A=50, k=1)
        HAPPINESS_BASELINE = 50
        HAPPINESS_CURVE_A = 50
        HAPPINESS_CURVE_K = 1
        
        total_change = 0.0
        current_happiness = self.happiness.value
        
        # 1. 피로도에 따른 기본 변화량
        if fatigue_ratio >= 0.5:  # 50% 이상
            # 피로도 높음 -> 감소
            base_fatigue_change = -10  # 기본 감소량
        else:  # 50% 미만
            # 피로도 낮음 -> 증가  
            base_fatigue_change = 5  # 기본 증가량
        
        # 2. 수익에 따른 기본 변화량
        if profit_amount.amount > 0:
            if is_profit:  # 흑자
                # 수익 크기에 따른 변화량 (100만원 기준)
                profit_ratio = min(1.0, profit_amount.amount / 1_000_000)
                base_profit_change = 15 * profit_ratio  # 최대 15 증가
            else:  # 적자
                # 손실 크기에 따른 변화량 (100만원 기준)
                loss_ratio = min(1.0, profit_amount.amount / 1_000_000)
                base_profit_change = -15 * loss_ratio  # 최대 15 감소
        else:  # 수익 없음
            base_profit_change = 0
        
        # 3. 기본 변화량 합계
        base_change = base_fatigue_change + base_profit_change
        
        # 4. README.md 공식 적용: 50에서 멀어질수록 변화량 감소
        # f(x) = 50 ± A√(|x-50|/k) - 이 공식은 변화량의 효율성을 조정
        distance_from_baseline = abs(current_happiness - HAPPINESS_BASELINE)
        efficiency_factor = 1.0 - (distance_from_baseline / 100.0)  # 0~1 사이 값
        efficiency_factor = max(0.1, efficiency_factor)  # 최소 10% 효율성 유지
        
        # 최종 변화량 = 기본 변화량 * 효율성 계수
        final_change = base_change * efficiency_factor
        
        # 5. 결과값을 행복도 범위(0~100) 내로 제한
        new_happiness = current_happiness + final_change
        new_happiness = max(0, min(100, new_happiness))
        
        return new_happiness - current_happiness
    
    def _replace(self, **changes) -> 'Player':
        """dataclass replace 메서드 래퍼"""
        from dataclasses import replace
        return replace(self, **changes)
    
    @classmethod
    def create_new(cls, name: str, character_type: str = "chef", initial_money: int = 1000000) -> 'Player':
        """새 플레이어 생성 팩토리 메서드"""
        from uuid import uuid4
        
        # 캐릭터별 스탯 프리셋 (characterSelect.py와 동일)
        character_presets = {
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
        
        # 캐릭터 타입 유효성 검사
        if character_type not in character_presets:
            raise ValueError(f"유효하지 않은 캐릭터 타입: {character_type}")
        
        preset = character_presets[character_type]
        
        # 스탯들 생성 (캐릭터 프리셋 값 + 경험치 0)
        base_exp = Experience(0)
        cooking = StatValue(preset["cooking"])
        management = StatValue(preset["management"]) 
        service = StatValue(preset["service"])
        tech = StatValue(preset["tech"])
        stamina = StatValue(preset["stamina"])
        
        # 첫 번째 매장 ID 생성 (실제 매장은 별도로 생성 필요)
        first_store_id = uuid4()
        
        return cls(
            id=uuid4(),
            name=name,
            cooking=cooking,
            management=management,
            service=service,
            tech=tech,
            stamina=stamina,
            fatigue=Percentage(0),
            happiness=Percentage(50),  # 중간 행복도로 시작
            money=Money(initial_money),
            store_ids=(first_store_id,),
            research_ids=()
        )


@dataclass(frozen=True)
class PlayerEffectiveStats:
    """피로도를 반영한 플레이어의 실제 스탯"""
    
    cooking: StatValue
    management: StatValue
    service: StatValue
    tech: StatValue
    stamina: StatValue
    
    def get_stat(self, stat_name: str) -> StatValue:
        """스탯 이름으로 스탯 값 조회"""
        return getattr(self, stat_name) 