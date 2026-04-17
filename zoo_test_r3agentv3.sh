#!/bin/bash
# zoo_launch_r3agentv3_test.sh
# R3AgentV3 评测脚本

# ============ 区域选择 ============
# REGION=wzj  -> /apdcephfs_wzj/share_304937439/ailab_data
# REGION=gz   -> /apdcephfs_fsgm/share_304220499
# REGION=zw   -> /apdcephfs_zwfy11/share_304220499/weixian
REGION="zw"
PATH_PREFIX=""  # 后面根据 REGION 自动设置

# ============ 代码源配置 ============
# 默认从共享存储拷贝代码（外租卡无法访问 git.woa.com）
CODE_SOURCE=""  # 后面根据 REGION 自动设置
LOCAL_CODE_DIR="/workspace/OSWorld"  # 容器本地代码目录

# ============ 默认值配置 ============
# 模型配置
MODEL_NAME="Qwen3-VL-4B-Instruct"

# 采样参数 (与 run_multienv_r3agentv3.py 默认值一致)
TEMPERATURE=0             # default=0
TOP_P=0.9                 # default=0.9
MAX_TOKENS=32768          # default=32768

# R3AgentV3 特有参数
HISTORY_N=3               # 历史消息数量 (default=3)
PROMPT_TYPE="l1"          # 提示词类型: l1, l2 (default=l1)
COORD="relative"          # 坐标类型: absolute, relative (default=relative)
ADD_THOUGHT_PREFIX=""     # 是否添加思考前缀 (空或 "--add_thought_prefix")

# 评测参数
NUM_ENVS=5                # 并行环境数，这个数量比较稳定
MAX_STEPS=15              # 每个任务最大步数 (R3AgentV3 默认为15)
TEST_ALL_META_PATH="evaluation_examples/test_nogdrive.json"  # 测试元数据路径
RESULT_DIR="/apdcephfs_zwfy11/share_304220499/weixian/exp/osworld_results"      # 结果保存目录

# vLLM 部署参数
TENSOR_PARALLEL_SIZE=1    # tensor parallel size
DATA_PARALLEL_SIZE=8      # data parallel size (>1 时启用数据并行)

# 路径配置 (默认为空，后面根据 REGION 自动设置)
DATA_PATH=""
MODEL_PATH=""
# =========================================

# ============ 命令行参数解析 ============
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --model-name NAME           模型名称 (default: Qwen3-VL-4B-Instruct)"
    echo "  --temperature TEMP          采样温度 (default: 0)"
    echo "  --top-p VALUE               Top-p 采样 (default: 0.9)"
    echo "  --max-tokens NUM            最大 token 数 (default: 32768)"
    echo "  --history-n NUM             历史消息数量 (default: 3)"
    echo "  --prompt-type TYPE          提示词类型: l1, l2, l3 (default: l1)"
    echo "  --coord TYPE                坐标类型: absolute, relative (default: relative)"
    echo "  --add-thought-prefix        添加思考前缀"
    echo "  --num-envs NUM              并行环境数 (default: 5)"
    echo "  --max-steps NUM             每个任务最大步数 (default: 15)"
    echo "  --test-all-meta-path PATH   测试元数据路径 (default: evaluation_examples/test_nogdrive.json)"
    echo "  --result-dir DIR            结果保存目录 (default: results)"
    echo "  --tensor-parallel-size NUM  Tensor parallel size (default: 1)"
    echo "  --data-parallel-size NUM    Data parallel size (default: 8)"
    echo "  --region REGION             区域: wzj, gz, zw (default: zw)"
    echo "  --code-source PATH          代码源路径 (默认根据 region 自动生成)"
    echo "  --local-code-dir PATH       本地代码目录 (default: /workspace/OSWorld)"
    echo "  --data-path PATH            数据路径"
    echo "  --model-path PATH           模型路径 (默认根据 model-name 自动生成)"
    echo "  -h, --help                  显示帮助信息"
    exit 0
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --model-name)
            MODEL_NAME="$2"
            shift 2
            ;;
        --temperature)
            TEMPERATURE="$2"
            shift 2
            ;;
        --top-p)
            TOP_P="$2"
            shift 2
            ;;
        --max-tokens)
            MAX_TOKENS="$2"
            shift 2
            ;;
        --history-n)
            HISTORY_N="$2"
            shift 2
            ;;
        --prompt-type)
            PROMPT_TYPE="$2"
            shift 2
            ;;
        --coord)
            COORD="$2"
            shift 2
            ;;
        --add-thought-prefix)
            ADD_THOUGHT_PREFIX="--add_thought_prefix"
            shift
            ;;
        --test-all-meta-path)
            TEST_ALL_META_PATH="$2"
            shift 2
            ;;
        --num-envs)
            NUM_ENVS="$2"
            shift 2
            ;;
        --max-steps)
            MAX_STEPS="$2"
            shift 2
            ;;
        --result-dir)
            RESULT_DIR="$2"
            shift 2
            ;;
        --tensor-parallel-size)
            TENSOR_PARALLEL_SIZE="$2"
            shift 2
            ;;
        --data-parallel-size)
            DATA_PARALLEL_SIZE="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --code-source)
            CODE_SOURCE="$2"
            shift 2
            ;;
        --local-code-dir)
            LOCAL_CODE_DIR="$2"
            shift 2
            ;;
        --data-path)
            DATA_PATH="$2"
            shift 2
            ;;
        --model-path)
            MODEL_PATH="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# 根据 REGION 设置 PATH_PREFIX
