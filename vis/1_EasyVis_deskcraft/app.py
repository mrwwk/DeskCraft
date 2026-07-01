"""
EasyVis DeskCraft - GUI Task Visualizer
Browse DeskCraft standard and interactive task definitions with agent trajectories.
"""

import os
import json
import glob
import uuid
import base64
import hashlib
import hmac
import datetime
import argparse
import logging
import requests as http_requests
from flask import Flask, send_from_directory, send_file, jsonify, request

from trajectory_service import load_trajectory, resolve_result_task_dir, _safe_path
from label_service import LABEL_FILENAME, load_all_labels, save_label, delete_label, label_path_for_task

app = Flask(__name__, static_folder="static")
logger = logging.getLogger("easyvis")
DEFAULTS_PATH = ""

# ─── LLM Configuration ( - Internal GPT API) ────────────────────────
LLM_CONFIG = {
    "provider": "openai",  # "openai" (蒸馏平台) or "kimi" (Kimi-K2.6) or "vllm" (OpenAI-compatible)
    # 蒸馏平台配置
    "openai": {
        "host": "http://trpc-gpt-eval.production.polaris:8080",
        "api_id": "6n6hsQrx_weixianlei",
        "api_key": "ataKyzIS8rYeJ6WY",
        "model_marker": "api_azure_openai_gpt-5.4-pro-2026-03-05",
        "timeout": 300,
    },
    # Kimi-K2.6 配置
    "kimi": {
        "base_url": "http://28.7.186.40:9090/v1",
        "model_name": "kimi_k26",
        "api_key": "EMPTY",
        "timeout": 300,
    },
    # vLLM / OpenAI-compatible 备选配置
    "vllm": {
        "base_url": "http://127.0.0.1:8080/v1",
        "model_name": "Qwen3-VL-235B-A22B-Instruct",
        "api_key": "EMPTY",
        "timeout": 120,
    },
    "max_tokens": 4096,
    "temperature": 0.3,
}


