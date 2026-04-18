#!/bin/bash
# start_vllm_r3agentv3.sh
# 单独启动 vLLM 服务，供 start_r3agentv3.sh 使用
# 用法: bash taiji_task/start_vllm_r3agentv3.sh
# 硬件: 8 x H20 (96GB/卡)，模型: 32B FP8 量化

# ============ 按需修改 ============
MODEL_PATH="/home/0416-model"   # 模型路径
MODEL_NAME="0416-model"

# 8xH20 + 32B FP8：单卡可放下（权重约 32GB << 96GB），
# 首选纯 DP 以获得更高吞吐并避免 TP NCCL 通信开销
TENSOR_PARALLEL_SIZE=2
DATA_PARALLEL_SIZE=4
PORT=8000

# 显存 / KV Cache 参数（若仍 OOM，按注释顺序继续下调）
MAX_MODEL_LEN=40960          # 客户端 max_tokens=32768，留余量；不设会按模型 config 的 128K/1M 预留 KV Cache -> OOM
MAX_NUM_SEQS=8               # 单 DP 进程并发 seq 数；8*DP8=64 路总并发，足够覆盖 NUM_ENVS=15
GPU_MEM_UTIL=0.88            # H20 显存充足；OOM 时降到 0.85 / 0.80
# ==================================

# CUDA + 多进程必须使用 spawn，防止 "Cannot re-initialize CUDA in forked subprocess"
export VLLM_WORKER_MULTIPROC_METHOD=spawn

# 激活虚拟环境（可选：不存在则使用系统 Python 环境）
VENV_ACTIVATE="/workspace/osworld/bin/activate"
if [ -f "${VENV_ACTIVATE}" ]; then
    echo "Activating venv: ${VENV_ACTIVATE}"
    # shellcheck disable=SC1090
    . "${VENV_ACTIVATE}"
else
    echo "[WARN] venv not found at ${VENV_ACTIVATE}, using system python: $(which python)"
fi

# 启动前自检：GPU 数量是否满足 TP*DP
NEED_GPUS=$((TENSOR_PARALLEL_SIZE * DATA_PARALLEL_SIZE))
HAVE_GPUS=$(nvidia-smi -L 2>/dev/null | wc -l)
echo "Need ${NEED_GPUS} GPUs, detected ${HAVE_GPUS} GPUs."
if [ "${HAVE_GPUS}" -lt "${NEED_GPUS}" ]; then
    echo "[ERROR] GPU 数量不足 (${HAVE_GPUS} < ${NEED_GPUS})，请调整 TENSOR_PARALLEL_SIZE / DATA_PARALLEL_SIZE！"
    exit 1
fi

VLLM_DP_ARGS=""
if [ "${DATA_PARALLEL_SIZE}" -gt 1 ]; then
    VLLM_DP_ARGS="--data-parallel-size ${DATA_PARALLEL_SIZE}"
fi

echo "========== Starting vLLM: ${MODEL_NAME} (TP=${TENSOR_PARALLEL_SIZE}, DP=${DATA_PARALLEL_SIZE}) =========="
vllm serve "${MODEL_PATH}" \
    --trust-remote-code \
    --limit-mm-per-prompt '{"image":5,"video":0}' \
    --tensor-parallel-size ${TENSOR_PARALLEL_SIZE} \
    ${VLLM_DP_ARGS} \
    --port ${PORT} \
    --served-model-name "${MODEL_NAME}" \
    --max-num-seqs ${MAX_NUM_SEQS} \
    --gpu-memory-utilization ${GPU_MEM_UTIL} \
    --swap-space 4
