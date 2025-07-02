"""
레시피 도메인 모델

제품의 기반이 되는 레시피를 나타내는 불변 엔티티입니다.
연구를 통해 개발되고 신제품 출시를 통해 제품으로 전환됩니다.
"""

from dataclasses import dataclass
from uuid import UUID

from .value_objects import Progress
from .product import ProductCategory


@dataclass(frozen=True)
class Recipe:
    """레시피 엔티티"""
    
    id: UUID
    name: str
    category: ProductCategory
    
    # 레시피 속성
    base_quality: int  # 기본 품질값
    research_level: Progress  # 연구도 (0~100)
    difficulty: int  # 연구 난이도 (높을수록 연구 진행 속도 감소)
    
    # 획득 방법 메타데이터
    acquired_from_event: bool = False  # 이벤트로 획득했는지
    
    def __post_init__(self):
        """생성 후 유효성 검사"""
        if not self.name.strip():
            raise ValueError("레시피 이름은 비어있을 수 없습니다")
        
        if self.base_quality < 0:
            raise ValueError("기본 품질은 음수일 수 없습니다")
        
        if self.difficulty <= 0:
            raise ValueError("난이도는 0보다 커야 합니다")
    
    def advance_research(self, progress_amount: int) -> 'Recipe':
        """연구 진행 후 새로운 Recipe 반환"""
        new_research_level = self.research_level + progress_amount
        return self._replace(research_level=new_research_level)
    
    def is_research_complete(self) -> bool:
        """연구가 완료되었는지 확인"""
        return self.research_level.is_complete()
    
    def can_launch_as_product(self) -> bool:
        """신제품 출시 가능한지 확인 (연구 완료 필요)"""
        return self.is_research_complete()
    
    def calculate_final_quality(self, cooking_stat: int, ingredient_quality: int) -> int:
        """최종 품질 계산 (기본 품질 + 요리 스탯 보너스 + 재료 품질 보너스)"""
        # 요리 스탯 보너스: 스탯 10당 품질 1 증가
        cooking_bonus = cooking_stat // 10
        
        # 연구도 보너스: 연구도 20%당 품질 1 증가
        research_bonus = int(self.research_level.value) // 20
        
        # 재료 품질 보너스: 재료 품질 그대로 반영
        ingredient_bonus = ingredient_quality
        
        # 최종 품질 = 기본 품질 + 모든 보너스의 합
        final_quality = self.base_quality + cooking_bonus + research_bonus + ingredient_bonus
        return max(0, final_quality)
    
    def get_research_difficulty_modifier(self) -> float:
        """연구 난이도 보정치 반환 (높을수록 진행 속도 감소)"""
        # 난이도가 높을수록 진행 속도가 느려짐
        return 1.0 / self.difficulty
    
    def get_display_info(self) -> str:
        """레시피 정보 문자열 반환"""
        status = "완료" if self.is_research_complete() else f"{self.research_level.value}%"
        source = " (이벤트)" if self.acquired_from_event else ""
        
        return f"{self.name} - 연구: {status}, 난이도: {self.difficulty}{source}"
    
    def _replace(self, **changes) -> 'Recipe':
        """dataclass replace 메서드 래퍼"""
        from dataclasses import replace
        return replace(self, **changes)


@dataclass(frozen=True)
class DefaultRecipes:
    """기본 레시피 정보 (게임 시작 시 제공)"""
    
    @staticmethod
    def create_fried_chicken_recipe() -> Recipe:
        """기본 후라이드 치킨 레시피 생성"""
        from uuid import uuid4
        
        return Recipe(
            id=uuid4(),
            name="후라이드 치킨",
            category=ProductCategory.FRIED_CHICKEN,
            base_quality=30,
            research_level=Progress(100),  # 기본 레시피는 완료 상태
            difficulty=1,  # 가장 낮은 난이도
        ) 