# LibreOffice 任务数据总览

> 最后更新：2026-04-02

---

## 1. 数据概况

### 总量一览

| 大类 | 应用 | 数量 | 评估方式 | 难度分布 |
|------|------|------|----------|----------|
| 静态任务 | Calc | 50 (30 new + 20 hard) | `compare_table` / `compare_csv` | L1:8, L2:15, L3:27 |
| 静态任务 | Writer | 30 | `compare_docx_files` | L1:5, L2:15, L3:10 |
| 静态任务 | Impress | 30 | `compare_pptx_files` / `check_transition` / `check_slide_orientation_Portrait` | L1:9, L2:9, L3:12 |
| 单应用交互 | Calc | 27 | `check_include_exclude` | L2:3, L3:24 |
| 单应用交互 | Writer | 26 | `check_include_exclude` | L1:7, L2:8, L3:11 |
| 单应用交互 | Impress | 25 | `check_include_exclude` | L2:5, L3:20 |
| 跨应用交互 | w2c / c2w / w2i / c2i | 60 | `check_include_exclude` | L1:5, L2:15, L3:40 |
| **合计** | | **248** | | |

### 按任务类型汇总

| 任务类型 | 数量 | 特点 |
|----------|------|------|
| 静态任务 | 110 | 单轮指令，agent 独立完成，通过文件对比评估 |
| 单应用交互任务 | 78 | 多阶段多轮，含模糊指令/需求变更/纠错/中断，单个应用内完成 |
| 跨应用交互任务 | 60 | 多阶段多轮，需要在两个应用间传递信息 |

---

## 2. 静态任务详情

### 2.1 Calc（50 条）

| 子集 | 数量 | 目录 | 说明 |
|------|------|------|------|
| calc_new | 30 | `evaluation_examples/examples/libreoffice_calc_new/` | 原始 OSWorld 数据集中的 Calc 任务 |
| calc_hard | 20 | `evaluation_examples/examples/libreoffice_calc_hard/` | 新造的较高难度 Calc 任务 |

- **入口文件**：`evaluation_examples/test_calc.json`（精选 30 条：16 new + 14 hard）
- **评估函数**：`compare_table`（49 条）、`compare_csv`（1 条）
- **规则类型**：`sheet_data`、`freeze`、`data_validation`、`chart`、`style`、`sheet_name`
- **素材格式**：`.xlsx`，通过 `upload_file` 上传到 VM 的 `/home/user/Desktop/`
- **Gold 文件**：每个任务对应一个 `*_gold.xlsx`，存放在 `cache/<task_id>/`

**难度分布**：

| 难度 | 数量 | 指令特征 | 示例 |
|------|------|----------|------|
| L1 | 8 | 单句单操作 | "Sort the data by Date column ascending" |
| L2 | 15 | 2-3 句 / 2-4 操作 | "Add a Profit column, then sort by profit descending" |
| L3 | 27 | 长段落 + 编号子步骤 | "Do ALL: (1) Add Profit column (2) Sort (3) Bold header (4) Create summary sheet..." |

### 2.2 Writer（30 条）

| 子集 | 数量 | 目录 |
|------|------|------|
| writer_hard | 30 | `evaluation_examples/examples/libreoffice_writer_hard/` |

- **入口文件**：`evaluation_examples/test_writer.json`（30 条）
- **评估函数**：`compare_docx_files`（全部）
- **素材格式**：`.docx`
- **Gold 文件**：`*_gold.docx`，存放在 `cache/<task_id>/`

**难度分布**：L1:5, L2:15, L3:10

### 2.3 Impress（30 条）

| 子集 | 数量 | 目录 |
|------|------|------|
| impress_v3 | 30 | `evaluation_examples/examples/libreoffice_impress_v3/` |

- **入口文件**：`evaluation_examples/test_impress.json`（30 条）
- **评估函数**：`compare_pptx_files`（28）、`check_transition`（1）、`check_slide_orientation_Portrait`（1）
- **素材格式**：`.pptx`（来自真实 PPT 模板）
- **Gold 文件**：`*_gold.pptx` 或特定检查函数

**难度分布**：L1:9, L2:9, L3:12

---

## 3. 单应用交互任务详情（78 条）

### 存放位置

- **Config 目录**：`desktopworld/evaluation_examples/examples/interactive/`
- **入口文件**：`desktopworld/evaluation_examples/test_interactive_single.json`（64 条）
  - 注：部分任务在 `test_interactive_multi.json` 的 `interactive` 键下（19 条）

### 分应用统计

