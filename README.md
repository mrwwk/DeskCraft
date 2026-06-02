# DeskCraft

DeskCraft 是一个面向真实桌面工作流的 GUI Agent 评测基准，对应论文 **"DeskCraft: Benchmarking Desktop Agents on Professional Workflows and Human-in-the-Loop Collaboration"**。本项目基于 OSWorld 的虚拟桌面执行框架扩展而来，重点评测智能体在专业软件、长程任务和人机协作场景中的能力。

与主要关注短任务或一次性指令执行的桌面基准不同，DeskCraft 将评测目标推进到更接近真实工作的设置：任务可能跨越多个应用、包含多个依赖步骤、需要保存或导出专业产物，并且用户可能在执行过程中补充、打断、澄清或修正需求。

论文和代码关注三个核心问题：

- Agent 能否在真实 Ubuntu 桌面环境中完成专业软件工作流。
- Agent 能否从 L1 原子操作扩展到 L2 组合任务和 L3 长程交付任务。
- Agent 能否在多阶段交互中主动提问、接收用户反馈并继续完成任务。

## 主要特性

- **538 个可执行桌面任务**：包括 386 个标准任务和 152 个交互任务。
- **L1/L2/L3 难度体系**：L1 测试单步或短路径操作，L2 测试相关操作组合，L3 测试长程专业交付工作流。
- **人机协作协议**：支持 `agent_done`、`agent_asks`、`step_count` 等触发机制，用于模拟任务完成后反馈、Agent 主动澄清和用户中途打断。
- **专业软件覆盖**：覆盖办公、浏览器、开发、创意设计、多媒体和 3D 工作流。
- **执行式验证**：从最终桌面状态、项目文件、导出文件、浏览器状态、音视频元数据或结构化文档中提取证据，使用程序化 evaluator 给出 0/1 分数。
- **多 Agent runner**：包含 UI-TARS、EvoCUA、Qwen-VL、Claude、Kimi、OpenAI CUA、AutoGLM、AGI 等多种 runner 入口。

## 任务覆盖

DeskCraft 覆盖 11 个应用和一个多应用类别：

- LibreOffice Writer、Calc、Impress
- Chrome
- VS Code
- GIMP、Inkscape
- Kdenlive、Audacity、Blender
- OS 系统操作
- Multi-app 跨应用工作流

论文中的任务规模为：

- 标准任务：386 个，包括 L1 126 个、L2 147 个、L3 113 个。
- 交互任务：152 个。
- 总任务：538 个。
- 资源文件：279 个，覆盖 `.jpg`、`.png`、`.svg`、`.docx`、`.pptx`、`.xlsx`、`.blend`、`.wav`、`.mp4`、`.html`、`.js`、`.json` 等 19 种格式。

## 难度定义

DeskCraft 不只按指令长度划分难度，而是按任务成功所需的执行能力划分。

- **L1 Atomic**：一个清晰、局部、可直接执行的操作，例如修改 SVG 文本字号、冻结表格首行、导出 WAV 文件或切换浏览器设置。
- **L2 Composition**：由 2 到 4 个相关操作组成，需要在同一应用或同一产物内进行小规模规划，例如添加公式并排序、编辑文档样式并补充段落、剪辑视频片段并添加简单转场。
- **L3 Long Horizon**：真实交付型工作流，通常需要超过 50 步，包含多个依赖子任务、跨区域一致性和一个或多个最终产物，例如完成 Blender 场景、GIMP 项目与导出图、UI 生成项目或多应用交付链路。

## 交互协议

交互任务将用户协作建模为可复现的阶段序列。每个阶段包含用户消息和触发条件，当触发条件满足时，UserSimulator 会向 Agent 注入下一条用户消息。

核心触发方式：

- `agent_done`：Agent 声明完成后，用户给出反馈、修正或追加需求。
- `agent_asks`：Agent 主动调用用户澄清接口时，用户回答缺失信息。
- `step_count`：执行到指定步数后，用户中途打断或改变约束。

当前代码中还支持 `agent_idle` 和 `llm_judge` 等扩展触发方式，详见 `README_INTERACTIVE.md`。

这种协议覆盖了论文中的主要协作模式：progressive refinement、ambiguity / clarification、requirement change、interruption、correction / feedback 和 multi-step workflow。

## 项目结构

```text
desktopworld/
├── main.pdf                         # DeskCraft 论文
├── README.md                        # 项目说明
├── README_INTERACTIVE.md            # 交互评测详细指南
├── requirements.txt                 # Python 依赖
├── quickstart.py                    # 环境连通性快速测试
├── calc_success_rate.py             # 扫描 result.txt 统计成功率
├── lib_run_single.py                # 标准任务执行循环
├── lib_run_interactive.py           # 交互任务执行循环
├── desktop_env/                     # 桌面环境、VM provider、evaluator 和 getter
├── mm_agents/                       # Agent 实现与模型适配
├── runners/                         # 各类 Agent 的评测入口
├── evaluation_examples/
│   ├── standard_task.json
│   ├── interactive_task.json
│   └── ubuntu_examples/             # 按应用划分的任务 JSON
├── assets/                          # 任务输入资源
├── monitor/                         # 监控相关工具
└── utils/                           # 辅助工具
```

