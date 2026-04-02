import logging
import re

logger = logging.getLogger("desktopenv.metrics.basic_os")


# ==============================================================================
# Legacy functions (kept for backward compatibility)
# ==============================================================================

def check_gnome_favorite_apps(apps_str: str, rule):
    # parse the string like "['thunderbird.desktop', 'vim.desktop', 'google-chrome.desktop']"
    # to a list of strings
    apps = eval(apps_str)

    expected_apps = rule["expected"]

    if len(apps) != len(expected_apps):
        return 0

    if set(apps) == set(expected_apps):
        return 1
    else:
        return 0


def is_utc_0(timedatectl_output):
    utc_line = timedatectl_output.split("\n")[3]
    if utc_line.endswith("+0000)"):
        return 1
    else:
        return 0


def check_text_enlarged(scaling_factor_str):
    scaling_factor = float(scaling_factor_str)
    if scaling_factor > 1.0:
        return 1
    else:
        return 0


def check_moved_jpgs(directory_list, rule):
    expected_jpgs = rule["expected"]
    moved_jpgs = [node['name'] for node in directory_list['children']]

    if len(moved_jpgs) != len(expected_jpgs):
        return 0

    if set(moved_jpgs) == set(expected_jpgs):
        return 1
    else:
        return 0


def is_in_vm_clickboard(config, terminal_output):
    print("terminal_output: ")
    print(terminal_output)


# ==============================================================================
# Helper: parse "key=value" lines from shell output
# ==============================================================================

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


# ==============================================================================
# A. GNOME Desktop Settings Evaluators
# ==============================================================================

def check_os_timezone_utc(result: str, rules: dict) -> float:
    """
    Verify timezone is set to expected value and NTP is active.
    Shell collector outputs: timezone=..., ntp=..., file_ok=...
    Expected rules: {"timezone": "Etc/UTC", "ntp": "active"}
    """
    try:
        kv = _parse_kv(result)
        expected_tz = rules.get("timezone", "Etc/UTC")
        expected_ntp = rules.get("ntp", "active")
        if kv.get("timezone") != expected_tz:
            return 0.0
        if kv.get("ntp") != expected_ntp:
            return 0.0
        if kv.get("file_ok") != "true":
            return 0.0
        return 1.0
    except Exception as e:
        logger.error(f"check_os_timezone_utc error: {e}")
        return 0.0


def check_os_gnome_favorites(result: str, rules: dict) -> float:
    """
    Verify GNOME favorites are set in exact order.
    Shell collector outputs: favorites=..., file_ok=...
    Expected rules: {"expected_apps": ["thunderbird.desktop", ...]}
    """
    try:
        kv = _parse_kv(result)
        if kv.get("file_ok") != "true":
            return 0.0
        import ast
        apps = ast.literal_eval(kv.get("favorites", "[]"))
        expected = rules.get("expected_apps", [])
        if apps == expected:
            return 1.0
        return 0.0
    except Exception as e:
        logger.error(f"check_os_gnome_favorites error: {e}")
        return 0.0


def check_os_accessibility(result: str, rules: dict) -> float:
    """
    Verify accessibility settings: text scaling, cursor size, magnifier.
    Shell collector outputs: text_scale=..., cursor_size=..., mag_enabled=..., mag_factor=...
    Expected rules: {"min_text_scale": 1.2, "min_cursor_size": 48, "min_mag_factor": 1.5}
    """
    try:
        kv = _parse_kv(result)
        text_scale = float(kv.get("text_scale", "0"))
        cursor_size = int(kv.get("cursor_size", "0"))
        mag_enabled = kv.get("mag_enabled", "false")
        mag_factor = float(kv.get("mag_factor", "0"))

        if text_scale < rules.get("min_text_scale", 1.2):
            return 0.0
        if cursor_size < rules.get("min_cursor_size", 48):
            return 0.0
        if mag_enabled != "true":
            return 0.0
        if mag_factor <= rules.get("min_mag_factor", 1.5):
            return 0.0
        return 1.0
    except Exception as e:
        logger.error(f"check_os_accessibility error: {e}")
        return 0.0


