"""
연구 도메인 모델

게임 내 연구 시스템을 나타내는 불변 엔티티입니다.
4가지 연구 분야에서 진행도를 관리하고 보너스를 제공합니다.
"""

from dataclasses import dataclass
from uuid import UUID

from .value_objects import Progress
from common.enums.research_type import ResearchType


@dataclass(frozen=True)
class Research:
    """연구 엔티티"""
    
    id: UUID
    research_type: ResearchType
    name: str
    description: str
    
    # 연구 진행도
    progress: Progress
    
    # 연구 속성
    difficulty: int  # 연구 난이도 (높을수록 진행 속도 감소)
    required_stat: str  # 필요 스탯 ("tech" 등)
    min_stat_required: int  # 최소 필요 스탯 수치
    
    def __post_init__(self):
        """생성 후 유효성 검사"""
        if not self.name.strip():
            raise ValueError("연구 이름은 비어있을 수 없습니다")
        
        if not self.description.strip():
            raise ValueError("연구 설명은 비어있을 수 없습니다")
        
        if self.difficulty <= 0:
            raise ValueError("연구 난이도는 0보다 커야 합니다")
        
        if self.min_stat_required < 0:
            raise ValueError("최소 필요 스탯은 음수일 수 없습니다")
    
    def advance_progress(self, progress_amount: int) -> 'Research':
        """연구 진행 후 새로운 Research 반환"""
        new_progress = self.progress + progress_amount
        return self._replace(progress=new_progress)
    
    def is_complete(self) -> bool:
        """연구가 완료되었는지 확인"""
        return self.progress.is_complete()
    
    def can_start_research(self, stat_value: int) -> bool:
        """연구 시작 가능한지 확인 (스탯 요구사항)"""
        return stat_value >= self.min_stat_required
    
    def calculate_progress_amount(self, stat_value: int) -> int:
        """스탯에 따른 연구 진행량 계산"""
        if not self.can_start_research(stat_value):
            return 0
        
        # 기본 진행량 = (스탯값 - 최소요구값) / 난이도
        base_progress = max(1, (stat_value - self.min_stat_required) // self.difficulty)
        return base_progress
    
    def get_difficulty_modifier(self) -> float:
        """난이도 보정치 반환"""
        return 1.0 / self.difficulty
    
    def get_completion_percentage(self) -> float:
        """완료 퍼센트 반환"""
        return self.progress.get_percentage()
    
    def get_display_info(self) -> str:
        """연구 정보 문자열 반환"""
        status = "완료" if self.is_complete() else f"{self.progress.value}%"
        return f"{self.name} - {status} (난이도: {self.difficulty}, 필요 {self.required_stat}: {self.min_stat_required})"
    
    def _replace(self, **changes) -> 'Research':
        """dataclass replace 메서드 래퍼"""
        from dataclasses import replace
        return replace(self, **changes)


@dataclass(frozen=True)
class ResearchTemplate:
    """연구 템플릿 (게임 초기화용)"""
    
    research_type: ResearchType
    name: str
    description: str
    difficulty: int
    required_stat: str
    min_stat_required: int
    
    def create_research(self, research_id: UUID) -> Research:
        """실제 Research 인스턴스 생성"""
        return Research(
            id=research_id,
            research_type=self.research_type,
            name=self.name,
            description=self.description,
            progress=Progress(0),  # 0%로 시작
            difficulty=self.difficulty,
            required_stat=self.required_stat,
            min_stat_required=self.min_stat_required,
        )


@dataclass(frozen=True)
class DefaultResearchTemplates:
    """기본 연구 템플릿 정보"""
    
    @staticmethod
    def get_all_templates() -> list[ResearchTemplate]:
        """모든 기본 연구 템플릿 반환"""
        return [
            # 요리 연구
            ResearchTemplate(
                research_type=ResearchType.COOKING,
                name="양념 치킨 레시피",
                description="매콤달콤한 양념 치킨 레시피를 개발합니다.",
                difficulty=2,
                required_stat="cooking",
                min_stat_required=20,
            ),
            ResearchTemplate(
                research_type=ResearchType.COOKING,
                name="크리스피 치킨 레시피",
                description="바삭한 크리스피 치킨 레시피를 개발합니다.",
                difficulty=3,
                required_stat="cooking",
                min_stat_required=30,
            ),
            
            # 마케팅 연구
            ResearchTemplate(
                research_type=ResearchType.MARKETING,
                name="SNS 마케팅",
                description="소셜미디어를 활용한 마케팅 기법을 연구합니다.",
                difficulty=2,
                required_stat="management",
                min_stat_required=25,
            ),
            
            # 경영 연구
            ResearchTemplate(
                research_type=ResearchType.MANAGEMENT,
                name="효율적인 매장 운영",
                description="매장 운영의 효율성을 높이는 방법을 연구합니다.",
                difficulty=2,
                required_stat="management",
                min_stat_required=20,
            ),
            
            # 기술 연구
            ResearchTemplate(
                research_type=ResearchType.TECHNOLOGY,
                name="자동 조리 시스템",
                description="조리 과정을 자동화하는 시스템을 개발합니다.",
                difficulty=4,
                required_stat="tech",
                min_stat_required=40,
            ),
        ] 