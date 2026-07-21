"""
Improved Blender material check script (v2).

Runs inside Blender via --background --python.
Outputs RESULT:{json} to stdout for grep capture.

Key improvement over v1: properly traces Image Texture connections through
intermediate nodes (Normal Map, Color Ramp, Mix, Math, etc.) to find the
final Principled BSDF input socket, rather than only reporting direct connections.

VM command pattern:
    /snap/bin/blender --background /home/user/Documents/scene.blend \
        --python /tmp/check_material.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'
"""

import bpy
import json


def _trace_to_principled(from_node, from_socket_name, visited=None, depth=0):
    """Recursively trace connections from a node's output socket to find
    the final Principled BSDF input socket name(s).

    Traverses through intermediate nodes such as Normal Map, Bump,
    Color Ramp, Mix, Math, Vector Math, Gamma, Invert, Hue/Saturation,
    Brightness/Contrast, RGB Curves, Map Range, and similar shader nodes.

    Args:
        from_node: Starting Blender shader node.
        from_socket_name: Name of the output socket to trace from.
        visited: Set of (node_name, socket_name) tuples to prevent cycles.
        depth: Current recursion depth (max 30).

    Returns:
        List of Principled BSDF input socket names reached.
    """
    if visited is None:
        visited = set()

    if depth > 30:
        return []

    node_key = (from_node.name, from_socket_name)
    if node_key in visited:
        return []
    visited.add(node_key)

    results = []

    output_socket = None
    for out in from_node.outputs:
        if out.name == from_socket_name:
            output_socket = out
            break

    if output_socket is None or not output_socket.is_linked:
        return []

    for link in output_socket.links:
        to_node = link.to_node
        to_socket = link.to_socket

        if to_node.type == 'BSDF_PRINCIPLED':
            # Direct connection to Principled BSDF — record the input socket
            results.append(to_socket.name)

        elif to_node.type in ('NORMAL_MAP', 'BUMP'):
            # Normal Map / Bump converts an input to a Normal output.
            # Follow the Normal output to find where it connects.
            results.extend(
                _trace_to_principled(to_node, 'Normal', visited.copy(), depth + 1)
            )

        elif to_node.type in ('GROUP', 'GROUP_INPUT', 'GROUP_OUTPUT'):
            # Group nodes — skip (too complex to trace generically)
            pass

        elif to_node.type == 'MATERIAL_OUTPUT':
            # Reached the terminal output node — not a Principled BSDF
            pass

        else:
            # Generic intermediate node (Color Ramp, Mix, Math, Gamma,
            # Invert, Hue/Sat, Brightness/Contrast, RGB Curves, Map Range,
            # Separate/Combine XYZ/Color, Vector Math, etc.).
            # Follow all linked outputs.
            for check_out in to_node.outputs:
                if check_out.is_linked:
                    results.extend(
                        _trace_to_principled(to_node, check_out.name, visited.copy(), depth + 1)
                    )

    return results


def check_material():
    """Extract material texture connections from the current Blender scene.

    Returns:
        dict: {object_name: [material_data, ...]}
        Each material_data contains:
            - name, use_nodes, base_color, metallic, roughness, alpha
            - image_textures: [{image_name, filepath, filename, connected_to}]
            - texture_connections: {filename: [socket_names]}
    """
    result = {}

    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue

        obj_materials = []
        for slot in obj.material_slots:
            mat = slot.material
            if mat is None or not mat.use_nodes:
                continue

            mat_data = {
                "name": mat.name,
                "use_nodes": mat.use_nodes,
            }

            nodes = mat.node_tree.nodes

            # Find Principled BSDF for PBR parameters
            principled = None
            for node in nodes:
                if node.type == 'BSDF_PRINCIPLED':
                    principled = node
                    break

            if principled:
                try:
                    mat_data["base_color"] = list(
                        principled.inputs['Base Color'].default_value
                    )
                except (KeyError, AttributeError):
                    mat_data["base_color"] = [0.8, 0.8, 0.8, 1.0]
                mat_data["metallic"] = principled.inputs.get(
                    'Metallic', type('', (), {'default_value': 0.0})()
                ).default_value
                mat_data["roughness"] = principled.inputs.get(
                    'Roughness', type('', (), {'default_value': 0.5})()
                ).default_value
                mat_data["alpha"] = principled.inputs.get(
                    'Alpha', type('', (), {'default_value': 1.0})()
                ).default_value

            # Find all Image Texture nodes and trace their connections
            image_textures = []
            texture_connections = {}

            for node in nodes:
                if node.type != 'TEX_IMAGE':
                    continue
                if node.image is None:
                    continue

                filename = node.image.name
                connected_to = []

                # Trace Color output
                color_out = node.outputs.get('Color')
                if color_out and color_out.is_linked:
                    targets = _trace_to_principled(node, 'Color')
                    connected_to.extend(targets)

                # Trace Alpha output (used for alpha/roughness maps occasionally)
                alpha_out = node.outputs.get('Alpha')
                if alpha_out and alpha_out.is_linked:
                    targets = _trace_to_principled(node, 'Alpha')
                    connected_to.extend(targets)

                # Deduplicate
                connected_to = list(set(connected_to))

                tex_data = {
                    "image_name": node.image.name,
                    "filepath": (
                        node.image.filepath
                        if hasattr(node.image, 'filepath')
                        else ""
                    ),
                    "filename": filename,
                    "connected_to": connected_to,
                }
                image_textures.append(tex_data)

                if filename not in texture_connections:
                    texture_connections[filename] = []
                for ct in connected_to:
                    if ct not in texture_connections[filename]:
                        texture_connections[filename].append(ct)

            mat_data["image_textures"] = image_textures
            mat_data["texture_connections"] = texture_connections

            obj_materials.append(mat_data)

        if obj_materials:
            result[obj.name] = obj_materials

    return result


if __name__ == "__main__":
    data = check_material()
    print(f"RESULT:{json.dumps(data)}")
