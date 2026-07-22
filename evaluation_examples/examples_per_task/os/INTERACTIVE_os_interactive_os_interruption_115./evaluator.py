"""
Evaluator for interactive_os_interruption_115:
Check that press_pick/manifest.txt has correct format, content, and ordering.

The manifest.txt is the final deliverable of this task. It must:
- Exist and be readable
- Contain exactly 2 entries (event/a.jpg, event/stage/speaker.jpg)
- Each line: <sha256>  <relative_path> (two spaces between)
- Entries sorted by relative path ascending
- No paths containing forbidden patterns (private, _raw)
- sha256 hashes match the original source files
"""

import logging
import os

logger = logging.getLogger("desktopenv.metric.custom")


def check_manifest(manifest_path, expected=None, **options):
    """
    Verify press_pick/manifest.txt is correctly generated.

    Args:
        manifest_path: Local path to manifest.txt pulled from VM via vm_file,
                       or None if the file does not exist in the VM.
        expected: Dict with:
            - expected_entries: list of [sha256, rel_path] pairs
            - forbidden_patterns: list of path substrings that must not appear
        **options: Additional options (reserved for framework compatibility).

    Returns:
        float: 1.0 if manifest matches all requirements, 0.0 otherwise.
    """
    if manifest_path is None:
        logger.warning("manifest.txt not found in press_pick (vm_file returned None)")
        return 0.0

    if not os.path.isfile(manifest_path):
        logger.warning(f"manifest.txt path is not a regular file: {manifest_path}")
        return 0.0

    # Read manifest content
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            content = f.read()
    except (IOError, OSError) as e:
        logger.error(f"Failed to read manifest.txt: {e}")
        return 0.0

    if expected is None:
        expected = {}

    expected_entries = expected.get("expected_entries", [])
    forbidden_patterns = expected.get("forbidden_patterns", [])

    # Split into non-empty lines, preserve exact content for comparison
    lines = [l for l in content.split("\n") if l.strip()]

    if len(lines) != len(expected_entries):
        logger.warning(
            f"Entry count mismatch: expected {len(expected_entries)}, got {len(lines)}"
        )
        return 0.0

    parsed_entries = []
    for i, line in enumerate(lines):
        # Each line must have exactly "  " (two spaces) separating sha256 and path
        if "  " not in line:
            logger.warning(
                f"Line {i + 1}: missing double-space separator: {repr(line)}"
            )
            return 0.0

        parts = line.split("  ", 1)
        file_hash = parts[0].strip()
        rel_path = parts[1].strip()

        # sha256 is 64 hex characters
        if len(file_hash) != 64 or not all(c in "0123456789abcdef" for c in file_hash):
            logger.warning(
                f"Line {i + 1}: invalid sha256 hash: {repr(file_hash)}"
            )
            return 0.0

        # Check forbidden patterns in the relative path
        for pattern in forbidden_patterns:
            if pattern in rel_path:
                logger.warning(
                    f"Line {i + 1}: forbidden pattern '{pattern}' found in path: {rel_path}"
                )
                return 0.0

        parsed_entries.append((file_hash, rel_path))

    # Verify entries are sorted by relative path (ascending)
    for i in range(1, len(parsed_entries)):
        if parsed_entries[i][1] <= parsed_entries[i - 1][1]:
            logger.warning(
                f"Entries not sorted by path: "
                f"'{parsed_entries[i - 1][1]}' before '{parsed_entries[i][1]}'"
            )
            return 0.0

    # Compare expected vs actual entries (order-independent after sorting verified)
    expected_set = set(tuple(e) for e in expected_entries)
    actual_set = set(parsed_entries)

    if expected_set != actual_set:
        only_expected = expected_set - actual_set
        only_actual = actual_set - expected_set
        if only_expected:
            logger.warning(f"Missing expected entries: {sorted(only_expected)}")
        if only_actual:
            logger.warning(f"Unexpected entries in manifest: {sorted(only_actual)}")
        return 0.0

    logger.info("manifest.txt validation passed")
    return 1.0


def check_include_exclude(result: str, rules: dict) -> float:
    if result is None:
        return 0.0
    include = rules.get('include', [])
    exclude = rules.get('exclude', [])
    return 1.0 if all(token in result for token in include) and all(token not in result for token in exclude) else 0.0
