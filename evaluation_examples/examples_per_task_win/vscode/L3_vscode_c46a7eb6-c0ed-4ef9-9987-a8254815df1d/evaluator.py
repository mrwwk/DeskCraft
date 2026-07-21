import json
from typing import Any, Dict


def _normalize_task_commands(obj: Any) -> None:
    """Normalize VS Code tasks.json command format in-place.

    VS Code tasks.json supports two semantically equivalent formats:
      1. "command": "npm run build"          (pure command string)
      2. "command": "npm", "args": ["run", "build"]  (command + args)

    This function merges format 2 into format 1 so that subsequent
    JSON comparison can treat them as equivalent.
    """
    if isinstance(obj, dict):
        # If this dict looks like a VS Code task with command + args,
        # merge them into a single command string.
        if (
            "command" in obj
            and "args" in obj
            and isinstance(obj["args"], list)
            and obj["args"]
        ):
            obj["command"] = obj["command"] + " " + " ".join(str(a) for a in obj["args"])
            del obj["args"]
        # Recurse into all values.
        for v in obj.values():
            _normalize_task_commands(v)
    elif isinstance(obj, list):
        for item in obj:
            _normalize_task_commands(item)


def _is_subset(expected: Any, actual: Any) -> bool:
    """Check whether *expected* is a structural subset of *actual*.

    - For dicts: every key in expected must exist in actual and its value
      must be a subset of the corresponding value in actual.
    - For lists: strict equality (order and content must match).
    - For scalars: exact equality.
    """
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return False
        for k, v in expected.items():
            if k not in actual:
                return False
            if not _is_subset(v, actual[k]):
                return False
        return True

    if isinstance(expected, list):
        return expected == actual

    return expected == actual


def compare_config(actual: str, rules: Dict, **options) -> float:
    """Compare a VS Code config JSON file against expected content.

    Args:
        actual: Path to the result JSON file produced by the agent.
        rules:  Dict with key "expected" containing the expected JSON as a
                string (for extensions.json / tasks.json) or dict.
        options: Optional flags (containment_ok, etc.).

    Returns:
        1.0 if the expected config is a subset of the actual config,
        0.0 otherwise.
    """
    if not actual:
        return 0.0

    expected_text = rules.get("expected")
    if not expected_text:
        return 0.0

    with open(actual, "r", encoding="utf-8") as f:
        actual_text = f.read()

    containment_ok = options.get("containment_ok", True)

    if containment_ok:
        try:
            actual_json = json.loads(actual_text)
            expected_json = json.loads(expected_text)

            # Normalize VS Code tasks.json command+args format so that
            # "command": "npm", "args": ["run", "build"] is treated as
            # equivalent to "command": "npm run build".
            _normalize_task_commands(expected_json)
            _normalize_task_commands(actual_json)

            if _is_subset(expected_json, actual_json):
                return 1.0
        except Exception:
            # Fallback: substring containment
            if expected_text.strip() in actual_text:
                return 1.0
        return 0.0

    # Strict legacy behavior (containment_ok=False)
    if actual_text == expected_text:
        return 1.0

    try:
        if json.loads(actual_text) == json.loads(expected_text):
            return 1.0
    except Exception:
        pass

    return 0.0


def check_json_settings(actual: str, expected: str, **options) -> float:
    """Check that settings.json contains all expected key-value pairs.

    Args:
        actual:   Path to the result settings.json file.
        expected: Dict with key "expected" containing the expected settings
                  as a nested dict.

    Returns:
        1.0 if every expected key exists in actual with the expected value,
        0.0 otherwise.
    """
    if not actual:
        return 0.0

    try:
        with open(actual, "r") as f:
            data = json.load(f)
    except Exception:
        return 0.0

    expect = expected["expected"]

    for key, value in expect.items():
        if key not in data or data[key] != value:
            return 0.0

    return 1.0
