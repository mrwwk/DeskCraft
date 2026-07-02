"""Helpers for locating and loading task configs.

``load_task_config`` reads a task JSON and injects the synthetic
``_task_config_path`` key (absolute path to the task.json) that the per-task
evaluator loader uses to resolve a relative ``evaluator.file``.

``resolve_task_config_path`` finds the actual task file on disk, preferring the
reorganized per-task directories (``examples_per_task/<domain>/<example_id>/task.json``)
and falling back to the legacy flat ``examples/<domain>/<example_id>.json`` layout.
It tolerates the differing ``--test_config_base_dir`` conventions across runners
(some include the ``examples`` segment in the base, some do not).
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict


def load_task_config(path: str) -> Dict[str, Any]:
    """Load a task JSON file and inject ``_task_config_path``.

    The injected value is the absolute path to ``path``. The per-task evaluator
    loader resolves a relative ``evaluator.file`` against the directory of this
    path, so a task's ``evaluator.py`` is found next to its ``task.json``.
    """
    with open(path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    cfg["_task_config_path"] = os.path.abspath(path)
    return cfg


def _revise_task_enabled() -> bool:
    """Return True when runners should prefer ``revise_task/task.json`` over the
    original task config. Opt-in, OFF by default (``DESKCRAFT_USE_REVISE_TASK=1``
    to enable). When enabled, ``resolve_task_config_path`` prepends revise_task
    candidates so a run pointed at a results tree loads repaired evaluators.
    """
    return os.environ.get("DESKCRAFT_USE_REVISE_TASK", "0") == "1"


def resolve_task_config_path(base_dir: str, domain: str, example_id: str) -> str:
    """Resolve the on-disk task config path for a (domain, example_id).

    Runners historically used inconsistent ``--test_config_base_dir`` conventions
    (some pass ``evaluation_examples`` and append ``examples/<domain>/...``;
    others pass ``evaluation_examples/ubuntu_examples`` and append
    ``<domain>/...``), and the actual files live under ``ubuntu_examples/`` while
    the reorganized per-task dirs live under ``examples_per_task/``. To tolerate
    every convention we try a comprehensive candidate list and return the first
    existing file.

    Priority:
      0. (only when ``DESKCRAFT_USE_REVISE_TASK=1``)
         ``<base>/<domain>/<id>/revise_task/task.json``              (repaired)
         ``<base>/examples_per_task/<domain>/<id>/revise_task/task.json``
      1. ``<base>/examples_per_task/<domain>/<id>/task.json``      (new per-task)
      2. ``<base>/examples_per_task/<domain>/<id>./task.json``     (new per-task,
         tolerates task directories accidentally created with a trailing dot)
      3. ``<parent(base)>/examples_per_task/<domain>/<id>/task.json``
         (covers base = ``.../ubuntu_examples`` or ``.../examples``)
      4. ``<parent(base)>/examples_per_task/<domain>/<id>./task.json``
      5. ``<base>/<domain>/<id>/task.json``                        (per-task sibling)
      6. ``<base>/<domain>/<id>./task.json``                       (per-task sibling,
         tolerates trailing-dot directories)
      7. ``<base>/examples/<domain>/<id>/task.json``
      8. ``<base>/ubuntu_examples/<domain>/<id>/task.json``
      9. ``<base>/<domain>/<id>.json``                             (flat, base=.../ubuntu_examples)
      10. ``<base>/examples/<domain>/<id>.json``                   (flat, base=evaluation_examples)
      11. ``<base>/ubuntu_examples/<domain>/<id>.json``            (flat, base=evaluation_examples)

    If none exist, candidate #1 is returned so a subsequent ``open()`` raises a
    clear ``FileNotFoundError``. When the revise_task switch is on and no
    revise_task file exists, resolution falls through to the normal candidates,
    so the switch is a safe no-op for tasks without a repair.
    """
    parent = os.path.dirname(os.path.normpath(base_dir))
    candidates: list[str] = []
    if _revise_task_enabled():
        candidates.append(os.path.join(base_dir, domain, example_id, "revise_task", "task.json"))
        candidates.append(os.path.join(base_dir, domain, f"{example_id}.", "revise_task", "task.json"))
        candidates.append(os.path.join(base_dir, "examples_per_task", domain, example_id, "revise_task", "task.json"))
        candidates.append(os.path.join(base_dir, "examples_per_task", domain, f"{example_id}.", "revise_task", "task.json"))
    candidates.extend([
        os.path.join(base_dir, "examples_per_task", domain, example_id, "task.json"),
        os.path.join(base_dir, "examples_per_task", domain, f"{example_id}.", "task.json"),
        os.path.join(parent, "examples_per_task", domain, example_id, "task.json"),
        os.path.join(parent, "examples_per_task", domain, f"{example_id}.", "task.json"),
        os.path.join(base_dir, domain, example_id, "task.json"),
        os.path.join(base_dir, domain, f"{example_id}.", "task.json"),
        os.path.join(base_dir, "examples", domain, example_id, "task.json"),
        os.path.join(base_dir, "ubuntu_examples", domain, example_id, "task.json"),
        os.path.join(base_dir, domain, f"{example_id}.json"),
        os.path.join(base_dir, "examples", domain, f"{example_id}.json"),
        os.path.join(base_dir, "ubuntu_examples", domain, f"{example_id}.json"),
    ])
    seen: set = set()
    for candidate in candidates:
        key = os.path.normpath(candidate)
        if key in seen:
            continue
        seen.add(key)
        if os.path.isfile(key):
            return key
    return candidates[0]
