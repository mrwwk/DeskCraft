# Audacity Task Design Document

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
    Args:
        file_path: 从 VM 下载到本地的 WAV 或 .aup3 文件路径
        rule: dict with expected values
    Returns:
        1.0 (pass) or 0.0 (fail)
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
| 文件格式 | WAV (标准音频) / .aup3 (SQLite) | .blend (二进制) |
| 验证方式 | `vm_file` → 下载后本地分析 | `vm_command_line` → VM 上运行 Python 脚本 |
| 依赖库 | `wave`, `struct`, `sqlite3`, `xml.etree` (全部 stdlib) | `bpy` (Blender 内嵌 Python) |
| 额外脚本 | 不需要 | 需要上传 check_*.py 到 VM |

---

## 1. Available Resources

All resource files are located at: `assets/audacity/`

Total: **27 WAV files + 1 Python utility, ~30 MB**

### 1.1 Audio Files (.wav) — 27 files

Generated via Python + NumPy + SciPy. All files are synthesized（非录制），采用 44100 Hz / 16-bit PCM / Mono 格式。

#### 1.1.1 Basic Test Files

| Filename | Duration | Size | Content | Purpose |
|----------|----------|------|---------|---------|
| `sample.wav` | 8s | 706 KB | 440Hz sine wave | General testing, import/export |
| `test.wav` | 5s | 441 KB | 440Hz sine wave | Basic operations |

#### 1.1.2 Speech-Like Audio

| Filename | Duration | Size | Content | Purpose |
|----------|----------|------|---------|---------|
| `speech.wav` | 12s | 1.1 MB | Frequency-varying pattern | Speech operations testing, delete + fade |

#### 1.1.3 Effect Test Files

| Filename | Duration | Size | Content | Purpose |
|----------|----------|------|---------|---------|
| `fade_test.wav` | 18s | 1.6 MB | 523Hz sine wave | Fade in/out effects |
| `volume_test.wav` | 10s | 882 KB | 392Hz sine wave | Amplify/volume/normalize |
| `noisy_recording.wav` | 14s | 1.2 MB | Sine wave + 15% noise | Noise reduction workflow |
| `eq_test.wav` | 20s | 1.8 MB | Multi-frequency (100Hz, 1kHz, 5kHz) | Equalization testing |
| `clipping_test.wav` | 15s | 1.3 MB | Overdriven sine wave | Find Clipping feature |

#### 1.1.4 Editing Test Files

| Filename | Duration | Size | Content | Purpose |
|----------|----------|------|---------|---------|
| `edit_test.wav` | 12s | 1.1 MB | 440Hz sine wave | Cut/paste/trim operations |
| `delete_test.wav` | 10s | 882 KB | 392Hz sine wave | Delete operations |
| `duplicate_test.wav` | 8s | 706 KB | 494Hz sine wave | Copy/duplicate/insert |
| `short_test.wav` | 3s | 265 KB | Short audio | Append silence, repeat |
| `long_test.wav` | 60s | 5.3 MB | Audio test track | Complex multi-step edits |
| `complex_sections.wav` | 20s | 1.8 MB | Section-based audio | Section edit with labels |

#### 1.1.5 Multi-Track Audio (for mixing)

| Filename | Duration | Size | Content | Purpose |
|----------|----------|------|---------|---------|
| `vocals.wav` | 30s | 2.6 MB | Melodic pattern (440-587Hz) | Vocal track mixing |
| `drums.wav` | 30s | 2.6 MB | Percussive low-frequency pattern | Drum track mixing |
| `bass.wav` | 30s | 2.6 MB | Low-frequency variation (80-100Hz) | Bass track mixing |

#### 1.1.6 Stereo Audio

| Filename | Duration | Size | Content | Purpose |
|----------|----------|------|---------|---------|
| `stereo_test.wav` | 15s | 1.3 MB | Stereo audio | Split stereo, mono mixdown |

#### 1.1.7 Advanced & Specialized Files

| Filename | Duration | Size | Content | Purpose |
|----------|----------|------|---------|---------|
| `label_test.wav` | 32s | 2.8 MB | 440Hz sine wave | Label track management |
| `crossfade_test.wav` | 15s | 1.3 MB | Combined 440Hz + 660Hz | Cross-fade between tracks |
| `analysis_test.wav` | 15s | 1.3 MB | 5-frequency harmonic series | Plot Spectrum analysis |
| `undo_test.wav` | 18s | 1.6 MB | 392Hz sine wave | Undo/redo history |
| `mute_solo_test.wav` | 25s | 2.2 MB | Dual-frequency pattern | Track mute/solo |
| `mix_test.wav` | 20s | 1.8 MB | 4-frequency chord | Track volume mixing |
| `silence_test.wav` | 10s | 882 KB | Silence test audio | Silence insertion/generation |
| `rhythmic_test.wav` | 12s | 1.1 MB | Rhythmic pattern | Rhythmic editing tasks |

---

### 1.2 Utility Scripts — 1 file

| Script | Location | Description |
|--------|----------|-------------|
| `audio_analysis.py` | `assets/audacity/projects/` | Audio analysis utility using librosa/scipy for development testing |

---

## 2. 评估函数设计

File: `desktop_env/evaluators/metrics/audacity.py`

使用 Python 标准库实现，无需第三方依赖（`wave`, `struct`, `sqlite3`, `xml.etree`）。

### 2.1 内部辅助函数

| Helper | Description |
|--------|-------------|
| `_read_wav_info(file_path)` | 读取 WAV 基本信息: channels, sample_rate, n_frames, duration, sampwidth |
| `_read_wav_samples(file_path)` | 读取 WAV 样本为 [-1.0, 1.0] 浮点列表，支持 8/16/24/32-bit |
| `_rms_db(samples)` | 计算 RMS 分贝值 |
| `_get_mono_samples(file_path)` | 读取 WAV 并返回单声道样本 + 采样率 |
| `_extract_time_range(samples, sr, start, end)` | 提取指定时间范围内的样本 |
| `_open_aup3(file_path)` | 打开 .aup3 文件作为 SQLite 数据库 |
| `_get_aup3_project_xml(file_path)` | 从 .aup3 中提取项目 XML |
| `_parse_aup3_tracks(file_path)` | 解析 .aup3 轨道信息（wave/label tracks） |

### 2.2 WAV 文件原子评估器

| Function | Description | result Type | expected Type | rule 参数 |
|----------|-------------|-------------|---------------|-----------|
| `check_audio_duration` | 验证音频时长 | `vm_file` (WAV) | `rule` | `{"expected_duration": float, "tolerance": float}` |
| `check_audio_sample_rate` | 验证采样率 | `vm_file` (WAV) | `rule` | `{"expected_sr": int}` |
| `check_audio_channels` | 验证声道数 | `vm_file` (WAV) | `rule` | `{"expected_channels": int}` |
| `check_audio_rms_level` | 验证 RMS 音量在范围内 | `vm_file` (WAV) | `rule` | `{"min_rms_db": float, "max_rms_db": float}` |
| `check_audio_fade_in` | 验证淡入效果（窗口 RMS 递增） | `vm_file` (WAV) | `rule` | `{"fade_duration": float, "num_windows": int}` |
| `check_audio_fade_out` | 验证淡出效果（窗口 RMS 递减） | `vm_file` (WAV) | `rule` | `{"fade_duration": float, "num_windows": int}` |
| `check_audio_silence_at` | 验证指定区域为静音 | `vm_file` (WAV) | `rule` | `{"start_time": float, "end_time": float, "max_rms_db": float}` |
| `check_audio_has_content_at` | 验证指定区域有音频内容 | `vm_file` (WAV) | `rule` | `{"start_time": float, "end_time": float, "min_rms_db": float}` |
| `check_audio_peak_amplitude` | 验证峰值振幅在范围内 | `vm_file` (WAV) | `rule` | `{"min_peak_db": float, "max_peak_db": float}` |
| `check_audio_file_valid` | 验证音频文件存在且可读 | `vm_file` (WAV) | `rule` | `{}` |

### 2.3 WAV 文件复合评估器

| Function | Description | result Type | expected Type | rule 参数 |
|----------|-------------|-------------|---------------|-----------|
| `check_audio_properties` | 时长 + 采样率 + 声道数一起验证 | `vm_file` (WAV) | `rule` | `{"expected_duration": float, "tolerance": float, "expected_sr": int, "expected_channels": int}` |
| `check_audio_with_fades` | 时长 + 可选淡入/淡出 | `vm_file` (WAV) | `rule` | `{"expected_duration": float, "tolerance": float, "fade_in_duration": float, "fade_out_duration": float}` |

