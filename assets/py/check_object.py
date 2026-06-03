"""check_object.py - Check objects in Blender scene.

Outputs JSON with all object info: name, type, location, scale, rotation,
visibility, parent, etc.

Usage:
    blender --background scene.blend --python check_object.py 2>/dev/null | grep '^RESULT:'
"""
import bpy
import json
import math

result = {"objects": [], "object_names": [], "object_count": 0}

for obj in bpy.data.objects:
    obj_info = {
        "name": obj.name,
        "type": obj.type,
        "location": [round(v, 4) for v in obj.location],
        "scale": [round(v, 4) for v in obj.scale],
        "rotation_euler_deg": [round(math.degrees(r), 2) for r in obj.rotation_euler],
        "hide_viewport": obj.hide_viewport,
        "hide_render": obj.hide_render,
        "parent": obj.parent.name if obj.parent else None,
        "children": [c.name for c in obj.children],
    }

    # Mesh-specific info
    if obj.type == 'MESH' and obj.data:
        obj_info["vertex_count"] = len(obj.data.vertices)
        obj_info["edge_count"] = len(obj.data.edges)
        obj_info["polygon_count"] = len(obj.data.polygons)
        obj_info["has_smooth"] = any(p.use_smooth for p in obj.data.polygons) if obj.data.polygons else False
        obj_info["material_count"] = len(obj.data.materials)

    # Light-specific info
    if obj.type == 'LIGHT' and obj.data:
        obj_info["light_type"] = obj.data.type
        obj_info["energy"] = obj.data.energy
        if hasattr(obj.data, 'color'):
            obj_info["light_color"] = list(obj.data.color)
        if obj.data.type == 'SPOT':
            obj_info["spot_size"] = round(obj.data.spot_size, 4)
            obj_info["spot_size_deg"] = round(math.degrees(obj.data.spot_size), 2)
            obj_info["spot_blend"] = round(obj.data.spot_blend, 4)
        if obj.data.type == 'AREA':
            obj_info["area_shape"] = obj.data.shape
            obj_info["area_size"] = round(obj.data.size, 4)
            if hasattr(obj.data, 'size_y'):
                obj_info["area_size_y"] = round(obj.data.size_y, 4)

    # Camera-specific info
    if obj.type == 'CAMERA' and obj.data:
        obj_info["focal_length"] = round(obj.data.lens, 2)
        obj_info["sensor_width"] = round(obj.data.sensor_width, 2)
        obj_info["clip_start"] = round(obj.data.clip_start, 4)
        obj_info["clip_end"] = round(obj.data.clip_end, 2)
        obj_info["dof_enabled"] = obj.data.dof.use_dof if hasattr(obj.data.dof, 'use_dof') else obj.data.dof.use_dof if hasattr(obj.data, 'dof') else False
        if hasattr(obj.data, 'dof') and obj.data.dof:
            obj_info["fstop"] = round(obj.data.dof.aperture_fstop, 2)
            obj_info["focus_distance"] = round(obj.data.dof.focus_distance, 2)

    # Font-specific info
    if obj.type == 'FONT' and obj.data:
        obj_info["text_body"] = obj.data.body
        obj_info["font_size"] = obj.data.size

    result["objects"].append(obj_info)

result["object_count"] = len(result["objects"])
result["object_names"] = [o["name"] for o in result["objects"]]

# Count by type
type_counts = {}
for o in result["objects"]:
    t = o["type"]
    type_counts[t] = type_counts.get(t, 0) + 1
result["type_counts"] = type_counts

print(f"RESULT:{json.dumps(result)}")
