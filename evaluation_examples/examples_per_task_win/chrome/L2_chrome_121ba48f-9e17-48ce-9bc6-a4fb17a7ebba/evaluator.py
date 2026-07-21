import logging
import re

logger = logging.getLogger("desktopenv.metrics.chrome")


def is_added_to_steam_cart(active_tab_info, rule):
    """
    Check if the expected items are present in the active tab's page content (Steam cart).
    """
    if not active_tab_info:
        return 0.

    items = rule.get('items', [])
    if not items:
        return 0.

    content = active_tab_info.get('content', '')
    if not content:
        logger.warning("active_tab_info has no 'content' field or content is empty")
        return 0.

    for item in items:
        if item not in content:
            logger.info("Item '%s' not found in cart content", item)
            return 0.

    return 1.


def is_expected_url_pattern_match(result, rules) -> float:
    """
    Check if the result URL matches all expected regex patterns.
    result can be a string URL or a dict with 'url' field (e.g. from active_tab_info).
    """
    if not result:
        return 0.

    # Extract URL from result parameter
    if isinstance(result, str):
        result_url = result
    elif isinstance(result, dict) and 'url' in result:
        result_url = result['url']
    else:
        logger.error("Invalid result format: %s, expected string URL or dict with 'url' field", type(result))
        return 0.

    logger.info("Result URL to match: %s", result_url)

    patterns = rules.get("expected", [])
    if not patterns:
        logger.warning("No expected patterns in rules")
        return 0.

    logger.info("expected patterns: %s", patterns)
    for pattern in patterns:
        match = re.search(pattern, result_url)
        logger.info("pattern '%s' match: %s", pattern, match)
        if not match:
            return 0.

    return 1.
