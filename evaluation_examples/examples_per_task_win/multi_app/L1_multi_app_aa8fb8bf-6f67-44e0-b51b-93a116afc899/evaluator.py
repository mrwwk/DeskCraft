import json
import logging
import os
from typing import Any, Dict, List, Union

import yaml

from desktop_env.evaluators.metrics.utils import _match_value_to_rule

logger = logging.getLogger("desktopenv.metrics.evaluator")


def is_expected_active_tab_approximate(active_tab_info: Dict[str, str], rule: Dict[str, Any]) -> float:
    """
    Checks if the expected active tab is open in Chrome, ignoring query parameters in the URL.
    """
    if not active_tab_info:
        return 0.

    match_type = rule['type']

    if match_type == "url":
        expected_url = rule['url']
        if isinstance(active_tab_info, Dict):
            actual_url = active_tab_info.get('url', None)
        else:
            actual_url = active_tab_info
        from urllib.parse import urlparse, urlunparse
        def strip_query(url):
            parsed = urlparse(url)
            return urlunparse(parsed._replace(query=""))
        if strip_query(expected_url) == strip_query(actual_url):
            return 1
        else:
            return 0
    else:
        logger.error(f"Unknown type: {match_type}")
        return 0


def check_json(result: str, rules: Dict[str, List[Dict[str, Union[List[str], str]]]], is_yaml: bool = False) -> float:
    """
    Args:
        result (str): path to json/yaml file
        rules (Dict): dict like
          {
            "expect": [{"key": list of str, "method": str, "ref": something}],
            "unexpect": <same as expect>
          }
        is_yaml (bool): yaml rather than json
    Returns:
        float
    """
    if result is None:
        logger.warning("Result file path is None, returning 0.0")
        return 0.

    if not os.path.exists(result):
        logger.warning(f"Result file does not exist: {result}, returning 0.0")
        return 0.

    try:
        with open(result, 'r', encoding='utf-8') as f:
            if is_yaml:
                try:
                    result_data: Dict[str, Any] = yaml.safe_load(f)
                    if result_data is None:
                        logger.warning(f"YAML file {result} is empty or contains only null values, returning 0.0")
                        return 0.
                except yaml.YAMLError as e:
                    logger.error(f"YAML parsing error in file {result}: {e}")
                    return 0.
                except Exception as e:
                    logger.error(f"Unexpected error parsing YAML file {result}: {e}")
                    return 0.
            else:
                try:
                    result_data: Dict[str, Any] = json.load(f)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parsing error in file {result}: {e}")
                    return 0.
                except Exception as e:
                    logger.error(f"Unexpected error parsing JSON file {result}: {e}")
                    return 0.
    except IOError as e:
        logger.error(f"IO error reading file {result}: {e}")
        return 0.
    except Exception as e:
        logger.error(f"Unexpected error reading file {result}: {e}")
        return 0.

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
                    return 0.
                except TypeError:
                    logger.debug(f"Cannot access key '{k}' - value is not a dictionary, returning 0.0")
                    return 0.
            metric = metric and _match_value_to_rule(value, r)
        except Exception as e:
            logger.error(f"Error processing expect rule {r}: {e}")
            return 0.

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
            return 0.

    return float(metric)


def check_include_exclude(result: str, rules: Dict[str, List[str]]) -> float:
    """
    Checks whether result string contains all items in include list and none in exclude list.
    """
    if result is None:
        return 0.

    include = rules.get("include", [])
    exclude = rules.get("exclude", [])
    if all(r in result for r in include) and all(r not in result for r in exclude):
        return 1.
    else:
        return 0.
