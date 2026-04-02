"""
Inkscape SVG evaluator functions for L1 tasks.

All evaluators parse SVG files using xml.etree.ElementTree with SVG/Inkscape namespace handling.
Each function takes (svg_file_path, rule) and returns 1.0 (pass) or 0.0 (fail).
"""

import re
import xml.etree.ElementTree as ET

# SVG namespaces
NS = {
    'svg': 'http://www.w3.org/2000/svg',
    'inkscape': 'http://www.inkscape.org/namespaces/inkscape',
    'sodipodi': 'http://sodipodi.sourceforge.net/DTD/sodipodi-0.0.dtd',
    'xlink': 'http://www.w3.org/1999/xlink',
    'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
}

# Register namespaces so ET doesn't mangle them on write
for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _parse_style(style_str):
    """Parse CSS-like style string 'fill:#ff0000;stroke:#000' into dict."""
    if not style_str:
        return {}
    result = {}
    for part in style_str.split(';'):
        part = part.strip()
        if ':' in part:
            key, val = part.split(':', 1)
            result[key.strip()] = val.strip()
    return result


def _normalize_color(color):
    """Normalize hex colors: #f00 → #ff0000, uppercase → lowercase. 'none' stays 'none'."""
    if not color:
        return None
    color = color.strip().lower()
    if color == 'none':
        return 'none'
    if color.startswith('#'):
        hex_part = color[1:]
        if len(hex_part) == 3:
            hex_part = ''.join(c * 2 for c in hex_part)
        elif len(hex_part) == 8:
            # #rrggbbaa → just take rrggbb
            hex_part = hex_part[:6]
        return '#' + hex_part.lower()
    # Named colors — just return as-is for now
    return color


def _find_element_by_id(root, element_id):
    """Find element by id attribute across all elements."""
    for elem in root.iter():
        if elem.get('id') == element_id:
            return elem
    return None


def _get_style_prop(elem, prop):
    """Get a style property from either inline style or direct attribute."""
    style = _parse_style(elem.get('style', ''))
    if prop in style:
        return style[prop]
    return elem.get(prop)


def _get_float(value, default=None):
    """Safely convert to float."""
    if value is None:
        return default
    try:
        # Handle units like "200px" or "5mm"
        return float(re.sub(r'[a-zA-Z%]+$', '', str(value).strip()))
    except (ValueError, TypeError):
        return default


def _parse_svg(svg_file_path):
    """Parse SVG file and return (tree, root). Returns (None, None) on error."""
    try:
        tree = ET.parse(svg_file_path)
        return tree, tree.getroot()
    except Exception:
        return None, None


def _tag_local(elem):
    """Get local tag name without namespace."""
    tag = elem.tag
    if '}' in tag:
        return tag.split('}', 1)[1]
    return tag


# ---------------------------------------------------------------------------
# L1 Evaluator functions
# ---------------------------------------------------------------------------

def check_inkscape_fill_color(svg_file_path, rule):
    """Verify element fill color.
    rule: {"element_id": str, "expected_fill": str}
    """
    _, root = _parse_svg(svg_file_path)
    if root is None:
        return 0.0

    element_id = rule.get("element_id")
    expected_fill = _normalize_color(rule.get("expected_fill"))

    elem = _find_element_by_id(root, element_id)
    if elem is None:
        return 0.0

    actual_fill = _get_style_prop(elem, 'fill')
    # For text elements, also check tspan children for fill
    if actual_fill is None and _tag_local(elem) == 'text':
        for child in elem:
            if _tag_local(child) == 'tspan':
                actual_fill = _get_style_prop(child, 'fill')
                if actual_fill:
                    break
    actual_fill = _normalize_color(actual_fill)

    if expected_fill == 'none':
        return 1.0 if actual_fill == 'none' else 0.0

    if actual_fill == expected_fill:
        return 1.0
    return 0.0


def check_inkscape_stroke(svg_file_path, rule):
    """Verify stroke color and/or width.
    rule: {"element_id": str, "expected_stroke": str, "expected_stroke_width": str}
    """
    _, root = _parse_svg(svg_file_path)
    if root is None:
        return 0.0

    element_id = rule.get("element_id")
    elem = _find_element_by_id(root, element_id)
    if elem is None:
        return 0.0

    if "expected_stroke" in rule:
        expected = _normalize_color(rule["expected_stroke"])
        actual = _normalize_color(_get_style_prop(elem, 'stroke'))
        if expected == 'none':
            if actual not in ('none', None):
                return 0.0
        elif actual != expected:
            return 0.0

    if "expected_stroke_width" in rule:
        expected_w = _get_float(rule["expected_stroke_width"])
        actual_w = _get_float(_get_style_prop(elem, 'stroke-width'))
        if expected_w is None or actual_w is None:
            return 0.0
        tolerance = _get_float(rule.get("tolerance"), 0.5)
        if abs(actual_w - expected_w) > tolerance:
            return 0.0

    return 1.0


def check_inkscape_element_geometry(svg_file_path, rule):
    """Verify element size and/or position.
    rule: {"element_id": str, "expected_width": str, "expected_height": str,
           "expected_x": str, "expected_y": str, "tolerance": float,
           "expected_scale_factor": float}
    """
    _, root = _parse_svg(svg_file_path)
    if root is None:
        return 0.0

    element_id = rule.get("element_id")
    elem = _find_element_by_id(root, element_id)
    if elem is None:
        return 0.0

    tolerance = _get_float(rule.get("tolerance"), 5)

    # Handle scale factor check (Task 1-35)
    if "expected_scale_factor" in rule:
        scale = _get_float(rule["expected_scale_factor"])
        # For circles/ellipses, check r/rx/ry; for rects, check width/height
        tag = _tag_local(elem)
        if tag == 'circle':
            r = _get_float(elem.get('r'))
            if r is None:
                return 0.0
            # Original r from the SVG design doc for logo_outer is known
            # We just check the transform attribute for scale
            transform = elem.get('transform', '')
            if 'scale' in transform or 'matrix' in transform:
                return 1.0
            # If dimensions changed directly
            return 0.0
        else:
            # Check if transform contains scale, or if w/h changed
            transform = elem.get('transform', '')
            if transform:
                return 1.0
            # Check direct attributes
            w = _get_float(elem.get('width'))
            h = _get_float(elem.get('height'))
            if w is not None and h is not None:
                return 1.0
        return 0.0

    # Check position
    if "expected_x" in rule:
        expected_x = _get_float(rule["expected_x"])
        actual_x = _get_float(elem.get('x'))
        if actual_x is None:
            actual_x = _get_float(elem.get('cx'))
        if actual_x is None or expected_x is None:
            return 0.0
        if abs(actual_x - expected_x) > tolerance:
            return 0.0

    if "expected_y" in rule:
        expected_y = _get_float(rule["expected_y"])
        actual_y = _get_float(elem.get('y'))
        if actual_y is None:
            actual_y = _get_float(elem.get('cy'))
        if actual_y is None or expected_y is None:
            return 0.0
        if abs(actual_y - expected_y) > tolerance:
            return 0.0

    # Check size
    if "expected_width" in rule:
        expected_w = _get_float(rule["expected_width"])
        actual_w = _get_float(elem.get('width'))
        if actual_w is None or expected_w is None:
            return 0.0
        if abs(actual_w - expected_w) > tolerance:
            return 0.0

    if "expected_height" in rule:
        expected_h = _get_float(rule["expected_height"])
        actual_h = _get_float(elem.get('height'))
        if actual_h is None or expected_h is None:
            return 0.0
        if abs(actual_h - expected_h) > tolerance:
            return 0.0

    return 1.0


