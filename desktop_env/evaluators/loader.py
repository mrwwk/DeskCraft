from __future__ import annotations

import hashlib
import importlib.util
import logging
import os
import sys
from types import ModuleType
from typing import Any, Callable, Dict

from desktop_env.evaluators import metrics

logger = logging.getLogger("desktopenv.evaluators.loader")


_MODULE_CACHE: Dict[str, ModuleType] = {}


def _resolve_evaluator_file(evaluator: Dict[str, Any], task_config: Dict[str, Any]) -> str:
    evaluator_file = evaluator.get("file")
    if not isinstance(evaluator_file, str) or not evaluator_file:
        raise ValueError("evaluator.file must be a non-empty string")

    evaluator_file = os.path.expandvars(os.path.expanduser(evaluator_file))
    if os.path.isabs(evaluator_file):
        return os.path.abspath(evaluator_file)

    task_config_path = task_config.get("_task_config_path")
    if not task_config_path:
        raise ValueError(
            "Relative evaluator.file requires task_config['_task_config_path'] "
            "so it can be resolved against the task JSON directory"
        )

    return os.path.abspath(os.path.join(os.path.dirname(task_config_path), evaluator_file))


def _load_module_from_file(module_path: str) -> ModuleType:
    if not os.path.isfile(module_path):
        raise FileNotFoundError(f"Evaluator file not found: {module_path}")

    cached = _MODULE_CACHE.get(module_path)
    if cached is not None:
        return cached

    digest = hashlib.sha256(module_path.encode("utf-8")).hexdigest()[:16]
    module_name = f"desktop_env_task_evaluator_{digest}"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not create import spec for evaluator file: {module_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    _MODULE_CACHE[module_path] = module
    return module


def resolve_metric(func_name: str, evaluator: Dict[str, Any], task_config: Dict[str, Any]) -> Callable:
    """Resolve a metric function from a per-task file or the legacy metrics module.

    Resolution order:
    1. If ``evaluator.file`` is set and ``_task_config_path`` is available, load the
       per-task ``evaluator.py`` and return ``getattr(module, func_name)``.
    2. Otherwise (no ``file``, or ``file`` set but ``_task_config_path`` missing),
       fall back to ``getattr(metrics, func_name)`` so that un-updated callers keep
       working against the central metrics registry.
    """
    if not isinstance(func_name, str):
        raise TypeError(f"Evaluator function name must be a string, got {type(func_name).__name__}")

    evaluator_file = evaluator.get("file")
    task_config_path = task_config.get("_task_config_path") if task_config else None

    if evaluator_file and task_config_path:
        module_path = _resolve_evaluator_file(evaluator, task_config)
        module = _load_module_from_file(module_path)
        try:
            metric = getattr(module, func_name)
        except AttributeError as exc:
            raise AttributeError(
                f"Evaluator function '{func_name}' not found in file {module_path}"
            ) from exc

        if not callable(metric):
            raise TypeError(f"Evaluator attribute '{func_name}' in {module_path} is not callable")
        return metric

    if evaluator_file and not task_config_path:
        # Per-task evaluator requested but the caller did not inject _task_config_path.
        # Fall back to the central metrics registry so the task still evaluates.
        logger.warning(
            "evaluator.file is set (%r) but _task_config_path is missing; "
            "falling back to central metrics for func %r", evaluator_file, func_name
        )

    return getattr(metrics, func_name)
