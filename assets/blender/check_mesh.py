"""check_mesh.py - Check mesh geometry data in Blender scene.

Outputs JSON with mesh data per object: vertex count, edge count, polygon count,
smooth shading status, bounding box dimensions, etc.

Usage:
    blender --background scene.blend --python check_mesh.py 2>/dev/null | grep '^RESULT:'
"""
import bpy
import json
import mathutils

result = {}

for obj in bpy.data.objects:
    if obj.type != 'MESH':
        continue

    mesh = obj.data
    mesh_info = {
        "vertex_count": len(mesh.vertices),
        "edge_count": len(mesh.edges),
        "polygon_count": len(mesh.polygons),
        "has_smooth": any(p.use_smooth for p in mesh.polygons) if mesh.polygons else False,
        "material_count": len(mesh.materials),
        "has_uv": len(mesh.uv_layers) > 0,
        "uv_layer_count": len(mesh.uv_layers),
    }

    # Bounding box dimensions (in local space)
    if obj.bound_box:
        bb = [list(v) for v in obj.bound_box]
        dims = obj.dimensions
        mesh_info["dimensions"] = [round(d, 4) for d in dims]
        mesh_info["bounding_box_min"] = [round(min(v[i] for v in bb), 4) for i in range(3)]
        mesh_info["bounding_box_max"] = [round(max(v[i] for v in bb), 4) for i in range(3)]

    # Vertex groups
    if obj.vertex_groups:
        mesh_info["vertex_groups"] = [vg.name for vg in obj.vertex_groups]

    # Modifier types on this object, useful for "applied modifier" validation.
    mesh_info["modifier_types"] = [mod.type for mod in obj.modifiers]

    result[obj.name] = mesh_info

print(f"RESULT:{json.dumps(result)}")
