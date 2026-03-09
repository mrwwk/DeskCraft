# 需求文档：Kdenlive L1 原子任务首批 5 个（MVP）

## 引言

本文档定义了在 OSWorld 基准测试框架中为 **Kdenlive** 构建首批 **5 个 L1 原子任务**的需求。

### 核心约束
- **每个任务使用独立的 evaluator function**（不做公共解耦），以 `check_kdenlive_{task_name}` 命名
- 所有 evaluator 函数放在一个 `desktop_env/evaluators/metrics/kdenlive.py` 文件中
- 在 `desktop_env/evaluators/metrics/__init__.py` 中注册导入
- 每个任务对应一个独立的 task JSON 文件，放在 `evaluation_examples/examples/kdenlive/` 目录下
- 通过解析 `.kdenlive` 项目文件（MLT XML）或使用 `ffprobe` 检查输出文件来验证
- 评估前通过 `postconfig` 使用 `Ctrl+S` 保存项目文件到 VM 后再取回验证

### Kdenlive 技术背景

- **项目文件格式**：`.kdenlive` 基于 MLT XML 格式，可用 `xml.etree.ElementTree` 解析
- **关键 XML 节点**：`<profile>`（项目参数）、`<producer>`（媒体素材）、`<playlist>` + `<entry>`（时间线片段）、`<filter>`（效果）、`<transition>`（转场）、`<tractor>` + `<track>`（多轨结构）
- **配置文件路径**：`~/.config/kdenliverc`（KDE Config / INI 格式）
- **启动命令**：`/home/user/.local/bin/kdenlive`
- **Evaluator 参数传递**：`result` → getter 取回文件路径 → 作为第一个参数传给 metric function；`expected` → getter 取回 → 作为第二个参数（如有）；`options` → 作为 `**kwargs` 传给 metric function

### Evaluator 函数签名约定

根据 OSWorld 框架的 dispatch 逻辑，evaluator 函数的签名取决于 task JSON 中的 `result`/`expected` 配置：

- **使用 `vm_file` result + `rule` expected**：`func(file_path, rule)` — 从 VM 取回项目文件，expected 中包含验证规则 dict
- **使用 `vm_file` result + `cloud_file` expected**：`func(result_path, expected_path)` — 对比两个文件
- **使用 `vm_file` result 无 expected**：`func(file_path)` — 仅检查结果文件
- 支持 `**options` 传递额外参数

---

## 需求

### 需求 1：Evaluator 函数文件与注册

**用户故事：** 作为一名开发者，我希望创建一个 `kdenlive.py` evaluator 模块并正确注册，以便 5 个 Kdenlive 任务的评估函数可以被评估管道正确调用。

#### 验收标准

1. WHEN 创建 `desktop_env/evaluators/metrics/kdenlive.py` 文件 THEN 文件 SHALL 包含 5 个独立的 evaluator 函数
2. WHEN 在 `__init__.py` 中添加 `from .kdenlive import (...)` THEN 评估管道 SHALL 能通过函数名动态调用这些函数
3. WHEN evaluator 函数执行中发生任何异常 THEN 函数 SHALL 捕获异常、记录 logger.error 日志并返回 0.0

### 需求 2：任务 1 — 导入视频文件到素材库

**用户故事：** 作为一名 AI Agent，我需要将桌面上的视频文件导入到 Kdenlive 的项目素材库中。

**任务描述**：Kdenlive 已启动并打开了一个空白项目。将 `/home/user/Desktop/sample_video.mp4` 导入到项目素材库中，然后保存项目。

**Evaluator 函数**：`check_kdenlive_import_video(project_file_path, rule)`

**验证逻辑**：解析 `.kdenlive` 项目文件 XML，搜索所有 `<producer>` 节点，检查是否存在某个 producer 的 `<property name="resource">` 值包含 `rule["expected_file"]` 指定的文件名（如 `sample_video.mp4`）。

#### 验收标准

1. WHEN Agent 导入视频文件后并保存项目 THEN evaluator SHALL 解析项目文件并在 `<producer>` 节点中找到指向 `sample_video.mp4` 的 resource 属性
2. IF 项目文件不存在或解析失败 THEN evaluator SHALL 返回 0.0
3. IF 项目文件中不存在任何指向 `sample_video.mp4` 的 producer THEN evaluator SHALL 返回 0.0
4. WHEN 成功找到匹配的 producer THEN evaluator SHALL 返回 1.0

