"""
Evaluator for deploy_config_full_pipeline_os_vscode_chrome (5811683a).
Checks four conditions with conj="and":
  1. /tmp/fastapi_logs/ directory exists
  2. ~/Desktop/env_summary.txt contains project=FastAPI Service and author=dev_team
  3. VS Code settings.json has editor.tabSize=2, editor.rulers=[88], files.exclude with __pycache__/.env/venv
  4. Chrome active tab URL matches https://fastapi.tiangolo.com/ (ignoring query params)
"""
import json
import re
from typing import Any, Dict, List
from urllib.parse import urlparse, urlunparse


def check_include_exclude(result: str, rules: Dict[str, List[str]], **options) -> float:
    """
    Check if result string contains all 'include' strings and none of the 'exclude' strings.

    Args:
        result: The command output string to check.
        rules: Dict with 'include' (list of required substrings) and 'exclude' (list of forbidden substrings).

    Returns:
        1.0 if all include strings are present and no exclude strings are present, else 0.0.
    """
    if result is None:
        return 0.0

    include = rules.get("include", [])
    exclude = rules.get("exclude", [])
    if all(r in result for r in include) and all(r not in result for r in exclude):
        return 1.0
    else:
        return 0.0


def check_json_settings(actual: str, expected: Dict, **options) -> float:
    """
    Check if a JSON file contains all expected key-value pairs.

    Args:
        actual: Path to the JSON file.
        expected: Dict with key 'expected' containing the expected key-value pairs.

    Returns:
        1.0 if all expected pairs are present and match, else 0.0.
    """
    if not actual:
        return 0.0

    try:
        with open(actual, 'r') as f:
            data = json.load(f)
    except Exception:
        return 0.0

    expect = expected.get('expected', {})
    if not expect:
        return 0.0

    for key, value in expect.items():
        if key not in data:
            return 0.0
        if data[key] != value:
            return 0.0

    return 1.0


def is_expected_active_tab_approximate(active_tab_info: Dict[str, str], rule: Dict[str, Any], **options) -> float:
    """
    Check if the active Chrome tab URL matches the expected URL, ignoring query parameters.

    Args:
        active_tab_info: Dict with 'url' key, or a plain URL string.
        rule: Dict with 'type' ('url') and 'url' (expected URL).

    Returns:
        1.0 if URLs match after stripping query params, else 0.0.
    """
    if not active_tab_info:
        return 0.0

    match_type = rule.get('type', '')
    if match_type != "url":
        return 0.0

    expected_url = rule.get('url', '')
    if isinstance(active_tab_info, dict):
        actual_url = active_tab_info.get('url', '')
    else:
        actual_url = str(active_tab_info)

    def strip_query(url: str) -> str:
        parsed = urlparse(url)
        return urlunparse(parsed._replace(query=""))

    if strip_query(expected_url) == strip_query(actual_url):
        return 1.0
    return 0.0
