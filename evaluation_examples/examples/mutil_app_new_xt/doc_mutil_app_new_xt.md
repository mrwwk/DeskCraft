# mutil_app_new_xt 任务设计文档

> 说明：目录名沿用仓库中的既有拼写 `mutil_app_new_xt`。本文档对应该目录下现有 44 个任务 JSON，按 `doc_audacity.md` 的组织方式整理，但由于这是跨应用工作流数据而非单应用功能树，章节内容会更强调初始化方式、跨应用联动和验证模式。

### 0.0 2026-04-02 复核更新

1. 对 L1 / L2 进行了语义难度复核，4 个原先标为 L1 的代码修复任务已提升为 L2：`3b925362`、`8157f31d`、`d8ceb1ff`、`fac50a62`。
2. 重写了 3 个原本融合较生硬的 Chrome + VS Code 任务，使 Chrome 页面成为任务来源而非独立占位动作：`54318a50`、`7654b5dc`、`4f35b6e1`。
3. 修复了 `check_bookmark_contains_url` 未从 `desktop_env.evaluators.metrics` 导出的问题；此前所有依赖该函数的任务都可能直接在 evaluator 装配阶段失败。
4. 继续复核 L3 后，将 2 个偏弱的 L3 任务下调到 L2：`51687b07`、`f1a30ea3`。
5. 同时将 2 个保留在 L3 的任务改为静态资产驱动的自然工作流，并新增了 `assets/mutil_app_new_xt/` 下的本地 handoff HTML 与 logo 资产：`5811683a`、`abe04a95`。
6. 继续补充了 4 个新的 L3 任务，其中 2 个采用本地 HTML + 资产驱动，2 个采用 handoff JSON + 配置迁移 / 代码修复驱动：`e4c1b218`、`7c3ae54d`、`b6f8b62f`、`c91a2f7d`。
7. 当前 JSON 任务分布以目录中的实际文件和 `difficulty` 字段为准：L1=16、L2=18、L3=10。
8. 下文详细任务说明主要保留原整理顺序；如与最新 L1/L2/L3 分层有差异，以本节复核结论和任务 JSON 为准。

## 0. 多应用任务验证策略

### 0.1 数据集定位

`mutil_app_new_xt` 不是围绕单一应用操作设计，而是围绕 **OS + VS Code + Chrome** 的组合式工作流设计。任务主要覆盖以下几类场景：

1. 从本地 JSON / HTML / Markdown / TXT 规格中读取要求，再同步到 VS Code 设置或项目文件。
2. 用 Chrome 打开本地页面或在线文档，随后在 VS Code 中完成配置、迁移或修复。
3. 借助终端完成目录创建、文件统计、Git 初始化、审计汇总，再结合 VS Code 设置或 Chrome 参考页。
4. 基于故障项目、测试脚本和文档页，完成代码修复并输出交付标记文件。

### 0.2 核心验证思路

这批任务的验证不依赖截图比对，而是依赖以下几类**可程序化检查的最终状态**：

1. 文件内容：如 `settings.json`、`package.json`、`_config.yml`、`README.md`、`*.txt`。
2. 命令行输出：如 `cat`、`ls`、目录存在性检查、统计结果文本。
3. 浏览器状态：当前活动标签 URL、书签栏内容、浏览器偏好状态。
4. 代码正确性：对被修复的 Python 文件运行给定测试脚本，要求测试通过。

### 0.3 评估器通用模式

多应用任务通常采用多指标合取验证，常见结构如下：

```json
{
  "evaluator": {
    "func": [
      "check_include_exclude",
      "check_json_settings",
      "is_expected_active_tab_approximate"
    ],
    "result": [
      {"type": "vm_command_line", "command": "cat ...", "shell": true},
      {"type": "vm_file", "path": "/home/user/.config/Code/User/settings.json", "dest": "settings.json"},
      {"type": "active_tab_info"}
    ],
    "expected": [
      {"type": "rule", "rules": {"include": ["..."], "exclude": []}},
      {"type": "rule", "rules": {"expected": {"editor.tabSize": 4}}},
      {"type": "rule", "rules": {"type": "url", "url": "https://..."}}
    ],
    "conj": "and"
  }
}
```

### 0.4 验证函数来源

虽然目录提示为 `desktop_env/evaluators/metrics`，但这批任务实际复用了多个评估器文件，而不是集中在单一模块：

| 文件 | 作用 |
|---|---|
| `desktop_env/evaluators/metrics/general.py` | 通用文本包含 / 排除检查、JSON / YAML 结构检查 |
| `desktop_env/evaluators/metrics/vscode.py` | VS Code `settings.json` 检查、Python 测试套执行 |
| `desktop_env/evaluators/metrics/chrome.py` | Chrome 当前活动标签 URL 检查 |
| `desktop_env/evaluators/metrics/mutil_apps_new.py` | 本目录专用的书签 URL 子串检查 |
| `desktop_env/evaluators/metrics/__init__.py` | 统一导出并注册上述评估函数 |

---

## 1. 数据概览

### 1.1 规模与分布

| 维度 | 数值 |
|---|---|
| 总任务数 | **44** |
| L1 | **16** |
| L2 | **18** |
| L3 | **10** |
| `snapshot=os` | **22** |
| `snapshot=multi_apps` | **22** |
| `proxy=true` | **24** |
| `proxy=false` | **20** |
| `source=authors` | **44** |
| `possibility_of_env_change=low` | **44** |

### 1.2 应用组合分布

将 `related_apps` 按集合归并后，这批任务主要集中在以下几种组合：

| 应用组合 | 任务数 |
|---|---|
| Chrome + VS Code + OS | **27** |
| VS Code + OS | **9** |
| Chrome + VS Code | **3** |
| Chrome + OS | **1** |

### 1.3 初始化方式特征

| 配置动作 | 使用次数 | 说明 |
|---|---|---|
| `launch` | 96 | 启动 Chrome、VS Code、`socat`、`code` |
| `execute` | 30 | 用脚本动态生成输入规格、故障项目、测试文件 |
| `activate_window` | 15 | 聚焦 VS Code 窗口 |
| `chrome_open_tabs` | 13 | 预置参考页或本地 `file://` 页面 |

这说明该数据集的输入大多**不是静态上传素材**，而是通过 `config.execute` 在环境中即时生成任务所需文件、项目和测试桩。

### 1.4 结果类型分布

| result 类型 | 使用次数 | 说明 |
|---|---|---|
| `vm_file` | 45 | 下载并检查 JSON / YAML / Python / 文本文件 |
| `vm_command_line` | 43 | 读取文件文本、目录列表、目录存在性、终端统计结果 |
| `active_tab_info` | 25 | 验证 Chrome 当前活动标签是否为指定页面 |
| `bookmarks` | 3 | 验证书签树中是否存在目标 URL |
| `new_startup_page` | 1 | 验证 Chrome 启动页偏好 |
| `enable_do_not_track` | 1 | 验证 Chrome Do Not Track 偏好 |

---

## 2. 评估函数设计

### 2.1 当前任务实际使用的评估函数

| 函数名 | 文件 | 使用次数 | 描述 |
|---|---|---|---|
| `check_include_exclude` | `general.py` | 45 | 对命令输出或文本文件做包含 / 排除串验证 |
| `check_json_settings` | `vscode.py` | 26 | 检查 VS Code `settings.json` 是否包含目标键值 |
| `is_expected_active_tab_approximate` | `chrome.py` | 25 | 检查 Chrome 当前标签 URL，忽略 query 参数差异 |
| `check_python_file_by_test_suite` | `vscode.py` | 10 | 运行给定测试脚本，验证 Python 代码修复结果 |
| `check_json` | `general.py` | 9 | 检查 JSON / YAML 文件中的嵌套键和值 |
| `check_bookmark_contains_url` | `mutil_apps_new.py` | 3 | 在整棵 Chrome 书签树中查找包含特定子串的 URL |

### 2.2 函数语义说明

#### `check_include_exclude`

- 适用场景：`cat` 文本、`ls` 输出、目录存在性标记、确认文件内容。
- 规则形式：`{"include": [...], "exclude": [...]}`。
- 在本数据集中承担了大量“轻量级状态验证”职责。

#### `check_json`

- 适用场景：`extensions.json`、`package.json`、`site.json`、`project_meta.json`、YAML 配置文件。
- 规则形式：`expect` 列表中给出键路径、比较方法和参考值。
- 其中 4 个任务通过 `options: {"is_yaml": true}` 将其扩展到 YAML 校验。

#### `check_json_settings`

- 专门用于 VS Code 用户设置或工作区设置文件。
- 只要求目标键值存在并精确匹配，不要求文件与基准完全一致。

#### `check_python_file_by_test_suite`

