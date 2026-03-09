# 实施计划：Kdenlive L1 原子任务首批 5 个（MVP）

> 基于需求文档 `requirements.md`，开发 5 个简单的 L1 原子任务，每个任务使用独立的 evaluator function。

---

- [ ] 1. 创建 Kdenlive evaluator 模块文件并在 `__init__.py` 中注册
  - 创建 `desktop_env/evaluators/metrics/kdenlive.py` 文件
  - 文件头部添加必要的 import：`os`、`logging`、`xml.etree.ElementTree`、`subprocess`、`json`
  - 初始化 `logger = logging.getLogger(__name__)`
  - 在 `desktop_env/evaluators/metrics/__init__.py` 末尾添加 `from .kdenlive import (check_kdenlive_import_video, check_kdenlive_add_to_timeline, check_kdenlive_grayscale_effect, check_kdenlive_volume_adjustment, check_kdenlive_render_mp4)`
  - _需求：1.1、1.2、1.3_

- [ ] 2. 实现 `check_kdenlive_import_video` evaluator 函数
  - 在 `kdenlive.py` 中实现函数 `check_kdenlive_import_video(project_file_path, rule)`
  - 使用 `xml.etree.ElementTree.parse()` 解析 `.kdenlive` 项目文件
  - 遍历 XML 中所有 `<producer>` 节点，对每个 producer 查找其子元素 `<property name="resource">`
  - 检查是否存在某个 producer 的 resource 属性值包含 `rule["expected_file"]`（如 `"sample_video.mp4"`）
  - 匹配成功返回 `1.0`，否则返回 `0.0`
  - 整个函数体包裹在 `try...except` 中，任何异常返回 `0.0` 并 `logger.error` 记录
  - _需求：2.1、2.2、2.3、2.4、9.1、9.2_

- [ ] 3. 实现 `check_kdenlive_add_to_timeline` evaluator 函数
  - 在 `kdenlive.py` 中实现函数 `check_kdenlive_add_to_timeline(project_file_path, rule)`
  - 解析项目文件 XML，遍历所有 `<playlist>` 节点
  - 对每个 playlist 检查是否包含 `<entry>` 子节点（排除仅包含 `<blank>` 的空轨道）
  - 对找到的 entry，获取其 `producer` 属性值，再在 XML 中查找对应的 `<producer>` 节点
  - 验证该 producer 的 `resource` 属性是否包含 `rule["expected_file"]`
  - 找到匹配返回 `1.0`，否则返回 `0.0`；异常情况同上
  - _需求：3.1、3.2、3.3、9.1、9.2_

- [ ] 4. 实现 `check_kdenlive_grayscale_effect` evaluator 函数
  - 在 `kdenlive.py` 中实现函数 `check_kdenlive_grayscale_effect(project_file_path, rule)`
  - 解析项目文件 XML，使用 `root.iter('filter')` 遍历所有 `<filter>` 节点（包括嵌套在 producer/playlist 内的）
  - 对每个 filter，提取其 `mlt_service` 属性值（可能在属性中直接出现，或在子元素 `<property name="mlt_service">` 中）
  - 定义灰度效果的合法 mlt_service 列表：`["grayscale", "avfilter.colorchannelmixer", "frei0r.colorize", "charcoal"]`
  - 检查是否有任一 filter 的 mlt_service 在合法列表中，匹配返回 `1.0`，否则返回 `0.0`
  - _需求：4.1、4.2、4.3、9.1、9.2_

- [ ] 5. 实现 `check_kdenlive_volume_adjustment` evaluator 函数
  - 在 `kdenlive.py` 中实现函数 `check_kdenlive_volume_adjustment(project_file_path, rule)`
  - 解析项目文件 XML，使用 `root.iter('filter')` 遍历所有 `<filter>` 节点
  - 查找 `mlt_service` 为 `"volume"` 的 filter
  - 对匹配的 filter，提取 `<property name="level">` 或 `<property name="gain">` 的值
  - 将值转为 float，与 `rule["expected_volume"]`（如 `0.5`）比较，容差为 `rule.get("tolerance", 0.05)`
  - 若在容差范围内返回 `1.0`，否则返回 `0.0`；异常情况同上
  - _需求：5.1、5.2、5.3、5.4、9.1、9.2_

- [ ] 6. 实现 `check_kdenlive_render_mp4` evaluator 函数
  - 在 `kdenlive.py` 中实现函数 `check_kdenlive_render_mp4(result_file_path, rule)`
  - 首先检查 `result_file_path` 文件是否存在且 `os.path.getsize() > 0`
  - 使用 `subprocess.run()` 调用 `ffprobe -v quiet -print_format json -show_streams {file_path}` 获取文件元数据
  - 解析 ffprobe 输出的 JSON，查找 `codec_type == "video"` 的 stream
  - 验证 `codec_name` 包含 `"h264"` 或 `"libx264"`
  - 提取 `duration`（如在 stream 中不存在则使用 `ffprobe -show_format` 的 `duration`），验证 > 1.0 秒
  - 所有检查通过返回 `1.0`，否则返回 `0.0`
  - 使用 `subprocess.TimeoutExpired` 异常处理防止 ffprobe 超时；设置 `timeout=30`
  - _需求：6.1、6.2、6.3、6.4、6.5、9.3_