def check_inkscape_text_content(svg_file_path, rule):
    """Verify text content of a text element.
    rule: {"element_id": str, "expected_text": str}
    """
    _, root = _parse_svg(svg_file_path)
    if root is None:
        return 0.0

    element_id = rule.get("element_id")
    expected_text = rule.get("expected_text", "").strip()

    elem = _find_element_by_id(root, element_id)
    if elem is None:
        return 0.0

    # Collect all text content from element and its children (tspan etc.)
    actual_text = ''.join(elem.itertext()).strip()

    if actual_text == expected_text:
        return 1.0
    return 0.0


def check_inkscape_text_style(svg_file_path, rule):
    """Verify text font properties (size, weight, style, family, fill).
    rule: {"element_id": str, "expected_font_size": str, "expected_font_weight": str,
           "expected_font_style": str, "expected_font_family": str, "expected_fill": str}
    """
    _, root = _parse_svg(svg_file_path)
    if root is None:
        return 0.0

    element_id = rule.get("element_id")
    elem = _find_element_by_id(root, element_id)
    if elem is None:
        return 0.0

    # Gather style from both the element and its tspan children
    def _get_text_style(el, prop):
        val = _get_style_prop(el, prop)
        if val:
            return val
        # Check tspan children
        for child in el:
            if _tag_local(child) == 'tspan':
                val = _get_style_prop(child, prop)
                if val:
                    return val
        return None

    if "expected_font_size" in rule:
        expected = _get_float(rule["expected_font_size"])
        actual = _get_float(_get_text_style(elem, 'font-size'))
        if actual is None or expected is None:
            return 0.0
        if abs(actual - expected) > 2:
            return 0.0

    if "expected_font_weight" in rule:
        expected = rule["expected_font_weight"].lower()
        actual = (_get_text_style(elem, 'font-weight') or '').lower()
        if expected == 'bold' and actual not in ('bold', '700'):
            return 0.0
        elif expected == 'normal' and actual not in ('normal', '400', '', None):
            return 0.0

    if "expected_font_style" in rule:
        expected = rule["expected_font_style"].lower()
        actual = (_get_text_style(elem, 'font-style') or '').lower()
        if actual != expected:
            return 0.0

    if "expected_font_family" in rule:
        expected = rule["expected_font_family"].lower().strip("'\"")
        actual_raw = _get_text_style(elem, 'font-family') or ''
        actual = actual_raw.lower().strip("'\"")
        if expected not in actual:
            return 0.0

    if "expected_fill" in rule:
        expected = _normalize_color(rule["expected_fill"])
        actual = _normalize_color(_get_text_style(elem, 'fill'))
        if actual != expected:
            return 0.0

    return 1.0


def check_inkscape_layer_visibility(svg_file_path, rule):
    """Verify layer visibility.
    rule: {"layer_label": str, "expected_visible": bool}
    """
    _, root = _parse_svg(svg_file_path)
    if root is None:
        return 0.0

    layer_label = rule.get("layer_label")
    expected_visible = rule.get("expected_visible", True)

    # Layers are <svg:g> with inkscape:groupmode="layer"
    ink_label = f'{{{NS["inkscape"]}}}label'
    ink_groupmode = f'{{{NS["inkscape"]}}}groupmode'

    for g in root.iter(f'{{{NS["svg"]}}}g'):
        if g.get(ink_groupmode) == 'layer' and g.get(ink_label) == layer_label:
            style = _parse_style(g.get('style', ''))
            display = style.get('display', 'inline')
            is_visible = display != 'none'
            return 1.0 if is_visible == expected_visible else 0.0

    # Also check without namespace prefix (some SVGs)
    for g in root.iter('g'):
        if g.get(ink_groupmode) == 'layer' and g.get(ink_label) == layer_label:
            style = _parse_style(g.get('style', ''))
            display = style.get('display', 'inline')
            is_visible = display != 'none'
            return 1.0 if is_visible == expected_visible else 0.0

    return 0.0


def check_inkscape_layer_name(svg_file_path, rule):
    """Verify layer has been renamed.
    rule: {"layer_id": str, "expected_label": str}
    """
    _, root = _parse_svg(svg_file_path)
    if root is None:
        return 0.0

    layer_id = rule.get("layer_id")
    expected_label = rule.get("expected_label")

    ink_label = f'{{{NS["inkscape"]}}}label'

    elem = _find_element_by_id(root, layer_id)
    if elem is None:
        return 0.0

    actual_label = elem.get(ink_label, '')
    return 1.0 if actual_label == expected_label else 0.0


def check_inkscape_element_deleted(svg_file_path, rule):
    """Verify element has been deleted (no longer exists).
    rule: {"deleted_element_id": str}
    """
    _, root = _parse_svg(svg_file_path)
    if root is None:
        return 0.0

    deleted_id = rule.get("deleted_element_id")
    elem = _find_element_by_id(root, deleted_id)
    return 1.0 if elem is None else 0.0


def check_inkscape_document_properties(svg_file_path, rule):
    """Verify document dimensions.
    rule: {"expected_width": str, "expected_height": str}
    """
    _, root = _parse_svg(svg_file_path)
    if root is None:
        return 0.0

    if "expected_width" in rule:
        expected_w = _get_float(rule["expected_width"])
        actual_w = _get_float(root.get('width'))
        # Also check viewBox
        if actual_w is None:
            vb = root.get('viewBox', '')
            parts = vb.split()
            if len(parts) == 4:
                actual_w = _get_float(parts[2])
        if actual_w is None or expected_w is None:
            return 0.0
        if abs(actual_w - expected_w) > 5:
            return 0.0

    if "expected_height" in rule:
        expected_h = _get_float(rule["expected_height"])
        actual_h = _get_float(root.get('height'))
        if actual_h is None:
            vb = root.get('viewBox', '')
            parts = vb.split()
            if len(parts) == 4:
                actual_h = _get_float(parts[3])
        if actual_h is None or expected_h is None:
            return 0.0
        if abs(actual_h - expected_h) > 5:
            return 0.0

    return 1.0


def check_inkscape_opacity(svg_file_path, rule):
    """Verify element master opacity.
    rule: {"element_id": str, "expected_opacity": str, "tolerance": str}
    """
    _, root = _parse_svg(svg_file_path)
    if root is None:
        return 0.0

    element_id = rule.get("element_id")
    expected = _get_float(rule.get("expected_opacity"))
    tolerance = _get_float(rule.get("tolerance"), 0.05)

    elem = _find_element_by_id(root, element_id)
    if elem is None or expected is None:
        return 0.0

    # Check style opacity and attribute opacity
    actual = _get_float(_get_style_prop(elem, 'opacity'))
    if actual is None:
        actual = 1.0  # default opacity is 1

    if abs(actual - expected) <= tolerance:
        return 1.0
    return 0.0


