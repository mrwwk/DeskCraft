import copy
import importlib.util
import json
import sys
import re
from typing import Dict


def check_json_keybindings(actual: str, expected: str, **options) -> float:
    """
    Args:
        actual (str): path to result text file
        expected (str): expected dict{}

    Return:
        float: the score
    """

    def direct_load_json(fp):
        try:
            with open(fp, 'r') as f:
                data = json.load(f)
            return data
        except:
            return None

    def skip_first_line_load_json(fp):
        try:
            with open(fp, 'r') as f:
                f.readline()
                data = json.load(f)
            return data
        except:
            return None

    for func in [direct_load_json, skip_first_line_load_json]:
        data = func(actual)
        if data is not None and type(data) == list:
            break
    else:
        return 0.0
    expected = expected['expected']
    if expected in data:
        return 1.0
    else:
        return 0.0


def check_json_settings(actual: str, expected: str, **options) -> float:
    """
    Args:
        actual (str): path to result text file
        expected (dict): expected dict{}, containing key "expect"

    Return:
        float: the score
    """
    if not actual:
        return 0.

    try:
        with open(actual, 'r') as f:
            data = json.load(f)
    except Exception as e:
        return 0.0

    expect = expected['expected']
    
    # Check if all expected key-value pairs are in the actual data
    for key, value in expect.items():
        if key not in data or data[key] != value:
            return 0.0
    
    return 1.0


def compare_text_file(actual: str, expected: str, **options) -> float:
    """
    Args:
        actual (str): path to result text file
        expected (str): path to gold text file

    Return:
        float: the score
    """
    if not actual:
        return 0.

    with open(actual) as f1:
        actual_text = f1.read()
    with open(expected) as f2:
        expected_text = f2.read()

    ignore_blanks = options.get('ignore_blanks', False)
    if ignore_blanks:
        actual_text = re.sub(r'[\t\n]', ' ', actual_text).strip()
        actual_text = re.sub(r'\s+', ' ', actual_text)
        expected_text = re.sub(r'[\t\n]', ' ', expected_text).strip()
        expected_text = re.sub(r'\s+', ' ', expected_text)

    ignore_case = options.get('ignore_case', False)
    if ignore_case:
        actual_text = actual_text.lower()
        expected_text = expected_text.lower()

    if actual_text == expected_text:
        return 1.0
    return 0.0

import zipfile
from difflib import SequenceMatcher
import PyPDF2

def compare_pdf_content(content1, content2, text_similarity_threshold):
    def extract_text_from_pdf(content):
        with open("temp.pdf", "wb") as temp_pdf:
            temp_pdf.write(content)
        with open("temp.pdf", "rb") as temp_pdf:
            pdf_reader = PyPDF2.PdfReader(temp_pdf)
            text = ''
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text()
        return text

    text1 = extract_text_from_pdf(content1)
    text2 = extract_text_from_pdf(content2)

    similarity_ratio = SequenceMatcher(None, text1, text2).ratio()

    return similarity_ratio >= text_similarity_threshold

def compare_zip_files(actual: str, expected: str, **options) -> float:
    """
    Args:
        actual (str): path to result zip file
        expected (str): path to gold zip file

    Return:
        float: the score
    """
    if not actual:
        return 0.

    with zipfile.ZipFile(actual, 'r') as zip_file1, zipfile.ZipFile(expected, 'r') as zip_file2:
        file_list1 = set(zip_file1.namelist())
        file_list2 = set(zip_file2.namelist())

        if file_list1 != file_list2:
            return 0.0
        
        for file_name in file_list1:
            content1 = zip_file1.read(file_name)
            content2 = zip_file2.read(file_name)

            if file_name.lower().endswith('.pdf'):
                if compare_pdf_content(content1, content2, 0.95):
                    continue
                else:
                    return 0.0
            elif content1 != content2:
                return 0.0
    return 1.0


import json
from typing import Any, Dict

def _is_subset(expected: Any, actual: Any) -> bool:
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return False
        for k, v in expected.items():
            if k not in actual:
                return False
            if not _is_subset(v, actual[k]):
                return False
        return True

    if isinstance(expected, list):
        return expected == actual

    return expected == actual


def compare_config(actual: str, rules: Dict, **options) -> float:
    if not actual:
        return 0.0

    expected_text = rules.get("expected")
    if not expected_text:
        return 0.0

    with open(actual, "r", encoding="utf-8") as f:
        actual_text = f.read()

    # English option key (default True => loose/containment semantics)
    containment_ok = options.get("containment_ok", True)

    if containment_ok:
        # Prefer robust JSON subset check
        try:
            actual_json = json.loads(actual_text)
            expected_json = json.loads(expected_text)
            if _is_subset(expected_json, actual_json):
                return 1.0
        except Exception:
            # Fallback: substring containment
            if expected_text.strip() in actual_text:
                return 1.0
        return 0.0

    # Strict legacy behavior
    if actual_text == expected_text:
        return 1.0

    # Optional: JSON equality ignoring formatting (still strict on extra keys)
    try:
        if json.loads(actual_text) == json.loads(expected_text):
            return 1.0
    except Exception:
        pass

    return 0.0



