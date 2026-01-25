# [프로젝트 이름] 문서

## 개요

**[프로젝트 이름]**은 [프로젝트 목표 및 설명].

---

## 핵심 가설/목표

> [핵심 가설 또는 연구 목표 기술]

---

## 프로젝트 구조

```text
project/
├── src/
│   ├── experiments/          # 실험 코드
│   │   ├── <experiment_type>/  # 실험 유형별 폴더
│   │   └── _legacy/            # 폐기된 실험
│   ├── data/                 # 데이터 로더
│   └── utils/                # 유틸리티
├── scripts/
│   └── slurm/                # SLURM 작업 스크립트
├── tests/                    # 테스트 파일
├── results/                  # 실험 결과
├── resource/                 # 데이터 리소스
├── configs/                  # 설정 파일
├── logs/                     # 로그 파일
│   └── slurm/                # SLURM 로그
└── documents/                # 문서
```

---

## 실험

### 1. [실험 유형 1] (`<folder>/`)

- `script_a.py`: [설명]
- `script_b.py`: [설명]

### 2. [실험 유형 2] (`<folder>/`)

- `script_c.py`: [설명]

---

## 벤치마크 결과

### [벤치마크 이름] (YYYY-MM-DD)

| 방법 | 지표 1 | 지표 2 | 비고 |
|------|:------:|:------:|------|
| Baseline | - | - | 기준선 |
| Method A | - | - | [설명] |
| Method B | - | - | [설명] |

**핵심 발견**: [요약]

---

## SLURM 실험

### 사용 가능한 리소스

- **노드**: [노드 이름]
- **GPU**: [GPU 정보]
- **메모리**: [메모리 정보]
- **CPU**: [CPU 정보]

### SLURM 스크립트

```text
scripts/slurm/
├── run_experiment.sh        # 기본 실험 스크립트
└── submit_all.sh            # 전체 제출 스크립트
```

### 실험 실행

```bash
# 단일 실험
sbatch --job-name=exp scripts/slurm/run_experiment.sh <args>

# 전체 제출
./scripts/slurm/submit_all.sh

# 모니터링
squeue -u $USER
tail -f logs/slurm/*.out
nvidia-smi
```

---

## 코드 가이드라인

### 사용 예시

```python
# 기본 사용 예시 코드
```

### 구현 체크리스트

1. [체크 항목 1]
2. [체크 항목 2]
3. [체크 항목 3]

---

## 폐기된 방법 (`_legacy/`)

| 방법 | 폐기 사유 |
|------|----------|
| [Method A] | [사유] |
| [Method B] | [사유] |

---

## 실험 로깅

`documents/logs/`에 발견사항 기록:

```markdown
# <실험 제목>

**날짜**: YYYY-MM-DD
**목표**: <간단한 설명>

## 결과
## 결론
## 생성된 파일
```

---

## 현재 포커스: [Phase 이름]

**목표**: [현재 Phase 목표]

| Phase | 작업 | 상태 |
|:------|:-----|:----:|
| Phase 1 | [작업] | ✅ 완료 |
| Phase 2 | [작업] | 🔄 진행 중 |
| Phase 3 | [작업] | ⏳ 예정 |

### 현재 Phase 핵심 결과

| 방법 | 결과 | 상태 |
|------|------|------|
| Method A | [결과] | ✅ |
| Method B | [결과] | ❌ |

**핵심 발견**: [요약]

자세한 내용은 [EXPERIMENT_PLAN.md](development/EXPERIMENT_PLAN.md) 참조.

---

**최종 업데이트**: YYYY-MM-DD
**프로젝트 상태**: [상태 요약]
