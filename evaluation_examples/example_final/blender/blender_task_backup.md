# Blender Task Backup — 备用任务

本文档包含从主设计文档中移出的 25 个备用任务，可在需要扩展任务集时使用。

---

## L1 备用任务 (10 个)

---

#### Task L1-3 (备用): 添加一个平面 (Plane)

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. Add a Plane to the scene, then save the file.
- **Upload Assets**: `default_cube.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_object.py` → `/tmp/check_object.py`
- **Evaluator**: `check_blender_object_exists` (复用 L1-2)
- **Check Script**: `check_object.py`
- **result**: `vm_command_line` → `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_object.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
- **expected**: `rule` → `{"object_type": "MESH", "name_contains": "Plane"}`
- **New Evaluator Required**: ❌

---

#### Task L1-8 (备用): 添加空物体 (Empty)

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. Add an Empty object (Plain Axes type) to the scene, then save the file.
- **Upload Assets**: `default_cube.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_object.py` → `/tmp/check_object.py`
- **Evaluator**: `check_blender_object_exists` (复用 L1-2)
- **Check Script**: `check_object.py`
- **result**: `vm_command_line` → `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_object.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
- **expected**: `rule` → `{"object_type": "EMPTY", "name_contains": "Empty"}`
- **New Evaluator Required**: ❌

---

#### Task L1-12 (备用): 添加摄像机

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. Add a new Camera to the scene (Add > Camera), then save the file.
- **Upload Assets**: `default_cube.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_object.py` → `/tmp/check_object.py`
- **Evaluator**: `check_blender_object_count`
- **Check Script**: `check_object.py`
- **result**: `vm_command_line` → `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_object.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
- **expected**: `rule` → `{"object_type": "CAMERA", "min_count": 2}`
- **验证逻辑**: 检查 type_counts["CAMERA"] >= 2（默认场景已有 1 个 Camera）
- **New Evaluator Required**: ❌ (复用 check_blender_object_count)

---

#### Task L1-16 (备用): 复制物体

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. Select the "Cube" object and duplicate it (Shift+D), then save the file.
- **Upload Assets**: `default_cube.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_object.py` → `/tmp/check_object.py`
- **Evaluator**: `check_blender_object_count`
- **Check Script**: `check_object.py`
- **result**: `vm_command_line` → `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_object.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
- **expected**: `rule` → `{"object_type": "MESH", "min_count": 2}`
- **New Evaluator Required**: ❌

---

#### Task L1-19 (备用): 添加文本物体

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. Add a Text object to the scene (Add > Text), then save the file.
- **Upload Assets**: `default_cube.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_object.py` → `/tmp/check_object.py`
- **Evaluator**: `check_blender_object_exists` (复用 L1-2)
- **Check Script**: `check_object.py`
- **result**: `vm_command_line` → `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_object.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
- **expected**: `rule` → `{"object_type": "FONT", "name_contains": "Text"}`
- **New Evaluator Required**: ❌

---

#### Task L1-22 (备用): 添加聚光灯 (Spot Light)

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. Add a Spot light to the scene (Add > Light > Spot), then save the file.
- **Upload Assets**: `default_cube.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_object.py` → `/tmp/check_object.py`
- **Evaluator**: `check_blender_light_type` (复用 L1-11)
- **Check Script**: `check_object.py`
- **result**: `vm_command_line` → `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_object.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
- **expected**: `rule` → `{"light_type": "SPOT"}`
- **New Evaluator Required**: ❌

---

#### Task L1-23 (备用): 添加环形体 (Torus)

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. Add a Torus mesh to the scene (Add > Mesh > Torus), then save the file.
- **Upload Assets**: `default_cube.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_object.py` → `/tmp/check_object.py`
- **Evaluator**: `check_blender_object_exists` (复用 L1-2)
- **Check Script**: `check_object.py`
- **result**: `vm_command_line` → `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_object.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
- **expected**: `rule` → `{"object_type": "MESH", "name_contains": "Torus"}`
- **New Evaluator Required**: ❌

---

#### Task L1-24 (备用): 添加猴头 (Monkey/Suzanne)

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. Add a Monkey mesh (Suzanne) to the scene (Add > Mesh > Monkey), then save the file.
- **Upload Assets**: `default_cube.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_object.py` → `/tmp/check_object.py`
- **Evaluator**: `check_blender_object_exists` (复用 L1-2)
- **Check Script**: `check_object.py`
- **result**: `vm_command_line` → `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_object.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
- **expected**: `rule` → `{"object_type": "MESH", "name_contains": "Suzanne"}`
- **New Evaluator Required**: ❌

