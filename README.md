# Chickenmaster2 🍗

한국 치킨집 경영 시뮬레이션 게임 - **헥사고날 아키텍처** 기반 Python 프로젝트

## 프로젝트 개요

TRPG 스타일의 D100 주사위 시스템과 AI 경쟁자가 있는 치킨집 경영 시뮬레이션 게임입니다.
불변 도메인 모델과 포트-어댑터 패턴을 적용한 **헥사고날 아키텍처**로 구현되었습니다.

## 주요 특징

- 🎲 **D100 주사위 시스템**: 확률 기반 게임플레이
- 🤖 **AI 경쟁자**: 지연 행동 시스템과 독립적 전략
- 📊 **복잡한 경영 시뮬레이션**: 가격/품질/인지도 점수 시스템
- 🏗️ **헥사고날 아키텍처**: 도메인 중심 설계, 테스트 가능한 구조
- 🔒 **불변 도메인 모델**: `@dataclass(frozen=True)` 기반 안정성
- 🧪 **AI 에이전트 통합**: GitHub Copilot 커스텀 에이전트와 스킬 활용


## Quick Start

```bash
# 의존성 설치
uv sync

# 게임 실행 (개발 중)
uv run python src/main.py

# 테스트 실행
uv run pytest tests/

# 도메인 모델 테스트
uv run python tests/test_domain_models.py

# GameLoopService 테스트
uv run python test_game_loop_service.py
```

## 게임 규칙

상세한 게임 규칙은 **[README_GAME_RULES.md](README_GAME_RULES.md)** 참조

### 핵심 메커니즘
- **턴 시스템**: 1턴 = 1일, 12시간 시간 자원
- **6가지 행동**: 조리, 광고, 운영, 연구, 개인, 휴식
- **5가지 스탯**: 요리, 경영, 서비스, 기술, 체력
- **피로도/행복도**: 스탯과 행동에 영향
- **AI 경쟁자**: 3~10턴 지연 반응, 파산 시스템
- **고객 AI**: 10% 개별 AI + 90% 수치 고객
- **점유율 시스템**: 가격/품질/인지도 기반


## 프로젝트 구조

```text
.
├── .github/
│   ├── agents/              # GitHub Copilot 커스텀 에이전트
│   ├── skills/              # 에이전트 스킬 (워크플로우)
│   └── copilot-instructions.md
├── AGENTS.md                # 에이전트 문서
├── README_GAME_RULES.md     # 게임 규칙 상세 (필독!)
├── TODO.md                  # 개발 계획
├── configs/                 # 설정 파일
├── data/                    # 게임 데이터 (이벤트 CSV 등)
├── documents/               # 프로젝트 문서
├── results/                 # 실험 결과 (JSON)
├── src/
│   ├── core/
│   │   ├── domain/          # 도메인 엔티티 (11개 모델)
│   │   └── ports/           # 포트 인터페이스 (미구현)
│   ├── application/         # 응용 서비스
│   ├── adapters/            # 어댑터 (I/O)
│   ├── engine/              # 게임 엔진 (주사위, AI 등)
│   ├── constants.py         # 게임 상수
│   └── main.py              # 진입점
├── tests/                   # 테스트 파일
└── tools/                   # AI 에이전트 도구
```

### 아키텍처 계층

**헥사고날 아키텍처 (Ports & Adapters)**
```
외부 세계
    ↓
Adapters (어댑터)
    ↓
Ports (인터페이스)
    ↓
Application (응용 서비스)
    ↓
Domain (도메인 모델) ← 핵심!
```

- **Domain**: 불변 엔티티, 비즈니스 로직
- **Ports**: 인터페이스 정의 (의존성 역전)
- **Application**: 유스케이스 구현
- **Adapters**: 외부 시스템 통합 (DB, UI 등)


## 개발 현황

### ✅ 완료된 부분
1. **도메인 모델** (11개 엔티티) - 100% 완성
   - Player, Competitor, Store, Product, Recipe
   - Research, Inventory, Customer, Event, Turn
2. **상수 & Enum** - 게임 규칙 정의 완료
3. **테스트** - 562줄 도메인 모델 단위 테스트
4. **이벤트 시스템** - CSV 로더 & 13개 이벤트
5. **응용 서비스** - GameLoop, Action, AI 서비스 구현

### 🚧 진행 중
- **포트 계층**: EventLoaderPort만 완성, 7개 미구현
- **엔진 계층**: DiceSystem, AI 엔진 미구현
- **저장소**: JSON 저장소 미구현
- **UI**: CLI/GUI 미구현

