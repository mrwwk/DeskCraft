import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger("desktopenv.metric.general")


def check_reference_added(result: str, rules: Dict[str, Any]) -> float:
    """Check that an academic reference was added to the PPTX slides.

    This evaluator uses regex patterns to detect reference-like text in the
    extracted PPTX content, matching the open-ended task instruction
    "Help me add a reference on one of the slides".

    Args:
        result: Extracted text from PPTX (stdout of vm_command_line).
        rules: Dict with optional 'patterns' key containing a list of regex
               pattern strings.

    Returns:
        1.0 if any reference pattern matches the extracted text, 0.0 otherwise.
    """
    if result is None or not result.strip():
        logger.info("check_reference_added: result is None or empty")
        return 0.0

    patterns: List[str] = rules.get("patterns", [
        r'[A-Z][a-z]+,\s+[A-Z]\.\s*\(\d{4}\)',
        r'[A-Z][a-z]+\s+et\s+al\.?,?\s*\d{4}',
    ])

    for pattern in patterns:
        if re.search(pattern, result):
            logger.info(f"check_reference_added: matched pattern '{pattern}'")
            return 1.0

    logger.info(f"check_reference_added: no pattern matched. result[:200]={result[:200]}")
    return 0.0
