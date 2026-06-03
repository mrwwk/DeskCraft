"""check_constraints.py - Check object constraints in Blender scene.

Outputs JSON with constraint info per object: type, target, influence, etc.

Usage:
    blender --background scene.blend --python check_constraints.py 2>/dev/null | grep '^RESULT:'
"""
import bpy
import json

result = {}

for obj in bpy.data.objects:
    if not obj.constraints:
        continue

    constraints = []
    for con in obj.constraints:
        con_info = {
            "name": con.name,
            "type": con.type,
            "influence": round(con.influence, 4),
            "mute": con.mute,
        }

        if hasattr(con, 'target') and con.target:
            con_info["target"] = con.target.name
        if hasattr(con, 'subtarget'):
            con_info["subtarget"] = con.subtarget

        # Type-specific properties
        if con.type == 'TRACK_TO':
            con_info["track_axis"] = con.track_axis
            con_info["up_axis"] = con.up_axis
        elif con.type == 'COPY_LOCATION':
            con_info["use_x"] = con.use_x
            con_info["use_y"] = con.use_y
            con_info["use_z"] = con.use_z
        elif con.type == 'COPY_ROTATION':
            con_info["use_x"] = con.use_x
            con_info["use_y"] = con.use_y
            con_info["use_z"] = con.use_z
        elif con.type == 'LIMIT_LOCATION':
            con_info["use_min_x"] = con.use_min_x
            con_info["use_max_x"] = con.use_max_x
        elif con.type == 'FOLLOW_PATH':
            con_info["use_curve_follow"] = con.use_curve_follow
            con_info["forward_axis"] = con.forward_axis
            if hasattr(con, 'up_axis'):
                con_info["up_axis"] = con.up_axis

        constraints.append(con_info)

    result[obj.name] = constraints

print(f"RESULT:{json.dumps(result)}")
