"""
Blender Evaluator Functions Module

Evaluator functions for Blender 3D tasks. Each function parses JSON output
from Blender Python check scripts (run via --background --python) or checks
rendered output files (PNG/MP4).

Check scripts output: RESULT:{json}
VM command pattern:
    /snap/bin/blender --background /home/user/Documents/scene.blend \
        --python /tmp/check_script.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'
"""

import json
import logging
import os
import subprocess

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


def _find_object(result, name):
    """Find object by exact name in check_object.py output."""
    for obj in result.get("objects", []):
        if obj.get("name") == name:
            return obj
    return None


def _find_object_by_name_contains(result, substring):
    """Find object whose name contains substring."""
    for obj in result.get("objects", []):
        if substring in obj.get("name", ""):
            return obj
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
# L1 Evaluator Functions — Basic Operations
# ============================================================================

def check_blender_object_deleted(command_output, rule):
    """Verify that a named object has been deleted from the scene.

    Args:
        command_output: JSON from check_object.py
        rule: {"deleted_object": "Cube"}
    """
    try:
        result = _parse_blender_output(command_output)
        if result is None:
            return 0.0

        deleted_name = rule.get("deleted_object", "")
        object_names = result.get("object_names", [])

        if deleted_name not in object_names:
            logger.info(f"Object '{deleted_name}' confirmed deleted")
            return 1.0

        logger.warning(f"Object '{deleted_name}' still exists in scene")
        return 0.0
    except Exception as e:
        logger.error(f"check_blender_object_deleted error: {e}")
        return 0.0


def check_blender_object_exists(command_output, rule):
    """Verify that an object with specified type/name exists.

    Args:
        command_output: JSON from check_object.py
        rule: {"object_type": "MESH", "name_contains": "Sphere"}
              or {"expected_type": "MESH", "name_contains": "Sphere"}
    """
    try:
        result = _parse_blender_output(command_output)
        if result is None:
            return 0.0

        obj_type = rule.get("object_type") or rule.get("expected_type")
        name_contains = rule.get("name_contains", "")

        for obj in result.get("objects", []):
            type_match = (not obj_type) or obj.get("type") == obj_type
            name_match = (not name_contains) or name_contains in obj.get("name", "")
            if type_match and name_match:
                logger.info(f"Found matching object: {obj['name']}")
                return 1.0

        logger.warning(f"No object found matching type={obj_type}, name contains '{name_contains}'")
        return 0.0
    except Exception as e:
        logger.error(f"check_blender_object_exists error: {e}")
        return 0.0


def check_blender_object_count(command_output, rule):
    """Verify minimum object count in scene.

    Args:
        command_output: JSON from check_object.py
        rule: {"min_count": 3} or {"object_type": "CAMERA", "min_count": 2}
    """
    try:
        result = _parse_blender_output(command_output)
        if result is None:
            return 0.0

        min_count = rule.get("min_count", 1)
        obj_type = rule.get("object_type")

        if obj_type:
            count = result.get("type_counts", {}).get(obj_type, 0)
        else:
            count = result.get("object_count", 0)

        if count >= min_count:
            logger.info(f"Object count {count} >= {min_count}")
            return 1.0

        logger.warning(f"Object count {count} < {min_count}")
        return 0.0
    except Exception as e:
        logger.error(f"check_blender_object_count error: {e}")
        return 0.0


def check_blender_object_location(command_output, rule):
    """Verify object position within tolerance.

    Args:
        command_output: JSON from check_object.py
        rule: {"object_name": "Cube", "expected_location": [3.0, 0.0, 2.0], "tolerance": 0.1}
    """
    try:
        result = _parse_blender_output(command_output)
        if result is None:
            return 0.0

        obj = _find_object(result, rule.get("object_name", ""))
        if obj is None:
            logger.warning(f"Object '{rule.get('object_name')}' not found")
            return 0.0

        expected = rule.get("expected_location", [0, 0, 0])
        tol = rule.get("tolerance", 0.1)
        actual = obj.get("location", [])

        if _check_vector_tolerance(actual, expected, tol):
            logger.info(f"Location matches: {actual} ~= {expected}")
            return 1.0

        logger.warning(f"Location mismatch: {actual} != {expected} (tol={tol})")
        return 0.0
    except Exception as e:
        logger.error(f"check_blender_object_location error: {e}")
        return 0.0


def check_blender_object_scale(command_output, rule):
    """Verify object scale within tolerance.

    Args:
        command_output: JSON from check_object.py
        rule: {"object_name": "Cube", "expected_scale": [2.0, 2.0, 2.0], "tolerance": 0.1}
    """
    try:
        result = _parse_blender_output(command_output)
        if result is None:
            return 0.0

        obj = _find_object(result, rule.get("object_name", ""))
        if obj is None:
            return 0.0

        expected = rule.get("expected_scale", [1, 1, 1])
        tol = rule.get("tolerance", 0.1)
        actual = obj.get("scale", [])

        if _check_vector_tolerance(actual, expected, tol):
            return 1.0

        logger.warning(f"Scale mismatch: {actual} != {expected}")
        return 0.0
    except Exception as e:
        logger.error(f"check_blender_object_scale error: {e}")
        return 0.0


def check_blender_object_rotation(command_output, rule):
    """Verify object rotation (degrees) within tolerance.

    Args:
        command_output: JSON from check_object.py
        rule: {"object_name": "Cube", "expected_rotation_deg": [0, 0, 45], "tolerance": 2}
    """
    try:
        result = _parse_blender_output(command_output)
        if result is None:
            return 0.0

        obj = _find_object(result, rule.get("object_name", ""))
        if obj is None:
            return 0.0

        expected = rule.get("expected_rotation_deg", [0, 0, 0])
        tol = rule.get("tolerance", 2)
        actual = obj.get("rotation_euler_deg", [])

        if _check_vector_tolerance(actual, expected, tol):
            return 1.0

        logger.warning(f"Rotation mismatch: {actual} != {expected}")
        return 0.0
    except Exception as e:
        logger.error(f"check_blender_object_rotation error: {e}")
        return 0.0


def check_blender_object_renamed(command_output, rule):
    """Verify object has been renamed.

    Args:
        command_output: JSON from check_object.py
        rule: {"expected_name": "MyCube", "old_name": "Cube"}
    """
    try:
        result = _parse_blender_output(command_output)
        if result is None:
            return 0.0

        expected_name = rule.get("expected_name", "")
        old_name = rule.get("old_name", "")
        names = result.get("object_names", [])

        if expected_name in names and (not old_name or old_name not in names):
            return 1.0

        logger.warning(f"Rename check failed: expected '{expected_name}' in {names}, old '{old_name}' should be gone")
        return 0.0
    except Exception as e:
        logger.error(f"check_blender_object_renamed error: {e}")
        return 0.0


