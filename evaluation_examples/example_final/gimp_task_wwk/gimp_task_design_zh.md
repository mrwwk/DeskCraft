# GIMP 任务设计文档（中文草稿，独立版）

> 说明：本草稿按你的要求，**忽视原有 GIMP 任务**，按“从零规划”方式设计。

## 0. 设计目标与边界

### 0.1 目标

为 `gimp_task` 建立一套有层次的任务规划，满足：

1. 多样化：覆盖日常高频图像编辑场景。
2. 可验证：每类任务有明确、可自动评测的输出标准。
3. 分层清晰：L1/L2/L3 难度与操作复杂度逐级提升。
4. 可扩展：后续能稳定扩充任务数量，而不破坏评测一致性。

### 0.2 边界

1. 本文不沿用历史任务 ID、历史任务描述、历史案例来源。
2. 采用全新命名、全新场景池、全新任务模板。
3. 当前为第一版草稿，优先保证结构完整与落地可行。

---

## 1. 任务分层定义

### 1.1 L1（原子任务）

- 目标：单一操作目标，1-2 个关键动作可完成。
- 核心能力：几何变换、色彩基础、格式导出、图层基础。
- 建议步骤数：2-5 步。

### 1.2 L2（复合任务）

- 目标：围绕一个真实业务场景，串联 4-6 个编辑动作并满足交付规格。
- 核心能力：多步骤流程编排、图层组织、局部处理、格式与体积双约束。
- 建议步骤数：8-14 步。

### 1.3 L3（工作流任务）

- 目标：完整交付流程，要求“可交付成品 + 可返工工程文件”。
- 核心能力：多图层组织、局部调色、版式设计、多格式导出。
- 建议步骤数：12-25 步。

---

## 2. 场景覆盖规划

### 2.1 常用场景池

1. 电商商品图：抠图、白底/透明、尺寸统一、压缩导出。
2. 社交媒体配图：封面比例、标题文字、风格化调色。
3. 海报设计：主视觉、层级文字、边框/装饰、规范导出。
4. 头像与证件照：裁剪、背景、尺寸与比例约束。
5. 品牌素材：Logo 简化、配色统一、图标导出。
6. 图层工程管理：图层命名、顺序、可见性、透明度。
7. 图像修复基础：亮度对比、降噪、颜色纠偏。
8. 教学/说明图：高亮标注、箭头、文本注释。

### 2.2 覆盖矩阵（草稿）

| 能力域 | L1 | L2 | L3 |
|---|---|---|---|
| 几何变换（裁剪/缩放/旋转） | ✅ | ✅ | ✅ |
| 色彩调整（亮度/对比/饱和） | ✅ | ✅ | ✅ |
| 背景处理（透明/替换） | ✅ | ✅ | ✅ |
| 文本与排版 | ✅ | ✅ | ✅ |
| 图层工程管理 | ✅ | ✅ | ✅ |
| 规范导出（格式/尺寸/体积） | ✅ | ✅ | ✅ |
| 多产物交付（PNG+JPG+XCF） |  | ✅ | ✅ |
| 整体视觉一致性 |  | ✅ | ✅ |

---

## 3. 资源规划（已完成首批采集）

素材目录：`assets/gimp_task/`

### 3.1 目录结构（当前）

1. `assets/gimp_task/photos/`：通用照片素材（风景、人像、城市、宠物、美食等）
2. `assets/gimp_task/products/`：电商产品素材（手表、鞋、香水、耳机、瓶装、相机）
3. `assets/gimp_task/texture/`：材质纹理（木纹、混凝土、纸张、金属）
4. `assets/gimp_task/graphic/`：图形素材（透明通道示例、无缝纹理、SVG 图标）
5. `assets/gimp_task/mask/`：合成与遮罩辅助素材

### 3.2 素材清单与来源链接（首批 28 个）

| 文件 | 类型 | 分辨率 | 大小（字节） | 来源链接 |
|---|---|---|---:|---|
| `photos/landscape_mountain_1108099.jpg` | JPEG | 2200x1650 | 230729 | https://images.pexels.com/photos/1108099/pexels-photo-1108099.jpeg?auto=compress&cs=tinysrgb&w=2200 |
| `photos/portrait_woman_774909.jpg` | JPEG | 1800x2700 | 360364 | https://images.pexels.com/photos/774909/pexels-photo-774909.jpeg?auto=compress&cs=tinysrgb&w=1800 |
| `photos/street_city_466685.jpg` | JPEG | 2200x1365 | 570106 | https://images.pexels.com/photos/466685/pexels-photo-466685.jpeg?auto=compress&cs=tinysrgb&w=2200 |
| `photos/pet_dog_1108099_alt.jpg` | JPEG | 2000x3000 | 282228 | https://images.pexels.com/photos/1805164/pexels-photo-1805164.jpeg?auto=compress&cs=tinysrgb&w=2000 |
| `photos/food_plate_1640777.jpg` | JPEG | 1800x1200 | 347525 | https://images.pexels.com/photos/1640777/pexels-photo-1640777.jpeg?auto=compress&cs=tinysrgb&w=1800 |
| `photos/architecture_247431.jpg` | JPEG | 2200x1501 | 392749 | https://images.pexels.com/photos/247431/pexels-photo-247431.jpeg?auto=compress&cs=tinysrgb&w=2200 |
| `photos/nature_forest_1103970.jpg` | JPEG | 2200x1467 | 56398 | https://images.pexels.com/photos/1103970/pexels-photo-1103970.jpeg?auto=compress&cs=tinysrgb&w=2200 |
| `photos/beach_people_1481105.jpg` | JPEG | 2200x2364 | 820702 | https://images.pexels.com/photos/1481105/pexels-photo-1481105.jpeg?auto=compress&cs=tinysrgb&w=2200 |
| `products/product_watch_190819.jpg` | JPEG | 2000x1330 | 205664 | https://images.pexels.com/photos/190819/pexels-photo-190819.jpeg?auto=compress&cs=tinysrgb&w=2000 |
| `products/product_shoes_2529148.jpg` | JPEG | 2000x2500 | 196232 | https://images.pexels.com/photos/2529148/pexels-photo-2529148.jpeg?auto=compress&cs=tinysrgb&w=2000 |
| `products/product_perfume_965989.jpg` | JPEG | 2000x1333 | 284529 | https://images.pexels.com/photos/965989/pexels-photo-965989.jpeg?auto=compress&cs=tinysrgb&w=2000 |
| `products/product_headphone_3394650.jpg` | JPEG | 2000x2000 | 62181 | https://images.pexels.com/photos/3394650/pexels-photo-3394650.jpeg?auto=compress&cs=tinysrgb&w=2000 |
| `products/product_bottle_4021779.jpg` | JPEG | 2000x1333 | 200552 | https://images.pexels.com/photos/4021779/pexels-photo-4021779.jpeg?auto=compress&cs=tinysrgb&w=2000 |
| `products/product_camera_90946.jpg` | JPEG | 2000x1325 | 103601 | https://images.pexels.com/photos/90946/pexels-photo-90946.jpeg?auto=compress&cs=tinysrgb&w=2000 |
| `texture/texture_wood_172289.jpg` | JPEG | 1800x1198 | 602698 | https://images.pexels.com/photos/172289/pexels-photo-172289.jpeg?auto=compress&cs=tinysrgb&w=1800 |
| `texture/texture_concrete_129733.jpg` | JPEG | 1800x1800 | 542417 | https://images.pexels.com/photos/129733/pexels-photo-129733.jpeg?auto=compress&cs=tinysrgb&w=1800 |
| `texture/texture_paper_723311.jpg` | JPEG | 1800x1800 | 354230 | https://images.pexels.com/photos/129731/pexels-photo-129731.jpeg?auto=compress&cs=tinysrgb&w=1800 |
| `texture/texture_metal_220182.jpg` | JPEG | 1800x1350 | 565317 | https://images.pexels.com/photos/220182/pexels-photo-220182.jpeg?auto=compress&cs=tinysrgb&w=1800 |
| `graphic/wikimedia_transparency_demo.png` | PNG | 800x600 | 224566 | https://upload.wikimedia.org/wikipedia/commons/4/47/PNG_transparency_demonstration_1.png |
| `graphic/pattern_asfalt_light.png` | PNG | 466x349 | 20845 | https://www.transparenttextures.com/patterns/asfalt-light.png |
| `graphic/pattern_subtle_white_feathers.png` | PNG | 500x333 | 177395 | https://www.transparenttextures.com/patterns/subtle-white-feathers.png |
| `graphic/pattern_brushed_alum_dark.png` | PNG | 400x400 | 90258 | https://www.transparenttextures.com/patterns/brushed-alum-dark.png |
| `graphic/icon_home.svg` | SVG | - | 173 | https://raw.githubusercontent.com/google/material-design-icons/master/src/action/home/materialicons/24px.svg |
| `graphic/icon_search.svg` | SVG | - | 372 | https://raw.githubusercontent.com/google/material-design-icons/master/src/action/search/materialicons/24px.svg |
| `graphic/icon_favorite.svg` | SVG | - | 312 | https://raw.githubusercontent.com/google/material-design-icons/master/src/action/favorite/materialicons/24px.svg |
| `graphic/icon_camera.svg` | SVG | - | 324 | https://raw.githubusercontent.com/google/material-design-icons/master/src/image/photo_camera/materialicons/24px.svg |
| `mask/abstract_shape_1.png` | PNG | 1600x1067 | 93120 | https://images.pexels.com/photos/7135004/pexels-photo-7135004.jpeg?auto=compress&cs=tinysrgb&w=1600 |
| `mask/abstract_shape_2.png` | PNG | 1600x1054 | 1621934 | https://images.pexels.com/photos/1183099/pexels-photo-1183099.jpeg?auto=compress&cs=tinysrgb&w=1600 |

### 3.3 多样性说明

本批素材覆盖以下任务方向：

1. 人像/宠物修图：`photos/portrait_*`, `photos/pet_*`
2. 风景与城市调色：`photos/landscape_*`, `photos/street_*`, `photos/beach_*`
3. 电商抠图与规格化：`products/*`
4. 纹理贴图与背景合成：`texture/*`, `graphic/pattern_*`
5. 透明与遮罩操作：`graphic/wikimedia_transparency_demo.png`, `mask/*`
6. 图标/矢量叠加：`graphic/icon_*.svg`

### 3.4 使用约束（建议）

1. 素材来源主要为 Pexels、Wikimedia Commons、Transparent Textures、Google Material Icons。
2. 具体商用/再分发限制需按各来源站点条款执行。
3. 任务数据集发布前，建议统一做一次 license 复核与清单补充。

---

## 4. 评测器规划（基于现有代码）

### 4.1 评测执行逻辑（先统一约束）

根据 `desktop_env/desktop_env.py` 当前实现，GIMP 任务评测需要遵守以下规则：

1. `evaluator.func` 可以是字符串（单评测器）或数组（多评测器）。
2. 当 `func` 是数组时，`result`、`expected`、`options` 必须等长，且用 `conj: and/or` 组合。
3. `result.type`/`expected.type` 会动态映射到 `get_<type>`，例如：`vm_file`、`cloud_file`、`rule`、`xcf_file`、`gimp_config_file`。
4. 评测函数必须在 `desktop_env/evaluators/metrics/__init__.py` 中导出，才能在 JSON 里通过 `func` 调用。
5. 建议 L1 优先使用单评测器；只有“格式 + 体积”这类双约束时再使用多评测器组合。

### 4.1.1 现有 gimp 任务启动方式（基于仓库盘点）

统计范围：`evaluation_examples/examples/gimp/*.json`（当前 31 个任务文件）。

1. `config.launch` 使用情况：`26/31`。
2. 启动命令形态全部为 `gimp`：
   - `[`gimp`]`：4 个（偏设置类任务）。
   - `[`gimp`, `/home/user/Desktop/<input>`]`：22 个（直接带输入文件打开）。
