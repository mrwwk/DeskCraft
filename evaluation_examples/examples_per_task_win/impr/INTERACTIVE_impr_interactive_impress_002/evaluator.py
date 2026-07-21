import logging
import os
import re
import zipfile
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional

logger = logging.getLogger("desktopenv.metric.general")


def check_summary_slide(result: str, rules: Dict[str, object]) -> float:
    """
    Check that the requested summary slide was added at the end of the deck.

    The result parameter is a local file path to the PPTX (pulled from VM by vm_file getter).
    This evaluator reads the PPTX as a zip/xml archive, checks the final slide text,
    and optionally verifies a minimum slide count.

    Args:
        result: Path to PPTX file (from vm_file getter) or raw text string (fallback).
        rules: Dict with "last_slide_include" and optional "min_slide_count".

    Returns:
        1.0 if the last slide contains all required strings and the slide count
        is sufficient, else 0.0.
    """
    if result is None:
        logger.warning("Result is None, returning 0.0")
        return 0.0

    required_last_slide = rules.get("last_slide_include", [])
    min_slide_count = rules.get("min_slide_count")

    slide_texts = _extract_pptx_slide_texts(result)
    if slide_texts is None:
        logger.info("check_summary_slide: could not extract slide text")
        return 0.0

    if min_slide_count is not None and len(slide_texts) < int(min_slide_count):
        logger.info(
            f"check_summary_slide: slide_count={len(slide_texts)}, "
            f"expected_at_least={min_slide_count}"
        )
        return 0.0

    last_slide_text = slide_texts[-1] if slide_texts else ""
    if all(text in last_slide_text for text in required_last_slide):
        return 1.0

    logger.info(
        f"check_summary_slide: required_last_slide={required_last_slide}, "
        f"last_slide_preview={last_slide_text[:200] if last_slide_text else '(empty)'}"
    )
    return 0.0


def _extract_pptx_slide_texts(file_path: str) -> Optional[List[str]]:
    """
    Extract text from each slide in slide order using only the Python standard library.

    Returns a list where each item is the concatenated text of one slide, or None
    if extraction fails.
    """
    if not os.path.isfile(file_path):
        logger.warning(f"File not found: {file_path}")
        return None

    try:
        with zipfile.ZipFile(file_path) as pptx:
            slide_names = [
                name for name in pptx.namelist()
                if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
            ]
            slide_names.sort(key=lambda name: int(re.search(r"slide(\d+)\.xml", name).group(1)))

            slide_texts = []
            for slide_name in slide_names:
                root = ET.fromstring(pptx.read(slide_name))
                parts = [
                    element.text
                    for element in root.iter()
                    if element.tag.endswith("}t") and element.text
                ]
                slide_texts.append(" ".join(parts))
            return slide_texts
    except Exception as e:
        logger.warning(f"Failed to read PPTX from {file_path}: {e}")
        return None