### 2.4 .aup3 项目文件评估器

| Function | Description | result Type | expected Type | rule 参数 |
|----------|-------------|-------------|---------------|-----------|
| `check_aup3_track_count` | 验证项目中轨道数量 | `vm_file` (.aup3) | `rule` | `{"expected_track_count": int}` |
| `check_aup3_track_gain` | 验证轨道增益（dB） | `vm_file` (.aup3) | `rule` | `{"track_index": int, "expected_gain_db": float, "tolerance": float}` |
| `check_aup3_track_mute` | 验证轨道静音状态 | `vm_file` (.aup3) | `rule` | `{"track_index": int, "expected_mute": bool}` |
| `check_aup3_labels` | 验证标签位置和文本 | `vm_file` (.aup3) | `rule` | `{"expected_labels": [{"time": float, "text": str}], "time_tolerance": float}` |

---

## 3. Task Definitions

### 3.1 Level 1 — 基础操作 (Single-step, directly verifiable) — 18 个

L1 任务为单步原子操作，每个任务只涉及一个核心 GUI 动作。所有任务统一使用以下模式：

- **Launch**: `/usr/bin/audacity /home/user/Documents/<input>.wav`
- **验证**: 通过 `vm_file` getter 下载导出的 WAV 文件或 .aup3 项目文件
- **上传文件**: WAV 素材 → `/home/user/Documents/<input>.wav`

---

#### Task L1-1: Import & Export WAV

- **ID**: `a1b00001-0001-4000-8000-000000000001`
- **Instruction**: Open /home/user/Documents/sample.wav in Audacity. Export the audio as a WAV file to /home/user/Documents/exports/sample_export.wav (File > Export > Export as WAV), then save the project.
- **Upload Assets**: `sample.wav` → `/home/user/Documents/sample.wav`
- **Evaluator**: `check_audio_properties`
- **result**: `vm_file` → `/home/user/Documents/exports/sample_export.wav`
- **expected**: `rule` → `{"expected_duration": 8.0, "tolerance": 0.5, "expected_sr": 44100, "expected_channels": 1}`
- **验证逻辑**: 时长 ≈ 8s + 采样率 44100Hz + 单声道
- **New Evaluator Required**: ❌

---

#### Task L1-2: Export WAV

- **ID**: `a1b00002-0002-4000-8000-000000000002`
- **Instruction**: Open /home/user/Documents/test.wav in Audacity. Export the audio as a WAV file to /home/user/Documents/exports/test_export.wav, then save the project.
- **Upload Assets**: `test.wav` → `/home/user/Documents/test.wav`
- **Evaluator**: `check_audio_duration`
- **result**: `vm_file` → `/home/user/Documents/exports/test_export.wav`
- **expected**: `rule` → `{"expected_duration": 5.0, "tolerance": 0.5}`
- **验证逻辑**: 时长 ≈ 5s
- **New Evaluator Required**: ❌

---

#### Task L1-3: Delete 2s Segment

- **ID**: `a1b00003-0003-4000-8000-000000000003`
- **Instruction**: Open /home/user/Documents/delete_test.wav in Audacity. Select the audio from 3.0 seconds to 5.0 seconds, then delete the selection (Edit > Delete). Export as WAV to /home/user/Documents/exports/deleted.wav, then save the project.
- **Upload Assets**: `delete_test.wav` → `/home/user/Documents/delete_test.wav`
- **Evaluator**: `check_audio_duration`
- **result**: `vm_file` → `/home/user/Documents/exports/deleted.wav`
- **expected**: `rule` → `{"expected_duration": 8.0, "tolerance": 0.5}`
- **验证逻辑**: 原 10s - 删除 2s = 8s
- **New Evaluator Required**: ❌

---

#### Task L1-4: Trim to Selection

- **ID**: `a1b00004-0004-4000-8000-000000000004`
- **Instruction**: Open /home/user/Documents/edit_test.wav in Audacity. Select the audio from 4.0 seconds to 8.0 seconds, then trim to selection (Edit > Remove Special > Trim Audio). Export as WAV to /home/user/Documents/exports/trimmed.wav, then save the project.
- **Upload Assets**: `edit_test.wav` → `/home/user/Documents/edit_test.wav`
- **Evaluator**: `check_audio_duration`
- **result**: `vm_file` → `/home/user/Documents/exports/trimmed.wav`
- **expected**: `rule` → `{"expected_duration": 4.0, "tolerance": 0.5}`
- **验证逻辑**: 保留 4-8s = 4s
- **New Evaluator Required**: ❌

---

#### Task L1-5: Fade-in (first 2s)

- **ID**: `a1b00005-0005-4000-8000-000000000005`
- **Instruction**: Open /home/user/Documents/fade_test.wav in Audacity. Select the first 2 seconds of audio (from 0.0 to 2.0 seconds), then apply a fade-in effect (Effect > Fade In). Export the result as WAV to /home/user/Documents/exports/fadein.wav, then save the project.
- **Upload Assets**: `fade_test.wav` → `/home/user/Documents/fade_test.wav`
- **Evaluator**: `check_audio_fade_in`
- **result**: `vm_file` → `/home/user/Documents/exports/fadein.wav`
- **expected**: `rule` → `{"fade_duration": 2.0, "num_windows": 5}`
- **验证逻辑**: 前 2 秒内 RMS 窗口呈递增趋势
- **New Evaluator Required**: ❌

---

#### Task L1-6: Fade-out (last 2s)

- **ID**: `a1b00006-0006-4000-8000-000000000006`
- **Instruction**: Open /home/user/Documents/fade_test.wav in Audacity. Select the last 2 seconds of audio, then apply a fade-out effect (Effect > Fade Out). Export the result as WAV to /home/user/Documents/exports/fadeout.wav, then save the project.
- **Upload Assets**: `fade_test.wav` → `/home/user/Documents/fade_test.wav`
- **Evaluator**: `check_audio_fade_out`
- **result**: `vm_file` → `/home/user/Documents/exports/fadeout.wav`
- **expected**: `rule` → `{"fade_duration": 2.0, "num_windows": 5}`
- **验证逻辑**: 最后 2 秒内 RMS 窗口呈递减趋势
- **New Evaluator Required**: ❌

---

#### Task L1-7: Amplify +6dB

- **ID**: `a1b00007-0007-4000-8000-000000000007`
- **Instruction**: Open /home/user/Documents/volume_test.wav in Audacity. Select all audio (Ctrl+A), then apply the Amplify effect (Effect > Amplify) with +6 dB amplification. Export as WAV to /home/user/Documents/exports/amplified.wav, then save the project.
- **Upload Assets**: `volume_test.wav` → `/home/user/Documents/volume_test.wav`
- **Evaluator**: `check_audio_rms_level`
- **result**: `vm_file` → `/home/user/Documents/exports/amplified.wav`
- **expected**: `rule` → `{"min_rms_db": -25.0, "max_rms_db": -5.0}`
- **验证逻辑**: 放大后 RMS 在指定范围内
- **New Evaluator Required**: ❌

---

#### Task L1-8: Append 3s Silence

- **ID**: `a1b00008-0008-4000-8000-000000000008`
- **Instruction**: Open /home/user/Documents/short_test.wav in Audacity. Place the cursor at the end of the audio track, then generate 3 seconds of silence (Generate > Silence). Export as WAV to /home/user/Documents/exports/with_silence.wav, then save the project.
- **Upload Assets**: `short_test.wav` → `/home/user/Documents/short_test.wav`
- **Evaluator**: 多指标 `["check_audio_duration", "check_audio_silence_at"]`, `"conj": "and"`
- **result**: 2 个 `vm_file` → `/home/user/Documents/exports/with_silence.wav`
- **expected**: 2 个 `rule`
  - `{"expected_duration": 6.0, "tolerance": 0.5}`
  - `{"start_time": 3.0, "end_time": 5.5, "max_rms_db": -40}`
- **验证逻辑**: 时长 ≈ 6s (3s原始 + 3s静音) + 后半段为静音
- **New Evaluator Required**: ❌

---

#### Task L1-9: Resample to 22050Hz

- **ID**: `a1b00009-0009-4000-8000-000000000009`
- **Instruction**: Open /home/user/Documents/test.wav in Audacity. Change the project sample rate to 22050 Hz (in the bottom-left Project Rate dropdown), then export as WAV to /home/user/Documents/exports/resampled.wav. Save the project.
- **Upload Assets**: `test.wav` → `/home/user/Documents/test.wav`
- **Evaluator**: `check_audio_sample_rate`
- **result**: `vm_file` → `/home/user/Documents/exports/resampled.wav`
- **expected**: `rule` → `{"expected_sr": 22050}`
- **验证逻辑**: 采样率 == 22050
- **New Evaluator Required**: ❌