3. `config.download` 使用情况：`25/31`，常见模式是“先下载素材到 Desktop，再启动 GIMP”。
4. 直接带文件启动的输入类型分布：`.png` 12、`.xcf` 5、`.jpeg` 3、`.jpg` 1、`.raw` 1。
5. 无 `launch` 的 5 个任务多为非标准编辑流程（大多是 `infeasible` 或非 GUI 评估路径）。

样例文件（可直接参考）：

1. 标准“下载 + 启动单图”：`72f83cdc-bf76-4531-9a1b-eb893a13f8aa.json`。
2. 启动 XCF 工程：`d16c99dc-2a1e-46f2-b350-d97c86c85c15.json`。
3. 仅启动 GIMP（配置类）：`7b7617bd-57cc-468e-9c91-40c4ec2bcb3d.json`。

### 4.1.2 现有 postconfig 后处理方式（基于仓库盘点）

统计范围同上，`20/31` 任务包含 `evaluator.postconfig`。后处理步骤类型只有 3 种：`execute`（51 次）、`sleep`（50 次）、`activate_window`（3 次）。

主流模式 A：导出文件自动收尾（6-7 步）

1. （可选）`activate_window` 聚焦 GIMP 主窗口。
2. `execute` 调 `python3 -c`，用 `pyautogui.hotkey(["shift", "ctrl", "e"])` 打开 Export 对话框。
3. `sleep 0.5s`。
4. `execute` 输入输出文件名并回车。
5. `sleep 2s`。
6. `execute` 再按一次 `enter`，确认导出参数或覆盖弹窗。
7. `sleep 5s`，等待文件落盘供 evaluator 读取。

参考：`72f83cdc-bf76-4531-9a1b-eb893a13f8aa.json`、`d16c99dc-2a1e-46f2-b350-d97c86c85c15.json`。

主流模式 B：配置类任务收尾（2 步）

1. `execute` 调 `pyautogui.hotkey(["ctrl", "q"])` 退出 GIMP，确保 `gimprc` 落盘。
2. `sleep 0.5s`。

参考：`7b7617bd-57cc-468e-9c91-40c4ec2bcb3d.json`、`7767eef2-56a3-4cea-8c9f-48c070c7d65b.json`、`d52d6308-ec58-42b7-a2c9-de80e4837b2b.json`。

特例模式 C：行为日志类任务

1. `execute` 先 `Esc` 再 `Ctrl+Q`，处理退出场景。
2. `execute` 模拟方向键/回车确认。
3. evaluator 使用 `vm_command_line`（例如 `cat ~/.config/GIMP/2.10/action-history`）校验行为痕迹。

参考：`a746add2-cab0-4740-ac36-c3769d9bfb46.json`。

### 4.1.3 新任务编写建议（与现有 gimp 任务对齐）

1. 编辑类任务优先沿用“模式 A”收尾，保证导出路径和文件名可控。
2. 建议保留 `sleep` 步骤，降低导出窗口焦点竞争导致的偶发失败。
3. 配置类任务必须在评测前退出 GIMP，否则 `gimprc` 可能未及时写盘。
4. 若任务可能被其他窗口抢焦点，显式加入 `activate_window`。
5. 输出文件路径建议统一到 `/home/user/Desktop/`，并在 `result.path` 里固定文件名。

推荐模板（编辑导出类）：

```json
"postconfig": [
  {"type": "activate_window", "parameters": {"window_name": "GNU Image Manipulation Program"}},
  {"type": "execute", "parameters": {"command": ["python3", "-c", "import time, pyautogui; time.sleep(1); pyautogui.hotkey([\"shift\", \"ctrl\", \"e\"])"]}},
  {"type": "sleep", "parameters": {"seconds": 0.5}},
  {"type": "execute", "parameters": {"command": ["python3", "-c", "import time, pyautogui; time.sleep(1); pyautogui.hotkey([\"ctrl\", \"a\"]); pyautogui.write(\"output_filename\"); pyautogui.press([\"enter\"])"]}},
  {"type": "sleep", "parameters": {"seconds": 2}},
  {"type": "execute", "parameters": {"command": ["python3", "-c", "import pyautogui; pyautogui.press([\"enter\"])"]}},
  {"type": "sleep", "parameters": {"seconds": 5}}
]
```

说明：导出对话框通常会预填当前文件名。`pyautogui.write(...)` 之前必须先发送 `ctrl+a` 全选当前文件名，再输入目标完整文件名，例如 `rot90.png`、`pattern_export.jpg`。不要直接在现有文件名后追加内容，否则容易出现目标文件名被拼接到原文件名后，或导出格式与 evaluator 预期不一致。

推荐模板（配置类）：

```json
"postconfig": [
  {"type": "execute", "parameters": {"command": ["python3", "-c", "import time, pyautogui; time.sleep(1); pyautogui.hotkey([\"ctrl\", \"q\"])"]}},
  {"type": "sleep", "parameters": {"seconds": 0.5}}
]
```

### 4.2 可直接复用的 L1 评测器（已有）

| 评测器 | 适用目标 | result / expected | 状态 |
|---|---|---|---|
| `check_045bf3ff_rotate` | 顺时针旋转 90° | `vm_file` / `cloud_file` | 已有 |
| `check_image_mirror` | 水平镜像 | `vm_file` / `cloud_file` | 已有 |
| `check_8ea73f6f_resize_1920x1080` | 固定尺寸缩放到 1920x1080 | `vm_file` / `cloud_file` | 已有 |
| `check_b148e375_resize_50_percent` | 按比例缩放 50% | `vm_file` / `cloud_file` | 已有 |
| `check_brightness_decrease_30_percent` | 亮度下降约 30% | `vm_file` / `cloud_file` | 已有 |
| `check_contrast_increase` | 对比度提升（支持阈值参数） | `cloud_file` / `vm_file` + `options` | 已有 |
| `check_554785e9_saturation_increase_40` | 饱和度提升约 40% | `vm_file` / `cloud_file` | 已有 |
| `check_045bf3ff_grayscale` | 转灰度 | `vm_file` / `cloud_file` | 已有 |
| `check_jpeg_format` | JPEG 格式校验 | `vm_file` / 无 | 已有 |
| `check_png_format` | PNG 格式校验 | `vm_file` / 无 | 已有 |
| `check_white_to_alpha_transparency` | 白底转透明（含内容保留） | `vm_file` / `cloud_file` | 已有 |
| `check_transparency_exists` | 是否存在透明像素 | `vm_file` / 无 | 已有 |
| `check_045bf3ff_indexed_color` | 转索引色 256 色 | `vm_file` / `cloud_file` | 已有 |
| `check_image_dimensions` | 宽高约束（可容忍） | `vm_file` / 无（参数走 `options`） | 已有 |
| `check_image_file_size` | 文件大小阈值 | `vm_file` / `rule` | 已有 |
| `check_b148e375_new_layer_circle` | 新建指定图层名 | `xcf_file` / `rule` | 已有 |
| `check_b148e375_duplicate_rename_hide` | 复制重命名并隐藏原图层 | `xcf_file` / `rule` | 已有 |
| `check_d16c99dc_opacity_and_layer_order` | 图层透明度 + 置顶 | `xcf_file` / `rule` | 已有 |
| `check_xcf_file_exists_and_has_layers` | XCF 中图层名存在性 | `xcf_file` / `rule` | 已有 |
| `check_7b7617bd_recent_files` | GIMP 配置项 max-recent-files | `gimp_config_file` / `rule` | 已有 |
| `check_7b7617bd_undo_levels` | GIMP 配置项 undo-levels | `gimp_config_file` / `rule` | 已有 |

### 4.3 需要新建的通用 L1 评测器

| 评测器（建议名） | 用途 | result / expected | 状态 |
|---|---|---|---|
| `check_aspect_ratio` | 比例约束（如 1:1、4:3） | `vm_file` / `rule` | 需新建 |
| `check_crop_region_similarity_generic` | 指定区域裁剪正确性（支持 center/top-left） | `vm_file` / `cloud_file` + `options` | 需新建 |
| `check_webp_format` | WebP 格式导出校验 | `vm_file` / 无 | 需新建 |
| `check_transparent_ratio` | 透明像素占比阈值 | `vm_file` / `rule` | 需新建 |
| `check_indexed_palette_size` | 任意索引色数量（非固定 64/128/256） | `vm_file` / `rule` | 需新建 |
| `check_text_region_change` | 指定区域文字叠加变化（弱 OCR/几何约束） | `vm_file` / `rule` | 需新建 |
| `check_xcf_layer_count` | XCF 图层数量 | `xcf_file` / `rule` | 需新建 |
| `check_xcf_layer_order_generic` | 通用图层顺序校验 | `xcf_file` / `rule` | 需新建 |
| `check_xcf_layer_visibility_generic` | 通用图层显隐校验 | `xcf_file` / `rule` | 需新建 |

### 4.4 L1 复合评测组合（建议）

1. 导出规格任务：`check_jpeg_format` + `check_image_file_size`（`conj: and`）。
2. 透明背景任务：`check_white_to_alpha_transparency` + `check_transparency_exists`（`conj: and`）。
3. 尺寸规格任务：`check_image_dimensions` + `check_structure_sim_resized`（`conj: and`，用于避免“空白图通过”）。

---

## 5. L1 任务池（细化版，首批 16 个）


L1 任务统一约束：

1. 指令只描述核心编辑动作，不再包含“打开文件/导出文件”步骤。
2. 打开输入由预处理 `config` 完成；导出或退出由后处理 `postconfig` 完成。
3. 所有 L1 任务都明确绑定预处理和后处理模板，降低评测阶段偶发失败。
4. `result`/`expected` 字段命名遵循当前 OSWorld evaluator 规范。
5. 每个任务都绑定可追溯来源链接。

### 5.1 L1 config 模板（预处理 + 后处理）

#### 模板 P1：图片编辑任务预处理

适用任务：L1-1 ~ L1-15。

```json
"config": [
  {
    "type": "download",
    "parameters": {
      "files": [
        {"url": "<asset_url>", "path": "/home/user/Desktop/<input_file>"}
      ]
    }
  },
  {
    "type": "launch",
    "parameters": {
      "command": ["gimp", "/home/user/Desktop/<input_file>"]
    }
  }
]
```

#### 模板 P2：配置任务预处理

适用任务：L1-16。

```json
"config": [
  {
    "type": "launch",
    "parameters": {
      "command": ["gimp"]
    }
  }
]
```

#### 模板 A：图片导出类（PNG/JPG）

适用任务：L1-1 ~ L1-12。

```json
"postconfig": [
  {"type": "activate_window", "parameters": {"window_name": "GNU Image Manipulation Program"}},
  {"type": "execute", "parameters": {"command": ["python3", "-c", "import time, pyautogui; time.sleep(1); pyautogui.hotkey([\"shift\", \"ctrl\", \"e\"])"]}},
  {"type": "sleep", "parameters": {"seconds": 0.5}},
  {"type": "execute", "parameters": {"command": ["python3", "-c", "import time, pyautogui; time.sleep(1); pyautogui.hotkey([\"ctrl\", \"a\"]); pyautogui.write(\"<output_filename>\"); pyautogui.press([\"enter\"])"]}},
  {"type": "sleep", "parameters": {"seconds": 2}},
  {"type": "execute", "parameters": {"command": ["python3", "-c", "import pyautogui; pyautogui.press([\"enter\"])"]}},
  {"type": "sleep", "parameters": {"seconds": 5}}
]
```

#### 模板 B：XCF 工程类

适用任务：L1-13 ~ L1-15。

```json
"postconfig": [
  {"type": "execute", "parameters": {"command": ["python3", "-c", "import time, pyautogui; time.sleep(1); pyautogui.hotkey([\"ctrl\", \"q\"])"]}},
  {"type": "sleep", "parameters": {"seconds": 0.5}}
]
```

#### 模板 C：配置类

适用任务：L1-16。

```json
"postconfig": [
  {"type": "execute", "parameters": {"command": ["python3", "-c", "import time, pyautogui; time.sleep(1); pyautogui.hotkey([\"ctrl\", \"q\"])"]}},
  {"type": "sleep", "parameters": {"seconds": 0.5}}
]
```

