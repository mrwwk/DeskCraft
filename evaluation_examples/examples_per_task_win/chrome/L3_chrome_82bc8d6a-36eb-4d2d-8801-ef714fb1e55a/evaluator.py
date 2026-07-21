import json
import logging
import os
import sqlite3

logger = logging.getLogger("desktopenv.metric.general")


def check_flight_search(result_path, rules, **options):
    """
    Check Chrome history SQLite DB for Qatar Airways flight search evidence.

    This function opens the Chrome History database (captured via vm_file
    getter from the VM) and searches for a URL that contains all the
    required patterns, proving the agent visited the Qatar Airways
    flight search results page with the correct parameters.

    Args:
        result_path: Path to Chrome History SQLite DB (from vm_file getter).
        rules: Dict with:
            - "url_contains": list of strings that must ALL appear in a URL.
            - "date_contains": optional string that must appear in the URL.
        **options: Additional options (unused).

    Returns:
        float: 1.0 if a matching URL is found in history, 0.0 otherwise.
    """
    if result_path is None:
        logger.info("History DB path is None, returning 0.0")
        return 0.0

    if not os.path.exists(result_path):
        logger.info(f"History DB not found at {result_path}, returning 0.0")
        return 0.0

    url_contains = rules.get("url_contains", [])
    date_contains = rules.get("date_contains", "")

    if not url_contains:
        logger.info("No url_contains patterns provided, returning 0.0")
        return 0.0

    try:
        conn = sqlite3.connect(result_path)
        cursor = conn.cursor()

        # Query all URLs from Chrome history
        cursor.execute("SELECT url FROM urls")
        rows = cursor.fetchall()
        conn.close()

        logger.info(f"Checking {len(rows)} URLs in Chrome history")

        for (url,) in rows:
            if url is None:
                continue
            url_lower = url.lower()

            # All required patterns must be found in this URL
            all_found = True
            for pattern in url_contains:
                if pattern.lower() not in url_lower:
                    all_found = False
                    break

            if all_found and (not date_contains or date_contains in url):
                logger.info(f"Found matching URL in history: {url}")
                return 1.0

        logger.info("No matching URL found in Chrome history")
        return 0.0

    except sqlite3.OperationalError as e:
        logger.error(f"SQLite error reading Chrome history: {e}")
        return 0.0
    except Exception as e:
        logger.error(f"Unexpected error checking Chrome history: {e}")
        return 0.0


def check_do_not_track(result_path, rules, **options):
    """
    Check Chrome Preferences JSON for Do Not Track being enabled.

    This function reads the Chrome Preferences file (captured via vm_file
    getter from the VM) and checks whether the "Do Not Track" privacy
    setting is enabled.

    Args:
        result_path: Path to Chrome Preferences JSON (from vm_file getter).
        rules: Dict with "expected": "true".
        **options: Additional options (unused).

    Returns:
        float: 1.0 if Do Not Track is enabled, 0.0 otherwise.
    """
    if result_path is None:
        logger.info("Preferences path is None, returning 0.0")
        return 0.0

    if not os.path.exists(result_path):
        logger.info(f"Preferences file not found at {result_path}, returning 0.0")
        return 0.0

    try:
        with open(result_path, 'r', encoding='utf-8') as f:
            prefs = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error in Preferences: {e}")
        return 0.0
    except Exception as e:
        logger.error(f"Error reading Preferences file: {e}")
        return 0.0

    dnt_enabled = False

    # Method 1: profile.enable_do_not_track (older Chrome versions)
    profile = prefs.get("profile", {})
    if isinstance(profile, dict):
        if profile.get("enable_do_not_track") is True:
            dnt_enabled = True
            logger.info("DNT enabled via profile.enable_do_not_track")

    # Method 2: content_settings.exceptions.do_not_track (newer Chrome)
    if not dnt_enabled and isinstance(profile, dict):
        cs = profile.get("content_settings", {})
        if isinstance(cs, dict):
            exc = cs.get("exceptions", {})
            if isinstance(exc, dict):
                dnt_exc = exc.get("do_not_track", {})
                if isinstance(dnt_exc, dict):
                    for key, value in dnt_exc.items():
                        if isinstance(value, dict):
                            setting = value.get("setting")
                            if setting in [1, "1"]:
                                dnt_enabled = True
                                logger.info(f"DNT enabled via content_settings exception: {key}")
                                break

    # Method 3: Fallback recursive search for any truthy do_not_track key
    if not dnt_enabled:
        dnt_enabled = _recursive_search_dnt(prefs)
        if dnt_enabled:
            logger.info("DNT enabled via recursive search")

    logger.info(f"Do Not Track enabled: {dnt_enabled}")
    return 1.0 if dnt_enabled else 0.0


def _recursive_search_dnt(obj, depth=0):
    """
    Recursively search a nested dict/list for any key containing
    'do_not_track' with a truthy value.
    """
    if depth > 12:
        return False
    if isinstance(obj, dict):
        for key, value in obj.items():
            key_lower = key.lower()
            if "do_not_track" in key_lower:
                if value is True or value == 1 or str(value).lower() == "true":
                    return True
            if _recursive_search_dnt(value, depth + 1):
                return True
    elif isinstance(obj, list):
        for item in obj:
            if _recursive_search_dnt(item, depth + 1):
                return True
    return False
