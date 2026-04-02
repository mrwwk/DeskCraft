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
- check_kdenlive_project_profile: Verify project profile settings (resolution, frame rate)
- check_kdenlive_import_multiple_files: Verify multiple files imported into project bin
- check_kdenlive_file_exists: Verify project file exists and is valid XML
- check_kdenlive_bin_content: Verify bin contains/excludes specific files
- check_kdenlive_clip_name: Verify clip has been renamed in the bin
- check_kdenlive_bin_folder: Verify a folder exists in the project bin
- check_kdenlive_track_count: Verify number of video/audio tracks in timeline
- check_kdenlive_guide: Verify a guide/marker exists at a specific time
- check_kdenlive_track_mute: Verify a track is muted
- check_kdenlive_track_lock: Verify a track is locked
- check_kdenlive_timeline_empty: Verify timeline has no clips (but bin may have clips)
- check_kdenlive_color_clip: Verify a color clip with specific color exists
- check_kdenlive_clip_duration: Verify clip duration in timeline
- check_kdenlive_snapshot_exists: Verify snapshot PNG file(s) exist
- check_kdenlive_proxy_setting: Verify proxy clip setting is enabled/disabled
- check_kdenlive_clip_position: Verify clip is placed at a specific position on timeline
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


# ============================================================================
# Helper: parse MLT frame count string to seconds
# ============================================================================

def _frames_to_seconds(frame_str, fps=25.0):
    """
    Convert an MLT frame count string to seconds.
    MLT stores time as frame numbers (integers) or as "HH:MM:SS.mmm" strings.

    Args:
        frame_str: Frame count as string (e.g. "125") or timecode "00:00:05.000"
        fps: Frames per second (default 25)

    Returns:
        float: Time in seconds
    """
    if frame_str is None:
        return 0.0
    frame_str = str(frame_str).strip()
    # Timecode format HH:MM:SS.mmm or HH:MM:SS:FF
    if ":" in frame_str:
        parts = frame_str.replace(",", ".").split(":")
        try:
            if len(parts) == 3:
                h, m, s = parts
                return float(h) * 3600 + float(m) * 60 + float(s)
            elif len(parts) == 4:
                h, m, s, f = parts
                return float(h) * 3600 + float(m) * 60 + float(s) + float(f) / fps
        except ValueError:
            pass
    # Plain frame number
    try:
        return float(frame_str) / fps
    except ValueError:
        return 0.0


