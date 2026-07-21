"""Targeted evaluator for the Van Gogh slide-formatting task."""

import posixpath
import re
import zipfile
from xml.etree import ElementTree as ET


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}


def _slide_count(zf):
    return len([n for n in zf.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)])


def _slide_root(zf, slide_index):
    slide_no = slide_index + 1
    return ET.fromstring(zf.read(f"ppt/slides/slide{slide_no}.xml"))


def _shape_text(shape):
    return "".join(t.text or "" for t in shape.findall(".//a:t", NS)).strip()


def _matching_shapes(root, keywords):
    lowered = [kw.lower() for kw in keywords]
    matches = []
    for shape in root.findall(".//p:sp", NS):
        text = _shape_text(shape)
        if text and any(kw in text.lower() for kw in lowered):
            matches.append(shape)
    return matches


def _nonempty_run_props(shape):
    for paragraph in shape.findall(".//a:p", NS):
        for run in paragraph.findall("./a:r", NS):
            text = "".join(t.text or "" for t in run.findall(".//a:t", NS)).strip()
            if not text:
                continue
            rpr = run.find("./a:rPr", NS)
            if rpr is not None:
                yield text, rpr


def _run_color(rpr):
    color = rpr.find(".//a:srgbClr", NS)
    return color.get("val", "").upper() if color is not None else ""


def _all_runs_match(shape, *, color=None, italic=None, bold=None, underline=None):
    runs = list(_nonempty_run_props(shape))
    if not runs:
        return False

    for _, rpr in runs:
        if color is not None and _run_color(rpr) != color.upper():
            return False
        if italic is not None and (rpr.get("i") == "1") != italic:
            return False
        if bold is not None and (rpr.get("b") == "1") != bold:
            return False
        if underline is not None and not rpr.get("u"):
            return False
    return True


def _normalized(text):
    return " ".join(text.split()).lower()


def _slide_notes(zf, slide_index):
    slide_no = slide_index + 1
    rels_path = f"ppt/slides/_rels/slide{slide_no}.xml.rels"
    if rels_path not in zf.namelist():
        return ""

    rels_root = ET.fromstring(zf.read(rels_path))
    for rel in rels_root.findall("./rel:Relationship", NS):
        target = rel.get("Target", "")
        if "notesSlides" not in target:
            continue
        notes_path = posixpath.normpath(posixpath.join("ppt/slides", target))
        if notes_path in zf.namelist():
            notes_root = ET.fromstring(zf.read(notes_path))
            return " ".join(t.text or "" for t in notes_root.findall(".//a:t", NS))
    return ""


def _get_single_target_shape(result_path, target_slide, keywords):
    with zipfile.ZipFile(result_path) as zf:
        if _slide_count(zf) <= target_slide:
            return None
        root = _slide_root(zf, target_slide)
        matches = _matching_shapes(root, keywords)
        if len(matches) != 1:
            return None
        return matches[0]


def check_slide5_body_format(result_path, expected=None, **options):
    """Check Slide 5 body text is entirely dark red and italic."""
    try:
        target_slide = options.get("target_slide", 4)  # 0-indexed: 4 = Slide 5
        target_color = options.get("target_color_rgb", "8B0000")
        keywords = options.get("body_text_keywords", ["decade of transformation", "artistic periods"])
        shape = _get_single_target_shape(result_path, target_slide, keywords)
        if shape is None:
            return 0.0
        return 1.0 if _all_runs_match(shape, color=target_color, italic=True) else 0.0
    except Exception:
        return 0.0


def check_slide4_title_format(result_path, expected=None, **options):
    """Check the Slide 4 title shape is entirely bold and underlined."""
    try:
        target_slide = options.get("target_slide", 3)  # 0-indexed: 3 = Slide 4
        keywords = options.get("title_keywords", ["Zundert", "Canvas"])
        shape = _get_single_target_shape(result_path, target_slide, keywords)
        if shape is None:
            return 0.0
        return 1.0 if _all_runs_match(shape, bold=True, underline=True) else 0.0
    except Exception:
        return 0.0


def check_slide4_note_content(result_path, expected=None, **options):
    """Check Slide 4 contains the requested speaker note."""
    try:
        target_slide = options.get("target_slide", 3)  # 0-indexed: 3 = Slide 4
        expected_note = options.get(
            "expected_note",
            "Van Gogh began his artistic career at 27 and produced over 860 oil paintings in just 10 years.",
        )
        with zipfile.ZipFile(result_path) as zf:
            if _slide_count(zf) <= target_slide:
                return 0.0
            actual_note = _slide_notes(zf, target_slide)
        return 1.0 if _normalized(expected_note) in _normalized(actual_note) else 0.0
    except Exception:
        return 0.0
