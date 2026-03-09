# Kdenlive 原子功能完全目录

本文档详细列出 Kdenlive 视频编辑器的所有原子功能（L1 级别），按功能域分类，并为每个功能说明：
- 功能描述
- 对应的 GUI 操作路径 / 快捷键
- Evaluator 验证策略（基于 `.kdenlive` 项目文件 XML 解析 / `ffprobe` 文件检查 / 配置文件检查）
- 可行性等级（✅ 高可行 / ⚠️ 中可行 / ❌ 低可行）

---

## 技术前提：Kdenlive 项目文件结构

Kdenlive 项目文件 (`.kdenlive`) 基于 **MLT XML** 格式，核心 XML 结构如下：

```xml
<mlt>
  <profile description="HD 1080p 30fps" width="1920" height="1080"
           frame_rate_num="30" frame_rate_den="1" ... />

  <!-- producer: 媒体素材/生成器 -->
  <producer id="producer0" in="00:00:00.000" out="00:00:10.000">
    <property name="resource">/home/user/Desktop/video.mp4</property>
    <property name="mlt_service">avformat</property>
    <filter id="filter0" mlt_service="volume">
      <property name="level">0.5</property>
    </filter>
  </producer>

  <!-- playlist: 轨道上的片段序列 -->
  <playlist id="playlist0">
    <entry producer="producer0" in="00:00:00.000" out="00:00:05.000"/>
    <blank length="00:00:02.000"/>
    <entry producer="producer1" in="00:00:00.000" out="00:00:03.000"/>
  </playlist>

  <!-- tractor: 多轨合成 -->
  <tractor id="tractor0">
    <track producer="playlist0"/>  <!-- V1 视频轨 -->
    <track producer="playlist1"/>  <!-- V2 视频轨 -->
    <track producer="playlist2"/>  <!-- A1 音频轨 -->
    <transition mlt_service="luma">...</transition>
    <transition mlt_service="mix">...</transition>
  </tractor>
</mlt>
```

**关键验证点**：
- `<profile>` → 项目分辨率、帧率
- `<producer>` + `<property name="resource">` → 导入的媒体文件
- `<playlist>` + `<entry>` → 时间线上的片段（in/out 点标记裁剪范围）
- `<filter>` → 应用的效果（volume, brightness, speed 等）
- `<transition>` → 转场效果
- `<tractor>` + `<track>` → 多轨结构

**配置文件**：`~/.config/kdenliverc`（INI 格式，KDE Config）

---

## 类别 1：项目管理

### 1.1 创建新项目并设置参数
- **操作**：File → New → 设置 Profile（分辨率/帧率）
- **快捷键**：`Ctrl+N`
- **验证策略**：解析 `.kdenlive` 文件的 `<profile>` 节点，检查 `width`、`height`、`frame_rate_num`、`frame_rate_den`
- **可行性**：✅ 高可行
- **示例 instruction**："Create a new Kdenlive project with 1920x1080 resolution at 30fps and save it to /home/user/Desktop/my_project.kdenlive"

### 1.2 保存项目到指定路径
- **操作**：File → Save As
- **快捷键**：`Ctrl+Shift+S`
- **验证策略**：检查指定路径是否存在 `.kdenlive` 文件，且文件大小 > 0
- **可行性**：✅ 高可行
- **示例 instruction**："Save the current Kdenlive project as /home/user/Desktop/saved_project.kdenlive"

### 1.3 修改现有项目的 Profile 设置
- **操作**：Project → Project Settings → 修改 Profile
- **验证策略**：解析修改后的 `.kdenlive` 文件的 `<profile>` 节点
- **可行性**：✅ 高可行
- **示例 instruction**："Change the current project's resolution to 3840x2160 (4K) and frame rate to 24fps"

### 1.4 设置项目时长/工作区域
- **操作**：Project → Project Settings → 设置项目时长
- **验证策略**：解析 `<tractor>` 的 `out` 属性验证总时长
- **可行性**：⚠️ 中可行（时长可能由内容自动决定）

---

## 类别 2：素材管理（Project Bin / 素材库）

