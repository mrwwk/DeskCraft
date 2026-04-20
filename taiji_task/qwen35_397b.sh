export NCCL_IB_TIMEOUT=24
export NCCL_IB_GID_INDEX=3
export NCCL_IB_SL=3
export NCCL_CHECK_DISABLE=1
export NCCL_P2P_DISABLE=0
export NCCL_IB_DISABLE=0
export NCCL_LL_THRESHOLD=16384
export NCCL_IB_CUDA_SUPPORT=1
export NCCL_SOCKET_IFNAME=bond1
export UCX_NET_DEVICES=bond1
export NCCL_IB_HCA=mlx5_bond_1,mlx5_bond_5,mlx5_bond_3,mlx5_bond_7,mlx5_bond_4,mlx5_bond_8,mlx5_bond_2,mlx5_bond_6
export NCCL_COLLNET_ENABLE=0
export SHARP_COLL_ENABLE_SAT=0
export NCCL_NET_GDR_LEVEL=2
export NCCL_IB_QPS_PER_CONNECTION=4
export NCCL_IB_TC=160
export NCCL_PXN_DISABLE=1
export NCCL_NVLS_ENABLE=0

clear

# ========== 多节点环境变量适配 ==========
# 探测 RANK / INDEX
if [ -n "$INDEX" ]; then
    RANK=$INDEX
elif [ -n "$RANK" ]; then
    RANK=$RANK
elif [ -n "$OMPI_COMM_WORLD_RANK" ]; then
    RANK=$OMPI_COMM_WORLD_RANK
elif [ -n "$PMI_RANK" ]; then
    RANK=$PMI_RANK
else
    RANK=0
fi

# 探测主节点 IP
if [ -n "$NODE_IP_0" ]; then
    MASTER_IP=$NODE_IP_0
elif [ -n "$MASTER_ADDR" ]; then
    MASTER_IP=$MASTER_ADDR
elif [ -n "$CHIEF_IP" ]; then
    MASTER_IP=$CHIEF_IP
else
    MASTER_IP=""
fi

# 探测本节点 IP
if [ -n "$LOCAL_IP" ]; then
    MY_IP=$LOCAL_IP
elif [ -n "$POD_IP" ]; then
    MY_IP=$POD_IP
else
    MY_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
fi

echo "========== Multi-node info =========="
echo "RANK=$RANK"
echo "MASTER_IP=$MASTER_IP"
echo "MY_IP=$MY_IP"
echo "====================================="

if [ -z "$MASTER_IP" ] || [ -z "$MY_IP" ]; then
    echo "[错误] 无法确定 MASTER_IP 或 MY_IP"
    echo "所有环境变量:"
    env | sort
    exit 1
fi

DIST_INIT_ADDR="${MASTER_IP}:29500"

#CONTEXT_LENGTH=262144
CONTEXT_LENGTH=32768
#sglang serve --model-path /root/local_hubs/Qwen35/Qwen3.5-397B-A17B \
#  --tensor-parallel-size 8 \
#  --pipeline-parallel-size 4 \
#  --context-length $CONTEXT_LENGTH \
#  --mem-fraction-static 0.4 \
#  --host $LOCAL_IP \
#  --port 8080 \
#  --nnodes 4 \
#  --node-rank $RANK \
#  --dist-init-addr $DIST_INIT_ADDR


. /workspace/osworld/bin/activate

# GPU 占用脚本（防止空闲被回收）
GPU_OCCUPY_SCRIPT="/tmp/gpu_occupy.py"
cat > ${GPU_OCCUPY_SCRIPT} << 'PYEOF'
import time
import subprocess
import torch
import threading

def get_gpu_utilization(gpu_id):
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu', '--format=csv,noheader,nounits', '-i', str(gpu_id)],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            return None
        return int(result.stdout.strip())
    except Exception:
        return None

def tensor_multiplication(gpu_id):
    while not stop_tensor_multiplication[gpu_id]:
        a = torch.randn(1000, 2000, device=f'cuda:{gpu_id}')
        b = torch.randn(2000, 1000, device=f'cuda:{gpu_id}')
        c = torch.matmul(a, b)

def monitor_gpu(gpu_id):
    global stop_tensor_multiplication
    tensor_thread = None
    low_utilization_counter = 0
    while True:
        utilization = get_gpu_utilization(gpu_id)
        if utilization is not None:
            if utilization < 10:
                low_utilization_counter += 1
            else:
                low_utilization_counter = 0
            if low_utilization_counter >= 1 and (tensor_thread is None or not tensor_thread.is_alive()):
                stop_tensor_multiplication[gpu_id] = False
                tensor_thread = threading.Thread(target=tensor_multiplication, args=(gpu_id,))
                tensor_thread.start()
            elif utilization > 20 and tensor_thread is not None and tensor_thread.is_alive():
                stop_tensor_multiplication[gpu_id] = True
                tensor_thread.join()
                tensor_thread = None
        time.sleep(1)

if __name__ == "__main__":
    stop_tensor_multiplication = [False] * 8
    for gpu_id in range(8):
        threading.Thread(target=monitor_gpu, args=(gpu_id,), daemon=True).start()
    while True:
        time.sleep(60)
PYEOF

echo "Starting GPU occupy script..."
python ${GPU_OCCUPY_SCRIPT} &
GPU_OCCUPY_PID=$!
echo "GPU occupy script started with PID: ${GPU_OCCUPY_PID}"

if [ "$MY_IP" == "$MASTER_IP" ]; then
  vllm serve /root/local_hubs/Qwen35/Qwen3.5-397B-A17B \
  --tensor-parallel-size 8 \
  --pipeline-parallel-size 4 \
  --reasoning-parser qwen3 \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_coder \
  --host $MY_IP \
  --port 9090 \
  --nnodes 4 \
  --node-rank $RANK \
  --master-addr $MASTER_IP
else
  vllm serve /root/local_hubs/Qwen35/Qwen3.5-397B-A17B \
  --tensor-parallel-size 8 \
  --pipeline-parallel-size 4 \
  --reasoning-parser qwen3 \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_coder \
  --host $MY_IP \
  --port 9090 \
  --nnodes 4 \
  --node-rank $RANK \
  --master-addr $MASTER_IP \
  --headless
fi