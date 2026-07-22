"""
Kdenlive Evaluator Functions — Task: import video+audio, add to V1/A1 tracks, group, save.

This module provides evaluator functions used by the multi-metric evaluator for
the L2 kdenlive task (383b7e01).  Each function parses the .kdenlive project file
(MLT XML format) and checks one aspect of task completion.
"""

import os
import logging
import json
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


# ============================================================================
# Helper Functions
# ============================================================================

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
# Metric 1 — Import Multiple Files (project bin)
# ============================================================================

def check_kdenlive_import_multiple_files(project_file_path, rule):
    """
    Verify that all specified files have been imported into the project bin.

    Checks that each expected file appears in at least one <producer> resource
    property in the .kdenlive project file.

    Args:
        project_file_path: Path to the .kdenlive project file
        rule: {"expected_files": ["file1.mp4", "file2.wav"]}

    Returns:
        float: 1.0 if ALL expected files are found in producer resources, 0.0 otherwise
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
# Metric 2/3 — Add Clip to Timeline
# ============================================================================

def check_kdenlive_add_to_timeline(project_file_path, rule):
    """
    Verify that a specific file has been placed on the timeline.

    Checks that a <playlist> (excluding bin playlists) contains an <entry>
    whose producer's resource references the expected file.

    Args:
        project_file_path: Path to the .kdenlive project file
        rule: {"expected_file": "sample_video.mp4"}

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

                # Direct match: entry's producer attribute references a producer
                resource = producer_resources.get(entry_producer, "")
                if resource and expected_file in resource:
                    logger.info(f"Found timeline entry referencing '{expected_file}' "
                                f"via producer '{entry_producer}' in playlist '{playlist.get('id', '')}'")
                    return 1.0

                # Indirect match: any producer resource contains expected file
                # and its id appears in the entry's producer reference
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
# Metric 4 — Clip Grouping
# ============================================================================

def check_kdenlive_clip_group(project_file_path, rule):
    """
    Verify that clips have been grouped together in the project.

    In Kdenlive, groups are stored as:
    - <property name="kdenlive:docproperties.groups"> containing JSON array
    - kdenlive:groupid on individual clip producers
    - <group> XML elements
    - JSON group data in playlist properties

    Args:
        project_file_path: Path to the .kdenlive project file
        rule: {"min_groups": 1, "min_clips_in_group": 2}

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
                            logger.info(f"Found {valid_groups} group(s) with >= {min_clips} clips "
                                        f"via kdenlive:docproperties.groups")
                            return 1.0
                except json.JSONDecodeError:
                    pass

        # Method 2: Check kdenlive:groupid on individual entries
        group_clips = {}  # group_id -> list of clip ids
        for playlist in root.iter("playlist"):
            playlist_id = playlist.get("id", "")
            if "bin" in playlist_id.lower():
                continue

            for entry in playlist.findall("entry"):
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

        # Method 4: Check for groups property in playlists (newer format)
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

        logger.warning(f"No groups found meeting requirements "
                       f"(min_groups={min_groups}, min_clips={min_clips})")
        return 0.0

    except ET.ParseError as e:
        logger.error(f"XML parse error: {e}")
        return 0.0
    except Exception as e:
        logger.error(f"check_kdenlive_clip_group error: {e}")
        return 0.0


def check_kdenlive_clip_on_specific_track(project_file_path, rule):
    try:
        if project_file_path is None or not os.path.exists(project_file_path):
            logger.error(f"Project file not found: {project_file_path}")
            return 0.0
        expected_file = rule.get("expected_file", "")
        expected_track_type = rule.get("expected_track_type")
        expected_track_number = int(rule.get("expected_track_number", 0) or 0)
        if not expected_file:
            return 0.0
        tree = ET.parse(project_file_path)
        root = tree.getroot()
        playlists = {pl.get("id", ""): pl for pl in root.iter("playlist") if pl.get("id")}
        producer_resources = {}
        for elem in list(root.iter("producer")) + list(root.iter("chain")):
            elem_id = elem.get("id", "")
            resource = _get_property_value(elem, "resource")
            if elem_id and resource:
                producer_resources[elem_id] = resource
        def resolve_playlist_ids(prod_ref, visited=None):
            if not prod_ref:
                return set()
            if visited is None:
                visited = set()
            if prod_ref in visited:
                return set()
            visited.add(prod_ref)
            if prod_ref in playlists:
                return {prod_ref}
            for tractor in root.iter("tractor"):
                if tractor.get("id", "") == prod_ref:
                    result = set()
                    for track in tractor.findall("track"):
                        result |= resolve_playlist_ids(track.get("producer", ""), visited)
                    return result
            return set()
        main_tractor = None
        for tractor in root.iter("tractor"):
            clipname = _get_property_value(tractor, "kdenlive:clipname")
            if clipname and "sequence" in clipname.lower():
                main_tractor = tractor
                break
        if main_tractor is None:
            tractors = list(root.iter("tractor"))
            if tractors:
                main_tractor = tractors[-1]
        track_map = {}
        if main_tractor is not None:
            audio_num = 0
            video_num = 0
            for track in main_tractor.findall("track"):
                prod_ref = track.get("producer", "")
                if not prod_ref or "black" in prod_ref.lower():
                    continue
                resolved = resolve_playlist_ids(prod_ref)
                if not resolved:
                    continue
                is_audio = any(playlists.get(pid) is not None and _get_property_value(playlists.get(pid), "kdenlive:audio_track") is not None for pid in resolved)
                if is_audio:
                    audio_num += 1
                    assigned = ("audio", audio_num)
                else:
                    video_num += 1
                    assigned = ("video", video_num)
                for pid in resolved:
                    track_map[pid] = assigned
        for playlist in root.iter("playlist"):
            playlist_id = playlist.get("id", "")
            if "bin" in playlist_id.lower():
                continue
            assigned = track_map.get(playlist_id)
            if assigned is None:
                audio_prop = _get_property_value(playlist, "kdenlive:audio_track")
                if audio_prop and str(audio_prop).isdigit():
                    assigned = ("audio", int(audio_prop))
            for entry in playlist.findall("entry"):
                producer_ref = entry.get("producer", "")
                resource = producer_resources.get(producer_ref, "")
                if not resource:
                    for elem_id, res in producer_resources.items():
                        if expected_file in res and elem_id in producer_ref:
                            resource = res
                            break
                if resource and expected_file in resource:
                    if expected_track_type and expected_track_number:
                        return 1.0 if assigned == (expected_track_type, expected_track_number) else 0.0
                    return 1.0
        return 0.0
    except Exception as e:
        logger.error(f"check_kdenlive_clip_on_specific_track error: {e}")
        return 0.0
