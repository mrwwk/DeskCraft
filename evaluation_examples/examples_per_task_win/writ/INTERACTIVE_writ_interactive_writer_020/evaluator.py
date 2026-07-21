from typing import Dict, List


def check_include_exclude(result: str, rules: Dict[str, List[str]]) -> float:
    """
    Check whether result string contains all required substrings (include)
    and none of the forbidden substrings (exclude).

    Args:
        result: The text content to check.
        rules: Dict with "include" (list of required substrings) and
               "exclude" (list of forbidden substrings).

    Returns:
        1.0 if all include substrings are present and no exclude substrings
        are present; otherwise 0.0.
    """
    if result is None:
        return 0.

    include = rules.get("include", [])
    exclude = rules.get("exclude", [])
    if all(r in result for r in include) and all(r not in result for r in exclude):
        return 1.
    else:
        return 0.
