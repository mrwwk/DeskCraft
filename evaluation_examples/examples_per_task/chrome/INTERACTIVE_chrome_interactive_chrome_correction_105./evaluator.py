"""
Evaluator for interactive_chrome_correction_105.

Checks:
  - is_expected_tabs: all open tabs match expected URLs
  - is_expected_active_tab: the active tab URL matches expected
  - is_expected_bookmarks: the bookmark bar contains expected URLs

The active_url_from_accessTree getter may return local file URLs with an
incorrect 'https:///' protocol prefix instead of 'file:///'.  This module
normalises that prefix before comparison so the metric is not falsely
penalised by a known getter-level artefact.
"""
import logging
from typing import Any, Dict, List

from desktop_env.evaluators.metrics.utils import are_lists_equal, compare_urls

logger = logging.getLogger("desktopenv.metrics.chrome")


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _normalize_local_file_url(url: str) -> str:
    """Normalise a local-file URL whose protocol may be misreported.

    The ``active_url_from_accessTree`` getter has been observed to return
    ``https:///home/user/...`` for files that should be ``file:///home/user/...``.
    This helper rewrites the known-wrong prefix so that downstream comparisons
    (e.g. ``compare_urls``) can succeed.
    """
    if not url:
        return url
    # Fix triple-slash https protocol for local files
    if url.startswith("https:///"):
        url = "file:///" + url[len("https:///"):]
    return url


# ---------------------------------------------------------------------------
# metric functions – keep signatures compatible with the framework:
#   metric_fn(result_state, expected_state, **options)
# ---------------------------------------------------------------------------

def is_expected_active_tab(active_tab_info: Dict[str, str],
                           rule: Dict[str, Any]) -> float:
    """Check whether the active Chrome tab matches the expected URL.

    *active_tab_info* is the dict returned by the ``active_url_from_accessTree``
    result getter (or a plain URL string).
    *rule* is the expected dict, e.g.
    ``{"type": "url", "url": "file:///home/user/.../api_authentication.html"}``.
    """
    if not active_tab_info:
        return 0.0

    match_type = rule["type"]

    if match_type == "url":
        expected_url = _normalize_local_file_url(rule["url"])
        if isinstance(active_tab_info, dict):
            actual_url = _normalize_local_file_url(
                active_tab_info.get("url", "")
            )
        else:
            actual_url = _normalize_local_file_url(str(active_tab_info))

        logger.info("expected_url: %s", expected_url)
        logger.info("actual_url:   %s", actual_url)
        return 1.0 if compare_urls(expected_url, actual_url) else 0.0
    else:
        logger.error("Unknown type: %s", match_type)
        return 0.0


def is_expected_tabs(open_tabs: List[Dict[str, str]],
                     rule: Dict[str, Any]) -> float:
    """Check whether the set of open Chrome tabs matches the expected URLs."""
    if not open_tabs:
        return 0.0

    match_type = rule["type"]

    if match_type == "url":
        expected_urls = rule["urls"]
        actual_urls = [tab["url"] for tab in open_tabs]
        if not are_lists_equal(expected_urls, actual_urls, compare_urls):
            logger.error("list not match")
            logger.error(expected_urls)
            logger.error(actual_urls)
            return 0.0
        return 1.0 if are_lists_equal(expected_urls, actual_urls, compare_urls) else 0.0
    else:
        logger.error("Unknown type: %s", match_type)
        return 0.0


def is_expected_bookmarks(bookmarks: List[str],
                          rule: Dict[str, Any]) -> float:
    """Check whether the expected bookmarks are present in Chrome."""
    if not bookmarks:
        return 0.0

    if rule["type"] == "bookmark_bar_folders_names":
        bookmark_bar_folders_names = [
            bm["name"] for bm in bookmarks["bookmark_bar"]["children"]
            if bm["type"] == "folder"
        ]
        return 1.0 if set(bookmark_bar_folders_names) == set(rule["names"]) else 0.0

    elif rule["type"] == "bookmark_bar_websites_urls":
        bookmark_bar_websites_urls = [
            bm["url"] for bm in bookmarks["bookmark_bar"]["children"]
            if bm["type"] == "url"
        ]
        return 1.0 if set(bookmark_bar_websites_urls) == set(rule["urls"]) else 0.0

    else:
        raise TypeError(f"{rule['type']} not support yet!")