### 2.1 导入视频文件到素材库
- **操作**：Project → Add Clip → 选择视频文件；或拖拽文件到素材库
- **快捷键**：无默认
- **验证策略**：解析 `.kdenlive` 文件，检查是否存在 `<producer>` 节点，其 `<property name="resource">` 值包含目标文件路径
- **可行性**：✅ 高可行
- **示例 instruction**："Import the video file /home/user/Desktop/sample_video.mp4 into the project bin"

### 2.2 导入音频文件到素材库
- **操作**：同上，选择音频文件
- **验证策略**：同上，检查 producer 的 resource 属性指向音频文件
- **可行性**：✅ 高可行
- **示例 instruction**："Import the audio file /home/user/Desktop/background_music.mp3 into the project bin"

### 2.3 导入图片文件到素材库
- **操作**：同上，选择图片文件
- **验证策略**：同上，检查 producer 的 resource 属性指向图片文件
- **可行性**：✅ 高可行
- **示例 instruction**："Import the image /home/user/Desktop/logo.png into the project bin"

### 2.4 创建纯色片段（Color Clip）
- **操作**：Project → Add Color Clip → 选择颜色
- **验证策略**：检查是否存在 `<producer>` 节点，其 `mlt_service` 为 `color` 且 `<property name="resource">` 包含颜色值
- **可行性**：✅ 高可行
- **示例 instruction**："Create a 5-second red color clip (#FF0000) in the project bin"

### 2.5 创建标题片段（Title Clip）
- **操作**：Project → Add Title Clip → 输入文字
- **验证策略**：检查是否存在标题类型的 `<producer>` 节点，其 `mlt_service` 为 `kdenlivetitle`，且子属性中包含指定文字内容（`xmldata` 属性中的文本）
- **可行性**：✅ 高可行
- **示例 instruction**："Create a title clip with the text 'Hello World' in white color on a transparent background"

### 2.6 删除素材库中的片段
- **操作**：在素材库中右键 → Delete Clip
- **验证策略**：解析项目文件，验证指定的 producer 不再存在
- **可行性**：⚠️ 中可行（需要对比前后状态）

### 2.7 重命名素材库中的片段
- **操作**：在素材库中右键 → Rename / 双击名称
- **验证策略**：解析项目文件中 producer 的 `kdenlive:clipname` 属性
- **可行性**：⚠️ 中可行

---

## 类别 3：时间线编辑

### 3.1 将素材添加到时间线轨道
- **操作**：从素材库拖拽到时间线；或右键 → Insert Clip
- **验证策略**：解析 `<playlist>` 中的 `<entry>` 节点，验证对应 producer 的引用和所在轨道
- **可行性**：✅ 高可行
- **示例 instruction**："Add the video clip sample_video.mp4 to the first video track (V1) in the timeline"

### 3.2 在指定时间点分割片段（Razor/Split）
- **操作**：选择剃刀工具（X 键）→ 在时间线上点击分割点
- **快捷键**：`X`（切换到剃刀工具）
- **验证策略**：检查 `<playlist>` 中原本一个 `<entry>` 变为两个相邻的 `<entry>`，且 out/in 值对应分割帧
- **可行性**：✅ 高可行
- **示例 instruction**："Split the video clip on track V1 at the 5-second mark"

### 3.3 删除时间线上的片段
- **操作**：选中片段 → Delete 键
- **验证策略**：检查 `<playlist>` 中对应的 `<entry>` 已被移除（或替换为 `<blank>`）
- **可行性**：✅ 高可行
- **示例 instruction**："Delete the second clip on track V1"

### 3.4 裁剪片段的入点/出点（Trim）
- **操作**：拖拽片段边缘调整入/出点
- **验证策略**：检查 `<entry>` 的 `in` 和 `out` 属性是否与预期值匹配
- **可行性**：✅ 高可行
- **示例 instruction**："Trim the video clip on V1 so it starts at 3 seconds and ends at 8 seconds"

### 3.5 移动片段到不同位置
- **操作**：选中片段 → 拖拽到新位置
- **验证策略**：检查 `<entry>` 在 `<playlist>` 中的位置和前后 `<blank>` 的长度
- **可行性**：⚠️ 中可行（位置由 blank 间接确定）

### 3.6 复制粘贴片段
- **操作**：`Ctrl+C` / `Ctrl+V`
- **验证策略**：检查 `<playlist>` 中是否出现重复的 `<entry>` 引用
- **可行性**：⚠️ 中可行

