#!/bin/bash
# start_kimi_k25.sh
# Kimi K2.5 评测脚本（通过远程 vLLM 服务调用）
#
# 用法示例:
#   bash taiji_task/start_kimi_k25.sh
#   THINKING=false NUM_ENVS=10 bash taiji_task/start_kimi_k25.sh

bash $(dirname "$0")/install_taiji_client.sh

# ============ 按需修改 ============
VLLM_BASE_URL="${VLLM_BASE_URL:-http://28.12.129.142:8000/v1}"
MODEL_NAME="${MODEL_NAME:-KimiK25}"
RUN_NAME="${RUN_NAME:-kimi-k25-${MODEL_NAME}-01}"

# 采样参数
TEMPERATURE="${TEMPERATURE:-1.0}"
TOP_P="${TOP_P:-0.95}"
MAX_TOKENS="${MAX_TOKENS:-40960}"

# 评测参数
NUM_ENVS="${NUM_ENVS:-15}"
MAX_STEPS="${MAX_STEPS:-100}"
THINKING="${THINKING:-true}"
TEST_ALL_META_PATH="evaluation_examples/example_final_non_interactive_all.json"
TEST_CONFIG_BASE_DIR="${TEST_CONFIG_BASE_DIR:-evaluation_examples/example_final}"
# ==================================

CODE_PATH="/cq_1/share_300000800/user/jackwkwang"

# 结果目录：results/<RUN_NAME>（由 --run_name 自动拼接）
RESULT_DIR="${CODE_PATH}/code/OSWorld/results"

# 环境变量
export AWS_REGION="us-east-1"
export AWS_SUBNET_ID="subnet-dummy"
export AWS_SECURITY_GROUP_ID="sg-dummy"

# KimiAgent 通过 OpenAI 兼容接口调用远程 vLLM
export KIMI_AUTH_MODE="openai"
export KIMI_API_KEY="EMPTY"
export KIMI_API_URL="${VLLM_BASE_URL}/chat/completions"

export PLAYWRIGHT_BROWSERS_PATH=${CODE_PATH}/pw-browsers

cd ${CODE_PATH}/code/OSWorld

# 安装 Docker（如未安装）
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
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
echo "Waiting for Docker daemon to be ready..."
while ! docker info > /dev/null 2>&1; do sleep 2; done
echo "Docker daemon is ready!"

# 清理残留容器
echo "Cleaning up old containers..."
docker ps -a --filter "ancestor=osworld" -q | xargs -r docker rm -f 2>/dev/null || true

# 加载 Docker 镜像
docker load -i osworld_image.tar

# 激活虚拟环境
. /workspace/osworld/bin/activate

# 准备 VM 数据
mkdir -p docker_vm_data

# quickstart 冒烟测试
python quickstart.py --provider_name docker --headless True

# 等待远程 vLLM 服务就绪
echo "Waiting for vLLM server (${VLLM_BASE_URL}) to be ready..."
while ! curl -s "${VLLM_BASE_URL}/models" > /dev/null 2>&1; do
    sleep 10
    echo "Still waiting for vLLM server..."
done
echo "vLLM server is ready!"

# 构建 thinking 参数
THINKING_ARG=""
if [ "${THINKING}" = "true" ]; then
    THINKING_ARG="--thinking"
fi

# 日志
LOG_DIR="${CODE_PATH}/code/OSWorld/logs/taiji_task"
mkdir -p "${LOG_DIR}"
LOG_FILE="${LOG_DIR}/run_kimi_k25_$(date +%Y%m%d_%H%M%S).log"
echo "Logging to: ${LOG_FILE}"

echo "========== Running Kimi K2.5: ${MODEL_NAME} =========="
echo "Run name:     ${RUN_NAME}"
echo "Result dir:   ${RESULT_DIR}"
echo "KIMI_API_URL: ${KIMI_API_URL}"
echo "THINKING:     ${THINKING}"
echo "NUM_ENVS:     ${NUM_ENVS}"
echo "MAX_STEPS:    ${MAX_STEPS}"
echo "========================================"

python3 ${CODE_PATH}/code/OSWorld/run_multienv_kimi_k25.py \
    --provider_name docker \
    --headless \
    --path_to_vm /home/Ubuntu.qcow2 \
    --observation_type screenshot \
    --num_envs ${NUM_ENVS} \
    --max_steps ${MAX_STEPS} \
    --model "${MODEL_NAME}" \
    --temperature ${TEMPERATURE} \
    --top_p ${TOP_P} \
    --max_tokens ${MAX_TOKENS} \
    --coordinate_type relative \
    ${THINKING_ARG} \
    --no-taiji \
    --test_all_meta_path ${TEST_ALL_META_PATH} \
    --test_config_base_dir ${TEST_CONFIG_BASE_DIR} \
    --sleep_after_execution 5 \
    --result_dir ${RESULT_DIR} \
    --run_name "${RUN_NAME}" 2>&1 | tee -a "${LOG_FILE}"