---

#### Task L1-10: Split Stereo, Export Left

- **ID**: `a1b00010-0010-4000-8000-000000000010`
- **Instruction**: Open /home/user/Documents/stereo_test.wav in Audacity. Split the stereo track into two mono tracks (click the track dropdown > Split Stereo to Mono). Delete the right (bottom) channel. Export the remaining left channel as mono WAV to /home/user/Documents/exports/left_channel.wav. Save the project.
- **Upload Assets**: `stereo_test.wav` → `/home/user/Documents/stereo_test.wav`
- **Evaluator**: 多指标 `["check_audio_channels", "check_audio_duration"]`, `"conj": "and"`
- **result**: 2 个 `vm_file` → `/home/user/Documents/exports/left_channel.wav`
- **expected**: 2 个 `rule`
  - `{"expected_channels": 1}`
  - `{"expected_duration": 15.0, "tolerance": 1.0}`
- **验证逻辑**: 单声道 + 时长保持 ≈ 15s
- **New Evaluator Required**: ❌

---

#### Task L1-26: Normalize to -1dB Peak

- **ID**: `a1b00026-0026-4000-8000-000000000026`
- **Instruction**: Open /home/user/Documents/volume_test.wav in Audacity. Select all audio (Ctrl+A) and apply the Normalize effect (Effect > Normalize) with peak amplitude -1.0 dB. Export as WAV to /home/user/Documents/exports/normalized.wav, then save the project.
- **Upload Assets**: `volume_test.wav` → `/home/user/Documents/volume_test.wav`
- **Evaluator**: `check_audio_peak_amplitude`
- **result**: `vm_file` → `/home/user/Documents/exports/normalized.wav`
- **expected**: `rule` → `{"min_peak_db": -2.0, "max_peak_db": 0.0}`
- **验证逻辑**: 峰值 ≈ -1dB
- **New Evaluator Required**: ❌

---

#### Task L1-27: Stereo to Mono Mixdown

- **ID**: `a1b00027-0027-4000-8000-000000000027`
- **Instruction**: Open /home/user/Documents/stereo_test.wav in Audacity. Mix the stereo track down to mono by going to Tracks > Mix > Mix Stereo Down to Mono. Export as WAV to /home/user/Documents/exports/mono_mix.wav. Save the project.
- **Upload Assets**: `stereo_test.wav` → `/home/user/Documents/stereo_test.wav`
- **Evaluator**: `check_audio_properties`
- **result**: `vm_file` → `/home/user/Documents/exports/mono_mix.wav`
- **expected**: `rule` → `{"expected_duration": 15.0, "tolerance": 1.0, "expected_channels": 1}`
- **验证逻辑**: 时长 ≈ 15s + 单声道
- **New Evaluator Required**: ❌

---

#### Task L1-28: Repeat Audio to Double Length

- **ID**: `a1b00028-0028-4000-8000-000000000028`
- **Instruction**: Open /home/user/Documents/short_test.wav in Audacity. Select all audio (Ctrl+A), then use Effect > Repeat with 1 repeat to double the length. Export as WAV to /home/user/Documents/exports/doubled.wav. Save the project.
- **Upload Assets**: `short_test.wav` → `/home/user/Documents/short_test.wav`
- **Evaluator**: `check_audio_duration`
- **result**: `vm_file` → `/home/user/Documents/exports/doubled.wav`
- **expected**: `rule` → `{"expected_duration": 6.0, "tolerance": 0.5}`
- **验证逻辑**: 原 3s × 2 = 6s
- **New Evaluator Required**: ❌

---

#### Task L1-29: Generate 5s Tone from Scratch

- **ID**: `a1b00029-0029-4000-8000-000000000029`
- **Instruction**: Open Audacity (without opening a file). Generate a 5-second tone using Generate > Tone with frequency 440 Hz, amplitude 0.8, and waveform Sine. Export as WAV to /home/user/Documents/exports/generated_tone.wav. Save the project.
- **Upload Assets**: 无（从空项目开始）
- **Evaluator**: `check_audio_properties`
- **result**: `vm_file` → `/home/user/Documents/exports/generated_tone.wav`
- **expected**: `rule` → `{"expected_duration": 5.0, "tolerance": 0.5, "expected_sr": 44100, "expected_channels": 1}`
- **验证逻辑**: 时长 ≈ 5s + 44100Hz + 单声道
- **New Evaluator Required**: ❌

---

#### Task L1-30: Delete Last 3 Seconds

- **ID**: `a1b00030-0030-4000-8000-000000000030`
- **Instruction**: Open /home/user/Documents/edit_test.wav in Audacity. Select the last 3 seconds of audio (from 9.0 to 12.0 seconds) and delete them (Edit > Delete). Export the result as WAV to /home/user/Documents/exports/trimmed_end.wav, then save the project.
- **Upload Assets**: `edit_test.wav` → `/home/user/Documents/edit_test.wav`
- **Evaluator**: `check_audio_duration`
- **result**: `vm_file` → `/home/user/Documents/exports/trimmed_end.wav`
- **expected**: `rule` → `{"expected_duration": 9.0, "tolerance": 0.5}`
- **验证逻辑**: 原 12s - 3s = 9s
- **New Evaluator Required**: ❌

---

#### Task L1-31: Export Selected Region Only

- **ID**: `a1b00031-0031-4000-8000-000000000031`
- **Instruction**: Open /home/user/Documents/long_test.wav in Audacity. Select the audio from 10.0 to 20.0 seconds. Export only the selected audio as WAV to /home/user/Documents/exports/selection.wav. Save the project.
- **Upload Assets**: `long_test.wav` → `/home/user/Documents/long_test.wav`
- **Evaluator**: `check_audio_duration`
- **result**: `vm_file` → `/home/user/Documents/exports/selection.wav`
- **expected**: `rule` → `{"expected_duration": 10.0, "tolerance": 0.5}`
- **验证逻辑**: 导出选区 10-20s = 10s
- **New Evaluator Required**: ❌

---

#### Task L1-32: Resample to 48000Hz

- **ID**: `a1b00032-0032-4000-8000-000000000032`
- **Instruction**: Open /home/user/Documents/sample.wav in Audacity. Change the project sample rate to 48000 Hz using the Project Rate dropdown. Export as WAV to /home/user/Documents/exports/resample48k.wav. Save the project.
- **Upload Assets**: `sample.wav` → `/home/user/Documents/sample.wav`
- **Evaluator**: `check_audio_sample_rate`
- **result**: `vm_file` → `/home/user/Documents/exports/resample48k.wav`
- **expected**: `rule` → `{"expected_sr": 48000}`
- **验证逻辑**: 采样率 == 48000
- **New Evaluator Required**: ❌

---

#### Task L1-33: Attenuate by -6dB

- **ID**: `a1b00033-0033-4000-8000-000000000033`
- **Instruction**: Open /home/user/Documents/fade_test.wav in Audacity. Select all audio (Ctrl+A) and apply the Amplify effect (Effect > Amplify) with -6 dB. Export as WAV to /home/user/Documents/exports/attenuated.wav. Save the project.
- **Upload Assets**: `fade_test.wav` → `/home/user/Documents/fade_test.wav`
- **Evaluator**: `check_audio_rms_level`
- **result**: `vm_file` → `/home/user/Documents/exports/attenuated.wav`
- **expected**: `rule` → `{"min_rms_db": -40.0, "max_rms_db": -10.0}`
- **验证逻辑**: 衰减后 RMS 在指定范围内
- **New Evaluator Required**: ❌

---

### L1 任务汇总

