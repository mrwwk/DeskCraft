"""
Evaluator for interactive_chrome_requirement_change_107.

Checks:
  1. is_expected_active_tab: the active Chrome tab URL is Security FAQ.
  2. is_expected_bookmarks: the bookmark bar contains only Security FAQ
     (Pricing Overview bookmark has been removed).

URL normalization is applied to handle a known Chrome accessTree artifact
where local file URLs are reported with an "https:///" prefix instead of
the correct "file:///" prefix.
"""
import logging
import re
from typing import Any, Dict, List, Union

logger = logging.getLogger("desktopenv.metrics.chrome")


def _normalize_url(url: str) -> str:
    """Normalize a URL to handle Chrome accessTree protocol artifacts.

    Chrome accessTree may report local file URLs with an http:// or https://
    protocol prefix (e.g. ``https:///home/user/...``) instead of the correct
    ``file:///`` prefix.  This function detects such artifacts and rewrites
    the protocol to ``file://`` so that downstream comparisons succeed.
    """
    if not url:
        return url
    # Match http/https protocol followed by an absolute local path.
    # Examples: https:///home/user/foo.html  →  file:///home/user/foo.html
    #           http:///tmp/bar.html          →  file:///tmp/bar.html
    m = re.match(r'^https?://(/[^/].*)$', url)
    if m:
        return 'file://' + m.group(1)
    return url


def is_expected_active_tab(
    active_tab_info: Union[Dict[str, str], str],
    rule: Dict[str, Any],
    **options,
) -> float:
    """Check whether the active Chrome tab matches the expected URL.

    Parameters
    ----------
    active_tab_info : dict or str
        Result from the ``active_url_from_accessTree`` getter.  May be a dict
        with a ``url`` key or a plain URL string.
    rule : dict
        Expected rule with keys ``type`` (``"url"``) and ``url``.
    """
    if not active_tab_info:
        return 0.0

    match_type = rule.get('type')
    if match_type != "url":
        logger.error("Unknown type: %s", match_type)
        return 0.0

    expected_url = _normalize_url(rule['url'])

    if isinstance(active_tab_info, dict):
        actual_url = _normalize_url(active_tab_info.get('url', ''))
    else:
        actual_url = _normalize_url(str(active_tab_info))

    logger.info("expected_url: %s", expected_url)
    logger.info("actual_url:   %s", actual_url)

    return 1.0 if expected_url == actual_url else 0.0


def is_expected_bookmarks(
    bookmarks: Dict[str, Any],
    rule: Dict[str, Any],
    **options,
) -> float:
    """Check whether the Chrome bookmark bar matches the expected state.

    Parameters
    ----------
    bookmarks : dict
        Result from the ``bookmarks`` getter.  Expected to contain a
        ``bookmark_bar`` key with a ``children`` list.
    rule : dict
        Expected rule.  Supported types:

        * ``bookmark_bar_folders_names`` – set-equal folder names.
        * ``bookmark_bar_websites_urls`` – set-equal bookmark URLs (after
          normalization for the accessTree protocol artifact).
        * ``liked_authors_websites_urls`` – check a "Liked Authors" folder.
    """
    if not bookmarks:
        return 0.0

    rule_type = rule['type']

    if rule_type == "bookmark_bar_folders_names":
        bookmark_bar_folders_names = [
            bm['name']
            for bm in bookmarks['bookmark_bar']['children']
            if bm['type'] == 'folder'
        ]
        return 1.0 if set(bookmark_bar_folders_names) == set(rule['names']) else 0.0

    elif rule_type == "bookmark_bar_websites_urls":
        bookmark_bar_websites_urls = [
            _normalize_url(bm['url'])
            for bm in bookmarks['bookmark_bar']['children']
            if bm['type'] == 'url'
        ]
        expected_urls = [_normalize_url(u) for u in rule['urls']]
        return 1.0 if set(bookmark_bar_websites_urls) == set(expected_urls) else 0.0

    elif rule_type == "liked_authors_websites_urls":
        from itertools import product

        liked_authors_folder = next(
            (
                bm
                for bm in bookmarks['bookmark_bar']['children']
                if bm['type'] == 'folder' and bm['name'] == 'Liked Authors'
            ),
            None,
        )
        if not liked_authors_folder:
            return 0.0

        logger.info("'Liked Authors' folder exists")
        liked_authors_urls = [
            _normalize_url(bm['url'])
            for bm in liked_authors_folder['children']
            if bm['type'] == 'url'
        ]
        logger.info(
            "Here is the 'Liked Authors' folder's urls: %s", liked_authors_urls
        )

        urls = rule['urls']
        for idx, url in enumerate(urls):
            if isinstance(url, str):
                urls[idx] = [_normalize_url(url)]

        combinations = product(*urls)
        for combination in combinations:
            if set(combination) == set(liked_authors_urls):
                return 1.0
        return 0.0

    else:
        raise TypeError(f"{rule_type} not support yet!")