- 通过动态加载测试文件执行 `test()`，属于这批数据中最强的功能性验证。
- 适合 `validator.py`、`slugify.py`、`format_alert.py` 一类代码修复任务。

#### `is_expected_active_tab_approximate`

- 用于验证 Chrome 最终是否保持在指定参考文档或本地 `file://` 页面。
- 该函数只检查当前活动标签的 URL，不验证阅读时长或浏览过程。

#### `check_bookmark_contains_url`

- 是 `mutil_app_new_xt` 中唯一的目录级自定义补充函数。
- 遍历整棵 Chrome 书签树，只要任一书签 URL 包含目标子串即判定成功。

### 2.3 验证器总体特点

1. 强依赖文件和文本状态，弱依赖 GUI 交互细节。
2. 对 VS Code 配置类任务特别友好，因为 `settings.json` 易于稳定校验。
3. 对 Chrome 行为的验证主要集中在“活动标签”和“书签树”，而不是过程级操作日志。
4. 代码修复任务通过测试套件获得了比纯文本检查更强的正确性保证。

---

## 3. 任务定义

> 说明：以下 `L1-1 / L2-1 / L3-1` 为本文档内部编号，便于阅读，不对应原始任务 UUID 排序语义。为便于后续 provenance 分析，本节已为每个任务补充 `source` 与英文 `能力分类`；如章节分组与最新分层存在差异，以第 0.0 节和任务 JSON 为准。`需要新评估函数` 在当前 44 个任务中均为 `❌`。

### 3.1 第一级（L1）—— 基础跨应用任务—— 20 个

L1 任务以 2 个应用联动或 1 个简单跨应用闭环为主，通常只要求：读取规格、改一个配置、写一个文件、或完成一个单点修复。

#### 任务 L1-1：VS Code 基础设置与交付记录

- **ID**：`0545144d-82cb-484d-842f-d5e4b6e58b2d`
- **task_slug**：`vscode_formatonsave_minimap_devnotes`
- **指令**：在 VS Code 用户设置中关闭 minimap、开启 Format on Save，并创建 `~/Desktop/dev_notes.txt`，首行精确为 `VS Code ready`。
- **涉及应用**：`vscode` + `os`
- **source**：https://code.visualstudio.com/docs/getstarted/settings；https://code.visualstudio.com/docs/editor/codebasics#_formatting；现实场景构造来源：开发者在新设备上完成 VS Code 初始收敛后，常见的“关闭 minimap + 开启保存即格式化 + 留下环境就绪标记”个人初始化需求
- **能力分类**：`Editor Settings Bootstrap`
- **前置数据**：仅启动 VS Code。
- **评估函数**：`check_json_settings` + `check_include_exclude`
- **result**：`settings.json` + `cat ~/Desktop/dev_notes.txt`
- **验证逻辑**：检查两个 VS Code 设置项是否生效，并确认交付文本包含目标语句。
- **需要新评估函数**：❌

#### 任务 L1-2：团队编辑规范应用并留档

- **ID**：`0b1b6179-db02-408c-a1cc-f6f1408829ed`
- **task_slug**：`team_editor_spec_apply_vscode_artifact`
- **指令**：读取 `~/.team_editor_spec` 中的 `tabSize`、`fontSize`、`lineHeight`，写入 VS Code 用户设置，并将原规范内容完整复制到 `~/Desktop/applied_editor_spec.txt`。
- **涉及应用**：`os` + `vscode`
- **source**：https://code.visualstudio.com/docs/getstarted/settings；https://code.visualstudio.com/docs/editor/codebasics；现实场景构造来源：团队成员按共享 editor spec 同步字号、行高与缩进，并留存应用结果供交接核对的常见入项流程
- **能力分类**：`Spec-to-Settings Transcription`
- **前置数据**：环境中已有团队规范文件。
- **评估函数**：`check_json_settings` + `check_include_exclude`
- **result**：`settings.json` + `cat ~/Desktop/applied_editor_spec.txt`
- **验证逻辑**：验证三项设置值正确，并确认留档文件包含原规范内容。
- **需要新评估函数**：❌

#### 任务 L1-3：从本地 HTML 读取偏好并同步到 VS Code

- **ID**：`152e5b37-c431-4143-90b5-1e135dd0904c`
- **task_slug**：`chrome_local_html_read_vscode_config`
- **指令**：用 Chrome 通过 `file://` 打开 `~/Desktop/editor_prefs.html`，读取其中的 `tabSize=4`、`fontSize=15`，同步到 VS Code 用户设置，完成时 Chrome 仍需停留在该本地页面。
- **涉及应用**：`chrome` + `vscode`
- **source**：https://code.visualstudio.com/docs/getstarted/settings；现实场景构造来源：团队把推荐编辑器参数放在本地 handoff HTML 中，要求成员边看说明页边同步到本机 VS Code 的常见入职配置流程
- **能力分类**：`Local HTML Settings Sync`
- **前置数据**：本地 HTML 偏好页已存在。
- **评估函数**：`is_expected_active_tab_approximate` + `check_json_settings`
- **result**：`active_tab_info` + `settings.json`
- **验证逻辑**：确认 Chrome 活动页仍是本地 HTML，且 VS Code 设置值准确。
- **需要新评估函数**：❌

#### 任务 L1-4：按 JSON 规格创建日志路径并配置编辑器

- **ID**：`26124979-e7ed-4e87-80b7-dd2fe745d88f`
- **task_slug**：`spec_json_vscode_project_dir_setup`
- **指令**：读取 `~/Desktop/project_spec.json`，按其中要求设置 `editor.tabSize`、`editor.wordWrap`，并用终端创建 `logPath` 指向的目录和空日志文件。
- **涉及应用**：`os` + `vscode`
- **source**：https://code.visualstudio.com/docs/getstarted/settings；现实场景构造来源：项目 kickoff 时从 JSON 规格一次性落地日志目录与编辑器默认值的轻量脚手架需求
- **能力分类**：`JSON Spec Environment Bootstrap`
- **前置数据**：`config.execute` 预先生成规格 JSON。
- **评估函数**：`check_json_settings` + `check_include_exclude`
- **result**：`settings.json` + 针对日志文件的命令输出
- **验证逻辑**：检查 VS Code 设置正确，并确认日志路径已按规格创建。
- **需要新评估函数**：❌

#### 任务 L1-5：正则文档辅助下修复邮箱校验器

- **ID**：`3b925362-bdda-4dd6-8b4c-79f86e0df9c0`
- **task_slug**：`email_validator_bugfix_with_regex_docs`
- **指令**：阅读 `ISSUE.txt`，在 Chrome 打开 Python 正则文档，用 VS Code 修复 `validator.py`，使测试通过，并创建 `FIXED.txt`。
- **涉及应用**：`chrome` + `vscode` + `os`
- **source**：https://docs.python.org/3/library/re.html；现实场景构造来源：表单校验 bug 修复时，开发者借助正则官方文档收敛邮箱匹配规则的常见测试驱动维护场景
- **能力分类**：`Regex-Guided Validator Repair`
- **前置数据**：`config.execute` 生成故障项目、问题描述和测试文件。
- **评估函数**：`check_python_file_by_test_suite` + `is_expected_active_tab_approximate` + `check_include_exclude`
- **result**：修复后的 Python 文件 + Chrome 活动标签 + `cat FIXED.txt`
- **验证逻辑**：测试通过、Chrome 最终保持文档标签为活动页、交付标记文件文本正确。
- **需要新评估函数**：❌

#### 任务 L1-6：启用 Chrome Do Not Track 并设置 VS Code 字号

- **ID**：`54318a50-1de1-4179-b9db-f3dbd5d80d9f`
- **task_slug**：`privacy_checklist_dnt_and_editor_fontsize`
- **指令**：在 Chrome 中启用 Do Not Track，同时在 VS Code 用户设置中将编辑器字号设为 16。
- **涉及应用**：`chrome` + `vscode`
- **source**：https://support.google.com/chrome/answer/2790761；https://code.visualstudio.com/docs/getstarted/settings；现实场景构造来源：隐私评审前先统一浏览器 Do Not Track 与共享演示字号设置的常见合规准备流程
- **能力分类**：`Privacy-and-Editor Sync`
- **前置数据**：无额外种子文件。
- **评估函数**：浏览器偏好 getter + `check_json_settings`
- **result**：`enable_do_not_track` + `settings.json`
- **验证逻辑**：验证 Chrome 隐私偏好已开启，且字号设置为 16。
- **需要新评估函数**：❌

#### 任务 L1-7：为 Python 文档建立书签并写入链接文件

