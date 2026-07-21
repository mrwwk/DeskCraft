import logging
from typing import Dict, List

logger = logging.getLogger("desktopenv.metric.general")


def check_include_exclude(result: str, rules: Dict[str, List[str]]) -> float:
    """Check if result string contains all 'include' patterns and none of 'exclude' patterns.

    Used by evaluator with vm_command_line result getter: the VM command prints
    'PASSED' when all conditions (backup exists, Profit column present, Sales
    sorted descending) are met, otherwise 'FAILED'.
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