def check_blender_object_visibility(command_output, rule):
    """Verify object viewport visibility state.

    Args:
        command_output: JSON from check_object.py
        rule: {"object_name": "Sphere", "hide_viewport": true}
              or {"object_name": "Sphere", "expected_visible": false}
    """
    try:
        result = _parse_blender_output(command_output)
        if result is None:
            return 0.0

        obj_name = rule.get("object_name", "")
        obj = _find_object(result, obj_name)
        if obj is None:
            return 0.0

        if "hide_viewport" in rule:
            expected_hidden = rule["hide_viewport"]
            if obj.get("hide_viewport") == expected_hidden:
                return 1.0
        elif "expected_visible" in rule:
            expected_visible = rule["expected_visible"]
            actual_hidden = obj.get("hide_viewport", False)
            if expected_visible != actual_hidden:
                return 1.0

        logger.warning(f"Visibility mismatch for '{obj_name}'")
        return 0.0
    except Exception as e:
        logger.error(f"check_blender_object_visibility error: {e}")
        return 0.0


def check_blender_light_type(command_output, rule):
    """Verify a light of specified type exists.

    Args:
        command_output: JSON from check_object.py
        rule: {"light_type": "SUN"} or {"light_name": "Light", "light_type": "SUN"}
    """
    try:
        result = _parse_blender_output(command_output)
        if result is None:
            return 0.0

        expected_type = rule.get("light_type", "")
        light_name = rule.get("light_name")

        for obj in result.get("objects", []):
            if obj.get("type") != "LIGHT":
                continue
            if light_name and obj.get("name") != light_name:
                continue
            if obj.get("light_type") == expected_type:
                return 1.0

        logger.warning(f"No light found with type '{expected_type}'")
        return 0.0
    except Exception as e:
        logger.error(f"check_blender_light_type error: {e}")
        return 0.0


def check_blender_light_energy(command_output, rule):
    """Verify light energy value within tolerance.

    Args:
        command_output: JSON from check_object.py
        rule: {"light_name": "PointLight", "expected_energy": 2000.0, "tolerance": 10}
    """
    try:
        result = _parse_blender_output(command_output)
        if result is None:
            return 0.0

        light_name = rule.get("light_name", "")
        expected_energy = rule.get("expected_energy", rule.get("energy", 0))
        tol = rule.get("tolerance", 10)

        obj = _find_object(result, light_name)
        if obj is None or obj.get("type") != "LIGHT":
            return 0.0

        actual = obj.get("energy", 0)
        if _check_tolerance(actual, expected_energy, tol):
            return 1.0

        logger.warning(f"Light energy mismatch: {actual} != {expected_energy}")
        return 0.0
    except Exception as e:
        logger.error(f"check_blender_light_energy error: {e}")
        return 0.0


