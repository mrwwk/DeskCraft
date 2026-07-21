"""
Combined evaluator for scan_spec_audit_and_metadata_update task.

Checks all file-based conditions in a single metric to avoid the
conj="and" short-circuit issue where subsequent metrics are not
evaluated when an earlier metric returns 0.0.

Checks performed:
  1. project_meta.json — pythonFiles, markdownFiles counts and status
  2. settings.json     — editor.tabSize and editor.rulers
  3. chrome URL        — noted in expected but cannot be verified
     without the active_tab_info getter (framework limitation).
"""

import functools
import json
import logging
import operator
import os
import re
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger("desktopenv.metric.custom")


# ---------------------------------------------------------------------------
# Utility: _match_value_to_rule (from desktop_env.evaluators.metrics.utils)
# ---------------------------------------------------------------------------

def _match_value_to_rule(value, rule):
    """Match a value against a rule dict like {"method": str, "ref": value}."""
    if rule["method"].startswith("re"):  # re.FLAGs
        flags = rule["method"].split(".")[1:]
        flag = functools.reduce(
            operator.or_,
            (getattr(re, fl) for fl in flags),
            re.RegexFlag(0),
        )
        match_ = re.search(rule["ref"], value, flag)
        return match_ is not None
    if rule["method"] in {"eq", "ne", "le", "lt", "ge", "gt"}:
        return getattr(operator, rule["method"])(value, rule["ref"])
    if rule["method"].startswith("approx"):
        threshold = float(rule["method"].split(":")[1])
        try:
            value = float(value)
        except (ValueError, TypeError):
            return False
        return abs(value - rule["ref"]) <= threshold
    raise NotImplementedError(f"Unknown method: {rule['method']}")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _check_json_content(result_path, rules):
    """Check a JSON file against expect/unexpect rules (from general.py:check_json)."""
    if result_path is None:
        logger.warning("Result file path is None, returning False")
        return False

    if not os.path.exists(result_path):
        logger.warning(f"Result file does not exist: {result_path}")
        return False

    try:
        with open(result_path, "r", encoding="utf-8") as f:
            result_data = json.load(f)
    except (json.JSONDecodeError, IOError, Exception) as e:
        logger.error(f"Error reading/parsing {result_path}: {e}")
        return False

    expect_rules = rules.get("expect", [])
    unexpect_rules = rules.get("unexpect", [])

    for r in expect_rules:
        value = result_data
        try:
            for k in r["key"]:
                value = value[k]
        except (KeyError, TypeError):
            logger.debug(f"Key path {r['key']} not found in {result_path}")
            return False
        if not _match_value_to_rule(value, r):
            return False

    for r in unexpect_rules:
        value = result_data
        try:
            for k in r["key"]:
                value = value[k]
        except (KeyError, TypeError):
            continue  # key not present → rule not triggered
        if _match_value_to_rule(value, r):
            return False

    return True


def _check_settings_content(settings_path, rules):
    """Check VS Code settings.json against expected key-value pairs (from vscode.py:check_json_settings)."""
    if not settings_path or not os.path.exists(settings_path):
        logger.warning(f"Settings file not found: {settings_path}")
        return False

    try:
        with open(settings_path, "r") as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Error reading settings file {settings_path}: {e}")
        return False

    expect = rules.get("expected", {})
    if not expect:
        logger.warning("No expected settings rules provided")
        return False

    for key, value in expect.items():
        if key not in data or data[key] != value:
            logger.info(
                f"Settings mismatch: key={key}, expected={value}, actual={data.get(key)}"
            )
            return False

    return True


# ---------------------------------------------------------------------------
# Main evaluator entry point
# ---------------------------------------------------------------------------

def check_all(result_state, expected=None, **options):
    """
    Combined check for all file-based task conditions.

    Args:
        result_state: List of two file paths:
                      [project_meta.json_path, settings.json_path]
                      (from vm_file getter with multi=true, gives=[0,1])
        expected: dict with keys:
                      "project_meta" — rules for check_json
                      "settings"     — rules for check_json_settings
                      "chrome"       — expected Chrome URL (not verifiable
                                       without active_tab_info getter;
                                       framework limitation)
        **options: reserved for future use.

    Returns:
        float: 1.0 if all verifiable conditions pass, 0.0 otherwise.
    """
    if result_state is None:
        logger.warning("result_state is None")
        return 0.0

    # result_state should be a list of two file paths (multi vm_file)
    if not isinstance(result_state, list) or len(result_state) < 2:
        logger.warning(
            f"Expected list of 2 file paths, got: {type(result_state)} "
            f"len={len(result_state) if isinstance(result_state, list) else 'N/A'}"
        )
        return 0.0

    project_meta_path, settings_path = result_state[0], result_state[1]

    if expected is None:
        logger.warning("expected is None, cannot evaluate")
        return 0.0

    # --- 1. Check project_meta.json ---
    pm_rules = expected.get("project_meta", {})
    if not _check_json_content(project_meta_path, pm_rules):
        logger.info("project_meta.json check FAILED")
        return 0.0
    logger.info("project_meta.json check PASSED")

    # --- 2. Check settings.json ---
    st_rules = expected.get("settings", {})
    if not _check_settings_content(settings_path, st_rules):
        logger.info("settings.json check FAILED")
        return 0.0
    logger.info("settings.json check PASSED")

    # --- 3. Chrome URL check ---
    # Cannot be verified in this metric because active_tab_info getter
    # is incompatible with file-based (vm_file) getter in a single metric.
    # The expected URL is available as expected["chrome"]["url"] for
    # reference but cannot be checked here.
    chrome_expected = expected.get("chrome", {})
    if chrome_expected:
        logger.info(
            "Chrome URL check skipped (framework limitation): "
            "expected URL = %s",
            chrome_expected.get("url", "unknown"),
        )

    return 1.0


from urllib.parse import urlparse, urlunparse


def is_expected_active_tab_approximate(active_tab_info, rule, **options) -> float:
    if not active_tab_info or not isinstance(active_tab_info, dict):
        return 0.0
    if rule.get('type') != 'url':
        return 0.0
    expected_url = rule.get('url', '')
    actual_url = active_tab_info.get('url', '')
    def strip_query(url):
        parsed = urlparse(url)
        return urlunparse(parsed._replace(query=""))
    return 1.0 if strip_query(expected_url) == strip_query(actual_url) else 0.0
