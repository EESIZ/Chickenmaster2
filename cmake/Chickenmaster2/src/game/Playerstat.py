from dataclasses import dataclass

@dataclass(frozen=True)
class PlayerStats:
    """캐릭터의 스탯을 나타내는 클래스. 모든 스탯은 불변입니다."""
    cooking: int
    management: int
    service: int
    stamina: int
    tech: int
