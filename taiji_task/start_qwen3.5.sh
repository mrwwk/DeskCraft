#!/bin/bash
# start_qwen3.5.sh
# Qwen3.5 系列模型评测脚本
#
# Qwen3.5 使用全新混合架构（Gated Delta Networks + MoE），与 Qwen3-VL 不同：
#   1. 需要 --reasoning-parser qwen3（默认开启思考模式）
#   2. 需要显式设置 --max-model-len（原生支持 262144，按显存调整）
#   3. 不需要 --limit-mm-per-prompt
#   4. 需要使用包含 Qwen3.5 支持的镜像（不再在脚本中安装 vLLM/transformers）
#
# 用法示例:
#   bash start_qwen3.5.sh
#   MODEL_NAME=Qwen3.5-397B-A17B TENSOR_PARALLEL_SIZE=8 bash start_qwen3.5.sh
#   MODEL_NAME=Qwen3.5-397B-A17B TENSOR_PARALLEL_SIZE=8 MAX_MODEL_LEN=65536 bash start_qwen3.5.sh
#   MODEL_NAME=Qwen3.5-397B-A17B TENSOR_PARALLEL_SIZE=8 bash start_qwen3.5.sh

bash $(dirname "$0")/install_taiji_client.sh

# ============ 路径前缀 ============
PATH_PREFIX="/apdcephfs_fsgm/share_304220499"

# ============ 模型配置 ============
MODEL_NAME="${MODEL_NAME:-Qwen3.5-397B-A17B}"

# ============ 采样参数 ============
TEMPERATURE="${TEMPERATURE:-0.6}"
TOP_P="${TOP_P:-0.95}"
MAX_TOKENS="${MAX_TOKENS:-32768}"

# ============ 评测参数 ============
NUM_ENVS="${NUM_ENVS:-5}"
MAX_STEPS="${MAX_STEPS:-100}"

# ============ vLLM 部署参数 ============
TENSOR_PARALLEL_SIZE="${TENSOR_PARALLEL_SIZE:-8}"
DATA_PARALLEL_SIZE="${DATA_PARALLEL_SIZE:-1}"
GPU_MEMORY_UTILIZATION="${GPU_MEMORY_UTILIZATION:-0.9}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-131072}"

# ============ 路径配置 ============
CODE_PATH="${CODE_PATH:-${PATH_PREFIX}/chenxuwu/osworld_wzj_code/OSWorld}"
DATA_PATH="${DATA_PATH:-${PATH_PREFIX}/chenxuwu}"
MODEL_PATH="${MODEL_PATH:-${PATH_PREFIX}/model/${MODEL_NAME}}"

# 本地工作目录（太极任务会将代码拷贝到此目录运行）
LOCAL_WORK_DIR="${LOCAL_WORK_DIR:-/data/workspace/OSWorld_local/OSWorld}"
# 结果回传目标目录（评测完成后将 results/ 拷贝回此路径，可通过环境变量修改）
RESULT_TARGET_DIR="${RESULT_TARGET_DIR:-${PATH_PREFIX}/chenxuwu/code1/OSWorld/results}"

# 环境变量
export AWS_REGION="us-east-1"
export AWS_SUBNET_ID="subnet-dummy"
export AWS_SECURITY_GROUP_ID="sg-dummy"
export OPENAI_API_KEY="EMPTY"
export OPENAI_BASE_URL="http://localhost:8000/v1"

# 拷贝代码到本地工作目录
echo "========== Copying code to local work dir =========="
echo "CODE_PATH=${CODE_PATH}"
echo "LOCAL_WORK_DIR=${LOCAL_WORK_DIR}"
if [ ! -d "${CODE_PATH}" ]; then
    echo "[错误] CODE_PATH 不存在: ${CODE_PATH}"
    ls -la "$(dirname ${CODE_PATH})" 2>&1 || true
    exit 1
