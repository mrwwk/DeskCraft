import logging
import re
from itertools import product

logger = logging.getLogger("desktopenv.metrics.chrome")


def is_expected_url_pattern_match(result, rules) -> float:
    """
    Checks if the URL matches the expected regex patterns.
    result can be a URL string (from active_url_from_accessTree) or a dict with 'url' field.
    rules["expected"] is a list of regex patterns; all must match for success (AND logic).
    """
    if not result:
        return 0.

    if isinstance(result, str):
        result_url = result
    elif isinstance(result, dict) and 'url' in result:
        result_url = result['url']
    else:
        logger.error(f"Invalid result format: {type(result)}, expected string URL or dict with 'url' field")
        return 0.

    logger.info(f"Result URL to match: {result_url}")

    patterns = rules["expected"]
    logger.info(f"Expected patterns: {patterns}")
    for pattern in patterns:
        match = re.search(pattern, result_url)
        if not match:
            logger.info(f"Pattern '{pattern}' did not match URL '{result_url}'")
            return 0.
    return 1.


def is_expected_bookmarks(bookmarks, rule) -> float:
    """
    Checks if the expected bookmarks are present in Chrome's bookmark bar.
    Modified from original: uses subset check for bookmark_bar_websites_urls
    (expected_urls.issubset(actual_urls)) instead of exact set equality,
    so pre-existing bookmarks on the bar do not cause false negatives.
    Also uses .get() for safer dict access on bookmark item keys.
    """
    if not bookmarks:
        return 0.

    if rule['type'] == "bookmark_bar_folders_names":
        bookmark_bar_folders_names = [
            bookmark['name'] for bookmark in bookmarks['bookmark_bar']['children']
            if bookmark.get('type') == 'folder'
        ]
        return 1. if set(bookmark_bar_folders_names) == set(rule['names']) else 0.

    elif rule['type'] == "bookmark_bar_websites_urls":
        bookmark_bar_websites_urls = [
            bookmark['url'] for bookmark in bookmarks['bookmark_bar']['children']
            if bookmark.get('type') == 'url'
        ]
        # Subset check: expected URLs must be present among bookmarked URLs.
        # This tolerates other pre-existing bookmarks on the bar.
        expected_urls = set(rule['urls'])
        actual_urls = set(bookmark_bar_websites_urls)
        logger.info(f"Expected bookmark URLs: {expected_urls}")
        logger.info(f"Actual bookmark bar URLs: {actual_urls}")
        return 1. if expected_urls.issubset(actual_urls) else 0.

    elif rule['type'] == "liked_authors_websites_urls":
        liked_authors_folder = next((
            bookmark for bookmark in bookmarks['bookmark_bar']['children']
            if bookmark.get('type') == 'folder' and bookmark.get('name') == 'Liked Authors'
        ), None)
        if liked_authors_folder:
            logger.info("'Liked Authors' folder exists")
            liked_authors_urls = [
                bookmark['url'] for bookmark in liked_authors_folder['children']
                if bookmark.get('type') == 'url'
            ]
            logger.info(f"'Liked Authors' folder URLs: {liked_authors_urls}")

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
