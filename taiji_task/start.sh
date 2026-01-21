# start.sh
# sleep 365d 仅允许在debug情况下使用sleep，禁止使用sleep命令占卡后提交正式任务

bash $(dirname "$0")/install_taiji_client.sh

# base dir
DATA_PATH="/apdcephfs_fsgm/share_304220499/chenxuwu"
MODEL_PATH="${DATA_PATH}/models/models--ByteDance-Seed--UI-TARS-1.5-7B"

# set AWS env vars to avoid import error (not actually using AWS)
export AWS_REGION="us-east-1"
export AWS_SUBNET_ID="subnet-dummy"
export AWS_SECURITY_GROUP_ID="sg-dummy"

# set DOUBAO API env vars (使用本地 vLLM 服务)
export DOUBAO_API_KEY="EMPTY"
export DOUBAO_API_URL="http://localhost:8000/v1/chat/completions"

# 1. prepare model file
mkdir -p ~/.cache/huggingface/hub
cp -r ${DATA_PATH}/models/models--ByteDance-Seed--UI-TARS-1.5-7B ~/.cache/huggingface/hub/

# 2. OSWorld code
cd ${DATA_PATH}/code/OSWorld

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

# 10. start vLLM server
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

# # 11. run OSWorld evaluation with docker provider, network on, 5 envs
python ${DATA_PATH}/code/OSWorld/run_multienv_uitars15_v2.py \
    --provider_name docker \
    --headless \
    --num_envs 3 \
    --model "UI-TARS-1.5-7B"
