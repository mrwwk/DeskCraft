"""check_collection.py - Check collections in Blender scene.

Outputs JSON with collection hierarchy and which objects belong to which collections.

Usage:
    blender --background scene.blend --python check_collection.py 2>/dev/null | grep '^RESULT:'
"""
import bpy
import json

result = {
    "collections": [],
    "object_collections": {},
}

# All collections (including nested)
def collect_info(coll, depth=0):
    info = {
        "name": coll.name,
        "depth": depth,
        "objects": [obj.name for obj in coll.objects],
        "children": [c.name for c in coll.children],
        "hide_viewport": coll.hide_viewport,
        "hide_render": coll.hide_render,
    }
    result["collections"].append(info)
    for child in coll.children:
        collect_info(child, depth + 1)

# Start from scene collection
scene_coll = bpy.context.scene.collection
collect_info(scene_coll)

# Also collect from bpy.data.collections (user-created)
result["user_collections"] = [c.name for c in bpy.data.collections]

# Object-to-collection mapping
for obj in bpy.data.objects:
    colls = [c.name for c in obj.users_collection]
    result["object_collections"][obj.name] = colls

print(f"RESULT:{json.dumps(result)}")
