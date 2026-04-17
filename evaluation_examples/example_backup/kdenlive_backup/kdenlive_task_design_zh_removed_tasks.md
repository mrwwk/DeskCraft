# Kdenlive 任务设计文档移除任务备份

日期：`2026-04-03`

本备份文件收录了从 `evaluation_examples/examples/kdenlive/kdenlive_task_design_zh.md` 中移除的 15 个任务，按难度保持相对平衡：Level 1 删除 5 个，Level 2 删除 5 个，Level 3 删除 5 个。

对应的任务 JSON 文件已移动到：`evaluation_examples/examples/kdenlive/backup/json/`

移除原则：

- 优先移除评测价值偏低、仅验证细碎 UI 状态的任务。
- 优先移除与现有任务高度重复、只是已有能力加一层轻量包装的任务。
- 尽量保留更核心的剪辑、时间线、渲染与音视频联合编辑能力。

---

## Level 1

### 任务 1-8：使用指定名称保存项目

移除原因：仅检查文件存在与 XML 有效性，任务过于基础，和一般“保存项目”能力高度重叠。

#### 任务 1-8：使用指定名称保存项目

- **任务 JSON 文件 ID**：`3d732f75-67af-4461-bd73-ac4c84887a28.json`
- **操作说明**：请帮我在 Kdenlive 里完成这个需求：新建项目并保存为 `/home/user/Videos/my_first_project.kdenlive`。
- **来源标注**：Kdenlive 官方手册（File Menu）：https://docs.kdenlive.org/en/user_interface/menu/file_menu.html
- **上传资源**：无
- **评测器**：`check_kdenlive_file_exists`（**新增**）
  - 仅检查指定路径文件是否存在，且为有效 MLT XML
- **result**：`vm_file` → `/home/user/Videos/my_first_project.kdenlive`
- **expected**：`rule` → `{"valid_xml": true}`
- **需要新评测器**：✅

---

### 任务 1-11：在项目箱创建文件夹

移除原因：更偏向项目箱组织操作，编辑能力覆盖面有限，实用性与区分度都偏弱。

#### 任务 1-11：在项目箱创建文件夹

- **任务 JSON 文件 ID**：`f1046974-df6f-406b-8d16-a71efbdea473.json`
- **操作说明**：请帮我在 Kdenlive 里完成这个需求：在项目箱中新建名为 “Footage” 的文件夹，然后保存到 `/home/user/Videos/project.kdenlive`。
- **来源标注**：Kdenlive 官方手册（Project Bin Folders）：https://docs.kdenlive.org/en/project_and_asset_management/project_bin/project_bin_use_folders.html
- **上传资源**：无
- **评测器**：`check_kdenlive_bin_folder`（**新增**）
  - 检查项目 XML 中的 `<property name="kdenlive:folderName">` 或 `<kdenlive_folder>` 元素
- **result**：`vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**：`rule` → `{"expected_folder": "Footage"}`
- **需要新评测器**：✅

---

### 任务 1-15：通过导标/标记设置时间线点位

移除原因：导标属于较窄的辅助功能，和核心剪辑、编排、导出链路关联较弱。

#### 任务 1-15：通过导标/标记设置时间线点位

- **任务 JSON 文件 ID**：`9ada9410-319f-41f9-bbe6-d04a7fa42541.json`
- **操作说明**：请帮我在 Kdenlive 里完成这个需求：在时间线 00:00:05:00（5 秒）添加一个名为 “Scene Start” 的导标，然后保存到 `/home/user/Videos/project.kdenlive`。
- **来源标注**：Kdenlive 官方手册（Timeline Markers）：https://docs.kdenlive.org/en/cutting_and_assembling/guides.html#add-guides
- **上传资源**：无
- **评测器**：`check_kdenlive_guide`（**新增**）
  - 解析 `<property name="kdenlive:docproperties.guides">` 的 JSON 数组，按时间和注释匹配
- **result**：`vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**：`rule` → `{"guide_comment": "Scene Start", "guide_time_seconds": 5.0, "tolerance": 0.5}`
- **需要新评测器**：✅

---

### 任务 1-21：创建图片序列/幻灯片来源（截图）

移除原因：任务产物主要落在项目外部 PNG 文件上，和当前 `.kdenlive` 项目评测体系不够一致，稳定性也偏弱。

#### 任务 1-21：创建图片序列/幻灯片来源（截图）

