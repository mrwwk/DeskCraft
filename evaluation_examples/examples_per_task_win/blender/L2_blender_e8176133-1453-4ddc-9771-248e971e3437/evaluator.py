"""
Blender Material Textures Evaluator

Evaluator function for verifying texture connections on materials.
Parses JSON output from Blender check scripts (run via --background --python).

Check scripts output: RESULT:{json}
VM command pattern:
    /snap/bin/blender --background /home/user/Documents/scene.blend \
        --python /tmp/check_material.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'
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


# ============================================================================
# Evaluator Function
# ============================================================================

def check_blender_material_textures(command_output, rule):
    """Verify multiple texture connections on a material.

    Evaluates whether Image Texture nodes in a material are connected to the
    correct Principled BSDF input sockets. Supports both direct connections
    and connections through intermediate nodes (Normal Map, Color Ramp, etc.) —
    as long as the check_material.py script on the VM traces them correctly.

    Args:
        command_output: JSON string from check_material.py (via vm_command_line),
            e.g. {"Cube": [{"name": "CubeMaterial", "image_textures": [...], ...}]}
        rule: dict with expected configuration, e.g.:
            {
                "object_name": "Cube",
                "textures": [
                    {"filename": "texture_brick.jpg", "connected_to": "Base Color"},
                    {"filename": "normal_brick.jpg", "connected_to": "Normal"}
                ],
                "metallic": 0.0,      # optional
                "roughness": 0.7,     # optional
                "tolerance": 0.05      # optional
            }

    Returns:
        1.0 if all texture connections match the expected rules (and
        optional PBR params match if specified), 0.0 otherwise.
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
                # 1) Look in image_textures array (new-style output with
                #    connected_to list per texture).
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

                # 2) Fallback: legacy texture_filename + Base Color
                if not found and mat.get("texture_filename") == filename:
                    if connected_to in (None, "Base Color"):
                        found = True

                if found:
                    break

            if not found:
                if connected_to:
                    logger.warning(
                        f"Texture '{filename}' not connected to '{connected_to}'"
                    )
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

        # If only texture checks were specified and they all passed
        if rule.get("textures") and "metallic" not in rule and "roughness" not in rule:
            return 1.0

        return 0.0
    except Exception as e:
        logger.error(f"check_blender_material_textures error: {e}")
        return 0.0