- **ID**：`69fc292d-39d0-41d0-9ed9-388bc05cd55d`
- **task_slug**：`chrome_bookmark_python_docs_file`
- **指令**：将已打开的 Python 3 文档加入书签栏，并在 `~/Desktop/dev_links.txt` 第一行写入 `https://docs.python.org/3/`。
- **涉及应用**：`chrome` + `os`
- **source**：https://support.google.com/chrome/answer/188842；https://docs.python.org/3/；现实场景构造来源：开发者把高频 API 文档加入书签栏，并在桌面维护一份快速链接清单的常见知识检索习惯
- **能力分类**：`Bookmark-and-Link Capture`
- **前置数据**：Chrome 预先打开 Python 文档页。
- **评估函数**：`check_bookmark_contains_url` + `check_include_exclude`
- **result**：`bookmarks` + `cat ~/Desktop/dev_links.txt`
- **验证逻辑**：验证书签树包含目标文档 URL，并确认文本文件中记录了链接。
- **需要新评估函数**：❌

#### 任务 L1-8：根据交接 JSON 创建工作区推荐配置

- **ID**：`6d1f60ca-ea94-4a09-8886-ddef96f1fd8a`
- **task_slug**：`workspace_recommendations_from_handoff_json`
- **指令**：读取 `~/Desktop/editor_handoff.json`，在 `~/Desktop/ml-dashboard/.vscode/` 下创建 `extensions.json` 与 `settings.json`，分别写入推荐扩展以及 `tabSize`、`trimTrailingWhitespace`。
- **涉及应用**：`os` + `vscode`
- **source**：https://code.visualstudio.com/docs/editor/multi-root-workspaces；https://code.visualstudio.com/docs/editor/extension-marketplace；现实场景构造来源：项目交接时常见的“根据 handoff JSON 生成 .vscode 推荐扩展和工作区设置”初始化需求
- **能力分类**：`Workspace Handoff Bootstrap`
- **前置数据**：`config.execute` 生成 handoff JSON，并创建项目目录。
- **评估函数**：`check_json` + `check_json_settings`
- **result**：`.vscode/extensions.json` + `.vscode/settings.json`
- **验证逻辑**：检查推荐扩展数组和工作区设置均与交接 JSON 对齐。
- **需要新评估函数**：❌

#### 任务 L1-9：Chrome 启动页设为新标签页并启用自动换行

- **ID**：`7654b5dc-1acb-401d-9c81-13fed5fbf55e`
- **task_slug**：`startup_guide_new_tab_and_word_wrap`
- **指令**：将 Chrome 启动页设置为 New Tab page，并在 VS Code 用户设置中开启 `wordWrap`。
- **涉及应用**：`chrome` + `vscode`
- **source**：https://support.google.com/chrome/answer/95314；https://code.visualstudio.com/docs/editing/codebasics#_how-do-i-turn-on-word-wrap；现实场景构造来源：新设备开工前统一浏览器启动行为与编辑器换行策略的常见个人环境整理流程
- **能力分类**：`Browser Startup Alignment`
- **前置数据**：无。
- **评估函数**：启动页偏好 getter + `check_json_settings`
- **result**：`new_startup_page` + `settings.json`
- **验证逻辑**：验证 Chrome 启动页偏好正确，且 VS Code `editor.wordWrap` 已开启。
- **需要新评估函数**：❌

#### 任务 L1-10：书签化 ESLint 扩展页并写设置说明

- **ID**：`7e92f083-61ca-4af4-b560-b4fd43c11743`
- **task_slug**：`chrome_bookmark_eslint_vscode_config_note`
- **指令**：在 Chrome 打开并书签化 ESLint 扩展页，在 VS Code 中关闭 minimap、开启括号对着色，并写 `~/Desktop/setup_notes.txt` 记录完成情况。
- **涉及应用**：`chrome` + `vscode` + `os`
- **source**：https://support.google.com/chrome/answer/188842；https://marketplace.visualstudio.com/items?itemName=dbaeumer.vscode-eslint；现实场景构造来源：新机器装配时常见的“先收藏核心扩展页，再同步基础显示设置并留下 setup note”开发环境启动流程
- **能力分类**：`Extension Bookmark Setup`
- **前置数据**：无，Chrome 直接打开 Marketplace URL。
- **评估函数**：`check_bookmark_contains_url` + `check_json_settings` + `check_include_exclude`
- **result**：`bookmarks` + `settings.json` + `cat setup_notes.txt`
- **验证逻辑**：书签、VS Code 设置和说明文本三项同时满足。
- **需要新评估函数**：❌

#### 任务 L1-11：CSV 文档辅助下修复汇总脚本

- **ID**：`8157f31d-3e6f-4342-aee9-82e5ed7426b9`
- **task_slug**：`csv_summary_bugfix_from_module_docs`
- **指令**：根据 `ISSUE.txt` 和 Python `csv` 文档修复 `summarize.py`，使测试通过，并创建 `SUMMARY_FIXED.txt`。
- **涉及应用**：`chrome` + `vscode` + `os`
- **source**：https://docs.python.org/3/library/csv.html；现实场景构造来源：报表脚本把 CSV 表头算入统计时，开发者对照 csv 模块文档修复汇总逻辑的常见数据处理维护场景
- **能力分类**：`CSV Parser Bugfix`
- **前置数据**：`config.execute` 生成带缺陷的汇总项目。
- **评估函数**：`check_python_file_by_test_suite` + `is_expected_active_tab_approximate` + `check_include_exclude`
- **result**：Python 文件 + Chrome 活动标签 + `cat SUMMARY_FIXED.txt`
- **验证逻辑**：要求代码修复正确、文档标签保持打开、交付标记文件文本精确。
- **需要新评估函数**：❌

#### 任务 L1-12：根据参考代码行数设置 `wordWrapColumn`

- **ID**：`a02f4ed4-e918-4109-b3e3-a746a0260187`
- **task_slug**：`wc_lines_vscode_wrapcolumn_from_file`
- **指令**：用终端统计 `/tmp/reference_code.py` 的行数，将整数写入 `~/Desktop/line_count.txt`，并将同一数值写入 VS Code `editor.wordWrapColumn`。
- **涉及应用**：`os` + `vscode`
- **source**：https://code.visualstudio.com/docs/editing/codebasics#_how-do-i-turn-on-word-wrap；现实场景构造来源：团队用参考代码样本反推统一换行列宽，再写回个人编辑器默认值的轻量规范同步需求
- **能力分类**：`Line-Count-Based Formatting`
- **前置数据**：参考文件已存在。
- **评估函数**：`check_include_exclude` + `check_json_settings`
- **result**：`cat line_count.txt` + `settings.json`
- **验证逻辑**：验证计数文件内容正确，并确认 `wordWrapColumn` 与该整数一致。
- **需要新评估函数**：❌

#### 任务 L1-13：基于本地 brief 更新站点 YAML

- **ID**：`aa8fb8bf-6f67-44e0-b51b-93a116afc899`
- **task_slug**：`profile_yaml_update_from_local_brief`
- **指令**：在 Chrome 打开 `PROFILE_BRIEF.txt`，读取新的人名、邮箱、角色信息；备份 `_config.yml` 为 `_config.yml.bak` 后，在 VS Code 中更新原 YAML。
- **涉及应用**：`chrome` + `vscode` + `os`
- **source**：https://docs.github.com/en/pages；现实场景构造来源：个人站点换人维护时，根据本地 profile brief 更新 Jekyll/YAML 资料并保留备份的常见 handoff 流程
- **能力分类**：`Local Brief YAML Migration`
- **前置数据**：`config.execute` 生成 brief 和旧 YAML。
- **评估函数**：`is_expected_active_tab_approximate` + `check_json` + `check_include_exclude`
- **result**：`active_tab_info` + `_config.yml` + 目录列表
- **验证逻辑**：确认 Chrome 停留在 brief 页面、YAML 字段被正确更新、备份文件存在。
- **需要新评估函数**：❌

#### 任务 L1-14：按工作区政策页生成项目级设置

- **ID**：`b92fb94a-9dd5-43ff-8c5a-c6993968aea0`
- **task_slug**：`workspace_policy_html_to_project_settings`
- **指令**：用 Chrome 打开 `workspace_policy.html`，在 `~/Desktop/ui-tooling/.vscode/settings.json` 中写入相对行号、末尾换行和 `files.exclude`，并创建 `POLICY_ACK.txt`。
- **涉及应用**：`chrome` + `vscode` + `os`
- **source**：https://code.visualstudio.com/docs/getstarted/settings；https://code.visualstudio.com/docs/editor/multi-root-workspaces；现实场景构造来源：前端项目把工作区显示规则写进本地 policy 页面，要求执行人按页生成 .vscode 设置并回执确认的常见协作流程
- **能力分类**：`Policy-to-Workspace Settings`
- **前置数据**：本地策略页和目标项目目录已存在。
- **评估函数**：`is_expected_active_tab_approximate` + `check_json_settings` + `check_include_exclude`
- **result**：`active_tab_info` + 工作区 `settings.json` + `cat POLICY_ACK.txt`
- **验证逻辑**：验证本地策略页已打开，项目级设置文件值正确，并存在确认文本。
- **需要新评估函数**：❌