### 3.7 添加/删除轨道
- **操作**：右键轨道头部 → Insert Track / Delete Track
- **验证策略**：检查 `<tractor>` 中 `<track>` 的数量以及对应的 `<playlist>` 数量
- **可行性**：✅ 高可行
- **示例 instruction**："Add a new video track (V3) above the existing tracks"

### 3.8 锁定/解锁轨道
- **操作**：点击轨道头部的锁定图标
- **验证策略**：检查项目文件中轨道的 `kdenlive:locked_track` 属性
- **可行性**：✅ 高可行
- **示例 instruction**："Lock the audio track A1"

### 3.9 静音/取消静音轨道
- **操作**：点击轨道头部的静音图标
- **验证策略**：检查 `<track>` 的 `hide` 属性（`audio` = 静音音频，`video` = 隐藏视频，`both` = 全隐藏）
- **可行性**：✅ 高可行
- **示例 instruction**："Mute the audio track A1"

### 3.10 设置片段的入点和出点标记
- **操作**：`I` 键设置入点，`O` 键设置出点
- **验证策略**：检查项目文件中的 zone 属性（`<property name="kdenlive:zone_in">` 和 `kdenlive:zone_out`）
- **可行性**：⚠️ 中可行

---

## 类别 4：视频效果（Video Effects / Filters）

### 4.1 调整亮度
- **操作**：Effects → Video Effects → Color Correction → Brightness
- **验证策略**：检查片段下的 `<filter>` 节点，`mlt_service` 为 `brightness` 或 `avfilter.eq`，检查 `brightness` 参数值
- **可行性**：✅ 高可行
- **示例 instruction**："Increase the brightness of the video clip on V1 by 20%"

### 4.2 调整对比度
- **操作**：Effects → Video Effects → Color Correction → Contrast
- **验证策略**：检查 `<filter>` 的 `contrast` 参数
- **可行性**：✅ 高可行
- **示例 instruction**："Increase the contrast of the video clip on V1 by 30%"

### 4.3 调整饱和度
- **操作**：Effects → Video Effects → Color Correction → Saturation
- **验证策略**：检查 `<filter>` 的 `saturation` 参数（`avfilter.eq` 或 `avfilter.hue`）
- **可行性**：✅ 高可行
- **示例 instruction**："Set the saturation of the video clip on V1 to 150%"

### 4.4 应用模糊效果
- **操作**：Effects → Video Effects → Blur and Hide → Box Blur / Gaussian Blur
- **验证策略**：检查 `<filter>` 的 `mlt_service` 为 `box_blur` 或 `avfilter.boxblur`
- **可行性**：✅ 高可行
- **示例 instruction**："Apply a Gaussian blur effect to the video clip on V1"

### 4.5 应用锐化效果
- **操作**：Effects → Video Effects → Sharpen
- **验证策略**：检查 `<filter>` 的 `mlt_service` 为 `avfilter.unsharp`
- **可行性**：✅ 高可行

### 4.6 水平/垂直翻转
- **操作**：Effects → Video Effects → Transform → Mirror
- **验证策略**：检查 `<filter>` 的 `mlt_service` 为 `mirror` 或 `avfilter.hflip` / `avfilter.vflip`
- **可行性**：✅ 高可行
- **示例 instruction**："Flip the video clip on V1 horizontally"

### 4.7 旋转视频
- **操作**：Effects → Video Effects → Transform → Rotate
- **验证策略**：检查 `<filter>` 的 `mlt_service` 为 `affine` 或 `qtblend`，检查 `rotate` 参数
- **可行性**：✅ 高可行
- **示例 instruction**："Rotate the video clip on V1 by 90 degrees clockwise"

### 4.8 裁剪画面区域（Crop）
- **操作**：Effects → Video Effects → Transform → Crop, Scale and Tilt
- **验证策略**：检查 `<filter>` 中的 `crop` 相关参数（left, right, top, bottom）
- **可行性**：✅ 高可行
- **示例 instruction**："Crop the video clip on V1 to remove the top 100 pixels"

