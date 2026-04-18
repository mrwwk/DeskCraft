#!/usr/bin/env python3
"""
验证 User Simulator 模型是否能正常连通并响应。

用法:
    python test_user_model.py
    python test_user_model.py --base_url http://28.12.129.142:8000/v1 --model KimiK25
"""

import argparse
import base64
import json
import sys
import time

import requests

# ──────────────────────────── 默认配置 ────────────────────────────
DEFAULT_BASE_URL = "http://28.12.129.142:8000/v1"
DEFAULT_MODEL    = "KimiK25"
DEFAULT_API_KEY  = "EMPTY"
TIMEOUT          = 30  # 秒


def check_health(base_url: str) -> bool:
    """检查 /health 端点是否可达"""
    url = base_url.rstrip("/").rsplit("/v1", 1)[0] + "/health"
    print(f"[1/4] 检查健康端点: {url}")
    try:
        resp = requests.get(url, timeout=TIMEOUT)
        if resp.status_code == 200:
            print(f"      ✓ /health 返回 200")
            return True
        else:
            print(f"      ✗ /health 返回 {resp.status_code}: {resp.text[:200]}")
            return False
    except Exception as e:
        print(f"      ✗ 无法连接: {e}")
        return False


def check_models(base_url: str, api_key: str, expected_model: str) -> bool:
    """检查 /models 端点，确认目标模型已加载"""
    url = base_url.rstrip("/") + "/models"
    print(f"[2/4] 获取模型列表: {url}")
    try:
        resp = requests.get(
            url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=TIMEOUT,
        )
        if resp.status_code != 200:
            print(f"      ✗ 返回 {resp.status_code}: {resp.text[:200]}")
            return False
        data = resp.json()
        models = [m["id"] for m in data.get("data", [])]
        print(f"      可用模型: {models}")
        if expected_model in models:
            print(f"      ✓ 找到目标模型: {expected_model}")
            return True
        else:
            # 有些服务 model id 不完全一致，给出提示但不直接失败
            print(f"      ⚠ 未精确匹配 '{expected_model}'，将继续尝试推理调用")
            return True  # 允许继续测试
    except Exception as e:
        print(f"      ✗ 请求失败: {e}")
        return False


def check_text_chat(base_url: str, api_key: str, model: str) -> bool:
    """纯文本对话：验证基础推理能力"""
    url = base_url.rstrip("/") + "/chat/completions"
    print(f"[3/4] 纯文本推理测试: {url}")
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant. Reply in JSON."},
            {
                "role": "user",
                "content": (
                    'Reply with exactly this JSON (no extra text): '
                    '{"action":"new_instruction","message":"hello","phase_complete":false}'
                ),
            },
        ],
        "temperature": 0,
        "max_tokens": 256,
    }
    try:
        t0 = time.time()
        resp = requests.post(
            url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=TIMEOUT,
        )
        elapsed = time.time() - t0
        if resp.status_code != 200:
            print(f"      ✗ 返回 {resp.status_code}: {resp.text[:300]}")
            return False
        content = resp.json()["choices"][0]["message"]["content"]
        print(f"      模型回复 ({elapsed:.1f}s): {content[:200]}")
        # 尝试解析 JSON
        try:
            parsed = json.loads(content.strip())
            print(f"      ✓ JSON 解析成功: action={parsed.get('action')}, phase_complete={parsed.get('phase_complete')}")
        except json.JSONDecodeError:
            print(f"      ⚠ 回复不是标准 JSON，但推理本身成功")
        return True
    except Exception as e:
        print(f"      ✗ 请求失败: {e}")
        return False


def _make_test_png_b64(width: int = 64, height: int = 64) -> str:
    """
    纯 Python 生成一张 width×height 的白色 PNG（无需 Pillow）。
    MoonViT-3D 需要足够大的图片，1×1 会触发处理错误。
    """
    import struct, zlib

    def chunk(tag: bytes, data: bytes) -> bytes:
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    sig  = b"\x89PNG\r\n\x1a\n"
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    # 每行：滤波字节 0x00 + RGB×width（全白）
    raw  = (b"\x00" + b"\xff\xff\xff" * width) * height
    idat = chunk(b"IDAT", zlib.compress(raw, 9))
    iend = chunk(b"IEND", b"")
    return base64.b64encode(sig + ihdr + idat + iend).decode()


