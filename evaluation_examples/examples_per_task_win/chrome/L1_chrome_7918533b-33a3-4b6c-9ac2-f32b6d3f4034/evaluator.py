"""
Evaluator for change_chrome_language_to_french task.

Metric 1 (exact_match): checks Chrome display language is "fr"
Metric 2 (check_include_exclude): checks Chrome is on Languages settings page
"""
from typing import Dict, List


def exact_match(result, rules) -> float:
    """Check that result exactly matches the expected value."""
    if result is None:
        return 0.0
    expect = rules["expected"]
    if result == expect:
        return 1.0
    else:
        return 0.0


def check_include_exclude(result: str, rules: Dict[str, List[str]]) -> float:
    """Check that result includes all strings in include list and none in exclude list."""
    if result is None:
        return 0.0

    include = rules.get("include", [])
    exclude = rules.get("exclude", [])
    if all(r in result for r in include) and all(r not in result for r in exclude):
        return 1.0
    else:
        return 0.0
