# Kdenlive Task Design Document

## 1. Available Resources

All resource files are located at: `assets/kdenlive/`

### 1.1 Video Files

| Filename | Resolution | FPS | Size | Description |
|----------|-----------|-----|------|-------------|
| `6533277-hd_1920_1080_24fps.mp4` | 1920×1080 | 24 | 4.73 MB | Standard HD landscape |
| `13590137_3840_2160_60fps.mp4` | 3840×2160 | 60 | 32.23 MB | 4K landscape |
| `13739698_1080_1920_30fps.mp4` | 1080×1920 | 30 | 13.95 MB | HD portrait |
| `14307439_1920_1080_60fps.mp4` | 1920×1080 | 60 | 7.40 MB | HD landscape 60fps |
| `15363990_2160_3840_30fps.mp4` | 2160×3840 | 30 | 12.50 MB | 4K portrait |
| `15368811_1920_1080_30fps.mp4` | 1920×1080 | 30 | 8.22 MB | HD landscape 30fps |
| `15401579_2160_3650_15fps.mp4` | 2160×3650 | 15 | 13.48 MB | Non-standard aspect ratio |
| `15449119_2160_3840_60fps.mp4` | 2160×3840 | 60 | 21.12 MB | 4K portrait 60fps |

### 1.2 Audio Files (MP3)

| Filename | Size |
|----------|------|
| `2de4019d3e239361315947bb82ca828c.mp3` | 1.58 MB |
| `6ec8ccb72e97ef2a98aa92d0f231b36f.mp3` | 3.17 MB |
| `77848f98a135c05bbfc8ceb62cea6fca.mp3` | 3.27 MB |
| `804c6281f9d23fa77df71776a6cca3c2.mp3` | 4.46 MB |
| `98f73cb483a429d5edf2313da9077769.mp3` | 2.59 MB |
| `f88f7fdbb6b72e3fc1e2a10078b99b18.mp3` | 2.88 MB |

### 1.3 Sound Effect Files (WAV)

| Filename | Size |
|----------|------|
| `mixkit-arcade-retro-game-over-213.wav` | 287.82 KB |
| `mixkit-classic-alarm-995.wav` | 865.83 KB |
| `mixkit-crickets-and-insects-in-the-wild-ambience-39.wav` | 4.38 MB |
| `mixkit-dog-barking-twice-1.wav` | 279.62 KB |
| `mixkit-fast-rocket-whoosh-1714.wav` | 1.20 MB |
| `mixkit-fast-small-sweep-transition-166.wav` | 135.49 KB |

---

## 2. Existing Evaluator Functions

File: `desktop_env/evaluators/metrics/kdenlive.py`

| Function | Description | result Type | expected Type |
|----------|-------------|-------------|---------------|
| `check_kdenlive_import_video` | Verify video imported into project bin by checking `<producer>` resource | `vm_file` (.kdenlive) | `rule` → `{"expected_file": "xxx.mp4"}` |
| `check_kdenlive_add_to_timeline` | Verify clip placed on timeline track by checking `<playlist>` entries | `vm_file` (.kdenlive) | `rule` → `{"expected_file": "xxx.mp4"}` |
| `check_kdenlive_grayscale_effect` | Verify grayscale effect applied by checking `<filter>` mlt_service | `vm_file` (.kdenlive) | `rule` → `{}` (can be empty) |
| `check_kdenlive_volume_adjustment` | Verify audio volume adjusted to target level | `vm_file` (.kdenlive) | `rule` → `{"expected_volume": 0.5, "tolerance": 0.05}` |
| `check_kdenlive_render_mp4` | Verify MP4 render output using ffprobe (codec, duration, file size) | `vm_file` (output.mp4) | `rule` → `{"min_duration": 1.0, "expected_codec": "h264"}` |

---

## 3. Task Definitions

### 3.1 Level 1 — Basic Operations (Single-step, directly verifiable)

---

#### Task 1-1: Import Video to Project Bin

- **ID**: `a1b2c3d4-e5f6-7890-abcd-ef1234567890` (already created)
- **Instruction**: Please help me in Kdenlive: import the video file `/home/user/Videos/6533277-hd_1920_1080_24fps.mp4` into the project bin, then save the project to `/home/user/Videos/kdenlive_project.kdenlive`.
- **Upload Resources**: `6533277-hd_1920_1080_24fps.mp4` → `/home/user/Videos/`
- **Evaluator**: `check_kdenlive_import_video` (existing)
- **result**: `vm_file` → `/home/user/Videos/kdenlive_project.kdenlive`
- **expected**: `rule` → `{"expected_file": "6533277-hd_1920_1080_24fps.mp4"}`
- **New Evaluator Required**: ❌

---

#### Task 1-3: Add Video Clip to Timeline

- **Instruction**: Please help me in Kdenlive: import `/home/user/Videos/6533277-hd_1920_1080_24fps.mp4` into the project bin, drag it to the timeline track V1, then save the project to `/home/user/Videos/project.kdenlive`.
- **Upload Resources**: `6533277-hd_1920_1080_24fps.mp4` → `/home/user/Videos/`
- **Evaluator**: `check_kdenlive_add_to_timeline` (existing)
- **result**: `vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**: `rule` → `{"expected_file": "6533277-hd_1920_1080_24fps.mp4"}`
- **New Evaluator Required**: ❌

---

#### Task 1-4: Set Project Resolution

- **Instruction**: Please help me in Kdenlive: create a new project with resolution 1920×1080, then save the project to `/home/user/Videos/project.kdenlive`.
- **Upload Resources**: None
- **Evaluator**: `check_kdenlive_project_profile` (**NEW**)
- **result**: `vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**: `rule` → `{"width": 1920, "height": 1080}`
- **New Evaluator Required**: ✅

---

#### Task 1-5: Import Multiple Files to Project Bin

- **Instruction**: Please help me in Kdenlive: import two video files `/home/user/Videos/6533277-hd_1920_1080_24fps.mp4` and `/home/user/Videos/15368811_1920_1080_30fps.mp4` into the project bin, then save the project to `/home/user/Videos/project.kdenlive`.
- **Upload Resources**: `6533277-hd_1920_1080_24fps.mp4` + `15368811_1920_1080_30fps.mp4` → `/home/user/Videos/`
- **Evaluator**: `check_kdenlive_import_multiple_files` (**NEW**)
  - Iterate all `<producer>` nodes and check that **all** expected files exist
- **result**: `vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**: `rule` → `{"expected_files": ["6533277-hd_1920_1080_24fps.mp4", "15368811_1920_1080_30fps.mp4"]}`
- **New Evaluator Required**: ✅

---

#### Task 1-7: Set Project Frame Rate

- **Instruction**: Please help me in Kdenlive: create a new project with frame rate 30fps, then save the project to `/home/user/Videos/project.kdenlive`.
- **Upload Resources**: None
- **Evaluator**: `check_kdenlive_project_profile` (reuse — check `frame_rate_num`/`frame_rate_den` in `<profile>`)
- **result**: `vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**: `rule` → `{"frame_rate_num": 30, "frame_rate_den": 1}`
- **New Evaluator Required**: ❌ (extend existing `check_kdenlive_project_profile`)

---

#### Task 1-8: Save Project with Specific Name

- **Instruction**: Please help me in Kdenlive: create a new project and save it as `/home/user/Videos/my_first_project.kdenlive`.
- **Upload Resources**: None
- **Evaluator**: `check_kdenlive_file_exists` (**NEW**)
  - Simply check that the file exists at the specified path and is a valid MLT XML
- **result**: `vm_file` → `/home/user/Videos/my_first_project.kdenlive`
- **expected**: `rule` → `{"valid_xml": true}`
- **New Evaluator Required**: ✅

---

#### Task 1-9: Delete a Clip from Project Bin

- **Instruction**: Please help me in Kdenlive: import two video files `/home/user/Videos/6533277-hd_1920_1080_24fps.mp4` and `/home/user/Videos/15368811_1920_1080_30fps.mp4` into the project bin, then delete `15368811_1920_1080_30fps.mp4` from the bin, and save the project to `/home/user/Videos/project.kdenlive`.
- **Upload Resources**: `6533277-hd_1920_1080_24fps.mp4` + `15368811_1920_1080_30fps.mp4` → `/home/user/Videos/`
- **Evaluator**: `check_kdenlive_bin_content` (**NEW**)
  - Verify that `expected_present` files exist in bin AND `expected_absent` files do NOT exist
- **result**: `vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**: `rule` → `{"expected_present": ["6533277-hd_1920_1080_24fps.mp4"], "expected_absent": ["15368811_1920_1080_30fps.mp4"]}`
- **New Evaluator Required**: ✅

---

#### Task 1-10: Rename a Clip in Project Bin

- **Instruction**: Please help me in Kdenlive: import `/home/user/Videos/6533277-hd_1920_1080_24fps.mp4` into the project bin, rename the clip to "Main Video" in the bin, then save the project to `/home/user/Videos/project.kdenlive`.
- **Upload Resources**: `6533277-hd_1920_1080_24fps.mp4` → `/home/user/Videos/`
- **Evaluator**: `check_kdenlive_clip_name` (**NEW**)
  - Check `<property name="kdenlive:clipname">` in the matching `<producer>` node
- **result**: `vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**: `rule` → `{"source_file": "6533277-hd_1920_1080_24fps.mp4", "expected_name": "Main Video"}`
- **New Evaluator Required**: ✅