def check_blender_render_settings(command_output, rule):
    """Verify render settings (engine, resolution, fps, samples, format, camera).

    Args:
        command_output: JSON from check_render.py
        rule: dict with any of: engine, resolution_x, resolution_y, fps, samples,
              image_format, active_camera
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
                    logger.warning(f"Render setting mismatch: {key} = {result.get(key)} != {rule[key]}")
                    return 0.0

        return 1.0
    except Exception as e:
        logger.error(f"check_blender_render_settings error: {e}")
        return 0.0


def check_blender_animation_range(command_output, rule):
    """Verify animation frame range.

    Args:
        command_output: JSON from check_render.py
        rule: {"frame_start": 1, "frame_end": 120}
    """
    try:
        result = _parse_blender_output(command_output)
        if result is None:
            return 0.0

        if "frame_start" in rule:
            if result.get("frame_start") != rule["frame_start"]:
                logger.warning(f"frame_start mismatch: {result.get('frame_start')} != {rule['frame_start']}")
                return 0.0
        if "frame_end" in rule:
            if result.get("frame_end") != rule["frame_end"]:
                logger.warning(f"frame_end mismatch: {result.get('frame_end')} != {rule['frame_end']}")
                return 0.0

        return 1.0
    except Exception as e:
        logger.error(f"check_blender_animation_range error: {e}")
        return 0.0


def check_blender_collection_exists(command_output, rule):
    """Verify a named collection exists.

    Args:
        command_output: JSON from check_collection.py
        rule: {"collection_name": "MyObjects"}
    """
    try:
        result = _parse_blender_output(command_output)
        if result is None:
            return 0.0

        coll_name = rule.get("collection_name", "")
        if coll_name in result.get("user_collections", []):
            return 1.0

        logger.warning(f"Collection '{coll_name}' not found in {result.get('user_collections', [])}")
        return 0.0
    except Exception as e:
        logger.error(f"check_blender_collection_exists error: {e}")
        return 0.0


def check_blender_object_in_collection(command_output, rule):
    """Verify an object is in a specific collection.

    Args:
        command_output: JSON from check_collection.py
        rule: {"object_name": "Cube", "collection_name": "Props"}
    """
    try:
        result = _parse_blender_output(command_output)
        if result is None:
            return 0.0

        obj_name = rule.get("object_name", "")
        coll_name = rule.get("collection_name", "")
        obj_colls = result.get("object_collections", {}).get(obj_name, [])

        if coll_name in obj_colls:
            return 1.0

        logger.warning(f"Object '{obj_name}' not in collection '{coll_name}' (in: {obj_colls})")
        return 0.0
    except Exception as e:
        logger.error(f"check_blender_object_in_collection error: {e}")
        return 0.0


def check_blender_text_content(command_output, rule):
    """Verify text object body content.

    Args:
        command_output: JSON from check_text.py
        rule: {"object_name": "Text", "expected_text": "Hello Blender"}
    """
    try:
        result = _parse_blender_output(command_output)
        if result is None:
            return 0.0

        obj_name = rule.get("object_name", "")
        expected_text = rule.get("expected_text", "")

        obj_data = result.get(obj_name)
        if obj_data is None:
            # Also check check_object.py format
            obj = _find_object(result, obj_name)
            if obj and obj.get("text_body") == expected_text:
                return 1.0
            logger.warning(f"Text object '{obj_name}' not found")
            return 0.0

        if obj_data.get("body") == expected_text:
            return 1.0

        logger.warning(f"Text mismatch: '{obj_data.get('body')}' != '{expected_text}'")
        return 0.0
    except Exception as e:
        logger.error(f"check_blender_text_content error: {e}")
        return 0.0


# ============================================================================
# L2 Evaluator Functions — Composite Operations
# ============================================================================

def check_blender_material_pbr(command_output, rule):
    """Verify material PBR parameters (name, base color, metallic, roughness).

    Args:
        command_output: JSON from check_material.py
        rule: {"object_name": "Cube", "material_name": "RedMetal",
               "expected_color": [1.0, 0.0, 0.0, 1.0], "metallic": 1.0,
               "roughness": 0.2, "tolerance": 0.05}
    """
    try:
        result = _parse_blender_output(command_output)
        if result is None:
            return 0.0

        obj_name = rule.get("object_name")
        name_contains = rule.get("object_name_contains", rule.get("name_contains", ""))

        # Build candidate object material lists.
        # This supports three patterns:
        # 1) exact object_name
        # 2) object name contains substring
        # 3) no object selector (search globally by material fields)
        candidates = []
        if obj_name:
            obj_mats = result.get(obj_name)
            if obj_mats is None:
                logger.warning(f"No materials for object '{obj_name}'")
                return 0.0
            candidates.append((obj_name, obj_mats))
        elif name_contains:
            for key, mats in result.items():
                if key.startswith("_"):
                    continue
                if name_contains in key:
                    candidates.append((key, mats))
            if not candidates:
                logger.warning(f"No materials for object name containing '{name_contains}'")
                return 0.0
        else:
            for key, mats in result.items():
                if key.startswith("_"):
                    continue
                candidates.append((key, mats))
            if not candidates:
                logger.warning("No material entries found in check output")
                return 0.0

        tol = rule.get("tolerance", 0.05)
        mat_name = rule.get("material_name")

        for _obj, obj_mats in candidates:
            if not isinstance(obj_mats, list):
                obj_mats = [obj_mats]

            for mat in obj_mats:
                # Check material name if specified
                if mat_name and mat.get("name") != mat_name:
                    continue

                # Check base color
                if "expected_color" in rule:
                    actual_color = mat.get("base_color", [])
                    if not _check_vector_tolerance(actual_color, rule["expected_color"], tol):
                        continue

                # Check metallic
                if "metallic" in rule:
                    if not _check_tolerance(mat.get("metallic"), rule["metallic"], tol):
                        continue

                # Check roughness
                if "roughness" in rule:
                    if not _check_tolerance(mat.get("roughness"), rule["roughness"], tol):
                        continue

                return 1.0

        logger.warning("No matching material found")
        return 0.0
    except Exception as e:
        logger.error(f"check_blender_material_pbr error: {e}")
        return 0.0


def check_blender_modifier_boolean(command_output, rule):
    """Verify Boolean modifier on an object.

    Args:
        command_output: JSON from check_modifier.py
        rule: {"object_name": "Cube", "modifier_type": "BOOLEAN",
               "operation": "DIFFERENCE", "target_object": "Sphere"}
    """
    try:
        result = _parse_blender_output(command_output)
        if result is None:
            return 0.0

        obj_name = rule.get("object_name", "")
        mods = result.get(obj_name, [])

        expected_type = rule.get("modifier_type", "BOOLEAN")

        for mod in mods:
            if mod.get("type") != expected_type:
                continue
            if "operation" in rule and mod.get("operation") != rule["operation"]:
                continue
            if "target_object" in rule and mod.get("object") != rule["target_object"]:
                continue
            return 1.0

        logger.warning(f"No matching Boolean modifier on '{obj_name}'")
        return 0.0
    except Exception as e:
        logger.error(f"check_blender_modifier_boolean error: {e}")
        return 0.0


def check_blender_texture_assigned(command_output, rule):
    """Verify image texture is assigned and connected.

    Args:
        command_output: JSON from check_material.py
        rule: {"object_name": "Cube", "texture_filename": "texture_wood.jpg",
               "input_name": "Base Color"}
    """
    try:
        result = _parse_blender_output(command_output)
        if result is None:
            return 0.0

        obj_name = rule.get("object_name", "")
        expected_filename = rule.get("texture_filename", "")
        expected_input = rule.get("input_name")
        obj_mats = result.get(obj_name, [])

        if not isinstance(obj_mats, list):
            obj_mats = [obj_mats]

        for mat in obj_mats:
            # Backward-compatible fast path for Base Color direct connection.
            if expected_input in (None, "Base Color") and mat.get("texture_filename") == expected_filename:
                return 1.0

            # Check image texture nodes with optional target socket constraints.
            for tex in mat.get("image_textures", []):
                if tex.get("filename") != expected_filename:
                    continue

                if expected_input:
                    connected_to = tex.get("connected_to", [])
                    if isinstance(connected_to, str):
                        connected_to = [connected_to]
                    if expected_input not in connected_to:
                        continue

                return 1.0

        if expected_input:
            logger.warning(
                f"Texture '{expected_filename}' not connected to '{expected_input}' on '{obj_name}'"
            )
        else:
            logger.warning(f"Texture '{expected_filename}' not found on '{obj_name}'")
        return 0.0
    except Exception as e:
        logger.error(f"check_blender_texture_assigned error: {e}")
        return 0.0


def check_blender_modifier_stack(command_output, rule):
    """Verify multiple modifier parameters on an object.

    Args:
        command_output: JSON from check_modifier.py
        rule: {"object_name": "Cube",
               "modifiers": {"ARRAY": {"count": 8}, "BEVEL": {"width": 0.05, "segments": 2}},
               "tolerance": 0.01}
    """
    try:
        result = _parse_blender_output(command_output)
        if result is None:
            return 0.0

        obj_name = rule.get("object_name", "")
        expected_mods = rule.get("modifiers", {})
        tol = rule.get("tolerance", 0.01)
        mods = result.get(obj_name, [])

        for mod_type, expected_params in expected_mods.items():
            found = False
            for mod in mods:
                if mod.get("type") != mod_type:
                    continue
                found = True
                for param, expected_val in expected_params.items():
                    actual_val = mod.get(param)
                    if isinstance(expected_val, (int, float)):
                        if not _check_tolerance(actual_val, expected_val, tol):
                            logger.warning(f"Modifier {mod_type}.{param}: {actual_val} != {expected_val}")
                            return 0.0
                    elif actual_val != expected_val:
                        logger.warning(f"Modifier {mod_type}.{param}: {actual_val} != {expected_val}")
                        return 0.0
                break
            if not found:
                logger.warning(f"Modifier type '{mod_type}' not found on '{obj_name}'")
                return 0.0

        return 1.0
    except Exception as e:
        logger.error(f"check_blender_modifier_stack error: {e}")
        return 0.0


def check_blender_world_hdri(command_output, rule):
    """Verify world environment uses specified HDRI file.

    Args:
        command_output: JSON from check_world.py
        rule: {"hdri_filename": "hdri_studio.exr"}
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

        logger.warning(f"HDRI mismatch: '{actual_filename}' != '{expected_filename}'")
        return 0.0
    except Exception as e:
        logger.error(f"check_blender_world_hdri error: {e}")
        return 0.0