- **任务 JSON 文件 ID**：`e337a827-fd4d-4303-b1e0-0cd38cce8ccc.json`
- **操作说明**：请帮我在 Kdenlive 里完成这个需求：导入 `/home/user/Videos/15368811_1920_1080_30fps.mp4`，使用“提取帧”或片段监视器截图并保存，然后保存项目到 `/home/user/Videos/project.kdenlive`。
- **来源标注**：Kdenlive 官方手册（Clip Monitor - Extract Frame）：https://docs.kdenlive.org/en/user_interface/monitors/clip_monitor.html
- **上传资源**：`15368811_1920_1080_30fps.mp4` → `/home/user/Videos/`
- **评测器**：`check_kdenlive_snapshot_exists`（**新增**）
  - 使用 `vm_command_line` 检查预期目录中是否存在截图图片
- **result**：`vm_command_line` → `ls /home/user/Videos/*.png 2>/dev/null | wc -l`
- **expected**：`rule` → `{"min_count": 1}`
- **需要新评测器**：✅

---

### 任务 1-23：设置项目预览分辨率

移除原因：与项目分辨率、帧率类设置任务重复度较高，属于边缘配置项，优先级低。

#### 任务 1-23：设置项目预览分辨率

- **任务 JSON 文件 ID**：`439e0cb1-3da3-447a-b781-5caf5136a8e6.json`
- **操作说明**：请帮我在 Kdenlive 里完成这个需求：进入项目设置并将预览分辨率设为 720×480，然后保存到 `/home/user/Videos/project.kdenlive`。
- **来源标注**：Kdenlive 官方手册（Project Settings - General）：https://docs.kdenlive.org/en/project_and_asset_management/project_settings/general_settings.html
- **上传资源**：无
- **评测器**：`check_kdenlive_project_profile`（复用：检查预览 profile 属性）
- **result**：`vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**：`rule` → `{"preview_width": 720, "preview_height": 480}`
- **需要新评测器**：❌（扩展已有 `check_kdenlive_project_profile`）

---

## Level 2

### 任务 2-7：对视频应用模糊效果

移除原因：与灰度、旋转、透明度这类效果任务一起看时，属于通用“加一个视频效果”的重复变体。

#### 任务 2-7：对视频应用模糊效果

- **任务 JSON 文件 ID**：`9f99251e-6e8f-4ed2-8668-d2c48367e096.json`
- **操作说明**：请帮我在 Kdenlive 里完成这个需求：导入 `/home/user/Videos/15368811_1920_1080_30fps.mp4` 并添加到时间线，对片段应用 “Box Blur” 或 “Blur” 效果，然后保存到 `/home/user/Videos/project.kdenlive`。
- **来源标注**：Kdenlive 官方手册（Video Effects - Blur and Sharpen）：https://docs.kdenlive.org/en/effects_and_filters/video_effects/blur_and_sharpen.html
- **上传资源**：`15368811_1920_1080_30fps.mp4` → `/home/user/Videos/`
- **评测器**：`check_kdenlive_effect_applied`（**新增**）
  - 通用特效检查：在 `<filter>` 中匹配 `mlt_service`
- **result**：`vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**：`rule` → `{"effect_service": ["box_blur", "boxblur", "blur"], "source_file": "15368811_1920_1080_30fps.mp4"}`
- **需要新评测器**：✅

---

### 任务 2-9：将视频旋转 90 度

移除原因：本质上仍是参数化特效任务，和透明度、PiP 的 Transform 类能力重叠明显。

#### 任务 2-9：将视频旋转 90 度

- **任务 JSON 文件 ID**：`003b7be6-4535-4980-b603-c52292b79c6e.json`
- **操作说明**：请帮我在 Kdenlive 里完成这个需求：导入 `/home/user/Videos/6533277-hd_1920_1080_24fps.mp4` 并添加到时间线，应用 “Rotate (keyframable)” 或 “Transform” 效果，将其顺时针旋转 90 度，然后保存到 `/home/user/Videos/project.kdenlive`。
- **来源标注**：Kdenlive 官方手册（Transform）：https://docs.kdenlive.org/en/effects_and_filters/video_effects/transform_distort_perspective/transform.html
- **上传资源**：`6533277-hd_1920_1080_24fps.mp4` → `/home/user/Videos/`
- **评测器**：`check_kdenlive_effect_param`（**新增**）
  - 检查 rotate/affine/qtblend 相关过滤器与旋转参数
