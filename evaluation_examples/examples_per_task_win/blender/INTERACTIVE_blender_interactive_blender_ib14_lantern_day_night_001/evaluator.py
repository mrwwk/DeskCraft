"""
Evaluator functions for interactive_blender_ib14_lantern_day_night_001.

Bundled from desktop_env.evaluators.metrics.blender and general for
self-contained evaluator loading via evaluator.file.
"""

import json
import logging
import os

logger = logging.getLogger(__name__)


# ============================================================================
# Helper
# ============================================================================

def _parse_blender_output(command_output):
    """Parse JSON output from blender check script (RESULT:{json} format)."""
    try:
        if not command_output or not command_output.strip():
            logger.error("Empty command output")
            return None
        return json.loads(command_output.strip())
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to parse blender output: {e}")
        logger.debug(f"Raw output: {command_output!r}")
        return None


# ============================================================================
# Metric: check_blender_render_settings
# ============================================================================

def check_blender_render_settings(command_output, rule):
    """Verify render settings (engine, resolution, format, etc.).

    Args:
        command_output: JSON string from check_render.py (RESULT:{json})
        rule: dict with any of: engine, resolution_x, resolution_y, fps,
              samples, image_format, active_camera
    """
    try:
        result = _parse_blender_output(command_output)
        if result is None:
            return 0.0

        checks = {
            "engine": lambda r, e: r.get("engine") == e,
            "resolution_x": lambda r, e: r.get("resolution_x") == e,
            "resolution_y": lambda r, e: r.get("resolution_y") == e,
            "fps": lambda r, e: r.get("fps") == e,
            "samples": lambda r, e: r.get("samples") == e,
            "image_format": lambda r, e: r.get("image_format") == e,
            "active_camera": lambda r, e: r.get("active_camera") == e,
        }

        for key, check_fn in checks.items():
            if key in rule:
                if not check_fn(result, rule[key]):
                    logger.warning(
                        f"Render setting mismatch: {key} = {result.get(key)} != {rule[key]}"
                    )
                    return 0.0

        return 1.0
    except Exception as e:
        logger.error(f"check_blender_render_settings error: {e}")
        return 0.0


# ============================================================================
# Metric: check_blender_world_hdri
# ============================================================================

def check_blender_world_hdri(command_output, rule):
    """Verify world environment uses specified HDRI file.

    Args:
        command_output: JSON string from check_world.py (RESULT:{json})
        rule: {"hdri_filename": "hdri_aerodynamics_workshop_1k.exr"}
    """
    try:
        result = _parse_blender_output(command_output)
        if result is None:
            return 0.0

        expected_filename = rule.get("hdri_filename", "")

        if not result.get("has_hdri"):
            logger.warning("No HDRI found in world environment")
            return 0.0

        actual_filename = result.get("hdri_filename", "")
        if expected_filename in actual_filename or actual_filename == expected_filename:
            return 1.0

        logger.warning(
            f"HDRI mismatch: '{actual_filename}' != '{expected_filename}'"
        )
        return 0.0
    except Exception as e:
        logger.error(f"check_blender_world_hdri error: {e}")
        return 0.0


# ============================================================================
# Metric: check_blender_render_output
# ============================================================================

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
            logger.warning(
                f"Width mismatch: {actual_width} != {rule['width']}"
            )
            return 0.0

        if "height" in rule and actual_height != rule["height"]:
            logger.warning(
                f"Height mismatch: {actual_height} != {rule['height']}"
            )
            return 0.0

        if "min_width" in rule and actual_width < rule["min_width"]:
            logger.warning(
                f"Width too small: {actual_width} < {rule['min_width']}"
            )
            return 0.0

        if "min_height" in rule and actual_height < rule["min_height"]:
            logger.warning(
                f"Height too small: {actual_height} < {rule['min_height']}"
            )
            return 0.0

        if "format" in rule:
            expected_fmt = rule["format"].upper()
            actual_fmt = img.format
            if actual_fmt and actual_fmt.upper() != expected_fmt:
                # Accept common aliases
                fmt_map = {"JPG": "JPEG"}
                if fmt_map.get(actual_fmt, actual_fmt) != fmt_map.get(expected_fmt, expected_fmt):
                    logger.warning(
                        f"Format mismatch: {actual_fmt} != {expected_fmt}"
                    )
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


# ============================================================================
# Metric: check_include_exclude
# ============================================================================

def check_include_exclude(result, rules):
    """Check that result string contains all 'include' substrings and none of
    the 'exclude' substrings.

    Args:
        result: String output from a shell command listing file existence.
        rules: {"include": [...], "exclude": [...]}
    """
    if result is None:
        return 0.0

    print(result, rules)
    include = rules.get("include", [])
    exclude = rules.get("exclude", [])
    if all(r in result for r in include) and all(r not in result for r in exclude):
        return 1.0
    else:
        return 0.0


def check_images_different(command_output, rule):
    """Verify day/night renders are not identical outputs."""
    try:
        result = _parse_blender_output(command_output)
        if result is None:
            return 0.0
        byte_diff_ratio = float(result.get("byte_diff_ratio", 0.0))
        min_byte_diff_ratio = float(rule.get("min_byte_diff_ratio", 0.02))
        return 1.0 if byte_diff_ratio >= min_byte_diff_ratio else 0.0
    except Exception as e:
        logger.error(f"check_images_different error: {e}")
        return 0.0


def check_compare_layout(file_path, rule):
    """Verify the comparison image is a side-by-side style PNG."""
    return check_blender_render_output(file_path, rule)
