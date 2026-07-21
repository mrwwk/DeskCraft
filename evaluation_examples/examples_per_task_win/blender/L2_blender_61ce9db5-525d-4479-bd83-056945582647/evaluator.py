"""
Blender Evaluator Functions — fixed for task 61ce9db5

Evaluator functions for Blender animation keyframe and frame range checks.
Each function parses JSON output from Blender Python check scripts
(run via --background --python).

Check scripts output: RESULT:{json}
VM command pattern:
    /snap/bin/blender --background /home/user/Documents/scene.blend \
        --python /tmp/check_script.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'
"""

import json
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Helper Functions
# ============================================================================

def _parse_blender_output(command_output):
    """Parse JSON output from blender check script."""
    try:
        if not command_output or not command_output.strip():
            logger.error("Empty command output")
            return None
        return json.loads(command_output.strip())
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to parse blender output: {e}")
        logger.debug(f"Raw output: {command_output!r}")
        return None


def _check_tolerance(actual, expected, tol):
    """Check if actual is within tolerance of expected."""
    if actual is None or expected is None:
        return False
    return abs(float(actual) - float(expected)) <= float(tol)


def _check_vector_tolerance(actual, expected, tol):
    """Check if each component of actual vector is within tolerance of expected."""
    if not actual or not expected:
        return False
    if len(actual) != len(expected):
        return False
    return all(abs(float(a) - float(e)) <= float(tol)
               for a, e in zip(actual, expected))


# ============================================================================
# Metric 0: check_blender_animation_keyframes
# ============================================================================

def check_blender_animation_keyframes(result_str, expected=None, **options):
    """Verify animation keyframe existence, frame distribution, and position values.

    Args:
        result_str: JSON string from check_animation.py (output of vm_command_line)
        expected: dict with rules:
            object_name (str): Object name to check (e.g. "Cube")
            min_keyframe_count (int): Minimum total keyframe count
            has_location_keys (bool): Whether location fcurves must exist
            expected_keyframe_frames (list[int]): Frames that must have location keyframes
            expected_keyframes (list[dict]): Per-frame position expectations
                [{"frame": 1, "location": [0, 0, 0]}, {"frame": 120, "location": [10, 0, 5]}]
            tolerance (float): Tolerance for position value comparison (default 0.01)
    """
    try:
        result = _parse_blender_output(result_str)
        if result is None:
            return 0.0

        if expected is None:
            expected = {}

        obj_name = expected.get("object_name", "")
        obj_anim = result.get(obj_name)
        if obj_anim is None:
            logger.warning(f"No animation data for '{obj_name}'")
            return 0.0

        tol = expected.get("tolerance", 0.01)

        # Check minimum keyframe count
        if "min_keyframe_count" in expected:
            actual_count = obj_anim.get("keyframe_count", 0)
            if actual_count < expected["min_keyframe_count"]:
                logger.warning(
                    f"Keyframe count {actual_count} < {expected['min_keyframe_count']}"
                )
                return 0.0

        # Check for location keyframes
        if expected.get("has_location_keys"):
            keyframes = obj_anim.get("keyframes", {})
            has_loc = any("location" in k for k in keyframes)
            if not has_loc:
                logger.warning("No location keyframes found")
                return 0.0

        # Check keyframes exist at expected frames
        if "expected_keyframe_frames" in expected:
            keyframes = obj_anim.get("keyframes", {})
            for expected_frame in expected["expected_keyframe_frames"]:
                found = False
                for channel, entries in keyframes.items():
                    if "location" not in channel:
                        continue
                    for entry in entries:
                        if abs(entry.get("frame", -1) - expected_frame) < 0.001:
                            found = True
                            break
                    if found:
                        break
                if not found:
                    logger.warning(
                        f"No location keyframe found at frame {expected_frame}"
                    )
                    return 0.0

        # Check specific keyframe position values
        if "expected_keyframes" in expected:
            keyframes = obj_anim.get("keyframes", {})
            location_channels = ["location[0]", "location[1]", "location[2]"]
            for expected_kf in expected["expected_keyframes"]:
                expected_frame = expected_kf["frame"]
                expected_loc = expected_kf.get("location", [])
                actual_loc = []
                for axis_idx, channel_key in enumerate(location_channels):
                    if axis_idx >= len(expected_loc):
                        break
                    entries = keyframes.get(channel_key, [])
                    val = None
                    for entry in entries:
                        if abs(entry.get("frame", -1) - expected_frame) < 0.001:
                            val = entry.get("value")
                            break
                    if val is None:
                        logger.warning(
                            f"No keyframe at frame {expected_frame} for {channel_key}"
                        )
                        return 0.0
                    actual_loc.append(val)
                if len(actual_loc) != len(expected_loc):
                    logger.warning(
                        f"Location vector length mismatch at frame {expected_frame}: "
                        f"{len(actual_loc)} != {len(expected_loc)}"
                    )
                    return 0.0
                if not _check_vector_tolerance(actual_loc, expected_loc, tol):
                    logger.warning(
                        f"Location mismatch at frame {expected_frame}: "
                        f"{actual_loc} != {expected_loc} (tol={tol})"
                    )
                    return 0.0

        return 1.0
    except Exception as e:
        logger.error(f"check_blender_animation_keyframes error: {e}")
        return 0.0


# ============================================================================
# Metric 1: check_blender_frame_range (delegates to check_blender_animation_range)
# ============================================================================

def check_blender_animation_range(result_str, expected=None, **options):
    """Verify animation frame range.

    Args:
        result_str: JSON string from check_render.py
        expected: dict with frame_start and/or frame_end
    """
    try:
        result = _parse_blender_output(result_str)
        if result is None:
            return 0.0

        if expected is None:
            expected = {}

        if "frame_start" in expected:
            if result.get("frame_start") != expected["frame_start"]:
                logger.warning(
                    f"frame_start mismatch: {result.get('frame_start')} != {expected['frame_start']}"
                )
                return 0.0
        if "frame_end" in expected:
            if result.get("frame_end") != expected["frame_end"]:
                logger.warning(
                    f"frame_end mismatch: {result.get('frame_end')} != {expected['frame_end']}"
                )
                return 0.0

        return 1.0
    except Exception as e:
        logger.error(f"check_blender_animation_range error: {e}")
        return 0.0


def check_blender_frame_range(result_str, expected=None, **options):
    """Verify frame range (alias for check_blender_animation_range).

    Args:
        result_str: JSON string from check_render.py
        expected: dict with frame_start and/or frame_end
    """
    return check_blender_animation_range(result_str, expected=expected, **options)
