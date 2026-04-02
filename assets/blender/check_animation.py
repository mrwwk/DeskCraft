"""check_animation.py - Check animation data in Blender scene.

Compatible with both Blender 5.0+ (layered actions) and legacy (fcurves on action).

Outputs JSON with animation info per object: action name, keyframe count,
keyframe data, frame range, etc.

Usage:
    blender --background scene.blend --python check_animation.py 2>/dev/null | grep '^RESULT:'
"""
import bpy
import json

result = {}


def get_fcurves_from_action(action):
    """Extract fcurves from action, supporting both Blender 5.0+ and legacy API."""
    fcurves = []

    # Blender 5.0+ layered action API
    if hasattr(action, 'layers') and action.layers:
        for layer in action.layers:
            if hasattr(layer, 'strips'):
                for strip in layer.strips:
                    if hasattr(strip, 'channelbags'):
                        for cb in strip.channelbags:
                            if hasattr(cb, 'fcurves'):
                                fcurves.extend(cb.fcurves)
        return fcurves

    # Legacy API (Blender < 5.0)
    if hasattr(action, 'fcurves'):
        return list(action.fcurves)

    return fcurves


for obj in bpy.data.objects:
    if not (obj.animation_data and obj.animation_data.action):
        continue

    action = obj.animation_data.action
    fcurves = get_fcurves_from_action(action)

    keyframes = {}
    for fcurve in fcurves:
        path = fcurve.data_path
        idx = fcurve.array_index
        kf_list = [{"frame": round(kf.co[0], 2), "value": round(kf.co[1], 4)}
                    for kf in fcurve.keyframe_points]
        keyframes[f"{path}[{idx}]"] = kf_list

    total_kf = sum(len(v) for v in keyframes.values())
    result[obj.name] = {
        "action_name": action.name,
        "keyframe_count": total_kf,
        "frame_range": [round(action.frame_range[0], 2), round(action.frame_range[1], 2)],
        "fcurve_count": len(fcurves),
        "keyframes": keyframes,
        "is_layered": hasattr(action, 'is_action_layered') and action.is_action_layered,
    }

# Scene frame range
result["_scene"] = {
    "frame_start": bpy.context.scene.frame_start,
    "frame_end": bpy.context.scene.frame_end,
}

print(f"RESULT:{json.dumps(result)}")
