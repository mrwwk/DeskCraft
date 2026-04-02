"""check_modifier.py - Check modifiers on objects in Blender scene.

Outputs JSON with modifier info per object: type, name, and type-specific
parameters (subdivision levels, boolean operation, mirror axes, array count, etc.)

Usage:
    blender --background scene.blend --python check_modifier.py 2>/dev/null | grep '^RESULT:'
"""
import bpy
import json

result = {}

for obj in bpy.data.objects:
    if not obj.modifiers:
        continue

    mods = []
    for mod in obj.modifiers:
        mod_info = {"name": mod.name, "type": mod.type}

        if mod.type == 'SUBSURF':
            mod_info["levels"] = mod.levels
            mod_info["render_levels"] = mod.render_levels

        elif mod.type == 'BOOLEAN':
            mod_info["operation"] = mod.operation
            mod_info["object"] = mod.object.name if mod.object else None

        elif mod.type == 'MIRROR':
            mod_info["use_axis"] = [mod.use_axis[0], mod.use_axis[1], mod.use_axis[2]]
            mod_info["mirror_object"] = mod.mirror_object.name if mod.mirror_object else None

        elif mod.type == 'ARRAY':
            mod_info["count"] = mod.count
            mod_info["use_relative_offset"] = mod.use_relative_offset
            mod_info["relative_offset_displace"] = list(mod.relative_offset_displace)

        elif mod.type == 'BEVEL':
            mod_info["width"] = round(mod.width, 4)
            mod_info["segments"] = mod.segments
            mod_info["limit_method"] = mod.limit_method

        elif mod.type == 'SOLIDIFY':
            mod_info["thickness"] = round(mod.thickness, 4)
            mod_info["offset"] = round(mod.offset, 4)

        elif mod.type == 'DECIMATE':
            mod_info["decimate_type"] = mod.decimate_type
            mod_info["ratio"] = round(mod.ratio, 4)

        elif mod.type == 'WIREFRAME':
            mod_info["thickness"] = round(mod.thickness, 4)

        elif mod.type == 'SCREW':
            mod_info["angle"] = round(mod.angle, 4)
            mod_info["steps"] = mod.steps
            mod_info["screw_offset"] = round(mod.screw_offset, 4)

        elif mod.type == 'SKIN':
            pass  # No simple params

        elif mod.type == 'REMESH':
            mod_info["mode"] = mod.mode
            mod_info["octree_depth"] = mod.octree_depth

        mods.append(mod_info)

    result[obj.name] = mods

print(f"RESULT:{json.dumps(result)}")