---

#### Task L1-26 (备用): 移动物体到场景原点

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. This scene contains a "Suzanne" object. Move it to the origin (X=0.0, Y=0.0, Z=0.0), then save the file.
- **Upload Assets**: `monkey_scene.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_object.py` → `/tmp/check_object.py`
- **Evaluator**: `check_blender_object_location` (复用 L1-4)
- **Check Script**: `check_object.py`
- **result**: `vm_command_line` → `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_object.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
- **expected**: `rule` → `{"object_name": "Suzanne", "expected_location": [0.0, 0.0, 0.0], "tolerance": 0.1}`
- **初始状态**: Suzanne 位于 (0,0,0)，Ground 位于 (0,0,-1)
- **New Evaluator Required**: ❌

---

#### Task L1-29 (备用): 添加圆柱体 (Cylinder)

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. Add a Cylinder mesh to the scene (Add > Mesh > Cylinder), then save the file.
- **Upload Assets**: `empty_scene.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_object.py` → `/tmp/check_object.py`
- **Evaluator**: `check_blender_object_exists` (复用 L1-2)
- **Check Script**: `check_object.py`
- **result**: `vm_command_line` → `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_object.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
- **expected**: `rule` → `{"object_type": "MESH", "name_contains": "Cylinder"}`
- **初始状态**: 空场景，仅有 Camera
- **New Evaluator Required**: ❌

---

## L2 备用任务 (10 个)

---

#### Task L2-8 (备用): 材质展示场景颜色调整

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. This scene has a "MetalSphere" with a Metal material and a "GlassCube" with a Glass material. Change the Metal material's Base Color to gold (R=1.0, G=0.84, B=0.0), and change the Glass material's Base Color to light blue (R=0.5, G=0.8, B=1.0). Set the Glass material's Roughness to 0.0 and IOR to 1.45, then save the file.
- **Upload Assets**: `materials_showcase.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_material.py` → `/tmp/check_material.py`
- **Evaluator**: `check_blender_multi_material`
- **Check Script**: `check_material.py`
- **result**: `vm_command_line` → `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_material.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
- **expected**: `rule` → `{"checks": [{"object_name": "MetalSphere", "expected_color": [1.0, 0.84, 0.0, 1.0]}, {"object_name": "GlassCube", "expected_color": [0.5, 0.8, 1.0, 1.0], "roughness": 0.0, "ior": 1.45}], "tolerance": 0.05}`
- **初始状态**: MetalSphere (金属银色), GlassCube (白色玻璃)
- **操作步骤数**: 4
- **New Evaluator Required**: ✅

---

#### Task L2-12 (备用): 镜像修改器 + 数组修改器组合

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. Select the "Cube" object. First add a Mirror modifier mirroring along the X axis with Clipping enabled. Then add an Array modifier on top of the Mirror, with a count of 4 and a Relative Offset X of 2.0, then save the file.
- **Upload Assets**: `default_cube.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_modifier.py` → `/tmp/check_modifier.py`
- **Evaluator**: `check_blender_modifier_stack`
- **Check Script**: `check_modifier.py`
- **result**: `vm_command_line` → `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_modifier.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
- **expected**: `rule` → `{"object_name": "Cube", "modifiers": {"MIRROR": {"use_axis": [true, false, false], "use_clip": true}, "ARRAY": {"count": 4, "relative_offset_displace_x": 2.0}}, "modifier_order": ["MIRROR", "ARRAY"]}`
- **操作步骤数**: 4
- **New Evaluator Required**: ❌ (复用 check_blender_modifier_stack)