def check_os_screen_lock(result: str, rules: dict) -> float:
    """
    Verify screen lock settings.
    Shell collector outputs: lock_enabled=..., idle_delay=..., lock_delay=..., file_ok=...
    Expected rules: {"lock_enabled": "true", "idle_delay": "300", "lock_delay": "0"}
    """
    try:
        kv = _parse_kv(result)
        if kv.get("lock_enabled") != rules.get("lock_enabled", "true"):
            return 0.0
        if kv.get("idle_delay") != rules.get("idle_delay", "300"):
            return 0.0
        if kv.get("lock_delay") != rules.get("lock_delay", "0"):
            return 0.0
        if kv.get("file_ok") != "true":
            return 0.0
        return 1.0
    except Exception as e:
        logger.error(f"check_os_screen_lock error: {e}")
        return 0.0


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


def check_os_notifications(result: str, rules: dict) -> float:
    """
    Verify notification settings.
    Shell collector outputs: show_banners=..., show_in_lock_screen=..., file_ok=...
    Expected rules: {"show_banners": "false", "show_in_lock_screen": "false"}
    """
    try:
        kv = _parse_kv(result)
        if kv.get("show_banners") != rules.get("show_banners", "false"):
            return 0.0
        if kv.get("show_in_lock_screen") != rules.get("show_in_lock_screen", "false"):
            return 0.0
        if kv.get("file_ok") != "true":
            return 0.0
        return 1.0
    except Exception as e:
        logger.error(f"check_os_notifications error: {e}")
        return 0.0


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


def check_os_battery_config(result: str, rules: dict) -> float:
    """
    Verify battery/power UI settings.
    Shell collector outputs: show_battery=..., power_profile=..., file_ok=...
    Expected rules: {"show_battery": "true", "allowed_power_profiles": ["balanced", "unsupported"]}
    """
    try:
        kv = _parse_kv(result)
        if kv.get("show_battery") != rules.get("show_battery", "true"):
            return 0.0
        actual_profile = kv.get("power_profile")
        expected_profile = rules.get("power_profile")
        allowed_profiles = rules.get("allowed_power_profiles")
        if expected_profile is not None and actual_profile != expected_profile:
            return 0.0
        if allowed_profiles is not None and actual_profile not in allowed_profiles:
            return 0.0
        if kv.get("file_ok") != "true":
            return 0.0
        return 1.0
    except Exception as e:
        logger.error(f"check_os_battery_config error: {e}")
        return 0.0


def check_os_audio_config(result: str, rules: dict) -> float:
    """
    Verify audio volume/mute and saved sink file.
    Shell collector outputs: volume=..., mute=..., sink_file_ok=...
    Expected rules: {"volume": "100", "mute": "no"}
    """
    try:
        kv = _parse_kv(result)
        if kv.get("volume") != rules.get("volume", "100"):
            return 0.0
        if kv.get("mute") != rules.get("mute", "no"):
            return 0.0
        if kv.get("sink_file_ok") != "true":
            return 0.0
        return 1.0
    except Exception as e:
        logger.error(f"check_os_audio_config error: {e}")
        return 0.0


# ==============================================================================
# B. File System Evaluators
# ==============================================================================

def check_os_file_manifest(result: str, rules: dict) -> float:
    """
    Verify that a file manifest matches expected content exactly.
    Shell collector outputs the file content directly.
    Expected rules: {"expected": "line1\\nline2\\n..."}
    """
    try:
        expected = rules.get("expected", "")
        if result is None:
            return 0.0
        if result.strip() == expected.strip():
            return 1.0
        return 0.0
    except Exception as e:
        logger.error(f"check_os_file_manifest error: {e}")
        return 0.0


