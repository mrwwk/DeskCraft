"""
Evaluator for Kdenlive task: Create color clip in project bin with specific duration.

This module provides check_kdenlive_bin_color_clip_duration, which verifies
that a color clip (mlt_service="color") exists in the project file and its
kdenlive:duration property is within the expected range.
"""

import os
import logging
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


# ============================================================================
# Helper Functions
# ============================================================================

def _get_mlt_service(element):
    """
    Extract the mlt_service value from an MLT XML element.

    The mlt_service can appear either as:
    - A direct XML attribute: <filter mlt_service="volume">
    - A child property element: <property name="mlt_service">volume</property>
    """
    service = element.get("mlt_service")
    if service:
        return service
    for prop in element.findall("property"):
        if prop.get("name") == "mlt_service":
            return prop.text
    return None


def _get_property_value(element, property_name):
    """
    Extract a property value from an MLT XML element's child <property> elements.
    """
    for prop in element.findall("property"):
        if prop.get("name") == property_name:
            return prop.text
    return None


def _get_project_fps(root):
    """
    Extract the frame rate from the MLT project profile.
    Returns float: Frames per second (default 25.0 if not found).
    """
    profile = root.find(".//profile")
    if profile is not None:
        try:
            num = float(profile.get("frame_rate_num", 25))
            den = float(profile.get("frame_rate_den", 1))
            if den > 0:
                return num / den
        except (ValueError, ZeroDivisionError):
            pass
    return 25.0


def _duration_str_to_seconds(duration_str, fps=25.0):
    """
    Convert a kdenlive:duration string to seconds.

    Supports formats:
    - "HH:MM:SS:FF" (hours:minutes:seconds:frames)
    - "HH:MM:SS.fff" or "HH:MM:SS,fff"
    - Plain frame number string
    """
    if duration_str is None:
        return 0.0
    duration_str = str(duration_str).strip()
    if ":" in duration_str:
        parts = duration_str.replace(",", ".").split(":")
        try:
            if len(parts) == 4:
                h, m, s, f = parts
                return float(h) * 3600 + float(m) * 60 + float(s) + float(f) / fps
            elif len(parts) == 3:
                h, m, s = parts
                return float(h) * 3600 + float(m) * 60 + float(s)
        except ValueError:
            pass
    try:
        return float(duration_str) / fps
    except ValueError:
        return 0.0


# ============================================================================
# Evaluator Function: Check Color Clip Duration in Project Bin
# ============================================================================

def check_kdenlive_bin_color_clip_duration(project_file_path, expected=None, **options):
    """
    Evaluator for Kdenlive task: Verify a color clip exists in the project bin
    with the expected default duration.

    This function searches for <producer> elements with mlt_service="color"
    (which represent color clips in the project bin) and validates the
    kdenlive:duration property against the expected range.

    Unlike check_kdenlive_clip_duration which only scans timeline playlists
    and skips the bin playlist, this function directly inspects producer
    elements to find color clips regardless of where they are placed.

    Args:
        project_file_path: Path to the .kdenlive project file (retrieved from VM)
        expected: Dictionary with validation rules:
            - min_duration_seconds: Minimum expected duration in seconds
            - max_duration_seconds: Maximum expected duration in seconds

    Returns:
        float: 1.0 if a color clip with matching duration is found, 0.0 otherwise
    """
    try:
        if project_file_path is None or not os.path.exists(project_file_path):
            logger.error(f"Project file not found: {project_file_path}")
            return 0.0

        # Read rules from expected dict
        rules = expected if isinstance(expected, dict) else {}
        min_dur = rules.get("min_duration_seconds")
        max_dur = rules.get("max_duration_seconds")

        tree = ET.parse(project_file_path)
        root = tree.getroot()
        fps = _get_project_fps(root)
        logger.info(f"Project FPS: {fps}")

        # Collect all producers with mlt_service="color"
        color_producers = []
        for producer in root.iter("producer"):
            service = _get_mlt_service(producer)
            if service and service.lower() == "color":
                color_producers.append(producer)

        if not color_producers:
            logger.warning("No color clip (mlt_service='color') found in project")
            return 0.0

        logger.info(f"Found {len(color_producers)} color producer(s) in project")

        # Check duration of each color producer via kdenlive:duration property
        for producer in color_producers:
            prod_id = producer.get("id", "unknown")
            duration_str = _get_property_value(producer, "kdenlive:duration")
            if duration_str is None:
                # Fallback: check "length" property (less common for color clips)
                duration_str = _get_property_value(producer, "length")

            duration_sec = _duration_str_to_seconds(duration_str, fps)
            logger.info(
                f"Color producer id='{prod_id}', "
                f"kdenlive:duration='{duration_str}', "
                f"parsed duration={duration_sec:.3f}s"
            )

            dur_ok = True
            if min_dur is not None and duration_sec < min_dur:
                dur_ok = False
            if max_dur is not None and duration_sec > max_dur:
                dur_ok = False

            if dur_ok:
                logger.info(
                    f"Found color clip '{prod_id}' with matching duration: "
                    f"{duration_sec:.3f}s in [{min_dur}, {max_dur}]"
                )
                return 1.0

        logger.warning(
            f"No color clip found with duration in [{min_dur}, {max_dur}] seconds"
        )
        return 0.0

    except ET.ParseError as e:
        logger.error(f"XML parse error in project file: {e}")
        return 0.0
    except Exception as e:
        logger.error(f"check_kdenlive_bin_color_clip_duration error: {e}")
        return 0.0
