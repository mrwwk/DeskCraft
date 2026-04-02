"""check_world.py - Check world/environment settings in Blender scene.

Outputs JSON with world environment info: HDRI filename, background color, etc.

Usage:
    blender --background scene.blend --python check_world.py 2>/dev/null | grep '^RESULT:'
"""
import bpy
import json
import os

result = {"has_hdri": False, "has_world": False}

world = bpy.context.scene.world
if world:
    result["has_world"] = True
    result["world_name"] = world.name

    if world.use_nodes:
        result["use_nodes"] = True

        for node in world.node_tree.nodes:
            if node.type == 'TEX_ENVIRONMENT' and node.image:
                result["has_hdri"] = True
                result["hdri_filepath"] = node.image.filepath
                result["hdri_filename"] = os.path.basename(node.image.filepath)
                result["hdri_name"] = node.image.name
                break

            if node.type == 'BACKGROUND':
                color = node.inputs['Color'].default_value
                result["background_color"] = [round(v, 4) for v in color]
                result["background_strength"] = round(node.inputs['Strength'].default_value, 4)

print(f"RESULT:{json.dumps(result)}")
