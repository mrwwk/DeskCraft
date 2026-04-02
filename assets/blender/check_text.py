"""check_text.py - Check text/font objects in Blender scene.

Outputs JSON with text object info: body text, font size, alignment, etc.

Usage:
    blender --background scene.blend --python check_text.py 2>/dev/null | grep '^RESULT:'
"""
import bpy
import json

result = {}

for obj in bpy.data.objects:
    if obj.type != 'FONT':
        continue

    text_data = obj.data
    result[obj.name] = {
        "body": text_data.body,
        "size": round(text_data.size, 4),
        "align_x": text_data.align_x,
        "align_y": text_data.align_y,
        "extrude": round(text_data.extrude, 4),
        "offset": round(text_data.offset, 4),
        "shear": round(text_data.shear, 4),
        "bevel_depth": round(text_data.bevel_depth, 4),
        "bevel_resolution": text_data.bevel_resolution,
        "space_character": round(text_data.space_character, 4),
        "space_line": round(text_data.space_line, 4),
        "space_word": round(text_data.space_word, 4),
        "material_count": len(text_data.materials),
        "location": [round(v, 4) for v in obj.location],
        "rotation_deg": [round(v * 57.2958, 2) for v in obj.rotation_euler],
    }

print(f"RESULT:{json.dumps(result)}")