def check_inkscape_element_count(svg_file_path, rule):
    """Count elements of a specific tag type.
    rule: {"element_tag": str, "min_count": int,
           "also_tag": str (optional), "combined_min": int (optional)}
    """
    _, root = _parse_svg(svg_file_path)
    if root is None:
        return 0.0

    tag = rule.get("element_tag")
    min_count = rule.get("min_count", 1)

    # Count elements with the given tag (with SVG namespace)
    count = len(root.findall(f'.//{{{NS["svg"]}}}{tag}'))
    # Also count without namespace
    count += len([e for e in root.iter() if _tag_local(e) == tag and f'{{{NS["svg"]}}}' not in e.tag])

    # Handle combined count (e.g., circle + ellipse)
    if "also_tag" in rule:
        also_tag = rule["also_tag"]
        also_count = len(root.findall(f'.//{{{NS["svg"]}}}{also_tag}'))
        also_count += len([e for e in root.iter() if _tag_local(e) == also_tag and f'{{{NS["svg"]}}}' not in e.tag])
        combined_min = rule.get("combined_min", min_count)
        return 1.0 if (count + also_count) >= combined_min else 0.0

    return 1.0 if count >= min_count else 0.0


def check_inkscape_text_align(svg_file_path, rule):
    """Verify text-anchor or text-align.
    rule: {"element_id": str, "expected_text_anchor": str}
    """
    _, root = _parse_svg(svg_file_path)
    if root is None:
        return 0.0

    element_id = rule.get("element_id")
    expected = rule.get("expected_text_anchor", "").lower()

    elem = _find_element_by_id(root, element_id)
    if elem is None:
        return 0.0

    actual = (_get_style_prop(elem, 'text-anchor') or '').lower()
    if actual == expected:
        return 1.0

    # Also check tspan children
    for child in elem:
        if _tag_local(child) == 'tspan':
            actual = (_get_style_prop(child, 'text-anchor') or '').lower()
            if actual == expected:
                return 1.0

    return 0.0


def check_inkscape_add_layer(svg_file_path, rule):
    """Verify a new layer with expected label exists.
    rule: {"expected_layer_label": str}
    """
    _, root = _parse_svg(svg_file_path)
    if root is None:
        return 0.0

    expected_label = rule.get("expected_layer_label")
    ink_label = f'{{{NS["inkscape"]}}}label'
    ink_groupmode = f'{{{NS["inkscape"]}}}groupmode'

    for g in root.iter():
        if _tag_local(g) == 'g' and g.get(ink_groupmode) == 'layer':
            if g.get(ink_label) == expected_label:
                return 1.0

    return 0.0


def check_inkscape_ungroup(svg_file_path, rule):
    """Verify a group has been ungrouped — specified children are now free.
    rule: {"ungrouped_id": str, "expected_free_ids": [str]}
    """
    _, root = _parse_svg(svg_file_path)
    if root is None:
        return 0.0

    ungrouped_id = rule.get("ungrouped_id")
    expected_free_ids = rule.get("expected_free_ids", [])

    # The original group should no longer exist
    group_elem = _find_element_by_id(root, ungrouped_id)
    if group_elem is not None:
        # Group still exists — check if the children are NOT inside it
        for fid in expected_free_ids:
            child = _find_element_by_id(group_elem, fid)
            if child is not None:
                return 0.0  # Still inside the group
        return 1.0

    # Group is gone, verify children exist as direct layer children
    for fid in expected_free_ids:
        elem = _find_element_by_id(root, fid)
        if elem is None:
            return 0.0

    return 1.0


def check_inkscape_zorder(svg_file_path, rule):
    """Verify element z-order position (top or bottom among siblings).
    rule: {"element_id": str, "expected_position": "top"|"bottom"}
    """
    _, root = _parse_svg(svg_file_path)
    if root is None:
        return 0.0

    element_id = rule.get("element_id")
    expected_pos = rule.get("expected_position", "").lower()

    # Find the element and its parent
    elem = _find_element_by_id(root, element_id)
    if elem is None:
        return 0.0

    # Find parent
    parent_map = {c: p for p in root.iter() for c in p}
    parent = parent_map.get(elem)
    if parent is None:
        return 0.0

    # Filter to shape/visual children only (skip defs, metadata, etc.)
    visual_children = [c for c in parent if _tag_local(c) not in
                       ('defs', 'metadata', 'namedview', 'title', 'desc')]

    if not visual_children:
        return 0.0

    if expected_pos == 'top':
        return 1.0 if visual_children[-1] is elem else 0.0
    elif expected_pos == 'bottom':
        return 1.0 if visual_children[0] is elem else 0.0

    return 0.0


def check_inkscape_stroke_dasharray(svg_file_path, rule):
    """Verify stroke has a dash pattern.
    rule: {"element_id": str, "expect_dash": bool}
    """
    _, root = _parse_svg(svg_file_path)
    if root is None:
        return 0.0

    element_id = rule.get("element_id")
    expect_dash = rule.get("expect_dash", True)

    elem = _find_element_by_id(root, element_id)
    if elem is None:
        return 0.0

    dasharray = _get_style_prop(elem, 'stroke-dasharray')
    has_dash = dasharray is not None and dasharray.lower() not in ('none', '', '0')

    return 1.0 if has_dash == expect_dash else 0.0


def check_inkscape_stroke_linecap(svg_file_path, rule):
    """Verify stroke-linecap property.
    rule: {"element_id": str, "expected_linecap": str}
    """
    _, root = _parse_svg(svg_file_path)
    if root is None:
        return 0.0

    element_id = rule.get("element_id")
    expected = rule.get("expected_linecap", "").lower()

    elem = _find_element_by_id(root, element_id)
    if elem is None:
        return 0.0

    actual = (_get_style_prop(elem, 'stroke-linecap') or '').lower()
    return 1.0 if actual == expected else 0.0


def check_inkscape_radial_gradient(svg_file_path, rule):
    """Verify radial gradient is applied to an element.
    rule: {"element_id": str, "gradient_type": str}
    """
    _, root = _parse_svg(svg_file_path)
    if root is None:
        return 0.0

    element_id = rule.get("element_id")
    expected_type = rule.get("gradient_type", "radialGradient")

    elem = _find_element_by_id(root, element_id)
    if elem is None:
        return 0.0

    fill = _get_style_prop(elem, 'fill') or ''
    # Fill should reference a gradient via url(#...)
    match = re.search(r'url\(#([^)]+)\)', fill)
    if not match:
        return 0.0

    grad_id = match.group(1)

    # Find the gradient definition in <defs>
    for defs in root.iter():
        if _tag_local(defs) == 'defs':
            for child in defs:
                if child.get('id') == grad_id and _tag_local(child) == expected_type:
                    return 1.0
                # Also check xlink:href chains
                href = child.get(f'{{{NS["xlink"]}}}href') or child.get('href')
                if href and href.lstrip('#') == grad_id:
                    continue
                if child.get('id') == grad_id:
                    if expected_type.lower() in _tag_local(child).lower():
                        return 1.0

    # Direct search anywhere
    for child in root.iter():
        if child.get('id') == grad_id and expected_type.lower() in _tag_local(child).lower():
            return 1.0

    return 0.0


