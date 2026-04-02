# Kdenlive 任务设计文档（中文）

## 1. 可用资源

所有资源文件位于：`assets/kdenlive/`

### 1.1 视频文件

| 文件名 | 分辨率 | FPS | 大小 | 说明 |
|--------|--------|-----|------|------|
| `6533277-hd_1920_1080_24fps.mp4` | 1920×1080 | 24 | 4.73 MB | 标准高清横屏 |
| `13590137_3840_2160_60fps.mp4` | 3840×2160 | 60 | 32.23 MB | 4K 横屏 |
| `13739698_1080_1920_30fps.mp4` | 1080×1920 | 30 | 13.95 MB | 高清竖屏 |
| `14307439_1920_1080_60fps.mp4` | 1920×1080 | 60 | 7.40 MB | 高清横屏 60fps |
| `15363990_2160_3840_30fps.mp4` | 2160×3840 | 30 | 12.50 MB | 4K 竖屏 |
| `15368811_1920_1080_30fps.mp4` | 1920×1080 | 30 | 8.22 MB | 高清横屏 30fps |
| `15401579_2160_3650_15fps.mp4` | 2160×3650 | 15 | 13.48 MB | 非标准宽高比 |
| `15449119_2160_3840_60fps.mp4` | 2160×3840 | 60 | 21.12 MB | 4K 竖屏 60fps |

### 1.2 音频文件（MP3）

| 文件名 | 大小 |
|--------|------|
| `2de4019d3e239361315947bb82ca828c.mp3` | 1.58 MB |
| `6ec8ccb72e97ef2a98aa92d0f231b36f.mp3` | 3.17 MB |
| `77848f98a135c05bbfc8ceb62cea6fca.mp3` | 3.27 MB |
| `804c6281f9d23fa77df71776a6cca3c2.mp3` | 4.46 MB |
| `98f73cb483a429d5edf2313da9077769.mp3` | 2.59 MB |
| `f88f7fdbb6b72e3fc1e2a10078b99b18.mp3` | 2.88 MB |

### 1.3 音效文件（WAV）

| 文件名 | 大小 |
|--------|------|
| `mixkit-arcade-retro-game-over-213.wav` | 287.82 KB |
| `mixkit-classic-alarm-995.wav` | 865.83 KB |
| `mixkit-crickets-and-insects-in-the-wild-ambience-39.wav` | 4.38 MB |
| `mixkit-dog-barking-twice-1.wav` | 279.62 KB |
| `mixkit-fast-rocket-whoosh-1714.wav` | 1.20 MB |
| `mixkit-fast-small-sweep-transition-166.wav` | 135.49 KB |

---

## 2. 现有评测函数

文件：`desktop_env/evaluators/metrics/kdenlive.py`

| 函数 | 说明 | result 类型 | expected 类型 |
|------|------|-------------|---------------|
| `check_kdenlive_import_video` | 通过检查 `<producer>` 的 resource，验证视频是否导入到项目箱 | `vm_file` (.kdenlive) | `rule` → `{"expected_file": "xxx.mp4"}` |
| `check_kdenlive_add_to_timeline` | 通过检查 `<playlist>` 条目，验证片段是否放入时间线轨道 | `vm_file` (.kdenlive) | `rule` → `{"expected_file": "xxx.mp4"}` |
| `check_kdenlive_grayscale_effect` | 通过检查 `<filter>` 的 mlt_service，验证灰度效果是否应用 | `vm_file` (.kdenlive) | `rule` → `{}`（可为空） |
| `check_kdenlive_volume_adjustment` | 验证音量是否被调整到目标值 | `vm_file` (.kdenlive) | `rule` → `{"expected_volume": 0.5, "tolerance": 0.05}` |
| `check_kdenlive_render_mp4` | 使用 ffprobe 验证 MP4 渲染结果（编码、时长、文件大小） | `vm_file` (output.mp4) | `rule` → `{"min_duration": 1.0, "expected_codec": "h264"}` |

---

## 3. 任务定义

### 3.1 Level 1 — 基础操作（单步骤，可直接验证）

#### 任务 1-1：导入视频到项目箱

- **任务 JSON 文件 ID**：`a1b2c3d4-e5f6-7890-abcd-ef1234567890.json`
- **操作说明**：请帮我在 Kdenlive 里完成这个需求：将视频 `/home/user/Videos/6533277-hd_1920_1080_24fps.mp4` 导入项目箱，然后将项目保存到 `/home/user/Videos/kdenlive_project.kdenlive`。
- **来源标注**：Kdenlive 官方手册（Add Clip or Folder）：https://docs.kdenlive.org/en/project_and_asset_management/project_bin/clips.html
- **上传资源**：`6533277-hd_1920_1080_24fps.mp4` → `/home/user/Videos/`
- **评测器**：`check_kdenlive_import_video`（已有）
- **result**：`vm_file` → `/home/user/Videos/kdenlive_project.kdenlive`
- **expected**：`rule` → `{"expected_file": "6533277-hd_1920_1080_24fps.mp4"}`
- **需要新评测器**：❌

---

#### 任务 1-3：将视频片段添加到时间线

- **任务 JSON 文件 ID**：`13d8f977-ed9b-4c21-b56a-2d018dabbac2.json`
- **操作说明**：请帮我在 Kdenlive 里完成这个需求：将 `/home/user/Videos/6533277-hd_1920_1080_24fps.mp4` 导入项目箱，拖到时间线 V1 轨道，然后保存到 `/home/user/Videos/project.kdenlive`。
- **来源标注**：Kdenlive 官方手册（Timeline）：https://docs.kdenlive.org/en/user_interface/timeline.html#timeline
- **上传资源**：`6533277-hd_1920_1080_24fps.mp4` → `/home/user/Videos/`
- **评测器**：`check_kdenlive_add_to_timeline`（已有）
- **result**：`vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**：`rule` → `{"expected_file": "6533277-hd_1920_1080_24fps.mp4"}`
- **需要新评测器**：❌

---

#### 任务 1-4：设置项目分辨率

- **任务 JSON 文件 ID**：`ee6aafce-ba7c-4245-a485-99ce0355f2ef.json`
- **操作说明**：请帮我在 Kdenlive 里完成这个需求：新建分辨率为 1920×1080 的项目，然后保存到 `/home/user/Videos/project.kdenlive`。
- **来源标注**：Kdenlive 官方手册（Project Settings - General）：https://docs.kdenlive.org/en/project_and_asset_management/project_settings/general_settings.html
- **上传资源**：无
- **评测器**：`check_kdenlive_project_profile`（**新增**）
- **result**：`vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**：`rule` → `{"width": 1920, "height": 1080}`
- **需要新评测器**：✅

---

#### 任务 1-5：导入多个文件到项目箱

- **任务 JSON 文件 ID**：`a07fedf6-92ed-4094-abb0-f3f5e3cccc49.json`
- **操作说明**：请帮我在 Kdenlive 里完成这个需求：将两个视频 `/home/user/Videos/6533277-hd_1920_1080_24fps.mp4` 和 `/home/user/Videos/15368811_1920_1080_30fps.mp4` 导入项目箱，然后保存到 `/home/user/Videos/project.kdenlive`。
- **来源标注**：Kdenlive 官方手册（Add Clip or Folder）：https://docs.kdenlive.org/en/project_and_asset_management/project_bin/clips.html
- **上传资源**：`6533277-hd_1920_1080_24fps.mp4` + `15368811_1920_1080_30fps.mp4` → `/home/user/Videos/`
- **评测器**：`check_kdenlive_import_multiple_files`（**新增**）
  - 遍历所有 `<producer>` 节点，检查**全部**期望文件都存在
- **result**：`vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**：`rule` → `{"expected_files": ["6533277-hd_1920_1080_24fps.mp4", "15368811_1920_1080_30fps.mp4"]}`
- **需要新评测器**：✅

---

#### 任务 1-7：设置项目帧率

- **任务 JSON 文件 ID**：`057389f4-a55e-4544-8b21-94090c813a93.json`
- **操作说明**：请帮我在 Kdenlive 里完成这个需求：新建帧率 30fps 的项目，然后保存到 `/home/user/Videos/project.kdenlive`。
- **来源标注**：Kdenlive 官方手册（Project Settings - General）：https://docs.kdenlive.org/en/project_and_asset_management/project_settings/general_settings.html
- **上传资源**：无
- **评测器**：`check_kdenlive_project_profile`（复用：检查 `<profile>` 的 `frame_rate_num`/`frame_rate_den`）
- **result**：`vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**：`rule` → `{"frame_rate_num": 30, "frame_rate_den": 1}`
- **需要新评测器**：❌（扩展已有 `check_kdenlive_project_profile`）

---

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

#### 任务 1-9：从项目箱删除片段

- **任务 JSON 文件 ID**：`9a6d3c50-8a6e-470b-a4ba-7b89fe03889c.json`
- **操作说明**：请帮我在 Kdenlive 里完成这个需求：先导入两个视频 `/home/user/Videos/6533277-hd_1920_1080_24fps.mp4` 和 `/home/user/Videos/15368811_1920_1080_30fps.mp4` 到项目箱，再删除 `15368811_1920_1080_30fps.mp4`，然后保存到 `/home/user/Videos/project.kdenlive`。
- **来源标注**：Kdenlive 官方手册（Using the Project Bin）：https://docs.kdenlive.org/en/project_and_asset_management/project_bin/project_bin_use.html
- **上传资源**：`6533277-hd_1920_1080_24fps.mp4` + `15368811_1920_1080_30fps.mp4` → `/home/user/Videos/`
- **评测器**：`check_kdenlive_bin_content`（**新增**）
  - 验证 `expected_present` 在项目箱中存在，且 `expected_absent` 不存在