## 安装

建议使用 Python 3.10 或更高版本。若使用 `pyproject.toml` 管理环境，请注意其中声明为 Python 3.12；若直接使用 `requirements.txt`，项目代码本身沿用 OSWorld/desktop-env 的 Python 3.10+ 约束。

```bash
cd /path/to/OSWorld/desktopworld

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
python -m playwright install
```

如果只需要安装桌面环境包，也可以使用：

```bash
pip install -e .
```

## 环境准备

DeskCraft 在真实虚拟桌面中运行任务。当前项目支持 Docker、VMware、VirtualBox、AWS、Azure 等 provider。论文和本仓库中的多数并行实验使用 Docker 或云端虚拟机。

常用环境变量：

```bash
# Agent 模型 API，按所用 runner 调整
export OPENAI_API_KEY="EMPTY"
export OPENAI_BASE_URL="http://localhost:8000/v1"

# 即使使用 Docker provider，部分代码路径也可能读取 AWS 变量
export AWS_REGION="us-east-1"
export AWS_SUBNET_ID="subnet-dummy"
export AWS_SECURITY_GROUP_ID="sg-dummy"
```

如果运行涉及 Google、Google Drive 或需要代理的任务，请参考：

- `ACCOUNT_GUIDELINE.md`
- `PUBLIC_EVALUATION_GUIDELINE.md`
- `desktop_env/providers/docker/DOCKER_GUIDELINE.md`
- `desktop_env/providers/aws/AWS_GUIDELINE.md`

## 快速测试

先确认虚拟桌面环境可以启动、重置和执行基本 pyautogui 动作：

```bash
python quickstart.py \
  --provider_name docker \
  --headless True
```

正常情况下，脚本会启动环境、reset 示例任务、执行一次右键点击，然后关闭环境。

## 运行标准任务

标准任务使用单轮指令，执行结束后由 evaluator 检查最终状态。实际任务索引位于 `evaluation_examples/standard_task.json`，任务文件位于 `evaluation_examples/ubuntu_examples/<domain>/`。

以下命令以带交互/非交互自动路由能力的 UI-TARS 1.5 runner 为例：

```bash
python runners/run_multienv_interactive.py \
  --provider_name docker \
  --headless \
  --domain gimp \
  --test_all_meta_path evaluation_examples/standard_task.json \
  --test_config_base_dir evaluation_examples/ubuntu_examples \
  --num_envs 3 \
  --max_steps 100 \
  --model "UI-TARS-1.5-7B" \
  --result_dir ./results \
  --run_name uitars15_gimp_standard
```

注意：部分 runner 仍沿用 OSWorld 旧默认值 `evaluation_examples/test_all.json` 和 `evaluation_examples/examples/<domain>/`。本仓库实际提供的 DeskCraft 索引与任务目录如上所示；如果某个 runner 不支持 `evaluation_examples/ubuntu_examples/<domain>/` 这种目录结构，请使用带有 `resolve_config_file()` 的 runner，或在 runner 中补充同样的路径解析逻辑。

## 运行交互任务

交互任务在标准任务循环之外加入 UserSimulator。UserSimulator 使用独立 LLM 服务模拟用户，在触发条件满足时向 Agent 注入阶段性用户消息。

以下命令以 EvoCUA 交互 runner 为例：

```bash
python runners/run_multienv_evocua_interactive.py \
  --provider_name docker \
  --headless \
  --domain gimp \
  --test_all_meta_path evaluation_examples/interactive_task.json \
  --test_config_base_dir evaluation_examples/ubuntu_examples \
  --num_envs 3 \
  --max_steps 100 \
  --model "EvoCUA-32B" \
  --prompt_style S2 \
  --coordinate_type relative \
  --resize_factor 32 \
  --user_model "gpt-4o" \
  --user_base_url "https://api.openai.com/v1" \
  --user_api_key "$OPENAI_API_KEY" \
  --result_dir ./results \
  --run_name evocua_gimp_interactive
```

交互评测的详细 JSON 格式、phase 设计、触发机制、`call_user` 行为和日志说明见 `README_INTERACTIVE.md`。

## 结果与日志

运行结果会保存在 `--result_dir/--run_name` 对应目录下。不同 runner 的结果目录可能略有差异：有些直接在 `pyautogui/screenshot/<domain>/` 下保存任务，有些会多一层 `pyautogui/screenshot/<model>/<domain>/`。

常见结构一：

```text
results/<run_name>/
└── pyautogui/
    └── screenshot/
        └── <domain>/
            └── <task_id>/
                ├── result.txt
                ├── traj.jsonl
                ├── runtime.log
                ├── recording.mp4
                └── interaction_log.json   # 交互任务生成
```

