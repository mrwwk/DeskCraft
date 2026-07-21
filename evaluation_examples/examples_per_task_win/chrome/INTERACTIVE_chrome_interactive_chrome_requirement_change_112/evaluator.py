import logging
from typing import Any, Dict

logger = logging.getLogger("desktopenv.metric.evaluator")


def exact_match(result, rules) -> float:
    """Exact string match between result and expected value."""
    expect = rules["expected"]
    if result == expect:
        return 1.
    else:
        return 0.


def is_expected_active_tab_approximate(active_tab_info, rule: Dict[str, Any]) -> float:
    """
    Checks if the expected active tab is open in Chrome, ignoring query parameters in the URL.
    """
    if not active_tab_info:
        logger.warning("active_tab_info is None or empty, returning 0.0")
        return 0.

    match_type = rule.get('type', '')

    if match_type == "url":
        expected_url = rule['url']
        if isinstance(active_tab_info, dict):
            actual_url = active_tab_info.get('url', None)
        else:
            actual_url = active_tab_info

        if actual_url is None:
            logger.warning("actual_url is None, returning 0.0")
            return 0.

        from urllib.parse import urlparse, urlunparse

        def strip_query(url):
            parsed = urlparse(url)
            return urlunparse(parsed._replace(query=""))

        expected_stripped = strip_query(expected_url)
        actual_stripped = strip_query(actual_url)

        if expected_stripped == actual_stripped:
            return 1.
        else:
            logger.info("URL mismatch: expected=%s, actual=%s", expected_stripped, actual_stripped)
            return 0.
    else:
        logger.error("Unknown match_type: %s", match_type)
        return 0.
