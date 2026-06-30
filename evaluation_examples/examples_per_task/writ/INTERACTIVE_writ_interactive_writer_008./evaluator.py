import logging

logger = logging.getLogger("desktopenv.metric.general")


def check_notes_section_added(result: str, **options) -> float:
    """
    Checks that the 'Important Notes' section in the training guide
    has had content added after the heading.

    The task instruction is ambiguous ('Help me add the notes section')
    and does not prescribe specific note content, so we only verify
    that non-empty lines exist after the 'Important Notes' heading.
    """
    if result is None:
        return 0.

    # Remove BOM if present (common in text files from some editors)
    if result.startswith('\ufeff'):
        result = result[1:]

    lines = result.splitlines()

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "Important Notes":
            # Check that at least one non-empty line exists after the heading
            for j in range(i + 1, len(lines)):
                if lines[j].strip():
                    return 1.
            # Heading found but no content after it
            return 0.

    # 'Important Notes' heading not found at all
    return 0.
