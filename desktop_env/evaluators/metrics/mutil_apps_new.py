import json
import logging
from typing import Any, Dict

logger = logging.getLogger("desktopenv.metrics.mutil_apps_new")


def check_bookmark_contains_url(bookmarks_roots: Any, rule: Dict[str, Any], **options) -> float:
    """
    Check whether any bookmark URL (anywhere in the bookmark tree) contains the given substring.

    Args:
        bookmarks_roots: dict returned by get_bookmarks — the Chrome Bookmarks JSON ``roots``
                         section, e.g. {"bookmark_bar": {"children": [...]}, "other": {...}, ...}
        rule: dict with key ``url_pattern`` — substring that must appear in at least one
              bookmark URL.  Example: {"url_pattern": "docs.python.org/3"}

    Returns:
        1.0 if any bookmark URL contains the pattern, 0.0 otherwise.
    """
    if not bookmarks_roots:
        return 0.

    url_pattern = rule.get("url_pattern", "")
    if not url_pattern:
        return 0.

    def _search(node: Any) -> bool:
        if not isinstance(node, dict):
            return False
        if node.get("type") == "url":
            if url_pattern in node.get("url", ""):
                return True
        for child in node.get("children", []):
            if _search(child):
                return True
        return False

    for section_data in bookmarks_roots.values():
        if _search(section_data):
            return 1.
    return 0.