#### 任务 L1-15：依据交接说明更新站点 JSON 元数据

- **ID**：`b95ce0eb-98a1-4192-88e2-168dc6097601`
- **task_slug**：`site_json_update_from_handoff_note`
- **指令**：阅读项目中的 `HANDOFF.txt`，备份 `site.json`，将 `title`、`owner`、`contactEmail` 更新后写入 `RELEASE_NOTE.txt`。
- **涉及应用**：`os` + `vscode`
- **source**：https://docs.github.com/en/pages；现实场景构造来源：站点发布前根据 handoff note 修正 JSON 元数据、补备份并留下 release note 的常见内容上线流程
- **能力分类**：`Handoff Metadata Refresh`
- **前置数据**：`config.execute` 生成旧 `site.json` 和 handoff 文本。
- **评估函数**：`check_json` + `check_include_exclude` + `check_include_exclude`
- **result**：`site.json` + `cat RELEASE_NOTE.txt` + 目录列表
- **验证逻辑**：检查 JSON 字段更新正确、发布说明文本存在、备份文件存在。
- **需要新评估函数**：❌

#### 任务 L1-16：设置延迟自动保存并写入 shell alias

- **ID**：`cd3cbf4e-c32e-412d-b74c-ce0633e9d7f5`
- **task_slug**：`vscode_autosave_delay_alias_bashrc`
- **指令**：在 VS Code 中设置 `files.autoSave=afterDelay` 与 `files.autoSaveDelay=1000`，并向 `~/.bashrc` 添加 `alias gs='git status'`。
- **涉及应用**：`vscode` + `os`
- **source**：https://code.visualstudio.com/docs/editing/codebasics#_save-auto-save；现实场景构造来源：开发者在整理个人环境时常见的“启用延迟自动保存 + 添加 git status shell alias”效率配置需求
- **能力分类**：`Auto-Save and Shell Alias`
- **前置数据**：无。
- **评估函数**：`check_json_settings` + `check_include_exclude`
- **result**：`settings.json` + `cat ~/.bashrc`
- **验证逻辑**：校验自动保存相关键值，并确认 alias 被写入 shell 配置。
- **需要新评估函数**：❌

#### 任务 L1-17：从发布清单页同步设置并记录文档链接

- **ID**：`d5bc8185-21b3-4c7a-ad02-9e564549e1a6`
- **task_slug**：`release_plan_html_to_vscode_and_note`
- **指令**：通过 `file://` 打开 `release_plan.html`，按页面要求设置相对行号和末尾换行，并把页面中的 docs URL 写到 `~/Desktop/release_ready.txt`。
- **涉及应用**：`chrome` + `vscode` + `os`
- **source**：https://code.visualstudio.com/docs/getstarted/settings；现实场景构造来源：发布负责人把操作清单导出为本地 HTML，要求执行人按页同步设置并记录后续文档入口的常见 release ready 流程
- **能力分类**：`HTML Checklist Settings Sync`
- **前置数据**：本地 HTML 页面已存在。
- **评估函数**：`is_expected_active_tab_approximate` + `check_json_settings` + `check_include_exclude`
- **result**：`active_tab_info` + `settings.json` + `cat release_ready.txt`
- **验证逻辑**：验证本地页面仍为活动页、VS Code 设置正确、记录文件中包含页面给出的文档 URL。
- **需要新评估函数**：❌

#### 任务 L1-18：按工作区 manifest 建项目并写注释文件

- **ID**：`d6f02b62-4b3e-4ac0-ba56-07b8d24e532f`
- **task_slug**：`workspace_manifest_bootstrap_and_settings`
- **指令**：读取 `workspace_manifest.json` 中的项目名、notes 路径与编辑器要求，用终端创建目录和 notes 文件，并把项目名写入该文件；再同步 `tabSize` 与 `insertFinalNewline` 到 VS Code。
- **涉及应用**：`os` + `vscode`
- **source**：https://code.visualstudio.com/docs/editor/multi-root-workspaces；https://code.visualstudio.com/docs/getstarted/settings；现实场景构造来源：小团队用 workspace manifest 一次性生成项目目录、注释文件和基础编辑器规则的常见项目起步流程
- **能力分类**：`Manifest-Driven Workspace Bootstrap`
- **前置数据**：`config.execute` 生成 manifest。
- **评估函数**：`check_include_exclude` + `check_json_settings` + `check_include_exclude`
- **result**：notes 文件文本 + `settings.json` + 目录 / 文件检查输出
- **验证逻辑**：确保 notes 文件内容正确，VS Code 设置与 manifest 一致，目标路径存在。
- **需要新评估函数**：❌

#### 任务 L1-19：字符串方法文档辅助下修复 slugify 工具

- **ID**：`d8ceb1ff-ed10-41bd-8cd5-f9fe098045af`
- **task_slug**：`slugify_bugfix_from_issue_and_docs`
- **指令**：依据 `BUG_REPORT.txt` 与 Python string methods 文档修复 `slugify.py`，使测试通过，并创建 `FIX_DONE.txt`。
- **涉及应用**：`chrome` + `vscode` + `os`
- **source**：https://docs.python.org/3/library/stdtypes.html#string-methods；现实场景构造来源：slug 生成逻辑异常时，开发者借助 string methods 文档修复清洗和替换规则的常见内容平台维护场景
- **能力分类**：`String-Method Slug Repair`
- **前置数据**：`config.execute` 生成缺陷项目和测试。
- **评估函数**：`check_python_file_by_test_suite` + `is_expected_active_tab_approximate` + `check_include_exclude`
- **result**：Python 文件 + `active_tab_info` + `cat FIX_DONE.txt`
- **验证逻辑**：要求修复通过测试、文档页仍为活动标签、交付标记正确。
- **需要新评估函数**：❌

#### 任务 L1-20：`splitlines` 文档辅助下修复报告解析器

- **ID**：`fac50a62-d441-44ac-8f46-ae29f24abe9a`
- **task_slug**：`report_parser_bugfix_with_splitlines_docs`
- **指令**：阅读 `ISSUE.txt`，打开 Python `splitlines` 文档，修复 `parser.py` 对空行的处理，并写入 `PARSER_FIXED.txt`。
- **涉及应用**：`chrome` + `vscode` + `os`
- **source**：https://docs.python.org/3/library/stdtypes.html#str.splitlines；现实场景构造来源：文本报告解析器在空行处理上回归后，开发者对照 splitlines 文档修复分段逻辑的常见测试驱动修复场景
- **能力分类**：`Splitlines Parser Repair`
- **前置数据**：`config.execute` 生成解析器项目。
- **评估函数**：`check_python_file_by_test_suite` + `is_expected_active_tab_approximate` + `check_include_exclude`
- **result**：Python 文件 + 活动标签 + `cat PARSER_FIXED.txt`
- **验证逻辑**：解析器测试通过、文档页保留为活动页、标记文件内容正确。
- **需要新评估函数**：❌

#### L1 小结

1. L1 任务主要集中在 VS Code 用户设置、工作区文件生成、本地网页读取和简单代码修复。
2. 在原整理顺序中的 20 个 L1 条目里，有 4 个属于“文档辅助 + 代码修复 + 测试验证”模式；按当前 JSON 实际分层，这 4 个任务已提升到 L2。
3. 其余任务多为规格同步、浏览器偏好设置、书签管理和基础项目引导。

---

### 3.2 第二级（L2）—— 复合跨应用任务—— 12 个

L2 任务开始出现更完整的工作流闭环：读取规范、创建项目结构、更新配置、打开参考页、写审计结果，通常需要跨两个以上应用来回切换。

#### 任务 L2-1：字典文档辅助下修复 JSON 合并逻辑

- **ID**：`1e5f3455-2940-42e0-ad41-bcf0710563e8`
- **task_slug**：`json_merge_bugfix_with_dict_docs`
- **指令**：阅读 `ISSUE.md`，打开 Python dictionary methods 文档，修复 `jsonmerge_app/` 中用户配置被默认值覆盖的问题，并创建 `MERGE_FIXED.txt`。
- **涉及应用**：`chrome` + `vscode` + `os`
- **source**：https://docs.python.org/3/library/stdtypes.html#dict.update；现实场景构造来源：配置合并逻辑回归时，开发者对照标准库文档修复 defaults 覆盖用户配置问题的常见 Python 维护场景
- **能力分类**：`Doc-Guided Merge Bugfix`
- **前置数据**：`config.execute` 生成缺陷项目与测试。
- **评估函数**：`check_python_file_by_test_suite` + `is_expected_active_tab_approximate` + `check_include_exclude`
- **验证逻辑**：测试通过、参考文档页为当前活动标签、修复确认文件存在且文本正确。
- **需要新评估函数**：❌

