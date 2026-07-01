"""Trajectory loading for EasyVis DeskCraft — adapted from monitor/task_service.py."""

import glob
import json
import os
from datetime import datetime


def _load_trajectory_label(result_dir: str):
    """Load the ``label`` field from trajectory_label.json if present."""
    label_file = os.path.join(result_dir, "trajectory_label.json")
    if not os.path.isfile(label_file):
        return None
    try:
        with open(label_file, "r", encoding="utf-8") as f:
            label_data = json.load(f)
        return label_data.get("label")
    except (json.JSONDecodeError, OSError):
        return None


def _load_json_file(path: str):
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _load_reward_components(result_dir: str) -> tuple[dict | None, str | None]:
    """Load per-component scores from cache/_cua_reward_components.json if present."""
    components_file = os.path.join(result_dir, "cache", "_cua_reward_components.json")
    if not os.path.isfile(components_file):
        return None, None
    try:
        with open(components_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or not isinstance(data.get("components"), list):
            return None, None
        return data, components_file
    except (json.JSONDecodeError, OSError):
        return None, None


def _load_interaction_log(result_dir: str) -> list | None:
    data = _load_json_file(os.path.join(result_dir, "interaction_log.json"))
    return data if isinstance(data, list) else None


def _load_evaluator_manifest(result_dir: str) -> tuple[dict | None, str | None]:
    manifest_path = os.path.join(result_dir, "evaluator", "manifest.json")
    data = _load_json_file(manifest_path)
    if isinstance(data, dict):
        return data, manifest_path
    return None, None


def _load_evaluator_audit(result_dir: str) -> tuple[dict | None, str | None]:
    audit_path = os.path.join(result_dir, "evaluator_audit.json")
    data = _load_json_file(audit_path)
    if isinstance(data, dict):
        return data, audit_path
    return None, None


def _safe_path(base_dir: str, *parts: str) -> str:
    base = os.path.abspath(os.path.expanduser(base_dir))
    path = os.path.abspath(os.path.join(base, *parts))
    if path != base and not path.startswith(base + os.sep):
        raise ValueError("Invalid path")
    return path


def resolve_result_task_dir(results_dir: str, task_id: str, domain: str | None = None) -> str | None:
    """Resolve task result directory (flat or domain-nested layout)."""
    results_dir = os.path.abspath(os.path.expanduser(results_dir))
    if not os.path.isdir(results_dir):
        return None

    candidates = []
    if domain:
        candidates.append(os.path.join(results_dir, domain, task_id))
    candidates.append(os.path.join(results_dir, task_id))

    for path in candidates:
        if os.path.isdir(path):
            return path

    try:
        for name in os.listdir(results_dir):
            nested = os.path.join(results_dir, name, task_id)
            if os.path.isdir(nested):
                return nested
    except OSError:
        pass
    return None


def load_trajectory(results_dir: str, task_id: str, domain: str | None = None) -> dict:
    """Load trajectory status and steps from a results folder."""
    results_dir = os.path.abspath(os.path.expanduser(results_dir))
    if not os.path.isdir(results_dir):
        return {"error": f"Results directory not found: {results_dir}", "found": False}

    result_dir = resolve_result_task_dir(results_dir, task_id, domain)
    if result_dir is None:
        return {
            "found": False,
            "status": "Not Started",
            "progress": 0,
            "total_steps": 0,
            "steps": [],
            "result": None,
            "has_recording": False,
        }

    traj_file = os.path.join(result_dir, "traj.jsonl")
    result_file = os.path.join(result_dir, "result.txt")
    recording_mp4 = os.path.join(result_dir, "recording.mp4")
    recording_webm = os.path.join(result_dir, "recording.webm")

    reward_components, reward_components_path = _load_reward_components(result_dir)
    interaction_log = _load_interaction_log(result_dir)
    evaluator_manifest, evaluator_manifest_path = _load_evaluator_manifest(result_dir)
    evaluator_audit, evaluator_audit_path = _load_evaluator_audit(result_dir)

    def _attach_extras(resp: dict) -> dict:
        if reward_components is not None:
            resp["reward_components"] = reward_components
            resp["reward_components_path"] = reward_components_path
        if interaction_log is not None:
            resp["interaction_log"] = interaction_log
        if evaluator_manifest is not None:
            resp["evaluator_manifest"] = evaluator_manifest
            resp["evaluator_manifest_path"] = evaluator_manifest_path
        if evaluator_audit is not None:
            resp["evaluator_audit"] = evaluator_audit
            resp["evaluator_audit_path"] = evaluator_audit_path
        return resp

    if not os.path.isfile(traj_file):
        resp = {
            "found": True,
            "status": "Preparing",
            "progress": 0,
            "total_steps": 0,
            "steps": [],
            "result": None,
            "has_recording": os.path.isfile(recording_mp4) or os.path.isfile(recording_webm),
            "trajectory_label": _load_trajectory_label(result_dir),
        }
        return _attach_extras(resp)

    steps = []
    try:
        with open(traj_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        steps.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except OSError as e:
        return {"error": str(e), "found": True}

    if not steps:
        resp = {
            "found": True,
            "status": "Initializing",
            "progress": 0,
            "total_steps": 0,
            "steps": [],
            "result": None,
            "has_recording": os.path.isfile(recording_mp4) or os.path.isfile(recording_webm),
            "trajectory_label": _load_trajectory_label(result_dir),
        }
        return _attach_extras(resp)

    last_step = steps[-1]
    actual_step_num = last_step.get("step_num", len(steps))

    if last_step.get("done", False):
        status = "Done"
    elif last_step.get("Error", False):
        status = "Error"
    elif actual_step_num >= 150:
        status = "Done (Max Steps)"
    else:
        status = "Running"

    result_content = None
    if status.startswith("Done") and os.path.isfile(result_file):
        with open(result_file, "r", encoding="utf-8") as f:
            result_content = f.read().strip()

    last_update = None
    if "action_timestamp" in last_step:
        ts = str(last_step["action_timestamp"])
        try:
            base_ts = ts[:15] if "@" in ts else ts
            last_update = datetime.strptime(base_ts, "%Y%m%d@%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            last_update = ts

    step_0_files = sorted(glob.glob(os.path.join(result_dir, "step_0_*.png")))
    step_0_file = os.path.basename(step_0_files[0]) if step_0_files else ""

    slim_steps = []
    for i, step in enumerate(steps):
        meta = step.get("metadata") or {}
        if i > 0:
            screenshot_before = steps[i - 1].get("screenshot_file", "")
        else:
            screenshot_before = step_0_file
        slim_steps.append({
            "step_num": step.get("step_num"),
            "action": step.get("action", ""),
            "screenshot_file": step.get("screenshot_file", ""),
            "screenshot_before": screenshot_before,
            "done": step.get("done", False),
            "action_description": step.get("natural_language_action") or meta.get("action", ""),
            "thought": step.get("thought") or meta.get("thought", ""),
            "response": step.get("response", ""),
            "phase": step.get("phase"),
        })

    trajectory_label = _load_trajectory_label(result_dir)

    resp = {
        "found": True,
        "status": status,
        "progress": actual_step_num,
        "total_steps": len(steps),
        "last_update": last_update,
        "steps": slim_steps,
        "step_0_file": step_0_file,
        "result": result_content,
        "has_recording": os.path.isfile(recording_mp4) or os.path.isfile(recording_webm),
        "trajectory_label": trajectory_label,
    }
    return _attach_extras(resp)
