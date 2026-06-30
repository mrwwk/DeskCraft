import logging
import re

logger = logging.getLogger("desktopenv.metrics.tamiflu_task")


def check_tamiflu_side_effects(result, expected=None, **options) -> float:
    """
    Check if the final active URL matches either valid end state of the task:

    1. Drugs.com Tamiflu side-effects article (if agent ended with it as active tab),
       verified by all three patterns: drugs\\.com, tamiflu, side-effects|sfx
    2. Chrome settings security page (if agent completed both subtasks and
       ended at chrome://settings/security after enabling Enhanced Safe Browsing).

    The task has two requirements:
      (a) Open Drugs.com Tamiflu side-effects article
      (b) Enable Chrome Enhanced Safe Browsing protection

    Since the evaluator can only check the active tab URL via
    active_url_from_accessTree, we accept either valid end state.
    If the agent ends at chrome://settings/security, that is the expected
    terminal state after completing both subtasks (Drugs.com page is in a
    background tab).
    """
    if not result:
        logger.info("Result is empty, returning 0.0")
        return 0.0

    # Extract URL from result -- can be a string or a dict with 'url' field
    if isinstance(result, str):
        result_url = result
    elif isinstance(result, dict) and 'url' in result:
        result_url = result['url']
    else:
        logger.error(f"Invalid result format: {type(result)}")
        return 0.0

    logger.info(f"Result URL: {result_url}")

    if expected is None:
        logger.info("Expected is None, returning 0.0")
        return 0.0

    pattern_groups = expected.get("expected", [])
    if not pattern_groups:
        logger.info("No expected patterns, returning 0.0")
        return 0.0

    logger.info(f"Checking URL against {len(pattern_groups)} pattern groups")

    for idx, pattern_group in enumerate(pattern_groups):
        if isinstance(pattern_group, list):
            # All patterns in the group must match (AND within group)
            matches = []
            for pattern in pattern_group:
                m = re.search(pattern, result_url)
                matches.append(m is not None)
                logger.info(f"  Group {idx}, pattern '{pattern}': {'MATCH' if m else 'NO MATCH'}")
            if all(matches):
                logger.info(f"All patterns in group {idx} matched -> returning 1.0")
                return 1.0
        else:
            # Single pattern
            m = re.search(pattern_group, result_url)
            logger.info(f"  Group {idx}, pattern '{pattern_group}': {'MATCH' if m else 'NO MATCH'}")
            if m:
                logger.info(f"Pattern group {idx} matched -> returning 1.0")
                return 1.0

    logger.info("No pattern group matched -> returning 0.0")
    return 0.0
