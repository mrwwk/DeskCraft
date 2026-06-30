import logging

logger = logging.getLogger("desktopenv.metric.custom")


def check_pptx_title_changed(result: str, rules: dict = None) -> float:
    """
    Verify that PPTX text was successfully extracted and that specified
    original title patterns have been removed — indicating the title was
    changed in response to an ambiguous interactive instruction like
    "Help me change that title".

    Checks:
      1. Text extraction succeeded (result is a non-empty string)
      2. Original title substrings (from exclude list) are no longer present

    Args:
        result: Extracted text from PPTX file via vm_command_line
        rules: Dict with optional 'exclude' list of substrings that should
               NOT appear in the result.

    Returns:
        1.0 if text was extracted and original titles are absent, 0.0 otherwise.
    """
    if result is None or not isinstance(result, str):
        logger.warning("Result is None or not a string — PPTX text extraction failed")
        return 0.0

    if not result.strip():
        logger.warning("Result is empty — PPTX text extraction returned no text")
        return 0.0

    if rules is None:
        rules = {}

    exclude = rules.get("exclude", [])

    for pattern in exclude:
        if pattern in result:
            logger.info(
                "Original title '%s' still found in PPTX text — title was not changed",
                pattern,
            )
            return 0.0

    logger.info(
        "PPTX title change verified: text extracted (%d chars), original titles removed",
        len(result),
    )
    return 1.0