def compare_answer(actual: str, rules: Dict, **options) -> float:
    """
    Args:
        actual (str): result string
        expected (str): gold string

    Return:
        float: the score
    """
    if not actual:
        return 0.

    if actual == rules['expected']:
        return 1.0

    # TODO: can use text embedding to get non-zero return
    return 0.0


def is_extension_installed(actual: str, rules: Dict, **options):
    if rules['type'] == 'contain':
        if rules['expected'] in actual:
            return 1.0
        return 0.0
    elif rules['type'] == 'not_contain':
        if rules['expected'] not in actual:
            return 1.0
        return 0.0
    else:
        raise NotImplementedError


def check_python_file_by_test_suite(actual_files, test_file, **options) -> float:
    """Check the python file by running the test suite in the given test file.
    
    This function is now more robust and handles various error conditions:
    - File existence validation
    - Module loading errors
    - Function execution errors
    - Proper resource cleanup
    - Working directory management
    """
    import os
    import uuid
    import logging
    from pathlib import Path
    
    logger = logging.getLogger(__name__)
    test_function_name = options.get('test_function_name', 'test')
    
    # Validate inputs
    if not test_file:
        logger.error("test_file is None or empty")
        return 0.0
    
    # Convert to absolute path and check existence
    test_file_path = Path(test_file).resolve()
    if not test_file_path.exists():
        logger.error(f"Test file does not exist: {test_file_path}")
        return 0.0
    
    if not test_file_path.is_file():
        logger.error(f"Test file path is not a file: {test_file_path}")
        return 0.0
    
    # Create unique module name to avoid conflicts
    module_name = f'dynamic_test_module_{uuid.uuid4().hex[:8]}'
    
    # Store original working directory and sys.path
    original_cwd = os.getcwd()
    original_sys_path = sys.path.copy()
    
    try:
        # Change to the directory containing the test file
        test_dir = test_file_path.parent
        os.chdir(test_dir)
        logger.debug(f"Changed working directory to: {test_dir}")
        
        # Add test directory to Python path if not already present
        if str(test_dir) not in sys.path:
            sys.path.insert(0, str(test_dir))
            logger.debug(f"Added {test_dir} to sys.path")
        
        # Try to load the module
        try:
            spec = importlib.util.spec_from_file_location(module_name, test_file_path)
            if spec is None:
                logger.error(f"Could not create module spec for {test_file_path}")
                return 0.0
            
            if spec.loader is None:
                logger.error(f"Module spec has no loader for {test_file_path}")
                return 0.0
            
            module = importlib.util.module_from_spec(spec)
            if module is None:
                logger.error(f"Could not create module from spec for {test_file_path}")
                return 0.0
            
            # Add to sys.modules temporarily
            sys.modules[module_name] = module
            
            # Execute the module
            spec.loader.exec_module(module)
            logger.debug(f"Successfully loaded test module: {module_name}")
            
        except SyntaxError as e:
            logger.error(f"Syntax error in test file: {e}")
            return 0.0
        except ImportError as e:
            logger.error(f"Import error loading test file: {e}")
            return 0.0
        except Exception as e:
            logger.error(f"Error loading test module: {e}")
            return 0.0
        
        # Try to get the test function
        try:
            if not hasattr(module, test_function_name):
                logger.error(f"Test function '{test_function_name}' not found in {test_file_path}")
                return 0.0
            
            test_function = getattr(module, test_function_name)
            
            if not callable(test_function):
                logger.error(f"'{test_function_name}' is not callable in {test_file_path}")
                return 0.0
            
            logger.debug(f"Found test function: {test_function_name}")
            
        except Exception as e:
            logger.error(f"Error getting test function: {e}")
            return 0.0
        
        # Execute the test function
        try:
            result = test_function()
            logger.debug(f"Test function returned: {result} (type: {type(result)})")
            
            # Handle different return types
            if isinstance(result, bool):
                return 1.0 if result else 0.0
            elif isinstance(result, (int, float)):
                # Normalize to 0.0-1.0 range
                normalized = max(0.0, min(1.0, float(result)))
                if normalized != result:
                    logger.warning(f"Test result {result} normalized to {normalized}")
                return normalized
            else:
                # For any other type, treat as True if truthy
                bool_result = bool(result)
                logger.warning(f"Test returned non-boolean/numeric value {result}, treating as {bool_result}")
                return 1.0 if bool_result else 0.0
                
        except Exception as e:
            logger.error(f"Error executing test function: {e}")
            return 0.0
    
    except Exception as e:
        logger.error(f"Unexpected error in check_python_file_by_test_suite: {e}")
        return 0.0
    
    finally:
        # Cleanup: remove the module from sys.modules
        if module_name in sys.modules:
            del sys.modules[module_name]
            logger.debug(f"Cleaned up module: {module_name}")
        
        # Restore original working directory
        try:
            os.chdir(original_cwd)
            logger.debug(f"Restored working directory to: {original_cwd}")
        except Exception as e:
            logger.warning(f"Could not restore working directory: {e}")
        
        # Restore original sys.path
        sys.path[:] = original_sys_path
        logger.debug("Restored sys.path")


