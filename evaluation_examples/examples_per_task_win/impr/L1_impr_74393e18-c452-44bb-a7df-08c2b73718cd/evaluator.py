"""
Evaluator for: "Make all title text bold AND italic across ALL slides."

The deck produced by LibreOffice does not preserve reliable title placeholder
metadata, so this evaluator falls back to visual title detection instead of
checking only the first text box on each slide.
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


def check_all_titles_bold_italic(result_path, expected=None, **options):
    """Return 1.0 when every inferred title run is bold AND italic."""
    del expected

    try:
        with zipfile.ZipFile(result_path) as pptx:
            slide_names = _slide_names(pptx)
            if not slide_names:
                logger.warning("No slides found in PPTX")
                return 0.0

            found_any_title = False
            for slide_idx, slide_name in enumerate(slide_names, start=1):
                root = ET.fromstring(pptx.read(slide_name))
                slide_width, slide_height = _presentation_size(pptx)
                shapes = _text_shapes(root, slide_width, slide_height)
                title_shapes = _find_title_shapes(shapes)

                if not title_shapes:
                    logger.info("Slide %d: no title-like text shape found", slide_idx)
                    return 0.0

                found_any_title = True
                for shape in title_shapes:
                    for run in shape["runs"]:
                        text = run["text"].strip()
                        if not text:
                            continue
                        if not run["bold"] or not run["italic"]:
                            logger.info(
                                "Slide %d title check failed: text='%s', bold=%s, italic=%s",
                                slide_idx,
                                text[:80],
                                run["bold"],
                                run["italic"],
                            )
                            return 0.0

            if not found_any_title:
                logger.warning("No title-like text found in presentation")
                return 0.0
            logger.info("All inferred title text is bold and italic")
            return 1.0
    except Exception as e:
        logger.error("Failed to evaluate title formatting: %s", e)
        return 0.0


def _slide_names(pptx):
    names = [
        name
        for name in pptx.namelist()
        if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
    ]
    return sorted(names, key=lambda name: int(re.search(r"slide(\d+)\.xml", name).group(1)))


def _presentation_size(pptx):
    try:
        root = ET.fromstring(pptx.read("ppt/presentation.xml"))
        sld_sz = root.find("p:sldSz", NS)
        if sld_sz is not None:
            return int(sld_sz.get("cx", "12192000")), int(sld_sz.get("cy", "6858000"))
    except Exception:
        pass
    return 12192000, 6858000


def _text_shapes(slide_root, slide_width, slide_height):
    shapes = []
    for sp in slide_root.findall(".//p:sp", NS):
        runs = []
        for run in sp.findall(".//a:r", NS):
            text = "".join(t.text or "" for t in run.findall(".//a:t", NS))
            if not text.strip():
                continue
            r_pr = run.find("a:rPr", NS)
            runs.append(
                {
                    "text": text,
                    "bold": r_pr is not None and r_pr.get("b") in ("1", "true"),
                    "italic": r_pr is not None and r_pr.get("i") in ("1", "true"),
                    "size": _font_size_pt(r_pr),
                }
            )

        text = "".join(run["text"] for run in runs).strip()
        if not text:
            continue

        xfrm = sp.find(".//a:xfrm", NS)
        off = xfrm.find("a:off", NS) if xfrm is not None else None
        ext = xfrm.find("a:ext", NS) if xfrm is not None else None
        y = int(off.get("y", "0")) if off is not None else 0
        h = int(ext.get("cy", "0")) if ext is not None else 0

        ph = sp.find(".//p:nvPr/p:ph", NS)
        ph_type = ph.get("type") if ph is not None else ""
        sizes = [run["size"] for run in runs if run["size"] is not None]

        shapes.append(
            {
                "text": text,
                "runs": runs,
                "y": y,
                "height": h,
                "center_y_ratio": (y + h / 2) / slide_height if slide_height else 0,
                "placeholder_type": ph_type,
                "max_size": max(sizes) if sizes else 0,
                "avg_size": sum(sizes) / len(sizes) if sizes else 0,
            }
        )
    return shapes


def _font_size_pt(r_pr):
    if r_pr is None:
        return None
    size = r_pr.get("sz")
    if not size:
        return None
    try:
        return int(size) / 100.0
    except ValueError:
        return None


def _find_title_shapes(shapes):
    placeholder_titles = [
        shape
        for shape in shapes
        if shape["placeholder_type"] in ("title", "ctrTitle")
    ]
    if placeholder_titles:
        return placeholder_titles

    meaningful = [shape for shape in shapes if not _is_minor_label(shape["text"])]
    if not meaningful:
        meaningful = shapes

    upper = [shape for shape in meaningful if shape["center_y_ratio"] <= 0.58]
    pool = upper or meaningful
    largest = max((shape["max_size"] for shape in pool), default=0)
    if largest <= 0:
        return []

    min_size = max(24.0, largest * 0.72)
    title_shapes = [
        shape
        for shape in pool
        if shape["max_size"] >= min_size and not _is_minor_label(shape["text"])
    ]

    if title_shapes:
        return title_shapes

    return [max(pool, key=lambda shape: (shape["max_size"], -shape["y"]))]


def _is_minor_label(text):
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return True
    if re.fullmatch(r"\d{1,2}", normalized):
        return True
    if re.fullmatch(r"chapter\s+\d{1,2}(?:\s*[•:-].*)?", normalized, re.I):
        return True
    if len(normalized) <= 3 and re.search(r"\d", normalized):
        return True
    return False
