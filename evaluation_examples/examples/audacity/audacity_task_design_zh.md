# Audacity 任务设计文档

## 0. Audacity 验证策略

### Audacity 路径

评测虚拟机中 Audacity 通过 dnf 安装，**二进制路径为 `/usr/bin/audacity`**。所有 task JSON 中的 `launch` 命令都必须使用此完整路径。

### 核心思路

Audacity 的验证通过两种互补方式实现：

1. **导出 WAV 文件分析**：使用 Python 标准库 `wave` + `struct` 对导出的 WAV 文件进行音频属性检查（时长、采样率、声道数、RMS 音量、淡入/淡出、静音段等）。
2. **`.aup3` SQLite 解析**：Audacity 3.x 的项目文件是 SQLite 数据库，包含 XML 格式的项目元数据。可解析轨道数量、增益、静音状态、标签等项目级信息。

**评估器架构**：所有评估函数接收通过 `vm_file` getter 从 VM 下载的文件路径，直接在本地进行分析判定。不需要在 VM 上运行额外脚本。

### 评估器通用模式

```python
def check_audio_xxx(file_path, rule) -> float:
    """
    参数：
        file_path: 从 VM 下载到本地的 WAV 或 .aup3 文件路径
        rule: 包含期望值的字典
    返回：
        1.0（通过）或 0.0（失败）
    """
    try:
        # ... 读取文件并验证
        return 1.0
    except:
        return 0.0
```

### 与 Blender 验证方式的对比

| 特性 | Audacity | Blender |
|------|----------|---------|
| 文件格式 | WAV（标准音频）/ .aup3（SQLite） | .blend（二进制） |
| 验证方式 | `vm_file` → 下载后本地分析 | `vm_command_line` → VM 上运行 Python 脚本 |
| 依赖库 | `wave`, `struct`, `sqlite3`, `xml.etree`（全部 stdlib） | `bpy`（Blender 内嵌 Python） |
| 额外脚本 | 不需要 | 需要上传 check_*.py 到 VM |

---

## 1. 可用资源

所有资源文件位于：`assets/audacity/`

总计：**27 个 WAV 文件 + 1 个 Python 工具脚本，约 30 MB**

### 1.1 音频文件（.wav）—— 27 个

通过 Python + NumPy + SciPy 生成。所有文件均为合成音频（非录制），采用 44100 Hz / 16-bit PCM / 单声道格式。

#### 1.1.1 基础测试文件

| 文件名 | 时长 | 大小 | 内容 | 用途 |
|--------|------|------|------|------|
| `sample.wav` | 8秒 | 706 KB | 440Hz 正弦波 | 通用测试，导入/导出 |
| `test.wav` | 5秒 | 441 KB | 440Hz 正弦波 | 基础操作 |

#### 1.1.2 语音类音频

| 文件名 | 时长 | 大小 | 内容 | 用途 |
|--------|------|------|------|------|
| `speech.wav` | 12秒 | 1.1 MB | 频率变化的模拟语音 | 语音操作测试，删除 + 淡出 |

#### 1.1.3 效果测试文件

| 文件名 | 时长 | 大小 | 内容 | 用途 |
|--------|------|------|------|------|
| `fade_test.wav` | 18秒 | 1.6 MB | 523Hz 正弦波 | 淡入/淡出效果 |
| `volume_test.wav` | 10秒 | 882 KB | 392Hz 正弦波 | 放大/音量/归一化 |
| `noisy_recording.wav` | 14秒 | 1.2 MB | 正弦波 + 15% 噪音 | 降噪工作流 |
| `eq_test.wav` | 20秒 | 1.8 MB | 多频率（100Hz、1kHz、5kHz） | 均衡器测试 |
| `clipping_test.wav` | 15秒 | 1.3 MB | 过驱正弦波 | 查找削波功能 |

#### 1.1.4 编辑测试文件

| 文件名 | 时长 | 大小 | 内容 | 用途 |
|--------|------|------|------|------|
| `edit_test.wav` | 12秒 | 1.1 MB | 440Hz 正弦波 | 剪切/粘贴/修剪操作 |
| `delete_test.wav` | 10秒 | 882 KB | 392Hz 正弦波 | 删除操作 |
| `duplicate_test.wav` | 8秒 | 706 KB | 494Hz 正弦波 | 复制/复制/插入 |
| `short_test.wav` | 3秒 | 265 KB | 短音频 | 追加静音、重复 |
| `long_test.wav` | 60秒 | 5.3 MB | 音频测试轨 | 复杂多步编辑 |
| `complex_sections.wav` | 20秒 | 1.8 MB | 分段音频 | 带标签的分段编辑 |

#### 1.1.5 多轨音频（用于混音）

| 文件名 | 时长 | 大小 | 内容 | 用途 |
|--------|------|------|------|------|
| `vocals.wav` | 30秒 | 2.6 MB | 旋律模式（440-587Hz） | 人声轨混音 |
| `drums.wav` | 30秒 | 2.6 MB | 打击乐低频模式 | 鼓轨混音 |
| `bass.wav` | 30秒 | 2.6 MB | 低频变化（80-100Hz） | 贝斯轨混音 |

#### 1.1.6 立体声音频

| 文件名 | 时长 | 大小 | 内容 | 用途 |
|--------|------|------|------|------|
| `stereo_test.wav` | 15秒 | 1.3 MB | 立体声音频 | 分离立体声、单声道混音 |

#### 1.1.7 高级与专用文件

| 文件名 | 时长 | 大小 | 内容 | 用途 |
|--------|------|------|------|------|
| `label_test.wav` | 32秒 | 2.8 MB | 440Hz 正弦波 | 标签轨管理 |
| `crossfade_test.wav` | 15秒 | 1.3 MB | 440Hz + 660Hz 合成 | 轨道交叉淡变 |
| `analysis_test.wav` | 15秒 | 1.3 MB | 5频率谐波序列 | 频谱分析 |
| `undo_test.wav` | 18秒 | 1.6 MB | 392Hz 正弦波 | 撤销/重做历史 |
| `mute_solo_test.wav` | 25秒 | 2.2 MB | 双频率模式 | 轨道静音/独奏 |
| `mix_test.wav` | 20秒 | 1.8 MB | 4频率和弦 | 轨道音量混音 |
| `silence_test.wav` | 10秒 | 882 KB | 静音测试音频 | 静音插入/生成 |
| `rhythmic_test.wav` | 12秒 | 1.1 MB | 节奏模式 | 节奏编辑任务 |

---

### 1.2 工具脚本 —— 1 个

| 脚本名 | 位置 | 描述 |
|--------|------|------|
| `audio_analysis.py` | `assets/audacity/projects/` | 使用 librosa/scipy 的音频分析工具，用于开发测试 |

---

## 2. 评估函数设计

文件：`desktop_env/evaluators/metrics/audacity.py`

使用 Python 标准库实现，无需第三方依赖（`wave`, `struct`, `sqlite3`, `xml.etree`）。

### 2.1 内部辅助函数

| 辅助函数 | 描述 |
|----------|------|
| `_read_wav_info(file_path)` | 读取 WAV 基本信息：声道数、采样率、帧数、时长、采样位宽 |
| `_read_wav_samples(file_path)` | 读取 WAV 样本为 [-1.0, 1.0] 浮点列表，支持 8/16/24/32-bit |
| `_rms_db(samples)` | 计算 RMS 分贝值 |
| `_get_mono_samples(file_path)` | 读取 WAV 并返回单声道样本 + 采样率 |
| `_extract_time_range(samples, sr, start, end)` | 提取指定时间范围内的样本 |
| `_open_aup3(file_path)` | 打开 .aup3 文件作为 SQLite 数据库 |
| `_get_aup3_project_xml(file_path)` | 从 .aup3 中提取项目 XML |
| `_parse_aup3_tracks(file_path)` | 解析 .aup3 轨道信息（音频轨/标签轨） |

### 2.2 WAV 文件原子评估器

| 函数名 | 描述 | result 类型 | expected 类型 | rule 参数 |
|--------|------|-------------|---------------|-----------|
| `check_audio_duration` | 验证音频时长 | `vm_file`（WAV） | `rule` | `{"expected_duration": float, "tolerance": float}` |
| `check_audio_sample_rate` | 验证采样率 | `vm_file`（WAV） | `rule` | `{"expected_sr": int}` |
| `check_audio_channels` | 验证声道数 | `vm_file`（WAV） | `rule` | `{"expected_channels": int}` |
| `check_audio_rms_level` | 验证 RMS 音量在范围内 | `vm_file`（WAV） | `rule` | `{"min_rms_db": float, "max_rms_db": float}` |
| `check_audio_fade_in` | 验证淡入效果（窗口 RMS 递增） | `vm_file`（WAV） | `rule` | `{"fade_duration": float, "num_windows": int}` |
| `check_audio_fade_out` | 验证淡出效果（窗口 RMS 递减） | `vm_file`（WAV） | `rule` | `{"fade_duration": float, "num_windows": int}` |
| `check_audio_silence_at` | 验证指定区域为静音 | `vm_file`（WAV） | `rule` | `{"start_time": float, "end_time": float, "max_rms_db": float}` |
| `check_audio_has_content_at` | 验证指定区域有音频内容 | `vm_file`（WAV） | `rule` | `{"start_time": float, "end_time": float, "min_rms_db": float}` |
| `check_audio_peak_amplitude` | 验证峰值振幅在范围内 | `vm_file`（WAV） | `rule` | `{"min_peak_db": float, "max_peak_db": float}` |
| `check_audio_file_valid` | 验证音频文件存在且可读 | `vm_file`（WAV） | `rule` | `{}` |

### 2.3 WAV 文件复合评估器

| 函数名 | 描述 | result 类型 | expected 类型 | rule 参数 |
|--------|------|-------------|---------------|-----------|
| `check_audio_properties` | 时长 + 采样率 + 声道数一起验证 | `vm_file`（WAV） | `rule` | `{"expected_duration": float, "tolerance": float, "expected_sr": int, "expected_channels": int}` |
| `check_audio_with_fades` | 时长 + 可选淡入/淡出 | `vm_file`（WAV） | `rule` | `{"expected_duration": float, "tolerance": float, "fade_in_duration": float, "fade_out_duration": float}` |

### 2.4 .aup3 项目文件评估器

| 函数名 | 描述 | result 类型 | expected 类型 | rule 参数 |
|--------|------|-------------|---------------|-----------|
| `check_aup3_track_count` | 验证项目中轨道数量 | `vm_file`（.aup3） | `rule` | `{"expected_track_count": int}` |
| `check_aup3_track_gain` | 验证轨道增益（dB） | `vm_file`（.aup3） | `rule` | `{"track_index": int, "expected_gain_db": float, "tolerance": float}` |
| `check_aup3_track_mute` | 验证轨道静音状态 | `vm_file`（.aup3） | `rule` | `{"track_index": int, "expected_mute": bool}` |
| `check_aup3_labels` | 验证标签位置和文本 | `vm_file`（.aup3） | `rule` | `{"expected_labels": [{"time": float, "text": str}], "time_tolerance": float}` |

---

## 3. 任务定义

### 3.1 第一级（L1）—— 基础操作（单步、可直接验证）—— 18 个