def check_inkscape_transform(svg_file_path, rule):
    """Verify element has expected transform.
    rule: {"element_id": str, "expected_transform_contains": str}
    """
    _, root = _parse_svg(svg_file_path)
    if root is None:
        return 0.0

    element_id = rule.get("element_id")
    expected_contains = rule.get("expected_transform_contains", "")

    elem = _find_element_by_id(root, element_id)
    if elem is None:
        return 0.0

    transform = elem.get('transform', '')
    if expected_contains in transform:
        return 1.0

    # Also check style transform (less common)
    style_transform = _get_style_prop(elem, 'transform') or ''
    if expected_contains in style_transform:
        return 1.0

    return 0.0


def check_inkscape_align(svg_file_path, rule):
    """Verify elements are aligned along an axis.
    rule: {"element_ids": [str], "align_axis": str, "page_width": float,
           "page_height": float, "tolerance": float}
    """
    _, root = _parse_svg(svg_file_path)
    if root is None:
        return 0.0

    element_ids = rule.get("element_ids", [])
    align_axis = rule.get("align_axis", "")
    tolerance = _get_float(rule.get("tolerance"), 10)

    centers = []
    for eid in element_ids:
        elem = _find_element_by_id(root, eid)
        if elem is None:
            return 0.0

        tag = _tag_local(elem)
        if tag == 'rect':
            x = _get_float(elem.get('x'), 0)
            y = _get_float(elem.get('y'), 0)
            w = _get_float(elem.get('width'), 0)
            h = _get_float(elem.get('height'), 0)
            cx = x + w / 2
            cy = y + h / 2
        elif tag in ('circle', 'ellipse'):
            cx = _get_float(elem.get('cx'), 0)
            cy = _get_float(elem.get('cy'), 0)
        else:
            x = _get_float(elem.get('x'), 0)
            y = _get_float(elem.get('y'), 0)
            cx, cy = x, y
        centers.append((cx, cy))

    if not centers:
        return 0.0

    if align_axis == "horizontal_center":
        # All elements should have same cx
        cx_values = [c[0] for c in centers]
        avg_cx = sum(cx_values) / len(cx_values)
        for cx in cx_values:
            if abs(cx - avg_cx) > tolerance:
                return 0.0
        return 1.0
    elif align_axis == "vertical_center":
        cy_values = [c[1] for c in centers]
        avg_cy = sum(cy_values) / len(cy_values)
        for cy in cy_values:
            if abs(cy - avg_cy) > tolerance:
                return 0.0
        return 1.0

    return 0.0


def check_inkscape_object_to_path(svg_file_path, rule):
    """Verify a shape has been converted to a <path>.
    rule: {"original_id": str, "expected_tag": str}
    """
    _, root = _parse_svg(svg_file_path)
    if root is None:
        return 0.0

    original_id = rule.get("original_id")
    expected_tag = rule.get("expected_tag", "path")

    elem = _find_element_by_id(root, original_id)
    if elem is None:
        return 0.0

    actual_tag = _tag_local(elem)
    return 1.0 if actual_tag == expected_tag else 0.0


def check_inkscape_fill_rule(svg_file_path, rule):
    """Verify fill-rule property.
    rule: {"element_id": str, "expected_fill_rule": str}
    """
    _, root = _parse_svg(svg_file_path)
    if root is None:
        return 0.0

    element_id = rule.get("element_id")
    expected = rule.get("expected_fill_rule", "").lower()

    elem = _find_element_by_id(root, element_id)
    if elem is None:
        return 0.0

    actual = (_get_style_prop(elem, 'fill-rule') or '').lower()
    return 1.0 if actual == expected else 0.0


def check_inkscape_snap_to_grid(svg_file_path, rule):
    """Verify a guide line exists with the expected orientation and position.
    rule: {"guide_orientation": str, "guide_position": float, "tolerance": float}
    """
    _, root = _parse_svg(svg_file_path)
    if root is None:
        return 0.0

    expected_orient = rule.get("guide_orientation", "").lower()  # "horizontal" or "vertical"
    expected_pos = _get_float(rule.get("guide_position"))
    tolerance = _get_float(rule.get("tolerance"), 2)

    if expected_pos is None:
        return 0.0

    # Guides are in <sodipodi:guide> elements inside <svg:namedview>
    for nv in root.iter(f'{{{NS["sodipodi"]}}}namedview'):
        for guide in nv:
            if _tag_local(guide) == 'guide':
                return _check_guide(guide, expected_orient, expected_pos, tolerance)

    # Also check inkscape namedview
    ink_nv_tag = f'{{{NS["inkscape"]}}}namedview'
    for nv in root.iter(ink_nv_tag):
        for guide in nv:
            if _tag_local(guide) == 'guide':
                return _check_guide(guide, expected_orient, expected_pos, tolerance)

    # Check sodipodi:guide directly
    for guide in root.iter(f'{{{NS["sodipodi"]}}}guide'):
        result = _check_guide(guide, expected_orient, expected_pos, tolerance)
        if result == 1.0:
            return 1.0

    # Also search all elements for guide
    for elem in root.iter():
        if 'guide' in _tag_local(elem).lower():
            result = _check_guide(elem, expected_orient, expected_pos, tolerance)
            if result == 1.0:
                return 1.0

    return 0.0


def _check_guide(guide, expected_orient, expected_pos, tolerance):
    """Check if a single guide matches orientation and position."""
    # Inkscape 1.x uses inkscape:label and position attribute
    pos = guide.get('position')
    orient = guide.get('orientation') or guide.get(f'{{{NS["inkscape"]}}}orient')

    # sodipodi:guide uses orient="0,1" for horizontal, "1,0" for vertical
    # and position="x,y"
    if orient:
        orient = orient.strip()
        if orient in ('0,1', '0 1'):
            actual_orient = 'horizontal'
        elif orient in ('1,0', '1 0'):
            actual_orient = 'vertical'
        else:
            actual_orient = orient
    else:
        actual_orient = ''

    if pos:
        parts = pos.replace(',', ' ').split()
        if actual_orient == 'horizontal' and len(parts) >= 2:
            actual_pos = _get_float(parts[1])
        elif actual_orient == 'vertical' and len(parts) >= 1:
            actual_pos = _get_float(parts[0])
        else:
            actual_pos = _get_float(parts[0]) if parts else None
    else:
        # Try inkscape:position
        actual_pos = _get_float(guide.get(f'{{{NS["inkscape"]}}}position'))

    if actual_orient == expected_orient and actual_pos is not None:
        if abs(actual_pos - expected_pos) <= tolerance:
            return 1.0

    return 0.0


# ---------------------------------------------------------------------------
# New atomic evaluator functions (used by L2/L3 composites)
# ---------------------------------------------------------------------------

def check_inkscape_filter(svg_file_path, rule):
    """Check if a filter (e.g., feGaussianBlur, feDropShadow) is applied to an element.
    rule: {"element_id": str, "expected_filter_type": str}
    expected_filter_type: "feGaussianBlur", "feDropShadow", etc.
    """
    _, root = _parse_svg(svg_file_path)
    if root is None:
        return 0.0

    element_id = rule.get("element_id")
    expected_filter = rule.get("expected_filter_type", "")

    elem = _find_element_by_id(root, element_id)
    if elem is None:
        return 0.0

    # Get filter reference from style or attribute
    filter_val = _get_style_prop(elem, 'filter') or ''
    if not filter_val:
        return 0.0

    # Extract filter ID from url(#...)
    match = re.search(r'url\(#([^)]+)\)', filter_val)
    if not match:
        return 0.0

    filter_id = match.group(1)

    # Find the filter definition and check its primitives
    for elem_iter in root.iter():
        if _tag_local(elem_iter) == 'filter' and elem_iter.get('id') == filter_id:
            for child in elem_iter:
                if expected_filter.lower() in _tag_local(child).lower():
                    return 1.0
            # Also check linked filters via xlink:href
            href = elem_iter.get(f'{{{NS["xlink"]}}}href') or elem_iter.get('href')
            if href:
                linked_id = href.lstrip('#')
                for linked in root.iter():
                    if _tag_local(linked) == 'filter' and linked.get('id') == linked_id:
                        for child in linked:
                            if expected_filter.lower() in _tag_local(child).lower():
                                return 1.0

    return 0.0


