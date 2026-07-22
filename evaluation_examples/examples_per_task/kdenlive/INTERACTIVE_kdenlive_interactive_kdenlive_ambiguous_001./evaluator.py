"""
Kdenlive Evaluator for interactive_kdenlive_ambiguous_001

Evaluates whether the agent successfully created a professional opening video
for tomorrow's report. Checks:
1. Rendered MP4 output exists with correct codec and title text in project
2. A dissolve (luma) transition exists between clips in the project file
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
    """
    if isinstance(result_paths, list):
        render_path = result_paths[0] if len(result_paths) > 0 else None
        project_path = result_paths[1] if len(result_paths) > 1 else None
        return render_path, project_path
    else:
        return result_paths, None


# ============================================================================
# Evaluator Function: Check Title Text in Project
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
                xmldata = _get_property_value(producer, "xmldata")
                if xmldata:
                    if expected_text.lower() in xmldata.lower():
                        logger.info(f"Found title text '{expected_text}' in title producer")
                        return 1.0

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
# Evaluator Function: Render Output + Title Verification
# ============================================================================

def check_kdenlive_render_title_video_title(result_paths, expected=None, **options):
    """
    Evaluator for Kdenlive task: Verify title-video-title render.

    Composite evaluator that checks:
    1. Rendered output file (codec, duration) via ffprobe
    2. Project file has title clips with expected text

    Args:
        result_paths: List of local file paths [output.mp4, project.kdenlive]
                      (downloaded from VM via multi:true result config)
        expected: Dictionary with validation rules (from expected getter).
                  Expected format: {
                      "min_duration": 1.0,
                      "expected_codec": "h264",
                      "expected_titles": ["Tomorrow's Report"]
                  }

    Returns:
        float: 1.0 if all checks pass, 0.0 otherwise
    """
    try:
        # Use expected (from framework's expected getter) if provided,
        # fall back to options for backward compatibility
        rule = expected if expected else options
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
# Evaluator Function: Check Transition Between Clips
# ============================================================================

def check_kdenlive_transition(project_file_path, expected=None, **options):
    """
    Evaluator for Kdenlive task: Verify a transition exists between clips.

    Checks for <transition> or <link> nodes in the project XML with
    a matching mlt_service. In MLT, "luma" is the service name for
    dissolve-type transitions.

    Args:
        project_file_path: Path to the .kdenlive project file
        expected: Dictionary with validation rules (from expected getter).
                  Expected format: {"transition_type": "luma"}
        **options: Additional options (fallback if expected is None)

    Returns:
        float: 1.0 if matching transition found, 0.0 otherwise
    """
    try:
        # Use expected (from framework's expected getter) if provided,
        # fall back to options for backward compatibility
        rule = expected if expected else options

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

            kdenlive_id = _get_property_value(transition, "kdenlive_id")
            if kdenlive_id and transition_type.lower() in kdenlive_id.lower():
                logger.info(f"Found transition with kdenlive_id='{kdenlive_id}'")
                return 1.0

        # Check <link> elements
        for link in root.iter("link"):
            service = _get_mlt_service(link)
            if service and service.lower() == transition_type.lower():
                logger.info(f"Found link transition with mlt_service='{service}'")
                return 1.0

        logger.warning(f"No transition found with type '{transition_type}'")
        return 0.0

    except ET.ParseError as e:
        logger.error(f"XML parse error: {e}")
        return 0.0
    except Exception as e:
        logger.error(f"check_kdenlive_transition error: {e}")
        return 0.0

def check_kdenlive_import_video(project_file_path, rule):
    try:
        if project_file_path is None or not os.path.exists(project_file_path):
            logger.error(f"Project file not found: {project_file_path}")
            return 0.0
        expected_file = rule.get("expected_file", "")
        if not expected_file:
            return 0.0
        root, parse_err = _load_project_xml(project_file_path)
        if root is None:
            logger.error(f"Project file load failed: {parse_err}")
            return 0.0
        for producer in root.iter("producer"):
            resource = _get_property_value(producer, "resource")
            if resource and expected_file in resource:
                return 1.0
        for chain in root.iter("chain"):
            resource = _get_property_value(chain, "resource")
            if resource and expected_file in resource:
                return 1.0
        return 0.0
    except Exception as e:
        logger.error(f"check_kdenlive_import_video error: {e}")
        return 0.0
