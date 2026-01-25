#!/bin/bash
#SBATCH --job-name=train
#SBATCH --output=logs/slurm/%x_%j.out
#SBATCH --error=logs/slurm/%x_%j.err
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=24:00:00

# ============================================================
# 학습 SLURM 스크립트 템플릿
# ============================================================
#
# 장시간 학습 작업용 템플릿
#
# 사용법:
#   sbatch --job-name=train_exp scripts/slurm/run_training.sh config.yaml
# ============================================================

set -e

CONFIG_FILE=${1:-configs/default.yaml}
shift || true

# 환경 설정
if [ -z "$PROJECT_ROOT" ]; then
    PROJECT_ROOT=$(pwd)
fi
cd "$PROJECT_ROOT"

# 로그 디렉토리 생성
mkdir -p logs/slurm
mkdir -p results

echo "=============================================="
echo "Training Job"
echo "=============================================="
echo "SLURM Job ID: ${SLURM_JOB_ID:-local}"
echo "Node: ${SLURM_NODELIST:-$(hostname)}"
echo "GPU: (allocated by SLURM)"
echo "Config: $CONFIG_FILE"
echo "Start Time: $(date)"
echo "=============================================="

# GPU 정보 출력
nvidia-smi

# 학습 실행
# TODO: 실제 학습 스크립트로 교체
uv run python src/experiments/train.py \
    --config "$CONFIG_FILE" \
    "$@"

echo "=============================================="
echo "End Time: $(date)"
echo "=============================================="
