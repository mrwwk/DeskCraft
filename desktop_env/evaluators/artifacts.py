"""Save evaluator inputs, source code, and replay helpers for offline reproduction."""

from __future__ import annotations

import ast
import inspect
import json
import logging
import os
import shutil
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from desktop_env.evaluators import metrics as metrics_pkg
from desktop_env.evaluators.loader import _resolve_evaluator_file, resolve_metric

if TYPE_CHECKING:
    from desktop_env.desktop_env import DesktopEnv

logger = logging.getLogger("desktopenv.evaluator.artifacts")

_LARGE_TEXT_THRESHOLD = 256 * 1024
_FILE_MARKER = "__type__"
_REPLAY_SCRIPT_NAME = "replay.py"


def artifacts_enabled() -> bool:
    """Return True iff the evaluator-artifacts replay switch is turned on.

    Controlled by the ``DESKCRAFT_SAVE_EVALUATOR_ARTIFACTS`` env var. Off by
    default (opt-in); set it to ``"1"`` to enable saving evaluator artifacts.
    """
    return os.environ.get("DESKCRAFT_SAVE_EVALUATOR_ARTIFACTS", "0") == "1"


def _json_dump(path: str, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def _unique_dest_path(files_dir: str, basename: str) -> str:
    dest = os.path.join(files_dir, basename)
    if not os.path.exists(dest):
        return dest
    stem, ext = os.path.splitext(basename)
    counter = 1
    while True:
        candidate = os.path.join(files_dir, f"{stem}_{counter}{ext}")
        if not os.path.exists(candidate):
            return candidate
        counter += 1


def serialize_value(
    value: Any,
    files_dir: str,
    copied_cache: Dict[str, str],
    text_counter: List[int],
) -> Any:
    """Serialize evaluator input values, copying files into files_dir."""
    if value is None:
        return None

    if isinstance(value, str):
        if os.path.isfile(value):
            if value in copied_cache:
                saved_as = copied_cache[value]
            else:
                os.makedirs(files_dir, exist_ok=True)
                basename = os.path.basename(value)
                dest = _unique_dest_path(files_dir, basename)
                shutil.copy2(value, dest)
                saved_as = os.path.join("files", os.path.basename(dest))
                copied_cache[value] = saved_as
            return {
                _FILE_MARKER: "file",
                "saved_as": saved_as,
                "original_path": value,
            }

        encoded = value.encode("utf-8")
        if len(encoded) > _LARGE_TEXT_THRESHOLD:
            os.makedirs(files_dir, exist_ok=True)
            text_counter[0] += 1
            filename = f"large_text_{text_counter[0]}.txt"
            dest = os.path.join(files_dir, filename)
            with open(dest, "w", encoding="utf-8") as f:
                f.write(value)
            saved_as = os.path.join("files", filename)
            return {_FILE_MARKER: "text_file", "saved_as": saved_as}

        return value

    if isinstance(value, (list, tuple)):
        return [serialize_value(item, files_dir, copied_cache, text_counter) for item in value]

    if isinstance(value, dict):
        return {
            key: serialize_value(item, files_dir, copied_cache, text_counter)
            for key, item in value.items()
        }

    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        return {_FILE_MARKER: "repr", "value": repr(value)}


def _metrics_dir() -> str:
    return os.path.dirname(metrics_pkg.__file__)


def _extract_function_source(py_file: str, function_name: str) -> Optional[str]:
    with open(py_file, "r", encoding="utf-8") as f:
        source = f.read()
    tree = ast.parse(source, filename=py_file)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
            segment = ast.get_source_segment(source, node)
            if segment:
                return segment
    return None


def _find_builtin_function_source(function_name: str) -> tuple[str, str]:
    metrics_dir = _metrics_dir()
    for py_file in sorted(os.path.join(metrics_dir, name) for name in os.listdir(metrics_dir)):
        if not py_file.endswith(".py"):
            continue
        function_source = _extract_function_source(py_file, function_name)
        if function_source:
            rel_path = os.path.relpath(py_file, metrics_dir)
            return rel_path, f"# Source: desktop_env/evaluators/metrics/{rel_path}\n{function_source}"
    raise FileNotFoundError(
        f"Could not find builtin metric function '{function_name}' under {metrics_dir}"
    )


def save_metric_source(
    code_dir: str,
    env: "DesktopEnv",
    func_names: List[str],
    task_config: Dict[str, Any],
) -> Dict[str, str]:
    """Copy or extract metric source code. Returns func_name -> code filename."""
    os.makedirs(code_dir, exist_ok=True)
    evaluator = env.evaluator
    func_to_file: Dict[str, str] = {}

    if evaluator.get("file"):
        source_path = _resolve_evaluator_file(evaluator, task_config)
        dest_name = os.path.basename(evaluator["file"]) or "evaluator.py"
        dest_path = os.path.join(code_dir, dest_name)
        shutil.copy2(source_path, dest_path)
        for func_name in func_names:
            func_to_file[func_name] = dest_name
        return func_to_file

    for func_name in func_names:
        metric = resolve_metric(func_name, evaluator, task_config)
        # Copy the metric's whole defining module so that helper functions and
        # module-level globals (e.g. `logger`) the metric depends on are
        # available to the offline replay script. Extracting only the function
        # via inspect.getsource drops those dependencies (NameError at replay).
        try:
            module_path = inspect.getfile(metric)
        except (OSError, TypeError):
            # Builtin/C function: fall back to AST extraction by name.
            rel_path, source = _find_builtin_function_source(func_name)
            dest_name = f"{func_name}.py"
            with open(os.path.join(code_dir, dest_name), "w", encoding="utf-8") as f:
                f.write(source)
            func_to_file[func_name] = dest_name
            continue

        dest_name = os.path.basename(module_path)
        dest_path = os.path.join(code_dir, dest_name)
        if not os.path.exists(dest_path):
            with open(module_path, "r", encoding="utf-8") as src_f:
                source = src_f.read()
            with open(dest_path, "w", encoding="utf-8") as f:
                f.write(f"# Source: {module_path}\n")
                f.write(source)
        func_to_file[func_name] = dest_name

    return func_to_file


def _task_config_from_env(env: "DesktopEnv") -> Dict[str, Any]:
    return {
        "id": getattr(env, "task_id", None),
        "_task_config_path": getattr(env, "_task_config_path", None),
    }


def _func_names(evaluator: Dict[str, Any]) -> List[str]:
    funcs = evaluator.get("func")
    if isinstance(funcs, str):
        return [funcs]
    if isinstance(funcs, list):
        return [str(name) for name in funcs]
    return []


def save_evaluator_artifacts(
    env: "DesktopEnv",
    metric_records: List[Dict[str, Any]],
    score: float,
    *,
    error: Optional[str] = None,
) -> Optional[str]:
    """Persist evaluator artifacts under env.eval_result_dir/evaluator."""
    if not artifacts_enabled():
        return None
    if not env.eval_result_dir:
        return None

    artifact_dir = os.path.join(env.eval_result_dir, "evaluator")
    metrics_root = os.path.join(artifact_dir, "metrics")
    code_dir = os.path.join(artifact_dir, "code")
    os.makedirs(artifact_dir, exist_ok=True)
    os.makedirs(metrics_root, exist_ok=True)

    evaluator = getattr(env, "evaluator", {}) or {}
    task_config = _task_config_from_env(env)
    func_names = _func_names(evaluator)

    try:
        func_to_file = save_metric_source(code_dir, env, func_names, task_config)
    except Exception as exc:
        logger.warning("Failed to save evaluator source code: %s", exc)
        func_to_file = {}

    for idx, record in enumerate(metric_records):
        metric_dir = os.path.join(metrics_root, str(idx))
        inputs_dir = os.path.join(metric_dir, "inputs")
        files_dir = os.path.join(inputs_dir, "files")
        os.makedirs(inputs_dir, exist_ok=True)

        copied_cache: Dict[str, str] = {}
        text_counter = [0]

        result_serialized = serialize_value(
            record.get("result_state"),
            files_dir,
            copied_cache,
            text_counter,
        )
        expected_serialized = serialize_value(
            record.get("expected_state"),
            files_dir,
            copied_cache,
            text_counter,
        )

        func_name = record.get("func_name", func_names[idx] if idx < len(func_names) else "unknown")
        with open(os.path.join(metric_dir, "func.txt"), "w", encoding="utf-8") as f:
            f.write(func_name)

        _json_dump(os.path.join(metric_dir, "result_getter.json"), record.get("result_getter_config"))
        _json_dump(os.path.join(metric_dir, "expected_getter.json"), record.get("expected_getter_config"))
        _json_dump(os.path.join(metric_dir, "options.json"), record.get("options") or {})
        _json_dump(os.path.join(inputs_dir, "result.json"), result_serialized)
        _json_dump(os.path.join(inputs_dir, "expected.json"), expected_serialized)

        metric_score = record.get("metric_score")
        if metric_score is not None:
            _json_dump(os.path.join(metric_dir, "metric_score.json"), {"score": metric_score})

        code_file = func_to_file.get(func_name)
        if code_file:
            with open(os.path.join(metric_dir, "code_file.txt"), "w", encoding="utf-8") as f:
                f.write(code_file)

    _json_dump(os.path.join(artifact_dir, "config.json"), evaluator)

    manifest = {
        "task_id": getattr(env, "task_id", None),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "score": score,
        "conj": evaluator.get("conj", "and"),
        "func": evaluator.get("func"),
        "postconfig": evaluator.get("postconfig", []),
        "code_files": func_to_file,
        "metric_count": len(metric_records),
        "error": error,
    }
    _json_dump(os.path.join(artifact_dir, "manifest.json"), manifest)
    write_replay_script(artifact_dir)
    logger.info("Saved evaluator artifacts to %s", artifact_dir)
    return artifact_dir


_REPLAY_SCRIPT = '''#!/usr/bin/env python3
"""Replay evaluator score from saved artifacts (offline, no VM required)."""

from __future__ import annotations

import importlib.util
import inspect
import json
import os
import sys
from typing import Any


def _artifact_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def _load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def deserialize_value(data: Any, inputs_dir: str) -> Any:
    if data is None:
        return None
    if isinstance(data, dict) and data.get("__type__") == "file":
        return os.path.join(inputs_dir, data["saved_as"])
    if isinstance(data, dict) and data.get("__type__") == "text_file":
        with open(os.path.join(inputs_dir, data["saved_as"]), "r", encoding="utf-8") as f:
            return f.read()
    if isinstance(data, dict) and data.get("__type__") == "repr":
        return data.get("value")
    if isinstance(data, list):
        return [deserialize_value(item, inputs_dir) for item in data]
    if isinstance(data, dict):
        return {key: deserialize_value(value, inputs_dir) for key, value in data.items()}
    return data


def _load_metric(code_dir: str, code_file: str, func_name: str):
    module_path = os.path.join(code_dir, code_file)
    if not os.path.isfile(module_path):
        raise FileNotFoundError(f"Metric source not found: {module_path}")
    spec = importlib.util.spec_from_file_location(f"replay_metric_{func_name}", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not import metric module: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    metric = getattr(module, func_name)
    if not callable(metric):
        raise TypeError(f"{func_name} is not callable in {module_path}")
    return metric


def _combine_scores(scores: list[float], conj: str) -> float:
    if not scores:
        return 0.0
    if conj == "or":
        return float(max(scores))
    return float(sum(scores) / len(scores))


def main() -> int:
    artifact_dir = _artifact_dir()
    manifest = _load_json(os.path.join(artifact_dir, "manifest.json"))
    config = _load_json(os.path.join(artifact_dir, "config.json"))
    conj = config.get("conj", manifest.get("conj", "and"))

    if config.get("func") == "infeasible":
        print("Task uses infeasible evaluator; replay is not applicable.")
        print(f"Saved score: {manifest.get('score')}")
        return 0

    metrics_root = os.path.join(artifact_dir, "metrics")
    code_dir = os.path.join(artifact_dir, "code")
    metric_dirs = []
    if os.path.isdir(metrics_root):
        metric_dirs = sorted(
            [
                os.path.join(metrics_root, name)
                for name in os.listdir(metrics_root)
                if os.path.isdir(os.path.join(metrics_root, name))
            ],
            key=lambda path: int(os.path.basename(path)),
        )

    scores: list[float] = []
    for metric_dir in metric_dirs:
        func_name = open(os.path.join(metric_dir, "func.txt"), "r", encoding="utf-8").read().strip()
        code_file = open(os.path.join(metric_dir, "code_file.txt"), "r", encoding="utf-8").read().strip()
        options = _load_json(os.path.join(metric_dir, "options.json"))
        expected_getter_config = _load_json(os.path.join(metric_dir, "expected_getter.json"))
        inputs_dir = os.path.join(metric_dir, "inputs")
        result_state = deserialize_value(_load_json(os.path.join(inputs_dir, "result.json")), inputs_dir)
        expected_path = os.path.join(inputs_dir, "expected.json")
        expected_state = None
        if os.path.isfile(expected_path):
            expected_state = deserialize_value(_load_json(expected_path), inputs_dir)

        metric = _load_metric(code_dir, code_file, func_name)
        positional = [
            param
            for param in inspect.signature(metric).parameters.values()
            if param.kind in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            )
        ]
        if len(positional) >= 2 and expected_getter_config is not None:
            metric_score = float(metric(result_state, expected_state, **options))
        else:
            metric_score = float(metric(result_state, **options))
        scores.append(metric_score)
        print(f"metric {os.path.basename(metric_dir)} ({func_name}): {metric_score}")

    replay_score = _combine_scores(scores, conj)
    saved_score = float(manifest.get("score", 0.0))
    print(f"Replay score: {replay_score}")
    print(f"Saved score:  {saved_score}")
    if abs(replay_score - saved_score) > 1e-9:
        print("WARNING: replay score differs from saved score", file=sys.stderr)
        return 1
    print("Replay matches saved score.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def write_replay_script(artifact_dir: str) -> str:
    replay_path = os.path.join(artifact_dir, _REPLAY_SCRIPT_NAME)
    with open(replay_path, "w", encoding="utf-8") as f:
        f.write(_REPLAY_SCRIPT)
    os.chmod(replay_path, 0o755)
    return replay_path