#### 任务 L2-2：Git 初始化与 VS Code 显示设置

- **ID**：`2824f346-6ec2-4cf8-968c-99ccbd3421d8`
- **task_slug**：`git_project_init_gitignore_vscode_config`
- **指令**：用终端创建 `~/Desktop/my_project` 并初始化 Git 仓库，写入两行 `.gitignore`，再在 VS Code 中设置 `renderWhitespace=all` 和 `tabSize=4`。
- **涉及应用**：`os` + `vscode`
- **source**：https://git-scm.com/docs/gitignore；https://code.visualstudio.com/docs/getstarted/settings；现实场景构造来源：新仓库创建时常见的“终端初始化 Git + 写 .gitignore + 收敛 VS Code 显示设置”开工流程
- **能力分类**：`Git Bootstrap and Editor Setup`
- **前置数据**：无。
- **评估函数**：`check_include_exclude` + `check_include_exclude` + `check_json_settings`
- **验证逻辑**：分别检查 Git 仓库 / `.gitignore` 结果和 VS Code 设置是否完成。
- **需要新评估函数**：❌

#### 任务 L2-3：`urljoin` 文档辅助下修复 API 客户端

- **ID**：`2de9abd5-cc88-4f50-8b7c-b58a6c0a7108`
- **task_slug**：`urljoin_bugfix_with_urllib_docs`
- **指令**：阅读 `ISSUE.md`，打开 `urllib.parse.urljoin` 文档，修复 `url_client/` 里 base URL 和 endpoint 拼接错误的问题，并创建 `FIX_NOTE.txt`。
- **涉及应用**：`chrome` + `vscode` + `os`
- **source**：https://docs.python.org/3/library/urllib.parse.html#urllib.parse.urljoin；现实场景构造来源：后端 API 客户端在 base URL 与 endpoint 规范不一致时，开发者对照 urllib 文档修复拼接逻辑的常见维护场景
- **能力分类**：`URL Assembly Bugfix`
- **前置数据**：`config.execute` 生成带缺陷的客户端项目。
- **评估函数**：`check_python_file_by_test_suite` + `is_expected_active_tab_approximate` + `check_include_exclude`
- **验证逻辑**：测试通过、参考文档保持打开、修复说明文本正确。
- **需要新评估函数**：❌

#### 任务 L2-4：学术站点交接迁移

- **ID**：`2ea8032e-8e28-4c23-b812-3795ccac8609`
- **task_slug**：`academic_site_config_migration_from_handoff`
- **指令**：在 Chrome 查看 `academicpages.github.io` 结构，再阅读项目中的 `HANDOFF.txt`，更新 `academic_site/_config.yml` 并创建 `_config.yml.bak`。
- **涉及应用**：`chrome` + `vscode` + `os`
- **source**：https://academicpages.github.io/；https://docs.github.com/en/pages；现实场景构造来源：学术主页换人维护时，常见的“参考线上示例站结构 + 读取 handoff + 更新本地 _config.yml 并备份”迁移流程
- **能力分类**：`Academic Site Handoff Migration`
- **前置数据**：`config.execute` 生成旧站点配置、handoff 文本与项目目录。
- **评估函数**：`is_expected_active_tab_approximate` + `check_json` + `check_include_exclude`
- **验证逻辑**：确认参考站点页为活动标签、YAML 中站点所有者信息更新正确、备份文件存在。
- **需要新评估函数**：❌

#### 任务 L2-5：系统信息采集 + VS Code 配置 + 本地预览

- **ID**：`3f797f22-da77-4bc5-a81e-5ef5f204fc5d`
- **task_slug**：`sysinfo_capture_vscode_config_chrome_local`
- **指令**：运行 `uname -a` 保存到 `~/Desktop/sysinfo.txt`，在 VS Code 中设置相对行号和末尾换行，再用 Chrome 通过 `file://` 打开这个文本文件预览。
- **涉及应用**：`os` + `vscode` + `chrome`
- **source**：https://code.visualstudio.com/docs/getstarted/settings；现实场景构造来源：排障或远程协作前，先抓取系统信息、收敛编辑器设置，再用浏览器快速预览产物的常见运维辅助流程
- **能力分类**：`System Snapshot and Preview`
- **前置数据**：无。
- **评估函数**：`check_include_exclude` + `check_json_settings` + `is_expected_active_tab_approximate`
- **验证逻辑**：系统信息文件存在且内容合理、VS Code 设置正确、Chrome 活动页为本地 `sysinfo.txt`。
- **需要新评估函数**：❌

#### 任务 L2-6：团队配置驱动的新项目引导

- **ID**：`42a9a163-a7b0-4bf0-9b9b-6057dc90fcc2`
- **task_slug**：`team_json_bootstrap_dir_vscode_exclude_chrome`
- **指令**：读取 `team_config.json`，在桌面创建 `DataPipeline/README.md`，按配置设置 `editor.tabSize` 和 `files.exclude`，再打开 `repoDocsUrl`。
- **涉及应用**：`chrome` + `os` + `vscode`
- **source**：https://code.visualstudio.com/docs/editor/multi-root-workspaces；现实场景构造来源：团队 handoff JSON 驱动新项目目录、README 和 files.exclude 规则落地，并顺手打开协作文档的常见入场流程
- **能力分类**：`Config-Driven Project Bootstrap`
- **前置数据**：`config.execute` 生成团队配置 JSON。
- **评估函数**：`check_include_exclude` + `check_json_settings` + `check_include_exclude` + `is_expected_active_tab_approximate`
- **验证逻辑**：README 内容正确、VS Code 设置与 JSON 一致、`files.exclude` 项完整、文档 URL 已在 Chrome 活动标签中打开。
- **需要新评估函数**：❌

#### 任务 L2-7：保存 VS Code 文档 URL 并设置自动保存

- **ID**：`4f35b6e1-15b6-4e66-ae1f-f005139a8093`
- **task_slug**：`editing_handoff_url_and_vscode_settings`
- **指令**：用 Chrome 打开 VS Code keybindings 文档页，把完整 URL 保存到 `~/Desktop/docs_url.txt`，并在 VS Code 中设置 `files.autoSave=onWindowChange` 与 `editor.linkedEditing=true`。
- **涉及应用**：`chrome` + `vscode` + `os`
- **source**：https://code.visualstudio.com/docs/getstarted/keybindings；https://code.visualstudio.com/docs/editing/codebasics#_save-auto-save；现实场景构造来源：文档团队通过 handoff 页面分发支持文档链接和编辑偏好，要求执行人同步保存策略并留存 URL 的常见协作流程
- **能力分类**：`Handoff URL Extraction`
- **前置数据**：无。
- **评估函数**：`check_include_exclude` + `check_json_settings`
- **验证逻辑**：验证 URL 已被正确写入文件，且 VS Code 两项设置已生效。
- **需要新评估函数**：❌

#### 任务 L2-8：解析开发说明并同步 ruler 配置

- **ID**：`7452efa6-2655-4a59-bd81-5bfbab581ad2`
- **task_slug**：`devnotes_parse_vscode_rulers_chrome_docs`
- **指令**：读取 `~/Desktop/DEVNOTES.md` 中的 `tabSize`、`wrapColumn`、`rulerAt` 和 `docsUrl`，同步到 VS Code，并创建 `DEVNOTES.applied`，同时打开参考文档页。
- **涉及应用**：`os` + `vscode` + `chrome`
- **source**：https://code.visualstudio.com/docs/editor/codebasics；https://code.visualstudio.com/docs/getstarted/settings；现实场景构造来源：团队把 tab size、wrap column、ruler 和文档链接写进 DEVNOTES，要求成员解析后同步到 VS Code 的常见规范下发流程
- **能力分类**：`Devnotes-to-Editor Sync`
- **前置数据**：开发说明 Markdown 已存在。
- **评估函数**：`check_json_settings` + `is_expected_active_tab_approximate` + `check_include_exclude`
- **验证逻辑**：VS Code 三项设置正确、文档页打开、处理标记文件存在。
- **需要新评估函数**：❌

#### 任务 L2-9：Python 项目审计与 PEP 8 配置

