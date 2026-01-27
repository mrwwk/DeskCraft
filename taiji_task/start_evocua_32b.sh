# start_evocua_32b.sh
# EvoCUA-32B OSWorld 评测脚本
# sleep 365d 仅允许在debug情况下使用sleep，禁止使用sleep命令占卡后提交正式任务

bash $(dirname "$0")/install_taiji_client.sh

# code dir，这里修改一下到自己的文件夹
CODE_PATH="/apdcephfs_fsgm/share_304220499/chenxuwu"

# 数据和模型路径
DATA_PATH="/apdcephfs_fsgm/share_304220499/chenxuwu"
MODEL_PATH="/apdcephfs_fsgm/share_304220499/model/EvoCUA-32B-20260105"

# set AWS env vars to avoid import error (not actually using AWS)
export AWS_REGION="us-east-1"
export AWS_SUBNET_ID="subnet-dummy"
export AWS_SECURITY_GROUP_ID="sg-dummy"

# set OpenAI API env vars (本地 vLLM 服务)
export OPENAI_API_KEY="EMPTY"
export OPENAI_BASE_URL="http://localhost:8000/v1"

# 1. OSWorld code
cd ${CODE_PATH}/code/OSWorld

# 2. prepare osworld cache file
if [ ! -d "cache" ]; then
    cp -r ${DATA_PATH}/data/osworld_cache.zip ./osworld_cache.zip
    unzip -q osworld_cache.zip && mv osworld_cache cache && rm -rf osworld_cache.zip
fi

# 3. install docker
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    # 配置腾讯云镜像源
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

# 4. start docker daemon with tmux
tmux new-session -d -s docker 'dockerd --storage-driver=vfs'
# wait for docker daemon to be ready
echo "Waiting for Docker daemon to be ready..."
while ! docker info > /dev/null 2>&1; do
    sleep 2
done
echo "Docker daemon is ready!"

# 清理残留的 osworld 容器
echo "Cleaning up old containers..."
docker ps -a --filter "ancestor=osworld" -q | xargs -r docker rm -f 2>/dev/null || true

# 5. prepare docker image from local tar
cp -r ${DATA_PATH}/data/osworld_image.tar ./osworld_image.tar
docker load -i osworld_image.tar
rm -f osworld_image.tar

# 6. activate osworld virtual environment
. /workspace/osworld/bin/activate

# 7. prepare VM data
mkdir -p docker_vm_data
if [ ! -f "docker_vm_data/Ubuntu.qcow2" ]; then
    cp -r ${DATA_PATH}/data/Ubuntu.qcow2.zip ./docker_vm_data/
    cd docker_vm_data && unzip -q Ubuntu.qcow2.zip && rm -f Ubuntu.qcow2.zip && cd ..
fi

# 8. test run
python quickstart.py --provider_name docker --headless True

# 9. start GPU occupy script
echo "Starting GPU occupy script..."
python ${CODE_PATH}/code/OSWorld/gpu_occupy.py &
GPU_OCCUPY_PID=$!
echo "GPU occupy script started with PID: ${GPU_OCCUPY_PID}"

# 10. start vLLM server for EvoCUA-32B (8卡部署)
echo "Starting vLLM server for EvoCUA-32B..."
vllm serve ${MODEL_PATH} \
    --trust-remote-code \
    --limit-mm-per-prompt '{"image":5,"video":0}' \
    --tensor-parallel-size 8 \
    --port 8000 \
    --served-model-name "EvoCUA-32B" &

# wait for vLLM server to be ready
echo "Waiting for vLLM server to be ready..."
while ! curl -s http://localhost:8000/health > /dev/null 2>&1; do
    sleep 10
    echo "Still waiting for vLLM server..."
done
echo "vLLM server is ready!"

# 11. 实验开始前重新设置代理并打印环境变量
echo "========== Setting proxy before experiment =========="
export http_proxy=http://hk-mmhttpproxy.woa.com:11113/
export https_proxy=http://hk-mmhttpproxy.woa.com:11113/
export no_proxy=localhost,127.0.0.1,28.33.*

echo "========== Current Environment Variables =========="
echo "http_proxy=${http_proxy}"
echo "https_proxy=${https_proxy}"
echo "no_proxy=${no_proxy}"
echo "OPENAI_API_KEY=${OPENAI_API_KEY}"
echo "OPENAI_BASE_URL=${OPENAI_BASE_URL}"
echo "AWS_REGION=${AWS_REGION}"
echo "CODE_PATH=${CODE_PATH}"
echo "DATA_PATH=${DATA_PATH}"
echo "MODEL_PATH=${MODEL_PATH}"
echo "==================================================="

# 12. run OSWorld evaluation with docker provider
python ${CODE_PATH}/code/OSWorld/run_multienv_evocua.py \
    --provider_name docker \
    --headless \
    --num_envs 5 \
    --max_steps 50 \
    --model "EvoCUA-32B" \
    --coordinate_type relative \
    --prompt_style S2 \
    --max_history_turns 4 \
    --resize_factor 32 \
    --temperature 0.01 \
    --max_tokens 32768 \
    --test_all_meta_path evaluation_examples/test_nogdrive.json
