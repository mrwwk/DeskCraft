#!/usr/bin/env python3
"""Repair DeskCraft initial-setup files with CodeBuddy.

For tasks under ``evaluation_examples/examples_per_task/{calc,impr,writ}`` whose
*initial* (uploaded) file already scores full marks against the task evaluator
(answer leakage / trivially-satisfiable task), this script asks CodeBuddy to
produce a revised initial file that is a genuine "before" state: it must NO
LONGER pass the evaluator, while remaining a valid, openable office document of
the same format and still transformable into the gold via the task instruction.

Outputs are written under ``revise_task/`` inside each task directory:
  - ``revise_task/<initial_filename>``  : the revised initial file
  - ``revise_task/task.json``           : full task JSON copy whose
                                          ``config`` upload_file ``local_path``
                                          points at the revised initial file
  - ``revise_task/repair_log.md``       : Chinese repair log

The original initial file, the gold file and the evaluator are never modified.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import importlib.util
import json
import logging
import os
import subprocess
import sys
import time
import traceback
import uuid
from pathlib import Path
from typing import Any, Optional, Tuple


# ---- reuse the offline scorer from check_initial_fullscore.py ----
SCRIPTS_DIR = Path(__file__).resolve().parent
_cis_spec = importlib.util.spec_from_file_location(
    "_cis_check_initial_fullscore", SCRIPTS_DIR / "check_initial_fullscore.py"
)
_cis = importlib.util.module_from_spec(_cis_spec)
_cis_spec.loader.exec_module(_cis)
PROJECT_DIR = Path(_cis.PROJECT_DIR)
EXAMPLES_DIR = Path(_cis.EXAMPLES_DIR)
as_list = _cis.as_list
load_module = _cis.load_module
resolve_expected = _cis.resolve_expected
run_metric = _cis.run_metric
find_initial_file = _cis.find_initial_file

# Per-task slides/docx evaluators attach DEBUG StreamHandlers that flood output
# and slow execution. Globally silence DEBUG/INFO while keeping WARNING+.
logging.disable(logging.INFO)

DEFAULT_DOMAINS = ("calc", "impr", "writ")
DEFAULT_THRESHOLD = 1.0  # only repair tasks whose initial file already scores full


SYSTEM_PROMPT = """你是一个严谨的 DeskCraft 初始文件（initial setup）修复工程师。

你的任务是：对于"初始文件评测后就已经满分"的任务（答案泄漏 / 题目天然已满足），生成一份修订后的初始文件，使其成为一个真正的"未完成"起始状态——评测器对它打分必须严格低于满分，同时它仍是同格式的合法可打开 office 文档，并且通过任务指令描述的操作仍然可以从这个修订初始文件变换到 gold/目标状态。

核心原则：
1. 只做与"消除答案泄漏"直接相关的最小修改；不要改动无关内容，不要重写评测器，不要修改 gold 文件，不要修改原始初始文件，不要做破坏性操作。
2. 必须修改初始文件中被评测器检查、且当前已经满足目标值的那些属性，使其不再满足目标值（例如：把已经排好序的列打乱、把已经设成 Georgia/40pt 的标题改回默认字体、把已经替换好的文本还原成原始文本、把已经加粗的标题改回非粗体等）。
3. 修订初始文件必须是同格式的合法文件（xlsx/pptx/docx），用 openpyxl / python-pptx / python-docx 等库编辑二进制文件，不要手写 XML，不要产出损坏文件。
4. 修订初始文件必须仍然"可由指令变换到 gold"：保持文件结构、数据规模、占位符等与原初始文件基本一致，只翻转被评测的那一处/几处属性；不要删除整张表/整页幻灯片/整段正文，不要引入与指令无关的破坏。
5. 如果评测器 expected 为 null（无 gold 文件，只检查 result 的某些属性，如标题字体），则把被检查的属性改成一个明确不同但仍合理的默认值。
6. 必须直接编辑文件系统，创建用户指定的 revise_task/<初始文件名>、revise_task/task.json 和 revise_task/repair_log.md。完成后只输出简短中文说明，不要输出完整源码或大段 Markdown 解释。"""


INITIAL_SETUP_EXPLANATION = """[DeskCraft 初始文件加载与评测逻辑]
下面是 DeskCraft 中与"初始文件"相关的实际逻辑，修复时必须严格遵守。

