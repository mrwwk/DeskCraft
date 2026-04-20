#!/bin/bash
# start_kimi_k25_eval.sh
# Kimi K2.5 OSWorld 评测脚本（连接远程已部署的 vLLM 服务）
#
# 此脚本不启动本地 vLLM，而是连接由 deploy/kimi_k25.sh 部署的远程模型服务。
#
# 用法示例:
#   VLLM_HOST=29.185.89.157 bash ip_scripts/start_kimi_k25_eval.sh
#   VLLM_HOST=29.185.89.157 THINKING=true NUM_ENVS=5 bash ip_scripts/start_kimi_k25_eval.sh

bash $(dirname "$0")/../install_taiji_client.sh

# ============ 远程模型服务配置 ============
VLLM_HOST="${VLLM_HOST:?请设置 VLLM_HOST 环境变量，指向 deploy/kimi_k25.sh 部署的 master 节点 IP}"
VLLM_PORT="${VLLM_PORT:-8000}"
MODEL_NAME="${MODEL_NAME:-Kimi-K2.5}"

# ============ 采样参数 ============
TEMPERATURE="${TEMPERATURE:-1.0}"
TOP_P="${TOP_P:-0.95}"
MAX_TOKENS="${MAX_TOKENS:-4096}"

# ============ 评测参数 ============
NUM_ENVS="${NUM_ENVS:-5}"
MAX_STEPS="${MAX_STEPS:-100}"
THINKING="${THINKING:-true}"

# ============ 路径前缀 ============
PATH_PREFIX="${PATH_PREFIX:-/apdcephfs_fsgm/share_304220499}"

# ============ 路径配置 ============
CODE_PATH="${CODE_PATH:-${PATH_PREFIX}/chenxuwu/osworld_wzj_code/OSWorld}"
DATA_PATH="${DATA_PATH:-${PATH_PREFIX}/chenxuwu}"

# 本地工作目录
LOCAL_WORK_DIR="${LOCAL_WORK_DIR:-/data/workspace/OSWorld_local/OSWorld}"
# 结果回传目标目录
RESULT_TARGET_DIR="${RESULT_TARGET_DIR:-${PATH_PREFIX}/chenxuwu/code1/OSWorld/results}"

# 环境变量
export AWS_REGION="us-east-1"
export AWS_SUBNET_ID="subnet-dummy"
export AWS_SECURITY_GROUP_ID="sg-dummy"
export OPENAI_API_KEY="EMPTY"
export OPENAI_BASE_URL="http://${VLLM_HOST}:${VLLM_PORT}/v1"

echo "========== Remote vLLM Configuration =========="
echo "VLLM_HOST=${VLLM_HOST}"
echo "VLLM_PORT=${VLLM_PORT}"
echo "OPENAI_BASE_URL=${OPENAI_BASE_URL}"
echo "MODEL_NAME=${MODEL_NAME}"
echo "========== Eval Configuration =========="
echo "NUM_ENVS=${NUM_ENVS}"
echo "MAX_STEPS=${MAX_STEPS}"
echo "THINKING=${THINKING}"
echo "TEMPERATURE=${TEMPERATURE}"
echo "TOP_P=${TOP_P}"
echo "MAX_TOKENS=${MAX_TOKENS}"
echo "========================================"

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

# 安装 openai 客户端
pip install openai -q

# 准备 VM 数据
mkdir -p docker_vm_data
if [ ! -f "docker_vm_data/Ubuntu.qcow2" ]; then
    cp -r ${DATA_PATH}/data/Ubuntu.qcow2.zip ./docker_vm_data/
    cd docker_vm_data && unzip -q Ubuntu.qcow2.zip && rm -f Ubuntu.qcow2.zip && cd ..
fi

# 测试 Docker VM
python quickstart.py --provider_name docker --headless True

# GPU 占用（防止空闲被回收）
echo "Starting GPU occupy script..."
python ${LOCAL_WORK_DIR}/gpu_occupy.py &
GPU_OCCUPY_PID=$!
echo "GPU occupy script started with PID: ${GPU_OCCUPY_PID}"

# 等待远程 vLLM 服务就绪
echo "========== Waiting for remote vLLM server at ${VLLM_HOST}:${VLLM_PORT} =========="

# 清除代理（确保直连远程 vLLM）
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
export no_proxy=localhost,127.0.0.1,28.33.*,29.185.*,${VLLM_HOST}

# 诊断：测试网络连通性
echo "[诊断] 测试到 ${VLLM_HOST} 的网络连通性..."
ping -c 2 -W 3 ${VLLM_HOST} 2>&1 || echo "[警告] ping 不通，可能是防火墙限制，继续尝试 HTTP..."
echo "[诊断] curl 测试 (--noproxy 强制直连，显示详细信息)..."
curl -v --noproxy '*' --max-time 10 "http://${VLLM_HOST}:${VLLM_PORT}/health" 2>&1 || true

MAX_WAIT="${MAX_WAIT_VLLM:-3600}"
WAITED=0
while true; do
    HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' --noproxy '*' --max-time 10 "http://${VLLM_HOST}:${VLLM_PORT}/health" 2>/dev/null)
    if [ "$HTTP_CODE" = "200" ]; then
        break
    fi
    sleep 10
    WAITED=$((WAITED + 10))
    echo "Still waiting for remote vLLM server... (${WAITED}s / ${MAX_WAIT}s) [last HTTP code: ${HTTP_CODE}]"
    if [ ${WAITED} -ge ${MAX_WAIT} ]; then
        echo "[错误] 等待远程 vLLM 服务超时 (${MAX_WAIT}s)，请检查 deploy/kimi_k25.sh 部署任务是否正常运行"
        curl -v --noproxy '*' --max-time 10 "http://${VLLM_HOST}:${VLLM_PORT}/health" 2>&1 || true
        exit 1
    fi
done
echo "Remote vLLM server is ready!"

# 验证模型可用
echo "========== Checking remote model =========="
curl -s --noproxy '*' "http://${VLLM_HOST}:${VLLM_PORT}/v1/models" | head -200
echo ""

# 设置代理（评测需要访问外网下载评测数据等）
export http_proxy=http://hk-mmhttpproxy.woa.com:11113/
export https_proxy=http://hk-mmhttpproxy.woa.com:11113/
export no_proxy=localhost,127.0.0.1,28.33.*,29.185.*,${VLLM_HOST}

# 构建 thinking 参数
THINKING_ARG=""
if [ "${THINKING}" = "true" ]; then
    THINKING_ARG="--thinking"
fi

echo "========== Running ${MODEL_NAME} evaluation =========="

# 运行评测
echo "OPENAI_BASE_URL=${OPENAI_BASE_URL}"
PYTHONPATH=. python ${LOCAL_WORK_DIR}/run_multienv_kimi_k25.py \
    --provider_name docker \
    --headless \
    --observation_type screenshot \
    --num_envs ${NUM_ENVS} \
    --max_steps ${MAX_STEPS} \
    --model "${MODEL_NAME}" \
    --temperature ${TEMPERATURE} \
    --top_p ${TOP_P} \
    --max_tokens ${MAX_TOKENS} \
    --api_base "${OPENAI_BASE_URL}" \
    ${THINKING_ARG} \
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