| # | Task | Asset File | Evaluator Function | New? |
|---|------|-----------|-------------------|------|
| 1 | Import & Export WAV | `sample.wav` | `check_audio_properties` | ❌ |
| 2 | Export WAV | `test.wav` | `check_audio_duration` | ❌ |
| 3 | Delete 2s Segment | `delete_test.wav` | `check_audio_duration` | ❌ |
| 4 | Trim to Selection | `edit_test.wav` | `check_audio_duration` | ❌ |
| 5 | Fade-in (first 2s) | `fade_test.wav` | `check_audio_fade_in` | ❌ |
| 6 | Fade-out (last 2s) | `fade_test.wav` | `check_audio_fade_out` | ❌ |
| 7 | Amplify +6dB | `volume_test.wav` | `check_audio_rms_level` | ❌ |
| 8 | Append 3s Silence | `short_test.wav` | `check_audio_duration` + `check_audio_silence_at` | ❌ |
| 9 | Resample to 22050Hz | `test.wav` | `check_audio_sample_rate` | ❌ |
| 10 | Split Stereo, Export Left | `stereo_test.wav` | `check_audio_channels` + `check_audio_duration` | ❌ |
| 26 | Normalize to -1dB | `volume_test.wav` | `check_audio_peak_amplitude` | ❌ |
| 27 | Stereo to Mono | `stereo_test.wav` | `check_audio_properties` | ❌ |
| 28 | Repeat Audio | `short_test.wav` | `check_audio_duration` | ❌ |
| 29 | Generate Tone | (empty project) | `check_audio_properties` | ❌ |
| 30 | Delete Last 3s | `edit_test.wav` | `check_audio_duration` | ❌ |
| 31 | Export Selection | `long_test.wav` | `check_audio_duration` | ❌ |
| 32 | Resample to 48000Hz | `sample.wav` | `check_audio_sample_rate` | ❌ |
| 33 | Attenuate -6dB | `fade_test.wav` | `check_audio_rms_level` | ❌ |

**L1 统计**:
- 总任务数: **18**
- 需要新评估函数: **0** 个
- 使用的 .wav 素材: 8 个
- 评估方式: 全部使用 `vm_file` getter + WAV 分析

---

### 3.2 Level 2 — 复合操作 (Multi-step composite operations) — 19 个

L2 任务为多步复合操作，每个任务涉及 **2-4 个关联 GUI 操作**。多数任务使用多指标评估（`func` 为列表，`conj: "and"`）。

---

#### Task L2-11: Delete + Fade-out

- **ID**: `a1b00011-0011-4000-8000-000000000011`
- **Instruction**: Open /home/user/Documents/speech.wav in Audacity. Select the region from 5.0 to 7.0 seconds and delete it (Edit > Delete). Then select the last 2 seconds of the remaining audio and apply a fade-out (Effect > Fade Out). Export as WAV to /home/user/Documents/exports/edit_fade.wav. Save the project.
- **Upload Assets**: `speech.wav` → `/home/user/Documents/speech.wav`
- **Evaluator**: 多指标 `["check_audio_duration", "check_audio_fade_out"]`, `"conj": "and"`
- **result**: 2 个 `vm_file` → `/home/user/Documents/exports/edit_fade.wav`
- **expected**: 2 个 `rule`
  - `{"expected_duration": 10.0, "tolerance": 0.5}`
  - `{"fade_duration": 2.0, "num_windows": 5}`
- **验证逻辑**: 12s - 2s删除 = 10s + 最后 2s 淡出
- **操作步骤数**: 3（选择删除 → 选择末尾 → 淡出）

---

#### Task L2-12: Amplify + Fade-in + Fade-out

- **ID**: `a1b00012-0012-4000-8000-000000000012`
- **Instruction**: Open /home/user/Documents/volume_test.wav in Audacity. Select all audio (Ctrl+A) and apply Amplify with +6 dB. Then select the first 2 seconds and apply Fade In (Effect > Fade In). Then select the last 2 seconds and apply Fade Out (Effect > Fade Out). Export as WAV to /home/user/Documents/exports/amp_fades.wav. Save the project.
- **Upload Assets**: `volume_test.wav` → `/home/user/Documents/volume_test.wav`
- **Evaluator**: 多指标 `["check_audio_rms_level", "check_audio_fade_in", "check_audio_fade_out"]`, `"conj": "and"`
- **result**: 3 个 `vm_file` → `/home/user/Documents/exports/amp_fades.wav`
- **expected**: 3 个 `rule`
  - `{"min_rms_db": -30.0, "max_rms_db": -5.0}`
  - `{"fade_duration": 2.0, "num_windows": 5}`
  - `{"fade_duration": 2.0, "num_windows": 5}`
- **验证逻辑**: RMS 增大 + 开头淡入 + 结尾淡出
- **操作步骤数**: 4（全选放大 → 选开头淡入 → 选结尾淡出 → 导出）

---

#### Task L2-13: Insert Silence in Middle

- **ID**: `a1b00013-0013-4000-8000-000000000013`
- **Instruction**: Open /home/user/Documents/duplicate_test.wav in Audacity. Place the cursor at 4.0 seconds and generate 2 seconds of silence (Generate > Silence, Duration 2s). Export as WAV to /home/user/Documents/exports/mid_silence.wav. Save the project.
- **Upload Assets**: `duplicate_test.wav` → `/home/user/Documents/duplicate_test.wav`
- **Evaluator**: 多指标 `["check_audio_duration", "check_audio_silence_at"]`, `"conj": "and"`
- **result**: 2 个 `vm_file` → `/home/user/Documents/exports/mid_silence.wav`
- **expected**: 2 个 `rule`
  - `{"expected_duration": 10.0, "tolerance": 0.5}`
  - `{"start_time": 4.0, "end_time": 5.5, "max_rms_db": -40}`
- **验证逻辑**: 原 8s + 2s = 10s + 中间 4-6s 为静音
- **操作步骤数**: 2（定位光标 → 生成静音）

---

#### Task L2-14: Join Two Files

- **ID**: `a1b00014-0014-4000-8000-000000000014`
- **Instruction**: Open /home/user/Documents/short_test.wav in Audacity. Import /home/user/Documents/test.wav as a second track (File > Import > Audio). Mix and render to one track, then export as WAV to /home/user/Documents/exports/joined.wav. Save the project.
- **Upload Assets**: `short_test.wav`, `test.wav` → `/home/user/Documents/`
- **Evaluator**: 多指标 `["check_audio_duration", "check_audio_has_content_at"]`, `"conj": "and"`
- **result**: 2 个 `vm_file` → `/home/user/Documents/exports/joined.wav`
- **expected**: 2 个 `rule`
  - `{"expected_duration": 5.0, "tolerance": 1.0}`
  - `{"start_time": 1.0, "end_time": 4.0, "min_rms_db": -30}`
- **验证逻辑**: 混合后时长 + 中间有内容
- **操作步骤数**: 3（导入第二文件 → 混合渲染 → 导出）

---

#### Task L2-15: Noise Reduction + Export

- **ID**: `a1b00015-0015-4000-8000-000000000015`
- **Instruction**: Open /home/user/Documents/noisy_recording.wav in Audacity. First, select a short silence region (0.0 to 0.5 seconds) and get noise profile (Effect > Noise Reduction > Get Noise Profile). Then select all audio (Ctrl+A) and apply noise reduction. Export as WAV to /home/user/Documents/exports/cleaned.wav. Save the project.
- **Upload Assets**: `noisy_recording.wav` → `/home/user/Documents/noisy_recording.wav`
- **Evaluator**: 多指标 `["check_audio_duration", "check_audio_rms_level"]`, `"conj": "and"`
- **result**: 2 个 `vm_file` → `/home/user/Documents/exports/cleaned.wav`
- **expected**: 2 个 `rule`
  - `{"expected_duration": 14.0, "tolerance": 0.5}`
  - `{"min_rms_db": -50.0, "max_rms_db": -5.0}`
- **验证逻辑**: 时长不变 + RMS 在合理范围
- **操作步骤数**: 4（选噪音 → 获取配置 → 全选 → 降噪）

---

#### Task L2-16: Create 3-Track Project

- **ID**: `a1b00016-0016-4000-8000-000000000016`
- **Instruction**: Open /home/user/Documents/vocals.wav in Audacity. Import /home/user/Documents/drums.wav and /home/user/Documents/bass.wav (File > Import > Audio for each). You should have 3 tracks. Save the project as /home/user/Documents/multitrack.aup3.
- **Upload Assets**: `vocals.wav`, `drums.wav`, `bass.wav` → `/home/user/Documents/`
- **Evaluator**: `check_aup3_track_count`
- **result**: `vm_file` → `/home/user/Documents/multitrack.aup3`
- **expected**: `rule` → `{"expected_track_count": 3}`
- **验证逻辑**: 项目包含 3 个轨道
- **操作步骤数**: 3（导入 drums → 导入 bass → 保存项目）

---

#### Task L2-17: Add Labels

