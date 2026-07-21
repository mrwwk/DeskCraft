import logging

logger = logging.getLogger("desktopenv.metric.general")


def check_include_exclude(result_path, rules, **options):
    """
    Read file content from result_path and check that all "include" strings
    are present and no "exclude" strings are present.

    Uses substring matching, so minor formatting differences (e.g. missing
    newlines between sections) do not cause false negatives.

    Args:
        result_path (str): Path to the result file on local disk.
        rules (dict): Dict with "include" (list of required substrings)
                      and "exclude" (list of forbidden substrings).
        **options: Reserved for framework compatibility; unused.

    Returns:
        float: 1.0 if all include strings are found and no exclude strings
               are found; 0.0 otherwise.
    """
    if result_path is None:
        logger.warning("result_path is None, returning 0.0")
        return 0.

    try:
        with open(result_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        logger.warning("Result file not found: %s", result_path)
        return 0.
    except Exception as e:
        logger.warning("Failed to read result file %s: %s", result_path, e)
        return 0.

    include = rules.get("include", [])
    exclude = rules.get("exclude", [])

    missing = [r for r in include if r not in content]
    if missing:
        logger.info("Missing required content: %s", missing)
        return 0.

    unexpected = [r for r in exclude if r in content]
    if unexpected:
        logger.info("Found unexpected content: %s", unexpected)
        return 0.

    return 1.
