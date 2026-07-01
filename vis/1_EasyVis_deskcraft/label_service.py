"""Task labeling persistence for EasyVis."""

import json
import os
from datetime import datetime, timezone

from trajectory_service import resolve_result_task_dir

LABEL_FILENAME = "easyvis_label.json"


def label_path_for_task(results_dir: str, task_id: str, domain: str | None = None) -> str:
    task_dir = resolve_result_task_dir(results_dir, task_id, domain)
    if not task_dir:
        raise ValueError(f"Task result directory not found: {task_id}")
    return os.path.join(task_dir, LABEL_FILENAME)


def _read_label_file(path: str) -> dict | None:
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except (json.JSONDecodeError, OSError):
        return None


def load_all_labels(results_dir: str) -> dict:
    results_dir = os.path.abspath(os.path.expanduser(results_dir))
    if not os.path.isdir(results_dir):
        return {}

    labels: dict[str, dict] = {}
    try:
        entries = os.listdir(results_dir)
    except OSError:
        return {}

    for name in entries:
        top = os.path.join(results_dir, name)
        if not os.path.isdir(top):
            continue

        label = _read_label_file(os.path.join(top, LABEL_FILENAME))
        if label and label.get("status") in ("usable", "unusable"):
            labels[name] = label
            continue

        try:
            sub_entries = os.listdir(top)
        except OSError:
            continue
        for sub in sub_entries:
            task_dir = os.path.join(top, sub)
            if not os.path.isdir(task_dir):
                continue
            label = _read_label_file(os.path.join(task_dir, LABEL_FILENAME))
            if label and label.get("status") in ("usable", "unusable"):
                labels[sub] = label

    return labels


def get_label(results_dir: str, task_id: str, domain: str | None = None) -> dict | None:
    try:
        return _read_label_file(label_path_for_task(results_dir, task_id, domain))
    except ValueError:
        return None


def save_label(
    results_dir: str,
    task_id: str,
    status: str,
    reason: str = "",
    reason_category: str = "",
    domain: str | None = None,
) -> dict:
    if status not in ("usable", "unusable"):
        raise ValueError("status must be 'usable' or 'unusable'")
    if reason_category and reason_category not in ("instruction", "config", "evaluator", "other"):
        raise ValueError("reason_category must be 'instruction', 'config', 'evaluator', or 'other'")
    if status == "unusable" and reason_category == "other" and not reason.strip():
        raise ValueError("reason is required when reason_category is 'other'")

    results_dir = os.path.abspath(os.path.expanduser(results_dir))
    if not os.path.isdir(results_dir):
        raise ValueError(f"Results directory not found: {results_dir}")

    task_dir = resolve_result_task_dir(results_dir, task_id, domain)
    if not task_dir:
        raise ValueError(f"Task result directory not found: {task_id}")

    entry = {
        "task_id": task_id,
        "status": status,
        "reason_category": reason_category if status == "unusable" else "",
        "reason": reason.strip() if status == "unusable" else "",
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
    }
    label_path = os.path.join(task_dir, LABEL_FILENAME)
    with open(label_path, "w", encoding="utf-8") as f:
        json.dump(entry, f, indent=2, ensure_ascii=False)
    return entry


def delete_label(results_dir: str, task_id: str, domain: str | None = None) -> bool:
    try:
        label_path = label_path_for_task(results_dir, task_id, domain)
    except ValueError:
        return False
    if not os.path.isfile(label_path):
        return False
    os.remove(label_path)
    return True