- **ID**: `a1b00017-0017-4000-8000-000000000017`
- **Instruction**: Open /home/user/Documents/label_test.wav in Audacity. Add a label track (Tracks > Add New > Label Track). Add labels: 'Intro' at 0.0s, 'Verse' at 8.0s, 'Chorus' at 16.0s, 'Outro' at 24.0s. Save the project as /home/user/Documents/labeled.aup3.
- **Upload Assets**: `label_test.wav` → `/home/user/Documents/label_test.wav`
- **Evaluator**: `check_aup3_labels`
- **result**: `vm_file` → `/home/user/Documents/labeled.aup3`
- **expected**: `rule` → `{"expected_labels": [{"time": 0.0, "text": "Intro"}, {"time": 8.0, "text": "Verse"}, {"time": 16.0, "text": "Chorus"}, {"time": 24.0, "text": "Outro"}], "time_tolerance": 1.0}`
- **验证逻辑**: 4 个标签的时间和文本匹配
- **操作步骤数**: 5（添加标签轨 → 添加 4 个标签）

---

#### Task L2-18: Set Track Volumes

- **ID**: `a1b00018-0018-4000-8000-000000000018`
- **Instruction**: Open /home/user/Documents/vocals.wav in Audacity. Import /home/user/Documents/drums.wav. Set the vocals track gain to -3 dB and drums track gain to -6 dB using the track gain sliders. Save the project as /home/user/Documents/mixed.aup3.
- **Upload Assets**: `vocals.wav`, `drums.wav` → `/home/user/Documents/`
- **Evaluator**: 多指标 `["check_aup3_track_gain", "check_aup3_track_gain"]`, `"conj": "and"`
- **result**: 2 个 `vm_file` → `/home/user/Documents/mixed.aup3`
- **expected**: 2 个 `rule`
  - `{"track_index": 0, "expected_gain_db": -3.0, "tolerance": 2.0}`
  - `{"track_index": 1, "expected_gain_db": -6.0, "tolerance": 2.0}`
- **验证逻辑**: 两个轨道的增益分别匹配
- **操作步骤数**: 3（导入 drums → 设 vocals 增益 → 设 drums 增益）

---

#### Task L2-19: Mute Track

- **ID**: `a1b00019-0019-4000-8000-000000000019`
- **Instruction**: Open /home/user/Documents/vocals.wav in Audacity. Import /home/user/Documents/drums.wav. Mute the drums track by clicking its Mute button. Save the project as /home/user/Documents/muted.aup3.
- **Upload Assets**: `vocals.wav`, `drums.wav` → `/home/user/Documents/`
- **Evaluator**: 多指标 `["check_aup3_track_count", "check_aup3_track_mute"]`, `"conj": "and"`
- **result**: 2 个 `vm_file` → `/home/user/Documents/muted.aup3`
- **expected**: 2 个 `rule`
  - `{"expected_track_count": 2}`
  - `{"track_index": 1, "expected_mute": true}`
- **验证逻辑**: 2 轨道 + drums 被静音
- **操作步骤数**: 2（导入 → 静音）

---

#### Task L2-20: Trim + Amplify + Fade-out

- **ID**: `a1b00020-0020-4000-8000-000000000020`
- **Instruction**: Open /home/user/Documents/edit_test.wav in Audacity. Select audio from 3.0 to 9.0 seconds and trim to selection. Apply Amplify +6 dB. Select the last 2 seconds and apply Fade Out. Export as WAV to /home/user/Documents/exports/trim_amp_fade.wav. Save the project.
- **Upload Assets**: `edit_test.wav` → `/home/user/Documents/edit_test.wav`
- **Evaluator**: 多指标 `["check_audio_duration", "check_audio_fade_out", "check_audio_rms_level"]`, `"conj": "and"`
- **result**: 3 个 `vm_file` → `/home/user/Documents/exports/trim_amp_fade.wav`
- **expected**: 3 个 `rule`
  - `{"expected_duration": 6.0, "tolerance": 0.5}`
  - `{"fade_duration": 2.0, "num_windows": 5}`
  - `{"min_rms_db": -30.0, "max_rms_db": -3.0}`
- **验证逻辑**: 6s + 淡出 + 增益提升
- **操作步骤数**: 4（选择修剪 → 放大 → 选结尾 → 淡出）

---

#### Task L2-34: Normalize + Fade-in + Fade-out

- **ID**: `a1b00034-0034-4000-8000-000000000034`
- **Instruction**: Open /home/user/Documents/volume_test.wav in Audacity. First normalize the audio (Effect > Normalize, peak amplitude -1.0 dB). Then apply fade-in to the first 2 seconds and fade-out to the last 2 seconds. Export as WAV to /home/user/Documents/exports/norm_fades.wav. Save the project.
- **Upload Assets**: `volume_test.wav` → `/home/user/Documents/volume_test.wav`
- **Evaluator**: 多指标 `["check_audio_peak_amplitude", "check_audio_fade_in", "check_audio_fade_out"]`, `"conj": "and"`
- **result**: 3 个 `vm_file` → `/home/user/Documents/exports/norm_fades.wav`
- **expected**: 3 个 `rule`
  - `{"min_peak_db": -2.0, "max_peak_db": 0.0}`
  - `{"fade_duration": 2.0, "num_windows": 5}`
  - `{"fade_duration": 2.0, "num_windows": 5}`
- **操作步骤数**: 4（归一化 → 选开头淡入 → 选结尾淡出 → 导出）

---

#### Task L2-35: Delete Two Separate Segments

- **ID**: `a1b00035-0035-4000-8000-000000000035`
- **Instruction**: Open /home/user/Documents/long_test.wav in Audacity. Delete 10-15s, then delete 25-30s in current timeline (original 30-35s). Export as WAV to /home/user/Documents/exports/double_delete.wav. Save the project.
- **Upload Assets**: `long_test.wav` → `/home/user/Documents/long_test.wav`
- **Evaluator**: `check_audio_duration`
- **result**: `vm_file` → `/home/user/Documents/exports/double_delete.wav`
- **expected**: `rule` → `{"expected_duration": 50.0, "tolerance": 1.0}`
- **验证逻辑**: 60s - 5s - 5s = 50s
- **操作步骤数**: 3（删除第一段 → 删除第二段 → 导出）

---

#### Task L2-36: Append Generated Tone

- **ID**: `a1b00036-0036-4000-8000-000000000036`
- **Instruction**: Open /home/user/Documents/test.wav in Audacity. Place cursor at end. Generate a 3-second tone (440 Hz). Export as WAV to /home/user/Documents/exports/with_tone.wav. Save the project.
- **Upload Assets**: `test.wav` → `/home/user/Documents/test.wav`
- **Evaluator**: 多指标 `["check_audio_duration", "check_audio_has_content_at"]`, `"conj": "and"`
- **result**: 2 个 `vm_file` → `/home/user/Documents/exports/with_tone.wav`
- **expected**: 2 个 `rule`
  - `{"expected_duration": 8.0, "tolerance": 0.5}`
  - `{"start_time": 5.0, "end_time": 7.5, "min_rms_db": -30}`
- **验证逻辑**: 5s + 3s = 8s + 后半有内容
- **操作步骤数**: 3（定位末尾 → 生成 tone → 导出）

---

#### Task L2-37: 2-Track Project with Gains

- **ID**: `a1b00037-0037-4000-8000-000000000037`
- **Instruction**: Open /home/user/Documents/vocals.wav in Audacity. Import /home/user/Documents/bass.wav. Set vocals gain to -2 dB and bass gain to -4 dB. Save as /home/user/Documents/two_track.aup3.
- **Upload Assets**: `vocals.wav`, `bass.wav` → `/home/user/Documents/`
- **Evaluator**: 多指标 `["check_aup3_track_count", "check_aup3_track_gain", "check_aup3_track_gain"]`, `"conj": "and"`
- **result**: 3 个 `vm_file` → `/home/user/Documents/two_track.aup3`
- **expected**: 3 个 `rule`
  - `{"expected_track_count": 2}`
  - `{"track_index": 0, "expected_gain_db": -2.0, "tolerance": 2.0}`
  - `{"track_index": 1, "expected_gain_db": -4.0, "tolerance": 2.0}`
- **操作步骤数**: 3（导入 → 设增益 × 2）

---

#### Task L2-38: Trim + Resample

- **ID**: `a1b00038-0038-4000-8000-000000000038`
- **Instruction**: Open /home/user/Documents/edit_test.wav in Audacity. Trim to 2-8s, change project rate to 22050 Hz. Export as WAV to /home/user/Documents/exports/trim_resample.wav. Save the project.
- **Upload Assets**: `edit_test.wav` → `/home/user/Documents/edit_test.wav`
- **Evaluator**: 多指标 `["check_audio_duration", "check_audio_sample_rate"]`, `"conj": "and"`
- **result**: 2 个 `vm_file` → `/home/user/Documents/exports/trim_resample.wav`
- **expected**: 2 个 `rule`
  - `{"expected_duration": 6.0, "tolerance": 0.5}`
  - `{"expected_sr": 22050}`
