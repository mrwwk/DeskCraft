"""
Kdenlive Multi-clip Render with Transitions Evaluator.

Evaluates: import 3 clips, place consecutively on timeline,
add Dissolve transitions between each pair, save project, render to MP4.

Evaluator function:
- check_kdenlive_render_multi_clip_transition
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


def _load_project_xml(project_path):
    """
    Shared helper: load and parse .kdenlive project file.

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

    Returns:
        tuple: (render_path, project_path)
    """
    if isinstance(result_paths, list):
        render_path = result_paths[0] if len(result_paths) > 0 else None
        project_path = result_paths[1] if len(result_paths) > 1 else None
        return render_path, project_path
    else:
        return result_paths, None


def _verify_render_output(result_file_path, rule):
    """
    Shared helper: verify rendered output file using ffprobe.

    Checks file existence, codec, and minimum duration.

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
        else:
            nb_frames = video_stream.get("nb_frames")
            r_frame_rate = video_stream.get("r_frame_rate", "30/1")
            if nb_frames:
                try:
                    num, den = r_frame_rate.split("/")
                    fps = float(num) / float(den)
                    duration = float(nb_frames) / fps
                except (ValueError, ZeroDivisionError):
                    pass

        logger.info(f"Video duration: {duration:.2f}s, codec: {codec_name}")

        if duration < min_duration:
            return False, f"Duration too short: {duration:.2f}s < {min_duration}s"

        return True, ""
    except subprocess.TimeoutExpired:
        return False, "ffprobe timed out after 30 seconds"
    except json.JSONDecodeError as e:
        return False, f"Failed to parse ffprobe JSON output: {e}"
    except Exception as e:
        return False, f"ffprobe error: {e}"


# ============================================================================
# Evaluator Function: Multi-clip Render with Transitions
# ============================================================================

def check_kdenlive_render_multi_clip_transition(result_paths, rule):
    """
    Evaluator for Kdenlive task: Verify multi-clip render with transitions.

    Composite evaluator that checks:
    1. Rendered output file (codec, duration) via ffprobe
    2. Project file has all expected clips imported as producers/chains
    3. Expected clips appear consecutively on the main timeline (in order)
    4. Project file has the expected number of dissolve/luma transitions

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

        expected_files = rule.get("expected_files", [])

        # Step 3: Verify all expected files are imported (producer / chain resources)
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

        # Step 4: Build producer/chain id -> resource mapping for timeline check
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

        # Step 5: Verify clips appear consecutively on the main timeline (in order)
        # Identify timeline playlists via the main tractor's <track> elements
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

        timeline_playlist_ids = set()
        if main_tractor is not None:
            for track in main_tractor.findall("track"):
                producer_ref = track.get("producer", "")
                if producer_ref and "black" not in producer_ref.lower():
                    timeline_playlist_ids.add(producer_ref)

        # Extract the ordered sequence of expected_files references from timeline entries
        timeline_file_order = []
        for playlist in root.iter("playlist"):
            playlist_id = playlist.get("id", "")
            if "bin" in playlist_id.lower():
                continue
            if timeline_playlist_ids and playlist_id not in timeline_playlist_ids:
                continue
            for entry in playlist.findall("entry"):
                producer_ref = entry.get("producer", "")
                if producer_ref and producer_ref in producer_resources:
                    resource = producer_resources[producer_ref]
                    for ef in expected_files:
                        if ef in resource:
                            timeline_file_order.append(ef)
                            break

        if timeline_file_order and expected_files:
            expected_order = list(expected_files)
            try:
                first_idx = timeline_file_order.index(expected_order[0])
                for i in range(1, len(expected_order)):
                    pos = first_idx + i
                    if pos >= len(timeline_file_order):
                        logger.error(
                            f"Timeline: expected file '{expected_order[i]}' not found "
                            f"after '{expected_order[0]}' (timeline has only "
                            f"{len(timeline_file_order)} entries)"
                        )
                        return 0.0
                    if timeline_file_order[pos] != expected_order[i]:
                        logger.error(
                            f"Timeline: expected consecutive order {expected_order}, "
                            f"but found {timeline_file_order[first_idx:first_idx + len(expected_order)]}"
                        )
                        return 0.0
                logger.info(
                    f"Timeline consecutiveness verified: "
                    f"{timeline_file_order[first_idx:first_idx + len(expected_order)]}"
                )
            except ValueError:
                logger.error(
                    f"Timeline: first expected file '{expected_order[0]}' not found on timeline"
                )
                return 0.0

        # Step 6: Verify transition count and type
        transition_type = rule.get("transition_type", "luma")
        min_expected_transitions = max(0, len(expected_files) - 1)

        transition_count = 0
        for transition in root.iter("transition"):
            service = _get_mlt_service(transition)
            if service and service.lower() == transition_type.lower():
                transition_count += 1

        for link in root.iter("link"):
            service = _get_mlt_service(link)
            if service and service.lower() == transition_type.lower():
                transition_count += 1

        if transition_count < min_expected_transitions:
            logger.error(
                f"Expected at least {min_expected_transitions} transitions of type "
                f"'{transition_type}', but found {transition_count}"
            )
            return 0.0

        logger.info(
            f"Transition check passed: found {transition_count} transitions of type "
            f"'{transition_type}' (min required: {min_expected_transitions})"
        )

        logger.info("check_kdenlive_render_multi_clip_transition: All checks passed")
        return 1.0

    except Exception as e:
        logger.error(f"check_kdenlive_render_multi_clip_transition error: {e}")
        return 0.0