### 📋 다음 단계
1. `src/core/ports/repository_port.py` 작성
2. `src/engine/dice_system.py` 구현
3. `src/adapters/repository/json_repository.py` 구현
4. 최소 CLI 구현

**진척률**: 약 30-35%

자세한 내용은 [TODO.md](TODO.md) 참조

## 도메인 모델

### 핵심 엔티티 (모두 `@dataclass(frozen=True)`)

| 엔티티 | 파일 | 설명 |
|--------|------|------|
| Player | `player.py` | 플레이어 (5가지 스탯, 피로도, 자금) |
| Competitor | `competitor.py` | 경쟁자 AI (지연 행동, 파산) |
| Store | `store.py` | 매장 (임대료, 제품, 알바) |
| Product | `product.py` | 제품 (가격, 품질, 인지도) |
| Recipe | `recipe.py` | 레시피 (연구도) |
| Research | `research.py` | 연구 (4가지 분야) |
| Inventory | `inventory.py` | 재고 (FIFO Queue) |
| Customer | `customer.py` | 고객 AI (욕구, 구매 판정) |
| Event | `event.py` | 이벤트 (5가지 분류) |
| Turn | `turn.py` | 턴 (6개 페이즈) |

### 값 객체 (Value Objects)

- `Money`: 자금
- `Percentage`: 피로도, 행복도, 점유율
- `StatValue`: 스탯 (값 + 경험치)
- `Progress`: 연구 진행도
- `Hours`: 시간 자원


## AI 에이전트 (GitHub Copilot)

프로젝트에는 GitHub Copilot 커스텀 에이전트가 포함되어 있습니다:

| 에이전트 | 용도 |
| :--- | :--- |
| `@research-{model}` | 연구 (Gemini=구현, GPT=이론, Claude=안전성) |
| `@fixer` | 자동 문제 해결 (버그, 테스트, 품질) |
| `@planner-{model}` | 계획 수립 (Gemini=실현가능성, GPT=구조, Claude=리스크) |
| `@orchestrator` | 자율 작업 관리자 |
| `@code-generator` | 프로덕션 코드 생성 |
| `@validator` | 아이디어 검증 |

**사용 예시**:
```
@fixer 피로도 시스템 버그 수정
@code-generator DiceSystem 구현
@validator 점유율 계산 로직 검증
```

자세한 내용은 [AGENTS.md](AGENTS.md) 참조

## Running the Game

### 개발 환경

```bash
# 의존성 설치
uv sync

# 메인 게임 실행 (미완성)
uv run python src/main.py

# 도메인 모델 테스트
uv run python tests/test_domain_models.py

# 게임 루프 테스트
uv run python test_game_loop_service.py
```

### 테스트

```bash
# 전체 테스트
uv run pytest tests/

# 특정 테스트
uv run pytest tests/test_domain_models.py -v

# 커버리지
uv run pytest --cov=src tests/
```

## 기술 스택

- **언어**: Python 3.11+
- **패키지 관리**: uv
- **아키텍처**: 헥사고날 (Ports & Adapters)
- **테스트**: pytest
- **타입 체킹**: mypy (예정)
- **AI**: GitHub Copilot 커스텀 에이전트


## 문서

- **[README_GAME_RULES.md](README_GAME_RULES.md)** - 게임 규칙 상세 (필독!)
- **[AGENTS.md](AGENTS.md)** - AI 에이전트 문서
- **[TODO.md](TODO.md)** - 개발 계획 및 진행 상황
- **[documents/PROJECT.md](documents/PROJECT.md)** - 프로젝트 개요
- **[TEMPLATE_GUIDE.md](TEMPLATE_GUIDE.md)** - 템플릿 가이드

## 기여 가이드

1. **코드 스타일**
   - 타입 힌팅 필수
   - Docstring 작성 (한글)
   - 불변 객체 원칙 준수

2. **커밋 메시지**
   ```
   <type>: <subject>
   
   Types: feat, fix, docs, refactor, test, chore
   ```

3. **브랜치 전략**
   - `master`: 안정 버전
   - `feature/<name>`: 새 기능
   - `experiment/<name>`: 실험적 기능

## 라이선스

MIT License

## 연락처

이슈나 질문은 GitHub Issues에 등록해주세요.

---

**🎮 즐거운 치킨집 경영 되세요! 🍗**