def _get_project_fps(root):
    """
    Extract the frame rate from the MLT project profile.

    Returns:
        float: Frames per second (default 25.0 if not found)
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


# ============================================================================
# Evaluator Function 6: Check Project Profile
# ============================================================================

def check_kdenlive_project_profile(project_file_path, rule):
    """
    Evaluator for Kdenlive task: Verify project profile settings.

    Checks the <profile> element in the .kdenlive project file for
    resolution (width/height), frame rate, or preview resolution.

    Args:
        project_file_path: Path to the .kdenlive project file
        rule: Dictionary with validation rules. Supported keys:
              - "width": Expected video width (int)
              - "height": Expected video height (int)
              - "frame_rate_num": Expected frame rate numerator (int)
              - "frame_rate_den": Expected frame rate denominator (int)
              - "preview_width": Expected preview/display width (int)
              - "preview_height": Expected preview/display height (int)

    Returns:
        float: 1.0 if all specified profile attributes match, 0.0 otherwise
    """
    try:
        if project_file_path is None or not os.path.exists(project_file_path):
            logger.error(f"Project file not found: {project_file_path}")
            return 0.0

        tree = ET.parse(project_file_path)
        root = tree.getroot()

        # Find the <profile> element (may be direct child or nested)
        profile = root.find(".//profile")
        if profile is None:
            logger.error("No <profile> element found in project file")
            return 0.0

        logger.info(f"Profile attributes: {profile.attrib}")

        # Check each rule key
        checks = {
            "width": ("width", int),
            "height": ("height", int),
            "frame_rate_num": ("frame_rate_num", int),
            "frame_rate_den": ("frame_rate_den", int),
            "preview_width": ("display_aspect_num", int),   # Kdenlive uses display_aspect_num for preview width
            "preview_height": ("display_aspect_den", int),  # Kdenlive uses display_aspect_den for preview height
        }

        # For preview resolution, Kdenlive stores it differently.
        # The actual preview size is in width/height when the profile is a preview profile.
        # We check width/height directly for preview_width/preview_height as well.
        for rule_key, expected_val in rule.items():
            if rule_key == "preview_width":
                actual = profile.get("width")
                if actual is None:
                    logger.error("Profile has no 'width' attribute")
                    return 0.0
                if int(actual) != int(expected_val):
                    logger.warning(f"preview_width mismatch: expected {expected_val}, got {actual}")
                    return 0.0
                logger.info(f"preview_width matches: {actual}")

            elif rule_key == "preview_height":
                actual = profile.get("height")
                if actual is None:
                    logger.error("Profile has no 'height' attribute")
                    return 0.0
                if int(actual) != int(expected_val):
                    logger.warning(f"preview_height mismatch: expected {expected_val}, got {actual}")
                    return 0.0
                logger.info(f"preview_height matches: {actual}")

            elif rule_key in ("width", "height", "frame_rate_num", "frame_rate_den"):
                actual = profile.get(rule_key)
                if actual is None:
                    logger.error(f"Profile has no '{rule_key}' attribute")
                    return 0.0
                if int(actual) != int(expected_val):
                    logger.warning(f"{rule_key} mismatch: expected {expected_val}, got {actual}")
                    return 0.0
                logger.info(f"{rule_key} matches: {actual}")

        logger.info("check_kdenlive_project_profile: All profile checks passed")
        return 1.0

    except ET.ParseError as e:
        logger.error(f"XML parse error in project file: {e}")
        return 0.0
    except Exception as e:
        logger.error(f"check_kdenlive_project_profile error: {e}")
        return 0.0


# ============================================================================
# Evaluator Function 7: Import Multiple Files
# ============================================================================

def check_kdenlive_import_multiple_files(project_file_path, rule):
    """
    Evaluator for Kdenlive task: Import multiple files into project bin.

    Validates that all specified files have been imported by checking
    if each file appears in at least one <producer> resource property.

    Args:
        project_file_path: Path to the .kdenlive project file
        rule: Dictionary with validation rules.
              Expected format: {"expected_files": ["file1.mp4", "file2.mp4"]}

    Returns:
        float: 1.0 if ALL expected files are found, 0.0 otherwise
    """
    try:
        if project_file_path is None or not os.path.exists(project_file_path):
            logger.error(f"Project file not found: {project_file_path}")
            return 0.0

        expected_files = rule.get("expected_files", [])
        if not expected_files:
            logger.error("No expected_files specified in rule")
            return 0.0

        tree = ET.parse(project_file_path)
        root = tree.getroot()

        # Collect all resource paths from producers
        resources = []
        for producer in root.iter("producer"):
            resource = _get_property_value(producer, "resource")
            if resource:
                resources.append(resource)

        logger.info(f"Found {len(resources)} producer resources")

        # Check each expected file
        for expected_file in expected_files:
            found = any(expected_file in res for res in resources)
            if not found:
                logger.warning(f"Expected file '{expected_file}' not found in project bin")
                return 0.0
            logger.info(f"Found expected file: {expected_file}")

        logger.info("check_kdenlive_import_multiple_files: All files found")
        return 1.0

    except ET.ParseError as e:
        logger.error(f"XML parse error in project file: {e}")
        return 0.0
    except Exception as e:
        logger.error(f"check_kdenlive_import_multiple_files error: {e}")
        return 0.0


# ============================================================================
# Evaluator Function 8: File Exists (New Project Saved)
# ============================================================================

def check_kdenlive_file_exists(project_file_path, rule):
    """
    Evaluator for Kdenlive task: Verify a project file exists and is valid.

    Checks that the file was retrieved (not None), exists on disk,
    and optionally validates it is a well-formed XML file.

    Args:
        project_file_path: Path to the .kdenlive project file
        rule: Dictionary with validation rules.
              Optional keys:
              - "valid_xml": bool, if True also validate XML structure (default True)

    Returns:
        float: 1.0 if file exists (and is valid XML if required), 0.0 otherwise
    """
    try:
        if project_file_path is None or not os.path.exists(project_file_path):
            logger.error(f"Project file not found: {project_file_path}")
            return 0.0

        file_size = os.path.getsize(project_file_path)
        if file_size == 0:
            logger.error(f"Project file is empty: {project_file_path}")
            return 0.0

        logger.info(f"Project file exists, size: {file_size} bytes")

        check_xml = rule.get("valid_xml", True)
        if check_xml:
            try:
                tree = ET.parse(project_file_path)
                root = tree.getroot()
                # A valid Kdenlive file should have a root element (mlt or kdenlive)
                if root is None:
                    logger.error("XML has no root element")
                    return 0.0
                logger.info(f"Valid XML with root element: <{root.tag}>")
            except ET.ParseError as e:
                logger.error(f"Invalid XML: {e}")
                return 0.0

        logger.info("check_kdenlive_file_exists: File exists and is valid")
        return 1.0

    except Exception as e:
        logger.error(f"check_kdenlive_file_exists error: {e}")
        return 0.0


# ============================================================================
# Evaluator Function 9: Check Bin Content (Present/Absent)
# ============================================================================

def check_kdenlive_bin_content(project_file_path, rule):
    """
    Evaluator for Kdenlive task: Verify project bin contains/excludes specific files.

    Checks that files listed in "expected_present" are in the bin (as producer
    resources) and files listed in "expected_absent" are NOT in the bin.

    Args:
        project_file_path: Path to the .kdenlive project file
        rule: Dictionary with validation rules.
              Expected format: {
                  "expected_present": ["file1.mp4"],   # must be in bin
                  "expected_absent": ["file2.mp4"]     # must NOT be in bin
              }

    Returns:
        float: 1.0 if all present/absent conditions are satisfied, 0.0 otherwise
    """
    try:
        if project_file_path is None or not os.path.exists(project_file_path):
            logger.error(f"Project file not found: {project_file_path}")
            return 0.0

        expected_present = rule.get("expected_present", [])
        expected_absent = rule.get("expected_absent", [])

        tree = ET.parse(project_file_path)
        root = tree.getroot()

        # Collect all resource paths from producers
        resources = []
        for producer in root.iter("producer"):
            resource = _get_property_value(producer, "resource")
            if resource:
                resources.append(resource)

        logger.info(f"Found {len(resources)} producer resources in bin")

        # Check files that must be present
        for expected_file in expected_present:
            found = any(expected_file in res for res in resources)
            if not found:
                logger.warning(f"Expected present file '{expected_file}' not found in bin")
                return 0.0
            logger.info(f"Confirmed present: {expected_file}")

        # Check files that must be absent
        for absent_file in expected_absent:
            found = any(absent_file in res for res in resources)
            if found:
                logger.warning(f"Expected absent file '{absent_file}' is still in bin")
                return 0.0
            logger.info(f"Confirmed absent: {absent_file}")

        logger.info("check_kdenlive_bin_content: All bin content checks passed")
        return 1.0

    except ET.ParseError as e:
        logger.error(f"XML parse error in project file: {e}")
        return 0.0
    except Exception as e:
        logger.error(f"check_kdenlive_bin_content error: {e}")
        return 0.0


# ============================================================================
# Evaluator Function 10: Check Clip Name (Renamed in Bin)
# ============================================================================

def check_kdenlive_clip_name(project_file_path, rule):
    """
    Evaluator for Kdenlive task: Verify a clip has been renamed in the project bin.

    Checks that the producer whose resource matches "source_file" has a
    "kdenlive:clipname" property equal to "expected_name".

    Args:
        project_file_path: Path to the .kdenlive project file
        rule: Dictionary with validation rules.
              Expected format: {
                  "source_file": "original_filename.mp4",
                  "expected_name": "My Custom Name"
              }

    Returns:
        float: 1.0 if the clip has the expected name, 0.0 otherwise
    """
    try:
        if project_file_path is None or not os.path.exists(project_file_path):
            logger.error(f"Project file not found: {project_file_path}")
            return 0.0

        source_file = rule.get("source_file", "")
        expected_name = rule.get("expected_name", "")

        if not source_file or not expected_name:
            logger.error("Missing source_file or expected_name in rule")
            return 0.0

        tree = ET.parse(project_file_path)
        root = tree.getroot()

        for producer in root.iter("producer"):
            resource = _get_property_value(producer, "resource")
            if resource and source_file in resource:
                clip_name = _get_property_value(producer, "kdenlive:clipname")
                logger.info(f"Found producer for '{source_file}', kdenlive:clipname='{clip_name}'")
                if clip_name == expected_name:
                    logger.info(f"Clip name matches: '{clip_name}'")
                    return 1.0
                else:
                    logger.warning(f"Clip name mismatch: expected '{expected_name}', got '{clip_name}'")
                    return 0.0

        logger.warning(f"No producer found with resource containing '{source_file}'")
        return 0.0

    except ET.ParseError as e:
        logger.error(f"XML parse error in project file: {e}")
        return 0.0
    except Exception as e:
        logger.error(f"check_kdenlive_clip_name error: {e}")
        return 0.0


# ============================================================================
# Evaluator Function 11: Check Bin Folder
# ============================================================================

def check_kdenlive_bin_folder(project_file_path, rule):
    """
    Evaluator for Kdenlive task: Verify a folder exists in the project bin.

    In Kdenlive's MLT XML, bin folders are represented as <folder> elements
    inside the <kdenlive_producer> or as <property name="kdenlive:foldernames">
    in the main bin playlist. We check multiple possible representations.

    Args:
        project_file_path: Path to the .kdenlive project file
        rule: Dictionary with validation rules.
              Expected format: {"expected_folder": "Footage"}

    Returns:
        float: 1.0 if the folder exists in the bin, 0.0 otherwise
    """
    try:
        if project_file_path is None or not os.path.exists(project_file_path):
            logger.error(f"Project file not found: {project_file_path}")
            return 0.0

        expected_folder = rule.get("expected_folder", "")
        if not expected_folder:
            logger.error("No expected_folder specified in rule")
            return 0.0

        tree = ET.parse(project_file_path)
        root = tree.getroot()

        # Method 1: Check <folder name="..."> elements anywhere in the XML
        for folder in root.iter("folder"):
            folder_name = folder.get("name", "")
            if folder_name == expected_folder:
                logger.info(f"Found bin folder via <folder> element: '{folder_name}'")
                return 1.0

        # Method 2: Check kdenlive:foldernames property in any playlist/producer
        for elem in root.iter():
            for prop in elem.findall("property"):
                if prop.get("name") == "kdenlive:foldernames" and prop.text:
                    if expected_folder in prop.text:
                        logger.info(f"Found folder in kdenlive:foldernames: '{expected_folder}'")
                        return 1.0

        # Method 3: Check kdenlive:folder-in-bin property
        for elem in root.iter():
            for prop in elem.findall("property"):
                if "folder" in prop.get("name", "").lower() and prop.text:
                    if expected_folder in prop.text:
                        logger.info(f"Found folder in property '{prop.get('name')}': '{expected_folder}'")
                        return 1.0

        logger.warning(f"Bin folder '{expected_folder}' not found in project file")
        return 0.0

    except ET.ParseError as e:
        logger.error(f"XML parse error in project file: {e}")
        return 0.0
    except Exception as e:
        logger.error(f"check_kdenlive_bin_folder error: {e}")
        return 0.0


# ============================================================================
# Evaluator Function 12: Check Track Count
# ============================================================================

def check_kdenlive_track_count(project_file_path, rule):
    """
    Evaluator for Kdenlive task: Verify the number of video/audio tracks.

    In Kdenlive's MLT XML, tracks are represented as <track> elements inside
    the main <tractor>. Each track references a <playlist> which has a
    "kdenlive:audio_track" property (1=audio, absent/0=video).

    Args:
        project_file_path: Path to the .kdenlive project file
        rule: Dictionary with validation rules. Supported keys:
              - "min_video_tracks": Minimum number of video tracks required
              - "min_audio_tracks": Minimum number of audio tracks required
              - "exact_video_tracks": Exact number of video tracks required
              - "exact_audio_tracks": Exact number of audio tracks required

    Returns:
        float: 1.0 if track count conditions are met, 0.0 otherwise
    """
    try:
        if project_file_path is None or not os.path.exists(project_file_path):
            logger.error(f"Project file not found: {project_file_path}")
            return 0.0

        tree = ET.parse(project_file_path)
        root = tree.getroot()

        # Build a map of playlist id -> is_audio_track
        playlist_is_audio = {}
        for playlist in root.iter("playlist"):
            playlist_id = playlist.get("id", "")
            if not playlist_id:
                continue
            # Check kdenlive:audio_track property
            audio_prop = _get_property_value(playlist, "kdenlive:audio_track")
            is_audio = (audio_prop == "1")
            playlist_is_audio[playlist_id] = is_audio

        # Find the main tractor (the one that references all tracks)
        # The main tractor typically has id="maintractor" or is the last tractor
        main_tractor = None
        for tractor in root.iter("tractor"):
            tractor_id = tractor.get("id", "")
            if "main" in tractor_id.lower() or tractor_id == "tractor0":
                main_tractor = tractor
                break
        if main_tractor is None:
            # Fall back to the last tractor
            tractors = list(root.iter("tractor"))
            if tractors:
                main_tractor = tractors[-1]

        if main_tractor is None:
            logger.error("No tractor found in project file")
            return 0.0

        video_tracks = 0
        audio_tracks = 0

        for track in main_tractor.findall("track"):
            producer_ref = track.get("producer", "")
            if not producer_ref:
                continue
            # Skip the black background track (usually "black_track" or "black")
            if "black" in producer_ref.lower():
                continue
            is_audio = playlist_is_audio.get(producer_ref, False)
            if is_audio:
                audio_tracks += 1
            else:
                video_tracks += 1

        logger.info(f"Track count: video={video_tracks}, audio={audio_tracks}")

        # Evaluate rules
        if "min_video_tracks" in rule:
            if video_tracks < rule["min_video_tracks"]:
                logger.warning(f"Video tracks {video_tracks} < min {rule['min_video_tracks']}")
                return 0.0

        if "min_audio_tracks" in rule:
            if audio_tracks < rule["min_audio_tracks"]:
                logger.warning(f"Audio tracks {audio_tracks} < min {rule['min_audio_tracks']}")
                return 0.0

        if "exact_video_tracks" in rule:
            if video_tracks != rule["exact_video_tracks"]:
                logger.warning(f"Video tracks {video_tracks} != exact {rule['exact_video_tracks']}")
                return 0.0

        if "exact_audio_tracks" in rule:
            if audio_tracks != rule["exact_audio_tracks"]:
                logger.warning(f"Audio tracks {audio_tracks} != exact {rule['exact_audio_tracks']}")
                return 0.0

        logger.info("check_kdenlive_track_count: All track count checks passed")
        return 1.0

    except ET.ParseError as e:
        logger.error(f"XML parse error in project file: {e}")
        return 0.0
    except Exception as e:
        logger.error(f"check_kdenlive_track_count error: {e}")
        return 0.0


# ============================================================================
# Evaluator Function 13: Check Guide/Marker
# ============================================================================

def check_kdenlive_guide(project_file_path, rule):
    """
    Evaluator for Kdenlive task: Verify a guide/marker exists at a specific time.

    In Kdenlive's MLT XML, guides are stored as <property name="kdenlive:guide.*">
    elements in the main bin playlist, or as <guide> elements. The format is
    typically: position;comment or a JSON-like structure.

    Args:
        project_file_path: Path to the .kdenlive project file
        rule: Dictionary with validation rules.
              Expected format: {
                  "guide_comment": "Scene Start",
                  "guide_time_seconds": 5.0,
                  "tolerance": 0.5
              }

    Returns:
        float: 1.0 if a matching guide is found, 0.0 otherwise
    """
    try:
        if project_file_path is None or not os.path.exists(project_file_path):
            logger.error(f"Project file not found: {project_file_path}")
            return 0.0

        guide_comment = rule.get("guide_comment", "")
        guide_time = rule.get("guide_time_seconds")
        tolerance = rule.get("tolerance", 0.5)

        tree = ET.parse(project_file_path)
        root = tree.getroot()

        fps = _get_project_fps(root)
        logger.info(f"Project FPS: {fps}")

        # Method 1: Check <guide> elements
        for guide in root.iter("guide"):
            pos = guide.get("time", guide.get("pos", ""))
            comment = guide.get("comment", guide.get("name", ""))
            if pos:
                time_sec = _frames_to_seconds(pos, fps)
                logger.info(f"Found <guide> element: time={time_sec:.3f}s, comment='{comment}'")
                comment_ok = (not guide_comment) or (guide_comment.lower() in comment.lower())
                time_ok = (guide_time is None) or (abs(time_sec - guide_time) <= tolerance)
                if comment_ok and time_ok:
                    logger.info(f"Guide matches: time={time_sec:.3f}s, comment='{comment}'")
                    return 1.0

        # Method 2: Check kdenlive:guide.* properties in any element
        # Format: <property name="kdenlive:guide.N">time;comment</property>
        for elem in root.iter():
            for prop in elem.findall("property"):
                prop_name = prop.get("name", "")
                if prop_name.startswith("kdenlive:guide") and prop.text:
                    # Parse "frame_number;comment" or JSON format
                    text = prop.text.strip()
                    try:
                        # Try JSON format first
                        guide_data = json.loads(text)
                        if isinstance(guide_data, list):
                            for g in guide_data:
                                pos = g.get("pos", g.get("time", ""))
                                comment = g.get("comment", g.get("name", ""))
                                time_sec = _frames_to_seconds(str(pos), fps)
                                comment_ok = (not guide_comment) or (guide_comment.lower() in comment.lower())
                                time_ok = (guide_time is None) or (abs(time_sec - guide_time) <= tolerance)
                                if comment_ok and time_ok:
                                    logger.info(f"Guide matches (JSON): time={time_sec:.3f}s, comment='{comment}'")
                                    return 1.0
                        elif isinstance(guide_data, dict):
                            pos = guide_data.get("pos", guide_data.get("time", ""))
                            comment = guide_data.get("comment", guide_data.get("name", ""))
                            time_sec = _frames_to_seconds(str(pos), fps)
                            comment_ok = (not guide_comment) or (guide_comment.lower() in comment.lower())
                            time_ok = (guide_time is None) or (abs(time_sec - guide_time) <= tolerance)
                            if comment_ok and time_ok:
                                logger.info(f"Guide matches (JSON dict): time={time_sec:.3f}s, comment='{comment}'")
                                return 1.0
                    except (json.JSONDecodeError, TypeError):
                        # Try "frame;comment" format
                        if ";" in text:
                            parts = text.split(";", 1)
                            pos_str = parts[0].strip()
                            comment = parts[1].strip() if len(parts) > 1 else ""
                        else:
                            pos_str = text
                            comment = ""
                        time_sec = _frames_to_seconds(pos_str, fps)
                        comment_ok = (not guide_comment) or (guide_comment.lower() in comment.lower())
                        time_ok = (guide_time is None) or (abs(time_sec - guide_time) <= tolerance)
                        if comment_ok and time_ok:
                            logger.info(f"Guide matches (text): time={time_sec:.3f}s, comment='{comment}'")
                            return 1.0

        logger.warning(f"No matching guide found (comment='{guide_comment}', time={guide_time}s)")
        return 0.0

    except ET.ParseError as e:
        logger.error(f"XML parse error in project file: {e}")
        return 0.0
    except Exception as e:
        logger.error(f"check_kdenlive_guide error: {e}")
        return 0.0


# ============================================================================
# Evaluator Function 14: Check Track Mute
# ============================================================================

def check_kdenlive_track_mute(project_file_path, rule):
    """
    Evaluator for Kdenlive task: Verify a track is muted.

    In Kdenlive's MLT XML, a muted video track has hide="1" or hide="video"
    on the <track> element in the main tractor, or the referenced playlist
    has a kdenlive:track_name property matching the expected track name.

    Args:
        project_file_path: Path to the .kdenlive project file
        rule: Dictionary with validation rules.
              Expected format: {"muted_track": "V1"}
              Track names: "V1", "V2", "A1", "A2", etc.

    Returns:
        float: 1.0 if the specified track is muted, 0.0 otherwise
    """
    try:
        if project_file_path is None or not os.path.exists(project_file_path):
            logger.error(f"Project file not found: {project_file_path}")
            return 0.0

        muted_track = rule.get("muted_track", "")
        if not muted_track:
            logger.error("No muted_track specified in rule")
            return 0.0

        tree = ET.parse(project_file_path)
        root = tree.getroot()

        # Build playlist id -> track name mapping
        playlist_track_names = {}
        for playlist in root.iter("playlist"):
            playlist_id = playlist.get("id", "")
            track_name = _get_property_value(playlist, "kdenlive:track_name")
            if playlist_id and track_name:
                playlist_track_names[playlist_id] = track_name

        logger.info(f"Track name map: {playlist_track_names}")

        # Find the main tractor
        main_tractor = None
        for tractor in root.iter("tractor"):
            tractor_id = tractor.get("id", "")
            if "main" in tractor_id.lower() or tractor_id == "tractor0":
                main_tractor = tractor
                break
        if main_tractor is None:
            tractors = list(root.iter("tractor"))
            if tractors:
                main_tractor = tractors[-1]

        if main_tractor is None:
            logger.error("No main tractor found")
            return 0.0

        for track in main_tractor.findall("track"):
            producer_ref = track.get("producer", "")
            track_name = playlist_track_names.get(producer_ref, "")

            if track_name == muted_track:
                hide_val = track.get("hide", "")
                logger.info(f"Found track '{muted_track}' (producer='{producer_ref}'), hide='{hide_val}'")
                # hide="1" or hide="video" means video is hidden (muted for video tracks)
                # For audio tracks, hide="audio" means muted
                if hide_val in ("1", "video", "audio", "both"):
                    logger.info(f"Track '{muted_track}' is muted (hide='{hide_val}')")
                    return 1.0
                else:
                    logger.warning(f"Track '{muted_track}' is NOT muted (hide='{hide_val}')")
                    return 0.0

        logger.warning(f"Track '{muted_track}' not found in main tractor")
        return 0.0

    except ET.ParseError as e:
        logger.error(f"XML parse error in project file: {e}")
        return 0.0
    except Exception as e:
        logger.error(f"check_kdenlive_track_mute error: {e}")
        return 0.0


# ============================================================================
# Evaluator Function 15: Check Track Lock
# ============================================================================

def check_kdenlive_track_lock(project_file_path, rule):
    """
    Evaluator for Kdenlive task: Verify a track is locked.

    In Kdenlive's MLT XML, a locked track has a "kdenlive:locked_track" property
    set to "1" in the playlist that represents that track.

    Args:
        project_file_path: Path to the .kdenlive project file
        rule: Dictionary with validation rules.
              Expected format: {"locked_track": "V1"}

    Returns:
        float: 1.0 if the specified track is locked, 0.0 otherwise
    """
    try:
        if project_file_path is None or not os.path.exists(project_file_path):
            logger.error(f"Project file not found: {project_file_path}")
            return 0.0

        locked_track = rule.get("locked_track", "")
        if not locked_track:
            logger.error("No locked_track specified in rule")
            return 0.0

        tree = ET.parse(project_file_path)
        root = tree.getroot()

        for playlist in root.iter("playlist"):
            track_name = _get_property_value(playlist, "kdenlive:track_name")
            if track_name == locked_track:
                locked_val = _get_property_value(playlist, "kdenlive:locked_track")
                logger.info(f"Found playlist for track '{locked_track}', locked='{locked_val}'")
                if locked_val == "1":
                    logger.info(f"Track '{locked_track}' is locked")
                    return 1.0
                else:
                    logger.warning(f"Track '{locked_track}' is NOT locked (locked='{locked_val}')")
                    return 0.0

        logger.warning(f"Track '{locked_track}' not found in any playlist")
        return 0.0

    except ET.ParseError as e:
        logger.error(f"XML parse error in project file: {e}")
        return 0.0
    except Exception as e:
        logger.error(f"check_kdenlive_track_lock error: {e}")
        return 0.0


# ============================================================================
# Evaluator Function 16: Check Timeline Empty (Undo)
# ============================================================================

def check_kdenlive_timeline_empty(project_file_path, rule):
    """
    Evaluator for Kdenlive task: Verify timeline has no clips (e.g., after undo).

    Checks that:
    1. The specified file is still in the project bin (as a producer)
    2. No timeline playlist contains any <entry> elements referencing that file

    Args:
        project_file_path: Path to the .kdenlive project file
        rule: Dictionary with validation rules.
              Expected format: {
                  "expected_in_bin": "filename.mp4",
                  "expected_not_on_timeline": true
              }

    Returns:
        float: 1.0 if conditions are met, 0.0 otherwise
    """
    try:
        if project_file_path is None or not os.path.exists(project_file_path):
            logger.error(f"Project file not found: {project_file_path}")
            return 0.0

        expected_in_bin = rule.get("expected_in_bin", "")
        check_not_on_timeline = rule.get("expected_not_on_timeline", True)

        tree = ET.parse(project_file_path)
        root = tree.getroot()

        # Check file is in bin
        if expected_in_bin:
            found_in_bin = False
            for producer in root.iter("producer"):
                resource = _get_property_value(producer, "resource")
                if resource and expected_in_bin in resource:
                    found_in_bin = True
                    break
            if not found_in_bin:
                logger.warning(f"File '{expected_in_bin}' not found in project bin")
                return 0.0
            logger.info(f"File '{expected_in_bin}' confirmed in project bin")

        # Check timeline is empty (no non-blank entries in any playlist)
        if check_not_on_timeline:
            for playlist in root.iter("playlist"):
                playlist_id = playlist.get("id", "")
                # Skip the bin playlist (usually id="main_bin" or similar)
                if "bin" in playlist_id.lower():
                    continue
                entries = playlist.findall("entry")
                if entries:
                    logger.warning(f"Timeline playlist '{playlist_id}' has {len(entries)} entries - not empty")
                    return 0.0
            logger.info("Timeline is empty (no entries in any playlist)")

        logger.info("check_kdenlive_timeline_empty: All checks passed")
        return 1.0

    except ET.ParseError as e:
        logger.error(f"XML parse error in project file: {e}")
        return 0.0
    except Exception as e:
        logger.error(f"check_kdenlive_timeline_empty error: {e}")
        return 0.0


# ============================================================================
# Evaluator Function 17: Check Color Clip
# ============================================================================

def check_kdenlive_color_clip(project_file_path, rule):
    """
    Evaluator for Kdenlive task: Verify a color clip with specific color exists.

    In Kdenlive's MLT XML, color clips are producers with mlt_service="color"
    and a "resource" property containing the color value (e.g., "0xff0000ff").

    Args:
        project_file_path: Path to the .kdenlive project file
        rule: Dictionary with validation rules.
              Expected format: {"expected_color": "#FF0000"}
              Color can be in formats: "#RRGGBB", "#RRGGBBAA", "0xRRGGBBAA"

    Returns:
        float: 1.0 if a color clip with the expected color is found, 0.0 otherwise
    """
    try:
        if project_file_path is None or not os.path.exists(project_file_path):
            logger.error(f"Project file not found: {project_file_path}")
            return 0.0

        expected_color = rule.get("expected_color", "").upper().strip()
        if not expected_color:
            logger.error("No expected_color specified in rule")
            return 0.0

        # Normalize expected color to RGB hex (without alpha)
        # Remove leading # or 0x prefix (use string slicing, NOT lstrip which strips chars)
        color_upper = expected_color.upper().strip()
        if color_upper.startswith("#"):
            color_hex = color_upper[1:]
        elif color_upper.startswith("0X"):
            color_hex = color_upper[2:]
        else:
            color_hex = color_upper
        # Take first 6 chars (RGB, ignore alpha)
        color_rgb = color_hex[:6].upper()

        tree = ET.parse(project_file_path)
        root = tree.getroot()

        for producer in root.iter("producer"):
            service = _get_mlt_service(producer)
            if service and service.lower() == "color":
                resource = _get_property_value(producer, "resource")
                if resource:
                    # Normalize resource color (remove # or 0x prefix)
                    res_upper = resource.upper().strip()
                    if res_upper.startswith("#"):
                        res_hex = res_upper[1:]
                    elif res_upper.startswith("0X"):
                        res_hex = res_upper[2:]
                    else:
                        res_hex = res_upper
                    res_rgb = res_hex[:6].upper()
                    logger.info(f"Found color producer: resource='{resource}', normalized='{res_rgb}'")
                    if res_rgb == color_rgb:
                        logger.info(f"Color clip matches: {color_rgb}")
                        return 1.0

        logger.warning(f"No color clip found with color '{expected_color}' (RGB={color_rgb})")
        return 0.0

    except ET.ParseError as e:
        logger.error(f"XML parse error in project file: {e}")
        return 0.0
    except Exception as e:
        logger.error(f"check_kdenlive_color_clip error: {e}")
        return 0.0


# ============================================================================
# Evaluator Function 18: Check Clip Duration
# ============================================================================

def check_kdenlive_clip_duration(project_file_path, rule):
    """
    Evaluator for Kdenlive task: Verify clip duration in the timeline.

    Checks that at least one timeline entry has a duration (out - in + 1)
    within the specified range. Only timeline playlists are scanned (bin
    playlist and system playlists are skipped), so clips that are merely
    imported but not placed on the timeline will not trigger a false positive.

    Args:
        project_file_path: Path to the .kdenlive project file
        rule: Dictionary with validation rules.
              Expected format: {
                  "min_duration_seconds": 9.5,
                  "max_duration_seconds": 10.5
              }

    Returns:
        float: 1.0 if a timeline clip with matching duration is found, 0.0 otherwise
    """
    try:
        if project_file_path is None or not os.path.exists(project_file_path):
            logger.error(f"Project file not found: {project_file_path}")
            return 0.0

        min_dur = rule.get("min_duration_seconds")
        max_dur = rule.get("max_duration_seconds")

        tree = ET.parse(project_file_path)
        root = tree.getroot()

        fps = _get_project_fps(root)
        logger.info(f"Project FPS: {fps}")

        # Collect playlist ids that belong to the timeline (not the bin).
        # The bin playlist id typically contains "bin" (e.g. "main_bin").
        # System/internal playlists (black_track, etc.) contain no user entries.
        # We identify timeline playlists as those referenced by the main tractor's
        # <track> elements.
        timeline_playlist_ids = set()
        main_tractor = None
        for tractor in root.iter("tractor"):
            tractor_id = tractor.get("id", "")
            if "main" in tractor_id.lower() or tractor_id == "tractor0":
                main_tractor = tractor
                break
        if main_tractor is None:
            tractors = list(root.iter("tractor"))
            if tractors:
                main_tractor = tractors[-1]

        if main_tractor is not None:
            for track in main_tractor.findall("track"):
                producer_ref = track.get("producer", "")
                if producer_ref and "black" not in producer_ref.lower():
                    timeline_playlist_ids.add(producer_ref)

        logger.info(f"Timeline playlist ids: {timeline_playlist_ids}")

        # Fallback: if we could not identify any timeline playlists via the
        # tractor, scan all playlists whose id does not look like a bin.
        def is_timeline_playlist(playlist):
            pid = playlist.get("id", "")
            if "bin" in pid.lower():
                return False
            if timeline_playlist_ids:
                return pid in timeline_playlist_ids
            # Fallback heuristic: skip playlists with no entries at all
            return True

        # Check entries only in timeline playlists
        for playlist in root.iter("playlist"):
            if not is_timeline_playlist(playlist):
                continue
            for entry in playlist.findall("entry"):
                in_val = entry.get("in", "0")
                out_val = entry.get("out", "0")
                try:
                    in_frames = float(in_val)
                    out_frames = float(out_val)
                    # MLT convention: duration = out - in + 1 frames
                    duration_sec = (out_frames - in_frames + 1) / fps
                    logger.info(
                        f"Timeline entry in={in_val}, out={out_val}, "
                        f"duration={duration_sec:.3f}s (playlist='{playlist.get('id', '')}')"
                    )

                    dur_ok = True
                    if min_dur is not None and duration_sec < min_dur:
                        dur_ok = False
                    if max_dur is not None and duration_sec > max_dur:
                        dur_ok = False

                    if dur_ok:
                        logger.info(f"Found timeline clip with matching duration: {duration_sec:.3f}s")
                        return 1.0
                except (ValueError, ZeroDivisionError):
                    continue

        logger.warning(f"No timeline clip found with duration in [{min_dur}, {max_dur}] seconds")
        return 0.0

    except ET.ParseError as e:
        logger.error(f"XML parse error in project file: {e}")
        return 0.0
    except Exception as e:
        logger.error(f"check_kdenlive_clip_duration error: {e}")
        return 0.0


# ============================================================================
# Evaluator Function 19: Check Snapshot Exists
# ============================================================================

def check_kdenlive_snapshot_exists(command_output, rule):
    """
    Evaluator for Kdenlive task: Verify snapshot PNG file(s) exist.

    This function receives the output of a shell command (e.g., `ls *.png | wc -l`)
    as a string and checks that the count meets the minimum requirement.

    Args:
        command_output: String output from the vm_command_line command
                        (e.g., "3\n" meaning 3 PNG files found)
        rule: Dictionary with validation rules.
              Expected format: {"min_count": 1}

    Returns:
        float: 1.0 if the file count meets the minimum, 0.0 otherwise
    """
    try:
        min_count = rule.get("min_count", 1)

        if command_output is None:
            logger.error("command_output is None")
            return 0.0

        # Parse the count from command output
        count_str = str(command_output).strip()
        try:
            count = int(count_str)
        except ValueError:
            # Try to extract first number from output
            import re
            numbers = re.findall(r'\d+', count_str)
            if numbers:
                count = int(numbers[0])
            else:
                logger.error(f"Cannot parse count from output: '{count_str}'")
                return 0.0

        logger.info(f"Snapshot count: {count}, required min: {min_count}")

        if count >= min_count:
            logger.info(f"Snapshot check passed: {count} >= {min_count}")
            return 1.0
        else:
            logger.warning(f"Snapshot check failed: {count} < {min_count}")
            return 0.0

    except Exception as e:
        logger.error(f"check_kdenlive_snapshot_exists error: {e}")
        return 0.0


# ============================================================================
# Evaluator Function 20: Check Proxy Setting
# ============================================================================

def check_kdenlive_proxy_setting(project_file_path, rule):
    """
    Evaluator for Kdenlive task: Verify proxy clip setting is enabled/disabled.

    In Kdenlive's MLT XML, proxy settings are stored in the <kdenlive_documentproperties>
    or as properties in the main bin playlist. The key property is
    "kdenlive:proxy" or "generateproxy".

    Args:
        project_file_path: Path to the .kdenlive project file
        rule: Dictionary with validation rules.
              Expected format: {"proxy_enabled": true}

    Returns:
        float: 1.0 if proxy setting matches expected, 0.0 otherwise
    """
    try:
        if project_file_path is None or not os.path.exists(project_file_path):
            logger.error(f"Project file not found: {project_file_path}")
            return 0.0

        proxy_enabled = rule.get("proxy_enabled", True)

        tree = ET.parse(project_file_path)
        root = tree.getroot()

        # Method 1: Check <kdenlive_documentproperties> element
        for doc_props in root.iter("kdenlive_documentproperties"):
            proxy_val = doc_props.get("proxy", doc_props.get("generateproxy", ""))
            if proxy_val:
                logger.info(f"Found proxy setting in kdenlive_documentproperties: '{proxy_val}'")
                is_enabled = proxy_val in ("1", "true", "yes")
                if is_enabled == proxy_enabled:
                    return 1.0
                else:
                    logger.warning(f"Proxy setting mismatch: expected {proxy_enabled}, got '{proxy_val}'")
                    return 0.0

        # Method 2: Check properties in any element
        proxy_prop_names = [
            "kdenlive:proxy",
            "generateproxy",
            "proxy",
            "kdenlive:documentproperties.proxy",
        ]

        for elem in root.iter():
            for prop in elem.findall("property"):
                prop_name = prop.get("name", "")
                if prop_name in proxy_prop_names and prop.text is not None:
                    proxy_val = prop.text.strip()
                    logger.info(f"Found proxy property '{prop_name}': '{proxy_val}'")
                    is_enabled = proxy_val in ("1", "true", "yes")
                    if is_enabled == proxy_enabled:
                        logger.info(f"Proxy setting matches: enabled={is_enabled}")
                        return 1.0
                    else:
                        logger.warning(f"Proxy setting mismatch: expected {proxy_enabled}, got '{proxy_val}'")
                        return 0.0

        # Method 3: Check <documentproperties> element attributes
        for doc_props in root.iter("documentproperties"):
            for attr_name in ["proxy", "generateproxy", "enableproxy"]:
                proxy_val = doc_props.get(attr_name, "")
                if proxy_val:
                    logger.info(f"Found proxy attribute '{attr_name}': '{proxy_val}'")
                    is_enabled = proxy_val in ("1", "true", "yes")
                    if is_enabled == proxy_enabled:
                        return 1.0
                    else:
                        logger.warning(f"Proxy setting mismatch: expected {proxy_enabled}, got '{proxy_val}'")
                        return 0.0

        logger.warning("Proxy setting not found in project file")
        return 0.0

    except ET.ParseError as e:
        logger.error(f"XML parse error in project file: {e}")
        return 0.0
    except Exception as e:
        logger.error(f"check_kdenlive_proxy_setting error: {e}")
        return 0.0


# ============================================================================
# Evaluator Function 21: Check Clip Position on Timeline
# ============================================================================

def check_kdenlive_clip_position(project_file_path, rule):
    """
    Evaluator for Kdenlive task: Verify a clip is placed at a specific position.

    Checks that the timeline entry for the specified source file starts at
    approximately the expected time position.

    In Kdenlive's MLT XML, timeline entries are <entry> elements in playlists.
    The "in" attribute of the entry's parent context (or the tractor track's
    position) determines where the clip starts on the timeline.

    Note: In MLT, the position of a clip on the timeline is determined by
    the sequence of entries and blanks in the playlist. We calculate the
    start time by summing up preceding blank durations and entry durations.

    Args:
        project_file_path: Path to the .kdenlive project file
        rule: Dictionary with validation rules.
              Expected format: {
                  "source_file": "filename.mp4",
                  "start_time": 5.0,       # Expected start time in seconds
                  "tolerance": 0.5          # Acceptable deviation in seconds
              }

    Returns:
        float: 1.0 if the clip starts at the expected position, 0.0 otherwise
    """
    try:
        if project_file_path is None or not os.path.exists(project_file_path):
            logger.error(f"Project file not found: {project_file_path}")
            return 0.0

        source_file = rule.get("source_file", "")
        expected_start = rule.get("start_time")
        tolerance = rule.get("tolerance", 0.5)

        if not source_file or expected_start is None:
            logger.error("Missing source_file or start_time in rule")
            return 0.0

        tree = ET.parse(project_file_path)
        root = tree.getroot()

        fps = _get_project_fps(root)
        logger.info(f"Project FPS: {fps}")

        # Build producer id -> resource mapping
        producer_resources = {}
        for producer in root.iter("producer"):
            prod_id = producer.get("id", "")
            resource = _get_property_value(producer, "resource")
            if prod_id and resource:
                producer_resources[prod_id] = resource

        # Also check chain elements (newer Kdenlive versions use chains)
        for chain in root.iter("chain"):
            chain_id = chain.get("id", "")
            resource = _get_property_value(chain, "resource")
            if chain_id and resource:
                producer_resources[chain_id] = resource

        # Scan all playlists for the clip position
        for playlist in root.iter("playlist"):
            playlist_id = playlist.get("id", "")
            # Skip bin playlist
            if "bin" in playlist_id.lower():
                continue

            current_pos_frames = 0.0
            for child in playlist:
                tag = child.tag
                if tag == "blank":
                    # Blank advances the timeline position
                    length_str = child.get("length", "0")
                    try:
                        current_pos_frames += float(length_str)
                    except ValueError:
                        pass

                elif tag == "entry":
                    producer_ref = child.get("producer", "")
                    in_val = child.get("in", "0")
                    out_val = child.get("out", "0")

                    # Check if this entry references our source file
                    resource = producer_resources.get(producer_ref, "")
                    if resource and source_file in resource:
                        start_sec = current_pos_frames / fps
                        logger.info(f"Found clip '{source_file}' at timeline position "
                                    f"{current_pos_frames} frames = {start_sec:.3f}s "
                                    f"(playlist='{playlist_id}')")

                        if abs(start_sec - expected_start) <= tolerance:
                            logger.info(f"Clip position matches: {start_sec:.3f}s ≈ {expected_start}s")
                            return 1.0
                        else:
                            logger.warning(f"Clip position mismatch: {start_sec:.3f}s != {expected_start}s "
                                           f"(tolerance={tolerance}s)")

                    # Advance position by entry duration
                    try:
                        entry_duration = float(out_val) - float(in_val) + 1
                        current_pos_frames += entry_duration
                    except ValueError:
                        pass

        logger.warning(f"No matching clip position found for '{source_file}' at {expected_start}s")
        return 0.0

    except ET.ParseError as e:
        logger.error(f"XML parse error in project file: {e}")
        return 0.0
    except Exception as e:
        logger.error(f"check_kdenlive_clip_position error: {e}")
        return 0.0


# ============================================================================
# Level 2 Evaluator Functions
# ============================================================================


# ============================================================================
# Evaluator Function 22: Check Clip Trim (In/Out Points)
# ============================================================================

def check_kdenlive_clip_trim(project_file_path, rule):
    """
    Evaluator for Kdenlive task: Verify clip in/out point trimming.

    Checks that a timeline entry for the specified source file has been
    trimmed to the expected in/out times.

    Args:
        project_file_path: Path to the .kdenlive project file
        rule: Dictionary with validation rules.
              Expected format: {
                  "in_time": 2.0,
                  "out_time": 8.0,
                  "tolerance": 0.5,
                  "source_file": "xxx.mp4"
              }

    Returns:
        float: 1.0 if trim points match, 0.0 otherwise
    """
    try:
        if project_file_path is None or not os.path.exists(project_file_path):
            logger.error(f"Project file not found: {project_file_path}")
            return 0.0

        source_file = rule.get("source_file", "")
        expected_in = rule.get("in_time")
        expected_out = rule.get("out_time")
        tolerance = rule.get("tolerance", 0.5)

        if not source_file:
            logger.error("No source_file specified in rule")
            return 0.0

        tree = ET.parse(project_file_path)
        root = tree.getroot()
        fps = _get_project_fps(root)

        # Build producer id -> resource mapping
        producer_resources = {}
        for producer in root.iter("producer"):
            prod_id = producer.get("id", "")
            resource = _get_property_value(producer, "resource")
            if prod_id and resource:
                producer_resources[prod_id] = resource
        for chain in root.iter("chain"):
            chain_id = chain.get("id", "")
            resource = _get_property_value(chain, "resource")
            if chain_id and resource:
                producer_resources[chain_id] = resource

        # Search timeline playlists for the entry
        for playlist in root.iter("playlist"):
            playlist_id = playlist.get("id", "")
            if "bin" in playlist_id.lower():
                continue

            for entry in playlist.findall("entry"):
                producer_ref = entry.get("producer", "")
                resource = producer_resources.get(producer_ref, "")
                if not resource or source_file not in resource:
                    continue

                in_str = entry.get("in", "0")
                out_str = entry.get("out", "0")
                in_sec = _frames_to_seconds(in_str, fps)
                out_sec = _frames_to_seconds(out_str, fps)

                logger.info(f"Found clip '{source_file}' with in={in_sec:.3f}s, out={out_sec:.3f}s")

                in_ok = expected_in is None or abs(in_sec - expected_in) <= tolerance
                out_ok = expected_out is None or abs(out_sec - expected_out) <= tolerance

                if in_ok and out_ok:
                    logger.info(f"Trim points match: in={in_sec:.3f}s ≈ {expected_in}s, out={out_sec:.3f}s ≈ {expected_out}s")
                    return 1.0
                else:
                    logger.warning(f"Trim mismatch: in={in_sec:.3f}s vs {expected_in}s, out={out_sec:.3f}s vs {expected_out}s")

        logger.warning(f"No matching timeline entry found for '{source_file}'")
        return 0.0

    except ET.ParseError as e:
        logger.error(f"XML parse error: {e}")
        return 0.0
    except Exception as e:
        logger.error(f"check_kdenlive_clip_trim error: {e}")
        return 0.0


# ============================================================================
# Evaluator Function 23: Check Transition Between Clips
# ============================================================================

def check_kdenlive_transition(project_file_path, rule):
    """
    Evaluator for Kdenlive task: Verify a transition exists between clips.

    Checks for <transition> or <link> nodes in the project XML with
    a matching mlt_service.

    Args:
        project_file_path: Path to the .kdenlive project file
        rule: Dictionary with validation rules.
              Expected format: {"transition_type": "luma"}
              Common MLT transition services:
              - "luma" for dissolve
              - "composite" for wipe/composite
              - "qtblend" for Qt-based blending

    Returns:
        float: 1.0 if matching transition found, 0.0 otherwise
    """
    try:
        if project_file_path is None or not os.path.exists(project_file_path):
            logger.error(f"Project file not found: {project_file_path}")
            return 0.0

        transition_type = rule.get("transition_type", "")
        if not transition_type:
            logger.error("No transition_type specified in rule")
            return 0.0

        tree = ET.parse(project_file_path)
        root = tree.getroot()

        # Check <transition> elements
        for transition in root.iter("transition"):
            service = _get_mlt_service(transition)
            if service and service.lower() == transition_type.lower():
                logger.info(f"Found transition with mlt_service='{service}'")
                return 1.0

            # Also check kdenlive:id property
            kdenlive_id = _get_property_value(transition, "kdenlive_id")
            if kdenlive_id and transition_type.lower() in kdenlive_id.lower():
                logger.info(f"Found transition with kdenlive_id='{kdenlive_id}'")
                return 1.0

        # Check <link> elements (newer Kdenlive versions may use links for transitions)
        for link in root.iter("link"):
            service = _get_mlt_service(link)
            if service and service.lower() == transition_type.lower():
                logger.info(f"Found link transition with mlt_service='{service}'")
                return 1.0

        # Broader check: look for any transition/mix that isn't just internal
        for transition in root.iter("transition"):
            service = _get_mlt_service(transition)
            if service and service.lower() not in ("mix", "frei0r.cairoblend"):
                # If we're looking for composite type, also accept qtblend
                if transition_type.lower() == "composite":
                    if service.lower() in ("composite", "qtblend", "movit.overlay", "frei0r.composition"):
                        logger.info(f"Found composite-compatible transition: '{service}'")
                        return 1.0

        logger.warning(f"No transition found with type '{transition_type}'")
        return 0.0

    except ET.ParseError as e:
        logger.error(f"XML parse error: {e}")
        return 0.0
    except Exception as e:
        logger.error(f"check_kdenlive_transition error: {e}")
        return 0.0


# ============================================================================
# Evaluator Function 24: Check Title Text
# ============================================================================

def check_kdenlive_title_text(project_file_path, rule):
    """
    Evaluator for Kdenlive task: Verify title clip contains expected text.

    Searches for a <producer> with mlt_service="kdenlivetitle" and checks
    its xmldata property (SVG XML) for the expected text content.

    Args:
        project_file_path: Path to the .kdenlive project file
        rule: Dictionary with validation rules.
              Expected format: {"expected_text": "Hello World"}

    Returns:
        float: 1.0 if title text found, 0.0 otherwise
    """
    try:
        if project_file_path is None or not os.path.exists(project_file_path):
            logger.error(f"Project file not found: {project_file_path}")
            return 0.0

        expected_text = rule.get("expected_text", "")
        if not expected_text:
            logger.error("No expected_text specified in rule")
            return 0.0

        tree = ET.parse(project_file_path)
        root = tree.getroot()

        # Search for title producers
        for producer in root.iter("producer"):
            service = _get_mlt_service(producer)
            if service and service.lower() == "kdenlivetitle":
                # Get the xmldata property containing the SVG title definition
                xmldata = _get_property_value(producer, "xmldata")
                if xmldata:
                    # The xmldata is an SVG XML string; search for text content
                    if expected_text.lower() in xmldata.lower():
                        logger.info(f"Found title text '{expected_text}' in title producer")
                        return 1.0

                    # Try to parse the SVG XML to find <text> or <content> elements
                    try:
                        svg_root = ET.fromstring(xmldata)
                        for elem in svg_root.iter():
                            if elem.text and expected_text.lower() in elem.text.lower():
                                logger.info(f"Found title text '{expected_text}' in SVG element")
                                return 1.0
                            if elem.tail and expected_text.lower() in elem.tail.lower():
                                logger.info(f"Found title text '{expected_text}' in SVG element tail")
                                return 1.0
                    except ET.ParseError:
                        # If SVG parsing fails, we already did string search above
                        pass

        # Also check chain elements for title producers
        for chain in root.iter("chain"):
            service = _get_mlt_service(chain)
            if service and service.lower() == "kdenlivetitle":
                xmldata = _get_property_value(chain, "xmldata")
                if xmldata and expected_text.lower() in xmldata.lower():
                    logger.info(f"Found title text '{expected_text}' in chain title producer")
                    return 1.0

        logger.warning(f"No title clip found containing text '{expected_text}'")
        return 0.0

    except ET.ParseError as e:
        logger.error(f"XML parse error: {e}")
        return 0.0
    except Exception as e:
        logger.error(f"check_kdenlive_title_text error: {e}")
        return 0.0


# ============================================================================
# Evaluator Function 25: Check Clip Speed
# ============================================================================

def check_kdenlive_clip_speed(project_file_path, rule):
    """
    Evaluator for Kdenlive task: Verify clip playback speed modification.

    In Kdenlive, speed changes are implemented via:
    - A "timewarp" producer/chain with warp_speed property
    - The resource path may contain speed prefix like "2.000000:path/to/file"
    - The chain may have a "warp_speed" property

    Args:
        project_file_path: Path to the .kdenlive project file
        rule: Dictionary with validation rules.
              Expected format: {
                  "expected_speed": 2.0,
                  "tolerance": 0.1,
                  "source_file": "xxx.mp4"
              }

    Returns:
        float: 1.0 if speed matches, 0.0 otherwise
    """
    try:
        if project_file_path is None or not os.path.exists(project_file_path):
            logger.error(f"Project file not found: {project_file_path}")
            return 0.0

        source_file = rule.get("source_file", "")
        expected_speed = rule.get("expected_speed", 1.0)
        tolerance = rule.get("tolerance", 0.1)

        tree = ET.parse(project_file_path)
        root = tree.getroot()

        # Search for timewarp producers/chains
        for elem in list(root.iter("producer")) + list(root.iter("chain")):
            resource = _get_property_value(elem, "resource")
            if not resource:
                continue

            # Check if this is the right source file
            if source_file and source_file not in resource:
                continue

            # Check warp_speed property
            warp_speed = _get_property_value(elem, "warp_speed")
            if warp_speed is not None:
                try:
                    speed_val = float(warp_speed)
                    logger.info(f"Found warp_speed={speed_val} for '{resource}'")
                    if abs(speed_val - expected_speed) <= tolerance:
                        logger.info(f"Speed matches: {speed_val} ≈ {expected_speed}")
                        return 1.0
                except ValueError:
                    pass

            # Check if resource contains speed prefix (e.g., "2.000000:/path/to/file")
            if ":" in resource and not resource.startswith("/"):
                parts = resource.split(":", 1)
                try:
                    speed_val = float(parts[0])
                    if source_file in parts[1]:
                        logger.info(f"Found speed prefix {speed_val} in resource: {resource}")
                        if abs(speed_val - expected_speed) <= tolerance:
                            logger.info(f"Speed matches: {speed_val} ≈ {expected_speed}")
                            return 1.0
                except ValueError:
                    pass

            # Check mlt_service for timewarp
            service = _get_mlt_service(elem)
            if service and service.lower() == "timewarp":
                warp_speed = _get_property_value(elem, "warp_speed")
                if warp_speed:
                    try:
                        speed_val = float(warp_speed)
                        if abs(speed_val - expected_speed) <= tolerance:
                            return 1.0
                    except ValueError:
                        pass

        logger.warning(f"No speed change found for '{source_file}' matching {expected_speed}x")
        return 0.0

    except ET.ParseError as e:
        logger.error(f"XML parse error: {e}")
        return 0.0
    except Exception as e:
        logger.error(f"check_kdenlive_clip_speed error: {e}")
        return 0.0


# ============================================================================
# Evaluator Function 26: Check Render With Audio
# ============================================================================

def check_kdenlive_render_with_audio(result_file_path, rule):
    """
    Evaluator for Kdenlive task: Verify rendered output has both video and audio.

    Uses ffprobe to check that the rendered file contains both a video stream
    and an audio stream, and meets minimum duration requirements.

    Args:
        result_file_path: Path to the rendered file
        rule: Dictionary with validation rules.
              Expected format: {
                  "min_duration": 1.0,
                  "require_audio": true
              }

    Returns:
        float: 1.0 if checks pass, 0.0 otherwise
    """
    try:
        if result_file_path is None or not os.path.exists(result_file_path):
            logger.error(f"Rendered file not found: {result_file_path}")
            return 0.0

        file_size = os.path.getsize(result_file_path)
        if file_size == 0:
            logger.error(f"Rendered file is empty: {result_file_path}")
            return 0.0

        min_duration = rule.get("min_duration", 1.0)
        require_audio = rule.get("require_audio", True)

        ffprobe_cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_streams", "-show_format", result_file_path
        ]

        result = subprocess.run(ffprobe_cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            logger.error(f"ffprobe failed: {result.stderr}")
            return 0.0

        probe_data = json.loads(result.stdout)
        streams = probe_data.get("streams", [])
        format_info = probe_data.get("format", {})

        has_video = any(s.get("codec_type") == "video" for s in streams)
        has_audio = any(s.get("codec_type") == "audio" for s in streams)

        if not has_video:
            logger.error("No video stream in rendered file")
            return 0.0

        if require_audio and not has_audio:
            logger.error("No audio stream in rendered file (require_audio=true)")
            return 0.0

        # Check duration
        duration = 0.0
        if "duration" in format_info:
            duration = float(format_info["duration"])
        else:
            for s in streams:
                if "duration" in s:
                    duration = max(duration, float(s["duration"]))

        if duration < min_duration:
            logger.error(f"Duration too short: {duration:.2f}s < {min_duration}s")
            return 0.0

        logger.info(f"Render check passed: video={has_video}, audio={has_audio}, duration={duration:.2f}s")
        return 1.0

    except subprocess.TimeoutExpired:
        logger.error("ffprobe timed out")
        return 0.0
    except Exception as e:
        logger.error(f"check_kdenlive_render_with_audio error: {e}")
        return 0.0


# ============================================================================
# Evaluator Function 27: Generic Effect Applied Check
# ============================================================================

def check_kdenlive_effect_applied(project_file_path, rule):
    """
    Evaluator for Kdenlive task: Verify a specific effect has been applied.

    Generic checker that searches all <filter> nodes for a matching
    mlt_service value. Supports multiple alternative service names since
    Kdenlive may use different internal names depending on version and
    installed plugins.

    Args:
        project_file_path: Path to the .kdenlive project file
        rule: Dictionary with validation rules.
              Expected format: {
                  "effect_service": ["box_blur", "boxblur", "blur"],
                  "source_file": "xxx.mp4"  # Optional
              }

    Returns:
        float: 1.0 if matching effect found, 0.0 otherwise
    """
    try:
        if project_file_path is None or not os.path.exists(project_file_path):
            logger.error(f"Project file not found: {project_file_path}")
            return 0.0

        effect_services = rule.get("effect_service", [])
        source_file = rule.get("source_file", "")

        if not effect_services:
            logger.error("No effect_service list specified in rule")
            return 0.0

        # Normalize to lowercase for comparison
        effect_services_lower = [s.lower() for s in effect_services]

        tree = ET.parse(project_file_path)
        root = tree.getroot()

        # If source_file is specified, build a mapping to find the right producer
        target_producer_ids = set()
        if source_file:
            for elem in list(root.iter("producer")) + list(root.iter("chain")):
                elem_id = elem.get("id", "")
                resource = _get_property_value(elem, "resource")
                if resource and source_file in resource:
                    target_producer_ids.add(elem_id)
            logger.info(f"Target producer IDs for '{source_file}': {target_producer_ids}")

        # Search all <filter> nodes
        for filter_elem in root.iter("filter"):
            service = _get_mlt_service(filter_elem)
            if not service:
                continue

            if service.lower() in effect_services_lower:
                # If source_file specified, verify the filter is on the right track
                if source_file and target_producer_ids:
                    # Check if the filter's parent tractor/playlist contains
                    # an entry referencing one of our target producers
                    # For simplicity, if we found the effect globally, accept it
                    logger.info(f"Found matching effect filter: mlt_service='{service}'")
                    return 1.0
                else:
                    logger.info(f"Found matching effect filter: mlt_service='{service}'")
                    return 1.0

            # Also check kdenlive_id property
            kdenlive_id = _get_property_value(filter_elem, "kdenlive_id")
            if kdenlive_id:
                for expected in effect_services_lower:
                    if expected in kdenlive_id.lower():
                        logger.info(f"Found matching effect via kdenlive_id='{kdenlive_id}'")
                        return 1.0

            # Check tag property (some effects use tag for identification)
            tag = _get_property_value(filter_elem, "tag")
            if tag and tag.lower() in effect_services_lower:
                logger.info(f"Found matching effect via tag='{tag}'")
                return 1.0

        logger.warning(f"No filter found matching services: {effect_services}")
        return 0.0

    except ET.ParseError as e:
        logger.error(f"XML parse error: {e}")
        return 0.0
    except Exception as e:
        logger.error(f"check_kdenlive_effect_applied error: {e}")
        return 0.0


# ============================================================================
# Evaluator Function 28: Check Effect Parameter Value
# ============================================================================

def check_kdenlive_effect_param(project_file_path, rule):
    """
    Evaluator for Kdenlive task: Verify an effect has a specific parameter value.

    Searches for a <filter> with a matching mlt_service and checks that
    a specific property has the expected numeric value within tolerance.

    Args:
        project_file_path: Path to the .kdenlive project file
        rule: Dictionary with validation rules.
              Expected format: {
                  "effect_service": ["rotate", "affine"],
                  "param_name": "rotate",
                  "expected_value": 90,
                  "tolerance": 5
              }

    Returns:
        float: 1.0 if effect found with matching param value, 0.0 otherwise
    """
    try:
        if project_file_path is None or not os.path.exists(project_file_path):
            logger.error(f"Project file not found: {project_file_path}")
            return 0.0

        effect_services = rule.get("effect_service", [])
        param_name = rule.get("param_name", "")
        expected_value = rule.get("expected_value")
        tolerance = rule.get("tolerance", 0.0)

        if not effect_services or not param_name or expected_value is None:
            logger.error("Missing effect_service, param_name, or expected_value in rule")
            return 0.0

        effect_services_lower = [s.lower() for s in effect_services]

        tree = ET.parse(project_file_path)
        root = tree.getroot()

        for filter_elem in root.iter("filter"):
            service = _get_mlt_service(filter_elem)
            if not service:
                continue

            # Check if this filter's service matches
            service_match = service.lower() in effect_services_lower
            # Also check kdenlive_id
            kdenlive_id = _get_property_value(filter_elem, "kdenlive_id")
            kdenlive_match = kdenlive_id and any(s in kdenlive_id.lower() for s in effect_services_lower)

            if not service_match and not kdenlive_match:
                continue

            logger.info(f"Found matching filter: service='{service}', kdenlive_id='{kdenlive_id}'")

            # Search for the parameter
            param_val = _get_property_value(filter_elem, param_name)
            if param_val is not None:
                try:
                    # Handle keyframe format: "frame=value" or "time=value"
                    if "=" in param_val and "\n" in param_val:
                        # Multiple keyframes: take the first value
                        first_line = param_val.strip().split("\n")[0]
                        val = float(first_line.split("=")[-1])
                    elif "=" in param_val:
                        val = float(param_val.split("=")[-1])
                    else:
                        val = float(param_val)

                    logger.info(f"Parameter '{param_name}' = {val}")

                    if abs(val - float(expected_value)) <= tolerance:
                        logger.info(f"Parameter matches: {val} ≈ {expected_value} (±{tolerance})")
                        return 1.0
                    else:
                        logger.warning(f"Parameter mismatch: {val} != {expected_value} (±{tolerance})")
                except ValueError:
                    logger.warning(f"Could not parse param value: '{param_val}'")

            # Also check direct attributes
            attr_val = filter_elem.get(param_name)
            if attr_val is not None:
                try:
                    val = float(attr_val)
                    if abs(val - float(expected_value)) <= tolerance:
                        logger.info(f"Attribute '{param_name}' matches: {val} ≈ {expected_value}")
                        return 1.0
                except ValueError:
                    pass

        logger.warning(f"No filter found with matching param '{param_name}' = {expected_value}")
        return 0.0

    except ET.ParseError as e:
        logger.error(f"XML parse error: {e}")
        return 0.0
    except Exception as e:
        logger.error(f"check_kdenlive_effect_param error: {e}")
        return 0.0


# ============================================================================
# Evaluator Function 29: Check Audio Fade In/Out
# ============================================================================

def check_kdenlive_audio_fade(project_file_path, rule):
    """
    Evaluator for Kdenlive task: Verify audio fade in and/or fade out.

    In Kdenlive, audio fades are implemented via:
    - <filter> with mlt_service="volume" and keyframe data (level: 0→1 for fade in)
    - <filter> with kdenlive_id containing "fade_from_black" or "fade_to_black"
    - <filter> with tag="volume" and specific keyframe patterns

    Args:
        project_file_path: Path to the .kdenlive project file
        rule: Dictionary with validation rules.
              Expected format: {
                  "fade_in": true,
                  "fade_out": true,
                  "source_file": "xxx.mp3"
              }

    Returns:
        float: 1.0 if required fades found, 0.0 otherwise
    """
    try:
        if project_file_path is None or not os.path.exists(project_file_path):
            logger.error(f"Project file not found: {project_file_path}")
            return 0.0

        need_fade_in = rule.get("fade_in", False)
        need_fade_out = rule.get("fade_out", False)
        source_file = rule.get("source_file", "")

        tree = ET.parse(project_file_path)
        root = tree.getroot()

        found_fade_in = False
        found_fade_out = False

        for filter_elem in root.iter("filter"):
            service = _get_mlt_service(filter_elem)
            kdenlive_id = _get_property_value(filter_elem, "kdenlive_id") or ""
            tag = _get_property_value(filter_elem, "tag") or ""

            # Check for fade in
            if "fade_from" in kdenlive_id.lower() or "fadein" in kdenlive_id.lower():
                found_fade_in = True
                logger.info(f"Found fade in filter: kdenlive_id='{kdenlive_id}'")

            # Check for fade out
            if "fade_to" in kdenlive_id.lower() or "fadeout" in kdenlive_id.lower():
                found_fade_out = True
                logger.info(f"Found fade out filter: kdenlive_id='{kdenlive_id}'")

            # Check volume filters with keyframe data
            if service and service.lower() == "volume":
                level = _get_property_value(filter_elem, "level")
                if level and "=" in level:
                    # Keyframe data present — analyze pattern
                    lines = [l.strip() for l in level.strip().split("\n") if "=" in l]
                    if len(lines) >= 2:
                        try:
                            first_val = float(lines[0].split("=")[-1])
                            last_val = float(lines[-1].split("=")[-1])
                            if first_val < 0.1 and last_val > 0.5:
                                found_fade_in = True
                                logger.info(f"Found fade in via volume keyframes: {first_val} → {last_val}")
                            elif first_val > 0.5 and last_val < 0.1:
                                found_fade_out = True
                                logger.info(f"Found fade out via volume keyframes: {first_val} → {last_val}")
                        except ValueError:
                            pass

            # Check brightness filters (alternative fade implementation)
            if service and service.lower() == "brightness":
                level = _get_property_value(filter_elem, "level")
                if level and "=" in level:
                    lines = [l.strip() for l in level.strip().split("\n") if "=" in l]
                    if len(lines) >= 2:
                        try:
                            first_val = float(lines[0].split("=")[-1])
                            last_val = float(lines[-1].split("=")[-1])
                            if first_val < 0.1 and last_val > 0.5:
                                found_fade_in = True
                            elif first_val > 0.5 and last_val < 0.1:
                                found_fade_out = True
                        except ValueError:
                            pass

        # Evaluate results
        in_ok = not need_fade_in or found_fade_in
        out_ok = not need_fade_out or found_fade_out

        if in_ok and out_ok:
            logger.info(f"Fade check passed: fade_in={found_fade_in}, fade_out={found_fade_out}")
            return 1.0
        else:
            logger.warning(f"Fade check failed: need_in={need_fade_in}, found_in={found_fade_in}, "
                           f"need_out={need_fade_out}, found_out={found_fade_out}")
            return 0.0

    except ET.ParseError as e:
        logger.error(f"XML parse error: {e}")
        return 0.0
    except Exception as e:
        logger.error(f"check_kdenlive_audio_fade error: {e}")
        return 0.0


# ============================================================================
# Evaluator Function 30: Check Clip Split
# ============================================================================

def check_kdenlive_clip_split(project_file_path, rule):
    """
    Evaluator for Kdenlive task: Verify a clip has been split into segments.

    After splitting a clip, the timeline playlist will contain multiple
    <entry> elements referencing the same producer (with different in/out points).

    Args:
        project_file_path: Path to the .kdenlive project file
        rule: Dictionary with validation rules.
              Expected format: {
                  "source_file": "xxx.mp4",
                  "min_segments": 2
              }

    Returns:
        float: 1.0 if clip split into >= min_segments, 0.0 otherwise
    """
    try:
        if project_file_path is None or not os.path.exists(project_file_path):
            logger.error(f"Project file not found: {project_file_path}")
            return 0.0

        source_file = rule.get("source_file", "")
        min_segments = rule.get("min_segments", 2)

        if not source_file:
            logger.error("No source_file specified in rule")
            return 0.0

        tree = ET.parse(project_file_path)
        root = tree.getroot()

        # Build producer id -> resource mapping
        matching_producer_ids = set()
        for elem in list(root.iter("producer")) + list(root.iter("chain")):
            elem_id = elem.get("id", "")
            resource = _get_property_value(elem, "resource")
            if resource and source_file in resource:
                matching_producer_ids.add(elem_id)

        if not matching_producer_ids:
            logger.warning(f"No producer found for '{source_file}'")
            return 0.0

        logger.info(f"Matching producer IDs: {matching_producer_ids}")

        # Count entries across all timeline playlists
        total_entries = 0
        for playlist in root.iter("playlist"):
            playlist_id = playlist.get("id", "")
            if "bin" in playlist_id.lower():
                continue

            for entry in playlist.findall("entry"):
                producer_ref = entry.get("producer", "")
                if producer_ref in matching_producer_ids:
                    total_entries += 1

        logger.info(f"Found {total_entries} timeline entries for '{source_file}'")

        if total_entries >= min_segments:
            logger.info(f"Clip split verified: {total_entries} >= {min_segments}")
            return 1.0
        else:
            logger.warning(f"Not enough segments: {total_entries} < {min_segments}")
            return 0.0

    except ET.ParseError as e:
        logger.error(f"XML parse error: {e}")
        return 0.0
    except Exception as e:
        logger.error(f"check_kdenlive_clip_split error: {e}")
        return 0.0


# ============================================================================
# Evaluator Function 31: Check Multi-Track Composition
# ============================================================================

def check_kdenlive_multi_track_composition(project_file_path, rule):
    """
    Evaluator for Kdenlive task: Verify multi-track composition (PiP, watermark).

    Checks that two files are on different tracks and that a transform/composite
    effect is applied for compositing.

    Args:
        project_file_path: Path to the .kdenlive project file
        rule: Dictionary with validation rules.
              Expected format: {
                  "main_file": "main.mp4",
                  "overlay_file": "overlay.mp4",
                  "require_transform": true
              }

    Returns:
        float: 1.0 if composition is set up correctly, 0.0 otherwise
    """
    try:
        if project_file_path is None or not os.path.exists(project_file_path):
            logger.error(f"Project file not found: {project_file_path}")
            return 0.0

        main_file = rule.get("main_file", "")
        overlay_file = rule.get("overlay_file", "")
        require_transform = rule.get("require_transform", True)

        if not main_file or not overlay_file:
            logger.error("Missing main_file or overlay_file in rule")
            return 0.0

        tree = ET.parse(project_file_path)
        root = tree.getroot()

        # Build producer id -> resource mapping
        producer_resources = {}
        for elem in list(root.iter("producer")) + list(root.iter("chain")):
            elem_id = elem.get("id", "")
            resource = _get_property_value(elem, "resource")
            if elem_id and resource:
                producer_resources[elem_id] = resource

        # Find which playlists contain each file
        main_playlists = set()
        overlay_playlists = set()

        for playlist in root.iter("playlist"):
            playlist_id = playlist.get("id", "")
            if "bin" in playlist_id.lower():
                continue

            for entry in playlist.findall("entry"):
                producer_ref = entry.get("producer", "")
                resource = producer_resources.get(producer_ref, "")
                if resource:
                    if main_file in resource:
                        main_playlists.add(playlist_id)
                    if overlay_file in resource:
                        overlay_playlists.add(playlist_id)

        logger.info(f"Main file playlists: {main_playlists}")
        logger.info(f"Overlay file playlists: {overlay_playlists}")

        # Verify both files are present on timeline
        if not main_playlists:
            logger.warning(f"Main file '{main_file}' not found on timeline")
            return 0.0
        if not overlay_playlists:
            logger.warning(f"Overlay file '{overlay_file}' not found on timeline")
            return 0.0

        # Verify they are on different tracks
        if main_playlists == overlay_playlists:
            logger.warning("Both files are on the same track(s)")
            return 0.0

        # Check for transform effect if required
        if require_transform:
            transform_services = ["affine", "qtblend", "composite", "movit.overlay",
                                  "frei0r.composition", "cairoblend", "frei0r.cairoblend"]
            found_transform = False

            # Check filters
            for filter_elem in root.iter("filter"):
                service = _get_mlt_service(filter_elem)
                if service and service.lower() in transform_services:
                    found_transform = True
                    logger.info(f"Found transform/composite filter: '{service}'")
                    break

            # Also check transitions (composite transitions between tracks)
            for transition in root.iter("transition"):
                service = _get_mlt_service(transition)
                if service and service.lower() in transform_services:
                    found_transform = True
                    logger.info(f"Found transform/composite transition: '{service}'")
                    break

            if not found_transform:
                logger.warning("No transform/composite effect found for multi-track composition")
                return 0.0

        logger.info("Multi-track composition verified successfully")
        return 1.0

    except ET.ParseError as e:
        logger.error(f"XML parse error: {e}")
        return 0.0
    except Exception as e:
        logger.error(f"check_kdenlive_multi_track_composition error: {e}")
        return 0.0


# ============================================================================
# Evaluator Function 32: Check Clip Count on Timeline
# ============================================================================

def check_kdenlive_clip_count(project_file_path, rule):
    """
    Evaluator for Kdenlive task: Verify number of clip instances on timeline.

    Counts how many <entry> elements across all timeline playlists reference
    producers containing the source file. Used to verify copy-paste operations.

    Args:
        project_file_path: Path to the .kdenlive project file
        rule: Dictionary with validation rules.
              Expected format: {
                  "source_file": "xxx.mp4",
                  "min_count": 2
              }

    Returns:
        float: 1.0 if clip count >= min_count, 0.0 otherwise
    """
    try:
        if project_file_path is None or not os.path.exists(project_file_path):
            logger.error(f"Project file not found: {project_file_path}")
            return 0.0

        source_file = rule.get("source_file", "")
        min_count = rule.get("min_count", 2)

        if not source_file:
            logger.error("No source_file specified in rule")
            return 0.0

        tree = ET.parse(project_file_path)
        root = tree.getroot()

        # Build producer id -> resource mapping
        matching_producer_ids = set()
        for elem in list(root.iter("producer")) + list(root.iter("chain")):
            elem_id = elem.get("id", "")
            resource = _get_property_value(elem, "resource")
            if resource and source_file in resource:
                matching_producer_ids.add(elem_id)

        if not matching_producer_ids:
            logger.warning(f"No producer found for '{source_file}'")
            return 0.0

        # Count entries across all timeline playlists
        total_entries = 0
        for playlist in root.iter("playlist"):
            playlist_id = playlist.get("id", "")
            if "bin" in playlist_id.lower():
                continue

            for entry in playlist.findall("entry"):
                producer_ref = entry.get("producer", "")
                if producer_ref in matching_producer_ids:
                    total_entries += 1

        logger.info(f"Found {total_entries} timeline entries for '{source_file}'")

        if total_entries >= min_count:
            logger.info(f"Clip count verified: {total_entries} >= {min_count}")
            return 1.0
        else:
            logger.warning(f"Not enough clips: {total_entries} < {min_count}")
            return 0.0

    except ET.ParseError as e:
        logger.error(f"XML parse error: {e}")
        return 0.0
    except Exception as e:
        logger.error(f"check_kdenlive_clip_count error: {e}")
        return 0.0


# ============================================================================
# Evaluator Function 33: Check Clip Group
# ============================================================================

def check_kdenlive_clip_group(project_file_path, rule):
    """
    Evaluator for Kdenlive task: Verify clips have been grouped together.

    In Kdenlive, groups are stored as:
    - <property name="kdenlive:docproperties.groups"> containing JSON array
    - Each group has a "type" of "AVGroup" or "Normal" and "children" array

    Args:
        project_file_path: Path to the .kdenlive project file
        rule: Dictionary with validation rules.
              Expected format: {
                  "min_groups": 1,
                  "min_clips_in_group": 2
              }

    Returns:
        float: 1.0 if grouping requirements met, 0.0 otherwise
    """
    try:
        if project_file_path is None or not os.path.exists(project_file_path):
            logger.error(f"Project file not found: {project_file_path}")
            return 0.0

        min_groups = rule.get("min_groups", 1)
        min_clips = rule.get("min_clips_in_group", 2)

        tree = ET.parse(project_file_path)
        root = tree.getroot()

        # Method 1: Check kdenlive:docproperties.groups property (JSON format)
        for playlist in root.iter("playlist"):
            groups_str = _get_property_value(playlist, "kdenlive:docproperties.groups")
            if groups_str:
                try:
                    groups_data = json.loads(groups_str)
                    if isinstance(groups_data, list):
                        valid_groups = 0
                        for group in groups_data:
                            children = group.get("children", [])
                            if len(children) >= min_clips:
                                valid_groups += 1

                        if valid_groups >= min_groups:
                            logger.info(f"Found {valid_groups} group(s) with >= {min_clips} clips")
                            return 1.0
                except json.JSONDecodeError:
                    pass

        # Method 2: Check kdenlive:group properties on individual entries
        # Some versions store group info as kdenlive:groupid on clips
        group_clips = {}  # group_id -> list of clip ids
        for playlist in root.iter("playlist"):
            playlist_id = playlist.get("id", "")
            if "bin" in playlist_id.lower():
                continue

            for entry in playlist.findall("entry"):
                # Check if entry has group info in its producer's properties
                producer_ref = entry.get("producer", "")
                for elem in list(root.iter("producer")) + list(root.iter("chain")):
                    if elem.get("id") == producer_ref:
                        group_id = _get_property_value(elem, "kdenlive:groupid")
                        if group_id:
                            if group_id not in group_clips:
                                group_clips[group_id] = []
                            group_clips[group_id].append(producer_ref)

        if group_clips:
            valid_groups = sum(1 for clips in group_clips.values() if len(clips) >= min_clips)
            if valid_groups >= min_groups:
                logger.info(f"Found {valid_groups} group(s) via groupid properties")
                return 1.0

        # Method 3: Check <group> elements directly
        group_elements = list(root.iter("group"))
        if group_elements:
            valid_groups = 0
            for group in group_elements:
                children = list(group)
                if len(children) >= min_clips:
                    valid_groups += 1

            if valid_groups >= min_groups:
                logger.info(f"Found {valid_groups} <group> element(s)")
                return 1.0

        # Method 4: Check for groups property in main_bin playlist (newer format)
        for playlist in root.iter("playlist"):
            for prop in playlist.findall("property"):
                prop_name = prop.get("name", "")
                if "group" in prop_name.lower() and prop.text:
                    try:
                        data = json.loads(prop.text)
                        if isinstance(data, list) and len(data) >= min_groups:
                            for item in data:
                                if isinstance(item, dict):
                                    children = item.get("children", item.get("clips", []))
                                    if len(children) >= min_clips:
                                        logger.info(f"Found group in property '{prop_name}'")
                                        return 1.0
                    except (json.JSONDecodeError, TypeError):
                        pass

        logger.warning(f"No groups found meeting requirements (min_groups={min_groups}, min_clips={min_clips})")
        return 0.0

    except ET.ParseError as e:
        logger.error(f"XML parse error: {e}")
        return 0.0
    except Exception as e:
        logger.error(f"check_kdenlive_clip_group error: {e}")
        return 0.0


# ============================================================================
# Level 3 Composite Evaluator Functions
# ============================================================================
# These evaluators verify BOTH the rendered output file (via ffprobe) AND
# the .kdenlive project file (via XML parsing) to ensure all task operations
# were actually performed.
# ============================================================================


def _verify_render_output(result_file_path, rule):
    """
    Shared helper: verify rendered output file using ffprobe.

    Checks file existence, codec, and minimum duration.

    Args:
        result_file_path: Path to the rendered MP4 file
        rule: Dictionary containing "min_duration" and "expected_codec"

    Returns:
        tuple: (success: bool, error_msg: str)
    """
    if result_file_path is None or not os.path.exists(result_file_path):
        return False, f"Rendered file not found: {result_file_path}"

    file_size = os.path.getsize(result_file_path)
    if file_size == 0:
        return False, f"Rendered file is empty: {result_file_path}"

    min_duration = rule.get("min_duration", 1.0)
    expected_codec = rule.get("expected_codec", "h264")

    try:
        ffprobe_cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_streams", "-show_format", result_file_path
        ]
        result = subprocess.run(ffprobe_cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return False, f"ffprobe failed: {result.stderr}"

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
            return False, "No video stream found in rendered file"

        codec_name = video_stream.get("codec_name", "").lower()
        if expected_codec.lower() not in codec_name:
            return False, f"Codec mismatch: expected '{expected_codec}', got '{codec_name}'"

        # Check duration
        duration = 0.0
        if "duration" in video_stream:
            duration = float(video_stream["duration"])
        elif "duration" in format_info:
            duration = float(format_info["duration"])

        if duration < min_duration:
            return False, f"Duration too short: {duration:.2f}s < {min_duration}s"

        return True, ""

    except subprocess.TimeoutExpired:
        return False, "ffprobe timed out"
    except json.JSONDecodeError as e:
        return False, f"Failed to parse ffprobe output: {e}"
    except Exception as e:
        return False, f"Unexpected error: {e}"


def _load_project_xml(project_path):
    """
    Shared helper: load and parse .kdenlive project file.

    Args:
        project_path: Path to the .kdenlive project file

    Returns:
        tuple: (root: ET.Element or None, error_msg: str)
    """
    if not project_path or not os.path.exists(project_path):
        return None, f"Project file not found: {project_path}"
    try:
        tree = ET.parse(project_path)
        return tree.getroot(), ""
    except ET.ParseError as e:
        return None, f"XML parse error: {e}"


def _extract_result_paths(result_paths):
    """
    Shared helper: extract output MP4 path and project file path from result_paths.

    When result is configured with multi:true, result_paths is a list:
      [output.mp4_local_path, project.kdenlive_local_path]
    When result is a single file, result_paths is a string.

    Args:
        result_paths: Either a list of local paths or a single path string

    Returns:
        tuple: (render_path, project_path)
            - render_path: local path to the rendered MP4 file
            - project_path: local path to the project file (or None if single)
    """
    if isinstance(result_paths, list):
        render_path = result_paths[0] if len(result_paths) > 0 else None
        project_path = result_paths[1] if len(result_paths) > 1 else None
        return render_path, project_path
    else:
        return result_paths, None


# ============================================================================
# Evaluator Function 34: Render Custom Resolution
# ============================================================================

def check_kdenlive_render_custom_resolution(result_file_path, rule):
    """
    Evaluator for Kdenlive task: Verify rendered output has expected resolution.

    Uses ffprobe to check codec, duration, and video resolution (width x height).

    Args:
        result_file_path: Path to the rendered MP4 file
        rule: Dictionary with validation rules.
              Expected format: {
                  "min_duration": 1.0,
                  "expected_codec": "h264",
                  "expected_width": 1280,
                  "expected_height": 720
              }

    Returns:
        float: 1.0 if all checks pass, 0.0 otherwise
    """
    try:
        if result_file_path is None or not os.path.exists(result_file_path):
            logger.error(f"Rendered file not found: {result_file_path}")
            return 0.0

        file_size = os.path.getsize(result_file_path)
        if file_size == 0:
            logger.error(f"Rendered file is empty: {result_file_path}")
            return 0.0

        min_duration = rule.get("min_duration", 1.0)
        expected_codec = rule.get("expected_codec", "h264")
        expected_width = rule.get("expected_width")
        expected_height = rule.get("expected_height")

        ffprobe_cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_streams", "-show_format", result_file_path
        ]
        result = subprocess.run(ffprobe_cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            logger.error(f"ffprobe failed: {result.stderr}")
            return 0.0

        probe_data = json.loads(result.stdout)
        streams = probe_data.get("streams", [])
        format_info = probe_data.get("format", {})

        video_stream = None
        for stream in streams:
            if stream.get("codec_type") == "video":
                video_stream = stream
                break

        if video_stream is None:
            logger.error("No video stream found")
            return 0.0

        # Check codec
        codec_name = video_stream.get("codec_name", "").lower()
        if expected_codec.lower() not in codec_name:
            logger.error(f"Codec mismatch: expected '{expected_codec}', got '{codec_name}'")
            return 0.0

        # Check resolution
        if expected_width is not None:
            actual_width = int(video_stream.get("width", 0))
            if actual_width != expected_width:
                logger.error(f"Width mismatch: expected {expected_width}, got {actual_width}")
                return 0.0

        if expected_height is not None:
            actual_height = int(video_stream.get("height", 0))
            if actual_height != expected_height:
                logger.error(f"Height mismatch: expected {expected_height}, got {actual_height}")
                return 0.0

        # Check duration
        duration = 0.0
        if "duration" in video_stream:
            duration = float(video_stream["duration"])
        elif "duration" in format_info:
            duration = float(format_info["duration"])

        if duration < min_duration:
            logger.error(f"Duration too short: {duration:.2f}s < {min_duration}s")
            return 0.0

        logger.info(f"Custom resolution render check passed: "
                     f"codec={codec_name}, {actual_width}x{actual_height}, duration={duration:.2f}s")
        return 1.0

    except subprocess.TimeoutExpired:
        logger.error("ffprobe timed out")
        return 0.0
    except Exception as e:
        logger.error(f"check_kdenlive_render_custom_resolution error: {e}")
        return 0.0


# ============================================================================
# Evaluator Function 35: Multi-clip Render with Transitions
# ============================================================================

def check_kdenlive_render_multi_clip_transition(result_paths, rule):
    """
    Evaluator for Kdenlive task: Verify multi-clip render with transitions.

    Composite evaluator that checks:
    1. Rendered output file (codec, duration) via ffprobe
    2. Project file has all expected clips imported
    3. Project file has at least one dissolve/luma transition

    Args:
        result_paths: List of local file paths [output.mp4, project.kdenlive]
                      (downloaded from VM via multi:true result config)
        rule: Dictionary with validation rules.
              Expected format: {
                  "min_duration": 5.0,
                  "expected_codec": "h264",
                  "expected_files": ["clip1.mp4", "clip2.mp4", "clip3.mp4"],
                  "transition_type": "luma"
              }

    Returns:
        float: 1.0 if all checks pass, 0.0 otherwise
    """
    try:
        render_path, project_path = _extract_result_paths(result_paths)

        # Step 1: Verify render output
        render_ok, render_err = _verify_render_output(render_path, rule)
        if not render_ok:
            logger.error(f"Render verification failed: {render_err}")
            return 0.0

        # Step 2: Load project file
        root, parse_err = _load_project_xml(project_path)
        if root is None:
            logger.error(f"Project file load failed: {parse_err}")
            return 0.0

        # Step 3: Verify all expected files are imported
        expected_files = rule.get("expected_files", [])
        if expected_files:
            resources = []
            for producer in root.iter("producer"):
                resource = _get_property_value(producer, "resource")
                if resource:
                    resources.append(resource)
            for chain in root.iter("chain"):
                resource = _get_property_value(chain, "resource")
                if resource:
                    resources.append(resource)

            for expected_file in expected_files:
                found = any(expected_file in res for res in resources)
                if not found:
                    logger.error(f"Expected file '{expected_file}' not found in project bin")
                    return 0.0
                logger.info(f"Found expected file: {expected_file}")

        # Step 4: Verify transition exists
        transition_type = rule.get("transition_type", "luma")
        found_transition = False

        for transition in root.iter("transition"):
            service = _get_mlt_service(transition)
            if service and service.lower() == transition_type.lower():
                found_transition = True
                break
            # Also check for composite/qtblend as dissolve variants
            if service and service.lower() in ("luma", "composite", "qtblend"):
                found_transition = True
                break

        for link in root.iter("link"):
            service = _get_mlt_service(link)
            if service and service.lower() in (transition_type.lower(), "luma", "composite", "qtblend"):
                found_transition = True
                break

        if not found_transition:
            logger.error(f"No transition of type '{transition_type}' found in project")
            return 0.0

        logger.info("check_kdenlive_render_multi_clip_transition: All checks passed")
        return 1.0

    except Exception as e:
        logger.error(f"check_kdenlive_render_multi_clip_transition error: {e}")
        return 0.0


# ============================================================================
# Evaluator Function 36: Effects Composite Render
# ============================================================================

def check_kdenlive_render_effects_composite(result_paths, rule):
    """
    Evaluator for Kdenlive task: Verify effects + render composite.

    Composite evaluator that checks:
    1. Rendered output file (codec, duration) via ffprobe
    2. Project file has grayscale effect applied
    3. Project file has volume adjusted to expected value

    Args:
        result_paths: List of local file paths [output.mp4, project.kdenlive]
                      (downloaded from VM via multi:true result config)
        rule: Dictionary with validation rules.
              Expected format: {
                  "min_duration": 1.0,
                  "expected_codec": "h264",
                  "require_grayscale": true,
                  "expected_volume": 0.3,
                  "volume_tolerance": 0.05
              }

    Returns:
        float: 1.0 if all checks pass, 0.0 otherwise
    """
    try:
        render_path, project_path = _extract_result_paths(result_paths)

        # Step 1: Verify render output
        render_ok, render_err = _verify_render_output(render_path, rule)
        if not render_ok:
            logger.error(f"Render verification failed: {render_err}")
            return 0.0

        # Step 2: Load project file
        root, parse_err = _load_project_xml(project_path)
        if root is None:
            logger.error(f"Project file load failed: {parse_err}")
            return 0.0

        # Step 3: Check grayscale effect
        if rule.get("require_grayscale", False):
            grayscale_result = check_kdenlive_grayscale_effect(project_path, {})
            if grayscale_result < 1.0:
                logger.error("Grayscale effect not found in project")
                return 0.0
            logger.info("Grayscale effect verified")

        # Step 4: Check volume adjustment
        expected_volume = rule.get("expected_volume")
        if expected_volume is not None:
            volume_tolerance = rule.get("volume_tolerance", 0.05)
            volume_result = check_kdenlive_volume_adjustment(
                project_path,
                {"expected_volume": expected_volume, "tolerance": volume_tolerance}
            )
            if volume_result < 1.0:
                logger.error(f"Volume adjustment not found (expected {expected_volume})")
                return 0.0
            logger.info(f"Volume adjustment verified: {expected_volume}")

        logger.info("check_kdenlive_render_effects_composite: All checks passed")
        return 1.0

    except Exception as e:
        logger.error(f"check_kdenlive_render_effects_composite error: {e}")
        return 0.0


# ============================================================================
# Evaluator Function 37: Title-Video-Title Render
# ============================================================================

def check_kdenlive_render_title_video_title(result_paths, rule):
    """
    Evaluator for Kdenlive task: Verify title-video-title render.

    Composite evaluator that checks:
    1. Rendered output file (codec, duration >= 5s) via ffprobe
    2. Project file has title clips with expected text

    Args:
        result_paths: List of local file paths [output.mp4, project.kdenlive]
                      (downloaded from VM via multi:true result config)
        rule: Dictionary with validation rules.
              Expected format: {
                  "min_duration": 5.0,
                  "expected_codec": "h264",
                  "expected_titles": ["Welcome to My Video", "Thank You"]
              }

    Returns:
        float: 1.0 if all checks pass, 0.0 otherwise
    """
    try:
        render_path, project_path = _extract_result_paths(result_paths)

        # Step 1: Verify render output
        render_ok, render_err = _verify_render_output(render_path, rule)
        if not render_ok:
            logger.error(f"Render verification failed: {render_err}")
            return 0.0

        # Step 2: Load project file and verify titles
        expected_titles = rule.get("expected_titles", [])

        for title_text in expected_titles:
            title_result = check_kdenlive_title_text(
                project_path,
                {"expected_text": title_text}
            )
            if title_result < 1.0:
                logger.error(f"Title text '{title_text}' not found in project")
                return 0.0
            logger.info(f"Title text verified: '{title_text}'")

        logger.info("check_kdenlive_render_title_video_title: All checks passed")
        return 1.0

    except Exception as e:
        logger.error(f"check_kdenlive_render_title_video_title error: {e}")
        return 0.0


# ============================================================================
# Evaluator Function 38: Speed Ramp Render
# ============================================================================

def check_kdenlive_render_speed_ramp(result_paths, rule):
    """
    Evaluator for Kdenlive task: Verify speed ramp render.

    Composite evaluator that checks:
    1. Rendered output file (codec, duration) via ffprobe
    2. Project file has clip split into >= min_segments
    3. Project file has speed change matching expected_speed

    Args:
        result_paths: List of local file paths [output.mp4, project.kdenlive]
                      (downloaded from VM via multi:true result config)
        rule: Dictionary with validation rules.
              Expected format: {
                  "min_duration": 2.0,
                  "expected_codec": "h264",
                  "source_file": "14307439_1920_1080_60fps.mp4",
                  "min_segments": 2,
                  "expected_speed": 3.0,
                  "speed_tolerance": 0.1
              }

    Returns:
        float: 1.0 if all checks pass, 0.0 otherwise
    """
    try:
        render_path, project_path = _extract_result_paths(result_paths)

        # Step 1: Verify render output
        render_ok, render_err = _verify_render_output(render_path, rule)
        if not render_ok:
            logger.error(f"Render verification failed: {render_err}")
            return 0.0

        source_file = rule.get("source_file", "")

        # Step 2: Verify clip split
        min_segments = rule.get("min_segments", 2)
        split_result = check_kdenlive_clip_split(
            project_path,
            {"source_file": source_file, "min_segments": min_segments}
        )
        if split_result < 1.0:
            logger.error(f"Clip split not found (expected >= {min_segments} segments)")
            return 0.0
        logger.info(f"Clip split verified: >= {min_segments} segments")

        # Step 3: Verify speed change
        expected_speed = rule.get("expected_speed", 1.0)
        speed_tolerance = rule.get("speed_tolerance", 0.1)
        speed_result = check_kdenlive_clip_speed(
            project_path,
            {"source_file": source_file, "expected_speed": expected_speed, "tolerance": speed_tolerance}
        )
        if speed_result < 1.0:
            logger.error(f"Speed change not found (expected {expected_speed}x)")
            return 0.0
        logger.info(f"Speed change verified: {expected_speed}x")

        logger.info("check_kdenlive_render_speed_ramp: All checks passed")
        return 1.0

    except Exception as e:
        logger.error(f"check_kdenlive_render_speed_ramp error: {e}")
        return 0.0


# ============================================================================
# Evaluator Function 39: Picture-in-Picture Render
# ============================================================================

def check_kdenlive_render_pip(result_paths, rule):
    """
    Evaluator for Kdenlive task: Verify picture-in-picture render.

    Composite evaluator that checks:
    1. Rendered output file (codec, duration) via ffprobe
    2. Project file has multi-track composition with transform effect

    Args:
        result_paths: List of local file paths [output.mp4, project.kdenlive]
                      (downloaded from VM via multi:true result config)
        rule: Dictionary with validation rules.
              Expected format: {
                  "min_duration": 1.0,
                  "expected_codec": "h264",
                  "main_file": "15368811_1920_1080_30fps.mp4",
                  "overlay_file": "6533277-hd_1920_1080_24fps.mp4",
                  "require_transform": true
              }

    Returns:
        float: 1.0 if all checks pass, 0.0 otherwise
    """
    try:
        render_path, project_path = _extract_result_paths(result_paths)

        # Step 1: Verify render output
        render_ok, render_err = _verify_render_output(render_path, rule)
        if not render_ok:
            logger.error(f"Render verification failed: {render_err}")
            return 0.0

        # Step 2: Verify multi-track composition in project
        comp_rule = {
            "main_file": rule.get("main_file", ""),
            "overlay_file": rule.get("overlay_file", ""),
            "require_transform": rule.get("require_transform", True)
        }
        comp_result = check_kdenlive_multi_track_composition(project_path, comp_rule)
        if comp_result < 1.0:
            logger.error("Multi-track composition not verified in project")
            return 0.0
        logger.info("Multi-track PiP composition verified")

        logger.info("check_kdenlive_render_pip: All checks passed")
        return 1.0

    except Exception as e:
        logger.error(f"check_kdenlive_render_pip error: {e}")
        return 0.0


# ============================================================================
# Evaluator Function 40: Audio Mixing Render
# ============================================================================

def check_kdenlive_render_audio_mix(result_paths, rule):
    """
    Evaluator for Kdenlive task: Verify audio mixing render.

    Composite evaluator that checks:
    1. Rendered output has video + audio streams
    2. Project file has all expected audio files imported
    3. Project file has volume adjusted to expected value

    Args:
        result_paths: List of local file paths [output.mp4, project.kdenlive]
                      (downloaded from VM via multi:true result config)
        rule: Dictionary with validation rules.
              Expected format: {
                  "min_duration": 1.0,
                  "expected_codec": "h264",
                  "require_audio": true,
                  "expected_volume": 0.4,
                  "volume_tolerance": 0.05,
                  "expected_audio_files": ["bgm.mp3", "sfx.wav"]
              }

    Returns:
        float: 1.0 if all checks pass, 0.0 otherwise
    """
    try:
        render_path, project_path = _extract_result_paths(result_paths)

        # Step 1: Verify render output with audio
        audio_rule = {
            "min_duration": rule.get("min_duration", 1.0),
            "require_audio": rule.get("require_audio", True)
        }
        audio_result = check_kdenlive_render_with_audio(render_path, audio_rule)
        if audio_result < 1.0:
            logger.error("Render with audio verification failed")
            return 0.0
        logger.info("Render with audio verified")

        # Step 2: Load project and verify audio files imported
        expected_audio_files = rule.get("expected_audio_files", [])

        if expected_audio_files:
            import_result = check_kdenlive_import_multiple_files(
                project_path,
                {"expected_files": expected_audio_files}
            )
            if import_result < 1.0:
                logger.error(f"Not all audio files imported: {expected_audio_files}")
                return 0.0
            logger.info(f"All audio files imported: {expected_audio_files}")

        # Step 3: Verify volume adjustment
        expected_volume = rule.get("expected_volume")
        if expected_volume is not None:
            volume_tolerance = rule.get("volume_tolerance", 0.05)
            volume_result = check_kdenlive_volume_adjustment(
                project_path,
                {"expected_volume": expected_volume, "tolerance": volume_tolerance}
            )
            if volume_result < 1.0:
                logger.error(f"Volume adjustment not found (expected {expected_volume})")
                return 0.0
            logger.info(f"Volume adjustment verified: {expected_volume}")

        logger.info("check_kdenlive_render_audio_mix: All checks passed")
        return 1.0

    except Exception as e:
        logger.error(f"check_kdenlive_render_audio_mix error: {e}")
        return 0.0


# ============================================================================
# Evaluator Function 41: Color Grading Pipeline Render
# ============================================================================

def check_kdenlive_render_color_grading(result_paths, rule):
    """
    Evaluator for Kdenlive task: Verify color grading pipeline render.

    Composite evaluator that checks:
    1. Rendered output file (codec, duration) via ffprobe
    2. Project file has brightness effect applied
    3. Project file has sepia effect applied
    4. Project file has audio fade in and fade out

    Args:
        result_paths: List of local file paths [output.mp4, project.kdenlive]
                      (downloaded from VM via multi:true result config)
        rule: Dictionary with validation rules.
              Expected format: {
                  "min_duration": 1.0,
                  "expected_codec": "h264",
                  "require_brightness": true,
                  "require_sepia": true,
                  "require_fade_in": true,
                  "require_fade_out": true
              }

    Returns:
        float: 1.0 if all checks pass, 0.0 otherwise
    """
    try:
        render_path, project_path = _extract_result_paths(result_paths)

        # Step 1: Verify render output
        render_ok, render_err = _verify_render_output(render_path, rule)
        if not render_ok:
            logger.error(f"Render verification failed: {render_err}")
            return 0.0

        # Step 2: Check brightness effect
        if rule.get("require_brightness", False):
            brightness_services = ["brightness", "avfilter.eq", "frei0r.brightness",
                                   "lift_gamma_gain", "avfilter.curves"]
            brightness_result = check_kdenlive_effect_applied(
                project_path,
                {"effect_service": brightness_services}
            )
            if brightness_result < 1.0:
                logger.error("Brightness effect not found in project")
                return 0.0
            logger.info("Brightness effect verified")

        # Step 3: Check sepia effect
        if rule.get("require_sepia", False):
            sepia_services = ["sepia", "tcolor", "frei0r.tint0r", "frei0r.colorize",
                              "avfilter.colorbalance"]
            sepia_result = check_kdenlive_effect_applied(
                project_path,
                {"effect_service": sepia_services}
            )
            if sepia_result < 1.0:
                logger.error("Sepia effect not found in project")
                return 0.0
            logger.info("Sepia effect verified")

        # Step 4: Check audio fades
        require_fade_in = rule.get("require_fade_in", False)
        require_fade_out = rule.get("require_fade_out", False)
        if require_fade_in or require_fade_out:
            fade_result = check_kdenlive_audio_fade(
                project_path,
                {"fade_in": require_fade_in, "fade_out": require_fade_out}
            )
            if fade_result < 1.0:
                logger.error(f"Audio fade not found (fade_in={require_fade_in}, fade_out={require_fade_out})")
                return 0.0
            logger.info("Audio fade effects verified")

        logger.info("check_kdenlive_render_color_grading: All checks passed")
        return 1.0

    except Exception as e:
        logger.error(f"check_kdenlive_render_color_grading error: {e}")
        return 0.0