### 需求 3：任务 2 — 将素材添加到时间线

**用户故事：** 作为一名 AI Agent，我需要将素材库中的视频片段放置到时间线轨道上。

**任务描述**：Kdenlive 已启动并打开了一个预配置项目（素材库中已包含 `sample_video.mp4`）。将该视频片段添加到第一个视频轨道（V1）上，然后保存项目。

**Evaluator 函数**：`check_kdenlive_add_to_timeline(project_file_path, rule)`

**验证逻辑**：解析项目文件 XML，检查是否存在至少一个 `<playlist>` 包含 `<entry>` 节点（排除全部为 `<blank>` 的空轨道），且 entry 引用的 producer 对应 `sample_video.mp4`。

#### 验收标准

1. WHEN Agent 将素材添加到时间线后并保存项目 THEN evaluator SHALL 在某个 `<playlist>` 中找到非空的 `<entry>` 节点
2. WHEN 检查 entry 引用 THEN evaluator SHALL 验证 entry 的 producer 属性指向的 producer 节点的 resource 包含预期文件名
3. IF 所有 playlist 都只包含 blank 条目 THEN evaluator SHALL 返回 0.0

### 需求 4：任务 3 — 添加视频效果（转为灰度）

**用户故事：** 作为一名 AI Agent，我需要为时间线上的视频片段应用灰度效果。

**任务描述**：Kdenlive 已启动并打开了一个预配置项目（时间线上已有一个视频片段）。为该视频片段应用灰度（Greyscale）效果，然后保存项目。

**Evaluator 函数**：`check_kdenlive_grayscale_effect(project_file_path, rule)`

**验证逻辑**：解析项目文件 XML，遍历所有 `<filter>` 节点（可能嵌套在 `<producer>` 或 `<playlist>` 内），检查是否存在 `mlt_service` 属性值为 `grayscale`、`avfilter.colorchannelmixer`（灰度模式）或 `<property name="mlt_service">grayscale</property>` 的 filter。

#### 验收标准

1. WHEN Agent 应用灰度效果后并保存项目 THEN evaluator SHALL 在项目文件中找到灰度相关的 filter 节点
2. WHEN 检查 filter 类型 THEN evaluator SHALL 接受以下任一 mlt_service 值：`grayscale`、`avfilter.colorchannelmixer`、`frei0r.colorize`
3. IF 项目文件中不存在任何灰度 filter THEN evaluator SHALL 返回 0.0

### 需求 5：任务 4 — 调整音量

**用户故事：** 作为一名 AI Agent，我需要调整时间线上片段的音频音量。

**任务描述**：Kdenlive 已启动并打开了一个预配置项目（时间线上已有一个带音频的视频片段）。将该片段的音量调整为 50%，然后保存项目。

**Evaluator 函数**：`check_kdenlive_volume_adjustment(project_file_path, rule)`

**验证逻辑**：解析项目文件 XML，搜索 `<filter>` 节点中 `mlt_service` 为 `volume` 的 filter，检查其 `level` 或 `gain` 参数是否在 `rule["expected_volume"]`（如 0.5）的容差范围内（如 ±0.05）。

#### 验收标准

1. WHEN Agent 调整音量后并保存项目 THEN evaluator SHALL 在项目文件中找到 volume 类型的 filter 节点
2. WHEN 检查音量参数 THEN evaluator SHALL 验证 `level` 参数值在 `expected_volume ± tolerance` 范围内（默认 tolerance=0.05）
3. IF 不存在 volume filter THEN evaluator SHALL 返回 0.0
4. IF volume filter 的参数值不在容差范围内 THEN evaluator SHALL 返回 0.0

### 需求 6：任务 5 — 渲染导出为 MP4

**用户故事：** 作为一名 AI Agent，我需要将项目渲染导出为 MP4 格式视频文件。

**任务描述**：Kdenlive 已启动并打开了一个预配置项目（时间线上已有一个视频片段）。将项目渲染为 MP4 格式（H.264 编码），输出到 `/home/user/Desktop/output.mp4`。

