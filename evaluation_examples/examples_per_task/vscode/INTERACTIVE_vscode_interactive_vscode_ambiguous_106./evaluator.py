import json
import logging

logger = logging.getLogger("desktopenv.metric.handoff")


def check_handoff_workspace(result, rules, **options):
    if result is None:
        return 0.0

    try:
        payload = json.loads(result.strip()) if isinstance(result, str) else dict(result)
    except Exception as exc:
        logger.warning("failed to parse result payload: %s", exc)
        return 0.0

    if payload.get("handoff_content") != rules.get("handoff_content"):
        return 0.0
    if payload.get("files_autoSave") != rules.get("files_autoSave"):
        return 0.0
    if payload.get("files_autoSaveDelay") != rules.get("files_autoSaveDelay"):
        return 0.0
    if payload.get("editor_wordWrap") != rules.get("editor_wordWrap"):
        return 0.0
    return 1.0