- **result**：`vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**：`rule` → `{"expected_present": ["6533277-hd_1920_1080_24fps.mp4"], "expected_absent": ["15368811_1920_1080_30fps.mp4"]}`
- **需要新评测器**：✅

---

#### 任务 1-10：重命名项目箱片段

- **任务 JSON 文件 ID**：`20b00b3b-b836-445c-9d0d-fa45d267ae3d.json`
- **操作说明**：请帮我在 Kdenlive 里完成这个需求：将 `/home/user/Videos/6533277-hd_1920_1080_24fps.mp4` 导入项目箱，在项目箱中重命名为 “Main Video”，然后保存到 `/home/user/Videos/project.kdenlive`。
- **来源标注**：Kdenlive 官方手册（Using the Project Bin）：https://docs.kdenlive.org/en/project_and_asset_management/project_bin/project_bin_use.html
- **上传资源**：`6533277-hd_1920_1080_24fps.mp4` → `/home/user/Videos/`
- **评测器**：`check_kdenlive_clip_name`（**新增**）
  - 在匹配的 `<producer>` 节点中检查 `<property name="kdenlive:clipname">`
- **result**：`vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**：`rule` → `{"source_file": "6533277-hd_1920_1080_24fps.mp4", "expected_name": "Main Video"}`
- **需要新评测器**：✅

---

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

#### 任务 1-12：新增视频轨道

- **任务 JSON 文件 ID**：`40ffa725-947f-4468-8582-7961625c67ad.json`
- **操作说明**：请帮我在 Kdenlive 里完成这个需求：在时间线添加一个新视频轨（总视频轨至少 3 条），然后保存到 `/home/user/Videos/project.kdenlive`。
- **来源标注**：Kdenlive 官方手册（Timeline - Adding Tracks）：https://docs.kdenlive.org/en/user_interface/timeline.html#adding-tracks
- **上传资源**：无
- **评测器**：`check_kdenlive_track_count`（**新增**）
  - 统计主 `<tractor>` 中对应视频轨的 `<playlist>` 或 `<track>` 元素
- **result**：`vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**：`rule` → `{"min_video_tracks": 3}`
- **需要新评测器**：✅

---

#### 任务 1-14：删除时间线轨道

- **任务 JSON 文件 ID**：`a9092adf-8064-48e2-99ea-ee6cb7dcabf8.json`
- **操作说明**：请帮我在 Kdenlive 里完成这个需求：删除 1 条视频轨，使剩余视频轨为 1 条，然后保存到 `/home/user/Videos/project.kdenlive`。
- **来源标注**：Kdenlive 官方手册（Timeline - Deleting Tracks）：https://docs.kdenlive.org/en/user_interface/timeline.html#deleting-tracks
- **上传资源**：无
- **评测器**：`check_kdenlive_track_count`（复用：验证精确数量）
- **result**：`vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**：`rule` → `{"exact_video_tracks": 1}`
- **需要新评测器**：❌（复用 `check_kdenlive_track_count`）

---

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

#### 任务 1-16：静音轨道

- **任务 JSON 文件 ID**：`7048a664-27f5-4626-8670-40999f2118e8.json`
- **操作说明**：请帮我在 Kdenlive 里完成这个需求：导入 `/home/user/Videos/6533277-hd_1920_1080_24fps.mp4` 并放到时间线，然后将视频轨 V1 静音并保存到 `/home/user/Videos/project.kdenlive`。
- **来源标注**：Kdenlive 官方手册（Timeline - Track Header）：https://docs.kdenlive.org/en/user_interface/timeline.html#track-header
- **上传资源**：`6533277-hd_1920_1080_24fps.mp4` → `/home/user/Videos/`
- **评测器**：`check_kdenlive_track_mute`（**新增**）
  - 检查 `<tractor>` 轨道属性中的 `hide` 或 `kdenlive:track_muted`
- **result**：`vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**：`rule` → `{"muted_track": "V1"}`
- **需要新评测器**：✅

---

#### 任务 1-17：锁定轨道

- **任务 JSON 文件 ID**：`18c45ea5-1cdb-4c4d-86f3-ba59a2ea1b10.json`
- **操作说明**：请帮我在 Kdenlive 里完成这个需求：在时间线锁定视频轨 V1，然后保存到 `/home/user/Videos/project.kdenlive`。
- **来源标注**：Kdenlive 官方手册（Timeline - Track Header）：https://docs.kdenlive.org/en/user_interface/timeline.html#track-header
- **上传资源**：无
- **评测器**：`check_kdenlive_track_lock`（**新增**）
  - 检查轨道 `<property name="kdenlive:locked_track">` 值
- **result**：`vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**：`rule` → `{"locked_track": "V1"}`
- **需要新评测器**：✅

---

#### 任务 1-18：撤销上一步操作

- **任务 JSON 文件 ID**：`46ef99e0-d318-41fd-9ac8-7d6f1ee3bfc9.json`
- **操作说明**：请帮我在 Kdenlive 里完成这个需求：导入 `/home/user/Videos/6533277-hd_1920_1080_24fps.mp4` 到项目箱并加到 V1，然后撤销最后一步（从时间线移除该片段），再保存到 `/home/user/Videos/project.kdenlive`。
- **来源标注**：Kdenlive 官方手册（Edit Menu）：https://docs.kdenlive.org/en/user_interface/menu/edit_menu.html
- **上传资源**：`6533277-hd_1920_1080_24fps.mp4` → `/home/user/Videos/`
- **评测器**：`check_kdenlive_timeline_empty`（**新增**）
  - 验证片段仍在项目箱中（存在 `<producer>`），但不在时间线（无 `<entry>` 引用）
- **result**：`vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**：`rule` → `{"expected_in_bin": "6533277-hd_1920_1080_24fps.mp4", "expected_not_on_timeline": true}`
- **需要新评测器**：✅

---

#### 任务 1-19：创建纯色片段

- **任务 JSON 文件 ID**：`b1814b15-e564-4e9f-b2f7-c84854a75b86.json`
- **操作说明**：请帮我在 Kdenlive 里完成这个需求：在项目箱创建一个红色（#FF0000）的纯色片段，然后保存到 `/home/user/Videos/project.kdenlive`。
- **来源标注**：Kdenlive 官方手册（Color Clip）：https://docs.kdenlive.org/en/project_and_asset_management/project_bin/color_clip.html
- **上传资源**：无
- **评测器**：`check_kdenlive_color_clip`（**新增**）
  - 搜索 `mlt_service="color"` 的 `<producer>`，检查 `resource` 颜色值
- **result**：`vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**：`rule` → `{"expected_color": "#FF0000"}`
- **需要新评测器**：✅

---

#### 任务 1-20：设置片段时长（纯色/标题）

- **任务 JSON 文件 ID**：`87e0281b-2063-4767-bf00-fb053014f47e.json`
- **操作说明**：请帮我在 Kdenlive 里完成这个需求：在项目箱创建纯色片段并将默认时长设为 10 秒，然后保存到 `/home/user/Videos/project.kdenlive`。
- **来源标注**：Kdenlive 官方手册（Color Clip / Title Clip）：https://docs.kdenlive.org/en/project_and_asset_management/project_bin/color_clip.html；https://docs.kdenlive.org/en/project_and_asset_management/project_bin/title_clip.html
- **上传资源**：无
- **评测器**：`check_kdenlive_clip_duration`（**新增**）
  - 检查纯色 producer 的 `length` 或 `out`，把帧数换算为秒
- **result**：`vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**：`rule` → `{"min_duration_seconds": 9.5, "max_duration_seconds": 10.5}`
- **需要新评测器**：✅

---

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

#### 任务 1-22：启用/禁用代理片段

- **任务 JSON 文件 ID**：`6b00667c-32a2-4bb6-8c90-4ca32db252b1.json`
- **操作说明**：请帮我在 Kdenlive 里完成这个需求：进入项目设置并为当前项目启用代理片段，然后保存到 `/home/user/Videos/project.kdenlive`。
- **来源标注**：Kdenlive 官方手册（Project Settings - Proxy）：https://docs.kdenlive.org/en/project_and_asset_management/project_settings/proxy_settings.html
- **上传资源**：无
- **评测器**：`check_kdenlive_proxy_setting`（**新增**）
  - 检查 `<property name="kdenlive:docproperties.enableproxy">` 是否为 "1"
- **result**：`vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**：`rule` → `{"proxy_enabled": true}`
- **需要新评测器**：✅

---

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

#### 任务 1-24：移动时间线片段位置

- **任务 JSON 文件 ID**：`3b531757-692d-4de3-9f49-5d8c3a1558a3.json`
- **操作说明**：请帮我在 Kdenlive 里完成这个需求：导入 `/home/user/Videos/6533277-hd_1920_1080_24fps.mp4`，将其放到 V1 并从 00:00:05:00（5 秒）开始，然后保存到 `/home/user/Videos/project.kdenlive`。
- **来源标注**：Kdenlive 官方手册（Editing）：https://docs.kdenlive.org/en/cutting_and_assembling/editing.html
- **上传资源**：`6533277-hd_1920_1080_24fps.mp4` → `/home/user/Videos/`
- **评测器**：`check_kdenlive_clip_position`（**新增**）
  - 检查轨道 playlist 中 `<entry>`/`<blank>`，验证片段起始帧对应 5 秒
- **result**：`vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**：`rule` → `{"source_file": "6533277-hd_1920_1080_24fps.mp4", "start_time": 5.0, "tolerance": 0.5}`
- **需要新评测器**：✅

---

### 3.2 Level 2 — 中级操作（多步骤，效果/属性修改）

#### 任务 2-1：对视频应用灰度效果

- **任务 JSON 文件 ID**：`07186918-9646-45af-805b-2a13c02ac63f.json（最接近任务，当前目录无仅灰度的独立 JSON）`
- **操作说明**：请帮我在 Kdenlive 里完成这个需求：导入 `/home/user/Videos/6533277-hd_1920_1080_24fps.mp4`，添加到时间线，对片段应用 Grayscale 效果，然后保存到 `/home/user/Videos/project.kdenlive`。
- **来源标注**：Kdenlive 官方手册（Video Effects - Stylize）：https://docs.kdenlive.org/en/effects_and_filters/video_effects/stylize.html
- **上传资源**：`6533277-hd_1920_1080_24fps.mp4` → `/home/user/Videos/`
- **评测器**：`check_kdenlive_grayscale_effect`（已有）
- **result**：`vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**：`rule` → `{}`
- **需要新评测器**：❌

---

#### 任务 2-2：调整音量

