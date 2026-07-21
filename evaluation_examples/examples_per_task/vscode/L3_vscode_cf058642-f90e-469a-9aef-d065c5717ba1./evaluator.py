import json
from pathlib import PurePosixPath


def _normalize_folder(workspace_file: str, raw_path: str):
    if not isinstance(raw_path, str):
        return None
    path = PurePosixPath(raw_path)
    if not path.is_absolute():
        path = PurePosixPath(workspace_file).parent.joinpath(path)
    return str(path)


def check_json_settings(actual: str, expected: dict, **options) -> float:
    if not actual:
        return 0.0
    try:
        with open(actual, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        return 0.0

    for key, value in expected.get('expected', {}).items():
        if data.get(key) != value:
            return 0.0
    return 1.0


def check_workspace_setup(actual: str, rules: dict, **options) -> float:
    if not actual:
        return 0.0

    try:
        with open(actual, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        return 0.0

    expected = rules.get('expected', {})
    actual_folders = [
        _normalize_folder(actual, item.get('path'))
        for item in data.get('folders', [])
        if isinstance(item, dict)
    ]
    expected_folders = expected.get('folders', [])
    if None in actual_folders:
        return 0.0
    if set(actual_folders) != set(expected_folders) or len(actual_folders) != len(expected_folders):
        return 0.0

    settings = data.get('settings', {})
    for key, value in expected.get('settings', {}).items():
        if settings.get(key) != value:
            return 0.0

    recs = data.get('extensions', {}).get('recommendations', [])
    if set(recs) != set(expected.get('recommendations', [])):
        return 0.0

    return 1.0


def check_tasks_config_relaxed(actual: str, rules: dict, **options) -> float:
    if not actual:
        return 0.0

    try:
        with open(actual, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        return 0.0

    expected = rules.get('expected', {})
    if data.get('version') != expected.get('version'):
        return 0.0

    tasks = {item.get('label'): item for item in data.get('tasks', []) if isinstance(item, dict)}
    for required in expected.get('tasks', []):
        label = required.get('label')
        actual_task = tasks.get(label)
        if actual_task is None:
            return 0.0
        if actual_task.get('type') != required.get('type'):
            return 0.0
        if actual_task.get('command') != required.get('command'):
            return 0.0

    return 1.0
