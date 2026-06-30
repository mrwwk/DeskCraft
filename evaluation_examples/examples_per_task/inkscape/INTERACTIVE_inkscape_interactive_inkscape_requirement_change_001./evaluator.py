"""
Inkscape evaluator functions for interactive_inkscape_requirement_change_001.

Contains only the functions referenced by evaluator.func:
  - check_interactive_inkscape_ii05 (SVG content check)
  - check_inkscape_export_file_exists (PNG export check, revised)

All other functions from the shared inkscape.py module are omitted for minimality.
"""

import os
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

for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _find_element_by_id(root, element_id):
    """Find element by id attribute across all elements."""
    for elem in root.iter():
        if elem.get('id') == element_id:
            return elem
    return None


def _parse_svg(svg_file_path):
    """Parse SVG file and return (tree, root). Returns (None, None) on error."""
    try:
        tree = ET.parse(svg_file_path)
        return tree, tree.getroot()
    except Exception:
        return None, None


# ---------------------------------------------------------------------------
# L1 atomic check functions (needed by check_interactive_inkscape_ii05)
# ---------------------------------------------------------------------------

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

    actual_text = ''.join(elem.itertext()).strip()

    if actual_text == expected_text:
        return 1.0
    return 0.0


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


# ---------------------------------------------------------------------------
# Interactive composite evaluator (metric 0)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# PNG export check (metric 1, revised)
# ---------------------------------------------------------------------------

def check_inkscape_export_file_exists(png_path, expected=None, **options):
    """Check exported PNG file exists and has correct dimensions.

    This revised version replaces the original string-matching logic that relied
    on vm_command_line output.  It now receives the actual PNG file path from a
    vm_file result getter and:
      - verifies the file exists on disk (existence is already implied when
        vm_file succeeds, but we double-check defensively)
      - if expected provides "expected_width", opens the PNG with PIL and
        validates that image.width equals the expected value

    Backward compatibility: if png_path does not look like a real file path
    (e.g. it is a short output string from an old vm_command_line result),
    this falls back to the original string-comparison behaviour when expected
    contains an "expected" key.
    """
    if not png_path:
        return 0.0

    # ---- backward-compat: vm_command_line string result ----
    if isinstance(png_path, str) and not os.path.isfile(png_path) and len(png_path.strip()) < 256:
        if expected and isinstance(expected, dict) and "expected" in expected:
            if png_path.strip() == expected["expected"].strip():
                # Old-style "OK" check – width was never verified in this path
                return 1.0
        return 0.0

    # ---- primary path: vm_file result (local PNG path) ----
    if not os.path.isfile(png_path):
        return 0.0

    # Check width if specified in expected rules
    if expected and isinstance(expected, dict):
        expected_width = expected.get("expected_width")
        if expected_width is not None:
            try:
                from PIL import Image
                with Image.open(png_path) as img:
                    if img.width != int(expected_width):
                        return 0.0
            except Exception:
                return 0.0

    return 1.0
