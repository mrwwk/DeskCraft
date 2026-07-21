import logging
from typing import Any, Dict, List
from urllib.parse import urlparse

logger = logging.getLogger("desktopenv.metrics.chrome")


def is_expected_active_tab(active_tab_info: Dict[str, str], rule: Dict[str, Any], **kwargs) -> float:
    """
    Checks if the expected active tab is open in Chrome.
    Compares URLs by path to handle protocol mismatches (e.g., https:// vs file:// for local files).
    """
    if not active_tab_info:
        return 0.

    match_type = rule['type']

    if match_type == "url":
        expected_url = rule['url']
        if isinstance(active_tab_info, dict):
            actual_url = active_tab_info.get('url', None)
        else:
            actual_url = active_tab_info

        if not actual_url:
            return 0.

        logger.info("expected_url: {}".format(expected_url))
        logger.info("actual_url: {}".format(actual_url))

        # Normalize URLs by comparing their path components.
        # This handles protocol mismatches such as:
        #   expected: file:///home/user/...  vs  actual: https:///home/user/...
        # Both parse to the same path, avoiding false negatives caused by the
        # active_url_from_accessTree getter sometimes returning https:// for local files.
        def get_path(url: str) -> str:
            parsed = urlparse(url)
            return parsed.path.rstrip('/')

        expected_path = get_path(expected_url)
        actual_path = get_path(actual_url)

        logger.info("expected_path: {}".format(expected_path))
        logger.info("actual_path: {}".format(actual_path))

        return 1.0 if expected_path == actual_path else 0.0
    else:
        logger.error(f"Unknown type: {match_type}")
        return 0


def is_expected_bookmarks(bookmarks, rule: Dict[str, Any], **kwargs) -> float:
    """
    Checks if the expected bookmarks are in Chrome.
    """
    if not bookmarks:
        return 0.
    elif rule['type'] == "bookmark_bar_folders_names":
        bookmark_bar_folders_names = [bookmark['name'] for bookmark in bookmarks['bookmark_bar']['children'] if
                                      bookmark['type'] == 'folder']
        return 1. if set(bookmark_bar_folders_names) == set(rule['names']) else 0.
    elif rule['type'] == "bookmark_bar_websites_urls":
        # Normalize URLs by path to handle potential protocol mismatches
        def get_path(url: str) -> str:
            parsed = urlparse(url)
            return parsed.path.rstrip('/')

        bookmark_bar_websites_urls = [get_path(bookmark['url']) for bookmark in bookmarks['bookmark_bar']['children'] if
                                      bookmark['type'] == 'url']
        expected_paths = [get_path(url) for url in rule['urls']]
        return 1. if set(bookmark_bar_websites_urls) == set(expected_paths) else 0.
    elif rule['type'] == "liked_authors_websites_urls":
        from itertools import product

        liked_authors_folder = next((bookmark for bookmark in bookmarks['bookmark_bar']['children'] if
                                     bookmark['type'] == 'folder' and bookmark['name'] == 'Liked Authors'), None)
        if liked_authors_folder:
            logger.info("'Liked Authors' folder exists")
            liked_authors_urls = [bookmark['url'] for bookmark in liked_authors_folder['children'] if
                                  bookmark['type'] == 'url']
            logger.info("Here is the 'Liked Authors' folder's urls: {}".format(liked_authors_urls))

            urls = rule['urls']

            for idx, url in enumerate(urls):
                if isinstance(url, str):
                    urls[idx] = [url]

            combinations = product(*urls)

            for combination in combinations:
                if set(combination) == set(liked_authors_urls):
                    return 1.
            return 0.
        else:
            return 0.
    else:
        raise TypeError(f"{rule['type']} not support yet!")
