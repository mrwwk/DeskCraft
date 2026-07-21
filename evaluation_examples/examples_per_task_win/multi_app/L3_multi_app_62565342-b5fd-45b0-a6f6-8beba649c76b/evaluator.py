"""
Evaluator for cli_tool_bugfix_from_issue_tests_and_docs (L3_multi_app).
Self-contained evaluator with no relative imports — safe for replay.py standalone loading.

Metrics:
  0. check_python_file_by_test_suite  – run test.py against repaired source files
  1. is_expected_active_tab_approximate – verify Chrome is on the f-string docs page
  2. check_include_exclude              – verify FIX_SUMMARY.txt contains "issue=CLI-204"
"""

import importlib.util
import logging
import os
import sys
import uuid
from pathlib import Path
from urllib.parse import urlparse, urlunparse

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Metric 0: check_python_file_by_test_suite
# ---------------------------------------------------------------------------

def check_python_file_by_test_suite(actual_files, test_file, **options) -> float:
    """Run the test suite in *test_file* against the repaired source files.

    *actual_files* (list[str] or str) is validated for existence / syntax
    before the test is executed.  The test is loaded from *test_file* and its
    ``test()`` function is called (override with *test_function_name* option).

    Returns 1.0 when the test passes, 0.0 otherwise.
    """
    test_function_name = options.get("test_function_name", "test")

    # -- validate test_file --------------------------------------------------
    if not test_file:
        logger.error("test_file is None or empty")
        return 0.0

    test_file_path = Path(test_file).resolve()
    if not test_file_path.exists():
        logger.error(f"Test file does not exist: {test_file_path}")
        return 0.0
    if not test_file_path.is_file():
        logger.error(f"Test file path is not a file: {test_file_path}")
        return 0.0

    # -- validate actual_files (if provided) ---------------------------------
    if actual_files:
        _files = actual_files if isinstance(actual_files, (list, tuple)) else [actual_files]
        for f in _files:
            fp = Path(f) if os.path.isabs(f) else Path(f).resolve()
            if not fp.exists():
                logger.warning("Actual source file missing: %s", fp)
            elif not fp.is_file():
                logger.warning("Actual source path is not a file: %s", fp)
            else:
                # Quick syntax check
                try:
                    with open(fp, "r", encoding="utf-8") as fh:
                        compile(fh.read(), str(fp), "exec")
                except SyntaxError as e:
                    logger.warning("Syntax error in actual file %s: %s", fp, e)

    # -- load and execute test module ----------------------------------------
    module_name = f"dynamic_test_module_{uuid.uuid4().hex[:8]}"

    original_cwd = os.getcwd()
    original_sys_path = sys.path.copy()

    try:
        test_dir = str(test_file_path.parent)
        os.chdir(test_dir)
        if test_dir not in sys.path:
            sys.path.insert(0, test_dir)

        # Load module
        try:
            spec = importlib.util.spec_from_file_location(module_name, test_file_path)
            if spec is None or spec.loader is None:
                logger.error("Could not create module spec for %s", test_file_path)
                return 0.0
            module = importlib.util.module_from_spec(spec)
            if module is None:
                logger.error("Could not create module from spec for %s", test_file_path)
                return 0.0
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
        except SyntaxError as e:
            logger.error("Syntax error in test file: %s", e)
            return 0.0
        except ImportError as e:
            logger.error("Import error loading test file: %s", e)
            return 0.0
        except Exception as e:
            logger.error("Error loading test module: %s", e)
            return 0.0

        # Get test function
        if not hasattr(module, test_function_name):
            logger.error("Test function '%s' not found in %s", test_function_name, test_file_path)
            return 0.0
        test_function = getattr(module, test_function_name)
        if not callable(test_function):
            logger.error("'%s' is not callable in %s", test_function_name, test_file_path)
            return 0.0

        # Execute
        result = test_function()
        if isinstance(result, bool):
            return 1.0 if result else 0.0
        if isinstance(result, (int, float)):
            return max(0.0, min(1.0, float(result)))
        return 1.0 if result else 0.0

    except Exception as e:
        logger.error("Unexpected error in check_python_file_by_test_suite: %s", e)
        return 0.0
    finally:
        if module_name in sys.modules:
            del sys.modules[module_name]
        try:
            os.chdir(original_cwd)
        except Exception:
            pass
        sys.path[:] = original_sys_path


# ---------------------------------------------------------------------------
# Metric 1: is_expected_active_tab_approximate
# ---------------------------------------------------------------------------

def is_expected_active_tab_approximate(actual, expected, **options) -> float:
    """Check whether the active Chrome tab URL matches *expected* URL.

    *actual* is the dict returned by the ``active_tab_info`` getter (must
    contain key ``"url"``), or a plain URL string.

    *expected* is the rules dict from ``rule`` getter, containing key ``"url"``.

    Query-string and fragment are stripped from both URLs before comparison,
    so minor URL variations (tracking params, anchors) are tolerated.
    """

    def _strip_query(url: str) -> str:
        parsed = urlparse(url)
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))

    if not actual:
        return 0.0

    # Normalise actual to a string URL
    if isinstance(actual, dict):
        actual_url = actual.get("url", "")
    else:
        actual_url = str(actual)

    expected_url = ""
    if isinstance(expected, dict):
        expected_url = expected.get("url", "")

    if not actual_url or not expected_url:
        return 0.0

    if _strip_query(actual_url) == _strip_query(expected_url):
        return 1.0
    return 0.0


# ---------------------------------------------------------------------------
# Metric 2: check_include_exclude
# ---------------------------------------------------------------------------

def check_include_exclude(actual, rules, **options) -> float:
    """Check that every string in *rules["include"]* appears in *actual*,
    and none of the strings in *rules["exclude"]* appear in *actual*.

    *actual* is the string output from ``vm_command_line`` (e.g. content of
    FIX_SUMMARY.txt).

    *rules* comes from a ``rule`` getter and must contain ``"include"`` (list)
    and ``"exclude"`` (list).
    """
    if not actual:
        return 0.0

    include = rules.get("include", []) if isinstance(rules, dict) else []
    exclude = rules.get("exclude", []) if isinstance(rules, dict) else []

    for s in include:
        if s not in actual:
            return 0.0

    for s in exclude:
        if s in actual:
            return 0.0

    return 1.0