---

#### 任务 L1-1：顺时针旋转 90 度

- **ID**：`a1b00001-0001-4000-8000-000000000001`
- **来源**：https://docs.gimp.org/2.10/en/gimp-image-transform-rotate.html
- **指令**：将当前图像顺时针旋转 90 度。
- **上传素材**：`assets/gimp_task/graphic/pattern_asfalt_light.png` -> `/home/user/Desktop/pattern_asfalt_light.png`
- **预处理流程**：模板 P1（输入 `pattern_asfalt_light.png`）。
- **后处理流程**：模板 A（`<output_filename>` = `rot90.png`）。
- **评估函数**：`check_045bf3ff_rotate`
- **result**：`vm_file` -> `/home/user/Desktop/rot90.png`
- **expected**：`cloud_file` -> `landscape_mountain_1108099.jpg`（与输入同图）
- **验证逻辑**：检查旋转后宽高互换，并与原图顺时针 90 度旋转结果进行结构相似度比对。
- **需要新评估函数**：❌

---

#### 任务 L1-2：水平镜像

- **ID**：`a1b00002-0002-4000-8000-000000000002`
- **来源**：https://docs.gimp.org/2.10/en/gimp-tool-flip.html
- **指令**：将当前图像执行水平翻转。
- **上传素材**：`assets/gimp_task/photos/street_city_466685.jpg` -> `/home/user/Desktop/street_city_466685.jpg`
- **预处理流程**：模板 P1（输入 `street_city_466685.jpg`）。
- **后处理流程**：模板 A（`<output_filename>` = `city_mirror.png`）。
- **评估函数**：`check_image_mirror`
- **result**：`vm_file` -> `/home/user/Desktop/city_mirror.png`
- **expected**：`cloud_file` -> `street_city_466685.jpg`（与输入同图）
- **验证逻辑**：将原图进行水平翻转后与输出图进行 SSIM 比较，达到阈值视为通过。
- **需要新评估函数**：❌

---

#### 任务 L1-3：缩放到 1920x1080

- **ID**：`a1b00003-0003-4000-8000-000000000003`
- **来源**：https://docs.gimp.org/2.10/en/gimp-image-scale.html
- **指令**：将当前图像缩放到 `1920x1080`。
- **上传素材**：`assets/gimp_task/photos/portrait_woman_774909.jpg` -> `/home/user/Desktop/portrait_woman_774909.jpg`
- **预处理流程**：模板 P1（输入 `portrait_woman_774909.jpg`）。
- **后处理流程**：模板 A（`<output_filename>` = `portrait_1920x1080.png`）。
- **评估函数**：`check_8ea73f6f_resize_1920x1080`
- **result**：`vm_file` -> `/home/user/Desktop/portrait_1920x1080.png`
- **expected**：`cloud_file` -> `portrait_woman_774909.jpg`（与输入同图）
- **验证逻辑**：输出分辨率必须精确为 1920x1080，且与基于源图缩放结果保持结构一致。
- **需要新评估函数**：❌

---

#### 任务 L1-4：等比缩放到 50%

- **ID**：`a1b00004-0004-4000-8000-000000000004`
- **来源**：https://docs.gimp.org/2.10/en/gimp-image-scale.html
- **指令**：将当前图像按 50% 等比缩放。
- **上传素材**：`assets/gimp_task/photos/architecture_247431.jpg` -> `/home/user/Desktop/architecture_247431.jpg`
- **预处理流程**：模板 P1（输入 `architecture_247431.jpg`）。
- **后处理流程**：模板 A（`<output_filename>` = `architecture_half.png`）。
- **评估函数**：`check_b148e375_resize_50_percent`
- **result**：`vm_file` -> `/home/user/Desktop/architecture_half.png`
- **expected**：`cloud_file` -> `architecture_247431.jpg`（与输入同图）
- **验证逻辑**：检查输出宽高是否为输入的一半（允许微小容差），并校验缩放后内容一致性。
- **需要新评估函数**：❌

---

#### 任务 L1-5：亮度降低约 30%

- **ID**：`a1b00005-0005-4000-8000-000000000005`
- **来源**：https://docs.gimp.org/2.10/en/gimp-tool-brightness-contrast.html
- **指令**：将当前图像亮度降低约 30%。
- **上传素材**：`assets/gimp_task/photos/food_plate_1640777.jpg` -> `/home/user/Desktop/food_plate_1640777.jpg`
- **预处理流程**：模板 P1（输入 `food_plate_1640777.jpg`）。
- **后处理流程**：模板 A（`<output_filename>` = `food_darker.png`）。
- **评估函数**：`check_brightness_decrease_30_percent`
- **result**：`vm_file` -> `/home/user/Desktop/food_darker.png`
- **expected**：`cloud_file` -> `food_plate_1640777.jpg`（与输入同图）
- **验证逻辑**：输出平均亮度低于输入，降幅在目标区间内，且图像结构保持一致。
- **需要新评估函数**：❌

---

#### 任务 L1-6：对比度提升至少 15%

- **ID**：`a1b00006-0006-4000-8000-000000000006`
- **来源**：https://docs.gimp.org/2.10/en/gimp-tool-brightness-contrast.html
- **指令**：将当前图像对比度提升至少 15%。
- **上传素材**：`assets/gimp_task/photos/nature_forest_1103970.jpg` -> `/home/user/Desktop/nature_forest_1103970.jpg`
- **预处理流程**：模板 P1（输入 `nature_forest_1103970.jpg`）。
- **后处理流程**：模板 A（`<output_filename>` = `forest_contrast.png`）。
- **评估函数**：`check_contrast_increase`，`options={"min_increase_percent": 15}`（`expected` 需为源图，`result` 为输出图）
- **result**：`cloud_file` -> `nature_forest_1103970.jpg`（源图）
- **expected**：`vm_file` -> `/home/user/Desktop/forest_contrast.png`（输出图）
- **验证逻辑**：输出图像对比度相对输入提升 >= 15%。
- **需要新评估函数**：❌

---

#### 任务 L1-7：饱和度提升约 40%

- **ID**：`a1b00007-0007-4000-8000-000000000007`
- **来源**：https://docs.gimp.org/2.10/en/gimp-tool-hue-saturation.html
- **指令**：将当前图像饱和度提升约 40%。
- **上传素材**：`assets/gimp_task/photos/beach_people_1481105.jpg` -> `/home/user/Desktop/beach_people_1481105.jpg`
- **预处理流程**：模板 P1（输入 `beach_people_1481105.jpg`）。
- **后处理流程**：模板 A（`<output_filename>` = `beach_saturation.png`）。
- **评估函数**：`check_554785e9_saturation_increase_40`
- **result**：`vm_file` -> `/home/user/Desktop/beach_saturation.png`
- **expected**：`cloud_file` -> `beach_people_1481105.jpg`（与输入同图）
- **验证逻辑**：校验平均饱和度提升达到预期阈值。
- **需要新评估函数**：❌

---

#### 任务 L1-8：转换为灰度图

- **ID**：`a1b00008-0008-4000-8000-000000000008`
- **来源**：https://docs.gimp.org/2.10/en/gimp-image-mode.html
- **指令**：将当前图像转换为灰度。
- **上传素材**：`assets/gimp_task/photos/portrait_woman_774909.jpg` -> `/home/user/Desktop/portrait_woman_774909.jpg`
- **预处理流程**：模板 P1（输入 `portrait_woman_774909.jpg`）。
- **后处理流程**：模板 A（`<output_filename>` = `portrait_gray.png`）。
- **评估函数**：`check_045bf3ff_grayscale`
- **result**：`vm_file` -> `/home/user/Desktop/portrait_gray.png`
- **expected**：`cloud_file` -> `portrait_woman_774909.jpg`（与输入同图）
- **验证逻辑**：输出图像应为灰度模式（或 RGB 三通道数值等价的灰度结果）。
- **需要新评估函数**：❌

---

#### 任务 L1-9：导出 JPEG

- **ID**：`a1b00009-0009-4000-8000-000000000009`
- **来源**：https://docs.gimp.org/2.10/en/file-jpeg-export.html
- **指令**：将当前 PNG 图像导出为 JPEG 文件。
- **上传素材**：`assets/gimp_task/graphic/pattern_asfalt_light.png` -> `/home/user/Desktop/pattern_asfalt_light.png`
- **预处理流程**：模板 P1（输入 `pattern_asfalt_light.png`）。
- **后处理流程**：模板 A（`<output_filename>` = `pattern_export.jpg`）。
- **评估函数**：`check_jpeg_format`
- **result**：`vm_file` -> `/home/user/Desktop/pattern_export.jpg`
- **expected**：无（`check_jpeg_format` 不需要 expected）。
- **验证逻辑**：检查输出文件是否为 JPEG 格式。
- **需要新评估函数**：❌

---

#### 任务 L1-10：白底转透明

- **ID**：`a1b00010-0010-4000-8000-000000000010`
- **来源**：https://docs.gimp.org/2.10/en/plug-in-colortoalpha.html
- **指令**：将当前图像中接近白色的背景转为透明。
- **上传素材**：`assets/gimp_task/products/product_headphone_3394650.jpg` -> `/home/user/Desktop/product_headphone_3394650.jpg`
- **预处理流程**：模板 P1（输入 `product_headphone_3394650.jpg`）。
- **后处理流程**：模板 A（`<output_filename>` = `headphone_transparent.png`）。
- **评估函数**：`check_white_to_alpha_transparency`
- **result**：`vm_file` -> `/home/user/Desktop/headphone_transparent.png`
- **expected**：`cloud_file` -> `product_headphone_3394650.jpg`（与输入同图）
- **验证逻辑**：检查输出存在 alpha 通道，白色区域被显著转为透明，主体内容保留。
- **需要新评估函数**：❌

---

#### 任务 L1-11：转换为 256 色索引图

- **ID**：`a1b00011-0011-4000-8000-000000000011`
- **来源**：https://docs.gimp.org/2.10/en/gimp-image-convert-indexed.html
- **指令**：将当前图像转换为 256 色索引模式。
- **上传素材**：`assets/gimp_task/products/product_camera_90946.jpg` -> `/home/user/Desktop/product_camera_90946.jpg`
- **预处理流程**：模板 P1（输入 `product_camera_90946.jpg`）。
- **后处理流程**：模板 A（`<output_filename>` = `camera_indexed_256.png`）。
- **评估函数**：`check_045bf3ff_indexed_color`
- **result**：`vm_file` -> `/home/user/Desktop/camera_indexed_256.png`
- **expected**：`cloud_file` -> `product_camera_90946.jpg`（与输入同图）
- **验证逻辑**：检查输出为索引色（`P` 模式）且调色板大小为 256 色。
- **需要新评估函数**：❌

---

#### 任务 L1-12：JPEG 导出且体积小于 500KB

- **ID**：`a1b00012-0012-4000-8000-000000000012`
- **来源**：https://docs.gimp.org/2.10/en/file-jpeg-export.html
- **指令**：将当前图像转换为 JPEG 格式，并将文件体积控制在 `500KB` 内。
- **上传素材**：`assets/gimp_task/photos/beach_people_1481105.jpg` -> `/home/user/Desktop/beach_people_1481105.jpg`
- **预处理流程**：模板 P1（输入 `beach_people_1481105.jpg`）。
- **后处理流程**：模板 A（`<output_filename>` = `beach_compressed.jpg`）。
- **评估函数**：多指标 `["check_jpeg_format", "check_image_file_size"]`，`"conj": "and"`
- **result**：2 个 `vm_file` -> `/home/user/Desktop/beach_compressed.jpg`（两个评估器都读取同一输出）
- **expected**：
  - `None`（`check_jpeg_format` 不需要 expected）
  - 1 个 `rule` -> `{"max_size": 512000}`
- **验证逻辑**：输出必须是 JPEG，且文件大小 < 500KB。
- **需要新评估函数**：❌

---

#### 任务 L1-13：新建图层并命名 Circle