- **ID**：`88d64722-8a52-4a19-bcd8-3e02ad61fcfb`
- **task_slug**：`python_pep8_project_audit_vscode_chrome`
- **指令**：递归统计 `/tmp/pyproject/` 下 Python 文件总行数，写 `audit_report.txt`，再按 PEP 8 要求设置 VS Code，并打开 PEP 8 官方文档。
- **涉及应用**：`os` + `vscode` + `chrome`
- **source**：https://peps.python.org/pep-0008/；https://code.visualstudio.com/docs/getstarted/settings；现实场景构造来源：接手 Python 仓库时，先做代码规模审计，再按 PEP 8 统一编辑器表现并打开规范原文的常见整备流程
- **能力分类**：`PEP8 Audit and Editor Alignment`
- **前置数据**：审计目标项目和 `requirements.txt` 已存在。
- **评估函数**：`check_include_exclude` + `check_json_settings` + `is_expected_active_tab_approximate`
- **验证逻辑**：审计报告文本、PEP 8 风格设置和文档页三者同时验证。
- **需要新评估函数**：❌

#### 任务 L2-10：按风格规范 JSON 审计项目并打开参考文档

- **ID**：`b0c06993-040c-4554-ba94-eb844eb85ab3`
- **task_slug**：`project_audit_from_spec_and_reference_docs`
- **指令**：读取 `audit_spec.json`，统计 `/tmp/audit_target/` 中 Python 文件数量和总行数，写入 `audit_summary.txt`，同步 `tabSize` 和 `rulers`，并打开 `docsUrl`。
- **涉及应用**：`os` + `vscode` + `chrome`
- **source**：https://peps.python.org/pep-0008/；https://code.visualstudio.com/docs/getstarted/settings；现实场景构造来源：技术负责人通过 audit spec 下发代码风格和统计口径，执行人据此完成仓库审计与编辑器同步的常见治理流程
- **能力分类**：`Spec-Driven Code Audit`
- **前置数据**：`config.execute` 生成审计规范和待审项目。
- **评估函数**：`check_include_exclude` + `check_json_settings` + `is_expected_active_tab_approximate`
- **验证逻辑**：审计摘要内容正确、VS Code 设置对齐规范、Chrome 文档页打开。
- **需要新评估函数**：❌

#### 任务 L2-11：根据 npm handoff 更新包元数据与 README

- **ID**：`b255560d-0a97-4914-aafe-310917fa3dfb`
- **task_slug**：`package_metadata_refresh_from_npm_handoff`
- **指令**：查看 `package.json` 文档页，读取 `widget-lib/HANDOFF.json`，更新 `package.json` 的 `name`、`description`、`repository.url`、`homepage`，同步修改 `README.md` 并备份 `package.json`。
- **涉及应用**：`chrome` + `vscode` + `os`
- **source**：https://docs.npmjs.com/cli/v10/configuring-npm/package-json；现实场景构造来源：npm 包交接时常见的“按 handoff 更新 package.json / README 并先备份旧元数据”发布准备流程
- **能力分类**：`Package Metadata Migration`
- **前置数据**：`config.execute` 生成旧 `package.json`、README 和 handoff 文件。
- **评估函数**：`is_expected_active_tab_approximate` + `check_json` + `check_include_exclude` + `check_include_exclude`
- **验证逻辑**：文档页打开、`package.json` 核心字段正确、README 提及新包名、备份文件存在。
- **需要新评估函数**：❌

#### 任务 L2-12：仓库扫描规范驱动的元数据更新

- **ID**：`dcd6f922-0976-40ba-bdf4-5d9a05d85432`
- **task_slug**：`scan_spec_audit_and_metadata_update`
- **指令**：根据 `scan_spec.json` 审计 `/tmp/knowledge_base/`，将统计结果写回 `~/Desktop/repo_audit/project_meta.json`，把 `status` 改为 `audited`，同步 VS Code 设置并打开参考文档。
- **涉及应用**：`os` + `vscode` + `chrome`
- **source**：https://code.visualstudio.com/docs/editor/codebasics；https://code.visualstudio.com/docs/getstarted/settings；现实场景构造来源：知识库仓库审计时常见的“依据 scan spec 更新 project_meta.json 并同步 VS Code 检查设置”元数据治理流程
- **能力分类**：`Repository Audit Metadata Update`
- **前置数据**：`config.execute` 生成扫描规范、待审目录和待更新元数据文件。
- **评估函数**：`check_json` + `check_json_settings` + `is_expected_active_tab_approximate`
- **验证逻辑**：JSON 中 `pythonFiles`、`markdownFiles`、`status` 更新正确，VS Code 设置对齐规范，Chrome 页签正确。
- **需要新评估函数**：❌

#### L2 小结

1. L2 相比 L1，更强调“从规格读取信息后驱动多个操作”的闭环。
2. 在原整理顺序中的 12 个 L2 条目里，既有代码修复，也有项目引导、项目审计、配置迁移和本地网页转设置；按当前 JSON，L2 总量已扩展到 18。
3. L2 已普遍采用三段式组合验证：文件 / 命令输出 + VS Code 设置 + Chrome 状态。

---

### 3.3 第三级（L3）—— 高级跨应用工作流—— 8 个

L3 任务通常包含 4 个以上动作，且经常把“配置迁移 + 代码修复 + 设置同步 + 文档保持打开”揉成一个完整流程。

#### 任务 L3-1：日志管道交接迁移与脚本修复

- **ID**：`36c5ad65-aaaa-417e-9dac-5f4051132653`
- **task_slug**：`log_pipeline_handoff_fix_and_config_migration`
- **指令**：读取 `log_pipeline/HANDOFF.json`，更新 `pipeline_config.yml` 中的 `appName` 和 `ownerEmail`，修复 `format_alert.py` 使测试通过，同步 VS Code `tabSize` 与 `ruler`，写 `MIGRATION_DONE.txt`，并保持日志文档页打开。
- **涉及应用**：`os` + `vscode` + `chrome`
- **source**：https://docs.python.org/3/library/logging.html；https://code.visualstudio.com/docs/getstarted/settings；现实场景构造来源：日志处理服务交接时常见的“按 handoff 迁移 YAML 配置 + 修复脚本 + 同步编辑器规范 + 写 migration 标记”完整维护流程
- **能力分类**：`Handoff-Driven Pipeline Migration`
- **前置数据**：`config.execute` 一次性生成 handoff、YAML 配置、缺陷脚本与测试。
- **评估函数**：`check_json` + `check_python_file_by_test_suite` + `check_json_settings` + `is_expected_active_tab_approximate` + `check_include_exclude`
- **验证逻辑**：同时验证 YAML 更新、代码修复、VS Code 设置、Chrome 文档页和迁移完成标记。
- **需要新评估函数**：❌

#### 任务 L3-2：Python 文件计数 + 多项编辑器配置 + 文档打开

- **ID**：`51687b07-7834-44a6-b62a-c6860810d8e4`
- **task_slug**：`py_count_vscode_multiconfig_chrome_docs`
- **指令**：统计 `/tmp/code_proj/` 下全部 `.py` 文件数量，写 `py_count.txt`，配置字号、行高、自动换行和去尾空白，并在 Chrome 打开 Python 文档主页。
- **涉及应用**：`os` + `vscode` + `chrome`
- **source**：https://docs.python.org/3/；https://code.visualstudio.com/docs/getstarted/settings；现实场景构造来源：代码走查前先统计 Python 文件规模，再统一字号、行高和换行设置并打开官方文档的常见开发准备流程
- **能力分类**：`Codebase Counting and Editor Tuning`
- **前置数据**：目标代码目录已存在。
- **评估函数**：`check_include_exclude` + `check_json_settings` + `is_expected_active_tab_approximate`
- **验证逻辑**：计数结果、四项 VS Code 配置和文档页状态同时满足。
- **需要新评估函数**：❌

#### 任务 L3-3：部署配置驱动的完整引导流程

- **ID**：`5811683a-fd91-418a-9c59-e9f306764875`
- **task_slug**：`deploy_package_bootstrap_with_local_launch_brief`
- **指令**：完全依据 `deploy_config.json` 创建日志目录、写环境摘要、同步 `tabSize` / `rulers` / `files.exclude`，并打开 `docsUrl`。
- **涉及应用**：`os` + `vscode` + `chrome`
- **source**：https://fastapi.tiangolo.com/；https://code.visualstudio.com/docs/getstarted/settings；现实场景构造来源：服务上线前常见的“依据 launch brief 和 deploy_config 生成目录、README、.env.example 与排除规则”部署包整理流程
- **能力分类**：`Config-Driven Service Bootstrap`
- **前置数据**：`config.execute` 生成部署配置 JSON。
- **评估函数**：`check_include_exclude` + `check_include_exclude` + `check_json_settings` + `is_expected_active_tab_approximate`
- **验证逻辑**：验证目录创建、摘要文本、VS Code 核心设置与文档页 URL，突出“配置驱动、禁止硬编码”的任务特征。
- **需要新评估函数**：❌

#### 任务 L3-4：CLI 工具跨文件修复与测试