- **result**：`vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**：`rule` → `{"effect_service": ["rotate", "affine", "qtblend"], "param_name": "rotate", "expected_value": 90, "tolerance": 5}`
- **需要新评测器**：✅

---

### 任务 2-15：复制并粘贴时间线片段

移除原因：更多是在验证复制粘贴这一表层交互，和时间线排布、片段计数任务高度相似。

#### 任务 2-15：复制并粘贴时间线片段

- **任务 JSON 文件 ID**：`cdd648e0-4ab6-4391-af4d-5075eaceea81.json`
- **操作说明**：请帮我在 Kdenlive 里完成这个需求：导入 `/home/user/Videos/6533277-hd_1920_1080_24fps.mp4`，放到 V1，再将该片段复制并紧接原片段粘贴到同一轨道，使视频连续播放两次，然后保存到 `/home/user/Videos/project.kdenlive`。
- **来源标注**：Kdenlive 官方手册（Right-Click Menu - Copy/Paste）：https://docs.kdenlive.org/en/cutting_and_assembling/right_click_menu.html
- **上传资源**：`6533277-hd_1920_1080_24fps.mp4` → `/home/user/Videos/`
- **评测器**：`check_kdenlive_clip_count`（**新增**）
  - 统计所有时间线 playlist 中引用该源文件 producer 的 `<entry>` 数量
- **result**：`vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**：`rule` → `{"source_file": "6533277-hd_1920_1080_24fps.mp4", "min_count": 2}`
- **需要新评测器**：✅

---

### 任务 2-16：在时间线分组片段

移除原因：主要验证分组元数据，属于较窄的编辑器组织能力，代表性不如剪切、转场、合成等核心任务。

#### 任务 2-16：在时间线分组片段

- **任务 JSON 文件 ID**：`383b7e01-d1e1-44ce-9eb4-ab50489a4235.json`
- **操作说明**：请帮我在 Kdenlive 里完成这个需求：导入 `/home/user/Videos/6533277-hd_1920_1080_24fps.mp4` 与 `/home/user/Music/mixkit-fast-rocket-whoosh-1714.wav`，分别放到 V1 与 A1，选中两段并分组，然后保存到 `/home/user/Videos/project.kdenlive`。
- **来源标注**：Kdenlive 官方手册（Grouping）：https://docs.kdenlive.org/en/cutting_and_assembling/grouping.html
- **上传资源**：`6533277-hd_1920_1080_24fps.mp4` → `/home/user/Videos/` + `mixkit-fast-rocket-whoosh-1714.wav` → `/home/user/Music/`
- **评测器**：`check_kdenlive_clip_group`（**新增**）
  - 检查 `<group>` 或 `<property name="kdenlive:group">` 是否关联多个片段
- **result**：`vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**：`rule` → `{"min_groups": 1, "min_clips_in_group": 2}`
- **需要新评测器**：✅

---

### 任务 2-17：调整片段不透明度/透明度

移除原因：依旧是 Transform/Opacity 参数调节，与旋转、PiP 等任务存在明显重复。

#### 任务 2-17：调整片段不透明度/透明度

- **任务 JSON 文件 ID**：`487c5d2e-b9bc-4d3f-871c-605414caf2ab.json`
- **操作说明**：请帮我在 Kdenlive 里完成这个需求：导入 `/home/user/Videos/15368811_1920_1080_30fps.mp4` 并添加到时间线，应用 “Opacity”（或使用 “Transform”）并将不透明度设为 50%，然后保存到 `/home/user/Videos/project.kdenlive`。
- **来源标注**：Kdenlive 官方手册（Transform / Opacity）：https://docs.kdenlive.org/en/effects_and_filters/video_effects/transform_distort_perspective/transform.html
- **上传资源**：`15368811_1920_1080_30fps.mp4` → `/home/user/Videos/`
- **评测器**：`check_kdenlive_effect_param`（复用）
  - 检查 transform/qtblend/affine 过滤器中的 opacity 参数
- **result**：`vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**：`rule` → `{"effect_service": ["qtblend", "affine", "frei0r.transparency"], "param_name": "opacity", "expected_value": 0.5, "tolerance": 0.1}`
- **需要新评测器**：❌（复用 `check_kdenlive_effect_param`）

---

## Level 3

### 任务 3-4：应用效果并渲染（综合任务）

移除原因：本质上是“灰度 + 音量 + 渲染”的组合包装，和已有基础效果、音量、渲染任务重叠较多。

#### 任务 3-4：应用效果并渲染（综合任务）