### 4.9 调整播放速度（Speed Effect）
- **操作**：右键片段 → Change Speed → 设置速度百分比
- **验证策略**：检查 `<producer>` 的 `mlt_service` 是否变为 `timewarp`，以及 `warp_speed` 参数
- **可行性**：✅ 高可行
- **示例 instruction**："Change the speed of the video clip on V1 to 2x (double speed)"

### 4.10 应用色彩平衡/色温调整
- **操作**：Effects → Video Effects → Color Correction → Color Balance / White Balance
- **验证策略**：检查 `<filter>` 的 `mlt_service` 为 `avfilter.colorbalance` 或 `lift_gamma_gain`，检查参数
- **可行性**：✅ 高可行
- **示例 instruction**："Apply a warm color temperature adjustment to the video clip on V1"

### 4.11 转换为黑白/灰度
- **操作**：Effects → Video Effects → Color Correction → Greyscale
- **验证策略**：检查 `<filter>` 的 `mlt_service` 为 `grayscale` 或 `avfilter.colorchannelmixer`
- **可行性**：✅ 高可行
- **示例 instruction**："Convert the video clip on V1 to grayscale (black and white)"

### 4.12 应用色度键/绿幕抠像（Chroma Key）
- **操作**：Effects → Video Effects → Alpha, Mask and Keying → Chroma Key
- **验证策略**：检查 `<filter>` 的 `mlt_service` 为 `avfilter.chromakey` 或 `frei0r.select0r`，检查颜色参数
- **可行性**：✅ 高可行
- **示例 instruction**："Apply chroma key effect to remove the green background from the video clip on V2"

### 4.13 应用视频淡入/淡出
- **操作**：Effects → Video Effects → Motion → Fade In / Fade Out
- **验证策略**：检查 `<filter>` 的 `mlt_service` 为 `brightness`（带 `alpha` 关键帧）或 `fade_from_black` / `fade_to_black`
- **可行性**：✅ 高可行
- **示例 instruction**："Add a 2-second fade-in from black at the beginning of the video clip on V1"

### 4.14 添加缩放/平移关键帧动画（Ken Burns / Keyframe）
- **操作**：Effects → Transform → Position and Zoom → 添加关键帧
- **验证策略**：检查 `<filter>` 中是否存在关键帧参数（如 `rect` 属性包含多帧值 `frame=x y w h`）
- **可行性**：⚠️ 中可行（关键帧参数格式复杂）

---

## 类别 5：音频效果（Audio Effects / Filters）

### 5.1 调整音量
- **操作**：Effects → Audio Effects → Volume → Volume (keyframable)
- **验证策略**：检查 `<filter>` 的 `mlt_service` 为 `volume`，检查 `level` 参数值
- **可行性**：✅ 高可行
- **示例 instruction**："Set the audio volume of the clip on A1 to 50%"

### 5.2 添加音频淡入效果
- **操作**：Effects → Audio Effects → Fade → Fade In
- **验证策略**：检查 `<filter>` 的 `mlt_service` 为 `volume`，且 `level` 参数包含从 0 到目标值的关键帧，或 `tag` 为 `fadeInVolume`
- **可行性**：✅ 高可行
- **示例 instruction**："Add a 3-second audio fade-in to the clip on A1"

### 5.3 添加音频淡出效果
- **操作**：Effects → Audio Effects → Fade → Fade Out
- **验证策略**：检查 `<filter>` 的 `tag` 为 `fadeOutVolume`，检查持续帧数
- **可行性**：✅ 高可行
- **示例 instruction**："Add a 5-second audio fade-out at the end of the clip on A1"

### 5.4 静音视频的原始音频
- **操作**：右键片段 → Disable Clip (audio)；或设置音量为 0
- **验证策略**：检查 `<filter>` 的 `mlt_service` 为 `volume`，`level` 为 0；或检查 `<entry>` 的属性
- **可行性**：✅ 高可行
- **示例 instruction**："Mute the original audio of the video clip on V1"

### 5.5 应用音频均衡器（EQ）
- **操作**：Effects → Audio Effects → Equalizer
- **验证策略**：检查 `<filter>` 的 `mlt_service` 为 `avfilter.equalizer` 或 `ladspa.*`
- **可行性**：⚠️ 中可行（参数较复杂）

