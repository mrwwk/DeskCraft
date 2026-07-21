# -*- coding: utf-8 -*-
"""
Evaluator for interactive_chrome_interruption_205.

Checks three conditions (AND conjunction):
  1. is_expected_tabs: only Dashboard and Onboarding tabs remain open.
  2. is_expected_active_tab: the active tab is Onboarding Prompts.
  3. is_expected_bookmarks: only Dashboard and Onboarding bookmarks remain.

Key fix: is_expected_tabs now filters out chrome:// internal URLs (e.g.
bookmarks-side-panel) before comparison, so that Chrome UI panels that are
still open at terminate time do not cause false negatives.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger("desktopenv.metrics.chrome")


# ---------------------------------------------------------------------------
# Utility functions (inlined for replay robustness)
# ---------------------------------------------------------------------------

def compare_urls(url1: str, url2: str) -> bool:
    """Compare two URLs for equality. Handles file:// URLs robustly."""
    if url1 is None or url2 is None:
        return url1 == url2

    # Normalize: strip trailing slashes for file:// URLs, ignore query/fragment
    def _normalize(u: str) -> str:
        # For file:// URLs, just compare the path part after stripping slashes
        if u.startswith("file://"):
            # Extract path and normalize
            path = u[len("file://"):]
            return path.rstrip("/")
        return u.rstrip("/")

    return _normalize(url1) == _normalize(url2)


def are_lists_equal(list1: List, list2: List, comparison_func) -> bool:
    """Check if two lists contain the same elements (order-independent)."""
    if len(list1) != len(list2):
        return False
    for item1 in list1:
        if not any(comparison_func(item1, item2) for item2 in list2):
            return False
    return True


# ---------------------------------------------------------------------------
# Metric functions
# ---------------------------------------------------------------------------

def is_expected_tabs(open_tabs: List[Dict[str, str]], rule: Dict[str, Any]) -> float:
    """
    Checks if the expected tabs are open in Chrome.

    Filters out chrome:// internal URLs (e.g. bookmarks-side-panel) before
    comparison, since these are Chrome UI internals, not user-opened tabs.
    """
    if not open_tabs:
        return 0.

    match_type = rule["type"]

    if match_type == "url":
        expected_urls = rule["urls"]
        # Filter out chrome:// internal URLs (bookmarks sidebar, settings, etc.)
        actual_urls = [
            tab["url"]
            for tab in open_tabs
            if not tab.get("url", "").startswith("chrome://")
        ]
        logger.info("is_expected_tabs: expected_urls=%s", expected_urls)
        logger.info("is_expected_tabs: actual_urls (filtered)=%s", actual_urls)
        if not are_lists_equal(expected_urls, actual_urls, compare_urls):
            logger.error("is_expected_tabs: lists do not match")
            return 0.
        return 1.
    else:
        logger.error("is_expected_tabs: Unknown type: %s", match_type)
        return 0.


def is_expected_active_tab(active_tab_info: Dict[str, str], rule: Dict[str, Any]) -> float:
    """
    Checks if the expected active tab is open in Chrome.
    """
    if not active_tab_info:
        return 0.

    match_type = rule["type"]

    if match_type == "url":
        expected_url = rule["url"]
        if isinstance(active_tab_info, dict):
            actual_url = active_tab_info.get("url", None)
        else:
            actual_url = active_tab_info
        logger.info("is_expected_active_tab: expected_url=%s", expected_url)
        logger.info("is_expected_active_tab: actual_url=%s", actual_url)
        return 1. if compare_urls(expected_url, actual_url) else 0.
    else:
        logger.error("is_expected_active_tab: Unknown type: %s", match_type)
        return 0.


def is_expected_bookmarks(bookmarks: List, rule: Dict[str, Any]) -> float:
    """
    Checks if the expected bookmarks are in Chrome.
    """
    if not bookmarks:
        return 0.

    if rule["type"] == "bookmark_bar_folders_names":
        bookmark_bar_folders_names = [
            bm["name"]
            for bm in bookmarks["bookmark_bar"]["children"]
            if bm["type"] == "folder"
        ]
        return 1. if set(bookmark_bar_folders_names) == set(rule["names"]) else 0.

    elif rule["type"] == "bookmark_bar_websites_urls":
        bookmark_bar_websites_urls = [
            bm["url"]
            for bm in bookmarks["bookmark_bar"]["children"]
            if bm["type"] == "url"
        ]
        return 1. if set(bookmark_bar_websites_urls) == set(rule["urls"]) else 0.

    else:
        raise TypeError(f"is_expected_bookmarks: {rule['type']} not supported yet!")