- **操作步骤数**: 3（选择修剪 → 改采样率 → 导出）

---

#### Task L2-39: Mute Track + Add Labels

- **ID**: `a1b00039-0039-4000-8000-000000000039`
- **Instruction**: Open /home/user/Documents/drums.wav in Audacity. Import bass.wav. Mute the drums track. Add a label track with labels 'Beat' at 5.0s and 'Drop' at 15.0s. Save as /home/user/Documents/labeled_mix.aup3.
- **Upload Assets**: `drums.wav`, `bass.wav` → `/home/user/Documents/`
- **Evaluator**: 多指标 `["check_aup3_track_mute", "check_aup3_labels"]`, `"conj": "and"`
- **result**: 2 个 `vm_file` → `/home/user/Documents/labeled_mix.aup3`
- **expected**: 2 个 `rule`
  - `{"track_index": 0, "expected_mute": true}`
  - `{"expected_labels": [{"time": 5.0, "text": "Beat"}, {"time": 15.0, "text": "Drop"}], "time_tolerance": 1.0}`
- **操作步骤数**: 4（导入 → 静音 → 添加标签轨 → 添加标签）

---

#### Task L2-40: Split Stereo + Amplify Left

- **ID**: `a1b00040-0040-4000-8000-000000000040`
- **Instruction**: Open /home/user/Documents/stereo_test.wav in Audacity. Split stereo to mono. Amplify the left (top) channel by +6 dB. Export the left channel only as WAV to /home/user/Documents/exports/left_loud.wav. Save the project.
- **Upload Assets**: `stereo_test.wav` → `/home/user/Documents/stereo_test.wav`
- **Evaluator**: 多指标 `["check_audio_channels", "check_audio_rms_level"]`, `"conj": "and"`
- **result**: 2 个 `vm_file` → `/home/user/Documents/exports/left_loud.wav`
- **expected**: 2 个 `rule`
  - `{"expected_channels": 1}`
  - `{"min_rms_db": -25.0, "max_rms_db": -3.0}`
- **操作步骤数**: 4（分离 → 删右声道 → 放大 → 导出）

---

#### Task L2-41: Insert Silence at Start + Fade-in

- **ID**: `a1b00041-0041-4000-8000-000000000041`
- **Instruction**: Open /home/user/Documents/sample.wav in Audacity. Insert 2 seconds of silence at position 0.0. Then apply fade-in to the first 3 seconds. Export as WAV to /home/user/Documents/exports/silence_fade.wav. Save the project.
- **Upload Assets**: `sample.wav` → `/home/user/Documents/sample.wav`
- **Evaluator**: 多指标 `["check_audio_duration", "check_audio_silence_at", "check_audio_fade_in"]`, `"conj": "and"`
- **result**: 3 个 `vm_file` → `/home/user/Documents/exports/silence_fade.wav`
- **expected**: 3 个 `rule`
  - `{"expected_duration": 10.0, "tolerance": 0.5}`
  - `{"start_time": 0.0, "end_time": 1.5, "max_rms_db": -40}`
  - `{"fade_duration": 3.0, "num_windows": 5}`
- **操作步骤数**: 3（插入静音 → 选 3s → 淡入）

---

#### Task L2-42: Repeat + Fade-out

- **ID**: `a1b00042-0042-4000-8000-000000000042`
- **Instruction**: Open /home/user/Documents/short_test.wav in Audacity. Repeat audio with 2 repeats (triple length). Apply fade-out to the last 3 seconds. Export as WAV to /home/user/Documents/exports/repeat_fade.wav. Save the project.
- **Upload Assets**: `short_test.wav` → `/home/user/Documents/short_test.wav`
- **Evaluator**: 多指标 `["check_audio_duration", "check_audio_fade_out"]`, `"conj": "and"`
- **result**: 2 个 `vm_file` → `/home/user/Documents/exports/repeat_fade.wav`
- **expected**: 2 个 `rule`
  - `{"expected_duration": 9.0, "tolerance": 0.5}`
  - `{"fade_duration": 3.0, "num_windows": 5}`
- **验证逻辑**: 3s × 3 = 9s + 最后 3s 淡出
- **操作步骤数**: 3（全选 → 重复 → 选末尾淡出）

---

### L2 任务汇总

| # | Task | Asset File(s) | Evaluator Function(s) | 步骤数 |
|---|------|--------------|----------------------|--------|
| 11 | Delete + Fade-out | `speech.wav` | duration + fade_out | 3 |
| 12 | Amplify + Fade-in + Fade-out | `volume_test.wav` | rms + fade_in + fade_out | 4 |
| 13 | Insert Silence in Middle | `duplicate_test.wav` | duration + silence_at | 2 |
| 14 | Join Two Files | `short_test.wav`, `test.wav` | duration + has_content_at | 3 |
| 15 | Noise Reduction + Export | `noisy_recording.wav` | duration + rms | 4 |
| 16 | Create 3-Track Project | `vocals.wav`, `drums.wav`, `bass.wav` | aup3_track_count | 3 |
| 17 | Add Labels | `label_test.wav` | aup3_labels | 5 |
| 18 | Set Track Volumes | `vocals.wav`, `drums.wav` | aup3_track_gain × 2 | 3 |
| 19 | Mute Track | `vocals.wav`, `drums.wav` | track_count + track_mute | 2 |
| 20 | Trim + Amplify + Fade-out | `edit_test.wav` | duration + fade_out + rms | 4 |
| 34 | Normalize + Fade-in + Fade-out | `volume_test.wav` | peak + fade_in + fade_out | 4 |
| 35 | Delete Two Segments | `long_test.wav` | duration | 3 |
| 36 | Append Generated Tone | `test.wav` | duration + has_content_at | 3 |
| 37 | 2-Track + Gains | `vocals.wav`, `bass.wav` | track_count + gain × 2 | 3 |
| 38 | Trim + Resample | `edit_test.wav` | duration + sample_rate | 3 |
| 39 | Mute + Labels | `drums.wav`, `bass.wav` | track_mute + labels | 4 |
| 40 | Split Stereo + Amplify | `stereo_test.wav` | channels + rms | 4 |
| 41 | Insert Silence + Fade-in | `sample.wav` | duration + silence_at + fade_in | 3 |
| 42 | Repeat + Fade-out | `short_test.wav` | duration + fade_out | 3 |

**L2 统计**:
- 总任务数: **19**
- 需要新评估函数: **0** 个
- 平均操作步骤: **3-4** 步/任务
- 使用 WAV 分析: 12 个
- 使用 .aup3 分析: 5 个
- 混合使用: 2 个

---

### 3.3 Level 3 — 高级工作流 (Advanced multi-step workflows) — 13 个

L3 任务为复杂多步工作流，每个任务涉及 **5+ 个 GUI 操作**，需要综合运用多种功能。多数任务同时使用 WAV 和 .aup3 两种验证方式。

---

#### Task L3-21: Multi-Track Mixdown

- **ID**: `a1b00021-0021-4000-8000-000000000021`
- **Instruction**: Open /home/user/Documents/vocals.wav in Audacity. Import drums.wav and bass.wav. Select all, mixdown and export as mono WAV to /home/user/Documents/exports/mixdown.wav. Save the project.
- **Upload Assets**: `vocals.wav`, `drums.wav`, `bass.wav` → `/home/user/Documents/`
- **Evaluator**: 多指标 `["check_audio_duration", "check_audio_channels"]`, `"conj": "and"`
- **result**: 2 个 `vm_file` → `/home/user/Documents/exports/mixdown.wav`
- **expected**: 2 个 `rule`
  - `{"expected_duration": 30.0, "tolerance": 1.0}`
  - `{"expected_channels": 1}`
- **操作步骤数**: 5+

---

#### Task L3-22: Multi-Track with Labels & Gains

- **ID**: `a1b00022-0022-4000-8000-000000000022`
- **Instruction**: Open /home/user/Documents/vocals.wav in Audacity. Import drums.wav and bass.wav. Set gains: vocals -2 dB, drums -4 dB, bass -3 dB. Add label track with labels: 'Intro' at 0.0s, 'Main' at 10.0s, 'End' at 20.0s. Save as /home/user/Documents/full_project.aup3.
- **Upload Assets**: `vocals.wav`, `drums.wav`, `bass.wav` → `/home/user/Documents/`
- **Evaluator**: 多指标 `["check_aup3_track_count", "check_aup3_labels", "check_aup3_track_gain", "check_aup3_track_gain", "check_aup3_track_gain"]`, `"conj": "and"`
- **result**: 5 个 `vm_file` → `/home/user/Documents/full_project.aup3`
- **expected**: 5 个 `rule`
  - `{"expected_track_count": 4}`
  - `{"expected_labels": [{"time": 0.0, "text": "Intro"}, {"time": 10.0, "text": "Main"}, {"time": 20.0, "text": "End"}], "time_tolerance": 1.0}`
  - `{"track_index": 0, "expected_gain_db": -2.0, "tolerance": 2.0}`
  - `{"track_index": 1, "expected_gain_db": -4.0, "tolerance": 2.0}`
  - `{"track_index": 2, "expected_gain_db": -3.0, "tolerance": 2.0}`
