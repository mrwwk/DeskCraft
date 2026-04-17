# start_evocua_interactive.sh
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

# set OPENAI API env vars (由于EvoCUA使用OpenAI Compatible API调用VLLM或者其他模型服务)
export OPENAI_API_KEY="EMPTY"
export OPENAI_BASE_URL="http://localhost:8000/v1"

# 1. prepare model file
mkdir -p ~/.cache/huggingface/hub

# 2. OSWorld code
cd ${CODE_PATH}/code/OSWorld

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

# # 9. test run
python quickstart.py --provider_name docker --headless True

# wait for your local LLM server to be ready (if using local VLLM)
echo "Waiting for LLM server to be ready..."
while ! curl -s http://localhost:8000/health > /dev/null 2>&1; do
    sleep 10
    echo "Still waiting for LLM server..."
done
echo "LLM server is ready!"

# 12. run OSWorld iterative evaluation with docker provider
# Create log directory and set up logging
LOG_DIR="${CODE_PATH}/code/OSWorld/logs/taiji_task"
mkdir -p "${LOG_DIR}"
LOG_FILE="${LOG_DIR}/run_evocua_interactive_$(date +%Y%m%d_%H%M%S).log"
echo "Logging to: ${LOG_FILE}"
export PLAYWRIGHT_BROWSERS_PATH=/cq_1/share_300000800/user/jackwkwang/pw-browsers
# Call the interactive task pipeline using user_base_url
#     --test_all_meta_path evaluation_examples/example_final_interactive_all.json \
python ${CODE_PATH}/code/OSWorld/run_multienv_evocua_interactive.py \
    --test_all_meta_path evaluation_examples/example_final_interactive_all.json \
    --test_config_base_dir evaluation_examples/example_final \
    --provider_name docker \
    --headless \
    --run_name EvoCUA-32B-20260105-interactive_final5 \
    --path_to_vm docker_vm_data/new_env/Ubuntu.qcow2 \
    --num_envs 7 \
    --max_steps 100 \
    --model "EvoCUA-32B-20260105" \
    --prompt_style S2 \
    --max_history_turns 4 \
    --coordinate_type relative \
    --resize_factor 32 \
    --user_base_url "http://29.160.43.141:8000/v1" \
    --user_api_key "EMPTY" \
    --user_model "Qwen3.5-122B-A10B" 2>&1 | tee -a "${LOG_FILE}"