- **ID**：`62565342-b5fd-45b0-a6f6-8beba649c76b`
- **task_slug**：`cli_tool_bugfix_from_issue_tests_and_docs`
- **指令**：阅读 `task_cli/ISSUE.md`，打开 Python f-string 文档，跨多个文件修复命令行状态格式化工具，并创建 `FIX_SUMMARY.txt`。
- **涉及应用**：`chrome` + `vscode` + `os`
- **source**：https://docs.python.org/3/tutorial/inputoutput.html#formatted-string-literals；现实场景构造来源：CLI 工具重构后格式串失效，开发者对照 f-string 文档跨文件修复并回填 issue 编号的常见命令行工具维护场景
- **能力分类**：`Cross-File CLI Repair`
- **前置数据**：`config.execute` 生成故障 CLI 项目和完整测试套。
- **评估函数**：`check_python_file_by_test_suite` + `is_expected_active_tab_approximate` + `check_include_exclude`
- **验证逻辑**：测试套全通过、Chrome 活动页是参考文档、修复摘要文件内容正确。
- **需要新评估函数**：❌

#### 任务 L3-5：作品集站点 YAML 迁移并修复脚本

- **ID**：`9fd8a238-9cf5-4bcb-9737-3d860ad86c61`
- **task_slug**：`portfolio_site_handoff_yaml_and_script_fix`
- **指令**：读取 `portfolio_site/HANDOFF.json`，更新 `_config.yml` 以匹配新 owner 信息，修复 `build_contact.py`，打开 handoff 中的参考文档，并写 `MIGRATION_DONE.txt`。
- **涉及应用**：`os` + `vscode` + `chrome`
- **source**：https://docs.github.com/en/pages；现实场景构造来源：作品集站点换人维护时常见的“按 handoff 更新 YAML、修联系人生成脚本、打开托管文档并写迁移标记”站点迁移流程
- **能力分类**：`Portfolio YAML Migration Repair`
- **前置数据**：`config.execute` 生成站点工程、handoff、故障脚本和测试。
- **评估函数**：`check_json` + `check_python_file_by_test_suite` + `is_expected_active_tab_approximate` + `check_include_exclude`
- **验证逻辑**：YAML 更新正确、脚本测试通过、文档页打开、迁移标记文件文本精确。
- **需要新评估函数**：❌

#### 任务 L3-6：Web 项目初始化 + 高级 VS Code 设置 + 书签

- **ID**：`abe04a95-081b-4afa-94f6-ed059abd515a`
- **task_slug**：`webapp_handoff_with_logo_and_css_reference`
- **指令**：通过终端创建 `webapp/` 目录结构、`.gitignore` 和 `src/main.py`，在 VS Code 中启用括号对着色、自动换行、末尾换行并设 `tabSize=2`，最后把 VS Code 官网加入书签栏。
- **涉及应用**：`os` + `vscode` + `chrome`
- **source**：https://developer.mozilla.org/en-US/docs/Web/CSS；https://support.google.com/chrome/answer/188842；现实场景构造来源：设计稿交接后常见的“创建 webapp 骨架、复制 logo、同步编辑器偏好并收藏 CSS 参考”前端启动流程
- **能力分类**：`Webapp Bootstrap and CSS Bookmark`
- **前置数据**：无。
- **评估函数**：`check_include_exclude` + `check_include_exclude` + `check_json_settings` + `check_bookmark_contains_url`
- **验证逻辑**：分别验证目录 / 文件初始化、`.gitignore` 内容、VS Code 设置和书签树状态。
- **需要新评估函数**：❌

#### 任务 L3-7：作品集 JSON 交接迁移 + 脚本修复 + 备份

- **ID**：`dba81463-c088-4cf3-9a68-53d2fa6b99be`
- **task_slug**：`portfolio_handoff_json_and_script_repair`
- **指令**：读取 `portfolio_handoff/HANDOFF.json`，更新 `site_config.json` 的 `title`、`owner`、`contactEmail`，创建 `site_config.json.bak`，修复 `build_signature.py`，打开参考文档，并写 `MIGRATION_DONE.txt`。
- **涉及应用**：`os` + `vscode` + `chrome`
- **source**：https://docs.github.com/en/pages；现实场景构造来源：作品集项目 JSON 配置交接时常见的“备份旧配置 + 迁移 owner 信息 + 修签名脚本 + 写 migration 完成标记”维护流程
- **能力分类**：`Portfolio JSON Migration Repair`
- **前置数据**：`config.execute` 生成 handoff、旧 JSON 配置、缺陷脚本和测试。
- **评估函数**：`check_json` + `check_python_file_by_test_suite` + `is_expected_active_tab_approximate` + `check_include_exclude` + `check_include_exclude`
- **验证逻辑**：JSON 更新、测试通过、文档页打开、备份存在、迁移标记文本正确。
- **需要新评估函数**：❌

#### 任务 L3-8：解析 DEVNOTES 完成环境搭建、统计和设置同步

- **ID**：`f1a30ea3-6e7b-4cdc-94d2-65c901308713`
- **task_slug**：`devnotes_pipeline_analysis_os_vscode_chrome`
- **指令**：解析 `/tmp/analysis_project/DEVNOTES.md` 中的 `MaxLineLen`、`TabSize`、`CheckUrl`、`Author`，统计 Python 文件数，写 `code_metrics.txt`，同步多项 VS Code 设置，并打开校验 URL。
- **涉及应用**：`os` + `vscode` + `chrome`
- **source**：https://pycodestyle.pycqa.org/；https://code.visualstudio.com/docs/getstarted/settings；现实场景构造来源：代码分析项目把检查列宽、作者和校验链接写进 DEVNOTES，要求执行人统计代码指标并同步环境的常见审计准备流程
- **能力分类**：`Devnotes-Driven Environment Audit`
- **前置数据**：项目目录与 DEVNOTES 已存在。
- **评估函数**：`check_include_exclude` + `check_json_settings` + `is_expected_active_tab_approximate`
- **验证逻辑**：指标报告、VS Code 设置和文档页三项组成完整闭环。
- **需要新评估函数**：❌

#### L3 小结

1. L3 任务最典型的结构是“读取 handoff / spec -> 修改项目配置 -> 修复代码 -> 同步编辑器设置 -> 打开文档 -> 写完成标记”。
2. 在原整理顺序中的 8 个 L3 条目里，有 4 个同时包含配置迁移和测试驱动代码修复；按当前 JSON，新增补任务后当前 L3 总量为 10。
3. 从可验证性角度看，L3 依然是强结构化任务，并没有引入真正开放式或长时依赖交互。

---

### 3.4 2026-04-02 新增任务补充

以下 4 个任务为 2026-04-02 复核后新补入 `mutil_app_new_xt` 的任务，统一补入 `source` 与英文能力短语，便于与前述 40 个旧整理条目一起做后续分析。

#### 新增任务 A：docs_portal_handoff_with_logo_yaml_and_bookmark

- **ID**：`7c3ae54d-74e8-46ec-bf67-7ef0e8f4b1c2`
- **task_slug**：`docs_portal_handoff_with_logo_yaml_and_bookmark`
- **指令概述**：依据本地 handoff HTML 和 logo 资产，迁移 docs portal 的 `site.yml`，修复 `render_nav.py`，复制 logo，写 README，同步 VS Code 设置，并将 CSS 参考页加入书签后返回本地 handoff 页。
- **涉及应用**：`os` + `vscode` + `chrome`
- **source**：https://www.mkdocs.org/user-guide/configuration/；https://developer.mozilla.org/en-US/docs/Web/CSS/color；https://support.google.com/chrome/answer/188842；现实场景构造来源：文档门户重建时常见的“按本地 handoff 页迁移 site.yml、修脚本、拷 logo、收藏 CSS 参考并保持 brief 页聚焦”内容平台交接流程
- **能力分类**：`Docs Portal Build and Bookmark`
- **核心验证**：`check_json` + `check_python_file_by_test_suite` + `check_include_exclude` + `check_bookmark_contains_url` + `check_json_settings` + `is_expected_active_tab_approximate`

#### 新增任务 B：support_queue_handoff_json_fix_and_docs_sync

- **ID**：`b6f8b62f-1a6e-4b4d-8c11-56d7a4d5e903`
- **task_slug**：`support_queue_handoff_json_fix_and_docs_sync`
- **指令概述**：读取 `support_queue/HANDOFF.json`，更新 `queue_config.json`，创建 `.bak`，修复状态行构建脚本，写 `RUNBOOK.md`，同步 VS Code 设置，并保持 docsUrl 打开。
- **涉及应用**：`os` + `vscode` + `chrome`
- **source**：https://docs.python.org/3/library/csv.html；https://code.visualstudio.com/docs/getstarted/settings；现实场景构造来源：支持队列工具交接时常见的“更新 queue_config、修状态行脚本、补 runbook、同步文档与编辑器偏好”运维 handoff 流程
- **能力分类**：`Support Queue Handoff Repair`
- **核心验证**：`check_json` + `check_python_file_by_test_suite` + `check_include_exclude` + `check_json_settings` + `is_expected_active_tab_approximate`