- **操作步骤数**: 8（导入 × 2 → 增益 × 3 → 标签轨 → 标签 × 3 → 保存）

---

#### Task L3-23: Complex Edit: Delete + Silence + Fades

- **ID**: `a1b00023-0023-4000-8000-000000000023`
- **Instruction**: Open /home/user/Documents/long_test.wav. Delete 40-50s, insert 5s silence at 20s, apply fade-in (first 3s) and fade-out (last 3s). Export as WAV to /home/user/Documents/exports/complex_edit.wav. Save the project.
- **Upload Assets**: `long_test.wav` → `/home/user/Documents/long_test.wav`
- **Evaluator**: 多指标 `["check_audio_duration", "check_audio_silence_at", "check_audio_fade_in", "check_audio_fade_out"]`, `"conj": "and"`
- **result**: 4 个 `vm_file` → `/home/user/Documents/exports/complex_edit.wav`
- **expected**: 4 个 `rule`
  - `{"expected_duration": 55.0, "tolerance": 1.5}`
  - `{"start_time": 20.0, "end_time": 24.0, "max_rms_db": -40}`
  - `{"fade_duration": 3.0, "num_windows": 5}`
  - `{"fade_duration": 3.0, "num_windows": 5}`
- **操作步骤数**: 6+

---

#### Task L3-24: Noise Reduce + Amplify + Fades

- **ID**: `a1b00024-0024-4000-8000-000000000024`
- **Instruction**: Open /home/user/Documents/noisy_recording.wav. Get noise profile from 0-0.5s. Apply noise reduction. Amplify +6 dB. Apply fade-in (first 2s) and fade-out (last 2s). Export as WAV to /home/user/Documents/exports/clean_loud.wav. Save the project.
- **Upload Assets**: `noisy_recording.wav` → `/home/user/Documents/noisy_recording.wav`
- **Evaluator**: 多指标 `["check_audio_duration", "check_audio_fade_in", "check_audio_fade_out", "check_audio_rms_level"]`, `"conj": "and"`
- **result**: 4 个 `vm_file` → `/home/user/Documents/exports/clean_loud.wav`
- **expected**: 4 个 `rule`
  - `{"expected_duration": 14.0, "tolerance": 0.5}`
  - `{"fade_duration": 2.0, "num_windows": 5}`
  - `{"fade_duration": 2.0, "num_windows": 5}`
  - `{"min_rms_db": -30.0, "max_rms_db": -3.0}`
- **操作步骤数**: 7+

---

#### Task L3-25: Multi-Section Edit with Labels

- **ID**: `a1b00025-0025-4000-8000-000000000025`
- **Instruction**: Open /home/user/Documents/complex_sections.wav. Delete 15-18s. Add label track with labels: 'Part1' at 0.0s, 'Gap' at 7.0s, 'End' at 14.0s. Export as WAV and save project as .aup3.
- **Upload Assets**: `complex_sections.wav` → `/home/user/Documents/complex_sections.wav`
- **Evaluator**: 多指标 `["check_audio_duration", "check_aup3_labels"]`, `"conj": "and"`
- **result**: 2 个 getter（1 个 `vm_file` WAV + 1 个 `vm_file` .aup3）
- **expected**: 2 个 `rule`
  - `{"expected_duration": 17.0, "tolerance": 1.0}`
  - `{"expected_labels": [{"time": 0.0, "text": "Part1"}, {"time": 7.0, "text": "Gap"}, {"time": 14.0, "text": "End"}], "time_tolerance": 2.0}`
- **操作步骤数**: 6+

---

#### Task L3-43: 3-Track with Gains + Mute + Labels

- **ID**: `a1b00043-0043-4000-8000-000000000043`
- **Instruction**: Open vocals.wav, import drums.wav and bass.wav. Set gains: vocals 0 dB, drums -4 dB, bass -2 dB. Mute drums. Add labels: 'Start' at 0.0s, 'Middle' at 15.0s. Save as production.aup3.
- **Upload Assets**: `vocals.wav`, `drums.wav`, `bass.wav` → `/home/user/Documents/`
- **Evaluator**: 多指标 `["check_aup3_track_count", "check_aup3_track_mute", "check_aup3_labels", "check_aup3_track_gain", "check_aup3_track_gain"]`, `"conj": "and"`
- **result**: 5 个 `vm_file` → `/home/user/Documents/production.aup3`
- **expected**: 5 个 `rule`
  - `{"expected_track_count": 4}`
  - `{"track_index": 1, "expected_mute": true}`
  - `{"expected_labels": [{"time": 0.0, "text": "Start"}, {"time": 15.0, "text": "Middle"}], "time_tolerance": 1.0}`
  - `{"track_index": 1, "expected_gain_db": -4.0, "tolerance": 2.0}`
  - `{"track_index": 2, "expected_gain_db": -2.0, "tolerance": 2.0}`
- **操作步骤数**: 8+

---

#### Task L3-44: Trim + Delete + Silence + Fade-in

- **ID**: `a1b00044-0044-4000-8000-000000000044`
- **Instruction**: Open long_test.wav. Trim to first 30s. Delete 10-15s. Insert 3s silence at 10s. Apply fade-in (first 3s). Export as WAV. Save the project.
- **Upload Assets**: `long_test.wav` → `/home/user/Documents/long_test.wav`
- **Evaluator**: 多指标 `["check_audio_duration", "check_audio_silence_at", "check_audio_fade_in"]`, `"conj": "and"`
- **result**: 3 个 `vm_file`
- **expected**: 3 个 `rule`
- **操作步骤数**: 6+

---

#### Task L3-45: Multi-Track Mixdown with Fades

- **ID**: `a1b00045-0045-4000-8000-000000000045`
- **Instruction**: Open vocals.wav, import drums.wav. Apply fade-in (first 3s) and fade-out (last 3s) on vocals. Mix and export as mono WAV. Save the project.
- **Upload Assets**: `vocals.wav`, `drums.wav` → `/home/user/Documents/`
- **Evaluator**: 多指标 `["check_audio_channels", "check_audio_duration", "check_audio_fade_in", "check_audio_fade_out"]`, `"conj": "and"`
- **result**: 4 个 `vm_file`
- **expected**: 4 个 `rule`
- **操作步骤数**: 7+

---

#### Task L3-46: Section Edit + Labels + Dual Save

- **ID**: `a1b00046-0046-4000-8000-000000000046`
- **Instruction**: Open complex_sections.wav. Delete 0-5s, delete another section. Add labels. Export WAV + save .aup3.
- **Upload Assets**: `complex_sections.wav` → `/home/user/Documents/complex_sections.wav`
- **Evaluator**: 多指标 `["check_audio_duration", "check_aup3_labels", "check_aup3_track_count"]`, `"conj": "and"`
- **result**: 3 个 getter（WAV + .aup3）
- **expected**: 3 个 `rule`
- **操作步骤数**: 7+

---

#### Task L3-47: Normalize + Trim + Resample + Fade-out

- **ID**: `a1b00047-0047-4000-8000-000000000047`
- **Instruction**: Open edit_test.wav. Normalize, trim to 2-8s, resample to 22050 Hz, apply fade-out (last 2s). Export WAV. Save the project.
- **Upload Assets**: `edit_test.wav` → `/home/user/Documents/edit_test.wav`
- **Evaluator**: 多指标 `["check_audio_duration", "check_audio_sample_rate", "check_audio_fade_out"]`, `"conj": "and"`
- **result**: 3 个 `vm_file`
- **expected**: 3 个 `rule`
- **操作步骤数**: 5+

---

#### Task L3-48: 4-Track Project with Gains + Labels

