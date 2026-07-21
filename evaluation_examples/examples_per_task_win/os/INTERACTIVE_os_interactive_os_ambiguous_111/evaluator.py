"""
Evaluator for interactive_os_ambiguous_111: station preparation check.

Checks three independent conditions:
1. GNOME favorite apps set to the expected triplet
2. Battery percentage display enabled
3. station_prep.txt exists with the expected content

Uses vm_file getters (via postconfig dump) for robust metric artifact capture.
"""
import logging
import os

logger = logging.getLogger("desktopenv.metric.station_prep")


def check_favorite_apps(result_file, rules, **options):
    """
    Check that GNOME shell favorite-apps matches expected list.

    Args:
        result_file: Local path to file containing gsettings get output.
        rules: dict with "expected" key (whitespace-normalized expected string).
    Returns:
        float: 1.0 if match, 0.0 otherwise.
    """
    if result_file is None:
        logger.warning("check_favorite_apps: result_file is None")
        return 0.0
    if not os.path.exists(result_file):
        logger.warning(f"check_favorite_apps: file not found: {result_file}")
        return 0.0
    try:
        with open(result_file, "r") as f:
            content = f.read()
        # Normalize: remove all whitespace for comparison (gsettings output
        # may contain spaces after commas, and expected is whitespace-free).
        actual = "".join(content.split())
        expected = "".join(rules.get("expected", "").split())
        if actual == expected:
            return 1.0
        logger.info(f"check_favorite_apps mismatch: got '{actual}', expected '{expected}'")
        return 0.0
    except Exception as e:
        logger.error(f"check_favorite_apps error: {e}")
        return 0.0


def check_battery_percentage(result_file, rules, **options):
    """
    Check that show-battery-percentage is set to true.

    Args:
        result_file: Local path to file containing gsettings get output.
        rules: dict with "expected" key (expected string, e.g. "true").
    Returns:
        float: 1.0 if match, 0.0 otherwise.
    """
    if result_file is None:
        logger.warning("check_battery_percentage: result_file is None")
        return 0.0
    if not os.path.exists(result_file):
        logger.warning(f"check_battery_percentage: file not found: {result_file}")
        return 0.0
    try:
        with open(result_file, "r") as f:
            content = f.read().strip().lower()
        expected = rules.get("expected", "true").strip().lower()
        if content == expected:
            return 1.0
        logger.info(f"check_battery_percentage mismatch: got '{content}', expected '{expected}'")
        return 0.0
    except Exception as e:
        logger.error(f"check_battery_percentage error: {e}")
        return 0.0


def check_station_prep_file(result_file, rules, **options):
    """
    Check that station_prep.txt exists with the expected 4-line content.

    Args:
        result_file: Local path to station_prep.txt pulled from VM.
        rules: dict with "expected_content" key containing expected text.
    Returns:
        float: 1.0 if content matches, 0.0 otherwise.
    """
    if result_file is None:
        logger.warning("check_station_prep_file: result_file is None")
        return 0.0
    if not os.path.exists(result_file):
        logger.warning(f"check_station_prep_file: file not found: {result_file}")
        return 0.0
    try:
        with open(result_file, "r") as f:
            content = f.read().strip()
        expected = rules.get("expected_content", "").strip()
        if content == expected:
            return 1.0
        logger.info(f"check_station_prep_file mismatch: got '{repr(content)}', expected '{repr(expected)}'")
        return 0.0
    except Exception as e:
        logger.error(f"check_station_prep_file error: {e}")
        return 0.0