#### 新增任务 C：preview_bundle_local_mock_and_asset_sync

- **ID**：`c91a2f7d-3d44-4a88-9e3f-42d8f76cb572`
- **task_slug**：`preview_bundle_local_mock_and_asset_sync`
- **指令概述**：依据 `preview_bundle.json` 修正 `bundle.json`，创建备份，修复 `render_banner.py`，同步 banner 资产和 checklist，并写入对应 VS Code 设置。
- **涉及应用**：`os` + `vscode` + `chrome`
- **source**：https://developer.mozilla.org/en-US/docs/Web/SVG；https://code.visualstudio.com/docs/getstarted/settings；现实场景构造来源：预览包发布前常见的“按 brief 与 spec 修正 bundle manifest、修渲染脚本、同步 banner 资产和检查清单”预发布整备流程
- **能力分类**：`Preview Bundle Repair and Asset Sync`
- **核心验证**：`check_json` + `check_python_file_by_test_suite` + `check_include_exclude` + `check_json_settings` + `is_expected_active_tab_approximate`

#### 新增任务 D：release_workspace_manifest_fix_with_local_brief

- **ID**：`e4c1b218-6f7c-4f64-bf2f-0d64f8c2d001`
- **task_slug**：`release_workspace_manifest_fix_with_local_brief`
- **指令概述**：依据本地 release brief 与 `release_spec.json` 更新 `release_manifest.json`，创建 `.bak`，修复 `build_release_note.py`，复制 badge，写 README，并同步 VS Code 设置。
- **涉及应用**：`os` + `vscode` + `chrome`
- **source**：https://code.visualstudio.com/docs/getstarted/settings；现实场景构造来源：发布工作区换班时常见的“按本地 brief 和 release spec 迁移 manifest、修发布说明脚本、复制 badge 并同步编辑器规则”release handoff 流程
- **能力分类**：`Release Workspace Migration`
- **核心验证**：`check_json` + `check_python_file_by_test_suite` + `check_include_exclude` + `check_json_settings` + `is_expected_active_tab_approximate`

---

## 4. 现有任务总结分析

### 4.1 任务族结构

从现有 44 个任务看，这批数据可以概括为 4 条主线：

1. **规格驱动型配置同步**：从 JSON / HTML / Markdown / TXT 中读取参数，再落到 VS Code 设置或项目文件中。
2. **开发环境引导型任务**：创建目录、生成 README / `.gitignore` / notes、写审计报告、配置编辑器。
3. **文档辅助型代码修复**：Chrome 打开 Python / npm / VS Code / FastAPI 等文档，VS Code 修复故障代码并跑测试。
4. **项目交接迁移型任务**：读取 handoff，更新 YAML / JSON / `package.json` / 站点配置，同时保留备份或迁移标记。

### 4.2 这批数据的优点

1. **可验证性强**：大部分任务都能通过文件内容、JSON 字段、目录状态、活动标签或测试套件来稳定验证。
2. **跨应用耦合清晰**：Chrome 负责参考信息，VS Code 负责修改，OS / 终端负责落地产物，角色分工明确。
3. **对代理能力有较好覆盖**：读取规格、切换应用、编辑配置、修复代码、写结果文件，都是桌面代理的核心能力。
4. **初始化成本低**：30 个任务使用 `execute` 动态生成输入数据，不依赖大量外部资源文件，便于扩展。
5. **测试驱动的子集质量较高**：10 个任务使用 `check_python_file_by_test_suite`，比纯字符串检查更能反映真实修复正确性。

### 4.3 任务分布上的偏向

1. **VS Code 占主导地位**：26 次 `check_json_settings` 说明大部分任务最终都收敛到 VS Code 设置文件。
2. **Chrome 主要是参考页载体**：25 次 `is_expected_active_tab_approximate` 表明 Chrome 更多扮演“打开文档 / 保持页面”的角色，而不是复杂网页交互主体。
3. **OS 操作多数是轻量级落地动作**：多为 `mkdir`、`cat`、统计、写文本，不涉及复杂系统设置或进程管理。
4. **代码修复类比例不低**：10 个任务直接依赖测试套件，整体风格明显偏向开发工作流而非通用桌面生产力场景。

---

## 5. 现有数据的不足之处

### 5.1 应用覆盖偏窄

虽然名为多应用任务，但现有数据几乎都围绕 **Chrome + VS Code + OS** 展开，没有进一步纳入 LibreOffice、Thunderbird、GIMP、PDF 阅读器、文件管理器复杂操作等更广泛的跨应用协作场景。

### 5.2 Chrome 侧交互深度不足

大多数 Chrome 相关任务只要求：

1. 打开某个本地 / 在线页面。
2. 保持该页面为活动标签。
3. 或把页面加入书签。

这意味着浏览器更多被当作“参考资料容器”，而不是需要真实导航、表单填写、站点搜索、页面理解或多标签切换协调的复杂应用。

### 5.3 验证过于偏向最终状态，过程信息较少

当前验证器基本只看最终文件状态、最终活动标签、最终书签树和最终测试结果，难以区分：

1. 代理是否真正按规格读取了参考文件。
2. 代理是否通过正确路径完成操作，还是走了捷径。
3. 代理是否发生过错误中间态再修复。

这对“真实桌面行为建模”来说覆盖还不够丰富。

### 5.4 环境风险分布单一

44 个任务全部标为 `possibility_of_env_change=low`，说明它们几乎都在稳定、可预期的环境里完成，没有覆盖：

1. 应用重启。
2. 窗口焦点丢失。
3. 中途弹窗。
4. 外部状态变化。
5. 中断恢复。

因此这批数据对鲁棒性和恢复能力的压力有限。

### 5.5 来源字段单一

全部任务 `source=authors`，缺少更细粒度的来源映射，例如：

1. 真实 handoff 工单。
2. 公开文档原型。
3. 实际开发流程访谈。
4. 论坛 / 支持工单抽象。

从论文叙事和数据 provenance 的角度看，这会让任务看起来更像“作者构造的高质量合成场景”，而不是“有来源证据链的现实工作流抽样”。

### 5.6 任务复杂度层次存在塌缩

虽然标注了 L1 / L2 / L3，但 L3 任务依然大多遵循同一模板：

1. 读 handoff / spec。
2. 改 1 个配置文件。
3. 修 1 个 Python 脚本。
4. 同步 1 组 VS Code 设置。
5. 打开 1 个文档页。
6. 写 1 个完成标记。

也就是说，复杂度更多来自“指标数量增加”，而不是工作流结构发生本质变化。缺少真正长链条、跨文件、多依赖、带回看和重规划的任务。

### 5.7 目录与模块命名存在一致性问题

`mutil_app_new_xt` 与 `mutil_apps_new.py` 中的 `mutil` 拼写会长期增加理解成本。再加上任务实际复用了 `general.py`、`vscode.py`、`chrome.py` 多个模块，目录名容易让人误以为所有验证逻辑都集中在 `mutil_apps_new.py` 中，但实际上该文件目前只提供了一个 `check_bookmark_contains_url`。

---

## 6. 后续补强建议

如果后续继续扩展这批数据，比较自然的方向是：

1. 增加真正的跨站点 Chrome 操作任务，例如登录态、搜索、复制信息、标签切换、下载后回到 VS Code 处理。
2. 增加 VS Code 之外的第二生产力应用，如 LibreOffice Writer / Calc、PDF 工具、邮件客户端，再与 OS 或 Chrome 联动。
3. 提高环境扰动等级，加入弹窗、重新聚焦、任务中断、前置状态不完全确定等条件。
4. 为 handoff / spec 类任务补充更细的来源标注和 evidence 字段，提升数据 provenance 的可解释性。
5. 把部分 L3 任务改造成多阶段或 interactive 版本，让代理必须在已有产物上继续返工，而不是单轮完成。

---

## 7. 总结

`mutil_app_new_xt` 当前是一组 **高度结构化、可验证性强、偏开发工作流导向** 的跨应用任务集合。它非常适合评估代理在以下方面的能力：读取规格、跨应用切换、同步编辑器设置、修复小型代码缺陷、生成交付文件、保持参考页上下文。

但从数据多样性和真实桌面复杂性角度看，这批任务仍明显偏向 **Chrome 参考页 + VS Code 编辑 + OS 落地** 的固定模式。它是一个不错的多应用起点，但还没有完全覆盖真实桌面代理在复杂办公、生产力软件协同和动态环境下的能力上限。