| 应用 | 数量 | 难度分布 |
|------|------|----------|
| Calc | 27 (25 普通 + 2 workflow) | L2:3, L3:24 |
| Writer | 26 (24 普通 + 2 workflow) | L1:7, L2:8, L3:11 |
| Impress | 25 (24 普通 + 1 workflow) | L2:5, L3:20 |

### 场景类型分布

| 场景类型 | Calc | Writer | Impress | 合计 | 说明 |
|----------|------|--------|---------|------|------|
| `ambiguous_target` | 4 | 4 | 3 | 11 | 目标模糊（"帮我算个总数"，没说哪列） |
| `ambiguous_detail` | 4 | 4 | 4 | 12 | 细节模糊（"帮我做个汇总"，没说格式） |
| `ambiguous_scope` | 4 | 4 | 3 | 11 | 范围模糊（"帮我清理数据"，没说哪些） |
| `progressive_refinement` | 4 | 4 | 6 | 14 | 渐进完善（做完第一步后追加新需求） |
| `requirement_change` | 5 | 4 | 4 | 13 | 需求变更（做到一半改主意） |
| `error_correction` | 2 | 2 | 2 | 6 | 纠错（"你做错了，撤销重来"） |
| `task_interruption` | 2 | 1 | 2 | 5 | 中断（"等等，先帮我做另一件事"） |
| `multi_step_workflow` | 2 | 2 | 1 | 5 | 多步工作流（分阶段明确指令） |
| `ambiguous_instruction` | 0 | 1 | 0 | 1 | 指令本身语义模糊 |

### 触发机制

| 触发链模式 | 数量 | 说明 |
|-----------|------|------|
| `agent_asks` → `agent_done` | 34 | Agent 主动提问后再执行（模糊指令场景） |
| `step_count` → `agent_done` | 28 | 执行若干步后用户插入新需求 |
| `step_count` → `agent_done` → `agent_done` | 10 | 3 阶段：执行→插入→继续 |
| `agent_done` → `agent_done` → `agent_done` → `agent_done` | 5 | 4 阶段工作流 |
| 其他组合 | 1 | |

### 评估方式

全部使用 `check_include_exclude`，在 VM 上执行命令行检查输出文件内容是否包含预期关键字。

---

## 4. 跨应用交互任务详情（60 条）

### 存放位置

- **Config 目录**：`desktopworld/evaluation_examples/examples/interactive/`（与单应用交互混放，以 `interactive_multiapp_` 前缀区分）
- **入口文件**：`desktopworld/evaluation_examples/test_interactive_multi.json` 中 `libreoffice_suite_njc` 键（60 条）

### 子类型分布

| 子类型 | 数量 | 数据流向 | 难度分布 |
|--------|------|----------|----------|
| w2c (Writer→Calc) | 20 | 从 Writer 文档提取信息写入 Calc 表格 | L1:0, L2:0, L3:20 |
| c2w (Calc→Writer) | 20 | 从 Calc 表格提取数据写入 Writer 文档 | L1:5, L2:8, L3:7 |
| w2i (Writer→Impress) | 10 | 从 Writer 文档提取信息制作 PPT | L1:0, L2:5, L3:5（含 3 个 L1） |
| c2i (Calc→Impress) | 10 | 从 Calc 表格提取数据制作 PPT | L1:0, L2:2, L3:8 |

### 评估方式

全部使用 `check_include_exclude`，通过 VM 命令行验证输出文件内容。

---

## 5. 文件目录索引

### 任务 Config 文件

| 路径 | 内容 | 数量 |
|------|------|------|
| `evaluation_examples/examples/libreoffice_calc_new/*.json` | Calc 静态任务（new） | 30 |
| `evaluation_examples/examples/libreoffice_calc_hard/*.json` | Calc 静态任务（hard） | 20 |
| `evaluation_examples/examples/libreoffice_writer_hard/*.json` | Writer 静态任务 | 30 |
| `evaluation_examples/examples/libreoffice_impress_v3/*.json` | Impress 静态任务 | 30 |
| `desktopworld/evaluation_examples/examples/interactive/interactive_calc_*.json` | Calc 单应用交互 | 27 |
| `desktopworld/evaluation_examples/examples/interactive/interactive_writer_*.json` | Writer 单应用交互 | 26 |
| `desktopworld/evaluation_examples/examples/interactive/interactive_impress_*.json` | Impress 单应用交互 | 25 |
| `desktopworld/evaluation_examples/examples/interactive/interactive_multiapp_*.json` | 跨应用交互 | 60 |

### 入口 JSON（运行测试用）

