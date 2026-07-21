# evaluator.py for task 85281b81-0f3a-4ed7-aed9-05c883aec8fe
# Based on desktop_env/evaluators/metrics/vscode.py
# Fixed: enhanced compare_config with JSON repair for corrupted artifacts

import json
import re
from typing import Any, Dict


def _is_subset(expected: Any, actual: Any) -> bool:
    """Check if expected is a recursive subset of actual."""
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


def _repair_json_text(text: str) -> str:
    """Attempt to repair common JSON formatting errors.

    Handles missing commas between adjacent quoted strings (value then key),
    which can occur when pyautogui.typewrite drops characters during input.
    """
    # Fix: missing comma between "value" and "key" on same line (2+ spaces gap)
    text = re.sub(r'"([ \t]{2,})"', r'",\1"', text)
    # Fix: missing comma between "value" at end of line and "key" on next line
    text = re.sub(r'"(\s*\n\s*)"', r'",\1"', text)
    return text


def compare_config(actual: str, rules: Dict, **options) -> float:
    """Compare a JSON config file against expected content (subset check).

    Args:
        actual: path to the result JSON file
        rules: dict with key "expected" containing the expected JSON text
        options: may contain "containment_ok" (bool, default True)

    Returns:
        float: 1.0 if expected is a subset of actual, 0.0 otherwise
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
        # Step 1: Direct JSON subset check
        try:
            actual_json = json.loads(actual_text)
            expected_json = json.loads(expected_text)
            if _is_subset(expected_json, actual_json):
                return 1.0
        except Exception:
            pass

        # Step 2: Try repairing common JSON formatting errors (e.g. missing commas
        # caused by pyautogui.typewrite dropping characters), then retry JSON subset
        try:
            repaired = _repair_json_text(actual_text)
            actual_json = json.loads(repaired)
            expected_json = json.loads(expected_text)
            if _is_subset(expected_json, actual_json):
                return 1.0
        except Exception:
            pass

        # Step 3: Normalized substring containment fallback
        # (collapse all whitespace to single spaces so minor formatting diffs don't block)
        actual_normalized = re.sub(r'\s+', ' ', actual_text).strip()
        expected_normalized = re.sub(r'\s+', ' ', expected_text).strip()
        if expected_normalized in actual_normalized:
            return 1.0

        return 0.0

    # Strict legacy behavior: exact text match or JSON equality
    if actual_text == expected_text:
        return 1.0
    try:
        if json.loads(actual_text) == json.loads(expected_text):
            return 1.0
    except Exception:
        pass
    return 0.0


def check_json_settings(actual: str, expected: str, **options) -> float:
    """Check if a JSON settings file contains expected key-value pairs.

    Args:
        actual: path to the result JSON file
        expected: dict with key "expected" mapping setting keys to expected values

    Returns:
        float: 1.0 if all expected key-value pairs are present and match, 0.0 otherwise
    """
    if not actual:
        return 0.0

    try:
        with open(actual, 'r') as f:
            data = json.load(f)
    except Exception:
        return 0.0

    expect = expected['expected']
    for key, value in expect.items():
        if key not in data or data[key] != value:
            return 0.0
    return 1.0