def check_python_file_by_gold_file(actual_files, gold_file: str, **options) -> float:
    pass


def check_html_background_image(src_path: str, rule: Dict = None) -> float:
    """
    Check if the background image is correctly set.
    multi-app:bb7db4c2-30b5-4be7-8dd7-b8c4ec7d3108
    """
    if not src_path:
        return 0.0

    from bs4 import BeautifulSoup
    with open(src_path, 'r') as f:
        html_content = f.read()
    soup = BeautifulSoup(html_content, 'html.parser')
    styles = soup.find_all('style')
    for style in styles:
        if f'background-image: url(\'{rule["value"]}\')' in style.text:
            return 1.0
    return 0.0


def compare_result_files(src_path, tgt_path):
    """
    Compare whether the content of two files are the same.
    multi-app:7f35355e-02a6-45b5-b140-f0be698bcf85
    """
    if not src_path or not tgt_path:
        return 0.0

    with open(src_path, 'r') as f:
        src_content = f.read().strip()
    with open(tgt_path, 'r') as f:
        tgt_content = f.read().strip()
    try:
        # Compare the content as numbers
        tgt_content_num = float(tgt_content)
        if tgt_content in src_content:
            # If the content of tgt is in src, return 1.0 since output src might be
            # a superset(language description+number) of tgt
            return 1.0
        src_content_num = float(src_content)
        if abs(src_content_num - tgt_content_num) < 1e-4:
            return 1.0
        return 0.0
    except:
        if src_content == tgt_content:
            return 1.0
    return 0.0


## generative ui

def _normalize_ui_bundle_path(path: str) -> str:
    return path.lstrip("./").replace("\\", "/")


def _load_ui_bundle_entries(actual: str):
    with zipfile.ZipFile(actual, "r") as zf:
        raw_names = set(zf.namelist())
        normalized_to_raw = {_normalize_ui_bundle_path(name): name for name in raw_names}
        file_sizes = {
            normalized_name: zf.getinfo(raw_name).file_size
            for normalized_name, raw_name in normalized_to_raw.items()
        }
        text_contents = {}
        for normalized_name, raw_name in normalized_to_raw.items():
            if normalized_name.lower().endswith((".html", ".css", ".js", ".json", ".md", ".txt", ".svg")):
                text_contents[normalized_name] = zf.read(raw_name).decode("utf-8", errors="ignore")
        return normalized_to_raw, file_sizes, text_contents


def _get_ui_bundle_html_soup(text_contents: Dict[str, str], file_name: str):
    from bs4 import BeautifulSoup

    normalized_name = _normalize_ui_bundle_path(file_name)
    html_text = text_contents.get(normalized_name)
    if html_text is None:
        return None
    return BeautifulSoup(html_text, "html.parser")


def check_ui_bundle_required_files(actual: str, rules: Dict, **options) -> float:
    if not actual:
        return 0.0

    required_files = rules.get("required_files", [])
    if not required_files:
        return 1.0

    try:
        normalized_to_raw, _, _ = _load_ui_bundle_entries(actual)
        for req in required_files:
            if _normalize_ui_bundle_path(req) not in normalized_to_raw:
                return 0.0
    except Exception:
        return 0.0

    return 1.0


def check_ui_bundle_min_file_sizes(actual: str, rules: Dict, **options) -> float:
    if not actual:
        return 0.0

    min_file_size_bytes = rules.get("min_file_size_bytes", {})
    if not min_file_size_bytes:
        return 1.0

    try:
        normalized_to_raw, file_sizes, _ = _load_ui_bundle_entries(actual)
        for file_name, min_size in min_file_size_bytes.items():
            normalized_name = _normalize_ui_bundle_path(file_name)
            if normalized_name not in normalized_to_raw:
                return 0.0
            if file_sizes.get(normalized_name, 0) < int(min_size):
                return 0.0
    except Exception:
        return 0.0

    return 1.0