| 路径 | 内容 | 数量 |
|------|------|------|
| `evaluation_examples/test_calc.json` | Calc 静态任务集 | 30 |
| `evaluation_examples/test_writer.json` | Writer 静态任务集 | 30 |
| `evaluation_examples/test_impress.json` | Impress 静态任务集 | 30 |
| `evaluation_examples/test_writer_new10.json` | Writer 新增 10 条（验证用） | 10 |
| `desktopworld/evaluation_examples/test_interactive_single.json` | 单应用交互任务集 | 64 |
| `desktopworld/evaluation_examples/test_interactive_multi.json` | 跨应用 + 部分交互任务集 | 79 |

### 素材与 Gold 文件

| 路径 | 内容 |
|------|------|
| `cache/<task_id>/` | 静态任务的素材文件（`.xlsx`/`.docx`/`.pptx`）和 gold 文件 |
| `desktopworld/cache/<task_id>/` | 同上（desktopworld 侧副本） |
| `PPTX/` | Impress 原始 PPT 模板文件 |

### 测试结果

| 路径 | 内容 |
|------|------|
| `desktopworld/results_calc_v1/` | Calc 静态任务测试结果 |
| `desktopworld/results_writer_v1/` | Writer 静态任务测试结果（old 20） |
| `desktopworld/results_writer_new10/` | Writer 新增 10 条测试结果 |
| `desktopworld/results_impress_v1/` | Impress 静态任务测试结果 |
| `desktopworld/results_interactive_v1/` | 交互任务测试结果（主要批次） |
| `desktopworld/results_interactive_val/` | 交互任务验证测试 |

---

## 6. 文档索引

| 文档 | 内容覆盖 | 行数 |
|------|----------|------|
| [`doc_libreoffice_calc.md`](doc_libreoffice_calc.md) | Calc 50 条静态 + 27 条单应用交互，验证策略、评估函数、Task JSON 模板、难度分布 | 1320 |
| [`doc_libreoffice_calc_en.md`](doc_libreoffice_calc_en.md) | 上述英文版 | 1235 |
| [`doc_libreoffice_writer.md`](doc_libreoffice_writer.md) | Writer 30 条静态 + 26 条单应用交互 | 784 |
| [`doc_libreoffice_writer_en.md`](doc_libreoffice_writer_en.md) | 上述英文版 | 746 |
| [`doc_libreoffice_impress.md`](doc_libreoffice_impress.md) | Impress 30 条静态 + 25 条单应用交互 | 903 |
| [`doc_libreoffice_impress_en.md`](doc_libreoffice_impress_en.md) | 上述英文版 | 861 |
| [`doc_interactive_multiapp.md`](doc_interactive_multiapp.md) | 60 条跨应用交互任务（w2c/c2w/w2i/c2i） | 692 |
| [`doc_interactive_multiapp_en.md`](doc_interactive_multiapp_en.md) | 上述英文版 | 692 |
| [`doc_test_report.md`](doc_test_report.md) | kimi-k2.5 模型测试报告，含各任务步数和正确率 | 648 |
| [`doc_audacity.md`](doc_audacity.md) | 参考模板（Audacity 任务设计文档格式） | 1372 |

---

## 7. 评估函数汇总

| 函数名 | 使用场景 | 依赖库 | 使用次数 |
|--------|----------|--------|----------|
| `compare_table` | Calc 静态任务 | `openpyxl` | 49 |
| `compare_csv` | Calc CSV 导出任务 | 标准库 | 1 |
| `compare_docx_files` | Writer 静态任务 | `python-docx` | 30 |
| `compare_pptx_files` | Impress 静态任务 | `python-pptx` | 28 |
| `check_transition` | Impress 过渡动画 | `python-pptx` | 1 |
| `check_slide_orientation_Portrait` | Impress 页面方向 | `python-pptx` | 1 |
| `check_include_exclude` | 全部交互任务 | 标准库 | 138 |

---

## 8. 运行环境

- **模型**：kimi-k2.5（本地 vLLM，`http://localhost:8000/v1`）
- **执行框架**：`desktopworld/run_multienv_evocua_interactive.py`
- **VM 环境**：Docker（`happysixd/osworld-docker`），含 LibreOffice 全套 + X11
- **最大步数**：静态任务 50 步 / 交互任务 80 步
- **并行环境数**：1-3 个 Docker 容器

---

## 9. 测试结果摘要

基于 kimi-k2.5 模型的最新测试：

| 应用 | 任务数 | 通过数 | 正确率 | 平均步数 |
|------|--------|--------|--------|----------|
| Calc（静态） | 50 | 9 | 18% | 41.0 |
| Writer（静态） | 30 | 11 | 37% | 35.7 |
| Impress（静态） | 30 | 1 | 3% | 45.8 |
| Interactive（全部） | 143 | 28 | 20% | 41.8 |

详细结果见 [`doc_test_report.md`](doc_test_report.md)。
