# 기여 가이드라인

프로젝트에 기여해주셔서 감사합니다!

## 목차

- [개발 환경 설정](#개발-환경-설정)
- [프로젝트 구조](#프로젝트-구조)
- [코딩 규칙](#코딩-규칙)
- [테스트 작성](#테스트-작성)
- [Pull Request 프로세스](#pull-request-프로세스)
- [문서화](#문서화)

## 개발 환경 설정

### 1. 저장소 클론

```bash
git clone https://github.com/<owner>/<project>.git
cd <project>
```

### 2. 가상환경 설정

이 프로젝트는 `uv`를 사용합니다:

```bash
# uv 설치 (없는 경우)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 의존성 설치
uv sync
```

### 3. VS Code 설정

권장 확장 프로그램:

- Python
- Pylance
- GitHub Copilot
- Markdown All in One

## 프로젝트 구조

```
project/
├── src/                    # 핵심 구현
│   ├── experiments/        # 실험 코드
│   ├── data/              # 데이터 로더
│   └── utils/             # 유틸리티
├── tests/                  # 테스트
├── scripts/                # 스크립트
│   └── slurm/             # SLURM 작업
└── documents/              # 문서
```

## 코딩 규칙

### Python 스타일 가이드

1. **타입 힌트 필수**

   ```python
   def process_data(
       data: torch.Tensor,
       config: dict[str, Any]
   ) -> torch.Tensor:
       """데이터 처리."""
       pass
   ```

2. **Docstring 규칙** (Google Style)

   ```python
   def forward(self, x: torch.Tensor) -> torch.Tensor:
       """Forward pass.

       Args:
           x: 입력 텐서 (batch, dim)

       Returns:
           출력 텐서 (batch, dim)

       Raises:
           ValueError: shape 불일치 시
       """
   ```

3. **명명 규칙**
   - 변수/함수: `snake_case`
   - 클래스: `PascalCase`
   - 상수: `UPPER_CASE`

4. **라인 길이**: 최대 88자 (Black formatter 기준)

### Import 순서

```python
# 1. 표준 라이브러리
import sys
from pathlib import Path

# 2. 서드파티
import torch
from transformers import AutoModel

# 3. 로컬
from src.utils import helper
```

## 테스트 작성

### 테스트 구조

```python
def test_feature():
    """기능 테스트."""
    # Setup
    data = create_test_data()

    # Test
    result = process(data)

    # Verify
    assert result.shape == expected_shape
```

### 테스트 실행

```bash
# 단일 테스트
uv run pytest tests/test_module.py

# 전체 테스트
uv run pytest tests/
```

## Pull Request 프로세스

### 1. 브랜치 생성

```bash
git checkout -b feature/your-feature-name
# 또는
git checkout -b fix/bug-description
```

### 2. 커밋 메시지 규칙

```
<type>: <subject>

<body>
```

**Type**:

- `feat`: 새로운 기능
- `fix`: 버그 수정
- `docs`: 문서 수정
- `test`: 테스트 추가/수정
- `refactor`: 리팩토링
- `chore`: 기타 작업

### 3. PR 체크리스트

- [ ] 코드가 모든 테스트를 통과함
- [ ] 새로운 기능에 테스트 추가됨
- [ ] Docstring이 작성됨
- [ ] 타입 힌트가 추가됨
- [ ] 문서가 업데이트됨

### 4. PR 제출

```bash
git push origin feature/your-feature-name
```

## 문서화

### 실험 결과 문서화

새로운 실험 결과는 `documents/logs/`에 추가:

```markdown
# <실험 이름>

**날짜**: YYYY-MM-DD
**목표**: <목표>

## 설정
## 결과
## 결론
## 생성된 파일
```

## 질문하기

Issues에 다음 정보와 함께 질문을 남겨주세요:

1. **문제 설명**: 무엇을 시도했는지
2. **예상 결과**: 무엇을 기대했는지
3. **실제 결과**: 무엇이 발생했는지
4. **환경 정보**: Python 버전, GPU 등

---

**감사합니다!** 🎉
