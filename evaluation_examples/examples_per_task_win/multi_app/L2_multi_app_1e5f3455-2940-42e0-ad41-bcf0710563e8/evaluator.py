"""
Evaluator for json_merge_bugfix_with_dict_docs task (task_id: 1e5f3455).

Three metrics:
  0. check_python_file_by_test_suite – run test suite against agent-modified code
  1. is_expected_active_tab_approximate – verify Chrome has the expected docs page open
  2. check_include_exclude – verify MERGE_FIXED.txt contains required content
"""
import importlib.util
import logging
import os
import shutil
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse, urlunparse

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Metric 0: check_python_file_by_test_suite
# ---------------------------------------------------------------------------

def check_python_file_by_test_suite(actual_files, test_file, **options) -> float:
    """Check agent-modified Python files by running the test suite.

    Copies the agent's actual files and the test file into a temporary
    directory, then loads and executes the test function.  If merge.py is
    missing from the captured artifacts but utils.py is present, a minimal
    merge.py is synthesized so the test can still run.

    Args:
        actual_files: Path (str), list of paths, or dict (artifact reference)
                      to the agent's modified source files.
        test_file: Path to the test suite Python file.
        **options: ``test_function_name`` (default ``'test'``).

    Returns:
        float: 1.0 if the test passes, 0.0 otherwise.
    """
    test_function_name = options.get('test_function_name', 'test')

    # ── validate test_file ──────────────────────────────────────────
    if not test_file:
        logger.error("test_file is None or empty")
        return 0.0

    test_file_path = Path(test_file).resolve()
    if not test_file_path.exists() or not test_file_path.is_file():
        logger.error("Test file does not exist: %s", test_file_path)
        return 0.0

    # ── normalise actual_files → list of Path ───────────────────────
    file_paths: List[Path] = []
    if actual_files is not None:
        if isinstance(actual_files, str):
            file_paths = [Path(actual_files)]
        elif isinstance(actual_files, list):
            file_paths = [Path(f) for f in actual_files if isinstance(f, str)]
        elif isinstance(actual_files, dict):
            # artifact-deserialised single file: {"__type__": "file", "saved_as": "files/…", …}
            saved_as = actual_files.get('saved_as', '')
            if saved_as:
                file_paths = [Path(saved_as)]

    # ── build temp workspace ────────────────────────────────────────
    temp_dir = Path(tempfile.mkdtemp(prefix='eval_merge_'))
    original_cwd = os.getcwd()
    original_sys_path = sys.path.copy()
    module_name = ''

    try:
        # copy test file
        dest_test = temp_dir / test_file_path.name
        shutil.copy2(test_file_path, dest_test)

        # copy agent files
        copied: set = set()
        for fp in file_paths:
            if fp.exists() and fp.is_file():
                shutil.copy2(fp, temp_dir / fp.name)
                copied.add(fp.name)
            else:
                # try beside the test file (replay scenario)
                alt = test_file_path.parent / fp.name
                if alt.exists() and alt.is_file():
                    shutil.copy2(alt, temp_dir / fp.name)
                    copied.add(fp.name)

        # ── synthesise merge.py if missing but utils.py present ──
        if 'merge.py' not in copied and 'utils.py' in copied:
            merge_src = (
                "from utils import merge_user_defaults\n"
                "\n"
                "def build_profile(user):\n"
                "    defaults = {'theme': 'light', 'language': 'en', 'timezone': 'UTC'}\n"
                "    return merge_user_defaults(defaults, user)\n"
            )
            (temp_dir / 'merge.py').write_text(merge_src)
            copied.add('merge.py')
            logger.debug("Synthesised merge.py from utils.py")

        # also try copying merge.py from the test file's neighbourhood
        if 'merge.py' not in copied:
            neighbour = test_file_path.parent / 'merge.py'
            if neighbour.exists():
                shutil.copy2(neighbour, temp_dir / 'merge.py')
                copied.add('merge.py')

        # ── run the test ─────────────────────────────────────────
        os.chdir(str(temp_dir))
        if str(temp_dir) not in sys.path:
            sys.path.insert(0, str(temp_dir))

        module_name = f'dynamic_test_{uuid.uuid4().hex[:8]}'
        spec = importlib.util.spec_from_file_location(module_name, str(dest_test))
        if spec is None or spec.loader is None:
            logger.error("Could not create module spec for %s", dest_test)
            return 0.0

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module

        try:
            spec.loader.exec_module(module)
        except SyntaxError as e:
            logger.error("Syntax error in test file: %s", e)
            return 0.0
        except ImportError as e:
            logger.error("Import error loading test module: %s", e)
            return 0.0
        except Exception as e:
            logger.error("Error loading test module: %s", e)
            return 0.0

        if not hasattr(module, test_function_name):
            logger.error("Test function '%s' not found in %s", test_function_name, dest_test)
            return 0.0

        test_fn = getattr(module, test_function_name)
        if not callable(test_fn):
            logger.error("'%s' is not callable", test_function_name)
            return 0.0

        try:
            result = test_fn()
        except AssertionError:
            # test assertion failed → the code fix is incorrect
            return 0.0
        except Exception as e:
            logger.error("Error executing test function: %s", e)
            return 0.0

        # Test completed without raising → treat as pass.
        # If it returns an explicit bool/int/float, honour it.
        if result is None:
            return 1.0
        if isinstance(result, bool):
            return 1.0 if result else 0.0
        elif isinstance(result, (int, float)):
            return max(0.0, min(1.0, float(result)))
        else:
            return 1.0 if result else 0.0

    finally:
        if module_name and module_name in sys.modules:
            del sys.modules[module_name]
        try:
            os.chdir(original_cwd)
        except Exception:
            pass
        sys.path[:] = original_sys_path
        shutil.rmtree(temp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Metric 1: is_expected_active_tab_approximate  (inlined from chrome.py)
# ---------------------------------------------------------------------------

def is_expected_active_tab_approximate(active_tab_info, rule) -> float:
    """Check whether the expected URL is the active Chrome tab (ignore query string).

    Args:
        active_tab_info: Dict with ``url`` key or a plain URL string.
        rule: Dict with ``type`` (currently only ``"url"``) and ``url``.

    Returns:
        float: 1.0 if the active tab URL matches (ignoring query params), else 0.0.
    """
    if not active_tab_info:
        return 0.0

    match_type = rule.get('type', '')
    if match_type != 'url':
        logger.error("Unknown match type: %s", match_type)
        return 0.0

    expected_url = rule['url']
    if isinstance(active_tab_info, dict):
        actual_url = active_tab_info.get('url', '')
    else:
        actual_url = str(active_tab_info)

    def _strip_query(url: str) -> str:
        parsed = urlparse(url)
        return urlunparse(parsed._replace(query=""))

    if _strip_query(expected_url) == _strip_query(actual_url):
        return 1.0
    return 0.0


# ---------------------------------------------------------------------------
# Metric 2: check_include_exclude  (inlined from general.py)
# ---------------------------------------------------------------------------

def check_include_exclude(result, rules) -> float:
    """Check that *result* contains every string in *include* and none from *exclude*.

    Args:
        result: The text to check (e.g. content of MERGE_FIXED.txt).
        rules: Dict with ``include`` (list of required substrings) and
               ``exclude`` (list of forbidden substrings).

    Returns:
        float: 1.0 if all include strings are present and no exclude strings
               are present; 0.0 otherwise.
    """
    if result is None:
        return 0.0

    include = rules.get('include', [])
    exclude = rules.get('exclude', [])

    if all(s in result for s in include) and all(s not in result for s in exclude):
        return 1.0
    return 0.0
