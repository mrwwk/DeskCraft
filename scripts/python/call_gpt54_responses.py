#!/usr/bin/env python3
"""GPT-5.4 Responses API example script.

This keeps the existing run scripts untouched and provides a standalone
Responses-style invocation example for manual validation.

Supported auth modes:
- Standard OpenAI-compatible: `OPENAI_API_KEY`
- NACI bearer pair: `APP_ID` + `APP_KEY`
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict, List

from openai import OpenAI


DEFAULT_BASE_URL = "http://llm-api.model-eval.woa.com"
DEFAULT_MODEL = "api_azure_openai_gpt-5.4"


def normalize_base_url(base_url: str) -> str:
    base_url = base_url.rstrip("/")
    if not base_url.endswith("/v1"):
        base_url = base_url + "/v1"
    return base_url


def build_client() -> OpenAI:
    base_url = normalize_base_url(os.getenv("OPENAI_BASE_URL", DEFAULT_BASE_URL))
    openai_api_key = os.getenv("OPENAI_API_KEY")
    app_id = os.getenv("APP_ID")
    app_key = os.getenv("APP_KEY")

    if app_id and app_key:
        return OpenAI(
            base_url=base_url,
            api_key="EMPTY",
            default_headers={"Authorization": f"Bearer {app_id}:{app_key}"},
        )

    if openai_api_key:
        return OpenAI(base_url=base_url, api_key=openai_api_key)

    print("请先设置 OPENAI_API_KEY，或者同时设置 APP_ID 和 APP_KEY。", file=sys.stderr)
    sys.exit(1)


def extract_text(response: Any) -> str:
    text = getattr(response, "output_text", None)
    if text:
        return text

    output = getattr(response, "output", []) or []
    parts: List[str] = []
    for item in output:
        if getattr(item, "type", None) == "message":
            for content in getattr(item, "content", []) or []:
                if getattr(content, "type", None) in {"output_text", "text"}:
                    value = getattr(content, "text", "")
                    if value:
                        parts.append(value)
    return "\n".join(parts)


def print_response(title: str, response: Any) -> None:
    print(f"=== {title} ===")
    print("response_id:", getattr(response, "id", ""))
    print("status:", getattr(response, "status", ""))
    usage = getattr(response, "usage", None)
    if usage is not None:
        print("usage:", getattr(usage, "model_dump", lambda: usage)())
    print("text:", extract_text(response))
    print()


def main() -> None:
    client = build_client()
    model = os.getenv("MODEL", DEFAULT_MODEL)

    response1 = client.responses.create(
        model=model,
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "你好，请回复 OK"},
                ],
            }
        ],
    )
    print_response("1. 最小请求对话", response1)

    response2 = client.responses.create(
        model=model,
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "这张图有什么？"},
                    {
                        "type": "input_image",
                        "image_url": "https://via.placeholder.com/300.png",
                    },
                ],
            }
        ],
    )
    print_response("2. 图片输入", response2)

    response3 = client.responses.create(
        model=model,
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "北京今天天气怎么样？"},
                ],
            }
        ],
        tools=[
            {
                "type": "function",
                "name": "get_weather",
                "description": "获取城市天气",
                "parameters": {
                    "type": "object",
                    "properties": {"city": {"type": "string"}},
                    "required": ["city"],
                },
            }
        ],
    )
    print_response("3. 工具调用", response3)

    response4a = client.responses.create(
        model=model,
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "我的名字叫小明。"},
                ],
            }
        ],
    )
    response4b = client.responses.create(
        model=model,
        previous_response_id=response4a.id,
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "请重复一下我的名字。"},
                ],
            }
        ],
    )
    print_response("4. 多轮对话", response4b)


if __name__ == "__main__":
    main()