L1 任务为单步原子操作，每个任务只涉及一个核心 GUI 动作。所有任务统一使用以下模式：

- **启动命令**：`/usr/bin/audacity /home/user/Documents/<输入文件>.wav`
- **验证方式**：通过 `vm_file` getter 下载导出的 WAV 文件或 .aup3 项目文件
- **上传文件**：WAV 素材 → `/home/user/Documents/<输入文件>.wav`

---

#### 任务 L1-1：导入并导出 WAV

- **ID**：`a1b00001-0001-4000-8000-000000000001`
- **指令**：我只想把这段音频重新导出一份 WAV 备份。请在 Audacity 中打开 /home/user/Documents/sample.wav，把它导出为 /home/user/Documents/exports/sample_export.wav，并顺手把项目保存一下。
- **上传素材**：`sample.wav` → `/home/user/Documents/sample.wav`
- **评估函数**：`check_audio_properties`
- **result**：`vm_file` → `/home/user/Documents/exports/sample_export.wav`
- **expected**：`rule` → `{"expected_duration": 8.0, "tolerance": 0.5, "expected_sr": 44100, "expected_channels": 1}`
- **验证逻辑**：时长 ≈ 8s + 采样率 44100Hz + 单声道
- **需要新评估函数**：❌

---

#### 任务 L1-3：删除 2 秒片段

- **ID**：`a1b00003-0003-4000-8000-000000000003`
- **指令**：这段音频里 3.0 到 5.0 秒那一小段不要了。请在 Audacity 中打开 /home/user/Documents/delete_test.wav，删掉这 2 秒内容后，把结果导出到 /home/user/Documents/exports/deleted.wav，并保存项目。
- **上传素材**：`delete_test.wav` → `/home/user/Documents/delete_test.wav`
- **评估函数**：`check_audio_duration`
- **result**：`vm_file` → `/home/user/Documents/exports/deleted.wav`
- **expected**：`rule` → `{"expected_duration": 8.0, "tolerance": 0.5}`
- **验证逻辑**：原 10s - 删除 2s = 8s
- **需要新评估函数**：❌

---

#### 任务 L1-4：修剪到选区

- **ID**：`a1b00004-0004-4000-8000-000000000004`
- **指令**：我只想保留这段音频里 4.0 到 8.0 秒的部分。请在 Audacity 中打开 /home/user/Documents/edit_test.wav，修剪到这段选区后，导出为 /home/user/Documents/exports/trimmed.wav，并保存项目。
- **上传素材**：`edit_test.wav` → `/home/user/Documents/edit_test.wav`
- **评估函数**：`check_audio_duration`
- **result**：`vm_file` → `/home/user/Documents/exports/trimmed.wav`
- **expected**：`rule` → `{"expected_duration": 4.0, "tolerance": 0.5}`
- **验证逻辑**：保留 4-8s = 4s
- **需要新评估函数**：❌

---

#### 任务 L1-5：淡入（前 2 秒）

- **ID**：`a1b00005-0005-4000-8000-000000000005`
- **指令**：这段音频开头有点生硬，帮我顺一下。请在 Audacity 中打开 /home/user/Documents/fade_test.wav，对前 2 秒做淡入，然后导出为 /home/user/Documents/exports/fadein.wav，并保存项目。
- **上传素材**：`fade_test.wav` → `/home/user/Documents/fade_test.wav`
- **评估函数**：`check_audio_fade_in`
- **result**：`vm_file` → `/home/user/Documents/exports/fadein.wav`
- **expected**：`rule` → `{"fade_duration": 2.0, "num_windows": 5}`
- **验证逻辑**：前 2 秒内 RMS 窗口呈递增趋势
- **需要新评估函数**：❌

---

<!-- #### 任务 L1-6：淡出（后 2 秒）

- **ID**：`a1b00006-0006-4000-8000-000000000006`
- **指令**：在 Audacity 中打开 /home/user/Documents/fade_test.wav。选择最后 2 秒的音频，然后应用淡出效果（效果 > 淡出）。将结果导出为 WAV 到 /home/user/Documents/exports/fadeout.wav，然后保存项目。
- **上传素材**：`fade_test.wav` → `/home/user/Documents/fade_test.wav`
- **评估函数**：`check_audio_fade_out`
- **result**：`vm_file` → `/home/user/Documents/exports/fadeout.wav`
- **expected**：`rule` → `{"fade_duration": 2.0, "num_windows": 5}`
- **验证逻辑**：最后 2 秒内 RMS 窗口呈递减趋势
- **需要新评估函数**：❌ -->

---

#### 任务 L1-7：放大 +6dB

- **ID**：`a1b00007-0007-4000-8000-000000000007`
- **指令**：这段素材整体有点小声，帮我把音量拉高一点。请在 Audacity 中打开 /home/user/Documents/volume_test.wav，全选后放大 +6 dB，再导出到 /home/user/Documents/exports/amplified.wav，并保存项目。
- **上传素材**：`volume_test.wav` → `/home/user/Documents/volume_test.wav`
- **评估函数**：`check_audio_rms_level`
- **result**：`vm_file` → `/home/user/Documents/exports/amplified.wav`
- **expected**：`rule` → `{"min_rms_db": -25.0, "max_rms_db": -5.0}`
- **验证逻辑**：放大后 RMS 在指定范围内
- **需要新评估函数**：❌

---

#### 任务 L1-8：追加 3 秒静音

- **ID**：`a1b00008-0008-4000-8000-000000000008`
- **指令**：我想让这段音频结尾多留一点空白。请在 Audacity 中打开 /home/user/Documents/short_test.wav，在轨道末尾追加 3 秒静音，然后导出到 /home/user/Documents/exports/with_silence.wav，并保存项目。
- **上传素材**：`short_test.wav` → `/home/user/Documents/short_test.wav`
- **评估函数**：多指标 `["check_audio_duration", "check_audio_silence_at"]`，`"conj": "and"`
- **result**：2 个 `vm_file` → `/home/user/Documents/exports/with_silence.wav`
- **expected**：2 个 `rule`
  - `{"expected_duration": 6.0, "tolerance": 0.5}`
  - `{"start_time": 3.0, "end_time": 5.5, "max_rms_db": -40}`
- **验证逻辑**：时长 ≈ 6s（3s 原始 + 3s 静音）+ 后半段为静音
- **需要新评估函数**：❌

---

#### 任务 L1-9：重采样至 22050Hz

- **ID**：`a1b00009-0009-4000-8000-000000000009`
- **指令**：我需要一个 22050 Hz 的版本。请在 Audacity 中打开 /home/user/Documents/test.wav，把项目采样率改成 22050 Hz 后导出为 /home/user/Documents/exports/resampled.wav，并保存项目。
- **上传素材**：`test.wav` → `/home/user/Documents/test.wav`
- **评估函数**：`check_audio_sample_rate`
- **result**：`vm_file` → `/home/user/Documents/exports/resampled.wav`
- **expected**：`rule` → `{"expected_sr": 22050}`
- **验证逻辑**：采样率 == 22050
- **需要新评估函数**：❌

---

#### 任务 L1-10：分离立体声，导出左声道

- **ID**：`a1b00010-0010-4000-8000-000000000010`
- **指令**：这个立体声文件里我只想单独保留左声道。请在 Audacity 中打开 /home/user/Documents/stereo_test.wav，把立体声分离成两个单声道轨，删除右声道，再把左声道导出为单声道 WAV 到 /home/user/Documents/exports/left_channel.wav，并保存项目。
- **上传素材**：`stereo_test.wav` → `/home/user/Documents/stereo_test.wav`
- **评估函数**：多指标 `["check_audio_channels", "check_audio_duration"]`，`"conj": "and"`
- **result**：2 个 `vm_file` → `/home/user/Documents/exports/left_channel.wav`
- **expected**：2 个 `rule`
  - `{"expected_channels": 1}`
  - `{"expected_duration": 15.0, "tolerance": 1.0}`
- **验证逻辑**：单声道 + 时长保持 ≈ 15s
- **需要新评估函数**：❌

---

#### 任务 L1-26：归一化至 -1dB 峰值

- **ID**：`a1b00026-0026-4000-8000-000000000026`
- **指令**：我想先把这段音频的峰值规范一下。请在 Audacity 中打开 /home/user/Documents/volume_test.wav，全选后做归一化，并把峰值振幅设为 -1.0 dB；然后导出为 /home/user/Documents/exports/normalized.wav，并保存项目。
- **上传素材**：`volume_test.wav` → `/home/user/Documents/volume_test.wav`
- **评估函数**：`check_audio_peak_amplitude`
- **result**：`vm_file` → `/home/user/Documents/exports/normalized.wav`
- **expected**：`rule` → `{"min_peak_db": -2.0, "max_peak_db": 0.0}`
- **验证逻辑**：峰值 ≈ -1dB
- **需要新评估函数**：❌

---

#### 任务 L1-27：立体声混音为单声道

- **ID**：`a1b00027-0027-4000-8000-000000000027`
- **指令**：帮我把这段立体声音频转成单声道版本。请在 Audacity 中打开 /home/user/Documents/stereo_test.wav，执行立体声混音为单声道后，导出到 /home/user/Documents/exports/mono_mix.wav，并保存项目。
- **上传素材**：`stereo_test.wav` → `/home/user/Documents/stereo_test.wav`
- **评估函数**：`check_audio_properties`
- **result**：`vm_file` → `/home/user/Documents/exports/mono_mix.wav`
- **expected**：`rule` → `{"expected_duration": 15.0, "tolerance": 1.0, "expected_channels": 1}`
- **验证逻辑**：时长 ≈ 15s + 单声道
- **需要新评估函数**：❌

---

#### 任务 L1-28：重复音频以加倍时长

- **ID**：`a1b00028-0028-4000-8000-000000000028`
- **指令**：我想把这段短音频循环一遍，让总时长变成原来的两倍。请在 Audacity 中打开 /home/user/Documents/short_test.wav，全选后重复 1 次，再导出为 /home/user/Documents/exports/doubled.wav，并保存项目。
- **上传素材**：`short_test.wav` → `/home/user/Documents/short_test.wav`
- **评估函数**：`check_audio_duration`
- **result**：`vm_file` → `/home/user/Documents/exports/doubled.wav`
- **expected**：`rule` → `{"expected_duration": 6.0, "tolerance": 0.5}`
- **验证逻辑**：原 3s × 2 = 6s
- **需要新评估函数**：❌

---

#### 任务 L1-29：从零生成 5 秒音调

- **ID**：`a1b00029-0029-4000-8000-000000000029`
- **指令**：我需要一个从零生成的测试音。请打开 Audacity（不要打开任何现有文件），生成一个 5 秒、440 Hz、振幅 0.8 的正弦波音调，然后导出到 /home/user/Documents/exports/generated_tone.wav，并保存项目。
- **上传素材**：无（从空项目开始）
- **评估函数**：`check_audio_properties`
- **result**：`vm_file` → `/home/user/Documents/exports/generated_tone.wav`
- **expected**：`rule` → `{"expected_duration": 5.0, "tolerance": 0.5, "expected_sr": 44100, "expected_channels": 1}`
- **验证逻辑**：时长 ≈ 5s + 44100Hz + 单声道
- **需要新评估函数**：❌

---

