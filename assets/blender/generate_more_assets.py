#!/usr/bin/env python3
"""Generate additional Blender .blend asset files for OSWorld tasks.

Usage:
    blender --background --python generate_more_assets.py

Generates scenes that cover more task scenarios beyond the basic set.
"""

import bpy
import os
import math

ASSET_DIR = os.path.dirname(os.path.abspath(__file__))


def reset_scene():
    """Remove all objects and orphan data."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
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
    for block in bpy.data.curves:
        if block.users == 0:
            bpy.data.curves.remove(block)
    for block in bpy.data.armatures:
        if block.users == 0:
            bpy.data.armatures.remove(block)
    for coll in list(bpy.data.collections):
        bpy.data.collections.remove(coll)


def add_default_camera_light():
    """Add standard camera and light to scene."""
    bpy.ops.object.camera_add(location=(7, -7, 5))
    cam = bpy.context.active_object
    cam.name = "Camera"
    cam.rotation_euler = (math.radians(63.6), 0, math.radians(46.7))
    bpy.context.scene.camera = cam

    bpy.ops.object.light_add(type='POINT', location=(4, 1, 6))
    light = bpy.context.active_object
    light.name = "Light"
    light.data.energy = 1000


def save_blend(filename):
    filepath = os.path.join(ASSET_DIR, filename)
    bpy.ops.wm.save_as_mainfile(filepath=filepath)
    print(f"  Saved: {filepath}")


# ============================================================
# 1. cube_sphere_boolean.blend
#    Cube and Sphere overlapping, ready for boolean operations
# ============================================================
def generate_cube_sphere_boolean():
    print("Generating cube_sphere_boolean.blend...")
    reset_scene()

    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    bpy.context.active_object.name = "Cube"

    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.3, location=(1, 1, 0))
    bpy.context.active_object.name = "Sphere"

    add_default_camera_light()
    save_blend("cube_sphere_boolean.blend")


# ============================================================
# 2. multi_light_scene.blend
#    Scene with Point, Sun, Spot, and Area lights
# ============================================================
def generate_multi_light():
    print("Generating multi_light_scene.blend...")
    reset_scene()

    # Ground
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
    bpy.context.active_object.name = "Ground"
    mat = bpy.data.materials.new(name="GroundMat")
    mat.use_nodes = True
    bpy.context.active_object.data.materials.append(mat)

    # Center sphere
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 1))
    bpy.context.active_object.name = "Sphere"

    # Point light
    bpy.ops.object.light_add(type='POINT', location=(3, 0, 3))
    bpy.context.active_object.name = "PointLight"
    bpy.context.active_object.data.energy = 500
    bpy.context.active_object.data.color = (1, 0.8, 0.6)

    # Sun light
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    bpy.context.active_object.name = "SunLight"
    bpy.context.active_object.data.energy = 3

    # Spot light
    bpy.ops.object.light_add(type='SPOT', location=(-3, -3, 5))
    spot = bpy.context.active_object
    spot.name = "SpotLight"
    spot.data.energy = 800
    spot.data.spot_size = math.radians(45)
    spot.rotation_euler = (math.radians(45), 0, math.radians(-135))

    # Area light
    bpy.ops.object.light_add(type='AREA', location=(0, 4, 4))
    area = bpy.context.active_object
    area.name = "AreaLight"
    area.data.energy = 300
    area.data.size = 2
    area.rotation_euler = (math.radians(-45), 0, 0)

    # Camera
    bpy.ops.object.camera_add(location=(7, -7, 5))
    cam = bpy.context.active_object
    cam.name = "Camera"
    cam.rotation_euler = (math.radians(63.6), 0, math.radians(46.7))
    bpy.context.scene.camera = cam

    save_blend("multi_light_scene.blend")


# ============================================================
# 3. curve_scene.blend
#    Scene with Bezier curve and NURBS path
# ============================================================
def generate_curve_scene():
    print("Generating curve_scene.blend...")
    reset_scene()

    # Bezier curve
    bpy.ops.curve.primitive_bezier_curve_add(location=(0, 0, 0))
    bpy.context.active_object.name = "BezierCurve"

    # NURBS circle
    bpy.ops.curve.primitive_nurbs_circle_add(radius=2, location=(0, 3, 0))
    bpy.context.active_object.name = "NurbsCircle"

    # Bezier circle (for path following)
    bpy.ops.curve.primitive_bezier_circle_add(radius=3, location=(0, 0, 0))
    bpy.context.active_object.name = "CirclePath"

    # Small cube to follow path
    bpy.ops.mesh.primitive_cube_add(size=0.5, location=(3, 0, 0))
    bpy.context.active_object.name = "Follower"

    add_default_camera_light()
    save_blend("curve_scene.blend")


# ============================================================
# 4. armature_scene.blend
#    Simple armature with 3 bones + a cylinder mesh
# ============================================================
def generate_armature_scene():
    print("Generating armature_scene.blend...")
    reset_scene()

    # Create cylinder (body)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=4, location=(0, 0, 2))
    body = bpy.context.active_object
    body.name = "Body"

    # Create armature
    bpy.ops.object.armature_add(location=(0, 0, 0))
    armature_obj = bpy.context.active_object
    armature_obj.name = "Armature"

    # Edit armature - add bones
    bpy.ops.object.mode_set(mode='EDIT')
    arm = armature_obj.data

    # Root bone (already exists)
    bone1 = arm.edit_bones[0]
    bone1.name = "Bone.Root"
    bone1.head = (0, 0, 0)
    bone1.tail = (0, 0, 1.5)

    # Middle bone
    bone2 = arm.edit_bones.new("Bone.Mid")
    bone2.head = (0, 0, 1.5)
    bone2.tail = (0, 0, 3)
    bone2.parent = bone1

    # Top bone
    bone3 = arm.edit_bones.new("Bone.Top")
    bone3.head = (0, 0, 3)
    bone3.tail = (0, 0, 4)
    bone3.parent = bone2

    bpy.ops.object.mode_set(mode='OBJECT')

    add_default_camera_light()
    save_blend("armature_scene.blend")


# ============================================================
# 5. materials_showcase.blend
#    Multiple objects each with different material setups
# ============================================================
def generate_materials_showcase():
    print("Generating materials_showcase.blend...")
    reset_scene()

    # Metal sphere
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.8, location=(-3, 0, 0.8))
    obj = bpy.context.active_object
    obj.name = "MetalSphere"
    mat = bpy.data.materials.new(name="Metal")
    mat.use_nodes = True
    p = mat.node_tree.nodes.get("Principled BSDF")
    p.inputs['Base Color'].default_value = (0.8, 0.8, 0.8, 1)
    p.inputs['Metallic'].default_value = 1.0
    p.inputs['Roughness'].default_value = 0.1
    obj.data.materials.append(mat)

    # Glass cube
    bpy.ops.mesh.primitive_cube_add(size=1.4, location=(0, 0, 0.7))
    obj = bpy.context.active_object
    obj.name = "GlassCube"
    mat = bpy.data.materials.new(name="Glass")
    mat.use_nodes = True
    p = mat.node_tree.nodes.get("Principled BSDF")
    p.inputs['Base Color'].default_value = (0.9, 0.95, 1.0, 1)
    p.inputs['Roughness'].default_value = 0.0
    p.inputs['IOR'].default_value = 1.45
    obj.data.materials.append(mat)

    # Rough ceramic cylinder
    bpy.ops.mesh.primitive_cylinder_add(radius=0.6, depth=1.6, location=(3, 0, 0.8))
    obj = bpy.context.active_object
    obj.name = "CeramicCylinder"
    mat = bpy.data.materials.new(name="Ceramic")
    mat.use_nodes = True
    p = mat.node_tree.nodes.get("Principled BSDF")
    p.inputs['Base Color'].default_value = (0.85, 0.45, 0.2, 1)
    p.inputs['Roughness'].default_value = 0.6
    p.inputs['Metallic'].default_value = 0.0
    obj.data.materials.append(mat)

    # Emissive torus
    bpy.ops.mesh.primitive_torus_add(major_radius=0.8, minor_radius=0.2, location=(0, 3, 0.8))
    obj = bpy.context.active_object
    obj.name = "EmissiveTorus"
    mat = bpy.data.materials.new(name="Emissive")
    mat.use_nodes = True
    p = mat.node_tree.nodes.get("Principled BSDF")
    p.inputs['Base Color'].default_value = (1.0, 0.3, 0.0, 1)
    p.inputs['Emission Color'].default_value = (1.0, 0.3, 0.0, 1)
    p.inputs['Emission Strength'].default_value = 5.0
    obj.data.materials.append(mat)

    # No-material cone
    bpy.ops.mesh.primitive_cone_add(radius1=0.6, depth=1.5, location=(-3, 3, 0.75))
    bpy.context.active_object.name = "PlainCone"

    # Ground
    bpy.ops.mesh.primitive_plane_add(size=15, location=(0, 0, 0))
    bpy.context.active_object.name = "Ground"

    add_default_camera_light()
    save_blend("materials_showcase.blend")


# ============================================================
# 6. hierarchy_scene.blend
#    Parent-child hierarchy: Solar system style
# ============================================================
def generate_hierarchy_scene():
    print("Generating hierarchy_scene.blend...")
    reset_scene()

    # Sun (center)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.5, location=(0, 0, 0))
    sun = bpy.context.active_object
    sun.name = "Sun"
    mat = bpy.data.materials.new(name="SunMat")
    mat.use_nodes = True
    p = mat.node_tree.nodes.get("Principled BSDF")
    p.inputs['Base Color'].default_value = (1.0, 0.8, 0.0, 1)
    p.inputs['Emission Color'].default_value = (1.0, 0.8, 0.0, 1)
    p.inputs['Emission Strength'].default_value = 3.0
    sun.data.materials.append(mat)

    # Planet 1
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.4, location=(4, 0, 0))
    planet1 = bpy.context.active_object
    planet1.name = "Planet1"

    # Planet 2
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.6, location=(7, 0, 0))
    planet2 = bpy.context.active_object
    planet2.name = "Planet2"

    # Moon of Planet 2
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.15, location=(8, 0, 0))
    moon = bpy.context.active_object
    moon.name = "Moon"
    moon.parent = planet2

    # Planet 3
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=(10, 0, 0))
    planet3 = bpy.context.active_object
    planet3.name = "Planet3"

    add_default_camera_light()
    bpy.context.scene.camera.location = (0, -15, 8)
    save_blend("hierarchy_scene.blend")


# ============================================================
# 7. multiple_collections.blend
#    Scene organized into multiple collections
# ============================================================
def generate_multiple_collections():
    print("Generating multiple_collections.blend...")
    reset_scene()

    # Create collections
    geo_coll = bpy.data.collections.new("Geometry")
    bpy.context.scene.collection.children.link(geo_coll)

    lights_coll = bpy.data.collections.new("Lights")
    bpy.context.scene.collection.children.link(lights_coll)

    cameras_coll = bpy.data.collections.new("Cameras")
    bpy.context.scene.collection.children.link(cameras_coll)

    # Objects in Geometry
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.active_object
    cube.name = "Cube"
    geo_coll.objects.link(cube)
    bpy.context.scene.collection.objects.unlink(cube)

    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(3, 0, 0))
    sphere = bpy.context.active_object
    sphere.name = "Sphere"
    geo_coll.objects.link(sphere)
    bpy.context.scene.collection.objects.unlink(sphere)

    bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=2, location=(-3, 0, 0))
    cyl = bpy.context.active_object
    cyl.name = "Cylinder"
    geo_coll.objects.link(cyl)
    bpy.context.scene.collection.objects.unlink(cyl)

    # Light
    bpy.ops.object.light_add(type='POINT', location=(4, 1, 6))
    light = bpy.context.active_object
    light.name = "Light"
    light.data.energy = 1000
    lights_coll.objects.link(light)
    bpy.context.scene.collection.objects.unlink(light)

    # Camera
    bpy.ops.object.camera_add(location=(7, -7, 5))
    cam = bpy.context.active_object
    cam.name = "Camera"
    cam.rotation_euler = (math.radians(63.6), 0, math.radians(46.7))
    bpy.context.scene.camera = cam
    cameras_coll.objects.link(cam)
    bpy.context.scene.collection.objects.unlink(cam)

    save_blend("multiple_collections.blend")


# ============================================================
# 8. uv_unwrapped_cube.blend
#    Cube with proper UV unwrap for texture mapping tasks
# ============================================================
def generate_uv_cube():
    print("Generating uv_unwrapped_cube.blend...")
    reset_scene()

    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.active_object
    cube.name = "Cube"

    # Smart UV project
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66))
    bpy.ops.object.mode_set(mode='OBJECT')

    # Create material
    mat = bpy.data.materials.new(name="CubeMaterial")
    mat.use_nodes = True
    cube.data.materials.append(mat)

    add_default_camera_light()
    save_blend("uv_unwrapped_cube.blend")


# ============================================================
# 9. empty_scene.blend
#    Completely empty scene (no objects, just camera)
# ============================================================
def generate_empty_scene():
    print("Generating empty_scene.blend...")
    reset_scene()

    bpy.ops.object.camera_add(location=(7, -7, 5))
    cam = bpy.context.active_object
    cam.name = "Camera"
    cam.rotation_euler = (math.radians(63.6), 0, math.radians(46.7))
    bpy.context.scene.camera = cam

    save_blend("empty_scene.blend")


# ============================================================
# 10. sculpt_base.blend
#     High-poly sphere ready for sculpting
# ============================================================
def generate_sculpt_base():
    print("Generating sculpt_base.blend...")
    reset_scene()

    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=2, location=(0, 0, 0))
    sphere = bpy.context.active_object
    sphere.name = "SculptSphere"

    add_default_camera_light()
    save_blend("sculpt_base.blend")


# ============================================================
# 11. modifier_stack.blend
#     Cube with multiple modifiers stacked
# ============================================================
def generate_modifier_stack():
    print("Generating modifier_stack.blend...")
    reset_scene()

    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.active_object
    cube.name = "Cube"

    # Array modifier
    arr = cube.modifiers.new(name="Array", type='ARRAY')
    arr.count = 3
    arr.relative_offset_displace = (1.2, 0, 0)

    # Bevel modifier
    bev = cube.modifiers.new(name="Bevel", type='BEVEL')
    bev.width = 0.05
    bev.segments = 2

    # Subdivision Surface
    sub = cube.modifiers.new(name="Subsurf", type='SUBSURF')
    sub.levels = 1
    sub.render_levels = 2

    add_default_camera_light()
    save_blend("modifier_stack.blend")


# ============================================================
# 12. animation_rotation.blend
#     Cube with rotation animation over 120 frames
# ============================================================
def generate_animation_rotation():
    print("Generating animation_rotation.blend...")
    reset_scene()

    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.active_object
    cube.name = "Cube"

    # Keyframe rotation
    bpy.context.scene.frame_set(1)
    cube.rotation_euler = (0, 0, 0)
    cube.keyframe_insert(data_path="rotation_euler", frame=1)

    cube.rotation_euler = (0, 0, math.radians(360))
    cube.keyframe_insert(data_path="rotation_euler", frame=120)

    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 120

    add_default_camera_light()
    save_blend("animation_rotation.blend")


# ============================================================
# 13. constraint_ready.blend
#     Objects positioned for constraint tasks (camera + targets)
# ============================================================
def generate_constraint_ready():
    print("Generating constraint_ready.blend...")
    reset_scene()

    # Target objects
    bpy.ops.mesh.primitive_cube_add(size=1.5, location=(0, 0, 0))
    bpy.context.active_object.name = "Target"

    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(3, 3, 0))
    bpy.context.active_object.name = "Orbiter"

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 3))
    bpy.context.active_object.name = "LookAtTarget"

    # Camera without constraint
    bpy.ops.object.camera_add(location=(7, -7, 5))
    cam = bpy.context.active_object
    cam.name = "Camera"
    cam.rotation_euler = (math.radians(63.6), 0, math.radians(46.7))
    bpy.context.scene.camera = cam

    bpy.ops.object.light_add(type='POINT', location=(4, 1, 6))
    bpy.context.active_object.name = "Light"
    bpy.context.active_object.data.energy = 1000

    save_blend("constraint_ready.blend")


# ============================================================
# 14. particles_ready.blend
#     Plane + emitter particle system already configured
# ============================================================
def generate_particles_ready():
    print("Generating particles_ready.blend...")
    reset_scene()

    # Emitter plane
    bpy.ops.mesh.primitive_plane_add(size=5, location=(0, 0, 3))
    plane = bpy.context.active_object
    plane.name = "Emitter"

    # Add particle system
    bpy.ops.object.particle_system_add()
    ps = plane.particle_systems[0]
    ps.settings.count = 500
    ps.settings.lifetime = 50
    ps.settings.type = 'EMITTER'

    # Ground
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
    bpy.context.active_object.name = "Ground"

    add_default_camera_light()
    save_blend("particles_ready.blend")


# ============================================================
# 15. render_ready_cycles.blend
#     Scene pre-configured for Cycles rendering
# ============================================================
def generate_render_ready_cycles():
    print("Generating render_ready_cycles.blend...")
    reset_scene()

    # Scene with objects
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
    cube = bpy.context.active_object
    cube.name = "Cube"

    # Material
    mat = bpy.data.materials.new(name="CubeMat")
    mat.use_nodes = True
    p = mat.node_tree.nodes.get("Principled BSDF")
    p.inputs['Base Color'].default_value = (0.2, 0.4, 0.8, 1)
    p.inputs['Metallic'].default_value = 0.3
    p.inputs['Roughness'].default_value = 0.4
    cube.data.materials.append(mat)

    # Ground
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = "Ground"
    gmat = bpy.data.materials.new(name="GroundMat")
    gmat.use_nodes = True
    ground.data.materials.append(gmat)

    # Camera
    bpy.ops.object.camera_add(location=(5, -5, 4))
    cam = bpy.context.active_object
    cam.name = "Camera"
    cam.rotation_euler = (math.radians(63.6), 0, math.radians(46.7))
    bpy.context.scene.camera = cam

    # Sun light
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    sun = bpy.context.active_object
    sun.name = "Sun"
    sun.data.energy = 5
    sun.rotation_euler = (math.radians(45), 0, math.radians(30))

    # Cycles settings
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 64
    bpy.context.scene.cycles.device = 'CPU'
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080

    save_blend("render_ready_cycles.blend")


# ============================================================
# 16. wireframe_display.blend
#     Multiple objects with different wireframe/solid setups
# ============================================================
def generate_wireframe():
    print("Generating wireframe_display.blend...")
    reset_scene()

    # Torus
    bpy.ops.mesh.primitive_torus_add(major_radius=1.5, minor_radius=0.4, location=(-3, 0, 1.5))
    bpy.context.active_object.name = "Torus"

    # Ico sphere
    bpy.ops.mesh.primitive_ico_sphere_add(radius=1, subdivisions=3, location=(0, 0, 1))
    bpy.context.active_object.name = "IcoSphere"

    # Cone
    bpy.ops.mesh.primitive_cone_add(radius1=1, depth=2, location=(3, 0, 1))
    bpy.context.active_object.name = "Cone"

    # Grid
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=10, y_subdivisions=10, size=4, location=(0, 4, 0))
    bpy.context.active_object.name = "Grid"

    add_default_camera_light()
    save_blend("wireframe_display.blend")


# ============================================================
# 17. linked_duplicates.blend
#     Objects sharing the same mesh data (linked duplicates)
# ============================================================
def generate_linked_duplicates():
    print("Generating linked_duplicates.blend...")
    reset_scene()

    # Original cube
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    original = bpy.context.active_object
    original.name = "Cube.Original"

    # Linked duplicates (share mesh data)
    for i, loc in enumerate([(2, 0, 0), (0, 2, 0), (2, 2, 0), (-2, 0, 0)]):
        bpy.ops.object.select_all(action='DESELECT')
        original.select_set(True)
        bpy.context.view_layer.objects.active = original
        bpy.ops.object.duplicate_move_linked(
            TRANSFORM_OT_translate={"value": loc}
        )
        bpy.context.active_object.name = f"Cube.Linked.{i+1}"

    add_default_camera_light()
    save_blend("linked_duplicates.blend")


# ============================================================
# 18. weight_paint_ready.blend
#     Mesh with vertex groups for weight painting tasks
# ============================================================
def generate_weight_paint():
    print("Generating weight_paint_ready.blend...")
    reset_scene()

    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.context.active_object
    cube.name = "Cube"

    # Subdivide for more vertices
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.subdivide(number_cuts=3)
    bpy.ops.object.mode_set(mode='OBJECT')

    # Add vertex groups
    vg1 = cube.vertex_groups.new(name="Top")
    vg2 = cube.vertex_groups.new(name="Bottom")

    # Assign vertices
    for v in cube.data.vertices:
        if v.co.z > 0:
            vg1.add([v.index], 1.0, 'REPLACE')
        else:
            vg2.add([v.index], 1.0, 'REPLACE')

    add_default_camera_light()
    save_blend("weight_paint_ready.blend")


# ============================================================
# 19. camera_views.blend
#     Scene with multiple cameras at different angles
# ============================================================
def generate_camera_views():
    print("Generating camera_views.blend...")
    reset_scene()

    # Subject
    bpy.ops.mesh.primitive_monkey_add(size=2, location=(0, 0, 0))
    bpy.context.active_object.name = "Suzanne"

    # Ground
    bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, -1))
    bpy.context.active_object.name = "Ground"

    # Camera 1 - Front
    bpy.ops.object.camera_add(location=(0, -7, 2))
    cam1 = bpy.context.active_object
    cam1.name = "Camera.Front"
    cam1.rotation_euler = (math.radians(80), 0, 0)

    # Camera 2 - Top
    bpy.ops.object.camera_add(location=(0, 0, 8))
    cam2 = bpy.context.active_object
    cam2.name = "Camera.Top"
    cam2.rotation_euler = (0, 0, 0)

    # Camera 3 - Side
    bpy.ops.object.camera_add(location=(7, 0, 2))
    cam3 = bpy.context.active_object
    cam3.name = "Camera.Side"
    cam3.rotation_euler = (math.radians(80), 0, math.radians(90))

    # Camera 4 - Perspective (active)
    bpy.ops.object.camera_add(location=(5, -5, 4))
    cam4 = bpy.context.active_object
    cam4.name = "Camera.Perspective"
    cam4.rotation_euler = (math.radians(63.6), 0, math.radians(46.7))
    bpy.context.scene.camera = cam4

    # Light
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    bpy.context.active_object.name = "Sun"
    bpy.context.active_object.data.energy = 5

    save_blend("camera_views.blend")


# ============================================================
# 20. kitchen_table.blend
#     Simple table scene for composition/arrangement tasks
# ============================================================
def generate_kitchen_table():
    print("Generating kitchen_table.blend...")
    reset_scene()

    # Table top
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 1))
    top = bpy.context.active_object
    top.name = "TableTop"
    top.scale = (2.5, 1.5, 0.05)

    # Table legs
    positions = [(2, 1.2, 0.5), (-2, 1.2, 0.5), (2, -1.2, 0.5), (-2, -1.2, 0.5)]
    for i, pos in enumerate(positions):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.06, depth=1, location=pos)
        leg = bpy.context.active_object
        leg.name = f"TableLeg.{i+1}"

    # Plate (flattened sphere)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=(0.5, 0, 1.1))
    plate = bpy.context.active_object
    plate.name = "Plate"
    plate.scale = (1, 1, 0.15)

    # Cup (cylinder)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.25, location=(-0.5, 0.3, 1.17))
    cup = bpy.context.active_object
    cup.name = "Cup"

    # Floor
    bpy.ops.mesh.primitive_plane_add(size=15, location=(0, 0, 0))
    bpy.context.active_object.name = "Floor"

    add_default_camera_light()
    bpy.context.scene.camera.location = (4, -4, 3)
    save_blend("kitchen_table.blend")


# ============================================================
# 21. smooth_objects.blend
#     Objects with flat shading for smooth shading tasks
# ============================================================
def generate_smooth_objects():
    print("Generating smooth_objects.blend...")
    reset_scene()

    # Sphere (flat shading by default)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(-2, 0, 1))
    bpy.context.active_object.name = "Sphere"

    # Cylinder
    bpy.ops.mesh.primitive_cylinder_add(radius=0.6, depth=2, location=(2, 0, 1))
    bpy.context.active_object.name = "Cylinder"

    # Torus
    bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.3, location=(0, 3, 1))
    bpy.context.active_object.name = "Torus"

    # Ground
    bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
    bpy.context.active_object.name = "Ground"

    add_default_camera_light()
    save_blend("smooth_objects.blend")


# ============================================================
# 22. compositing_scene.blend
#     Scene with compositing nodes setup
# ============================================================
def generate_compositing():
    print("Generating compositing_scene.blend...")
    reset_scene()

    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
    cube = bpy.context.active_object
    cube.name = "Cube"

    mat = bpy.data.materials.new(name="Red")
    mat.use_nodes = True
    p = mat.node_tree.nodes.get("Principled BSDF")
    p.inputs['Base Color'].default_value = (0.8, 0.1, 0.1, 1)
    cube.data.materials.append(mat)

    bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
    bpy.context.active_object.name = "Ground"

    add_default_camera_light()

    # Enable compositing
    bpy.context.scene.use_nodes = True

    save_blend("compositing_scene.blend")


# ============================================================
# 23. physics_ready.blend
#     Objects set up for physics simulation tasks
# ============================================================
def generate_physics_ready():
    print("Generating physics_ready.blend...")
    reset_scene()

    # Ground plane (collision)
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = "Ground"

    # Falling cube
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 5))
    cube = bpy.context.active_object
    cube.name = "FallingCube"

    # Sphere on slope
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(3, 0, 3))
    sphere = bpy.context.active_object
    sphere.name = "RollingSphere"

    # Stack of cubes
    for i in range(3):
        bpy.ops.mesh.primitive_cube_add(size=0.8, location=(- 3, 0, 0.4 + i * 0.85))
        bpy.context.active_object.name = f"StackCube.{i+1}"

    bpy.context.scene.frame_end = 120

    add_default_camera_light()
    save_blend("physics_ready.blend")


# ============================================================
# 24. text_3d_scene.blend
#     Multiple text objects with different content
# ============================================================
def generate_text_3d():
    print("Generating text_3d_scene.blend...")
    reset_scene()

    # Title text
    bpy.ops.object.text_add(location=(0, 0, 2))
    title = bpy.context.active_object
    title.name = "Title"
    title.data.body = "Title"
    title.data.size = 1.5
    title.data.align_x = 'CENTER'

    # Subtitle
    bpy.ops.object.text_add(location=(0, 0, 0.5))
    sub = bpy.context.active_object
    sub.name = "Subtitle"
    sub.data.body = "Subtitle"
    sub.data.size = 0.8
    sub.data.align_x = 'CENTER'

    # Extruded text
    bpy.ops.object.text_add(location=(0, -3, 0))
    ext = bpy.context.active_object
    ext.name = "ExtrudedText"
    ext.data.body = "3D"
    ext.data.size = 2.0
    ext.data.extrude = 0.3
    ext.data.align_x = 'CENTER'

    add_default_camera_light()
    save_blend("text_3d_scene.blend")


# ============================================================
# 25. donut_base.blend
#     Classic Blender donut tutorial starting point
# ============================================================
def generate_donut():
    print("Generating donut_base.blend...")
    reset_scene()

    # Donut (torus)
    bpy.ops.mesh.primitive_torus_add(
        major_radius=1.0,
        minor_radius=0.4,
        major_segments=48,
        minor_segments=16,
        location=(0, 0, 0)
    )
    donut = bpy.context.active_object
    donut.name = "Donut"

    # Donut material
    mat = bpy.data.materials.new(name="DonutMat")
    mat.use_nodes = True
    p = mat.node_tree.nodes.get("Principled BSDF")
    p.inputs['Base Color'].default_value = (0.76, 0.52, 0.28, 1)
    p.inputs['Roughness'].default_value = 0.7
    donut.data.materials.append(mat)

    # Plate
    bpy.ops.mesh.primitive_cylinder_add(radius=1.5, depth=0.05, location=(0, 0, -0.4))
    plate = bpy.context.active_object
    plate.name = "Plate"
    pmat = bpy.data.materials.new(name="PlateMat")
    pmat.use_nodes = True
    pp = pmat.node_tree.nodes.get("Principled BSDF")
    pp.inputs['Base Color'].default_value = (0.9, 0.9, 0.9, 1)
    pp.inputs['Roughness'].default_value = 0.3
    plate.data.materials.append(pmat)

    # Table
    bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, -0.43))
    table = bpy.context.active_object
    table.name = "Table"

    add_default_camera_light()
    bpy.context.scene.camera.location = (3, -3, 2.5)

    save_blend("donut_base.blend")


# ============================================================
# Main
# ============================================================
if __name__ == "__main__":
    print(f"\n{'='*60}")
    print(f"Generating additional Blender assets in: {ASSET_DIR}")
    print(f"{'='*60}\n")

    generate_cube_sphere_boolean()      # 1
    generate_multi_light()              # 2
    generate_curve_scene()              # 3
    generate_armature_scene()           # 4
    generate_materials_showcase()       # 5
    generate_hierarchy_scene()          # 6
    generate_multiple_collections()     # 7
    generate_uv_cube()                  # 8
    generate_empty_scene()              # 9
    generate_sculpt_base()              # 10
    generate_modifier_stack()           # 11
    generate_animation_rotation()       # 12
    generate_constraint_ready()         # 13
    generate_particles_ready()          # 14
    generate_render_ready_cycles()      # 15
    generate_wireframe()                # 16
    generate_linked_duplicates()        # 17
    generate_weight_paint()             # 18
    generate_camera_views()             # 19
    generate_kitchen_table()            # 20
    generate_smooth_objects()           # 21
    generate_compositing()              # 22
    generate_physics_ready()            # 23
    generate_text_3d()                  # 24
    generate_donut()                    # 25

    print(f"\n{'='*60}")
    print(f"Done! Generated 25 additional .blend files")
    print(f"{'='*60}")
