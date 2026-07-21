# Revised evaluator for interactive_chrome_interruption_208
# Fix: added URL scheme normalization for Chrome accessibility tree quirk
# where local file:// URLs are reported as https:/// (empty host).
import logging
from typing import Any, Dict, List

from desktop_env.evaluators.metrics.utils import are_lists_equal, compare_urls

logger = logging.getLogger("desktopenv.metrics.chrome")


def _normalize_local_file_url(url: str) -> str:
    """Normalize Chrome accessibility tree URL scheme quirks.

    Chrome sometimes reports local file:// URLs as https:/// (with an empty
    host in the accessibility tree). This helper converts https:/// back to
    file:/// so that scheme differences do not cause false negatives when
    the actual page is the same local file.
    """
    if url and url.startswith("https:///"):
        return "file:///" + url[len("https:///"):]
    return url


def is_expected_tabs(
    open_tabs: List[Dict[str, str]], rule: Dict[str, Any]
) -> float:
    """Checks if the expected tabs are open in Chrome."""
    if not open_tabs:
        return 0.

    match_type = rule["type"]

    if match_type == "url":
        expected_urls = rule["urls"]
        actual_urls = [tab["url"] for tab in open_tabs]
        if not are_lists_equal(expected_urls, actual_urls, compare_urls):
            logger.error("list not match")
            logger.error(expected_urls)
            logger.error(actual_urls)
            return 0
        return 1 if are_lists_equal(expected_urls, actual_urls, compare_urls) else 0
    else:
        logger.error(f"Unknown type: {match_type}")
        return 0


def is_expected_active_tab(
    active_tab_info: Dict[str, str], rule: Dict[str, Any]
) -> float:
    """Checks if the expected active tab is open in Chrome.

    Includes tolerance for Chrome accessibility tree reporting local
    file:// URLs as https:/// (empty host).  When the strict compare_urls
    fails due to a scheme mismatch, both URLs are normalized and re-compared.
    """
    if not active_tab_info:
        return 0.

    match_type = rule["type"]

    if match_type == "url":
        expected_url = rule["url"]
        if isinstance(active_tab_info, Dict):
            actual_url = active_tab_info.get("url", None)
        else:
            actual_url = active_tab_info
        logger.info("expected_url: {}".format(expected_url))
        logger.info("actual_url: {}".format(actual_url))

        # First attempt: exact comparison via compare_urls
        if compare_urls(expected_url, actual_url):
            return 1

        # Second attempt: normalize both URLs to work around Chrome
        # accessibility tree reporting local file:// URLs as https:///
        normalized_expected = _normalize_local_file_url(expected_url)
        normalized_actual = _normalize_local_file_url(actual_url)
        if compare_urls(normalized_expected, normalized_actual):
            logger.info(
                "URL matched after scheme normalization: %s -> %s, %s -> %s",
                expected_url, normalized_expected,
                actual_url, normalized_actual,
            )
            return 1

        return 0
    else:
        logger.error(f"Unknown type: {match_type}")
        return 0


def is_expected_bookmarks(
    bookmarks: Dict, rule: Dict[str, Any]
) -> float:
    """Checks if the expected bookmarks are in Chrome.

    Supports bookmark_bar_folders_names, bookmark_bar_websites_urls, and
    liked_authors_websites_urls rule types.  URL comparisons are normalized
    to tolerate Chrome accessibility tree scheme quirks.
    """
    if not bookmarks:
        return 0.

    if rule["type"] == "bookmark_bar_folders_names":
        bookmark_bar_folders_names = [
            bookmark["name"]
            for bookmark in bookmarks["bookmark_bar"]["children"]
            if bookmark["type"] == "folder"
        ]
        return 1.0 if set(bookmark_bar_folders_names) == set(rule["names"]) else 0.0

    elif rule["type"] == "bookmark_bar_websites_urls":
        bookmark_bar_websites_urls = [
            bookmark["url"]
            for bookmark in bookmarks["bookmark_bar"]["children"]
            if bookmark["type"] == "url"
        ]

        # Try exact set comparison first
        if set(bookmark_bar_websites_urls) == set(rule["urls"]):
            return 1.0

        # Retry with normalized URLs to handle Chrome accessibility tree
        # reporting local file:// URLs as https:///
        normalized_actual = {_normalize_local_file_url(u) for u in bookmark_bar_websites_urls}
        normalized_expected = {_normalize_local_file_url(u) for u in rule["urls"]}
        if normalized_actual == normalized_expected:
            logger.info(
                "Bookmark URLs matched after scheme normalization"
            )
            return 1.0

        return 0.0

    elif rule["type"] == "liked_authors_websites_urls":
        from itertools import product

        liked_authors_folder = next(
            (
                bookmark
                for bookmark in bookmarks["bookmark_bar"]["children"]
                if bookmark["type"] == "folder"
                and bookmark["name"] == "Liked Authors"
            ),
            None,
        )
        if liked_authors_folder:
            logger.info("'Liked Authors' folder exists")
            liked_authors_urls = [
                bookmark["url"]
                for bookmark in liked_authors_folder["children"]
                if bookmark["type"] == "url"
            ]
            logger.info(
                "Here is the 'Liked Authors' folder's urls: {}".format(
                    liked_authors_urls
                )
            )

            urls = rule["urls"]
            for idx, url in enumerate(urls):
                if isinstance(url, str):
                    urls[idx] = [url]

            combinations = product(*urls)
            for combination in combinations:
                if set(combination) == set(liked_authors_urls):
                    return 1.0
            return 0.0
        else:
            return 0.0
    else:
        raise TypeError(f"{rule['type']} not support yet!")
