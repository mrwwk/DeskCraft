"""
Self-contained evaluator for portfolio_site_handoff_yaml_and_script_fix.

Contains all four metric functions:
- check_json: validates _config.yml YAML content against expected key-value rules
- check_python_file_by_test_suite: runs test.py to verify build_contact.py correctness
- is_expected_active_tab_approximate: checks Chrome active tab URL (ignoring query params)
- check_include_exclude: validates MIGRATION_DONE.txt contains required text
"""

import builtins
import functools
import importlib.util
import json
import logging
import operator
import os
import re
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Union
from urllib.parse import urlparse, urlunparse

import yaml

logger = logging.getLogger("desktopenv.metric.general")


# ---------------------------------------------------------------------------
# Helper: _match_value_to_rule (inlined from desktop_env.evaluators.metrics.utils)
# ---------------------------------------------------------------------------

def _match_value_to_rule(value, rule):
    """
    Match a value against a rule dict like {"method": str, "ref": ...}.

    Supported methods: eq, ne, le, lt, ge, gt, re*, approx:THRESHOLD,
    range.xx, str_list_eq, str_set_eq.
    """
    if rule["method"].startswith("re"):  # re.FLAGs
        flags = rule["method"].split(".")[1:]
        flags = (getattr(re, fl) for fl in flags)
        flag = functools.reduce(operator.or_, flags, re.RegexFlag(0))

        match_ = re.search(rule["ref"], value, flag)
        return match_ is not None

    if rule["method"] in {"eq", "ne", "le", "lt", "ge", "gt"}:
        return getattr(operator, rule["method"])(value, rule["ref"])

    if rule["method"].startswith("approx"):  # approx:THRESHOLD
        threshold = float(rule["method"].split(":")[1])
        try:
            value = float(value)
        except (ValueError, TypeError):
            return False
        else:
            return abs(value - rule["ref"]) <= threshold

    if rule["method"].startswith("range."):  # e.g., range.te [0, 2] -> 0 < x <= 2
        left_et = rule["method"][6]
        right_et = rule["method"][7]
        return (
            getattr(operator, "l" + left_et)(rule["ref"][0], value)
            and getattr(operator, "l" + right_et)(value, rule["ref"][1])
        )

    if rule["method"] in {"str_list_eq", "str_set_eq"}:
        container_type_str = rule["method"][4:-3]
        container_type = getattr(builtins, container_type_str)

        value = container_type(value.strip("\"'").split(","))
        ref = container_type(rule["ref"])
        return value == ref

    raise NotImplementedError(f"Unknown method: {rule['method']}")


# ---------------------------------------------------------------------------
# Metric 0: check_json (YAML content validation)
# ---------------------------------------------------------------------------

def check_json(
    result: str,
    rules: Dict[str, List[Dict[str, Union[List[str], str]]]],
    is_yaml: bool = False,
) -> float:
    """
    Validate a JSON or YAML file against expected/unexpected key-value rules.

    Args:
        result: path to the JSON/YAML file
        rules: dict with "expect" and optional "unexpect" lists of rule dicts
        is_yaml: if True, parse as YAML instead of JSON

    Returns:
        1.0 if all expect rules match and no unexpect rules match, else 0.0
    """
    if result is None:
        logger.warning("Result file path is None, returning 0.0")
        return 0.0

    if not os.path.exists(result):
        logger.warning(f"Result file does not exist: {result}, returning 0.0")
        return 0.0

    try:
        with open(result, "r", encoding="utf-8") as f:
            if is_yaml:
                try:
                    result_data = yaml.safe_load(f)
                    if result_data is None:
                        logger.warning(
                            f"YAML file {result} is empty or contains only null values, returning 0.0"
                        )
                        return 0.0
                except yaml.YAMLError as e:
                    logger.error(f"YAML parsing error in file {result}: {e}")
                    return 0.0
                except Exception as e:
                    logger.error(f"Unexpected error parsing YAML file {result}: {e}")
                    return 0.0
            else:
                try:
                    result_data = json.load(f)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parsing error in file {result}: {e}")
                    return 0.0
                except Exception as e:
                    logger.error(f"Unexpected error parsing JSON file {result}: {e}")
                    return 0.0
    except IOError as e:
        logger.error(f"IO error reading file {result}: {e}")
        return 0.0
    except Exception as e:
        logger.error(f"Unexpected error reading file {result}: {e}")
        return 0.0

    expect_rules = rules.get("expect", {})
    unexpect_rules = rules.get("unexpect", {})

    metric = True
    for r in expect_rules:
        value = result_data
        try:
            for k in r["key"]:
                try:
                    value = value[k]
                except KeyError:
                    logger.debug(f"Key '{k}' not found in result data, returning 0.0")
                    return 0.0
                except TypeError:
                    logger.debug(
                        f"Cannot access key '{k}' - value is not a dictionary, returning 0.0"
                    )
                    return 0.0
            metric = metric and _match_value_to_rule(value, r)
        except Exception as e:
            logger.error(f"Error processing expect rule {r}: {e}")
            return 0.0

    for r in unexpect_rules:
        value = result_data
        try:
            for k in r["key"]:
                try:
                    value = value[k]
                except KeyError:
                    value = None
                    break
                except TypeError:
                    value = None
                    break
            metric = metric and not _match_value_to_rule(value, r)
        except Exception as e:
            logger.error(f"Error processing unexpect rule {r}: {e}")
            return 0.0

    return float(metric)


# ---------------------------------------------------------------------------
# Metric 1: check_python_file_by_test_suite (run test.py against build_contact.py)
# ---------------------------------------------------------------------------