def check_blender_animation_keyframes(command_output, rule):
    """Verify animation keyframe existence and properties.

    Args:
        command_output: JSON from check_animation.py
        rule: {"object_name": "Cube", "min_keyframe_count": 2, "has_location_keys": true}
    """
    try:
        result = _parse_blender_output(command_output)
        if result is None:
            return 0.0

        obj_name = rule.get("object_name", "")
        obj_anim = result.get(obj_name)
        if obj_anim is None:
            logger.warning(f"No animation data for '{obj_name}'")
            return 0.0

        # Check minimum keyframe count
        if "min_keyframe_count" in rule:
            actual_count = obj_anim.get("keyframe_count", 0)
            if actual_count < rule["min_keyframe_count"]:
                logger.warning(f"Keyframe count {actual_count} < {rule['min_keyframe_count']}")
                return 0.0

        # Check for location keyframes
        if rule.get("has_location_keys"):
            keyframes = obj_anim.get("keyframes", {})
            has_loc = any("location" in k for k in keyframes)
            if not has_loc:
                logger.warning("No location keyframes found")
                return 0.0

        return 1.0
    except Exception as e:
        logger.error(f"check_blender_animation_keyframes error: {e}")
        return 0.0


def check_blender_parent_child(command_output, rule):
    """Verify parent-child relationships.

    Args:
        command_output: JSON from check_object.py
        rule: {"parent": "Cube", "expected_children": ["Sphere", "Cylinder"]}
              or {"parent_map": {"Moon": "Planet1"}, "not_parent": {"Moon": "Planet2"}}
    """
    try:
        result = _parse_blender_output(command_output)
        if result is None:
            return 0.0

        # Pattern 1: parent + expected_children
        if "parent" in rule and "expected_children" in rule:
            parent_name = rule["parent"]
            parent_obj = _find_object(result, parent_name)
            if parent_obj is None:
                return 0.0
            actual_children = set(parent_obj.get("children", []))
            expected_children = set(rule["expected_children"])
            if not expected_children.issubset(actual_children):
                logger.warning(f"Missing children: {expected_children - actual_children}")
                return 0.0
            return 1.0

        # Pattern 2: parent_map + not_parent
        if "parent_map" in rule:
            for child_name, expected_parent in rule["parent_map"].items():
                child_obj = _find_object(result, child_name)
                if child_obj is None:
                    logger.warning(f"Child object '{child_name}' not found")
                    return 0.0
                if child_obj.get("parent") != expected_parent:
                    logger.warning(f"'{child_name}' parent is '{child_obj.get('parent')}', expected '{expected_parent}'")
                    return 0.0

        if "not_parent" in rule:
            for child_name, wrong_parent in rule["not_parent"].items():
                child_obj = _find_object(result, child_name)
                if child_obj and child_obj.get("parent") == wrong_parent:
                    logger.warning(f"'{child_name}' should NOT have parent '{wrong_parent}'")
                    return 0.0

        # Pattern 3: parent_has_children + min_children_count
        if rule.get("parent_has_children"):
            min_count = rule.get("min_children_count", 1)
            for obj in result.get("objects", []):
                if len(obj.get("children", [])) >= min_count:
                    return 1.0
            logger.warning(f"No object has >= {min_count} children")
            return 0.0

        return 1.0
    except Exception as e:
        logger.error(f"check_blender_parent_child error: {e}")
        return 0.0


def check_blender_collection_members(command_output, rule):
    """Verify collection contains expected member objects.

    Args:
        command_output: JSON from check_collection.py
        rule: {"collection_name": "Props", "expected_members": ["Cube", "Sphere"]}
    """
    try:
        result = _parse_blender_output(command_output)
        if result is None:
            return 0.0

        coll_name = rule.get("collection_name", "")
        expected_members = set(rule.get("expected_members", []))

        # Find the collection's objects
        for coll in result.get("collections", []):
            if coll.get("name") == coll_name:
                actual_members = set(coll.get("objects", []))
                if expected_members.issubset(actual_members):
                    return 1.0
                logger.warning(f"Collection '{coll_name}' missing: {expected_members - actual_members}")
                return 0.0

        # Also check via object_collections
        for member in expected_members:
            colls = result.get("object_collections", {}).get(member, [])
            if coll_name not in colls:
                logger.warning(f"Object '{member}' not in collection '{coll_name}'")
                return 0.0
        return 1.0
    except Exception as e:
        logger.error(f"check_blender_collection_members error: {e}")
        return 0.0


def check_blender_constraints_multi(command_output, rule):
    """Verify multiple constraints across objects.

    Args:
        command_output: JSON from check_constraints.py
        rule: {"constraints": [{"object_name": "Orbiter", "type": "TRACK_TO", "target": "Target"}, ...]}
    """
    try:
        result = _parse_blender_output(command_output)
        if result is None:
            return 0.0

        for expected in rule.get("constraints", []):
            obj_name = expected.get("object_name", "")
            obj_constraints = result.get(obj_name, [])

            found = False
            for con in obj_constraints:
                if con.get("type") != expected.get("type"):
                    continue
                if "target" in expected and con.get("target") != expected["target"]:
                    continue
                if "track_axis" in expected and con.get("track_axis") != expected["track_axis"]:
                    continue
                if "up_axis" in expected and con.get("up_axis") != expected["up_axis"]:
                    continue
                found = True
                break

            if not found:
                logger.warning(f"Constraint not found on '{obj_name}': {expected}")
                return 0.0

        return 1.0
    except Exception as e:
        logger.error(f"check_blender_constraints_multi error: {e}")
        return 0.0


def check_blender_applied_modifier(command_output, rule):
    """Verify a modifier has been applied (vertices increased, modifier type gone).

    Args:
        command_output: JSON from check_mesh.py
        rule: {"object_name": "Cube", "min_vertices": 20, "no_modifier_type": "SUBSURF"}
    """
    try:
        result = _parse_blender_output(command_output)
        if result is None:
            return 0.0

        obj_name = rule.get("object_name", "")
        mesh_info = result.get(obj_name)
        if mesh_info is None:
            return 0.0

        # Check minimum vertex count
        if "min_vertices" in rule:
            if mesh_info.get("vertex_count", 0) < rule["min_vertices"]:
                logger.warning(f"Vertex count too low: {mesh_info.get('vertex_count')}")
                return 0.0

        # Optional stricter check: ensure a modifier type no longer exists.
        if "no_modifier_type" in rule:
            forbidden_type = rule["no_modifier_type"]
            modifier_types = mesh_info.get("modifier_types")
            if modifier_types is None:
                logger.warning("modifier_types missing from check_mesh output")
                return 0.0
            if forbidden_type in modifier_types:
                logger.warning(f"Modifier '{forbidden_type}' still exists on '{obj_name}'")
                return 0.0

        return 1.0
    except Exception as e:
        logger.error(f"check_blender_applied_modifier error: {e}")
        return 0.0


