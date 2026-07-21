import logging
import re

logger = logging.getLogger("desktopenv.metrics.basic_os")


def check_os_recent_manifest(result: str, rules: dict) -> float:
    """
    Verify recent file manifest CSV matches expected content.
    Shell collector outputs the file content directly.
    Expected rules: {"expected": "path,count\\n..."}

    Normalizes './' prefix on relative paths before comparison,
    since 'find .' naturally produces './'-prefixed paths while
    expected paths may not include the prefix.
    """
    try:
        expected = rules.get("expected", "")
        if result is None:
            return 0.0

        def _normalize_path(line: str) -> str:
            """Strip './' prefix from the path component of a CSV line."""
            line = line.strip()
            # Remove leading './' if present (common output from find . command)
            line = re.sub(r'^\./', '', line)
            return line

        result_lines = [_normalize_path(l) for l in result.strip().split('\n') if l.strip()]
        expected_lines = [_normalize_path(l) for l in expected.strip().split('\n') if l.strip()]

        if result_lines == expected_lines:
            return 1.0
        return 0.0
    except Exception as e:
        logger.error(f"check_os_recent_manifest error: {e}")
        return 0.0