def check_inkscape_boolean_operation(svg_file_path, rule):
    """Check boolean op result: original elements gone, result path remains.
    rule: {"original_ids": [str], "result_id": str (optional),
           "expected_result_tag": str (default "path")}
    """
    _, root = _parse_svg(svg_file_path)
    if root is None:
        return 0.0

    original_ids = rule.get("original_ids", [])
    result_id = rule.get("result_id")
    expected_tag = rule.get("expected_result_tag", "path")

    # All original elements should be gone (consumed by boolean op)
    for oid in original_ids:
        if _find_element_by_id(root, oid) is not None:
            return 0.0

    # If a result_id is specified, check it exists with expected tag
    if result_id:
        result_elem = _find_element_by_id(root, result_id)
        if result_elem is None:
            return 0.0
        if expected_tag and _tag_local(result_elem) != expected_tag:
            return 0.0

    return 1.0


def check_inkscape_gradient(svg_file_path, rule):
    """Check gradient type and optional stop count on an element.
    rule: {"element_id": str, "expected_gradient_type": str,
           "min_stops": int (optional)}
    expected_gradient_type: "linearGradient" or "radialGradient"
    """
    _, root = _parse_svg(svg_file_path)
    if root is None:
        return 0.0

    element_id = rule.get("element_id")
    expected_type = rule.get("expected_gradient_type", "linearGradient")
    min_stops = rule.get("min_stops", 0)

    elem = _find_element_by_id(root, element_id)
    if elem is None:
        return 0.0

    fill = _get_style_prop(elem, 'fill') or ''
    match = re.search(r'url\(#([^)]+)\)', fill)
    if not match:
        return 0.0

    grad_id = match.group(1)

    # Find the gradient, following xlink:href chains
    def _find_gradient(gid, depth=0):
        if depth > 5:
            return None
        for e in root.iter():
            if e.get('id') == gid:
                return e
        return None

    grad = _find_gradient(grad_id)
    if grad is None:
        return 0.0

    # Follow href chain to find the base gradient with stops
    base_grad = grad
    href = grad.get(f'{{{NS["xlink"]}}}href') or grad.get('href')
    if href:
        linked = _find_gradient(href.lstrip('#'))
        if linked is not None:
            base_grad = linked

    # Check type
    if expected_type.lower() not in _tag_local(grad).lower():
        # Also check base gradient type
        if expected_type.lower() not in _tag_local(base_grad).lower():
            return 0.0

    # Check stop count
    if min_stops > 0:
        stops = [c for c in base_grad if _tag_local(c) == 'stop']
        if not stops:
            stops = [c for c in grad if _tag_local(c) == 'stop']
        if len(stops) < min_stops:
            return 0.0

    return 1.0


def check_inkscape_clone_exists(svg_file_path, rule):
    """Count <use> clones referencing a source element.
    rule: {"source_id": str, "min_clones": int}
    """
    _, root = _parse_svg(svg_file_path)
    if root is None:
        return 0.0

    source_id = rule.get("source_id")
    min_clones = rule.get("min_clones", 1)

    clone_count = 0
    for elem in root.iter():
        if _tag_local(elem) == 'use':
            href = elem.get(f'{{{NS["xlink"]}}}href') or elem.get('href') or ''
            if href.lstrip('#') == source_id:
                clone_count += 1

    return 1.0 if clone_count >= min_clones else 0.0


def check_inkscape_layer_order(svg_file_path, rule):
    """Verify layer stacking order by labels (bottom to top).
    rule: {"expected_order": [str]}  # list of layer labels from bottom to top
    """
    _, root = _parse_svg(svg_file_path)
    if root is None:
        return 0.0

    expected_order = rule.get("expected_order", [])
    ink_label = f'{{{NS["inkscape"]}}}label'
    ink_groupmode = f'{{{NS["inkscape"]}}}groupmode'

    # Collect layers in document order (top-level <g> with groupmode=layer)
    layers = []
    for g in root:
        if _tag_local(g) == 'g' and g.get(ink_groupmode) == 'layer':
            label = g.get(ink_label, '')
            layers.append(label)

    # Check order matches
    if len(layers) < len(expected_order):
        return 0.0

    # Filter to only the expected labels in order
    filtered = [l for l in layers if l in expected_order]
    if filtered == expected_order:
        return 1.0

    return 0.0


def check_inkscape_group_children(svg_file_path, rule):
    """Verify elements share the same <g> parent (are grouped together).
    rule: {"element_ids": [str], "group_id": str (optional)}
    """
    _, root = _parse_svg(svg_file_path)
    if root is None:
        return 0.0

    element_ids = rule.get("element_ids", [])
    group_id = rule.get("group_id")

    if not element_ids:
        return 0.0

    # Build parent map
    parent_map = {c: p for p in root.iter() for c in p}

    parents = set()
    for eid in element_ids:
        elem = _find_element_by_id(root, eid)
        if elem is None:
            return 0.0
        parent = parent_map.get(elem)
        if parent is None:
            return 0.0
        parents.add(id(parent))

    # All elements must share the same parent
    if len(parents) != 1:
        return 0.0

    # If group_id specified, verify the parent is that group
    if group_id:
        first_elem = _find_element_by_id(root, element_ids[0])
        parent = parent_map.get(first_elem)
        if parent.get('id') != group_id:
            return 0.0

    # Parent must be a <g> element
    first_elem = _find_element_by_id(root, element_ids[0])
    parent = parent_map.get(first_elem)
    if _tag_local(parent) != 'g':
        return 0.0

    return 1.0


def check_inkscape_layer_lock(svg_file_path, rule):
    """Check sodipodi:insensitive (lock) attribute on a layer.
    rule: {"layer_label": str, "expected_locked": bool}
    """
    _, root = _parse_svg(svg_file_path)
    if root is None:
        return 0.0

    layer_label = rule.get("layer_label")
    expected_locked = rule.get("expected_locked", True)

    ink_label = f'{{{NS["inkscape"]}}}label'
    ink_groupmode = f'{{{NS["inkscape"]}}}groupmode'
    sodi_insensitive = f'{{{NS["sodipodi"]}}}insensitive'

    for g in root.iter():
        if _tag_local(g) == 'g' and g.get(ink_groupmode) == 'layer':
            if g.get(ink_label) == layer_label:
                is_locked = g.get(sodi_insensitive) == 'true'
                return 1.0 if is_locked == expected_locked else 0.0

    return 0.0


def check_inkscape_export_file_exists(result_str, rule):
    """Check exported file exists (used with vm_command_line result).
    result_str: stdout from command checking file existence
    rule: {"expected": str}
    """
    expected = rule.get("expected", "OK")
    if result_str and result_str.strip() == expected.strip():
        return 1.0
    return 0.0


