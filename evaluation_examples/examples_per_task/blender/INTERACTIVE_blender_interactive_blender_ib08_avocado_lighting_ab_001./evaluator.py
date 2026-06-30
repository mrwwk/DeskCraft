"""
Blender evaluator functions for avocado lighting task.

Checks:
  1. check_blender_render_output — verify avocado_a.png dimensions & format
  2. check_image_has_content     — verify rendered image has visible content
"""
import logging
import os

logger = logging.getLogger(__name__)


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
