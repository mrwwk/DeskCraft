"""
Evaluator for L2_multi_app_4f35b6e1: Chrome + VS Code multi-step task.

Three metrics (conj="and"):
  1. check_chrome_tab_url  – verify Chrome has a tab with the target URL
  2. check_trimmed_match   – verify the saved URL file contains the exact URL
  3. check_json_settings   – verify VS Code settings.json has correct values
"""

import json
import os


def check_chrome_tab_url(result: str, rules: dict, **options) -> float:
    """
    Check that Chrome DevTools Protocol JSON shows a tab with the target URL.

    Args:
        result: JSON string from ``curl -s http://localhost:9222/json``
        rules:  dict with key "url" containing the expected URL
    """
    if result is None:
        return 0.0

    target_url = rules.get("url", "")
    if not target_url:
        return 0.0

    try:
        tabs = json.loads(result)
    except (json.JSONDecodeError, TypeError, ValueError):
        return 0.0

    if not isinstance(tabs, list):
        return 0.0

    for tab in tabs:
        if not isinstance(tab, dict):
            continue
        tab_url = tab.get("url", "")
        # Accept exact match or URL that starts with the target (handles trailing
        # slashes / fragments / query params that Chrome may append).
        if tab_url == target_url or tab_url.startswith(target_url):
            return 1.0

    return 0.0


def check_trimmed_match(result: str, rules: dict, **options) -> float:
    """
    Check that the result string, after stripping whitespace, equals the expected string.

    Args:
        result: command output string (e.g. from ``cat ~/Desktop/docs_url.txt``)
        rules:  dict with key "expected" containing the exact expected string
    """
    if result is None:
        return 0.0

    expected = rules.get("expected", "")
    if result.strip() == expected.strip():
        return 1.0
    return 0.0


def check_json_settings(actual: str, expected: dict, **options) -> float:
    """
    Check that a JSON file contains all expected key-value pairs.

    Copied and adapted from desktop_env.evaluators.metrics.vscode.

    Args:
        actual:   path to the settings.json file (from vm_file getter)
        expected: dict with key "expected" mapping to a dict of key-value pairs
                  that must all be present in the JSON file
    """
    if not actual:
        return 0.0

    if not os.path.exists(actual):
        return 0.0

    try:
        with open(actual, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError, OSError):
        return 0.0

    expect = expected.get("expected", {})
    if not isinstance(expect, dict):
        return 0.0

    for key, value in expect.items():
        if key not in data or data[key] != value:
            return 0.0

    return 1.0