def check_python_file_by_test_suite(actual_files, test_file, **options) -> float:
    """Check the python file by running the test suite in the given test file.

    This function:
    - Changes working directory to the test file's directory so that imports work
    - Loads the test module dynamically
    - Runs the specified test function
    - Returns 1.0 on success, 0.0 on any failure
    """
    test_function_name = options.get("test_function_name", "test")

    # Validate inputs
    if not test_file:
        logger.error("test_file is None or empty")
        return 0.0

    test_file_path = Path(test_file).resolve()
    if not test_file_path.exists():
        logger.error(f"Test file does not exist: {test_file_path}")
        return 0.0

    if not test_file_path.is_file():
        logger.error(f"Test file path is not a file: {test_file_path}")
        return 0.0

    # Create unique module name to avoid conflicts
    module_name = f"dynamic_test_module_{uuid.uuid4().hex[:8]}"

    # Store original working directory and sys.path
    original_cwd = os.getcwd()
    original_sys_path = sys.path.copy()

    try:
        # Change to the directory containing the test file
        test_dir = test_file_path.parent
        os.chdir(test_dir)
        logger.debug(f"Changed working directory to: {test_dir}")

        # Add test directory to Python path if not already present
        if str(test_dir) not in sys.path:
            sys.path.insert(0, str(test_dir))
            logger.debug(f"Added {test_dir} to sys.path")

        # Try to load the module
        try:
            spec = importlib.util.spec_from_file_location(module_name, test_file_path)
            if spec is None:
                logger.error(f"Could not create module spec for {test_file_path}")
                return 0.0

            if spec.loader is None:
                logger.error(f"Module spec has no loader for {test_file_path}")
                return 0.0

            module = importlib.util.module_from_spec(spec)
            if module is None:
                logger.error(f"Could not create module from spec for {test_file_path}")
                return 0.0

            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            logger.debug(f"Successfully loaded test module: {module_name}")

        except SyntaxError as e:
            logger.error(f"Syntax error in test file: {e}")
            return 0.0
        except ImportError as e:
            logger.error(f"Import error loading test file: {e}")
            return 0.0
        except Exception as e:
            logger.error(f"Error loading test module: {e}")
            return 0.0

        # Try to get the test function
        try:
            if not hasattr(module, test_function_name):
                logger.error(
                    f"Test function '{test_function_name}' not found in {test_file_path}"
                )
                return 0.0

            test_function = getattr(module, test_function_name)

            if not callable(test_function):
                logger.error(
                    f"'{test_function_name}' is not callable in {test_file_path}"
                )
                return 0.0

            logger.debug(f"Found test function: {test_function_name}")

        except Exception as e:
            logger.error(f"Error getting test function: {e}")
            return 0.0

        # Execute the test function
        try:
            result = test_function()
            logger.debug(f"Test function returned: {result} (type: {type(result)})")

            if isinstance(result, bool):
                return 1.0 if result else 0.0
            elif isinstance(result, (int, float)):
                normalized = max(0.0, min(1.0, float(result)))
                if normalized != result:
                    logger.warning(f"Test result {result} normalized to {normalized}")
                return normalized
            else:
                bool_result = bool(result)
                logger.warning(
                    f"Test returned non-boolean/numeric value {result}, treating as {bool_result}"
                )
                return 1.0 if bool_result else 0.0

        except Exception as e:
            logger.error(f"Error executing test function: {e}")
            return 0.0

    except Exception as e:
        logger.error(f"Unexpected error in check_python_file_by_test_suite: {e}")
        return 0.0

    finally:
        # Cleanup
        if module_name in sys.modules:
            del sys.modules[module_name]
            logger.debug(f"Cleaned up module: {module_name}")

        try:
            os.chdir(original_cwd)
            logger.debug(f"Restored working directory to: {original_cwd}")
        except Exception as e:
            logger.warning(f"Could not restore working directory: {e}")

        sys.path[:] = original_sys_path
        logger.debug("Restored sys.path")


# ---------------------------------------------------------------------------
# Metric 2: is_expected_active_tab_approximate (Chrome tab URL check)
# ---------------------------------------------------------------------------

def is_expected_active_tab_approximate(
    active_tab_info: Dict[str, str], rule: Dict[str, Any]
) -> float:
    """
    Checks if the expected active tab is open in Chrome, ignoring query parameters.

    Args:
        active_tab_info: dict with 'url' key, or a plain URL string
        rule: dict like {"type": "url", "url": "https://..."}

    Returns:
        1.0 if the active tab URL matches (ignoring query string), else 0.0
    """
    if not active_tab_info:
        return 0.0

    match_type = rule["type"]

    if match_type == "url":
        expected_url = rule["url"]
        if isinstance(active_tab_info, dict):
            actual_url = active_tab_info.get("url", None)
        else:
            actual_url = active_tab_info

        def strip_query(url):
            parsed = urlparse(url)
            return urlunparse(parsed._replace(query=""))

        if strip_query(expected_url) == strip_query(actual_url):
            return 1.0
        else:
            return 0.0
    else:
        logger.error(f"Unknown type: {match_type}")
        return 0.0


# ---------------------------------------------------------------------------
# Metric 3: check_include_exclude (text content check)
# ---------------------------------------------------------------------------

def check_include_exclude(result: str, rules: Dict[str, List[str]]) -> float:
    """
    Check that required strings are present and excluded strings are absent.

    Args:
        result: the text content to check
        rules: dict with "include" (required substrings) and "exclude" (forbidden substrings)

    Returns:
        1.0 if all include strings are present and all exclude strings absent, else 0.0
    """
    if result is None:
        return 0.0

    print(result, rules)
    include = rules.get("include", [])
    exclude = rules.get("exclude", [])
    if all(r in result for r in include) and all(r not in result for r in exclude):
        return 1.0
    else:
        return 0.0