- **ID**：`a1b00013-0013-4000-8000-000000000013`
- **来源**：https://docs.gimp.org/2.10/en/gimp-layer-new.html
- **指令**：在当前工程中新建透明图层并命名为 `Circle`。
- **上传素材**：`assets/gimp_task/photos/pet_dog_1108099_alt.jpg` -> `/home/user/Desktop/pet_dog_1108099_alt.jpg`
- **预处理流程**：模板 P1（输入 `pet_dog_1108099_alt.jpg`）。
- **后处理流程**：模板 B（退出前需确保已保存到 `/home/user/Desktop/l1_layer_circle.xcf`）。
- **评估函数**：`check_b148e375_new_layer_circle`
- **result**：`xcf_file` -> `/home/user/Desktop/l1_layer_circle.xcf`
- **expected**：`rule` -> `{"layer_name": "Circle"}`
- **验证逻辑**：解析 XCF，检查是否存在名为 `Circle` 的图层。
- **需要新评估函数**：❌

---

#### 任务 L1-14：复制图层并隐藏原图层

- **ID**：`a1b00014-0014-4000-8000-000000000014`
- **来源**：https://docs.gimp.org/2.10/en/gimp-layer-dialog.html
- **指令**：在当前工程中复制当前图层并命名 `Backup`，隐藏原图层。
- **上传素材**：`assets/gimp_task/photos/pet_dog_1108099_alt.jpg` -> `/home/user/Desktop/pet_dog_1108099_alt.jpg`
- **预处理流程**：模板 P1（输入 `pet_dog_1108099_alt.jpg`）。
- **后处理流程**：模板 B（退出前需确保已保存到 `/home/user/Desktop/l1_layer_backup.xcf`）。
- **评估函数**：`check_b148e375_duplicate_rename_hide`
- **result**：`xcf_file` -> `/home/user/Desktop/l1_layer_backup.xcf`
- **expected**：`rule` -> `{"duplicate_name": "Backup"}`
- **验证逻辑**：解析 XCF，验证 `Backup` 图层存在且可见，并且至少有一个非 `Backup` 图层被隐藏。
- **需要新评估函数**：❌

---

#### 任务 L1-15：设置图层透明度为 75% 并置顶

- **ID**：`a1b00015-0015-4000-8000-000000000015`
- **来源**：https://docs.gimp.org/2.10/en/gimp-layer-dialog.html
- **指令**：在当前工程中将当前图层改名为 `dog`、透明度设为 75%、并置顶。
- **上传素材**：`assets/gimp_task/photos/pet_dog_1108099_alt.jpg` -> `/home/user/Desktop/pet_dog_1108099_alt.jpg`
- **预处理流程**：模板 P1（输入 `pet_dog_1108099_alt.jpg`）。
- **后处理流程**：模板 B（退出前需确保已保存到 `/home/user/Desktop/l1_layer_opacity.xcf`）。
- **评估函数**：`check_d16c99dc_opacity_and_layer_order`
- **result**：`xcf_file` -> `/home/user/Desktop/l1_layer_opacity.xcf`
- **expected**：`rule` -> `{"layer_name": "dog", "opacity": 75}`
- **验证逻辑**：解析 XCF，检查 `dog` 图层存在、透明度约为 75%，并位于最上层。
- **需要新评估函数**：❌

---

#### 任务 L1-16：设置最近文件数为 15

- **ID**：`a1b00016-0016-4000-8000-000000000016`
- **来源**：https://www.youtube.com/watch?v=G_PjQAy0iiU
- **指令**：将 GIMP 的最近文件显示数量设置为 `15`。
- **上传素材**：无
- **预处理流程**：模板 P2。
- **后处理流程**：模板 C。
- **评估函数**：`check_7b7617bd_recent_files`
- **result**：`gimp_config_file` -> `~/.config/GIMP/2.10/gimprc`
- **expected**：`rule` -> `{"key": "max-recent-files", "value": "15"}`
- **验证逻辑**：解析 `gimprc`，检查 `(max-recent-files 15)` 是否存在。
- **需要新评估函数**：❌

---
### 5.2 L1 evaluator 映射修正（基于现有 evaluator 实现）

以下是本版 L1 的 evaluator 映射修正结论，已按当前代码签名对齐：

1. L1-6 `check_contrast_increase`：参数顺序是 `(src_path, tgt_path)`，因此应配置为 `result=cloud_file(源图)`、`expected=vm_file(输出图)`，并保留 `options.min_increase_percent`。
2. L1-9 JPEG 导出：应使用 `check_jpeg_format`（只检查输出格式），不应继续使用 `check_045bf3ff_jpeg_export`（仓内无该 JSON 实例，且签名含冗余 `src_path`）。
3. L1-12 双指标：第一项 `check_jpeg_format` 不需要 expected，需在 `expected` 列表第一项放 `None`，第二项保留 `rule.max_size`。
4. L1-13~L1-15 XCF 类：评估函数依赖 `xcf_file + rule`，后处理必须确保“先保存目标 XCF，再退出”。
5. L1-16 配置类：`check_7b7617bd_recent_files(actual_config_path, rule)` 映射正确，继续使用 `gimp_config_file + rule`。

### 5.3 L1 扩展任务（需补评估函数后落地）

#### 任务 L1-X1：中心裁剪为 1:1

- **ID**：`a1b10001-1001-4000-8000-000000000001`
- **来源**：https://docs.gimp.org/2.10/en/gimp-tool-crop.html
- **指令**：将当前人像从中心裁成 1:1。
- **上传素材**：`assets/gimp_task/photos/portrait_woman_774909.jpg` -> `/home/user/Desktop/portrait_woman_774909.jpg`
- **评估函数**：多指标 `["check_aspect_ratio", "check_crop_region_similarity_generic"]`，`"conj": "and"`
- **result**：2 个 `vm_file` -> `/home/user/Desktop/portrait_square.png`
- **expected**：
  - 1 个 `rule` -> `{"ratio": "1:1", "tolerance": 0.01}`
  - 1 个 `cloud_file` -> `portrait_woman_774909.jpg`（与输入同图，配合 `options` 指定 center crop）
- **验证逻辑**：比例必须为 1:1，且裁剪区域与“中心裁剪参考结果”一致。
- **需要新评估函数**：✅

---

#### 任务 L1-X2：导出 WebP 且体积小于 400KB

- **ID**：`a1b10002-1002-4000-8000-000000000002`
- **来源**：https://docs.gimp.org/2.10/en/file-webp-export.html
- **指令**：将当前海边图转换为 WebP，并将文件体积控制在 400KB 以内。
- **上传素材**：`assets/gimp_task/photos/beach_people_1481105.jpg` -> `/home/user/Desktop/beach_people_1481105.jpg`
- **评估函数**：多指标 `["check_webp_format", "check_image_file_size"]`，`"conj": "and"`
- **result**：2 个 `vm_file` -> `/home/user/Desktop/beach_small.webp`
- **expected**：
  - `None`（`check_webp_format` 不需要 expected）
  - 1 个 `rule` -> `{"max_size": 409600}`
- **验证逻辑**：文件必须是 WebP 格式，且大小 < 400KB。
- **需要新评估函数**：✅（`check_webp_format`）

---

#### 任务 L1-X3：将图层数量调整为 3 层

- **ID**：`a1b10003-1003-4000-8000-000000000003`
- **来源**：https://docs.gimp.org/2.10/en/gimp-layer-dialog.html
- **指令**：将当前工程图层总数调整为 3 层。
- **上传素材**：`assets/gimp_task/photos/pet_dog_1108099_alt.jpg` -> `/home/user/Desktop/pet_dog_1108099_alt.jpg`
- **评估函数**：`check_xcf_layer_count`
- **result**：`xcf_file` -> `/home/user/Desktop/layer_count_3.xcf`
- **expected**：`rule` -> `{"layer_count": 3}`
- **验证逻辑**：解析 XCF 图层列表，图层总数必须等于 3。
- **需要新评估函数**：✅

---

#### 任务 L1-X4：底部居中添加文本 SALE

- **ID**：`a1b10004-1004-4000-8000-000000000004`
- **来源**：https://docs.gimp.org/2.10/en/gimp-tool-text.html
- **指令**：在当前手表图底部居中添加 `SALE` 文案（白色，约 48 px）。
- **上传素材**：`assets/gimp_task/products/product_watch_190819.jpg` -> `/home/user/Desktop/product_watch_190819.jpg`
- **评估函数**：`check_text_region_change`
- **result**：`vm_file` -> `/home/user/Desktop/watch_sale.png`
- **expected**：`rule` -> `{"region": "bottom_center", "text": "SALE", "min_change_ratio": 0.01}`
- **验证逻辑**：底部中心区域应出现显著文本像素变化，且与期望文本特征匹配。
- **需要新评估函数**：✅

---

## 6. L2 任务池（细化版，首批 12 个）

L2 任务统一约束：

1. 每个任务至少串联 4 个关键编辑动作（几何、调色、图层、文本、导出中至少覆盖 3 类）。
2. 每个任务必须有明确交付规格（尺寸/比例/格式/体积至少 2 项）。
3. 默认输出为“成品图 + 可返工 XCF”，少数轻量任务可只交付成品图。
4. 评测优先采用多指标 `conj: and`，避免单一指标造成误判。
5. 每个任务附可追溯教程来源，优先 GIMP 官方文档与公开教程站点。

### 6.1 电商与商品图

#### 任务 L2-1：香水透明主图标准化（平台上架）

- **ID**：`a2b00001-0001-4000-8000-000000000001`
- **来源**：
  - https://docs.gimp.org/2.10/en/gimp-layer-color-to-alpha.html
  - https://docs.gimp.org/2.10/en/gimp-using-web-transparency.html
  - https://docs.gimp.org/2.10/en/gimp-image-scale.html
- **指令**：请将 `/home/user/Desktop/product_perfume_965989.jpg` 制作为电商透明主图：去掉近白背景后，将主体放入 `1200x1200` 透明画布并居中；主体最终高度控制在 `840-960 px`（约 70%-80%）；在主体下方添加椭圆阴影（不透明度 `25%-40%`，高斯模糊半径 `20-40 px`）；图层命名为 `Product`、`Shadow`、`Guide_BG`；导出 `/home/user/Desktop/perfume_listing.png`，并保存 `/home/user/Desktop/perfume_listing.xcf`。
- **上传素材**：`assets/gimp_task/products/product_perfume_965989.jpg` -> `/home/user/Desktop/product_perfume_965989.jpg`
- **评估函数建议**：`check_l2_perfume_listing_complete`（复合，内部校验透明、尺寸、主体占比、阴影、XCF 图层）
- **result / expected 建议**：
  - `vm_file` -> `/home/user/Desktop/perfume_listing.png`（PNG + 透明 + 1200x1200）
  - `xcf_file` -> `/home/user/Desktop/perfume_listing.xcf`（包含指定图层名）
- **需要新评估函数**：❌

---

#### 任务 L2-2：手表白底标准图 + 柔影 + 体积控制

- **ID**：`a2b00002-0002-4000-8000-000000000002`
- **来源**：
  - https://docs.gimp.org/2.10/en/gimp-tool-levels.html
  - https://docs.gimp.org/2.10/en/gimp-tool-curves.html
  - https://docs.gimp.org/2.10/en/gimp-filter-dropshadow.html
- **指令**：将 `/home/user/Desktop/product_watch_190819.jpg` 做成平台白底图：先用色阶或曲线增强主体层次，使成品对比度相对原图至少提升 `8%`；再放到纯白 `1600x1600` 画布中居中（背景像素中 `RGB>=245` 的占比不少于 `95%`），添加轻微阴影（阴影层不透明度 `15%-35%`）；图层命名 `Watch_Main`、`Shadow_Soft`、`BG_White`；导出 `/home/user/Desktop/watch_white_standard.jpg`（小于 `450KB`），并保存 `/home/user/Desktop/watch_white_standard.xcf`。
- **上传素材**：`assets/gimp_task/products/product_watch_190819.jpg` -> `/home/user/Desktop/product_watch_190819.jpg`
- **评估函数建议**：`check_l2_watch_white_standard_complete`（复合，内部校验白底占比、阴影、对比度、体积、XCF 图层）
- **result / expected 建议**：
  - `vm_file` -> `/home/user/Desktop/watch_white_standard.jpg`
  - `rule` -> `{"max_size": 460800, "width": 1600, "height": 1600}`
  - `xcf_file` -> `/home/user/Desktop/watch_white_standard.xcf`
