#!/bin/bash
# run_kimi.sh
# 顺序运行两个 Kimi K2.5 评测任务：先跑 non-interactive，完成后再跑 interactive

SCRIPT_DIR=$(dirname "$0")

echo "=========================================="
echo "  Step 1/2: Kimi K2.5 Non-Interactive"
echo "=========================================="
bash "${SCRIPT_DIR}/start_kimi_k25.sh"
EXIT_CODE=$?
echo "=========================================="
echo "  Step 1/2 finished (exit code: ${EXIT_CODE})"
echo "=========================================="

echo "=========================================="
echo "  Step 2/2: Kimi K2.5 Interactive"
echo "=========================================="
bash "${SCRIPT_DIR}/start_kimi_k25_interactive.sh"
EXIT_CODE=$?
echo "=========================================="
echo "  Step 2/2 finished (exit code: ${EXIT_CODE})"
echo "=========================================="

echo "All Kimi K2.5 evaluations done."
