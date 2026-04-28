#!/bin/bash
# start_qwen3_8b_interactive.sh
# Qwen3-8B interactive 评测脚本（调用 scripts/python/run_multienv_qwen3vl_interactive.py）
#
# 用法:
#   bash scripts/bash/start_qwen3_8b_interactive.sh
#   ENABLE_THINKING=true NUM_ENVS=10 bash scripts/bash/start_qwen3_8b_interactive.sh

set -uo pipefail

# code dir
CODE_PATH="${CODE_PATH:-/home/xiongtao3/Projects/OSWorld-Pro/desktopworld}"
RESULT_ROOT="${RESULT_ROOT:-${CODE_PATH}/results}"

# ============ Agent (Qwen3-8B) ============
# 必须与 vLLM 启动脚本里 --served-model-name 完全一致
MODEL_NAME="${MODEL_NAME:-Qwen3-VL-8B-Instruct}"
NUM_ENVS="${NUM_ENVS:-30}"
MAX_STEPS="${MAX_STEPS:-100}"
RUN_NAME="${RUN_NAME:-${MODEL_NAME}_interactive_$(date +%Y%m%d)_envs${NUM_ENVS}_steps${MAX_STEPS}}"

# Qwen3VLAgent 专属采样 / prompt 旋钮
COORD="${COORD:-relative}"                  # absolute | relative
HISTORY_N="${HISTORY_N:-4}"                # qwen3vl 无 image collapse，不要太大, 原始代码默认是4
TEMPERATURE="${TEMPERATURE:-0.0}"
TOP_P="${TOP_P:-0.9}"
MAX_TOKENS="${MAX_TOKENS:-32768}"
ENABLE_THINKING="${ENABLE_THINKING:-true}"  # true 开启 thinking 模式（需 vLLM --reasoning-parser qwen3）
TAIJI="${TAIJI:-false}"                     # 本地跑默认关闭 taiji 代理

# Qwen3-8B 独有的 agent 参数（可覆盖，默认对齐 qwen3vl_agent defaults）
API_BACKEND="${API_BACKEND:-openai}"        # openai | dashscope
PLATFORM="${PLATFORM:-ubuntu}"
THINKING_BUDGET="${THINKING_BUDGET:-32768}" # dashscope 路径才生效，openai 忽略

# Qwen3-8B vLLM 服务（OpenAI 兼容）
LLM_BASE_URL="${LLM_BASE_URL:-http://10.44.215.117:3001/v1}"
LLM_HEALTH_URL="${LLM_HEALTH_URL:-${LLM_BASE_URL%/v1}/health}"
export OPENAI_API_KEY="${OPENAI_API_KEY:-EMPTY}"
export OPENAI_BASE_URL="${OPENAI_BASE_URL:-${LLM_BASE_URL}}"

# ============ VM / Tasks ============
PATH_TO_VM="${PATH_TO_VM:-/home/xiongtao3/Projects/OSWorld-Pro/ubuntu-qcow2/Ubuntu.qcow2}"
TEST_META_PATH="${TEST_META_PATH:-evaluation_examples/example_final_interactive_all.json}"
TEST_CONFIG_BASE_DIR="${TEST_CONFIG_BASE_DIR:-evaluation_examples/example_final}"

# ============ User Simulator ============
# 默认与 GUI Agent 共用同一个 vLLM 服务和模型；可通过 USER_BASE_URL / USER_MODEL 覆盖。
USER_BASE_URL="${USER_BASE_URL:-${LLM_BASE_URL}}"
USER_API_KEY="${USER_API_KEY:-${OPENAI_API_KEY}}"
USER_MODEL="${USER_MODEL:-${MODEL_NAME}}"
USER_TEMPERATURE="${USER_TEMPERATURE:-0.7}"

# ============ Misc ============
SLEEP_AFTER_EXECUTION="${SLEEP_AFTER_EXECUTION:-3}"
LOG_LEVEL="${LOG_LEVEL:-INFO}"