---

#### Task L2-14 (备用): 材质透明度 + Alpha Blend 模式

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. Select the "Cube", create a new material named "GlassMat". Set the Alpha value to 0.3 in the Principled BSDF, change the Blend Mode to "Alpha Blend" in the Material Properties > Settings section, and also enable "Show Backface" (Backface Culling off), then save the file.
- **Upload Assets**: `default_cube.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_material.py` → `/tmp/check_material.py`
- **Evaluator**: `check_blender_material_transparency`
- **Check Script**: `check_material.py`
- **result**: `vm_command_line` → `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_material.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
- **expected**: `rule` → `{"object_name": "Cube", "material_name": "GlassMat", "alpha": 0.3, "blend_method": "BLEND", "tolerance": 0.05}`
- **操作步骤数**: 4
- **New Evaluator Required**: ✅

---

#### Task L2-16 (备用): Edit Mode 挤出 + 倒角

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. Select the "Cube", enter Edit Mode, select the top face and extrude it upward by 2 units. Then exit Edit Mode, and add a Bevel modifier with width 0.05 and 3 segments, then save the file.
- **Upload Assets**: `default_cube.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_mesh.py` → `/tmp/check_mesh.py`, `check_modifier.py` → `/tmp/check_modifier.py`
- **Evaluator**: 多指标 `["check_blender_mesh_extruded", "check_blender_modifier_bevel"]`, `"conj": "and"`
- **result**: 2 个 `vm_command_line`
- **expected**: 2 个 `rule`
  - `{"object_name": "Cube", "min_vertices": 12}`
  - `{"object_name": "Cube", "modifier_type": "BEVEL", "width": 0.05, "segments": 3, "tolerance": 0.01}`
- **操作步骤数**: 4
- **New Evaluator Required**: ❌ (复用)

---

#### Task L2-19 (备用): 渲染设置全配置

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. Configure the render settings: switch to Cycles engine, set render samples to 256, set resolution to 2560×1440, set the output format to OpenEXR, and set the frame rate to 30 fps, then save the file.
- **Upload Assets**: `render_ready_cycles.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_render.py` → `/tmp/check_render.py`
- **Evaluator**: `check_blender_render_full_config`
- **Check Script**: `check_render.py`
- **result**: `vm_command_line` → `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_render.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
- **expected**: `rule` → `{"engine": "CYCLES", "samples": 256, "resolution_x": 2560, "resolution_y": 1440, "output_format": "OPEN_EXR", "fps": 30}`
- **初始状态**: Cycles 引擎, 1920×1080, 64 samples, PNG, 24fps
- **操作步骤数**: 5
- **New Evaluator Required**: ❌

---

#### Task L2-23 (备用): 关联复制物体独立化

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. This scene has "Cube.Original" and 4 linked duplicates "Cube.Linked.001" through "Cube.Linked.004" that share the same mesh data. Select "Cube.Linked.001" and make it a single-user copy (Object > Relations > Make Single User > Object & Data). Then scale "Cube.Linked.001" to (2.0, 2.0, 2.0) to verify it's independent, and save the file.
- **Upload Assets**: `linked_duplicates.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_object.py` → `/tmp/check_object.py`, `check_mesh.py` → `/tmp/check_mesh.py`
- **Evaluator**: 多指标 `["check_blender_independent_mesh", "check_blender_object_scale"]`, `"conj": "and"`
- **result**: 2 个 `vm_command_line`
- **expected**: 2 个 `rule`
  - `{"object_name": "Cube.Linked.001", "unique_mesh": true}`
  - `{"object_name": "Cube.Linked.001", "expected_scale": [2.0, 2.0, 2.0], "tolerance": 0.1}`
- **初始状态**: 5 个 Cube 共享同一 mesh data
- **操作步骤数**: 3
- **New Evaluator Required**: ✅

---

