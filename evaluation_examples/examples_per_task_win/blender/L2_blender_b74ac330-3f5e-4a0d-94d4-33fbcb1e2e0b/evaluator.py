"""
Blender Multi-Light Config Evaluator

Evaluator for L2_blender task: checks that PointLight energy/color,
SpotLight cone angle, and AreaLight shape/size are correctly configured.

Includes sRGB-to-linear color space conversion because:
- check_object.py outputs light_color in Blender's internal linear color space
- The task instruction asks the user to set colors via the UI, which uses sRGB
- Expected rule values are expressed in sRGB (matching what the user sees in the UI)
- Therefore expected sRGB values must be converted to linear space before comparison
"""

import json
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# sRGB <-> Linear Color Space Conversion
# ============================================================================

def _srgb_to_linear(c):
    """Convert a single sRGB component to linear space.

    Standard sRGB transfer function (IEC 61966-2-1):
    - If c <= 0.04045: linear = c / 12.92
    - If c >  0.04045: linear = ((c + 0.055) / 1.055) ^ 2.4
    """
    c = float(c)
    if c <= 0.04045:
        return c / 12.92
    else:
        return ((c + 0.055) / 1.055) ** 2.4


def _srgb_color_to_linear(color):
    """Convert an sRGB color triplet [R, G, B] to linear space."""
    return [_srgb_to_linear(c) for c in color]


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
# Evaluator Function
# ============================================================================

def check_blender_multi_light_config(command_output, rule):
    """Verify multiple light parameters.

    Args:
        command_output: JSON string from check_object.py (extended with light data)
        rule: {"lights": [{"name": "PointLight", "energy": 500.0,
                           "color": [1.0, 0.9, 0.8], "color_tolerance": 0.05}, ...]}

    Note on color comparison:
        check_object.py reports light_color in Blender's internal linear color
        space.  The expected color values in the rule are expressed in sRGB
        (the color space the user interacts with in the Blender UI).  This
        function converts expected sRGB values to linear space before comparing
        them against the actual linear-space values from the scene data.
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

            # --- Energy check ---
            if "energy" in light_spec:
                tol = light_spec.get("energy_tolerance", 50)
                if not _check_tolerance(obj.get("energy"), light_spec["energy"], tol):
                    logger.warning(
                        f"Light '{light_name}' energy mismatch: "
                        f"{obj.get('energy')} != {light_spec['energy']}"
                    )
                    return 0.0

            # --- Color check (with sRGB → linear conversion) ---
            if "color" in light_spec:
                actual_color = obj.get("light_color", [])
                # Convert expected sRGB values to linear space for fair comparison
                expected_linear = _srgb_color_to_linear(light_spec["color"])
                color_tol = light_spec.get("color_tolerance", 0.05)
                if not _check_vector_tolerance(actual_color, expected_linear, color_tol):
                    logger.warning(
                        f"Light '{light_name}' color mismatch: "
                        f"actual(linear)={actual_color} != "
                        f"expected(sRGB)={light_spec['color']} "
                        f"→ expected(linear)={expected_linear} "
                        f"(tol={color_tol})"
                    )
                    return 0.0

            # --- SpotLight cone angle check ---
            if "spot_size_deg" in light_spec:
                if obj.get("light_type") != "SPOT":
                    logger.warning(
                        f"Light '{light_name}' is not a SPOT light "
                        f"(type={obj.get('light_type')})"
                    )
                    return 0.0
                spot_tol = light_spec.get("spot_tolerance",
                                           light_spec.get("angle_tolerance", 5.0))
                if not _check_tolerance(obj.get("spot_size_deg"),
                                        light_spec["spot_size_deg"], spot_tol):
                    logger.warning(
                        f"Light '{light_name}' spot_size_deg mismatch: "
                        f"{obj.get('spot_size_deg')} != {light_spec['spot_size_deg']}"
                    )
                    return 0.0

            # --- AreaLight shape check ---
            if "shape" in light_spec:
                if obj.get("light_type") != "AREA":
                    logger.warning(
                        f"Light '{light_name}' is not an AREA light "
                        f"(type={obj.get('light_type')})"
                    )
                    return 0.0
                if obj.get("area_shape") != light_spec["shape"]:
                    logger.warning(
                        f"Light '{light_name}' area_shape mismatch: "
                        f"{obj.get('area_shape')} != {light_spec['shape']}"
                    )
                    return 0.0

            # --- AreaLight size check ---
            expected_area_size = light_spec.get("area_size",
                                                light_spec.get("size"))
            if expected_area_size is not None:
                area_tol = light_spec.get("area_tolerance", 0.1)
                if not _check_tolerance(obj.get("area_size"),
                                        expected_area_size, area_tol):
                    logger.warning(
                        f"Light '{light_name}' area_size mismatch: "
                        f"{obj.get('area_size')} != {expected_area_size}"
                    )
                    return 0.0

        return 1.0
    except Exception as e:
        logger.error(f"check_blender_multi_light_config error: {e}")
        return 0.0