fi
mkdir -p ${LOCAL_WORK_DIR}
cp -a ${CODE_PATH}/* ${LOCAL_WORK_DIR}/
echo "Code copied to ${LOCAL_WORK_DIR}"
ls ${LOCAL_WORK_DIR}/ | head -20
cd ${LOCAL_WORK_DIR}

# 准备 cache
if [ ! -d "cache" ]; then
    cp -r ${DATA_PATH}/data/osworld_cache.zip ./osworld_cache.zip
    unzip -q osworld_cache.zip && mv osworld_cache cache && rm -rf osworld_cache.zip
fi

# 安装 Docker
if ! command -v docker &> /dev/null; then
    cp /etc/apt/sources.list /etc/apt/sources.list.bak 2>/dev/null || true
    cat > /etc/apt/sources.list << 'EOF'
deb http://mirrors.tencentyun.com/ubuntu/ jammy main restricted universe multiverse
deb http://mirrors.tencentyun.com/ubuntu/ jammy-updates main restricted universe multiverse
deb http://mirrors.tencentyun.com/ubuntu/ jammy-backports main restricted universe multiverse
deb http://mirrors.tencentyun.com/ubuntu/ jammy-security main restricted universe multiverse
EOF
    apt-get update -qq
    apt-get install -y -qq docker.io
fi

# 启动 Docker daemon
tmux new-session -d -s docker 'dockerd --storage-driver=vfs'
while ! docker info > /dev/null 2>&1; do sleep 2; done
docker ps -a --filter "ancestor=osworld" -q | xargs -r docker rm -f 2>/dev/null || true

# 准备 Docker 镜像
cp -r ${DATA_PATH}/data/osworld_image.tar ./osworld_image.tar
docker load -i osworld_image.tar
rm -f osworld_image.tar

# 激活虚拟环境
. /workspace/osworld/bin/activate

# 准备 VM 数据
mkdir -p docker_vm_data
if [ ! -f "docker_vm_data/Ubuntu.qcow2" ]; then
    cp -r ${DATA_PATH}/data/Ubuntu.qcow2.zip ./docker_vm_data/
    cd docker_vm_data && unzip -q Ubuntu.qcow2.zip && rm -f Ubuntu.qcow2.zip && cd ..
fi

# 测试
python quickstart.py --provider_name docker --headless True

# GPU 占用
python ${LOCAL_WORK_DIR}/gpu_occupy.py &

# 启动 vLLM
echo "========== vLLM Configuration =========="
echo "MODEL_NAME=${MODEL_NAME}"
echo "MODEL_PATH=${MODEL_PATH}"
echo "TENSOR_PARALLEL_SIZE=${TENSOR_PARALLEL_SIZE}"
echo "DATA_PARALLEL_SIZE=${DATA_PARALLEL_SIZE}"
echo "GPU_MEMORY_UTILIZATION=${GPU_MEMORY_UTILIZATION}"
echo "MAX_MODEL_LEN=${MAX_MODEL_LEN}"
echo "========== Eval Configuration =========="
echo "NUM_ENVS=${NUM_ENVS}"
echo "MAX_STEPS=${MAX_STEPS}"
echo "TEMPERATURE=${TEMPERATURE}"
echo "TOP_P=${TOP_P}"
echo "MAX_TOKENS=${MAX_TOKENS}"
echo "========================================"

VLLM_DP_ARGS=""
if [ "${DATA_PARALLEL_SIZE}" -gt 1 ]; then
    VLLM_DP_ARGS="--data-parallel-size ${DATA_PARALLEL_SIZE}"
fi

start_vllm() {
    vllm serve ${MODEL_PATH} \
        --trust-remote-code \
        --tensor-parallel-size ${TENSOR_PARALLEL_SIZE} \
        ${VLLM_DP_ARGS} \
        --port 8000 \
        --gpu-memory-utilization ${GPU_MEMORY_UTILIZATION} \
        --max-model-len ${MAX_MODEL_LEN} \
        --reasoning-parser qwen3 \
        --served-model-name "${MODEL_NAME}" &
}

start_vllm

while ! curl -s http://localhost:8000/health > /dev/null 2>&1; do sleep 10; done
echo "vLLM server is ready!"

# vLLM 健康监控
(
    while true; do
        sleep 60
        if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo "[Monitor] vLLM down, restarting..."
            pkill -f "vllm serve" 2>/dev/null || true
            sleep 5
            start_vllm
            sleep 120
        fi
    done
) &

echo "========== Running ${MODEL_NAME} =========="

# 运行评测
python ${LOCAL_WORK_DIR}/run_multienv_qwen3vl.py \
    --provider_name docker \
    --headless \
    --num_envs ${NUM_ENVS} \
    --max_steps ${MAX_STEPS} \
    --model "${MODEL_NAME}" \
    --temperature ${TEMPERATURE} \
    --top_p ${TOP_P} \
    --max_tokens ${MAX_TOKENS} \
    --test_all_meta_path evaluation_examples/test_nogdrive.json

# 回传结果
echo "========== Copying results back =========="
if [ -d "${LOCAL_WORK_DIR}/results" ]; then
    mkdir -p ${RESULT_TARGET_DIR}
    cp -a ${LOCAL_WORK_DIR}/results/* ${RESULT_TARGET_DIR}/
    echo "Results copied to ${RESULT_TARGET_DIR}"
else
    echo "No results directory found, skipping copy-back"
fi
