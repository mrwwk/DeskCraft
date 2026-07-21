import json
from typing import Any, Dict, List
from urllib.parse import urlparse, urlunparse


def check_include_exclude(result: str, rules: Dict[str, List[str]]) -> float:
    """Check that include substrings are present and exclude substrings are absent in result."""
    if result is None:
        return 0.

    include = rules.get("include", [])
    exclude = rules.get("exclude", [])
    if all(r in result for r in include) and all(r not in result for r in exclude):
        return 1.
    else:
        return 0.


def check_json_settings(actual: str, expected: dict, **options) -> float:
    """
    Check that expected key-value pairs exist in a VS Code settings.json file.

    Args:
        actual (str): path to the settings.json file
        expected (dict): dict containing key "expected" with key-value pairs to check

    Returns:
        float: 1.0 if all expected pairs match, 0.0 otherwise
    """
    if not actual:
        return 0.

    try:
        with open(actual, 'r') as f:
            data = json.load(f)
    except Exception:
        return 0.0

    expect = expected.get('expected', {})

    # Check if all expected key-value pairs are in the actual data
    for key, value in expect.items():
        if key not in data or data[key] != value:
            return 0.0

    return 1.0


def is_expected_active_tab_approximate(active_tab_info: Dict[str, str], rule: Dict[str, Any]) -> float:
    """
    Checks if the expected active tab is open in Chrome, ignoring query parameters in the URL.

    Args:
        active_tab_info (dict): dict with 'url' key from active_tab_info getter
        rule (dict): dict with 'type' and 'url' keys

    Returns:
        float: 1.0 if URLs match (ignoring query params), 0.0 otherwise
    """
    if not active_tab_info:
        return 0.

    match_type = rule.get('type')

    if match_type == "url":
        expected_url = rule.get('url', '')
        if isinstance(active_tab_info, dict):
            actual_url = active_tab_info.get('url', None)
        else:
            actual_url = active_tab_info

        if not actual_url:
            return 0.

        def strip_query(url):
            parsed = urlparse(url)
            return urlunparse(parsed._replace(query=""))

        if strip_query(expected_url) == strip_query(actual_url):
            return 1.
        else:
            return 0.
    else:
        return 0.
