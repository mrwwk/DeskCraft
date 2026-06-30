import logging
from typing import Any, Dict, List
from urllib.parse import urlparse

logger = logging.getLogger("desktopenv.metrics.chrome")


def _compare_urls_scheme_tolerant(url1: str, url2: str) -> bool:
    """
    Compare two URLs allowing scheme differences when paths and netloc match.

    The active_url_from_accessTree getter may capture local file:// URLs
    with an 'https' scheme due to how Chrome's accessibility tree reports
    the URL. This function normalizes the comparison to be scheme-tolerant
    when the path and netloc portions are identical.
    """
    if not url1 or not url2:
        return url1 == url2

    # Quick exact match after normalization
    u1 = url1.rstrip('/').lower()
    u2 = url2.rstrip('/').lower()
    if u1 == u2:
        return True

    # Parse and compare path + netloc (scheme-tolerant)
    p1 = urlparse(u1)
    p2 = urlparse(u2)

    if p1.path.rstrip('/') == p2.path.rstrip('/') and p1.netloc == p2.netloc:
        logger.info(
            "URLs match by path/netloc despite scheme difference: "
            "'%s' vs '%s'", p1.scheme, p2.scheme
        )
        return True

    return False


def is_expected_active_tab(active_tab_info, rule, **options) -> float:
    """
    Checks if the expected active tab is open in Chrome.
    Uses scheme-tolerant URL comparison to handle cases where
    active_url_from_accessTree may capture local file URLs with
    a non-file scheme (e.g., https).
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
        logger.info("expected_url: %s", expected_url)
        logger.info("actual_url: %s", actual_url)
        return 1.0 if _compare_urls_scheme_tolerant(expected_url, actual_url) else 0.0
    else:
        logger.error("Unknown type: %s", match_type)
        return 0.0


def is_expected_bookmarks(bookmarks, rule, **options) -> float:
    """
    Checks if the expected bookmarks are in Chrome.
    Uses scheme-tolerant URL comparison for bookmark bar website URLs.
    """
    if not bookmarks:
        return 0.0

    if rule['type'] == "bookmark_bar_folders_names":
        bookmark_bar_folders_names = [
            bookmark['name'] for bookmark in bookmarks['bookmark_bar']['children']
            if bookmark['type'] == 'folder'
        ]
        return 1.0 if set(bookmark_bar_folders_names) == set(rule['names']) else 0.0

    elif rule['type'] == "bookmark_bar_websites_urls":
        bookmark_bar_websites_urls = [
            bookmark['url'] for bookmark in bookmarks['bookmark_bar']['children']
            if bookmark['type'] == 'url'
        ]
        expected_urls = rule['urls']

        logger.info("expected bookmark urls: %s", expected_urls)
        logger.info("actual bookmark urls: %s", bookmark_bar_websites_urls)

        # Bidirectional scheme-tolerant set comparison
        for expected_url in expected_urls:
            if not any(
                _compare_urls_scheme_tolerant(expected_url, actual_url)
                for actual_url in bookmark_bar_websites_urls
            ):
                logger.info("Expected bookmark URL not found: %s", expected_url)
                return 0.0

        for actual_url in bookmark_bar_websites_urls:
            if not any(
                _compare_urls_scheme_tolerant(expected_url, actual_url)
                for expected_url in expected_urls
            ):
                logger.info("Unexpected bookmark URL found: %s", actual_url)
                return 0.0

        return 1.0

    else:
        raise TypeError(f"{rule['type']} not support yet!")