- **ID**: `a1b00048-0048-4000-8000-000000000048`
- **Instruction**: Open vocals.wav, import drums.wav, bass.wav, and a generated tone track. Set gains for tracks. Add labels. Save as .aup3.
- **Upload Assets**: `vocals.wav`, `drums.wav`, `bass.wav` + generated → `/home/user/Documents/`
- **Evaluator**: 多指标 `["check_aup3_track_count", "check_aup3_labels", "check_aup3_track_gain", "check_aup3_track_gain"]`, `"conj": "and"`
- **result**: 4 个 `vm_file`
- **expected**: 4 个 `rule`
- **操作步骤数**: 10+

---

#### Task L3-49: Multi-Track + Silence + Fades + Mono

- **ID**: `a1b00049-0049-4000-8000-000000000049`
- **Instruction**: Open vocals.wav, import drums.wav. Insert silence. Apply fades. Mix to mono. Export WAV. Save the project.
- **Upload Assets**: `vocals.wav`, `drums.wav` → `/home/user/Documents/`
- **Evaluator**: 多指标 `["check_audio_channels", "check_audio_duration", "check_audio_fade_in", "check_audio_fade_out"]`, `"conj": "and"`
- **result**: 4 个 `vm_file`
- **expected**: 4 个 `rule`
- **操作步骤数**: 8+

---

#### Task L3-50: Extended Edit + Fades + Labels + Dual Save

- **ID**: `a1b00050-0050-4000-8000-000000000050`
- **Instruction**: Open long_test.wav. Delete two segments. Generate 5s silence at end. Apply fade-in (first 3s) and fade-out (last 3s). Add labels: 'Begin', 'Gap', 'Silence'. Export WAV + save .aup3.
- **Upload Assets**: `long_test.wav` → `/home/user/Documents/long_test.wav`
- **Evaluator**: 多指标 `["check_audio_duration", "check_audio_fade_in", "check_audio_fade_out", "check_aup3_labels"]`, `"conj": "and"`
- **result**: 4 个 getter（3 个 WAV + 1 个 .aup3）
- **expected**: 4 个 `rule`
  - `{"expected_duration": 50.0, "tolerance": 1.5}`
  - `{"fade_duration": 3.0, "num_windows": 5}`
  - `{"fade_duration": 3.0, "num_windows": 5}`
  - `{"expected_labels": [{"time": 0.0, "text": "Begin"}, {"time": 15.0, "text": "Gap"}, {"time": 45.0, "text": "Silence"}], "time_tolerance": 2.0}`
- **操作步骤数**: 10+

---

### L3 任务汇总

| # | Task | Asset File(s) | 评估指标数 | 步骤数 | WAV/aup3 |
|---|------|--------------|-----------|--------|----------|
| 21 | Multi-Track Mixdown | vocals + drums + bass | 2 | 5+ | WAV |
| 22 | Multi-Track + Labels + Gains | vocals + drums + bass | 5 | 8+ | .aup3 |
| 23 | Delete + Silence + Fades | long_test | 4 | 6+ | WAV |
| 24 | Noise Reduce + Amplify + Fades | noisy_recording | 4 | 7+ | WAV |
| 25 | Section Edit + Labels | complex_sections | 2 | 6+ | WAV + .aup3 |
| 43 | 3-Track + Gains + Mute + Labels | vocals + drums + bass | 5 | 8+ | .aup3 |
| 44 | Trim + Delete + Silence + Fade | long_test | 3 | 6+ | WAV |
| 45 | Multi-Track Mixdown + Fades | vocals + drums | 4 | 7+ | WAV |
| 46 | Section Edit + Labels + Dual Save | complex_sections | 3 | 7+ | WAV + .aup3 |
| 47 | Normalize + Trim + Resample + Fade | edit_test | 3 | 5+ | WAV |
| 48 | 4-Track + Gains + Labels | vocals + drums + bass | 4 | 10+ | .aup3 |
| 49 | Multi-Track + Fades + Mono | vocals + drums | 4 | 8+ | WAV |
| 50 | Extended Edit + Fades + Labels | long_test | 4 | 10+ | WAV + .aup3 |

**L3 统计**:
- 总任务数: **13**
- 需要新评估函数: **0** 个
- 平均操作步骤: **7+** 步/任务
- 平均评估指标: **3.6** 个/任务
- 同时使用 WAV + .aup3 验证: **3** 个任务

---

## 4. 评估函数汇总

File: `desktop_env/evaluators/metrics/audacity.py`

| # | Function Name | Category | Description | Complexity |
|---|--------------|----------|-------------|------------|
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
| 14 | `check_aup3_track_gain` | .aup3 | 验证轨道增益 (dB) | 中 |
| 15 | `check_aup3_track_mute` | .aup3 | 验证轨道静音状态 | 低 |
| 16 | `check_aup3_labels` | .aup3 | 验证标签时间和文本 | 中 |

**总计**: 16 个评估函数，覆盖 50 个任务（18 L1 + 19 L2 + 13 L3）。全部已实现，无需新增。

---

## 5. 素材生成说明

所有音频素材使用 Python + NumPy + SciPy 生成，位于 `assets/audacity/audio/` 目录。

### 技术规格

| Property | Value |
|----------|-------|
| Sample Rate | 44100 Hz |
| Bit Depth | 16-bit PCM |
| Channels | Mono (除 stereo_test.wav 为 Stereo) |
| Format | WAV |
| Total Files | 27 |
| Total Size | ~30 MB |

### 频率范围

| Range | Value |
|-------|-------|
| Minimum | 80 Hz (bass.wav) |
| Maximum | 3200 Hz (analysis_test harmonics) |
| Most Common | 390-530 Hz |

### 持续时间范围

| Range | Value |
|-------|-------|
| Shortest | 3 seconds (short_test.wav) |
| Longest | 60 seconds (long_test.wav) |
| Most Common | 10-20 seconds |

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

| Level | Count | 平均步骤 | Description | Examples |
|-------|-------|---------|-------------|---------|
| L1 | 18 | 1 步 | 单步原子操作 | 导入/导出 WAV、删除段、修剪、淡入/淡出、放大、生成静音、重采样、拆分立体声 |
| L2 | 19 | 3-4 步 | 多步复合操作 | 删除 + 淡出、放大 + 淡入淡出、降噪 + 导出、多轨 + 增益、标签管理、修剪 + 重采样 |
| L3 | 13 | 7+ 步 | 复杂工作流 | 多轨混音 + 标签 + 增益、多段编辑 + 静音 + 淡入淡出、降噪 + 放大 + 淡入淡出、多轨 + 静音 + 标签 + 双格式保存 |
| **Total** | **50** | | | |

### 可验证性保证

所有任务的验证基于以下两种可靠机制：

1. **WAV 文件分析**：使用 Python `wave` 模块读取标准 WAV 格式，通过 `struct` 解析样本数据。验证时长、采样率、声道、RMS 音量、淡入/淡出趋势、静音/有声区域等客观指标。

2. **`.aup3` SQLite 解析**：Audacity 3.x 项目文件为 SQLite 数据库，通过 `sqlite3` 读取 `project` 表中的 XML 元数据，解析轨道数量、增益、静音状态、标签位置和文本等项目级信息。

**不依赖**截图对比、OCR 或其他不可靠的视觉检查方法。全部使用 Python 标准库，无第三方依赖。

---

## 9. Common Pitfalls

### .aup3 解析注意事项

- **XML 命名空间**：Audacity .aup3 中的项目 XML 可能包含命名空间前缀，解析时需要处理 `{namespace}tag` 格式。
- **Gain 存储格式**：.aup3 中 gain 以线性倍率存储（如 0.5 对应 -6dB），需转换为 dB 进行比较。
- **Mute 存储格式**：存储为字符串 `"0"` 或 `"1"`，需转换为布尔值。
- **Label 标签名**：不同 Audacity 版本可能使用 `<label>` 或 `<Label>`，时间属性可能为 `t` 或 `t0`。

### WAV 分析注意事项

- **采样宽度**：需支持 8/16/24/32-bit 格式，每种格式的归一化系数不同。
- **淡入/淡出检测**：基于窗口化 RMS 趋势，允许少量非单调（tolerance: `num_windows - 2` 个递增/递减即可通过）。
- **多声道处理**：分析前先混合为单声道（各声道取平均）。
- **时间精度**：时长比较默认容差 0.5s，标签时间比较默认容差 1.0s。

### Task JSON 常见问题

- **exports 目录**：WAV 导出路径通常为 `/home/user/Documents/exports/`，需确保目录在评测前存在或由 Agent 创建。
- **双格式保存**：部分 L3 任务同时需要导出 WAV 和保存 .aup3，两个文件路径都需要在 evaluator 中指定。
- **生成音频任务**：Task L1-29 不打开现有文件，而是从空项目开始，config 中无 `upload_file`。
