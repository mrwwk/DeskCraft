import logging

logger = logging.getLogger("desktopenv.metric.custom")


def check_customer_update_file(result_path, expected, **options):
    """
    Check that the customer_update.md file pulled from VM has the correct content.

    Args:
        result_path: Local file path to customer_update.md (from vm_file getter).
        expected: Dict with key "expected_content" containing the expected file text.
        **options: Additional options (unused).

    Returns:
        float: 1.0 if content matches, 0.0 otherwise.
    """
    if result_path is None:
        logger.warning("result_path is None, returning 0.0")
        return 0.0

    try:
        with open(result_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except (FileNotFoundError, IOError, OSError) as e:
        logger.warning(f"Cannot read result file {result_path}: {e}")
        return 0.0
    except Exception as e:
        logger.error(f"Unexpected error reading {result_path}: {e}")
        return 0.0

    expected_content = expected.get("expected_content", "")
    if not expected_content:
        logger.warning("No expected_content in rules, returning 0.0")
        return 0.0

    # Normalize: convert Windows line endings, strip trailing whitespace/newlines
    content_norm = content.replace('\r\n', '\n').rstrip()
    expected_norm = expected_content.replace('\r\n', '\n').rstrip()

    if content_norm == expected_norm:
        return 1.0

    logger.info(
        "Content mismatch. "
        "Expected len=%d, got len=%d. "
        "Expected repr first 200: %r",
        len(expected_norm), len(content_norm),
        expected_norm[:200]
    )
    return 0.0
