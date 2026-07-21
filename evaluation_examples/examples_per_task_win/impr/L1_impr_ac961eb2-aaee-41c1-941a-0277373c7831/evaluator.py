"""
Evaluator for: On slide 1, change all text to Times New Roman font.

This is intentionally scoped to the requested slide and property. It avoids
whole-presentation golden-file comparison, which is too brittle for Impress.
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


def check_slide1_text_font_times_new_roman(result_path, expected=None, **options):
    """Return 1.0 when every non-empty text run on slide 1 uses Times New Roman."""
    del expected

    target_font = _normalize_font(options.get("target_font", "Times New Roman"))

    try:
        with zipfile.ZipFile(result_path) as pptx:
            slide_name = "ppt/slides/slide1.xml"
            if slide_name not in pptx.namelist():
                logger.error("Slide XML not found: %s", slide_name)
                return 0.0

            root = ET.fromstring(pptx.read(slide_name))
            runs = _text_runs(root)
            if not runs:
                logger.error("No non-empty text runs found on slide 1")
                return 0.0

            for run in runs:
                fonts = [_normalize_font(font) for font in run["fonts"] if font]
                if target_font not in fonts:
                    logger.info(
                        "Slide 1 run '%s' has fonts=%s, expected %s",
                        run["text"][:80],
                        run["fonts"],
                        options.get("target_font", "Times New Roman"),
                    )
                    return 0.0

            logger.info("All %d slide 1 text runs use Times New Roman", len(runs))
            return 1.0
    except Exception as e:
        logger.error("Failed to evaluate slide 1 text font: %s", e)
        return 0.0


def _text_runs(slide_root):
    runs = []
    for run in slide_root.findall(".//a:r", NS):
        text = "".join(node.text or "" for node in run.findall(".//a:t", NS))
        if not text.strip():
            continue

        r_pr = run.find("a:rPr", NS)
        fonts = []
        if r_pr is not None:
            for tag in ("a:latin", "a:ea", "a:cs"):
                node = r_pr.find(tag, NS)
                if node is not None and node.get("typeface"):
                    fonts.append(node.get("typeface"))

        runs.append({"text": text, "fonts": fonts})
    return runs


def _normalize_font(font_name):
    return re.sub(r"\s+", " ", str(font_name)).strip().lower()