- **任务 JSON 文件 ID**：`07186918-9646-45af-805b-2a13c02ac63f.json（最接近任务，当前目录无仅音量 50% 的独立 JSON）`
- **操作说明**：请帮我在 Kdenlive 里完成这个需求：导入 `/home/user/Music/98f73cb483a429d5edf2313da9077769.mp3`，放到 A1，设置音量为 50%，然后保存到 `/home/user/Videos/project.kdenlive`。
- **来源标注**：Kdenlive 官方手册（Volume (keyframable)）：https://docs.kdenlive.org/en/effects_and_filters/audio_effects/volume_and_dynamics/volume_keyframable.html
- **上传资源**：`98f73cb483a429d5edf2313da9077769.mp3` → `/home/user/Music/`
- **评测器**：`check_kdenlive_volume_adjustment`（已有）
- **result**：`vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**：`rule` → `{"expected_volume": 0.5, "tolerance": 0.05}`
- **需要新评测器**：❌

---

#### 任务 2-3：修剪视频片段（设置入点/出点）

- **任务 JSON 文件 ID**：`8b5c202b-81ac-46b0-9f11-1af977f9656f.json（最接近任务，当前目录无 In/Out 修剪的独立 JSON）`
- **操作说明**：请帮我在 Kdenlive 里完成这个需求：导入 `/home/user/Videos/14307439_1920_1080_60fps.mp4`，加到时间线，修剪为 2 秒开始、8 秒结束，然后保存到 `/home/user/Videos/project.kdenlive`。
- **来源标注**：Kdenlive 官方手册（Editing / Trim）：https://docs.kdenlive.org/en/cutting_and_assembling/editing.html
- **上传资源**：`14307439_1920_1080_60fps.mp4` → `/home/user/Videos/`
- **评测器**：`check_kdenlive_clip_trim`（**新增**）
- **result**：`vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**：`rule` → `{"in_time": 2.0, "out_time": 8.0, "tolerance": 0.5, "source_file": "14307439_1920_1080_60fps.mp4"}`
- **需要新评测器**：✅

---

#### 任务 2-4：在两个片段之间添加转场

- **任务 JSON 文件 ID**：`bb095bd9-5919-4a02-86da-2a9bb6380ff1.json（最接近任务，含 Dissolve 但附带渲染）`
- **操作说明**：请帮我在 Kdenlive 里完成这个需求：导入两个视频 `/home/user/Videos/6533277-hd_1920_1080_24fps.mp4` 和 `/home/user/Videos/15368811_1920_1080_30fps.mp4`，依次放到时间线，并在两者间添加 “Dissolve” 转场，然后保存到 `/home/user/Videos/project.kdenlive`。
- **来源标注**：Kdenlive 官方手册（Mixes / Same-track Transitions）：https://docs.kdenlive.org/en/compositing/transitions/mixes.html
- **上传资源**：`6533277-hd_1920_1080_24fps.mp4` + `15368811_1920_1080_30fps.mp4` → `/home/user/Videos/`
- **评测器**：`check_kdenlive_transition`（**新增**）
- **result**：`vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**：`rule` → `{"transition_type": "luma"}`
- **需要新评测器**：✅

---

#### 任务 2-5：添加标题文本

- **任务 JSON 文件 ID**：`081b45e0-3ecc-4fde-b2ca-62eed6400255.json（最接近任务，标题内容不同且附带渲染）`
- **操作说明**：请帮我在 Kdenlive 里完成这个需求：新建项目，在时间线添加内容为 “Hello World” 的标题片段，然后保存到 `/home/user/Videos/project.kdenlive`。
- **来源标注**：Kdenlive 官方手册（Titles）：https://docs.kdenlive.org/en/titles_and_graphics/titles/titles.html
- **上传资源**：无
- **评测器**：`check_kdenlive_title_text`（**新增**）
- **result**：`vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**：`rule` → `{"expected_text": "Hello World"}`
- **需要新评测器**：✅

---

#### 任务 2-6：修改片段播放速度

- **任务 JSON 文件 ID**：`abbaf9fe-861f-400e-8fd8-77a03e50a281.json（最接近任务，速度为 300% 且附带渲染）`
- **操作说明**：请帮我在 Kdenlive 里完成这个需求：导入 `/home/user/Videos/6533277-hd_1920_1080_24fps.mp4`，放到时间线，将速度改为 200%（2 倍速），然后保存到 `/home/user/Videos/project.kdenlive`。
- **来源标注**：Kdenlive 官方手册（Change Speed of a Clip）：https://docs.kdenlive.org/en/cutting_and_assembling/editing.html#change-speed-of-a-clip
- **上传资源**：`6533277-hd_1920_1080_24fps.mp4` → `/home/user/Videos/`
- **评测器**：`check_kdenlive_clip_speed`（**新增**）
- **result**：`vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**：`rule` → `{"expected_speed": 2.0, "tolerance": 0.1, "source_file": "6533277-hd_1920_1080_24fps.mp4"}`
- **需要新评测器**：✅

---

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

#### 任务 2-12：添加音频淡入和淡出

- **任务 JSON 文件 ID**：`c8b836c8-45ff-471a-a2b4-4ae6b7f0c0e6.json`
- **操作说明**：请帮我在 Kdenlive 里完成这个需求：导入 `/home/user/Music/f88f7fdbb6b72e3fc1e2a10078b99b18.mp3`，放到 A1，在开头添加 2 秒淡入，结尾添加 2 秒淡出，然后保存到 `/home/user/Videos/project.kdenlive`。
- **来源标注**：Kdenlive 官方手册（Fade In / Fade Out）：https://docs.kdenlive.org/en/effects_and_filters/audio_effects/volume_and_dynamics/fade_in.html；https://docs.kdenlive.org/en/effects_and_filters/audio_effects/volume_and_dynamics/fade_out.html
- **上传资源**：`f88f7fdbb6b72e3fc1e2a10078b99b18.mp3` → `/home/user/Music/`
- **评测器**：`check_kdenlive_audio_fade`（**新增**）
  - 检查音频片段上的 `volume` / `fade_from` / `fade_to` 与关键帧数据
- **result**：`vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**：`rule` → `{"fade_in": true, "fade_out": true, "source_file": "f88f7fdbb6b72e3fc1e2a10078b99b18.mp3"}`
- **需要新评测器**：✅

---

#### 任务 2-13：在时间线分割/切割片段

- **任务 JSON 文件 ID**：`8b5c202b-81ac-46b0-9f11-1af977f9656f.json`
- **操作说明**：请帮我在 Kdenlive 里完成这个需求：导入 `/home/user/Videos/14307439_1920_1080_60fps.mp4`，放到 V1，用 Razor 工具在 5 秒处分割成两个片段，然后保存到 `/home/user/Videos/project.kdenlive`。
- **来源标注**：Kdenlive 官方手册（Razor Tool）：https://docs.kdenlive.org/en/cutting_and_assembling/editing.html#razor-tool
- **上传资源**：`14307439_1920_1080_60fps.mp4` → `/home/user/Videos/`
- **评测器**：`check_kdenlive_clip_split`（**新增**）
  - 统计引用同一 producer 的 `<entry>` 数量，分割后应 ≥ 2
- **result**：`vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**：`rule` → `{"source_file": "14307439_1920_1080_60fps.mp4", "min_segments": 2}`
- **需要新评测器**：✅

---

#### 任务 2-14：创建画中画（PiP）合成

- **任务 JSON 文件 ID**：`5bd77807-0a8d-46cf-847d-c86b2c1b6447.json`
- **操作说明**：请帮我在 Kdenlive 里完成这个需求：导入两个视频 `/home/user/Videos/6533277-hd_1920_1080_24fps.mp4` 与 `/home/user/Videos/15368811_1920_1080_30fps.mp4`，第一个放 V1（主画面），第二个放 V2（叠加层），对 V2 应用 “Transform” 或 “Position and Zoom” 缩放到屏幕 1/4 并放在右下角，然后保存到 `/home/user/Videos/project.kdenlive`。
- **来源标注**：Kdenlive 官方手册（Compositions + Transform）：https://docs.kdenlive.org/en/compositing/compositions.html；https://docs.kdenlive.org/en/effects_and_filters/video_effects/transform_distort_perspective/transform.html
- **上传资源**：`6533277-hd_1920_1080_24fps.mp4` + `15368811_1920_1080_30fps.mp4` → `/home/user/Videos/`
- **评测器**：`check_kdenlive_multi_track_composition`（**新增**）
  - 验证两个片段在不同轨道，且叠加轨应用 transform/affine 效果
- **result**：`vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**：`rule` → `{"main_file": "6533277-hd_1920_1080_24fps.mp4", "overlay_file": "15368811_1920_1080_30fps.mp4", "require_transform": true}`
- **需要新评测器**：✅

---

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

### 3.3 Level 3 — 高级操作（多步骤合成，包含渲染）

#### 任务 3-1：将项目渲染为 MP4

- **任务 JSON 文件 ID**：`fd3ae9f3-841f-4b11-b72d-e090eea0e706.json`
- **操作说明**：请帮我在 Kdenlive 里完成这个需求：导入 `/home/user/Videos/6533277-hd_1920_1080_24fps.mp4` 并放到时间线，渲染为 MP4（H.264）到 `/home/user/Videos/output.mp4`，并等待渲染完成。
- **来源标注**：Kdenlive 官方手册（Rendering）：https://docs.kdenlive.org/en/exporting/render.html
- **上传资源**：`6533277-hd_1920_1080_24fps.mp4` → `/home/user/Videos/`
- **评测器**：`check_kdenlive_render_mp4`（已有）
- **result**：`vm_file` → `/home/user/Videos/output.mp4`
- **expected**：`rule` → `{"min_duration": 1.0, "expected_codec": "h264"}`
- **需要新评测器**：❌

---

#### 任务 3-2：添加背景音乐并渲染

