import json
import re
import zipfile
from typing import Any, Dict


def _is_subset(expected: Any, actual: Any) -> bool:
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return False
        for key, value in expected.items():
            if key not in actual:
                return False
            if not _is_subset(value, actual[key]):
                return False
        return True

    if isinstance(expected, list):
        return expected == actual

    return expected == actual


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


def _get_node_document_index(soup, node) -> int:
    for index, descendant in enumerate(soup.descendants):
        if descendant is node:
            return index
    return -1


def _extract_css_blocks(css_text: str, selector: str):
    pattern = re.compile(rf"{re.escape(selector)}\s*\{{(.*?)\}}", re.IGNORECASE | re.DOTALL)
    return pattern.findall(css_text)


def _normalize_compact_text(value: str) -> str:
    return re.sub(r"\s+", "", value.lower())


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


def check_ui_bundle_required_patterns(actual: str, rules: Dict, **options) -> float:
    if not actual:
        return 0.0

    required_file_patterns = rules.get("required_file_patterns", {})
    if not required_file_patterns:
        return 1.0

    try:
        normalized_to_raw, _, text_contents = _load_ui_bundle_entries(actual)
        for file_name, patterns in required_file_patterns.items():
            normalized_name = _normalize_ui_bundle_path(file_name)
            if normalized_name not in normalized_to_raw:
                return 0.0
            content = text_contents.get(normalized_name, "")
            for pattern in patterns:
                if re.search(str(pattern), content, re.IGNORECASE | re.DOTALL) is None:
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


def check_ui_bundle_section_order(actual: str, rules: Dict, **options) -> float:
    if not actual:
        return 0.0

    section_order = rules.get("section_order", {})
    if not section_order:
        return 1.0

    try:
        normalized_to_raw, _, text_contents = _load_ui_bundle_entries(actual)
        for file_name, ordered_selectors in section_order.items():
            normalized_name = _normalize_ui_bundle_path(file_name)
            if normalized_name not in normalized_to_raw:
                return 0.0
            soup = _get_ui_bundle_html_soup(text_contents, normalized_name)
            if soup is None:
                return 0.0

            last_index = -1
            for selector in ordered_selectors:
                node = soup.select_one(selector)
                if node is None:
                    return 0.0
                current_index = _get_node_document_index(soup, node)
                if current_index <= last_index:
                    return 0.0
                last_index = current_index
    except Exception:
        return 0.0

    return 1.0


def check_ui_bundle_css_declarations(actual: str, rules: Dict, **options) -> float:
    if not actual:
        return 0.0

    css_declarations = rules.get("css_declarations", {})
    if not css_declarations:
        return 1.0

    try:
        normalized_to_raw, _, text_contents = _load_ui_bundle_entries(actual)
        for file_name, selector_rules in css_declarations.items():
            normalized_name = _normalize_ui_bundle_path(file_name)
            if normalized_name not in normalized_to_raw:
                return 0.0
            css_text = text_contents.get(normalized_name, "")
            for selector_rule in selector_rules:
                selector = selector_rule.get("selector")
                properties = selector_rule.get("properties", {})
                if not selector or not isinstance(properties, dict):
                    return 0.0
                blocks = _extract_css_blocks(css_text, selector)
                if not blocks:
                    return 0.0

                matched_block = False
                for block in blocks:
                    normalized_block = _normalize_compact_text(block)
                    matched_block = True
                    for prop_name, prop_value in properties.items():
                        normalized_prop = _normalize_compact_text(str(prop_name))
                        if normalized_prop not in normalized_block:
                            matched_block = False
                            break
                        if prop_value is not None:
                            expected_pair = _normalize_compact_text(f"{prop_name}:{prop_value}")
                            if expected_pair not in normalized_block:
                                matched_block = False
                                break
                    if matched_block:
                        break

                if not matched_block:
                    return 0.0
    except Exception:
        return 0.0

    return 1.0


def check_ui_bundle_local_asset_links(actual: str, rules: Dict, **options) -> float:
    if not actual:
        return 0.0

    local_asset_links = rules.get("local_asset_links", {})
    if not local_asset_links:
        return 1.0

    try:
        normalized_to_raw, _, text_contents = _load_ui_bundle_entries(actual)
        for file_name, asset_paths in local_asset_links.items():
            normalized_name = _normalize_ui_bundle_path(file_name)
            if normalized_name not in normalized_to_raw:
                return 0.0
            content = text_contents.get(normalized_name, "")
            for asset_path in asset_paths:
                normalized_asset_path = _normalize_ui_bundle_path(asset_path)
                if normalized_asset_path not in normalized_to_raw:
                    return 0.0
                if asset_path not in content:
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
                    if "http://" in content_lower and ext in content_lower:
                        return 0.0
                    if "https://" in content_lower and ext in content_lower:
                        return 0.0
    except Exception:
        return 0.0

    return 1.0


def check_generative_ui_bundle(actual: str, rules: Dict, **options) -> float:
    if not actual or not isinstance(rules, dict):
        return 0.0

    checks = [
        check_ui_bundle_required_files,
        check_ui_bundle_min_file_sizes,
        check_ui_bundle_required_keywords,
        check_ui_bundle_required_patterns,
        check_ui_bundle_manifest_subset,
        check_ui_bundle_html_checks,
        check_ui_bundle_section_order,
        check_ui_bundle_css_declarations,
        check_ui_bundle_local_asset_links,
        check_ui_bundle_no_remote_image_urls,
    ]
    for check in checks:
        if check(actual, rules, **options) == 0.0:
            return 0.0
    return 1.0


def check_ui_previewable_generative_bundle(actual: str, rules: Dict, **options) -> float:
    return check_generative_ui_bundle(actual, rules, **options)