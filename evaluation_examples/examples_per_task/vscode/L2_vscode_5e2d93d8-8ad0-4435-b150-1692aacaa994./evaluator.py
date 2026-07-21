import json
from pathlib import PurePosixPath


def _normalize_folder(workspace_file: str, raw_path: str):
    if not isinstance(raw_path, str):
        return None
    path = PurePosixPath(raw_path)
    if not path.is_absolute():
        path = PurePosixPath(workspace_file).parent.joinpath(path)
    return str(path)


def check_workspace_multiroot(actual: str, expected: dict, **options) -> float:
    if not actual:
        return 0.0

    try:
        with open(actual, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        return 0.0

    rules = expected.get('expected', {})
    expected_folders = rules.get('folders', [])
    actual_folders = [
        _normalize_folder(actual, item.get('path'))
        for item in data.get('folders', [])
        if isinstance(item, dict)
    ]
    if None in actual_folders:
        return 0.0
    if set(actual_folders) != set(expected_folders) or len(actual_folders) != len(expected_folders):
        return 0.0

    settings = data.get('settings', {})
    for key, value in rules.get('settings', {}).items():
        if settings.get(key) != value:
            return 0.0

    return 1.0
