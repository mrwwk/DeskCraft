import logging
import re
from docx import Document
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.shared import RGBColor

logger = logging.getLogger("desktopenv.metrics.writ")

FOOTER_TEXT = "This proposal requires executive approval before implementation."
HEADING_TEXTS = {"Budget", "Expected Benefits", "Background", "Objectives", "Scope of Work"}
OLD_TERMS = ["Q1 2025", "Q2-Q3 2025", "Q4 2025", "Q1 2026"]
NEW_TERMS = ["First Quarter 2025", "Second-Third Quarter 2025", "Fourth Quarter 2025", "First Quarter 2026"]
DARK_BLUE = RGBColor(0x00, 0x00, 0x8B)


def _nonempty_paragraphs(doc):
    return [p for p in doc.paragraphs if p.text.strip()]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _is_heading(paragraph) -> bool:
    return _normalize(paragraph.text) in HEADING_TEXTS


def evaluate_proposal_docx(result_path, expected=None, **options):
    if not result_path:
        return 0.0

    try:
        doc = Document(result_path)
    except Exception as exc:
        logger.error("cannot open proposal docx: %s", exc)
        return 0.0

    paragraphs = _nonempty_paragraphs(doc)
    if not paragraphs:
        return 0.0

    checks = [
        _check_text_updates(paragraphs),
        _check_title_format(paragraphs[0]),
        _check_heading_colors(paragraphs),
        _check_body_font(paragraphs),
        _check_footer(paragraphs),
    ]
    return sum(1.0 for passed in checks if passed) / len(checks)


def _check_text_updates(paragraphs) -> bool:
    full_text = "\n".join(p.text for p in paragraphs)
    if any(term in full_text for term in OLD_TERMS):
        return False
    return all(term in full_text for term in NEW_TERMS)


def _check_title_format(paragraph) -> bool:
    if paragraph.paragraph_format.alignment != WD_PARAGRAPH_ALIGNMENT.CENTER:
        return False
    text_runs = [run for run in paragraph.runs if run.text.strip()]
    if not text_runs:
        return False
    if not all(run.bold for run in text_runs):
        return False
    return any(run.font.size and abs(run.font.size.pt - 20) < 0.5 for run in text_runs)


def _check_heading_colors(paragraphs) -> bool:
    heading_paragraphs = [p for p in paragraphs if _is_heading(p)]
    if not heading_paragraphs:
        return False
    for paragraph in heading_paragraphs:
        text_runs = [run for run in paragraph.runs if run.text.strip()]
        if not text_runs:
            return False
        for run in text_runs:
            if run.font.color.rgb != DARK_BLUE:
                return False
    return True


def _check_body_font(paragraphs) -> bool:
    candidate_paragraphs = [p for p in paragraphs if not _is_heading(p) and _normalize(p.text) != FOOTER_TEXT]
    total_runs = 0
    mismatched_runs = 0
    for paragraph in candidate_paragraphs:
        for run in paragraph.runs:
            if not run.text.strip():
                continue
            total_runs += 1
            if run.font.name is not None and run.font.name != 'Georgia':
                mismatched_runs += 1
    if total_runs == 0:
        return False
    return mismatched_runs == 0


def _check_footer(paragraphs) -> bool:
    return _normalize(paragraphs[-1].text) == FOOTER_TEXT
