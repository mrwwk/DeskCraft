#!/bin/bash
IP_ADDRESS=$1
PORT=$2
TASK_NAME=$3
TARGET_DIR=$4
MODEL_NAME=$5
MAX_STEP=$6
TASK_COMPLETE_FILE=$7  # 任务完成标记文件路径

if [ -z "$IP_ADDRESS" ] || [ -z "$PORT" ] || [ -z "$TASK_NAME" ] || [ -z "$TARGET_DIR" ] || [ -z "$MODEL_NAME" ] || [ -z "$MAX_STEP" ] || [ -z "$TASK_COMPLETE_FILE" ]; then
    echo "Usage: $0 <IP_ADDRESS> <PORT> <TASK_NAME> <TARGET_DIR> <MODEL_NAME> <MAX_STEP> <TASK_COMPLETE_FILE>"
    exit 1
fi

echo "IP_ADDRESS: $IP_ADDRESS"
echo "PORT: $PORT"
echo "TASK_NAME: $TASK_NAME"
echo "TARGET_DIR: $TARGET_DIR"
echo "MODEL_NAME: $MODEL_NAME"
echo "MAX_STEP: $MAX_STEP"
echo "TASK_COMPLETE_FILE: $TASK_COMPLETE_FILE"

# 设置错误处理：任何命令失败时退出
set -e

# 任务执行函数
run_task() {
    # 在这里执行你的实际任务
    # 例如：运行你的模型训练、评估等
    echo "开始执行任务: $TASK_NAME"
    
    # 测试模型API是否可访问
    echo "=========================================="
    echo "测试模型API连接: http://${IP_ADDRESS}:${PORT}/v1/models"
    echo "=========================================="
    
    # 使用curl测试API，设置超时时间为10秒
    API_URL="http://${IP_ADDRESS}:${PORT}/v1/models"
    TEMP_RESPONSE_FILE="/tmp/api_test_response_${TASK_NAME}_$$.json"
    
    # 执行curl请求，捕获HTTP状态码和响应
    HTTP_CODE=$(curl -s -o "$TEMP_RESPONSE_FILE" -w "%{http_code}" --max-time 10 --connect-timeout 5 "$API_URL" 2>&1)
    CURL_EXIT_CODE=$?
    
    # 检查curl是否执行成功
    if [ $CURL_EXIT_CODE -ne 0 ]; then
        echo "错误: 无法连接到模型API"
        echo "curl退出码: $CURL_EXIT_CODE"
        echo "请检查:"
        echo "  1. IP地址和端口是否正确: ${IP_ADDRESS}:${PORT}"
        echo "  2. 模型服务是否正在运行"
        echo "  3. 网络连接是否正常"
        rm -f "$TEMP_RESPONSE_FILE"
        return 1
    fi
    
    # 检查HTTP状态码
    if [ -z "$HTTP_CODE" ] || [ "$HTTP_CODE" != "200" ]; then
        echo "错误: 模型API返回错误状态码"
        echo "HTTP状态码: ${HTTP_CODE:-'未知'}"
        if [ -f "$TEMP_RESPONSE_FILE" ]; then
            echo "响应内容:"
            cat "$TEMP_RESPONSE_FILE"
            echo ""
        fi
        rm -f "$TEMP_RESPONSE_FILE"
        return 1
    fi
    
    # 检查响应文件是否存在且不为空
    if [ ! -f "$TEMP_RESPONSE_FILE" ] || [ ! -s "$TEMP_RESPONSE_FILE" ]; then
        echo "错误: API响应为空"
        rm -f "$TEMP_RESPONSE_FILE"
        return 1
    fi
    
    # 检查响应是否为有效的JSON
    if ! python3 -m json.tool "$TEMP_RESPONSE_FILE" > /dev/null 2>&1; then
        echo "错误: API响应不是有效的JSON格式"
        echo "响应内容:"
        cat "$TEMP_RESPONSE_FILE"
        echo ""
        rm -f "$TEMP_RESPONSE_FILE"
        return 1
    fi
    
    echo "✓ 模型API连接成功"
    echo "✓ HTTP状态码: 200"
    echo "✓ 响应为有效JSON格式"
    echo ""
    echo "API响应预览:"
    python3 -m json.tool "$TEMP_RESPONSE_FILE" | head -30
    echo ""
    echo "=========================================="
    
    # 清理临时文件
    rm -f "$TEMP_RESPONSE_FILE"
    
    # 验证模型是否在 API 中可用
    echo "=========================================="
    echo "验证模型是否在 API 中可用: $MODEL_NAME"
    echo "=========================================="
    SCRIPT_DIR="$(dirname "$0")"
    if ! python3 "$SCRIPT_DIR/check_model_available.py" "$IP_ADDRESS" "$PORT" "$MODEL_NAME"; then
        echo "错误: 模型验证失败，任务终止"
        return 1
    fi
    echo "=========================================="
    echo ""
    
    # 使用外部定义的 LOCAL_RESULT_DIR（在函数外部已创建）
    # 确保目录存在
    mkdir -p "$LOCAL_RESULT_DIR"
    
    echo "本地临时结果目录: $LOCAL_RESULT_DIR"
    echo "目标远程目录: $TARGET_DIR"
    
    # 调用 osworld 任务脚本（使用本地临时结果目录）
    "$(dirname "$0")/run_osworld_task.sh" "$IP_ADDRESS" "$PORT" "$TASK_NAME" "$LOCAL_RESULT_DIR" "$MODEL_NAME" "$MAX_STEP"
    
    echo "任务执行完成: $TASK_NAME"
    echo "结果已保存到: $LOCAL_RESULT_DIR"
}

# 执行任务（在try-catch中执行，确保即使失败也创建标记文件）
# 注意：LOCAL_RESULT_DIR 需要在函数外部定义，以便在完成标记文件中记录
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOCAL_RESULT_BASE_DIR="$(dirname "$(dirname "$TASK_COMPLETE_FILE")")/temp_results"
LOCAL_RESULT_DIR="${LOCAL_RESULT_BASE_DIR}/${TASK_NAME}_${TIMESTAMP}"

if run_task; then
    # 任务成功完成
    # 在完成标记文件中记录本地结果目录和目标远程目录，以便后续移动
    echo "{\"status\": \"success\", \"completed_at\": \"$(date -Iseconds)\", \"task_name\": \"$TASK_NAME\", \"local_result_dir\": \"$LOCAL_RESULT_DIR\", \"target_dir\": \"$TARGET_DIR\"}" > "$TASK_COMPLETE_FILE"
    echo "任务成功完成，标记文件已创建: $TASK_COMPLETE_FILE"
    echo "本地结果目录: $LOCAL_RESULT_DIR"
    echo "目标远程目录: $TARGET_DIR"
    exit 0
else
    # 任务执行失败
    EXIT_CODE=$?
    # 即使失败也记录路径信息，以便清理或调试
    echo "{\"status\": \"failed\", \"completed_at\": \"$(date -Iseconds)\", \"task_name\": \"$TASK_NAME\", \"exit_code\": $EXIT_CODE, \"local_result_dir\": \"$LOCAL_RESULT_DIR\", \"target_dir\": \"$TARGET_DIR\"}" > "$TASK_COMPLETE_FILE"
    echo "任务执行失败，退出码: $EXIT_CODE"
    echo "本地结果目录: $LOCAL_RESULT_DIR"
    exit $EXIT_CODE
fi