1. 任务 JSON 的 config 用于初始化 VM：
   - 第一步通常是 {"type": "upload_file", "parameters": {"files": [{"local_path": "<相对 DeskCraft 项目根的路径>", "path": "<VM 内绝对路径>"}]}}，把本地初始文件上传到 VM。
   - 紧接着 {"type": "open", ...} 在 LibreOffice 中打开该文件。
   - local_path 是相对 DeskCraft 项目根目录的相对路径（例如 assets/xlsx/Foo.xlsx 或 cache/<id>/Foo.xlsx）。
2. 评测流程：agent 操作后，evaluator.postconfig 会激活窗口并 Ctrl+S 保存；evaluator.result（type=vm_file）从 VM 拉回该文件，evaluator.expected（type=cache_file 或 null）提供 gold/参考，evaluator.func 用 per-task evaluator.py 中的函数打分。
3. 因此"修订初始文件"只需要：生成一份新的本地初始文件，并把它放到一个新路径，再在 revise_task/task.json 的 config upload_file 中把 local_path 指向这个新路径；VM 内 path（dest）保持不变即可。
4. 评测器函数签名与调用：metric(result_path, expected_path, **options) 或 metric(result_path, **options)。修订初始文件要让该调用对"修订初始文件 vs gold"返回严格小于 1.0 的分数。
5. 多 metric 时 evaluator.conj（默认 "and"）合并：任一 metric 为 0 即总分 0，否则取平均；"or" 时任一为 1 即总分 1。要让总分严格低于 1.0，在 "and" 下至少破坏一个 metric，在 "or" 下破坏所有当前为 1.0 的 metric。
"""


USER_PROMPT_TEMPLATE = """请修复这个 DeskCraft 任务的初始文件，消除"初始即满分"的答案泄漏。

[任务目录]
{task_dir}

[原始初始文件]
- 路径（项目相对）: {initial_rel}
- 绝对路径: {initial_abs}

[Gold / 参考文件]
{gold_info}

[必须写入的修订文件]
- 修订初始文件: {revised_initial_abs}
- 修订 task.json: {revised_task_json_abs}
- 修复日志: {repair_log_abs}

重要约束：
- 不要覆盖或修改原始初始文件、gold 文件、原始 task.json、evaluator.py。
- 把修订后的初始文件写入 {revised_initial_abs}（与原文件同名，放在 revise_task/ 下）。
- 把完整 task.json 复制到 revise_task/task.json，仅将 config 中 upload_file 的 local_path 改为 "{revised_initial_rel}"（项目相对路径），其余字段（id、instruction、evaluator、trajectory、related_apps 等）原样保留；VM 内 path/dest 保持不变。
- 写入 revise_task/repair_log.md（中文）。

{loading_explanation}

[任务指令]
{instruction}

[初始文件当前评测结果（为何是答案泄漏）]
{score_report}

[评测器配置（task.json 的 evaluator 字段）]
{evaluator_json}

[评测器源码 evaluator.py]
{evaluator_code}

[修复要求]
1. 先阅读评测器源码和上面的 score_report，弄清楚初始文件当前已经满足、被评测器检查的属性是什么。
2. 用 openpyxl / python-pptx / python-docx 读取原始初始文件，做最小修改翻转那些属性，使其不再满足目标值，另存为 {revised_initial_abs}。修改要合理：是"未完成"的起始状态，且能通过指令变换到 gold。
3. 不要为了"看起来更难"而大改无关内容；不要删除整张表/整页/整段；保持文件可被对应库正常打开。
4. 如果 expected 为 null，把被检查属性改成明确不同但仍合理的默认值。
5. 更新 revise_task/task.json 的 config upload_file local_path 指向修订文件，其余保持原样。
6. repair_log.md 用中文记录：原始初始文件为何即满分、改了哪些属性、新初始文件期望的评测分数（应 < 1.0）、仍有哪些风险、是否仍可由指令变换到 gold。