- **任务 JSON 文件 ID**：`07186918-9646-45af-805b-2a13c02ac63f.json`
- **操作说明**：请帮我在 Kdenlive 里完成这个需求：导入 `/home/user/Videos/13590137_3840_2160_60fps.mp4`，加到时间线，应用灰度效果，将音量设置为 30%，保存项目到 `/home/user/Videos/project.kdenlive`，再渲染到 `/home/user/Videos/output.mp4`。
- **来源标注**：Kdenlive 官方手册（Effects and Filters + Volume + Rendering）：https://docs.kdenlive.org/en/effects_and_filters.html；https://docs.kdenlive.org/en/effects_and_filters/audio_effects/volume_and_dynamics/volume_keyframable.html；https://docs.kdenlive.org/en/exporting/render.html
- **上传资源**：`13590137_3840_2160_60fps.mp4` → `/home/user/Videos/`
- **评测器**：`check_kdenlive_render_effects_composite`（**新增**）
  - 验证渲染输出 + 验证项目中有灰度效果且 volume=0.3
- **result**：`vm_file` → `/home/user/Videos/output.mp4`
- **expected**：`rule` → `{"min_duration": 1.0, "expected_codec": "h264", "project_path": "/home/user/Videos/project.kdenlive", "require_grayscale": true, "expected_volume": 0.3, "volume_tolerance": 0.05}`
- **需要新评测器**：✅

---

### 任务 3-5：标题开场 + 视频 + 片尾标题并渲染

移除原因：和标题任务、转场任务、基础渲染任务组合度过高，单独保留性价比不高。

#### 任务 3-5：标题开场 + 视频 + 片尾标题并渲染

- **任务 JSON 文件 ID**：`081b45e0-3ecc-4fde-b2ca-62eed6400255.json`
- **操作说明**：请帮我在 Kdenlive 里完成这个需求：创建标题片段“Welcome to My Video”并放在 V1 开头（约 3 秒）；导入 `/home/user/Videos/6533277-hd_1920_1080_24fps.mp4` 并紧接其后；再创建标题“Thank You”并放在视频后（约 3 秒）；在标题与视频间添加 “Dissolve” 转场，保存项目到 `/home/user/Videos/project.kdenlive`，再渲染到 `/home/user/Videos/output.mp4`。
- **来源标注**：Kdenlive 官方手册（Titles + Mixes + Rendering）：https://docs.kdenlive.org/en/titles_and_graphics/titles/titles.html；https://docs.kdenlive.org/en/compositing/transitions/mixes.html；https://docs.kdenlive.org/en/exporting/render.html
- **上传资源**：`6533277-hd_1920_1080_24fps.mp4` → `/home/user/Videos/`
- **评测器**：`check_kdenlive_render_title_video_title`（**新增**）
  - 验证渲染输出（编码、时长 ≥ 5s）+ 验证项目中两条标题文字
- **result**：`vm_file` → `/home/user/Videos/output.mp4`
- **expected**：`rule` → `{"min_duration": 5.0, "expected_codec": "h264", "project_path": "/home/user/Videos/project.kdenlive", "expected_titles": ["Welcome to My Video", "Thank You"]}`
- **需要新评测器**：✅

---

### 任务 3-6：速度渐变视频并渲染

移除原因：与分割、变速等中级任务高度重叠，只是再加一层渲染收尾。

#### 任务 3-6：速度渐变视频并渲染

- **任务 JSON 文件 ID**：`abbaf9fe-861f-400e-8fd8-77a03e50a281.json`
- **操作说明**：请帮我在 Kdenlive 里完成这个需求：导入 `/home/user/Videos/14307439_1920_1080_60fps.mp4` 并放入时间线，在 3 秒处分割片段，将第二段速度改为 300%（3 倍速），保存项目到 `/home/user/Videos/project.kdenlive`，再渲染到 `/home/user/Videos/output.mp4`。
- **来源标注**：Kdenlive 官方手册（Razor + Change Speed + Rendering）：https://docs.kdenlive.org/en/cutting_and_assembling/editing.html#razor-tool；https://docs.kdenlive.org/en/cutting_and_assembling/editing.html#change-speed-of-a-clip；https://docs.kdenlive.org/en/exporting/render.html
- **上传资源**：`14307439_1920_1080_60fps.mp4` → `/home/user/Videos/`
- **评测器**：`check_kdenlive_render_speed_ramp`（**新增**）
  - 验证渲染输出 + 验证项目中有分割（≥2 段）且速度变更为 3.0x
