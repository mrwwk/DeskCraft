#!/bin/bash
# 用于启动 osworld 任务的脚本
# Usage: ./run_osworld_task.sh <IP_ADDRESS> <PORT> <TASK_NAME> <LOCAL_RESULT_DIR> <MODEL_NAME> <MAX_STEP>
# 注意：LOCAL_RESULT_DIR 是本地临时结果目录（在volume映射的目录内），任务完成后需要移动到远程目录

IP_ADDRESS=$1
PORT=$2
TASK_NAME=$3
LOCAL_RESULT_DIR=$4  # 本地临时结果目录（在Docker内可访问）
MODEL_NAME=$5
MAX_STEP=$6

# 切换到脚本所在目录（OSWorld 目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

# 设置环境变量
export OPENAI_BASE_URL="http://${IP_ADDRESS}:${PORT}/v1"
# export GET_OBS_BEFORE_ACTION=1

# 使用本地临时结果目录（在volume映射的目录内，Docker可以访问）
RESULT_DIR="${LOCAL_RESULT_DIR}"
mkdir -p "$RESULT_DIR"
echo "结果将保存到本地临时目录: $RESULT_DIR"

# 运行 osworld 任务
python run_multienv_qwen3vl.py \
  --provider_name docker \
  --test_all_meta_path evaluation_examples/test_small.json \
  --headless \
  --max_steps "$MAX_STEP" \
  --domain all \
  --num_envs 5 \
  --result_dir "$RESULT_DIR" \
  --log_level INFO \
  --sleep_after_execution 3 \
  --model "$MODEL_NAME"