# ---------------------------------------------------------------------------
# L2 Composite evaluator functions
# ---------------------------------------------------------------------------

def check_inkscape_l2_boolean_restyle(svg_file_path, rule):
    """L2 Task 2-1: Boolean union + change fill + add stroke.
    rule: {"boolean_check": {...}, "fill_check": {...}, "stroke_check": {...}}
    """
    # Sub-check 1: Boolean operation
    if check_inkscape_boolean_operation(svg_file_path, rule.get("boolean_check", {})) < 1.0:
        return 0.0
    # Sub-check 2: Fill color of result
    if check_inkscape_fill_color(svg_file_path, rule.get("fill_check", {})) < 1.0:
        return 0.0
    # Sub-check 3: Stroke on result
    if check_inkscape_stroke(svg_file_path, rule.get("stroke_check", {})) < 1.0:
        return 0.0
    return 1.0


def check_inkscape_l2_boolean_move(svg_file_path, rule):
    """L2 Task 2-2: Boolean difference + change fill color.
    rule: {"boolean_check": {...}, "fill_check": {...}}
    """
    if check_inkscape_boolean_operation(svg_file_path, rule.get("boolean_check", {})) < 1.0:
        return 0.0
    if check_inkscape_fill_color(svg_file_path, rule.get("fill_check", {})) < 1.0:
        return 0.0
    return 1.0


def check_inkscape_l2_blur_opacity(svg_file_path, rule):
    """L2 Task 2-3: Apply blur filter + set opacity + change fill.
    rule: {"filter_check": {...}, "opacity_check": {...}, "fill_check": {...}}
    """
    if check_inkscape_filter(svg_file_path, rule.get("filter_check", {})) < 1.0:
        return 0.0
    if check_inkscape_opacity(svg_file_path, rule.get("opacity_check", {})) < 1.0:
        return 0.0
    if check_inkscape_fill_color(svg_file_path, rule.get("fill_check", {})) < 1.0:
        return 0.0
    return 1.0


def check_inkscape_l2_clone_restyle(svg_file_path, rule):
    """L2 Task 2-4: Create clones + change source fill + resize document.
    rule: {"clone_check": {...}, "fill_check": {...}, "doc_check": {...}}
    """
    if check_inkscape_clone_exists(svg_file_path, rule.get("clone_check", {})) < 1.0:
        return 0.0
    if check_inkscape_fill_color(svg_file_path, rule.get("fill_check", {})) < 1.0:
        return 0.0
    if check_inkscape_document_properties(svg_file_path, rule.get("doc_check", {})) < 1.0:
        return 0.0
    return 1.0


def check_inkscape_l2_gradient_shadow(svg_file_path, rule):
    """L2 Task 2-5: Apply gradient + add drop shadow + set stroke.
    rule: {"gradient_check": {...}, "filter_check": {...}, "stroke_check": {...}}
    """
    if check_inkscape_gradient(svg_file_path, rule.get("gradient_check", {})) < 1.0:
        return 0.0
    if check_inkscape_filter(svg_file_path, rule.get("filter_check", {})) < 1.0:
        return 0.0
    if check_inkscape_stroke(svg_file_path, rule.get("stroke_check", {})) < 1.0:
        return 0.0
    return 1.0


def check_inkscape_l2_multi_transform(svg_file_path, rule):
    """L2 Task 2-6: Apply two transforms + change fill.
    rule: {"transform_check_1": {...}, "transform_check_2": {...}, "fill_check": {...}}
    """
    if check_inkscape_transform(svg_file_path, rule.get("transform_check_1", {})) < 1.0:
        return 0.0
    if check_inkscape_transform(svg_file_path, rule.get("transform_check_2", {})) < 1.0:
        return 0.0
    if check_inkscape_fill_color(svg_file_path, rule.get("fill_check", {})) < 1.0:
        return 0.0
    return 1.0


def check_inkscape_l2_layer_ops(svg_file_path, rule):
    """L2 Task 2-8: Reorder layers + rename layer + toggle visibility.
    rule: {"layer_order_check": {...}, "layer_name_check": {...}, "visibility_check": {...}}
    """
    if check_inkscape_layer_order(svg_file_path, rule.get("layer_order_check", {})) < 1.0:
        return 0.0
    if check_inkscape_layer_name(svg_file_path, rule.get("layer_name_check", {})) < 1.0:
        return 0.0
    if check_inkscape_layer_visibility(svg_file_path, rule.get("visibility_check", {})) < 1.0:
        return 0.0
    return 1.0


def check_inkscape_l2_group_transform(svg_file_path, rule):
    """L2 Task 2-9: Group elements + transform group + change fill.
    rule: {"group_check": {...}, "transform_check": {...}, "fill_check": {...}}
    transform_check.expected_transform_contains is checked on the parent <g> group
    (not on a child element), since Inkscape applies group transforms to the group node.
    """
    if check_inkscape_group_children(svg_file_path, rule.get("group_check", {})) < 1.0:
        return 0.0

    # Check transform on the parent group of the grouped elements
    _, root = _parse_svg(svg_file_path)
    if root is None:
        return 0.0
    transform_rule = rule.get("transform_check", {})
    expected_contains = transform_rule.get("expected_transform_contains", "")
    group_elem_ids = rule.get("group_check", {}).get("element_ids", [])
    if group_elem_ids and expected_contains:
        # Find the parent <g> of the first grouped element
        parent_map = {c: p for p in root.iter() for c in p}
        first_elem = _find_element_by_id(root, group_elem_ids[0])
        if first_elem is not None:
            parent = parent_map.get(first_elem)
            if parent is not None and _tag_local(parent) == 'g':
                transform = parent.get('transform', '')
                if expected_contains not in transform:
                    return 0.0
            else:
                return 0.0
        else:
            return 0.0
    elif transform_rule:
        if check_inkscape_transform(svg_file_path, transform_rule) < 1.0:
            return 0.0

    if check_inkscape_fill_color(svg_file_path, rule.get("fill_check", {})) < 1.0:
        return 0.0
    return 1.0


def check_inkscape_l2_path_stroke(svg_file_path, rule):
    """L2 Task 2-10: Object to path + dash stroke + set stroke color.
    rule: {"path_check": {...}, "dash_check": {...}, "stroke_check": {...}}
    """
    if check_inkscape_object_to_path(svg_file_path, rule.get("path_check", {})) < 1.0:
        return 0.0
    if check_inkscape_stroke_dasharray(svg_file_path, rule.get("dash_check", {})) < 1.0:
        return 0.0
    if check_inkscape_stroke(svg_file_path, rule.get("stroke_check", {})) < 1.0:
        return 0.0
    return 1.0


def check_inkscape_l2_scale_guide(svg_file_path, rule):
    """L2 Task 2-11: Change document size + add guide.
    rule: {"doc_check": {...}, "guide_check": {...}}
    """
    if check_inkscape_document_properties(svg_file_path, rule.get("doc_check", {})) < 1.0:
        return 0.0
    if check_inkscape_snap_to_grid(svg_file_path, rule.get("guide_check", {})) < 1.0:
        return 0.0
    return 1.0


