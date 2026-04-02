#!/usr/bin/env python3
"""Generate all Blender .blend asset files for OSWorld tasks.

Usage:
    blender --background --python generate_blend_assets.py

This script must be run inside Blender's embedded Python environment.
"""

import bpy
import os
import math

ASSET_DIR = os.path.dirname(os.path.abspath(__file__))


def clear_scene():
    """Remove all objects from the scene."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)


def save_blend(filename):
    """Save current scene as .blend file."""
    filepath = os.path.join(ASSET_DIR, filename)
    bpy.ops.wm.save_as_mainfile(filepath=filepath)
    print(f"  Saved: {filepath}")


def reset_scene():
    """Reset to a clean state by removing everything."""
    # Remove all objects
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    # Remove orphan data
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)
    for block in bpy.data.cameras:
        if block.users == 0:
            bpy.data.cameras.remove(block)
    for block in bpy.data.lights:
        if block.users == 0:
            bpy.data.lights.remove(block)
    # Remove extra collections
    for coll in list(bpy.data.collections):
        bpy.data.collections.remove(coll)


# ============================================================
# 1. default_cube.blend - Blender default scene
# ============================================================
def generate_default_cube():
    print("Generating default_cube.blend...")
    reset_scene()

    # Cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    bpy.context.active_object.name = "Cube"

    # Camera
    bpy.ops.object.camera_add(location=(7.359, -6.926, 4.958))
    cam = bpy.context.active_object
    cam.name = "Camera"
    cam.rotation_euler = (math.radians(63.6), 0, math.radians(46.7))
    bpy.context.scene.camera = cam

    # Light
    bpy.ops.object.light_add(type='POINT', location=(4.076, 1.006, 5.904))
    light = bpy.context.active_object
    light.name = "Light"
    light.data.energy = 1000

    save_blend("default_cube.blend")


# ============================================================
# 2. simple_scene.blend - Multiple basic objects
# ============================================================
def generate_simple_scene():
    print("Generating simple_scene.blend...")
    reset_scene()

    # Cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    bpy.context.active_object.name = "Cube"

    # Sphere
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(3, 0, 0))
    bpy.context.active_object.name = "Sphere"

    # Cylinder
    bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=2, location=(-3, 0, 0))
    bpy.context.active_object.name = "Cylinder"

    # Plane (ground)
    bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, -1))
    bpy.context.active_object.name = "Plane"

    # Empty
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 2))
    bpy.context.active_object.name = "Empty"

    # Camera
    bpy.ops.object.camera_add(location=(7, -7, 5))
    cam = bpy.context.active_object
    cam.name = "Camera"
    cam.rotation_euler = (math.radians(63.6), 0, math.radians(46.7))
    bpy.context.scene.camera = cam

    # Light
    bpy.ops.object.light_add(type='POINT', location=(4, 1, 6))
    light = bpy.context.active_object
    light.name = "Light"
    light.data.energy = 1000

    save_blend("simple_scene.blend")


# ============================================================
# 3. animated_ball.blend - Ball with keyframe animation
# ============================================================
def generate_animated_ball():
    print("Generating animated_ball.blend...")
    reset_scene()

    # Ball
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0))
    ball = bpy.context.active_object
    ball.name = "Ball"

    # Keyframe at frame 1
    bpy.context.scene.frame_set(1)
    ball.location = (0, 0, 0)
    ball.keyframe_insert(data_path="location", frame=1)

    # Keyframe at frame 60
    ball.location = (5, 0, 3)
    ball.keyframe_insert(data_path="location", frame=60)

    # Set frame range
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 60

    # Camera
    bpy.ops.object.camera_add(location=(7, -7, 5))
    cam = bpy.context.active_object
    cam.name = "Camera"
    cam.rotation_euler = (math.radians(63.6), 0, math.radians(46.7))
    bpy.context.scene.camera = cam

    # Sun light
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    light = bpy.context.active_object
    light.name = "Sun"
    light.data.energy = 5

    save_blend("animated_ball.blend")


# ============================================================
# 4. textured_cube.blend - Cube with material (ready for texture)
# ============================================================
def generate_textured_cube():
    print("Generating textured_cube.blend...")
    reset_scene()

    # Cube with UV map
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.active_object
    cube.name = "Cube"

    # Create material with Principled BSDF
    mat = bpy.data.materials.new(name="CubeMaterial")
    mat.use_nodes = True
    cube.data.materials.append(mat)

    # Camera
    bpy.ops.object.camera_add(location=(5, -5, 4))
    cam = bpy.context.active_object
    cam.name = "Camera"
    cam.rotation_euler = (math.radians(63.6), 0, math.radians(46.7))
    bpy.context.scene.camera = cam

    # Light
    bpy.ops.object.light_add(type='POINT', location=(3, -3, 5))
    light = bpy.context.active_object
    light.name = "Light"
    light.data.energy = 1000

    save_blend("textured_cube.blend")


# ============================================================
# 5. cube_with_subsurf.blend - Cube with Subdivision Surface
# ============================================================
def generate_cube_with_subsurf():
    print("Generating cube_with_subsurf.blend...")
    reset_scene()

    # Cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.active_object
    cube.name = "Cube"

    # Add Subdivision Surface modifier
    mod = cube.modifiers.new(name="Subdivision", type='SUBSURF')
    mod.levels = 2
    mod.render_levels = 2

    # Camera
    bpy.ops.object.camera_add(location=(5, -5, 4))
    cam = bpy.context.active_object
    cam.name = "Camera"
    cam.rotation_euler = (math.radians(63.6), 0, math.radians(46.7))
    bpy.context.scene.camera = cam

    # Light
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    light = bpy.context.active_object
    light.name = "Sun"
    light.data.energy = 5

    save_blend("cube_with_subsurf.blend")


# ============================================================
# 6. text_scene.blend - Scene with Text object
# ============================================================
def generate_text_scene():
    print("Generating text_scene.blend...")
    reset_scene()

    # Text
    bpy.ops.object.text_add(location=(0, 0, 0))
    text_obj = bpy.context.active_object
    text_obj.name = "Text"
    text_obj.data.body = "Text"

    # Camera
    bpy.ops.object.camera_add(location=(5, -5, 4))
    cam = bpy.context.active_object
    cam.name = "Camera"
    cam.rotation_euler = (math.radians(63.6), 0, math.radians(46.7))
    bpy.context.scene.camera = cam

    # Light
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    light = bpy.context.active_object
    light.name = "Sun"
    light.data.energy = 5

    save_blend("text_scene.blend")


# ============================================================
# 7. simple_scene_with_collection.blend - Scene with empty Props collection
# ============================================================
def generate_scene_with_collection():
    print("Generating simple_scene_with_collection.blend...")
    reset_scene()

    # Cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    bpy.context.active_object.name = "Cube"

    # Sphere
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(3, 0, 0))
    bpy.context.active_object.name = "Sphere"

    # Camera
    bpy.ops.object.camera_add(location=(7, -7, 5))
    cam = bpy.context.active_object
    cam.name = "Camera"
    cam.rotation_euler = (math.radians(63.6), 0, math.radians(46.7))
    bpy.context.scene.camera = cam

    # Light
    bpy.ops.object.light_add(type='POINT', location=(4, 1, 6))
    light = bpy.context.active_object
    light.name = "Light"
    light.data.energy = 1000

    # Create empty "Props" collection
    props_coll = bpy.data.collections.new("Props")
    bpy.context.scene.collection.children.link(props_coll)

    save_blend("simple_scene_with_collection.blend")


# ============================================================
# 8. multi_material.blend - Object with multiple materials
# ============================================================
def generate_multi_material():
    print("Generating multi_material.blend...")
    reset_scene()

    # Cube
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.active_object
    cube.name = "Cube"

    # Material 1 - Red
    mat1 = bpy.data.materials.new(name="Red")
    mat1.use_nodes = True
    principled1 = mat1.node_tree.nodes.get("Principled BSDF")
    principled1.inputs['Base Color'].default_value = (1.0, 0.0, 0.0, 1.0)
    cube.data.materials.append(mat1)

    # Material 2 - Blue
    mat2 = bpy.data.materials.new(name="Blue")
    mat2.use_nodes = True
    principled2 = mat2.node_tree.nodes.get("Principled BSDF")
    principled2.inputs['Base Color'].default_value = (0.0, 0.0, 1.0, 1.0)
    cube.data.materials.append(mat2)

    # Material 3 - Green
    mat3 = bpy.data.materials.new(name="Green")
    mat3.use_nodes = True
    principled3 = mat3.node_tree.nodes.get("Principled BSDF")
    principled3.inputs['Base Color'].default_value = (0.0, 1.0, 0.0, 1.0)
    cube.data.materials.append(mat3)

    # Camera
    bpy.ops.object.camera_add(location=(5, -5, 4))
    cam = bpy.context.active_object
    cam.name = "Camera"
    cam.rotation_euler = (math.radians(63.6), 0, math.radians(46.7))
    bpy.context.scene.camera = cam

    # Light
    bpy.ops.object.light_add(type='POINT', location=(3, -3, 5))
    light = bpy.context.active_object
    light.name = "Light"
    light.data.energy = 1000

    save_blend("multi_material.blend")


# ============================================================
# 9. two_cubes.blend - Two cubes for boolean operations etc.
# ============================================================
def generate_two_cubes():
    print("Generating two_cubes.blend...")
    reset_scene()

    # Cube 1
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    bpy.context.active_object.name = "Cube"

    # Cube 2 (overlapping)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(1.5, 1.5, 0))
    bpy.context.active_object.name = "Cube.001"

    # Camera
    bpy.ops.object.camera_add(location=(7, -7, 5))
    cam = bpy.context.active_object
    cam.name = "Camera"
    cam.rotation_euler = (math.radians(63.6), 0, math.radians(46.7))
    bpy.context.scene.camera = cam

    # Light
    bpy.ops.object.light_add(type='POINT', location=(4, 1, 6))
    light = bpy.context.active_object
    light.name = "Light"
    light.data.energy = 1000

    save_blend("two_cubes.blend")


# ============================================================
# 10. monkey_scene.blend - Suzanne monkey head for complex mesh tests
# ============================================================
def generate_monkey_scene():
    print("Generating monkey_scene.blend...")
    reset_scene()

    # Monkey (Suzanne)
    bpy.ops.mesh.primitive_monkey_add(size=2, location=(0, 0, 0))
    bpy.context.active_object.name = "Suzanne"

    # Ground plane
    bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, -1))
    bpy.context.active_object.name = "Ground"

    # Camera
    bpy.ops.object.camera_add(location=(5, -5, 3))
    cam = bpy.context.active_object
    cam.name = "Camera"
    cam.rotation_euler = (math.radians(70), 0, math.radians(46.7))
    bpy.context.scene.camera = cam

    # Light
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    light = bpy.context.active_object
    light.name = "Sun"
    light.data.energy = 5

    save_blend("monkey_scene.blend")


# ============================================================
# Main
# ============================================================
if __name__ == "__main__":
    print(f"\n{'='*60}")
    print(f"Generating Blender assets in: {ASSET_DIR}")
    print(f"{'='*60}\n")

    generate_default_cube()
    generate_simple_scene()
    generate_animated_ball()
    generate_textured_cube()
    generate_cube_with_subsurf()
    generate_text_scene()
    generate_scene_with_collection()
    generate_multi_material()
    generate_two_cubes()
    generate_monkey_scene()

    print(f"\n{'='*60}")
    print(f"Done! Generated 10 .blend files in {ASSET_DIR}")
    print(f"{'='*60}")