#### Task L2-25 (备用): Edit Mode 分离网格 + 独立材质

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. Select the "Cube", enter Edit Mode, select the top face only, and separate it into a new object (Mesh > Separate > Selection). Then select the newly separated object, create a new material named "TopFaceMat" with Base Color set to yellow (R=1.0, G=1.0, B=0.0), and save the file.
- **Upload Assets**: `default_cube.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_object.py` → `/tmp/check_object.py`, `check_material.py` → `/tmp/check_material.py`
- **Evaluator**: 多指标 `["check_blender_object_count", "check_blender_separated_material"]`, `"conj": "and"`
- **result**: 2 个 `vm_command_line`
- **expected**: 2 个 `rule`
  - `{"min_mesh_count": 2}`
  - `{"material_name": "TopFaceMat", "expected_color": [1.0, 1.0, 0.0, 1.0], "tolerance": 0.05}`
- **操作步骤数**: 5
- **New Evaluator Required**: ✅

---

#### Task L2-27 (备用): 场景灯光替换

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. Delete the existing "Light" point light. Add a new Sun light, rename it to "MainSun", set its energy to 3.0 and color to warm tone (R=1.0, G=0.95, B=0.9). Position it at (0, 0, 10), then save the file.
- **Upload Assets**: `default_cube.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_object.py` → `/tmp/check_object.py`
- **Evaluator**: `check_blender_light_replacement`
- **Check Script**: `check_object.py`
- **result**: `vm_command_line` → `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_object.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
- **expected**: `rule` → `{"deleted_light": "Light", "new_light": {"name": "MainSun", "type": "SUN", "energy": 3.0, "color": [1.0, 0.95, 0.9], "location_z": 10.0}, "tolerance": 0.5}`
- **操作步骤数**: 5
- **New Evaluator Required**: ✅

---

#### Task L2-28 (备用): 摄像机参数配置

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. Select the "Camera.Perspective" camera. Change its focal length to 85mm, set the Sensor Size to 36mm, enable Depth of Field, set the Focus Distance to 5.0, and set the F-Stop to 2.8, then save the file.
- **Upload Assets**: `camera_views.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_object.py` → `/tmp/check_object.py`
- **Evaluator**: `check_blender_camera_config`
- **Check Script**: `check_object.py`
- **result**: `vm_command_line` → `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_object.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
- **expected**: `rule` → `{"camera_name": "Camera.Perspective", "focal_length": 85.0, "sensor_width": 36.0, "dof_enabled": true, "focus_distance": 5.0, "fstop": 2.8, "tolerance": 0.5}`
- **初始状态**: Camera.Perspective 为活动摄像机，默认 50mm 镜头
- **操作步骤数**: 5
- **New Evaluator Required**: ✅

---

