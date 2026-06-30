import logging
from typing import Dict, List

logger = logging.getLogger("desktopenv.metric.general")


def check_include_exclude(result: str, rules: Dict[str, List[str]]) -> float:
    """
    Check if the result string contains all required substrings (include)
    and does not contain any forbidden substrings (exclude).

    Args:
        result: The string output to check (e.g. stdout of a VM command).
        rules: Dict with "include" (list of required substrings) and
               "exclude" (list of forbidden substrings).

    Returns:
        1.0 if all include strings are present and no exclude strings are
        present; otherwise 0.0.
    """
    if result is None:
        return 0.

    print(result, rules)
    include = rules.get("include", [])
    exclude = rules.get("exclude", [])
    if all(r in result for r in include) and all(r not in result for r in exclude):
        return 1.
    else:
        return 0.
