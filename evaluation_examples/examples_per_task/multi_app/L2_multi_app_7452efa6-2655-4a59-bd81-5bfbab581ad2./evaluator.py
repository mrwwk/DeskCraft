import json
import os
from typing import Any, Dict, List


def check_json_settings(actual: str, expected: str, **options) -> float:
    """
    Check that all expected key-value pairs exist in the VS Code settings.json file.

    Args:
        actual (str): path to the captured settings.json file
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

    expect = expected['expected']

    for key, value in expect.items():
        if key not in data or data[key] != value:
            return 0.0

    return 1.0


def is_expected_active_tab_approximate(active_tab_info: Dict[str, str], rule: Dict[str, Any]) -> float:
    """
    Checks if the expected active tab is open in Chrome, ignoring query parameters in the URL.

    Args:
        active_tab_info (dict): dict with 'url' key from active_tab_info getter
        rule (dict): dict with 'type' and 'url' keys specifying the expected URL

    Return:
        float: 1.0 if the active tab URL matches (ignoring query params), 0.0 otherwise
    """
    if not active_tab_info:
        return 0.0

    match_type = rule['type']

    if match_type == "url":
        expected_url = rule['url']
        if isinstance(active_tab_info, dict):
            actual_url = active_tab_info.get('url', None)
        else:
            actual_url = active_tab_info
        from urllib.parse import urlparse, urlunparse

        def strip_query(url):
            if not url:
                return url
            parsed = urlparse(url)
            return urlunparse(parsed._replace(query=""))

        if strip_query(expected_url) == strip_query(actual_url):
            return 1.0
        else:
            return 0.0
    else:
        return 0.0


def check_include_exclude(result: str, rules: Dict[str, List[str]], **options) -> float:
    """
    Check that the result contains all strings in 'include' and none in 'exclude'.

    When result is a file path (from vm_file getter), the file content is read first.
    When result is a raw string (from vm_command_line getter), it is used directly.

    Args:
        result (str): file path or raw string content to check
        rules (dict): dict with 'include' (required substrings) and 'exclude' (forbidden substrings)

    Return:
        float: 1.0 if all include strings are present and no exclude strings are present, 0.0 otherwise
    """
    if result is None:
        return 0.0

    # If result looks like a file path that exists, read its content
    content = result
    if os.path.exists(result):
        try:
            with open(result, 'r') as f:
                content = f.read()
        except Exception:
            return 0.0

    include = rules.get("include", [])
    exclude = rules.get("exclude", [])

    if all(r in content for r in include) and all(r not in content for r in exclude):
        return 1.0
    else:
        return 0.0