- **需要新评估函数**：❌

---

#### 任务 L2-3：三商品横向对比图（详情页首屏）

- **ID**：`a2b00003-0003-4000-8000-000000000003`
- **状态**：`已删除`
- **删除原因**：与 L3-6「相机产品页三图组合」都属于多商品/多产物电商版式任务，且该任务对“三栏均衡”的要求高度依赖启发式布局检测，稳定性不足，和其带来的增量覆盖不成正比。

---

### 6.2 社媒与内容配图

#### 任务 L2-4：3:4 社媒活动封面（城市夜跑）

- **ID**：`a2b00004-0004-4000-8000-000000000004`
- **来源**：
  - https://docs.gimp.org/2.10/en/gimp-tool-crop.html
  - https://docs.gimp.org/2.10/en/gimp-tool-levels.html
  - https://docs.gimp.org/2.10/en/gimp-tool-curves.html
- **指令**：把 `/home/user/Desktop/street_city_466685.jpg` 做成活动封面：裁剪为 `1080x1440`（3:4）；整体对比度和饱和度相对原图均至少提升 `10%`；顶部添加高度 `180-260 px` 的半透明深色条（不透明度 `35%-60%`）并添加标题 `CITY NIGHT RUN`；图层命名 `BG_City`、`Title_Bar`、`Title_Text`；导出 `/home/user/Desktop/city_night_run_cover.jpg`（小于 `700KB`），并保存 `/home/user/Desktop/city_night_run_cover.xcf`。
- **上传素材**：`assets/gimp_task/photos/street_city_466685.jpg` -> `/home/user/Desktop/street_city_466685.jpg`
- **评估函数建议**：`check_l2_city_night_run_cover_complete`（复合，内部校验尺寸、体积、对比/饱和度、顶部标题条、XCF 图层）
- **需要新评估函数**：❌

---

#### 任务 L2-5：公众号头图（安全边距 + Logo 水印）

- **ID**：`a2b00005-0005-4000-8000-000000000005`
- **来源**：
  - https://docs.gimp.org/2.10/en/gimp-image-guides.html
  - https://docs.gimp.org/2.10/en/gimp-image-scale.html
  - https://docs.gimp.org/2.10/en/gimp-layer-groups.html
- **指令**：用 `/home/user/Desktop/landscape_mountain_1108099.jpg` 制作公众号头图，成品尺寸 `900x383`。要求：先用参考线规划左右安全边距（各 `60±10 px`），再完成裁切与构图；加入 `/home/user/Desktop/icon_home.svg` 作为左下角水印图标（宽度 `48-96 px`），并在右下角添加文案 `WEEKEND ESCAPE`；图层命名 `BG_Mountain`、`Logo_Icon`、`Caption_Text`；导出 `/home/user/Desktop/wechat_header_mountain.png`，并保存 `/home/user/Desktop/wechat_header_mountain.xcf`。
- **上传素材**：
  - `assets/gimp_task/graphic/pattern_asfalt_light.png` -> `/home/user/Desktop/pattern_asfalt_light.png`
  - `assets/gimp_task/graphic/icon_home.svg` -> `/home/user/Desktop/icon_home.svg`
- **评估函数建议**：`check_l2_wechat_header_mountain_complete`（复合，内部校验尺寸、安全边距、图标区域、文本区域、XCF 图层）
- **需要新评估函数**：❌

---

### 6.3 图层协同与视觉合成

#### 任务 L2-7：相机金属质感海报底图

- **ID**：`a2b00007-0007-4000-8000-000000000007`
- **来源**：
  - https://docs.gimp.org/2.10/en/gimp-layer-groups.html
  - https://docs.gimp.org/2.10/en/gimp-layer-mask-add.html
  - https://docs.gimp.org/2.10/en/gimp-filter-dropshadow.html
- **指令**：使用 `/home/user/Desktop/product_camera_90946.jpg` 和 `/home/user/Desktop/texture_metal_220182.jpg` 制作 `1600x1000` 产品海报底图：金属纹理铺满背景；产品抠出后放在画面 `55%-70%` 横向位置（中心偏右）；叠加轻微投影和暗角；添加主标题 `PRO SHOOT`（建议位于左上象限）。图层命名 `BG_Metal`、`Camera_Main`、`Shadow`、`Vignette`、`Title`；导出 `/home/user/Desktop/camera_metal_poster.png`，并保存 `/home/user/Desktop/camera_metal_poster.xcf`。
- **上传素材**：
  - `assets/gimp_task/products/product_camera_90946.jpg` -> `/home/user/Desktop/product_camera_90946.jpg`
  - `assets/gimp_task/texture/texture_metal_220182.jpg` -> `/home/user/Desktop/texture_metal_220182.jpg`
- **评估函数建议**：`check_l2_camera_metal_poster_complete`（复合，内部校验尺寸、主体偏右、标题区域、XCF 图层）
- **需要新评估函数**：❌

---

#### 任务 L2-8：街景广告牌透视替换（Mockup）

- **ID**：`a2b00008-0008-4000-8000-000000000008`
- **来源**：
  - https://docs.gimp.org/2.10/en/gimp-tool-perspective.html
  - https://docs.gimp.org/2.10/en/gimp-image-guides.html
  - https://daviesmediadesign.com/tutorials/
- **指令**：在 `/home/user/Desktop/street_city_466685.jpg` 中完成广告牌替换：保持原始 `2200x1365` 画布，先用 `/home/user/Desktop/texture_paper_723311.jpg` 做广告底，再加入标题 `CITY DEALS` 与 `icon_search.svg`；将广告层透视贴合到牌面四点区域（近似坐标：`(1130,260)`、`(1580,250)`、`(1600,620)`、`(1100,640)`，允许 `±40 px`），并将合成层不透明度设置在 `70%-90%` 以融入环境；图层命名 `Billboard_Art`、`Billboard_Text`、`Billboard_Composite`；导出 `/home/user/Desktop/street_billboard_mockup.jpg`，并保存 `/home/user/Desktop/street_billboard_mockup.xcf`。
- **上传素材**：
  - `assets/gimp_task/photos/street_city_466685.jpg` -> `/home/user/Desktop/street_city_466685.jpg`
  - `assets/gimp_task/texture/texture_paper_723311.jpg` -> `/home/user/Desktop/texture_paper_723311.jpg`
  - `assets/gimp_task/graphic/icon_search.svg` -> `/home/user/Desktop/icon_search.svg`
- **评估函数建议**：`check_l2_street_billboard_mockup_complete`（复合，内部校验原图尺寸、指定区域透视替换、标题区域、XCF 图层）
- **需要新评估函数**：❌（已落地 `check_perspective_overlay_region` 并封装进 `check_l2_street_billboard_mockup_complete`）

---

#### 任务 L2-9：纸纹活动海报（图层组管理）

- **ID**：`a2b00009-0009-4000-8000-000000000009`
- **来源**：
  - https://docs.gimp.org/2.10/en/gimp-layer-groups.html
  - https://docs.gimp.org/2.10/en/gimp-layer-mask-add.html
  - https://docs.gimp.org/2.10/en/gimp-tool-curves.html
- **指令**：基于 `/home/user/Desktop/beach_people_1481105.jpg` 与 `/home/user/Desktop/texture_paper_723311.jpg` 制作活动海报，尺寸 `1200x1800`。要求：使用图层组 `BG_Group`、`Photo_Group`、`Text_Group`、`Deco_Group` 管理素材；照片边缘使用图层蒙版做渐隐；文本必须包含 `BEACH PARTY`、`2026.08.16`、`SANYA COAST`；导出 `/home/user/Desktop/beach_event_poster.png`，并保存 `/home/user/Desktop/beach_event_poster.xcf`。
- **上传素材**：
  - `assets/gimp_task/photos/beach_people_1481105.jpg` -> `/home/user/Desktop/beach_people_1481105.jpg`
  - `assets/gimp_task/texture/texture_paper_723311.jpg` -> `/home/user/Desktop/texture_paper_723311.jpg`
- **评估函数建议**：`check_l2_beach_event_poster_complete`（复合，内部校验尺寸、三段文本区域、图层组命名）
- **需要新评估函数**：❌

---

### 6.4 说明图与标注

#### 任务 L2-10：相机结构标注图（教学页）

- **ID**：`a2b00010-0010-4000-8000-000000000010`
- **来源**：
  - https://docs.gimp.org/2.10/en/gimp-image-guides.html
  - https://docs.gimp.org/2.10/en/gimp-layer-groups.html
  - https://daviesmediadesign.com/tutorials/
- **指令**：将 `/home/user/Desktop/product_camera_90946.jpg` 制作成教学标注图：保留原分辨率，添加 3 处功能标注，文本固定为 `Lens`、`Grip`、`Mode Dial`（每处都需要箭头或连线）；底部添加高度 `120-220 px` 的半透明说明栏；图层命名 `Base_Image`、`Callout_1`、`Callout_2`、`Callout_3`、`Footer_Note`；导出 `/home/user/Desktop/camera_annotation.png`，并保存 `/home/user/Desktop/camera_annotation.xcf`。
- **上传素材**：`assets/gimp_task/products/product_camera_90946.jpg` -> `/home/user/Desktop/product_camera_90946.jpg`
- **评估函数建议**：`check_l2_camera_annotation_complete`（复合，内部校验原图尺寸、3 处标注、指定文本、XCF 图层）
- **需要新评估函数**：❌（已落地 `check_annotation_callout_count` 并封装进 `check_l2_camera_annotation_complete`）

---

#### 任务 L2-11：前后对比拼图（调色教学）

- **ID**：`a2b00011-0011-4000-8000-000000000011`
- **状态**：`已删除`
- **删除原因**：与 L3-7「前后对比 + 步骤总览」主题重复，且单独保留时只是在更简单层级重复“前后对比教学图”模式，没有形成独立能力增量。

---

#### 任务 L2-12：透明通道三步教学卡片

- **ID**：`a2b00012-0012-4000-8000-000000000012`
- **状态**：`已删除`
- **删除原因**：与 L3-10「透明通道课程封面与信息图组合」场景重复，都是围绕透明通道课程内容的教学视觉交付；L2 版本只保留三栏卡片，覆盖面明显更弱。

---

### 6.5 L2 多样性核对（首批）

| 任务编号 | 场景类型 | 核心复合能力 | 是否含 XCF | 评测器数量建议 |
|---|---|---|---|---:|
| L2-1 | 电商上架图 | 抠图 + 透明 + 规格化 + 阴影 | ✅ | 4 |
| L2-2 | 电商白底图 | 调色 + 白底 + 投影 + 压缩 | ✅ | 4 |
| L2-4 | 社媒封面 | 裁剪 + 调色 + 标题区设计 + 压缩 | ✅ | 5-6 |
| L2-5 | 公众号头图 | 参考线构图 + 图标水印 + 文案 | ✅ | 4 |
| L2-7 | 产品海报底图 | 纹理合成 + 图层蒙版 + 标题排版 | ✅ | 4 |
| L2-8 | 广告牌 Mockup | 透视变换 + 融合 + 图层组织 | ✅ | 3-4 |
| L2-9 | 纸纹海报 | 图层组 + 蒙版 + 文案排版 | ✅ | 4 |
| L2-10 | 教学标注图 | 标注对象管理 + 说明栏 + 文本 | ✅ | 4-5 |

> 清理后保留的 L2 首批任务为 `8` 个：L2-1、L2-2、L2-4、L2-5、L2-7、L2-8、L2-9、L2-10。

---


### 6.6 L2 指令清晰度与评测闭环（新增落地步骤）

#### 6.6.1 执行步骤（写入任务设计规范）

