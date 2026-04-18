#!/usr/bin/env python3
"""
测试 KimiK25 thinking / no-thinking 模式下的响应结构。
打印 content 和 reasoning_content 的原始值，方便确认哪个字段携带回复。

用法:
    python test_thinking_mode.py
"""

import json
import requests

BASE_URL = "http://28.12.129.142:8000/v1"
MODEL    = "KimiK25"
API_KEY  = "EMPTY"
URL      = f"{BASE_URL}/chat/completions"
HEADERS  = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

MESSAGES = [
    {"role": "user", "content": "Say hello in one sentence."}
]

def call(label: str, extra_body: dict | None = None):
    print(f"\n{'='*55}")
    print(f"  场景: {label}")
    print(f"{'='*55}")
    payload = {
        "model": MODEL,
        "messages": MESSAGES,
        "temperature": 0.6,
        "max_tokens": 256,
    }
    if extra_body:
        payload["extra_body"] = extra_body

    resp = requests.post(URL, headers=HEADERS, json=payload, timeout=60)
    print(f"  HTTP status : {resp.status_code}")

    try:
        data = resp.json()
    except Exception:
        print(f"  ✗ 非 JSON 响应: {resp.text[:300]}")
        return

    if "choices" not in data:
        print(f"  ✗ 无 choices 字段，完整响应:")
        print(json.dumps(data, ensure_ascii=False, indent=2)[:600])
        return

    msg = data["choices"][0]["message"]
    content           = msg.get("content")
    reasoning_content = msg.get("reasoning_content")

    print(f"  content           = {repr(content)[:300]}")
    print(f"  reasoning_content = {repr(reasoning_content)[:300]}")
    print(f"  finish_reason     = {data['choices'][0].get('finish_reason')}")


# 场景 1：不传任何 extra_body（默认行为）
call("默认（不传 thinking 参数）")

# 场景 2：显式禁用 thinking
call("no-think: thinking disabled", extra_body={"thinking": {"type": "disabled"}})

# 场景 3：显式开启 thinking（budget 较小加速测试）
call("think: thinking enabled (budget=512)", extra_body={"thinking": {"type": "enabled", "budget_tokens": 512}})