- **任务 JSON 文件 ID**：`4be9b350-d9ad-4bd9-82b3-788bb214bb7d.json`
- **操作说明**：请帮我在 Kdenlive 里完成这个需求：导入视频 `/home/user/Videos/15368811_1920_1080_30fps.mp4` 和音频 `/home/user/Music/804c6281f9d23fa77df71776a6cca3c2.mp3`，视频放 V1、音频放 A1，渲染到 `/home/user/Videos/output.mp4`。
- **来源标注**：Kdenlive 官方手册（Volume + Rendering）：https://docs.kdenlive.org/en/effects_and_filters/audio_effects/volume_and_dynamics/volume_keyframable.html；https://docs.kdenlive.org/en/exporting/render.html
- **上传资源**：`15368811_1920_1080_30fps.mp4` → `/home/user/Videos/` + `804c6281f9d23fa77df71776a6cca3c2.mp3` → `/home/user/Music/`
- **评测器**：`check_kdenlive_render_with_audio`（**新增**）
- **result**：`vm_file` → `/home/user/Videos/output.mp4`
- **expected**：`rule` → `{"min_duration": 1.0, "require_audio": true}`
- **需要新评测器**：✅

---

#### 任务 3-3：多片段拼接 + 转场 + 渲染

- **任务 JSON 文件 ID**：`bb095bd9-5919-4a02-86da-2a9bb6380ff1.json`
- **操作说明**：请帮我在 Kdenlive 里完成这个需求：导入三个视频 `/home/user/Videos/6533277-hd_1920_1080_24fps.mp4`、`/home/user/Videos/14307439_1920_1080_60fps.mp4`、`/home/user/Videos/15368811_1920_1080_30fps.mp4`，按顺序放入时间线并在相邻片段间添加 “Dissolve” 转场，先保存项目到 `/home/user/Videos/project.kdenlive`，再渲染到 `/home/user/Videos/output.mp4`。
- **来源标注**：Kdenlive 官方手册（Mixes + Rendering）：https://docs.kdenlive.org/en/compositing/transitions/mixes.html；https://docs.kdenlive.org/en/exporting/render.html
- **上传资源**：`6533277-hd_1920_1080_24fps.mp4` + `14307439_1920_1080_60fps.mp4` + `15368811_1920_1080_30fps.mp4` → `/home/user/Videos/`
- **评测器**：`check_kdenlive_render_multi_clip_transition`（**新增**）
  - 验证渲染输出（编码、时长）+ 验证项目文件含 3 个片段及 dissolve 转场
- **result**：`vm_file` → `/home/user/Videos/output.mp4`
- **expected**：`rule` → `{"min_duration": 5.0, "expected_codec": "h264", "project_path": "/home/user/Videos/project.kdenlive", "expected_files": ["6533277-hd_1920_1080_24fps.mp4", "14307439_1920_1080_60fps.mp4", "15368811_1920_1080_30fps.mp4"], "transition_type": "luma"}`
- **需要新评测器**：✅

---

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

#### 任务 3-8：多音轨混音并渲染

- **任务 JSON 文件 ID**：`d3a66c10-476d-4f83-9155-5e3526d6cf31.json`
- **操作说明**：请帮我在 Kdenlive 里完成这个需求：导入视频 `/home/user/Videos/15368811_1920_1080_30fps.mp4`，再导入两条音频 `/home/user/Music/98f73cb483a429d5edf2313da9077769.mp3`（背景音乐）和 `/home/user/Music/mixkit-fast-rocket-whoosh-1714.wav`（音效）；视频放 V1，背景音乐放 A1 并设音量 40%，音效放 A2 且起始于 2 秒处，保存项目到 `/home/user/Videos/project.kdenlive`，再渲染到 `/home/user/Videos/output.mp4`。
- **来源标注**：Kdenlive 官方手册（Timeline + Volume + Rendering）：https://docs.kdenlive.org/en/user_interface/timeline.html#tracks；https://docs.kdenlive.org/en/effects_and_filters/audio_effects/volume_and_dynamics/volume_keyframable.html；https://docs.kdenlive.org/en/exporting/render.html
- **上传资源**：`15368811_1920_1080_30fps.mp4` → `/home/user/Videos/` + `98f73cb483a429d5edf2313da9077769.mp3` + `mixkit-fast-rocket-whoosh-1714.wav` → `/home/user/Music/`
- **评测器**：`check_kdenlive_render_audio_mix`（**新增**）
  - 验证渲染输出（编码、时长、有音频流）+ 验证项目中 BGM 音量=0.4 且音效文件存在
- **result**：`vm_file` → `/home/user/Videos/output.mp4`
- **expected**：`rule` → `{"min_duration": 1.0, "expected_codec": "h264", "project_path": "/home/user/Videos/project.kdenlive", "require_audio": true, "expected_volume": 0.4, "volume_tolerance": 0.05, "expected_audio_files": ["98f73cb483a429d5edf2313da9077769.mp3", "mixkit-fast-rocket-whoosh-1714.wav"]}`
- **需要新评测器**：✅

---

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

---

#### 任务 3-10：以自定义分辨率渲染 MP4

- **任务 JSON 文件 ID**：`49c6d9d4-a682-46fa-a8ef-907eb976d042.json`
- **操作说明**：请帮我在 Kdenlive 里完成这个需求：导入 `/home/user/Videos/13590137_3840_2160_60fps.mp4` 并加到时间线，将项目分辨率改为 1280×720，然后以 MP4（H.264）格式渲染到 `/home/user/Videos/output.mp4`（1280×720）。
- **来源标注**：Kdenlive 官方手册（Project Settings + Rendering）：https://docs.kdenlive.org/en/project_and_asset_management/project_settings/general_settings.html；https://docs.kdenlive.org/en/exporting/render.html
- **上传资源**：`13590137_3840_2160_60fps.mp4` → `/home/user/Videos/`
- **评测器**：`check_kdenlive_render_custom_resolution`（**新增**）
  - 使用 ffprobe 验证输出视频的分辨率、编码和时长
- **result**：`vm_file` → `/home/user/Videos/output.mp4`
- **expected**：`rule` → `{"min_duration": 1.0, "expected_codec": "h264", "expected_width": 1280, "expected_height": 720}`
- **需要新评测器**：✅

---

### 3.4 Interactive 任务（Kdenlive，多轮）—— 5 个（设计草案）

> 说明：以下为 interactive 任务构建设计，后续可落地为 `evaluation_examples/examples/interactive/interactive_kdenlive_*.json`。
> 触发方式覆盖：`step_count`（2 个）+ `ask(agent_asks)`（1 个）+ `agent_done`（5 个任务收尾，且 4 个任务含多轮 `agent_done`）。

#### IK-01：横版剪辑中途改竖版交付（step_count）

- **建议 Task ID**：`interactive_kdenlive_requirement_change_001`
- **场景类型**：`requirement_change`
- **素材**：`/home/user/Videos/15368811_1920_1080_30fps.mp4`
- **核心目标**：Agent 已开始做横版首稿时，用户中途改成竖版社媒交付。
- **现实工作场景**：短视频运营同学在午间审稿会上临时通知“同一素材要改投竖屏信息流广告”，编辑需在原横版时间线基础上快速改版并当日交付。
- **Phase 设计**：
  - **Phase 1**：`先把这个视频做一个横版预告片，标题写“新品预告”，准备导出。`
    - `trigger`: `{"type": "step_count", "value": 3}`
  - **Phase 2**：`我改主意了，改成竖版 1080x1920，标题先不要，导出到 /home/user/Videos/teaser_vertical.mp4，并保存工程 /home/user/Videos/teaser_vertical.kdenlive。`
    - `trigger`: `{"type": "agent_done"}`
- **建议评测器组合**：`check_kdenlive_render_custom_resolution` + `check_kdenlive_file_exists`
- **预期考点**：执行中需求切换、项目分辨率调整、最终导出与工程保存一致性。

#### IK-02：分阶段交付剪辑工作流（agent_done）

- **建议 Task ID**：`interactive_kdenlive_workflow_001`
- **场景类型**：`multi_step_workflow`
- **素材**：`/home/user/Videos/6533277-hd_1920_1080_24fps.mp4`、`/home/user/Videos/14307439_1920_1080_60fps.mp4`、`/home/user/Music/98f73cb483a429d5edf2313da9077769.mp3`
- **核心目标**：先交粗剪，再补音乐并做最终交付。
- **现实工作场景**：品牌内容团队常见“两段式交付”流程：上午先给市场经理看粗剪节奏，确认后下午补 BGM 和响度并输出正式版给媒介投放。
- **Phase 设计**：
  - **Phase 1**：`把两个视频按顺序放时间线，每段保留前 5 秒，中间加 Dissolve，先保存预览工程 /home/user/Videos/workflow_preview.kdenlive。`
    - `trigger`: `{"type": "agent_done"}`
  - **Phase 2**：`可以，继续把背景音乐放到 A1，音量调到大约 35%。`
    - `trigger`: `{"type": "agent_done"}`
  - **Phase 3**：`现在渲染最终成片到 /home/user/Videos/workflow_final.mp4。`
    - `trigger`: `{"type": "agent_done"}`
- **建议评测器组合**：`check_kdenlive_transition` + `check_kdenlive_render_with_audio`
- **预期考点**：阶段状态记忆、跨阶段连续编辑、最终音视频联合导出。

#### IK-03：模糊开场需求需先澄清（ask / agent_asks）

- **建议 Task ID**：`interactive_kdenlive_ambiguous_001`
- **场景类型**：`ambiguous_instruction`
- **素材**：`/home/user/Videos/6533277-hd_1920_1080_24fps.mp4`
- **核心目标**：第一轮需求刻意模糊，要求 Agent 先提问澄清，再执行。
- **现实工作场景**：业务负责人只给出“做得更专业一点”这类口头需求，剪辑师需先追问标题文案、时长与转场偏好，再落地为可执行编辑参数。
- **Phase 设计**：
  - **Phase 1**：`帮我做一个看起来更专业的开场视频，明天汇报要用。`
    - `trigger`: `{"type": "agent_asks"}`
  - **Phase 2**：`具体要求是：先做 3 秒标题“Q2 产品回顾”，再接这个视频，标题和视频之间加 Dissolve。`
    - `trigger`: `{"type": "agent_done"}`
  - **Phase 3**：`导出到 /home/user/Videos/q2_intro.mp4，并把工程保存成 /home/user/Videos/q2_intro.kdenlive。`
    - `trigger`: `{"type": "agent_done"}`
- **建议评测器组合**：`check_kdenlive_title_text` + `check_kdenlive_transition` + `check_kdenlive_render_mp4`
- **预期考点**：澄清能力（`CALL_USER`）、澄清后参数化执行、双产物交付。