- **result**：`vm_file` → `/home/user/Videos/output.mp4`
- **expected**：`rule` → `{"min_duration": 2.0, "expected_codec": "h264", "project_path": "/home/user/Videos/project.kdenlive", "source_file": "14307439_1920_1080_60fps.mp4", "min_segments": 2, "expected_speed": 3.0, "speed_tolerance": 0.1}`
- **需要新评测器**：✅

---

### 任务 3-7：画中画合成并渲染

移除原因：与中级 PiP 合成任务几乎是同一能力链条，只增加最终导出步骤，重复度偏高。

#### 任务 3-7：画中画合成并渲染

- **任务 JSON 文件 ID**：`a73dd78e-fb7d-4dd5-a829-f174b5603a85.json`
- **操作说明**：请帮我在 Kdenlive 里完成这个需求：导入两个视频 `/home/user/Videos/15368811_1920_1080_30fps.mp4` 和 `/home/user/Videos/6533277-hd_1920_1080_24fps.mp4`，第一个放 V1（主背景），第二个放 V2（叠加层），在 V2 应用 “Transform” 或 “Position and Zoom” 缩放到 1/4 并放到左上角，保存项目到 `/home/user/Videos/project.kdenlive`，再渲染到 `/home/user/Videos/output.mp4`。
- **来源标注**：Kdenlive 官方手册（Compositions + Transform + Rendering）：https://docs.kdenlive.org/en/compositing/compositions.html；https://docs.kdenlive.org/en/effects_and_filters/video_effects/transform_distort_perspective/transform.html；https://docs.kdenlive.org/en/exporting/render.html
- **上传资源**：`15368811_1920_1080_30fps.mp4` + `6533277-hd_1920_1080_24fps.mp4` → `/home/user/Videos/`
- **评测器**：`check_kdenlive_render_pip`（**新增**）
  - 验证渲染输出 + 验证项目中多轨合成与 transform 效果
- **result**：`vm_file` → `/home/user/Videos/output.mp4`
- **expected**：`rule` → `{"min_duration": 1.0, "expected_codec": "h264", "project_path": "/home/user/Videos/project.kdenlive", "main_file": "15368811_1920_1080_30fps.mp4", "overlay_file": "6533277-hd_1920_1080_24fps.mp4", "require_transform": true}`
- **需要新评测器**：✅

---

### 任务 3-9：调色流程并渲染

移除原因：是多效果叠加的综合任务，但和效果链、音频淡入淡出、渲染等已有能力组合重复明显。

#### 任务 3-9：调色流程并渲染

- **任务 JSON 文件 ID**：`8c708e3d-ff5e-4306-8fd3-3a4c674f30e7.json`
- **操作说明**：请帮我在 Kdenlive 里完成这个需求：导入 `/home/user/Videos/6533277-hd_1920_1080_24fps.mp4` 并放到时间线，按顺序应用：(1) Brightness 提升亮度，(2) Sepia 复古色调；再在音频开头添加 2 秒淡入、结尾添加 2 秒淡出，保存项目到 `/home/user/Videos/project.kdenlive`，再渲染到 `/home/user/Videos/output.mp4`。
- **来源标注**：Kdenlive 官方手册（Color Correction + Stylize + Fade + Rendering）：https://docs.kdenlive.org/en/effects_and_filters/video_effects/color_image_correction.html；https://docs.kdenlive.org/en/effects_and_filters/video_effects/stylize.html；https://docs.kdenlive.org/en/effects_and_filters/audio_effects/volume_and_dynamics/fade_in.html；https://docs.kdenlive.org/en/effects_and_filters/audio_effects/volume_and_dynamics/fade_out.html；https://docs.kdenlive.org/en/exporting/render.html
- **上传资源**：`6533277-hd_1920_1080_24fps.mp4` → `/home/user/Videos/`
- **评测器**：`check_kdenlive_render_color_grading`（**新增**）
  - 验证渲染输出 + 验证项目中存在 brightness、sepia、音频淡入/淡出
- **result**：`vm_file` → `/home/user/Videos/output.mp4`
- **expected**：`rule` → `{"min_duration": 1.0, "expected_codec": "h264", "project_path": "/home/user/Videos/project.kdenlive", "require_brightness": true, "require_sepia": true, "require_fade_in": true, "require_fade_out": true}`
- **需要新评测器**：✅
