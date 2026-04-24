#!/bin/bash
# 顺序执行 interactive 评测：
# 1) start_r3agentv3_interactive.sh
# 2) start_kimi_k25_interactive.sh
#
# 用法:
#   bash taiji_task/start_r3_then_kimi_interactive.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
R3_SCRIPT="${SCRIPT_DIR}/start_r3agentv3_interactive.sh"
KIMI_SCRIPT="${SCRIPT_DIR}/start_kimi_k25_interactive.sh"

echo "[1/2] Running: ${R3_SCRIPT}"
bash "${R3_SCRIPT}"
echo "[1/2] Finished successfully."
docker ps -aq | xargs -r docker rm -f
echo "[2/2] Running: ${KIMI_SCRIPT}"
bash "${KIMI_SCRIPT}"
echo "[2/2] Finished successfully."

echo "All interactive jobs finished."
