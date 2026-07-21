"""
Evaluator for project_audit_from_spec_and_reference_docs task.

Combines three checks into a single function so that all sub-checks are
always evaluated and saved as one metric, avoiding the short-circuit
artifact-loss issue with conj="and" multi-metric evaluators.
"""
import json
from urllib.parse import urlparse, urlunparse


def check_project_audit(result: str, expected: dict, **options) -> float:
    """Check all three sub-tasks of the project audit task.

    Args:
        result: JSON string with keys:
            - summary: content of ~/Desktop/audit_summary.txt
            - vscode: parsed settings.json dict
            - chrome_url: active Chrome tab URL
        expected: dict with keys:
            - audit_summary: {"py_files": "...", "total_lines": "..."}
            - vscode_settings: {"editor.tabSize": N, "editor.rulers": [...]}
            - chrome_url: expected URL string

    Returns:
        1.0 if all three checks pass, 0.0 otherwise.
    """
    if not result or not result.strip():
        return 0.0

    try:
        data = json.loads(result)
    except (json.JSONDecodeError, TypeError):
        return 0.0

    # ── Check 1: audit_summary.txt ──────────────────────────────────
    expected_summary = expected.get("audit_summary", {})
    expected_py_files = str(expected_summary.get("py_files", ""))
    expected_total_lines = str(expected_summary.get("total_lines", ""))

    summary = data.get("summary", "")
    summary_dict = {}
    for line in summary.strip().split("\n"):
        line = line.strip()
        if "=" in line:
            k, v = line.split("=", 1)
            summary_dict[k.strip()] = v.strip()

    if summary_dict.get("py_files") != expected_py_files:
        return 0.0
    if summary_dict.get("total_lines") != expected_total_lines:
        return 0.0

    # ── Check 2: VS Code settings.json ──────────────────────────────
    vscode = data.get("vscode", {})
    expected_vscode = expected.get("vscode_settings", {})
    for key, expected_val in expected_vscode.items():
        if vscode.get(key) != expected_val:
            return 0.0

    # ── Check 3: Chrome active tab URL ──────────────────────────────
    # Approximate match: ignore query parameters (same semantics as
    # the original is_expected_active_tab_approximate).
    chrome_url = data.get("chrome_url", "")
    expected_url = expected.get("chrome_url", "")

    def _strip_query(url: str) -> str:
        parsed = urlparse(url)
        return urlunparse(parsed._replace(query=""))

    if _strip_query(chrome_url) != _strip_query(expected_url):
        return 0.0

    return 1.0
