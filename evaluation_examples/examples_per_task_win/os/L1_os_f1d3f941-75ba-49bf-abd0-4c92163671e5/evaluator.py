import logging
import re

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


def check_os_night_light(result: str, rules: dict) -> float:
    """
    Verify Night Light settings.
    Shell collector outputs: enabled=..., temperature=..., file_ok=...
    Expected rules: {"enabled": "true", "temperature": "3700"}
    """
    try:
        kv = _parse_kv(result)
        if kv.get("enabled") != rules.get("enabled", "true"):
            return 0.0
        if kv.get("temperature") != rules.get("temperature", "3700"):
            return 0.0
        if kv.get("file_ok") != "true":
            return 0.0
        return 1.0
    except Exception as e:
        logger.error(f"check_os_night_light error: {e}")
        return 0.0
