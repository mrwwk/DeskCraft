"""
Evaluator for task: google_search_pdf_dnt
Checks:
  1. Google search results page is open with the correct query (URL regex match)
  2. Chrome Safe Browsing protection is enabled (exact match)
"""
import logging
import re

logger = logging.getLogger("desktopenv.metrics.chrome")


def is_expected_url_pattern_match(result, rules) -> float:
    """
    Check if the active tab URL matches the expected regex patterns.
    
    Args:
        result: Output of active_tab_info getter - can be a string URL or a dict with 'url' field.
        rules: Expected rules dict with 'expected' key containing a list of regex pattern strings.
    
    Returns:
        1.0 if all patterns match the URL, 0.0 otherwise.
    """
    if not result:
        logger.warning("is_expected_url_pattern_match: result is falsy, returning 0.0")
        return 0.0

    # Extract URL from result - can be either a string URL or a dict with 'url' field
    if isinstance(result, str):
        result_url = result
    elif isinstance(result, dict) and 'url' in result:
        result_url = result['url']
    else:
        logger.error(f"Invalid result format: {type(result)}, expected string URL or dict with 'url' field")
        return 0.0

    logger.info(f"Result URL to match: {result_url}")

    patterns = rules["expected"]
    logger.info(f"Expected regex patterns: {patterns}")

    for pattern in patterns:
        match = re.search(pattern, result_url)
        logger.info(f"Pattern '{pattern}' matched: {bool(match)}")
        if not match:
            return 0.0

    return 1.0


def exact_match(result, rules) -> float:
    """
    Check if the result exactly matches the expected value.
    
    Args:
        result: Output of enable_safe_browsing getter - typically a string like "true"/"false".
        rules: Expected rules dict with 'expected' key containing the expected value.
    
    Returns:
        1.0 if result matches expected, 0.0 otherwise.
    """
    if result is None:
        logger.warning("exact_match: result is None, returning 0.0")
        return 0.0

    expect = rules["expected"]
    logger.info(f"exact_match: result='{result}', expected='{expect}'")

    # Case-insensitive string comparison for robustness
    if str(result).strip().lower() == str(expect).strip().lower():
        return 1.0
    else:
        return 0.0
