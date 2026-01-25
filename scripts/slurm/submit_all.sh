#!/bin/bash
# ============================================================
# 다중 실험 제출 스크립트 템플릿
# ============================================================
#
# 사용법:
#   ./scripts/slurm/submit_all.sh [experiment_type]
#
# 예시:
#   ./scripts/slurm/submit_all.sh all       # 모든 실험
#   ./scripts/slurm/submit_all.sh phase1    # Phase 1 실험만
# ============================================================

set -e

EXPERIMENT_TYPE=${1:-all}

# 프로젝트 루트 설정
export PROJECT_ROOT=$(pwd)

echo "=============================================="
echo "Submitting experiments: $EXPERIMENT_TYPE"
echo "Project Root: $PROJECT_ROOT"
echo "=============================================="

# 로그 디렉토리 생성
mkdir -p logs/slurm

case $EXPERIMENT_TYPE in
    "all")
        echo "Submitting all experiments..."
        sbatch --job-name=exp1 scripts/slurm/run_experiment.sh exp1 0
        sbatch --job-name=exp2 scripts/slurm/run_experiment.sh exp2 1
        ;;
    "phase1")
        echo "Submitting Phase 1 experiments..."
        sbatch --job-name=phase1_a scripts/slurm/run_experiment.sh phase1_a 0
        ;;
    "phase2")
        echo "Submitting Phase 2 experiments..."
        sbatch --job-name=phase2_a scripts/slurm/run_experiment.sh phase2_a 0
        ;;
    *)
        echo "Unknown experiment type: $EXPERIMENT_TYPE"
        echo "Available: all, phase1, phase2"
        exit 1
        ;;
esac

echo "=============================================="
echo "Jobs submitted. Check status with: squeue -u \$USER"
echo "=============================================="
