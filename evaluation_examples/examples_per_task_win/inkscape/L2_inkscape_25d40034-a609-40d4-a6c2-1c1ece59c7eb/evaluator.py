"""Per-task evaluator for the overlapping-circles Difference task."""

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


def _normalize_color(color):
    if not color:
        return None
    color = color.strip().lower()
    if color == "none":
        return "none"
    if color.startswith("#"):
        value = color[1:]
        if len(value) == 3:
            value = "".join(ch * 2 for ch in value)
        elif len(value) == 8:
            value = value[:6]
        return "#" + value
    return color


def _parse_svg(svg_file_path):
    try:
        tree = ET.parse(svg_file_path)
        return tree, tree.getroot()
    except Exception:
        return None, None


def _tag_local(elem):
    tag = elem.tag
    return tag.split("}", 1)[1] if "}" in tag else tag


def _find_element_by_id(root, element_id):
    for elem in root.iter():
        if elem.get("id") == element_id:
            return elem
    return None


def _get_style_prop(elem, prop):
    style = _parse_style(elem.get("style", ""))
    return style.get(prop, elem.get(prop))


def _path_points(d_attr):
    """Extract endpoint-like coordinate pairs from common SVG path commands."""
    if not d_attr:
        return []

    tokens = re.findall(r"[AaCcHhLlMmQqSsTtVvZz]|[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", d_attr)
    points = []
    command = None
    index = 0
    current_x = 0.0
    current_y = 0.0

    def is_command(value):
        return bool(re.fullmatch(r"[AaCcHhLlMmQqSsTtVvZz]", value))

    def take_numbers(start):
        values = []
        while start < len(tokens) and not is_command(tokens[start]):
            values.append(float(tokens[start]))
            start += 1
        return values, start

    while index < len(tokens):
        if is_command(tokens[index]):
            command = tokens[index]
            index += 1
            if command in "Zz":
                continue

        values, index = take_numbers(index)
        if not command or not values:
            continue

        absolute = command.isupper()
        cmd = command.upper()
        step = {
            "M": 2,
            "L": 2,
            "T": 2,
            "H": 1,
            "V": 1,
            "C": 6,
            "S": 4,
            "Q": 4,
            "A": 7,
        }.get(cmd)
        if not step:
            continue

        for offset in range(0, len(values) - step + 1, step):
            chunk = values[offset : offset + step]
            if cmd in ("M", "L", "T"):
                x, y = chunk[-2], chunk[-1]
            elif cmd == "H":
                x, y = chunk[-1], current_y
            elif cmd == "V":
                x, y = current_x, chunk[-1]
            else:
                x, y = chunk[-2], chunk[-1]
            if not absolute:
                x += current_x
                y += current_y
            current_x, current_y = x, y
            points.append((x, y))

        if cmd == "M":
            command = "L" if absolute else "l"
    return points


def _path_has_difference_geometry(path_elem, rule):
    """Check the result resembles left circle minus right circle, not just a full circle."""
    d_attr = path_elem.get("d", "")
    if not d_attr:
        return False

    points = _path_points(d_attr)
    if len(points) < 3:
        return False

    # The original circles are centered at (320,300) and (480,300), r=120.
    # Their intersections are around x=400, y=210.6 and y=389.4. A correct
    # Difference path should include boundary points near that cut line while
    # still retaining the left circle's outer extent.
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    tolerance = float(rule.get("geometry_tolerance", 12))

    has_left_extent = min_x <= 200 + tolerance
    has_cut_x = any(abs(x - 400) <= tolerance for x in xs)
    has_intersection_y = any(abs(y - 210.6) <= tolerance or abs(y - 389.4) <= tolerance for y in ys)

    # A full original left circle would still reach x ~= 440. After subtracting
    # the right circle, the visible shape should stop near the intersection x.
    no_full_right_extent = max_x <= 400 + tolerance
    has_curve = bool(re.search(r"[AaCc]", d_attr))

    return has_left_extent and has_cut_x and has_intersection_y and no_full_right_extent and has_curve


def check_inkscape_fill_color(svg_file_path, rule):
    _, root = _parse_svg(svg_file_path)
    if root is None:
        return 0.0

    elem = _find_element_by_id(root, rule.get("element_id"))
    if elem is None:
        return 0.0

    expected_fill = _normalize_color(rule.get("expected_fill"))
    actual_fill = _normalize_color(_get_style_prop(elem, "fill"))
    return 1.0 if actual_fill == expected_fill else 0.0


def check_inkscape_boolean_operation(svg_file_path, rule):
    _, root = _parse_svg(svg_file_path)
    if root is None:
        return 0.0

    for original_id in rule.get("original_ids", []):
        if _find_element_by_id(root, original_id) is not None:
            return 0.0

    result_id = rule.get("result_id", "circle_left")
    result_elem = _find_element_by_id(root, result_id)
    if result_elem is None:
        return 0.0

    if _tag_local(result_elem) != rule.get("expected_result_tag", "path"):
        return 0.0

    if rule.get("require_difference_geometry", True):
        if not _path_has_difference_geometry(result_elem, rule):
            return 0.0

    return 1.0


def check_inkscape_l2_boolean_move(svg_file_path, rule):
    if check_inkscape_boolean_operation(svg_file_path, rule.get("boolean_check", {})) < 1.0:
        return 0.0
    if check_inkscape_fill_color(svg_file_path, rule.get("fill_check", {})) < 1.0:
        return 0.0
    return 1.0
