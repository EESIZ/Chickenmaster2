# Foundation Model 특성 및 역할 정의 (Project Engram)

**작성일**: 2026-01-16  
**문서 유형**: Technical Reference  
**관련 Agent**: Idea Generator, Planner, Orchestrator

---

## 1. 개요
본 프로젝트에서는 세 가지 Foundation Model (Gemini 3 Pro, GPT-5.2, Claude Opus 4.5)의 고유한 강점을 활용하여 에이전트의 역할을 특화하였습니다. 단일 모델에 의존하는 대신, 각 모델의 "성격(Persona)"에 맞는 전문 분야를 할당함으로써 **Multi-Model Synthesis**의 품질을 극대화합니다.

---

## 2. 모델별 특성 및 할당 역할

### 🟢 Gemini 3 Pro (Preview)
*   **핵심 역량 (Core Strength)**: **Feasibility & Resources (실현 가능성 및 자원)**
*   **특성**:
    *   숫자와 데이터에 강함 (Quantitative Analysis)
    *   하드웨어 자원(GPU, 메모리) 산정 및 비용 추정에 정밀함
    *   구체적인 구현 코드(PyTorch 등) 생성에 능숙함
    *   "실제로 돌아가는가?"에 초점을 맞춤
*   **담당 Agent**:
    *   `planner-gemini`: 자원 예산, 하드웨어 스펙, 타임라인 산정
    *   `idea-generator-gemini`: 기술적 구현 가능성, 비용 효율성 중심의 아이디어
    *   `research-gemini`: 구현 세부 사항, API 명세, 라이브러리 호환성 분석

### 🔵 GPT-5.2
*   **핵심 역량 (Core Strength)**: **Structure & Strategy (구조 및 전략)**
*   **특성**:
    *   구조적 사고(Structured Thinking)와 시스템 설계를 잘함
    *   비즈니스 모델, 로드맵, 단계별 계획 수립에 강점
    *   이론적 배경 및 학술적 개념 정리 (Abstract/Theory)
    *   "전체 시스템이 논리적인가?"에 초점을 맞춤
*   **담당 Agent**:
    *   `planner-gpt`: 시스템 아키텍처(Mermaid), 단계별 실행 계획(Phasing)
    *   `idea-generator-gpt`: 비즈니스 모델, 플랫폼 전략, 확장성(Scalability) 중심의 아이디어
    *   `research-gpt`: 이론적 배경 조사, 개념 정의, 선행 연구 분석

### 🟠 Claude Opus 4.5
*   **핵심 역량 (Core Strength)**: **Safety, UX & Risk (안전, 사용자 경험 및 리스크)**
*   **특성**:
    *   확산적 사고(Divergent Thinking)와 창의적 발상
    *   윤리적 문제, 안전성(Safety), 잠재적 위험(Risk) 분석에 탁월
    *   사용자 경험(UX) 및 인간 중심적(Human-centric) 관점
    *   "안전하고 사용자에게 유익한가?"에 초점을 맞춤
*   **담당 Agent**:
    *   `planner-claude`: 리스크 매트릭스, QA/테스트 계획, 엣지 케이스 분석
    *   `idea-generator-claude`: 차별화된 UX, 창의적(Blue Ocean) 아이디어, 윤리적 검토
    *   `research-claude`: 시스템 복잡도 분석(Big-O), 엔지니어링 제약 조건, 보안/Safety 분석

---

## 3. Orchestration 합성 프로토콜 (Synthesis Protocol)

Orchestrator는 위 모델들의 출력을 다음 원칙에 따라 합성합니다.

### A. Master Plan Synthesis (계획 수립 시)
1.  **자원 및 일정(Timeline & Resources)** → **Gemini**의 계산 결과를 신뢰 (Trust Gemini)
2.  **구조 및 단계(Architecture & Steps)** → **GPT**의 설계안을 신뢰 (Trust GPT)
3.  **안전 및 품질(Safety & QA)** → **Claude**의 검증 기준을 신뢰 (Trust Claude)

### B. Ideation Synthesis (아이디어 발상 시)
1.  **기술적 실현 가능성(Tech Feasibility)** → **Gemini**의 점수 반영
2.  **비즈니스/전략적 가치(Business Value)** → **GPT**의 모델 반영
3.  **참신함/사용자 가치(Novelty & UX)** → **Claude**의 아이디어 반영

### C. Research Synthesis (심층 조사 시)
1.  **코드 구현(Implementation)** → **Gemini**
2.  **이론적 기반(Theory)** → **GPT**
3.  **시스템 제약(Constraints)** → **Claude**

---

## 4. 결론 및 활용 가이드
이러한 특성 분류를 통해 각 작업의 성격에 따라 가장 적합한 모델(Agent)을 호출하거나, 복합적인 문제 해결 시 세 모델의 결과를 **Ensemble**하여 상호 보완적인 최적의 결과를 도출할 수 있습니다.