---

#### Task 1-11: Create a Folder in Project Bin

- **Instruction**: Please help me in Kdenlive: create a new folder named "Footage" in the project bin, then save the project to `/home/user/Videos/project.kdenlive`.
- **Upload Resources**: None
- **Evaluator**: `check_kdenlive_bin_folder` (**NEW**)
  - Check `<property name="kdenlive:folderName">` or `<kdenlive_folder>` elements in the project XML
- **result**: `vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**: `rule` → `{"expected_folder": "Footage"}`
- **New Evaluator Required**: ✅

---

#### Task 1-12: Add a Video Track

- **Instruction**: Please help me in Kdenlive: add a new video track to the timeline (so there are at least 3 video tracks), then save the project to `/home/user/Videos/project.kdenlive`.
- **Upload Resources**: None
- **Evaluator**: `check_kdenlive_track_count` (**NEW**)
  - Count `<playlist>` or `<track>` elements in the main `<tractor>` that correspond to video tracks
- **result**: `vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**: `rule` → `{"min_video_tracks": 3}`
- **New Evaluator Required**: ✅

---

#### Task 1-14: Delete a Track from Timeline

- **Instruction**: Please help me in Kdenlive: delete one video track from the timeline so that only 1 video track remains, then save the project to `/home/user/Videos/project.kdenlive`.
- **Upload Resources**: None
- **Evaluator**: `check_kdenlive_track_count` (reuse — verify exact count)
- **result**: `vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**: `rule` → `{"exact_video_tracks": 1}`
- **New Evaluator Required**: ❌ (reuse `check_kdenlive_track_count`)

---

#### Task 1-15: Set Timeline Zoom Level via Guide/Marker

- **Instruction**: Please help me in Kdenlive: add a guide marker at position 00:00:05:00 (5 seconds) with the label "Scene Start" in the timeline, then save the project to `/home/user/Videos/project.kdenlive`.
- **Upload Resources**: None
- **Evaluator**: `check_kdenlive_guide` (**NEW**)
  - Parse `<property name="kdenlive:docproperties.guides">` JSON array for guide with matching time and comment
- **result**: `vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**: `rule` → `{"guide_comment": "Scene Start", "guide_time_seconds": 5.0, "tolerance": 0.5}`
- **New Evaluator Required**: ✅

---

#### Task 1-16: Mute a Track

- **Instruction**: Please help me in Kdenlive: import `/home/user/Videos/6533277-hd_1920_1080_24fps.mp4` into the project bin, add it to the timeline, then mute the video track V1, and save the project to `/home/user/Videos/project.kdenlive`.
- **Upload Resources**: `6533277-hd_1920_1080_24fps.mp4` → `/home/user/Videos/`
- **Evaluator**: `check_kdenlive_track_mute` (**NEW**)
  - Check track properties in `<tractor>` for `hide` attribute or `kdenlive:track_muted` property
- **result**: `vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**: `rule` → `{"muted_track": "V1"}`
- **New Evaluator Required**: ✅

---

#### Task 1-17: Lock a Track

- **Instruction**: Please help me in Kdenlive: lock the video track V1 in the timeline, then save the project to `/home/user/Videos/project.kdenlive`.
- **Upload Resources**: None
- **Evaluator**: `check_kdenlive_track_lock` (**NEW**)
  - Check track `<property name="kdenlive:locked_track">` value
- **result**: `vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**: `rule` → `{"locked_track": "V1"}`
- **New Evaluator Required**: ✅

---

#### Task 1-18: Undo Last Operation

- **Instruction**: Please help me in Kdenlive: import `/home/user/Videos/6533277-hd_1920_1080_24fps.mp4` into the project bin, add it to the timeline on V1, then undo the last action (removing it from the timeline), and save the project to `/home/user/Videos/project.kdenlive`.
- **Upload Resources**: `6533277-hd_1920_1080_24fps.mp4` → `/home/user/Videos/`
- **Evaluator**: `check_kdenlive_timeline_empty` (**NEW**)
  - Verify that the clip is in the bin (`<producer>` exists) but NOT on the timeline (no `<entry>` referencing it)
- **result**: `vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**: `rule` → `{"expected_in_bin": "6533277-hd_1920_1080_24fps.mp4", "expected_not_on_timeline": true}`
- **New Evaluator Required**: ✅

---

#### Task 1-19: Create Color Clip

- **Instruction**: Please help me in Kdenlive: create a color clip with the color red (#FF0000) in the project bin, then save the project to `/home/user/Videos/project.kdenlive`.
- **Upload Resources**: None
- **Evaluator**: `check_kdenlive_color_clip` (**NEW**)
  - Search for `<producer>` with `mlt_service="color"` and check `resource` property for color value
- **result**: `vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**: `rule` → `{"expected_color": "#FF0000"}`
- **New Evaluator Required**: ✅

---

#### Task 1-20: Set Clip Duration (Color/Title Clip)

- **Instruction**: Please help me in Kdenlive: create a color clip in the project bin, set its default duration to 10 seconds, then save the project to `/home/user/Videos/project.kdenlive`.
- **Upload Resources**: None
- **Evaluator**: `check_kdenlive_clip_duration` (**NEW**)
  - Check `length` or `out` property of the color producer, convert frames to seconds
