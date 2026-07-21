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

        if "min_color_stddev" in rule:
            from PIL import ImageStat
            rgb = img.convert("RGB")
            rgb.thumbnail((256, 256))
            stat = ImageStat.Stat(rgb)
            color_stddev = sum(stat.stddev) / len(stat.stddev)
            if color_stddev < float(rule["min_color_stddev"]):
                logger.warning(f"Image appears blank/flat: stddev={color_stddev:.2f}")
                return 0.0

        return 1.0
    except ImportError:
        logger.error("PIL not available for image verification")
        # Fall back to just checking file exists
        return 1.0 if file_path and os.path.exists(file_path) else 0.0
    except Exception as e:
        logger.error(f"check_blender_render_output error: {e}")
        return 0.0


def check_image_safe_area_clear(file_path, rule):
    """Verify the upper-right compliance safe area is visually quiet."""
    try:
        if file_path is None or not os.path.exists(file_path):
            logger.error(f"Image file not found: {file_path}")
            return 0.0

        from PIL import Image, ImageStat

        img = Image.open(file_path).convert("RGB")
        width, height = img.size
        x0 = int(width * float(rule.get("safe_x_ratio", 0.72)))
        y1 = int(height * float(rule.get("safe_y_ratio", 0.28)))
        safe_area = img.crop((x0, 0, width, y1))
        stat = ImageStat.Stat(safe_area)
        safe_stddev = sum(stat.stddev) / len(stat.stddev)
        max_stddev = float(rule.get("max_safe_area_stddev", 35.0))
        logger.info(f"safe area stddev={safe_stddev:.2f}, max={max_stddev:.2f}")
        return 1.0 if safe_stddev <= max_stddev else 0.0
    except Exception as e:
        logger.error(f"check_image_safe_area_clear error: {e}")
        return 0.0


def check_include_exclude(result, rules):
    if result is None:
        return 0.0
    include = rules.get("include", [])
    exclude = rules.get("exclude", [])
    return 1.0 if all(r in result for r in include) and all(r not in result for r in exclude) else 0.0