#### IK-04：画中画编辑中断追加规格（step_count）

- **建议 Task ID**：`interactive_kdenlive_interruption_001`
- **场景类型**：`interruption`
- **素材**：`/home/user/Videos/15368811_1920_1080_30fps.mp4`、`/home/user/Videos/6533277-hd_1920_1080_24fps.mp4`
- **核心目标**：Agent 正在搭建 PiP 时，用户临时插入分辨率与构图改动。
- **现实工作场景**：直播回放二创常出现“主讲+产品演示”双画面需求，运营在制作中途会追加平台分辨率和版位规范，要求编辑即时调整后重导出。
- **Phase 设计**：
  - **Phase 1**：`先做画中画：15368811 做主画面放 V1，6533277 放 V2 缩小到右下角。`
    - `trigger`: `{"type": "step_count", "value": 2}`
  - **Phase 2**：`补充新要求：副画面改到左上角，最终按 1280x720 渲染到 /home/user/Videos/pip_720.mp4，并保存工程 /home/user/Videos/pip_720.kdenlive。`
    - `trigger`: `{"type": "agent_done"}`
- **建议评测器组合**：`check_kdenlive_render_pip` + `check_kdenlive_render_custom_resolution`
- **预期考点**：中断后重规划能力、合成参数修改、导出规格变更。

#### IK-05：先交初版再渐进细化（agent_done）

- **建议 Task ID**：`interactive_kdenlive_progressive_001`
- **场景类型**：`progressive_refinement`
- **素材**：`/home/user/Videos/6533277-hd_1920_1080_24fps.mp4`
- **核心目标**：先给可用初稿，再按反馈逐轮增加调色和音频收尾。
- **现实工作场景**：客户评审通常先看结构版（v1），再提出“画面更暖、收尾更柔和”等二轮反馈，最终形成带调色与淡入淡出的定稿输出。
- **Phase 设计**：
  - **Phase 1**：`先把视频前 12 秒做成初稿，保存工程 /home/user/Videos/color_v1.kdenlive。`
    - `trigger`: `{"type": "agent_done"}`
  - **Phase 2**：`继续优化：给画面加 Brightness 和 Sepia 两个效果。`
    - `trigger`: `{"type": "agent_done"}`
  - **Phase 3**：`最后给音频加 2 秒淡入和 2 秒淡出，渲染到 /home/user/Videos/color_final.mp4。`
    - `trigger`: `{"type": "agent_done"}`
- **建议评测器组合**：`check_kdenlive_render_color_grading`
- **预期考点**：迭代式返工、效果链追加、最终渲染稳定性。

#### Interactive 触发分布汇总（本批 5 个）

| 任务ID | trigger 覆盖 |
|---|---|
| IK-01 | `step_count` + `agent_done` |
| IK-02 | `agent_done` |
| IK-03 | `agent_asks`（ask） + `agent_done` |
| IK-04 | `step_count` + `agent_done` |
| IK-05 | `agent_done` |

#### Interactive 任务来源映射（本批 5 个）

> 目标：为每个 Kdenlive interactive 任务补齐“现实来源证据链”，使任务呈现为来自真实剪辑协作需求的结构化采样。

| 任务ID | 场景类型 | 现实工作来源（Primary Source） | 证据包（最小） | Task JSON `source` 建议写法 |
|---|---|---|---|---|
| IK-01 | `requirement_change` | 社媒投放临时改版：横版预告改竖版信息流 | ① 原始横版需求摘录 ② 中途改版指令截图 ③ 竖版导出验收记录 | `kdenlive_interactive;source_type=marketing_change_request;source_ref=<id_or_url>;evidence=aspect_ratio_pivot` |
| IK-02 | `multi_step_workflow` | 内容团队分阶段交付：粗剪确认后补配乐定稿 | ① 粗剪确认记录 ② 音乐与音量规范 ③ 正式版导出路径 | `kdenlive_interactive;source_type=internal_workflow;source_ref=<id_or_url>;evidence=staged_delivery` |
| IK-03 | `ambiguous_instruction` | 业务口头模糊需求需澄清后执行 | ① 模糊原始需求 ② 澄清问答记录 ③ 明确化参数清单 | `kdenlive_interactive;source_type=stakeholder_brief;source_ref=<id_or_url>;evidence=clarification_required` |
| IK-04 | `interruption` | 直播回放二创中途追加平台规格与构图要求 | ① 初始 PiP 需求 ② 中断时新增规格 ③ 改版前后导出对照 | `kdenlive_interactive;source_type=platform_change_request;source_ref=<id_or_url>;evidence=mid_process_interruption` |
| IK-05 | `progressive_refinement` | 客户多轮评审返工：结构版→调色→音频收尾 | ① v1 评审意见 ② 二轮返工要求 ③ 最终版验收记录 | `kdenlive_interactive;source_type=iterative_delivery;source_ref=<id_or_url>;evidence=rework_loop` |

#### 来源字段落地建议（统一）

- **source_type**：`marketing_change_request` / `internal_workflow` / `stakeholder_brief` / `platform_change_request` / `iterative_delivery`
- **source_ref**：来源标识（匿名化 URL、工单号、采访记录编号）
- **captured_at**：取证日期（`YYYY-MM-DD`）
- **anonymized_excerpt**：匿名化原始需求摘录（1~3 句）
- **mapping_note**：原始需求如何映射到 `phases` 与 `trigger`
- **reviewers**：双人审核与仲裁记录（`reviewer_a/reviewer_b/adjudicator`）

---

## 4. 新增评测器函数规范

> **说明**：4.1–4.6 来自原始设计。4.7–4.21 为扩展后的 Level 1 新增内容。4.22–4.28 为扩展后的 Level 2 新增内容。4.29–4.36 为 Level 3 渲染与组合评测器。

### 4.1 `check_kdenlive_project_profile`

**用途**：验证项目分辨率/帧率设置。

**校验逻辑**：
- 解析 `.kdenlive` 文件（MLT XML 格式）
- 查找 `<profile>` 元素并检查 `width`、`height` 等属性
- 与期望值比较

```python
def check_kdenlive_project_profile(project_file_path, rule):
    """
    Args:
        project_file_path: .kdenlive 项目文件路径
        rule: {"width": 1920, "height": 1080}
    Returns:
        float: 分辨率匹配返回 1.0，否则返回 0.0
    """
    # 解析 <profile width="..." height="..."> 节点
    # 校验 width/height 是否与期望一致
```

---

### 4.2 `check_kdenlive_clip_trim`

**用途**：验证片段入点/出点修剪结果。

**校验逻辑**：
- 找到匹配 `source_file` 的 producer，获取帧率
- 找到引用该 producer 的时间线 `<entry>`
- 读取 `in`、`out`（帧号）
- 按帧率换算为秒
- 与 `in_time`/`out_time` 在 `tolerance` 范围内比较

```python
def check_kdenlive_clip_trim(project_file_path, rule):
    """
    Args:
        project_file_path: .kdenlive 项目文件路径
        rule: {"in_time": 2.0, "out_time": 8.0, "tolerance": 0.5, "source_file": "xxx.mp4"}
    Returns:
        float: 修剪点匹配返回 1.0，否则返回 0.0
    """
    # 找到 source_file 对应 producer，获取 frame_rate_num/frame_rate_den
    # 找时间线 entry，读取 in/out 帧数
    # 帧转秒：time = frame / fps
    # 与期望 in_time/out_time ± tolerance 比较
```

---

### 4.3 `check_kdenlive_transition`

**用途**：验证片段间存在转场效果。

**校验逻辑**：
- 搜索项目 XML 中的 `<transition>` 或 `<link>`
- 检查 `mlt_service` 是否匹配期望 `transition_type`
- 例如 Dissolve 常对应 `luma`

```python
def check_kdenlive_transition(project_file_path, rule):
    """
    Args:
        project_file_path: .kdenlive 项目文件路径
        rule: {"transition_type": "luma"}
    Returns:
        float: 找到匹配转场返回 1.0，否则返回 0.0
    """
    # 遍历 <transition> / <link> 节点
    # 检查 mlt_service 是否匹配 transition_type
```

---

### 4.4 `check_kdenlive_title_text`

**用途**：验证标题片段包含期望文本。

**校验逻辑**：
- 查找 `mlt_service="kdenlivetitle"` 的 `<producer>`
- 提取 `xmldata` 属性（内部为 SVG/XML 标题定义）
- 解析 SVG XML 文本内容
- 检查是否包含期望文本

```python
def check_kdenlive_title_text(project_file_path, rule):
    """
    Args:
        project_file_path: .kdenlive 项目文件路径
        rule: {"expected_text": "Hello World"}
    Returns:
        float: 文本匹配返回 1.0，否则返回 0.0
    """
    # 查找 mlt_service="kdenlivetitle" 的 producer
    # 解析 xmldata（SVG XML）
    # 判断文本内容是否包含 expected_text
```

---

### 4.5 `check_kdenlive_clip_speed`

**用途**：验证片段播放速度修改。

**校验逻辑**：
- 查找匹配 `source_file` 的 producer/chain
- 检查 `warp_speed` 或 timewarp 相关 service
- 在容差范围内比较速度值

```python
def check_kdenlive_clip_speed(project_file_path, rule):
    """
    Args:
        project_file_path: .kdenlive 项目文件路径
        rule: {"expected_speed": 2.0, "tolerance": 0.1, "source_file": "xxx.mp4"}
    Returns:
        float: 速度匹配返回 1.0，否则返回 0.0
    """
    # 查找 source_file 对应 chain/producer
    # 读取 warp_speed 或 timewarp 链接中的速度参数
    # 与 expected_speed ± tolerance 比较
```

---

### 4.6 `check_kdenlive_render_with_audio`

**用途**：验证渲染输出同时包含视频流和音频流。

**校验逻辑**：
- 使用 ffprobe 检查输出文件
- 验证存在视频流
- 若 `require_audio=true`，验证存在音频流
- 检查时长不低于下限

