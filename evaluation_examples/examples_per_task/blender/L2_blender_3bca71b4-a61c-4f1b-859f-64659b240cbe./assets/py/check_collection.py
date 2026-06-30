"""check_collection.py - Check collections in Blender scene.

Outputs JSON with collection hierarchy and which objects belong to which collections.
Also reads LayerCollection.hide_viewport (the Outliner eye icon state).

Usage:
    blender --background scene.blend --python check_collection.py 2>/dev/null | grep '^RESULT:'
"""
import bpy
import json

result = {
    "collections": [],
    "object_collections": {},
}

# Build a map of all LayerCollection hide_viewport states.
# LayerCollection.hide_viewport corresponds to the Outliner "eye icon"
# and is independent of Collection.hide_viewport (data-block property).
def build_layer_collection_map(layer_coll, result_map):
    """Recursively collect LayerCollection hide_viewport states."""
    result_map[layer_coll.name] = layer_coll.hide_viewport
    for child in layer_coll.children:
        build_layer_collection_map(child, result_map)

layer_coll_map = {}
# bpy.context.view_layer.layer_collection is the root (Scene Collection)
build_layer_collection_map(bpy.context.view_layer.layer_collection, layer_coll_map)

# All collections (including nested)
def collect_info(coll, depth=0):
    info = {
        "name": coll.name,
        "depth": depth,
        "objects": [obj.name for obj in coll.objects],
        "children": [c.name for c in coll.children],
        "hide_viewport": coll.hide_viewport,
        "hide_render": coll.hide_render,
        # LayerCollection hide_viewport: the actual Outliner eye icon state
        "viewlayer_hide_viewport": layer_coll_map.get(
            coll.name, coll.hide_viewport
        ),
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