常见结构二：

```text
results/<run_name>/
└── pyautogui/
    └── screenshot/
        └── <model>/
            └── <domain>/
                └── <task_id>/
                    ├── result.txt
                    ├── traj.jsonl
                    ├── runtime.log
                    ├── recording.mp4
                    └── interaction_log.json
```

统计成功率：

```bash
python calc_success_rate.py results/<run_name>
```

`calc_success_rate.py` 适用于直接按 domain 存放的结果目录；如果你使用的 runner 额外插入了模型名目录，可以根据实际结果结构调整统计脚本或使用 runner 运行时打印的 success rate。`result.txt` 中的分数通常为 `1.0` 或 `0.0`。`traj.jsonl` 保存 Agent 的逐步轨迹，`recording.mp4` 保存屏幕录制，交互任务还会保存 `interaction_log.json`。

## 评测机制

DeskCraft 使用执行式验证，而不是人工主观评分。每个任务 JSON 包含：

- `config`：重置 VM 后上传文件、创建初始状态、启动应用或等待 GUI 初始化。
- `instruction` 或 `phases`：标准任务使用单条指令，交互任务使用多阶段用户消息。
- `evaluator.result`：从 VM 中取回文件、命令输出、浏览器状态、项目文件或其他结果。
- `evaluator.expected`：规则、参考文件或期望状态。
- `evaluator.func`：用于比较结果和期望的程序化 metric。

不同应用使用不同的 native artifact 检查方式：

- SVG 任务解析 XML、样式、transform、文本和图层。
- Office 任务读取 `.docx`、`.xlsx`、`.pptx` 的结构、内容和格式。
- Audacity 任务检查 WAV 信号、时长、声道、RMS、静音段、fade 或 `.aup3` 工程。
- Kdenlive 任务解析项目 XML、时间线、素材、转场、特效和导出视频元数据。
- Blender 任务通过 background Blender 脚本读取 `bpy` 场景图。
- Chrome、OS、VS Code 和 multi-app 任务检查文件系统、配置、浏览器状态、命令输出或测试结果。

## 添加新任务

新增任务建议遵循论文中的 construction blueprint：

1. 明确目标应用、初始资源、最终产物和可程序化验证的状态。
2. 将任务放到 `evaluation_examples/ubuntu_examples/<domain>/`。
3. 标准任务使用 `instruction`；交互任务使用 `interactive: true` 和 `phases`。
4. 确保 instruction 明确说明目标文件和保存/导出路径。
5. 确保 `config` 中上传或生成的文件路径与 `evaluator.result.path` 一致。
6. 在 `desktop_env/evaluators/metrics/` 中实现或复用 evaluator。
7. 在 `desktop_env/evaluators/__init__.py` 注册 evaluator 函数。
8. 将任务 ID 加入对应索引文件。
9. 用单任务索引进行小规模回归测试。

更多 evaluator 和 getter 的设计细节可参考 `desktop_env/evaluators/README.md` 以及现有任务 JSON。

## 论文结果概览

论文评测了 18 个 proprietary 和 open-source GUI agents。主要发现包括：

- 当前最强模型在 DeskCraft 上仍远未可靠：Kimi-K2.6 在标准任务上达到 33.8%，GPT-5.4 在交互任务上达到 27.6%。
- 难度从 L1/L2 增加到 L3 后，成功率显著下降；长程专业交付仍是主要瓶颈。
- 将步数预算扩展到 300 可以恢复少量额外成功，但 100 步之后的收益有限。
- 在交互任务中，Agent 更容易处理明确的修正反馈，但较少主动请求澄清；模糊任务中的主要失败模式是过早猜测用户意图。

这些结果说明，桌面 Agent 的关键挑战已经从单步 GUI 执行转向长程规划、状态保持、错误恢复和主动协作。

## 相关文档

- `main.pdf`：DeskCraft 论文。
- `README_INTERACTIVE.md`：多阶段交互评测指南。
- `desktop_env/evaluators/README.md`：evaluator 设计与使用说明。
- `mm_agents/README.md`：Agent 接口说明。
- `PUBLIC_EVALUATION_GUIDELINE.md`：公开评测与云端运行说明。
- `ACCOUNT_GUIDELINE.md`：账号与 OAuth 配置说明。

## Citation

如果使用 DeskCraft，请引用论文：

```bibtex
@misc{deskcraft2026,
  title = {DeskCraft: Benchmarking Desktop Agents on Professional Workflows and Human-in-the-Loop Collaboration},
  author = {Wang, Wenkai and Xiong, Tao and Ni, Jingchen and Bao, Yunpeng and Li, Xiyun and Liu, Tianqi and Guo, Hongcan and Huang, Zilong and Zhang, Shengyu},
  year = {2026},
  note = {Benchmark for professional desktop workflows and human-in-the-loop collaboration}
}
```

本项目基于 OSWorld / desktop-env 的真实虚拟桌面执行框架扩展。若使用底层环境，也请同时引用 OSWorld。