完成后输出中文说明。"""


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _json_for_prompt(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def _read_text(path: Path, *, max_chars: int | None = None) -> str:
    text = path.read_text(encoding="utf-8")
    if max_chars is not None and len(text) > max_chars:
        return text[:max_chars] + "\n...[truncated]..."
    return text


def compute_initial_score(task_dir: Path, initial_path: str) -> Tuple[Optional[float], list[dict]]:
    """Run the per-task evaluator metric on `initial_path` (vs the task's gold).

    Returns (combined_score, per_metric_entries). combined_score is None on error.
    """
    task = _load_json(task_dir / "task.json")
    ev = task.get("evaluator", {})
    func_names = as_list(ev.get("func"))
    if not func_names:
        return None, [{"func": "?", "error": "no func"}]
    eval_file = ev.get("file")
    if not eval_file:
        return None, [{"func": "?", "error": "no per-task evaluator file"}]
    eval_file_path = eval_file if os.path.isabs(eval_file) else str(task_dir / eval_file)
    try:
        module = load_module(eval_file_path)
    except Exception as e:
        return None, [{"func": "?", "error": f"load evaluator failed: {type(e).__name__}: {e}"}]

    result_cfgs = as_list(ev.get("result"))
    expected_cfgs = as_list(ev.get("expected"))
    options_list = as_list(ev.get("options"))
    if len(options_list) == 1 and not isinstance(ev.get("options"), list):
        options_list = [ev.get("options")] * len(func_names)
    elif not options_list:
        options_list = [None] * len(func_names)

    entries: list[dict] = []
    for i, fname in enumerate(func_names):
        fn = getattr(module, fname, None)
        entry = {"func": fname}
        if fn is None:
            entry["error"] = "func not found"
            entries.append(entry)
            continue
        expected_cfg = expected_cfgs[i] if i < len(expected_cfgs) else (expected_cfgs[0] if expected_cfgs else None)
        gold_path = resolve_expected(str(task_dir), expected_cfg)
        opts = options_list[i] if i < len(options_list) else None
        try:
            entry["score"] = run_metric(fn, initial_path, gold_path, opts)
        except Exception as e:
            entry["error"] = f"{type(e).__name__}: {e}"
        entries.append(entry)

    conj = ev.get("conj", "and")
    numeric = [e.get("score") for e in entries if isinstance(e.get("score"), (int, float))]
    has_err = any("error" in e for e in entries)
    if has_err or not numeric:
        return None, entries
    if conj == "or":
        total = 1.0 if any(v >= 1.0 for v in numeric) else 0.0
    else:
        total = 1.0 if all(v >= 1.0 for v in numeric) else (sum(numeric) / len(numeric))
    return total, entries


def initial_basename(task: dict) -> Optional[str]:
    for step in task.get("config", []):
        if step.get("type") == "upload_file":
            files = step.get("parameters", {}).get("files", [])
            if files:
                local = files[0].get("local_path", "")
                return os.path.basename(local)
    return None


def is_file_comparison_task(task: dict) -> bool:
    ev = task.get("evaluator", {})
    result_cfgs = as_list(ev.get("result"))
    expected_cfgs = as_list(ev.get("expected"))
    result_types = [c.get("type") if isinstance(c, dict) else None for c in result_cfgs]
    expected_types = [c.get("type") if isinstance(c, dict) else None for c in expected_cfgs]
    return (
        len(result_cfgs) > 0
        and all(rt in ("vm_file", None) for rt in result_types)
        and all(et in ("cache_file", None) for et in expected_types)
    )


def discover_task_dirs(root: Path, domains: list[str]) -> list[Path]:
    dirs: list[Path] = []
    for d in domains:
        ddir = root / d
        if not ddir.is_dir():
            continue
        for name in sorted(os.listdir(ddir)):
            p = ddir / name
            if p.is_dir() and (p / "task.json").is_file():
                dirs.append(p)
    return dirs


def build_score_report(entries: list[dict], total: Optional[float]) -> str:
    lines = [f"初始文件总分: {total}"]
    for e in entries:
        lines.append(f"  - {e.get('func')}: score={e.get('score')} {e.get('error', '')}")
    return "\n".join(lines)


def build_prompt(task_dir: Path) -> Optional[str]:
    task = _load_json(task_dir / "task.json")
    if not is_file_comparison_task(task):
        return None
    ev = task.get("evaluator", {})
    result_cfgs = as_list(ev.get("result"))
    result_vm_path = result_cfgs[0].get("path") if result_cfgs and isinstance(result_cfgs[0], dict) else None
    init = find_initial_file(task, result_vm_path)
    if isinstance(init, tuple) or not init or not os.path.isfile(init):
        return None
    initial_abs = str(Path(init).resolve())
    initial_rel = os.path.relpath(initial_abs, PROJECT_DIR)

    expected_cfgs = as_list(ev.get("expected"))
    expected_cfg = expected_cfgs[0] if expected_cfgs else None
    gold_path = resolve_expected(str(task_dir), expected_cfg)
    if gold_path:
        gold_info = f"- 路径（项目相对）: {os.path.relpath(gold_path, PROJECT_DIR)}\n- 绝对路径: {gold_path}\n- 注意：gold 仅供参考目标状态，不要修改 gold。"
    else:
        gold_info = "- 无 gold 文件（expected 为 null）。评测器只检查 result 文件的某些属性；把被检查属性改成明确不同但仍合理的默认值即可。"

    basename = os.path.basename(initial_abs)
    revise_dir = task_dir / "revise_task"
    revised_initial_abs = str((revise_dir / basename).resolve())
    revised_initial_rel = os.path.relpath(revised_initial_abs, PROJECT_DIR)

    eval_file = ev.get("file", "evaluator.py")
    eval_file_path = eval_file if os.path.isabs(eval_file) else str(task_dir / eval_file)
    try:
        evaluator_code = _read_text(Path(eval_file_path), max_chars=80_000)
    except Exception:
        evaluator_code = "(读取 evaluator.py 失败)"

    total, entries = compute_initial_score(task_dir, initial_abs)
    instruction = task.get("instruction", "(无 instruction 字段)")

    return USER_PROMPT_TEMPLATE.format(
        task_dir=str(task_dir.resolve()),
        initial_rel=initial_rel,
        initial_abs=initial_abs,
        gold_info=gold_info,
        revised_initial_abs=revised_initial_abs,
        revised_task_json_abs=str((revise_dir / "task.json").resolve()),
        repair_log_abs=str((revise_dir / "repair_log.md").resolve()),
        revised_initial_rel=revised_initial_rel,
        loading_explanation=INITIAL_SETUP_EXPLANATION,
        instruction=instruction,
        score_report=build_score_report(entries, total),
        evaluator_json=_json_for_prompt(ev),
        evaluator_code=evaluator_code,
    )


def call_codebuddy(
    codebuddy_cmd: str,
    prompt: str,
    cwd: Path,
    timeout: int,
    effort: str | None,
    model: str | None,
    permission_mode: str | None,
) -> subprocess.CompletedProcess[str]:
    cmd = [
        codebuddy_cmd,
        "-p",
        prompt,
        "--system-prompt",
        SYSTEM_PROMPT,
        "--session-id",
        f"initial-setup-repair-{uuid.uuid4().hex}",
        "--output-format",
        "text",
    ]
    if model:
        cmd.extend(["--model", model])
    if effort:
        cmd.extend(["--effort", effort])
    if permission_mode:
        cmd.extend(["--permission-mode", permission_mode])
    return subprocess.run(
        cmd,
        text=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd,
        timeout=timeout,
        check=False,
    )


def call_codebuddy_with_retries(
    codebuddy_cmd: str,
    prompt: str,
    cwd: Path,
    timeout: int,
    effort: str | None,
    model: str | None,
    permission_mode: str | None,
    retries: int,
    retry_backoff: float,
) -> subprocess.CompletedProcess[str]:
    last_timeout: subprocess.TimeoutExpired | None = None
    for attempt in range(retries + 1):
        try:
            return call_codebuddy(codebuddy_cmd, prompt, cwd, timeout, effort, model, permission_mode)
        except subprocess.TimeoutExpired as exc:
            last_timeout = exc
            if attempt >= retries:
                raise
            wait_seconds = retry_backoff * (attempt + 1)
            print(
                f"CodeBuddy timed out after {timeout}s; retrying ({attempt + 1}/{retries}) in {wait_seconds:.1f}s...",
                file=sys.stderr,
            )
            if wait_seconds > 0:
                time.sleep(wait_seconds)
    raise last_timeout if last_timeout else RuntimeError("CodeBuddy retry failed unexpectedly")


def validate_revised_outputs(task_dir: Path, threshold: float) -> tuple[list[str], dict]:
    """Validate revise_task outputs. Returns (errors, info)."""
    revise_dir = task_dir / "revise_task"
    errors: list[str] = []
    info: dict[str, Any] = {}

    task_path = revise_dir / "task.json"
    revised_initial_path: Optional[Path] = None
    if not task_path.is_file():
        errors.append("missing:revise_task/task.json")
    else:
        try:
            task = _load_json(task_path)
        except json.JSONDecodeError as exc:
            errors.append(f"invalid_json:revise_task/task.json:{exc}")
            task = {}
        # find revised initial local_path from config
        local_paths: list[str] = []
        for step in task.get("config", []):
            if step.get("type") == "upload_file":
                for f in step.get("parameters", {}).get("files", []):
                    local_paths.append(f.get("local_path", ""))
        if not local_paths:
            errors.append("missing:config.upload_file.local_path")
        else:
            lp = local_paths[0]
            resolved = lp if os.path.isabs(lp) else str(PROJECT_DIR / lp)
            if not os.path.isfile(resolved):
                errors.append(f"revised_initial_not_found:{lp}")
            revised_initial_path = Path(resolved)

    # repair log
    if not (revise_dir / "repair_log.md").is_file():
        errors.append("missing:revise_task/repair_log.md")

    # re-score the revised initial file: must be < 1.0 (no longer full)
    if revised_initial_path and revised_initial_path.is_file():
        try:
            total, entries = compute_initial_score(task_dir, str(revised_initial_path))
        except Exception as exc:
            errors.append(f"rescore_failed:{type(exc).__name__}:{exc}")
            total, entries = None, []
        info["revised_score"] = total
        info["revised_entries"] = entries
        if total is None:
            errors.append("rescore_returned_none")
        elif total >= 1.0:
            errors.append(f"still_full_score:{total}")
        elif total >= threshold:
            # allowed: still below 1.0 is the hard requirement; threshold only
            # governs selection. We accept any score < 1.0.
            pass
    else:
        errors.append("cannot_rescore:revised_initial_missing")

    return errors, info


def write_run_artifacts(
    task_dir: Path,
    prompt: str,
    result: subprocess.CompletedProcess[str] | None,
    *,
    save_prompt: bool,
) -> None:
    revise_dir = task_dir / "revise_task"
    revise_dir.mkdir(parents=True, exist_ok=True)
    if save_prompt:
        (revise_dir / "repair_prompt.txt").write_text(prompt, encoding="utf-8")
    if result is None:
        return
    if result.stdout:
        (revise_dir / "codebuddy_stdout.txt").write_text(result.stdout, encoding="utf-8")
    if result.stderr:
        (revise_dir / "codebuddy_stderr.txt").write_text(result.stderr, encoding="utf-8")


def repair_task(task_dir: Path, args: argparse.Namespace) -> tuple[bool, Path | None, str | None]:
    task = _load_json(task_dir / "task.json")
    if not is_file_comparison_task(task):
        return True, None, "skipped_non_file_eval"
    ev = task.get("evaluator", {})
    result_cfgs = as_list(ev.get("result"))
    result_vm_path = result_cfgs[0].get("path") if result_cfgs and isinstance(result_cfgs[0], dict) else None
    init = find_initial_file(task, result_vm_path)
    if isinstance(init, tuple):
        return True, None, "skipped_download_initial"
    if not init or not os.path.isfile(init):
        return False, None, f"initial_not_found:{init}"

    total, _entries = compute_initial_score(task_dir, init)
    if total is None:
        return False, None, "initial_score_none"
    if total < args.threshold:
        return True, None, f"skipped_score_below_threshold:{total}"
    if total < 1.0 and args.only_full and args.threshold >= 1.0:
        # threshold==1.0 and only_full => require exactly full
        pass
    if args.only_full and total < 1.0:
        return True, None, f"skipped_not_full:{total}"

    revise_dir = task_dir / "revise_task"
    if args.skip_existing and (revise_dir / "task.json").is_file():
        # still validate
        errs, info = validate_revised_outputs(task_dir, args.threshold)
        if errs:
            return False, revise_dir, "skipped_existing_but_invalid:" + ",".join(errs)
        return True, revise_dir, f"skipped_existing (revised_score={info.get('revised_score')})"

    prompt = build_prompt(task_dir)
    if prompt is None:
        return False, None, "build_prompt_failed"
    if args.print_prompt:
        print(prompt)
    if args.dry_run:
        if args.save_prompt:
            write_run_artifacts(task_dir, prompt, None, save_prompt=True)
        return True, revise_dir, "dry_run"

    revise_dir.mkdir(parents=True, exist_ok=True)
    try:
        result = call_codebuddy_with_retries(
            args.codebuddy_cmd,
            prompt,
            task_dir,
            args.timeout,
            args.effort,
            args.model,
            args.permission_mode,
            args.retries,
            args.retry_backoff,
        )
    except subprocess.TimeoutExpired:
        write_run_artifacts(task_dir, prompt, None, save_prompt=args.save_prompt)
        return False, revise_dir, "codebuddy_timeout"

    write_run_artifacts(task_dir, prompt, result, save_prompt=args.save_prompt)
    if result.returncode != 0:
        return False, revise_dir, f"codebuddy_returncode_{result.returncode}"

    errs, info = validate_revised_outputs(task_dir, args.threshold)
    if errs:
        return False, revise_dir, "invalid_revised_outputs:" + ",".join(errs)
    return True, revise_dir, f"revised_score={info.get('revised_score')}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Repair DeskCraft initial-setup files (answer leakage) with CodeBuddy."
    )
    parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=EXAMPLES_DIR,
        help=f"Task root (default: {EXAMPLES_DIR}).",
    )
    parser.add_argument(
        "--domains",
        nargs="+",
        default=list(DEFAULT_DOMAINS),
        help="Domain subdirs to scan (default: calc impr writ).",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help="Repair tasks whose initial score >= threshold (default 1.0 = only full-score).",
    )
    parser.add_argument(
        "--only-full",
        action="store_true",
        default=True,
        help="Only repair tasks whose initial score is exactly 1.0 (default). Use --no-only-full to relax.",
    )
    parser.add_argument(
        "--include-partial",
        action="store_true",
        help="Also repair partial-score tasks (>= --threshold and < 1.0). Sets only_full=False.",
    )
    parser.add_argument(
        "--single",
        type=Path,
        default=None,
        help="Repair a single task directory directly (skip discovery).",
    )
    parser.add_argument("--codebuddy-cmd", default="codebuddy")
    parser.add_argument("--effort", default="high", choices=["low", "medium", "high"])
    parser.add_argument("--model", default="deepseek-v4-pro-ioa")
    parser.add_argument(
        "--permission-mode",
        default="bypassPermissions",
        choices=["acceptEdits", "bypassPermissions", "default", "plan"],
    )
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--retries", type=int, default=1)
    parser.add_argument("--retry-backoff", type=float, default=5.0)
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--save-prompt", action="store_true")
    parser.add_argument("--print-prompt", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.include_partial:
        args.only_full = False
    return args


def main() -> int:
    args = parse_args()

    if args.print_prompt and args.concurrency != 1:
        print("Note: --print-prompt forced sequential.", file=sys.stderr)
        args.concurrency = 1

    if args.single:
        task_dirs = [args.single.resolve()]
    else:
        root = args.root.resolve()
        task_dirs = discover_task_dirs(root, args.domains)

    if not task_dirs:
        print(f"No task directories found.", file=sys.stderr)
        return 1

    print(f"Found {len(task_dirs)} task directories. Selecting for repair "
          f"(threshold={args.threshold}, only_full={args.only_full})...")
    selected: list[Path] = []
    for td in task_dirs:
        try:
            task = _load_json(td / "task.json")
        except Exception:
            print(f"[SKIP] {td} (unreadable task.json)")
            continue
        if not is_file_comparison_task(task):
            continue
        ev = task.get("evaluator", {})
        rcfgs = as_list(ev.get("result"))
        rvm = rcfgs[0].get("path") if rcfgs and isinstance(rcfgs[0], dict) else None
        init = find_initial_file(task, rvm)
        if isinstance(init, tuple) or not init or not os.path.isfile(init):
            continue
        total, _ = compute_initial_score(td, init)
        marker = "REPAIR" if (total is not None and total >= args.threshold and (not args.only_full or total >= 1.0)) else "SKIP"
        print(f"[{marker}] {td}  initial_score={total}")
        if marker == "REPAIR":
            selected.append(td)

    print(f"\nSelected {len(selected)} task(s) for repair.\n")

    failures = 0
    results: list[tuple[Path, tuple[bool, Path | None, str | None]]] = []
    if args.concurrency <= 1:
        for td in task_dirs:
            try:
                r = repair_task(td, args)
            except Exception as exc:
                r = (False, None, f"exception:{type(exc).__name__}:{exc}\n{traceback.format_exc(limit=3)}")
            results.append((td, r))
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as ex:
            fut = {ex.submit(repair_task, td, args): td for td in task_dirs}
            for f in concurrent.futures.as_completed(fut):
                td = fut[f]
                try:
                    r = f.result()
                except Exception as exc:
                    r = (False, None, f"exception:{type(exc).__name__}:{exc}")
                results.append((td, r))

    for td, (ok, out, reason) in results:
        if ok:
            print(f"[OK] {td} -> {out} ({reason})")
        else:
            failures += 1
            print(f"[FAIL] {td}: {reason}", file=sys.stderr)

    if failures:
        print(f"\nCompleted with {failures} failure(s).", file=sys.stderr)
        return 1
    print(f"\nCompleted successfully. Selected {len(selected)} repair task(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
