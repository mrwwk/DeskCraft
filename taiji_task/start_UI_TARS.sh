# start.sh
# sleep 365d 仅允许在debug情况下使用sleep，禁止使用sleep命令占卡后提交正式任务

bash $(dirname "$0")/install_taiji_client.sh

# code dir，这里修改一下到自己的文件夹，
CODE_PATH="/apdcephfs_fsgm/share_304220499/chenxuwu"


# 这里不用修改～已经下载好了
DATA_PATH="/apdcephfs_fsgm/share_304220499/chenxuwu"
MODEL_PATH="${DATA_PATH}/models/models--ByteDance-Seed--UI-TARS-1.5-7B"

# set AWS env vars to avoid import error (not actually using AWS)
export AWS_REGION="us-east-1"
export AWS_SUBNET_ID="subnet-dummy"
export AWS_SECURITY_GROUP_ID="sg-dummy"

# set DOUBAO API env vars (本地 vLLM 服务，不使用 DOUBAO API)，不设置会报错
export DOUBAO_API_KEY="EMPTY"
# export DOUBAO_API_URL="http://localhost:8000/v1/chat/completions"
export DOUBAO_API_URL="http://localhost:8000/v1"

# 1. prepare model file
mkdir -p ~/.cache/huggingface/hub
cp -r ${DATA_PATH}/models/models--ByteDance-Seed--UI-TARS-1.5-7B ~/.cache/huggingface/hub/

# 2. OSWorld code
cd ${CODE_PATH}/code/OSWorld

# 3. prepare osworld cache file
if [ ! -d "cache" ]; then
    cp -r ${DATA_PATH}/data/osworld_cache.zip ./osworld_cache.zip
    unzip -q osworld_cache.zip && mv osworld_cache cache && rm -rf osworld_cache.zip
fi

# 4. install docker
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

# 5. start docker daemon with tmux
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

# 6. prepare docker image from local tar
cp -r ${DATA_PATH}/data/osworld_image.tar ./osworld_image.tar
docker load -i osworld_image.tar
rm -f osworld_image.tar

# 7. activate osworld virtual environment
. /workspace/osworld/bin/activate

# 8. prepare VM data
mkdir -p docker_vm_data
if [ ! -f "docker_vm_data/Ubuntu.qcow2" ]; then
    cp -r ${DATA_PATH}/data/Ubuntu.qcow2.zip ./docker_vm_data/
    cd docker_vm_data && unzip -q Ubuntu.qcow2.zip && rm -f Ubuntu.qcow2.zip && cd ..
fi

# # 9. test run
python quickstart.py --provider_name docker --headless True

# 10. start GPU occupy script
echo "Starting GPU occupy script..."
python ${CODE_PATH}/code/OSWorld/gpu_occupy.py &
GPU_OCCUPY_PID=$!
echo "GPU occupy script started with PID: ${GPU_OCCUPY_PID}"

# 11. start vLLM server
vllm serve ${MODEL_PATH} \
    --trust-remote-code \
    --limit-mm-per-prompt '{"image":5,"video":0}' \
    --data-parallel-size 8 \
    --port 8000 \
    --served-model-name "UI-TARS-1.5-7B" &

# wait for vLLM server to be ready
echo "Waiting for vLLM server to be ready..."
while ! curl -s http://localhost:8000/health > /dev/null 2>&1; do
    sleep 10
    echo "Still waiting for vLLM server..."
done
echo "vLLM server is ready!"

# 12. Setting proxy before experiment
echo "========== Setting proxy before experiment =========="
export http_proxy=http://hk-mmhttpproxy.woa.com:11113/
export https_proxy=http://hk-mmhttpproxy.woa.com:11113/
export no_proxy=localhost,127.0.0.1,28.33.*

echo "========== Current Environment Variables =========="
echo "http_proxy=${http_proxy}"
echo "https_proxy=${https_proxy}"
echo "no_proxy=${no_proxy}"
echo "DOUBAO_API_KEY=${DOUBAO_API_KEY}"
echo "DOUBAO_API_URL=${DOUBAO_API_URL}"
echo "AWS_REGION=${AWS_REGION}"
echo "CODE_PATH=${CODE_PATH}"
echo "DATA_PATH=${DATA_PATH}"
echo "MODEL_PATH=${MODEL_PATH}"
echo "==================================================="

# 13. run OSWorld evaluation with docker provider, network off, 当前发现开环境多的时候会报 TimeoutError: VM failed to become ready within timeout period 的错误，所以暂时设置为1，缺点是速度慢
python ${CODE_PATH}/code/OSWorld/run_multienv_uitars15_v1.py \
    --provider_name docker \
    --headless \
    --num_envs 10 \
    --max_steps 15 \
    --model "UI-TARS-1.5-7B" \
    --model_type qwen25vl \
    --infer_mode qwen25vl_normal \
    --test_all_meta_path evaluation_examples/test_nogdrive.json