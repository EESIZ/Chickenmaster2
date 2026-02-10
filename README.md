# Chickenmaster2

치킨집 경영 시뮬레이션 웹 게임 — Python FastAPI + Vanilla JS SPA

## Quick Start

```bash
# 의존성 설치
uv sync

# 서버 실행
PYTHONPATH="src;." python -X utf8 web/main.py

# 브라우저에서 접속
# http://localhost:8000/
```

## 게임 개요

4구간 하루 시스템으로 치킨집을 경영합니다.

| 구간 | 기본 시간 | 내용 |
|------|-----------|------|
| PREP (준비) | 3h (07~10시) | 재료 준비, 점검, 청소, 장비 점검 |
| BUSINESS (영업) | 11h (10~21시) | 타임랩스 영업, 의사결정 이벤트 |
| NIGHT (야간) | 3h (21~24시) | 연구, 학습, 운동, 광고, 재료 주문 |
| SLEEP (수면) | 7h (24~07시) | 자동 피로 회복 → 다음 날 |

상세 규칙: [README_GAME_RULES.md](README_GAME_RULES.md)

## 기술 스택

- **Backend**: Python 3.11+, FastAPI, SQLite (WAL mode)
- **Frontend**: Vanilla JS SPA (web/static/v2/)
- **Architecture**: Hexagonal (Ports & Adapters) + DB-based GameService

## 프로젝트 구조

```
web/
├── app.py                  # FastAPI 앱 팩토리
├── main.py                 # 서버 엔트리포인트
├── config.py               # 설정 (DB 경로, CORS 등)
├── api/
│   ├── router.py           # API 라우터 통합
│   └── game_router_v2.py   # v2 게임 API (/api/v2/games/...)
├── services/
│   ├── game_service.py     # 게임 오케스트레이터
│   ├── balance.py          # 밸런스 수치 중앙 관리
│   ├── serializers.py      # 도메인→JSON 직렬화
│   └── engines/            # 순수 계산 로직
│       ├── sales_engine.py
│       └── decision_engine.py
└── static/v2/              # 프론트엔드 SPA
    ├── index.html
    ├── app.js
    ├── state.js
    └── business.js

src/                        # 도메인 + 인프라
├── core/domain/            # 불변 도메인 모델 (@dataclass frozen)
├── core/ports/             # 포트 인터페이스 (ABC)
├── application/            # 행동/AI/이벤트/판매/정산 서비스
├── adapters/repository/    # SQLite 저장소
└── common/enums/           # ActionType, EventType 등

data/
├── chickenmaster.db        # 게임 DB (자동 생성)
└── events.csv              # 이벤트 데이터
```

## API (v2)

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/v2/games` | 새 게임 생성 |
| GET | `/api/v2/games/{id}` | 게임 상태 조회 |
| DELETE | `/api/v2/games/{id}` | 게임 삭제 |
| PUT | `/api/v2/games/{id}/time-config` | 시간 설정 변경 |
| GET | `/api/v2/games/{id}/actions/available` | 사용 가능한 행동 목록 |
| POST | `/api/v2/games/{id}/actions/queue` | 행동 큐잉 |
| DELETE | `/api/v2/games/{id}/actions/queue/{slot}` | 큐에서 제거 |
| POST | `/api/v2/games/{id}/segments/prep/confirm` | 준비 완료 → 영업 전환 |
| POST | `/api/v2/games/{id}/business/start` | 영업 시작 (의사결정 생성) |
| POST | `/api/v2/games/{id}/business/decisions/{did}` | A/B 선택 제출 |
| POST | `/api/v2/games/{id}/business/complete` | 영업 완료 → 야간 전환 |
| POST | `/api/v2/games/{id}/segments/night/confirm` | 야간 완료 → 수면 전환 |
| POST | `/api/v2/games/{id}/sleep/execute` | 수면 실행 → 다음 날 |

## 개발

```bash
# 테스트
PYTHONPATH="src;." pytest tests/

# 서버 (개발 모드 — auto-reload)
PYTHONPATH="src;." uvicorn web.app:create_app --factory --reload
```

## 향후 계획

[TODO.md](TODO.md) 참조

## 라이선스

MIT License
