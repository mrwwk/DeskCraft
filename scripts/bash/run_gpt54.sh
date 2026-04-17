#!/bin/bash
set -euo pipefail

bash "$(dirname "$0")/../../taiji_task/install_taiji_client.sh"

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CODE_PATH="$(cd "${REPO_ROOT}/../.." && pwd)"
export APP_ID='m1gjTHxx_jackwkwang'
export APP_KEY='tM1urhJTxl7KFSyo'
export BASE_URL='http://llm-api.model-eval.woa.com'
export MODEL='api_azure_openai_gpt-5.4-2026-03-05'
# Set AWS env vars to avoid import errors even when using docker locally.
export AWS_REGION="${AWS_REGION:-us-east-1}"
export AWS_SUBNET_ID="${AWS_SUBNET_ID:-subnet-dummy}"
export AWS_SECURITY_GROUP_ID="${AWS_SECURITY_GROUP_ID:-sg-dummy}"

if [ -n "${API_KEY:-}" ] && [ -z "${APP_KEY:-}" ]; then
    export APP_KEY="${API_KEY}"
fi

if [ -n "${OPENAI_BASE_URL:-}" ] && [ -z "${BASE_URL:-}" ]; then
    export BASE_URL="${OPENAI_BASE_URL}"
fi

export BASE_URL="${BASE_URL:-http://llm-api.model-eval.woa.com}"
export MODEL="${MODEL:-api_azure_openai_gpt-5.4-2026-03-05}"
export OPENAI_TIMEOUT="${OPENAI_TIMEOUT:-120}"

cd "${REPO_ROOT}"

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

if ! command -v tmux &> /dev/null; then
    echo "Installing tmux..."
    apt-get update -qq
    apt-get install -y -qq tmux
fi

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

echo "Cleaning up old containers..."
docker ps -a --filter "ancestor=osworld" -q | xargs -r docker rm -f 2>/dev/null || true

if [ ! -f "osworld_image.tar" ]; then
    echo "Docker image tar not found: osworld_image.tar"
    exit 1
fi
docker load -i osworld_image.tar

if [ ! -f "/workspace/osworld/bin/activate" ]; then
    echo "OSWorld virtualenv not found: /workspace/osworld/bin/activate"
    exit 1
fi
. /workspace/osworld/bin/activate

mkdir -p docker_vm_data

PATH_TO_VM="${PATH_TO_VM:-docker_vm_data/new_env/Ubuntu.qcow2}"
if [ ! -f "${PATH_TO_VM}" ]; then
    echo "VM image not found: ${PATH_TO_VM}"
    exit 1
fi

if [ -d "/cq_1/share_300000800/user/jackwkwang/pw-browsers" ]; then
    export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-/cq_1/share_300000800/user/jackwkwang/pw-browsers}"
fi

LOG_DIR="${LOG_DIR:-${CODE_PATH}/code/OSWorld/logs/taiji_task}"
mkdir -p logs "${LOG_DIR}"

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="${LOG_FILE:-${LOG_DIR}/run_gpt54_${TIMESTAMP}.log}"

echo "Logging to ${LOG_FILE}"

python scripts/python/run_multienv_gpt54.py \
    --provider_name "${PROVIDER_NAME:-docker}" \
    --headless \
    --path_to_vm "${PATH_TO_VM}" \
    --run_name "${RUN_NAME:-gpt54_not_interactive—think_low}" \
    --model "${MODEL}" \
    --result_dir "${RESULT_DIR:-./results}" \
    --test_config_base_dir "${TEST_CONFIG_BASE_DIR:-evaluation_examples/example_final}" \
    --test_all_meta_path "${TEST_META_PATH:-evaluation_examples/test_all.json}" \
    --max_steps "${MAX_STEPS:-100}" \
    --num_envs "${NUM_ENVS:-1}" \
    --sleep_after_execution "${SLEEP_AFTER_EXECUTION:-5}" \
    --log_level "${LOG_LEVEL:-DEBUG}" \
    2>&1 | tee -a "${LOG_FILE}"
# /apdcephfs/hunyuanaidjpsh2/jp_sh2_cephfs/apdcephfs_sh2/share_300000800/user/jackwkwang/code/OSWorld/evaluation_examples/