```python
def check_kdenlive_render_with_audio(result_file_path, rule):
    """
    Args:
        result_file_path: 渲染输出 MP4 路径
        rule: {"min_duration": 1.0, "require_audio": true}
    Returns:
        float: 满足要求返回 1.0，否则返回 0.0
    """
    # 使用 ffprobe 检查输出
    # 验证视频流存在
    # 若 require_audio 为 true，验证音频流存在
    # 验证 duration >= min_duration
```

---

### 4.7 `check_kdenlive_import_multiple_files`

**用途**：验证所有期望文件都已导入项目箱。

```python
def check_kdenlive_import_multiple_files(project_file_path, rule):
    """
    Args:
        project_file_path: .kdenlive 项目文件路径
        rule: {"expected_files": ["file1.mp4", "file2.mp4"]}
    Returns:
        float: 所有文件都存在于 producers 中返回 1.0，否则 0.0
    """
    # 收集全部 <producer> 的 resource
    # 检查每个 expected_file 是否至少命中一条 resource
    # 仅当全部命中时返回 1.0
```

---

### 4.8 `check_kdenlive_file_exists`

**用途**：验证项目文件存在且为有效 MLT XML。

```python
def check_kdenlive_file_exists(project_file_path, rule):
    """
    Args:
        project_file_path: .kdenlive 项目文件路径
        rule: {"valid_xml": true}
    Returns:
        float: 文件存在且可解析为 <mlt> 根节点时返回 1.0，否则 0.0
    """
    # 检查文件存在且大小 > 0
    # 解析 XML，确认根标签为 <mlt>
```

---

### 4.9 `check_kdenlive_bin_content`

**用途**：验证项目箱包含应保留文件，且不包含被删除文件。

```python
def check_kdenlive_bin_content(project_file_path, rule):
    """
    Args:
        project_file_path: .kdenlive 项目文件路径
        rule: {
            "expected_present": ["file1.mp4"],  # 必须存在
            "expected_absent": ["file2.mp4"]    # 必须不存在
        }
    Returns:
        float: 条件都满足返回 1.0，否则 0.0
    """
    # 收集全部 producer resource
    # expected_present 必须全部命中
    # expected_absent 必须全部不命中
```

---

### 4.10 `check_kdenlive_clip_name`

**用途**：验证项目箱内片段重命名结果。

```python
def check_kdenlive_clip_name(project_file_path, rule):
    """
    Args:
        project_file_path: .kdenlive 项目文件路径
        rule: {"source_file": "xxx.mp4", "expected_name": "Main Video"}
    Returns:
        float: 名称匹配返回 1.0，否则 0.0
    """
    # 找到 resource 包含 source_file 的 <producer>
    # 检查 <property name="kdenlive:clipname"> 是否为 expected_name
```

---

### 4.11 `check_kdenlive_bin_folder`

**用途**：验证项目箱文件夹是否存在。

```python
def check_kdenlive_bin_folder(project_file_path, rule):
    """
    Args:
        project_file_path: .kdenlive 项目文件路径
        rule: {"expected_folder": "Footage"}
    Returns:
        float: 找到文件夹返回 1.0，否则 0.0
    """
    # 解析 kdenlive:docproperties.kdenlive:folders 或 <folder> 元素
    # 检查文件夹名称是否匹配 expected_folder
```

---

### 4.12 `check_kdenlive_track_count`

**用途**：验证时间线视频/音频轨道数量。

```python
def check_kdenlive_track_count(project_file_path, rule):
    """
    Args:
        project_file_path: .kdenlive 项目文件路径
        rule: {
            "min_video_tracks": 3,     # 可选：视频轨最小值
            "min_audio_tracks": 3,     # 可选：音频轨最小值
            "exact_video_tracks": 1,   # 可选：视频轨精确值
            "exact_audio_tracks": 2    # 可选：音频轨精确值
        }
    Returns:
        float: 满足约束返回 1.0，否则 0.0
    """
    # 统计主 <tractor> 中 <track> 数量
    # 结合 kdenlive:track_type 区分视频/音频
    # 按 min/exact 规则校验
```

---

### 4.13 `check_kdenlive_guide`

**用途**：验证时间线导标/标记的标签与位置。

```python
def check_kdenlive_guide(project_file_path, rule):
    """
    Args:
        project_file_path: .kdenlive 项目文件路径
        rule: {"guide_comment": "Scene Start", "guide_time_seconds": 5.0, "tolerance": 0.5}
    Returns:
        float: 找到匹配导标返回 1.0，否则 0.0
    """
    # 解析 <property name="kdenlive:docproperties.guides"> 的 JSON 数组
    # 每条 guide 形如 {"comment": "...", "pos": frame_number, ...}
    # 将 pos 转秒，与 guide_time_seconds ± tolerance 比较
    # comment 与 guide_comment 精确匹配
```

---

### 4.14 `check_kdenlive_track_mute`

**用途**：验证指定轨道是否被静音。

```python
def check_kdenlive_track_mute(project_file_path, rule):
    """
    Args:
        project_file_path: .kdenlive 项目文件路径
        rule: {"muted_track": "V1"}
    Returns:
        float: 轨道静音返回 1.0，否则 0.0
    """
    # 根据索引/名称定位 <tractor> 中目标轨道
    # 检查 <track> 的 hide 属性（audio/video/both）
    # 或检查 kdenlive:track 相关静音属性
```

---

### 4.15 `check_kdenlive_track_lock`

**用途**：验证指定轨道是否被锁定。

```python
def check_kdenlive_track_lock(project_file_path, rule):
    """
    Args:
        project_file_path: .kdenlive 项目文件路径
        rule: {"locked_track": "V1"}
    Returns:
        float: 轨道锁定返回 1.0，否则 0.0
    """
    # 在 <tractor> 中定位轨道
    # 检查 <property name="kdenlive:locked_track"> 是否为 "1" / true
```

---

### 4.16 `check_kdenlive_timeline_empty`

**用途**：验证片段在项目箱中，但不在时间线中（例如撤销后）。

```python
def check_kdenlive_timeline_empty(project_file_path, rule):
    """
    Args:
        project_file_path: .kdenlive 项目文件路径
        rule: {"expected_in_bin": "xxx.mp4", "expected_not_on_timeline": true}
    Returns:
        float: 条件满足返回 1.0，否则 0.0
    """
    # 检查匹配 resource 的 <producer> 存在（在项目箱）
    # 检查时间线 playlists 中没有 <entry> 引用该 producer
```

---

### 4.17 `check_kdenlive_color_clip`

**用途**：验证纯色片段存在且颜色正确。

```python
def check_kdenlive_color_clip(project_file_path, rule):
    """
    Args:
        project_file_path: .kdenlive 项目文件路径
        rule: {"expected_color": "#FF0000"}
    Returns:
        float: 匹配颜色片段返回 1.0，否则 0.0
    """
    # 查找 mlt_service="color" 的 <producer>
    # 检查 resource 中颜色值（如 0xff0000ff 或 #FF0000）
    # 归一化后比较
```

---

### 4.18 `check_kdenlive_clip_duration`

**用途**：验证片段时长（纯色片段/标题片段）。

```python
def check_kdenlive_clip_duration(project_file_path, rule):
    """
    Args:
        project_file_path: .kdenlive 项目文件路径
        rule: {"min_duration_seconds": 9.5, "max_duration_seconds": 10.5}
    Returns:
        float: 时长在范围内返回 1.0，否则 0.0
    """
    # 查找纯色/标题 producer
    # 读取 length/out（帧数）
    # 读取项目 fps
    # 换算为秒并校验区间
```

---

### 4.19 `check_kdenlive_proxy_setting`

**用途**：验证代理片段设置是否启用/禁用。

```python
def check_kdenlive_proxy_setting(project_file_path, rule):
    """
    Args:
        project_file_path: .kdenlive 项目文件路径
        rule: {"proxy_enabled": true}
    Returns:
        float: 设置匹配返回 1.0，否则 0.0
    """
    # 检查 <property name="kdenlive:docproperties.enableproxy">
    # "1" 表示启用，"0" 表示禁用
```

---

### 4.20 `check_kdenlive_clip_position`

**用途**：验证片段在时间线上的起始位置。

```python
def check_kdenlive_clip_position(project_file_path, rule):
    """
    Args:
        project_file_path: .kdenlive 项目文件路径
        rule: {"source_file": "xxx.mp4", "start_time": 5.0, "tolerance": 0.5}
    Returns:
        float: 起始位置匹配返回 1.0，否则 0.0
    """
    # 找到包含目标片段的轨道 playlist
    # 累加该 <entry> 之前所有 <blank length="N"/> 的帧数
    # 用项目 fps 转换为秒
    # 与 start_time ± tolerance 比较
```

---

### 4.21 `check_kdenlive_snapshot_exists`

**用途**：验证截图图片文件是否已生成。

```python
def check_kdenlive_snapshot_exists(result, rule):
    """
    Args:
        result: vm_command_line 的输出（文件数量字符串）
        rule: {"min_count": 1}
    Returns:
        float: 文件数 >= min_count 返回 1.0，否则 0.0
    """
    # 从结果字符串解析整数
    # 与 min_count 比较
```

---

### 4.22 `check_kdenlive_effect_applied`

**用途**：通用评测器，验证指定视频/音频效果已应用。

**校验逻辑**：
- 找到匹配 `source_file` 的 `<producer>` 或 `<chain>`
- 查找与之关联的 `<filter>`
- 判断是否存在 `mlt_service` 命中 `effect_service` 列表
- 支持多个可选服务名（兼容 Kdenlive 内部命名差异）

```python
def check_kdenlive_effect_applied(project_file_path, rule):
    """
    Args:
        project_file_path: .kdenlive 项目文件路径
        rule: {
            "effect_service": ["box_blur", "boxblur", "blur"],  # 可接受的 mlt_service 名称
            "source_file": "xxx.mp4"                               # 可选：限定片段
        }
    Returns:
        float: 找到匹配效果返回 1.0，否则 0.0
    """
    # 遍历 tractor/playlist 中所有 <filter>
    # 检查 mlt_service 是否在 effect_service 列表
    # 若指定 source_file，需确认效果应用在该片段上
```

---

### 4.23 `check_kdenlive_effect_param`

**用途**：验证某效果的参数值（如旋转角度、不透明度）。

**校验逻辑**：
- 查找匹配 `mlt_service` 的 `<filter>`
- 读取目标参数属性值
- 在容差范围内与期望值比较

