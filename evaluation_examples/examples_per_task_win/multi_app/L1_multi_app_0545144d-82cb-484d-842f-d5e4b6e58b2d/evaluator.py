import json
from typing import Any, Dict, List


def check_json_settings(actual: str, expected: Dict, **options) -> float:
    """
    Check if all expected key-value pairs are present in the VS Code settings.json.

    Args:
        actual (str): path to the result settings.json file (from vm_file getter)
        expected (dict): dict containing key "expected" with the expected key-value pairs

    Return:
        float: 1.0 if all expected pairs match, 0.0 otherwise
    """
    if not actual:
        return 0.0

    try:
        with open(actual, 'r') as f:
            data = json.load(f)
    except Exception:
        return 0.0

    expect = expected.get('expected', {})

    for key, value in expect.items():
        if key not in data or data[key] != value:
            return 0.0

    return 1.0


def check_include_exclude(actual: str, rules: Dict[str, List[str]], **options) -> float:
    """
    Check whether a text file contains all required strings and excludes all forbidden strings.

    Args:
        actual (str): path to the result text file (from vm_file getter)
        rules (dict): dict with 'include' (list of strings that must all be present)
                      and 'exclude' (list of strings that must all be absent)

    Return:
        float: 1.0 if all conditions are met, 0.0 otherwise
    """
    if not actual:
        return 0.0

    try:
        with open(actual, 'r') as f:
            content = f.read()
    except Exception:
        return 0.0

    include = rules.get("include", [])
    exclude = rules.get("exclude", [])

    if all(r in content for r in include) and all(r not in content for r in exclude):
        return 1.0
    else:
        return 0.0
