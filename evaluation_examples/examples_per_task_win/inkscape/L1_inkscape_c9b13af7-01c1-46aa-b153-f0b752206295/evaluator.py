"""Per-task evaluator for scaling the complete logo selection to 150%."""

import math
import re
import xml.etree.ElementTree as ET


def _parse_style(style_str):
    if not style_str:
        return {}
    result = {}
    for part in style_str.split(";"):
        if ":" in part:
            key, value = part.split(":", 1)
            result[key.strip()] = value.strip()
    return result


def _find_element_by_id(root, element_id):
    for elem in root.iter():
        if elem.get("id") == element_id:
            return elem
    return None


def _get_style_prop(elem, prop):
    style = _parse_style(elem.get("style", ""))
    return style.get(prop, elem.get(prop))


def _get_float(value, default=None):
    if value is None:
        return default
    try:
        return float(re.sub(r"[a-zA-Z%]+$", "", str(value).strip()))
    except (TypeError, ValueError):
        return default


def _parse_svg(svg_file_path):
    try:
        tree = ET.parse(svg_file_path)
        return tree, tree.getroot()
    except Exception:
        return None, None


def _tag_local(elem):
    tag = elem.tag
    return tag.split("}", 1)[1] if "}" in tag else tag


def _transform_scale(transform):
    """Return approximate x/y scale factors encoded by SVG transform strings."""
    sx = 1.0
    sy = 1.0
    if not transform:
        return sx, sy

    for name, args in re.findall(r"([a-zA-Z]+)\(([^)]*)\)", transform):
        values = [_get_float(v) for v in re.split(r"[,\s]+", args.strip()) if v]
        values = [v for v in values if v is not None]
        lname = name.lower()
        if lname == "scale" and values:
            sx *= values[0]
            sy *= values[1] if len(values) > 1 else values[0]
        elif lname == "matrix" and len(values) >= 4:
            a, b, c, d = values[:4]
            sx *= math.hypot(a, b)
            sy *= math.hypot(c, d)
    return abs(sx), abs(sy)


def _parent_map(root):
    return {child: parent for parent in root.iter() for child in parent}


def _effective_transform_scale(elem, parents):
    sx = 1.0
    sy = 1.0
    current = elem
    while current is not None:
        tsx, tsy = _transform_scale(current.get("transform", ""))
        sx *= tsx
        sy *= tsy
        current = parents.get(current)
    return sx, sy


def _effective_size(elem, parents):
    tag = _tag_local(elem)
    sx, sy = _effective_transform_scale(elem, parents)

    if tag == "circle":
        r = _get_float(elem.get("r"))
        if r is None:
            return None, None
        return r * sx, r * sy

    if tag == "ellipse":
        rx = _get_float(elem.get("rx"))
        ry = _get_float(elem.get("ry"))
        if rx is None or ry is None:
            return None, None
        return rx * sx, ry * sy

    if tag == "text":
        font_size = _get_float(_get_style_prop(elem, "font-size"))
        if font_size is None:
            return None, None
        return font_size * sx, font_size * sy

    width = _get_float(elem.get("width"))
    height = _get_float(elem.get("height"))
    if width is not None and height is not None:
        return width * sx, height * sy

    return None, None


def _check_scaled_element(root, parents, check, expected_scale, tolerance):
    elem = _find_element_by_id(root, check.get("element_id"))
    if elem is None:
        return False

    actual_x, actual_y = _effective_size(elem, parents)
    if actual_x is None or actual_y is None:
        return False

    base_x = _get_float(check.get("base_size"))
    base_y = _get_float(check.get("base_size_y"), base_x)
    if base_x is None or base_y is None:
        return False

    expected_x = base_x * expected_scale
    expected_y = base_y * expected_scale
    return abs(actual_x - expected_x) <= tolerance and abs(actual_y - expected_y) <= tolerance


def check_inkscape_element_geometry(svg_file_path, rule):
    """Verify every logo object was uniformly scaled to the expected factor."""
    _, root = _parse_svg(svg_file_path)
    if root is None:
        return 0.0

    expected_scale = _get_float(rule.get("expected_scale_factor"), 1.5)
    tolerance = _get_float(rule.get("tolerance"), 0.75)
    checks = rule.get("element_checks", [])

    if not checks:
        checks = [
            {"element_id": "logo_outer", "base_size": 150},
            {"element_id": "logo_inner", "base_size": 100},
            {"element_id": "logo_text", "base_size": 120},
            {"element_id": "dot1", "base_size": 12},
            {"element_id": "dot2", "base_size": 12},
            {"element_id": "dot3", "base_size": 12},
        ]

    parents = _parent_map(root)
    for check in checks:
        if not _check_scaled_element(root, parents, check, expected_scale, tolerance):
            return 0.0

    return 1.0