def check_inkscape_l2_shadow_zorder(svg_file_path, rule):
    """L2 Task 2-12: Add drop shadow filter + change z-order + verify element count.
    rule: {"filter_check": {...}, "zorder_check": {...}, "count_check": {...}}
    """
    if check_inkscape_filter(svg_file_path, rule.get("filter_check", {})) < 1.0:
        return 0.0
    if check_inkscape_zorder(svg_file_path, rule.get("zorder_check", {})) < 1.0:
        return 0.0
    if check_inkscape_element_count(svg_file_path, rule.get("count_check", {})) < 1.0:
        return 0.0
    return 1.0


# ---------------------------------------------------------------------------
# L3 Composite evaluator functions
# ---------------------------------------------------------------------------

def check_inkscape_infographic_rebrand(svg_file_path, rule):
    """L3 Task 3-1: Multi-step infographic rebrand (recolor + restyle text + resize).
    rule: {"fill_checks": [{...}], "text_check": {...}, "doc_check": {...},
           "stroke_check": {...}}
    """
    # Check multiple fill color changes
    for fc in rule.get("fill_checks", []):
        if check_inkscape_fill_color(svg_file_path, fc) < 1.0:
            return 0.0
    # Check text style change
    if "text_check" in rule:
        if check_inkscape_text_style(svg_file_path, rule["text_check"]) < 1.0:
            return 0.0
    # Check document resize
    if "doc_check" in rule:
        if check_inkscape_document_properties(svg_file_path, rule["doc_check"]) < 1.0:
            return 0.0
    # Check stroke addition
    if "stroke_check" in rule:
        if check_inkscape_stroke(svg_file_path, rule["stroke_check"]) < 1.0:
            return 0.0
    return 1.0


def check_inkscape_icon_composition(svg_file_path, rule):
    """L3 Task 3-2: Icon composition (group + align + recolor + resize).
    rule: {"group_check": {...}, "fill_checks": [{...}], "doc_check": {...},
           "align_check": {...}}
    """
    if "group_check" in rule:
        if check_inkscape_group_children(svg_file_path, rule["group_check"]) < 1.0:
            return 0.0
    for fc in rule.get("fill_checks", []):
        if check_inkscape_fill_color(svg_file_path, fc) < 1.0:
            return 0.0
    if "doc_check" in rule:
        if check_inkscape_document_properties(svg_file_path, rule["doc_check"]) < 1.0:
            return 0.0
    if "align_check" in rule:
        if check_inkscape_align(svg_file_path, rule["align_check"]) < 1.0:
            return 0.0
    return 1.0


def check_inkscape_boolean_pipeline(svg_file_path, rule):
    """L3 Task 3-3: Boolean pipeline (multiple boolean ops + recolor + stroke).
    rule: {"boolean_checks": [{...}], "fill_check": {...}, "stroke_check": {...},
           "element_count_check": {...}}
    """
    for bc in rule.get("boolean_checks", []):
        if check_inkscape_boolean_operation(svg_file_path, bc) < 1.0:
            return 0.0
    if "fill_check" in rule:
        if check_inkscape_fill_color(svg_file_path, rule["fill_check"]) < 1.0:
            return 0.0
    if "stroke_check" in rule:
        if check_inkscape_stroke(svg_file_path, rule["stroke_check"]) < 1.0:
            return 0.0
    if "element_count_check" in rule:
        if check_inkscape_element_count(svg_file_path, rule["element_count_check"]) < 1.0:
            return 0.0
    return 1.0


def check_inkscape_layer_workflow(svg_file_path, rule):
    """L3 Task 3-4: Layer management workflow (reorder + rename + lock + visibility + add layer).
    rule: {"layer_order_check": {...}, "layer_name_check": {...},
           "lock_check": {...}, "visibility_check": {...}, "add_layer_check": {...}}
    """
    if "layer_order_check" in rule:
        if check_inkscape_layer_order(svg_file_path, rule["layer_order_check"]) < 1.0:
            return 0.0
    if "layer_name_check" in rule:
        if check_inkscape_layer_name(svg_file_path, rule["layer_name_check"]) < 1.0:
            return 0.0
    if "lock_check" in rule:
        if check_inkscape_layer_lock(svg_file_path, rule["lock_check"]) < 1.0:
            return 0.0
    if "visibility_check" in rule:
        if check_inkscape_layer_visibility(svg_file_path, rule["visibility_check"]) < 1.0:
            return 0.0
    if "add_layer_check" in rule:
        if check_inkscape_add_layer(svg_file_path, rule["add_layer_check"]) < 1.0:
            return 0.0
    return 1.0


def check_inkscape_complex_path_workflow(svg_file_path, rule):
    """L3 Task 3-5: Complex path workflow (object-to-path + filter + stroke + fill-rule).
    rule: {"path_check": {...}, "filter_check": {...}, "stroke_check": {...},
           "fill_rule_check": {...}, "fill_check": {...}}
    """
    if "path_check" in rule:
        if check_inkscape_object_to_path(svg_file_path, rule["path_check"]) < 1.0:
            return 0.0
    if "filter_check" in rule:
        if check_inkscape_filter(svg_file_path, rule["filter_check"]) < 1.0:
            return 0.0
    if "stroke_check" in rule:
        if check_inkscape_stroke(svg_file_path, rule["stroke_check"]) < 1.0:
            return 0.0
    if "fill_rule_check" in rule:
        if check_inkscape_fill_rule(svg_file_path, rule["fill_rule_check"]) < 1.0:
            return 0.0
    if "fill_check" in rule:
        if check_inkscape_fill_color(svg_file_path, rule["fill_check"]) < 1.0:
            return 0.0
    return 1.0


def check_inkscape_full_poster_workflow(svg_file_path, rule):
    """L3 Task 3-6: Full poster workflow (text + fill + gradient + doc resize + transform).
    rule: {"text_checks": [{...}], "fill_checks": [{...}], "gradient_check": {...},
           "doc_check": {...}, "transform_check": {...}}
    """
    for tc in rule.get("text_checks", []):
        if check_inkscape_text_style(svg_file_path, tc) < 1.0:
            return 0.0
    for fc in rule.get("fill_checks", []):
        if check_inkscape_fill_color(svg_file_path, fc) < 1.0:
            return 0.0
    if "gradient_check" in rule:
        if check_inkscape_gradient(svg_file_path, rule["gradient_check"]) < 1.0:
            return 0.0
    if "doc_check" in rule:
        if check_inkscape_document_properties(svg_file_path, rule["doc_check"]) < 1.0:
            return 0.0
    if "transform_check" in rule:
        if check_inkscape_transform(svg_file_path, rule["transform_check"]) < 1.0:
            return 0.0
    return 1.0


def check_inkscape_shape_composition_workflow(svg_file_path, rule):
    """L3 Task 3-7: Shape composition (boolean + group + gradient + filter + stroke).
    rule: {"boolean_check": {...}, "group_check": {...}, "gradient_check": {...},
           "filter_check": {...}, "stroke_check": {...}}
    """
    if "boolean_check" in rule:
        if check_inkscape_boolean_operation(svg_file_path, rule["boolean_check"]) < 1.0:
            return 0.0
    if "group_check" in rule:
        if check_inkscape_group_children(svg_file_path, rule["group_check"]) < 1.0:
            return 0.0
    if "gradient_check" in rule:
        if check_inkscape_gradient(svg_file_path, rule["gradient_check"]) < 1.0:
            return 0.0
    if "filter_check" in rule:
        if check_inkscape_filter(svg_file_path, rule["filter_check"]) < 1.0:
            return 0.0
    if "stroke_check" in rule:
        if check_inkscape_stroke(svg_file_path, rule["stroke_check"]) < 1.0:
            return 0.0
    return 1.0


