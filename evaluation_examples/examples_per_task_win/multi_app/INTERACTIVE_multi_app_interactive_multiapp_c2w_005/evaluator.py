import logging
from typing import Dict, List

logger = logging.getLogger("desktopenv.metric.general")


def check_include_exclude(result: str, rules: Dict[str, List[str]]) -> float:
    """
    Check if result string contains all required substrings (include)
    and none of the forbidden substrings (exclude).

    Args:
        result (str): The text content to check.
        rules (Dict[str, List[str]]): dict with "include" and "exclude" keys,
            each mapping to a list of substrings.

    Returns:
        float: 1.0 if all include patterns are found and no exclude patterns
               are found, 0.0 otherwise (including when result is None).
    """
    if result is None:
        return 0.

    include = rules.get("include", [])
    exclude = rules.get("exclude", [])
    if all(r in result for r in include) and all(r not in result for r in exclude):
        return 1.
    else:
        return 0.