#### Task L2-30 (备用): 纹理贴图 + PBR 完整设置

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. Select the "Cube" which has material "CubeMaterial". In the Shader Editor, set up a complete PBR material: (1) Load `/home/user/Documents/texture_metal.jpg` as the Base Color texture. (2) Load `/home/user/Documents/roughness_metal.jpg` and connect it to the Roughness input. (3) Set Metallic to 1.0. Then save the file.
- **Upload Assets**: `uv_unwrapped_cube.blend` → `/home/user/Documents/scene.blend`, `texture_metal.jpg` → `/home/user/Documents/texture_metal.jpg`, `roughness_metal.jpg` → `/home/user/Documents/roughness_metal.jpg`
- **Upload Check Script**: `check_material.py` → `/tmp/check_material.py`
- **Evaluator**: `check_blender_pbr_setup`
- **Check Script**: `check_material.py`
- **result**: `vm_command_line` → `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_material.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
- **expected**: `rule` → `{"object_name": "Cube", "textures": [{"filename": "texture_metal.jpg", "connected_to": "Base Color"}, {"filename": "roughness_metal.jpg", "connected_to": "Roughness"}], "metallic": 1.0, "tolerance": 0.05}`
- **初始状态**: Cube 已 UV 展开，含空材质 CubeMaterial
- **操作步骤数**: 5
- **New Evaluator Required**: ✅

---

## L3 备用任务 (5 个)

---

#### Task L3-4 (备用): 摄像机动画 + Track To 约束 + 渲染

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. Do the following: (1) Add a "Track To" constraint on the "Camera" targeting the "Cube", with Track axis "-Z" and Up axis "Y". (2) Set the scene frame range to 1-120. (3) Select the Camera, move it to position (7, -7, 5) and insert a Location keyframe at frame 1. (4) Move the Camera to (-7, 7, 5) and insert a Location keyframe at frame 120. (5) Set the output format to PNG. (6) Render frame 60 and save to `/home/user/Documents/frame60.png`. Then save the project file.
- **Upload Assets**: `default_cube.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_constraints.py`, `check_animation.py`, `check_render.py` → `/tmp/`
- **Evaluator**: 多指标 `["check_blender_constraint_track_to", "check_blender_camera_animation", "check_blender_render_output"]`, `"conj": "and"`
- **result**: 3 个 getter (2 个 `vm_command_line` + 1 个 `vm_file`)
- **expected**: 3 个 `rule`
  - `{"object_name": "Camera", "type": "TRACK_TO", "target": "Cube"}`
  - `{"object_name": "Camera", "min_keyframe_count": 2, "has_location_keys": true}`
  - `{"min_width": 100, "format": "PNG"}`
- **操作步骤数**: 8+
- **New Evaluator Required**: ❌

---

#### Task L3-6 (备用): 粒子草地 + HDRI 环境 + 渲染

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. This scene has a "Ground" plane. Do the following: (1) Select "Ground" and add a Hair particle system with count 5000, hair length 0.5. (2) Create a material for "Ground" with Base Color green (R=0.1, G=0.5, B=0.05). (3) Load the HDRI environment `/home/user/Documents/hdri_outdoor.exr` in World Properties. (4) Switch to Cycles engine with 64 samples. (5) Set resolution to 1920×1080. (6) Render the scene to `/home/user/Documents/grass_render.png`. Then save the project file.
- **Upload Assets**: `monkey_scene.blend` → `/home/user/Documents/scene.blend`, `hdri_outdoor.exr` → `/home/user/Documents/hdri_outdoor.exr`
- **Upload Check Script**: `check_particles.py`, `check_material.py`, `check_world.py`, `check_render.py` → `/tmp/`
- **Evaluator**: 多指标 4 项, `"conj": "and"`
- **result**: 4 个 getter (3 个 `vm_command_line` + 1 个 `vm_file`)
- **expected**: 4 个 `rule`
  - `{"object_name": "Ground", "particle_type": "HAIR", "min_count": 5000}`
  - `{"object_name": "Ground", "expected_color": [0.1, 0.5, 0.05, 1.0], "tolerance": 0.1}`
  - `{"hdri_filename": "hdri_outdoor.exr"}`
  - `{"width": 1920, "height": 1080, "format": "PNG"}`
- **操作步骤数**: 9+
- **New Evaluator Required**: ❌

---

#### Task L3-9 (备用): 甜甜圈材质 + 修改器 + 环境完整流程

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. This is a donut scene. Do the following: (1) Select the "Donut" and add a Subdivision Surface modifier with viewport level 2. (2) Set the "Donut" to Smooth Shading. (3) Change the DonutMat Base Color to warm brown (R=0.6, G=0.3, B=0.1). (4) Select the "Plate", change PlateMat Base Color to cream (R=0.95, G=0.93, B=0.88) with Roughness 0.05. (5) Load HDRI `/home/user/Documents/hdri_interior.exr` as the world environment. (6) Switch to Cycles engine with 128 samples. (7) Set the active camera to "Camera" and render at 1920×1080 to `/home/user/Documents/donut_render.png`. Then save the project file.
- **Upload Assets**: `donut_base.blend` → `/home/user/Documents/scene.blend`, `hdri_interior.exr` → `/home/user/Documents/hdri_interior.exr`
- **Upload Check Script**: `check_modifier.py`, `check_mesh.py`, `check_material.py`, `check_world.py`, `check_render.py` → `/tmp/`
- **Evaluator**: 多指标 5 项, `"conj": "and"`
- **result**: 5 个 getter (4 个 `vm_command_line` + 1 个 `vm_file`)
- **expected**: 5 个 `rule`
  - `{"object_name": "Donut", "modifier_type": "SUBSURF", "levels": 2}`
  - `{"object_name": "Donut", "has_smooth": true}`
  - `{"checks": [{"object_name": "Donut", "expected_color": [0.6, 0.3, 0.1, 1.0]}, {"object_name": "Plate", "expected_color": [0.95, 0.93, 0.88, 1.0], "roughness": 0.05}], "tolerance": 0.05}`
  - `{"hdri_filename": "hdri_interior.exr"}`
  - `{"width": 1920, "height": 1080, "format": "PNG"}`
- **操作步骤数**: 10+
- **New Evaluator Required**: ❌

---

#### Task L3-13 (备用): 多物体动画场景

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. This scene has Cube, Sphere, Cylinder, and Plane. Create a coordinated animation: (1) Set the scene frame range to 1-120 and fps to 24. (2) Select "Cube", insert Location keyframes: frame 1 at (-5, 0, 0), frame 60 at (0, 0, 3), frame 120 at (5, 0, 0). (3) Select "Sphere", insert Scale keyframes: frame 1 at (1, 1, 1), frame 60 at (2, 2, 2), frame 120 at (1, 1, 1). (4) Select "Cylinder", insert Rotation keyframes: frame 1 at 0°, frame 120 at 360° around the Z axis. (5) Create a material for "Cube" with red color, and a material for "Sphere" with green color. Then save the file.
- **Upload Assets**: `simple_scene.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_animation.py`, `check_material.py`, `check_render.py` → `/tmp/`
- **Evaluator**: 多指标 3 项, `"conj": "and"`
- **result**: 3 个 `vm_command_line`
- **expected**: 3 个 `rule`
  - `{"animated_objects": ["Cube", "Sphere", "Cylinder"], "min_keyframes_per_object": 2}`
  - `{"checks": [{"object_name": "Cube", "expected_color": [1.0, 0.0, 0.0, 1.0]}, {"object_name": "Sphere", "expected_color": [0.0, 1.0, 0.0, 1.0]}], "tolerance": 0.1}`
  - `{"frame_start": 1, "frame_end": 120, "fps": 24}`
- **操作步骤数**: 12+
- **New Evaluator Required**: ✅ (check_blender_multi_object_animation)

---

#### Task L3-14 (备用): 约束驱动太阳系动画

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. Build a simple orbital animation: (1) Parent "Planet1", "Planet2", "Planet3" all to "Sun". (2) Add a "Copy Rotation" constraint on "Moon" targeting "Planet2" (so Moon inherits Planet2's rotation). (3) Set scene frame range to 1-240. (4) Select "Planet1", insert Rotation Z keyframes: frame 1 at 0°, frame 240 at 360°. (5) Select "Planet2", insert Rotation Z keyframes: frame 1 at 0°, frame 240 at 720° (faster orbit). (6) Create materials: "Sun" → yellow (R=1.0, G=0.9, B=0.0) with Emission strength 5.0, "Planet1" → blue, "Planet2" → red. Then save the file.
- **Upload Assets**: `hierarchy_scene.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_object.py`, `check_animation.py`, `check_constraints.py`, `check_material.py` → `/tmp/`
- **Evaluator**: 多指标 4 项, `"conj": "and"`
- **result**: 4 个 `vm_command_line`
- **expected**: 4 个 `rule`
  - `{"parent_map": {"Planet1": "Sun", "Planet2": "Sun", "Planet3": "Sun"}}`
  - `{"constraints": [{"object_name": "Moon", "type": "COPY_ROTATION", "target": "Planet2"}]}`
  - `{"animated_objects": ["Planet1", "Planet2"], "min_keyframes_per_object": 2}`
  - `{"checks": [{"object_name": "Sun", "expected_color": [1.0, 0.9, 0.0, 1.0]}, {"object_name": "Planet1", "expected_color": [0.0, 0.0, 1.0, 1.0]}, {"object_name": "Planet2", "expected_color": [1.0, 0.0, 0.0, 1.0]}], "tolerance": 0.1}`
- **操作步骤数**: 12+
- **New Evaluator Required**: ❌