1. **先做指令量化**：每个 L2 指令必须把“尽量/轻微/简短/约”等描述改成可判定数值（如像素范围、比例范围、透明度范围、文本固定值）。
2. **再做评测映射**：把每条指令要求映射到可脚本化检查项，至少覆盖尺寸/格式/体积/文本/图层结构中的 3 类。
3. **补齐结构评测器**：涉及排版、透视、分栏、标注数量的任务，不能只用格式和尺寸检查，必须增加布局类 evaluator。
4. **统一 JSON 组合方式**：优先使用 `func` 列表 + `conj: and`，并显式给出 `result`、`expected`、`options` 的一一对应关系。
5. **回归验证**：每个任务至少做“正例 1 次 + 反例 1 次”验证，确保评测器对错误结果能稳定判 0。
6. **避免退化型格式转换任务**：如果指令是“转换/导出为某格式”，输入素材默认不应已经是同格式文件。例如“导出 JPEG”任务不应上传 `.jpg/.jpeg` 作为唯一输入，否则 agent 即使什么都不改，只要重新导出同格式文件也可能通过，任务失去有效区分度。更合理的做法是使用 `png`/`bmp` 等异格式输入，并让输出文件名、扩展名、评测路径保持一致。
7. **导出前先全选并输入完整文件名**：凡是依赖 `postconfig` 自动导出图片的任务，在 `pyautogui.write(...)` 前必须先发送 `ctrl+a`，把导出对话框中预填的原文件名完整选中，再输入带完整后缀的目标文件名。这样可以避免目标文件名被追加到原文件名后，也能避免实际导出格式和 evaluator 路径发生偏差。

#### 6.6.2 现有函数风险与修订建议

| 现有函数 | 当前风险 | 修订动作 |
|---|---|---|
| `check_text_in_image_basic` | 只检测边缘密度，无法确认指定文本内容，误判率高 | 新增 `check_text_in_region_keywords`（按区域 + 关键词校验）并优先替换 |
| `check_text_in_image` | 与 `expected_text` 参数语义不一致，未真正做 OCR 关键词匹配 | 新增 `check_text_keywords_simple_ocr` 或降级为“区域变化检查”并重命名 |
| `check_xcf_file_exists_and_has_layers` | 仅做二进制字符串包含，无法校验层级/顺序/组关系 | 新增 `check_xcf_layers_structure`（层名、顺序、组名） |
| `check_image_file_size` | 只支持上限，不支持区间控制 | 新增 `check_image_file_size_range`（`min_size` + `max_size`） |
| 同名函数（如 `check_jpeg_format`、`check_image_dimensions`） | 在不同模块重复定义，后续扩展易混淆 | 新增统一命名版本（如 `_l2_atomic` 后缀）并在任务 JSON 中固定引用 |

#### 6.6.3 L2 已实现补强评测器清单（按任务）

| 任务 | 建议新增 evaluator | 主要校验点 |
|---|---|---|
| L2-1 | `check_subject_scale_and_center`、`check_soft_shadow_presence` | 主体占比/居中、阴影存在与位置 |
| L2-2 | `check_white_background_ratio`、`check_soft_shadow_presence` | 白底占比、阴影层效果 |
| L2-4 | `check_top_title_bar_and_text` | 顶部条区域参数 + 标题区域文本 |
| L2-5 | `check_safe_margin_layout`、`check_icon_presence_region` | 安全边距、Logo 区域存在 |
| L2-8 | `check_perspective_overlay_region` | 指定四点区域透视替换与融合 |
| L2-10 | `check_annotation_callout_count` | 标注对象数量和分布 |

#### 6.6.4 推荐的 L2 评测组合模板

```json
{
  "func": [
    "check_jpeg_format",
    "check_image_dimensions",
    "check_image_file_size_range",
    "check_top_title_bar_and_text",
    "check_text_in_region_keywords",
    "check_xcf_layers_structure"
  ],
  "conj": "and",
  "result": [
    {"type": "vm_file", "path": "...", "dest": "..."},
    {"type": "vm_file", "path": "...", "dest": "..."},
    {"type": "vm_file", "path": "...", "dest": "..."},
    {"type": "vm_file", "path": "...", "dest": "..."},
    {"type": "vm_file", "path": "...", "dest": "..."},
    {"type": "vm_file", "path": "...", "dest": "..."}
  ],
  "expected": [
    null,
    {"type": "rule", "rules": {"width": 1080, "height": 1440}},
    {"type": "rule", "rules": {"max_size": 716800}},
    {"type": "rule", "rules": {"bar_min_ratio": 0.12, "bar_max_ratio": 0.22, "min_darkness_delta": 8}},
    {"type": "rule", "rules": {"regions": ["top_center"], "keywords": ["CITY NIGHT RUN"]}},
    {"type": "rule", "rules": {"layers": ["BG_City", "Title_Bar", "Title_Text"]}}
  ]
}
```

> 注：`check_text_in_region_keywords`、`check_xcf_layers_structure`、`check_image_file_size_range` 及布局类函数已在 `desktop_env/evaluators/metrics/gimp_l2.py` 实现并导出到 `desktop_env/evaluators/metrics/__init__.py`；后续新增任务应优先复用这些通用检查，而不是继续堆积一次性 evaluator。


---

## 7. L3 任务池（细化版，首批 9 个）

L3 任务统一约束：

1. 每个任务至少包含 8 个关键编辑动作，覆盖几何、色彩、图层、文本、导出中的至少 4 类。
2. 每个任务要求交付“成品图 + XCF 工程”，且至少 1 个任务要求双成品导出（如 PNG + JPEG）。
3. 每个任务必须含可脚本化验证点：尺寸、格式、体积、图层命名、文本存在、颜色/对比变化、布局结构等。
4. 评测建议优先使用“1 个场景复合评测器”或“5-8 个原子评测器组合（`conj: and`）”。
5. 任务来源优先采用 GIMP 官方文档和公开教程站点，保证流程可复现。

### 7.1 品牌与海报工作流

#### 任务 L3-1：城市音乐节主视觉海报（双格式交付）

- **ID**：`a3b00001-0001-4000-8000-000000000001`
- **来源**：
  - https://docs.gimp.org/2.10/en/gimp-image-combining.html
  - https://docs.gimp.org/2.10/en/gimp-filter-dropshadow.html
  - https://docs.gimp.org/2.10/en/gimp-tool-curves.html
  - https://daviesmediadesign.com/tutorials/
- **任务场景**：线下活动设计师需要在 30 分钟内产出“可发社媒 + 可返工”的音乐节海报。
- **指令**：使用 `/home/user/Desktop/street_city_466685.jpg` 作为主背景，叠加 `/home/user/Desktop/abstract_shape_1.png` 和 `/home/user/Desktop/pattern_brushed_alum_dark.png` 做氛围层，制作 `2400x3200` 竖版海报。要求整体夜景对比度相对原图至少提升 `6%`；文本必须包含主标题 `CITY MUSIC FEST`、一行含日期+地点的副标题，以及一行同时包含 `LIVE` 与 `NIGHT` 的 CTA；图层结构至少包括 `BG_Base`、`FX_Gradient`、`FX_Texture`、`Title_Main`、`Title_Sub`、`CTA`、`Frame`。导出 `/home/user/Desktop/city_music_poster.png` 与 `/home/user/Desktop/city_music_poster.jpg`（JPEG 小于 1MB），并保存 `/home/user/Desktop/city_music_poster.xcf`。
- **上传素材**：
  - `assets/gimp_task/photos/street_city_466685.jpg` -> `/home/user/Desktop/street_city_466685.jpg`
  - `assets/gimp_task/mask/abstract_shape_1.png` -> `/home/user/Desktop/abstract_shape_1.png`
  - `assets/gimp_task/graphic/pattern_brushed_alum_dark.png` -> `/home/user/Desktop/pattern_brushed_alum_dark.png`
- **评估函数建议**：
  - 方案 A（复合）：`check_l3_city_music_poster_complete`
  - 方案 B（组合）：`[`check_png_format`, `check_jpeg_format`, `check_image_dimensions`, `check_text_in_image_basic`, `check_image_file_size`, `check_xcf_file_exists_and_has_layers`]`
- **需要新评估函数**：❌（已落地 `check_l3_city_music_poster_complete`）

---

#### 任务 L3-2：杂志封面风格人物海报

- **ID**：`a3b00002-0002-4000-8000-000000000002`
- **来源**：
  - https://docs.gimp.org/2.10/en/gimp-tool-crop.html
  - https://docs.gimp.org/2.10/en/gimp-tool-levels.html
  - https://docs.gimp.org/2.10/en/gimp-filter-unsharp-mask.html
  - https://www.gimp.org/tutorials/
- **任务场景**：内容团队需要一个“人物 + 栏目条 + 日期”的杂志封面样稿供提案。
- **指令**：基于 `/home/user/Desktop/portrait_woman_774909.jpg` 设计 `1800x2400` 封面：保留人物主体，保持肤色自然，并将整体对比度相对原图小幅提升；封面文字中必须可见 `STYLE`、`ISSUE`、`2026`；使用分层管理：`Masthead`、`Coverline_1`、`Coverline_2`、`Coverline_3`、`Date_Issue`、`Portrait_Base`、`Color_Grade`。导出 `/home/user/Desktop/mag_cover_portrait.jpg`（小于 900KB）并保存 `/home/user/Desktop/mag_cover_portrait.xcf`。
- **上传素材**：`assets/gimp_task/photos/portrait_woman_774909.jpg` -> `/home/user/Desktop/portrait_woman_774909.jpg`
- **评估函数建议**：`check_l3_mag_cover_complete`（复合）或 6 项原子组合。
- **需要新评估函数**：❌（已落地 `check_l3_mag_cover_complete`）

---

#### 任务 L3-3：品牌 KV 横版与竖版联动导出

- **ID**：`a3b00003-0003-4000-8000-000000000003`
- **状态**：`已删除`
- **删除原因**：双版 KV 一致性主要依赖 `_check_color_tone_consistency` 与区域文本启发式，评测可靠性弱于其它 L3；同时它与海报/品牌主视觉类任务在能力覆盖上重叠明显。

---

### 7.2 电商与商品视觉系统

#### 任务 L3-4：鞋类电商首图 + 卖点角标 + 透明版备份

- **ID**：`a3b00004-0004-4000-8000-000000000004`
- **来源**：
  - https://docs.gimp.org/2.10/en/gimp-layer-color-to-alpha.html
  - https://docs.gimp.org/2.10/en/gimp-filter-dropshadow.html
  - https://docs.gimp.org/2.10/en/gimp-using-web-transparency.html
- **任务场景**：电商运营要求一套“主图 JPEG + 透明 PNG 备份 + XCF 工程”完整交付。
- **指令**：使用 `/home/user/Desktop/product_shoes_2529148.jpg` 产出：
  - 主图 `/home/user/Desktop/shoes_main_listing.jpg`（`1600x1600`，白底，含 `NEW` 角标，< 500KB）
  - 透明备份 `/home/user/Desktop/shoes_cutout.png`（`1600x1600`，主体居中）
  要求图层包含 `Shoes_Product`、`Shadow_Soft`、`Badge_NEW`、`BG_White`；保存 `/home/user/Desktop/shoes_listing_project.xcf`。
- **上传素材**：`assets/gimp_task/products/product_shoes_2529148.jpg` -> `/home/user/Desktop/product_shoes_2529148.jpg`
- **评估函数建议**：`check_l3_shoes_listing_complete`（复合）或 `8` 个原子函数组合（双产物 + XCF + 文本 + 体积）。
- **需要新评估函数**：❌（已落地 `check_l3_shoes_listing_complete`）

---

#### 任务 L3-5：香水品牌详情页主视觉（含质感背景）

- **ID**：`a3b00005-0005-4000-8000-000000000005`
- **来源**：
  - https://docs.gimp.org/2.10/en/gimp-image-combining.html
  - https://docs.gimp.org/2.10/en/gimp-layer-mask-add.html
  - https://docs.gimp.org/2.10/en/gimp-tool-curves.html
