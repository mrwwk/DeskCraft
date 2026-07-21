"""
Evaluator for interactive_vscode_requirement_change_107:
Check that release_runbook.md content matches the expected final version,
with trailing-whitespace normalization to avoid platform-dependent newline mismatches.
"""

import os


def check_release_runbook_content(result_path, expected_rules, **options) -> float:
    """Compare the saved release_runbook.md against the expected final content.

    result_path: local path to the file pulled from VM via vm_file getter.
    expected_rules: dict with key "expected" containing the canonical text.
    Returns 1.0 on match, 0.0 otherwise.
    """
    if result_path is None:
        return 0.0

    if not os.path.isfile(result_path):
        return 0.0

    try:
        with open(result_path, "r", encoding="utf-8") as f:
            actual = f.read()
    except (IOError, OSError):
        return 0.0

    expected = expected_rules.get("expected", "")

    # Normalize: replace Windows-style line endings, then strip all trailing
    # whitespace (newlines, spaces, carriage returns).  This avoids false
    # negatives caused by platform- or editor-dependent trailing newline behaviour.
    actual_norm = actual.replace("\r\n", "\n").rstrip()
    expected_norm = expected.replace("\r\n", "\n").rstrip()

    if actual_norm == expected_norm:
        return 1.0
    else:
        return 0.0