def check_ui_bundle_required_keywords(actual: str, rules: Dict, **options) -> float:
    if not actual:
        return 0.0

    required_file_keywords = rules.get("required_file_keywords", {})
    if not required_file_keywords:
        return 1.0

    try:
        normalized_to_raw, _, text_contents = _load_ui_bundle_entries(actual)
        for file_name, keywords in required_file_keywords.items():
            normalized_name = _normalize_ui_bundle_path(file_name)
            if normalized_name not in normalized_to_raw:
                return 0.0
            content_lower = text_contents.get(normalized_name, "").lower()
            for keyword in keywords:
                if str(keyword).lower() not in content_lower:
                    return 0.0
    except Exception:
        return 0.0

    return 1.0


def check_ui_bundle_manifest_subset(actual: str, rules: Dict, **options) -> float:
    if not actual:
        return 0.0

    expected_manifest = rules.get("expected_manifest")
    if expected_manifest is None:
        return 1.0

    try:
        normalized_to_raw, _, text_contents = _load_ui_bundle_entries(actual)
        manifest_name = _normalize_ui_bundle_path("manifest.json")
        if manifest_name not in normalized_to_raw:
            return 0.0
        manifest_obj = json.loads(text_contents.get(manifest_name, ""))
        if not _is_subset(expected_manifest, manifest_obj):
            return 0.0
    except Exception:
        return 0.0

    return 1.0


def check_ui_bundle_html_checks(actual: str, rules: Dict, **options) -> float:
    if not actual:
        return 0.0

    html_checks = rules.get("html_checks", {})
    if not html_checks:
        return 1.0

    try:
        normalized_to_raw, _, text_contents = _load_ui_bundle_entries(actual)
        for file_name, checks in html_checks.items():
            normalized_name = _normalize_ui_bundle_path(file_name)
            if normalized_name not in normalized_to_raw:
                return 0.0
            soup = _get_ui_bundle_html_soup(text_contents, normalized_name)
            if soup is None:
                return 0.0

            for check in checks:
                check_type = check.get("type")
                if check_type == "selector_exists":
                    selector = check.get("selector")
                    if not selector or soup.select_one(selector) is None:
                        return 0.0
                elif check_type == "selector_count":
                    selector = check.get("selector")
                    expected_count = check.get("count")
                    if selector is None or expected_count is None:
                        return 0.0
                    if len(soup.select(selector)) != int(expected_count):
                        return 0.0
                elif check_type == "selector_text_contains":
                    selector = check.get("selector")
                    expected_text = check.get("text", "")
                    if not selector:
                        return 0.0
                    node = soup.select_one(selector)
                    if node is None or expected_text.lower() not in node.get_text(" ", strip=True).lower():
                        return 0.0
                elif check_type == "selector_attribute_equals":
                    selector = check.get("selector")
                    attribute = check.get("attribute")
                    expected_value = check.get("value")
                    if not selector or not attribute or expected_value is None:
                        return 0.0
                    node = soup.select_one(selector)
                    if node is None or node.get(attribute) != expected_value:
                        return 0.0
                elif check_type == "text_present":
                    expected_text = check.get("text", "")
                    if expected_text.lower() not in soup.get_text(" ", strip=True).lower():
                        return 0.0
                else:
                    return 0.0
    except Exception:
        return 0.0

    return 1.0


def check_ui_bundle_no_remote_image_urls(actual: str, rules: Dict, **options) -> float:
    if not actual:
        return 0.0

    if not rules.get("forbid_remote_image_urls", False):
        return 1.0

    image_extensions = tuple(rules.get("image_extensions", [".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"]))

    try:
        _, _, text_contents = _load_ui_bundle_entries(actual)
        for normalized_name, content in text_contents.items():
            if not normalized_name.lower().endswith((".html", ".css", ".js")):
                continue
            content_lower = content.lower()
            if "http://" in content_lower or "https://" in content_lower:
                for ext in image_extensions:
                    if f"http://" in content_lower and ext in content_lower:
                        return 0.0
                    if f"https://" in content_lower and ext in content_lower:
                        return 0.0
    except Exception:
        return 0.0

    return 1.0

def check_generative_ui_bundle(actual: str, rules: Dict, **options) -> float:
    """
    Validate a generated UI project packed as a zip archive.

    Expected rule format:
    {
      "required_files": ["index.html", ...],
      "min_file_size_bytes": {"assets/hero.jpg": 1000, ...},
      "required_file_keywords": {
        "index.html": ["<canvas", "app.js"],
        ...
      },
      "expected_manifest": {...},
      "forbid_remote_image_urls": true,
      "image_extensions": [".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"]
    }
    """
    if not actual or not isinstance(rules, dict):
        return 0.0

    checks = [
        check_ui_bundle_required_files,
        check_ui_bundle_min_file_sizes,
        check_ui_bundle_required_keywords,
        check_ui_bundle_manifest_subset,
        check_ui_bundle_html_checks,
        check_ui_bundle_no_remote_image_urls,
    ]
    for check in checks:
        if check(actual, rules, **options) == 0.0:
            return 0.0
    return 1.0