def check_os_file_operations(result: str, rules: dict) -> float:
    """
    Generic file operations checker: verifies multiple file existence/absence/content conditions.
    Shell collector outputs key=value pairs for each check.
    Expected rules: {"checks": {"key1": "value1", "key2": "value2", ...}}
    All checks must pass.
    """
    try:
        kv = _parse_kv(result)
        checks = rules.get("checks", {})
        for key, expected_val in checks.items():
            if kv.get(key) != expected_val:
                return 0.0
        return 1.0
    except Exception as e:
        logger.error(f"check_os_file_operations error: {e}")
        return 0.0


def check_os_file_permissions(result: str, rules: dict) -> float:
    """
    Verify file permissions match expected values.
    Shell collector outputs: perm_<filename>=<mode> for each file.
    Expected rules: {"permissions": {"file1": "640", "file2": "755", ...}}
    """
    try:
        kv = _parse_kv(result)
        perms = rules.get("permissions", {})
        for fname, expected_mode in perms.items():
            key = f"perm_{fname}"
            if kv.get(key) != expected_mode:
                return 0.0
        return 1.0
    except Exception as e:
        logger.error(f"check_os_file_permissions error: {e}")
        return 0.0


def check_os_copy_filter(result: str, rules: dict) -> float:
    """
    Verify copy/move operations with filter conditions.
    Shell collector outputs: present_<name>=true/false, absent_<name>=true/false, extra checks.
    Expected rules: {"present": ["file1", ...], "absent": ["file2", ...], "extra_checks": {"key": "val"}}
    """
    try:
        kv = _parse_kv(result)
        for f in rules.get("present", []):
            if kv.get(f"present_{f}") != "true":
                return 0.0
        for f in rules.get("absent", []):
            if kv.get(f"absent_{f}") != "true":
                return 0.0
        for key, val in rules.get("extra_checks", {}).items():
            if kv.get(key) != val:
                return 0.0
        return 1.0
    except Exception as e:
        logger.error(f"check_os_copy_filter error: {e}")
        return 0.0


def check_os_dir_hierarchy(result: str, rules: dict) -> float:
    """
    Verify directory hierarchy operations.
    Shell collector outputs key=value checks.
    Expected rules: {"checks": {"key1": "val1", ...}, "manifest_match": "true"}
    """
    try:
        kv = _parse_kv(result)
        checks = rules.get("checks", {})
        for key, expected_val in checks.items():
            if kv.get(key) != expected_val:
                return 0.0
        if rules.get("manifest_match") and kv.get("manifest_match") != "true":
            return 0.0
        return 1.0
    except Exception as e:
        logger.error(f"check_os_dir_hierarchy error: {e}")
        return 0.0


def check_os_compress_logs(result: str, rules: dict) -> float:
    """
    Verify compressed log operations.
    Shell collector outputs key=value checks for gz existence, exclusion, report content.
    Expected rules: {"checks": {"key1": "val1", ...}}
    """
    try:
        kv = _parse_kv(result)
        checks = rules.get("checks", {})
        for key, expected_val in checks.items():
            if kv.get(key) != expected_val:
                return 0.0
        return 1.0
    except Exception as e:
        logger.error(f"check_os_compress_logs error: {e}")
        return 0.0


