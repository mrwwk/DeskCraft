from pptx import Presentation


def check_slide_orientation_Portrait(pptx_path):
    """Check if the PPTX slide orientation is Portrait (slide_height > slide_width).

    Args:
        pptx_path: Path to the PPTX file.

    Returns:
        1 if Portrait (height > width), 0 otherwise.
    """
    presentation = Presentation(pptx_path)

    slide_height = presentation.slide_height
    slide_width = presentation.slide_width

    if slide_width < slide_height:
        return 1
    return 0
