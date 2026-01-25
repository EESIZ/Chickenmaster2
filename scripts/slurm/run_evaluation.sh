#!/bin/bash
#SBATCH --job-name=eval
#SBATCH --output=logs/slurm/%x_%j.out
#SBATCH --error=logs/slurm/%x_%j.err
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00

# ============================================================
# 평가 SLURM 스크립트 템플릿
# ============================================================
#
# 모델 평가 작업용 템플릿
#
# 사용법:
#   sbatch --job-name=eval_model scripts/slurm/run_evaluation.sh checkpoint_path
# ============================================================

set -e

CHECKPOINT_PATH=${1:-results/checkpoint}
shift || true

# 환경 설정
if [ -z "$PROJECT_ROOT" ]; then
    PROJECT_ROOT=$(pwd)
fi
cd "$PROJECT_ROOT"

# 로그 디렉토리 생성
mkdir -p logs/slurm
mkdir -p results/evaluation

echo "=============================================="
echo "Evaluation Job"
echo "=============================================="
echo "SLURM Job ID: ${SLURM_JOB_ID:-local}"
echo "Node: ${SLURM_NODELIST:-$(hostname)}"
echo "GPU: (allocated by SLURM)"
echo "Checkpoint: $CHECKPOINT_PATH"
echo "Start Time: $(date)"
echo "=============================================="

# GPU 정보 출력 (가능한 경우)
nvidia-smi -L || true

# 평가 실행
# TODO: 실제 평가 스크립트로 교체
uv run python src/experiments/evaluate.py \
    --checkpoint "$CHECKPOINT_PATH" \
    "$@"

echo "=============================================="
echo "End Time: $(date)"
echo "=============================================="
