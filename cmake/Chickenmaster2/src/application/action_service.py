"""
플레이어 행동 응용 서비스

플레이어의 행동 실행과 관련된 유스케이스를 구현합니다.
README.md 규칙에 따라 6가지 행동 카테고리를 처리합니다.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from core.domain.player import Player
from core.domain.store import Store
from core.domain.inventory import Inventory
from core.domain.research import Research
from core.domain.value_objects import Money, Percentage
from core.ports.repository_port import RepositoryPort
from common.enums.action_type import (
    ActionType,
    CookingAction,
    AdvertisingAction,
    OperationAction,
    ResearchAction,
    PersonalAction,
    RestAction,
)


@dataclass(frozen=True)
class ActionRequest:
    """행동 요청 DTO"""
    player_id: UUID
    action_type: ActionType
    specific_action: str  # 세부 행동 (예: "FLYER", "RECIPE")
    time_hours: int  # 소모할 시간 (시간 단위)
    target_id: Optional[UUID] = None  # 대상 ID (매장, 연구 등)


@dataclass(frozen=True)
class ActionResult:
    """행동 결과 DTO"""
    success: bool
    message: str
    time_consumed: int  # 실제 소모된 시간
    fatigue_change: float  # 피로도 변화량
    money_change: int  # 자금 변화량
    experience_gains: Dict[str, int]  # 스탯별 경험치 획득량
    updated_player: Player


class ActionService:
    """플레이어 행동 응용 서비스"""
    
    # README.md 규칙에 따른 행동별 기본 시간 소모량 (시간 단위)
    ACTION_TIME_COSTS = {
        # 조리 행동
        CookingAction.PREPARE_INGREDIENTS: 2,
        CookingAction.COOK: 3,
        CookingAction.INSPECT_INGREDIENTS: 1,
        
        # 광고 행동
        AdvertisingAction.FLYER: 2,
        AdvertisingAction.ONLINE_AD: 1,
        AdvertisingAction.DELIVERY_APP: 1,
        
        # 운영 행동
        OperationAction.ORDER_INGREDIENTS: 1,
        OperationAction.CLEAN: 2,
        OperationAction.EQUIPMENT_CHECK: 1,
        OperationAction.HIRE_PARTTIME: 2,
        
        # 연구 행동
        ResearchAction.RECIPE: 3,
        ResearchAction.MANAGEMENT: 3,
        ResearchAction.ADVERTISING_RESEARCH: 3,
        ResearchAction.SERVICE: 3,
        
        # 개인 행동
        PersonalAction.VACATION: 4,
        PersonalAction.STUDY: 2,
        PersonalAction.EXERCISE: 2,
        
        # 휴식 행동
        RestAction.SLEEP: 1,  # 1시간당 처리
    }
    
    # 행동별 피로도 변화량 (시간당)
    ACTION_FATIGUE_COSTS = {
        # 조리 행동 (중간 피로도)
        CookingAction.PREPARE_INGREDIENTS: 3,
        CookingAction.COOK: 4,
        CookingAction.INSPECT_INGREDIENTS: 2,
        
        # 광고 행동 (낮은 피로도)
        AdvertisingAction.FLYER: 2,
        AdvertisingAction.ONLINE_AD: 1,
        AdvertisingAction.DELIVERY_APP: 1,
        
        # 운영 행동 (높은 피로도)
        OperationAction.ORDER_INGREDIENTS: 2,
        OperationAction.CLEAN: 5,
        OperationAction.EQUIPMENT_CHECK: 3,
        OperationAction.HIRE_PARTTIME: 2,
        
        # 연구 행동 (중간 피로도)
        ResearchAction.RECIPE: 3,
        ResearchAction.MANAGEMENT: 2,
        ResearchAction.ADVERTISING_RESEARCH: 2,
        ResearchAction.SERVICE: 3,
        
        # 개인 행동 (피로도 회복 또는 증가)
        PersonalAction.VACATION: -8,  # 휴가는 피로도 감소
        PersonalAction.STUDY: 2,
        PersonalAction.EXERCISE: 4,
        
        # 휴식 행동 (피로도 회복)
        RestAction.SLEEP: -16,  # README.md: 시간당 16 피로도 감소
    }
    
    # 행동별 경험치 획득량 (시간당)
    ACTION_EXPERIENCE_GAINS = {
        # 조리 행동 -> 요리 스탯
        CookingAction.PREPARE_INGREDIENTS: {"cooking": 8},
        CookingAction.COOK: {"cooking": 12},
        CookingAction.INSPECT_INGREDIENTS: {"cooking": 4, "management": 2},
        
        # 광고 행동 -> 경영 스탯
        AdvertisingAction.FLYER: {"management": 6},
        AdvertisingAction.ONLINE_AD: {"management": 8, "tech": 4},
        AdvertisingAction.DELIVERY_APP: {"management": 6, "tech": 6},
        
        # 운영 행동 -> 경영, 서비스 스탯
        OperationAction.ORDER_INGREDIENTS: {"management": 8},
        OperationAction.CLEAN: {"service": 10},
        OperationAction.EQUIPMENT_CHECK: {"tech": 8, "management": 4},
        OperationAction.HIRE_PARTTIME: {"management": 10, "service": 4},
        
        # 연구 행동 -> 해당 분야 스탯
        ResearchAction.RECIPE: {"cooking": 15},
        ResearchAction.MANAGEMENT: {"management": 15},
        ResearchAction.ADVERTISING_RESEARCH: {"management": 12, "tech": 8},
        ResearchAction.SERVICE: {"service": 15},
        
        # 개인 행동 -> 체력, 기술 스탯
        PersonalAction.VACATION: {"stamina": 12},  # 휴가는 체력 회복
        PersonalAction.STUDY: {"tech": 15, "management": 5},
        PersonalAction.EXERCISE: {"stamina": 20},
        
        # 휴식 행동 -> 체력 스탯
        RestAction.SLEEP: {"stamina": 8},
    }
    
    def __init__(self, repository: RepositoryPort):
        self._repository = repository
    
    def execute_action(self, request: ActionRequest) -> ActionResult:
        """플레이어 행동 실행"""
        try:
            # 1. 플레이어 조회
            player = self._repository.get_player(request.player_id)
            if not player:
                return ActionResult(
                    success=False,
                    message="플레이어를 찾을 수 없습니다.",
                    time_consumed=0,
                    fatigue_change=0,
                    money_change=0,
                    experience_gains={},
                    updated_player=player
                )
            
            # 2. 행동 유효성 검사
            validation_result = self._validate_action(player, request)
            if not validation_result[0]:
                return ActionResult(
                    success=False,
                    message=validation_result[1],
                    time_consumed=0,
                    fatigue_change=0,
                    money_change=0,
                    experience_gains={},
                    updated_player=player
                )
            
            # 3. 행동 실행
            return self._execute_specific_action(player, request)
            
        except Exception as e:
            return ActionResult(
                success=False,
                message=f"행동 실행 중 오류가 발생했습니다: {str(e)}",
                time_consumed=0,
                fatigue_change=0,
                money_change=0,
                experience_gains={},
                updated_player=player if 'player' in locals() else None
            )
    
    def get_available_actions(self, player_id: UUID, remaining_time: int) -> List[Dict[str, any]]:
        """플레이어가 수행 가능한 행동 목록 반환"""
        player = self._repository.get_player(player_id)
        if not player:
            return []
        
        available_actions = []
        
        # 각 행동 카테고리별로 확인
        for action_type in ActionType:
            if action_type == ActionType.COOKING:
                available_actions.extend(self._get_cooking_actions(player, remaining_time))
            elif action_type == ActionType.ADVERTISING:
                available_actions.extend(self._get_advertising_actions(player, remaining_time))
            elif action_type == ActionType.OPERATION:
                available_actions.extend(self._get_operation_actions(player, remaining_time))
            elif action_type == ActionType.RESEARCH:
                available_actions.extend(self._get_research_actions(player, remaining_time))
            elif action_type == ActionType.PERSONAL:
                available_actions.extend(self._get_personal_actions(player, remaining_time))
            elif action_type == ActionType.REST:
                available_actions.extend(self._get_rest_actions(player, remaining_time))
        
        return available_actions
    
    def _validate_action(self, player: Player, request: ActionRequest) -> Tuple[bool, str]:
        """행동 유효성 검사"""
        # 1. 완전 탈진 상태 확인 (휴식은 예외)
        if player.is_completely_exhausted() and request.action_type != ActionType.REST:
            return False, "완전 탈진 상태에서는 행동할 수 없습니다. 휴식이 필요합니다."
        
        # 2. 행동별 세부 검증
        specific_action = self._parse_specific_action(request.action_type, request.specific_action)
        if not specific_action:
            return False, f"잘못된 행동입니다: {request.specific_action}"
        
        # 3. 시간 소모량 확인
        required_time = self.ACTION_TIME_COSTS.get(specific_action, request.time_hours)
        if required_time <= 0:
            return False, "행동에 필요한 시간이 잘못되었습니다."
        
        # 4. 자금 확인 (필요한 경우)
        required_money = self._get_action_cost(specific_action, player)
        if required_money > 0 and player.money.amount < required_money:
            return False, f"자금이 부족합니다. 필요: {Money(required_money).format_korean()}"
        
        return True, "유효한 행동입니다."
    
    def _execute_specific_action(self, player: Player, request: ActionRequest) -> ActionResult:
        """구체적인 행동 실행"""
        specific_action = self._parse_specific_action(request.action_type, request.specific_action)
        
        # 기본 정보 수집
        time_cost = self.ACTION_TIME_COSTS.get(specific_action, request.time_hours)
        fatigue_per_hour = self.ACTION_FATIGUE_COSTS.get(specific_action, 0)
        exp_gains = self.ACTION_EXPERIENCE_GAINS.get(specific_action, {})
        action_cost = self._get_action_cost(specific_action, player)
        
        # 효과 적용
        total_fatigue_change = fatigue_per_hour * time_cost
        total_exp_gains = {stat: exp * time_cost for stat, exp in exp_gains.items()}
        
        # 플레이어 상태 업데이트
        updated_player = player
        
        # 1. 피로도 적용
        if total_fatigue_change != 0:
            new_fatigue = max(0, min(200, player.fatigue.value + total_fatigue_change))
            updated_player = updated_player._replace(fatigue=Percentage(new_fatigue))
        
        # 2. 자금 차감
        if action_cost > 0:
            updated_player = updated_player.spend_money(Money(action_cost))
        
        # 3. 경험치 적용
        for stat_name, exp_amount in total_exp_gains.items():
            if exp_amount > 0:
                updated_player = updated_player.gain_stat_experience(stat_name, exp_amount)
        
        # 4. 특수 효과 처리
        special_result = self._apply_special_effects(updated_player, specific_action, request)
        updated_player = special_result[0]
        special_message = special_result[1]
        
        # 5. 저장
        self._repository.save_player(updated_player)
        
        # 결과 메시지 생성
        message = self._generate_action_message(specific_action, time_cost, total_fatigue_change, total_exp_gains)
        if special_message:
            message += f" {special_message}"
        
        return ActionResult(
            success=True,
            message=message,
            time_consumed=time_cost,
            fatigue_change=total_fatigue_change,
            money_change=-action_cost,
            experience_gains=total_exp_gains,
            updated_player=updated_player
        )
    
    def _parse_specific_action(self, action_type: ActionType, specific_action: str):
        """문자열을 구체적인 행동 Enum으로 변환"""
        try:
            if action_type == ActionType.COOKING:
                return CookingAction[specific_action]
            elif action_type == ActionType.ADVERTISING:
                return AdvertisingAction[specific_action]
            elif action_type == ActionType.OPERATION:
                return OperationAction[specific_action]
            elif action_type == ActionType.RESEARCH:
                return ResearchAction[specific_action]
            elif action_type == ActionType.PERSONAL:
                return PersonalAction[specific_action]
            elif action_type == ActionType.REST:
                return RestAction[specific_action]
        except KeyError:
            return None
        
        return None
    
    def _get_action_cost(self, specific_action, player: Player) -> int:
        """행동별 자금 소모량 계산"""
        # 기본적으로 대부분의 행동은 무료
        action_costs = {
            AdvertisingAction.FLYER: 50000,  # 전단지 5만원
            AdvertisingAction.ONLINE_AD: 100000,  # 온라인광고 10만원
            AdvertisingAction.DELIVERY_APP: 30000,  # 배달앱 3만원
            OperationAction.ORDER_INGREDIENTS: 200000,  # 재료주문 20만원
            OperationAction.HIRE_PARTTIME: 80000,  # 알바고용 8만원
            PersonalAction.VACATION: 150000,  # 휴가 15만원
        }
        
        return action_costs.get(specific_action, 0)
    
    def _apply_special_effects(self, player: Player, specific_action, request: ActionRequest) -> Tuple[Player, str]:
        """행동별 특수 효과 적용"""
        special_message = ""
        updated_player = player
        
        # 연구 행동의 경우 연구 진행도 증가
        if isinstance(specific_action, ResearchAction):
            if request.target_id:
                research = self._repository.get_research(request.target_id)
                if research and research.owner_id == player.id:
                    # 연구 진행도 계산 (README.md 공식)
                    progress_increase = self._calculate_research_progress(player, specific_action, research)
                    updated_research = research.add_progress(progress_increase)
                    self._repository.save_research(updated_research)
                    special_message = f"연구가 {progress_increase:.1f}% 진행되었습니다."
        
        # 광고 행동의 경우 매장 인지도 증가
        elif isinstance(specific_action, AdvertisingAction):
            if request.target_id:
                store = self._repository.get_store(request.target_id)
                if store and store.owner_id == player.id:
                    awareness_increase = self._calculate_awareness_increase(specific_action)
                    updated_store = store.add_awareness(awareness_increase)
                    self._repository.save_store(updated_store)
                    special_message = f"매장 인지도가 {awareness_increase}% 증가했습니다."
        
        return updated_player, special_message
    
    def _calculate_research_progress(self, player: Player, research_action: ResearchAction, research: Research) -> float:
        """연구 진행도 계산 (README.md 공식)"""
        # README.md: {1+[calldice/10]}*{관련 스테이터스}*(난이도 보정치)
        import random
        
        # 주사위 굴리기 (1~20)
        calldice = random.randint(1, 20)
        dice_factor = 1 + (calldice / 10)
        
        # 관련 스탯 확인
        related_stat = self._get_research_related_stat(research_action, player)
        
        # 난이도 보정치
        difficulty_modifier = 1.0 / research.difficulty
        
        # 최종 진행도
        progress = dice_factor * related_stat * difficulty_modifier
        
        return min(progress, 100 - research.progress)  # 100% 초과 방지
    
    def _get_research_related_stat(self, research_action: ResearchAction, player: Player) -> int:
        """연구 행동에 관련된 스탯값 반환"""
        effective_stats = player.get_effective_stats()
        
        if research_action == ResearchAction.RECIPE:
            return effective_stats.cooking.base_value
        elif research_action == ResearchAction.MANAGEMENT:
            return effective_stats.management.base_value
        elif research_action == ResearchAction.ADVERTISING_RESEARCH:
            return effective_stats.management.base_value
        elif research_action == ResearchAction.SERVICE:
            return effective_stats.service.base_value
        
        return 10  # 기본값
    
    def _calculate_awareness_increase(self, advertising_action: AdvertisingAction) -> float:
        """광고 행동별 인지도 증가량 계산"""
        awareness_gains = {
            AdvertisingAction.FLYER: 5.0,
            AdvertisingAction.ONLINE_AD: 8.0,
            AdvertisingAction.DELIVERY_APP: 12.0,
        }
        
        return awareness_gains.get(advertising_action, 3.0)
    
    def _generate_action_message(self, specific_action, time_cost: int, fatigue_change: float, exp_gains: Dict[str, int]) -> str:
        """행동 결과 메시지 생성"""
        action_names = {
            # 조리
            CookingAction.PREPARE_INGREDIENTS: "재료를 준비했습니다",
            CookingAction.COOK: "요리를 했습니다",
            CookingAction.INSPECT_INGREDIENTS: "재료를 점검했습니다",
            
            # 광고
            AdvertisingAction.FLYER: "전단지를 배포했습니다",
            AdvertisingAction.ONLINE_AD: "온라인 광고를 집행했습니다",
            AdvertisingAction.DELIVERY_APP: "배달앱에 등록했습니다",
            
            # 운영
            OperationAction.ORDER_INGREDIENTS: "재료를 주문했습니다",
            OperationAction.CLEAN: "매장을 청소했습니다",
            OperationAction.EQUIPMENT_CHECK: "장비를 점검했습니다",
            OperationAction.HIRE_PARTTIME: "아르바이트생을 고용했습니다",
            
            # 연구
            ResearchAction.RECIPE: "레시피를 연구했습니다",
            ResearchAction.MANAGEMENT: "경영을 연구했습니다",
            ResearchAction.ADVERTISING_RESEARCH: "광고를 연구했습니다",
            ResearchAction.SERVICE: "서비스를 연구했습니다",
            
            # 개인
            PersonalAction.VACATION: "휴가를 보냈습니다",
            PersonalAction.STUDY: "공부를 했습니다",
            PersonalAction.EXERCISE: "운동을 했습니다",
            
            # 휴식
            RestAction.SLEEP: "잠을 잤습니다",
        }
        
        base_message = action_names.get(specific_action, "행동을 수행했습니다")
        base_message += f" ({time_cost}시간 소모)"
        
        if fatigue_change > 0:
            base_message += f", 피로도 +{fatigue_change:.1f}"
        elif fatigue_change < 0:
            base_message += f", 피로도 {fatigue_change:.1f}"
        
        if exp_gains:
            exp_messages = [f"{stat} +{exp}" for stat, exp in exp_gains.items() if exp > 0]
            if exp_messages:
                base_message += f", 경험치: {', '.join(exp_messages)}"
        
        return base_message
    
    def _get_cooking_actions(self, player: Player, remaining_time: int) -> List[Dict[str, any]]:
        """조리 행동 목록 반환"""
        actions = []
        for action in CookingAction:
            time_cost = self.ACTION_TIME_COSTS.get(action, 1)
            if time_cost <= remaining_time:
                actions.append({
                    "action_type": ActionType.COOKING,
                    "specific_action": action.name,
                    "name": self._get_action_display_name(action),
                    "time_cost": time_cost,
                    "description": self._get_action_description(action)
                })
        return actions
    
    def _get_advertising_actions(self, player: Player, remaining_time: int) -> List[Dict[str, any]]:
        """광고 행동 목록 반환"""
        actions = []
        for action in AdvertisingAction:
            time_cost = self.ACTION_TIME_COSTS.get(action, 1)
            money_cost = self._get_action_cost(action, player)
            if time_cost <= remaining_time and player.money.amount >= money_cost:
                actions.append({
                    "action_type": ActionType.ADVERTISING,
                    "specific_action": action.name,
                    "name": self._get_action_display_name(action),
                    "time_cost": time_cost,
                    "money_cost": money_cost,
                    "description": self._get_action_description(action)
                })
        return actions
    
    def _get_operation_actions(self, player: Player, remaining_time: int) -> List[Dict[str, any]]:
        """운영 행동 목록 반환"""
        actions = []
        for action in OperationAction:
            time_cost = self.ACTION_TIME_COSTS.get(action, 1)
            money_cost = self._get_action_cost(action, player)
            if time_cost <= remaining_time and player.money.amount >= money_cost:
                actions.append({
                    "action_type": ActionType.OPERATION,
                    "specific_action": action.name,
                    "name": self._get_action_display_name(action),
                    "time_cost": time_cost,
                    "money_cost": money_cost,
                    "description": self._get_action_description(action)
                })
        return actions
    
    def _get_research_actions(self, player: Player, remaining_time: int) -> List[Dict[str, any]]:
        """연구 행동 목록 반환"""
        actions = []
        for action in ResearchAction:
            time_cost = self.ACTION_TIME_COSTS.get(action, 1)
            if time_cost <= remaining_time:
                actions.append({
                    "action_type": ActionType.RESEARCH,
                    "specific_action": action.name,
                    "name": self._get_action_display_name(action),
                    "time_cost": time_cost,
                    "description": self._get_action_description(action)
                })
        return actions
    
    def _get_personal_actions(self, player: Player, remaining_time: int) -> List[Dict[str, any]]:
        """개인 행동 목록 반환"""
        actions = []
        for action in PersonalAction:
            time_cost = self.ACTION_TIME_COSTS.get(action, 1)
            money_cost = self._get_action_cost(action, player)
            if time_cost <= remaining_time and player.money.amount >= money_cost:
                actions.append({
                    "action_type": ActionType.PERSONAL,
                    "specific_action": action.name,
                    "name": self._get_action_display_name(action),
                    "time_cost": time_cost,
                    "money_cost": money_cost,
                    "description": self._get_action_description(action)
                })
        return actions
    
    def _get_rest_actions(self, player: Player, remaining_time: int) -> List[Dict[str, any]]:
        """휴식 행동 목록 반환"""
        actions = []
        for action in RestAction:
            # 휴식은 남은 시간만큼 할 수 있음
            max_time = min(remaining_time, 12)  # 최대 12시간
            if max_time > 0:
                actions.append({
                    "action_type": ActionType.REST,
                    "specific_action": action.name,
                    "name": self._get_action_display_name(action),
                    "time_cost": 1,  # 1시간 단위
                    "max_time": max_time,
                    "description": self._get_action_description(action)
                })
        return actions
    
    def _get_action_display_name(self, action) -> str:
        """행동 표시 이름 반환"""
        display_names = {
            # 조리
            CookingAction.PREPARE_INGREDIENTS: "재료 준비",
            CookingAction.COOK: "조리",
            CookingAction.INSPECT_INGREDIENTS: "재료 점검",
            
            # 광고
            AdvertisingAction.FLYER: "전단지 배포",
            AdvertisingAction.ONLINE_AD: "온라인 광고",
            AdvertisingAction.DELIVERY_APP: "배달앱 등록",
            
            # 운영
            OperationAction.ORDER_INGREDIENTS: "재료 주문",
            OperationAction.CLEAN: "매장 청소",
            OperationAction.EQUIPMENT_CHECK: "장비 점검",
            OperationAction.HIRE_PARTTIME: "아르바이트생 고용",
            
            # 연구
            ResearchAction.RECIPE: "레시피 연구",
            ResearchAction.MANAGEMENT: "경영 연구",
            ResearchAction.ADVERTISING_RESEARCH: "광고 연구",
            ResearchAction.SERVICE: "서비스 연구",
            
            # 개인
            PersonalAction.VACATION: "휴가",
            PersonalAction.STUDY: "학습",
            PersonalAction.EXERCISE: "운동",
            
            # 휴식
            RestAction.SLEEP: "수면",
        }
        
        return display_names.get(action, str(action))
    
    def _get_action_description(self, action) -> str:
        """행동 설명 반환"""
        descriptions = {
            # 조리
            CookingAction.PREPARE_INGREDIENTS: "요리에 필요한 재료를 준비합니다. 요리 스킬이 향상됩니다.",
            CookingAction.COOK: "실제로 요리를 합니다. 요리 스킬이 크게 향상됩니다.",
            CookingAction.INSPECT_INGREDIENTS: "재료의 상태를 확인합니다. 요리와 경영 스킬이 향상됩니다.",
            
            # 광고
            AdvertisingAction.FLYER: "전단지를 제작하고 배포합니다. 매장 인지도가 증가합니다.",
            AdvertisingAction.ONLINE_AD: "온라인 광고를 집행합니다. 매장 인지도가 크게 증가합니다.",
            AdvertisingAction.DELIVERY_APP: "배달앱에 매장을 등록합니다. 매장 인지도와 배달 주문이 증가합니다.",
            
            # 운영
            OperationAction.ORDER_INGREDIENTS: "필요한 재료를 주문합니다. 경영 스킬이 향상됩니다.",
            OperationAction.CLEAN: "매장을 깨끗하게 청소합니다. 서비스 스킬이 향상됩니다.",
            OperationAction.EQUIPMENT_CHECK: "장비 상태를 점검하고 정비합니다. 기술과 경영 스킬이 향상됩니다.",
            OperationAction.HIRE_PARTTIME: "아르바이트생을 고용합니다. 경영과 서비스 스킬이 향상됩니다.",
            
            # 연구
            ResearchAction.RECIPE: "새로운 레시피를 연구합니다. 요리 스킬이 크게 향상됩니다.",
            ResearchAction.MANAGEMENT: "경영 기법을 연구합니다. 경영 스킬이 크게 향상됩니다.",
            ResearchAction.ADVERTISING_RESEARCH: "광고 전략을 연구합니다. 경영과 기술 스킬이 향상됩니다.",
            ResearchAction.SERVICE: "서비스 방법을 연구합니다. 서비스 스킬이 크게 향상됩니다.",
            
            # 개인
            PersonalAction.VACATION: "휴가를 보내며 휴식합니다. 피로도가 크게 감소하고 체력이 향상됩니다.",
            PersonalAction.STUDY: "새로운 지식을 학습합니다. 기술과 경영 스킬이 향상됩니다.",
            PersonalAction.EXERCISE: "운동을 하여 체력을 기릅니다. 체력이 크게 향상됩니다.",
            
            # 휴식
            RestAction.SLEEP: "잠을 자며 피로를 회복합니다. 피로도가 감소하고 체력이 향상됩니다.",
        }
        
        return descriptions.get(action, "행동을 수행합니다.")