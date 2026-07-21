"""
Evaluator for Meeting_L3_08.docx formatting task.

Checks all 6 requirements from the task instruction:
  1. Title (first paragraph) is centered, 18pt, bold.
  2. Attendees list paragraph is center-aligned.
  3. All section headings are underlined and bold.
  4. All action item lines (starting with names + colon) are bold.
  5. All body text font is set to "Arial".
  6. Required footer text is present at the document end.
"""
import logging
import re

from docx import Document
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

logger = logging.getLogger("desktopenv.metric.docs")

# Section heading keywords commonly found in meeting documents
HEADING_KEYWORDS = [
    "agenda", "minutes", "discussion", "action item", "action items",
    "report", "update", "review", "planning", "budget", "schedule",
    "project", "status", "meeting", "introduction", "conclusion",
    "summary", "note", "attendee", "attendees", "objective", "goal",
    "topic", "item", "old business", "new business", "announcement",
    "opening", "closing", "approval", "motion", "vote", "decision",
    "follow-up", "follow up", "next steps", "next meeting",
    "present", "absent", "apologies", "call to order", "adjourn",
]

# Pattern for action items: starts with a name (capitalized word(s)) followed by colon
ACTION_ITEM_PATTERN = re.compile(
    r'^\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\s*:.*',
)

REQUIRED_FOOTER = (
    "Recorded by: Meeting Secretary | Distribution: All attendees + Board"
)


def evaluate_meeting_docx(result_path, expected=None, **options):
    """
    Evaluate a .docx file against all 6 formatting requirements for
    Meeting_L3_08.docx.

    Args:
        result_path: Local path to the agent's output .docx file.
        expected: Not used (expected is null in task config).
        **options: Reserved for future threshold/rule overrides.

    Returns:
        float: Score between 0.0 and 1.0 (average of 6 binary checks).
    """
    if not result_path:
        logger.warning("result_path is empty or None")
        return 0.0

    try:
        doc = Document(result_path)
    except Exception as e:
        logger.error(f"Failed to open document {result_path}: {e}")
        return 0.0

    paragraphs = doc.paragraphs
    non_empty = [p for p in paragraphs if p.text.strip()]

    if not non_empty:
        logger.warning("Document has no non-empty paragraphs")
        return 0.0

    checks = [
        _check_title_formatting(non_empty),
        _check_attendees_centered(non_empty),
        _check_section_headings_bold_underline(non_empty),
        _check_action_items_bold(non_empty),
        _check_font_arial(paragraphs),
        _check_footer_text(non_empty),
    ]

    passed = sum(1 for c in checks if c)
    score = passed / len(checks)
    logger.info(
        f"evaluate_meeting_docx: {passed}/{len(checks)} checks passed, "
        f"score={score:.2f}, details={checks}"
    )
    return score


def _check_title_formatting(non_empty):
    """Check 1: First paragraph is centered, 18pt, and bold."""
    first = non_empty[0]

    # Check alignment
    align_ok = (
        first.paragraph_format.alignment == WD_PARAGRAPH_ALIGNMENT.CENTER
    )
    if not align_ok:
        logger.info("Check 1 FAIL: title not centered")
        return False

    # Check formatting on runs in the first paragraph
    if not first.runs:
        logger.info("Check 1 FAIL: title paragraph has no runs")
        return False

    # All runs in title should be bold, at least one should be 18pt
    bold_ok = all(run.bold for run in first.runs if run.text.strip())
    size_ok = any(
        run.font.size and run.font.size.pt == 18
        for run in first.runs if run.text.strip()
    )

    if not bold_ok:
        logger.info("Check 1 FAIL: title not bold on all runs")
        return False
    if not size_ok:
        logger.info("Check 1 FAIL: title not 18pt on any run")
        return False

    logger.info("Check 1 PASS: title centered, 18pt, bold")
    return True


def _check_attendees_centered(non_empty):
    """Check 2: Attendees list paragraph is center-aligned."""
    attendees_keywords = ["attendee", "attend"]

    for p in non_empty:
        text_lower = p.text.lower()
        if any(kw in text_lower for kw in attendees_keywords):
            centered = (
                p.paragraph_format.alignment
                == WD_PARAGRAPH_ALIGNMENT.CENTER
            )
            if centered:
                logger.info("Check 2 PASS: attendees paragraph centered")
            else:
                logger.info("Check 2 FAIL: attendees paragraph not centered")
            return centered

    # If no explicit attendees paragraph found, check if the second
    # non-empty paragraph is centered (common layout: title then attendees)
    if len(non_empty) >= 2:
        second = non_empty[1]
        centered = (
            second.paragraph_format.alignment
            == WD_PARAGRAPH_ALIGNMENT.CENTER
        )
        if centered:
            logger.info(
                "Check 2 PASS: second paragraph centered "
                "(inferred as attendees)"
            )
        else:
            logger.info(
                "Check 2 FAIL: second paragraph not centered "
                "(inferred as attendees)"
            )
        return centered

    logger.info("Check 2 FAIL: no attendees paragraph found")
    return False