- **任务场景**：品牌站详情页需要“高级质感”首屏图，强调产品与材质融合。
- **指令**：用 `/home/user/Desktop/product_perfume_965989.jpg` + `/home/user/Desktop/texture_concrete_129733.jpg` + `/home/user/Desktop/texture_metal_220182.jpg` 制作 `2200x1400` 主视觉。要求：产品为视觉焦点，背景至少两层材质混合，局部光效增强瓶身，整体对比度和饱和度相对原图均小幅提升，且文案中必须包含 `ESSENCE` 与 `PREMIUM`；图层命名 `Perfume_Main`、`BG_Concrete`、`BG_Metal`、`Light_Glow`、`Title`、`Subtitle`。导出 `/home/user/Desktop/perfume_hero_banner.png`，保存 `/home/user/Desktop/perfume_hero_banner.xcf`。
- **上传素材**：
  - `assets/gimp_task/products/product_perfume_965989.jpg` -> `/home/user/Desktop/product_perfume_965989.jpg`
  - `assets/gimp_task/texture/texture_concrete_129733.jpg` -> `/home/user/Desktop/texture_concrete_129733.jpg`
  - `assets/gimp_task/texture/texture_metal_220182.jpg` -> `/home/user/Desktop/texture_metal_220182.jpg`
- **评估函数建议**：`check_l3_perfume_hero_complete`（复合）
- **需要新评估函数**：❌（已落地 `check_l3_perfume_hero_complete`）

---

#### 任务 L3-6：相机产品页三图组合（主图 + 细节图 + 参数图）

- **ID**：`a3b00006-0006-4000-8000-000000000006`
- **来源**：
  - https://docs.gimp.org/2.10/en/gimp-image-guides.html
  - https://docs.gimp.org/2.10/en/gimp-layer-groups.html
  - https://docs.gimp.org/2.10/en/gimp-filter-unsharp-mask.html
- **任务场景**：详情页要求一次性交付三张风格统一的图片，减少重复修图成本。
- **指令**：基于 `/home/user/Desktop/product_camera_90946.jpg` 生成三张图（均 `1600x1600`）：
  1. 主图 `/home/user/Desktop/camera_detail_main.jpg`
  2. 细节特写图 `/home/user/Desktop/camera_detail_closeup.jpg`
  3. 参数标注图 `/home/user/Desktop/camera_detail_specs.jpg`
  三图要求统一调色和边距；参数图至少包含 `3` 处标注，且文字中必须可见 `LENS`、`SENSOR`、`ISO`。保存统一工程 `/home/user/Desktop/camera_detail_pack.xcf`，图层组含 `Main_View`、`Closeup_View`、`Specs_View`。
- **上传素材**：`assets/gimp_task/products/product_camera_90946.jpg` -> `/home/user/Desktop/product_camera_90946.jpg`
- **评估函数建议**：`check_l3_camera_detail_pack_complete`（复合多文件评测）
- **需要新评估函数**：❌（已落地 `check_l3_camera_detail_pack_complete`）

---

### 7.3 教学与修复工作流

#### 任务 L3-7：风景“前后对比 + 步骤总览”教学素材包

- **ID**：`a3b00007-0007-4000-8000-000000000007`
- **来源**：
  - https://www.gimp.org/tutorials/Blending_Exposures/
  - https://docs.gimp.org/2.10/en/gimp-tool-levels.html
  - https://docs.gimp.org/2.10/en/gimp-tool-curves.html
- **任务场景**：讲师需要一次交付“步骤图 + 总览图 + 工程文件”用于课堂演示。
- **指令**：用 `/home/user/Desktop/architecture_247431.jpg` 生成 3 个文件：
  - `step1_base.jpg`（原图加说明）
  - `step2_grade.jpg`（调色后加说明，且相对原图明显提升对比度与饱和度）
  - `step3_compare.jpg`（前后对比拼图）
  并合成总览图 `/home/user/Desktop/architecture_tutorial_overview.png`（三栏布局，包含 `STEP 1`、`STEP 2`、`STEP 3` 标题）。所有文案和步骤编号必须可见；保存 `/home/user/Desktop/architecture_tutorial_pack.xcf`。
- **上传素材**：`assets/gimp_task/photos/architecture_247431.jpg` -> `/home/user/Desktop/architecture_247431.jpg`
- **评估函数建议**：`check_l3_tutorial_pack_complete`（复合）
- **需要新评估函数**：❌（已落地 `check_l3_tutorial_pack_complete`）

---

#### 任务 L3-8：宠物写真精修与背景替换

- **ID**：`a3b00008-0008-4000-8000-000000000008`
- **来源**：
  - https://docs.gimp.org/2.10/en/gimp-layer-mask-add.html
  - https://docs.gimp.org/2.10/en/gimp-tool-heal.html
  - https://docs.gimp.org/2.10/en/gimp-filter-unsharp-mask.html
- **任务场景**：宠物摄影客户要求交付“自然背景版 + 纯色背景版”两种风格。
- **指令**：使用 `/home/user/Desktop/pet_dog_1108099_alt.jpg` 和 `/home/user/Desktop/texture_wood_172289.jpg` 产出两张 `1800x2400` 图：
  - 自然风格 `/home/user/Desktop/dog_portrait_natural.jpg`
  - 纯色商业风 `/home/user/Desktop/dog_portrait_clean.png`
  要求：两种风格需明显不同；自然版相对原图的整体对比度至少提升 `4%`，并增强毛发细节；自然版右下角添加包含 `BY` 的作者签名。保存 `/home/user/Desktop/dog_portrait_project.xcf`，图层至少含 `Dog_Subject`、`BG_Natural`、`BG_Clean`、`Detail_Enhance`、`Signature`。
- **上传素材**：
  - `assets/gimp_task/photos/pet_dog_1108099_alt.jpg` -> `/home/user/Desktop/pet_dog_1108099_alt.jpg`
  - `assets/gimp_task/texture/texture_wood_172289.jpg` -> `/home/user/Desktop/texture_wood_172289.jpg`
- **评估函数建议**：`check_l3_dog_portrait_dual_output_complete`（复合）
- **需要新评估函数**：❌（已落地 `check_l3_dog_portrait_dual_output_complete`）

---

#### 任务 L3-9：旧图修复海报化交付

- **ID**：`a3b00009-0009-4000-8000-000000000009`
- **来源**：
  - https://docs.gimp.org/2.10/en/gimp-tool-heal.html
  - https://docs.gimp.org/2.10/en/gimp-tool-curves.html
  - https://docs.gimp.org/2.10/en/gimp-filter-unsharp-mask.html
- **任务场景**：历史社媒素材质量较差，需要修复后再做成活动宣发图。
- **指令**：使用 `/home/user/Desktop/beach_people_1481105.jpg` 完成瑕疵修复与色调统一，并制作 `2000x1200` 活动横幅。要求相对原图小幅提升对比度和锐度，且文案中必须可见 `SUMMER` 与 `2026`；输出 `/home/user/Desktop/beach_restore_banner.jpg`（< 800KB）与工程 `/home/user/Desktop/beach_restore_banner.xcf`，图层至少含 `Restore_Base`、`Color_Grade`、`Title`、`Meta_Info`。
- **上传素材**：`assets/gimp_task/photos/beach_people_1481105.jpg` -> `/home/user/Desktop/beach_people_1481105.jpg`
- **评估函数建议**：`check_l3_restore_banner_complete`（复合）
- **需要新评估函数**：❌（已落地 `check_l3_restore_banner_complete`）

---

#### 任务 L3-10：透明通道课程封面与信息图组合

- **ID**：`a3b00010-0010-4000-8000-000000000010`
- **来源**：
  - https://docs.gimp.org/2.10/en/gimp-using-web-transparency.html
  - https://docs.gimp.org/2.10/en/gimp-layer-mask-menu.html
  - https://docs.gimp.org/2.10/en/gimp-layer-color-to-alpha.html
- **任务场景**：在线课程需要“课程封面 + 一页信息图”两张配套视觉。
- **指令**：使用 `/home/user/Desktop/wikimedia_transparency_demo.png`、`/home/user/Desktop/pattern_asfalt_light.png`、`/home/user/Desktop/icon_camera.svg` 产出：
  - 课程封面 `/home/user/Desktop/transparency_course_cover.png`（`1600x900`，封面文字必须包含 `TRANSPARENCY` 与 `COURSE`）
  - 信息图 `/home/user/Desktop/transparency_course_infographic.png`（`1600x2000`，至少包含 `4` 个步骤模块）
  两图需统一主题色和字体层级。工程保存 `/home/user/Desktop/transparency_course_assets.xcf`，图层组含 `Cover_Group`、`Infographic_Group`、`Icons_Group`、`Text_Group`。
- **上传素材**：
  - `assets/gimp_task/graphic/wikimedia_transparency_demo.png` -> `/home/user/Desktop/wikimedia_transparency_demo.png`
  - `assets/gimp_task/graphic/pattern_asfalt_light.png` -> `/home/user/Desktop/pattern_asfalt_light.png`
  - `assets/gimp_task/graphic/icon_camera.svg` -> `/home/user/Desktop/icon_camera.svg`
- **评估函数建议**：`check_l3_transparency_course_assets_complete`（复合）
- **需要新评估函数**：❌（已落地 `check_l3_transparency_course_assets_complete`）

---

### 7.4 L3 已实现复合评测器（确保可脚本验证）

| 评测器（建议名） | 覆盖任务 | 核心验证维度 | result / expected |
|---|---|---|---|
| `check_l3_city_music_poster_complete` | L3-1 | PNG+JPG 双导出、尺寸、文本存在、XCF 图层、JPEG 体积 | `result_paths` / `rule` |
| `check_l3_mag_cover_complete` | L3-2 | 封面尺寸、文本密度、对比提升、XCF 图层结构 | `result_paths` / `rule` |
| `check_l3_shoes_listing_complete` | L3-4 | 白底主图 + 透明备份、角标文本、体积、图层 | `result_paths` / `rule` |
| `check_l3_perfume_hero_complete` | L3-5 | 多材质融合、标题文本、尺寸、XCF 层命名 | `result_paths` / `rule` |
| `check_l3_camera_detail_pack_complete` | L3-6 | 三张规格图完整性、尺寸一致、标注文本、XCF 组 | `result_paths` / `rule` |
| `check_l3_tutorial_pack_complete` | L3-7 | 步骤图数量、总览图布局、步骤文本、XCF 工程 | `result_paths` / `rule` |
| `check_l3_dog_portrait_dual_output_complete` | L3-8 | 双风格导出、尺寸、细节增强（锐度/对比）、签名文本、XCF | `result_paths` / `rule` |
| `check_l3_restore_banner_complete` | L3-9 | 修复后横幅质量、文本信息区、体积、XCF | `result_paths` / `rule` |
| `check_l3_transparency_course_assets_complete` | L3-10 | 封面+信息图双产物、步骤模块数量、图层组命名 | `result_paths` / `rule` |

L3 评测器维护建议（统一模式）：

1. 复用已有原子函数作为子检查：`check_png_format`、`check_jpeg_format`、`check_image_dimensions`、`check_image_file_size`、`check_text_in_image_basic`、`check_xcf_file_exists_and_has_layers`。
2. 在新复合函数内按权重聚合得分（例如必选项失败直接 0，非关键项按比例扣分），输出 0-1 分数。
3. 多产物任务统一使用 `result_paths` 约定顺序，避免 JSON 和评测实现错位。
4. 对“布局类”验证统一增加轻量几何规则（区域占比/文本区位置/分栏边界），避免只靠 OCR 弱特征。

---

## 8. 每层示例任务模板（供 JSON 编写）

### 8.1 L1 模板

- 任务目标：单操作验证。
- 输入：1 张图片。
- 输出：1 个导出文件。
- 评测：1-2 个原子函数。

### 8.2 L2 模板

- 任务目标：场景化复合任务（至少 4 个关键编辑动作）。
- 输入：1-3 个素材（可含纹理/图标辅助素材）。
- 输出：1 张成品图 + 1 个 XCF（建议默认必选）。
- 评测：3-6 个原子函数，必要时增加 1 个结构类复合函数，`conj: and`。