```python
def check_kdenlive_effect_param(project_file_path, rule):
    """
    Args:
        project_file_path: .kdenlive 项目文件路径
        rule: {
            "effect_service": ["rotate", "affine"],  # 可接受的 mlt_service 名称
            "param_name": "rotate",                    # 要检查的参数名
            "expected_value": 90,                       # 期望数值
            "tolerance": 5                              # 比较容差
        }
    Returns:
        float: 参数匹配返回 1.0，否则 0.0
    """
    # 找 mlt_service 命中的 <filter>
    # 读取 <property name="param_name"> 值
    # 转 float 后与 expected_value ± tolerance 比较
```

---

### 4.24 `check_kdenlive_audio_fade`

**用途**：验证片段音频淡入/淡出效果。

**校验逻辑**：
- 找到匹配 `source_file` 的 producer
- 检查 `volume`/`brightness` 过滤器关键帧数据，或 `fade_from_audio` / `fade_to_audio`
- 验证是否存在淡入（0→1）和/或淡出（1→0）

```python
def check_kdenlive_audio_fade(project_file_path, rule):
    """
    Args:
        project_file_path: .kdenlive 项目文件路径
        rule: {
            "fade_in": true,
            "fade_out": true,
            "source_file": "xxx.mp3"
        }
    Returns:
        float: 满足淡入/淡出要求返回 1.0，否则 0.0
    """
    # 查找带关键帧的 volume/brightness 过滤器
    # 或查找 fade_from_audio / fade_to_audio
    # fade_in: 音量由 0 上升
    # fade_out: 音量向 0 下降
```

---

### 4.25 `check_kdenlive_clip_split`

**用途**：验证片段在时间线上已被分割为多个片段。

**校验逻辑**：
- 在所有时间线 playlist 中查找引用 `source_file` 对应 producer 的 `<entry>`
- 统计片段数量
- 判断是否达到 `min_segments`

```python
def check_kdenlive_clip_split(project_file_path, rule):
    """
    Args:
        project_file_path: .kdenlive 项目文件路径
        rule: {
            "source_file": "xxx.mp4",
            "min_segments": 2
        }
    Returns:
        float: 分段数 >= min_segments 返回 1.0，否则 0.0
    """
    # 找到匹配 source_file 的 producer id
    # 统计所有 playlist 中引用这些 producer 的 <entry>
    # count >= min_segments 则通过
```

---

### 4.26 `check_kdenlive_multi_track_composition`

**用途**：验证多轨合成场景（如 PiP、水印叠加）。

**校验逻辑**：
- 验证 `main_file` 和 `overlay_file` 都存在
- 验证两者在**不同**轨道
- 若 `require_transform=true`，验证叠加轨有 transform/affine/qtblend 等效果

```python
def check_kdenlive_multi_track_composition(project_file_path, rule):
    """
    Args:
        project_file_path: .kdenlive 项目文件路径
        rule: {
            "main_file": "main.mp4",
            "overlay_file": "overlay.mp4",
            "require_transform": true
        }
    Returns:
        float: 合成配置正确返回 1.0，否则 0.0
    """
    # 查找 main_file 与 overlay_file 对应 producer
    # 验证它们位于不同轨道
    # 若 require_transform，检查 overlay 轨上的 affine/qtblend/composite 过滤器
```

---

### 4.27 `check_kdenlive_clip_count`

**用途**：验证片段在时间线出现次数（如复制粘贴后）。

**校验逻辑**：
- 查找匹配 `source_file` 的 producers
- 统计所有时间线 playlist 中引用这些 producer 的 `<entry>` 数量
- 与 `min_count` 比较

```python
def check_kdenlive_clip_count(project_file_path, rule):
    """
    Args:
        project_file_path: .kdenlive 项目文件路径
        rule: {
            "source_file": "xxx.mp4",
            "min_count": 2
        }
    Returns:
        float: 出现次数 >= min_count 返回 1.0，否则 0.0
    """
    # 找到匹配 source_file 的 producer id
    # 统计引用次数
    # count >= min_count 则通过
```

---

### 4.28 `check_kdenlive_clip_group`

**用途**：验证时间线上片段分组是否成功。

**校验逻辑**：
- 解析项目 XML 中的 `<group>` 或 `kdenlive:group`
- 统计分组数量及每组片段数
- 验证至少有 `min_groups` 个分组，且每组至少 `min_clips_in_group` 个片段

```python
def check_kdenlive_clip_group(project_file_path, rule):
    """
    Args:
        project_file_path: .kdenlive 项目文件路径
        rule: {
            "min_groups": 1,
            "min_clips_in_group": 2
        }
    Returns:
        float: 满足分组约束返回 1.0，否则 0.0
    """
    # 解析 <group> 或 kdenlive:group
    # 统计分组和成员片段数量
    # 校验约束
```

---

### 4.29 `check_kdenlive_render_custom_resolution`

**用途**：验证渲染输出分辨率、编码和时长。

**校验逻辑**：
- ffprobe 检查输出文件
- 验证视频编码与期望一致
- 验证分辨率（宽×高）与期望一致
- 验证时长不低于下限

```python
def check_kdenlive_render_custom_resolution(result_file_path, rule):
    """
    Args:
        result_file_path: 渲染输出 MP4 路径
        rule: {
            "min_duration": 1.0,
            "expected_codec": "h264",
            "expected_width": 1280,
            "expected_height": 720
        }
    Returns:
        float: 全部匹配返回 1.0，否则 0.0
    """
    # 用 ffprobe 获取流信息
    # 校验 codec
    # 校验 width/height
    # 校验 duration >= min_duration
```

---

### 4.30 `check_kdenlive_render_multi_clip_transition`

**用途**：验证“多片段 + 转场 + 渲染”任务，需同时检查输出视频与项目文件。

**校验逻辑**：
1. ffprobe 验证输出 MP4（编码、时长）
2. 解析 `.kdenlive`，确认所有期望片段已导入
3. 确认至少存在一个目标转场（如 dissolve/luma）

```python
def check_kdenlive_render_multi_clip_transition(result_file_path, rule):
    """
    Args:
        result_file_path: 渲染输出 MP4 路径
        rule: {
            "min_duration": 5.0,
            "expected_codec": "h264",
            "project_path": "/home/user/Videos/project.kdenlive",
            "expected_files": ["clip1.mp4", "clip2.mp4", "clip3.mp4"],
            "transition_type": "luma"
        }
    Returns:
        float: 全部检查通过返回 1.0，否则 0.0
    """
    # Step 1: 复用 check_kdenlive_render_mp4 逻辑
    # Step 2: 解析 project_path，验证 expected_files 都存在
    # Step 3: 验证 <transition> 中存在 transition_type
```

---

### 4.31 `check_kdenlive_render_effects_composite`

**用途**：验证“效果 + 渲染”综合任务，检查灰度效果与音量调整。

**校验逻辑**：
1. ffprobe 验证输出 MP4（编码、时长）
2. 解析 `.kdenlive`，验证灰度效果存在
3. 验证音量调整值匹配

```python
def check_kdenlive_render_effects_composite(result_file_path, rule):
    """
    Args:
        result_file_path: 渲染输出 MP4 路径
        rule: {
            "min_duration": 1.0,
            "expected_codec": "h264",
            "project_path": "/home/user/Videos/project.kdenlive",
            "require_grayscale": true,
            "expected_volume": 0.3,
            "volume_tolerance": 0.05
        }
    Returns:
        float: 全部检查通过返回 1.0，否则 0.0
    """
    # Step 1: 复用 check_kdenlive_render_mp4
    # Step 2: 复用 check_kdenlive_grayscale_effect
    # Step 3: 复用 check_kdenlive_volume_adjustment
```

---

### 4.32 `check_kdenlive_render_title_video_title`

**用途**：验证“标题 + 视频 + 标题 + 渲染”任务。

**校验逻辑**：
1. ffprobe 验证输出 MP4（编码、时长 ≥ 5s）
2. 解析 `.kdenlive`，确认标题 producer 存在
3. 对每个期望标题文本，验证其出现在 kdenlivetitle 的 xmldata 中

```python
def check_kdenlive_render_title_video_title(result_file_path, rule):
    """
    Args:
        result_file_path: 渲染输出 MP4 路径
        rule: {
            "min_duration": 5.0,
            "expected_codec": "h264",
            "project_path": "/home/user/Videos/project.kdenlive",
            "expected_titles": ["Welcome to My Video", "Thank You"]
        }
    Returns:
        float: 全部检查通过返回 1.0，否则 0.0
    """
    # Step 1: 复用 check_kdenlive_render_mp4
    # Step 2: 对 expected_titles 逐个执行 check_kdenlive_title_text 逻辑
```

---

### 4.33 `check_kdenlive_render_speed_ramp`

**用途**：验证“速度变化 + 渲染”任务。

**校验逻辑**：
1. ffprobe 验证输出 MP4（编码、时长）
2. 解析 `.kdenlive`，验证片段已分割（≥ min_segments）
3. 验证存在与 `expected_speed` 匹配的速度修改

```python
def check_kdenlive_render_speed_ramp(result_file_path, rule):
    """
    Args:
        result_file_path: 渲染输出 MP4 路径
        rule: {
            "min_duration": 2.0,
            "expected_codec": "h264",
            "project_path": "/home/user/Videos/project.kdenlive",
            "source_file": "14307439_1920_1080_60fps.mp4",
            "min_segments": 2,
            "expected_speed": 3.0,
            "speed_tolerance": 0.1
        }
    Returns:
        float: 全部检查通过返回 1.0，否则 0.0
    """
    # Step 1: 复用 check_kdenlive_render_mp4
    # Step 2: 复用 check_kdenlive_clip_split（min_segments）
    # Step 3: 复用 check_kdenlive_clip_speed（expected_speed）
```

---

### 4.34 `check_kdenlive_render_pip`

**用途**：验证“画中画 + 渲染”任务。

**校验逻辑**：
1. ffprobe 验证输出 MP4（编码、时长）
2. 解析 `.kdenlive`，验证两个片段位于不同轨道
3. 验证叠加轨有 transform/affine 效果

