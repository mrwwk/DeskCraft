# Blender Task Design Document

## 0. Blender 验证策略

### Blender 路径

评测虚拟机中 Blender 通过 snap 安装，**二进制路径为 `/snap/bin/blender`**。所有 task JSON 中的 `launch` 命令和 `vm_command_line` 评估命令都必须使用此完整路径。

### 核心思路

Blender 的 `.blend` 文件是二进制格式，无法像 Kdenlive (MLT XML) 那样直接用 XML 解析。但 Blender 提供了强大的 Python API (`bpy`)，可以通过以下方式进行验证：

```bash
/snap/bin/blender --background /path/to/file.blend --python /path/to/check_script.py
```

**评估器架构**：每个评估函数通过 `vm_command_line` getter 在 VM 上运行 Blender Python 脚本，将检查结果以 JSON 格式输出到 stdout，然后在评估函数中解析 JSON 进行判定。

**替代方案**：对于渲染输出（PNG/EXR/MP4），可直接用 `vm_file` getter 下载后用 PIL/ffprobe 验证。

### 评估器通用模式

```python
def check_blender_xxx(command_output, rule) -> float:
    """
    Args:
        command_output: JSON string from blender --background --python check_script.py
        rule: dict with expected values
    Returns:
        1.0 or 0.0
    """
    import json
    try:
        result = json.loads(command_output.strip())
        # ... validation logic
        return 1.0
    except:
        return 0.0
```

### VM 命令模式

```bash
/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_script.py 2>/dev/null | grep '^RESULT:' | sed 's/^RESULT://'
```

检查脚本通过 `config` 中的 `upload_file` 上传到 VM，输出格式统一为 `RESULT:{"key": "value"}`。

---

## 1. Available Resources

All resource files are located at: `assets/blender/`

Total: **89 files, ~41 MB**

### 1.1 Scene Files (.blend) — 35 files

Generated via `blender --background --python generate_blend_assets.py` and `generate_more_assets.py`.

#### 1.1.1 Basic Scenes

| Filename | Size | Objects | Description |
|----------|------|---------|-------------|
| `default_cube.blend` | 86 KB | Cube, Camera, Light | Blender 默认场景，大部分 L1 任务起点 |
| `empty_scene.blend` | 85 KB | Camera | 空场景，仅含摄像机 |
| `simple_scene.blend` | 106 KB | Cube, Sphere, Cylinder, Plane, Empty, Camera, Light | 多物体基础场景 |
| `two_cubes.blend` | 86 KB | Cube, Cube.001, Camera, Light | 两个重叠立方体，用于布尔运算 |
| `monkey_scene.blend` | 105 KB | Suzanne, Ground, Camera, Sun | 猴头(Suzanne) + 地面 |

#### 1.1.2 Material & Texture Scenes

| Filename | Size | Objects | Materials | Description |
|----------|------|---------|-----------|-------------|
| `textured_cube.blend` | 88 KB | Cube, Camera, Light | CubeMaterial | 带空材质的 Cube，用于纹理贴图任务 |
| `uv_unwrapped_cube.blend` | 88 KB | Cube, Camera, Light | CubeMaterial | 已 UV 展开的 Cube，用于纹理映射验证 |
| `multi_material.blend` | 90 KB | Cube, Camera, Light | Red, Blue, Green | 含三个材质的 Cube |
| `materials_showcase.blend` | 127 KB | MetalSphere, GlassCube, CeramicCylinder, EmissiveTorus, PlainCone, Ground | Metal, Glass, Ceramic, Emissive | 金属/玻璃/陶瓷/发光材质展示 |

#### 1.1.3 Modifier Scenes

| Filename | Size | Objects | Modifiers | Description |
|----------|------|---------|-----------|-------------|
| `cube_with_subsurf.blend` | 86 KB | Cube, Camera, Sun | SUBSURF (lv2) | 细分曲面修改器 |
| `modifier_stack.blend` | 86 KB | Cube, Camera, Light | ARRAY + BEVEL + SUBSURF | 多修改器堆叠 |
| `cube_sphere_boolean.blend` | 103 KB | Cube, Sphere, Camera, Light | (无，待添加) | Cube+Sphere 重叠，用于布尔运算任务 |

#### 1.1.4 Animation Scenes

| Filename | Size | Objects | Animation | Description |
|----------|------|---------|-----------|-------------|
| `animated_ball.blend` | 103 KB | Ball, Camera, Sun | Location 1→60帧 | 球体位移动画 (0,0,0)→(5,0,3) |
| `animation_rotation.blend` | 87 KB | Cube, Camera, Light | Rotation 1→120帧 | 立方体 Z 轴 360° 旋转动画 |

#### 1.1.5 Lighting Scenes

| Filename | Size | Objects | Description |
|----------|------|---------|-------------|
| `multi_light_scene.blend` | 105 KB | PointLight, SunLight, SpotLight, AreaLight, Sphere, Ground, Camera | 四种灯光类型展示 |

#### 1.1.6 Camera Scenes

| Filename | Size | Objects | Description |
|----------|------|---------|-------------|
| `camera_views.blend` | 106 KB | Camera.Front, Camera.Top, Camera.Side, Camera.Perspective, Suzanne, Ground, Sun | 多角度摄像机（活动: Perspective） |

#### 1.1.7 Collection & Hierarchy Scenes

| Filename | Size | Objects | Collections | Description |
|----------|------|---------|-------------|-------------|
| `simple_scene_with_collection.blend` | 104 KB | Cube, Sphere, Camera, Light | Props (空) | 含空 "Props" 集合 |
| `multiple_collections.blend` | 106 KB | Cube, Sphere, Cylinder, Camera, Light | Geometry, Lights, Cameras | 多集合组织场景 |
| `hierarchy_scene.blend` | 144 KB | Sun, Planet1, Planet2, Moon, Planet3, Camera, Light | (无) | 太阳系层级（Moon→Planet2 父子关系） |

#### 1.1.8 Constraint Scenes

| Filename | Size | Objects | Description |
|----------|------|---------|-------------|
| `constraint_ready.blend` | 104 KB | Target, Orbiter, LookAtTarget (Empty), Camera, Light | 约束任务起点：含目标物体和空物体 |

#### 1.1.9 Particle Scenes

| Filename | Size | Objects | Description |
|----------|------|---------|-------------|
| `particles_ready.blend` | 87 KB | Emitter (Plane+粒子系统), Ground, Camera, Light | 已配置 Emitter 粒子系统 (count=500) |

#### 1.1.10 Curve & Armature Scenes

| Filename | Size | Objects | Description |
|----------|------|---------|-------------|
| `curve_scene.blend` | 87 KB | BezierCurve, NurbsCircle, CirclePath, Follower, Camera, Light | 曲线路径 + 跟随物体 |
| `armature_scene.blend` | 88 KB | Armature (3 bones), Body (Cylinder), Camera, Light | 简单骨骼绑定 |

#### 1.1.11 Mesh & Sculpt Scenes

| Filename | Size | Objects | Description |
|----------|------|---------|-------------|
| `sculpt_base.blend` | 152 KB | SculptSphere (64×32 segments), Camera, Light | 高面数球体，用于雕刻任务 |
| `weight_paint_ready.blend` | 89 KB | Cube (细分+顶点组 Top/Bottom), Camera, Light | 已细分的 Cube，含顶点组 |
| `smooth_objects.blend` | 122 KB | Sphere, Cylinder, Torus, Ground, Camera, Light | 多物体平面着色，用于平滑着色任务 |
| `wireframe_display.blend` | 116 KB | Torus, IcoSphere, Cone, Grid, Camera, Light | 多种几何体展示 |
| `linked_duplicates.blend` | 86 KB | Cube.Original + 4× Cube.Linked, Camera, Light | 关联复制物体（共享网格数据） |

#### 1.1.12 Render & Compositing Scenes

| Filename | Size | Objects | Description |
|----------|------|---------|-------------|
| `render_ready_cycles.blend` | 89 KB | Cube (CubeMat), Ground (GroundMat), Camera, Sun | 预配置 Cycles 引擎 (1920×1080, 64 samples) |
| `compositing_scene.blend` | 88 KB | Cube (Red mat), Ground, Camera, Light | 合成节点已启用 |

#### 1.1.13 Complex Scenes

| Filename | Size | Objects | Description |
|----------|------|---------|-------------|
| `kitchen_table.blend` | 108 KB | TableTop, TableLeg.1-4, Plate, Cup, Floor, Camera, Light | 厨房桌面场景，用于场景搭建/布局任务 |
| `donut_base.blend` | 112 KB | Donut (DonutMat), Plate (PlateMat), Table, Camera, Light | 甜甜圈经典场景 |
| `physics_ready.blend` | 105 KB | FallingCube, RollingSphere, StackCube.1-3, Ground, Camera, Light | 物理模拟场景 (120帧) |

#### 1.1.14 Text Scenes

| Filename | Size | Objects | Description |
|----------|------|---------|-------------|
| `text_scene.blend` | 86 KB | Text (body="Text"), Camera, Sun | 基础文本物体 |
| `text_3d_scene.blend` | 86 KB | Title (size=1.5), Subtitle (size=0.8), ExtrudedText (extrude=0.3) | 多文本物体 + 3D 挤出 |

---

### 1.2 Diffuse Textures — 15 files

