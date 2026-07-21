import logging

logger = logging.getLogger("desktopenv.metrics.basic_os")


def _parse_kv(output: str) -> dict:
    """Parse key=value lines from shell output into a dict."""
    result = {}
    if not output:
        return result
    for line in output.strip().split("\n"):
        line = line.strip()
        if "=" in line:
            k, v = line.split("=", 1)
            result[k.strip()] = v.strip()
    return result


def check_os_batch_extract(result: str, rules: dict) -> float:
    """
    Verify batch extraction and classification by file type.
    Shell collector outputs key=value for each expected file/dir.
    """
    try:
        kv = _parse_kv(result)
        checks = rules.get("checks", {})
        for key, expected in checks.items():
            if kv.get(key) != expected:
                return 0.0
        return 1.0
    except Exception as e:
        logger.error(f"check_os_batch_extract error: {e}")
        return 0.0