def check_blender_smooth_shading(command_output, rule):
    """Verify smooth shading on object(s).

    Args:
        command_output: JSON from check_mesh.py
        rule: {"object_name": "Cube", "has_smooth": true}
              or {"object_name_contains": "Sphere", "has_smooth": true}
    """
    try:
        result = _parse_blender_output(command_output)
        if result is None:
            return 0.0

        obj_name = rule.get("object_name")
        name_contains = rule.get("object_name_contains")
        expected_smooth = rule.get("has_smooth", True)

        if obj_name:
            mesh_info = result.get(obj_name)
            if mesh_info is None:
                return 0.0
            if mesh_info.get("has_smooth") == expected_smooth:
                return 1.0
            return 0.0

        if name_contains:
            for key, mesh_info in result.items():
                if name_contains in key and isinstance(mesh_info, dict):
                    if mesh_info.get("has_smooth") == expected_smooth:
                        return 1.0
            return 0.0

        return 0.0
    except Exception as e:
        logger.error(f"check_blender_smooth_shading error: {e}")
        return 0.0


def check_blender_particle_params(command_output, rule):
    """Verify particle system parameters.

    Args:
        command_output: JSON from check_particles.py
        rule: {"object_name": "Emitter", "count": 2000, "lifetime": 100.0, ...}
    """
    try:
        result = _parse_blender_output(command_output)
        if result is None:
            return 0.0

        obj_name = rule.get("object_name", "")
        particles = result.get(obj_name, [])
        tol = rule.get("tolerance", 1.0)

        if not particles:
            logger.warning(f"No particle systems on '{obj_name}'")
            return 0.0

        ps = particles[0]  # Check first particle system

        checks = ["count", "lifetime", "frame_start", "frame_end", "normal_factor"]
        for param in checks:
            if param in rule:
                actual = ps.get(param)
                expected = rule[param]
                if not _check_tolerance(actual, expected, tol):
                    logger.warning(f"Particle {param}: {actual} != {expected}")
                    return 0.0

        return 1.0
    except Exception as e:
        logger.error(f"check_blender_particle_params error: {e}")
        return 0.0


def check_blender_selective_smooth(command_output, rule):
    """Verify selective smooth shading (some smooth, some flat).

    Args:
        command_output: JSON from check_mesh.py
        rule: {"smooth_objects": ["Sphere", "Cylinder"], "flat_objects": ["Ground"]}
    """
    try:
        result = _parse_blender_output(command_output)
        if result is None:
            return 0.0

        for name in rule.get("smooth_objects", []):
            mesh_info = result.get(name)
            if mesh_info is None or not mesh_info.get("has_smooth"):
                logger.warning(f"'{name}' should have smooth shading")
                return 0.0

        for name in rule.get("flat_objects", []):
            mesh_info = result.get(name)
            if mesh_info and mesh_info.get("has_smooth"):
                logger.warning(f"'{name}' should NOT have smooth shading")
                return 0.0

        return 1.0
    except Exception as e:
        logger.error(f"check_blender_selective_smooth error: {e}")
        return 0.0


def check_blender_animation_extended(command_output, rule):
    """Verify animation has been extended (more keyframes, later max frame).

    Args:
        command_output: JSON from check_animation.py
        rule: {"object_name": "Cube", "min_keyframe_count": 3, "max_frame": 240}
    """
    try:
        result = _parse_blender_output(command_output)
        if result is None:
            return 0.0

        obj_name = rule.get("object_name", "")
        obj_anim = result.get(obj_name)
        if obj_anim is None:
            return 0.0

        if "min_keyframe_count" in rule:
            if obj_anim.get("keyframe_count", 0) < rule["min_keyframe_count"]:
                return 0.0

        if "max_frame" in rule:
            frame_range = obj_anim.get("frame_range", [0, 0])
            if frame_range[1] < rule["max_frame"]:
                logger.warning(f"Max frame {frame_range[1]} < {rule['max_frame']}")
                return 0.0

        return 1.0
    except Exception as e:
        logger.error(f"check_blender_animation_extended error: {e}")
        return 0.0


def check_blender_collection_organization(command_output, rule):
    """Verify collection creation, membership changes, and visibility.

    Args:
        command_output: JSON from check_collection.py
        rule: {"new_collection": "Background",
               "member_in_collection": {"Cylinder": "Background"},
               "hidden_collections": ["Lights"]}
    """
    try:
        result = _parse_blender_output(command_output)
        if result is None:
            return 0.0

        # Check new collection exists
        if "new_collection" in rule:
            if rule["new_collection"] not in result.get("user_collections", []):
                logger.warning(f"Collection '{rule['new_collection']}' not found")
                return 0.0

        # Check object-to-collection membership
        for obj_name, coll_name in rule.get("member_in_collection", {}).items():
            obj_colls = result.get("object_collections", {}).get(obj_name, [])
            if coll_name not in obj_colls:
                logger.warning(f"'{obj_name}' not in collection '{coll_name}'")
                return 0.0

        # Check hidden collections
        for coll_name in rule.get("hidden_collections", []):
            for coll in result.get("collections", []):
                if coll.get("name") == coll_name:
                    if not coll.get("hide_viewport"):
                        logger.warning(f"Collection '{coll_name}' is not hidden")
                        return 0.0
                    break

        return 1.0
    except Exception as e:
        logger.error(f"check_blender_collection_organization error: {e}")
        return 0.0


def check_blender_hierarchy(command_output, rule):
    """Verify parent hierarchy relationships.

    Args:
        command_output: JSON from check_object.py
        rule: {"parent_map": {"Moon": "Planet1", "Planet3": "Sun"},
               "not_parent": {"Moon": "Planet2"}}
    """
    return check_blender_parent_child(command_output, rule)


def check_blender_multi_light_config(command_output, rule):
    """Verify multiple light parameters.

    Args:
        command_output: JSON from check_object.py (extended with light data)
        rule: {"lights": [{"name": "PointLight", "energy": 500.0, "color": [1.0, 0.9, 0.8]}, ...]}
    """
    try:
        result = _parse_blender_output(command_output)
        if result is None:
            return 0.0

        for light_spec in rule.get("lights", []):
            light_name = light_spec.get("name", "")
            obj = _find_object(result, light_name)
            if obj is None or obj.get("type") != "LIGHT":
                logger.warning(f"Light '{light_name}' not found")
                return 0.0

            if "energy" in light_spec:
                tol = light_spec.get("energy_tolerance", 50)
                if not _check_tolerance(obj.get("energy"), light_spec["energy"], tol):
                    return 0.0

            if "color" in light_spec:
                actual_color = obj.get("light_color", [])
                color_tol = light_spec.get("color_tolerance", 0.05)
                if not _check_vector_tolerance(actual_color, light_spec["color"], color_tol):
                    return 0.0

            if "spot_size_deg" in light_spec:
                if obj.get("light_type") != "SPOT":
                    return 0.0
                # Support legacy key angle_tolerance as alias.
                spot_tol = light_spec.get("spot_tolerance", light_spec.get("angle_tolerance", 5.0))
                if not _check_tolerance(obj.get("spot_size_deg"), light_spec["spot_size_deg"], spot_tol):
                    return 0.0

            if "shape" in light_spec:
                if obj.get("light_type") != "AREA":
                    return 0.0
                if obj.get("area_shape") != light_spec["shape"]:
                    return 0.0

            # Support legacy key size as alias.
            expected_area_size = light_spec.get("area_size", light_spec.get("size"))
            if expected_area_size is not None:
                area_tol = light_spec.get("area_tolerance", 0.1)
                if not _check_tolerance(obj.get("area_size"), expected_area_size, area_tol):
                    return 0.0

        return 1.0
    except Exception as e:
        logger.error(f"check_blender_multi_light_config error: {e}")
        return 0.0