```python
def check_kdenlive_render_pip(result_file_path, rule):
    """
    Args:
        result_file_path: 渲染输出 MP4 路径
        rule: {
            "min_duration": 1.0,
            "expected_codec": "h264",
            "project_path": "/home/user/Videos/project.kdenlive",
            "main_file": "15368811_1920_1080_30fps.mp4",
            "overlay_file": "6533277-hd_1920_1080_24fps.mp4",
            "require_transform": true
        }
    Returns:
        float: 全部检查通过返回 1.0，否则 0.0
    """
    # Step 1: 复用 check_kdenlive_render_mp4
    # Step 2: 复用 check_kdenlive_multi_track_composition
```

---

### 4.35 `check_kdenlive_render_audio_mix`

**用途**：验证“多轨混音 + 渲染”任务。

**校验逻辑**：
1. ffprobe 验证输出 MP4（编码、时长、音频流）
2. 解析 `.kdenlive`，验证期望音频文件均已导入
3. 验证背景音乐音量与期望值一致

```python
def check_kdenlive_render_audio_mix(result_file_path, rule):
    """
    Args:
        result_file_path: 渲染输出 MP4 路径
        rule: {
            "min_duration": 1.0,
            "expected_codec": "h264",
            "project_path": "/home/user/Videos/project.kdenlive",
            "require_audio": true,
            "expected_volume": 0.4,
            "volume_tolerance": 0.05,
            "expected_audio_files": ["bgm.mp3", "sfx.wav"]
        }
    Returns:
        float: 全部检查通过返回 1.0，否则 0.0
    """
    # Step 1: 复用 check_kdenlive_render_with_audio
    # Step 2: 复用 check_kdenlive_import_multiple_files（expected_audio_files）
    # Step 3: 复用 check_kdenlive_volume_adjustment（expected_volume）
```

---

### 4.36 `check_kdenlive_render_color_grading`

**用途**：验证“调色流水线 + 渲染”任务。

**校验逻辑**：
1. ffprobe 验证输出 MP4（编码、时长）
2. 解析 `.kdenlive`，验证亮度效果已应用
3. 验证 sepia 效果已应用
4. 验证音频淡入和淡出存在

```python
def check_kdenlive_render_color_grading(result_file_path, rule):
    """
    Args:
        result_file_path: 渲染输出 MP4 路径
        rule: {
            "min_duration": 1.0,
            "expected_codec": "h264",
            "project_path": "/home/user/Videos/project.kdenlive",
            "require_brightness": true,
            "require_sepia": true,
            "require_fade_in": true,
            "require_fade_out": true
        }
    Returns:
        float: 全部检查通过返回 1.0，否则 0.0
    """
    # Step 1: 复用 check_kdenlive_render_mp4
    # Step 2: 复用 check_kdenlive_effect_applied（brightness）
    # Step 3: 复用 check_kdenlive_effect_applied（sepia）
    # Step 4: 复用 check_kdenlive_audio_fade（fade_in + fade_out）
```

---

## 5. 任务难度总览

```text
Level 1（基础）— 21 个任务
────────────────────────────────────────────────────────────
类别：项目箱管理
  任务 1-1  导入视频到项目箱
  任务 1-5  导入多个文件到项目箱
  任务 1-9  从项目箱删除片段
  任务 1-10 在项目箱重命名片段
  任务 1-11 在项目箱创建文件夹
  任务 1-19 创建纯色片段
  任务 1-20 设置片段时长（纯色/标题）

类别：时间线基础操作
  任务 1-3  添加视频到时间线
  任务 1-24 移动时间线片段位置
  任务 1-18 撤销上一步操作
  任务 1-21 从片段监视器截图

类别：轨道管理
  任务 1-12 新增视频轨
  任务 1-14 删除轨道
  任务 1-15 添加导标/标记
  任务 1-16 轨道静音
  任务 1-17 轨道锁定

类别：项目设置
  任务 1-4  设置项目分辨率
  任务 1-7  设置项目帧率
  任务 1-8  以指定名称保存项目
  任务 1-22 启用代理片段
  任务 1-23 设置预览分辨率


Level 2（中级）— 14 个任务
────────────────────────────────────────────────────────────
类别：视频效果
  任务 2-1  应用灰度效果
  任务 2-7  应用模糊效果
  任务 2-9  视频旋转 90 度
  任务 2-17 调整不透明度/透明度

类别：音频效果
  任务 2-2  调整音量
  任务 2-12 添加音频淡入/淡出

类别：时间线编辑
  任务 2-3  修剪视频片段
  任务 2-6  修改片段播放速度
  任务 2-13 分割/切割片段
  任务 2-15 复制并粘贴片段
  任务 2-16 分组片段

类别：转场与合成
  任务 2-4  添加 Dissolve 转场
  任务 2-14 画中画（PiP）

类别：文本/标题
  任务 2-5  添加标题文本


Level 3（高级）— 10 个任务
────────────────────────────────────────────────────────────
类别：基础渲染
  任务 3-1  渲染 MP4
  任务 3-10 渲染自定义分辨率 MP4

类别：音视频联合渲染
  任务 3-2  添加 BGM + 渲染
  任务 3-8  多音轨混音 + 渲染

类别：多片段编辑 + 渲染
  任务 3-3  多片段 + 转场 + 渲染
  任务 3-5  标题开场 + 视频 + 片尾 + 渲染
  任务 3-6  速度变化视频 + 渲染

类别：合成 + 渲染
  任务 3-7  画中画 + 渲染

类别：效果流水线 + 渲染
  任务 3-4  效果 + 渲染（综合）
  任务 3-9  调色流水线 + 渲染
```

---

## 6. 新评测器注册

实现新评测器后，需要在 `desktop_env/evaluators/metrics/__init__.py` 中注册：

```python
from .kdenlive import (
    check_kdenlive_import_video,
    check_kdenlive_add_to_timeline,
    check_kdenlive_grayscale_effect,
    check_kdenlive_volume_adjustment,
    check_kdenlive_render_mp4,
    # 需要新增注册的函数：
    check_kdenlive_project_profile,
    check_kdenlive_clip_trim,
    check_kdenlive_transition,
    check_kdenlive_title_text,
    check_kdenlive_clip_speed,
    check_kdenlive_render_with_audio,
    # Level 1 扩展函数：
    check_kdenlive_import_multiple_files,
    check_kdenlive_file_exists,
    check_kdenlive_bin_content,
    check_kdenlive_clip_name,
    check_kdenlive_bin_folder,
    check_kdenlive_track_count,
    check_kdenlive_guide,
    check_kdenlive_track_mute,
    check_kdenlive_track_lock,
    check_kdenlive_timeline_empty,
    check_kdenlive_color_clip,
    check_kdenlive_clip_duration,
    check_kdenlive_proxy_setting,
    check_kdenlive_clip_position,
    check_kdenlive_snapshot_exists,
    # Level 2 扩展函数：
    check_kdenlive_effect_applied,
    check_kdenlive_effect_param,
    check_kdenlive_audio_fade,
    check_kdenlive_clip_split,
    check_kdenlive_multi_track_composition,
    check_kdenlive_clip_count,
    check_kdenlive_clip_group,
    # Level 3 扩展函数：
    check_kdenlive_render_custom_resolution,
    check_kdenlive_render_multi_clip_transition,
    check_kdenlive_render_effects_composite,
    check_kdenlive_render_title_video_title,
    check_kdenlive_render_speed_ramp,
    check_kdenlive_render_pip,
    check_kdenlive_render_audio_mix,
    check_kdenlive_render_color_grading,
)
```

---

## 7. 实现说明

1. **优先级**：优先实现 Level 1 和 Level 2。这两类主要依赖 `.kdenlive` XML 解析，执行快且稳定，无需等待渲染。

2. **渲染任务（Level 3）**：渲染可能耗时数分钟。建议在 `config` 中增加 `sleep` 时长，或在 `postconfig` 中等待渲染完成。

3. **项目文件路径约定**：所有任务都应在 `instruction` 中明确要求保存到统一路径（例如 `/home/user/Videos/project.kdenlive`）。

4. **配置执行顺序**：`upload_file` → `launch` → `sleep` →（Agent 执行任务）→ `postconfig` → 评测。

5. **Kdenlive 启动路径**：所有任务使用 `/home/user/.local/bin/kdenlive` 作为启动命令。

   标准 `config` 中的启动步骤应始终放在所有 `upload_file` 之后、`sleep` 之前。

---

## 8. Level 3 任务 JSON ID 映射

| 任务 | UUID | 评测器 |
|------|------|--------|
| 任务 3-1：渲染 MP4 | `fd3ae9f3-841f-4b11-b72d-e090eea0e706` | `check_kdenlive_render_mp4` |
| 任务 3-2：添加 BGM + 渲染 | `4be9b350-d9ad-4bd9-82b3-788bb214bb7d` | `check_kdenlive_render_with_audio` |
| 任务 3-3：多片段 + 转场 + 渲染 | `bb095bd9-5919-4a02-86da-2a9bb6380ff1` | `check_kdenlive_render_multi_clip_transition` |
| 任务 3-4：效果 + 渲染 | `07186918-9646-45af-805b-2a13c02ac63f` | `check_kdenlive_render_effects_composite` |
| 任务 3-5：标题 + 视频 + 标题 + 渲染 | `081b45e0-3ecc-4fde-b2ca-62eed6400255` | `check_kdenlive_render_title_video_title` |
| 任务 3-6：速度变化 + 渲染 | `abbaf9fe-861f-400e-8fd8-77a03e50a281` | `check_kdenlive_render_speed_ramp` |
| 任务 3-7：画中画 + 渲染 | `a73dd78e-fb7d-4dd5-a829-f174b5603a85` | `check_kdenlive_render_pip` |
| 任务 3-8：混音 + 渲染 | `d3a66c10-476d-4f83-9155-5e3526d6cf31` | `check_kdenlive_render_audio_mix` |
| 任务 3-9：调色 + 渲染 | `8c708e3d-ff5e-4306-8fd3-3a4c674f30e7` | `check_kdenlive_render_color_grading` |
| 任务 3-10：自定义分辨率 + 渲染 | `49c6d9d4-a682-46fa-a8ef-907eb976d042` | `check_kdenlive_render_custom_resolution` |
