#!/bin/bash
# run_gpt54_interactive.sh
# GPT-5.4 OSWorld interactive 评测脚本
# sleep 365d 仅允许在debug情况下使用sleep，禁止使用sleep命令占卡后提交正式任务

bash "$(dirname "$0")/../../taiji_task/install_taiji_client.sh"

# code dir
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CODE_PATH="$(cd "${REPO_ROOT}/../.." && pwd)"

export APP_ID="${APP_ID:-m1gjTHxx_jackwkwang}"
export APP_KEY="${APP_KEY:-tM1urhJTxl7KFSyo}"
export BASE_URL="${BASE_URL:-http://llm-api.model-eval.woa.com}"
export MODEL="${MODEL:-api_azure_openai_gpt-5-nano}"
export OPENAI_TIMEOUT="${OPENAI_TIMEOUT:-120}"

# set AWS env vars to avoid import error (not actually using AWS)
export AWS_REGION="${AWS_REGION:-us-east-1}"
export AWS_SUBNET_ID="${AWS_SUBNET_ID:-subnet-dummy}"
export AWS_SECURITY_GROUP_ID="${AWS_SECURITY_GROUP_ID:-sg-dummy}"

if [ -n "${API_KEY:-}" ] && [ -z "${APP_KEY:-}" ]; then
    export APP_KEY="${API_KEY}"
fi

if [ -n "${OPENAI_BASE_URL:-}" ] && [ -z "${BASE_URL:-}" ]; then
    export BASE_URL="${OPENAI_BASE_URL}"
fi

if [ -z "${OPENAI_API_KEY:-}" ] && { [ -z "${APP_ID:-}" ] || [ -z "${APP_KEY:-}" ]; }; then
    echo "Either OPENAI_API_KEY or APP_ID with API_KEY/APP_KEY must be set"
    exit 1
fi

# 1. OSWorld code
cd "${REPO_ROOT}"

# 2. install docker
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
    apt-get install -y -qq docker.io tmux
fi

# 3. start docker daemon with tmux
if ! docker info > /dev/null 2>&1; then
    if ! tmux has-session -t docker 2>/dev/null; then
        tmux new-session -d -s docker 'dockerd --storage-driver=vfs'
    fi

    echo "Waiting for Docker daemon to be ready..."
    while ! docker info > /dev/null 2>&1; do
        sleep 2
    done
    echo "Docker daemon is ready!"
fi

# 清理残留的 osworld 容器
echo "Cleaning up old containers..."
docker ps -a --filter "ancestor=osworld" -q | xargs -r docker rm -f 2>/dev/null || true

# 4. prepare docker image from local tar
docker load -i osworld_image.tar

# 5. activate osworld virtual environment
. /workspace/osworld/bin/activate

# 6. prepare VM data
mkdir -p docker_vm_data

PATH_TO_VM="${PATH_TO_VM:-docker_vm_data/new_env/Ubuntu.qcow2}"
if [ ! -f "${PATH_TO_VM}" ]; then
    echo "VM image not found: ${PATH_TO_VM}"
    exit 1
fi

if [ -d "/cq_1/share_300000800/user/jackwkwang/pw-browsers" ]; then
    export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-/cq_1/share_300000800/user/jackwkwang/pw-browsers}"
fi

# 7. run GPT-5.4 interactive evaluation
LOG_DIR="${LOG_DIR:-${CODE_PATH}/code/OSWorld/logs/taiji_task}"
mkdir -p logs "${LOG_DIR}"
LOG_FILE="${LOG_FILE:-${LOG_DIR}/run_gpt54_interactive_$(date +%Y%m%d_%H%M%S).log}"
echo "Logging to: ${LOG_FILE}"

python scripts/python/run_multienv_gpt54_interactive.py \
    --test_config_base_dir evaluation_examples/example_final \
    --run_name "${RUN_NAME:-gpt5-nano_interactive}" \
    --provider_name "${PROVIDER_NAME:-docker}" \
    --headless \
    --path_to_vm "${PATH_TO_VM}" \
    --model "${MODEL}" \
    --result_dir "${RESULT_DIR:-./results}" \
    --test_all_meta_path "${TEST_META_PATH:-evaluation_examples/test.json}" \
    --max_steps "${MAX_STEPS:-100}" \
    --num_envs "${NUM_ENVS:-2}" \
    --sleep_after_execution "${SLEEP_AFTER_EXECUTION:-5}" \
    --log_level "${LOG_LEVEL:-DEBUG}" \
    --user_base_url "${USER_BASE_URL:-http://29.160.43.141:8000/v1}" \
    --user_api_key "${USER_SIM_API_KEY:-${USER_API_KEY:-EMPTY}}" \
    --user_model "${USER_MODEL:-Qwen3.5-122B-A10B}" \
    --user_temperature "${USER_TEMPERATURE:-0.7}" \
    2>&1 | tee -a "${LOG_FILE}"
