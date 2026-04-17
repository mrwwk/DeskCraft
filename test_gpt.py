#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""标准协议调用示例：POST /v1/chat/completions（Azure GPT-5.4 异步）"""

import sys
import requests

APP_ID = "m1gjTHxx_jackwkwang"
APP_KEY = "tM1urhJTxl7KFSyo"
BASE_URL = "http://llm-api.model-eval.woa.com"
MODEL = "api_azure_openai_gpt-5-nano"

URL = BASE_URL.rstrip("/") + "/v1/chat/completions"
HEADERS = {"Content-Type": "application/json", "Authorization": f"Bearer {APP_ID}:{APP_KEY}"}


def call(body):
    r = requests.post(URL, headers=HEADERS, json=body, timeout=300)
    return r.status_code, r.json() if r.text else None


def main():
    if not APP_ID or not APP_KEY:
        print("请先填写 APP_ID、APP_KEY。", file=sys.stderr)
        sys.exit(1)

    # 1. 最小请求对话
    print("=== 1. 最小请求对话 ===")
    status, data = call({"model": MODEL, "messages": [{"role": "user", "content": "你好，请回复 OK"}], "stream": False})
    print("status:", status)
    if data and data.get("choices"):
        print("输出:", data["choices"][0].get("message"))
    else:
        print("响应:", data)
    print()

    # 2. 图片输入
    print("=== 2. 图片输入 ===")
    body2 = {
        "model": MODEL,
        "messages": [{"role": "user", "content": [{"type": "text", "text": "这张图有什么？"}, {"type": "image_url", "image_url": {"url": "https://via.placeholder.com/300.png"}}]}],
        "stream": False,
    }
    status, data = call(body2)
    print("status:", status)
    if data and data.get("choices"):
        print("输出:", data["choices"][0].get("message"))
    else:
        print("响应:", data)
    print()

    # 3. 工具调用
    print("=== 3. 工具调用 ===")
    body3 = {
        "model": MODEL,
        "messages": [{"role": "user", "content": "北京今天天气怎么样？"}],
        "stream": False,
        "tools": [{"type": "function", "function": {"name": "get_weather", "description": "获取城市天气", "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}}}],
        "tool_choice": "auto",
    }
    status, data = call(body3)
    print("status:", status)
    if data and data.get("choices"):
        print("输出:", data["choices"][0].get("message"))
    else:
        print("响应:", data)
    print()

    # 4. 多轮对话
    print("=== 4. 多轮对话 ===")
    body4 = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": "我的名字叫小明。"},
            {"role": "assistant", "content": "你好小明。"},
            {"role": "user", "content": "请重复一下我的名字。"},
        ],
        "stream": False,
    }
    status, data = call(body4)
    print("status:", status)
    if data and data.get("choices"):
        print("输出:", data["choices"][0].get("message"))
    else:
        print("响应:", data)


if __name__ == "__main__":
    main()
# from openai import OpenAI

# client = OpenAI(base_url="http://localhost:8000/v1", api_key="empty")

# response = client.chat.completions.create(
#     model="EvoCUA-32B-20260105",
#     messages=[{"role": "user", "content": "帮我搜索一下今天的天气"}],
#     tools=[{
#         "type": "function",
#         "function": {
#             "name": "ai_search__10__160",
#             "description": "智能搜索引擎",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "keyword": {"type": "string", "description": "搜索关键词"}
#                 },
#                 "required": ["keyword"]
#             }
#         }
#     }]
# )

# print(response)