- **result**: `vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**: `rule` → `{"min_duration_seconds": 9.5, "max_duration_seconds": 10.5}`
- **New Evaluator Required**: ✅

---

#### Task 1-21: Create Image Sequence / Slideshow Clip

- **Instruction**: Please help me in Kdenlive: import the video file `/home/user/Videos/15368811_1920_1080_30fps.mp4` into the project bin, then use "Extract Frame" or the clip monitor to take a snapshot and save it, then save the project to `/home/user/Videos/project.kdenlive`.
- **Upload Resources**: `15368811_1920_1080_30fps.mp4` → `/home/user/Videos/`
- **Evaluator**: `check_kdenlive_snapshot_exists` (**NEW**)
  - Use `vm_command_line` to check if a snapshot image file exists in the expected directory
- **result**: `vm_command_line` → `ls /home/user/Videos/*.png 2>/dev/null | wc -l`
- **expected**: `rule` → `{"min_count": 1}`
- **New Evaluator Required**: ✅

---

#### Task 1-22: Enable/Disable Proxy Clips

- **Instruction**: Please help me in Kdenlive: open the project settings and enable proxy clips for the current project, then save the project to `/home/user/Videos/project.kdenlive`.
- **Upload Resources**: None
- **Evaluator**: `check_kdenlive_proxy_setting` (**NEW**)
  - Check `<property name="kdenlive:docproperties.enableproxy">` value is "1"
- **result**: `vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**: `rule` → `{"proxy_enabled": true}`
- **New Evaluator Required**: ✅

---

#### Task 1-23: Set Project Preview Resolution

- **Instruction**: Please help me in Kdenlive: open project settings and set the preview resolution to 720×480, then save the project to `/home/user/Videos/project.kdenlive`.
- **Upload Resources**: None
- **Evaluator**: `check_kdenlive_project_profile` (reuse — check preview profile properties)
- **result**: `vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**: `rule` → `{"preview_width": 720, "preview_height": 480}`
- **New Evaluator Required**: ❌ (extend existing `check_kdenlive_project_profile`)

---

#### Task 1-24: Move Clip Position on Timeline

- **Instruction**: Please help me in Kdenlive: import `/home/user/Videos/6533277-hd_1920_1080_24fps.mp4`, add it to the timeline on track V1 starting at position 00:00:05:00 (5 seconds), then save the project to `/home/user/Videos/project.kdenlive`.
- **Upload Resources**: `6533277-hd_1920_1080_24fps.mp4` → `/home/user/Videos/`
- **Evaluator**: `check_kdenlive_clip_position` (**NEW**)
  - Check `<entry>` or `<blank>` elements in the track playlist to verify clip starts at frame corresponding to 5 seconds
- **result**: `vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**: `rule` → `{"source_file": "6533277-hd_1920_1080_24fps.mp4", "start_time": 5.0, "tolerance": 0.5}`
- **New Evaluator Required**: ✅

---

### 3.2 Level 2 — Intermediate Operations (Multi-step, effects/properties modification)

---

#### Task 2-1: Apply Grayscale Effect to Video

- **Instruction**: Please help me in Kdenlive: import `/home/user/Videos/6533277-hd_1920_1080_24fps.mp4`, add it to the timeline, apply the Grayscale video effect to the clip, then save the project to `/home/user/Videos/project.kdenlive`.
- **Upload Resources**: `6533277-hd_1920_1080_24fps.mp4` → `/home/user/Videos/`
- **Evaluator**: `check_kdenlive_grayscale_effect` (existing)
- **result**: `vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**: `rule` → `{}`
- **New Evaluator Required**: ❌

---

#### Task 2-2: Adjust Audio Volume

- **Instruction**: Please help me in Kdenlive: import `/home/user/Music/98f73cb483a429d5edf2313da9077769.mp3`, add it to the timeline on track A1, set the audio volume to 50%, then save the project to `/home/user/Videos/project.kdenlive`.
- **Upload Resources**: `98f73cb483a429d5edf2313da9077769.mp3` → `/home/user/Music/`
- **Evaluator**: `check_kdenlive_volume_adjustment` (existing)
- **result**: `vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**: `rule` → `{"expected_volume": 0.5, "tolerance": 0.05}`
- **New Evaluator Required**: ❌

---

#### Task 2-3: Trim Video Clip (Set In/Out Points)

- **Instruction**: Please help me in Kdenlive: import `/home/user/Videos/14307439_1920_1080_60fps.mp4`, add it to the timeline, trim the clip so it starts at 2 seconds and ends at 8 seconds, then save the project to `/home/user/Videos/project.kdenlive`.
- **Upload Resources**: `14307439_1920_1080_60fps.mp4` → `/home/user/Videos/`
- **Evaluator**: `check_kdenlive_clip_trim` (**NEW**)
- **result**: `vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**: `rule` → `{"in_time": 2.0, "out_time": 8.0, "tolerance": 0.5, "source_file": "14307439_1920_1080_60fps.mp4"}`
- **New Evaluator Required**: ✅

---

#### Task 2-4: Add Transition Between Two Clips

- **Instruction**: Please help me in Kdenlive: import two video files `/home/user/Videos/6533277-hd_1920_1080_24fps.mp4` and `/home/user/Videos/15368811_1920_1080_30fps.mp4`, place them consecutively on the timeline, add a "Dissolve" transition between them, then save the project to `/home/user/Videos/project.kdenlive`.
- **Upload Resources**: `6533277-hd_1920_1080_24fps.mp4` + `15368811_1920_1080_30fps.mp4` → `/home/user/Videos/`
- **Evaluator**: `check_kdenlive_transition` (**NEW**)
- **result**: `vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**: `rule` → `{"transition_type": "luma"}`
- **New Evaluator Required**: ✅

---

#### Task 2-5: Add Title Text

- **Instruction**: Please help me in Kdenlive: create a new project, add a title clip with the text "Hello World" on the timeline, then save the project to `/home/user/Videos/project.kdenlive`.
- **Upload Resources**: None
- **Evaluator**: `check_kdenlive_title_text` (**NEW**)
- **result**: `vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**: `rule` → `{"expected_text": "Hello World"}`
- **New Evaluator Required**: ✅

---

#### Task 2-6: Change Clip Playback Speed

- **Instruction**: Please help me in Kdenlive: import `/home/user/Videos/6533277-hd_1920_1080_24fps.mp4`, add it to the timeline, change the clip speed to 200% (2x speed), then save the project to `/home/user/Videos/project.kdenlive`.
- **Upload Resources**: `6533277-hd_1920_1080_24fps.mp4` → `/home/user/Videos/`
- **Evaluator**: `check_kdenlive_clip_speed` (**NEW**)
- **result**: `vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**: `rule` → `{"expected_speed": 2.0, "tolerance": 0.1, "source_file": "6533277-hd_1920_1080_24fps.mp4"}`
- **New Evaluator Required**: ✅

---

#### Task 2-7: Apply Blur Effect to Video

- **Instruction**: Please help me in Kdenlive: import `/home/user/Videos/15368811_1920_1080_30fps.mp4`, add it to the timeline, apply the "Box Blur" (or "Blur") video effect to the clip, then save the project to `/home/user/Videos/project.kdenlive`.
- **Upload Resources**: `15368811_1920_1080_30fps.mp4` → `/home/user/Videos/`
- **Evaluator**: `check_kdenlive_effect_applied` (**NEW**)
  - Generic effect checker: search `<filter>` nodes for matching `mlt_service` value
- **result**: `vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**: `rule` → `{"effect_service": ["box_blur", "boxblur", "blur"], "source_file": "15368811_1920_1080_30fps.mp4"}`
- **New Evaluator Required**: ✅

---

#### Task 2-9: Rotate Video Clip 90 Degrees

- **Instruction**: Please help me in Kdenlive: import `/home/user/Videos/6533277-hd_1920_1080_24fps.mp4`, add it to the timeline, apply the "Rotate (keyframable)" or "Transform" effect and rotate the clip 90 degrees clockwise, then save the project to `/home/user/Videos/project.kdenlive`.
- **Upload Resources**: `6533277-hd_1920_1080_24fps.mp4` → `/home/user/Videos/`
- **Evaluator**: `check_kdenlive_effect_param` (**NEW**)
  - Check for `<filter>` with rotate/affine/qtblend service and verify rotation parameter value
- **result**: `vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**: `rule` → `{"effect_service": ["rotate", "affine", "qtblend"], "param_name": "rotate", "expected_value": 90, "tolerance": 5}`
- **New Evaluator Required**: ✅

---

#### Task 2-12: Add Audio Fade In and Fade Out

- **Instruction**: Please help me in Kdenlive: import `/home/user/Music/f88f7fdbb6b72e3fc1e2a10078b99b18.mp3`, add it to the timeline on track A1, apply a "Fade In" effect at the beginning (2 seconds) and a "Fade Out" effect at the end (2 seconds), then save the project to `/home/user/Videos/project.kdenlive`.
- **Upload Resources**: `f88f7fdbb6b72e3fc1e2a10078b99b18.mp3` → `/home/user/Music/`
- **Evaluator**: `check_kdenlive_audio_fade` (**NEW**)
  - Check for `volume` or `fade_from` / `fade_to` filter on the audio clip with keyframe data indicating fade
- **result**: `vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**: `rule` → `{"fade_in": true, "fade_out": true, "source_file": "f88f7fdbb6b72e3fc1e2a10078b99b18.mp3"}`
- **New Evaluator Required**: ✅

---

#### Task 2-13: Split/Cut a Clip on Timeline

- **Instruction**: Please help me in Kdenlive: import `/home/user/Videos/14307439_1920_1080_60fps.mp4`, add it to the timeline on track V1, split the clip at the 5-second mark using the Razor tool so that it becomes two separate segments, then save the project to `/home/user/Videos/project.kdenlive`.
- **Upload Resources**: `14307439_1920_1080_60fps.mp4` → `/home/user/Videos/`
- **Evaluator**: `check_kdenlive_clip_split` (**NEW**)
  - Count the number of `<entry>` elements in the track playlist that reference the same producer — after a split there should be ≥ 2 entries
- **result**: `vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**: `rule` → `{"source_file": "14307439_1920_1080_60fps.mp4", "min_segments": 2}`
- **New Evaluator Required**: ✅

---

#### Task 2-14: Create Picture-in-Picture (PiP) Composition

- **Instruction**: Please help me in Kdenlive: import two video files `/home/user/Videos/6533277-hd_1920_1080_24fps.mp4` and `/home/user/Videos/15368811_1920_1080_30fps.mp4`, place the first video on track V1 (main) and the second on track V2 (overlay), apply a "Transform" or "Position and Zoom" effect on the V2 clip to resize it to 1/4 of the screen and position it in the bottom-right corner, then save the project to `/home/user/Videos/project.kdenlive`.
- **Upload Resources**: `6533277-hd_1920_1080_24fps.mp4` + `15368811_1920_1080_30fps.mp4` → `/home/user/Videos/`
- **Evaluator**: `check_kdenlive_multi_track_composition` (**NEW**)
  - Verify both clips are on different tracks and a transform/affine effect is applied on the overlay track
- **result**: `vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**: `rule` → `{"main_file": "6533277-hd_1920_1080_24fps.mp4", "overlay_file": "15368811_1920_1080_30fps.mp4", "require_transform": true}`
- **New Evaluator Required**: ✅

---

#### Task 2-15: Copy and Paste a Clip on Timeline

- **Instruction**: Please help me in Kdenlive: import `/home/user/Videos/6533277-hd_1920_1080_24fps.mp4`, add it to the timeline on track V1, then copy the clip and paste it right after the original clip on the same track, so that the video plays twice consecutively, then save the project to `/home/user/Videos/project.kdenlive`.
- **Upload Resources**: `6533277-hd_1920_1080_24fps.mp4` → `/home/user/Videos/`
- **Evaluator**: `check_kdenlive_clip_count` (**NEW**)
  - Count the number of `<entry>` elements across all timeline playlists that reference producers containing the source file
- **result**: `vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**: `rule` → `{"source_file": "6533277-hd_1920_1080_24fps.mp4", "min_count": 2}`
- **New Evaluator Required**: ✅

---

#### Task 2-16: Group Clips on Timeline

- **Instruction**: Please help me in Kdenlive: import `/home/user/Videos/6533277-hd_1920_1080_24fps.mp4` and `/home/user/Music/mixkit-fast-rocket-whoosh-1714.wav`, add the video to track V1 and the audio to track A1, select both clips and group them together, then save the project to `/home/user/Videos/project.kdenlive`.
- **Upload Resources**: `6533277-hd_1920_1080_24fps.mp4` → `/home/user/Videos/` + `mixkit-fast-rocket-whoosh-1714.wav` → `/home/user/Music/`
- **Evaluator**: `check_kdenlive_clip_group` (**NEW**)
  - Check `<group>` or `<property name="kdenlive:group">` elements linking multiple clips together
- **result**: `vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**: `rule` → `{"min_groups": 1, "min_clips_in_group": 2}`
- **New Evaluator Required**: ✅

---

#### Task 2-17: Adjust Clip Opacity/Transparency

- **Instruction**: Please help me in Kdenlive: import `/home/user/Videos/15368811_1920_1080_30fps.mp4`, add it to the timeline, apply the "Opacity" (or use the "Transform" effect) and set the clip opacity to 50%, then save the project to `/home/user/Videos/project.kdenlive`.
- **Upload Resources**: `15368811_1920_1080_30fps.mp4` → `/home/user/Videos/`
- **Evaluator**: `check_kdenlive_effect_param` (reuse)
  - Check for opacity-related parameter in transform/qtblend/affine filter
- **result**: `vm_file` → `/home/user/Videos/project.kdenlive`
- **expected**: `rule` → `{"effect_service": ["qtblend", "affine", "frei0r.transparency"], "param_name": "opacity", "expected_value": 0.5, "tolerance": 0.1}`
- **New Evaluator Required**: ❌ (reuse `check_kdenlive_effect_param`)

---

### 3.3 Level 3 — Advanced Operations (Multi-step composition, rendering involved)

---

#### Task 3-1: Render Project as MP4

- **Instruction**: Please help me in Kdenlive: import `/home/user/Videos/6533277-hd_1920_1080_24fps.mp4`, add it to the timeline, render the project as MP4 (H.264) to `/home/user/Videos/output.mp4`, then wait for rendering to complete.
- **Upload Resources**: `6533277-hd_1920_1080_24fps.mp4` → `/home/user/Videos/`
- **Evaluator**: `check_kdenlive_render_mp4` (existing)
- **result**: `vm_file` → `/home/user/Videos/output.mp4`
- **expected**: `rule` → `{"min_duration": 1.0, "expected_codec": "h264"}`
- **New Evaluator Required**: ❌

---

#### Task 3-2: Add Background Music and Render

- **Instruction**: Please help me in Kdenlive: import video `/home/user/Videos/15368811_1920_1080_30fps.mp4` and audio `/home/user/Music/804c6281f9d23fa77df71776a6cca3c2.mp3`, place the video on track V1 and the audio on track A1, render the project to `/home/user/Videos/output.mp4`.
- **Upload Resources**: `15368811_1920_1080_30fps.mp4` → `/home/user/Videos/` + `804c6281f9d23fa77df71776a6cca3c2.mp3` → `/home/user/Music/`
- **Evaluator**: `check_kdenlive_render_with_audio` (**NEW**)
- **result**: `vm_file` → `/home/user/Videos/output.mp4`
- **expected**: `rule` → `{"min_duration": 1.0, "require_audio": true}`
- **New Evaluator Required**: ✅

---

#### Task 3-3: Multi-clip Splicing with Transitions and Render

- **Instruction**: Please help me in Kdenlive: import three video clips `/home/user/Videos/6533277-hd_1920_1080_24fps.mp4`, `/home/user/Videos/14307439_1920_1080_60fps.mp4`, and `/home/user/Videos/15368811_1920_1080_30fps.mp4`, place them consecutively on the timeline with "Dissolve" transitions between each pair, save the project to `/home/user/Videos/project.kdenlive`, then render the final project to `/home/user/Videos/output.mp4`.
- **Upload Resources**: `6533277-hd_1920_1080_24fps.mp4` + `14307439_1920_1080_60fps.mp4` + `15368811_1920_1080_30fps.mp4` → `/home/user/Videos/`
- **Evaluator**: `check_kdenlive_render_multi_clip_transition` (**NEW**)
  - Verify render output (codec, duration) + verify .kdenlive project has all 3 clips imported and a dissolve transition exists
- **result**: `vm_file` → `/home/user/Videos/output.mp4`
- **expected**: `rule` → `{"min_duration": 5.0, "expected_codec": "h264", "project_path": "/home/user/Videos/project.kdenlive", "expected_files": ["6533277-hd_1920_1080_24fps.mp4", "14307439_1920_1080_60fps.mp4", "15368811_1920_1080_30fps.mp4"], "transition_type": "luma"}`
- **New Evaluator Required**: ✅

---

#### Task 3-4: Apply Effects and Render (Comprehensive Task)

- **Instruction**: Please help me in Kdenlive: import `/home/user/Videos/13590137_3840_2160_60fps.mp4`, add it to the timeline, apply the Grayscale effect, set audio volume to 30%, save the project to `/home/user/Videos/project.kdenlive`, then render to `/home/user/Videos/output.mp4`.
- **Upload Resources**: `13590137_3840_2160_60fps.mp4` → `/home/user/Videos/`
- **Evaluator**: `check_kdenlive_render_effects_composite` (**NEW**)
  - Verify render output (codec, duration) + verify .kdenlive project has grayscale effect and volume=0.3
- **result**: `vm_file` → `/home/user/Videos/output.mp4`
- **expected**: `rule` → `{"min_duration": 1.0, "expected_codec": "h264", "project_path": "/home/user/Videos/project.kdenlive", "require_grayscale": true, "expected_volume": 0.3, "volume_tolerance": 0.05}`
- **New Evaluator Required**: ✅

---

#### Task 3-5: Title Intro + Video + Outro and Render

- **Instruction**: Please help me in Kdenlive: create a title clip with the text "Welcome to My Video" and add it to the beginning of the timeline on track V1 (approximately 3 seconds), then import `/home/user/Videos/6533277-hd_1920_1080_24fps.mp4` and place it right after the title on the same track, create another title clip with the text "Thank You" and place it after the video (approximately 3 seconds), add "Dissolve" transitions between the title and video clips, save the project to `/home/user/Videos/project.kdenlive`, then render the final project to `/home/user/Videos/output.mp4`.
- **Upload Resources**: `6533277-hd_1920_1080_24fps.mp4` → `/home/user/Videos/`
- **Evaluator**: `check_kdenlive_render_title_video_title` (**NEW**)
  - Verify render output (codec, duration ≥ 5s) + verify .kdenlive project has two title clips with expected text
- **result**: `vm_file` → `/home/user/Videos/output.mp4`
- **expected**: `rule` → `{"min_duration": 5.0, "expected_codec": "h264", "project_path": "/home/user/Videos/project.kdenlive", "expected_titles": ["Welcome to My Video", "Thank You"]}`
- **New Evaluator Required**: ✅

---

#### Task 3-6: Speed Ramp Video and Render

- **Instruction**: Please help me in Kdenlive: import `/home/user/Videos/14307439_1920_1080_60fps.mp4`, add it to the timeline, split the clip at the 3-second mark, change the second segment's playback speed to 300% (3x fast), save the project to `/home/user/Videos/project.kdenlive`, then render the project to `/home/user/Videos/output.mp4`.
- **Upload Resources**: `14307439_1920_1080_60fps.mp4` → `/home/user/Videos/`
- **Evaluator**: `check_kdenlive_render_speed_ramp` (**NEW**)
  - Verify render output (codec, duration) + verify .kdenlive project has clip split (≥2 segments) and speed change (3.0x)
- **result**: `vm_file` → `/home/user/Videos/output.mp4`
- **expected**: `rule` → `{"min_duration": 2.0, "expected_codec": "h264", "project_path": "/home/user/Videos/project.kdenlive", "source_file": "14307439_1920_1080_60fps.mp4", "min_segments": 2, "expected_speed": 3.0, "speed_tolerance": 0.1}`
- **New Evaluator Required**: ✅

---

#### Task 3-7: Picture-in-Picture Composition and Render

- **Instruction**: Please help me in Kdenlive: import two video files `/home/user/Videos/15368811_1920_1080_30fps.mp4` and `/home/user/Videos/6533277-hd_1920_1080_24fps.mp4`, place the first video on track V1 (main background) and the second on track V2 (overlay), apply a "Transform" or "Position and Zoom" effect on the V2 clip to resize it to 1/4 of the screen and position it in the top-left corner, save the project to `/home/user/Videos/project.kdenlive`, then render the project to `/home/user/Videos/output.mp4`.
- **Upload Resources**: `15368811_1920_1080_30fps.mp4` + `6533277-hd_1920_1080_24fps.mp4` → `/home/user/Videos/`
- **Evaluator**: `check_kdenlive_render_pip` (**NEW**)
  - Verify render output (codec, duration) + verify .kdenlive project has two clips on different tracks with transform effect
- **result**: `vm_file` → `/home/user/Videos/output.mp4`
- **expected**: `rule` → `{"min_duration": 1.0, "expected_codec": "h264", "project_path": "/home/user/Videos/project.kdenlive", "main_file": "15368811_1920_1080_30fps.mp4", "overlay_file": "6533277-hd_1920_1080_24fps.mp4", "require_transform": true}`
- **New Evaluator Required**: ✅

---

#### Task 3-8: Audio Mixing with Multiple Tracks and Render

- **Instruction**: Please help me in Kdenlive: import video `/home/user/Videos/15368811_1920_1080_30fps.mp4`, import two audio files `/home/user/Music/98f73cb483a429d5edf2313da9077769.mp3` (background music) and `/home/user/Music/mixkit-fast-rocket-whoosh-1714.wav` (sound effect), place the video on V1, the background music on track A1 with volume set to 40%, place the sound effect on track A2 starting at the 2-second mark, save the project to `/home/user/Videos/project.kdenlive`, then render the project to `/home/user/Videos/output.mp4`.
- **Upload Resources**: `15368811_1920_1080_30fps.mp4` → `/home/user/Videos/` + `98f73cb483a429d5edf2313da9077769.mp3` + `mixkit-fast-rocket-whoosh-1714.wav` → `/home/user/Music/`
- **Evaluator**: `check_kdenlive_render_audio_mix` (**NEW**)
  - Verify render output (codec, duration, has audio stream) + verify .kdenlive project has volume=0.4 on BGM and sound effect clip is present
- **result**: `vm_file` → `/home/user/Videos/output.mp4`
- **expected**: `rule` → `{"min_duration": 1.0, "expected_codec": "h264", "project_path": "/home/user/Videos/project.kdenlive", "require_audio": true, "expected_volume": 0.4, "volume_tolerance": 0.05, "expected_audio_files": ["98f73cb483a429d5edf2313da9077769.mp3", "mixkit-fast-rocket-whoosh-1714.wav"]}`
- **New Evaluator Required**: ✅

---

#### Task 3-9: Color Grading Pipeline and Render

- **Instruction**: Please help me in Kdenlive: import `/home/user/Videos/6533277-hd_1920_1080_24fps.mp4`, add it to the timeline, apply the following effects in order: (1) "Brightness" effect to increase brightness, (2) "Sepia" effect for a vintage look, then add an audio fade-in of 2 seconds at the beginning and an audio fade-out of 2 seconds at the end, save the project to `/home/user/Videos/project.kdenlive`, then render the project to `/home/user/Videos/output.mp4`.
- **Upload Resources**: `6533277-hd_1920_1080_24fps.mp4` → `/home/user/Videos/`
- **Evaluator**: `check_kdenlive_render_color_grading` (**NEW**)
  - Verify render output (codec, duration) + verify .kdenlive project has brightness effect, sepia effect, and audio fade in/out
- **result**: `vm_file` → `/home/user/Videos/output.mp4`
- **expected**: `rule` → `{"min_duration": 1.0, "expected_codec": "h264", "project_path": "/home/user/Videos/project.kdenlive", "require_brightness": true, "require_sepia": true, "require_fade_in": true, "require_fade_out": true}`
- **New Evaluator Required**: ✅

---

#### Task 3-10: Render Project as Custom Resolution MP4

- **Instruction**: Please help me in Kdenlive: import `/home/user/Videos/13590137_3840_2160_60fps.mp4`, add it to the timeline, change the project resolution to 1280×720, then render the project to `/home/user/Videos/output.mp4` in MP4 (H.264) format at 1280×720 resolution.
- **Upload Resources**: `13590137_3840_2160_60fps.mp4` → `/home/user/Videos/`
- **Evaluator**: `check_kdenlive_render_custom_resolution` (**NEW**)
  - Use ffprobe to verify output file has correct resolution, codec, and duration
- **result**: `vm_file` → `/home/user/Videos/output.mp4`
- **expected**: `rule` → `{"min_duration": 1.0, "expected_codec": "h264", "expected_width": 1280, "expected_height": 720}`
- **New Evaluator Required**: ✅

---

## 4. New Evaluator Functions Specification

> **Note**: Section 4.1–4.6 are from the original design. Section 4.7–4.18 are newly added for the expanded Level 1 tasks.

### 4.1 `check_kdenlive_project_profile`

**Purpose**: Verify project resolution/frame rate settings.

**Validation Logic**:
- Parse `.kdenlive` file (MLT XML format)
- Find `<profile>` element and check `width`, `height` attributes
- Compare with expected values

```python
def check_kdenlive_project_profile(project_file_path, rule):
    """
    Args:
        project_file_path: Path to .kdenlive project file
        rule: {"width": 1920, "height": 1080}
    Returns:
        float: 1.0 if resolution matches, 0.0 otherwise
    """
    # Parse <profile width="..." height="..."> node
    # Verify width and height match expected values
```

---

### 4.2 `check_kdenlive_clip_trim`

**Purpose**: Verify clip in/out point trimming.

**Validation Logic**:
- Find the producer matching `source_file` to get its frame rate
- Find timeline `<entry>` referencing that producer
- Read `in` and `out` attributes (frame numbers)
- Convert to seconds using frame rate
- Compare with expected `in_time`/`out_time` within `tolerance`

```python
def check_kdenlive_clip_trim(project_file_path, rule):
    """
    Args:
        project_file_path: Path to .kdenlive project file
        rule: {"in_time": 2.0, "out_time": 8.0, "tolerance": 0.5, "source_file": "xxx.mp4"}
    Returns:
        float: 1.0 if trim points match, 0.0 otherwise
    """
    # Find source_file's producer → get fps from frame_rate_num/frame_rate_den
    # Find timeline entry → read in/out attributes (frame count)
    # Convert frames to seconds: time = frame / fps
    # Compare with expected in_time/out_time ± tolerance
```

---

### 4.3 `check_kdenlive_transition`

**Purpose**: Verify transition effect exists between clips.

**Validation Logic**:
- Search for `<transition>` or `<link>` nodes in the project XML
- Check `mlt_service` attribute against expected `transition_type`
- For "Dissolve", the MLT service is `luma`

```python
def check_kdenlive_transition(project_file_path, rule):
    """
    Args:
        project_file_path: Path to .kdenlive project file
        rule: {"transition_type": "luma"}
    Returns:
        float: 1.0 if matching transition found, 0.0 otherwise
    """
    # Iterate <transition> and <link> nodes
    # Check mlt_service matches transition_type
```

---

### 4.4 `check_kdenlive_title_text`

**Purpose**: Verify title clip contains expected text.

**Validation Logic**:
- Find `<producer>` with `mlt_service="kdenlivetitle"`
- Extract `xmldata` property (contains SVG/XML title definition)
- Parse the SVG XML to find text content
- Check if expected text is present

```python
def check_kdenlive_title_text(project_file_path, rule):
    """
    Args:
        project_file_path: Path to .kdenlive project file
        rule: {"expected_text": "Hello World"}
    Returns:
        float: 1.0 if title text matches, 0.0 otherwise
    """
    # Find producer with mlt_service="kdenlivetitle"
    # Parse xmldata property (SVG XML)
    # Check text content contains expected_text
```

---

### 4.5 `check_kdenlive_clip_speed`

**Purpose**: Verify clip playback speed modification.

**Validation Logic**:
- Find the producer/chain matching `source_file`
- Check for `warp_speed` property or `timewarp` link service
- Compare speed value with expected value within tolerance

```python
def check_kdenlive_clip_speed(project_file_path, rule):
    """
    Args:
        project_file_path: Path to .kdenlive project file
        rule: {"expected_speed": 2.0, "tolerance": 0.1, "source_file": "xxx.mp4"}
    Returns:
        float: 1.0 if speed matches, 0.0 otherwise
    """
    # Find source_file's chain/producer
    # Check warp_speed property or timewarp link speed parameter
    # Compare with expected_speed ± tolerance
```

---

### 4.6 `check_kdenlive_render_with_audio`

**Purpose**: Verify rendered output contains both video and audio streams.

**Validation Logic**:
- Use ffprobe to inspect the output file
- Verify both video stream and audio stream exist
- Check duration meets minimum requirement

```python
def check_kdenlive_render_with_audio(result_file_path, rule):
    """
    Args:
        result_file_path: Path to rendered MP4 file
        rule: {"min_duration": 1.0, "require_audio": true}
    Returns:
        float: 1.0 if both video and audio streams exist with sufficient duration, 0.0 otherwise
    """
    # Use ffprobe to check output file
    # Verify video stream exists
    # Verify audio stream exists (if require_audio is true)
    # Verify duration >= min_duration
```

### 4.7 `check_kdenlive_import_multiple_files`

**Purpose**: Verify that ALL expected files are imported into project bin.

```python
def check_kdenlive_import_multiple_files(project_file_path, rule):
    """
    Args:
        project_file_path: Path to .kdenlive project file
        rule: {"expected_files": ["file1.mp4", "file2.mp4"]}
    Returns:
        float: 1.0 if ALL expected files found in producers, 0.0 otherwise
    """
    # Collect all <producer> resource values
    # Check each expected_file is present in at least one resource
    # Return 1.0 only if ALL files are found
```

---

### 4.8 `check_kdenlive_file_exists`

**Purpose**: Verify project file exists and is valid MLT XML.

```python
def check_kdenlive_file_exists(project_file_path, rule):
    """
    Args:
        project_file_path: Path to .kdenlive project file
        rule: {"valid_xml": true}
    Returns:
        float: 1.0 if file exists and parses as valid XML with <mlt> root, 0.0 otherwise
    """
    # Check file exists and size > 0
    # Parse XML, verify root tag is <mlt>
```

---

### 4.9 `check_kdenlive_bin_content`

**Purpose**: Verify project bin contains expected files and does NOT contain removed files.

```python
def check_kdenlive_bin_content(project_file_path, rule):
    """
    Args:
        project_file_path: Path to .kdenlive project file
        rule: {
            "expected_present": ["file1.mp4"],  # Must exist in bin
            "expected_absent": ["file2.mp4"]    # Must NOT exist in bin
        }
    Returns:
        float: 1.0 if all conditions met, 0.0 otherwise
    """
    # Collect all producer resources
    # Check expected_present: all must be found
    # Check expected_absent: none should be found
```

---

### 4.10 `check_kdenlive_clip_name`

**Purpose**: Verify a clip has been renamed in the project bin.

```python
def check_kdenlive_clip_name(project_file_path, rule):
    """
    Args:
        project_file_path: Path to .kdenlive project file
        rule: {"source_file": "xxx.mp4", "expected_name": "Main Video"}
    Returns:
        float: 1.0 if clip has expected name, 0.0 otherwise
    """
    # Find <producer> whose resource contains source_file
    # Check <property name="kdenlive:clipname"> matches expected_name
```

---

### 4.11 `check_kdenlive_bin_folder`

**Purpose**: Verify a folder exists in the project bin.

```python
def check_kdenlive_bin_folder(project_file_path, rule):
    """
    Args:
        project_file_path: Path to .kdenlive project file
        rule: {"expected_folder": "Footage"}
    Returns:
        float: 1.0 if folder found, 0.0 otherwise
    """
    # Parse kdenlive:docproperties.kdenlive:folders or <folder> elements
    # Check folder name matches expected_folder
```

---

### 4.12 `check_kdenlive_track_count`

**Purpose**: Verify the number of video/audio tracks in the timeline.

```python
def check_kdenlive_track_count(project_file_path, rule):
    """
    Args:
        project_file_path: Path to .kdenlive project file
        rule: {
            "min_video_tracks": 3,     # Optional: minimum video tracks
            "min_audio_tracks": 3,     # Optional: minimum audio tracks
            "exact_video_tracks": 1,   # Optional: exact video track count
            "exact_audio_tracks": 2    # Optional: exact audio track count
        }
    Returns:
        float: 1.0 if track counts match, 0.0 otherwise
    """
    # Count <track> elements in main <tractor>
    # Classify video vs audio by checking kdenlive:track_type property
    # Compare against min/exact constraints
```

---

### 4.13 `check_kdenlive_guide`

**Purpose**: Verify a timeline guide/marker exists with expected label and position.

```python
def check_kdenlive_guide(project_file_path, rule):
    """
    Args:
        project_file_path: Path to .kdenlive project file
        rule: {"guide_comment": "Scene Start", "guide_time_seconds": 5.0, "tolerance": 0.5}
    Returns:
        float: 1.0 if matching guide found, 0.0 otherwise
    """
    # Parse <property name="kdenlive:docproperties.guides"> JSON array
    # Each guide: {"comment": "...", "pos": frame_number, ...}
    # Convert pos to seconds, compare with guide_time_seconds ± tolerance
    # Check comment matches guide_comment
```

---

### 4.14 `check_kdenlive_track_mute`

**Purpose**: Verify a specific track is muted.

```python
def check_kdenlive_track_mute(project_file_path, rule):
    """
    Args:
        project_file_path: Path to .kdenlive project file
        rule: {"muted_track": "V1"}
    Returns:
        float: 1.0 if track is muted, 0.0 otherwise
    """
    # Find the track by index/name in <tractor>
    # Check <track> element's hide attribute ("audio" or "video" or "both")
    # Or check kdenlive:track properties for mute state
```

---

### 4.15 `check_kdenlive_track_lock`

**Purpose**: Verify a specific track is locked.

```python
def check_kdenlive_track_lock(project_file_path, rule):
    """
    Args:
        project_file_path: Path to .kdenlive project file
        rule: {"locked_track": "V1"}
    Returns:
        float: 1.0 if track is locked, 0.0 otherwise
    """
    # Find the track in <tractor>
    # Check <property name="kdenlive:locked_track"> is "1" or true
```

---

### 4.16 `check_kdenlive_timeline_empty`

**Purpose**: Verify clip is in bin but NOT on timeline (e.g., after undo).

```python
def check_kdenlive_timeline_empty(project_file_path, rule):
    """
    Args:
        project_file_path: Path to .kdenlive project file
        rule: {"expected_in_bin": "xxx.mp4", "expected_not_on_timeline": true}
    Returns:
        float: 1.0 if clip in bin but not on timeline, 0.0 otherwise
    """
    # Check <producer> with matching resource exists (in bin)
    # Check no <entry> in timeline playlists references that producer
```

---

### 4.17 `check_kdenlive_color_clip`

**Purpose**: Verify a color clip exists with the expected color.

```python
def check_kdenlive_color_clip(project_file_path, rule):
    """
    Args:
        project_file_path: Path to .kdenlive project file
        rule: {"expected_color": "#FF0000"}
    Returns:
        float: 1.0 if matching color clip found, 0.0 otherwise
    """
    # Find <producer> with mlt_service="color"
    # Check resource property for color value (format: 0xff0000ff or #FF0000)
    # Normalize and compare color values
```

---

### 4.18 `check_kdenlive_clip_duration`

**Purpose**: Verify clip duration (for color/title clips).

```python
def check_kdenlive_clip_duration(project_file_path, rule):
    """
    Args:
        project_file_path: Path to .kdenlive project file
        rule: {"min_duration_seconds": 9.5, "max_duration_seconds": 10.5}
    Returns:
        float: 1.0 if duration within range, 0.0 otherwise
    """
    # Find color/title producer
    # Get length/out property (frame count)
    # Get fps from project profile
    # Convert to seconds, compare with min/max range
```

---

### 4.19 `check_kdenlive_proxy_setting`

**Purpose**: Verify proxy clip setting is enabled/disabled.

```python
def check_kdenlive_proxy_setting(project_file_path, rule):
    """
    Args:
        project_file_path: Path to .kdenlive project file
        rule: {"proxy_enabled": true}
    Returns:
        float: 1.0 if proxy setting matches, 0.0 otherwise
    """
    # Check <property name="kdenlive:docproperties.enableproxy"> value
    # "1" = enabled, "0" = disabled
```

---

### 4.20 `check_kdenlive_clip_position`

**Purpose**: Verify a clip starts at a specific position on the timeline.

```python
def check_kdenlive_clip_position(project_file_path, rule):
    """
    Args:
        project_file_path: Path to .kdenlive project file
        rule: {"source_file": "xxx.mp4", "start_time": 5.0, "tolerance": 0.5}
    Returns:
        float: 1.0 if clip position matches, 0.0 otherwise
    """
    # Find the track playlist containing the clip
    # Sum <blank length="N"/> frames before the <entry> to get start frame
    # Convert to seconds using project fps
    # Compare with start_time ± tolerance
```

---

### 4.21 `check_kdenlive_snapshot_exists`

**Purpose**: Verify a snapshot image file was created.

```python
def check_kdenlive_snapshot_exists(result, rule):
    """
    Args:
        result: Output of vm_command_line (file count string)
        rule: {"min_count": 1}
    Returns:
        float: 1.0 if file count >= min_count, 0.0 otherwise
    """
    # Parse the integer from result string
    # Compare with min_count
```

---

> **Note**: Section 4.22–4.28 are newly added for the expanded Level 2 tasks.

### 4.22 `check_kdenlive_effect_applied`

**Purpose**: Generic evaluator to verify that a specific video/audio effect has been applied to a clip.

**Validation Logic**:
- Find the `<producer>` or `<chain>` matching `source_file`
- Search for `<filter>` nodes associated with that producer/chain
- Check if any filter's `mlt_service` matches one of the expected service names
- Supports multiple alternative service names (since Kdenlive may use different internal names)

```python
def check_kdenlive_effect_applied(project_file_path, rule):
    """
    Args:
        project_file_path: Path to .kdenlive project file
        rule: {
            "effect_service": ["box_blur", "boxblur", "blur"],  # List of acceptable mlt_service names
            "source_file": "xxx.mp4"                              # Optional: specific clip to check
        }
    Returns:
        float: 1.0 if matching effect found, 0.0 otherwise
    """
    # Iterate all <filter> nodes in tractor/playlist
    # Check mlt_service matches any value in effect_service list
    # If source_file specified, verify the filter is applied to that specific clip
```

---

### 4.23 `check_kdenlive_effect_param`

**Purpose**: Verify that an effect is applied with a specific parameter value (e.g., rotation angle, opacity level).

**Validation Logic**:
- Find `<filter>` with matching `mlt_service`
- Read the target parameter property value
- Compare with expected value within tolerance

```python
def check_kdenlive_effect_param(project_file_path, rule):
    """
    Args:
        project_file_path: Path to .kdenlive project file
        rule: {
            "effect_service": ["rotate", "affine"],  # List of acceptable mlt_service names
            "param_name": "rotate",                    # Property name to check
            "expected_value": 90,                       # Expected numeric value
            "tolerance": 5                              # ± tolerance for comparison
        }
    Returns:
        float: 1.0 if effect found with matching parameter, 0.0 otherwise
    """
    # Find <filter> with mlt_service in effect_service list
    # Read <property name="param_name"> value
    # Parse as float and compare with expected_value ± tolerance
```

---

### 4.24 `check_kdenlive_audio_fade`

**Purpose**: Verify audio fade in and/or fade out effects are applied to a clip.

**Validation Logic**:
- Find the producer matching `source_file`
- Look for `<filter>` with `mlt_service` being `volume` or `brightness` with keyframe data
- Check for fade_from_audio / fade_to_audio filters
- Verify presence of fade in (volume 0→1) and/or fade out (volume 1→0)

```python
def check_kdenlive_audio_fade(project_file_path, rule):
    """
    Args:
        project_file_path: Path to .kdenlive project file
        rule: {
            "fade_in": true,                                     # Check fade in exists
            "fade_out": true,                                    # Check fade out exists
            "source_file": "xxx.mp3"                             # Source file to check
        }
    Returns:
        float: 1.0 if required fades found, 0.0 otherwise
    """
    # Look for volume/brightness filter with keyframe data
    # Or find fade_from_audio / fade_to_audio type filters
    # Check fade_in: volume starts at 0 and ramps up
    # Check fade_out: volume ramps down to 0
```

---

### 4.25 `check_kdenlive_clip_split`

**Purpose**: Verify a clip has been split into multiple segments on the timeline.

**Validation Logic**:
- Find all `<entry>` elements across timeline playlists that reference producers containing `source_file`
- Count the number of segments (entries)
- Verify count meets `min_segments` requirement

```python
def check_kdenlive_clip_split(project_file_path, rule):
    """
    Args:
        project_file_path: Path to .kdenlive project file
        rule: {
            "source_file": "xxx.mp4",  # File that was split
            "min_segments": 2           # Minimum number of segments expected
        }
    Returns:
        float: 1.0 if clip has been split into >= min_segments pieces, 0.0 otherwise
    """
    # Find producer IDs matching source_file
    # Count <entry> elements referencing those producers across all timeline playlists
    # Return 1.0 if count >= min_segments
```

---

### 4.26 `check_kdenlive_multi_track_composition`

**Purpose**: Verify a multi-track composition setup (e.g., picture-in-picture, watermark overlay).

**Validation Logic**:
- Verify both `main_file` and `overlay_file` exist as producers
- Verify they are placed on **different** tracks
- If `require_transform` is true, check that a transform/affine/qtblend effect is applied on the overlay track

```python
def check_kdenlive_multi_track_composition(project_file_path, rule):
    """
    Args:
        project_file_path: Path to .kdenlive project file
        rule: {
            "main_file": "main.mp4",        # Main background video
            "overlay_file": "overlay.mp4",   # Overlay video/image
            "require_transform": true         # Whether transform effect is required
        }
    Returns:
        float: 1.0 if multi-track composition is set up correctly, 0.0 otherwise
    """
    # Find producers for main_file and overlay_file
    # Verify they are on different tracks
    # If require_transform, check for affine/qtblend/composite filter on overlay
```

---

### 4.27 `check_kdenlive_clip_count`

**Purpose**: Verify the number of times a clip appears on the timeline (e.g., after copy-paste).

**Validation Logic**:
- Find all producers matching `source_file`
- Count `<entry>` elements across all timeline playlists that reference those producers
- Compare with `min_count`

```python
def check_kdenlive_clip_count(project_file_path, rule):
    """
    Args:
        project_file_path: Path to .kdenlive project file
        rule: {
            "source_file": "xxx.mp4",  # File to count
            "min_count": 2              # Minimum number of timeline entries
        }
    Returns:
        float: 1.0 if clip appears >= min_count times on timeline, 0.0 otherwise
    """
    # Find producer IDs matching source_file
    # Count <entry> elements referencing those producers
    # Return 1.0 if count >= min_count
```

---

### 4.28 `check_kdenlive_clip_group`

**Purpose**: Verify that clips have been grouped together on the timeline.

**Validation Logic**:
- Parse `<group>` elements or `kdenlive:group` properties in the project XML
- Count the number of groups and clips within each group
- Verify at least `min_groups` groups exist with `min_clips_in_group` clips each

```python
def check_kdenlive_clip_group(project_file_path, rule):
    """
    Args:
        project_file_path: Path to .kdenlive project file
        rule: {
            "min_groups": 1,           # Minimum number of groups
            "min_clips_in_group": 2    # Minimum clips per group
        }
    Returns:
        float: 1.0 if grouping requirements met, 0.0 otherwise
    """
    # Parse <group> elements or kdenlive:group properties
    # Count groups and their member clips
    # Verify constraints are met
```

---

> **Note**: Section 4.29 is newly added for the expanded Level 3 basic render tasks. Section 4.30–4.36 are composite evaluators for Level 3 advanced tasks that verify both rendered output AND project file operations.

### 4.29 `check_kdenlive_render_custom_resolution`

**Purpose**: Verify rendered output has the expected resolution, codec, and duration.

**Validation Logic**:
- Use ffprobe to inspect the output file
- Verify video stream codec matches expected codec
- Verify video resolution (width × height) matches expected values
- Check duration meets minimum requirement

```python
def check_kdenlive_render_custom_resolution(result_file_path, rule):
    """
    Args:
        result_file_path: Path to rendered MP4 file
        rule: {
            "min_duration": 1.0,          # Minimum duration in seconds
            "expected_codec": "h264",     # Expected video codec
            "expected_width": 1280,       # Expected video width
            "expected_height": 720        # Expected video height
        }
    Returns:
        float: 1.0 if resolution, codec, and duration all match, 0.0 otherwise
    """
    # Use ffprobe to check output file
    # Verify video stream codec matches expected_codec
    # Verify video resolution matches expected_width × expected_height
    # Verify duration >= min_duration
```

---

> **Note**: Section 4.30–4.36 are newly added composite evaluators for Level 3 tasks. Each composite evaluator verifies BOTH the rendered output file (via ffprobe) AND the .kdenlive project file (via XML parsing) to ensure all task operations were actually performed.

### 4.30 `check_kdenlive_render_multi_clip_transition`

**Purpose**: Verify multi-clip render with transitions. Checks both the rendered output and the project file.

**Validation Logic**:
1. Use ffprobe to verify output MP4 (codec, duration)
2. Parse `.kdenlive` project file to verify all expected clips are imported
3. Verify at least one transition (dissolve/luma) exists in the project

```python
def check_kdenlive_render_multi_clip_transition(result_file_path, rule):
    """
    Args:
        result_file_path: Path to rendered MP4 file
        rule: {
            "min_duration": 5.0,
            "expected_codec": "h264",
            "project_path": "/home/user/Videos/project.kdenlive",
            "expected_files": ["clip1.mp4", "clip2.mp4", "clip3.mp4"],
            "transition_type": "luma"
        }
    Returns:
        float: 1.0 if all checks pass, 0.0 otherwise
    """
    # Step 1: check_kdenlive_render_mp4 logic on result_file_path
    # Step 2: Parse project_path XML, verify all expected_files are in producers
    # Step 3: Verify transition_type exists in <transition> nodes
```

---

### 4.31 `check_kdenlive_render_effects_composite`

**Purpose**: Verify effects + render composite task. Checks rendered output and project file for grayscale effect and volume adjustment.

**Validation Logic**:
1. Use ffprobe to verify output MP4 (codec, duration)
2. Parse `.kdenlive` project file to verify grayscale effect is applied
3. Verify volume adjustment matches expected value

```python
def check_kdenlive_render_effects_composite(result_file_path, rule):
    """
    Args:
        result_file_path: Path to rendered MP4 file
        rule: {
            "min_duration": 1.0,
            "expected_codec": "h264",
            "project_path": "/home/user/Videos/project.kdenlive",
            "require_grayscale": true,
            "expected_volume": 0.3,
            "volume_tolerance": 0.05
        }
    Returns:
        float: 1.0 if all checks pass, 0.0 otherwise
    """
    # Step 1: check_kdenlive_render_mp4 logic on result_file_path
    # Step 2: check_kdenlive_grayscale_effect logic on project_path
    # Step 3: check_kdenlive_volume_adjustment logic on project_path
```

---

### 4.32 `check_kdenlive_render_title_video_title`

**Purpose**: Verify title-video-title render. Checks rendered output and project file for title clips with expected text.

**Validation Logic**:
1. Use ffprobe to verify output MP4 (codec, duration ≥ 5s)
2. Parse `.kdenlive` project file to verify title clip producers exist
3. For each expected title text, verify it appears in a kdenlivetitle producer's xmldata

```python
def check_kdenlive_render_title_video_title(result_file_path, rule):
    """
    Args:
        result_file_path: Path to rendered MP4 file
        rule: {
            "min_duration": 5.0,
            "expected_codec": "h264",
            "project_path": "/home/user/Videos/project.kdenlive",
            "expected_titles": ["Welcome to My Video", "Thank You"]
        }
    Returns:
        float: 1.0 if all checks pass, 0.0 otherwise
    """
    # Step 1: check_kdenlive_render_mp4 logic on result_file_path
    # Step 2: For each title in expected_titles, check_kdenlive_title_text logic on project_path
```

---

### 4.33 `check_kdenlive_render_speed_ramp`

**Purpose**: Verify speed ramp render. Checks rendered output and project file for clip split and speed change.

**Validation Logic**:
1. Use ffprobe to verify output MP4 (codec, duration)
2. Parse `.kdenlive` project file to verify clip is split into ≥ min_segments
3. Verify a speed change (warp_speed) matching expected_speed exists

```python
def check_kdenlive_render_speed_ramp(result_file_path, rule):
    """
    Args:
        result_file_path: Path to rendered MP4 file
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
        float: 1.0 if all checks pass, 0.0 otherwise
    """
    # Step 1: check_kdenlive_render_mp4 logic on result_file_path
    # Step 2: check_kdenlive_clip_split logic on project_path (min_segments)
    # Step 3: check_kdenlive_clip_speed logic on project_path (expected_speed)
```

---

### 4.34 `check_kdenlive_render_pip`

**Purpose**: Verify picture-in-picture render. Checks rendered output and project file for multi-track composition with transform.

**Validation Logic**:
1. Use ffprobe to verify output MP4 (codec, duration)
2. Parse `.kdenlive` project file to verify two clips on different tracks
3. Verify a transform/affine effect is applied on the overlay track

```python
def check_kdenlive_render_pip(result_file_path, rule):
    """
    Args:
        result_file_path: Path to rendered MP4 file
        rule: {
            "min_duration": 1.0,
            "expected_codec": "h264",
            "project_path": "/home/user/Videos/project.kdenlive",
            "main_file": "15368811_1920_1080_30fps.mp4",
            "overlay_file": "6533277-hd_1920_1080_24fps.mp4",
            "require_transform": true
        }
    Returns:
        float: 1.0 if all checks pass, 0.0 otherwise
    """
    # Step 1: check_kdenlive_render_mp4 logic on result_file_path
    # Step 2: check_kdenlive_multi_track_composition logic on project_path
```

---

### 4.35 `check_kdenlive_render_audio_mix`

**Purpose**: Verify audio mixing render. Checks rendered output has audio stream, and project file has volume adjustment and all audio files imported.

**Validation Logic**:
1. Use ffprobe to verify output MP4 (codec, duration, has audio stream)
2. Parse `.kdenlive` project file to verify all expected audio files are imported
3. Verify volume adjustment on BGM matches expected value

```python
def check_kdenlive_render_audio_mix(result_file_path, rule):
    """
    Args:
        result_file_path: Path to rendered MP4 file
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
        float: 1.0 if all checks pass, 0.0 otherwise
    """
    # Step 1: check_kdenlive_render_with_audio logic on result_file_path
    # Step 2: check_kdenlive_import_multiple_files logic on project_path (expected_audio_files)
    # Step 3: check_kdenlive_volume_adjustment logic on project_path (expected_volume)
```

---

### 4.36 `check_kdenlive_render_color_grading`

**Purpose**: Verify color grading pipeline render. Checks rendered output and project file for brightness, sepia, and audio fade effects.

**Validation Logic**:
1. Use ffprobe to verify output MP4 (codec, duration)
2. Parse `.kdenlive` project file to verify brightness effect is applied
3. Verify sepia effect is applied
4. Verify audio fade in and fade out effects exist

```python
def check_kdenlive_render_color_grading(result_file_path, rule):
    """
    Args:
        result_file_path: Path to rendered MP4 file
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
        float: 1.0 if all checks pass, 0.0 otherwise
    """
    # Step 1: check_kdenlive_render_mp4 logic on result_file_path
    # Step 2: check_kdenlive_effect_applied logic on project_path (brightness services)
    # Step 3: check_kdenlive_effect_applied logic on project_path (sepia services)
    # Step 4: check_kdenlive_audio_fade logic on project_path (fade_in + fade_out)
```

---

## 5. Task Difficulty Overview

```
Level 1 (Basic) — 21 Tasks
────────────────────────────────────────────────────────────
Category: Project Bin Management
  Task 1-1  Import Video to Bin
  Task 1-5  Import Multiple Files to Bin
  Task 1-9  Delete Clip from Bin
  Task 1-10 Rename Clip in Bin
  Task 1-11 Create Folder in Bin
  Task 1-19 Create Color Clip
  Task 1-20 Set Clip Duration (Color/Title)

Category: Timeline Basic Operations
  Task 1-3  Add Video to Timeline
  Task 1-24 Move Clip Position on Timeline
  Task 1-18 Undo Last Operation
  Task 1-21 Take Snapshot from Clip Monitor

Category: Track Management
  Task 1-12 Add a Video Track
  Task 1-14 Delete a Track
  Task 1-15 Add Guide/Marker
  Task 1-16 Mute a Track
  Task 1-17 Lock a Track

Category: Project Settings
  Task 1-4  Set Project Resolution
  Task 1-7  Set Project Frame Rate
  Task 1-8  Save Project with Specific Name
  Task 1-22 Enable Proxy Clips
  Task 1-23 Set Preview Resolution


Level 2 (Intermediate) — 14 Tasks
────────────────────────────────────────────────────────────
Category: Video Effects
  Task 2-1  Apply Grayscale Effect
  Task 2-7  Apply Blur Effect
  Task 2-9  Rotate Video 90 Degrees
  Task 2-17 Adjust Clip Opacity/Transparency

Category: Audio Effects
  Task 2-2  Adjust Audio Volume
  Task 2-12 Add Audio Fade In/Out

Category: Timeline Editing
  Task 2-3  Trim Video Clip
  Task 2-6  Change Clip Playback Speed
  Task 2-13 Split/Cut a Clip
  Task 2-15 Copy and Paste a Clip
  Task 2-16 Group Clips

Category: Transitions & Composition
  Task 2-4  Add Dissolve Transition
  Task 2-14 Picture-in-Picture (PiP)

Category: Text/Title
  Task 2-5  Add Title Text


Level 3 (Advanced) — 10 Tasks
────────────────────────────────────────────────────────────
Category: Basic Rendering
  Task 3-1  Render MP4
  Task 3-10 Render Custom Resolution MP4

Category: Audio + Video Render
  Task 3-2  Add BGM + Render
  Task 3-8  Audio Mixing Multi-track + Render

Category: Multi-clip Editing + Render
  Task 3-3  Multi-clip + Transition + Render
  Task 3-5  Title Intro + Video + Outro + Render
  Task 3-6  Speed Ramp Video + Render

Category: Composition + Render
  Task 3-7  Picture-in-Picture + Render

Category: Effects Pipeline + Render
  Task 3-4  Effects + Render (Comprehensive)
  Task 3-9  Color Grading Pipeline + Render
```

---

## 6. New Evaluator Registration

After implementing new evaluator functions, they must be registered in `desktop_env/evaluators/metrics/__init__.py`:

```python
from .kdenlive import (
    check_kdenlive_import_video,
    check_kdenlive_add_to_timeline,
    check_kdenlive_grayscale_effect,
    check_kdenlive_volume_adjustment,
    check_kdenlive_render_mp4,
    # New functions to add:
    check_kdenlive_project_profile,
    check_kdenlive_clip_trim,
    check_kdenlive_transition,
    check_kdenlive_title_text,
    check_kdenlive_clip_speed,
    check_kdenlive_render_with_audio,
    # Level 1 expanded functions:
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
    # Level 2 expanded functions:
    check_kdenlive_effect_applied,
    check_kdenlive_effect_param,
    check_kdenlive_audio_fade,
    check_kdenlive_clip_split,
    check_kdenlive_multi_track_composition,
    check_kdenlive_clip_count,
    check_kdenlive_clip_group,
    # Level 3 expanded functions:
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

## 7. Implementation Notes

1. **Priority**: Implement Level 1 and Level 2 tasks first — they validate via `.kdenlive` XML parsing, which is fast and stable without needing render.

2. **Render tasks (Level 3)**: Rendering can take several minutes. Consider adding longer `sleep` times in `config`, or use `postconfig` to wait for render completion.

3. **Project file path convention**: All tasks should instruct the Agent to save the project to a consistent path (e.g., `/home/user/Videos/project.kdenlive`) specified explicitly in the `instruction`.

4. **Config execution order**: `upload_file` → `launch` → `sleep` → (Agent performs task) → `postconfig` → Evaluate.

5. **Kdenlive launch path**: All tasks use `/home/user/.local/bin/kdenlive` as the launch command. The standard `config` entry for launching Kdenlive is:

   This should always be placed **after** any `upload_file` steps and **before** the `sleep` step in the `config` array.

---

## 8. Level 3 Task JSON ID Mapping

| Task | UUID | Evaluator |
|------|------|-----------|
| Task 3-1: Render MP4 | `fd3ae9f3-841f-4b11-b72d-e090eea0e706` | `check_kdenlive_render_mp4` |
| Task 3-2: Add BGM + Render | `4be9b350-d9ad-4bd9-82b3-788bb214bb7d` | `check_kdenlive_render_with_audio` |
| Task 3-3: Multi-clip + Transition + Render | `bb095bd9-5919-4a02-86da-2a9bb6380ff1` | `check_kdenlive_render_multi_clip_transition` |
| Task 3-4: Effects + Render | `07186918-9646-45af-805b-2a13c02ac63f` | `check_kdenlive_render_effects_composite` |
| Task 3-5: Title + Video + Title + Render | `081b45e0-3ecc-4fde-b2ca-62eed6400255` | `check_kdenlive_render_title_video_title` |
| Task 3-6: Speed Ramp + Render | `abbaf9fe-861f-400e-8fd8-77a03e50a281` | `check_kdenlive_render_speed_ramp` |
| Task 3-7: PiP + Render | `a73dd78e-fb7d-4dd5-a829-f174b5603a85` | `check_kdenlive_render_pip` |
| Task 3-8: Audio Mix + Render | `d3a66c10-476d-4f83-9155-5e3526d6cf31` | `check_kdenlive_render_audio_mix` |
| Task 3-9: Color Grading + Render | `8c708e3d-ff5e-4306-8fd3-3a4c674f30e7` | `check_kdenlive_render_color_grading` |
| Task 3-10: Custom Resolution + Render | `49c6d9d4-a682-46fa-a8ef-907eb976d042` | `check_kdenlive_render_custom_resolution` |