#### 任务 L1-31：仅导出选区

- **ID**：`a1b00031-0031-4000-8000-000000000031`
- **指令**：这段长录音里我只要 10.0 到 20.0 秒这一段。请在 Audacity 中打开 /home/user/Documents/long_test.wav，只导出选区到 /home/user/Documents/exports/selection.wav，并保存项目。
- **上传素材**：`long_test.wav` → `/home/user/Documents/long_test.wav`
- **评估函数**：`check_audio_duration`
- **result**：`vm_file` → `/home/user/Documents/exports/selection.wav`
- **expected**：`rule` → `{"expected_duration": 10.0, "tolerance": 0.5}`
- **验证逻辑**：导出选区 10-20s = 10s
- **需要新评估函数**：❌

---

### L1 任务汇总

| # | 任务名称 | 素材文件 | 评估函数 | 新增？ |
|---|---------|---------|---------|--------|
| 1 | 导入并导出 WAV | `sample.wav` | `check_audio_properties` | ❌ |
| 3 | 删除 2 秒片段 | `delete_test.wav` | `check_audio_duration` | ❌ |
| 4 | 修剪到选区 | `edit_test.wav` | `check_audio_duration` | ❌ |
| 5 | 淡入（前 2 秒） | `fade_test.wav` | `check_audio_fade_in` | ❌ |
| 6 | 淡出（后 2 秒） | `fade_test.wav` | `check_audio_fade_out` | ❌ |
| 7 | 放大 +6dB | `volume_test.wav` | `check_audio_rms_level` | ❌ |
| 8 | 追加 3 秒静音 | `short_test.wav` | `check_audio_duration` + `check_audio_silence_at` | ❌ |
| 9 | 重采样至 22050Hz | `test.wav` | `check_audio_sample_rate` | ❌ |
| 10 | 分离立体声，导出左声道 | `stereo_test.wav` | `check_audio_channels` + `check_audio_duration` | ❌ |
| 26 | 归一化至 -1dB | `volume_test.wav` | `check_audio_peak_amplitude` | ❌ |
| 27 | 立体声混音为单声道 | `stereo_test.wav` | `check_audio_properties` | ❌ |
| 28 | 重复音频 | `short_test.wav` | `check_audio_duration` | ❌ |
| 29 | 生成音调 | （空项目） | `check_audio_properties` | ❌ |
| 31 | 导出选区 | `long_test.wav` | `check_audio_duration` | ❌ |

**L1 统计**：
- 总任务数：**18**
- 需要新评估函数：**0** 个
- 使用的 .wav 素材：8 个
- 评估方式：全部使用 `vm_file` getter + WAV 分析

#### L1 任务来源标注

> 标注原则：L1 以单个核心操作为主，优先映射到 Audacity 官方手册的具体功能页；若任务同时包含“打开/导出”等必要配套动作，则允许组合 2 个官方页面作为复合来源。