def check_blender_text_styling(command_output, rule):
    """Verify text object styling (body, size, extrude, alignment).

    Args:
        command_output: JSON from check_text.py
        rule: {"object_name": "Title", "body": "HELLO WORLD", "size": 2.0,
               "extrude": 0.15, "align_x": "CENTER", "tolerance": 0.05}
    """
    try:
        result = _parse_blender_output(command_output)
        if result is None:
            return 0.0

        obj_name = rule.get("object_name", "")
        text_data = result.get(obj_name)
        if text_data is None:
            return 0.0

        tol = rule.get("tolerance", 0.05)

        if "body" in rule and text_data.get("body") != rule["body"]:
            logger.warning(f"Text body mismatch: '{text_data.get('body')}' != '{rule['body']}'")
            return 0.0

        if "size" in rule:
            if not _check_tolerance(text_data.get("size"), rule["size"], tol):
                return 0.0

        if "extrude" in rule:
            if not _check_tolerance(text_data.get("extrude"), rule["extrude"], tol):
                return 0.0

        if "bevel_depth" in rule:
            if not _check_tolerance(text_data.get("bevel_depth"), rule["bevel_depth"], tol):
                return 0.0

        if "align_x" in rule:
            if text_data.get("align_x") != rule["align_x"]:
                return 0.0

        return 1.0
    except Exception as e:
        logger.error(f"check_blender_text_styling error: {e}")
        return 0.0


def check_blender_material_textures(command_output, rule):
    """Verify multiple texture connections on a material.

    Args:
        command_output: JSON from check_material.py
        rule: {"object_name": "Cube",
               "textures": [{"filename": "texture_brick.jpg", "connected_to": "Base Color"}, ...],
               "metallic": 0.0, "roughness": 0.7, "tolerance": 0.05}
    """
    try:
        result = _parse_blender_output(command_output)
        if result is None:
            return 0.0

        obj_name = rule.get("object_name", "")
        obj_mats = result.get(obj_name, [])
        if not isinstance(obj_mats, list):
            obj_mats = [obj_mats]

        tol = rule.get("tolerance", 0.05)

        # Check textures
        for tex_spec in rule.get("textures", []):
            filename = tex_spec.get("filename", "")
            connected_to = tex_spec.get("connected_to")
            found = False
            for mat in obj_mats:
                for tex in mat.get("image_textures", []):
                    if tex.get("filename") != filename:
                        continue

                    if connected_to:
                        targets = tex.get("connected_to", [])
                        if isinstance(targets, str):
                            targets = [targets]
                        if connected_to not in targets:
                            continue

                    found = True
                    break

                # Also check texture_filename for Base Color fallback.
                if not found and mat.get("texture_filename") == filename:
                    if connected_to in (None, "Base Color"):
                        found = True

                if found:
                    break
            if not found:
                if connected_to:
                    logger.warning(f"Texture '{filename}' not connected to '{connected_to}'")
                else:
                    logger.warning(f"Texture '{filename}' not found")
                return 0.0

        # Check PBR params if specified
        for mat in obj_mats:
            if "metallic" in rule:
                if not _check_tolerance(mat.get("metallic"), rule["metallic"], tol):
                    continue
            if "roughness" in rule:
                if not _check_tolerance(mat.get("roughness"), rule["roughness"], tol):
                    continue
            return 1.0

        if rule.get("textures") and "metallic" not in rule and "roughness" not in rule:
            return 1.0

        return 0.0
    except Exception as e:
        logger.error(f"check_blender_material_textures error: {e}")
        return 0.0


def check_blender_follow_path(command_output, rule):
    """Verify Follow Path constraint setup.

    Args:
        command_output: JSON from check_constraints.py
        rule: {"object_name": "Follower", "constraint_type": "FOLLOW_PATH",
               "target": "BezierCurve", "use_curve_follow": true, "forward_axis": "FORWARD_Y"}
    """
    try:
        result = _parse_blender_output(command_output)
        if result is None:
            return 0.0

        obj_name = rule.get("object_name", "")
        constraints = result.get(obj_name, [])

        expected_type = rule.get("constraint_type", "FOLLOW_PATH")

        for con in constraints:
            if con.get("type") != expected_type:
                continue
            if "target" in rule and con.get("target") != rule["target"]:
                continue
            if "use_curve_follow" in rule and con.get("use_curve_follow") != rule["use_curve_follow"]:
                continue
            if "forward_axis" in rule and con.get("forward_axis") != rule["forward_axis"]:
                continue
            if "up_axis" in rule and con.get("up_axis") != rule["up_axis"]:
                continue
            return 1.0

        logger.warning(f"Follow Path constraint not found on '{obj_name}'")
        return 0.0
    except Exception as e:
        logger.error(f"check_blender_follow_path error: {e}")
        return 0.0


def check_blender_modifier_order(command_output, rule):
    """Verify modifier order and parameters.

    Args:
        command_output: JSON from check_modifier.py
        rule: {"object_name": "Cube", "modifier_order": ["SUBSURF", "SOLIDIFY"],
               "params": {"SOLIDIFY": {"thickness": 0.1}}, "tolerance": 0.01}
    """
    try:
        result = _parse_blender_output(command_output)
        if result is None:
            return 0.0

        obj_name = rule.get("object_name", "")
        mods = result.get(obj_name, [])
        expected_order = rule.get("modifier_order", [])
        tol = rule.get("tolerance", 0.01)

        # Check order
        actual_types = [m.get("type") for m in mods]
        expected_indices = []
        for mod_type in expected_order:
            try:
                idx = actual_types.index(mod_type)
                expected_indices.append(idx)
            except ValueError:
                logger.warning(f"Modifier type '{mod_type}' not found")
                return 0.0

        # Verify order is correct (each index should be greater than previous)
        for i in range(1, len(expected_indices)):
            if expected_indices[i] <= expected_indices[i - 1]:
                logger.warning(f"Modifier order incorrect: {actual_types}")
                return 0.0

        # Check params
        params = rule.get("params", {})
        for mod_type, expected_params in params.items():
            for mod in mods:
                if mod.get("type") == mod_type:
                    for param, expected_val in expected_params.items():
                        actual_val = mod.get(param)
                        if isinstance(expected_val, (int, float)):
                            if not _check_tolerance(actual_val, expected_val, tol):
                                return 0.0
                        elif actual_val != expected_val:
                            return 0.0
                    break

        return 1.0
    except Exception as e:
        logger.error(f"check_blender_modifier_order error: {e}")
        return 0.0


