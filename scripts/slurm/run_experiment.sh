#!/bin/bash
#SBATCH --job-name=<experiment_name>
#SBATCH --output=logs/slurm/%x_%j.out
#SBATCH --error=logs/slurm/%x_%j.err
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=02:00:00

# ============================================================
# 기본 실험 SLURM 스크립트 템플릿
# ============================================================
#
# 사용법:
#   sbatch --job-name=<name> scripts/slurm/run_experiment.sh <args>
#
# 환경변수:
#   PROJECT_ROOT: 프로젝트 루트 디렉토리 (필수)
#
# 예시:
#   export PROJECT_ROOT=/path/to/project
#   sbatch --job-name=test scripts/slurm/run_experiment.sh experiment_name
# ============================================================

set -e

# 인자 파싱
EXPERIMENT_NAME=${1:-default}
shift || true

# 환경 설정
if [ -z "$PROJECT_ROOT" ]; then
    # SLURM 제출 시 현재 디렉토리 사용
    PROJECT_ROOT=$(pwd)
fi
cd "$PROJECT_ROOT"

# 로그 디렉토리 생성
mkdir -p logs/slurm
mkdir -p results

# 실험 정보 출력
echo "=============================================="
echo "Experiment: $EXPERIMENT_NAME"
echo "=============================================="
echo "SLURM Job ID: ${SLURM_JOB_ID:-local}"
echo "Node: ${SLURM_NODELIST:-$(hostname)}"
echo "GPU: (allocated by SLURM)"
echo "Working Directory: $(pwd)"
echo "Start Time: $(date)"
echo "=============================================="

# GPU 정보 출력 (가능한 경우)
nvidia-smi -L || true

# 실험 실행
# TODO: 실제 실험 스크립트로 교체
uv run python src/experiments/<script>.py \
    --experiment "$EXPERIMENT_NAME" \
    "$@"

echo "=============================================="
echo "End Time: $(date)"
echo "=============================================="
