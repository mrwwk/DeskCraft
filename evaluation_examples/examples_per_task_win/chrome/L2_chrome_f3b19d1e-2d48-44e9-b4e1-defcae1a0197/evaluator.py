"""
Evaluator for ticketek_delivery_faq_safe task.

Checks:
  1. is_expected_active_tab — verifies a Ticketek help center Ticket Delivery
     article is open in the active tab (regex pattern matching on URL).
  2. exact_match — verifies Safe Browsing is enabled.
"""
import logging
import re
from typing import Any, Dict, Union

logger = logging.getLogger("desktopenv.metrics.chrome")


def is_expected_active_tab(active_tab_info, rule, **options):
    """
    Checks if the expected active tab is open in Chrome.

    Supports:
      - "url_pattern": regex pattern matching on the full URL.
      - "url": exact URL comparison (fallback, uses compare_urls if available).
    """
    if not active_tab_info:
        logger.info("active_tab_info is empty/None, returning 0.0")
        return 0.0

    match_type = rule.get("type")

    if isinstance(active_tab_info, dict):
        actual_url = active_tab_info.get("url", "")
    else:
        actual_url = str(active_tab_info)

    logger.info("expected rule: %s", rule)
    logger.info("actual_url: %s", actual_url)

    if match_type == "url_pattern":
        pattern = rule["pattern"]
        if re.search(pattern, actual_url):
            logger.info("Pattern '%s' matched URL: %s", pattern, actual_url)
            return 1.0
        logger.info("Pattern '%s' did NOT match URL: %s", pattern, actual_url)
        return 0.0

    if match_type == "url":
        expected_url = rule["url"]
        try:
            from desktop_env.evaluators.metrics.utils import compare_urls
            return 1.0 if compare_urls(expected_url, actual_url) else 0.0
        except ImportError:
            return 1.0 if expected_url == actual_url else 0.0

    logger.error("Unknown match_type: %s", match_type)
    return 0.0


def exact_match(result, rules, **options):
    """
    Checks if the result matches the expected value (case-insensitive string
    comparison).  Used for boolean-like checks such as Safe Browsing status.
    """
    if result is None:
        logger.info("exact_match: result is None, returning 0.0")
        return 0.0

    expected = rules.get("expected", "")
    actual_str = str(result).lower()
    expected_str = str(expected).lower()

    logger.info("exact_match: expected=%s, actual=%s", expected_str, actual_str)

    if actual_str == expected_str:
        return 1.0

    # Also accept boolean True / "true" equivalence
    if expected_str in ("true", "1") and actual_str in ("true", "1"):
        return 1.0

    return 0.0
