import json
import logging

logger = logging.getLogger("desktopenv.metric.custom")


def check_customer_update_file(result, expected, **options):
    if result is None:
        return 0.0

    try:
        payload = json.loads(result.strip()) if isinstance(result, str) else dict(result)
    except Exception as exc:
        logger.warning("failed to parse interruption payload: %s", exc)
        return 0.0

    actual = payload.get("customer_content")
    if actual is None:
        return 0.0

    actual_norm = actual.replace("\r\n", "\n").rstrip()
    expected_norm = expected.get("expected_content", "").replace("\r\n", "\n").rstrip()
    if actual_norm != expected_norm:
        return 0.0

    if expected.get("incident_must_be_absent_or_empty") and payload.get("incident_nonempty"):
        return 0.0

    return 1.0