**Evaluator 函数**：`check_kdenlive_render_mp4(result_file_path, rule)`

**验证逻辑**：使用 `subprocess` 调用 `ffprobe` 检查输出文件的属性：(1) 文件存在且大小 > 0；(2) 视频编码为 `h264`；(3) 容器格式为 `mp4`；(4) 视频时长 > 1 秒。

#### 验收标准

1. WHEN Agent 完成渲染后 THEN evaluator SHALL 验证输出文件存在且大小 > 0 字节
2. WHEN 使用 ffprobe 检查输出文件 THEN evaluator SHALL 验证视频编码名称包含 `h264`
3. WHEN 使用 ffprobe 检查输出文件 THEN evaluator SHALL 验证时长大于 1 秒
4. IF 文件不存在或 ffprobe 执行失败 THEN evaluator SHALL 返回 0.0
5. IF 编码格式不匹配 THEN evaluator SHALL 返回 0.0

### 需求 7：Task JSON 文件规范

**用户故事：** 作为一名开发者，我希望 5 个任务的 JSON 文件结构统一规范，以便无缝接入 OSWorld 评估管道。

#### 验收标准

1. WHEN 每个 task JSON 被创建 THEN 文件 SHALL 包含以下必要字段：
   - `id`：使用 `{uuid}-L1_{N}` 格式
   - `snapshot`：值为 `"kdenlive"`
   - `instruction`：英文自然语言任务描述
   - `source`：值为 `"Custom created for Kdenlive evaluation"`
   - `config`：包含 `download`（如需下载素材/项目文件）+ `launch`（启动 Kdenlive）+ `sleep`（等待启动，至少 15 秒）
   - `evaluator`：包含 `postconfig`（评估前保存项目）+ `func` + `result` + `expected`
   - `related_apps`：值为 `["kdenlive"]`
   - `trajectory`：值为 `"trajectories/"`
   - `proxy`：值为 `false`
   - `fixed_ip`：值为 `false`
   - `possibility_of_env_change`：值为 `"low"`

2. WHEN evaluator 的 postconfig 被配置 THEN postconfig SHALL 包含使用 `Ctrl+S` 保存项目的 pyautogui 操作及 sleep 等待

3. WHEN evaluator 需要取回项目文件 THEN result SHALL 使用 `"type": "vm_file"` 并指定项目文件在 VM 中的路径

4. WHEN evaluator 使用 rule 模式 THEN expected SHALL 使用 `"type": "rule"` 并在 `rules` 字段中传递验证规则

5. WHEN 任务需要预置 `.kdenlive` 项目文件 THEN config SHALL 包含 `download` 配置下载预配置项目文件，并通过 `launch` 命令直接打开该项目文件

### 需求 8：测试素材准备

**用户故事：** 作为一名开发者，我希望准备任务所需的测试媒体素材和预配置项目文件。

#### 验收标准

1. WHEN 准备视频素材 THEN 系统 SHALL 提供一个 FFmpeg 命令来生成 10 秒 1080p 30fps MP4 测试视频（带音频）
2. WHEN 准备预配置项目文件 THEN 系统 SHALL 提供用于构造 `.kdenlive` XML 文件的 Python 脚本
3. WHEN 素材需要在 VM 中使用 THEN 素材 SHALL 通过 config 的 download 配置从可访问 URL 下载到 VM

### 需求 9：边界情况与错误处理

**用户故事：** 作为一名评估研究者，我希望 evaluator 在各种异常情况下都能安全返回 0.0 而不崩溃。

#### 验收标准

1. WHEN `.kdenlive` 文件不存在或为空 THEN evaluator SHALL 返回 0.0 并记录错误日志
2. WHEN XML 解析失败 THEN evaluator SHALL 捕获 `xml.etree.ElementTree.ParseError` 并返回 0.0
3. WHEN ffprobe 命令不存在或执行超时 THEN evaluator SHALL 捕获异常并返回 0.0
4. WHEN Kdenlive 启动缓慢 THEN config 中的 sleep 等待时间 SHALL 至少 15 秒
5. WHEN 渲染任务需要等待 THEN 该任务的 postconfig SHALL 不使用 Ctrl+S（因为渲染是独立操作），而是增加足够的 sleep 等待时间