def _check_section_headings_bold_underline(non_empty):
    """Check 3: All section headings are underlined and bold."""
    heading_paragraphs = []

    for p in non_empty[1:]:  # skip title
        text = p.text.strip()
        text_lower = text.lower()

        is_heading = False
        # Check if text matches any heading keyword
        for kw in HEADING_KEYWORDS:
            if text_lower.startswith(kw) or (
                len(text.split()) <= 4 and kw in text_lower
            ):
                is_heading = True
                break

        # Also treat short, all-caps lines as potential headings
        if not is_heading and len(text) < 60 and text.isupper():
            is_heading = True

        # Treat lines that look like a section marker (e.g., "1. Topic")
        if not is_heading and re.match(r'^[\dIVX]+[\.\)]\s+\w+', text):
            is_heading = True

        if is_heading:
            heading_paragraphs.append(p)

    if not heading_paragraphs:
        # No headings found — vacuously true
        logger.info("Check 3 PASS: no section headings detected (vacuously true)")
        return True

    for h in heading_paragraphs:
        for run in h.runs:
            if not run.text.strip():
                continue
            if not run.bold:
                logger.info(
                    f"Check 3 FAIL: heading not bold: '{h.text[:50]}'"
                )
                return False
            if not run.underline:
                logger.info(
                    f"Check 3 FAIL: heading not underlined: '{h.text[:50]}'"
                )
                return False

    logger.info(
        f"Check 3 PASS: {len(heading_paragraphs)} heading(s) bold+underline"
    )
    return True


def _check_action_items_bold(non_empty):
    """Check 4: All action item lines (name: ...) are bold."""
    action_paragraphs = []

    for p in non_empty:
        if ACTION_ITEM_PATTERN.match(p.text):
            action_paragraphs.append(p)

    if not action_paragraphs:
        # No action items — vacuously true
        logger.info(
            "Check 4 PASS: no action items detected (vacuously true)"
        )
        return True

    for ap in action_paragraphs:
        for run in ap.runs:
            if not run.text.strip():
                continue
            if not run.bold:
                logger.info(
                    f"Check 4 FAIL: action item not bold: '{ap.text[:50]}'"
                )
                return False

    logger.info(
        f"Check 4 PASS: {len(action_paragraphs)} action item(s) bold"
    )
    return True


def _check_font_arial(paragraphs):
    """Check 5: All body text font is set to 'Arial'."""
    total_runs = 0
    arial_runs = 0

    for p in paragraphs:
        for run in p.runs:
            if not run.text.strip():
                continue
            total_runs += 1
            font_name = run.font.name
            if font_name and font_name.lower() == "arial":
                arial_runs += 1

    if total_runs == 0:
        logger.info("Check 5 FAIL: no text runs in document")
        return False

    ratio = arial_runs / total_runs
    # Require >= 90% of runs to use Arial to allow for minor edge cases
    ok = ratio >= 0.9
    if ok:
        logger.info(
            f"Check 5 PASS: {arial_runs}/{total_runs} runs use Arial "
            f"({ratio:.1%})"
        )
    else:
        logger.info(
            f"Check 5 FAIL: only {arial_runs}/{total_runs} runs use Arial "
            f"({ratio:.1%}, need >= 90%)"
        )
    return ok


def _check_footer_text(non_empty):
    """Check 6: Required footer text is present at document end."""
    if not non_empty:
        logger.info("Check 6 FAIL: document is empty")
        return False

    last_text = non_empty[-1].text.strip()
    # Check both exact match and containment (handles trailing whitespace/extra chars)
    ok = (
        REQUIRED_FOOTER in last_text
        or last_text == REQUIRED_FOOTER
    )
    if ok:
        logger.info("Check 6 PASS: required footer text found at end")
    else:
        logger.info(
            f"Check 6 FAIL: footer text not found at end. "
            f"Expected: '{REQUIRED_FOOTER[:60]}...', "
            f"Got: '{last_text[:60]}...'"
        )
    return ok