def check_blender_transform_applied(command_output, rule):
    """Verify that transforms have been applied (location/scale reset).

    Args:
        command_output: JSON from check_object.py
        rule: {"object_name": "Suzanne", "expected_location": [0,0,0],
               "expected_scale": [1,1,1], "location_tolerance": 0.1}
    """
    try:
        result = _parse_blender_output(command_output)
        if result is None:
            return 0.0

        obj = _find_object(result, rule.get("object_name", ""))
        if obj is None:
            return 0.0

        loc_tol = rule.get("location_tolerance", rule.get("tolerance", 0.1))

        if "expected_location" in rule:
            if not _check_vector_tolerance(obj.get("location", []), rule["expected_location"], loc_tol):
                return 0.0

        if "expected_scale" in rule:
            if not _check_vector_tolerance(obj.get("scale", []), rule["expected_scale"], loc_tol):
                return 0.0

        return 1.0
    except Exception as e:
        logger.error(f"check_blender_transform_applied error: {e}")
        return 0.0


def check_blender_mesh_bounds(command_output, rule):
    """Verify mesh bounding dimensions.

    Args:
        command_output: JSON from check_mesh.py
        rule: {"object_name": "Suzanne", "min_dimension": 1.5}
    """
    try:
        result = _parse_blender_output(command_output)
        if result is None:
            return 0.0

        obj_name = rule.get("object_name", "")
        mesh_info = result.get(obj_name)
        if mesh_info is None:
            return 0.0

        if "min_dimension" in rule:
            dims = mesh_info.get("dimensions", [0, 0, 0])
            max_dim = max(dims) if dims else 0
            if max_dim < rule["min_dimension"]:
                logger.warning(f"Max dimension {max_dim} < {rule['min_dimension']}")
                return 0.0

        return 1.0
    except Exception as e:
        logger.error(f"check_blender_mesh_bounds error: {e}")
        return 0.0


# ============================================================================
# L3 Evaluator Functions — Render Output & Scene-Level
# ============================================================================

