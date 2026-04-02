# External Blender Assets (Expanded Real-world Pool)

This folder contains additional public assets downloaded for more diverse, realistic Blender task design.
All selected assets are from permissive sources (primarily CC0).

## 1) glTF Sample Models (Khronos, CC0)
Source repo: https://github.com/KhronosGroup/glTF-Sample-Models

| File | License | Suggested Scenarios |
|---|---|---|
| `model_avocado.glb` | CC0 | 食品产品打光、近景构图、广告静帧 |
| `model_waterbottle.glb` | CC0 | 包装产品旋转展示、折射/高光控制 |
| `model_lantern.glb` | CC0 | 室内静物渲染、金属与玻璃材质对比 |
| `model_boombox.glb` | CC0 | 消费电子产品主视觉、反光材质调优 |
| `model_corset.glb` | CC0 | 服饰软材质、布料粗糙度与法线细节 |

## 2) Poly Haven Model Packs (CC0)
Source site/API: https://polyhaven.com/

### ArmChair_01 (vintage furniture)
- Blend scene:
  - `polyhaven_armchair_01/ArmChair_01_1k.blend`
- Textures:
  - `polyhaven_armchair_01/textures/Armchair_01_diff_1k.jpg`
  - `polyhaven_armchair_01/textures/Armchair_01_nor_gl_1k.jpg`
  - `polyhaven_armchair_01/textures/Armchair_01_arm_1k.jpg`
- Suggested scenarios: 室内家具布景、材质替换、镜头景深练习

### BarberShopChair_01 (salon prop)
- Blend scene:
  - `polyhaven_barbershop_chair_01/BarberShopChair_01_1k.blend`
- Textures:
  - `polyhaven_barbershop_chair_01/textures/BarberShopChair_01_diff_1k.jpg`
  - `polyhaven_barbershop_chair_01/textures/BarberShopChair_01_nor_gl_1k.jpg`
  - `polyhaven_barbershop_chair_01/textures/BarberShopChair_01_arm_1k.jpg`
- Suggested scenarios: 复古商业空间渲染、材质节点调参与布光

## 3) Additional HDRI Lighting (Poly Haven, CC0)

| File | Source Asset | Suggested Scenarios |
|---|---|---|
| `hdri_kloppenheim_06_puresky_1k.exr` | `kloppenheim_06_puresky` | 户外自然光场景、低对比产品图 |
| `hdri/hdri_aerodynamics_workshop_1k.exr` | `aerodynamics_workshop` | 工业室内布光、金属表面细节测试 |

## 4) Additional PBR Texture Set (Poly Haven, CC0)

| File | Source Asset | Suggested Scenarios |
|---|---|---|
| `textures/texture_coast_sand_rocks_02_diff_1k.jpg` | `coast_sand_rocks_02` | 地表/背景贴图 |
| `textures/texture_coast_sand_rocks_02_nor_gl_1k.jpg` | `coast_sand_rocks_02` | 法线细节增强 |
| `textures/texture_coast_sand_rocks_02_rough_1k.jpg` | `coast_sand_rocks_02` | 粗糙度控制 |

## Notes

- Some Poly Haven downloads had intermittent TLS issues; downloads were completed with retry + `--http1.1`.
- Naming intentionally follows task-oriented conventions to simplify future `upload_file` paths.
