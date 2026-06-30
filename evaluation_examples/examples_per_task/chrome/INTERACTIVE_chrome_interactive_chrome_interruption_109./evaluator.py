"""
Custom evaluator for interactive_chrome_interruption_109.
Fixes is_expected_active_tab to normalize URL protocol from active_url_from_accessTree getter,
which incorrectly reports file:/// URLs as https:///.
"""
import logging
from typing import Any, Dict, List

from desktop_env.evaluators.metrics.utils import are_lists_equal, compare_urls

logger = logging.getLogger("desktopenv.metrics.chrome")


def is_expected_tabs(open_tabs: List[Dict[str, str]], rule: Dict[str, Any]) -> float:
    """
    Checks if the expected tabs are open in Chrome.
    """
    if not open_tabs:
        return 0.

    match_type = rule['type']

    if match_type == "url":
        expected_urls = rule['urls']
        actual_urls = [tab['url'] for tab in open_tabs]
        if not are_lists_equal(expected_urls, actual_urls, compare_urls):
            logger.error("list not match")
            logger.error(expected_urls)
            logger.error(actual_urls)
            return 0
        return 1 if are_lists_equal(expected_urls, actual_urls, compare_urls) else 0
    else:
        logger.error(f"Unknown type: {match_type}")
        return 0


def is_expected_active_tab(active_tab_info: Dict[str, str], rule: Dict[str, Any]) -> float:
    """
    Checks if the expected active tab is open in Chrome.

    Includes a workaround for the active_url_from_accessTree getter which
    sometimes reports file:/// URLs with an https:/// protocol prefix.
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

        # Normalize: active_url_from_accessTree getter sometimes returns
        # "https:///home/user/..." instead of "file:///home/user/..."
        # for local files. Fix the protocol before comparison.
        if actual_url and actual_url.startswith('https:///'):
            actual_url = 'file:///' + actual_url[len('https:///'):]

        logger.info("expected_url: {}".format(expected_url))
        logger.info("actual_url: {}".format(actual_url))
        return 1 if compare_urls(expected_url, actual_url) else 0
    else:
        logger.error(f"Unknown type: {match_type}")
        return 0