def check_blender_render_output(file_path, rule):
    """Verify rendered image output (existence, dimensions, format).

    Args:
        file_path: Path to downloaded render output file (PNG/EXR)
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


def check_blender_render_video(file_path, rule):
    """Verify rendered video output (existence, duration, codec).

    Args:
        file_path: Path to downloaded video file (MP4)
        rule: {"min_duration": 1.5, "codec": "h264"}
    """
    try:
        if file_path is None or not os.path.exists(file_path):
            logger.error(f"Video file not found: {file_path}")
            return 0.0

        # Use ffprobe to check video
        cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=duration,codec_name",
            "-show_entries", "format=duration",
            "-of", "json",
            file_path
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        info = json.loads(proc.stdout)

        # Get duration
        duration = None
        if info.get("format", {}).get("duration"):
            duration = float(info["format"]["duration"])
        elif info.get("streams"):
            for stream in info["streams"]:
                if stream.get("duration"):
                    duration = float(stream["duration"])
                    break

        if "min_duration" in rule and duration is not None:
            if duration < rule["min_duration"]:
                logger.warning(f"Video duration {duration}s < {rule['min_duration']}s")
                return 0.0

        # Check codec
        if "codec" in rule and info.get("streams"):
            codec = info["streams"][0].get("codec_name", "")
            if codec.lower() != rule["codec"].lower():
                logger.warning(f"Codec mismatch: {codec} != {rule['codec']}")
                return 0.0

        return 1.0
    except FileNotFoundError:
        logger.error("ffprobe not available")
        return 1.0 if file_path and os.path.exists(file_path) else 0.0
    except Exception as e:
        logger.error(f"check_blender_render_video error: {e}")
        return 0.0


def check_blender_multi_material_scene(command_output, rule):
    """Verify multiple objects have correct materials.

    Args:
        command_output: JSON from check_material.py
        rule: {"materials": [{"object_name": "TableTop", "has_texture": "texture_wood.jpg"},
                             {"object_name": "Plate", "expected_color": [0.9, 0.9, 0.9, 1.0]}],
               "tolerance": 0.05}
    """
    try:
        result = _parse_blender_output(command_output)
        if result is None:
            return 0.0

        tol = rule.get("tolerance", 0.05)

        for mat_spec in rule.get("materials", []):
            obj_name = mat_spec.get("object_name", "")
            obj_mats = result.get(obj_name, [])
            if not obj_mats:
                logger.warning(f"No materials on '{obj_name}'")
                return 0.0

            if not isinstance(obj_mats, list):
                obj_mats = [obj_mats]

            matched = False
            for mat in obj_mats:
                # Check texture
                if "has_texture" in mat_spec:
                    tex_name = mat_spec["has_texture"]
                    found_tex = False
                    if mat.get("texture_filename") == tex_name:
                        found_tex = True
                    for tex in mat.get("image_textures", []):
                        if tex.get("filename") == tex_name:
                            found_tex = True
                    if not found_tex:
                        continue

                # Check color
                if "expected_color" in mat_spec:
                    if not _check_vector_tolerance(mat.get("base_color"), mat_spec["expected_color"], tol):
                        continue

                # Check roughness
                if "roughness" in mat_spec:
                    if not _check_tolerance(mat.get("roughness"), mat_spec["roughness"], tol):
                        continue

                # Check metallic
                if "metallic" in mat_spec:
                    if not _check_tolerance(mat.get("metallic"), mat_spec["metallic"], tol):
                        continue

                matched = True
                break

            if not matched:
                logger.warning(f"Material check failed for '{obj_name}'")
                return 0.0

        return 1.0
    except Exception as e:
        logger.error(f"check_blender_multi_material_scene error: {e}")
        return 0.0


def check_blender_scene_objects(command_output, rule):
    """Verify scene has required object types and names.

    Args:
        command_output: JSON from check_object.py
        rule: {"has_objects": ["Ball"], "has_light_type": "SUN", "has_plane": true,
               "min_mesh_count": 2, "has_cylinder": true}
    """
    try:
        result = _parse_blender_output(command_output)
        if result is None:
            return 0.0

        objects = result.get("objects", [])
        names = result.get("object_names", [])

        # Check named objects exist
        for name in rule.get("has_objects", []):
            if name not in names:
                logger.warning(f"Object '{name}' not found")
                return 0.0

        # Check light type
        if "has_light_type" in rule:
            found = any(o.get("light_type") == rule["has_light_type"]
                        for o in objects if o.get("type") == "LIGHT")
            if not found:
                return 0.0

        # Check for plane (flat scaled object)
        if rule.get("has_plane"):
            found = any(o.get("type") == "MESH" for o in objects)
            if not found:
                return 0.0

        # Check mesh count
        if "min_mesh_count" in rule:
            mesh_count = sum(1 for o in objects if o.get("type") == "MESH")
            if mesh_count < rule["min_mesh_count"]:
                return 0.0

        # Check cylinder exists
        if rule.get("has_cylinder"):
            found = any("Cylinder" in o.get("name", "") or "cylinder" in o.get("name", "").lower()
                        for o in objects if o.get("type") == "MESH")
            if not found:
                return 0.0

        return 1.0
    except Exception as e:
        logger.error(f"check_blender_scene_objects error: {e}")
        return 0.0


def check_blender_material_color(command_output, rule):
    """Verify material base color on a specific object.

    Args:
        command_output: JSON from check_material.py
        rule: {"object_name": "Ball", "expected_color": [1.0, 0.0, 0.0, 1.0],
               "metallic": 0.5, "tolerance": 0.1, "material_name": "...",
               "material_name_contains": ""}
    """
    return check_blender_material_pbr(command_output, rule)


def check_blender_camera_config(command_output, rule):
    """Verify camera configuration (focal length, DOF, etc.).

    Args:
        command_output: JSON from check_object.py (camera info)
        rule: {"camera_name": "Camera", "focal_length": 85.0, "dof_enabled": true,
               "fstop": 2.8, "tolerance": 0.5}

    Note: This function checks what's available in check_object.py output.
    Camera-specific data (focal_length, dof) may need a dedicated check script.
    Falls back to checking camera existence.
    """
    try:
        result = _parse_blender_output(command_output)
        if result is None:
            return 0.0

        camera_name = rule.get("camera_name", "Camera")
        obj = _find_object(result, camera_name)
        if obj is None:
            logger.warning(f"Camera '{camera_name}' not found")
            return 0.0

        if obj.get("type") != "CAMERA":
            return 0.0

        # Camera-specific properties from check_object.py
        tol = rule.get("tolerance", 0.5)

        if "focal_length" in rule:
            if "focal_length" not in obj:
                logger.warning("focal_length missing in camera info")
                return 0.0
            if not _check_tolerance(obj["focal_length"], rule["focal_length"], tol):
                return 0.0

        if "dof_enabled" in rule:
            if "dof_enabled" not in obj:
                logger.warning("dof_enabled missing in camera info")
                return 0.0
            if obj["dof_enabled"] != rule["dof_enabled"]:
                return 0.0

        if "fstop" in rule:
            if "fstop" not in obj:
                logger.warning("fstop missing in camera info")
                return 0.0
            if not _check_tolerance(obj["fstop"], rule["fstop"], tol):
                return 0.0

        if "focus_distance" in rule:
            if "focus_distance" not in obj:
                logger.warning("focus_distance missing in camera info")
                return 0.0
            if not _check_tolerance(obj["focus_distance"], rule["focus_distance"], tol):
                return 0.0

        return 1.0
    except Exception as e:
        logger.error(f"check_blender_camera_config error: {e}")
        return 0.0


# ============================================================================
# Alias Functions — Thin wrappers for L3 multi-metric use
# ============================================================================

def check_blender_modifier_subsurf(command_output, rule):
    """Verify Subdivision Surface modifier (alias for modifier_stack).

    Args:
        command_output: JSON from check_modifier.py
        rule: {"object_name_contains": "Sphere", "modifier_type": "SUBSURF", "levels": 3}
    """
    try:
        result = _parse_blender_output(command_output)
        if result is None:
            return 0.0

        obj_name = rule.get("object_name")
        name_contains = rule.get("object_name_contains", "")

        # Find matching object
        target_mods = None
        if obj_name:
            target_mods = result.get(obj_name, [])
        elif name_contains:
            for key in result:
                if name_contains in key:
                    target_mods = result[key]
                    break

        if not target_mods:
            return 0.0

        for mod in target_mods:
            if mod.get("type") == rule.get("modifier_type", "SUBSURF"):
                if "levels" in rule:
                    if mod.get("levels") == rule["levels"]:
                        return 1.0
                else:
                    return 1.0

        return 0.0
    except Exception as e:
        logger.error(f"check_blender_modifier_subsurf error: {e}")
        return 0.0


def check_blender_render_engine(command_output, rule):
    """Verify render engine (alias for render_settings with just engine).

    Args:
        command_output: JSON from check_render.py
        rule: {"engine": "CYCLES"}
    """
    return check_blender_render_settings(command_output, rule)


def check_blender_frame_range(command_output, rule):
    """Verify frame range (alias for animation_range).

    Args:
        command_output: JSON from check_render.py
        rule: {"frame_start": 1, "frame_end": 120}
    """
    return check_blender_animation_range(command_output, rule)


def check_blender_fps(command_output, rule):
    """Verify FPS setting (alias for render_settings with just fps).

    Args:
        command_output: JSON from check_render.py
        rule: {"fps": 30}
    """
    return check_blender_render_settings(command_output, rule)


def check_blender_mesh_modified(command_output, rule):
    """Verify mesh has been modified (alias for applied_modifier).

    Args:
        command_output: JSON from check_mesh.py
        rule: {"object_name": "Cube", "min_vertices": 20, "no_modifier_type": "BOOLEAN"}
    """
    return check_blender_applied_modifier(command_output, rule)


def check_blender_modifier_bevel(command_output, rule):
    """Verify Bevel modifier on an object.

    Args:
        command_output: JSON from check_modifier.py
        rule: {"object_name": "Cube", "modifier_type": "BEVEL",
               "width": 0.02, "segments": 3, "tolerance": 0.01}
    """
    try:
        result = _parse_blender_output(command_output)
        if result is None:
            return 0.0

        obj_name = rule.get("object_name", "")
        mods = result.get(obj_name, [])
        tol = rule.get("tolerance", 0.01)

        expected_type = rule.get("modifier_type", "BEVEL")

        for mod in mods:
            if mod.get("type") != expected_type:
                continue
            if "width" in rule:
                if not _check_tolerance(mod.get("width"), rule["width"], tol):
                    continue
            if "segments" in rule:
                if mod.get("segments") != rule["segments"]:
                    continue
            return 1.0

        return 0.0
    except Exception as e:
        logger.error(f"check_blender_modifier_bevel error: {e}")
        return 0.0


def check_blender_pbr_setup(command_output, rule):
    """Verify PBR material with textures (alias for material_textures).

    Args:
        command_output: JSON from check_material.py
        rule: same as check_blender_material_textures
    """
    return check_blender_material_textures(command_output, rule)
