#!/bin/bash
# start_r3agentv3_interactive.sh
# R3AgentV3 Interactive 评测脚本
# 前提：vLLM 服务已由 start_vllm_r3agentv3.sh 单独启动
# sleep 365d 仅允许在debug情况下使用sleep，禁止使用sleep命令占卡后提交正式任务

bash $(dirname "$0")/install_taiji_client.sh

# ============ 按需修改 ============
MODEL_NAME="0416-model"
RUN_NAME="r3agentv3-interactive-${MODEL_NAME}-02"

PROMPT_TYPE="l2"          # 提示词类型: l1, l2, l3
HISTORY_N=4               # 历史消息数量
COORD="relative"          # 坐标类型: absolute, relative

NUM_ENVS=15                # 并行 Docker 容器数
MAX_STEPS=100              # 每个任务最大步数
TEST_ALL_META_PATH="evaluation_examples/example_final_interactive_gpt54_all.json"
TEST_CONFIG_BASE_DIR="evaluation_examples/example_final" 
# example_final_interactive_gpt54_all.json
TEMPERATURE=0
TOP_P=0.9
MAX_TOKENS=32768

# User Simulator 配置（用于 interactive 任务）
USER_BASE_URL="http://28.12.129.142:8000/v1"
USER_API_KEY="EMPTY"
USER_MODEL="KimiK25"
# ==================================

CODE_PATH="/cq_1/share_300000800/user/jackwkwang"

# 结果目录：results/<RUN_NAME>（由 --run_name 自动拼接）
RESULT_DIR="${CODE_PATH}/code/OSWorld/results"

# set AWS env vars to avoid import error (not actually using AWS)
export AWS_REGION="us-east-1"
export AWS_SUBNET_ID="subnet-dummy"
export AWS_SECURITY_GROUP_ID="sg-dummy"

# set OPENAI API env vars (R3AgentV3 通过 OpenAI Compatible API 调用 vLLM)
export OPENAI_API_KEY="EMPTY"
export OPENAI_BASE_URL="http://localhost:8000/v1"
export PLAYWRIGHT_BROWSERS_PATH=/cq_1/share_300000800/user/jackwkwang/pw-browsers

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

# 清理残留的 osworld 容器
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

# 等待 vLLM 服务就绪
echo "Waiting for vLLM server to be ready..."
while ! curl -s http://localhost:8000/health > /dev/null 2>&1; do
    sleep 10
    echo "Still waiting for vLLM server..."
done
echo "vLLM server is ready!"

# 日志
LOG_DIR="${CODE_PATH}/code/OSWorld/logs/taiji_task"
mkdir -p "${LOG_DIR}"
LOG_FILE="${LOG_DIR}/run_r3agentv3_interactive_$(date +%Y%m%d_%H%M%S).log"
echo "Logging to: ${LOG_FILE}"

echo "========== Running R3AgentV3 Interactive: ${MODEL_NAME} =========="
echo "Run name:      ${RUN_NAME}"
echo "Prompt type:   ${PROMPT_TYPE}"
echo "History N:     ${HISTORY_N}"
echo "Coordinate:    ${COORD}"
echo "User model:    ${USER_MODEL}"
echo "User base URL: ${USER_BASE_URL}"
echo "Result dir:    ${RESULT_DIR}"

python ${CODE_PATH}/code/OSWorld/run_multienv_r3agentv3.py \
    --provider_name docker \
    --headless \
    --path_to_vm /home/Ubuntu.qcow2 \
    --num_envs ${NUM_ENVS} \
    --max_steps ${MAX_STEPS} \
    --model "${MODEL_NAME}" \
    --temperature ${TEMPERATURE} \
    --top_p ${TOP_P} \
    --max_tokens ${MAX_TOKENS} \
    --history_n ${HISTORY_N} \
    --prompt_type ${PROMPT_TYPE} \
    --coord ${COORD} \
    --test_all_meta_path ${TEST_ALL_META_PATH} \
    --test_config_base_dir ${TEST_CONFIG_BASE_DIR} \
    --sleep_after_execution 5 \
    --result_dir ${RESULT_DIR} \
    --run_name "${RUN_NAME}" \
    --user_base_url "${USER_BASE_URL}" \
    --user_api_key "${USER_API_KEY}" \
    --user_model "${USER_MODEL}" \
    --no-taiji 2>&1 | tee -a "${LOG_FILE}"
