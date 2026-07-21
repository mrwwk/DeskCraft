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


def check_os_power_settings(result: str, rules: dict) -> float:
    """
    Verify power settings.
    Shell collector outputs: idle_dim=..., idle_delay=..., file_ok=...
    Expected rules: {"idle_dim": "false", "idle_delay": "0"}
    """
    try:
        kv = _parse_kv(result)
        if kv.get("idle_dim") != rules.get("idle_dim", "false"):
            return 0.0
        if kv.get("idle_delay") != rules.get("idle_delay", "0"):
            return 0.0
        if kv.get("file_ok") != "true":
            return 0.0
        return 1.0
    except Exception as e:
        logger.error(f"check_os_power_settings error: {e}")
        return 0.0
