# start_new_env.sh - Load new environment from docker_vm_data/new_env/Ubuntu.qcow2
# sleep 365d 仅允许在debug情况下使用sleep，禁止使用sleep命令占卡后提交正式任务

bash $(dirname "$0")/install_taiji_client.sh

# code dir，这里修改一下到自己的文件夹
CODE_PATH="/cq_1/share_300000800/user/jackwkwang"

# 这里不用修改～已经下载好了
DATA_PATH="/apdcephfs/jp_fsgm_cephfs3/apdcephfs_fsgm/share_304220499/chenxuwu"
MODEL_PATH="/cq_1/share_300000800/user/jackwkwang/models/UI-TARS-1.5-7B"

# New environment VM path
NEW_VM_PATH="${CODE_PATH}/code/OSWorld/docker_vm_data/new_env/Ubuntu.qcow2"

# set AWS env vars to avoid import error (not actually using AWS)
export AWS_REGION="us-east-1"
export AWS_SUBNET_ID="subnet-dummy"
export AWS_SECURITY_GROUP_ID="sg-dummy"

# set DOUBAO API env vars (本地 vLLM 服务，不使用 DOUBAO API)，不设置会报错
export DOUBAO_API_KEY="EMPTY"
export DOUBAO_API_URL="http://localhost:8000/v1/chat/completions"

# 1. prepare model file
mkdir -p ~/.cache/huggingface/hub

# 2. OSWorld code
cd ${CODE_PATH}/code/OSWorld

# 3. check new env VM image exists
if [ ! -f "${NEW_VM_PATH}" ]; then
    echo "ERROR: New environment image not found at ${NEW_VM_PATH}"
    echo "Please ensure the qcow2 file exists before running."
    exit 1
fi
echo "Using new VM image: ${NEW_VM_PATH}"

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
docker load -i osworld_image.tar

# 7. activate osworld virtual environment
. /workspace/osworld/bin/activate

# 8. test run with new env VM path
python quickstart_blender.py --provider_name docker --headless True --path_to_vm "${NEW_VM_PATH}"


# 9. start GPU occupy script