### 5.6 应用音频降噪
- **操作**：Effects → Audio Effects → Noise Gate / Noise Reduction
- **验证策略**：检查 `<filter>` 的 `mlt_service` 为 `avfilter.afftdn` 或类似降噪 filter
- **可行性**：⚠️ 中可行

### 5.7 调整音频声道（左/右/立体声）
- **操作**：Effects → Audio Effects → Channels → Audio Pan / Balance
- **验证策略**：检查 `<filter>` 的 `mlt_service` 为 `panner` 或 `avfilter.pan`
- **可行性**：⚠️ 中可行

---

## 类别 6：转场效果（Transitions / Compositions）

### 6.1 添加溶解转场（Dissolve）
- **操作**：在两个重叠片段之间右键 → Add Transition → Dissolve
- **验证策略**：检查 `<transition>` 节点，`mlt_service` 为 `luma` 且无 `resource`（纯溶解），或 `mlt_service` 为 `mix`
- **可行性**：✅ 高可行
- **示例 instruction**："Add a 1-second dissolve transition between the two clips on V1"

### 6.2 添加擦除转场（Wipe）
- **操作**：Add Transition → Wipe
- **验证策略**：检查 `<transition>` 的 `mlt_service` 为 `luma`，且 `resource` 指向擦除图案文件
- **可行性**：✅ 高可行
- **示例 instruction**："Add a wipe transition (left to right) between the two clips on V1"

### 6.3 添加合成模式（Composite）
- **操作**：在叠加轨道的片段上右键 → Add Composition → Composite
- **验证策略**：检查 `<transition>` 的 `mlt_service` 为 `composite` 或 `qtblend`
- **可行性**：✅ 高可行

### 6.4 添加画中画效果（PIP / Affine Transform）
- **操作**：Compositions → Affine / Transform → 设置位置和大小参数
- **验证策略**：检查 `<transition>` 的 `mlt_service` 为 `affine` 或 `qtblend`，检查 `rect` 参数中的位置和尺寸
- **可行性**：✅ 高可行（rect 参数 "x y w h" 可精确验证）
- **示例 instruction**："Create a picture-in-picture effect: place the V2 clip in the bottom-right corner at 25% size"

### 6.5 设置转场时长
- **操作**：拖拽转场边缘调整时长
- **验证策略**：检查 `<transition>` 的 `in` 和 `out` 属性，计算帧数差
- **可行性**：✅ 高可行

---

## 类别 7：渲染/导出（Rendering）

### 7.1 渲染为 MP4 (H.264)
- **操作**：Project → Render → 选择 MP4 Profile → 设置输出路径 → Render
- **验证策略**：使用 `ffprobe` 验证输出文件的 codec_name 为 `h264`，container 为 `mp4`
- **可行性**：✅ 高可行
- **示例 instruction**："Render the project as an MP4 file (H.264) to /home/user/Desktop/output.mp4"

### 7.2 渲染为 WebM (VP9)
- **操作**：Project → Render → 选择 WebM Profile
- **验证策略**：`ffprobe` 验证 codec_name 为 `vp9`，container 为 `webm`
- **可行性**：✅ 高可行
- **示例 instruction**："Render the project as a WebM file (VP9) to /home/user/Desktop/output.webm"

### 7.3 渲染为指定分辨率
- **操作**：Render → 设置 Resolution
- **验证策略**：`ffprobe` 验证输出文件的 width 和 height
- **可行性**：✅ 高可行
- **示例 instruction**："Render the project at 1280x720 (720p) resolution to /home/user/Desktop/output_720p.mp4"

### 7.4 仅渲染选定区域（Zone Rendering）
- **操作**：设置 Zone In/Out → Render → 勾选 "Selected Zone"
- **验证策略**：`ffprobe` 验证输出视频时长对应选定区域的长度
- **可行性**：✅ 高可行
- **示例 instruction**："Render only the zone from 5 seconds to 15 seconds as /home/user/Desktop/zone_output.mp4"

### 7.5 仅导出音频
- **操作**：Render → 选择 Audio Only Profile（如 WAV、MP3）
- **验证策略**：`ffprobe` 验证输出文件仅有音频流（`nb_streams=1`，codec_type=audio）
- **可行性**：✅ 高可行
- **示例 instruction**："Export the project audio only as /home/user/Desktop/output_audio.wav"

