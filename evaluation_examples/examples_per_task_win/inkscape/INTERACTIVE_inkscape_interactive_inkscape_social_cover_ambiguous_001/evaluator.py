"""Evaluator for INTERACTIVE_inkscape_interactive_inkscape_social_cover_ambiguous_001."""

import os
import re
import xml.etree.ElementTree as ET


def _parse_svg(svg_file_path):
    try:
        tree = ET.parse(svg_file_path)
        return tree, tree.getroot()
    except Exception:
        return None, None


def _get_float(value, default=None):
    if value is None:
        return default
    try:
        return float(re.sub(r"[a-zA-Z%]+$", "", str(value).strip()))
    except (TypeError, ValueError):
        return default


def _find_element_by_id(root, element_id):
    for elem in root.iter():
        if elem.get("id") == element_id:
            return elem
    return None


def _tag_local(elem):
    if "}" in elem.tag:
        return elem.tag.split("}", 1)[1]
    return elem.tag


def _document_size(root):
    width = _get_float(root.get("width"))
    height = _get_float(root.get("height"))
    if width is not None and height is not None:
        return width, height

    view_box = root.get("viewBox", "")
    parts = view_box.split()
    if len(parts) == 4:
        return _get_float(parts[2]), _get_float(parts[3])
    return width, height


def _text_elements(root):
    return [elem for elem in root.iter() if _tag_local(elem) == "text"]


def _element_text(elem):
    return "".join(elem.itertext()).strip()


def _position(elem):
    x = _get_float(elem.get("x"))
    y = _get_float(elem.get("y"))

    if x is None or y is None:
        for child in elem.iter():
            if x is None:
                x = _get_float(child.get("x"))
            if y is None:
                y = _get_float(child.get("y"))
            if x is not None and y is not None:
                break

    transform = elem.get("transform", "")
    match = re.search(r"translate\(\s*([-0-9.]+)[,\s]+([-0-9.]+)\s*\)", transform)
    if match:
        tx = _get_float(match.group(1), 0)
        ty = _get_float(match.group(2), 0)
        x = (x or 0) + tx
        y = (y or 0) + ty

    return x, y


def check_inkscape_document_properties(svg_file_path, rule):
    _, root = _parse_svg(svg_file_path)
    if root is None:
        return 0.0

    actual_w, actual_h = _document_size(root)
    expected_w = _get_float(rule.get("expected_width"))
    expected_h = _get_float(rule.get("expected_height"))
    tolerance = _get_float(rule.get("tolerance"), 5)

    if expected_w is not None and (actual_w is None or abs(actual_w - expected_w) > tolerance):
        return 0.0
    if expected_h is not None and (actual_h is None or abs(actual_h - expected_h) > tolerance):
        return 0.0
    return 1.0


def check_inkscape_text_content(svg_file_path, rule):
    _, root = _parse_svg(svg_file_path)
    if root is None:
        return 0.0

    elem = _find_element_by_id(root, rule.get("element_id"))
    if elem is None:
        return 0.0
    return 1.0 if _element_text(elem) == rule.get("expected_text", "").strip() else 0.0


def check_inkscape_text_element(svg_file_path, rule):
    """Check that required copy exists as an SVG text element, optionally in a page region."""
    _, root = _parse_svg(svg_file_path)
    if root is None:
        return 0.0

    expected_text = rule.get("expected_text", "").strip()
    region = rule.get("region")
    page_w, page_h = _document_size(root)

    matches = [elem for elem in _text_elements(root) if _element_text(elem) == expected_text]
    if not matches:
        return 0.0

    if not region:
        return 1.0

    for elem in matches:
        x, y = _position(elem)
        if x is None or y is None or page_w is None or page_h is None:
            continue
        if region == "top_right" and x >= page_w * 0.55 and y <= page_h * 0.30:
            return 1.0
    return 0.0


def check_png_dimensions(png_path, rule):
    if not png_path or not os.path.isfile(png_path):
        return 0.0

    try:
        from PIL import Image

        with Image.open(png_path) as img:
            expected_w = int(rule.get("expected_width"))
            expected_h = int(rule.get("expected_height"))
            return 1.0 if img.width == expected_w and img.height == expected_h else 0.0
    except Exception:
        return 0.0