def check_inkscape_dashboard_surgery(svg_file_path, rule):
    """L3 Task 3-8: Dashboard surgery (lock layer + recolor + delete + text edit + resize).
    rule: {"lock_check": {...}, "fill_checks": [{...}], "delete_check": {...},
           "text_check": {...}, "doc_check": {...}}
    """
    if "lock_check" in rule:
        if check_inkscape_layer_lock(svg_file_path, rule["lock_check"]) < 1.0:
            return 0.0
    for fc in rule.get("fill_checks", []):
        if check_inkscape_fill_color(svg_file_path, fc) < 1.0:
            return 0.0
    if "delete_check" in rule:
        if check_inkscape_element_deleted(svg_file_path, rule["delete_check"]) < 1.0:
            return 0.0
    if "text_check" in rule:
        if check_inkscape_text_content(svg_file_path, rule["text_check"]) < 1.0:
            return 0.0
    if "doc_check" in rule:
        if check_inkscape_document_properties(svg_file_path, rule["doc_check"]) < 1.0:
            return 0.0
    return 1.0


def check_inkscape_tiled_pattern_workflow(svg_file_path, rule):
    """L3 Task 3-9: Tiled pattern (clone + transform + fill + stroke + doc resize).
    rule: {"clone_check": {...}, "transform_check": {...}, "fill_check": {...},
           "stroke_check": {...}, "doc_check": {...}}
    """
    if "clone_check" in rule:
        if check_inkscape_clone_exists(svg_file_path, rule["clone_check"]) < 1.0:
            return 0.0
    if "transform_check" in rule:
        if check_inkscape_transform(svg_file_path, rule["transform_check"]) < 1.0:
            return 0.0
    if "fill_check" in rule:
        if check_inkscape_fill_color(svg_file_path, rule["fill_check"]) < 1.0:
            return 0.0
    if "stroke_check" in rule:
        if check_inkscape_stroke(svg_file_path, rule["stroke_check"]) < 1.0:
            return 0.0
    if "doc_check" in rule:
        if check_inkscape_document_properties(svg_file_path, rule["doc_check"]) < 1.0:
            return 0.0
    return 1.0


def check_inkscape_dual_export_poster(svg_file_path, rule):
    """L3 Task 3-10: Dual export poster (gradient + text + fill + stroke + doc resize).
    rule: {"gradient_check": {...}, "text_checks": [{...}], "fill_checks": [{...}],
           "stroke_check": {...}, "doc_check": {...}}
    """
    if "gradient_check" in rule:
        if check_inkscape_gradient(svg_file_path, rule["gradient_check"]) < 1.0:
            return 0.0
    for tc in rule.get("text_checks", []):
        if check_inkscape_text_style(svg_file_path, tc) < 1.0:
            return 0.0
    for fc in rule.get("fill_checks", []):
        if check_inkscape_fill_color(svg_file_path, fc) < 1.0:
            return 0.0
    if "stroke_check" in rule:
        if check_inkscape_stroke(svg_file_path, rule["stroke_check"]) < 1.0:
            return 0.0
    if "doc_check" in rule:
        if check_inkscape_document_properties(svg_file_path, rule["doc_check"]) < 1.0:
            return 0.0
    return 1.0


# ---------------------------------------------------------------------------
# Interactive composite evaluator functions
# ---------------------------------------------------------------------------


def check_interactive_inkscape_ii01(svg_file_path, rule):
    """II-01: Clarified infographic rebrand after ambiguous initial request.
    rule: {"text_checks": [{...}], "fill_checks": [{...}]}
    """
    for tc in rule.get("text_checks", []):
        if check_inkscape_text_content(svg_file_path, tc) < 1.0:
            return 0.0
    for fc in rule.get("fill_checks", []):
        if check_inkscape_fill_color(svg_file_path, fc) < 1.0:
            return 0.0
    return 1.0


def check_interactive_inkscape_ii02(svg_file_path, rule):
    """II-02: Interrupted poster revision with late canvas constraint.
    rule: {"text_checks": [{...}], "fill_checks": [{...}], "doc_check": {...}}
    """
    for tc in rule.get("text_checks", []):
        if check_inkscape_text_content(svg_file_path, tc) < 1.0:
            return 0.0
    for fc in rule.get("fill_checks", []):
        if check_inkscape_fill_color(svg_file_path, fc) < 1.0:
            return 0.0
    if "doc_check" in rule:
        if check_inkscape_document_properties(svg_file_path, rule["doc_check"]) < 1.0:
            return 0.0
    return 1.0


def check_interactive_inkscape_ii03(svg_file_path, rule):
    """II-03: Progressive icon refinement across multiple feedback rounds.
    rule: {"fill_checks": [{...}], "text_check": {...}}
    """
    for fc in rule.get("fill_checks", []):
        if check_inkscape_fill_color(svg_file_path, fc) < 1.0:
            return 0.0
    if "text_check" in rule:
        if check_inkscape_text_content(svg_file_path, rule["text_check"]) < 1.0:
            return 0.0
    return 1.0


def check_interactive_inkscape_ii04(svg_file_path, rule):
    """II-04: User correction after targeting the wrong object initially.
    rule: {"fill_check": {...}, "delete_check": {...}, "zorder_check": {...}}
    """
    if "fill_check" in rule:
        if check_inkscape_fill_color(svg_file_path, rule["fill_check"]) < 1.0:
            return 0.0
    if "delete_check" in rule:
        if check_inkscape_element_deleted(svg_file_path, rule["delete_check"]) < 1.0:
            return 0.0
    if "zorder_check" in rule:
        if check_inkscape_zorder(svg_file_path, rule["zorder_check"]) < 1.0:
            return 0.0
    return 1.0


def check_interactive_inkscape_ii05(svg_file_path, rule):
    """II-05: Requirement change from internal version to public release.
    rule: {"text_check": {...}, "delete_checks": [{...}]}
    """
    if "text_check" in rule:
        if check_inkscape_text_content(svg_file_path, rule["text_check"]) < 1.0:
            return 0.0
    for dc in rule.get("delete_checks", []):
        if check_inkscape_element_deleted(svg_file_path, dc) < 1.0:
            return 0.0
    return 1.0


def check_interactive_inkscape_ii06(svg_file_path, rule):
    """II-06: Multi-stage layer handoff workflow.
    rule: {"layer_order_check": {...}, "layer_name_check": {...},
           "visibility_check": {...}, "fill_check": {...}}
    """
    if "layer_order_check" in rule:
        if check_inkscape_layer_order(svg_file_path, rule["layer_order_check"]) < 1.0:
            return 0.0
    if "layer_name_check" in rule:
        if check_inkscape_layer_name(svg_file_path, rule["layer_name_check"]) < 1.0:
            return 0.0
    if "visibility_check" in rule:
        if check_inkscape_layer_visibility(svg_file_path, rule["visibility_check"]) < 1.0:
            return 0.0
    if "fill_check" in rule:
        if check_inkscape_fill_color(svg_file_path, rule["fill_check"]) < 1.0:
            return 0.0
    return 1.0
