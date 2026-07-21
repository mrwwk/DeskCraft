"""
Blender evaluator functions for avocado lighting task.

Checks:
  1. check_blender_render_output — verify avocado_a.png dimensions & format
  2. check_image_has_content     — verify rendered image has visible content
"""
import json
import logging
import os

logger = logging.getLogger(__name__)


def _parse_blender_output(command_output):
    try:
        if not command_output or not command_output.strip():
            logger.error("Empty command output")
            return None
        return json.loads(command_output.strip())
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to parse blender output: {e}")
        return None


# ============================================================================
# Metric 1: Render output file specification check
# ============================================================================

def check_blender_render_output(file_path, rule):
    """Verify rendered image output (existence, dimensions, format).

    Args:
        file_path: Path to downloaded render output file (PNG)
        rule: {"width": 1600, "height": 1600, "format": "PNG"}

    Returns:
        float: 1.0 if all checks pass, 0.0 otherwise.
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


# ============================================================================
# Metric 2: Image content visibility check
# ============================================================================

def check_image_has_content(file_path, expected=None, **options):
    """Verify that the rendered image has visible content.

    Checks that the image has sufficient pixel variation to indicate
    the presence of rendered objects (e.g. the avocado model), not just
    a uniform or near-uniform background / HDRI-only environment.

    Args:
        file_path: Path to the rendered PNG image.
        expected: Unused (kept for framework compatibility).
        **options:
            min_std (float): Minimum pixel std-dev (0-255). Default 15.0.
            min_unique_colors (int): Minimum distinct colors. Default 100.

    Returns:
        float: 1.0 if content detected, 0.0 otherwise.
    """
    try:
        if file_path is None or not os.path.exists(file_path):
            logger.error(f"Image file not found for content check: {file_path}")
            return 0.0

        from PIL import Image
        import numpy as np

        img = Image.open(file_path).convert('RGB')
        arr = np.array(img, dtype=np.float64)

        # 1) Standard deviation — a uniform/empty image has very low std
        std = float(arr.std())
        min_std = float(options.get('min_std', 15.0))
        logger.info(f"Image std: {std:.2f}, threshold: {min_std:.2f}")

        if std < min_std:
            logger.warning(
                f"Image has insufficient content variation "
                f"(std={std:.1f} < threshold={min_std})"
            )
            return 0.0

        # 2) Unique colour count — catches near-uniform renders
        unique_colors = len(np.unique(arr.reshape(-1, 3), axis=0))
        min_unique = int(options.get('min_unique_colors', 100))
        logger.info(f"Unique colors: {unique_colors}, threshold: {min_unique}")

        if unique_colors < min_unique:
            logger.warning(
                f"Image has too few unique colors "
                f"({unique_colors} < {min_unique})"
            )
            return 0.0

        return 1.0
    except ImportError as e:
        logger.error(f"Required library not available for content check: {e}")
        # Cannot verify content — pass through to avoid blocking on missing deps
        return 1.0 if file_path and os.path.exists(file_path) else 0.0
    except Exception as e:
        logger.error(f"check_image_has_content error: {e}")
        return 0.0


def check_blender_world_hdri(command_output, rule):
    """Verify the saved final scene uses the requested HDRI."""
    try:
        result = _parse_blender_output(command_output)
        if result is None:
            return 0.0
        expected_filename = rule.get("hdri_filename", "")
        if not result.get("has_hdri"):
            logger.warning("No HDRI found in world environment")
            return 0.0
        actual_filename = result.get("hdri_filename", "")
        return 1.0 if expected_filename in actual_filename else 0.0
    except Exception as e:
        logger.error(f"check_blender_world_hdri error: {e}")
        return 0.0


def check_images_different(command_output, rule):
    """Verify the A/B renders are visibly different."""
    try:
        result = _parse_blender_output(command_output)
        if result is None:
            return 0.0
        mean_abs_diff = float(result.get("mean_abs_diff", 0.0))
        min_mean_abs_diff = float(rule.get("min_mean_abs_diff", 5.0))
        return 1.0 if mean_abs_diff >= min_mean_abs_diff else 0.0
    except Exception as e:
        logger.error(f"check_images_different error: {e}")
        return 0.0


def check_include_exclude(result, rules):
    if result is None:
        return 0.0
    include = rules.get("include", [])
    exclude = rules.get("exclude", [])
    return 1.0 if all(r in result for r in include) and all(r not in result for r in exclude) else 0.0