def check_vision_chat(base_url: str, api_key: str, model: str) -> bool:
    """
    多模态（图文）对话：验证视觉输入能力。
    修复要点：
      1. 使用 64×64 PNG 而非 1×1，满足 MoonViT-3D 最小分辨率要求
      2. 先文字后图片（官方示例顺序）
      3. 兼容推理模型（reasoning_content / content 均可能携带回复）
      4. 禁用 thinking 模式加快测试速度
    """
    url = base_url.rstrip("/") + "/chat/completions"
    print(f"[4/4] 多模态（vision）测试: {url}")

    img_b64 = _make_test_png_b64(64, 64)
    print(f"      测试图片: 64×64 白色 PNG ({len(img_b64)} bytes base64)")

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    # 官方示例：文字在前，图片在后
                    {"type": "text", "text": "What color is the background of this image? Reply in one word."},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
                ],
            }
        ],
        "temperature": 0.6,
        "max_tokens": 128,
        # 关闭推理模式，加快测试速度；KimiK25 reasoning 模型支持此参数
        "extra_body": {"thinking": {"type": "disabled"}},
    }
    try:
        t0 = time.time()
        resp = requests.post(
            url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=60,  # vision 推理比纯文本慢，给足时间
        )
        elapsed = time.time() - t0
        print(f"      HTTP {resp.status_code} ({elapsed:.1f}s)")

        try:
            resp_json = resp.json()
        except Exception:
            print(f"      ✗ 响应不是合法 JSON: {resp.text[:400]}")
            return False

        if resp.status_code != 200 or "choices" not in resp_json:
            err = resp_json.get("error", resp_json)
            print(f"      ✗ 响应缺少 'choices'，错误详情:")
            print(f"      {json.dumps(err, ensure_ascii=False, indent=2)[:600]}")
            return False

        msg = resp_json["choices"][0]["message"]
        # 推理模型：content 可能为 None，真正回复在 reasoning_content
        content          = msg.get("content") or ""
        reasoning_content = msg.get("reasoning_content") or ""

        if content:
            print(f"      content          : {content[:200]}")
        if reasoning_content:
            print(f"      reasoning_content: {reasoning_content[:200]}")

        if content or reasoning_content:
            print(f"      ✓ 多模态调用成功")
            return True
        else:
            print(f"      ✗ content 和 reasoning_content 均为空，完整 message: {msg}")
            return False

    except Exception as e:
        print(f"      ✗ 请求异常: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="验证 User Simulator 模型连通性")
    parser.add_argument("--base_url", default=DEFAULT_BASE_URL, help="API base URL")
    parser.add_argument("--model",    default=DEFAULT_MODEL,    help="模型名称")
    parser.add_argument("--api_key",  default=DEFAULT_API_KEY,  help="API Key")
    args = parser.parse_args()

    print("=" * 60)
    print(f"  User Model 连通性验证")
    print(f"  base_url : {args.base_url}")
    print(f"  model    : {args.model}")
    print("=" * 60)

    results = {}

    results["health"]      = check_health(args.base_url)
    results["models"]      = check_models(args.base_url, args.api_key, args.model)
    results["text_chat"]   = check_text_chat(args.base_url, args.api_key, args.model)
    results["vision_chat"] = check_vision_chat(args.base_url, args.api_key, args.model)

    print()
    print("=" * 60)
    print("  检测结果汇总")
    print("=" * 60)
    all_pass = True
    for name, ok in results.items():
        status = "✓ PASS" if ok else "✗ FAIL"
        print(f"  {status}  {name}")
        if not ok:
            all_pass = False

    print()
    if all_pass:
        print("  ✅ 所有检查通过，User Model 可正常使用！")
        sys.exit(0)
    else:
        print("  ❌ 存在失败项，请检查服务状态或模型配置。")
        sys.exit(1)


if __name__ == "__main__":
    main()
