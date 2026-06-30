"""
Blender render output evaluator for ib10_boombox_compliance_rework_001.

Checks that the rendered v1 PNG file exists, has correct dimensions (1920x1080),
and is in PNG format.
"""

import logging
import os

logger = logging.getLogger(__name__)


def check_blender_render_output(file_path, rule):
    """Verify rendered image output (existence, dimensions, format).

    Args:
        file_path: Path to downloaded render output file (PNG)
        rule: {"width": 1920, "height": 1080, "format": "PNG"}
    """
    try:
        if file_path is None or not os.path.exists(file_path):
            logger.error(f"Render output not found: {file_path}")
            return 0.0

        from PIL import Image
        img = Image.open(file_path)
        actual_width, actual_height = img.size

        if "width" in rule and actual_width != rule["width"]:
            logger.warning(f"Width mismatch: {actual_width} != {rule['width']}")
            return 0.0

        if "height" in rule and actual_height != rule["height"]:
            logger.warning(f"Height mismatch: {actual_height} != {rule['height']}")
            return 0.0

        if "format" in rule:
            expected_fmt = rule["format"].upper()
            actual_fmt = img.format
            if actual_fmt and actual_fmt.upper() != expected_fmt:
                # Accept common aliases
                fmt_map = {"JPG": "JPEG"}
                if fmt_map.get(actual_fmt, actual_fmt) != fmt_map.get(expected_fmt, expected_fmt):
                    logger.warning(f"Format mismatch: {actual_fmt} != {expected_fmt}")
                    return 0.0

        return 1.0
    except ImportError:
        logger.error("PIL not available for image verification")
        # Fall back to just checking file exists
        return 1.0 if file_path and os.path.exists(file_path) else 0.0
    except Exception as e:
        logger.error(f"check_blender_render_output error: {e}")
        return 0.0