# AWS env vars to avoid import errors (not actually used)
export AWS_REGION="${AWS_REGION:-us-east-1}"
export AWS_SUBNET_ID="${AWS_SUBNET_ID:-subnet-dummy}"
export AWS_SECURITY_GROUP_ID="${AWS_SECURITY_GROUP_ID:-sg-dummy}"

# 让本地服务地址绕开公司代理
export no_proxy="${no_proxy:-localhost,127.0.0.1,10.44.215.117,29.160.43.141}"

# ---- 1. cd 到工程根 ----
cd "${CODE_PATH}"

# ---- 2. 清理残留 osworld 容器 ----
echo "Cleaning up old containers..."
docker ps -a --filter "ancestor=osworld" -q | xargs -r docker rm -f 2>/dev/null || true

# ---- 3. 等待 Qwen3-8B LLM 服务就绪 ----
echo "Waiting for LLM server (${LLM_HEALTH_URL}) to be ready..."
while ! curl -s "${LLM_HEALTH_URL}" > /dev/null 2>&1; do
    sleep 10
    echo "Still waiting for LLM server..."
done
echo "LLM server is ready!"

# ---- 4. 日志 ----
LOG_DIR="${LOG_DIR:-${CODE_PATH}/logs}"
mkdir -p "${LOG_DIR}" || true
LOG_FILE="${LOG_FILE:-${LOG_DIR}/run_qwen3_8b_interactive_$(date +%Y%m%d_%H%M%S).log}"

echo "Logging to:        ${LOG_FILE}"
echo "Result dir:        ${RESULT_ROOT}/${RUN_NAME}"
echo "Agent endpoint:    ${OPENAI_BASE_URL}"
echo "Agent model:       ${MODEL_NAME}  (api_backend=${API_BACKEND})"
echo "User-sim endpoint: ${USER_BASE_URL} (model=${USER_MODEL})"
echo "Thinking:          ${ENABLE_THINKING}"
echo "Taiji proxy:       ${TAIJI}"
echo "NUM_ENVS / STEPS:  ${NUM_ENVS} / ${MAX_STEPS}"
echo "HISTORY_N:         ${HISTORY_N}"

# ---- 5. 拼接条件 flag ----
THINKING_ARG=""
if [ "${ENABLE_THINKING}" = "true" ]; then
    THINKING_ARG="--enable_thinking"
fi
TAIJI_ARG="--no-taiji"
if [ "${TAIJI}" = "true" ]; then
    TAIJI_ARG=""
fi

# ---- 6. 跑评测 ----
python "${CODE_PATH}/scripts/python/run_multienv_qwen3vl_interactive.py" \
    --provider_name docker \
    --path_to_vm "${PATH_TO_VM}" \
    --headless \
    --num_envs "${NUM_ENVS}" \
    --max_steps "${MAX_STEPS}" \
    --model "${MODEL_NAME}" \
    --temperature "${TEMPERATURE}" \
    --top_p "${TOP_P}" \
    --max_tokens "${MAX_TOKENS}" \
    --coord "${COORD}" \
    --history_n "${HISTORY_N}" \
    --api_backend "${API_BACKEND}" \
    --platform "${PLATFORM}" \
    --thinking_budget "${THINKING_BUDGET}" \
    ${THINKING_ARG} \
    ${TAIJI_ARG} \
    --result_dir "${RESULT_ROOT}" \
    --run_name "${RUN_NAME}" \
    --test_all_meta_path "${TEST_META_PATH}" \
    --test_config_base_dir "${TEST_CONFIG_BASE_DIR}" \
    --sleep_after_execution "${SLEEP_AFTER_EXECUTION}" \
    --log_level "${LOG_LEVEL}" \
    --user_base_url "${USER_BASE_URL}" \
    --user_api_key "${USER_API_KEY}" \
    --user_model "${USER_MODEL}" \
    --user_temperature "${USER_TEMPERATURE}" \
    2>&1 | tee -a "${LOG_FILE}"
