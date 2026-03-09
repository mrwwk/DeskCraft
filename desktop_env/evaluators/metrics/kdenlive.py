"""
Kdenlive Evaluator Functions Module

This module contains task-specific evaluator functions for Kdenlive video editor tasks.
Each function validates task completion by parsing .kdenlive project files (MLT XML format)
or using ffprobe to check rendered output files.

Evaluator functions:
- check_kdenlive_import_video: Verify video imported into project bin
- check_kdenlive_add_to_timeline: Verify clip added to timeline track
- check_kdenlive_grayscale_effect: Verify grayscale effect applied
- check_kdenlive_volume_adjustment: Verify audio volume adjustment
- check_kdenlive_render_mp4: Verify MP4 render output
"""

import os
import logging
import json
import subprocess
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

    Args:
        element: An xml.etree.ElementTree.Element

    Returns:
        str or None: The mlt_service value, or None if not found
    """
    # Check direct attribute first
    service = element.get("mlt_service")
    if service:
        return service

    # Check child <property name="mlt_service"> element
    for prop in element.findall("property"):
        if prop.get("name") == "mlt_service":
            return prop.text

    return None


def _get_property_value(element, property_name):
    """
    Extract a property value from an MLT XML element's child <property> elements.

    Args:
        element: An xml.etree.ElementTree.Element
        property_name: The name attribute to search for

    Returns:
        str or None: The property text value, or None if not found
    """
    for prop in element.findall("property"):
        if prop.get("name") == property_name:
            return prop.text
    return None


# ============================================================================
# Evaluator Function 1: Import Video to Project Bin
# ============================================================================

def check_kdenlive_import_video(project_file_path, rule):
    """
    Evaluator for Kdenlive task: Import video file into project bin.

    Validates that a specific video file has been imported by checking
    if any <producer> node in the .kdenlive project file contains a
    <property name="resource"> referencing the expected file.

    Args:
        project_file_path: Path to the .kdenlive project file (retrieved from VM)
        rule: Dictionary with validation rules.
              Expected format: {"expected_file": "sample_video.mp4"}

    Returns:
        float: 1.0 if the expected file is found in a producer's resource, 0.0 otherwise
    """
    try:
        if project_file_path is None or not os.path.exists(project_file_path):
            logger.error(f"Project file not found: {project_file_path}")
            return 0.0

        expected_file = rule.get("expected_file", "")
        if not expected_file:
            logger.error("No expected_file specified in rule")
            return 0.0

        logger.info(f"Checking for imported file '{expected_file}' in {project_file_path}")

        tree = ET.parse(project_file_path)
        root = tree.getroot()

        # Iterate over all <producer> nodes in the XML
        for producer in root.iter("producer"):
            resource = _get_property_value(producer, "resource")
            if resource and expected_file in resource:
                logger.info(f"Found matching producer with resource: {resource}")
                return 1.0

        logger.warning(f"No producer found with resource containing '{expected_file}'")
        return 0.0

    except ET.ParseError as e:
        logger.error(f"XML parse error in project file: {e}")
        return 0.0
    except Exception as e:
        logger.error(f"check_kdenlive_import_video error: {e}")
        return 0.0


# ============================================================================
# Evaluator Function 2: Add Clip to Timeline
# ============================================================================

def check_kdenlive_add_to_timeline(project_file_path, rule):
    """
    Evaluator for Kdenlive task: Add video clip to timeline track.

    Validates that a clip has been placed on the timeline by checking
    if any <playlist> contains an <entry> node (not just <blank> nodes),
    and that the entry references a producer whose resource matches
    the expected file.

    Args:
        project_file_path: Path to the .kdenlive project file (retrieved from VM)
        rule: Dictionary with validation rules.
              Expected format: {"expected_file": "sample_video.mp4"}

    Returns:
        float: 1.0 if the expected clip is found on the timeline, 0.0 otherwise
    """
    try:
        if project_file_path is None or not os.path.exists(project_file_path):
            logger.error(f"Project file not found: {project_file_path}")
            return 0.0

        expected_file = rule.get("expected_file", "")
        if not expected_file:
            logger.error("No expected_file specified in rule")
            return 0.0

        logger.info(f"Checking timeline for clip '{expected_file}' in {project_file_path}")

        tree = ET.parse(project_file_path)
        root = tree.getroot()

        # Build a mapping from producer id to resource path
        producer_resources = {}
        for producer in root.iter("producer"):
            prod_id = producer.get("id", "")
            resource = _get_property_value(producer, "resource")
            if prod_id and resource:
                producer_resources[prod_id] = resource

        logger.info(f"Found {len(producer_resources)} producers in project")

        # Check all <playlist> nodes for <entry> elements
        for playlist in root.iter("playlist"):
            entries = playlist.findall("entry")
            if not entries:
                continue

            for entry in entries:
                entry_producer = entry.get("producer", "")
                if not entry_producer:
                    continue

                # The entry's producer attribute may reference a producer directly
                # or a tractor/chain - check direct match first
                resource = producer_resources.get(entry_producer, "")
                if resource and expected_file in resource:
                    logger.info(f"Found timeline entry referencing '{expected_file}' "
                                f"via producer '{entry_producer}' in playlist '{playlist.get('id', '')}'")
                    return 1.0

                # Also check if any producer resource contains the expected file
                # (producer id naming can vary, e.g., "producer0", "chain0", etc.)
                for prod_id, res in producer_resources.items():
                    if expected_file in res and prod_id in entry_producer:
                        logger.info(f"Found timeline entry with indirect match: "
                                    f"entry_producer='{entry_producer}', resource='{res}'")
                        return 1.0

        logger.warning(f"No timeline entry found referencing '{expected_file}'")
        return 0.0

    except ET.ParseError as e:
        logger.error(f"XML parse error in project file: {e}")
        return 0.0
    except Exception as e:
        logger.error(f"check_kdenlive_add_to_timeline error: {e}")
        return 0.0


# ============================================================================
# Evaluator Function 3: Apply Grayscale Effect
# ============================================================================

def check_kdenlive_grayscale_effect(project_file_path, rule):
    """
    Evaluator for Kdenlive task: Apply grayscale video effect to a clip.

    Validates that a grayscale-type effect has been applied by checking
    if any <filter> node in the project file has an mlt_service matching
    known grayscale effect identifiers.

    Args:
        project_file_path: Path to the .kdenlive project file (retrieved from VM)
        rule: Dictionary with validation rules (can be empty {} for this task)

    Returns:
        float: 1.0 if a grayscale filter is found, 0.0 otherwise
    """
    # Known MLT service names that produce grayscale/black-and-white effects
    GRAYSCALE_SERVICES = [
        "grayscale",                    # Native MLT grayscale filter
        "greyscale",                    # Alternative spelling
        "avfilter.colorchannelmixer",   # FFmpeg colorchannelmixer (can do grayscale)
        "frei0r.colorize",              # Frei0r colorize plugin
        "charcoal",                     # Charcoal effect (produces B&W)
        "frei0r.bw0r",                  # Frei0r black & white filter
    ]

    try:
        if project_file_path is None or not os.path.exists(project_file_path):
            logger.error(f"Project file not found: {project_file_path}")
            return 0.0

        logger.info(f"Checking for grayscale effect in {project_file_path}")

        tree = ET.parse(project_file_path)
        root = tree.getroot()

        # Iterate over ALL <filter> nodes (they can be nested inside
        # <producer>, <playlist>, <tractor>, etc.)
        for filter_elem in root.iter("filter"):
            service = _get_mlt_service(filter_elem)
            if service and service.lower() in [s.lower() for s in GRAYSCALE_SERVICES]:
                logger.info(f"Found grayscale filter with mlt_service='{service}'")
                return 1.0

            # Also check kdenlive:id property which may identify the effect
            kdenlive_id = _get_property_value(filter_elem, "kdenlive_id")
            if kdenlive_id and "grey" in kdenlive_id.lower() or kdenlive_id and "gray" in kdenlive_id.lower():
                logger.info(f"Found grayscale filter with kdenlive_id='{kdenlive_id}'")
                return 1.0

        logger.warning("No grayscale filter found in project file")
        return 0.0

    except ET.ParseError as e:
        logger.error(f"XML parse error in project file: {e}")
        return 0.0
    except Exception as e:
        logger.error(f"check_kdenlive_grayscale_effect error: {e}")
        return 0.0


# ============================================================================
# Evaluator Function 4: Adjust Audio Volume
# ============================================================================

def check_kdenlive_volume_adjustment(project_file_path, rule):
    """
    Evaluator for Kdenlive task: Adjust audio volume of a clip.

    Validates that the audio volume has been adjusted by checking
    if a volume filter exists with the expected level/gain value
    within a specified tolerance.

    In Kdenlive/MLT, volume is represented as:
    - level: linear gain factor (e.g., 0.5 = 50%, 1.0 = 100%)
    - gain: similar to level, sometimes in dB

    Args:
        project_file_path: Path to the .kdenlive project file (retrieved from VM)
        rule: Dictionary with validation rules.
              Expected format: {
                  "expected_volume": 0.5,    # Target volume (linear, 0.0-1.0)
                  "tolerance": 0.05          # Acceptable deviation (optional, default 0.05)
              }

    Returns:
        float: 1.0 if volume filter matches expected value within tolerance, 0.0 otherwise
    """
    try:
        if project_file_path is None or not os.path.exists(project_file_path):
            logger.error(f"Project file not found: {project_file_path}")
            return 0.0

        expected_volume = rule.get("expected_volume")
        if expected_volume is None:
            logger.error("No expected_volume specified in rule")
            return 0.0

        tolerance = rule.get("tolerance", 0.05)
        expected_volume = float(expected_volume)

        logger.info(f"Checking for volume={expected_volume} (±{tolerance}) in {project_file_path}")

        tree = ET.parse(project_file_path)
        root = tree.getroot()

        # Search all <filter> nodes for volume filters
        for filter_elem in root.iter("filter"):
            service = _get_mlt_service(filter_elem)
            if not service or service.lower() != "volume":
                continue

            logger.info(f"Found volume filter: {filter_elem.attrib}")

            # Check 'level' property (primary volume control)
            level_str = _get_property_value(filter_elem, "level")
            if level_str is not None:
                try:
                    # Handle keyframe format: "00:00:00.000=0.5" or simple "0.5"
                    if "=" in level_str:
                        # Take the last keyframe value
                        parts = level_str.strip().split("\n")
                        last_part = parts[-1].strip()
                        level_value = float(last_part.split("=")[-1])
                    else:
                        level_value = float(level_str)

                    logger.info(f"Volume level value: {level_value}")

                    if abs(level_value - expected_volume) <= tolerance:
                        logger.info(f"Volume matches: {level_value} ≈ {expected_volume}")
                        return 1.0
                except ValueError:
                    logger.warning(f"Could not parse level value: '{level_str}'")

            # Check 'gain' property (alternative volume control)
            gain_str = _get_property_value(filter_elem, "gain")
            if gain_str is not None:
                try:
                    if "=" in gain_str:
                        parts = gain_str.strip().split("\n")
                        last_part = parts[-1].strip()
                        gain_value = float(last_part.split("=")[-1])
                    else:
                        gain_value = float(gain_str)

                    logger.info(f"Volume gain value: {gain_value}")

                    if abs(gain_value - expected_volume) <= tolerance:
                        logger.info(f"Volume gain matches: {gain_value} ≈ {expected_volume}")
                        return 1.0
                except ValueError:
                    logger.warning(f"Could not parse gain value: '{gain_str}'")

        logger.warning(f"No volume filter found matching expected_volume={expected_volume}")
        return 0.0

    except ET.ParseError as e:
        logger.error(f"XML parse error in project file: {e}")
        return 0.0
    except Exception as e:
        logger.error(f"check_kdenlive_volume_adjustment error: {e}")
        return 0.0


# ============================================================================
# Evaluator Function 5: Render to MP4
# ============================================================================

def check_kdenlive_render_mp4(result_file_path, rule):
    """
    Evaluator for Kdenlive task: Render project as MP4 (H.264).

    Validates the rendered output file by checking:
    1. File exists and has size > 0
    2. Video codec is H.264 (using ffprobe)
    3. Video duration is > 1 second

    Args:
        result_file_path: Path to the rendered MP4 file (retrieved from VM)
        rule: Dictionary with validation rules (can be empty {} for basic check)
              Optional keys:
              - "min_duration": Minimum expected duration in seconds (default 1.0)
              - "expected_codec": Expected codec name (default "h264")

    Returns:
        float: 1.0 if all checks pass, 0.0 otherwise
    """
    try:
        if result_file_path is None or not os.path.exists(result_file_path):
            logger.error(f"Rendered file not found: {result_file_path}")
            return 0.0

        # Check file size > 0
        file_size = os.path.getsize(result_file_path)
        if file_size == 0:
            logger.error(f"Rendered file is empty (0 bytes): {result_file_path}")
            return 0.0

        logger.info(f"Rendered file exists, size: {file_size} bytes")

        min_duration = rule.get("min_duration", 1.0)
        expected_codec = rule.get("expected_codec", "h264")

        # Use ffprobe to inspect the file
        ffprobe_cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_streams",
            "-show_format",
            result_file_path
        ]

        result = subprocess.run(
            ffprobe_cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            logger.error(f"ffprobe failed with return code {result.returncode}: {result.stderr}")
            return 0.0

        probe_data = json.loads(result.stdout)
        streams = probe_data.get("streams", [])
        format_info = probe_data.get("format", {})

        # Find video stream
        video_stream = None
        for stream in streams:
            if stream.get("codec_type") == "video":
                video_stream = stream
                break

        if video_stream is None:
            logger.error("No video stream found in rendered file")
            return 0.0

        # Check video codec
        codec_name = video_stream.get("codec_name", "").lower()
        logger.info(f"Video codec: {codec_name}")

        if expected_codec.lower() not in codec_name:
            logger.error(f"Codec mismatch: expected '{expected_codec}', got '{codec_name}'")
            return 0.0

        # Check duration (try stream first, then format)
        duration = 0.0
        if "duration" in video_stream:
            duration = float(video_stream["duration"])
        elif "duration" in format_info:
            duration = float(format_info["duration"])
        else:
            # Try to calculate from nb_frames and frame rate
            nb_frames = video_stream.get("nb_frames")
            r_frame_rate = video_stream.get("r_frame_rate", "30/1")
            if nb_frames:
                try:
                    num, den = r_frame_rate.split("/")
                    fps = float(num) / float(den)
                    duration = float(nb_frames) / fps
                except (ValueError, ZeroDivisionError):
                    pass

        logger.info(f"Video duration: {duration:.2f} seconds")

        if duration < min_duration:
            logger.error(f"Duration too short: {duration:.2f}s < {min_duration}s")
            return 0.0

        logger.info(f"check_kdenlive_render_mp4: All checks passed "
                     f"(codec={codec_name}, duration={duration:.2f}s, size={file_size})")
        return 1.0

    except subprocess.TimeoutExpired:
        logger.error("ffprobe timed out after 30 seconds")
        return 0.0
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse ffprobe JSON output: {e}")
        return 0.0
    except Exception as e:
        logger.error(f"check_kdenlive_render_mp4 error: {e}")
        return 0.0
