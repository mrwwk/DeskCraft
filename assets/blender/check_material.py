"""check_material.py - Check materials and shader properties in Blender scene.

Outputs JSON with material info per object: base color, metallic, roughness,
alpha, texture connections, etc.

Usage:
    blender --background scene.blend --python check_material.py 2>/dev/null | grep '^RESULT:'
"""
import bpy
import json
import os

result = {}

for obj in bpy.data.objects:
    if obj.type not in ('MESH', 'FONT') or not obj.data.materials:
        continue

    obj_materials = []
    for mat in obj.data.materials:
        if not mat:
            continue
        mat_info = {
            "name": mat.name,
            "use_nodes": mat.use_nodes,
        }

        if mat.use_nodes:
            for node in mat.node_tree.nodes:
                if node.type == 'BSDF_PRINCIPLED':
                    bc = node.inputs['Base Color'].default_value
                    mat_info["base_color"] = [round(v, 4) for v in bc]
                    mat_info["metallic"] = round(node.inputs['Metallic'].default_value, 4)
                    mat_info["roughness"] = round(node.inputs['Roughness'].default_value, 4)

                    # Alpha - try both 'Alpha' and 'Transmission Weight' for Blender 4+
                    for alpha_name in ['Alpha', 'Transmission Weight']:
                        if alpha_name in node.inputs:
                            mat_info["alpha"] = round(node.inputs[alpha_name].default_value, 4)
                            break

                    # Check for connected image texture on Base Color
                    for link in mat.node_tree.links:
                        if link.to_node == node and link.to_socket.name == 'Base Color':
                            from_node = link.from_node
                            if from_node.type == 'TEX_IMAGE' and from_node.image:
                                mat_info["texture_filepath"] = from_node.image.filepath
                                mat_info["texture_filename"] = os.path.basename(from_node.image.filepath)
                                mat_info["texture_name"] = from_node.image.name
                    break  # Only check first Principled BSDF

            # Also check for any image texture nodes
            tex_nodes = []
            # Build a per-image list of sockets this image eventually drives
            # (directly or through helper nodes like Normal Map).
            connections_by_image = {}

            def walk_outputs(node, visited=None):
                if visited is None:
                    visited = set()
                if node in visited:
                    return []
                visited.add(node)

                results = []
                for out_socket in node.outputs:
                    for link in out_socket.links:
                        to_node = link.to_node
                        # If this path reaches Principled BSDF, record its socket name.
                        if to_node.type == 'BSDF_PRINCIPLED':
                            results.append(link.to_socket.name)
                        else:
                            results.extend(walk_outputs(to_node, visited.copy()))
                return results

            for node in mat.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image:
                    connected_to = sorted(set(walk_outputs(node)))
                    connections_by_image[node.image.name] = connected_to
                    tex_nodes.append({
                        "image_name": node.image.name,
                        "filepath": node.image.filepath,
                        "filename": os.path.basename(node.image.filepath),
                        "connected_to": connected_to,
                    })
            if tex_nodes:
                mat_info["image_textures"] = tex_nodes
                mat_info["texture_connections"] = connections_by_image

        obj_materials.append(mat_info)

    result[obj.name] = obj_materials

print(f"RESULT:{json.dumps(result)}")
