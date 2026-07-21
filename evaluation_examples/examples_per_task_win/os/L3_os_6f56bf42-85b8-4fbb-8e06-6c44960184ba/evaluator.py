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


def check_os_deploy_files(result: str, rules: dict) -> float:
    """
    Verify file deployment to multiple directories.
    Shell collector dynamically enumerates all node* directories (excluding /backup/),
    checks file existence, content match (cmp), permissions=600, and mtime preservation,
    then outputs a single aggregate key: all_nodes_ok=true/false.
    Expected rules: {"checks": {"all_nodes_ok": "true", "no_backup_node4": "true", "no_backup_deep": "true"}}
    """
    try:
        kv = _parse_kv(result)
        checks = rules.get("checks", {})
        for key, expected_val in checks.items():
            if kv.get(key) != expected_val:
                return 0.0
        return 1.0
    except Exception as e:
        logger.error(f"check_os_deploy_files error: {e}")
        return 0.0