def check_os_deploy_files(result: str, rules: dict) -> float:
    """
    Verify file deployment to multiple directories.
    Shell collector outputs key=value checks for each target.
    Expected rules: {"checks": {"key1": "val1", ...}}
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


def check_os_trash_recovery(result: str, rules: dict) -> float:
    """
    Verify files recovered from trash.
    Shell collector outputs key=value checks.
    Expected rules: {"checks": {"key1": "val1", ...}}
    """
    try:
        kv = _parse_kv(result)
        checks = rules.get("checks", {})
        for key, expected_val in checks.items():
            if kv.get(key) != expected_val:
                return 0.0
        return 1.0
    except Exception as e:
        logger.error(f"check_os_trash_recovery error: {e}")
        return 0.0


def check_os_rename_dirs(result: str, rules: dict) -> float:
    """
    Verify directory rename operations and rename log.
    Shell collector outputs key=value checks.
    Expected rules: {"checks": {"key1": "val1", ...}}
    """
    try:
        kv = _parse_kv(result)
        checks = rules.get("checks", {})
        for key, expected_val in checks.items():
            if kv.get(key) != expected_val:
                return 0.0
        return 1.0
    except Exception as e:
        logger.error(f"check_os_rename_dirs error: {e}")
        return 0.0


# ==============================================================================
# C. Shell / Terminal Environment Evaluators
# ==============================================================================

def check_os_terminal_size(result: str, rules: dict) -> float:
    """
    Verify terminal size persistence and bashrc backup.
    Shell collector outputs: size_ok=..., backup_ok=..., bashrc_ok=...
    Expected rules: {"rows": "46", "cols": "140"}
    """
    try:
        kv = _parse_kv(result)
        if kv.get("size_ok") != "true":
            return 0.0
        if kv.get("backup_ok") != "true":
            return 0.0
        if kv.get("bashrc_ok") != "true":
            return 0.0
        return 1.0
    except Exception as e:
        logger.error(f"check_os_terminal_size error: {e}")
        return 0.0


def check_os_python_alias(result: str, rules: dict) -> float:
    """
    Verify python/pip alias configuration.
    Shell collector outputs: python_ok=..., pip_ok=..., file_ok=...
    """
    try:
        kv = _parse_kv(result)
        if kv.get("python_ok") != "true":
            return 0.0
        if kv.get("pip_ok") != "true":
            return 0.0
        if kv.get("file_ok") != "true":
            return 0.0
        return 1.0
    except Exception as e:
        logger.error(f"check_os_python_alias error: {e}")
        return 0.0


def check_os_php_line_count(result: str, rules: dict) -> float:
    """
    Verify PHP line count result.
    Shell collector outputs: file_exists=..., content_ok=...
    Expected rules: {"expected_total": "TOTAL=9"}
    """
    try:
        kv = _parse_kv(result)
        if kv.get("file_exists") != "true":
            return 0.0
        if kv.get("content_ok") != "true":
            return 0.0
        return 1.0
    except Exception as e:
        logger.error(f"check_os_php_line_count error: {e}")
        return 0.0


def check_os_text_transform(result: str, rules: dict) -> float:
    """
    Verify text transformation output (e.g., HTML list generation).
    Shell collector outputs: output_ok=..., summary_ok=...
    Expected rules: not used directly, shell does content compare.
    """
    try:
        kv = _parse_kv(result)
        if kv.get("output_ok") != "true":
            return 0.0
        if kv.get("summary_ok") != "true":
            return 0.0
        return 1.0
    except Exception as e:
        logger.error(f"check_os_text_transform error: {e}")
        return 0.0


def check_os_meeting_template(result: str, rules: dict) -> float:
    """
    Verify meeting template creation.
    Shell collector outputs: template_ok=..., status_ok=...
    """
    try:
        kv = _parse_kv(result)
        if kv.get("template_ok") != "true":
            return 0.0
        if kv.get("status_ok") != "true":
            return 0.0
        return 1.0
    except Exception as e:
        logger.error(f"check_os_meeting_template error: {e}")
        return 0.0


# ==============================================================================
# D. System Admin / Service Evaluators
# ==============================================================================

def check_os_bluetooth_service(result: str, rules: dict) -> float:
    """
    Verify bluetooth service state.
    Shell collector outputs: enabled=..., active=..., file_ok=...
    Expected rules: {"enabled": "enabled", "active": "active"}
    """
    try:
        kv = _parse_kv(result)
        if kv.get("enabled") != rules.get("enabled", "enabled"):
            return 0.0
        if kv.get("active") != rules.get("active", "active"):
            return 0.0
        if kv.get("file_ok") != "true":
            return 0.0
        return 1.0
    except Exception as e:
        logger.error(f"check_os_bluetooth_service error: {e}")
        return 0.0


def check_os_install_local_app(result: str, rules: dict) -> float:
    """
    Verify local app installation (binary, launcher, desktop entry, version).
    Shell collector outputs: binary_ok=..., launcher_ok=..., desktop_ok=..., version_ok=...
    """
    try:
        kv = _parse_kv(result)
        if kv.get("binary_ok") != "true":
            return 0.0
        if kv.get("launcher_ok") != "true":
            return 0.0
        if kv.get("desktop_ok") != "true":
            return 0.0
        if kv.get("version_ok") != "true":
            return 0.0
        return 1.0
    except Exception as e:
        logger.error(f"check_os_install_local_app error: {e}")
        return 0.0


def check_os_switch_user(result: str, rules: dict) -> float:
    """
    Verify user session switch result.
    Shell collector outputs: file_exists=..., content_ok=..., owner_ok=...
    """
    try:
        kv = _parse_kv(result)
        if kv.get("file_exists") != "true":
            return 0.0
        if kv.get("content_ok") != "true":
            return 0.0
        if kv.get("owner_ok") != "true":
            return 0.0
        return 1.0
    except Exception as e:
        logger.error(f"check_os_switch_user error: {e}")
        return 0.0


def check_os_sftp_user(result: str, rules: dict) -> float:
    """
    Verify SFTP-only user creation with proper permissions.
    Shell collector outputs: group_ok=..., user_ok=..., home_ok=..., shell_ok=...,
                             home_perm_ok=..., upload_perm_ok=..., optional ssh_conf_ok.
    """
    try:
        kv = _parse_kv(result)
        checks = rules.get("checks", {})
        if checks:
            for key, expected in checks.items():
                if kv.get(key) != expected:
                    return 0.0
            return 1.0
        for key in ["group_ok", "user_ok", "home_ok", "shell_ok",
                    "home_perm_ok", "upload_perm_ok"]:
            if kv.get(key) != "true":
                return 0.0
        return 1.0
    except Exception as e:
        logger.error(f"check_os_sftp_user error: {e}")
        return 0.0


def check_os_extract_services(result: str, rules: dict) -> float:
    """
    Verify extracted failing services list matches expected.
    Shell collector outputs the file content directly.
    Expected rules: {"expected": "auth\\nbilling\\n..."}
    """
    try:
        expected = rules.get("expected", "")
        if result is None:
            return 0.0
        if result.strip() == expected.strip():
            return 1.0
        return 0.0
    except Exception as e:
        logger.error(f"check_os_extract_services error: {e}")
        return 0.0


def check_os_recent_manifest(result: str, rules: dict) -> float:
    """
    Verify recent file manifest CSV matches expected content.
    Shell collector outputs the file content directly.
    Expected rules: {"expected": "path,count\\n..."}
    """
    try:
        expected = rules.get("expected", "")
        if result is None:
            return 0.0
        if result.strip() == expected.strip():
            return 1.0
        return 0.0
    except Exception as e:
        logger.error(f"check_os_recent_manifest error: {e}")
        return 0.0


# ---------------------------------------------------------------------------
# New evaluators – batch 2 (L2/L3 additions)
# ---------------------------------------------------------------------------

def check_os_cron_job(result: str, rules: dict) -> float:
    """
    Verify cron job was created correctly.
    Shell collector outputs: cron_exists=true/false, schedule_ok=true/false,
    command_ok=true/false, output_ok=true/false.
    """
    try:
        kv = _parse_kv(result)
        checks = rules.get("checks", {})
        if not checks:
            for key in ["cron_exists", "schedule_ok", "command_ok", "output_ok"]:
                if kv.get(key) != "true":
                    return 0.0
            return 1.0
        for key, expected in checks.items():
            if kv.get(key) != expected:
                return 0.0
        return 1.0
    except Exception as e:
        logger.error(f"check_os_cron_job error: {e}")
        return 0.0


def check_os_disk_cleanup(result: str, rules: dict) -> float:
    """
    Verify disk cleanup operation: files removed, report generated.
    Shell collector outputs key=value pairs for each check.
    """
    try:
        kv = _parse_kv(result)
        checks = rules.get("checks", {})
        for key, expected in checks.items():
            if kv.get(key) != expected:
                return 0.0
        return 1.0
    except Exception as e:
        logger.error(f"check_os_disk_cleanup error: {e}")
        return 0.0


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


def check_os_hosts_block(result: str, rules: dict) -> float:
    """
    Verify /etc/hosts domain blocking configuration.
    Shell collector outputs: blocked_X=true/false, preserved_ok=true/false,
    backup_ok=true/false, verify_ok=true/false.
    """
    try:
        kv = _parse_kv(result)
        checks = rules.get("checks", {})
        for key, expected in checks.items():
            if kv.get(key) != expected:
                return 0.0
        return 1.0
    except Exception as e:
        logger.error(f"check_os_hosts_block error: {e}")
        return 0.0


def check_os_systemd_timer_basic(result: str, rules: dict) -> float:
    """
    Verify basic systemd timer + service unit creation.
    Shell collector outputs: service_file_ok, timer_file_ok, timer_enabled,
    timer_active, exec_ok.
    """
    try:
        kv = _parse_kv(result)
        checks = rules.get("checks", {})
        if not checks:
            for key in ["service_file_ok", "timer_file_ok", "timer_enabled", "timer_active"]:
                if kv.get(key) != "true":
                    return 0.0
            return 1.0
        for key, expected in checks.items():
            if kv.get(key) != expected:
                return 0.0
        return 1.0
    except Exception as e:
        logger.error(f"check_os_systemd_timer_basic error: {e}")
        return 0.0


def check_os_quota_dirs(result: str, rules: dict) -> float:
    """
    Verify multi-user directory quota/permission setup.
    Shell collector outputs per-user directory checks.
    """
    try:
        kv = _parse_kv(result)
        checks = rules.get("checks", {})
        for key, expected in checks.items():
            if kv.get(key) != expected:
                return 0.0
        return 1.0
    except Exception as e:
        logger.error(f"check_os_quota_dirs error: {e}")
        return 0.0


def check_os_log_rotate_pipeline(result: str, rules: dict) -> float:
    """
    Verify log rotation + compression + archival pipeline.
    Shell collector outputs checks for rotated files, compressed archives,
    cleanup status, and report file.
    """
    try:
        kv = _parse_kv(result)
        checks = rules.get("checks", {})
        for key, expected in checks.items():
            if kv.get(key) != expected:
                return 0.0
        return 1.0
    except Exception as e:
        logger.error(f"check_os_log_rotate_pipeline error: {e}")
        return 0.0


def check_os_systemd_custom_service(result: str, rules: dict) -> float:
    """
    Verify custom systemd service + timer with full lifecycle.
    Checks service file, timer file, enabled/active status, ExecStart,
    timer schedule, and log output.
    """
    try:
        kv = _parse_kv(result)
        checks = rules.get("checks", {})
        for key, expected in checks.items():
            if kv.get(key) != expected:
                return 0.0
        return 1.0
    except Exception as e:
        logger.error(f"check_os_systemd_custom_service error: {e}")
        return 0.0


def check_os_firewall_rules(result: str, rules: dict) -> float:
    """
    Verify UFW/iptables firewall rule configuration.
    Shell collector outputs: fw_active, rule_ssh, rule_http, rule_https,
    deny_default, report_ok.
    """
    try:
        kv = _parse_kv(result)
        checks = rules.get("checks", {})
        for key, expected in checks.items():
            if kv.get(key) != expected:
                return 0.0
        return 1.0
    except Exception as e:
        logger.error(f"check_os_firewall_rules error: {e}")
        return 0.0