| 任务 | 来源类型 | 具体来源 | 标注理由 |
|---|---|---|---|
| L1-1 | 官方手册 | [Importing Audio](https://manual.audacityteam.org/man/importing_audio.html) + [File Export Dialog](https://manual.audacityteam.org/man/file_export_dialog.html) | 对应“打开现有音频并重新导出备份” |
| L1-3、L1-4、L1-31 | 官方教程 | [Tutorial - Editing an Existing File](https://manual.audacityteam.org/man/tutorial_editing_an_existing_file.html) | 覆盖删除片段、修剪到选区、导出局部选区等基础编辑 |
| L1-5、L1-6 | 官方手册 | [Fade and Crossfade](https://manual.audacityteam.org/man/fade_and_crossfade.html) | 对应淡入/淡出原子操作 |
| L1-7 | 官方手册 | [Amplify](https://manual.audacityteam.org/man/amplify.html) | 对应整体放大增益 |
| L1-8 | 官方手册 | [Silence](https://manual.audacityteam.org/man/silence.html) | 对应在轨道末尾追加静音 |
| L1-9 | 官方手册 | [Sample Rates](https://manual.audacityteam.org/man/sample_rates.html) | 对应项目采样率调整与导出采样率控制 |
| L1-10、L1-27 | 官方手册 | [Splitting and Joining Stereo Tracks](https://manual.audacityteam.org/man/splitting_and_joining_stereo_tracks.html) + [Audio Track Dropdown Menu](https://manual.audacityteam.org/man/audio_track_dropdown_menu.html) | 对应立体声拆分、保留单边声道、转单声道等轨道级操作 |
| L1-26 | 官方手册 | [Normalize](https://manual.audacityteam.org/man/normalize.html) | 对应峰值规范化到目标电平 |
| L1-28 | 官方手册 | [Repeat](https://manual.audacityteam.org/man/repeat.html) | 对应循环重复以延长时长 |
| L1-29 | 官方手册 | [Tone](https://manual.audacityteam.org/man/tone.html) | 对应从空项目生成测试音调 |

---

### 3.2 第二级（L2）—— 复合操作（多步复合操作）—— 19 个

L2 任务为多步复合操作，每个任务涉及 **2-4 个关联 GUI 操作**。多数任务使用多指标评估（`func` 为列表，`conj: "and"`）。

---

#### 任务 L2-11：删除 + 淡出

- **ID**：`a1b00011-0011-4000-8000-000000000011`
- **指令**：这段录音中间有一小段想删掉，结尾也想收得自然一点。请在 Audacity 中打开 /home/user/Documents/speech.wav，删除 5.0 到 7.0 秒的内容，再对处理后音频的最后 2 秒做淡出，导出到 /home/user/Documents/exports/edit_fade.wav，并保存项目。
- **上传素材**：`speech.wav` → `/home/user/Documents/speech.wav`
- **评估函数**：多指标 `["check_audio_duration", "check_audio_fade_out"]`，`"conj": "and"`
- **result**：2 个 `vm_file` → `/home/user/Documents/exports/edit_fade.wav`
- **expected**：2 个 `rule`
  - `{"expected_duration": 10.0, "tolerance": 0.5}`
  - `{"fade_duration": 2.0, "num_windows": 5}`
- **验证逻辑**：12s - 2s 删除 = 10s + 最后 2s 淡出
- **操作步骤数**：3（选择删除 → 选择末尾 → 淡出）

---

#### 任务 L2-12：放大 + 淡入 + 淡出

- **ID**：`a1b00012-0012-4000-8000-000000000012`
- **指令**：我想做一个更响一点、头尾也更顺的版本。请在 Audacity 中打开 /home/user/Documents/volume_test.wav，全选后放大 +6 dB，再对前 2 秒做淡入、最后 2 秒做淡出，导出为 /home/user/Documents/exports/amp_fades.wav，并保存项目。
- **上传素材**：`volume_test.wav` → `/home/user/Documents/volume_test.wav`
- **评估函数**：多指标 `["check_audio_rms_level", "check_audio_fade_in", "check_audio_fade_out"]`，`"conj": "and"`
- **result**：3 个 `vm_file` → `/home/user/Documents/exports/amp_fades.wav`
- **expected**：3 个 `rule`
  - `{"min_rms_db": -30.0, "max_rms_db": -5.0}`
  - `{"fade_duration": 2.0, "num_windows": 5}`
  - `{"fade_duration": 2.0, "num_windows": 5}`
- **验证逻辑**：RMS 增大 + 开头淡入 + 结尾淡出
- **操作步骤数**：4（全选放大 → 选开头淡入 → 选结尾淡出 → 导出）

---

#### 任务 L2-13：在中间插入静音

- **ID**：`a1b00013-0013-4000-8000-000000000013`
- **指令**：我想在这段音频中间留一小段空白。请在 Audacity 中打开 /home/user/Documents/duplicate_test.wav，把光标放到 4.0 秒处，插入 2 秒静音，然后导出到 /home/user/Documents/exports/mid_silence.wav，并保存项目。
- **上传素材**：`duplicate_test.wav` → `/home/user/Documents/duplicate_test.wav`
- **评估函数**：多指标 `["check_audio_duration", "check_audio_silence_at"]`，`"conj": "and"`
- **result**：2 个 `vm_file` → `/home/user/Documents/exports/mid_silence.wav`
- **expected**：2 个 `rule`
  - `{"expected_duration": 10.0, "tolerance": 0.5}`
  - `{"start_time": 4.0, "end_time": 5.5, "max_rms_db": -40}`
- **验证逻辑**：原 8s + 2s = 10s + 中间 4-6s 为静音
- **操作步骤数**：2（定位光标 → 生成静音）

---

#### 任务 L2-14：合并两个文件

- **ID**：`a1b00014-0014-4000-8000-000000000014`
- **指令**：我想把两段素材叠在一起听一下效果。请在 Audacity 中打开 /home/user/Documents/short_test.wav，再把 /home/user/Documents/test.wav 导入成第二条轨道，混音并渲染为单轨后导出到 /home/user/Documents/exports/joined.wav，并保存项目。
- **上传素材**：`short_test.wav`，`test.wav` → `/home/user/Documents/`
- **评估函数**：多指标 `["check_audio_duration", "check_audio_has_content_at"]`，`"conj": "and"`
- **result**：2 个 `vm_file` → `/home/user/Documents/exports/joined.wav`
- **expected**：2 个 `rule`
  - `{"expected_duration": 5.0, "tolerance": 1.0}`
  - `{"start_time": 1.0, "end_time": 4.0, "min_rms_db": -30}`
- **验证逻辑**：混合后时长 + 中间有内容
- **操作步骤数**：3（导入第二文件 → 混合渲染 → 导出）

---

#### 任务 L2-15：降噪 + 导出

- **ID**：`a1b00015-0015-4000-8000-000000000015`
- **指令**：这段录音底噪比较明显，先帮我做一个基础清理版。请在 Audacity 中打开 /home/user/Documents/noisy_recording.wav，先用 0.0 到 0.5 秒获取噪音特征，再对整段音频应用降噪，然后导出为 /home/user/Documents/exports/cleaned.wav，并保存项目。
- **上传素材**：`noisy_recording.wav` → `/home/user/Documents/noisy_recording.wav`
- **评估函数**：多指标 `["check_audio_duration", "check_audio_rms_level"]`，`"conj": "and"`
- **result**：2 个 `vm_file` → `/home/user/Documents/exports/cleaned.wav`
- **expected**：2 个 `rule`
  - `{"expected_duration": 14.0, "tolerance": 0.5}`
  - `{"min_rms_db": -50.0, "max_rms_db": -5.0}`
- **验证逻辑**：时长不变 + RMS 在合理范围
- **操作步骤数**：4（选噪音 → 获取配置 → 全选 → 降噪）

---

#### 任务 L2-16：创建 3 轨项目

- **ID**：`a1b00016-0016-4000-8000-000000000016`
- **指令**：我想先搭一个简单的三轨工程，后面再继续处理。请在 Audacity 中打开 /home/user/Documents/vocals.wav，再分别导入 /home/user/Documents/drums.wav 和 /home/user/Documents/bass.wav，最后把项目保存为 /home/user/Documents/multitrack.aup3。
- **上传素材**：`vocals.wav`，`drums.wav`，`bass.wav` → `/home/user/Documents/`
- **评估函数**：`check_aup3_track_count`
- **result**：`vm_file` → `/home/user/Documents/multitrack.aup3`
- **expected**：`rule` → `{"expected_track_count": 3}`
- **验证逻辑**：项目包含 3 个轨道
- **操作步骤数**：3（导入 drums → 导入 bass → 保存项目）

---

#### 任务 L2-17：添加标签

- **ID**：`a1b00017-0017-4000-8000-000000000017`
- **指令**：我想先把这段素材的结构标出来，方便后面继续编辑。请在 Audacity 中打开 /home/user/Documents/label_test.wav，添加标签轨，并在 0.0s、8.0s、16.0s、24.0s 分别标上 Intro、Verse、Chorus、Outro，最后保存为 /home/user/Documents/labeled.aup3。
- **上传素材**：`label_test.wav` → `/home/user/Documents/label_test.wav`
- **评估函数**：`check_aup3_labels`
- **result**：`vm_file` → `/home/user/Documents/labeled.aup3`
- **expected**：`rule` → `{"expected_labels": [{"time": 0.0, "text": "Intro"}, {"time": 8.0, "text": "Verse"}, {"time": 16.0, "text": "Chorus"}, {"time": 24.0, "text": "Outro"}], "time_tolerance": 1.0}`
- **验证逻辑**：4 个标签的时间和文本匹配
- **操作步骤数**：5（添加标签轨 → 添加 4 个标签）

---

#### 任务 L2-18：设置轨道音量

- **ID**：`a1b00018-0018-4000-8000-000000000018`
- **指令**：我想先做一个简单的双轨平衡版本。请在 Audacity 中打开 /home/user/Documents/vocals.wav，再导入 /home/user/Documents/drums.wav，把人声轨增益调到 -3 dB、鼓轨调到 -6 dB，然后保存为 /home/user/Documents/mixed.aup3。
- **上传素材**：`vocals.wav`，`drums.wav` → `/home/user/Documents/`
- **评估函数**：多指标 `["check_aup3_track_gain", "check_aup3_track_gain"]`，`"conj": "and"`
- **result**：2 个 `vm_file` → `/home/user/Documents/mixed.aup3`
- **expected**：2 个 `rule`
  - `{"track_index": 0, "expected_gain_db": -3.0, "tolerance": 2.0}`
  - `{"track_index": 1, "expected_gain_db": -6.0, "tolerance": 2.0}`
- **验证逻辑**：两个轨道的增益分别匹配
- **操作步骤数**：3（导入 drums → 设人声增益 → 设鼓轨增益）

---

#### 任务 L2-19：静音轨道

- **ID**：`a1b00019-0019-4000-8000-000000000019`
- **指令**：我想保留人声做参考，先把鼓轨静音。请在 Audacity 中打开 /home/user/Documents/vocals.wav，再导入 /home/user/Documents/drums.wav，把鼓轨设为静音后保存为 /home/user/Documents/muted.aup3。
- **上传素材**：`vocals.wav`，`drums.wav` → `/home/user/Documents/`
- **评估函数**：多指标 `["check_aup3_track_count", "check_aup3_track_mute"]`，`"conj": "and"`
- **result**：2 个 `vm_file` → `/home/user/Documents/muted.aup3`
- **expected**：2 个 `rule`
  - `{"expected_track_count": 2}`
  - `{"track_index": 1, "expected_mute": true}`
- **验证逻辑**：2 个轨道 + 鼓轨被静音
- **操作步骤数**：2（导入 → 静音）

---

#### 任务 L2-20：修剪 + 放大 + 淡出

- **ID**：`a1b00020-0020-4000-8000-000000000020`
- **指令**：我想先截出可用的部分，再把它提亮一点，结尾也顺一下。请在 Audacity 中打开 /home/user/Documents/edit_test.wav，保留 3.0 到 9.0 秒的片段，放大 +6 dB，再对最后 2 秒做淡出，最后导出为 /home/user/Documents/exports/trim_amp_fade.wav，并保存项目。
- **上传素材**：`edit_test.wav` → `/home/user/Documents/edit_test.wav`
- **评估函数**：多指标 `["check_audio_duration", "check_audio_fade_out", "check_audio_rms_level"]`，`"conj": "and"`
- **result**：3 个 `vm_file` → `/home/user/Documents/exports/trim_amp_fade.wav`
- **expected**：3 个 `rule`
  - `{"expected_duration": 6.0, "tolerance": 0.5}`
  - `{"fade_duration": 2.0, "num_windows": 5}`
  - `{"min_rms_db": -30.0, "max_rms_db": -3.0}`
- **验证逻辑**：6s + 淡出 + 增益提升
- **操作步骤数**：4（选择修剪 → 放大 → 选结尾 → 淡出）

---

#### 任务 L2-34：归一化 + 淡入 + 淡出

- **ID**：`a1b00034-0034-4000-8000-000000000034`
- **指令**：我想把这段音频先规范一下峰值，再顺一下头尾。请在 Audacity 中打开 /home/user/Documents/volume_test.wav，先归一化到峰值 -1.0 dB，再对前 2 秒做淡入、最后 2 秒做淡出，导出为 /home/user/Documents/exports/norm_fades.wav，并保存项目。
- **上传素材**：`volume_test.wav` → `/home/user/Documents/volume_test.wav`
- **评估函数**：多指标 `["check_audio_peak_amplitude", "check_audio_fade_in", "check_audio_fade_out"]`，`"conj": "and"`
- **result**：3 个 `vm_file` → `/home/user/Documents/exports/norm_fades.wav`
- **expected**：3 个 `rule`
  - `{"min_peak_db": -2.0, "max_peak_db": 0.0}`
  - `{"fade_duration": 2.0, "num_windows": 5}`
  - `{"fade_duration": 2.0, "num_windows": 5}`
- **操作步骤数**：4（归一化 → 选开头淡入 → 选结尾淡出 → 导出）

---

#### 任务 L2-35：删除两个独立片段

- **ID**：`a1b00035-0035-4000-8000-000000000035`
- **指令**：这段长录音里有两处多余内容需要删掉。请在 Audacity 中打开 /home/user/Documents/long_test.wav，先删除 10-15s，再按当前时间轴删除 25-30s 这一段，然后导出到 /home/user/Documents/exports/double_delete.wav，并保存项目。
- **上传素材**：`long_test.wav` → `/home/user/Documents/long_test.wav`
- **评估函数**：`check_audio_duration`
- **result**：`vm_file` → `/home/user/Documents/exports/double_delete.wav`
- **expected**：`rule` → `{"expected_duration": 50.0, "tolerance": 1.0}`
- **验证逻辑**：60s - 5s - 5s = 50s
- **操作步骤数**：3（删除第一段 → 删除第二段 → 导出）

---

#### 任务 L2-36：追加生成的音调

- **ID**：`a1b00036-0036-4000-8000-000000000036`
- **指令**：我想在这段音频末尾补一个短测试音。请在 Audacity 中打开 /home/user/Documents/test.wav，把光标放到末尾后生成一个 3 秒、440 Hz 的音调，然后导出为 /home/user/Documents/exports/with_tone.wav，并保存项目。
- **上传素材**：`test.wav` → `/home/user/Documents/test.wav`
- **评估函数**：多指标 `["check_audio_duration", "check_audio_has_content_at"]`，`"conj": "and"`
- **result**：2 个 `vm_file` → `/home/user/Documents/exports/with_tone.wav`
- **expected**：2 个 `rule`
  - `{"expected_duration": 8.0, "tolerance": 0.5}`
  - `{"start_time": 5.0, "end_time": 7.5, "min_rms_db": -30}`
- **验证逻辑**：5s + 3s = 8s + 后半有内容
- **操作步骤数**：3（定位末尾 → 生成音调 → 导出）

---

#### 任务 L2-37：双轨项目 + 增益设置

- **ID**：`a1b00037-0037-4000-8000-000000000037`
- **指令**：我想先搭一个双轨工程，把两条轨道的电平先定下来。请在 Audacity 中打开 /home/user/Documents/vocals.wav，再导入 /home/user/Documents/bass.wav，把人声轨调到 -2 dB、贝斯轨调到 -4 dB，最后保存为 /home/user/Documents/two_track.aup3。
- **上传素材**：`vocals.wav`，`bass.wav` → `/home/user/Documents/`
- **评估函数**：多指标 `["check_aup3_track_count", "check_aup3_track_gain", "check_aup3_track_gain"]`，`"conj": "and"`
- **result**：3 个 `vm_file` → `/home/user/Documents/two_track.aup3`
- **expected**：3 个 `rule`
  - `{"expected_track_count": 2}`
  - `{"track_index": 0, "expected_gain_db": -2.0, "tolerance": 2.0}`
  - `{"track_index": 1, "expected_gain_db": -4.0, "tolerance": 2.0}`
- **操作步骤数**：3（导入 → 设增益 × 2）

---

#### 任务 L2-38：修剪 + 重采样

- **ID**：`a1b00038-0038-4000-8000-000000000038`
- **指令**：我只想保留这段素材中间可用的部分，并顺便导出一个更低采样率的版本。请在 Audacity 中打开 /home/user/Documents/edit_test.wav，修剪到 2-8s，再把项目采样率改成 22050 Hz，导出到 /home/user/Documents/exports/trim_resample.wav，并保存项目。
- **上传素材**：`edit_test.wav` → `/home/user/Documents/edit_test.wav`
- **评估函数**：多指标 `["check_audio_duration", "check_audio_sample_rate"]`，`"conj": "and"`
- **result**：2 个 `vm_file` → `/home/user/Documents/exports/trim_resample.wav`
- **expected**：2 个 `rule`
  - `{"expected_duration": 6.0, "tolerance": 0.5}`
  - `{"expected_sr": 22050}`
- **操作步骤数**：3（选择修剪 → 改采样率 → 导出）

---

#### 任务 L2-39：静音轨道 + 添加标签

- **ID**：`a1b00039-0039-4000-8000-000000000039`
- **指令**：我想做一个带标记的工程版本，同时先把鼓轨静音。请在 Audacity 中打开 /home/user/Documents/drums.wav，再导入 bass.wav，把鼓轨静音后添加标签轨，并在 5.0s 和 15.0s 分别标上 Beat 和 Drop，最后保存为 /home/user/Documents/labeled_mix.aup3。
- **上传素材**：`drums.wav`，`bass.wav` → `/home/user/Documents/`
- **评估函数**：多指标 `["check_aup3_track_mute", "check_aup3_labels"]`，`"conj": "and"`
- **result**：2 个 `vm_file` → `/home/user/Documents/labeled_mix.aup3`
- **expected**：2 个 `rule`
  - `{"track_index": 0, "expected_mute": true}`
  - `{"expected_labels": [{"time": 5.0, "text": "Beat"}, {"time": 15.0, "text": "Drop"}], "time_tolerance": 1.0}`
- **操作步骤数**：4（导入 → 静音 → 添加标签轨 → 添加标签）

---

#### 任务 L2-40：分离立体声 + 放大左声道

- **ID**：`a1b00040-0040-4000-8000-000000000040`
- **指令**：这个立体声文件里我只想留左声道，而且还想让它更响一点。请在 Audacity 中打开 /home/user/Documents/stereo_test.wav，把立体声分离成单声道后，对左声道放大 +6 dB，只导出左声道到 /home/user/Documents/exports/left_loud.wav，并保存项目。
- **上传素材**：`stereo_test.wav` → `/home/user/Documents/stereo_test.wav`
- **评估函数**：多指标 `["check_audio_channels", "check_audio_rms_level"]`，`"conj": "and"`
- **result**：2 个 `vm_file` → `/home/user/Documents/exports/left_loud.wav`
- **expected**：2 个 `rule`
  - `{"expected_channels": 1}`
  - `{"min_rms_db": -25.0, "max_rms_db": -3.0}`
- **操作步骤数**：4（分离 → 删右声道 → 放大 → 导出）

---

#### 任务 L2-41：在开头插入静音 + 淡入

- **ID**：`a1b00041-0041-4000-8000-000000000041`
- **指令**：我想让这段音频开头先留一点空白，再慢慢进来。请在 Audacity 中打开 /home/user/Documents/sample.wav，在 0.0 秒处插入 2 秒静音，然后对前 3 秒做淡入，导出到 /home/user/Documents/exports/silence_fade.wav，并保存项目。
- **上传素材**：`sample.wav` → `/home/user/Documents/sample.wav`
- **评估函数**：多指标 `["check_audio_duration", "check_audio_silence_at", "check_audio_fade_in"]`，`"conj": "and"`
- **result**：3 个 `vm_file` → `/home/user/Documents/exports/silence_fade.wav`
- **expected**：3 个 `rule`
  - `{"expected_duration": 10.0, "tolerance": 0.5}`
  - `{"start_time": 0.0, "end_time": 1.5, "max_rms_db": -40}`
  - `{"fade_duration": 3.0, "num_windows": 5}`
- **操作步骤数**：3（插入静音 → 选 3s → 淡入）

---

#### 任务 L2-42：重复 + 淡出

- **ID**：`a1b00042-0042-4000-8000-000000000042`
- **指令**：我想把这段短音频多循环几遍，最后再平滑收尾。请在 Audacity 中打开 /home/user/Documents/short_test.wav，把音频重复 2 次，让总时长变成原来的三倍，再对最后 3 秒做淡出，导出到 /home/user/Documents/exports/repeat_fade.wav，并保存项目。
- **上传素材**：`short_test.wav` → `/home/user/Documents/short_test.wav`
- **评估函数**：多指标 `["check_audio_duration", "check_audio_fade_out"]`，`"conj": "and"`
- **result**：2 个 `vm_file` → `/home/user/Documents/exports/repeat_fade.wav`
- **expected**：2 个 `rule`
  - `{"expected_duration": 9.0, "tolerance": 0.5}`
  - `{"fade_duration": 3.0, "num_windows": 5}`
- **验证逻辑**：3s × 3 = 9s + 最后 3s 淡出
- **操作步骤数**：3（全选 → 重复 → 选末尾淡出）

---

### L2 任务汇总

| # | 任务名称 | 素材文件 | 评估函数 | 步骤数 |
|---|---------|---------|---------|--------|
| 11 | 删除 + 淡出 | `speech.wav` | 时长 + 淡出 | 3 |
| 12 | 放大 + 淡入 + 淡出 | `volume_test.wav` | RMS + 淡入 + 淡出 | 4 |
| 13 | 在中间插入静音 | `duplicate_test.wav` | 时长 + 静音区域 | 2 |
| 14 | 合并两个文件 | `short_test.wav`，`test.wav` | 时长 + 有内容区域 | 3 |
| 15 | 降噪 + 导出 | `noisy_recording.wav` | 时长 + RMS | 4 |
| 16 | 创建 3 轨项目 | `vocals.wav`，`drums.wav`，`bass.wav` | 轨道数量 | 3 |
| 17 | 添加标签 | `label_test.wav` | 标签内容 | 5 |
| 18 | 设置轨道音量 | `vocals.wav`，`drums.wav` | 轨道增益 × 2 | 3 |
| 19 | 静音轨道 | `vocals.wav`，`drums.wav` | 轨道数量 + 静音状态 | 2 |
| 20 | 修剪 + 放大 + 淡出 | `edit_test.wav` | 时长 + 淡出 + RMS | 4 |
| 34 | 归一化 + 淡入 + 淡出 | `volume_test.wav` | 峰值 + 淡入 + 淡出 | 4 |
| 35 | 删除两个片段 | `long_test.wav` | 时长 | 3 |
| 36 | 追加生成的音调 | `test.wav` | 时长 + 有内容区域 | 3 |
| 37 | 双轨 + 增益 | `vocals.wav`，`bass.wav` | 轨道数量 + 增益 × 2 | 3 |
| 38 | 修剪 + 重采样 | `edit_test.wav` | 时长 + 采样率 | 3 |
| 39 | 静音 + 标签 | `drums.wav`，`bass.wav` | 静音状态 + 标签 | 4 |
| 40 | 分离立体声 + 放大 | `stereo_test.wav` | 声道数 + RMS | 4 |
| 41 | 插入静音 + 淡入 | `sample.wav` | 时长 + 静音区域 + 淡入 | 3 |
| 42 | 重复 + 淡出 | `short_test.wav` | 时长 + 淡出 | 3 |

**L2 统计**：
- 总任务数：**19**
- 需要新评估函数：**0** 个
- 平均操作步骤：**3-4** 步/任务
- 使用 WAV 分析：12 个
- 使用 .aup3 分析：5 个
- 混合使用：2 个

#### L2 任务来源标注

> 标注原则：L2 任务包含 2-4 个关联操作，优先映射到 Audacity 官方教程页；若一个任务跨越多个官方页面且缺乏单一稳定教程承载，则将其标注为“现实场景构造来源”，强调其来自常见编辑/混音/整理工作流的组合抽象。

| 任务 | 来源类型 | 具体来源 | 标注理由 |
|---|---|---|---|
| L2-11、L2-20、L2-35、L2-38 | 官方教程 | [Tutorial - Editing an Existing File](https://manual.audacityteam.org/man/tutorial_editing_an_existing_file.html) | 对应多步波形编辑：删除、修剪、局部保留、再次导出 |
| L2-12、L2-34、L2-41、L2-42 | 官方手册组合 | [Amplify](https://manual.audacityteam.org/man/amplify.html) / [Normalize](https://manual.audacityteam.org/man/normalize.html) / [Fade and Crossfade](https://manual.audacityteam.org/man/fade_and_crossfade.html) / [Silence](https://manual.audacityteam.org/man/silence.html) / [Repeat](https://manual.audacityteam.org/man/repeat.html) | 这些任务是多个基础效果操作的典型串联 |
| L2-13 | 官方手册 | [Silence](https://manual.audacityteam.org/man/silence.html) | 对应插入中段静音的编辑需求 |
| L2-14 | 官方教程 | [Tutorial - Mixing a Narration with Background Music](https://manual.audacityteam.org/man/tutorial_mixing_a_narration_with_background_music.html) | 虽非完全同模板，但核心是导入第二轨并混合渲染 |
| L2-15 | 官方手册 | [Noise Reduction](https://manual.audacityteam.org/man/noise_reduction.html) | 对应“获取噪声样本 → 应用整段降噪” |
| L2-16、L2-18、L2-19、L2-37、L2-39 | 现实场景构造来源 | 多轨工程整理场景：播客/采访粗混、配乐草稿、素材分轨检查 | 这些任务涉及导轨、调增益、静音、标签等工程管理动作，难以稳定对应到单一官方教程 |
| L2-17 | 官方手册 | [Label Tracks](https://manual.audacityteam.org/man/label_tracks.html) | 对应标签轨创建与结构标注 |
| L2-36 | 官方手册 | [Tone](https://manual.audacityteam.org/man/tone.html) | 对应在现有音频末尾追加生成测试音 |
| L2-40 | 官方手册组合 | [Splitting and Joining Stereo Tracks](https://manual.audacityteam.org/man/splitting_and_joining_stereo_tracks.html) + [Amplify](https://manual.audacityteam.org/man/amplify.html) | 对应拆分立体声后单独处理左声道 |

---

### 3.3 第三级（L3）—— 高级工作流（复杂多步工作流）—— 13 个

L3 任务为复杂多步工作流，每个任务涉及 **5 个以上 GUI 操作**，需要综合运用多种功能。多数任务同时使用 WAV 和 .aup3 两种验证方式。

---

#### 任务 L3-21：多轨混音

- **ID**：`a1b00021-0021-4000-8000-000000000021`
- **指令**：我想先做一个简单的单声道混音版本发给同事预听。请在 Audacity 中打开 /home/user/Documents/vocals.wav，再把 drums.wav 和 bass.wav 导入进来，最后混成单声道并导出到 /home/user/Documents/exports/mixdown.wav，工程也保存一下。
- **上传素材**：`vocals.wav`，`drums.wav`，`bass.wav` → `/home/user/Documents/`
- **评估函数**：多指标 `["check_audio_duration", "check_audio_channels"]`，`"conj": "and"`
- **result**：2 个 `vm_file` → `/home/user/Documents/exports/mixdown.wav`
- **expected**：2 个 `rule`
  - `{"expected_duration": 30.0, "tolerance": 1.0}`
  - `{"expected_channels": 1}`
- **操作步骤数**：5+

---

#### 任务 L3-22：多轨 + 标签 + 增益

- **ID**：`a1b00022-0022-4000-8000-000000000022`
- **指令**：我在整理一个后面还要继续改的多轨工程。请打开 /home/user/Documents/vocals.wav，再导入 drums.wav 和 bass.wav，把三条轨道的增益分别调到人声 -2 dB、鼓 -4 dB、贝斯 -3 dB；然后加一个标签轨，在 0.0s、10.0s、20.0s 分别标上 'Intro'、'Main'、'End'，最后保存为 /home/user/Documents/full_project.aup3。
- **上传素材**：`vocals.wav`，`drums.wav`，`bass.wav` → `/home/user/Documents/`
- **评估函数**：多指标 `["check_aup3_track_count", "check_aup3_labels", "check_aup3_track_gain", "check_aup3_track_gain", "check_aup3_track_gain"]`，`"conj": "and"`
- **result**：5 个 `vm_file` → `/home/user/Documents/full_project.aup3`
- **expected**：5 个 `rule`
  - `{"expected_track_count": 4}`
  - `{"expected_labels": [{"time": 0.0, "text": "Intro"}, {"time": 10.0, "text": "Main"}, {"time": 20.0, "text": "End"}], "time_tolerance": 1.0}`
  - `{"track_index": 0, "expected_gain_db": -2.0, "tolerance": 2.0}`
  - `{"track_index": 1, "expected_gain_db": -4.0, "tolerance": 2.0}`
  - `{"track_index": 2, "expected_gain_db": -3.0, "tolerance": 2.0}`
- **操作步骤数**：8（导入 × 2 → 增益 × 3 → 标签轨 → 标签 × 3 → 保存）

---

#### 任务 L3-23：复杂编辑：删除 + 静音 + 淡入淡出

- **ID**：`a1b00023-0023-4000-8000-000000000023`
- **指令**：这段长录音里有一段不要了，我还想在中间留一小段空白，头尾也顺一下。请打开 /home/user/Documents/long_test.wav，删掉 40-50s，在 20s 位置插入 5s 静音，再给开头 3s 做淡入、结尾 3s 做淡出，最后导出为 /home/user/Documents/exports/complex_edit.wav，并保存项目。
- **上传素材**：`long_test.wav` → `/home/user/Documents/long_test.wav`
- **评估函数**：多指标 `["check_audio_duration", "check_audio_silence_at", "check_audio_fade_in", "check_audio_fade_out"]`，`"conj": "and"`
- **result**：4 个 `vm_file` → `/home/user/Documents/exports/complex_edit.wav`
- **expected**：4 个 `rule`
  - `{"expected_duration": 55.0, "tolerance": 1.5}`
  - `{"start_time": 20.0, "end_time": 24.0, "max_rms_db": -40}`
  - `{"fade_duration": 3.0, "num_windows": 5}`
  - `{"fade_duration": 3.0, "num_windows": 5}`
- **操作步骤数**：6+

---

#### 任务 L3-24：降噪 + 放大 + 淡入淡出

- **ID**：`a1b00024-0024-4000-8000-000000000024`
- **指令**：这段录音底噪有点重，帮我清理一下，再把整体音量拉起来一点，头尾别太生硬。请打开 /home/user/Documents/noisy_recording.wav，用 0-0.5s 这段做噪音样本完成降噪，然后放大 +6 dB，再给前 2s 做淡入、最后 2s 做淡出，导出到 /home/user/Documents/exports/clean_loud.wav，并保存项目。
- **上传素材**：`noisy_recording.wav` → `/home/user/Documents/noisy_recording.wav`
- **评估函数**：多指标 `["check_audio_duration", "check_audio_fade_in", "check_audio_fade_out", "check_audio_rms_level"]`，`"conj": "and"`
- **result**：4 个 `vm_file` → `/home/user/Documents/exports/clean_loud.wav`
- **expected**：4 个 `rule`
  - `{"expected_duration": 14.0, "tolerance": 0.5}`
  - `{"fade_duration": 2.0, "num_windows": 5}`
  - `{"fade_duration": 2.0, "num_windows": 5}`
  - `{"min_rms_db": -30.0, "max_rms_db": -3.0}`
- **操作步骤数**：7+

---

#### 任务 L3-25：多段编辑 + 标签

- **ID**：`a1b00025-0025-4000-8000-000000000025`
- **指令**：我在整理这段素材的结构，想先删掉中间一小段，再把几个位置标出来方便后续继续剪。请打开 /home/user/Documents/complex_sections.wav，删除 15-18s，添加标签轨后在 0.0s、7.0s、14.0s 分别标上 'Part1'、'Gap'、'End'，然后导出一份 WAV，并把项目另存为 .aup3。
- **上传素材**：`complex_sections.wav` → `/home/user/Documents/complex_sections.wav`
- **评估函数**：多指标 `["check_audio_duration", "check_aup3_labels"]`，`"conj": "and"`
- **result**：2 个 getter（1 个 `vm_file` WAV + 1 个 `vm_file` .aup3）
- **expected**：2 个 `rule`
  - `{"expected_duration": 17.0, "tolerance": 1.0}`
  - `{"expected_labels": [{"time": 0.0, "text": "Part1"}, {"time": 7.0, "text": "Gap"}, {"time": 14.0, "text": "End"}], "time_tolerance": 2.0}`
- **操作步骤数**：6+

---

#### 任务 L3-43：3 轨 + 增益 + 静音 + 标签

- **ID**：`a1b00043-0043-4000-8000-000000000043`
- **指令**：我想做一个还要继续调整的三轨工程版本。请打开 vocals.wav，再导入 drums.wav 和 bass.wav，把人声保持在 0 dB、鼓调到 -4 dB、贝斯调到 -2 dB，同时把鼓轨静音；然后加上 0.0s 的 'Start' 和 15.0s 的 'Middle' 两个标签，最后保存为 production.aup3。
- **上传素材**：`vocals.wav`，`drums.wav`，`bass.wav` → `/home/user/Documents/`
- **评估函数**：多指标 `["check_aup3_track_count", "check_aup3_track_mute", "check_aup3_labels", "check_aup3_track_gain", "check_aup3_track_gain"]`，`"conj": "and"`
- **result**：5 个 `vm_file` → `/home/user/Documents/production.aup3`
- **expected**：5 个 `rule`
  - `{"expected_track_count": 4}`
  - `{"track_index": 1, "expected_mute": true}`
  - `{"expected_labels": [{"time": 0.0, "text": "Start"}, {"time": 15.0, "text": "Middle"}], "time_tolerance": 1.0}`
  - `{"track_index": 1, "expected_gain_db": -4.0, "tolerance": 2.0}`
  - `{"track_index": 2, "expected_gain_db": -2.0, "tolerance": 2.0}`
- **操作步骤数**：8+

---

#### 任务 L3-44：修剪 + 删除 + 静音 + 淡入

- **ID**：`a1b00044-0044-4000-8000-000000000044`
- **指令**：我想先把这段长音频收成一个更短的版本，再顺手处理掉中间的空档。请打开 long_test.wav，先修剪到前 30s，再删除 10-15s 的内容，并在 10s 的位置插入 3s 静音；开头 3s 做一个淡入，最后导出为 WAV 并保存项目。
- **上传素材**：`long_test.wav` → `/home/user/Documents/long_test.wav`
- **评估函数**：多指标 `["check_audio_duration", "check_audio_silence_at", "check_audio_fade_in"]`，`"conj": "and"`
- **result**：3 个 `vm_file`
- **expected**：3 个 `rule`
- **操作步骤数**：6+

---

#### 任务 L3-45：多轨混音 + 淡入淡出

- **ID**：`a1b00045-0045-4000-8000-000000000045`
- **指令**：我想做一个简单的混音预览版，人声开头和结尾需要更顺一点。请打开 vocals.wav，再导入 drums.wav，对人声轨前 3s 做淡入、后 3s 做淡出，然后混成单声道 WAV 导出，并把项目保存好。
- **上传素材**：`vocals.wav`，`drums.wav` → `/home/user/Documents/`
- **评估函数**：多指标 `["check_audio_channels", "check_audio_duration", "check_audio_fade_in", "check_audio_fade_out"]`，`"conj": "and"`
- **result**：4 个 `vm_file`
- **expected**：4 个 `rule`
- **操作步骤数**：7+

---

#### 任务 L3-46：分段编辑 + 标签 + 双格式保存

- **ID**：`a1b00046-0046-4000-8000-000000000046`
- **指令**：我想先把这段素材裁干净，再做好标记，顺便留一个后面还能继续改的工程文件。请打开 complex_sections.wav，删除 0-5s，再删除另一段不需要的内容，补上需要的标签，最后同时导出 WAV 并保存 .aup3 项目。
- **上传素材**：`complex_sections.wav` → `/home/user/Documents/complex_sections.wav`
- **评估函数**：多指标 `["check_audio_duration", "check_aup3_labels", "check_aup3_track_count"]`，`"conj": "and"`
- **result**：3 个 getter（WAV + .aup3）
- **expected**：3 个 `rule`
- **操作步骤数**：7+

---

#### 任务 L3-47：归一化 + 修剪 + 重采样 + 淡出

- **ID**：`a1b00047-0047-4000-8000-000000000047`
- **指令**：这段音频我想顺手做一次基础整理：先统一音量，再截出需要的部分，最后输出一个更低采样率的版本。请打开 edit_test.wav，先归一化，再修剪到 2-8s，把采样率改成 22050 Hz，并对最后 2s 做淡出，最后导出 WAV 并保存项目。
- **上传素材**：`edit_test.wav` → `/home/user/Documents/edit_test.wav`
- **评估函数**：多指标 `["check_audio_duration", "check_audio_sample_rate", "check_audio_fade_out"]`，`"conj": "and"`
- **result**：3 个 `vm_file`
- **expected**：3 个 `rule`
- **操作步骤数**：5+

---

#### 任务 L3-48：4 轨项目 + 增益 + 标签

- **ID**：`a1b00048-0048-4000-8000-000000000048`
- **指令**：我想搭一个四轨工程，后面还要继续往里加东西。请打开 vocals.wav，再导入 drums.wav、bass.wav，并额外生成一个音调轨；把各轨增益调到任务要求的状态，补上需要的标签，最后把工程保存成 .aup3。
- **上传素材**：`vocals.wav`，`drums.wav`，`bass.wav` + 生成 → `/home/user/Documents/`
- **评估函数**：多指标 `["check_aup3_track_count", "check_aup3_labels", "check_aup3_track_gain", "check_aup3_track_gain"]`，`"conj": "and"`
- **result**：4 个 `vm_file`
- **expected**：4 个 `rule`
- **操作步骤数**：10+

---

#### 任务 L3-49：多轨 + 静音 + 淡入淡出 + 单声道

- **ID**：`a1b00049-0049-4000-8000-000000000049`
- **指令**：我想把这两个轨道整理成一个更适合预听的单声道版本，中间要留一点空白，头尾也处理顺一点。请打开 vocals.wav，再导入 drums.wav，按要求插入静音并应用淡入淡出，最后混成单声道、导出 WAV，并保存项目。
- **上传素材**：`vocals.wav`，`drums.wav` → `/home/user/Documents/`
- **评估函数**：多指标 `["check_audio_channels", "check_audio_duration", "check_audio_fade_in", "check_audio_fade_out"]`，`"conj": "and"`
- **result**：4 个 `vm_file`
- **expected**：4 个 `rule`
- **操作步骤数**：8+

---

#### 任务 L3-50：扩展编辑 + 淡入淡出 + 标签 + 双格式保存

- **ID**：`a1b00050-0050-4000-8000-000000000050`
- **指令**：我想把这段长音频整理成一个既能直接交付、又方便后续返工的版本。请打开 long_test.wav，删掉两段不需要的内容，在末尾补 5s 静音，再给开头 3s 做淡入、结尾 3s 做淡出，并添加 'Begin'、'Gap'、'Silence' 这几个标签；最后导出 WAV，同时把项目保存成 .aup3。
- **上传素材**：`long_test.wav` → `/home/user/Documents/long_test.wav`
- **评估函数**：多指标 `["check_audio_duration", "check_audio_fade_in", "check_audio_fade_out", "check_aup3_labels"]`，`"conj": "and"`
- **result**：4 个 getter（3 个 WAV + 1 个 .aup3）
- **expected**：4 个 `rule`
  - `{"expected_duration": 50.0, "tolerance": 1.5}`
  - `{"fade_duration": 3.0, "num_windows": 5}`
  - `{"fade_duration": 3.0, "num_windows": 5}`
  - `{"expected_labels": [{"time": 0.0, "text": "Begin"}, {"time": 15.0, "text": "Gap"}, {"time": 45.0, "text": "Silence"}], "time_tolerance": 2.0}`
- **操作步骤数**：10+

---

### L3 任务汇总

| # | 任务名称 | 素材文件 | 评估指标数 | 步骤数 | 验证格式 |
|---|---------|---------|-----------|--------|----------|
| 21 | 多轨混音 | vocals + drums + bass | 2 | 5+ | WAV |
| 22 | 多轨 + 标签 + 增益 | vocals + drums + bass | 5 | 8+ | .aup3 |
| 23 | 删除 + 静音 + 淡入淡出 | long_test | 4 | 6+ | WAV |
| 24 | 降噪 + 放大 + 淡入淡出 | noisy_recording | 4 | 7+ | WAV |
| 25 | 分段编辑 + 标签 | complex_sections | 2 | 6+ | WAV + .aup3 |
| 43 | 3 轨 + 增益 + 静音 + 标签 | vocals + drums + bass | 5 | 8+ | .aup3 |
| 44 | 修剪 + 删除 + 静音 + 淡入 | long_test | 3 | 6+ | WAV |
| 45 | 多轨混音 + 淡入淡出 | vocals + drums | 4 | 7+ | WAV |
| 46 | 分段编辑 + 标签 + 双格式保存 | complex_sections | 3 | 7+ | WAV + .aup3 |
| 47 | 归一化 + 修剪 + 重采样 + 淡出 | edit_test | 3 | 5+ | WAV |
| 48 | 4 轨 + 增益 + 标签 | vocals + drums + bass | 4 | 10+ | .aup3 |
| 49 | 多轨 + 淡入淡出 + 单声道 | vocals + drums | 4 | 8+ | WAV |
| 50 | 扩展编辑 + 淡入淡出 + 标签 | long_test | 4 | 10+ | WAV + .aup3 |

**L3 统计**：
- 总任务数：**13**
- 需要新评估函数：**0** 个
- 平均操作步骤：**7+** 步/任务
- 平均评估指标：**3.6** 个/任务
- 同时使用 WAV + .aup3 验证：**3** 个任务

#### L3 任务来源标注

> 标注原则：L3 任务以真实工作流重组为主。若能找到明显的官方教程原型，则标注为“官方教程启发”；若任务同时覆盖多轨组织、标签管理、返工留档、交付导出等多个真实环节，则标注为“现实场景构造来源”。这类来源更接近论文中“由专业人员根据实际工作内容组合设计”的叙述方式。

| 任务 | 来源类型 | 具体来源 | 标注理由 |
|---|---|---|---|
| L3-21、L3-45、L3-49 | 官方教程启发 + 现实场景构造 | [Tutorial - Mixing a Narration with Background Music](https://manual.audacityteam.org/man/tutorial_mixing_a_narration_with_background_music.html) + 预听混音/粗混交付场景 | 核心原型来自多轨导入与混音，但加入了单声道导出、淡入淡出、静音等更接近真实交付约束 |
| L3-22、L3-43、L3-48 | 现实场景构造来源 | 多轨制作工程整理：demo 工程搭建、轨道电平预设、标签定位、后续返工留档 | 多轨 + 增益 + 标签 + 项目保存通常是制作现场组合流程，不易对应到单篇手册页 |
| L3-23、L3-44、L3-46、L3-50 | 官方教程启发 + 现实场景构造 | [Tutorial - Editing an Existing File](https://manual.audacityteam.org/man/tutorial_editing_an_existing_file.html) + 长音频整理/交付前清稿场景 | 基于官方编辑操作原型扩展成多段删除、插入静音、标签、双格式保存等复杂清稿流程 |
| L3-24 | 官方手册组合 | [Noise Reduction](https://manual.audacityteam.org/man/noise_reduction.html) + [Amplify](https://manual.audacityteam.org/man/amplify.html) + [Fade and Crossfade](https://manual.audacityteam.org/man/fade_and_crossfade.html) | 对应录音清理链路：降噪、补偿音量、顺滑头尾 |
| L3-25 | 官方手册 + 现实场景构造 | [Label Tracks](https://manual.audacityteam.org/man/label_tracks.html) + 音频内容分段整理场景 | 标签与结构化整理能对齐手册，但“删段后再标结构”的整体工作流更像真实素材整理任务 |
| L3-47 | 官方手册组合 | [Normalize](https://manual.audacityteam.org/man/normalize.html) + [Sample Rates](https://manual.audacityteam.org/man/sample_rates.html) + [Fade and Crossfade](https://manual.audacityteam.org/man/fade_and_crossfade.html) | 对应交付前基础技术整理：统一峰值、裁片段、降采样、处理尾部 |

---

### 3.4 Interactive 任务（Audacity，多轮）—— 5 个（设计草案）

> 说明：以下是先行设计描述，用于后续落地为 `evaluation_examples/examples/interactive/interactive_audacity_*.json`。
> 触发方式覆盖：`step_count`（2 个）+ `agent_done`（2 个）+ `agent_asks`（1 个）。

#### IA-01：降噪需求中途变更（step_count）

- **场景类型**：`requirement_change`
- **素材**：`/home/user/Documents/noisy_recording.wav`
- **核心目标**：先做基础降噪；用户中途改需求，要求保留前段原声并重新导出。
- **Phase 设计**：
  - **Phase 1**："先把这段录音的底噪处理一下，直接导出一个 clean 版本。"
    - `trigger`: `{"type": "step_count", "value": 3}`
  - **Phase 2**："我改主意了，0s-2s 保留原样，不要降噪；2s 之后再做降噪，导出到 /home/user/Documents/exports/clean_partial.wav。"
    - `trigger`: `{"type": "agent_done"}`
- **预期考点**：中途需求切换、时间段选择、降噪仅作用于局部、最终导出路径正确。

#### IA-02：分段精修工作流（agent_done）

- **场景类型**：`multi_step_workflow`
- **素材**：`/home/user/Documents/edit_test.wav`
- **核心目标**：按用户分阶段要求完成修剪、响度处理与收尾。
- **Phase 设计**：
  - **Phase 1**："先把这段音频裁成 2s 到 8s，并导出一个临时版本让我确认。"
    - `trigger`: `{"type": "agent_done"}`
  - **Phase 2**："可以，接着把它归一化到接近 -1 dB 峰值，最后 2 秒做淡出，导出到 /home/user/Documents/exports/polished.wav。"
    - `trigger`: `{"type": "agent_done"}`
- **预期考点**：分阶段执行稳定性、已完成阶段记忆、导出结果持续覆盖。

#### IA-03：模糊需求需主动追问（agent_asks）

- **场景类型**：`ambiguous_instruction`
- **素材**：`/home/user/Documents/interview_raw.wav`（可由现有语音素材替代）
- **核心目标**：第一轮给出模糊目标，要求 Agent 主动澄清后再执行。
- **Phase 设计**：
  - **Phase 1**："这段采访听着不够专业，你帮我处理下。"
    - `trigger`: `{"type": "agent_asks"}`
  - **Phase 2**："我的意思是：先去噪，再把开头 0-1.5 秒删掉，最后 3 秒做淡出，导出到 /home/user/Documents/exports/interview_clean.wav。"
    - `trigger`: `{"type": "agent_done"}`
  - **Phase 3**："另外把工程也保存为 /home/user/Documents/interview_clean.aup3。"
    - `trigger`: `{"type": "agent_done"}`
- **预期考点**：`CALL_USER` 触发后的澄清能力、澄清后准确执行、双格式产物管理。

#### IA-04：混音过程中插入新约束（step_count）

- **场景类型**：`interruption`
- **素材**：`/home/user/Documents/vocals.wav` + `/home/user/Documents/drums.wav`
- **核心目标**：在 Agent 已开始混音后，用户追加“中间留空白+单声道”要求。
- **Phase 设计**：
  - **Phase 1**："打开 vocals.wav，导入 drums.wav，先做一个平衡一点的混音。"
    - `trigger`: `{"type": "step_count", "value": 2}`
  - **Phase 2**："补充一下，中间 15s 到 17s 需要插入静音，而且最后要混成单声道再导出 /home/user/Documents/exports/mix_with_gap.wav。"
    - `trigger`: `{"type": "agent_done"}`
- **预期考点**：中断后上下文衔接、多轨编辑 + 静音插入 + 声道转换复合验证。

#### IA-05：先交付再返工（agent_done）

- **场景类型**：`progressive_refinement`
- **素材**：`/home/user/Documents/long_test.wav`
- **核心目标**：先交付可用剪辑，再按新反馈进行返工并补标签。
- **Phase 设计**：
  - **Phase 1**："先把这段长录音裁成 10s 到 35s，导出一个可听版本。"
    - `trigger`: `{"type": "agent_done"}`
  - **Phase 2**："我刚听了，末尾太突兀。请给最后 3 秒做淡出，并在 12s 打上标签 'KeyPoint'，重新导出到 /home/user/Documents/exports/revised_clip.wav。"
    - `trigger`: `{"type": "agent_done"}`
- **预期考点**：返工场景下的二次编辑、标签与音频效果并行处理、同路径重导出一致性。

#### Interactive 触发分布汇总（本批 5 个）

| 任务ID | trigger 覆盖 |
|---|---|
| IA-01 | `step_count` + `agent_done` |
| IA-02 | `agent_done` |
| IA-03 | `agent_asks` + `agent_done` |
| IA-04 | `step_count` + `agent_done` |
| IA-05 | `agent_done` |

#### Interactive 任务来源映射（本批 5 个）

> 目标：为每个 Interactive 任务补齐“来源证据链”，用于论文中证明任务来自真实工作流并经过人工筛选。
> 说明：`source_ref` 可填写匿名化 URL、工单号、课程作业编号或访谈记录编号；`evidence_pack` 建议与任务 JSON 同步归档。

| 任务ID | 场景类型 | 真实工作来源（Primary Source） | 证据包（最小） | Task JSON `source` 建议写法 |
|---|---|---|---|---|
| IA-01 | `requirement_change` | 录音降噪中的中途需求变更（先全局降噪，后要求前段保留原样） | ① 原始需求摘录（匿名） ② 变更后指令摘录 ③ 导出文件验收记录 | `audacity_interactive;source_type=freelance_brief;source_ref=<id_or_url>;evidence=requirement_change` |
| IA-02 | `multi_step_workflow` | 分阶段交付的后期工作流（先预览裁剪，再定稿归一化与淡出） | ① v1/v2 两阶段说明 ② 每阶段确认语句 ③ 最终导出规范 | `audacity_interactive;source_type=internal_workflow;source_ref=<id_or_url>;evidence=staged_delivery` |
| IA-03 | `ambiguous_instruction` | 模糊需求需澄清的采访音频处理（“做专业点”→澄清后执行） | ① 模糊原始需求 ② 澄清问答记录 ③ 澄清后操作清单 | `audacity_interactive;source_type=forum_or_support;source_ref=<id_or_url>;evidence=clarification_required` |
| IA-04 | `interruption` | 混音中断追加约束（进行中新增“插入静音 + 单声道导出”） | ① 初始混音需求 ② 追加约束时间点 ③ 追加前后差异记录 | `audacity_interactive;source_type=production_change_request;source_ref=<id_or_url>;evidence=mid_process_interruption` |
| IA-05 | `progressive_refinement` | 先交付后返工的迭代场景（初版剪辑→反馈→补淡出与标签） | ① 首版交付说明 ② 返工反馈 ③ 二次导出与项目保存记录 | `audacity_interactive;source_type=iterative_delivery;source_ref=<id_or_url>;evidence=rework_loop` |

#### 来源证据落地字段（建议统一）

- **source_type**：`freelance_brief` / `internal_ticket` / `forum_or_support` / `course_assignment` / `production_change_request`
- **source_ref**：来源标识（匿名化 URL、工单号、访谈记录编号）
- **captured_at**：取证日期（`YYYY-MM-DD`）
- **anonymized_excerpt**：匿名化原文摘录（1~3 句）
- **mapping_note**：原始需求如何映射到 `phases` 与 `trigger`
- **reviewers**：双人审核与仲裁记录（`reviewer_a/reviewer_b/adjudicator`）

---

## 4. 评估函数汇总

文件：`desktop_env/evaluators/metrics/audacity.py`

| # | 函数名 | 类别 | 描述 | 复杂度 |
|---|--------|------|------|--------|
| 1 | `check_audio_duration` | WAV 原子 | 验证音频时长 | 低 |
| 2 | `check_audio_sample_rate` | WAV 原子 | 验证采样率 | 低 |
| 3 | `check_audio_channels` | WAV 原子 | 验证声道数 | 低 |
| 4 | `check_audio_rms_level` | WAV 原子 | 验证 RMS 音量范围 | 低 |
| 5 | `check_audio_fade_in` | WAV 原子 | 验证淡入效果（窗口 RMS 递增） | 中 |
| 6 | `check_audio_fade_out` | WAV 原子 | 验证淡出效果（窗口 RMS 递减） | 中 |
| 7 | `check_audio_silence_at` | WAV 原子 | 验证指定区域静音 | 低 |
| 8 | `check_audio_has_content_at` | WAV 原子 | 验证指定区域有内容 | 低 |
| 9 | `check_audio_peak_amplitude` | WAV 原子 | 验证峰值振幅范围 | 低 |
| 10 | `check_audio_file_valid` | WAV 原子 | 验证文件存在且可读 | 低 |
| 11 | `check_audio_properties` | WAV 复合 | 时长 + 采样率 + 声道 | 中 |
| 12 | `check_audio_with_fades` | WAV 复合 | 时长 + 可选淡入/淡出 | 中 |
| 13 | `check_aup3_track_count` | .aup3 | 验证轨道数 | 低 |
| 14 | `check_aup3_track_gain` | .aup3 | 验证轨道增益（dB） | 中 |
| 15 | `check_aup3_track_mute` | .aup3 | 验证轨道静音状态 | 低 |
| 16 | `check_aup3_labels` | .aup3 | 验证标签时间和文本 | 中 |

**总计**：16 个评估函数，覆盖 50 个任务（18 个 L1 + 19 个 L2 + 13 个 L3）。全部已实现，无需新增。

---

## 5. 素材生成说明

所有音频素材使用 Python + NumPy + SciPy 生成，位于 `assets/audacity/audio/` 目录。

### 技术规格

| 属性 | 值 |
|------|-----|
| 采样率 | 44100 Hz |
| 位深 | 16-bit PCM |
| 声道 | 单声道（除 stereo_test.wav 为立体声） |
| 格式 | WAV |
| 总文件数 | 27 |
| 总大小 | ~30 MB |

### 频率范围

| 范围 | 值 |
|------|-----|
| 最低频率 | 80 Hz（bass.wav） |
| 最高频率 | 3200 Hz（analysis_test 谐波） |
| 最常见 | 390-530 Hz |

### 时长范围

| 范围 | 值 |
|------|-----|
| 最短 | 3 秒（short_test.wav） |
| 最长 | 60 秒（long_test.wav） |
| 最常见 | 10-20 秒 |

---

## 6. Task JSON 模板

### 单指标评估（大部分 L1 任务）

```json
{
  "id": "<uuid4>",
  "snapshot": "audacity",
  "instruction": "Open /home/user/Documents/<input>.wav in Audacity. <操作描述>. Export as WAV to /home/user/Documents/exports/<output>.wav, then save the project.",
  "source": "",
  "config": [
    {
      "type": "upload_file",
      "parameters": {
        "files": [
          {
            "local_path": "assets/audacity/<input>.wav",
            "path": "/home/user/Documents/<input>.wav"
          }
        ]
      }
    },
    {
      "type": "launch",
      "parameters": {
        "command": ["/usr/bin/audacity", "/home/user/Documents/<input>.wav"]
      }
    },
    {
      "type": "sleep",
      "parameters": {
        "seconds": 3
      }
    }
  ],
  "trajectory": "trajectories/",
  "related_apps": ["audacity"],
  "evaluator": {
    "postconfig": [],
    "func": "check_audio_duration",
    "result": {
      "type": "vm_file",
      "path": "/home/user/Documents/exports/<output>.wav",
      "dest": "<output>.wav"
    },
    "expected": {
      "type": "rule",
      "rules": {
        "expected_duration": 8.0,
        "tolerance": 0.5
      }
    }
  },
  "proxy": false,
  "fixed_ip": false,
  "possibility_of_env_change": "low"
}
```

### 多指标评估（大部分 L2/L3 任务）

```json
{
  "id": "<uuid4>",
  "snapshot": "audacity",
  "instruction": "Open /home/user/Documents/<input>.wav in Audacity. <多步操作描述>. Export as WAV to /home/user/Documents/exports/<output>.wav, then save the project.",
  "source": "",
  "config": [
    {
      "type": "upload_file",
      "parameters": {
        "files": [
          {"local_path": "assets/audacity/<input>.wav", "path": "/home/user/Documents/<input>.wav"}
        ]
      }
    },
    {
      "type": "launch",
      "parameters": {
        "command": ["/usr/bin/audacity", "/home/user/Documents/<input>.wav"]
      }
    },
    {
      "type": "sleep",
      "parameters": {"seconds": 3}
    }
  ],
  "trajectory": "trajectories/",
  "related_apps": ["audacity"],
  "evaluator": {
    "postconfig": [],
    "func": ["check_audio_duration", "check_audio_fade_out"],
    "conj": "and",
    "result": [
      {"type": "vm_file", "path": "/home/user/Documents/exports/<output>.wav", "dest": "<output>.wav"},
      {"type": "vm_file", "path": "/home/user/Documents/exports/<output>.wav", "dest": "<output>.wav"}
    ],
    "expected": [
      {"type": "rule", "rules": {"expected_duration": 10.0, "tolerance": 0.5}},
      {"type": "rule", "rules": {"fade_duration": 2.0, "num_windows": 5}}
    ]
  },
  "proxy": false,
  "fixed_ip": false,
  "possibility_of_env_change": "low"
}
```

### .aup3 项目评估（项目级验证）

```json
{
  "id": "<uuid4>",
  "snapshot": "audacity",
  "instruction": "Open /home/user/Documents/<input>.wav in Audacity. <多轨操作描述>. Save the project as /home/user/Documents/<project>.aup3.",
  "source": "",
  "config": [
    {
      "type": "upload_file",
      "parameters": {
        "files": [
          {"local_path": "assets/audacity/<input>.wav", "path": "/home/user/Documents/<input>.wav"},
          {"local_path": "assets/audacity/<extra>.wav", "path": "/home/user/Documents/<extra>.wav"}
        ]
      }
    },
    {
      "type": "launch",
      "parameters": {
        "command": ["/usr/bin/audacity", "/home/user/Documents/<input>.wav"]
      }
    },
    {
      "type": "sleep",
      "parameters": {"seconds": 3}
    }
  ],
  "trajectory": "trajectories/",
  "related_apps": ["audacity"],
  "evaluator": {
    "postconfig": [],
    "func": "check_aup3_track_count",
    "result": {
      "type": "vm_file",
      "path": "/home/user/Documents/<project>.aup3",
      "dest": "<project>.aup3"
    },
    "expected": {
      "type": "rule",
      "rules": {
        "expected_track_count": 3
      }
    }
  },
  "proxy": false,
  "fixed_ip": false,
  "possibility_of_env_change": "low"
}
```

---

## 7. Docker 镜像要求

VM/Docker 镜像需要预装：

- **Audacity 3.x**（推荐 3.4+，支持 .aup3 格式）
  ```bash
  dnf install audacity
  # 或 apt-get install audacity
  ```
- **X11 显示环境**（Audacity 需要 GUI）
- **Python 3**（评估器运行环境，标准库即可）

验证安装：
```bash
/usr/bin/audacity --version
# 或检查可执行文件
which audacity
```

**注意**：评估器仅使用 Python 标准库（`wave`, `struct`, `sqlite3`, `xml.etree`），不需要在 VM 上安装 `numpy`、`librosa` 等第三方库。

---

## 8. 任务难度分布总结

| 级别 | 数量 | 平均步骤 | 描述 | 示例 |
|------|------|---------|------|------|
| L1 | 18 | 1 步 | 单步原子操作 | 导入/导出 WAV、删除段、修剪、淡入/淡出、放大、生成静音、重采样、拆分立体声 |
| L2 | 19 | 3-4 步 | 多步复合操作 | 删除 + 淡出、放大 + 淡入淡出、降噪 + 导出、多轨 + 增益、标签管理、修剪 + 重采样 |
| L3 | 13 | 7+ 步 | 复杂工作流 | 多轨混音 + 标签 + 增益、多段编辑 + 静音 + 淡入淡出、降噪 + 放大 + 淡入淡出、多轨 + 静音 + 标签 + 双格式保存 |
| **总计** | **50** | | | |

### 可验证性保证

所有任务的验证基于以下两种可靠机制：

1. **WAV 文件分析**：使用 Python `wave` 模块读取标准 WAV 格式，通过 `struct` 解析样本数据。验证时长、采样率、声道、RMS 音量、淡入/淡出趋势、静音/有声区域等客观指标。

2. **`.aup3` SQLite 解析**：Audacity 3.x 项目文件为 SQLite 数据库，通过 `sqlite3` 读取 `project` 表中的 XML 元数据，解析轨道数量、增益、静音状态、标签位置和文本等项目级信息。

**不依赖**截图对比、OCR 或其他不可靠的视觉检查方法。全部使用 Python 标准库，无第三方依赖。

---

## 9. 常见陷阱

### .aup3 解析注意事项

- **XML 命名空间**：Audacity .aup3 中的项目 XML 可能包含命名空间前缀，解析时需要处理 `{namespace}tag` 格式。
- **增益存储格式**：.aup3 中增益以线性倍率存储（如 0.5 对应 -6dB），需转换为 dB 进行比较。
- **静音存储格式**：存储为字符串 `"0"` 或 `"1"`，需转换为布尔值。
- **标签名称**：不同 Audacity 版本可能使用 `<label>` 或 `<Label>`，时间属性可能为 `t` 或 `t0`。

### WAV 分析注意事项

- **采样位宽**：需支持 8/16/24/32-bit 格式，每种格式的归一化系数不同。
- **淡入/淡出检测**：基于窗口化 RMS 趋势，允许少量非单调（容差：`num_windows - 2` 个递增/递减即可通过）。
- **多声道处理**：分析前先混合为单声道（各声道取平均）。
- **时间精度**：时长比较默认容差 0.5s，标签时间比较默认容差 1.0s。

### Task JSON 常见问题

- **exports 目录**：WAV 导出路径通常为 `/home/user/Documents/exports/`，需确保目录在评测前存在或由智能体创建。
- **双格式保存**：部分 L3 任务同时需要导出 WAV 和保存 .aup3，两个文件路径都需要在 evaluator 中指定。
- **生成音频任务**：任务 L1-29 不打开现有文件，而是从空项目开始，config 中无 `upload_file`。
