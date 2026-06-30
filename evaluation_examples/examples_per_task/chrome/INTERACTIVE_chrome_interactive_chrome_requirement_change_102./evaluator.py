import logging
import re
from typing import Any, Dict, List

from desktop_env.evaluators.metrics.utils import are_lists_equal, compare_urls

logger = logging.getLogger("desktopenv.metrics.chrome")


def _normalize_access_tree_url(url: str) -> str:
    """
    Fix URLs corrupted by get_active_url_from_accessTree getter.

    The getter adds 'https://' prefix by default (because accessibility tree
    returns URLs without scheme). For local file:// URLs, this produces
    corrupted forms like 'https:///home/user/...' which should actually be
    'file:///home/user/...'.

    This function detects the 'https:///' (three-slash) pattern that indicates
    a file path was incorrectly prefixed, and converts it to the correct
    file:// scheme.
    """
    if not url:
        return url
    # Match: https:// followed by / and an absolute path (starting with /, not //)
    # Example: https:///home/user/foo.html -> file:///home/user/foo.html
    match = re.match(r'^https://(/[^/].*)$', url)
    if match:
        return 'file://' + match.group(1)
    return url


def is_expected_active_tab(active_tab_info: Dict[str, str], rule: Dict[str, Any]) -> float:
    """
    Checks if the expected active tab is open in Chrome.
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

        # Normalize URL that may have been corrupted by the accessibility tree
        # getter (https:///path -> file:///path)
        if actual_url:
            actual_url = _normalize_access_tree_url(actual_url)

        logger.info("expected_url: {}".format(expected_url))
        logger.info("actual_url: {}".format(actual_url))
        return 1 if compare_urls(expected_url, actual_url) else 0
    else:
        logger.error(f"Unknown type: {match_type}")
        return 0


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
