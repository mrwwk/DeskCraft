import json
import logging

logger = logging.getLogger("desktopenv.metric.custom")


def check_pptx_title_changed(result: str, rules: dict = None) -> float:
    """
    Verify that slide 1 text was extracted and that its cover title changed.

    The vm_command_line result is expected to be a JSON list of text runs from
    ppt/slides/slide1.xml. In the source template, the first text run is the
    cover-slide title.
    """
    if result is None or not isinstance(result, str):
        logger.warning("Result is None or not a string - PPTX text extraction failed")
        return 0.0

    if not result.strip():
        logger.warning("Result is empty - PPTX text extraction returned no text")
        return 0.0

    rules = rules or {}
    exclude = rules.get("exclude", [])

    try:
        parsed = json.loads(result)
        texts = parsed if isinstance(parsed, list) else [str(parsed)]
    except Exception:
        texts = [result]

    texts = [str(text).strip() for text in texts if str(text).strip()]
    if not texts:
        logger.warning("Slide 1 text extraction returned no usable text")
        return 0.0

    title = texts[0]
    for pattern in exclude:
        if pattern in title:
            logger.info(
                "Original title '%s' still found in slide 1 title - title was not changed",
                pattern,
            )
            return 0.0

    logger.info("PPTX title change verified: slide 1 title changed to '%s'", title)
    return 1.0