case "${REGION}" in
    wzj) PATH_PREFIX="/apdcephfs_wzj/share_304937439/ailab_data" ;;
    gz)  PATH_PREFIX="/apdcephfs_fsgm/share_304220499" ;;
    zw)  PATH_PREFIX="/apdcephfs_zwfy11/share_304220499/weixian" ;;
    *)   echo "[错误] 未知 REGION: ${REGION}，仅支持 wzj, gz 或 zw"; exit 1 ;;
esac

# 如果路径未指定，则根据 PATH_PREFIX 自动生成
if [ "${REGION}" = "zw" ]; then
    # zw 区域使用独立的路径结构
    if [ -z "${CODE_SOURCE}" ]; then
        CODE_SOURCE="${PATH_PREFIX}/code/OSWorld"
    fi
    if [ -z "${DATA_PATH}" ]; then
        DATA_PATH="${PATH_PREFIX}"
    fi
    if [ -z "${MODEL_PATH}" ]; then
        MODEL_PATH="${PATH_PREFIX}/ckpt/${MODEL_NAME}"
    fi
else
    # wzj/gz 区域使用原有的路径结构
    SHARED_PATH="${PATH_PREFIX}/chenxuwu"  # 共享存储路径（只读数据）
    if [ -z "${CODE_SOURCE}" ]; then
        if [ "${REGION}" = "gz" ]; then
            CODE_SOURCE="/apdcephfs_fsgm/share_304220499/weixian/code/OSWorld"
        else
            CODE_SOURCE="${PATH_PREFIX}/chenxuwu/osworld_wzj_code/OSWorld"
        fi
    fi
    if [ -z "${DATA_PATH}" ]; then
        DATA_PATH="${SHARED_PATH}"
    fi
    if [ -z "${MODEL_PATH}" ]; then
        MODEL_PATH="${PATH_PREFIX}/model/${MODEL_NAME}"
    fi
fi
# =========================================



#从此开始不需要修改

# 环境变量
export AWS_REGION="us-east-1"
export AWS_SUBNET_ID="subnet-dummy"
export AWS_SECURITY_GROUP_ID="sg-dummy"
export OPENAI_API_KEY="EMPTY"
export OPENAI_BASE_URL="http://localhost:8000/v1"

# 拷贝 OSWorld 代码到容器本地目录（隔离）
echo "========== Copying code from ${CODE_SOURCE} =========="
cp -r "${CODE_SOURCE}" "${LOCAL_CODE_DIR}"
cd ${LOCAL_CODE_DIR}
CODE_PATH="${LOCAL_CODE_DIR}"
echo "CODE_PATH=${CODE_PATH}"

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
#python ${CODE_PATH}/gpu_occupy.py &

# 启动 vLLM
echo "Starting vLLM server with ${MODEL_NAME} (TP=${TENSOR_PARALLEL_SIZE}, DP=${DATA_PARALLEL_SIZE})..."
VLLM_DP_ARGS=""
if [ "${DATA_PARALLEL_SIZE}" -gt 1 ]; then
    VLLM_DP_ARGS="--data-parallel-size ${DATA_PARALLEL_SIZE}"
fi
vllm serve ${MODEL_PATH} \
    --trust-remote-code \
    --limit-mm-per-prompt '{"image":5,"video":0}' \
    --tensor-parallel-size ${TENSOR_PARALLEL_SIZE} \
    ${VLLM_DP_ARGS} \
    --port 8000 \
    --served-model-name "${MODEL_NAME}" &

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
            vllm serve ${MODEL_PATH} \
                --trust-remote-code \
                --limit-mm-per-prompt '{"image":5,"video":0}' \
                --tensor-parallel-size ${TENSOR_PARALLEL_SIZE} \
                ${VLLM_DP_ARGS} \
                --port 8000 \
                --served-model-name "${MODEL_NAME}" &
            sleep 120
        fi
    done
) &

# 设置代理 (根据 REGION 选择不同的代理)
case "${REGION}" in
    wzj)
        export http_proxy=http://star-proxy.oa.com:3128/
        export https_proxy=http://star-proxy.oa.com:3128/
        export no_proxy=localhost,127.0.0.1,28.33.*
        ;;
    gz|zw)
        export http_proxy=http://hk-mmhttpproxy.woa.com:11113/
        export https_proxy=http://hk-mmhttpproxy.woa.com:11113/
        export no_proxy=localhost
        ;;
esac

echo "========== Running R3AgentV3 with ${MODEL_NAME} =========="
echo "Prompt Type: ${PROMPT_TYPE}"
echo "History N: ${HISTORY_N}"
echo "Coordinate: ${COORD}"

# 运行评测
python ${CODE_PATH}/run_multienv_r3agentv3.py \
    --provider_name docker \
    --headless \
    --num_envs ${NUM_ENVS} \
    --max_steps ${MAX_STEPS} \
    --model "${MODEL_NAME}" \
    --temperature ${TEMPERATURE} \
    --top_p ${TOP_P} \
    --max_tokens ${MAX_TOKENS} \
    --history_n ${HISTORY_N} \
    --prompt_type ${PROMPT_TYPE} \
    --coord ${COORD} \
    ${ADD_THOUGHT_PREFIX} \
    --region ${REGION} \
    --test_all_meta_path ${TEST_ALL_META_PATH} \
    --sleep_after_execution 5 \
    --result_dir ${RESULT_DIR}
