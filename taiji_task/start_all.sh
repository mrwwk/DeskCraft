#!/bin/bash
# start_kdenlive.sh
# EvoCUA Kdenlive 评测脚本
# VM 环境: docker_vm_data/new_env/Ubuntu.qcow2 (relative path)
# sleep 365d 仅允许在debug情况下使用sleep，禁止使用sleep命令占卡后提交正式任务

bash $(dirname "$0")/install_taiji_client.sh

# code dir，这里修改一下到自己的文件夹，
CODE_PATH="/cq_1/share_300000800/user/jackwkwang"


# 这里不用修改～已经下载好了
DATA_PATH="/apdcephfs/jp_fsgm_cephfs3/apdcephfs_fsgm/share_304220499/chenxuwu"
MODEL_PATH="/cq_1/share_300000800/user/jackwkwang/models/UI-TARS-1.5-7B"

# set AWS env vars to avoid import error (not actually using AWS)
export AWS_REGION="us-east-1"
export AWS_SUBNET_ID="subnet-dummy"
export AWS_SECURITY_GROUP_ID="sg-dummy"

# set DOUBAO API env vars (本地 vLLM 服务，不使用 DOUBAO API)，不设置会报错

export OPENAI_API_KEY="EMPTY"
export OPENAI_BASE_URL="http://localhost:8000/v1"

# 1. prepare model file
mkdir -p ~/.cache/huggingface/hub
#cp -r ${DATA_PATH}/models/models--ByteDance-Seed--UI-TARS-1.5-7B ~/.cache/huggingface/hub/

# 2. OSWorld code
cd ${CODE_PATH}/code/OSWorld

# 3. prepare osworld cache file
# if [ ! -d "cache" ]; then
#     cp -r ${DATA_PATH}/data/osworld_cache.zip ./osworld_cache.zip
#     unzip -q osworld_cache.zip && mv osworld_cache cache && rm -rf osworld_cache.zip
# fi

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
#cp -r ${DATA_PATH}/data/osworld_image.tar ./osworld_image.tar
docker load -i osworld_image.tar
# rm -f osworld_image.tar

# 7. activate osworld virtual environment
. /workspace/osworld/bin/activate

# 8. prepare VM data
mkdir -p docker_vm_data
# if [ ! -f "docker_vm_data/Ubuntu.qcow2" ]; then
#     cp -r ${DATA_PATH}/data/Ubuntu.qcow2.zip ./docker_vm_data/
#     cd docker_vm_data && unzip -q Ubuntu.qcow2.zip && rm -f Ubuntu.qcow2.zip && cd ..
# fi

# # 9. test run
# python quickstart.py --provider_name docker --headless True

# wait for vLLM server to be ready
echo "Waiting for vLLM server to be ready..."
while ! curl -s http://localhost:8000/health > /dev/null 2>&1; do
    sleep 10
    echo "Still waiting for vLLM server..."
done
echo "vLLM server is ready!"

# 12. run Kdenlive evaluation with EvoCUA
LOG_DIR="${CODE_PATH}/code/OSWorld/logs/taiji_task"
mkdir -p "${LOG_DIR}"
LOG_FILE="${LOG_DIR}/run_kdenlive_$(date +%Y%m%d_%H%M%S).log"
echo "Logging to: ${LOG_FILE}"
export PLAYWRIGHT_BROWSERS_PATH=/cq_1/share_300000800/user/jackwkwang/pw-browsers
python ${CODE_PATH}/code/OSWorld/run_multienv_evocua.py \
    --provider_name docker \
    --test_config_base_dir evaluation_examples/example_final \
    --headless \
    --path_to_vm docker_vm_data/new_env/Ubuntu.qcow2 \
    --run_name EvoCUA-32B-20260105-not_interactive_final \
    --num_envs 5 \
    --max_steps 100 \
    --model "EvoCUA-32B-20260105" \
    --coordinate_type relative \
    --prompt_style S2 \
    --max_history_turns 4 \
    --resize_factor 32 \
    --temperature 0.01 \
    --max_tokens 32768 \
    --test_all_meta_path evaluation_examples/example_final_non_interactive_all.json 2>&1 | tee -a "${LOG_FILE}"
# /apdcephfs/hunyuanaidjpsh2/jp_sh2_cephfs/apdcephfs_sh2/share_300000800/user/jackwkwang/code/OSWorld/evaluation_examples/
# /apdcephfs/hunyuanaidjpsh2/jp_sh2_cephfs/apdcephfs_sh2/share_300000800/user/jackwkwang/code/OSWorld/evaluation_examples/
# /apdcephfs/hunyuanaidjpsh2/jp_sh2_cephfs/apdcephfs_sh2/share_300000800/user/jackwkwang/code/OSWorld/evaluation_examples/