### 7.6 渲染为图片序列
- **操作**：Render → 选择 Image Sequence Profile
- **验证策略**：检查输出目录下的图片文件数量和格式
- **可行性**：⚠️ 中可行

### 7.7 渲染为 GIF
- **操作**：Render → 选择 GIF Profile（如果可用）；或使用自定义 FFmpeg 参数
- **验证策略**：检查输出文件扩展名和 ffprobe 的 codec_name
- **可行性**：⚠️ 中可行

---

## 类别 8：应用设置与偏好（Preferences / Settings）

### 8.1 修改默认项目 Profile
- **操作**：Settings → Configure Kdenlive → Project Defaults → Profile
- **验证策略**：读取 `~/.config/kdenliverc`，检查 `[project]` section 下的 `default_profile` 值
- **可行性**：✅ 高可行
- **示例 instruction**："Set the default project profile to HD 1080p 25fps in Kdenlive preferences"

### 8.2 修改自动保存间隔
- **操作**：Settings → Configure Kdenlive → Environment → Auto Save interval
- **验证策略**：读取 `~/.config/kdenliverc`，检查 `[unmanaged]` 下的 `KAutoSave` 值
- **可行性**：✅ 高可行
- **示例 instruction**："Change the auto-save interval to 5 minutes in Kdenlive preferences"

### 8.3 修改代理片段设置
- **操作**：Settings → Configure Kdenlive → Proxy Clips → Enable/Disable
- **验证策略**：读取 `~/.config/kdenliverc`，检查 proxy 相关配置项
- **可行性**：✅ 高可行
- **示例 instruction**："Enable proxy clips generation in Kdenlive preferences"

### 8.4 修改渲染线程数
- **操作**：Settings → Configure Kdenlive → Environment → Processing Threads
- **验证策略**：读取 `~/.config/kdenliverc`，检查 `encodethreads` 配置项
- **可行性**：✅ 高可行
- **示例 instruction**："Set the rendering thread count to 4 in Kdenlive preferences"

### 8.5 修改默认时间线轨道数
- **操作**：Settings → Configure Kdenlive → Timeline → Default number of tracks
- **验证策略**：读取配置文件中的 `videotracks` 和 `audiotracks` 值
- **可行性**：✅ 高可行
- **示例 instruction**："Set the default number of video tracks to 4 and audio tracks to 4"

### 8.6 修改界面主题/配色
- **操作**：Settings → Color Theme
- **验证策略**：读取 `~/.config/kdenliverc`，检查 theme 相关配置
- **可行性**：⚠️ 中可行

### 8.7 修改键盘快捷键
- **操作**：Settings → Configure Keyboard Shortcuts
- **验证策略**：读取 `~/.config/kdenlive/kdenliveui.rc` 或 `~/.local/share/kxmlgui5/kdenlive/kdenliveui.rc` 文件
- **可行性**：⚠️ 中可行

---

## 类别 9：字幕与标题（Subtitles & Titles）

### 9.1 添加字幕轨道
- **操作**：Project → Subtitles → Add Subtitle
- **验证策略**：检查项目文件中是否存在字幕相关节点，或检查是否生成了 `.srt` 文件
- **可行性**：⚠️ 中可行
- **示例 instruction**："Add a subtitle track to the project"

### 9.2 添加字幕条目
- **操作**：在字幕轨道上创建字幕，输入文字
- **验证策略**：解析项目文件中的字幕数据节点或导出的 `.srt` 文件
- **可行性**：⚠️ 中可行
- **示例 instruction**："Add a subtitle 'Welcome to my video' from 00:00:02 to 00:00:05"

### 9.3 导入 SRT 字幕文件
- **操作**：Project → Subtitles → Import Subtitle File
- **验证策略**：检查项目文件中是否包含导入的字幕数据
- **可行性**：⚠️ 中可行
- **示例 instruction**："Import the subtitle file /home/user/Desktop/subtitles.srt"

### 9.4 导出 SRT 字幕文件
- **操作**：Project → Subtitles → Export Subtitle File
- **验证策略**：检查导出的 `.srt` 文件是否存在且内容正确
- **可行性**：✅ 高可行
- **示例 instruction**："Export the subtitles as /home/user/Desktop/output_subtitles.srt"

