import json
import logging
import re

logger = logging.getLogger("desktopenv.metric.recreation")


def check_page_has_availability_grid(result, expected=None, **options) -> float:
    """
    Check that the result HTML parse data contains the camp-sortable-column-header key
    with a non-empty value, indicating the campground availability grid is visible on the page.

    Args:
        result: Dict from active_tab_html_parse (e.g. {"camp-sortable-column-header": "Sat4"})
                or a JSON string that can be parsed into such a dict.
        expected: Not used (null expected in config). Accepted for framework compatibility.
        **options: Additional options (unused).

    Returns:
        1.0 if the availability grid column header exists with non-empty content, 0.0 otherwise.
    """
    if isinstance(result, str):
        result = result.strip()
        result = result.replace("'", '"')
        try:
            result = json.loads(result)
        except json.JSONDecodeError:
            logger.warning("check_page_has_availability_grid: failed to parse result JSON string")
            return 0.

    if result is None:
        logger.info("check_page_has_availability_grid: result is None")
        return 0.

    if not isinstance(result, dict):
        logger.info("check_page_has_availability_grid: result is not a dict, got %s", type(result))
        return 0.

    header_value = result.get("camp-sortable-column-header", None)
    if header_value is not None and len(str(header_value).strip()) > 0:
        logger.info("check_page_has_availability_grid: found camp-sortable-column-header with value '%s'", header_value)
        return 1.0

    logger.info("check_page_has_availability_grid: camp-sortable-column-header not found or empty in result")
    return 0.


def check_sorting_label(result, expected=None, **options) -> float:
    """
    Check that the page exposes the requested availability sort label.
    """
    if isinstance(result, str):
        result = result.strip()
        result = result.replace("'", '"')
        try:
            result = json.loads(result)
        except json.JSONDecodeError:
            logger.warning("check_sorting_label: failed to parse result JSON string")
            return 0.

    if not isinstance(result, dict):
        logger.info("check_sorting_label: result is not a dict, got %s", type(result))
        return 0.

    expected_text = ""
    if isinstance(expected, dict):
        expected_text = expected.get("expected", "")

    actual_text = result.get("availability_sort", "")
    normalize = lambda value: re.sub(r"\s+", " ", str(value)).strip().lower()

    if normalize(expected_text) and normalize(expected_text) in normalize(actual_text):
        logger.info("check_sorting_label: found expected sort label '%s'", expected_text)
        return 1.0

    logger.info(
        "check_sorting_label: expected '%s' not found in actual '%s'",
        expected_text,
        actual_text,
    )
    return 0.


def is_expected_url_pattern_match(result, rules) -> float:
    """
    Check that the active tab URL matches all expected regex patterns.

    Args:
        result: URL string or dict with 'url' key (from active_tab_info).
        rules: Dict with "expected" key containing a list of regex pattern strings.

    Returns:
        1.0 if all patterns match the URL, 0.0 otherwise.
    """
    if not result:
        return 0.

    # Extract URL from result parameter
    if isinstance(result, str):
        result_url = result
    elif isinstance(result, dict) and 'url' in result:
        result_url = result['url']
    else:
        logger.error("is_expected_url_pattern_match: invalid result format: %s", type(result))
        return 0.

    logger.info("is_expected_url_pattern_match: result URL: %s", result_url)

    patterns = rules["expected"]
    logger.info("is_expected_url_pattern_match: patterns: %s", patterns)

    for pattern in patterns:
        match = re.search(pattern, result_url)
        if not match:
            logger.info("is_expected_url_pattern_match: pattern '%s' not found in URL, returning 0.0", pattern)
            return 0.

    logger.info("is_expected_url_pattern_match: all patterns matched, returning 1.0")
    return 1.0
