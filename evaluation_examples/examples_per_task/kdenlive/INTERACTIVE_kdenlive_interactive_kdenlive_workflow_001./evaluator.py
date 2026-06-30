"""
Kdenlive Preview Project Evaluator

Evaluates whether the agent successfully:
1. Saved a .kdenlive preview project file
2. Placed two videos in sequence on V1 timeline track
3. Added a Dissolve (luma) transition between the two clips
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
    Returns float: Frames per second (default 25.0 if not found)
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
# Evaluator Function
# ============================================================================

def check_kdenlive_preview_project(project_file_path, expected):
    """
    Evaluator for Kdenlive interactive workflow Phase 1: Build rough cut.

    Validates that:
    1. The preview project file exists and is valid XML
    2. All expected video files are imported into the project bin
    3. Both videos are placed on the V1 timeline track, in sequence
    4. A dissolve/luma transition exists between the two clips

    Args:
        project_file_path: Path to the .kdenlive project file (from VM)
        expected: Dictionary with validation rules.
                  Expected format: {
                      "expected_files": ["video1.mp4", "video2.mp4"],
                      "transition_type": "luma"
                  }

    Returns:
        float: 1.0 if all checks pass, 0.0 otherwise
    """
    try:
        # --- Check 1: File exists and is non-empty ---
        if project_file_path is None or not os.path.exists(project_file_path):
            logger.error(f"Preview project file not found: {project_file_path}")
            return 0.0

        file_size = os.path.getsize(project_file_path)
        if file_size == 0:
            logger.error(f"Preview project file is empty: {project_file_path}")
            return 0.0

        logger.info(f"Preview project file exists, size: {file_size} bytes")

        # --- Check 2: File is valid XML ---
        try:
            tree = ET.parse(project_file_path)
            root = tree.getroot()
            if root is None:
                logger.error("XML has no root element")
                return 0.0
            logger.info(f"Valid XML with root element: <{root.tag}>")
        except ET.ParseError as e:
            logger.error(f"Invalid XML in preview project: {e}")
            return 0.0

        expected_files = expected.get("expected_files", [])
        if not expected_files:
            logger.error("No expected_files specified in rule")
            return 0.0

        transition_type = expected.get("transition_type", "luma")

        # --- Check 3: All expected files are in the project bin ---
        # Build mapping: producer id -> resource path
        producer_resources = {}
        for producer in root.iter("producer"):
            prod_id = producer.get("id", "")
            resource = _get_property_value(producer, "resource")
            if prod_id and resource:
                producer_resources[prod_id] = resource

        logger.info(f"Found {len(producer_resources)} producers in project")

        # Verify each expected file appears in at least one producer resource
        for expected_file in expected_files:
            found = any(expected_file in res for res in producer_resources.values())
            if not found:
                logger.warning(f"Expected file '{expected_file}' not found in project bin")
                return 0.0
            logger.info(f"Confirmed file in bin: {expected_file}")

        # --- Check 4: Both videos are on V1 timeline track, in sequence ---
        # Build playlist id -> track_name mapping
        playlist_track_names = {}
        for playlist_elem in root.iter("playlist"):
            pid = playlist_elem.get("id", "")
            track_name = _get_property_value(playlist_elem, "kdenlive:track_name")
            if pid and track_name:
                playlist_track_names[pid] = track_name

        logger.info(f"Track name map: {playlist_track_names}")

        # Find playlists that are V1 (video track 1)
        v1_playlist_ids = [pid for pid, tname in playlist_track_names.items() if tname == "V1"]
        if not v1_playlist_ids:
            logger.warning("No V1 track playlist found in project")
            return 0.0

        logger.info(f"V1 playlist ids: {v1_playlist_ids}")

        # Collect entries (clips) from V1 playlists and determine their order
        # by scanning blank/entry sequence
        v1_entries = []  # list of (entry_element, playlist_id)
        for playlist_elem in root.iter("playlist"):
            pid = playlist_elem.get("id", "")
            if pid not in v1_playlist_ids:
                continue
            for entry in playlist_elem.findall("entry"):
                v1_entries.append((entry, pid))

        if not v1_entries:
            logger.warning("No entries found on V1 timeline track")
            return 0.0

        logger.info(f"Found {len(v1_entries)} entries on V1")

        # Check that at least the expected number of video clips are on V1
        # by matching entry producer references to expected file resources
        matched_files = []
        for entry, _pid in v1_entries:
            producer_ref = entry.get("producer", "")
            if not producer_ref:
                continue
            resource = producer_resources.get(producer_ref, "")
            for expected_file in expected_files:
                if expected_file in resource and expected_file not in matched_files:
                    matched_files.append(expected_file)
                    logger.info(f"Found '{expected_file}' on V1 timeline via producer '{producer_ref}'")
                    break

        if len(matched_files) < len(expected_files):
            missing = [f for f in expected_files if f not in matched_files]
            logger.warning(f"Not all expected files found on V1 timeline. Missing: {missing}")
            return 0.0

        logger.info(f"All {len(expected_files)} expected files found on V1 timeline")

        # --- Check 5: Verify clips are in sequence (no gap between them) ---
        # For V1 playlists, scan entries in document order and verify
        # the two matched clips appear consecutively (no other entries between them)
        v1_entry_resources = []
        for playlist_elem in root.iter("playlist"):
            pid = playlist_elem.get("id", "")
            if pid not in v1_playlist_ids:
                continue
            for entry in playlist_elem.findall("entry"):
                producer_ref = entry.get("producer", "")
                resource = producer_resources.get(producer_ref, "")
                v1_entry_resources.append(resource)

        # Find indices of matched files in the V1 entry list
        matched_indices = []
        for i, res in enumerate(v1_entry_resources):
            for ef in expected_files:
                if ef in res and i not in matched_indices:
                    matched_indices.append(i)
                    break

        if len(matched_indices) >= 2:
            matched_indices.sort()
            # Check they are consecutive (in sequence, no other clip between them)
            is_consecutive = (matched_indices[-1] - matched_indices[0]) == (len(matched_indices) - 1)
            if is_consecutive:
                logger.info(f"Clips are in sequence on V1 (indices: {matched_indices})")
            else:
                logger.warning(f"Clips on V1 are NOT in sequence (indices: {matched_indices})")
                return 0.0
        else:
            logger.warning("Less than 2 matched clips on V1, cannot verify sequence")
            return 0.0

        # --- Check 6: A dissolve/luma transition exists ---
        transition_found = False
        for transition in root.iter("transition"):
            service = _get_mlt_service(transition)
            if service and service.lower() == transition_type.lower():
                logger.info(f"Found transition with mlt_service='{service}'")
                transition_found = True
                break

            # Also check kdenlive:id property for dissolve-like identifiers
            kdenlive_id = _get_property_value(transition, "kdenlive_id")
            if kdenlive_id and transition_type.lower() in kdenlive_id.lower():
                logger.info(f"Found transition with kdenlive_id='{kdenlive_id}'")
                transition_found = True
                break

        if not transition_found:
            # Also check <link> elements (newer Kdenlive versions)
            for link in root.iter("link"):
                service = _get_mlt_service(link)
                if service and service.lower() == transition_type.lower():
                    logger.info(f"Found link transition with mlt_service='{service}'")
                    transition_found = True
                    break

        if not transition_found:
            logger.warning(f"No transition found with type '{transition_type}'")
            return 0.0

        logger.info("check_kdenlive_preview_project: All checks passed "
                     f"(files in bin, on V1 in sequence, transition='{transition_type}')")
        return 1.0

    except ET.ParseError as e:
        logger.error(f"XML parse error in preview project: {e}")
        return 0.0
    except Exception as e:
        logger.error(f"check_kdenlive_preview_project error: {e}")
        return 0.0
