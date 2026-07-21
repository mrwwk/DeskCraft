import logging
import re

logger = logging.getLogger("desktopenv.metric.custom")


def check_arxiv_url_patterns(result, expected, **options) -> float:
    """
    Check that the arXiv search URL contains all required query parameters.

    Uses regex patterns to verify that the URL includes:
    - search path with query parameters
    - query=vision+transformer (or %20 variant)
    - searchtype=all
    - abstracts=show
    - order=-announced_date_first

    Args:
        result: URL string or dict with 'url' key from active_tab_info getter.
        expected: dict with 'patterns' key containing a list of regex pattern strings.
        **options: Additional options (unused).

    Returns:
        1.0 if all patterns match, 0.0 otherwise.
    """
    if result is None:
        logger.info("check_arxiv_url_patterns: result is None, returning 0.0")
        return 0.0

    # Extract URL string from whatever active_tab_info returns
    if isinstance(result, dict):
        url = result.get("url", "") or str(result)
    else:
        url = str(result)

    if not url:
        logger.info("check_arxiv_url_patterns: empty URL extracted, returning 0.0")
        return 0.0

    patterns = expected.get("patterns", [])
    if not patterns:
        logger.info("check_arxiv_url_patterns: no patterns in expected, returning 0.0")
        return 0.0

    logger.info(f"check_arxiv_url_patterns: checking URL '{url}' against {len(patterns)} patterns")

    for pattern in patterns:
        if not re.search(pattern, url, re.IGNORECASE):
            logger.info(f"check_arxiv_url_patterns: pattern '{pattern}' NOT found in URL, returning 0.0")
            return 0.0

    logger.info("check_arxiv_url_patterns: all patterns matched, returning 1.0")
    return 1.0


def check_safe_browsing_enabled(result, expected, **options) -> float:
    """
    Check that Chrome's Safe Browsing protection is enabled.

    Args:
        result: String from enable_safe_browsing getter (e.g. "true" or "false").
        expected: dict with 'expected' key containing the expected value (default "true").
        **options: Additional options (unused).

    Returns:
        1.0 if result matches expected, 0.0 otherwise.
    """
    if result is None:
        logger.info("check_safe_browsing_enabled: result is None, returning 0.0")
        return 0.0

    expected_val = expected.get("expected", "true") if isinstance(expected, dict) else str(expected)

    # Normalize both to lowercase stripped strings for robust comparison
    result_str = str(result).strip().lower()
    expected_str = str(expected_val).strip().lower()

    logger.info(f"check_safe_browsing_enabled: result='{result_str}', expected='{expected_str}'")

    if result_str == expected_str:
        return 1.0
    else:
        return 0.0
