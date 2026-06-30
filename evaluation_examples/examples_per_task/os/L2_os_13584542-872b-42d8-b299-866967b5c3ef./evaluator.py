# Revised evaluator for terminal_size_persist task (13584542-872b-42d8-b299-866967b5c3ef)
# Fixes:
#   1. Flexible grep in result command (task.json) accepts both "stty rows 46 cols 140"
#      and "stty cols 140 rows 46" (semantically equivalent in stty).
#   2. Removed size_ok as a hard requirement: vm_command_line is not a GUI terminal,
#      so stty size is unreliable. The postconfig opens a new GUI terminal and types
#      "stty size" for visual verification; bashrc_ok verifies the config is in place.
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


def check_os_terminal_size(result: str, rules: dict) -> float:
    """
    Verify terminal size persistence and bashrc backup.

    Shell collector outputs: size_ok=..., backup_ok=..., bashrc_ok=...
    Expected rules: {"rows": "46", "cols": "140"}

    Note: size_ok is computed but NOT required as a hard condition,
    because vm_command_line runs in a non-GUI shell where stty size is
    unreliable. The postconfig already opens a new GUI terminal and types
    "stty size" for visual verification. bashrc_ok (with flexible grep)
    ensures the stty configuration is correctly present in ~/.bashrc.
    """
    try:
        kv = _parse_kv(result)
        # backup must exist
        if kv.get("backup_ok") != "true":
            return 0.0
        # bashrc must contain the stty config (flexible grep handles both
        # "stty rows 46 cols 140" and "stty cols 140 rows 46")
        if kv.get("bashrc_ok") != "true":
            return 0.0
        # size_ok is best-effort; not required (see docstring above)
        return 1.0
    except Exception as e:
        logger.error(f"check_os_terminal_size error: {e}")
        return 0.0