### 8.3 L3 模板

- 任务目标：完整商业交付工作流（多阶段编辑 + 多产物交付）。
- 输入：2-5 个素材（主图、纹理、图标、遮罩等）。
- 输出：成品图（必选）+ 工程文件（必选）+ 1-2 个衍生图（建议）。
- 评测：优先 1 个复合函数；或 5-8 个原子函数 + 1 个结构校验函数，`conj: and`。

### 8.4 Interactive 任务草案（GIMP，完全可验证版）

这一版不再把“必须复用现有 evaluator”当成前提。允许新增 evaluator，但必须满足下面三条：

1. 验收条件必须是确定性的，能用脚本稳定判断，不依赖人工审美。
2. evaluator 优先检查几何尺寸、颜色模式、透明度、图层命名、局部区域变化、文本区域存在、标注数量、前后对比度/锐度变化等硬信号。
3. interactive 只改变多轮交互节奏；最终交付规格必须收敛到一个清晰、可计算的目标状态。

因此，这 6 个任务的设计原则是：

1. 能直接复用现有复合 evaluator 的，优先复用，因为稳定性最高。
2. 如果现有 evaluator 不够，但任务本身仍然可验证，则允许补充新的专用 evaluator。
3. 不再使用 gold image 逐像素匹配作为主方案。

先对齐当前 `evaluation_examples/examples/interactive/` 里的触发写法：

1. “step” 类中断触发，在现有样例中实际写作 `step_count`。
2. “agent_done” 类阶段推进触发，适合先交初稿、再继续细化。
3. “ask” 类澄清触发，在现有样例中实际写作 `agent_asks`。

下面给出 6 个 GIMP interactive 任务，全部都能直接复用已有 evaluator。

#### 8.4.1 IGI-1 手表主图做到一半，临时被要求改成平台白底标准图

- 建议 ID：`interactive_gimp_watch_white_standard_interruption_001`
- 触发方式：`step_count`
- 场景类型：`interruption`
- 真实场景：运营先让设计随手修一版商品图，中途又说平台审核必须走白底标准图规范。
- 复用素材：`assets/gimp_task/products/product_watch_190819.jpg`
- 初始打开：`gimp /home/user/Desktop/product_watch_190819.jpg`
- phases 草案：
  1. Phase 1：先按普通商品图思路开始处理。触发 `step_count`，建议值 4。
  2. Phase 2：中途改口，最终必须做成 1600x1600 白底平台主图，手表居中，对比度至少提升 8%，并带轻微投影。触发 `agent_done`。
  3. Phase 3：导出 `/home/user/Desktop/watch_white_standard.jpg`，保存 `/home/user/Desktop/watch_white_standard.xcf`，图层名必须是 `Watch_Main`、`Shadow_Soft`、`BG_White`。触发 `agent_done`。
- 最终评测：可直接复用 `check_l2_watch_white_standard_complete`
- 可验证性来源：尺寸、白底占比、对比度提升、阴影存在、XCF 图层命名，全部是硬约束。
- 如需单独拆 evaluator：可拆成 `check_jpeg_format` + `check_image_dimensions` + `check_white_background_ratio` + `check_soft_shadow_presence` + `check_contrast_increase` + `check_xcf_layers_structure`。

#### 8.4.2 IGI-2 城市活动图做了一半，被要求切成夜跑封面规范

- 建议 ID：`interactive_gimp_city_night_run_interruption_001`
- 触发方式：`step_count`
- 场景类型：`requirement_change`
- 真实场景：市场同学先说做张城市宣传图，做到一半又补成“夜跑活动封面”，并给出明确标题和版式要求。
- 复用素材：`assets/gimp_task/photos/street_city_466685.jpg`
- 初始打开：`gimp /home/user/Desktop/street_city_466685.jpg`
- phases 草案：
  1. Phase 1：先按普通城市活动图开始处理。触发 `step_count`，建议值 5。
  2. Phase 2：中途补充最终要求：裁成 1080x1440，整体增强对比和饱和度，在顶部加入深色半透明标题栏和 `CITY NIGHT RUN` 文案。触发 `agent_done`。
  3. Phase 3：导出 `/home/user/Desktop/city_night_run_cover.jpg`，保存 `/home/user/Desktop/city_night_run_cover.xcf`，图层名必须是 `BG_City`、`Title_Bar`、`Title_Text`。触发 `agent_done`。
- 最终评测：可直接复用 `check_l2_city_night_run_cover_complete`
- 可验证性来源：尺寸、文件大小、对比度/饱和度提升、顶部标题栏、文本区域、XCF 图层命名均已实现。
- 如需新增专用 evaluator：也可把“顶栏存在”和“`CITY NIGHT RUN` 文本存在”拆成更细粒度规则，仍然完全可验证。

#### 8.4.3 IGI-3 香水透明主图按阶段交付，先看草稿再看正式版

- 建议 ID：`interactive_gimp_perfume_listing_workflow_001`
- 触发方式：`agent_done`
- 场景类型：`multi_step_workflow`
- 真实场景：品牌方常先看抠图和摆位草稿，确认后再要求导出正式透明电商图。
- 复用素材：`assets/gimp_task/products/product_perfume_965989.jpg`
- 初始打开：`gimp /home/user/Desktop/product_perfume_965989.jpg`
- phases 草案：
  1. Phase 1：先做透明主图草稿，我先看主体位置。触发 `agent_done`。
  2. Phase 2：通过后按正式要求收口：1200x1200 透明画布，商品居中，占画面高度约 70%-80%，并加柔和阴影。触发 `agent_done`。
  3. Phase 3：导出 `/home/user/Desktop/perfume_listing.png`，保存 `/home/user/Desktop/perfume_listing.xcf`，图层名必须是 `Product`、`Shadow`、`Guide_BG`。触发 `agent_done`。
- 最终评测：可直接复用 `check_l2_perfume_listing_complete`
- 可验证性来源：透明通道、主体尺寸占比、居中程度、阴影、XCF 图层命名均已实现脚本化检查。
- 这是非常适合 interactive 的任务，因为“先看草稿再收口正式版”很真实，同时最终指标完全客观。

#### 8.4.5 IGI-5 用户先模糊说要电商图，澄清后收敛到白底手表主图

- 建议 ID：`interactive_gimp_watch_white_standard_ambiguous_001`
- 触发方式：`agent_asks`
- 场景类型：`ambiguous_instruction`
- 真实场景：商家只会说“帮我做个能上架的主图”，通常不会一开始说明平台规格、背景要求和图层交付要求。
- 复用素材：`assets/gimp_task/products/product_watch_190819.jpg`
- 初始打开：`gimp /home/user/Desktop/product_watch_190819.jpg`
- phases 草案：
  1. Phase 1：用户先说“帮我把这张手表图做成能上架的平台主图”。触发 `agent_asks`。
  2. Phase 2：澄清后给出明确要求：1600x1600 白底、手表居中、对比度提升至少 8%、带轻微投影。触发 `agent_done`。
  3. Phase 3：导出 `/home/user/Desktop/watch_white_standard.jpg`，保存 `/home/user/Desktop/watch_white_standard.xcf`，图层名必须是 `Watch_Main`、`Shadow_Soft`、`BG_White`。触发 `agent_done`。
- 最终评测：可直接复用 `check_l2_watch_white_standard_complete`
- 可验证性来源：和 IGI-1 相同，最终规格完全一致，只是第一轮通过追问拿到明确需求。
- 这个任务说明了一点：`agent_asks` 并不要求新增 evaluator；真正决定可验证性的，是澄清后能否收敛成确定输出。

#### 8.4.6 IGI-6 用户先模糊说做说明图，澄清后收敛到相机标注图

- 建议 ID：`interactive_gimp_camera_annotation_ambiguous_001`
- 触发方式：`agent_asks`
- 场景类型：`ambiguous_instruction`
- 真实场景：客服或培训同学常只会说“帮我做张相机说明图”，但不会先把要标哪些部位和底部说明条说清楚。
- 复用素材：`assets/gimp_task/products/product_camera_90946.jpg`
- 初始打开：`gimp /home/user/Desktop/product_camera_90946.jpg`
- phases 草案：
  1. Phase 1：用户先说“帮我做一张相机说明图”。触发 `agent_asks`。
  2. Phase 2：澄清后给出最终要求：保持原分辨率，标注 `Lens`、`Grip`、`Mode Dial` 三个 callout，并在底部加半透明说明栏。触发 `agent_done`。
  3. Phase 3：导出 `/home/user/Desktop/camera_annotation.png`，保存 `/home/user/Desktop/camera_annotation.xcf`，图层名必须是 `Base_Image`、`Callout_1`、`Callout_2`、`Callout_3`、`Footer_Note`。触发 `agent_done`。
- 最终评测：可直接复用 `check_l2_camera_annotation_complete`
- 可验证性来源：分辨率、callout 数量、底部说明区、文本区域、XCF 图层命名已有现成 evaluator。
- 若后续想减少 OCR 依赖，可以新增一个更严格的 `camera_annotation` evaluator，把三个 callout 的目标区域和底栏区域写成几何规则，而不是放宽到通用文本检测。

### 8.5 Interactive 任务编写建议（针对 GIMP，允许新增 evaluator）

1. interactive 版本可以复用已有 L2/L3 evaluator，也可以新增 evaluator；关键不是“新不新”，而是“验收条件是否确定”。
2. 适合新增 evaluator 的任务，应当落在可量化能力上，例如：画布尺寸、白底比例、透明像素比例、主体中心偏移、矩形标注框位置、标题栏区域占比、图层名集合、导出格式和文件大小。
3. 不适合新增 evaluator 的任务，是那些核心目标依赖主观视觉判断的，例如“更高级”“更像杂志大片”“更有品牌感”。
4. `step_count` 任务最适合做“中途改规格但最终要求明确”的场景，因为第二阶段可以直接补充完整参数。
5. `agent_asks` 任务必须故意缺少关键可验证参数，例如尺寸、背景、输出路径、是否透明、图层名要求；否则追问行为没有必要性。
6. 如果需要新增 evaluator，优先写成“若干原子检查 + 一个轻量复合函数”的形式，避免重新引入大而不稳的黑盒判断。
7. 如果某个任务最终不得不依赖 gold image、逐像素匹配或纯 OCR 才能判断，那它通常不适合作为 GIMP interactive 首批任务。

---

## 9. gimp_task 首版落地计划（草稿）

### 9.1 第一批任务规模

1. L1：16 个
2. L2：9 个
3. L3：9 个

合计 34 个，当前版本已完成首轮清理：删除 4 个重复或弱可验证任务，保留任务均已落到 `evaluation_examples/examples/gimp_task/`。

### 9.2 实施顺序

1. 先稳定 L1 原子任务与通用导出后处理。
2. 再落地可稳定验证的 L2/L3 复合任务。
3. 对保留任务做持续回归，避免重新引入重复主题和弱评测。

### 9.3 验收标准

1. 每个任务至少完成一次人工演练。
2. 每个任务在评测脚本下可重复通过（低随机性）。
3. 输出路径、文件名、格式约束统一。

---

## 10. 风险与规避

1. 文本检测误判：
- 规避：优先检测文本区域变化与颜色块，不强依赖 OCR。

2. XCF 解析依赖不稳定：
- 规避：设计“严格校验 + 退化校验”双模式。

3. 导出参数导致轻微像素差异：
- 规避：使用阈值评估（尺寸、直方图、SSIM 区间），避免像素级全等。

4. 任务描述歧义：
- 规避：每个任务明确输入路径、输出路径、尺寸/比例/格式。

---

## 11. 本草稿下一步

1. 优先为保留的 34 个任务补充一次自动回归执行记录。
2. 如需扩容，优先补“能力新增型”任务，不再补与现有任务高度相似的教学卡片或多版式变体。
3. 如需继续扩展，可单独补一份 `gimp_task_eval_plan.md`，列出每个任务对应评测函数和参数。
