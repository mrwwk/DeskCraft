"""
Evaluator for: On slide 1, make the title bold, 48pt, and underlined.

This check reads the slide XML directly so font-size units are unambiguous:
OpenXML stores text size in hundredths of a point, so 48pt is sz="4800".
The title is identified by the expected title text instead of by largest font
size, avoiding false matches against subtitle or decorative text runs.
"""
import logging
import re
import zipfile
import xml.etree.ElementTree as ET

logger = logging.getLogger("desktopenv.metric.slides")

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
}


def check_slide1_title_format(result_path, rules, **options):
    """Return 1.0 when the target slide title is bold, underlined, and 48pt."""
    del options

    rules = rules or {}
    slide_index = int(rules.get("slide_index", 0))
    title_text = _normalize_text(rules.get("title_text", "BUSINESS PLAN"))
    expected_size = _expected_size_centipoints(rules)
    check_bold = bool(rules.get("check_bold", True))
    check_underline = bool(rules.get("check_underline", True))

    try:
        with zipfile.ZipFile(result_path) as pptx:
            slide_name = f"ppt/slides/slide{slide_index + 1}.xml"
            if slide_name not in pptx.namelist():
                logger.error("Slide XML not found: %s", slide_name)
                return 0.0

            root = ET.fromstring(pptx.read(slide_name))
            title_shape = _find_shape_by_text(root, title_text)
            if title_shape is None:
                logger.error("Could not find title text '%s' on slide %d", title_text, slide_index + 1)
                return 0.0

            runs = _text_runs(title_shape)
            if not runs:
                logger.error("No non-empty text runs found in title shape")
                return 0.0

            for run in runs:
                text = run["text"].strip()
                if check_bold and not run["bold"]:
                    logger.info("Title run '%s' is not bold", text[:80])
                    return 0.0
                if check_underline and not run["underline"]:
                    logger.info("Title run '%s' is not underlined", text[:80])
                    return 0.0
                if run["size"] != expected_size:
                    logger.info(
                        "Title run '%s' has size %s, expected %s",
                        text[:80],
                        run["size"],
                        expected_size,
                    )
                    return 0.0

            logger.info(
                "Slide %d title '%s' is bold, underlined, and %.1fpt",
                slide_index + 1,
                title_text,
                expected_size / 100.0,
            )
            return 1.0
    except Exception as e:
        logger.error("Failed to evaluate PPTX title formatting: %s", e)
        return 0.0


def _expected_size_centipoints(rules):
    if "expected_font_size_pt" in rules:
        return int(round(float(rules["expected_font_size_pt"]) * 100))

    raw_size = rules.get("expected_font_size", 4800)
    try:
        raw_size = float(raw_size)
    except (TypeError, ValueError):
        return 4800

    # Backward compatibility: old tasks used OpenXML centipoints (4800).
    # If an EMU value is supplied, convert it to points and then centipoints.
    if raw_size > 10000:
        return int(round((raw_size / 12700.0) * 100))
    return int(round(raw_size))


def _find_shape_by_text(slide_root, expected_text):
    candidates = []
    for shape in slide_root.findall(".//p:sp", NS):
        shape_text = _normalize_text(
            "".join(text.text or "" for text in shape.findall(".//a:t", NS))
        )
        if shape_text == expected_text:
            return shape
        if expected_text and expected_text in shape_text:
            candidates.append(shape)
    return candidates[0] if candidates else None


def _text_runs(shape):
    runs = []
    for run in shape.findall(".//a:r", NS):
        text = "".join(node.text or "" for node in run.findall(".//a:t", NS))
        if not text.strip():
            continue
        r_pr = run.find("a:rPr", NS)
        runs.append(
            {
                "text": text,
                "bold": r_pr is not None and r_pr.get("b") in ("1", "true"),
                "underline": r_pr is not None and r_pr.get("u") not in (None, "none"),
                "size": _run_size_centipoints(r_pr),
            }
        )
    return runs


def _run_size_centipoints(r_pr):
    if r_pr is None:
        return None
    size = r_pr.get("sz")
    if not size:
        return None
    try:
        return int(size)
    except ValueError:
        return None


def _normalize_text(text):
    return re.sub(r"\s+", " ", str(text)).strip()