---

## 类别 10：辅助工具操作

### 10.1 使用选择工具
- **操作**：按 `S` 键切换到选择工具
- **验证策略**：❌ 纯 UI 状态，无法通过文件验证
- **可行性**：❌ 低可行（仅改变 UI 状态，无文件可验证）

### 10.2 使用剃刀工具
- **操作**：按 `X` 键切换到剃刀工具，然后点击切割
- **验证策略**：通过切割结果（时间线片段分割）间接验证
- **可行性**：✅ 高可行（通过结果验证）

### 10.3 撤销/重做
- **操作**：`Ctrl+Z` / `Ctrl+Shift+Z`
- **验证策略**：❌ 无法可靠验证（状态依赖）
- **可行性**：❌ 低可行

### 10.4 缩放时间线
- **操作**：`Ctrl+滚轮` 或 `+/-` 键
- **验证策略**：❌ 纯 UI 状态
- **可行性**：❌ 低可行

---

## 原子功能可行性汇总表

| 类别 | 功能数量 | ✅ 高可行 | ⚠️ 中可行 | ❌ 低可行 |
|------|----------|-----------|-----------|-----------|
| 1. 项目管理 | 4 | 3 | 1 | 0 |
| 2. 素材管理 | 7 | 5 | 2 | 0 |
| 3. 时间线编辑 | 10 | 7 | 3 | 0 |
| 4. 视频效果 | 14 | 13 | 1 | 0 |
| 5. 音频效果 | 7 | 4 | 3 | 0 |
| 6. 转场效果 | 5 | 5 | 0 | 0 |
| 7. 渲染/导出 | 7 | 5 | 2 | 0 |
| 8. 应用设置 | 7 | 5 | 2 | 0 |
| 9. 字幕与标题 | 4 | 1 | 3 | 0 |
| 10. 辅助工具 | 4 | 1 | 0 | 3 |
| **总计** | **69** | **49** | **17** | **3** |

---

## 推荐优先实现的 L1 原子任务（Top 20）

基于 **评估可行性高 + 功能覆盖面广 + 操作独立性好** 的原则，推荐首批实现以下 20 个 L1 任务：

| 序号 | 类别 | 功能 | Evaluator 核心方法 |
|------|------|------|-------------------|
| 1 | 项目管理 | 创建新项目并设置分辨率/帧率 | `check_kdenlive_project_profile` |
| 2 | 项目管理 | 保存项目到指定路径 | `check_file_exists` |
| 3 | 素材管理 | 导入视频到素材库 | `check_kdenlive_producer_resource` |
| 4 | 素材管理 | 导入音频到素材库 | `check_kdenlive_producer_resource` |
| 5 | 素材管理 | 创建纯色片段 | `check_kdenlive_color_producer` |
| 6 | 素材管理 | 创建标题片段 | `check_kdenlive_title_text` |
| 7 | 时间线 | 将素材添加到时间线 | `check_kdenlive_timeline_entry` |
| 8 | 时间线 | 分割片段 | `check_kdenlive_clip_split` |
| 9 | 时间线 | 裁剪片段入点/出点 | `check_kdenlive_entry_in_out` |
| 10 | 时间线 | 添加/删除轨道 | `check_kdenlive_track_count` |
| 11 | 视频效果 | 调整亮度 | `check_kdenlive_filter_param` |
| 12 | 视频效果 | 调整播放速度 | `check_kdenlive_speed_effect` |
| 13 | 视频效果 | 水平翻转 | `check_kdenlive_filter_exists` |
| 14 | 视频效果 | 转为黑白/灰度 | `check_kdenlive_filter_exists` |
| 15 | 音频效果 | 调整音量 | `check_kdenlive_volume_level` |
| 16 | 音频效果 | 音频淡入 | `check_kdenlive_audio_fade` |
| 17 | 转场效果 | 添加溶解转场 | `check_kdenlive_transition` |
| 18 | 转场效果 | 画中画效果 | `check_kdenlive_pip_params` |
| 19 | 渲染 | 渲染为 MP4 (H.264) | `check_video_file_properties` |
| 20 | 设置 | 修改默认项目 Profile | `check_kdenlive_config_value` |