All 1024×1024 resolution. Downloaded from [Poly Haven](https://polyhaven.com/) (CC0 license) or generated with Python.

| Filename | Size | Source | Description |
|----------|------|--------|-------------|
| `texture_wood.jpg` | 965 KB | Poly Haven `wood_table` | 木质纹理 |
| `texture_metal.jpg` | 677 KB | Poly Haven `metal_plate` | 金属纹理 |
| `texture_brick.jpg` | 679 KB | Poly Haven `red_brick_03` | 红砖墙纹理 |
| `texture_concrete.jpg` | 520 KB | Poly Haven `concrete_wall_004` | 混凝土纹理 |
| `texture_fabric.jpg` | 771 KB | Poly Haven `fabric_pattern_07` | 布料纹理 |
| `texture_marble.jpg` | 305 KB | Poly Haven `marble_01` | 大理石纹理 |
| `texture_leather.jpg` | 728 KB | Poly Haven `leather_white` | 皮革纹理 |
| `texture_rock.jpg` | 733 KB | Poly Haven `rock_face` | 岩石纹理 |
| `texture_grass.jpg` | 667 KB | Poly Haven `aerial_grass_rock` | 草地纹理 |
| `texture_sand.jpg` | 839 KB | Poly Haven `coast_sand_rocks_02` | 沙滩纹理 |
| `texture_tiles.jpg` | 776 KB | Poly Haven `concrete_floor_02` | 地砖纹理 |
| `texture_checker.png` | 6 KB | Python 生成 | 棋盘格纹理（64px 格子，UV 验证用） |
| `texture_color_grid.png` | 8 KB | Python 生成 | 4×4 彩色编号格子（UV 方向验证用） |
| `texture_gradient.png` | 3 KB | Python 生成 | 水平黑→白渐变 |
| `texture_noise.png` | 3.1 MB | Python 生成 | 随机噪波纹理 |

---

### 1.3 Normal Maps — 5 files

All 1024×1024 resolution.

| Filename | Size | Source | Description |
|----------|------|--------|-------------|
| `normal_wood.jpg` | 611 KB | Poly Haven `wood_table` nor_gl | 木质法线贴图 |
| `normal_brick.jpg` | 934 KB | Poly Haven `red_brick_03` nor_gl | 砖墙法线贴图 |
| `normal_metal.jpg` | 753 KB | Poly Haven `metal_plate` nor_gl | 金属法线贴图 |
| `normal_concrete.jpg` | 971 KB | Poly Haven `concrete_wall_004` nor_gl | 混凝土法线贴图 |
| `normal_map.png` | 1.3 MB | Python 生成 | 通用法线贴图（微扰动） |

---

### 1.4 Roughness Maps — 3 files

All 1024×1024 resolution.

| Filename | Size | Source | Description |
|----------|------|--------|-------------|
| `roughness_wood.jpg` | 605 KB | Poly Haven `wood_table` rough | 木质粗糙度贴图 |
| `roughness_metal.jpg` | 758 KB | Poly Haven `metal_plate` rough | 金属粗糙度贴图 |
| `roughness_concrete.jpg` | 228 KB | Poly Haven `concrete_wall_004` rough | 混凝土粗糙度贴图 |

---

### 1.5 HDRI Environments — 6 files

EXR format, 1K resolution.

| Filename | Size | Source | Description |
|----------|------|--------|-------------|
| `hdri_studio.exr` | 1.3 MB | Poly Haven `studio_small_09` | 摄影棚灯光环境 |
| `hdri_outdoor.exr` | 5.2 MB | Poly Haven `kloppenheim_06_puresky` | 晴天户外环境 |
| `hdri_sunset.exr` | 5.3 MB | Poly Haven `kloofendal_48d_partly_cloudy_puresky` | 日落环境 |
| `hdri_forest.exr` | 5.1 MB | Poly Haven `syferfontein_0d_clear_puresky` | 森林/田野环境 |
| `hdri_night.exr` | 1.5 MB | Poly Haven `moonless_golf` | 夜间环境 |
| `hdri_interior.exr` | 1.8 MB | Poly Haven `abandoned_workshop_02` | 室内车间环境 |

---

### 1.6 Displacement & AO Maps — 3 files

All 1024×1024 resolution.

| Filename | Size | Source | Description |
|----------|------|--------|-------------|
| `displacement_brick.jpg` | 187 KB | Poly Haven `red_brick_03` disp | 砖墙置换贴图 |
| `displacement_rock.jpg` | 88 KB | Poly Haven `rock_06` disp | 岩石置换贴图 |
| `ao_wood.jpg` | 624 KB | Poly Haven `wood_table` ao | 木质环境光遮蔽贴图 |

---

### 1.7 Solid Color Images — 5 files

512×512 PNG, for material color testing.

| Filename | Size | Color |
|----------|------|-------|
| `solid_red.png` | 1.9 KB | #FF0000 |
| `solid_green.png` | 1.9 KB | #00FF00 |
| `solid_blue.png` | 1.9 KB | #0000FF |
| `solid_white.png` | 1.9 KB | #FFFFFF |
| `solid_black.png` | 842 B | #000000 |

---

### 1.8 Masks, Overlays & Height Maps — 4 files

| Filename | Resolution | Size | Description |
|----------|-----------|------|-------------|
| `alpha_mask.png` | 512×512 | 3.7 KB | 白色圆形遮罩（RGBA，圆外透明） |
| `mask_star.png` | 1024×1024 | 5.8 KB | 五角星形状蒙版（灰度） |
| `overlay_logo.png` | 512×512 | 3.9 KB | 带透明通道的 LOGO 水印 |
| `heightmap_hills.png` | 1024×1024 | 95 KB | 平滑丘陵高度图（灰度，sin×cos） |

---

### 1.9 Check Scripts — 11 files

Blender Python scripts uploaded to VM `/tmp/` for evaluation. Compatible with **Blender 5.0+** (layered action API).

| Script | Output Fields | Used By Tasks |
|--------|--------------|---------------|
| `check_object.py` | objects (name, type, location, scale, rotation, visibility, parent, children, vertex_count, light_type, text_body), type_counts | L1-1~L1-20, L2-2, L2-7, L2-8, L2-14, L2-15, L2-20, L3-4, L3-5, L3-6, L3-7 |
| `check_material.py` | per-object materials (base_color, metallic, roughness, alpha, texture_filepath) | L2-1, L2-6, L2-11, L2-16, L3-3, L3-9 |
| `check_modifier.py` | per-object modifiers (type, levels, operation, count, width, segments, use_axis) | L2-2~L2-4, L2-10, L2-14, L2-20 |
| `check_render.py` | engine, resolution, fps, samples, frame_range, output_path, active_camera | L1-7, L1-8, L1-13, L1-14, L1-17, L1-18, L2-5, L2-6, L2-12, L3-1, L3-2, L3-7 |
| `check_animation.py` | per-object keyframes (frame, value), frame_range, fcurve_count, is_layered | L2-8, L3-5, L3-6 |
| `check_world.py` | has_hdri, hdri_filepath, hdri_filename, background_color, background_strength | L2-7, L3-3, L3-10 |
| `check_collection.py` | collections (name, objects, children), user_collections, object_collections | L1-13, L1-14, L3-8 |
| `check_particles.py` | per-object particles (type, count, lifetime, hair_length, render_type) | L2-13, L3-9 |
| `check_constraints.py` | per-object constraints (type, target, influence, track_axis) | L2-12, L3-6 |
| `check_mesh.py` | per-object mesh data (vertex_count, polygon_count, has_smooth, dimensions, vertex_groups) | L2-10, L2-17, L2-19 |
| `check_text.py` | per-object text (body, size, align_x, extrude) | L1-15, L1-20, L2-16, L3-9 |

---

### 1.10 Generator Scripts — 2 files

| Script | Description |
|--------|-------------|
| `generate_blend_assets.py` | Generates 10 basic .blend files (default_cube, simple_scene, etc.) |
| `generate_more_assets.py` | Generates 25 additional .blend files (materials, curves, armature, etc.) |


### 1.11 External Real-World Asset Pack — 19 files (~61 MB)

为覆盖更真实的制作流（电商主图、短视频封面、目录图、LookDev 返工、交接打包），补充了一组外部素材。
存放路径：`assets/blender/external/`；来源与许可清单见 `assets/blender/external/README.md`。

#### 1.11.1 产品模型（glTF, CC0）— 5 files

| Filename | Size | Source | 典型制作场景 |
|----------|------|--------|--------------|
| `model_avocado.glb` | 8.0 MB | Khronos glTF Sample Models | 食品电商主图、自然光广告静帧 |
| `model_waterbottle.glb` | 8.6 MB | Khronos glTF Sample Models | 包装产品多尺寸交付、透明背景抠图 |
| `model_lantern.glb` | 9.5 MB | Khronos glTF Sample Models | 灯具产品日夜双版本渲染 |
| `model_boombox.glb` | 11 MB | Khronos glTF Sample Models | 消费电子 Hero Shot、法务安全区版本 |
| `model_corset.glb` | 13 MB | Khronos glTF Sample Models | 服饰软材质 LookDev 与评审返工 |

#### 1.11.2 家具模型包（Poly Haven Blend + 贴图, CC0）— 8 files

| Asset Pack | Included Files | Source | 典型制作场景 |
|------------|----------------|--------|--------------|
| `polyhaven_armchair_01` | `ArmChair_01_1k.blend` + `diff/nor_gl/arm` 贴图 | Poly Haven `ArmChair_01` | 家居目录图、室内布光与镜头高度迭代 |
| `polyhaven_barbershop_chair_01` | `BarberShopChair_01_1k.blend` + `diff/nor_gl/arm` 贴图 | Poly Haven `BarberShopChair_01` | 复古商业空间静物渲染、材质氛围稿 |

#### 1.11.3 额外 HDRI（CC0）— 2 files

| Filename | Size | Source | 典型制作场景 |
|----------|------|--------|--------------|
| `hdri_kloppenheim_06_puresky_1k.exr` | 5.2 MB | Poly Haven `kloppenheim_06_puresky` | 户外自然光、低对比电商风格 |
| `hdri/hdri_aerodynamics_workshop_1k.exr` | 1.4 MB | Poly Haven `aerodynamics_workshop` | 工业室内光、金属细节高反差测试 |

#### 1.11.4 额外 PBR 贴图组（CC0）— 3 files

| Filename | Size | Source | 典型制作场景 |
|----------|------|--------|--------------|
| `textures/texture_coast_sand_rocks_02_diff_1k.jpg` | 820 KB | Poly Haven `coast_sand_rocks_02` | 地表/背景底色 |
| `textures/texture_coast_sand_rocks_02_nor_gl_1k.jpg` | 1.3 MB | Poly Haven `coast_sand_rocks_02` | 表面法线细节增强 |
| `textures/texture_coast_sand_rocks_02_rough_1k.jpg` | 613 KB | Poly Haven `coast_sand_rocks_02` | 粗糙度层次与高光控制 |

#### 1.11.5 新素材到任务类型映射（建议）

| 素材组 | 推荐任务类型 | 推荐验证重点 |
|--------|-------------|-------------|
| `model_avocado` + `model_waterbottle` | 电商 A/B 主图、多尺寸交付 | `check_blender_render_output` + `check_blender_render_settings` |
| `model_lantern` + 双 HDRI | 日夜风格切换返工 | `check_blender_world_hdri` + `check_blender_render_output` |
| `model_boombox` | 宣传图中途插单（安全区/水印） | 分辨率与构图导出一致性（`vm_file` + rule） |
| `model_corset` | 服饰材质 LookDev 评审回合 | `check_blender_material_property` + 渲染输出 |
| `polyhaven_armchair_01` / `polyhaven_barbershop_chair_01` | 家居目录图、镜头与灯光迭代 | 相机参数 + 材质贴图连接 + 最终出图 |
| `coast_sand_rocks_02` 贴图组 | 场景地面与背景材质搭建 | `check_blender_texture_assigned` + 材质 roughness/normal 验证 |
---

## 2. 评估函数设计

File: `desktop_env/evaluators/metrics/blender.py`

### 2.1 基于 Blender Python 脚本的检查（vm_command_line）

| Function | Description | result Type | expected Type |
|----------|-------------|-------------|---------------|
| `check_blender_object_exists` | 验证场景中存在指定名称的物体 | `vm_command_line` | `rule` → `{"object_name": "Cube.001"}` |
| `check_blender_object_count` | 验证场景中物体数量 | `vm_command_line` | `rule` → `{"min_count": 3}` |
| `check_blender_object_deleted` | 验证某物体已被删除 | `vm_command_line` | `rule` → `{"deleted_object": "Cube"}` |
| `check_blender_object_location` | 验证物体位置 (x, y, z) | `vm_command_line` | `rule` → `{"object_name": "Cube", "expected_location": [1.0, 2.0, 0.0], "tolerance": 0.1}` |
| `check_blender_object_scale` | 验证物体缩放 | `vm_command_line` | `rule` → `{"object_name": "Cube", "expected_scale": [2.0, 2.0, 2.0], "tolerance": 0.1}` |
| `check_blender_object_rotation` | 验证物体旋转（欧拉角，度） | `vm_command_line` | `rule` → `{"object_name": "Cube", "expected_rotation_deg": [0, 0, 45], "tolerance": 2}` |
| `check_blender_material_exists` | 验证物体上存在指定材质 | `vm_command_line` | `rule` → `{"object_name": "Cube", "material_name": "Red_Material"}` |
| `check_blender_material_color` | 验证材质基础颜色 (RGBA) | `vm_command_line` | `rule` → `{"object_name": "Cube", "expected_color": [1.0, 0.0, 0.0, 1.0], "tolerance": 0.05}` |
| `check_blender_modifier_exists` | 验证物体上存在指定修改器 | `vm_command_line` | `rule` → `{"object_name": "Cube", "modifier_type": "SUBSURF"}` |
| `check_blender_modifier_param` | 验证修改器参数值 | `vm_command_line` | `rule` → `{"object_name": "Cube", "modifier_type": "SUBSURF", "param": "levels", "expected_value": 3}` |
| `check_blender_render_settings` | 验证渲染引擎和分辨率设置 | `vm_command_line` | `rule` → `{"engine": "CYCLES", "resolution_x": 1920, "resolution_y": 1080}` |
| `check_blender_camera_exists` | 验证场景中存在活动摄像机 | `vm_command_line` | `rule` → `{"has_active_camera": true}` |
| `check_blender_light_type` | 验证灯光类型和参数 | `vm_command_line` | `rule` → `{"light_name": "Light", "light_type": "SUN", "energy": 5.0}` |
| `check_blender_keyframe_exists` | 验证物体上存在关键帧动画 | `vm_command_line` | `rule` → `{"object_name": "Cube", "has_animation": true}` |
| `check_blender_animation_range` | 验证动画帧范围 | `vm_command_line` | `rule` → `{"frame_start": 1, "frame_end": 120}` |
| `check_blender_vertex_count` | 验证网格顶点数（检验细分/建模操作） | `vm_command_line` | `rule` → `{"object_name": "Cube", "min_vertices": 100}` |
| `check_blender_parent_child` | 验证父子关系 | `vm_command_line` | `rule` → `{"child": "Cube", "parent": "Empty"}` |
| `check_blender_collection_exists` | 验证集合（Collection）存在 | `vm_command_line` | `rule` → `{"collection_name": "My Collection"}` |
| `check_blender_object_in_collection` | 验证物体在指定集合中 | `vm_command_line` | `rule` → `{"object_name": "Cube", "collection_name": "My Collection"}` |
| `check_blender_texture_assigned` | 验证材质节点树中存在图片纹理节点 | `vm_command_line` | `rule` → `{"object_name": "Cube", "texture_filename": "texture_wood.jpg"}` |
| `check_blender_world_hdri` | 验证世界环境使用了 HDRI | `vm_command_line` | `rule` → `{"hdri_filename": "hdri_studio.exr"}` |
| `check_blender_particle_system` | 验证粒子系统存在及类型 | `vm_command_line` | `rule` → `{"object_name": "Plane", "particle_type": "HAIR"}` |
| `check_blender_constraint_exists` | 验证物体约束存在 | `vm_command_line` | `rule` → `{"object_name": "Cube", "constraint_type": "TRACK_TO"}` |
| `check_blender_object_visibility` | 验证物体可见性 | `vm_command_line` | `rule` → `{"object_name": "Cube", "hide_viewport": true}` |
| `check_blender_object_renamed` | 验证物体已重命名 | `vm_command_line` | `rule` → `{"expected_name": "MyCustomCube", "object_exists": true}` |

### 2.2 基于渲染输出的检查（vm_file）

| Function | Description | result Type | expected Type |
|----------|-------------|-------------|---------------|
| `check_blender_render_output` | 验证渲染输出图片存在且尺寸正确 | `vm_file` (PNG/EXR) | `rule` → `{"width": 1920, "height": 1080, "format": "PNG"}` |
| `check_blender_render_video` | 验证渲染视频输出（ffprobe） | `vm_file` (MP4) | `rule` → `{"min_duration": 2.0, "codec": "h264"}` |

---

## 3. Task Definitions

> **备用任务**: 从原始 75 个任务中精选 35 个。其余 40 个备用任务见 [`blender_task_backup.md`](blender_task_backup.md)。

### 3.1 Level 1 — 基础操作 (Single-step, directly verifiable) — 15 个

L1 任务为单步原子操作，每个任务只涉及一个 GUI 动作。所有任务统一使用以下模式：

- **Launch**: `/snap/bin/blender /home/user/Documents/scene.blend`
- **Check Command**: `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/<check_script>.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
- **上传文件**: `.blend` 素材 → `/home/user/Documents/scene.blend`，检查脚本 → `/tmp/<check_script>.py`

---

#### Task L1-1: 删除默认立方体
- **Task ID**: `660df56a-e995-4dff-a7e0-762f64dba8c9`
- **JSON File**: `660df56a-e995-4dff-a7e0-762f64dba8c9.json`

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. Delete the default "Cube" object from the scene, then save the file.
- **来源**: Blender Manual（https://docs.blender.org/manual/en/latest/）Scene Layout > Object > Editing > Delete
- **Upload Assets**: `default_cube.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_object.py` → `/tmp/check_object.py`
- **Evaluator**: `check_blender_object_deleted`
- **Check Script**: `check_object.py`
- **result**: `vm_command_line` → `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_object.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
- **expected**: `rule` → `{"deleted_object": "Cube"}`
- **验证逻辑**: 解析 JSON，检查 `object_names` 中不包含 `"Cube"`
- **New Evaluator Required**: ✅

---
---

#### Task L1-2: 添加一个球体 (UV Sphere)
- **Task ID**: `029db559-ff0d-4a32-b744-7a53ab469387`
- **JSON File**: `029db559-ff0d-4a32-b744-7a53ab469387.json`

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. Add a UV Sphere to the scene, then save the file.
- **来源**: Blender Manual（https://docs.blender.org/manual/en/latest/）Modeling > Meshes > Primitives
- **Upload Assets**: `default_cube.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_object.py` → `/tmp/check_object.py`
- **Evaluator**: `check_blender_object_exists`
- **Check Script**: `check_object.py`
- **result**: `vm_command_line` → `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_object.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
- **expected**: `rule` → `{"object_type": "MESH", "name_contains": "Sphere"}`
- **验证逻辑**: 遍历 `objects`，找到 type=MESH 且 name 含 "Sphere" 的物体
- **New Evaluator Required**: ✅

---
---

#### Task L1-3: 缩放物体
- **Task ID**: `027a294b-6c5a-4724-ab1d-d82ac9528993`
- **JSON File**: `027a294b-6c5a-4724-ab1d-d82ac9528993.json`

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. Select the "Cube" object and scale it to 2x on all axes (Scale X=2.0, Y=2.0, Z=2.0), then save the file.
- **来源**: Blender Manual（https://docs.blender.org/manual/en/latest/）Scene Layout > Object > Editing > Transform > Scale
- **Upload Assets**: `default_cube.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_object.py` → `/tmp/check_object.py`
- **Evaluator**: `check_blender_object_scale`
- **Check Script**: `check_object.py`
- **result**: `vm_command_line` → `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_object.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
- **expected**: `rule` → `{"object_name": "Cube", "expected_scale": [2.0, 2.0, 2.0], "tolerance": 0.1}`
- **验证逻辑**: 找到 name="Cube" 的物体，比较 scale 各分量与 expected 的差值 ≤ tolerance
- **New Evaluator Required**: ✅

---

#### Task L1-4: 移动物体到指定位置
- **Task ID**: `faccdde0-d05d-4757-8196-34447d49497f`
- **JSON File**: `faccdde0-d05d-4757-8196-34447d49497f.json`

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. Select the "Cube" object and move it to location X=3.0, Y=0.0, Z=2.0, then save the file.
- **来源**: Blender Manual（https://docs.blender.org/manual/en/latest/）Scene Layout > Object > Editing > Transform > Move
- **Upload Assets**: `default_cube.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_object.py` → `/tmp/check_object.py`
- **Evaluator**: `check_blender_object_location`
- **Check Script**: `check_object.py`
- **result**: `vm_command_line` → `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_object.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
- **expected**: `rule` → `{"object_name": "Cube", "expected_location": [3.0, 0.0, 2.0], "tolerance": 0.1}`
- **验证逻辑**: 找到 name="Cube" 的物体，比较 location 各分量与 expected 的差值 ≤ tolerance
- **New Evaluator Required**: ✅

---

#### Task L1-5: 旋转物体 45 度
- **Task ID**: `d0d0bc23-1ac2-4bc4-9475-5af04ebe012a`
- **JSON File**: `d0d0bc23-1ac2-4bc4-9475-5af04ebe012a.json`

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. Select the "Cube" object and rotate it 45 degrees around the Z axis, then save the file.
- **来源**: Blender Manual（https://docs.blender.org/manual/en/latest/）Scene Layout > Object > Editing > Transform > Rotate
- **Upload Assets**: `default_cube.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_object.py` → `/tmp/check_object.py`
- **Evaluator**: `check_blender_object_rotation`
- **Check Script**: `check_object.py`
- **result**: `vm_command_line` → `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_object.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
- **expected**: `rule` → `{"object_name": "Cube", "expected_rotation_deg": [0, 0, 45], "tolerance": 2}`
- **验证逻辑**: 找到 name="Cube" 的物体，比较 rotation_euler_deg 各分量与 expected 的差值 ≤ tolerance
- **New Evaluator Required**: ✅

---
---

#### Task L1-6: 重命名物体
- **Task ID**: `0fbdd695-5224-4f6d-80ae-b06ee48e5c61`
- **JSON File**: `0fbdd695-5224-4f6d-80ae-b06ee48e5c61.json`

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. Rename the "Cube" object to "MyCube" in the Outliner or Properties panel, then save the file.
- **来源**: Blender Manual（https://docs.blender.org/manual/en/latest/）Scene Layout > Object > Properties（对象命名与属性管理）
- **Upload Assets**: `default_cube.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_object.py` → `/tmp/check_object.py`
- **Evaluator**: `check_blender_object_renamed`
- **Check Script**: `check_object.py`
- **result**: `vm_command_line` → `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_object.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
- **expected**: `rule` → `{"expected_name": "MyCube", "old_name": "Cube"}`
- **验证逻辑**: 检查 `object_names` 包含 "MyCube" 且不包含 "Cube"
- **New Evaluator Required**: ✅

---
---

#### Task L1-7: 设置渲染分辨率为 1280×720
- **Task ID**: `a68611d8-9bba-40d8-9243-903c3480ba25`
- **JSON File**: `a68611d8-9bba-40d8-9243-903c3480ba25.json`

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. In the Output Properties panel, set the render resolution to 1280×720, then save the file.
- **来源**: Blender Manual（https://docs.blender.org/manual/en/latest/）Render > Output Properties（Resolution）
- **Upload Assets**: `default_cube.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_render.py` → `/tmp/check_render.py`
- **Evaluator**: `check_blender_render_settings`
- **Check Script**: `check_render.py`
- **result**: `vm_command_line` → `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_render.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
- **expected**: `rule` → `{"resolution_x": 1280, "resolution_y": 720}`
- **验证逻辑**: 解析 JSON，检查 resolution_x == 1280 且 resolution_y == 720
- **New Evaluator Required**: ✅

---
---

#### Task L1-8: 切换渲染引擎为 Cycles
- **Task ID**: `7c4b5aa4-7f3f-440f-8027-3ea73f2c384b`
- **JSON File**: `7c4b5aa4-7f3f-440f-8027-3ea73f2c384b.json`

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. In the Render Properties panel, switch the render engine from Eevee to Cycles, then save the file.
- **来源**: Blender Manual（https://docs.blender.org/manual/en/latest/）Render > Cycles（Render Engine 切换）
- **Upload Assets**: `default_cube.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_render.py` → `/tmp/check_render.py`
- **Evaluator**: `check_blender_render_settings` (复用 L1-7)
- **Check Script**: `check_render.py`
- **result**: `vm_command_line` → `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_render.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
- **expected**: `rule` → `{"engine": "CYCLES"}`
- **New Evaluator Required**: ❌

---
---

#### Task L1-9: 添加太阳光 (Sun Light)
- **Task ID**: `d5622f1d-0bc7-4e5f-8bf4-51a930fd2269`
- **JSON File**: `d5622f1d-0bc7-4e5f-8bf4-51a930fd2269.json`

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. Add a Sun light to the scene (Add > Light > Sun), then save the file.
- **来源**: Blender Manual（https://docs.blender.org/manual/en/latest/）Render > Lights > Light Objects（Sun）
- **Upload Assets**: `default_cube.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_object.py` → `/tmp/check_object.py`
- **Evaluator**: `check_blender_light_type`
- **Check Script**: `check_object.py`
- **result**: `vm_command_line` → `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_object.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
- **expected**: `rule` → `{"light_type": "SUN"}`
- **验证逻辑**: 遍历 objects，找到 type=LIGHT 且 light_type="SUN" 的物体
- **New Evaluator Required**: ✅

---
---

#### Task L1-10: 创建新集合 (Collection)
- **Task ID**: `14db88ce-fb57-4afa-9470-e2510b67502d`
- **JSON File**: `14db88ce-fb57-4afa-9470-e2510b67502d.json`

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. Create a new Collection named "MyObjects" in the Outliner, then save the file.
- **来源**: Blender Manual（https://docs.blender.org/manual/en/latest/）Scene Layout > Collections > Introduction
- **Upload Assets**: `default_cube.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_collection.py` → `/tmp/check_collection.py`
- **Evaluator**: `check_blender_collection_exists`
- **Check Script**: `check_collection.py`
- **result**: `vm_command_line` → `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_collection.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
- **expected**: `rule` → `{"collection_name": "MyObjects"}`
- **验证逻辑**: 检查 user_collections 列表中包含 "MyObjects"
- **New Evaluator Required**: ✅

---
---

#### Task L1-11: 将物体移到指定集合
- **Task ID**: `ae385d6f-65af-4c40-8680-478de9c3847d`
- **JSON File**: `ae385d6f-65af-4c40-8680-478de9c3847d.json`

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. This scene has an empty collection named "Props". Move the "Cube" object into the "Props" collection, then save the file.
- **来源**: Blender Manual（https://docs.blender.org/manual/en/latest/）Scene Layout > Collections；Scene Layout > Object Relations（Move to Collection）
- **Upload Assets**: `simple_scene_with_collection.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_collection.py` → `/tmp/check_collection.py`
- **Evaluator**: `check_blender_object_in_collection`
- **Check Script**: `check_collection.py`
- **result**: `vm_command_line` → `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_collection.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
- **expected**: `rule` → `{"object_name": "Cube", "collection_name": "Props"}`
- **验证逻辑**: 检查 object_collections["Cube"] 包含 "Props"
- **初始状态**: scene 含 Cube, Sphere, Camera, Light + 空 "Props" 集合
- **New Evaluator Required**: ✅

---
---

#### Task L1-12: 隐藏物体（视口可见性）
- **Task ID**: `16787234-af24-4f13-9ee8-b34a6442c9e2`
- **JSON File**: `16787234-af24-4f13-9ee8-b34a6442c9e2.json`

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. Hide the "Sphere" object in the viewport by pressing H or clicking the eye icon in the Outliner, then save the file.
- **来源**: Blender Manual（https://docs.blender.org/manual/en/latest/）Scene Layout > Object > Editing > Show/Hide
- **Upload Assets**: `simple_scene.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_object.py` → `/tmp/check_object.py`
- **Evaluator**: `check_blender_object_visibility`
- **Check Script**: `check_object.py`
- **result**: `vm_command_line` → `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_object.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
- **expected**: `rule` → `{"object_name": "Sphere", "hide_viewport": true}`
- **验证逻辑**: 找到 name="Sphere" 的物体，检查 hide_viewport == true
- **初始状态**: scene 含 Cube, Sphere, Cylinder, Plane, Empty, Camera, Light
- **New Evaluator Required**: ✅

---
---

#### Task L1-13: 设置动画帧范围
- **Task ID**: `ed597e7a-66c8-4e29-ae72-510d2545d3e1`
- **JSON File**: `ed597e7a-66c8-4e29-ae72-510d2545d3e1.json`

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. In the Output Properties panel, set the animation frame range to start at frame 1 and end at frame 120, then save the file.
- **来源**: Blender Manual（https://docs.blender.org/manual/en/latest/）Editors > Timeline（Frame Range）
- **Upload Assets**: `default_cube.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_render.py` → `/tmp/check_render.py`
- **Evaluator**: `check_blender_animation_range`
- **Check Script**: `check_render.py`
- **result**: `vm_command_line` → `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_render.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
- **expected**: `rule` → `{"frame_start": 1, "frame_end": 120}`
- **验证逻辑**: 检查 frame_start == 1 且 frame_end == 120（默认为 250）
- **New Evaluator Required**: ✅

---
---

#### Task L1-14: 修改文本内容
- **Task ID**: `4bd9519c-41fe-486f-8fc7-45d966d46f1b`
- **JSON File**: `4bd9519c-41fe-486f-8fc7-45d966d46f1b.json`

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. This scene contains a Text object. Select it, enter Edit Mode (Tab), change the text content to "Hello Blender", then save the file.
- **来源**: Blender Manual（https://docs.blender.org/manual/en/latest/）Modeling > Texts > Editing
- **Upload Assets**: `text_scene.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_text.py` → `/tmp/check_text.py`
- **Evaluator**: `check_blender_text_content`
- **Check Script**: `check_text.py`
- **result**: `vm_command_line` → `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_text.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
- **expected**: `rule` → `{"object_name": "Text", "expected_text": "Hello Blender"}`
- **验证逻辑**: 找到 name="Text" 的物体，检查 body == "Hello Blender"
- **初始状态**: scene 含 Text (body="Text"), Camera, Sun
- **New Evaluator Required**: ✅

---
---

#### Task L1-15: 修改灯光能量值
- **Task ID**: `698d2b6a-8843-40ef-9258-d31d4fef6a0a`
- **JSON File**: `698d2b6a-8843-40ef-9258-d31d4fef6a0a.json`

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. Select the "PointLight" object and set its power (energy) to 2000 watts in the Object Data Properties panel, then save the file.
- **来源**: Blender Manual（https://docs.blender.org/manual/en/latest/）Render > Lights > Light Objects（Power/Energy）
- **Upload Assets**: `multi_light_scene.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_object.py` → `/tmp/check_object.py`
- **Evaluator**: `check_blender_light_energy`
- **Check Script**: `check_object.py`
- **result**: `vm_command_line` → `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_object.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
- **expected**: `rule` → `{"light_name": "PointLight", "expected_energy": 2000.0, "tolerance": 10}`
- **验证逻辑**: 找到 name="PointLight" 的物体，检查 energy ≈ 2000
- **初始状态**: PointLight (500W), SunLight (3), SpotLight (800W), AreaLight (300W)
- **New Evaluator Required**: ✅

---
---

### L1 任务汇总

| # | Task | Asset File | Check Script | Evaluator Function | New? |
|---|------|-----------|-------------|-------------------|------|
| 1 | 删除默认立方体 | `default_cube.blend` | `check_object.py` | `check_blender_object_deleted` | ✅ |
| 2 | 添加球体 | `default_cube.blend` | `check_object.py` | `check_blender_object_exists` | ✅ |
| 3 | 缩放物体 | `default_cube.blend` | `check_object.py` | `check_blender_object_scale` | ✅ |
| 4 | 移动物体到指定位置 | `default_cube.blend` | `check_object.py` | `check_blender_object_location` | ✅ |
| 5 | 旋转物体 45 度 | `default_cube.blend` | `check_object.py` | `check_blender_object_rotation` | ✅ |
| 6 | 重命名物体 | `default_cube.blend` | `check_object.py` | `check_blender_object_renamed` | ✅ |
| 7 | 设置渲染分辨率 | `default_cube.blend` | `check_render.py` | `check_blender_render_settings` | ✅ |
| 8 | 切换渲染引擎 | `default_cube.blend` | `check_render.py` | `check_blender_render_settings` | ❌ |
| 9 | 添加太阳光 | `default_cube.blend` | `check_object.py` | `check_blender_light_type` | ✅ |
| 10 | 创建新集合 | `default_cube.blend` | `check_collection.py` | `check_blender_collection_exists` | ✅ |
| 11 | 移动物体到集合 | `simple_scene_with_collection.blend` | `check_collection.py` | `check_blender_object_in_collection` | ✅ |
| 12 | 隐藏物体 | `simple_scene.blend` | `check_object.py` | `check_blender_object_visibility` | ✅ |
| 13 | 设置动画帧范围 | `default_cube.blend` | `check_render.py` | `check_blender_animation_range` | ✅ |
| 14 | 修改文本内容 | `text_scene.blend` | `check_text.py` | `check_blender_text_content` | ✅ |
| 15 | 修改灯光能量 | `multi_light_scene.blend` | `check_object.py` | `check_blender_light_energy` | ✅ |

**L1 统计**: 15 个任务，14 个新评估函数，1 个复用

---

### 3.2 Level 2 — 中级操作 (Multi-step composite operations) — 10 个

L2 任务为多步复合操作，每个任务涉及 **2-4 个关联 GUI 操作**，需要在多个面板/编辑器之间切换。所有任务统一使用以下模式：

- **Launch**: `/snap/bin/blender /home/user/Documents/scene.blend`
- **Check Command**: `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/<check_script>.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
- **上传文件**: `.blend` 素材 → `/home/user/Documents/scene.blend`，检查脚本 → `/tmp/<check_script>.py`，纹理/HDRI → `/home/user/Documents/`

---

#### Task L2-1: 创建命名材质并设置 PBR 参数
- **Task ID**: `aa43e3af-d5ad-4366-b3e1-e61c74a5a5a9`
- **JSON File**: `aa43e3af-d5ad-4366-b3e1-e61c74a5a5a9.json`

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. Select the "Cube" object, create a new material named "RedMetal", set the Base Color to red (R=1.0, G=0.0, B=0.0), the Metallic value to 1.0, and the Roughness to 0.2, then save the file.
- **来源**: Blender Manual（https://docs.blender.org/manual/en/latest/）Rendering > Shader Nodes > Principled BSDF
- **Upload Assets**: `default_cube.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_material.py` → `/tmp/check_material.py`
- **Evaluator**: `check_blender_material_pbr`
- **Check Script**: `check_material.py`
- **result**: `vm_command_line` → `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_material.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
- **expected**: `rule` → `{"object_name": "Cube", "material_name": "RedMetal", "expected_color": [1.0, 0.0, 0.0, 1.0], "metallic": 1.0, "roughness": 0.2, "tolerance": 0.05}`
- **验证逻辑**: 解析 JSON，检查 Cube 的材质名称匹配，base_color/metallic/roughness 在容差范围内
- **操作步骤数**: 4（选物体 → 新建材质 → 改名 → 设置 3 个 PBR 参数）
- **New Evaluator Required**: ✅

---
---

#### Task L2-2: 布尔差集运算并隐藏切割体
- **Task ID**: `e258592e-acfb-4e2a-b762-12dbb0624e23`
- **JSON File**: `e258592e-acfb-4e2a-b762-12dbb0624e23.json`

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. This scene contains a "Cube" and a "Sphere" that overlap. Add a Boolean modifier to the "Cube" with the Difference operation, using "Sphere" as the boolean object. Then hide the "Sphere" in the viewport (click the eye icon in the Outliner), and save the file.
- **来源**: Blender Manual（https://docs.blender.org/manual/en/latest/）Modeling > Modifiers > Generate > Boolean；Scene Layout > Object > Show/Hide
- **Upload Assets**: `cube_sphere_boolean.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_modifier.py` → `/tmp/check_modifier.py`, `check_object.py` → `/tmp/check_object.py`
- **Evaluator**: 多指标 `["check_blender_modifier_boolean", "check_blender_object_visibility"]`, `"conj": "and"`
- **Check Scripts**: `check_modifier.py`, `check_object.py`
- **result**: 2 个 `vm_command_line`
  - `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_modifier.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
  - `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_object.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
- **expected**: 2 个 `rule`
  - `{"object_name": "Cube", "modifier_type": "BOOLEAN", "operation": "DIFFERENCE", "target_object": "Sphere"}`
  - `{"object_name": "Sphere", "hide_viewport": true}`
- **初始状态**: Cube 和 Sphere 重叠放置，Sphere 中心在 Cube 内
- **验证逻辑**: 检查 Cube 上存在 Boolean 修改器（Difference 操作，目标为 Sphere）+ Sphere 的 hide_viewport 为 True
- **操作步骤数**: 3（添加布尔修改器 → 设置差集和目标 → 隐藏 Sphere）
- **New Evaluator Required**: ✅ (check_blender_modifier_boolean + check_blender_object_visibility)

---
---

#### Task L2-3: 为物体添加木纹纹理并设置 UV 映射
- **Task ID**: `86766b15-f7a2-44f6-a5be-e4004ade98c0`
- **JSON File**: `86766b15-f7a2-44f6-a5be-e4004ade98c0.json`

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. The "Cube" object has a material "CubeMaterial" and has been UV unwrapped. Open the Shader Editor, add an Image Texture node, load the image `/home/user/Documents/texture_wood.jpg`, and connect it to the Base Color input of the Principled BSDF shader. Set the texture mapping to UV, then save the file.
- **来源**: Blender Manual（https://docs.blender.org/manual/en/latest/）Rendering > Shader Nodes > Image Texture；Modeling > Meshes > UV
- **Upload Assets**: `uv_unwrapped_cube.blend` → `/home/user/Documents/scene.blend`, `texture_wood.jpg` → `/home/user/Documents/texture_wood.jpg`
- **Upload Check Script**: `check_material.py` → `/tmp/check_material.py`
- **Evaluator**: `check_blender_texture_assigned`
- **Check Script**: `check_material.py`
- **result**: `vm_command_line` → `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_material.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
- **expected**: `rule` → `{"object_name": "Cube", "texture_filename": "texture_wood.jpg"}`
- **初始状态**: Cube 已 UV 展开，含空材质 CubeMaterial
- **验证逻辑**: 检查材质节点树中存在 Image Texture 节点，图片文件名匹配，且连接到 Base Color 输入
- **操作步骤数**: 4（打开 Shader Editor → 添加 Image Texture → 加载图片 → 连接到 Base Color）
- **New Evaluator Required**: ✅

---
---

#### Task L2-4: 修改器堆叠调参
- **Task ID**: `1d7857fe-2cff-4663-957a-390ddbdfc302`
- **JSON File**: `1d7857fe-2cff-4663-957a-390ddbdfc302.json`

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. The "Cube" has three modifiers: Array, Bevel, and Subdivision Surface. Change the Array count to 8, set the Bevel width to 0.05 with 2 segments, and set the Subdivision Surface viewport level to 3, then save the file.
- **来源**: Blender Manual（https://docs.blender.org/manual/en/latest/）Modifiers > Array / Bevel / Subdivision Surface
- **Upload Assets**: `modifier_stack.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_modifier.py` → `/tmp/check_modifier.py`
- **Evaluator**: `check_blender_modifier_stack`
- **Check Script**: `check_modifier.py`
- **result**: `vm_command_line` → `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_modifier.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
- **expected**: `rule` → `{"object_name": "Cube", "modifiers": {"ARRAY": {"count": 8}, "BEVEL": {"width": 0.05, "segments": 2}, "SUBSURF": {"levels": 3}}, "tolerance": 0.01}`
- **初始状态**: Cube 已有 Array(count=3) + Bevel(width=0.1, segments=1) + Subsurf(levels=2) 修改器
- **验证逻辑**: 解析所有修改器参数，逐一检查是否匹配预期值
- **操作步骤数**: 3（调整 Array count → 调整 Bevel 参数 → 调整 Subsurf level）
- **New Evaluator Required**: ✅

---
---

#### Task L2-5: 设置世界 HDRI 环境并切换 Cycles 引擎
- **Task ID**: `38c043ec-ee56-4104-8360-1ea450238202`
- **JSON File**: `38c043ec-ee56-4104-8360-1ea450238202.json`

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. Switch the render engine to Cycles. Then go to World Properties, set the Surface to "Environment Texture", load the HDRI file `/home/user/Documents/hdri_studio.exr` as the environment map, then save the file.
- **来源**: Blender Manual（https://docs.blender.org/manual/en/latest/）Render > Cycles；Render > World（Environment Texture/HDRI）
- **Upload Assets**: `default_cube.blend` → `/home/user/Documents/scene.blend`, `hdri_studio.exr` → `/home/user/Documents/hdri_studio.exr`
- **Upload Check Script**: `check_render.py` → `/tmp/check_render.py`, `check_world.py` → `/tmp/check_world.py`
- **Evaluator**: 多指标 `["check_blender_render_engine", "check_blender_world_hdri"]`, `"conj": "and"`
- **result**: 2 个 `vm_command_line`
  - `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_render.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
  - `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_world.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
- **expected**: 2 个 `rule`
  - `{"engine": "CYCLES"}`
  - `{"hdri_filename": "hdri_studio.exr"}`
- **验证逻辑**: 渲染引擎为 CYCLES + 世界节点包含指定 HDRI 文件
- **操作步骤数**: 3（切换引擎 → 设置世界环境 → 加载 HDRI）
- **New Evaluator Required**: ✅ (check_blender_world_hdri)

---
---

#### Task L2-6: 创建关键帧动画并设置帧范围
- **Task ID**: `61ce9db5-525d-4479-bd83-056945582647`
- **JSON File**: `61ce9db5-525d-4479-bd83-056945582647.json`

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. Select the "Cube" object, set the scene frame range to 1-120. Insert a Location keyframe at frame 1 with position (0, 0, 0), and insert another Location keyframe at frame 120 with position (10, 0, 5). Then save the file.
- **来源**: Blender Manual（https://docs.blender.org/manual/en/latest/）Animation > Keyframes；Editors > Timeline
- **Upload Assets**: `default_cube.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_animation.py` → `/tmp/check_animation.py`, `check_render.py` → `/tmp/check_render.py`
- **Evaluator**: 多指标 `["check_blender_animation_keyframes", "check_blender_frame_range"]`, `"conj": "and"`
- **result**: 2 个 `vm_command_line`
  - `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_animation.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
  - `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_render.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
- **expected**: 2 个 `rule`
  - `{"object_name": "Cube", "min_keyframe_count": 2, "has_location_keys": true}`
  - `{"frame_start": 1, "frame_end": 120}`
- **验证逻辑**: Cube 有 location 通道的关键帧（至少 2 个）+ 场景帧范围为 1-120
- **操作步骤数**: 4（设置帧范围 → 跳到第 1 帧插关键帧 → 跳到第 120 帧 → 移动物体并插关键帧）
- **New Evaluator Required**: ✅ (check_blender_animation_keyframes)

---
---

#### Task L2-7: 设置父子层级关系并组织集合
- **Task ID**: `eef91461-f7d3-478a-93f4-eb4298051d17`
- **JSON File**: `eef91461-f7d3-478a-93f4-eb4298051d17.json`

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. This scene has a "Cube", "Sphere", and "Cylinder". Set "Cube" as the parent of both "Sphere" and "Cylinder". Then move all three objects into the existing "Props" collection, and save the file.
- **来源**: Blender Manual（https://docs.blender.org/manual/en/latest/）Scene Layout > Object > Parent；Scene Layout > Collections
- **Upload Assets**: `simple_scene_with_collection.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_object.py` → `/tmp/check_object.py`, `check_collection.py` → `/tmp/check_collection.py`
- **Evaluator**: 多指标 `["check_blender_parent_child", "check_blender_collection_members"]`, `"conj": "and"`
- **result**: 2 个 `vm_command_line`
  - `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_object.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
  - `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_collection.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
- **expected**: 2 个 `rule`
  - `{"parent": "Cube", "expected_children": ["Sphere", "Cylinder"]}`
  - `{"collection_name": "Props", "expected_members": ["Cube", "Sphere", "Cylinder"]}`
- **初始状态**: 含空 Props 集合，Cube/Sphere/Cylinder 在默认 Collection 中
- **验证逻辑**: Sphere 和 Cylinder 的 parent 为 Cube + Props 集合包含三个物体
- **操作步骤数**: 3（设 Cube 为 Sphere 父级 → 设 Cube 为 Cylinder 父级 → 移动到 Props 集合）
- **New Evaluator Required**: ✅ (check_blender_parent_child, check_blender_collection_members)

---
---

#### Task L2-8: 添加 Track To 约束并设置约束参数
- **Task ID**: `812ee9e0-c2a1-41e4-bb62-cb23ccd68dbb`
- **JSON File**: `812ee9e0-c2a1-41e4-bb62-cb23ccd68dbb.json`

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. This scene has a "Target" sphere, an "Orbiter" cube, and an empty "LookAtTarget". Add a "Track To" constraint to the "Orbiter" targeting "Target", with the Track Axis set to "-Z" and Up axis to "Y". Also add a "Track To" constraint to the Camera targeting "LookAtTarget", then save the file.
- **来源**: Blender Manual（https://docs.blender.org/manual/en/latest/）Animation > Constraints > Tracking > Track To
- **Upload Assets**: `constraint_ready.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_constraints.py` → `/tmp/check_constraints.py`
- **Evaluator**: `check_blender_constraints_multi`
- **Check Script**: `check_constraints.py`
- **result**: `vm_command_line` → `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_constraints.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
- **expected**: `rule` → `{"constraints": [{"object_name": "Orbiter", "type": "TRACK_TO", "target": "Target", "track_axis": "TRACK_NEGATIVE_Z", "up_axis": "UP_Y"}, {"object_name": "Camera", "type": "TRACK_TO", "target": "LookAtTarget"}]}`
- **初始状态**: Target, Orbiter, LookAtTarget (Empty) 已存在，无约束
- **验证逻辑**: 检查两个物体各自的 Track To 约束及参数
- **操作步骤数**: 4（给 Orbiter 加约束 → 设置轴 → 给 Camera 加约束 → 设置目标）
- **New Evaluator Required**: ✅

---
---

#### Task L2-9: 应用细分修改器并设置平滑着色
- **Task ID**: `a1622619-b429-4c1f-ae76-0736c108bab1`
- **JSON File**: `a1622619-b429-4c1f-ae76-0736c108bab1.json`

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. The "Cube" has a Subdivision Surface modifier with level 2. Apply the modifier so the extra geometry becomes permanent. Then set the object's shading to Smooth Shading (Right-click > Shade Smooth), and save the file.
- **来源**: Blender Manual（https://docs.blender.org/manual/en/latest/）Modeling > Modifiers（Apply）；Object > Shade Smooth
- **Upload Assets**: `cube_with_subsurf.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_object.py` → `/tmp/check_object.py`, `check_mesh.py` → `/tmp/check_mesh.py`
- **Evaluator**: 多指标 `["check_blender_applied_modifier", "check_blender_smooth_shading"]`, `"conj": "and"`
- **result**: 2 个 `vm_command_line`
  - `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_mesh.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
  - `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_mesh.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
- **expected**: 2 个 `rule`
  - `{"object_name": "Cube", "min_vertices": 20, "no_modifier_type": "SUBSURF"}`
  - `{"object_name": "Cube", "has_smooth": true}`
- **初始状态**: Cube 带 Subdivision Surface (level 2)，平面着色
- **验证逻辑**: 修改器不存在 + 顶点数 > 20 (应用后增加) + 面的 use_smooth 为 True
- **操作步骤数**: 3（应用修改器 → 右键 → Shade Smooth）
- **New Evaluator Required**: ✅ (check_blender_applied_modifier, check_blender_smooth_shading)

---
---

#### Task L2-10: 粒子系统参数配置
- **Task ID**: `77eaebd4-eb04-4471-a02d-af14dca41afd`
- **JSON File**: `77eaebd4-eb04-4471-a02d-af14dca41afd.json`

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. The "Emitter" plane has an existing particle system. Change the particle count to 2000, set the lifetime to 100 frames, set the emission start frame to 1 and end frame to 50, and change the normal velocity to 5.0, then save the file.
- **来源**: Blender Manual（https://docs.blender.org/manual/en/latest/）Physics > Particles > Emitter
- **Upload Assets**: `particles_ready.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_particles.py` → `/tmp/check_particles.py`
- **Evaluator**: `check_blender_particle_params`
- **Check Script**: `check_particles.py`
- **result**: `vm_command_line` → `/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_particles.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'`
- **expected**: `rule` → `{"object_name": "Emitter", "count": 2000, "lifetime": 100.0, "frame_start": 1.0, "frame_end": 50.0, "normal_factor": 5.0, "tolerance": 1.0}`
- **初始状态**: Emitter 平面已有粒子系统 (count=500)
- **验证逻辑**: 检查粒子系统的各项参数是否匹配
- **操作步骤数**: 5（改 count → 改 lifetime → 改 start frame → 改 end frame → 改 normal velocity）
- **New Evaluator Required**: ✅

---
---






### L2 任务汇总

| # | 任务名称 | 素材文件 | 检查脚本 | 步骤数 | 新评估器 |
|---|----------|----------|----------|--------|---------|
| 1 | PBR 材质创建 | `default_cube.blend` | `check_material.py` | 4 | ✅ |
| 2 | 布尔差集 + 隐藏 | `cube_sphere_boolean.blend` | `check_modifier.py` + `check_object.py` | 3 | ✅ |
| 3 | 木纹纹理映射 | `uv_unwrapped_cube.blend` | `check_material.py` | 4 | ✅ |
| 4 | 修改器堆叠调参 | `modifier_stack.blend` | `check_modifier.py` | 3 | ✅ |
| 5 | HDRI + Cycles | `default_cube.blend` | `check_render.py` + `check_world.py` | 3 | ✅ |
| 6 | 关键帧动画 + 帧范围 | `default_cube.blend` | `check_animation.py` + `check_render.py` | 4 | ✅ |
| 7 | 父子层级 + 集合 | `simple_scene_with_collection.blend` | `check_object.py` + `check_collection.py` | 3 | ✅ |
| 8 | 双 Track To 约束 | `constraint_ready.blend` | `check_constraints.py` | 4 | ✅ |
| 9 | 应用修改器 + Smooth | `cube_with_subsurf.blend` | `check_mesh.py` | 3 | ✅ |
| 10 | 粒子系统参数 | `particles_ready.blend` | `check_particles.py` | 5 | ✅ |

**L2 统计**: 10 个任务，10 个新评估函数，平均 3.6 步/任务

---

### 3.3 Level 3 — 高级操作 (Complex multi-step workflows) — 10 个

L3 任务为复杂多步工作流，每个任务涉及 **5-10+ 个 GUI 操作**，需要跨多个面板/编辑器/模式协作完成。部分任务包含渲染输出验证。

- **Launch**: `/snap/bin/blender /home/user/Documents/scene.blend`
- **Check Command**: 同 L1/L2
- **上传文件**: `.blend` 素材 → `/home/user/Documents/scene.blend`，检查脚本 → `/tmp/`，纹理/HDRI → `/home/user/Documents/`

---

#### Task L3-1: 完整 PBR 材质 + HDRI + Cycles 渲染输出
- **Task ID**: `8919e24a-4acf-4364-8ea8-27d331833f63`
- **JSON File**: `8919e24a-4acf-4364-8ea8-27d331833f63.json`

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. The "Cube" has a material "CubeMaterial" and is UV unwrapped. Do the following: (1) In the Shader Editor, load `/home/user/Documents/texture_wood.jpg` as the Base Color texture. (2) Load `/home/user/Documents/normal_wood.jpg` and connect it through a Normal Map node to the Normal input. (3) Set Metallic to 0.0 and Roughness to 0.7. (4) Go to World Properties, set the environment to use `/home/user/Documents/hdri_studio.exr`. (5) Switch the render engine to Cycles with 64 samples. (6) Set resolution to 1920×1080 and render the current frame, saving the image to `/home/user/Documents/render_output.png`. Then save the project file.
- **来源**: Blender Guru 教程站（https://www.blenderguru.com/tutorials）Donut Beginner Workflow（纹理、法线、HDRI、Cycles 渲染）
- **Upload Assets**: `uv_unwrapped_cube.blend` → `/home/user/Documents/scene.blend`, `texture_wood.jpg`, `normal_wood.jpg`, `hdri_studio.exr` → `/home/user/Documents/`
- **Upload Check Script**: `check_material.py` → `/tmp/check_material.py`, `check_world.py` → `/tmp/check_world.py`, `check_render.py` → `/tmp/check_render.py`
- **Evaluator**: 多指标 `["check_blender_material_textures", "check_blender_world_hdri", "check_blender_render_output"]`, `"conj": "and"`
- **result**: 3 个 getter
  - `vm_command_line` → material check
  - `vm_command_line` → world check
  - `vm_file` → `/home/user/Documents/render_output.png`
- **expected**: 3 个 `rule`
  - `{"object_name": "Cube", "textures": [{"filename": "texture_wood.jpg", "connected_to": "Base Color"}, {"filename": "normal_wood.jpg", "connected_to": "Normal"}], "metallic": 0.0, "roughness": 0.7, "tolerance": 0.05}`
  - `{"hdri_filename": "hdri_studio.exr"}`
  - `{"width": 1920, "height": 1080, "format": "PNG"}`
- **验证逻辑**: 纹理节点连接正确 + HDRI 加载 + 渲染图片存在且分辨率正确
- **操作步骤数**: 10+
- **New Evaluator Required**: ✅ (check_blender_render_output — PIL 验证图片)

---
---

#### Task L3-2: 动画视频渲染全流程
- **Task ID**: `d0c6f54f-7489-454f-a7ff-bc97460cd3e7`
- **JSON File**: `d0c6f54f-7489-454f-a7ff-bc97460cd3e7.json`

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. This scene has a ball with a 60-frame location animation. Do the following: (1) Set the scene frame rate to 30 fps. (2) Set the frame range to 1-60. (3) Switch to Cycles engine with 32 samples. (4) Set resolution to 1280×720. (5) Set the output format to FFmpeg Video with MP4 container and H.264 codec. (6) Set the output path to `/home/user/Documents/animation.mp4`. (7) Render the full animation. Then save the project file.
- **来源**: Blender Manual（https://docs.blender.org/manual/en/latest/）Animation + Render Output（FFmpeg/MP4 动画导出流程）
- **Upload Assets**: `animated_ball.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_render.py` → `/tmp/check_render.py`
- **Evaluator**: 多指标 `["check_blender_render_settings", "check_blender_render_video"]`, `"conj": "and"`
- **result**: 2 个 getter
  - `vm_command_line` → render settings check
  - `vm_file` → `/home/user/Documents/animation.mp4`
- **expected**: 2 个 `rule`
  - `{"engine": "CYCLES", "samples": 32, "resolution_x": 1280, "resolution_y": 720, "fps": 30}`
  - `{"min_duration": 1.5, "codec": "h264"}`
- **初始状态**: Ball 有 1→60 帧位移动画
- **验证逻辑**: 渲染参数正确 + MP4 文件存在且时长 > 1.5s
- **操作步骤数**: 8+
- **New Evaluator Required**: ✅ (check_blender_render_video — ffprobe 验证)

---
---

#### Task L3-3: 建模 + 修改器 + 材质 + 着色组合
- **Task ID**: `9b55a239-39e0-4953-9f19-f30dc9ba9a03`
- **JSON File**: `9b55a239-39e0-4953-9f19-f30dc9ba9a03.json`

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. Do the following: (1) Delete the default "Cube". (2) Add a UV Sphere. (3) Add a Subdivision Surface modifier to the sphere with viewport level 3. (4) Set the sphere to Smooth Shading. (5) Create a new material named "BlueSphere" with Base Color (R=0.0, G=0.2, B=1.0), Metallic 0.8, and Roughness 0.1. (6) Switch the render engine to Cycles. Then save the file.
- **来源**: Grant Abbitt 教学频道（https://www.youtube.com/@grabbitt）初学者建模/修改器/材质组合练习
- **Upload Assets**: `default_cube.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_object.py` → `/tmp/check_object.py`, `check_modifier.py` → `/tmp/check_modifier.py`, `check_material.py` → `/tmp/check_material.py`, `check_mesh.py` → `/tmp/check_mesh.py`, `check_render.py` → `/tmp/check_render.py`
- **Evaluator**: 多指标 `["check_blender_object_deleted", "check_blender_object_exists", "check_blender_modifier_subsurf", "check_blender_smooth_shading", "check_blender_material_pbr", "check_blender_render_engine"]`, `"conj": "and"`
- **result**: 6 个 `vm_command_line`
- **expected**: 6 个 `rule`
  - `{"deleted_object": "Cube"}`
  - `{"expected_type": "MESH", "name_contains": "Sphere"}`
  - `{"object_name_contains": "Sphere", "modifier_type": "SUBSURF", "levels": 3}`
  - `{"object_name_contains": "Sphere", "has_smooth": true}`
  - `{"object_name_contains": "Sphere", "material_name": "BlueSphere", "expected_color": [0.0, 0.2, 1.0, 1.0], "metallic": 0.8, "roughness": 0.1, "tolerance": 0.05}`
  - `{"engine": "CYCLES"}`
- **验证逻辑**: Cube 已删除 + Sphere 存在 + 修改器 + Smooth Shading + 材质参数 + 引擎
- **操作步骤数**: 8
- **New Evaluator Required**: ❌ (组合复用)

---
---

#### Task L3-4: 多物体桌面场景搭建
- **Task ID**: `d89c7be8-cce7-4106-920a-544616846c7d`
- **JSON File**: `d89c7be8-cce7-4106-920a-544616846c7d.json`

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. Build a simple table scene from scratch: (1) Delete the default "Cube". (2) Add a Cube, scale it to (3, 2, 0.1) and position at (0, 0, 1) as the table top. (3) Add 4 Cylinder objects as table legs, scale each to (0.1, 0.1, 0.5), positioned at (2.5, 1.5, 0.5), (-2.5, 1.5, 0.5), (2.5, -1.5, 0.5), (-2.5, -1.5, 0.5). (4) Select the table top, create a material named "WoodTable" with Base Color brown (R=0.4, G=0.2, B=0.05). (5) Parent all 4 legs to the table top. Then save the file.
- **来源**: 现实场景构造来源：家具电商详情页常见的“桌面单品搭建 + 材质 + 父子层级”制作需求
- **Upload Assets**: `default_cube.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_object.py` → `/tmp/check_object.py`, `check_material.py` → `/tmp/check_material.py`
- **Evaluator**: 多指标 `["check_blender_object_deleted", "check_blender_scene_objects", "check_blender_material_color", "check_blender_hierarchy"]`, `"conj": "and"`
- **result**: 4 个 `vm_command_line`
- **expected**: 4 个 `rule`
  - `{"deleted_object": "Cube"}`
  - `{"min_mesh_count": 5, "has_cylinder": true}`
  - `{"object_name": "Cube", "expected_color": [0.4, 0.2, 0.05, 1.0], "tolerance": 0.05}`
  - `{"parent_has_children": true, "min_children_count": 4}`
- **验证逻辑**: 原 Cube 删除 + 至少 5 个 mesh + 材质正确 + 父子关系
- **操作步骤数**: 10+
- **New Evaluator Required**: ❌ (组合复用)

---
---

#### Task L3-5: 物体层级 + 集合组织 + 约束完整工作流
- **Task ID**: `407b1850-9689-49a9-b4fa-abddbfeede0a`
- **JSON File**: `407b1850-9689-49a9-b4fa-abddbfeede0a.json`

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. This is a solar system hierarchy scene. Do the following: (1) Create a new collection named "Orbits". (2) Move "Planet1", "Planet2", "Planet3" into the "Orbits" collection. (3) Parent "Planet3" to "Sun" (it has no parent currently). (4) Add a "Track To" constraint to the Camera targeting "Sun". (5) Add a "Copy Location" constraint to "Moon" targeting "Planet1" (to make it orbit Planet1 instead of Planet2). (6) Clear "Moon"'s current parent "Planet2" and set "Planet1" as the new parent. Then save the file.
- **来源**: 现实场景构造来源：天文教学可视化项目中的“行星层级组织 + 约束控制”任务
- **Upload Assets**: `hierarchy_scene.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_object.py` → `/tmp/check_object.py`, `check_collection.py` → `/tmp/check_collection.py`, `check_constraints.py` → `/tmp/check_constraints.py`
- **Evaluator**: 多指标 `["check_blender_collection_members", "check_blender_hierarchy", "check_blender_constraints_multi"]`, `"conj": "and"`
- **result**: 3 个 `vm_command_line`
- **expected**: 3 个 `rule`
  - `{"collection_name": "Orbits", "expected_members": ["Planet1", "Planet2", "Planet3"]}`
  - `{"parent_map": {"Planet3": "Sun", "Moon": "Planet1"}, "not_parent": {"Moon": "Planet2"}}`
  - `{"constraints": [{"object_name": "Camera", "type": "TRACK_TO", "target": "Sun"}, {"object_name": "Moon", "type": "COPY_LOCATION", "target": "Planet1"}]}`
- **初始状态**: Sun → Planet1, Planet2 → Moon, Planet3 (无父级), 无集合组织
- **验证逻辑**: 集合成员 + 父子关系调整 + 约束添加
- **操作步骤数**: 8+
- **New Evaluator Required**: ❌ (组合复用)

---
---

#### Task L3-6: 厨房桌面场景材质 + 灯光 + 渲染
- **Task ID**: `e42d53eb-2f25-4938-9432-6ba77efca8e6`
- **JSON File**: `e42d53eb-2f25-4938-9432-6ba77efca8e6.json`

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. This is a kitchen table scene with TableTop, legs, Plate, Cup, and Floor. Do the following: (1) Create a material for "TableTop" with the wood texture `/home/user/Documents/texture_wood.jpg` as Base Color. (2) Create a material for "Plate" with white color (R=0.9, G=0.9, B=0.9) and Roughness 0.1. (3) Create a material for "Cup" with blue color (R=0.1, G=0.2, B=0.8) and Metallic 0.3. (4) Create a material for "Floor" using `/home/user/Documents/texture_tiles.jpg` as Base Color. (5) Set the Light energy to 800W. (6) Switch to Cycles with 128 samples and render to `/home/user/Documents/kitchen_render.png` at 1920×1080. Then save the project file.
- **来源**: 现实场景构造来源：家居视觉稿制作中的“厨房静帧场景材质、灯光与出图”工作流
- **Upload Assets**: `kitchen_table.blend` → `/home/user/Documents/scene.blend`, `texture_wood.jpg`, `texture_tiles.jpg` → `/home/user/Documents/`
- **Upload Check Script**: `check_material.py` → `/tmp/check_material.py`, `check_object.py` → `/tmp/check_object.py`, `check_render.py` → `/tmp/check_render.py`
- **Evaluator**: 多指标 `["check_blender_multi_material_scene", "check_blender_light_energy", "check_blender_render_output"]`, `"conj": "and"`
- **result**: 3 个 getter (2 个 `vm_command_line` + 1 个 `vm_file`)
- **expected**: 3 个 `rule`
  - `{"materials": [{"object_name": "TableTop", "has_texture": "texture_wood.jpg"}, {"object_name": "Plate", "expected_color": [0.9, 0.9, 0.9, 1.0], "roughness": 0.1}, {"object_name": "Cup", "expected_color": [0.1, 0.2, 0.8, 1.0], "metallic": 0.3}, {"object_name": "Floor", "has_texture": "texture_tiles.jpg"}], "tolerance": 0.05}`
  - `{"light_name": "Light", "energy": 800.0, "tolerance": 50}`
  - `{"width": 1920, "height": 1080, "format": "PNG"}`
- **初始状态**: 桌面场景无材质
- **验证逻辑**: 4 个物体材质正确 + 灯光能量 + 渲染输出
- **操作步骤数**: 12+
- **New Evaluator Required**: ✅ (check_blender_multi_material_scene)

---
---

#### Task L3-7: 从空场景搭建完整带动画场景
- **Task ID**: `c862b70f-9b34-4d47-aeba-19bf1f578af5`
- **JSON File**: `c862b70f-9b34-4d47-aeba-19bf1f578af5.json`

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. This is an empty scene with only a Camera. Build a complete animated scene: (1) Add a Plane at the origin, scale to (10, 10, 1) as the ground. (2) Add a UV Sphere at position (0, 0, 2), name it "Ball". (3) Create a material for "Ball" with red color (R=1.0, G=0.0, B=0.0) and Metallic 0.5. (4) Add a Sun light at position (5, 5, 10) with energy 3.0. (5) Set the scene frame range to 1-60. (6) Select "Ball", insert a Location keyframe at frame 1 with position (0, 0, 5). (7) Insert a Location keyframe at frame 30 with position (0, 0, 1). (8) Insert a Location keyframe at frame 60 with position (0, 0, 5). (9) Switch to Cycles with 32 samples, resolution 1280×720. Then save the file.
- **来源**: 现实场景构造来源：3D 动画岗位入门测试中的“从空场景完成建模、材质、动画、渲染设置”综合题
- **Upload Assets**: `empty_scene.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_object.py` → `/tmp/check_object.py`, `check_material.py` → `/tmp/check_material.py`, `check_animation.py` → `/tmp/check_animation.py`, `check_render.py` → `/tmp/check_render.py`
- **Evaluator**: 多指标 `["check_blender_scene_objects", "check_blender_material_color", "check_blender_animation_keyframes", "check_blender_render_settings"]`, `"conj": "and"`
- **result**: 4 个 `vm_command_line`
- **expected**: 4 个 `rule`
  - `{"has_objects": ["Ball"], "has_light_type": "SUN", "has_plane": true, "min_mesh_count": 2}`
  - `{"object_name": "Ball", "expected_color": [1.0, 0.0, 0.0, 1.0], "metallic": 0.5, "tolerance": 0.1}`
  - `{"object_name": "Ball", "min_keyframe_count": 3, "has_location_keys": true}`
  - `{"engine": "CYCLES", "samples": 32, "resolution_x": 1280, "resolution_y": 720}`
- **初始状态**: 仅有 Camera 的空场景
- **验证逻辑**: 物体存在 + 材质 + 动画关键帧 + 渲染设置
- **操作步骤数**: 12+
- **New Evaluator Required**: ❌ (组合复用)

---
---

#### Task L3-8: 物体布尔运算 + 材质 + 修改器工作流
- **Task ID**: `083eb099-2407-4a38-9145-2d6f42b0815c`
- **JSON File**: `083eb099-2407-4a38-9145-2d6f42b0815c.json`

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. This scene has a "Cube" and a "Sphere" overlapping. Do the following: (1) Add a Boolean modifier to "Cube" with Difference operation, target "Sphere". (2) Apply the Boolean modifier. (3) Delete the "Sphere" object. (4) Add a Bevel modifier to "Cube" with width 0.02 and 3 segments. (5) Set "Cube" to Smooth Shading. (6) Create a new material named "BronzeMetal" with Base Color (R=0.72, G=0.45, B=0.2), Metallic 1.0, Roughness 0.3. Then save the file.
- **来源**: Blender Manual（https://docs.blender.org/manual/en/latest/）Boolean + Bevel + Shade Smooth + PBR Material 组合工作流
- **Upload Assets**: `cube_sphere_boolean.blend` → `/home/user/Documents/scene.blend`
- **Upload Check Script**: `check_object.py` → `/tmp/check_object.py`, `check_mesh.py` → `/tmp/check_mesh.py`, `check_modifier.py` → `/tmp/check_modifier.py`, `check_material.py` → `/tmp/check_material.py`
- **Evaluator**: 多指标 `["check_blender_object_deleted", "check_blender_mesh_modified", "check_blender_modifier_bevel", "check_blender_smooth_shading", "check_blender_material_pbr"]`, `"conj": "and"`
- **result**: 5 个 `vm_command_line`
- **expected**: 5 个 `rule`
  - `{"deleted_object": "Sphere"}`
  - `{"object_name": "Cube", "min_vertices": 20, "no_modifier_type": "BOOLEAN"}`
  - `{"object_name": "Cube", "modifier_type": "BEVEL", "width": 0.02, "segments": 3, "tolerance": 0.01}`
  - `{"object_name": "Cube", "has_smooth": true}`
  - `{"object_name": "Cube", "material_name": "BronzeMetal", "expected_color": [0.72, 0.45, 0.2, 1.0], "metallic": 1.0, "roughness": 0.3, "tolerance": 0.05}`
- **初始状态**: Cube + Sphere 重叠
- **验证逻辑**: Sphere 删除 + 布尔已应用(顶点增加) + Bevel 修改器 + Smooth + 材质
- **操作步骤数**: 8+
- **New Evaluator Required**: ❌ (组合复用)

---
---

#### Task L3-9: 文字建模 + 挤出 + 材质 + 渲染
- **Task ID**: `1f157bab-72e1-4c29-8fed-453077dbf28f`
- **JSON File**: `1f157bab-72e1-4c29-8fed-453077dbf28f.json`

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. Do the following: (1) Select the "Title" text object and change its body to "BLENDER". (2) Set the font size to 3.0 and horizontal alignment to CENTER. (3) Set extrude depth to 0.3 and bevel depth to 0.02. (4) Create a material named "GoldText" with Base Color (R=1.0, G=0.84, B=0.0), Metallic 1.0, Roughness 0.2. (5) Load HDRI `/home/user/Documents/hdri_studio.exr` as the world environment. (6) Switch to Cycles with 64 samples, resolution 1920×1080. (7) Render to `/home/user/Documents/text_render.png`. Then save the project file.
- **来源**: Blender Manual（https://docs.blender.org/manual/en/latest/）Modeling > Texts；Rendering > Materials/World；Text 渲染流程
- **Upload Assets**: `text_3d_scene.blend` → `/home/user/Documents/scene.blend`, `hdri_studio.exr` → `/home/user/Documents/hdri_studio.exr`
- **Upload Check Script**: `check_text.py` → `/tmp/check_text.py`, `check_material.py` → `/tmp/check_material.py`, `check_world.py` → `/tmp/check_world.py`, `check_render.py` → `/tmp/check_render.py`
- **Evaluator**: 多指标 `["check_blender_text_styling", "check_blender_material_pbr", "check_blender_world_hdri", "check_blender_render_output"]`, `"conj": "and"`
- **result**: 4 个 getter (3 个 `vm_command_line` + 1 个 `vm_file`)
- **expected**: 4 个 `rule`
  - `{"object_name": "Title", "body": "BLENDER", "size": 3.0, "align_x": "CENTER", "extrude": 0.3, "bevel_depth": 0.02, "tolerance": 0.05}`
  - `{"object_name": "Title", "material_name": "GoldText", "expected_color": [1.0, 0.84, 0.0, 1.0], "metallic": 1.0, "roughness": 0.2, "tolerance": 0.05}`
  - `{"hdri_filename": "hdri_studio.exr"}`
  - `{"width": 1920, "height": 1080, "format": "PNG"}`
- **初始状态**: Title (size=1.5), Subtitle (size=0.8), ExtrudedText (extrude=0.3)
- **验证逻辑**: 文本内容和样式 + 材质 + HDRI + 渲染输出
- **操作步骤数**: 10+
- **New Evaluator Required**: ❌ (组合复用)

---
---

#### Task L3-10: 完整产品展示渲染流程
- **Task ID**: `a2ba5904-0f5f-4282-be35-9976a34b6c33`
- **JSON File**: `a2ba5904-0f5f-4282-be35-9976a34b6c33.json`

- **Instruction**: Open the Blender project `/home/user/Documents/scene.blend`. Set up a professional product visualization: (1) Select the "Cube" and add a Bevel modifier with width 0.05 and 4 segments. (2) Add a Subdivision Surface modifier with viewport level 2. (3) Set Smooth Shading. (4) Create a material with `/home/user/Documents/texture_metal.jpg` as Base Color, `/home/user/Documents/roughness_metal.jpg` connected to Roughness, and Metallic set to 0.9. (5) Load `/home/user/Documents/hdri_studio.exr` as HDRI environment. (6) Select the Camera, set focal length to 85mm, enable Depth of Field with F-Stop 2.8 and Focus Distance 5.0. (7) Switch to Cycles with 256 samples, resolution 2560×1440. (8) Render to `/home/user/Documents/product_render.png`. Then save the project file.
- **来源**: 现实场景构造来源（参考产品可视化教程范式）：电商产品主视觉常见的“倒角细分 + PBR + HDRI + DOF + 高分辨率渲染”流程
- **Upload Assets**: `uv_unwrapped_cube.blend` → `/home/user/Documents/scene.blend`, `texture_metal.jpg`, `roughness_metal.jpg`, `hdri_studio.exr` → `/home/user/Documents/`
- **Upload Check Script**: `check_modifier.py`, `check_mesh.py`, `check_material.py`, `check_world.py`, `check_render.py`, `check_object.py` → `/tmp/`
- **Evaluator**: 多指标 `["check_blender_modifier_stack", "check_blender_smooth_shading", "check_blender_pbr_setup", "check_blender_world_hdri", "check_blender_camera_config", "check_blender_render_output"]`, `"conj": "and"`
- **result**: 6 个 getter (5 个 `vm_command_line` + 1 个 `vm_file`)
- **expected**: 6 个 `rule`
  - `{"object_name": "Cube", "modifiers": {"BEVEL": {"width": 0.05, "segments": 4}, "SUBSURF": {"levels": 2}}}`
  - `{"object_name": "Cube", "has_smooth": true}`
  - `{"object_name": "Cube", "textures": [{"filename": "texture_metal.jpg", "connected_to": "Base Color"}, {"filename": "roughness_metal.jpg", "connected_to": "Roughness"}], "metallic": 0.9, "tolerance": 0.05}`
  - `{"hdri_filename": "hdri_studio.exr"}`
  - `{"camera_name": "Camera", "focal_length": 85.0, "dof_enabled": true, "tolerance": 0.5}`
  - `{"width": 2560, "height": 1440, "format": "PNG"}`
- **验证逻辑**: 修改器 + Smooth + PBR 纹理 + HDRI + 相机 DOF + 渲染输出
- **操作步骤数**: 15+
- **New Evaluator Required**: ❌ (组合复用)

---

### L3 任务汇总

| # | 任务名称 | 素材文件 | 检查脚本数 | 评估指标数 | 步骤数 | 新评估器 |
|---|----------|----------|-----------|-----------|--------|---------|
| 1 | PBR + HDRI + 渲染 | `uv_unwrapped_cube` + 纹理 + HDRI | 3 | 3 | 10+ | ✅ |
| 2 | 动画视频渲染 | `animated_ball` | 1 | 2 | 8+ | ✅ |
| 3 | 建模+修改器+材质+着色 | `default_cube` | 5 | 6 | 8 | ❌ |
| 4 | 多物体桌面场景 | `default_cube` | 2 | 4 | 10+ | ❌ |
| 5 | 层级+集合+约束 | `hierarchy_scene` | 3 | 3 | 8+ | ❌ |
| 6 | 厨房场景材质+渲染 | `kitchen_table` + 纹理 | 3 | 3 | 12+ | ✅ |
| 7 | 从空场景搭建动画 | `empty_scene` | 4 | 4 | 12+ | ❌ |
| 8 | 布尔+修改器+材质 | `cube_sphere_boolean` | 4 | 5 | 8+ | ❌ |
| 9 | 文字建模+材质+渲染 | `text_3d_scene` + HDRI | 4 | 4 | 10+ | ❌ |
| 10 | 产品展示完整渲染 | `uv_unwrapped_cube` + 纹理 + HDRI | 6 | 6 | 15+ | ❌ |

**L3 统计**: 10 个任务，3 个新评估函数，平均 10+ 步/任务


### 3.4 Interactive 任务（Blender，多轮）—— 6 个（设计草案）

> 说明：以下为 Blender interactive 场景规划，后续可落地到 `evaluation_examples/examples/interactive/interactive_blender_*.json`。
> 触发方式覆盖：`step_count`（2 个）+ `agent_asks`（1 个）+ `agent_done`（6 个任务收尾）。

#### Interactive 构建流程（与现有代码实现对齐）

1. **任务结构**：JSON 需包含 `interactive: true`、`scenario_type`、`user_persona`、`phases`。
2. **环境准备**：在 `config` 里先上传 `.blend` 与贴图/HDRI，再用 `/snap/bin/blender /home/user/Documents/scene.blend` 启动。
3. **阶段推进**：
   - `step_count`：按“当前 phase 内执行步数”触发（不是全局 step）。
   - `agent_asks`：当 Agent 输出 `CALL_USER` 时触发用户回复。
   - `agent_done`：当 Agent 输出 `DONE` 或 `FAIL` 时进入下一阶段。
4. **设计约束**：非 `agent_asks` 阶段不建议依赖 `CALL_USER`，避免无效打断；最终统一使用终态评估器检查最后产物。

#### IB-01：电商主图中途换材质（step_count）

- **场景类型**：`requirement_change`
- **素材**：`render_ready_cycles.blend`，`texture_metal.jpg`，`texture_wood.jpg`，`hdri_studio.exr`
- **核心目标**：先按金属风做产品图，用户中途改为木质风并要求重新出图。
- **Phase 设计**：
  - **Phase 1**："先做一个冷色金属质感版本，渲染到 `/home/user/Documents/product_v1.png`。"
    - `trigger`: `{"type": "step_count", "value": 4}`
  - **Phase 2**："方向改了，主体改成木纹（`texture_wood.jpg`），保持摄影棚 HDRI，重新渲染 `/home/user/Documents/product_final.png`，并保存工程。"
    - `trigger`: `{"type": "agent_done"}`
- **预期考点**：中途需求切换、材质节点替换、同场景返工重渲染。

#### IB-02：短视频片头分阶段交付（agent_done）

- **场景类型**：`multi_step_workflow`
- **素材**：`animation_rotation.blend`
- **核心目标**：先交低清预览，再按确认稿输出正式片头和封面帧。
- **Phase 设计**：
  - **Phase 1**："先导出低清审片版 MP4（`/home/user/Documents/teaser_preview.mp4`），我先看节奏。"
    - `trigger`: `{"type": "agent_done"}`
  - **Phase 2**："可以，按定稿参数导出 1920x1080 的正式 MP4 到 `/home/user/Documents/teaser_final.mp4`。"
    - `trigger`: `{"type": "agent_done"}`
  - **Phase 3**："再补一张中间帧封面图到 `/home/user/Documents/teaser_cover.png`，并保存工程。"
    - `trigger`: `{"type": "agent_done"}`
- **预期考点**：多轮交付稳定性、视频与静帧双产物输出、阶段记忆。

#### IB-03：模糊创意简报需主动追问（agent_asks）

- **场景类型**：`ambiguous_instruction`
- **素材**：`text_3d_scene.blend`，`hdri_studio.exr`
- **核心目标**：首轮需求故意模糊，要求 Agent 主动澄清后再执行。
- **Phase 设计**：
  - **Phase 1**："帮我做个科技感标题封面，先整一个。"
    - `trigger`: `{"type": "agent_asks"}`
  - **Phase 2**："具体要求是：标题文字改成 `NEON LOOP`，金属感偏蓝，使用 `hdri_studio.exr`，输出 `/home/user/Documents/neon_cover.png`。"
    - `trigger`: `{"type": "agent_done"}`
  - **Phase 3**："再导出一张透明背景 PNG 到 `/home/user/Documents/neon_title_alpha.png`，用于后期叠加。"
    - `trigger`: `{"type": "agent_done"}`
- **预期考点**：`CALL_USER` 触发澄清、澄清后参数化执行、同主题多格式导出。

#### IB-04：构图进行中插入平台规格（step_count）

- **场景类型**：`interruption`
- **素材**：`kitchen_table.blend`
- **核心目标**：在正常摆拍流程中插入新约束（竖版比例 + DOF 特写）。
- **Phase 设计**：
  - **Phase 1**："先把厨房桌面场景调成干净的商品图构图并准备渲染。"
    - `trigger`: `{"type": "step_count", "value": 3}`
  - **Phase 2**："临时改需求：用于短视频封面，改成 1080x1920，焦点放在 Cup 上并开启景深，输出 `/home/user/Documents/coffee_story.png`。"
    - `trigger`: `{"type": "agent_done"}`
  - **Phase 3**："最后把工程保存为 `/home/user/Documents/kitchen_story.blend`。"
    - `trigger`: `{"type": "agent_done"}`
- **预期考点**：中断后继续编辑、镜头与相机参数重设、平台尺寸适配。

#### IB-05：先交初稿再按反馈返工（agent_done）

- **场景类型**：`progressive_refinement`
- **素材**：`donut_base.blend`
- **核心目标**：先出可评审版本，再根据反馈改材质和镜头产出最终图。
- **Phase 设计**：
  - **Phase 1**："先导出一个可评审版本 `/home/user/Documents/donut_v1.png`。"
    - `trigger`: `{"type": "agent_done"}`
  - **Phase 2**："反馈：甜甜圈看起来太塑料，降低高光感、提升糖霜粗糙度后重渲 `/home/user/Documents/donut_v2.png`。"
    - `trigger`: `{"type": "agent_done"}`
  - **Phase 3**："再给一个 1:1 近景图 `/home/user/Documents/donut_square.png`，并保存工程。"
    - `trigger`: `{"type": "agent_done"}`
- **预期考点**：返工场景下材质二次调参、构图迭代、重复导出一致性。

#### IB-06：资产交接前的场景规范化（agent_done）

- **场景类型**：`multi_step_workflow`
- **素材**：`simple_scene_with_collection.blend`
- **核心目标**：模拟团队协作中“可继续制作”的场景交接流程。
- **Phase 设计**：
  - **Phase 1**："先整理场景：把 `Cube`、`Sphere` 移进 `Props` 集合，并按资产命名规范重命名。"
    - `trigger`: `{"type": "agent_done"}`
  - **Phase 2**："给场景补一个交接预览渲染图 `/home/user/Documents/handoff_preview.png`。"
    - `trigger`: `{"type": "agent_done"}`
  - **Phase 3**："最后把交接文件保存为 `/home/user/Documents/scene_handoff.blend`。"
    - `trigger`: `{"type": "agent_done"}`
- **预期考点**：Outliner 组织、命名与集合规范、可交接产物打包。

#### Interactive 触发分布汇总（本批 6 个）

| 任务ID | trigger 覆盖 |
|---|---|
| IB-01 | `step_count` + `agent_done` |
| IB-02 | `agent_done` |
| IB-03 | `agent_asks` + `agent_done` |
| IB-04 | `step_count` + `agent_done` |
| IB-05 | `agent_done` |
| IB-06 | `agent_done` |

#### Interactive 任务来源映射（本批 6 个）

| 任务ID | 场景类型 | 真实工作来源（Primary Source） | 证据包（最小） | Task JSON `source` 建议写法 |
|---|---|---|---|---|
| IB-01 | `requirement_change` | 电商主图制作中客户临时换材质方向 | ① 初稿需求摘录 ② 变更指令 ③ 重渲染验收截图 | `blender_interactive;source_type=ecommerce_brief;source_ref=<id_or_url>;evidence=requirement_change` |
| IB-02 | `multi_step_workflow` | 短视频片头“预览版→正式版”分阶段交付 | ① 预览确认记录 ② 定稿参数 ③ 最终导出验收 | `blender_interactive;source_type=content_pipeline;source_ref=<id_or_url>;evidence=staged_delivery` |
| IB-03 | `ambiguous_instruction` | 创意简报含糊，设计师先澄清再执行 | ① 模糊简报原文 ② 澄清问答 ③ 执行后的参数单 | `blender_interactive;source_type=creative_brief;source_ref=<id_or_url>;evidence=clarification_required` |
| IB-04 | `interruption` | 视觉稿进行中被插入平台规格（竖版/景深） | ① 初始需求 ② 中断时新增约束 ③ 改版结果对比 | `blender_interactive;source_type=platform_change_request;source_ref=<id_or_url>;evidence=mid_process_interruption` |
| IB-05 | `progressive_refinement` | 初稿评审后按反馈迭代材质与镜头 | ① v1 评审意见 ② 返工清单 ③ v2/v3 导出记录 | `blender_interactive;source_type=iterative_delivery;source_ref=<id_or_url>;evidence=rework_loop` |
| IB-06 | `multi_step_workflow` | 团队协作中常见的场景整理与交接 | ① 命名规范文档 ② 交接清单 ③ 预览图与工程文件 | `blender_interactive;source_type=team_handoff;source_ref=<id_or_url>;evidence=handoff_packaging` |

### 3.5 Interactive 任务扩展（Blender，多轮）—— 新增 8 个（真实制作流草案）

> 说明：以下 8 个任务重点使用 `assets/blender/external/` 新素材，强调真实制作中的“预览-确认-返工-交付”。
> 触发方式覆盖建议：`step_count`（3 个）+ `agent_asks`（1 个）+ `agent_done`（全部收尾）。

#### IB-07：电商饮品套图（预览→定稿→透明底）

- **场景类型**：`multi_step_workflow`
- **素材**：`model_waterbottle.glb`，`hdri_kloppenheim_06_puresky_1k.exr`
- **核心目标**：模拟电商常见“一稿确认后再补透明底 PNG”。
- **Phase 设计**：
  - **Phase 1**："先做一个预览图到 `/home/user/Documents/bottle_preview.jpg`，我只看构图。"
    - `trigger`: `{"type": "agent_done"}`
  - **Phase 2**："构图可以，改成 2000x2000 的正式图 `/home/user/Documents/bottle_final.png`。"
    - `trigger`: `{"type": "agent_done"}`
  - **Phase 3**："再导一张透明背景版本 `/home/user/Documents/bottle_cutout.png`，并保存工程。"
    - `trigger`: `{"type": "agent_done"}`
- **预期考点**：同一资产多交付规格、透明背景导出、参数继承稳定性。

#### IB-08：食品广告 A/B 光照对比（step_count）

- **场景类型**：`requirement_change`
- **素材**：`model_avocado.glb`，`hdri_kloppenheim_06_puresky_1k.exr`，`hdri/hdri_aerodynamics_workshop_1k.exr`
- **核心目标**：先做自然光版本，中途切换到工业棚感做 B 版。
- **Phase 设计**：
  - **Phase 1**："先用户外自然光做 A 版，输出 `/home/user/Documents/avocado_a.png`。"
    - `trigger`: `{"type": "step_count", "value": 4}`
  - **Phase 2**："改成更硬一点的棚感光，做 B 版 `/home/user/Documents/avocado_b.png`，保存工程。"
    - `trigger`: `{"type": "agent_done"}`
- **预期考点**：HDRI 切换、风格迁移、双版本导出。

#### IB-09：复古空间道具图（中断插单改比例）

- **场景类型**：`interruption`
- **素材**：`polyhaven_barbershop_chair_01/BarberShopChair_01_1k.blend`（含 textures）
- **核心目标**：先做横版目录图，中途改为竖版短视频封面。
- **Phase 设计**：
  - **Phase 1**："先输出 16:9 横版目录图 `/home/user/Documents/chair_catalog.png`。"
    - `trigger`: `{"type": "step_count", "value": 3}`
  - **Phase 2**："临时插单：改成 9:16 竖版封面 `/home/user/Documents/chair_story.png`，主体尽量居中偏下。"
    - `trigger`: `{"type": "agent_done"}`
  - **Phase 3**："再补存工程 `/home/user/Documents/chair_pack.blend`。"
    - `trigger`: `{"type": "agent_done"}`
- **预期考点**：画幅切换、构图重排、导出链路不中断。

#### IB-10：消费电子主视觉合规返工（agent_done）

- **场景类型**：`progressive_refinement`
- **素材**：`model_boombox.glb`
- **核心目标**：模拟营销图被法务反馈后快速返工。
- **Phase 设计**：
  - **Phase 1**："先做主视觉图 `/home/user/Documents/boombox_hero_v1.png`。"
    - `trigger`: `{"type": "agent_done"}`
  - **Phase 2**："法务反馈：右上角留 15% 安全区，重渲 `/home/user/Documents/boombox_hero_v2.png`。"
    - `trigger`: `{"type": "agent_done"}`
  - **Phase 3**："再导一版小尺寸预览图 `/home/user/Documents/boombox_thumb.png`（长边 1080）。"
    - `trigger`: `{"type": "agent_done"}`
- **预期考点**：构图安全区、同内容多尺寸交付、迭代重渲。

#### IB-11：服饰材质 LookDev 澄清式需求（agent_asks）

- **场景类型**：`ambiguous_instruction`
- **素材**：`model_corset.glb`，`hdri/hdri_aerodynamics_workshop_1k.exr`
- **核心目标**：用户只说“高级一点”，要求 Agent 主动问清风格后执行。
- **Phase 设计**：
  - **Phase 1**："这个服饰效果不够高级，帮我调一下。"
    - `trigger`: `{"type": "agent_asks"}`
  - **Phase 2**："我想要偏冷色、丝绸感更明显、保留细节阴影，输出 `/home/user/Documents/corset_lookdev.png`。"
    - `trigger`: `{"type": "agent_done"}`
  - **Phase 3**："最后保存工程到 `/home/user/Documents/corset_lookdev.blend`。"
    - `trigger`: `{"type": "agent_done"}`
- **预期考点**：`CALL_USER` 澄清能力、材质风格调参、审美要求转参数。

#### IB-12：家居目录图三阶段交付（agent_done）

- **场景类型**：`multi_step_workflow`
- **素材**：`polyhaven_armchair_01/ArmChair_01_1k.blend`（含 textures）
- **核心目标**：模拟家居目录常见“白底图 + 情绪图 + 工程归档”。
- **Phase 设计**：
  - **Phase 1**："先出白底目录图 `/home/user/Documents/armchair_catalog.png`。"
    - `trigger`: `{"type": "agent_done"}`
  - **Phase 2**："再出一张氛围图 `/home/user/Documents/armchair_mood.png`，可以用室内 HDRI。"
    - `trigger`: `{"type": "agent_done"}`
  - **Phase 3**："把工程保存为 `/home/user/Documents/armchair_delivery.blend`。"
    - `trigger`: `{"type": "agent_done"}`
- **预期考点**：同资产多风格交付、背景与灯光切换、最终归档。

#### IB-13：场景地表材质追加需求（step_count）

- **场景类型**：`interruption`
- **素材**：`simple_scene.blend`，`textures/texture_coast_sand_rocks_02_{diff,nor_gl,rough}_1k.jpg`
- **核心目标**：先完成基础摆放，中途要求给地面补完整 PBR 贴图链路。
- **Phase 设计**：
  - **Phase 1**："先把这个场景的主体构图整理好，准备渲染。"
    - `trigger`: `{"type": "step_count", "value": 3}`
  - **Phase 2**："补充：地面要用海岸岩砂贴图，diff+normal+roughness 都接好，渲染 `/home/user/Documents/scene_ground_final.png`。"
    - `trigger`: `{"type": "agent_done"}`
- **预期考点**：中途新增技术约束、节点连接完整性、最终渲染一致性。

#### IB-14：灯具详情页日夜双版本（agent_done）

- **场景类型**：`progressive_refinement`
- **素材**：`model_lantern.glb`，`hdri_kloppenheim_06_puresky_1k.exr`，`hdri/hdri_aerodynamics_workshop_1k.exr`
- **核心目标**：详情页常见的同构图双光照版本交付。
- **Phase 设计**：
  - **Phase 1**："先做白天版 `/home/user/Documents/lantern_day.png`（自然光）。"
    - `trigger`: `{"type": "agent_done"}`
  - **Phase 2**："再做夜间版 `/home/user/Documents/lantern_night.png`（更强反差）。"
    - `trigger`: `{"type": "agent_done"}`
  - **Phase 3**："最后导出对比拼图 `/home/user/Documents/lantern_compare.png`，并保存工程。"
    - `trigger`: `{"type": "agent_done"}`
- **预期考点**：同镜头双风格一致性、HDRI 快速切换、多输出文件组织。

#### Interactive 触发分布汇总（新增 8 个）

| 任务ID | trigger 覆盖 |
|---|---|
| IB-07 | `agent_done` |
| IB-08 | `step_count` + `agent_done` |
| IB-09 | `step_count` + `agent_done` |
| IB-10 | `agent_done` |
| IB-11 | `agent_asks` + `agent_done` |
| IB-12 | `agent_done` |
| IB-13 | `step_count` + `agent_done` |
| IB-14 | `agent_done` |

#### Interactive 任务来源映射（新增 8 个）

| 任务ID | 场景类型 | 真实工作来源（Primary Source） | 证据包（最小） | Task JSON `source` 建议写法 |
|---|---|---|---|---|
| IB-07 | `multi_step_workflow` | 电商商品图常见“预览-定稿-透明底”链路 | ① 需求单 ② 交付清单 ③ 透明底验收图 | `blender_interactive;source_type=ecommerce_pipeline;source_ref=<id_or_url>;evidence=multi_output_delivery` |
| IB-08 | `requirement_change` | 广告图中途更换光照风格（A/B） | ① 初版方向 ② 临时变更记录 ③ A/B 对比稿 | `blender_interactive;source_type=marketing_change_request;source_ref=<id_or_url>;evidence=lighting_style_switch` |
| IB-09 | `interruption` | 社媒封面插单导致画幅切换 | ① 原画幅需求 ② 新平台规格 ③ 改版输出记录 | `blender_interactive;source_type=social_media_interruption;source_ref=<id_or_url>;evidence=aspect_ratio_switch` |
| IB-10 | `progressive_refinement` | 营销物料法务返工（安全区/可读性） | ① v1 反馈 ② 返工约束 ③ v2/v3 验收 | `blender_interactive;source_type=compliance_rework;source_ref=<id_or_url>;evidence=safe_area_adjustment` |
| IB-11 | `ambiguous_instruction` | 设计评审中的抽象审美反馈需澄清 | ① 模糊反馈 ② 澄清问答 ③ 参数化改动记录 | `blender_interactive;source_type=design_review;source_ref=<id_or_url>;evidence=clarification_required` |
| IB-12 | `multi_step_workflow` | 家居目录图分阶段交付流程 | ① 白底图规范 ② 氛围图要求 ③ 工程归档要求 | `blender_interactive;source_type=catalog_pipeline;source_ref=<id_or_url>;evidence=staged_catalog_delivery` |
| IB-13 | `interruption` | 场景制作中追加 PBR 技术规范 | ① 初始美术需求 ② 技术补充需求 ③ 节点检查结果 | `blender_interactive;source_type=tech_art_change_request;source_ref=<id_or_url>;evidence=pbr_chain_insertion` |
| IB-14 | `progressive_refinement` | 商品详情页日夜双版本需求 | ① 白天版需求 ② 夜间版需求 ③ 对比图验收 | `blender_interactive;source_type=product_detail_page;source_ref=<id_or_url>;evidence=day_night_variant` |

### 3.6 Interactive JSON 字段级模板（IB-07 ~ IB-14 可直接落地）

> 目标：把 3.5 的 8 个草案细化为可以直接落地为 JSON 的字段模板。
> 约束：评估函数统一使用 `desktop_env/evaluators/metrics/blender.py` 中已有函数。

#### 3.6.1 通用骨架模板（8 个任务通用）

```json
{
  "id": "interactive_blender_<slug>_001",
  "snapshot": "blender",
  "interactive": true,
  "scenario_type": "<multi_step_workflow|requirement_change|interruption|ambiguous_instruction|progressive_refinement>",
  "scenario_description": "<场景一句话描述>",
  "user_persona": {
    "expertise_level": "intermediate",
    "communication_style": "casual_chinese"
  },
  "source": "blender_interactive;source_type=<...>;source_ref=<id_or_url>;evidence=<...>",
  "config": [
    {
      "type": "upload_file",
      "parameters": {
        "files": [
          {"local_path": "assets/blender/empty_scene.blend", "path": "/home/user/Documents/scene_start.blend"},
          {"local_path": "assets/blender/<asset_or_external_file>", "path": "/home/user/Documents/<asset_or_external_file>"},
          {"local_path": "assets/blender/check_render.py", "path": "/tmp/check_render.py"},
          {"local_path": "assets/blender/check_world.py", "path": "/tmp/check_world.py"},
          {"local_path": "assets/blender/check_material.py", "path": "/tmp/check_material.py"}
        ]
      }
    },
    {
      "type": "launch",
      "parameters": {
        "command": ["/snap/bin/blender", "/home/user/Documents/scene_start.blend"]
      }
    },
    {
      "type": "sleep",
      "parameters": {
        "seconds": 3
      }
    }
  ],
  "phases": [
    {
      "phase_id": 1,
      "instruction": "<phase-1 user message>",
      "trigger": {"type": "<step_count|agent_done|agent_asks>", "value": 3}
    },
    {
      "phase_id": 2,
      "instruction": "<phase-2 user message>",
      "trigger": {"type": "agent_done"}
    },
    {
      "phase_id": 3,
      "instruction": "<phase-3 user message>",
      "trigger": {"type": "agent_done"}
    }
  ],
  "trajectory": "trajectories/",
  "related_apps": ["blender"],
  "evaluator": {
    "postconfig": [],
    "func": [
      "check_blender_render_settings",
      "check_blender_world_hdri",
      "check_blender_render_output"
    ],
    "conj": "and",
    "result": [
      {
        "type": "vm_command_line",
        "command": "/snap/bin/blender --background /home/user/Documents/<saved_scene>.blend --python /tmp/check_render.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'",
        "shell": true
      },
      {
        "type": "vm_command_line",
        "command": "/snap/bin/blender --background /home/user/Documents/<saved_scene>.blend --python /tmp/check_world.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'",
        "shell": true
      },
      {
        "type": "vm_file",
        "path": "/home/user/Documents/<final_output>.png",
        "dest": "<final_output>.png"
      }
    ],
    "expected": [
      {
        "type": "rule",
        "rules": {
          "engine": "CYCLES",
          "resolution_x": 2000,
          "resolution_y": 2000,
          "image_format": "PNG"
        }
      },
      {
        "type": "rule",
        "rules": {
          "hdri_filename": "<expected_hdri>.exr"
        }
      },
      {
        "type": "rule",
        "rules": {
          "width": 2000,
          "height": 2000,
          "format": "PNG"
        }
      }
    ]
  },
  "proxy": false,
  "fixed_ip": false,
  "possibility_of_env_change": "low",
  "difficulty": "L3"
}
```

#### 3.6.2 IB-07 完整字段模板（可直接拷贝改 ID）

```json
{
  "id": "interactive_blender_ib07_bottle_multidelivery_001",
  "snapshot": "blender",
  "interactive": true,
  "scenario_type": "multi_step_workflow",
  "scenario_description": "电商饮品图分阶段交付：预览图 -> 正式方图 -> 透明底抠图。",
  "user_persona": {
    "expertise_level": "intermediate",
    "communication_style": "casual_chinese"
  },
  "source": "blender_interactive;source_type=ecommerce_pipeline;source_ref=<id_or_url>;evidence=multi_output_delivery",
  "config": [
    {
      "type": "upload_file",
      "parameters": {
        "files": [
          {"local_path": "assets/blender/empty_scene.blend", "path": "/home/user/Documents/scene_start.blend"},
          {"local_path": "assets/blender/external/model_waterbottle.glb", "path": "/home/user/Documents/model_waterbottle.glb"},
          {"local_path": "assets/blender/external/hdri_kloppenheim_06_puresky_1k.exr", "path": "/home/user/Documents/hdri_kloppenheim_06_puresky_1k.exr"},
          {"local_path": "assets/blender/check_render.py", "path": "/tmp/check_render.py"},
          {"local_path": "assets/blender/check_world.py", "path": "/tmp/check_world.py"}
        ]
      }
    },
    {
      "type": "launch",
      "parameters": {
        "command": ["/snap/bin/blender", "/home/user/Documents/scene_start.blend"]
      }
    },
    {
      "type": "sleep",
      "parameters": {
        "seconds": 3
      }
    }
  ],
  "phases": [
    {
      "phase_id": 1,
      "instruction": "先做一个预览图到 /home/user/Documents/bottle_preview.jpg，我只看构图。",
      "trigger": {"type": "agent_done"}
    },
    {
      "phase_id": 2,
      "instruction": "构图可以，改成 2000x2000 的正式图 /home/user/Documents/bottle_final.png。",
      "trigger": {"type": "agent_done"}
    },
    {
      "phase_id": 3,
      "instruction": "再导一张透明背景版本 /home/user/Documents/bottle_cutout.png，并保存工程到 /home/user/Documents/ib07_delivery.blend。",
      "trigger": {"type": "agent_done"}
    }
  ],
  "trajectory": "trajectories/",
  "related_apps": ["blender"],
  "evaluator": {
    "postconfig": [],
    "func": [
      "check_blender_render_settings",
      "check_blender_world_hdri",
      "check_blender_render_output",
      "check_blender_render_output",
      "check_blender_render_output"
    ],
    "conj": "and",
    "result": [
      {
        "type": "vm_command_line",
        "command": "/snap/bin/blender --background /home/user/Documents/ib07_delivery.blend --python /tmp/check_render.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'",
        "shell": true
      },
      {
        "type": "vm_command_line",
        "command": "/snap/bin/blender --background /home/user/Documents/ib07_delivery.blend --python /tmp/check_world.py 2>&1 | grep '^RESULT:' | sed 's/^RESULT://'",
        "shell": true
      },
      {
        "type": "vm_file",
        "path": "/home/user/Documents/bottle_preview.jpg",
        "dest": "ib07_bottle_preview.jpg"
      },
      {
        "type": "vm_file",
        "path": "/home/user/Documents/bottle_final.png",
        "dest": "ib07_bottle_final.png"
      },
      {
        "type": "vm_file",
        "path": "/home/user/Documents/bottle_cutout.png",
        "dest": "ib07_bottle_cutout.png"
      }
    ],
    "expected": [
      {
        "type": "rule",
        "rules": {
          "engine": "CYCLES",
          "resolution_x": 2000,
          "resolution_y": 2000,
          "image_format": "PNG"
        }
      },
      {
        "type": "rule",
        "rules": {
          "hdri_filename": "hdri_kloppenheim_06_puresky_1k.exr"
        }
      },
      {
        "type": "rule",
        "rules": {
          "format": "JPEG"
        }
      },
      {
        "type": "rule",
        "rules": {
          "width": 2000,
          "height": 2000,
          "format": "PNG"
        }
      },
      {
        "type": "rule",
        "rules": {
          "format": "PNG"
        }
      }
    ]
  },
  "proxy": false,
  "fixed_ip": false,
  "possibility_of_env_change": "low",
  "difficulty": "L3"
}
```

#### 3.6.3 IB-08 ~ IB-14 字段级落地矩阵（按 3.6.1 骨架填充）

| 任务ID | `config` 关键 `local_path` | `phases` trigger | `evaluator.func`（全部来自 `blender.py`） | `result/expected` 关键字段 |
|---|---|---|---|---|
| IB-08 | `model_avocado.glb` + `hdri_kloppenheim_06_puresky_1k.exr` + `hdri/hdri_aerodynamics_workshop_1k.exr` + `check_world.py` + `check_render.py` | P1 `step_count:4`, P2 `agent_done` | `check_blender_world_hdri`, `check_blender_render_output`, `check_blender_render_output`, `check_blender_render_settings` | 检查 `avocado_a.png`、`avocado_b.png` 均存在；最终保存 `ib08_delivery.blend` 并验证可被 `check_render.py` 读取 |
| IB-09 | `polyhaven_barbershop_chair_01/BarberShopChair_01_1k.blend` + 3 张 chair textures + `check_render.py` | P1 `step_count:3`, P2/P3 `agent_done` | `check_blender_render_settings`, `check_blender_render_output`, `check_blender_render_output`, `check_blender_render_settings` | 竖版图 `chair_story.png` 要求 `1080x1920`；横版 `chair_catalog.png` 存在；保存 `chair_pack.blend` |
| IB-10 | `model_boombox.glb` + `check_render.py` | 三阶段 `agent_done` | `check_blender_render_output`, `check_blender_render_output`, `check_blender_render_settings` | 检查 `boombox_hero_v2.png` 与 `boombox_thumb.png`（建议设为 `1080x1080`）；保存 `ib10_delivery.blend` |
| IB-11 | `model_corset.glb` + `hdri/hdri_aerodynamics_workshop_1k.exr` + `check_world.py` + `check_material.py` + `check_render.py` | P1 `agent_asks`, P2/P3 `agent_done` | `check_blender_world_hdri`, `check_blender_material_pbr`, `check_blender_render_output`, `check_blender_render_settings` | 输出 `corset_lookdev.png`；材质规则可约束 `metallic/roughness`；保存 `corset_lookdev.blend` |
| IB-12 | `polyhaven_armchair_01/ArmChair_01_1k.blend` + 3 张 armchair textures + `check_render.py` | 三阶段 `agent_done` | `check_blender_render_output`, `check_blender_render_output`, `check_blender_render_settings` | 检查 `armchair_catalog.png` + `armchair_mood.png`；保存 `armchair_delivery.blend` |
| IB-13 | `simple_scene.blend` + `texture_coast_sand_rocks_02_{diff,nor_gl,rough}_1k.jpg` + `check_material.py` + `check_render.py` | P1 `step_count:3`, P2 `agent_done` | `check_blender_material_textures`, `check_blender_render_output`, `check_blender_render_settings` | 在 `Plane` 上校验三贴图连接（`Base Color/Normal/Roughness`）；输出 `scene_ground_final.png`；保存 `ib13_delivery.blend` |
| IB-14 | `model_lantern.glb` + 双 HDRI + `check_world.py` + `check_render.py` | 三阶段 `agent_done` | `check_blender_world_hdri`, `check_blender_render_output`, `check_blender_render_output`, `check_blender_render_output`, `check_blender_render_settings` | 检查 `lantern_day.png`、`lantern_night.png`、`lantern_compare.png`；最终 HDRI 可约束为夜间版；保存 `ib14_delivery.blend` |

#### 3.6.4 `phases` 字段可复制片段

`step_count + agent_done` 模式（IB-08/09/13）：

```json
"phases": [
  {
    "phase_id": 1,
    "instruction": "<先做初版>",
    "trigger": {"type": "step_count", "value": 3}
  },
  {
    "phase_id": 2,
    "instruction": "<追加/变更需求>",
    "trigger": {"type": "agent_done"}
  },
  {
    "phase_id": 3,
    "instruction": "<保存工程或补导出>",
    "trigger": {"type": "agent_done"}
  }
]
```

`agent_asks` 模式（IB-11）：

```json
"phases": [
  {
    "phase_id": 1,
    "instruction": "这个服饰效果不够高级，帮我调一下。",
    "trigger": {"type": "agent_asks"}
  },
  {
    "phase_id": 2,
    "instruction": "我想要偏冷色、丝绸感更明显、保留细节阴影，输出 /home/user/Documents/corset_lookdev.png。",
    "trigger": {"type": "agent_done"}
  },
  {
    "phase_id": 3,
    "instruction": "保存工程到 /home/user/Documents/corset_lookdev.blend。",
    "trigger": {"type": "agent_done"}
  }
]
```

#### 3.6.5 评估器落地注意事项（字段级）

1. 对“中间产物也要存在”的任务，不要只检查最终图；把中间图（如 `preview`、`v1`）也作为独立 `vm_file` + `check_blender_render_output`。
2. 对“工程必须保存”的要求，建议把保存路径写成新文件（如 `ib08_delivery.blend`），并用 `check_blender_render_settings` + `vm_command_line` 在该路径上执行 `check_render.py`。
3. `check_blender_material_textures` 的 `connected_to` 要与节点目标一致（推荐用 `Base Color`、`Normal`、`Roughness`）。
4. `step_count` 在当前 phase 内计数，phase 切换后重置；阈值应按单阶段复杂度设置。
5. `agent_asks` 任务中，phase-1 指令要刻意模糊，phase-2 给出可执行参数，这样能稳定触发并评估澄清能力。


## 4. 检查脚本模板

每个评估任务需要上传一个 Python 检查脚本到 VM。以下是各检查脚本的模板：

### 4.1 通用物体检查脚本 (`check_object.py`)

```python
import bpy
import json
import sys

result = {}

# List all objects
objects = []
for obj in bpy.data.objects:
    objects.append({
        "name": obj.name,
        "type": obj.type,
        "location": list(obj.location),
        "scale": list(obj.scale),
        "rotation_euler": [round(r * 180 / 3.14159265, 2) for r in obj.rotation_euler],
        "hide_viewport": obj.hide_viewport,
        "hide_render": obj.hide_render,
        "parent": obj.parent.name if obj.parent else None,
    })

result["objects"] = objects
result["object_count"] = len(objects)
result["object_names"] = [o["name"] for o in objects]

print(f"RESULT:{json.dumps(result)}")
```

### 4.2 材质检查脚本 (`check_material.py`)

```python
import bpy
import json

result = {}

for obj in bpy.data.objects:
    if obj.type == 'MESH' and obj.data.materials:
        for mat in obj.data.materials:
            if mat and mat.use_nodes:
                for node in mat.node_tree.nodes:
                    if node.type == 'BSDF_PRINCIPLED':
                        base_color = node.inputs['Base Color'].default_value
                        result[obj.name] = {
                            "material_name": mat.name,
                            "base_color": list(base_color),
                            "metallic": node.inputs['Metallic'].default_value,
                            "roughness": node.inputs['Roughness'].default_value,
                            "alpha": node.inputs['Alpha'].default_value,
                        }
                        # Check for image texture connected to Base Color
                        for link in mat.node_tree.links:
                            if link.to_node == node and link.to_socket.name == 'Base Color':
                                if link.from_node.type == 'TEX_IMAGE' and link.from_node.image:
                                    result[obj.name]["texture"] = link.from_node.image.filepath

print(f"RESULT:{json.dumps(result)}")
```

### 4.3 修改器检查脚本 (`check_modifier.py`)

```python
import bpy
import json

result = {}

for obj in bpy.data.objects:
    if obj.modifiers:
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
            elif mod.type == 'ARRAY':
                mod_info["count"] = mod.count
            elif mod.type == 'BEVEL':
                mod_info["width"] = mod.width
                mod_info["segments"] = mod.segments
            mods.append(mod_info)
        result[obj.name] = mods

print(f"RESULT:{json.dumps(result)}")
```

### 4.4 渲染设置检查脚本 (`check_render.py`)

```python
import bpy
import json

scene = bpy.context.scene
result = {
    "engine": scene.render.engine,
    "resolution_x": scene.render.resolution_x,
    "resolution_y": scene.render.resolution_y,
    "fps": scene.render.fps,
    "frame_start": scene.frame_start,
    "frame_end": scene.frame_end,
    "film_transparent": scene.render.film_transparent,
    "image_format": scene.render.image_settings.file_format,
}

if scene.render.engine == 'CYCLES':
    result["samples"] = scene.cycles.samples
elif scene.render.engine == 'BLENDER_EEVEE':
    result["samples"] = scene.eevee.taa_render_samples

print(f"RESULT:{json.dumps(result)}")
```

### 4.5 动画检查脚本 (`check_animation.py`)

```python
import bpy
import json

result = {}

for obj in bpy.data.objects:
    if obj.animation_data and obj.animation_data.action:
        action = obj.animation_data.action
        keyframes = {}
        for fcurve in action.fcurves:
            path = fcurve.data_path
            idx = fcurve.array_index
            kf_list = [(kf.co[0], kf.co[1]) for kf in fcurve.keyframe_points]
            keyframes[f"{path}[{idx}]"] = kf_list
        result[obj.name] = {
            "action_name": action.name,
            "keyframe_count": sum(len(v) for v in keyframes.values()),
            "keyframes": keyframes,
            "frame_range": list(action.frame_range),
        }

print(f"RESULT:{json.dumps(result)}")
```

### 4.6 世界环境检查脚本 (`check_world.py`)

```python
import bpy
import json

result = {"has_hdri": False}

world = bpy.context.scene.world
if world and world.use_nodes:
    for node in world.node_tree.nodes:
        if node.type == 'TEX_ENVIRONMENT' and node.image:
            result["has_hdri"] = True
            result["hdri_filepath"] = node.image.filepath
            result["hdri_name"] = node.image.name

print(f"RESULT:{json.dumps(result)}")
```

### 4.7 集合检查脚本 (`check_collection.py`)

```python
import bpy
import json

result = {
    "collections": [],
    "object_collections": {}
}

for coll in bpy.data.collections:
    result["collections"].append({
        "name": coll.name,
        "objects": [obj.name for obj in coll.objects],
    })

for obj in bpy.data.objects:
    colls = [c.name for c in obj.users_collection]
    result["object_collections"][obj.name] = colls

print(f"RESULT:{json.dumps(result)}")
```

### 4.8 粒子系统检查脚本 (`check_particles.py`)

```python
import bpy
import json

result = {}

for obj in bpy.data.objects:
    if obj.particle_systems:
        particles = []
        for ps in obj.particle_systems:
            particles.append({
                "name": ps.name,
                "type": ps.settings.type,  # 'EMITTER' or 'HAIR'
                "count": ps.settings.count,
            })
        result[obj.name] = particles

print(f"RESULT:{json.dumps(result)}")
```

### 4.9 约束检查脚本 (`check_constraints.py`)

```python
import bpy
import json

result = {}

for obj in bpy.data.objects:
    if obj.constraints:
        constraints = []
        for con in obj.constraints:
            con_info = {"name": con.name, "type": con.type}
            if hasattr(con, 'target') and con.target:
                con_info["target"] = con.target.name
            constraints.append(con_info)
        result[obj.name] = constraints

print(f"RESULT:{json.dumps(result)}")
```

### 4.10 网格数据检查脚本 (`check_mesh.py`)

```python
import bpy
import json

result = {}

for obj in bpy.data.objects:
    if obj.type == 'MESH':
        mesh = obj.data
        result[obj.name] = {
            "vertex_count": len(mesh.vertices),
            "edge_count": len(mesh.edges),
            "polygon_count": len(mesh.polygons),
            "has_smooth": any(p.use_smooth for p in mesh.polygons),
        }

print(f"RESULT:{json.dumps(result)}")
```

### 4.11 文本物体检查脚本 (`check_text.py`)

```python
import bpy
import json

result = {}

for obj in bpy.data.objects:
    if obj.type == 'FONT':
        result[obj.name] = {
            "body": obj.data.body,
            "font_size": obj.data.size,
            "align_x": obj.data.align_x,
        }

print(f"RESULT:{json.dumps(result)}")
```

---

## 5. 需要新建的评估函数汇总

| # | Function Name | Description | Estimated Complexity |
|---|--------------|-------------|---------------------|
| 1 | `check_blender_object_exists` | 检查指定物体是否存在 | 低 |
| 2 | `check_blender_object_deleted` | 检查指定物体是否已删除 | 低 |
| 3 | `check_blender_object_count` | 检查物体数量 | 低 |
| 4 | `check_blender_object_location` | 检查物体位置 | 低 |
| 5 | `check_blender_object_scale` | 检查物体缩放 | 低 |
| 6 | `check_blender_object_rotation` | 检查物体旋转 | 低 |
| 7 | `check_blender_object_renamed` | 检查物体重命名 | 低 |
| 8 | `check_blender_object_visibility` | 检查物体可见性 | 低 |
| 9 | `check_blender_render_settings` | 检查渲染引擎/分辨率/采样/帧率 | 中 |
| 10 | `check_blender_light_type` | 检查灯光类型和参数 | 低 |
| 11 | `check_blender_collection_exists` | 检查集合是否存在 | 低 |
| 12 | `check_blender_object_in_collection` | 检查物体在指定集合中 | 低 |
| 13 | `check_blender_animation_range` | 检查动画帧范围 | 低 |
| 14 | `check_blender_text_content` | 检查文本物体内容 | 低 |
| 15 | `check_blender_material_color` | 检查材质颜色 | 中 |
| 16 | `check_blender_material_property` | 检查材质属性（金属/粗糙度/透明） | 中 |
| 17 | `check_blender_modifier_exists` | 检查修改器是否存在 | 低 |
| 18 | `check_blender_modifier_param` | 检查修改器参数 | 中 |
| 19 | `check_blender_parent_child` | 检查父子关系 | 低 |
| 20 | `check_blender_texture_assigned` | 检查图片纹理分配 | 中 |
| 21 | `check_blender_world_hdri` | 检查世界环境 HDRI | 中 |
| 22 | `check_blender_keyframe_exists` | 检查关键帧动画 | 中 |
| 23 | `check_blender_vertex_count` | 检查网格顶点数 | 低 |
| 24 | `check_blender_particle_system` | 检查粒子系统 | 中 |
| 25 | `check_blender_constraint_exists` | 检查约束 | 低 |
| 26 | `check_blender_smooth_shading` | 检查平滑着色 | 低 |
| 27 | `check_blender_render_output` | 检查渲染图片输出 | 中 |
| 28 | `check_blender_render_video` | 检查渲染视频输出 | 中 |

**总计**: 28 个评估函数，覆盖 35 个任务（15 L1 + 10 L2 + 10 L3）

---

## 6. 素材生成脚本

```python
#!/usr/bin/env python3
"""generate_blend_assets.py - Generate Blender asset files for OSWorld tasks."""

import subprocess
import os

ASSET_DIR = "assets/blender"
os.makedirs(ASSET_DIR, exist_ok=True)

# 1. default_cube.blend - Blender default scene
script_default = '''
import bpy
bpy.ops.wm.save_as_mainfile(filepath="{output}")
'''

# 2. simple_scene.blend - Scene with multiple basic objects
script_simple = '''
import bpy
# Clear default
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Add objects
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
bpy.context.active_object.name = "Cube"

bpy.ops.mesh.primitive_uv_sphere_add(location=(3, 0, 0))
bpy.context.active_object.name = "Sphere"

bpy.ops.mesh.primitive_cylinder_add(location=(-3, 0, 0))
bpy.context.active_object.name = "Cylinder"

bpy.ops.mesh.primitive_plane_add(location=(0, 0, -1), scale=(5, 5, 1))
bpy.context.active_object.name = "Plane"

bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 2))
bpy.context.active_object.name = "Empty"

# Add camera and light
bpy.ops.object.camera_add(location=(7, -7, 5))
cam = bpy.context.active_object
cam.name = "Camera"
bpy.context.scene.camera = cam

bpy.ops.object.light_add(type='POINT', location=(4, 1, 6))
bpy.context.active_object.name = "Light"

bpy.ops.wm.save_as_mainfile(filepath="{output}")
'''

# 3. animated_ball.blend - Ball with keyframe animation
script_animated = '''
import bpy
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

bpy.ops.mesh.primitive_uv_sphere_add(location=(0, 0, 0))
ball = bpy.context.active_object
ball.name = "Ball"

# Keyframe at frame 1
bpy.context.scene.frame_set(1)
ball.location = (0, 0, 0)
ball.keyframe_insert(data_path="location", frame=1)

# Keyframe at frame 60
ball.location = (5, 0, 3)
ball.keyframe_insert(data_path="location", frame=60)

bpy.context.scene.frame_end = 60

# Add camera
bpy.ops.object.camera_add(location=(7, -7, 5))
bpy.context.scene.camera = bpy.context.active_object

bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))

bpy.ops.wm.save_as_mainfile(filepath="{output}")
'''

# 4. textured_cube.blend - Cube with a basic material (no texture yet)
script_textured = '''
import bpy
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
cube = bpy.context.active_object
cube.name = "Cube"

mat = bpy.data.materials.new(name="CubeMaterial")
mat.use_nodes = True
cube.data.materials.append(mat)

bpy.ops.object.camera_add(location=(5, -5, 4))
bpy.context.scene.camera = bpy.context.active_object
bpy.ops.object.light_add(type='POINT', location=(3, -3, 5))

bpy.ops.wm.save_as_mainfile(filepath="{output}")
'''

# 5. cube_with_subsurf.blend - Cube with Subdivision Surface modifier
script_subsurf = '''
import bpy
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
cube = bpy.context.active_object
cube.name = "Cube"

mod = cube.modifiers.new(name="Subdivision", type='SUBSURF')
mod.levels = 2
mod.render_levels = 2

bpy.ops.object.camera_add(location=(5, -5, 4))
bpy.context.scene.camera = bpy.context.active_object
bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))

bpy.ops.wm.save_as_mainfile(filepath="{output}")
'''

# 6. text_scene.blend - Scene with a Text object
script_text = '''
import bpy
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

bpy.ops.object.text_add(location=(0, 0, 0))
text_obj = bpy.context.active_object
text_obj.name = "Text"
text_obj.data.body = "Text"

bpy.ops.object.camera_add(location=(5, -5, 4))
bpy.context.scene.camera = bpy.context.active_object
bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))

bpy.ops.wm.save_as_mainfile(filepath="{output}")
'''

# 7. simple_scene_with_collection.blend
script_collection = '''
import bpy

# Keep default objects
# Create a "Props" collection
props_coll = bpy.data.collections.new("Props")
bpy.context.scene.collection.children.link(props_coll)

bpy.ops.wm.save_as_mainfile(filepath="{output}")
'''

assets = {
    "default_cube.blend": script_default,
    "simple_scene.blend": script_simple,
    "animated_ball.blend": script_animated,
    "textured_cube.blend": script_textured,
    "cube_with_subsurf.blend": script_subsurf,
    "text_scene.blend": script_text,
    "simple_scene_with_collection.blend": script_collection,
}

for filename, script in assets.items():
    output_path = os.path.abspath(os.path.join(ASSET_DIR, filename))
    script_filled = script.format(output=output_path)
    tmp_script = "/tmp/gen_blend.py"
    with open(tmp_script, "w") as f:
        f.write(script_filled)

    print(f"Generating {filename}...")
    subprocess.run([
        "blender", "--background", "--python", tmp_script
    ], capture_output=True)
    print(f"  -> {output_path}")

print("\nDone! Generated all .blend assets.")
print("\nNext steps:")
print("1. Download textures from Poly Haven (CC0):")
print("   wget https://dl.polyhaven.org/file/ph-assets/Textures/jpg/1k/wood_table/wood_table_diff_1k.jpg -O assets/blender/texture_wood.jpg")
print("   wget https://dl.polyhaven.org/file/ph-assets/HDRIs/exr/1k/studio_small_09_1k.exr -O assets/blender/hdri_studio.exr")
```

---

## 7. Task JSON 模板

### 基于 `vm_command_line` 的任务（大部分任务）

```json
{
  "id": "<uuid4>",
  "snapshot": "blender",
  "instruction": "Open the Blender project /home/user/Documents/scene.blend. <操作描述>, then save the file.",
  "source": "",
  "config": [
    {
      "type": "upload_file",
      "parameters": {
        "files": [
          {
            "local_path": "assets/blender/default_cube.blend",
            "path": "/home/user/Documents/scene.blend"
          },
          {
            "local_path": "assets/blender/check_object.py",
            "path": "/tmp/check_object.py"
          }
        ]
      }
    },
    {
      "type": "launch",
      "parameters": {
        "command": ["/snap/bin/blender", "/home/user/Documents/scene.blend"]
      }
    },
    {
      "type": "sleep",
      "parameters": {
        "seconds": 5
      }
    }
  ],
  "trajectory": "trajectories/",
  "related_apps": ["blender"],
  "evaluator": {
    "postconfig": [
      {
        "type": "sleep",
        "parameters": {"seconds": 2}
      }
    ],
    "func": "check_blender_object_exists",
    "result": {
      "type": "vm_command_line",
      "command": "/snap/bin/blender --background /home/user/Documents/scene.blend --python /tmp/check_object.py 2>/dev/null | grep '^RESULT:' | sed 's/^RESULT://'",
      "shell": true
    },
    "expected": {
      "type": "rule",
      "rules": {
        "object_type": "MESH",
        "name_contains": "Sphere"
      }
    }
  },
  "proxy": false,
  "fixed_ip": false,
  "possibility_of_env_change": "low"
}
```

### 基于 `vm_file` 的渲染输出任务

```json
{
  "id": "<uuid4>",
  "snapshot": "blender",
  "instruction": "Open the Blender project /home/user/Documents/scene.blend. Render the scene and save to /home/user/Documents/render.png, then save the project file.",
  "source": "",
  "config": [
    {
      "type": "upload_file",
      "parameters": {
        "files": [
          {
            "local_path": "assets/blender/default_cube.blend",
            "path": "/home/user/Documents/scene.blend"
          }
        ]
      }
    },
    {
      "type": "launch",
      "parameters": {
        "command": ["/snap/bin/blender", "/home/user/Documents/scene.blend"]
      }
    },
    {
      "type": "sleep",
      "parameters": {
        "seconds": 5
      }
    }
  ],
  "trajectory": "trajectories/",
  "related_apps": ["blender"],
  "evaluator": {
    "postconfig": [],
    "func": "check_blender_render_output",
    "result": {
      "type": "vm_file",
      "path": "/home/user/Documents/render.png",
      "dest": "render.png"
    },
    "expected": {
      "type": "rule",
      "rules": {
        "width": 1920,
        "height": 1080,
        "format": "PNG"
      }
    }
  },
  "proxy": false,
  "fixed_ip": false,
  "possibility_of_env_change": "low"
}
```

---

## 8. Docker 镜像要求

VM/Docker 镜像需要预装：

- **Blender 3.6 LTS** 或 **Blender 4.x**（推荐 4.0+）
  ```bash
  apt-get install blender
  # 或从官网下载：https://www.blender.org/download/
  ```
- **ffprobe**（用于视频渲染输出检查）
  ```bash
  apt-get install ffmpeg
  ```
- **Python 3**（Blender 自带嵌入式 Python）

验证安装：
```bash
/snap/bin/blender --version
/snap/bin/blender --background --python-expr "import bpy; print(bpy.app.version_string)"
```

---

## 9. 任务难度分布总结

| Level | Count | 平均步骤 | Description | Examples |
|-------|-------|---------|-------------|---------|
| L1 | 15 | 1 步 | 单步原子操作 | 添加/删除物体、移动/缩放/旋转、设置渲染参数、修改文本 |
| L2 | 10 | 3-5 步 | 多步复合操作 | PBR 材质+调参、布尔+隐藏、修改器堆叠、动画+帧范围、纹理+法线贴图、集合组织+父子层级 |
| L3 | 10 | 8-15 步 | 复杂工作流 | 完整渲染流程(材质+HDRI+Cycles)、场景搭建+材质+动画、布尔+修改器+材质组合 |
| **Total** | **35** | | | |

> 另有 40 个备用任务存储在 [`blender_task_backup.md`](blender_task_backup.md) 中。

### 可验证性保证

所有任务的验证都基于以下两种可靠机制：

1. **Blender Python API (`bpy`)**: 通过 `/snap/bin/blender --background --python` 读取 `.blend` 文件的完整内部状态，包括物体属性、材质节点树、修改器参数、动画数据等。**这是最可靠的验证方式**，因为它直接访问 Blender 的内部数据结构。

2. **文件分析工具 (`PIL`/`ffprobe`)**: 对渲染输出的图片/视频进行格式、分辨率、时长等客观检查。

**不依赖**截图对比、OCR 或其他不可靠的视觉检查方法。

---