- [ ] 7. 创建任务 1 的 Task JSON 文件（导入视频到素材库）
  - 创建 `evaluation_examples/examples/kdenlive/{uuid}-L1_1.json`
  - `config` 部分：(1) `download` 下载 `sample_video.mp4` 到 `/home/user/Desktop/sample_video.mp4`；(2) `launch` 启动 `/home/user/.local/bin/kdenlive`（不打开项目文件，让 Kdenlive 创建默认空项目）；(3) `sleep` 等待 15 秒
  - `instruction`：`"Import the video file /home/user/Desktop/sample_video.mp4 into Kdenlive's project bin, then save the project as /home/user/Desktop/project.kdenlive"`
  - `evaluator` 部分：`postconfig` 使用 `Ctrl+S` 保存项目 + sleep 2 秒；`func` 为 `"check_kdenlive_import_video"`；`result` 为 `{"type": "vm_file", "path": "/home/user/Desktop/project.kdenlive", "dest": "project.kdenlive"}`；`expected` 为 `{"type": "rule", "rules": {"expected_file": "sample_video.mp4"}}`
  - _需求：2、7.1、7.2、7.3、7.4、7.5_

- [ ] 8. 创建任务 2 的 Task JSON 文件（将素材添加到时间线）
  - 创建 `evaluation_examples/examples/kdenlive/{uuid}-L1_2.json`
  - `config` 部分：(1) `download` 下载测试视频 `sample_video.mp4` + 预配置的 `.kdenlive` 项目文件（项目中已导入 sample_video.mp4 但未放到时间线）到 `/home/user/Desktop/`；(2) `launch` 启动 kdenlive 并打开预配置项目文件 `/home/user/Desktop/project_with_clip.kdenlive`；(3) `sleep` 等待 15 秒
  - `instruction`：`"Add the video clip 'sample_video.mp4' from the project bin to the first video track (V1) in the timeline, then save the project."`
  - `evaluator` 部分：`postconfig` 使用 `Ctrl+S` + sleep；`func` 为 `"check_kdenlive_add_to_timeline"`；`result` 为 vm_file 取回项目文件；`expected` 为 rule `{"expected_file": "sample_video.mp4"}`
  - 需要手动构造一个预配置的 `.kdenlive` XML 文件（包含 producer 引用 sample_video.mp4 但 playlist 为空）并上传
  - _需求：3、7.1、7.2、7.3、7.4、7.5、8.2_

- [ ] 9. 创建任务 3 的 Task JSON 文件（添加灰度效果）
  - 创建 `evaluation_examples/examples/kdenlive/{uuid}-L1_3.json`
  - `config` 部分：(1) `download` 下载测试视频 + 预配置项目文件（时间线上已有视频片段）；(2) `launch` 打开预配置项目；(3) `sleep` 15 秒
  - `instruction`：`"Apply a Greyscale (grayscale) video effect to the video clip on the timeline, then save the project."`
  - `evaluator` 部分：`postconfig` Ctrl+S + sleep；`func` 为 `"check_kdenlive_grayscale_effect"`；`result` 为 vm_file；`expected` 为 rule `{}`（空 rule，函数内无需额外参数）
  - 需要构造一个含有时间线视频片段的预配置 `.kdenlive` 项目文件并上传
  - _需求：4、7.1、7.2、7.3、7.4、7.5、8.2_

- [ ] 10. 创建任务 4 和任务 5 的 Task JSON 文件（调整音量 + 渲染 MP4）
  - **任务 4**：创建 `evaluation_examples/examples/kdenlive/{uuid}-L1_4.json`
    - `config`：download 测试视频 + 预配置项目文件（时间线已有片段）；launch 打开项目；sleep 15 秒
    - `instruction`：`"Adjust the audio volume of the video clip on the timeline to 50%, then save the project."`
    - `evaluator`：postconfig Ctrl+S + sleep；func `"check_kdenlive_volume_adjustment"`；result vm_file；expected rule `{"expected_volume": 0.5, "tolerance": 0.05}`
  - **任务 5**：创建 `evaluation_examples/examples/kdenlive/{uuid}-L1_5.json`
    - `config`：download 测试视频 + 预配置项目文件；launch 打开项目；sleep 15 秒
    - `instruction`：`"Render the current project as an MP4 file with H.264 encoding to /home/user/Desktop/output.mp4"`
    - `evaluator`：postconfig **不使用 Ctrl+S**，改为 sleep 60 秒（等待渲染完成）；func `"check_kdenlive_render_mp4"`；result `{"type": "vm_file", "path": "/home/user/Desktop/output.mp4", "dest": "output.mp4"}`；expected rule `{}`
  - _需求：5、6、7.1、7.2、7.3、7.4、7.5、8.2、9.5_

- [ ] 11. 编写测试素材生成脚本
  - 创建 `evaluation_examples/examples/kdenlive/generate_test_assets.py` 脚本
  - 脚本功能 1：调用 FFmpeg 生成 10 秒 1080p 30fps 测试视频（带音频）`sample_video.mp4`
  - 脚本功能 2：使用 Python `xml.etree.ElementTree` 生成多个预配置的 `.kdenlive` 项目文件模板：
    - `project_with_clip.kdenlive`：仅素材库中包含视频引用（用于任务 2）
    - `project_with_timeline.kdenlive`：素材在时间线上（用于任务 3、4、5）
  - 脚本生成的文件输出到 `evaluation_examples/examples/kdenlive/assets/` 目录
  - 脚本最后打印所有文件路径和对应的上传指引
  - _需求：8.1、8.2_