def _get_hmac_auth(source: str, secret_id: str, secret_key: str):
    """Generate HMAC-SHA1 authentication for internal GPT API."""
    date_time = datetime.datetime.now(datetime.timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')
    auth = f'hmac id="{secret_id}", algorithm="hmac-sha1", headers="date source", signature="'
    sign_str = f"date: {date_time}\nsource: {source}"
    sign = hmac.new(secret_key.encode(), sign_str.encode(), hashlib.sha1).digest()
    sign = base64.b64encode(sign).decode()
    return auth + sign + '"', date_time


def call_llm_openai_platform(system_prompt: str, user_prompt: str) -> str:
    """Call LLM via  (Internal GPT API with HMAC auth)."""
    cfg = LLM_CONFIG["openai"]
    source = "gpt_eval"
    sign, date_time = _get_hmac_auth(source, cfg["api_id"], cfg["api_key"])

    headers = {
        "Content-Type": "application/json",
        "Apiversion": "v2.03",
        "Authorization": sign,
        "Date": date_time,
        "Source": source,
    }

    # Build message content
    content = [
        {"type": "text", "value": f"{system_prompt}\n\n{user_prompt}"},
    ]

    payload = {
        "request_id": str(uuid.uuid4()),
        "model_marker": cfg["model_marker"],
        "messages": [{"role": "user", "content": content}],
        "params": {},
        "timeout": 6000,
    }

    url = f"{cfg['host']}/api/v1/data_eval"
    resp = http_requests.post(url, headers=headers, json=payload, timeout=cfg["timeout"])

    if resp.status_code != 200:
        raise Exception(f"API request failed: HTTP {resp.status_code} - {resp.text[:200]}")

    result = resp.json()
    if result.get("code") != 0:
        raise Exception(f"API error (code={result.get('code')}): {result.get('msg', 'unknown')}")

    raw_response = result.get("answer", [{}])[0].get("value", "")
    return raw_response


def call_llm_vllm(system_prompt: str, user_prompt: str) -> str:
    """Call LLM via vLLM / OpenAI-compatible API."""
    cfg = LLM_CONFIG["vllm"]
    url = f"{cfg['base_url']}/chat/completions"
    headers = {"Content-Type": "application/json"}
    if cfg["api_key"] and cfg["api_key"] != "EMPTY":
        headers["Authorization"] = f"Bearer {cfg['api_key']}"

    payload = {
        "model": cfg["model_name"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": LLM_CONFIG["max_tokens"],
        "temperature": LLM_CONFIG["temperature"],
    }

    resp = http_requests.post(url, headers=headers, json=payload, timeout=cfg["timeout"])
    resp.raise_for_status()
    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    # Strip thinking tags if present (Qwen3 style)
    if content and "<think>" in content and "</think>" in content:
        content = content.split("</think>")[-1].strip()
    return content or ""


def call_llm_kimi(system_prompt: str, user_prompt: str) -> str:
    """Call Kimi-K2.6 via OpenAI-compatible API (with reasoning support)."""
    cfg = LLM_CONFIG["kimi"]
    url = f"{cfg['base_url']}/chat/completions"
    headers = {"Content-Type": "application/json"}
    if cfg["api_key"] and cfg["api_key"] != "EMPTY":
        headers["Authorization"] = f"Bearer {cfg['api_key']}"

    payload = {
        "model": cfg["model_name"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": LLM_CONFIG["max_tokens"],
        "temperature": LLM_CONFIG["temperature"],
    }

    resp = http_requests.post(url, headers=headers, json=payload, timeout=cfg["timeout"])
    resp.raise_for_status()
    data = resp.json()
    msg = data["choices"][0]["message"]
    # Kimi-K2.6: content has the final answer, reasoning has the thinking process
    content = msg.get("content") or ""
    # If content is empty but reasoning exists, use reasoning as fallback
    if not content.strip() and msg.get("reasoning"):
        content = msg["reasoning"]
    return content.strip()


def call_llm(system_prompt: str, user_prompt: str) -> str:
    """Unified LLM call dispatcher."""
    try:
        provider = LLM_CONFIG["provider"]
        if provider == "openai":
            return call_llm_openai_platform(system_prompt, user_prompt)
        elif provider == "kimi":
            return call_llm_kimi(system_prompt, user_prompt)
        elif provider == "vllm":
            return call_llm_vllm(system_prompt, user_prompt)
        else:
            return f"[LLM Error] Unknown provider: {provider}"
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        return f"[LLM Error] {str(e)}"


# ─── Prompt Templates ────────────────────────────────────────────────────────

PROMPTS = {
    "translate_instruction": {
        "zh": "请将以下GUI Agent任务指令翻译为中文。保持原意，直接输出翻译结果，不加解释。",
        "en": "Translate the following GUI Agent task instruction into English. Preserve original meaning, output translation directly, no explanation.",
    },
    "describe_config": {
        "zh": """请简洁分析这个GUI task的config是否为task执行提供了必要的环境初始化。

背景：
- config的作用是初始化环境（如准备文件、启动应用、设置系统状态等），为task的执行提供前置条件
- config执行完毕后，Agent才开始在此环境中通过鼠标/键盘完成instruction
- 本分析仅检查task定义的质量，不涉及Agent的任何交互行为
- config中有些步骤是核心初始化（为task提供必要前置条件），有些是环境多样性干扰项（壁纸、dock、无关应用）

请输出：
1. **核心初始化**：简要罗列为task提供必要前置条件的步骤（如"启动Chrome"、"下载目标文件到桌面"），不需要展开参数细节
2. **缺失/问题**：config是否缺少task执行所需的必要前置条件？如有请指出；如无则写"无明显缺失"
3. **结论**：✅充分 / ⚠️有风险 / ❌不充分

简洁输出，忽略干扰项（壁纸、dock等），聚焦核心初始化是否充分。""",
        "en": """Briefly analyze whether this GUI task's config provides necessary environment initialization for task execution.

Background:
- Config's role is to initialize the environment (prepare files, launch apps, set system state, etc.), providing preconditions for task execution
- After config completes, the Agent then operates via mouse/keyboard to complete the instruction
- This analysis only checks the quality of the task definition, NOT any Agent interaction
- Some config steps are core initialization (providing necessary preconditions), others are diversity distractors (wallpaper, dock, unrelated apps)

Output:
1. **Core initialization**: Briefly list steps providing necessary preconditions (e.g. "Launch Chrome", "Download target file to Desktop"), no need for parameter details
2. **Missing/Issues**: Does config lack necessary preconditions for task execution? Point out if yes; write "No obvious gaps" if none
3. **Conclusion**: ✅Sufficient / ⚠️Risky / ❌Insufficient

Be concise, ignore distractors (wallpaper, dock, etc.), focus on whether core initialization is sufficient.""",
    },
    "describe_evaluator": {
        "zh": """请简洁分析这个GUI task的evaluator能否正确评价task是否完成。

背景：
- evaluator的作用是在task执行结束后，通过程序化方式检查环境状态来判定task是否完成
- postconfig在检查前做准备工作（如保存文件、重启应用验证持久化），不涉及Agent交互
- 整个评估流程是自动化的：postconfig准备 → result获取实际状态 → expected定义期望状态 → func对比判定
- 本分析仅检查evaluator逻辑是否能准确反映instruction的完成情况

结合instruction分析：
- instruction中的每个要求，evaluator是否有对应的验证？
- 哪些部分能被evaluator正确验证（✓标记）
- 哪些部分evaluator无法验证或验证逻辑有漏洞（✗标记）

请输出：
1. **覆盖分析**（逐条对照instruction要求与evaluator验证）：
   - ✓ [instruction要求X] → [evaluator如何验证]
   - ✗ [instruction要求Y] → [为何无法验证/验证不准确]
2. **风险**：是否有假阳性（没完成但判对）或假阴性（完成了但判错）风险？一句话说明
3. **结论**：✅准确 / ⚠️部分覆盖 / ❌不可靠

简洁输出，直击要点。""",
        "en": """Briefly analyze whether this GUI task's evaluator can correctly assess task completion.

Background:
- The evaluator's role is to programmatically check environment state after task execution to determine completion
- Postconfig prepares before checking (e.g. saving files, restarting apps to verify persistence), NO Agent interaction involved
- The entire evaluation is automated: postconfig preparation → result gets actual state → expected defines desired state → func compares
- This analysis only checks whether evaluator logic accurately reflects instruction completion

Cross-reference instruction with evaluator:
- For each requirement in instruction, does evaluator have corresponding verification?
- Mark parts correctly verified (✓)
- Mark parts not verified or with logic gaps (✗)

Output:
1. **Coverage analysis** (map instruction requirements to evaluator verification):
   - ✓ [requirement X] → [how evaluator verifies]
   - ✗ [requirement Y] → [why not verifiable/inaccurate]
2. **Risk**: Any false positive (pass when incomplete) or false negative (fail when correct) risk? One sentence
3. **Conclusion**: ✅Accurate / ⚠️Partial coverage / ❌Unreliable

Be concise, get to the point.""",
    },
    "suggestions": {
        "zh": """请综合分析这个GUI task的instruction、config、evaluator，给出质量判断。

背景：
- config为task提供环境初始化（准备文件、启动应用等前置条件）
- Agent在config初始化后的环境中通过鼠标/键盘完成instruction
- evaluator在task结束后通过程序化检查判定是否完成（postconfig准备 → 获取状态 → 对比期望）
- 本分析检查的是task定义本身的质量，不涉及Agent的任何行为

分析要求：
- 将instruction拆解为具体的子要求/子步骤
- 逐条检查config和evaluator对这些子要求的支撑情况
- 有问题时：明确指出是哪个子要求没有被满足，具体缺了什么
- 没问题时：列举已经满足的关键条件，说明为什么充分

请输出：

## Config支撑度：✅/⚠️/❌
逐条说明：
- ✓ [已满足的前置条件] — 具体说明config哪一步提供了什么
- ✗ [未满足的前置条件] — 具体说明缺少什么，为什么需要（如有）

## Evaluator可靠度：✅/⚠️/❌
逐条对照instruction子要求：
- ✓ [instruction要求X] → evaluator通过[具体方式]验证
- ✗ [instruction要求Y] → 未验证/验证逻辑有问题：[具体说明]

## 关键问题
有问题则用bullet指出具体位置和原因；无问题则写"无明显问题"

## 总结：✅推荐 / ⚠️需修改 / ❌不推荐
一句话结论+理由

简洁但具体，每条结论必须有对应的依据。""",
        "en": """Comprehensively analyze this GUI task's instruction, config, and evaluator. Give a quality judgment.

Background:
- Config provides environment initialization (preparing files, launching apps, etc. as preconditions)
- Agent completes the instruction via mouse/keyboard in the config-initialized environment
- Evaluator programmatically checks completion after task ends (postconfig preparation → get state → compare with expected)
- This analysis checks the quality of the task definition itself, NOT any Agent behavior

Requirements:
- Break instruction into specific sub-requirements/sub-steps
- Check config and evaluator support for each sub-requirement
- If issues exist: clearly point out which sub-requirement is unsatisfied and what's missing
- If no issues: list the key conditions already satisfied and explain why they're sufficient

Output:

## Config Support: ✅/⚠️/❌
Item by item:
- ✓ [satisfied precondition] — which config step provides what
- ✗ [unsatisfied precondition] — what's missing and why it's needed (if any)

## Evaluator Reliability: ✅/⚠️/❌
Map against instruction sub-requirements:
- ✓ [instruction requirement X] → evaluator verifies via [specific method]
- ✗ [instruction requirement Y] → not verified / logic issue: [specific explanation]

## Key Issues
If issues exist, bullet point with specific location and reason; if none, write "No obvious issues"

## Summary: ✅Recommended / ⚠️Needs modification / ❌Not recommended
One sentence conclusion + reason

Concise but specific, every conclusion must have supporting evidence.""",
    },
}


def find_task_json(examples_dir: str, task_id: str, domain: str | None = None) -> str | None:
    """Recursively find a task JSON file by its ID in the examples directory."""
    candidates = []
    # DeskCraft per-task layout: {domain}/{task_id}./task.json
    if domain:
        candidates.append(os.path.join(examples_dir, domain, f"{task_id}.", "task.json"))
        candidates.append(os.path.join(examples_dir, domain, task_id, "task.json"))
    # mini-osworld per-task layout: {domain}/{task_id}/task.json
    if "_task_" in task_id:
        inferred_domain = task_id.rsplit("_task_", 1)[0]
        candidates.append(os.path.join(examples_dir, inferred_domain, task_id, "task.json"))
    for path in candidates:
        if os.path.isfile(path):
            return path
    # OSWorld flat layout: {task_id}.json
    for path in glob.glob(os.path.join(examples_dir, "**", f"{task_id}.json"), recursive=True):
        return path
    # Fallback: recursive search for per-task layout (with or without trailing dot)
    for path in glob.glob(os.path.join(examples_dir, "**", task_id, "task.json"), recursive=True):
        return path
    for path in glob.glob(os.path.join(examples_dir, "**", f"{task_id}.", "task.json"), recursive=True):
        return path
    return None


def _load_json_file(path: str) -> dict | list | None:
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None



@app.route("/api/defaults")
def get_defaults():
    """Return server-side default paths (from --defaults profile JSON)."""
    if not DEFAULTS_PATH or not os.path.isfile(DEFAULTS_PATH):
        return jsonify({})
    try:
        with open(DEFAULTS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data if isinstance(data, dict) else {})
    except (json.JSONDecodeError, OSError) as e:
        return jsonify({"error": str(e)}), 500


# ─── Routes ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/load", methods=["POST"])
def load_data():
    """Load task config and validate examples dir."""
    data = request.get_json()
    config_path = data.get("config_path", "").strip()
    examples_dir = data.get("examples_dir", "").strip()
    results_dir = data.get("results_dir", "").strip()
    cache_dir = data.get("cache_dir", "").strip()

    if not config_path:
        return jsonify({"error": "Config path is required"}), 400
    if not examples_dir:
        return jsonify({"error": "Examples directory is required"}), 400

    config_path = os.path.abspath(os.path.expanduser(config_path))
    examples_dir = os.path.abspath(os.path.expanduser(examples_dir))
    if results_dir:
        results_dir = os.path.abspath(os.path.expanduser(results_dir))
    if cache_dir:
        cache_dir = os.path.abspath(os.path.expanduser(cache_dir))

    if not os.path.isfile(config_path):
        return jsonify({"error": f"Config file not found: {config_path}"}), 404
    if not os.path.isdir(examples_dir):
        return jsonify({"error": f"Examples directory not found: {examples_dir}"}), 404
    if results_dir and not os.path.isdir(results_dir):
        return jsonify({"error": f"Results directory not found: {results_dir}"}), 404
    if cache_dir and not os.path.isdir(cache_dir):
        return jsonify({"error": f"Cache directory not found: {cache_dir}"}), 404

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            task_config = json.load(f)
    except json.JSONDecodeError as e:
        return jsonify({"error": f"Invalid JSON in config file: {e}"}), 400

    resp = {
        "config": task_config,
        "config_path": config_path,
        "examples_dir": examples_dir,
    }
    if results_dir:
        resp["results_dir"] = results_dir
    if cache_dir:
        resp["cache_dir"] = cache_dir
    return jsonify(resp)


@app.route("/api/task", methods=["POST"])
def get_task():
    """Return the full JSON content of a specific task."""
    data = request.get_json()
    task_id = data.get("task_id", "").strip()
    examples_dir = data.get("examples_dir", "").strip()
    cache_dir = data.get("cache_dir", "").strip()
    results_dir = data.get("results_dir", "").strip()
    domain = data.get("domain", "").strip() or None

    if not task_id:
        return jsonify({"error": "task_id is required"}), 400
    if not examples_dir:
        return jsonify({"error": "examples_dir is required"}), 400

    examples_dir = os.path.abspath(os.path.expanduser(examples_dir))
    if not os.path.isdir(examples_dir):
        return jsonify({"error": f"Examples directory not found: {examples_dir}"}), 404

    task_path = find_task_json(examples_dir, task_id, domain)
    if not task_path:
        return jsonify({"error": f"Task {task_id} not found in {examples_dir}"}), 404

    with open(task_path, "r", encoding="utf-8") as f:
        task_data = json.load(f)

    task_dir = os.path.dirname(task_path)
    task_data["task_key"] = task_id

    if cache_dir:
        cache_dir = os.path.abspath(os.path.expanduser(cache_dir))
        task_cache_dir = os.path.join(cache_dir, task_id)

        reward_py_path = os.path.join(task_cache_dir, "reward.py")
        if os.path.isfile(reward_py_path):
            with open(reward_py_path, "r", encoding="utf-8") as f:
                task_data["evaluator_py"] = f.read()
            task_data["evaluator_py_path"] = reward_py_path

        initial_setup_path = os.path.join(task_cache_dir, "initial_setup.py")
        if os.path.isfile(initial_setup_path):
            with open(initial_setup_path, "r", encoding="utf-8") as f:
                task_data["initial_setup_py"] = f.read()
            task_data["initial_setup_py_path"] = initial_setup_path

        reward_label_path = os.path.join(task_cache_dir, "reward_label.json")
        reward_label_doc = _load_json_file(reward_label_path)
        if isinstance(reward_label_doc, dict):
            label = reward_label_doc.get("label")
            if isinstance(label, dict):
                task_data["reward_label"] = label
            task_data["reward_label_path"] = reward_label_path

    evaluator_py_path = os.path.join(task_dir, "evaluator.py")
    if "evaluator_py" not in task_data and os.path.isfile(evaluator_py_path):
        with open(evaluator_py_path, "r", encoding="utf-8") as f:
            task_data["evaluator_py"] = f.read()
        task_data["evaluator_py_path"] = evaluator_py_path

    evaluator_labels_path = os.path.join(task_dir, "evaluator_function_labels.json")
    evaluator_labels_doc = _load_json_file(evaluator_labels_path)
    if isinstance(evaluator_labels_doc, dict):
        label = evaluator_labels_doc.get("label")
        if isinstance(label, dict) and "evaluator_detail" not in task_data:
            task_data["evaluator_detail"] = label
            task_data["evaluator_detail_path"] = evaluator_labels_path

    evaluator_detail_path = os.path.join(task_dir, "evaluator_detail.json")
    if "evaluator_detail" not in task_data:
        evaluator_detail = _load_json_file(evaluator_detail_path)
        if isinstance(evaluator_detail, dict):
            task_data["evaluator_detail"] = evaluator_detail
            task_data["evaluator_detail_path"] = evaluator_detail_path

    if results_dir:
        results_dir = os.path.abspath(os.path.expanduser(results_dir))
        result_dir = resolve_result_task_dir(results_dir, task_id, domain)
        if result_dir:
            evaluator_audit = _load_json_file(os.path.join(result_dir, "evaluator_audit.json"))
            if isinstance(evaluator_audit, dict):
                task_data["evaluator_audit"] = evaluator_audit
                task_data["evaluator_audit_path"] = os.path.join(result_dir, "evaluator_audit.json")

            manifest = _load_json_file(os.path.join(result_dir, "evaluator", "manifest.json"))
            if isinstance(manifest, dict):
                task_data["evaluator_manifest"] = manifest
                task_data["evaluator_manifest_path"] = os.path.join(result_dir, "evaluator", "manifest.json")

            eval_label = _load_json_file(os.path.join(result_dir, "evaluator", "label.json"))
            if isinstance(eval_label, dict) and "evaluator_detail" not in task_data:
                inner = eval_label.get("label", eval_label)
                if isinstance(inner, dict):
                    task_data["evaluator_detail"] = inner
                    task_data["evaluator_detail_path"] = os.path.join(result_dir, "evaluator", "label.json")

            result_task_json = os.path.join(result_dir, "task.json")
            if os.path.isfile(result_task_json):
                task_data["result_task_json_path"] = result_task_json

    return jsonify(task_data)


@app.route("/api/labels")
def api_labels():
    """Load all task labels from trajectory result directories."""
    results_dir = request.args.get("results_dir", "").strip()
    if not results_dir:
        return jsonify({"error": "results_dir is required"}), 400
    results_dir = os.path.abspath(os.path.expanduser(results_dir))
    if not os.path.isdir(results_dir):
        return jsonify({"error": f"Results directory not found: {results_dir}"}), 404
    labels = load_all_labels(results_dir)
    return jsonify({
        "labels": labels,
        "label_filename": LABEL_FILENAME,
        "results_dir": results_dir,
    })


@app.route("/api/label", methods=["POST"])
def api_save_label():
    """Save a task label (usable / unusable)."""
    data = request.get_json()
    task_id = data.get("task_id", "").strip()
    results_dir = data.get("results_dir", "").strip()
    status = data.get("status", "").strip()
    reason = data.get("reason", "").strip()
    reason_category = data.get("reason_category", "").strip()
    domain = data.get("domain", "").strip() or None

    if not task_id:
        return jsonify({"error": "task_id is required"}), 400
    if not results_dir:
        return jsonify({"error": "results_dir is required"}), 400
    if not status:
        return jsonify({"error": "status is required"}), 400

    results_dir = os.path.abspath(os.path.expanduser(results_dir))
    if not os.path.isdir(results_dir):
        return jsonify({"error": f"Results directory not found: {results_dir}"}), 404

    try:
        entry = save_label(results_dir, task_id, status, reason, reason_category, domain)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({
        "status": "ok",
        "label": entry,
        "label_path": label_path_for_task(results_dir, task_id, domain),
    })


@app.route("/api/label", methods=["DELETE"])
def api_delete_label():
    """Remove a task label."""
    data = request.get_json(silent=True) or {}
    task_id = (data.get("task_id") or request.args.get("task_id", "")).strip()
    results_dir = (data.get("results_dir") or request.args.get("results_dir", "")).strip()
    domain = (data.get("domain") or request.args.get("domain", "")).strip() or None

    if not task_id:
        return jsonify({"error": "task_id is required"}), 400
    if not results_dir:
        return jsonify({"error": "results_dir is required"}), 400

    results_dir = os.path.abspath(os.path.expanduser(results_dir))
    if not os.path.isdir(results_dir):
        return jsonify({"error": f"Results directory not found: {results_dir}"}), 404

    deleted = delete_label(results_dir, task_id, domain)
    return jsonify({"status": "ok", "deleted": deleted})


@app.route("/api/trajectory", methods=["POST"])
def get_trajectory():
    """Return trajectory steps for a task from a results directory."""
    data = request.get_json()
    task_id = data.get("task_id", "").strip()
    results_dir = data.get("results_dir", "").strip()
    domain = data.get("domain", "").strip() or None

    if not task_id:
        return jsonify({"error": "task_id is required"}), 400
    if not results_dir:
        return jsonify({"error": "results_dir is required"}), 400

    results_dir = os.path.abspath(os.path.expanduser(results_dir))
    result = load_trajectory(results_dir, task_id, domain)
    if result.get("error") and not result.get("found"):
        return jsonify(result), 404
    return jsonify(result)


@app.route("/api/trajectory/screenshot/<task_id>/<path:filename>")
def trajectory_screenshot(task_id, filename):
    """Serve a trajectory screenshot image."""
    results_dir = request.args.get("results_dir", "").strip()
    domain = request.args.get("domain", "").strip() or None
    if not results_dir:
        return jsonify({"error": "results_dir is required"}), 400
    try:
        results_dir = os.path.abspath(os.path.expanduser(results_dir))
        task_dir = resolve_result_task_dir(results_dir, task_id, domain)
        if not task_dir:
            return jsonify({"error": "Task result directory not found"}), 404
        img_path = os.path.join(task_dir, filename)
        img_path = os.path.abspath(img_path)
        if not img_path.startswith(task_dir + os.sep):
            return jsonify({"error": "Invalid path"}), 400
    except ValueError:
        return jsonify({"error": "Invalid path"}), 400
    if not os.path.isfile(img_path):
        return jsonify({"error": "Screenshot not found"}), 404
    ext = os.path.splitext(filename)[1].lower()
    mimetype = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"
    return send_file(img_path, mimetype=mimetype)


@app.route("/api/trajectory/recording/<task_id>")
def trajectory_recording(task_id):
    """Serve trajectory recording video."""
    results_dir = request.args.get("results_dir", "").strip()
    domain = request.args.get("domain", "").strip() or None
    if not results_dir:
        return jsonify({"error": "results_dir is required"}), 400
    try:
        results_dir = os.path.abspath(os.path.expanduser(results_dir))
        base = resolve_result_task_dir(results_dir, task_id, domain)
        if not base:
            return jsonify({"error": "Task result directory not found"}), 404
    except ValueError:
        return jsonify({"error": "Invalid path"}), 400
    for fname, mime in [("recording.mp4", "video/mp4"), ("recording.webm", "video/webm")]:
        path = os.path.join(base, fname)
        if os.path.isfile(path):
            return send_file(path, mimetype=mime)
    return jsonify({"error": "Recording not found"}), 404


@app.route("/api/llm/analyze", methods=["POST"])
def llm_analyze():
    """LLM analysis endpoint. Accepts task data + analysis type + target language."""
    data = request.get_json()
    analysis_type = data.get("type", "")  # translate_instruction, describe_config, describe_evaluator, suggestions
    lang = data.get("lang", "zh")  # zh or en
    task_data = data.get("task", {})

    if not analysis_type:
        return jsonify({"error": "Analysis type is required"}), 400
    if analysis_type not in PROMPTS:
        return jsonify({"error": f"Unknown analysis type: {analysis_type}"}), 400
    if not task_data:
        return jsonify({"error": "Task data is required"}), 400

    system_prompt = PROMPTS[analysis_type].get(lang, PROMPTS[analysis_type]["en"])

    # Build user prompt based on analysis type
    if analysis_type == "translate_instruction":
        user_prompt = f"Task Instruction:\n{task_data.get('instruction', '')}"
    elif analysis_type == "describe_config":
        config = task_data.get("config", [])
        user_prompt = f"Task Instruction: {task_data.get('instruction', '')}\n\nSetup Config:\n{json.dumps(config, indent=2, ensure_ascii=False)}"
    elif analysis_type == "describe_evaluator":
        evaluator = task_data.get("evaluator", {})
        config = task_data.get("config", [])
        user_prompt = f"Task Instruction: {task_data.get('instruction', '')}\n\nSetup Config (for context):\n{json.dumps(config, indent=2, ensure_ascii=False)}\n\nEvaluator:\n{json.dumps(evaluator, indent=2, ensure_ascii=False)}"
    elif analysis_type == "suggestions":
        user_prompt = f"Task Instruction: {task_data.get('instruction', '')}\n\nConfig:\n{json.dumps(task_data.get('config', []), indent=2, ensure_ascii=False)}\n\nEvaluator:\n{json.dumps(task_data.get('evaluator', {}), indent=2, ensure_ascii=False)}"
    else:
        return jsonify({"error": "Invalid analysis type"}), 400

    result = call_llm(system_prompt, user_prompt)
    return jsonify({"result": result})


@app.route("/api/llm/config")
def get_llm_config():
    """Return current LLM configuration (for display in UI)."""
    provider = LLM_CONFIG["provider"]
    if provider == "openai":
        cfg = LLM_CONFIG["openai"]
        return jsonify({
            "provider": provider,
            "provider_label": "openai (蒸馏平台)",
            "model": cfg["model_marker"],
            "host": cfg["host"],
            "max_tokens": LLM_CONFIG["max_tokens"],
            "temperature": LLM_CONFIG["temperature"],
        })
    elif provider == "kimi":
        cfg = LLM_CONFIG["kimi"]
        return jsonify({
            "provider": provider,
            "provider_label": "kimi (Kimi-K2.6)",
            "model": cfg["model_name"],
            "host": cfg["base_url"],
            "max_tokens": LLM_CONFIG["max_tokens"],
            "temperature": LLM_CONFIG["temperature"],
        })
    else:
        cfg = LLM_CONFIG["vllm"]
        return jsonify({
            "provider": provider,
            "provider_label": "vllm",
            "model": cfg["model_name"],
            "host": cfg["base_url"],
            "max_tokens": LLM_CONFIG["max_tokens"],
            "temperature": LLM_CONFIG["temperature"],
        })


@app.route("/api/llm/config", methods=["POST"])
def update_llm_config():
    """Update LLM configuration at runtime."""
    data = request.get_json()
    if "provider" in data:
        LLM_CONFIG["provider"] = data["provider"]
    if "model_marker" in data:
        LLM_CONFIG["openai"]["model_marker"] = data["model_marker"]
    if "kimi_url" in data:
        LLM_CONFIG["kimi"]["base_url"] = data["kimi_url"]
    if "kimi_model" in data:
        LLM_CONFIG["kimi"]["model_name"] = data["kimi_model"]
    if "vllm_url" in data:
        LLM_CONFIG["vllm"]["base_url"] = data["vllm_url"]
    if "vllm_model" in data:
        LLM_CONFIG["vllm"]["model_name"] = data["vllm_model"]
    if "max_tokens" in data:
        LLM_CONFIG["max_tokens"] = int(data["max_tokens"])
    if "temperature" in data:
        LLM_CONFIG["temperature"] = float(data["temperature"])
    return jsonify({"status": "ok"})


@app.route("/api/llm/test")
def llm_test():
    """Test LLM connectivity."""
    result = call_llm(
        "You are a helpful assistant.",
        "Please respond with exactly: 'LLM connection successful.' Nothing else."
    )
    return jsonify({"result": result})


def main():
    parser = argparse.ArgumentParser(description="EasyVis - GUI Task Visualizer")
    parser.add_argument("--port", "-p", type=int, default=8080, help="Port (default: 8080)")
    parser.add_argument("--host", default="0.0.0.0", help="Host (default: 0.0.0.0)")
    parser.add_argument("--provider", default=None, choices=["openai", "kimi", "vllm"], help="LLM provider")
    parser.add_argument("--model", default=None, help="Model name/marker")
    parser.add_argument("--max-tokens", type=int, default=None, help="Max tokens for LLM generation (default: 4096)")
    parser.add_argument("--defaults", default=None, help="JSON file with default config/examples/cache/results paths")
    args = parser.parse_args()

    global DEFAULTS_PATH
    DEFAULTS_PATH = os.path.abspath(os.path.expanduser(args.defaults)) if args.defaults else ""

    if args.provider:
        LLM_CONFIG["provider"] = args.provider
    if args.max_tokens:
        LLM_CONFIG["max_tokens"] = args.max_tokens
    if args.model:
        p = LLM_CONFIG["provider"]
        if p == "openai":
            LLM_CONFIG["openai"]["model_marker"] = args.model
        elif p == "kimi":
            LLM_CONFIG["kimi"]["model_name"] = args.model
        else:
            LLM_CONFIG["vllm"]["model_name"] = args.model

    provider = LLM_CONFIG["provider"]
    if provider == "openai":
        model_info = f"{LLM_CONFIG['openai']['model_marker']} @ {LLM_CONFIG['openai']['host']}"
    elif provider == "kimi":
        model_info = f"{LLM_CONFIG['kimi']['model_name']} @ {LLM_CONFIG['kimi']['base_url']}"
    else:
        model_info = f"{LLM_CONFIG['vllm']['model_name']} @ {LLM_CONFIG['vllm']['base_url']}"

    print(f"=" * 60)
    title = "EasyVis CUA-Gym"
    if DEFAULTS_PATH:
        try:
            with open(DEFAULTS_PATH, "r", encoding="utf-8") as f:
                prof = json.load(f)
            if isinstance(prof, dict) and prof.get("title"):
                title = prof["title"]
        except (json.JSONDecodeError, OSError):
            pass
    print(f"  {title}")
    print(f"  Serving on http://{args.host}:{args.port}")
    print(f"  LLM Provider: {provider}")
    print(f"  LLM Model: {model_info}")
    print(f"=" * 60)

    app.run(host=args.host, port=args.port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
