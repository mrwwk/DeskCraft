# VS Code New 任务设计文档

## 0. VS Code 验证策略

### VS Code 路径与配置位置

- 启动命令统一使用 `code`。
- 用户级配置文件默认位于：
  - `settings.json` -> `/home/user/.config/Code/User/settings.json`
  - `keybindings.json` -> `/home/user/.config/Code/User/keybindings.json`
  - `snippets/python.json` -> `/home/user/.config/Code/User/snippets/python.json`
- 工作区与项目级配置常见位置：
  - `<name>.code-workspace`
  - `/home/user/<project>/.vscode/settings.json`
  - `/home/user/<project>/.vscode/tasks.json`
  - `/home/user/<project>/.vscode/launch.json`
  - `/home/user/<project>/.vscode/extensions.json`

### 核心思路

VS Code 任务的验证主要依赖两类结果：

1. JSON 配置文件分析
   - 直接下载用户配置文件、工作区文件或 `.vscode/*` 文件到本地。
   - 使用 `json.load` 后做子集匹配或数组成员匹配。
   - 适合验证设置项、键绑定、代码片段、任务、启动配置、扩展推荐等静态产物。

2. 命令行结果分析
   - 对扩展安装类任务，直接执行 `code --list-extensions` 并检查输出中是否包含目标扩展 ID。
   - 适合验证“扩展是否已安装”这一结果型状态。

### 评估器架构

`vs_code_new` 当前任务全部复用 `desktop_env/evaluators/metrics/vscode.py` 中已有函数，无需新增评估函数。

其整体模式是：

```python
def check_xxx(actual, expected, **options) -> float:
    if not actual:
        return 0.0
    try:
        # 读取 JSON / 文本 / 命令行结果
        # 做包含性或等价性判断
        return 1.0 if passed else 0.0
    except Exception:
        return 0.0
```

### 与 Audacity 类任务的区别

| 维度 | VS Code New | Audacity |
|---|---|---|
| 核心产物 | JSON 配置文件、扩展列表 | WAV / `.aup3` |
| 验证方式 | 本地读配置文件或命令输出 | 本地读音频文件或 SQLite |
| 依赖 | `json`、文本比较、CLI 输出 | `wave`、`sqlite3`、`xml.etree` |
| 是否依赖视觉验证 | 否 | 否 |
| 额外脚本 | 不需要 | 不需要 |

---

## 1. 数据概览

### 任务规模

`vs_code_new` 当前共 **30 个任务**：

| 级别 | 数量 | 主要目标 |
|---|---:|---|
| L1 | 15 | 单文件用户配置与基础键绑定 |
| L2 | 9 | 多文件配置、工作区保存、任务/片段/扩展 |
| L3 | 6 | 多工作区与项目脚手架组合配置 |
| 总计 | 30 | 覆盖用户配置、项目配置、工作区配置、扩展与调试 |

### 预置步骤统计

所有任务使用的 `config` 步骤类型如下：

| config 类型 | 次数 | 用途 |
|---|---:|---|
| `launch` | 30 | 启动 VS Code |
| `activate_window` | 30 | 将焦点切到 VS Code |
| `command` | 22 | 预建目录、工作区目录、缓存目录等 |
| `execute` | 4 | 预写入 `.code-workspace` 或项目样例文件 |
| `download` | 1 | 下载本地 VSIX 安装包 |

### 可用资源

与 Audacity 不同，`vs_code_new` 没有大量静态素材文件。当前数据主要依赖以下资源形态：

1. 预建目录
   - 例如 `/home/user/project`、`/home/user/data1`、`/home/user/runbooks`。

2. 预写入工作区或项目文件
   - 例如初始 `workspace1.code-workspace`。

3. 单个外部下载资源
   - `0512bb38-d531-4acf-9e7e-0add90816068_L2` 会下载 `/home/user/test.vsix`。

4. 用户配置目录
   - `/home/user/.config/Code/User/` 下的 `settings.json`、`keybindings.json`、`snippets/`。

### 当前主要验证产物

| 产物类型 | 典型路径 | 主要任务层级 |
|---|---|---|
| 用户设置 | `/home/user/.config/Code/User/settings.json` | L1/L2/L3 |
| 用户键绑定 | `/home/user/.config/Code/User/keybindings.json` | L1/L2/L3 |
| 用户代码片段 | `/home/user/.config/Code/User/snippets/python.json` | L2/L3 |
| 工作区文件 | `/home/user/*.code-workspace` | L2/L3 |
| 项目任务配置 | `/home/user/<project>/.vscode/tasks.json` | L2/L3 |
| 项目启动配置 | `/home/user/<project>/.vscode/launch.json` | L3 |
| 项目扩展推荐 | `/home/user/<project>/.vscode/extensions.json` | L2/L3 |
| 扩展列表输出 | `code --list-extensions` | L2 |

---

## 2. 评估函数设计

文件：`desktop_env/evaluators/metrics/vscode.py`

### 2.1 当前实际使用的评估函数

| 函数名 | 使用层级 | 作用 | 当前用途 |
|---|---|---|---|
| `check_json_settings` | L1/L2/L3 | 读取 JSON 对象并检查期望键值是否全部存在 | `settings.json`、简单 `.code-workspace` |
| `check_json_keybindings` | L1/L2/L3 | 读取键绑定数组并检查目标对象存在，或同时检查必需项/禁止项 | `keybindings.json` |
| `compare_config` | L2/L3 | 对任意 JSON 文本做子集匹配 | `.code-workspace`、`tasks.json`、`launch.json`、`extensions.json`、`snippets` |
| `is_extension_installed` | L2 | 检查 CLI 输出是否包含目标扩展 ID | VSIX 安装验证 |

### 2.2 内部匹配逻辑

#### `check_json_settings`

- 输入：目标 JSON 文件路径 + `expected` 字典。
- 逻辑：逐项检查期望键是否存在且值完全相等。
- 支持嵌套对象，例如：

```json
{
  "editor.codeActionsOnSave": {
    "source.organizeImports": "explicit"
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  }
}
```

#### `check_json_keybindings`

- 输入：`keybindings.json` 路径。
- 逻辑：尝试将文件解析为数组，然后支持三种验证模式：
  - `expected`：检查单个目标键绑定存在。
  - `all_of`：检查多个目标键绑定全部存在。
  - `none_of`：检查某些键绑定不存在。
- 匹配时使用子集语义，因此即使实际项包含额外字段，也可以通过。
- 兼容两种文件格式：
  - 文件开头直接是 JSON 数组。
  - 第一行存在注释或前缀文本，跳过首行后再解析。

#### `compare_config`

- 用于更泛化的 JSON 文本比较。
- 默认采用包含式验证：只要求期望 JSON 是实际 JSON 的子集，不要求完全一致。
- 因而适合：
  - 工作区文件中只验证部分 `folders/settings/extensions`
  - `tasks.json` 中只验证必要 task
  - `launch.json` 中只验证必要 configuration
  - `snippets` 中只验证某个 snippet 条目

#### `is_extension_installed`

- 当前实现非常轻量：
  - 从命令输出字符串中检查目标扩展 ID 是否存在。
- 优点：直接、稳定。
- 局限：只验证“装上了”，不验证扩展是否可用或是否被启用。

### 2.3 当前验证方式的边界

| 边界 | 说明 |
|---|---|
| 不验证 UI 实际呈现 | 例如主题、图标主题、minimap 仅验证配置文件，不验证界面是否真的切换 |
| 不验证更高层的快捷键优先级语义 | 即使显式旧项已删除，仍不验证 VS Code 内置默认绑定或上下文优先级的运行时效果 |
| 不验证 task / launch 的运行成功 | 当前只检查文件内容，不执行任务或调试配置 |
| 不验证 snippet 的编辑器展开效果 | 当前只检查 `python.json` 内容 |

---

## 3. L1 任务定义

### 3.0 能力分类词表（供 L1/L2/L3 共用）

为避免后续分析阶段出现“每题一个新标签”的碎片化问题，`vs_code_new` 的能力分类统一收敛到下表中的有限词表。后续每个任务条目都只从该词表中选取一个主分类。

| 能力分类 | 范围说明 |
|---|---|
| `Save and Wrap Preferences` | 自动保存、换行、保存清理、ruler 等基础编辑行为配置 |
| `Python Development Preferences` | Python 专属编辑、分析、默认语言、缓存隐藏等开发偏好配置 |
| `Visual and Safety Preferences` | 主题、图标、minimap、Unicode 高亮、空白字符显示等可视化与安全提示配置 |
| `Debugging Preferences` | 调试时焦点、inline values 等调试体验偏好 |
| `Keybinding Customization` | 用户级快捷键新增、重绑定、冲突移除与焦点导航配置 |
| `Extension and Environment Provisioning` | 扩展安装、扩展更新策略与运行环境补齐 |
| `Multi-root Workspace Management` | 多根工作区创建、扩展已有工作区、工作区级目录组合与排除规则 |
| `Project Scaffold Configuration` | 项目级 `.vscode/*`、扩展推荐、任务、工作区 bundle 等脚手架式配置 |
| `Snippet and Completion Configuration` | snippet 文件、tabCompletion、snippetSuggestions 等模板与补全效率配置 |
| `Debug and Test Workflow Setup` | `tasks.json`、`launch.json`、测试框架与调试入口联动配置 |

### 3.1 第一级（L1）—— 基础配置（单文件、可直接验证）—— 15 个

L1 任务为单文件原子配置任务，每个任务只要求完成一个清晰的 VS Code 基础配置目标。当前 L1 统一具备以下特点：

- **启动命令**：`code`
- **验证方式**：通过 `vm_file` getter 下载 `settings.json` 或 `keybindings.json`
- **主要产物**：`/home/user/.config/Code/User/` 下的用户级配置文件

---

#### 任务 L1-1：700ms 自动保存 + 保存清理 + 自动换行

- **ID**：`0ed39f63-6049-43d4-ba4d-5fa2fe04a951`
- **指令**：Please update VS Code User Settings with all of the following at once: enable Auto Save after delay with a 700ms delay, trim trailing whitespace on save, insert a final newline on save, and enable editor word wrap.
- **能力分类**：`Save and Wrap Preferences`
- **来源**：`https://code.visualstudio.com/docs/getstarted/settings`；`https://code.visualstudio.com/docs/editing/codebasics`
- **评估函数**：`check_json_settings`
- **result**：`vm_file` -> `/home/user/.config/Code/User/settings.json`
- **expected**：`rule` -> `{"files.autoSave":"afterDelay","files.autoSaveDelay":700,"files.trimTrailingWhitespace":true,"files.insertFinalNewline":true,"editor.wordWrap":"on"}`
- **验证逻辑**：检查自动保存模式、延时、保存清理和自动换行四项是否同时写入用户设置。
- **需要新评估函数**：❌

---

#### 任务 L1-2：72 列换行配置

- **ID**：`276cc624-87ea-4f08-ab93-f770e3790175`
- **指令**：Please configure VS Code wrapping behavior in User Settings: set line wrap column to 72, enable wrapping by column mode, and keep normal editor word wrap behavior enabled.
- **能力分类**：`Save and Wrap Preferences`
- **来源**：`https://code.visualstudio.com/docs/getstarted/settings`；`https://code.visualstudio.com/docs/editing/codebasics`
- **评估函数**：`check_json_settings`
- **result**：`vm_file` -> `/home/user/.config/Code/User/settings.json`
- **expected**：`rule` -> `{"editor.wordWrap":"on","editor.wordWrapColumn":72,"editor.wrappingStrategy":"advanced"}`
- **验证逻辑**：验证换行开关、列宽阈值与换行策略是否一致。
- **需要新评估函数**：❌

---

#### 任务 L1-3：Python 格式化保存与默认格式器

- **ID**：`4e60007a-f5be-4bfc-9723-c39affa0a6d3`
- **指令**：Please update VS Code User Settings to improve Python editing workflow: turn on format-on-save, organize imports on save explicitly, set Python as the default formatter, and set editor tab size to 2.
- **能力分类**：`Python Development Preferences`
- **来源**：`https://code.visualstudio.com/docs/python/formatting`；`https://code.visualstudio.com/docs/python/settings-reference`；`https://code.visualstudio.com/docs/getstarted/settings`
- **评估函数**：`check_json_settings`
- **result**：`vm_file` -> `/home/user/.config/Code/User/settings.json`
- **expected**：`rule` -> `{"editor.formatOnSave":true,"editor.codeActionsOnSave":{"source.organizeImports":"explicit"},"[python]":{"editor.defaultFormatter":"ms-python.black-formatter"},"editor.tabSize":2}`
- **验证逻辑**：要求同时覆盖通用保存行为、Python 语言专属 formatter 和缩进宽度。
- **需要新评估函数**：❌

---

#### 任务 L1-4：Python 新建文件默认语言与空白字符显示

- **ID**：`57242fad-77ca-454f-b71b-f187181a9f23`
- **指令**：Please update VS Code User Settings for creating Python files faster: set default language for new untitled files to python, enable auto save on focus change, and enable rendering of whitespace for all characters.
- **能力分类**：`Python Development Preferences`
- **来源**：`https://code.visualstudio.com/docs/getstarted/settings`；`https://code.visualstudio.com/docs/python/settings-reference`
- **评估函数**：`check_json_settings`
- **result**：`vm_file` -> `/home/user/.config/Code/User/settings.json`
- **expected**：`rule` -> `{"files.defaultLanguage":"python","files.autoSave":"onFocusChange","editor.renderWhitespace":"all"}`
- **验证逻辑**：验证新文件默认语言、失焦自动保存和空白字符显示策略。
- **需要新评估函数**：❌

---

#### 任务 L1-5：800ms 自动保存与保存清理

- **ID**：`70745df8-f2f5-42bd-8074-fbc10334fcc5`
- **指令**：Please configure VS Code Auto Save behavior in User Settings: enable afterDelay mode with an 800ms delay, and also enable trim trailing whitespace and insert final newline on save.
- **能力分类**：`Save and Wrap Preferences`
- **来源**：`https://code.visualstudio.com/docs/getstarted/settings`；`https://code.visualstudio.com/docs/editing/codebasics`
- **评估函数**：`check_json_settings`
- **result**：`vm_file` -> `/home/user/.config/Code/User/settings.json`
- **expected**：`rule` -> `{"files.autoSave":"afterDelay","files.autoSaveDelay":800,"files.trimTrailingWhitespace":true,"files.insertFinalNewline":true}`
- **验证逻辑**：验证保存时序和保存清理动作是否一起生效。
- **需要新评估函数**：❌

---

#### 任务 L1-6：Python Inlay Hints 与括号配对着色

- **ID**：`7aeae0e2-70ee-4705-821d-1bba5d5b2ddd`
- **指令**：Please optimize Python editing in VS Code User Settings: enable inlay hints for variable types and function return types, and enable bracket pair colorization.
- **能力分类**：`Python Development Preferences`
- **来源**：`https://code.visualstudio.com/docs/python/settings-reference`；`https://code.visualstudio.com/docs/getstarted/settings`
- **评估函数**：`check_json_settings`
- **result**：`vm_file` -> `/home/user/.config/Code/User/settings.json`
- **expected**：`rule` -> `{"editor.inlayHints.enabled":"on","python.analysis.inlayHints.variableTypes":true,"python.analysis.inlayHints.functionReturnTypes":true,"editor.bracketPairColorization.enabled":true}`
- **验证逻辑**：验证 Python 类型提示与编辑器视觉辅助是否一起打开。
- **需要新评估函数**：❌

---

#### 任务 L1-7：Unicode 高亮配置

- **ID**：`7c4cc09e-7a92-40dd-8338-b2286535c4ed`
- **指令**：Please configure VS Code User Settings for multilingual coding by setting Unicode highlight to include ambiguous and invisible characters, while allowing comments and strings.
- **能力分类**：`Visual and Safety Preferences`
- **来源**：`https://code.visualstudio.com/docs/getstarted/settings`；现实场景构造来源：多语言开发与内容安全审查场景下常见的“高亮歧义字符与不可见字符，同时保留注释和字符串可读性”编辑器防误判需求
- **评估函数**：`check_json_settings`
- **result**：`vm_file` -> `/home/user/.config/Code/User/settings.json`
- **expected**：`rule` -> `{"editor.unicodeHighlight.ambiguousCharacters":true,"editor.unicodeHighlight.invisibleCharacters":true,"editor.unicodeHighlight.includeComments":true,"editor.unicodeHighlight.includeStrings":true}`
- **验证逻辑**：验证 Unicode 高亮与 comments/strings 白名单是否完整配置。
- **需要新评估函数**：❌

---

#### 任务 L1-8：调试焦点与 Inline Values

- **ID**：`9439a27b-18ae-42d8-9778-5f68f891805e`
- **指令**：Please update VS Code User Settings for debugging so that the editor does not steal focus on break, auto-expand lazy variables is enabled, and inline values are shown during debug.
- **能力分类**：`Debugging Preferences`
- **来源**：`https://code.visualstudio.com/docs/debugtest/debugging`；`https://code.visualstudio.com/docs/getstarted/settings`
- **评估函数**：`check_json_settings`
- **result**：`vm_file` -> `/home/user/.config/Code/User/settings.json`
- **expected**：`rule` -> `{"debug.focusEditorOnBreak":false,"debug.autoExpandLazyVariables":true,"debug.inlineValues":true}`
- **验证逻辑**：验证调试体验相关的三个常用 debug 设置是否同时存在。
- **需要新评估函数**：❌

---

#### 任务 L1-9：Python Scratch 启动配置

- **ID**：`971cbb5b-3cbf-4ff7-9e24-b5c84fcebfa6`
- **指令**：Please configure VS Code for quick Python scratch files: set default language to python, start with a new untitled file on startup, and enable auto save after delay with 1000ms.
- **能力分类**：`Python Development Preferences`
- **来源**：`https://code.visualstudio.com/docs/getstarted/settings`；`https://code.visualstudio.com/docs/python/settings-reference`；现实场景构造来源：开发者临时编写 Python 草稿或验证脚本时常见的“新建即 Python + 启动空白文件 + 延迟自动保存”个人工作流需求
- **评估函数**：`check_json_settings`
- **result**：`vm_file` -> `/home/user/.config/Code/User/settings.json`
- **expected**：`rule` -> `{"files.defaultLanguage":"python","workbench.startupEditor":"newUntitledFile","files.autoSave":"afterDelay","files.autoSaveDelay":1000}`
- **验证逻辑**：验证 scratch 工作流相关的默认语言、启动页和自动保存行为。
- **需要新评估函数**：❌

---

#### 任务 L1-10：包裹标签页与关闭按钮位置

- **ID**：`9d425400-e9b2-4424-9a4b-d4c7abac4140`
- **指令**：Please tune VS Code tab behavior in User Settings by enabling wrapped tabs, disabling tab pinning, and setting tab close button visibility to left.
- **能力分类**：`Visual and Safety Preferences`
- **来源**：`https://code.visualstudio.com/docs/getstarted/userinterface`；`https://code.visualstudio.com/docs/getstarted/settings`
- **评估函数**：`check_json_settings`
- **result**：`vm_file` -> `/home/user/.config/Code/User/settings.json`
- **expected**：`rule` -> `{"workbench.editor.wrapTabs":true,"workbench.editor.enablePreview":false,"workbench.editor.tabCloseButton":"left"}`
- **验证逻辑**：验证工作台标签页行为和关闭按钮位置。
- **需要新评估函数**：❌

---

#### 任务 L1-11：隐藏 Python 缓存目录

- **ID**：`c6bf789c-ba3a-4209-971d-b63abf0ab733`
- **指令**：Please update VS Code User Settings to hide Python cache folders in Explorer, including __pycache__, .pytest_cache, and .mypy_cache.
- **能力分类**：`Python Development Preferences`
- **来源**：`https://code.visualstudio.com/docs/getstarted/settings`；`https://code.visualstudio.com/docs/getstarted/userinterface`
- **评估函数**：`check_json_settings`
- **result**：`vm_file` -> `/home/user/.config/Code/User/settings.json`
- **expected**：`rule` -> `{"files.exclude":{"**/__pycache__":true,"**/.pytest_cache":true,"**/.mypy_cache":true}}`
- **验证逻辑**：验证 Explorer 隐藏规则中三个 Python 缓存目录模式是否完整。
- **需要新评估函数**：❌

---

#### 任务 L1-12：Dark Modern + Seti + Minimap 关闭

- **ID**：`dcbe20e8-647f-4f1d-8696-f1c5bbb570e3`
- **指令**：Please customize VS Code appearance by setting color theme to Default Dark Modern, icon theme to Seti (Visual Studio Code), and disable minimap.
- **能力分类**：`Visual and Safety Preferences`
- **来源**：`https://code.visualstudio.com/docs/getstarted/userinterface`；`https://code.visualstudio.com/docs/getstarted/settings`
- **评估函数**：`check_json_settings`
- **result**：`vm_file` -> `/home/user/.config/Code/User/settings.json`
- **expected**：`rule` -> `{"workbench.colorTheme":"Default Dark Modern","workbench.iconTheme":"vs-seti","editor.minimap.enabled":false}`
- **验证逻辑**：验证外观主题、图标主题和编辑区 minimap 状态。
- **需要新评估函数**：❌

---

#### 任务 L1-13：Python Analysis 基础诊断模式

- **ID**：`e2b5e914-ffe1-44d2-8e92-58f8c5d92bb2`
- **指令**：Please modify VS Code User Settings for Python analysis with all requirements together: disable reportMissingImports, set reportUnusedImport to information level, set typeCheckingMode to basic, and enable auto import completions.
- **能力分类**：`Python Development Preferences`
- **来源**：`https://code.visualstudio.com/docs/python/settings-reference`；`https://code.visualstudio.com/docs/getstarted/settings`
- **评估函数**：`check_json_settings`
- **result**：`vm_file` -> `/home/user/.config/Code/User/settings.json`
- **expected**：`rule` -> `{"python.analysis.diagnosticSeverityOverrides":{"reportMissingImports":"none","reportUnusedImport":"information"},"python.analysis.typeCheckingMode":"basic","python.analysis.autoImportCompletions":true}`
- **验证逻辑**：验证 Pylance 诊断级别、类型检查模式与自动导入补全。
- **需要新评估函数**：❌

---

#### 任务 L1-14：运行 Python 文件快捷键

- **ID**：`eabc805a-bfcf-4460-b250-ac92135819f6`
- **指令**：Please create a custom VS Code keybinding so that pressing Ctrl+Alt+R runs Python file in terminal, and make it active only when the editor is focused and the current language is Python.
- **能力分类**：`Keybinding Customization`
- **来源**：`https://code.visualstudio.com/docs/getstarted/keybindings`；`https://code.visualstudio.com/docs/python/settings-reference`
- **评估函数**：`check_json_keybindings`
- **result**：`vm_file` -> `/home/user/.config/Code/User/keybindings.json`
- **expected**：`rule` -> `{"key":"ctrl+alt+r","command":"python.execInTerminal","when":"editorTextFocus && editorLangId == python"}`
- **验证逻辑**：验证新增键绑定的键位、命令和上下文条件。
- **需要新评估函数**：❌

---

#### 任务 L1-15：缩进选中行快捷键

- **ID**：`ec71221e-ac43-46f9-89b8-ee7d80f7e1c5`
- **指令**：Please create a VS Code keybinding so that Ctrl+Alt+] indents selected lines, and it should only work when the editor has focus and the editor is not read-only.
- **能力分类**：`Keybinding Customization`
- **来源**：`https://code.visualstudio.com/docs/getstarted/keybindings`；`https://code.visualstudio.com/docs/editing/codebasics`
- **评估函数**：`check_json_keybindings`
- **result**：`vm_file` -> `/home/user/.config/Code/User/keybindings.json`
- **expected**：`rule` -> `{"key":"ctrl+alt+]","command":"editor.action.indentLines","when":"editorTextFocus && !editorReadonly"}`
- **验证逻辑**：验证缩进命令绑定和编辑器上下文限制。
- **需要新评估函数**：❌

---

### 3.2 L1 任务汇总

| # | 任务名称 | 目标文件 | 评估函数 | 新增评估器？ |
|---|---|---|---|---|
| 1 | 700ms 自动保存 + 保存清理 + 自动换行 | `settings.json` | `check_json_settings` | ❌ |
| 2 | 72 列换行配置 | `settings.json` | `check_json_settings` | ❌ |
| 3 | Python 格式化保存与默认格式器 | `settings.json` | `check_json_settings` | ❌ |
| 4 | Python 新建文件默认语言与空白字符显示 | `settings.json` | `check_json_settings` | ❌ |
| 5 | 800ms 自动保存与保存清理 | `settings.json` | `check_json_settings` | ❌ |
| 6 | Python Inlay Hints 与括号配对着色 | `settings.json` | `check_json_settings` | ❌ |
| 7 | Unicode 高亮配置 | `settings.json` | `check_json_settings` | ❌ |
| 8 | 调试焦点与 Inline Values | `settings.json` | `check_json_settings` | ❌ |
| 9 | Python Scratch 启动配置 | `settings.json` | `check_json_settings` | ❌ |
| 10 | 包裹标签页与关闭按钮位置 | `settings.json` | `check_json_settings` | ❌ |
| 11 | 隐藏 Python 缓存目录 | `settings.json` | `check_json_settings` | ❌ |
| 12 | Dark Modern + Seti + Minimap 关闭 | `settings.json` | `check_json_settings` | ❌ |
| 13 | Python Analysis 基础诊断模式 | `settings.json` | `check_json_settings` | ❌ |
| 14 | 运行 Python 文件快捷键 | `keybindings.json` | `check_json_keybindings` | ❌ |
| 15 | 缩进选中行快捷键 | `keybindings.json` | `check_json_keybindings` | ❌ |

**L1 统计**：
- 总任务数：**15**
- `settings.json` 任务数：**13**
- `keybindings.json` 任务数：**2**
- 评估函数种类：**2**
- 官方文档来源占比：**100%**

### 3.3 L1 的当前定位

L1 明显偏向“用户级偏好设置”和“基础键绑定”两类能力，强调：

- 通过 Settings UI 或 JSON 编辑器修改用户配置
- 通过 Keyboard Shortcuts UI 或 `keybindings.json` 配置快捷键
- 在不依赖项目上下文的情况下完成配置

它适合作为 VS Code 域中的“基础配置层”，但还不是“基础功能全覆盖层”。

### 3.4 L1 任务来源标注

> 标注原则：L1 以用户级设置与基础键绑定为主，优先映射到 VS Code 官方 Settings / Keybindings 文档；涉及 Python 编辑体验的题目，使用通用设置文档与 Python 扩展文档组合标注。

| 任务 | 来源类型 | 具体来源 | 标注理由 |
|---|---|---|---|
| L1-1、L1-5 | 官方文档 | [Settings](https://code.visualstudio.com/docs/getstarted/settings) + [Basic Editing](https://code.visualstudio.com/docs/editing/codebasics) | 对应自动保存、保存时清理和自动换行这一组最基础的编辑器行为设置 |
| L1-2、L1-10 | 官方文档 | [Settings](https://code.visualstudio.com/docs/getstarted/settings) | 对应换行列宽、标签页布局、关闭按钮位置等纯工作台显示偏好 |
| L1-3、L1-4、L1-9、L1-11、L1-13 | 官方文档组合 | [Settings](https://code.visualstudio.com/docs/getstarted/settings) + [Python Settings Reference](https://code.visualstudio.com/docs/python/settings-reference) | 对应 Python 新建文件、formatter、analysis、缓存目录隐藏等 Python 高频开发偏好 |
| L1-6、L1-7、L1-12 | 官方文档 | [Settings](https://code.visualstudio.com/docs/getstarted/settings) | 对应 Inlay Hints、Unicode 高亮、主题/图标/minimap 等纯显示与安全偏好 |
| L1-8 | 官方文档组合 | [Debugging](https://code.visualstudio.com/docs/debugtest/debugging) + [Settings](https://code.visualstudio.com/docs/getstarted/settings) | 对应调试时焦点保留、inline values 等调试可视化偏好 |
| L1-14、L1-15 | 官方文档 | [Key Bindings for Visual Studio Code](https://code.visualstudio.com/docs/getstarted/keybindings) | 对应用户级快捷键新增与重绑定 |

---

## 4. L2 任务定义

### 4.1 第二级（L2）—— 复合配置（2-4 个关联动作）—— 9 个

L2 任务开始引入多文件、工作区级别或“安装 + 配置”级别的复合目标。当前 L2 统一具备以下特点：

- **启动命令**：`code` 或 `code /home/user/<project>` 或 `code /home/user/<workspace>.code-workspace`
- **验证方式**：`vm_file` 与 `vm_command_line` 混合使用
- **主要产物**：`.code-workspace`、`.vscode/*`、`keybindings.json`、`snippets/python.json`

---

#### 任务 L2-1：安装本地 VSIX 并关闭自动更新

- **ID**：`0512bb38-d531-4acf-9e7e-0add90816068`
- **指令**：Please install the local VSIX extension from /home/user/test.vsix in VS Code, and also disable extension auto-update in User Settings.
- **能力分类**：`Extension and Environment Provisioning`
- **来源**：`https://code.visualstudio.com/docs/editor/extension-marketplace`；`https://code.visualstudio.com/docs/getstarted/settings`；现实场景构造来源：团队内部分发固定版本扩展包时常见的“离线安装 VSIX + 关闭自动更新以避免版本漂移”配置需求
- **预置资源**：下载 `test.vsix` 到 `/home/user/test.vsix`
- **评估函数**：多指标 `[`is_extension_installed`, `check_json_settings`]`，`conj: and`
- **result**：
  - `vm_command_line` -> `code --list-extensions | grep undefined_publisher.test`
  - `vm_file` -> `/home/user/.config/Code/User/settings.json`
- **expected**：
  - `rule` -> `{"type":"contain","expected":"undefined_publisher.test"}`
  - `rule` -> `{"extensions.autoUpdate":false}`
- **验证逻辑**：同时验证扩展已安装，且用户设置中关闭了扩展自动更新。
- **操作步骤数**：2（安装 VSIX -> 修改设置）
- **需要新评估函数**：❌

---

#### 任务 L2-2：analytics 项目扩展推荐与本地设置

- **ID**：`05a13a28-f108-4db4-bb75-575d37e0025e`
- **指令**：Please open /home/user/analytics-app in VS Code and set up the project for data work. Create .vscode/extensions.json recommending ms-python.python and ms-toolsai.jupyter. Also create .vscode/settings.json so editor.tabSize is 4, files.trimTrailingWhitespace is true, and files.exclude hides data/raw and .venv.
- **能力分类**：`Project Scaffold Configuration`
- **来源**：`https://code.visualstudio.com/docs/editor/extension-marketplace`；`https://code.visualstudio.com/docs/getstarted/settings`；现实场景构造来源：数据分析项目初始化时常见的“推荐 Python/Jupyter 扩展 + 收敛项目级编辑设置与目录隐藏规则”脚手架需求
- **预置资源**：创建 `/home/user/analytics-app/data/raw` 与 `/home/user/analytics-app/.venv`
- **评估函数**：多指标 `[`compare_config`, `check_json_settings`]`，`conj: and`
- **result**：
  - `vm_file` -> `/home/user/analytics-app/.vscode/extensions.json`
  - `vm_file` -> `/home/user/analytics-app/.vscode/settings.json`
- **expected**：
  - `rule` -> `{"recommendations":["ms-python.python","ms-toolsai.jupyter"]}`
  - `rule` -> `{"editor.tabSize":4,"files.trimTrailingWhitespace":true,"files.exclude":{"data/raw":true,".venv":true}}`
- **验证逻辑**：同时检查扩展推荐和项目级编辑/隐藏设置。
- **操作步骤数**：3（打开项目 -> 写扩展推荐 -> 写项目设置）
- **需要新评估函数**：❌

---

#### 任务 L2-3：从单文件夹创建多根工作区

- **ID**：`53ad5833-3455-407b-bbc6-45b4c79ab8fb`
- **指令**：Please open the folder /home/user/project in VS Code, add /home/user/data1 and /home/user/data2 into the same workspace, then save the workspace file as /home/user/project.code-workspace.
- **能力分类**：`Multi-root Workspace Management`
- **来源**：`https://code.visualstudio.com/docs/editor/multi-root-workspaces`
- **预置资源**：创建 `/home/user/project`、`/home/user/data1`、`/home/user/data2`
- **评估函数**：`check_json_settings`
- **result**：`vm_file` -> `/home/user/project.code-workspace`
- **expected**：`rule` -> `{"folders":[{"path":"project"},{"path":"data1"},{"path":"data2"}]}`
- **验证逻辑**：验证多根工作区文件中三组目录是否都被保存。
- **操作步骤数**：3（打开主目录 -> 添加两个目录 -> 保存工作区）
- **需要新评估函数**：❌

---

#### 任务 L2-4：多根工作区 + 工作区隐藏规则

- **ID**：`5e2d93d8-8ad0-4435-b150-1692aacaa994`
- **指令**：Please open /home/user/project in VS Code, add /home/user/docs and /home/user/scripts into the same workspace, save the multi-root workspace as /home/user/project_advanced.code-workspace, and in that workspace configure files.exclude so .cache and node_modules are hidden.
- **能力分类**：`Multi-root Workspace Management`
- **来源**：`https://code.visualstudio.com/docs/editor/multi-root-workspaces`；`https://code.visualstudio.com/docs/getstarted/settings`
- **预置资源**：创建 `/home/user/project`、`/home/user/project/.cache`、`/home/user/project/node_modules`、`/home/user/docs`、`/home/user/scripts`
- **评估函数**：`check_json_settings`
- **result**：`vm_file` -> `/home/user/project_advanced.code-workspace`
- **expected**：`rule` -> `{"folders":[{"path":"project"},{"path":"docs"},{"path":"scripts"}],"settings":{"files.exclude":{".cache":true,"node_modules":true}}}`
- **验证逻辑**：验证多根目录结构和工作区级 Explorer 隐藏规则是否同时写入。
- **操作步骤数**：4（打开项目 -> 添加 docs -> 添加 scripts -> 保存并写入工作区设置）
- **需要新评估函数**：❌

---

#### 任务 L2-5：修改已有工作区文件并追加目录

- **ID**：`847a96b6-df94-4927-97e6-8cc9ea66ced7`
- **指令**：Please open /home/user/workspace1.code-workspace in VS Code, add /home/user/project2 and /home/user/project3 as folders into this workspace, and save the workspace file.
- **能力分类**：`Multi-root Workspace Management`
- **来源**：`https://code.visualstudio.com/docs/editor/multi-root-workspaces`
- **预置资源**：创建 `/home/user/project1`、`/home/user/project2`、`/home/user/project3`，并预写入仅包含 `project1` 的 `workspace1.code-workspace`
- **评估函数**：`check_json_settings`
- **result**：`vm_file` -> `/home/user/workspace1.code-workspace`
- **expected**：`rule` -> `{"folders":[{"path":"project1"},{"path":"project2"},{"path":"project3"}]}`
- **验证逻辑**：验证在已有工作区基础上继续追加两个文件夹并保存。
- **操作步骤数**：3（打开已有工作区 -> 添加两个目录 -> 保存）
- **需要新评估函数**：❌

---

#### 任务 L2-6：service-app 的 Tasks 与 Python Testing 设置

- **ID**：`9159259c-ef0e-42f5-9dbb-cb28c8f3642f`
- **指令**：Please open /home/user/service-app in VS Code and set up test tooling for the project. Create .vscode/tasks.json with two shell tasks named Run Tests using `pytest` and Lint using `ruff check .`. Also create .vscode/settings.json so python.testing.pytestEnabled is true, python.testing.unittestEnabled is false, and python.testing.pytestArgs is ["tests"].
- **能力分类**：`Debug and Test Workflow Setup`
- **来源**：`https://code.visualstudio.com/docs/debugtest/tasks`；`https://code.visualstudio.com/docs/python/testing`；`https://code.visualstudio.com/docs/python/settings-reference`；现实场景构造来源：Python 服务项目接手时常见的“补齐测试任务 + 统一 pytest 发现配置 + 保留 lint 入口”工程化配置需求
- **预置资源**：创建 `/home/user/service-app/tests`
- **评估函数**：多指标 `[`compare_config`, `check_json_settings`]`，`conj: and`
- **result**：
  - `vm_file` -> `/home/user/service-app/.vscode/tasks.json`
  - `vm_file` -> `/home/user/service-app/.vscode/settings.json`
- **expected**：
  - `rule` -> `tasks.json` 中包含 `Run Tests` 与 `Lint` 两个 shell task
  - `rule` -> `{"python.testing.pytestEnabled":true,"python.testing.unittestEnabled":false,"python.testing.pytestArgs":["tests"]}`
- **验证逻辑**：同时验证项目任务配置和 Python 测试框架切换。
- **操作步骤数**：3（打开项目 -> 建 tasks -> 建 testing 设置）
- **需要新评估函数**：❌

---

#### 任务 L2-7：终端与编辑器双向焦点快捷键

- **ID**：`930fdb3b-11a8-46fe-9bac-577332e2640e`
- **指令**：Please configure two VS Code terminal navigation keybindings: Ctrl+J should move focus from terminal to editor when terminal is focused, and Ctrl+Shift+J should focus terminal when editor is focused.
- **能力分类**：`Keybinding Customization`
- **来源**：`https://code.visualstudio.com/docs/getstarted/keybindings`；`https://code.visualstudio.com/docs/getstarted/userinterface`
- **评估函数**：`check_json_keybindings`
- **result**：`vm_file` -> `/home/user/.config/Code/User/keybindings.json`
- **expected**：`rule` -> `all_of=[{"key":"ctrl+j","command":"workbench.action.focusActiveEditorGroup","when":"terminalFocus"},{"key":"ctrl+shift+j","command":"workbench.action.terminal.focus","when":"editorTextFocus"}]`
- **验证逻辑**：要求两个方向的焦点切换快捷键都存在，避免只配一半。
- **操作步骤数**：2（配置 terminal -> editor，配置 editor -> terminal）
- **需要新评估函数**：❌（复用增强后的 `check_json_keybindings`）

---

#### 任务 L2-8：Explorer 搜索快捷键冲突调整

- **ID**：`ea98c5d7-3cf9-4f9b-8ad3-366b58e0fcae`
- **指令**：Please resolve Explorer shortcut conflicts in VS Code by removing Ctrl+F for list.find and adding Ctrl+Alt+F for the same Tree View Find command with the same condition.
- **能力分类**：`Keybinding Customization`
- **来源**：`https://code.visualstudio.com/docs/getstarted/keybindings`；`https://code.visualstudio.com/docs/getstarted/userinterface`
- **评估函数**：`check_json_keybindings`
- **result**：`vm_file` -> `/home/user/.config/Code/User/keybindings.json`
- **expected**：`rule` -> `all_of=[{"key":"ctrl+alt+f","command":"list.find","when":"listFocus && listSupportsFind"}], none_of=[{"key":"ctrl+f","command":"list.find","when":"listFocus && listSupportsFind"}]`
- **验证逻辑**：不仅要求新增 `Ctrl+Alt+F`，还要求旧的 `Ctrl+F` 绑定被显式移除。
- **操作步骤数**：2（移除旧绑定 -> 添加新绑定）
- **需要新评估函数**：❌（复用增强后的 `check_json_keybindings`）

---

#### 任务 L2-9：Python 用户 Snippet 与补全偏好

- **ID**：`f66b89b9-f980-496d-9a3f-9b02af82f249`
- **指令**：Please configure VS Code Python productivity defaults. Create a Python user snippet named pytest_func with prefix tpytest, body lines `def test_${1:name}():` and `    assert ${2:actual} == ${3:expected}`, and description `Pytest function template`. Also update User Settings so editor.tabCompletion is on and editor.snippetSuggestions is top.
- **能力分类**：`Snippet and Completion Configuration`
- **来源**：`https://code.visualstudio.com/docs/editor/userdefinedsnippets`；`https://code.visualstudio.com/docs/getstarted/settings`；现实场景构造来源：Python 测试驱动开发时常见的“自定义 pytest 模板 + 提升 snippet 命中优先级与 Tab 展开效率”个人效率配置需求
- **预置资源**：创建 `/home/user/.config/Code/User/snippets`
- **评估函数**：多指标 `[`compare_config`, `check_json_settings`]`，`conj: and`
- **result**：
  - `vm_file` -> `/home/user/.config/Code/User/snippets/python.json`
  - `vm_file` -> `/home/user/.config/Code/User/settings.json`
- **expected**：
  - `rule` -> `python.json` 中包含 `pytest_func` snippet
  - `rule` -> `{"editor.tabCompletion":"on","editor.snippetSuggestions":"top"}`
- **验证逻辑**：同时验证 snippet 内容和 snippet 使用体验设置。
- **操作步骤数**：3（建 snippet -> 打开 tabCompletion -> 调整 snippetSuggestions）
- **需要新评估函数**：❌

---

### 4.2 L2 任务汇总

| # | 任务名称 | 主要产物 | 评估函数 | 步骤数 |
|---|---|---|---|---|
| 1 | 安装本地 VSIX 并关闭自动更新 | 扩展列表输出 + `settings.json` | `is_extension_installed` + `check_json_settings` | 2 |
| 2 | analytics 项目扩展推荐与本地设置 | `extensions.json` + `.vscode/settings.json` | `compare_config` + `check_json_settings` | 3 |
| 3 | 从单文件夹创建多根工作区 | `.code-workspace` | `check_json_settings` | 3 |
| 4 | 多根工作区 + 工作区隐藏规则 | `.code-workspace` | `check_json_settings` | 4 |
| 5 | 修改已有工作区文件并追加目录 | `.code-workspace` | `check_json_settings` | 3 |
| 6 | service-app 的 Tasks 与 Python Testing 设置 | `tasks.json` + `.vscode/settings.json` | `compare_config` + `check_json_settings` | 3 |
| 7 | 终端与编辑器双向焦点快捷键 | `keybindings.json` | `check_json_keybindings` | 2 |
| 8 | Explorer 搜索快捷键冲突调整 | `keybindings.json` | `check_json_keybindings` | 2 |
| 9 | Python 用户 Snippet 与补全偏好 | `python.json` + `settings.json` | `compare_config` + `check_json_settings` | 3 |

**L2 统计**：
- 总任务数：**9**
- 多根工作区任务：**3**
- 项目级 `.vscode/*` 任务：**3**
- 键绑定任务：**2**
- snippet 任务：**1**
- 扩展安装任务：**1**

### 4.3 L2 检查结论与必要修改

本轮检查后，L2 的总体难度已经达到“复合配置任务”的标准，但原始数据里有三类问题，现已完成必要修正：

1. **指令与验证不完全一致**
   - `0512bb38-d531-4acf-9e7e-0add90816068` 原先只验证“扩展装上了”，没有验证 instruction 中要求的 `extensions.autoUpdate=false`。
   - 现已改为联合验证：扩展安装 + 用户设置。

2. **只检查新增，不检查冲突解除**
   - `ea98c5d7-3cf9-4f9b-8ad3-366b58e0fcae` 原先只能验证新快捷键存在，不能验证旧冲突项被移除。
   - 现已增强 `check_json_keybindings`，支持 `all_of` / `none_of`，并将该任务改为“新增 + 删除”双向检查。

3. **个别工作区任务重复度偏高**
   - `5e2d93d8-8ad0-4435-b150-1692aacaa994` 原先与另一个多根工作区任务过于接近。
   - 现已提升为“多根工作区 + 工作区级 `files.exclude`”，让 L2 在工作区设置层面也有覆盖。

此外，`930fdb3b-11a8-46fe-9bac-577332e2640e` 现在要求两个焦点切换快捷键都必须存在，避免过去只配置一个键绑定也可能误过的情况。

### 4.4 L2 的当前能力覆盖

相对 L1，L2 已经覆盖以下更高阶能力：

- `.code-workspace` 文件的创建与修改
- 工作区级 `settings` 写入
- 项目级 `.vscode/settings.json` / `tasks.json` / `extensions.json` 写入
- 用户 snippet 文件写入
- 本地 VSIX 安装
- 键绑定冲突处理与双向导航配置

在不引入运行时执行验证的前提下，当前 L2 的能力面已经基本够用。

### 4.5 L2 任务来源标注

> 标注原则：L2 开始出现“多文件协同”与“项目/工作区上下文”，因此来源标注以 VS Code 官方功能页组合为主，并辅以常见工程脚手架实践。

| 任务 | 来源类型 | 具体来源 | 标注理由 |
|---|---|---|---|
| VSIX 安装 + 自动更新控制 | 官方文档组合 | [Extension Marketplace](https://code.visualstudio.com/docs/editor/extension-marketplace) + [Settings](https://code.visualstudio.com/docs/getstarted/settings) | 对应离线安装扩展并同步控制扩展更新策略 |
| 多根工作区保存、目录组合与隐藏规则 | 官方文档 | [Multi-root Workspaces](https://code.visualstudio.com/docs/editor/multi-root-workspaces) | 对应将多个目录纳入工作区并写入工作区级 `settings` |
| 项目级 `.vscode/settings.json`、`tasks.json`、`extensions.json` | 官方文档组合 | [Tasks](https://code.visualstudio.com/docs/editor/tasks) + [Settings](https://code.visualstudio.com/docs/getstarted/settings) + [Extension Marketplace](https://code.visualstudio.com/docs/editor/extension-marketplace) | 对应项目脚手架中最常见的三类配置文件 |
| 终端/编辑器切换与 Explorer 查找冲突处理 | 官方文档 | [Key Bindings for Visual Studio Code](https://code.visualstudio.com/docs/getstarted/keybindings) | 对应真实使用中常见的快捷键冲突消解与焦点导航 |
| Python 用户 snippet 与补全偏好 | 官方文档组合 | [User Defined Snippets](https://code.visualstudio.com/docs/editor/userdefinedsnippets) + [Settings](https://code.visualstudio.com/docs/getstarted/settings) | 对应 snippet 文件维护与补全策略联动 |

---

## 5. L3 任务定义

### 5.1 第三级（L3）—— 高级配置工作流（5 个以上动作或 3 个以上产物）—— 6 个

L3 任务是典型的“配置 bundle”或“工作区脚手架”任务，需要同时维护多个配置文件，或在工作区与项目级配置之间完成联动。当前 L3 统一具备以下特点：

- **启动命令**：`code`、`code /home/user/<project>` 或 `code /home/user/<workspace>.code-workspace`
- **验证方式**：多文件 `vm_file` 联合验证，少量场景使用多次 `check_json_keybindings`
- **主要产物**：`.code-workspace`、`.vscode/tasks.json`、`.vscode/launch.json`、`.vscode/settings.json`、`.vscode/extensions.json`、用户级 `keybindings.json`、`snippets/python.json`

---

#### 任务 L3-1：ops-toolkit 工作区与任务脚手架

- **ID**：`03354b44-fefb-46a8-90a5-bb683fd488b3`
- **指令**：Please open /home/user/ops-toolkit in VS Code, add /home/user/runbooks and /home/user/scripts into the same workspace, and save it as /home/user/ops-toolkit.code-workspace. In that workspace configure files.exclude so .terraform and .cache are hidden, and add extension recommendations for redhat.vscode-yaml and ms-python.python. Also create .vscode/tasks.json inside /home/user/ops-toolkit with two shell tasks named Validate JSON running `python -m json.tool config.json` and Search TODO running `grep -R TODO .`.
- **能力分类**：`Project Scaffold Configuration`
- **来源**：`https://code.visualstudio.com/docs/editor/multi-root-workspaces`；`https://code.visualstudio.com/docs/debugtest/tasks`；`https://code.visualstudio.com/docs/editor/extension-marketplace`；现实场景构造来源：运维交接仓库常见的“多目录工作区 + 推荐 YAML/Python 扩展 + 内置巡检任务”工作区脚手架需求
- **预置资源**：创建 `ops-toolkit/.terraform`、`ops-toolkit/.cache`、`runbooks`、`scripts`，并写入 `config.json`
- **评估函数**：多指标 `[`compare_config`, `compare_config`]`，`conj: and`
- **result**：
  - `vm_file` -> `/home/user/ops-toolkit.code-workspace`
  - `vm_file` -> `/home/user/ops-toolkit/.vscode/tasks.json`
- **expected**：
  - `rule` -> 工作区文件中包含三根目录、`files.exclude` 和扩展推荐
  - `rule` -> `tasks.json` 中包含 `Validate JSON` 与 `Search TODO` 两个 shell task
- **验证逻辑**：同时验证多根工作区搭建和项目任务脚手架。
- **操作步骤数**：5+（打开主目录 -> 添加两个目录 -> 保存工作区 -> 配置工作区 -> 建 tasks）
- **需要新评估函数**：❌

---

#### 任务 L3-2：Python 效率套装配置包

- **ID**：`1f9b6bcc-bcc6-4c23-b874-c79a4ec0c81a`
- **指令**：Please configure a Python productivity bundle in VS Code User settings. Add two custom keybindings: Ctrl+Alt+R should run Python file in terminal when editorTextFocus and editorLangId is python, and Ctrl+Alt+S should save all files when editorTextFocus. Also create a Python user snippet named main_guard with prefix mg, body lines `if __name__ == '__main__':` and `    ${1:main()}`, and description `Python main guard`. Finally set editor.formatOnSave to true and editor.tabCompletion to on in User Settings.
- **能力分类**：`Snippet and Completion Configuration`
- **来源**：`https://code.visualstudio.com/docs/getstarted/keybindings`；`https://code.visualstudio.com/docs/editor/userdefinedsnippets`；`https://code.visualstudio.com/docs/getstarted/settings`；现实场景构造来源：个人 Python 开发环境整理时常见的“运行快捷键 + 保存快捷键 + main_guard snippet + 保存格式化”效率套装需求
- **预置资源**：创建 `/home/user/.config/Code/User/snippets`
- **评估函数**：多指标 `[`check_json_keybindings`, `check_json_keybindings`, `compare_config`, `check_json_settings`]`，`conj: and`
- **result**：
  - `vm_file` -> `/home/user/.config/Code/User/keybindings.json`
  - `vm_file` -> `/home/user/.config/Code/User/keybindings.json`
  - `vm_file` -> `/home/user/.config/Code/User/snippets/python.json`
  - `vm_file` -> `/home/user/.config/Code/User/settings.json`
- **expected**：
  - `rule` -> `Ctrl+Alt+R` 运行 Python 文件
  - `rule` -> `Ctrl+Alt+S` 保存全部文件
  - `rule` -> `python.json` 中包含 `main_guard` snippet
  - `rule` -> `{"editor.formatOnSave":true,"editor.tabCompletion":"on"}`
- **验证逻辑**：同时验证用户快捷键、用户 snippet 和通用编辑设置，属于典型的跨用户配置文件 bundle。
- **操作步骤数**：5+（配两项 keybinding -> 建 snippet -> 写两个设置）
- **需要新评估函数**：❌

---

#### 任务 L3-3：已有工作区扩展为 Python 多目录工作区

- **ID**：`6ed0a554-cbee-4b44-84ea-fd6c042f4fe1`
- **指令**：Please open /home/user/project.code-workspace in VS Code, add /home/user/data1, /home/user/data2 and /home/user/data3 into this workspace, configure workspace settings to hide __pycache__ and .venv folders in Explorer, and create .vscode/extensions.json inside /home/user/project recommending ms-python.python and ms-python.vscode-pylance.
- **能力分类**：`Multi-root Workspace Management`
- **来源**：`https://code.visualstudio.com/docs/editor/multi-root-workspaces`；`https://code.visualstudio.com/docs/editor/extension-marketplace`；`https://code.visualstudio.com/docs/getstarted/settings`；现实场景构造来源：数据与代码分目录维护的 Python 团队常见的“扩展已有工作区 + 隐藏虚拟环境与缓存目录 + 推荐语言扩展”协作配置需求
- **预置资源**：创建 `/home/user/project`、`/home/user/project/.venv`、`/home/user/project/__pycache__`、`/home/user/data1`、`/home/user/data2`、`/home/user/data3`，并预写入仅包含 `project` 的工作区文件
- **评估函数**：多指标 `[`compare_config`, `compare_config`]`，`conj: and`
- **result**：
  - `vm_file` -> `/home/user/project.code-workspace`
  - `vm_file` -> `/home/user/project/.vscode/extensions.json`
- **expected**：
  - `rule` -> 工作区文件中包含四个目录和 `files.exclude` 规则
  - `rule` -> `extensions.json` 推荐 `ms-python.python` 与 `ms-python.vscode-pylance`
- **验证逻辑**：同时验证已有工作区扩展、工作区级隐藏规则和项目级扩展推荐。
- **操作步骤数**：5+（打开已有工作区 -> 添加三个目录 -> 写隐藏规则 -> 建扩展推荐）
- **需要新评估函数**：❌

---

#### 任务 L3-4：数据管线项目的 tasks + launch + Python 分析设置

- **ID**：`85281b81-0f3a-4ed7-aed9-05c883aec8fe`
- **指令**：Please open /home/user/data-pipeline in VS Code and prepare it for running and debugging. Create .vscode/tasks.json with a shell task named Install Requirements that runs `pip install -r requirements.txt` and another task named Run Current File that runs `python ${file}`. Then create .vscode/launch.json with a Python launch configuration named Debug Current File that launches ${file} in the integrated terminal and uses Install Requirements as its preLaunchTask. Also create .vscode/settings.json so python.analysis.typeCheckingMode is basic.
- **能力分类**：`Debug and Test Workflow Setup`
- **来源**：`https://code.visualstudio.com/docs/debugtest/tasks`；`https://code.visualstudio.com/docs/debugtest/debugging-configuration`；`https://code.visualstudio.com/docs/python/debugging`；`https://code.visualstudio.com/docs/python/settings-reference`；现实场景构造来源：数据管线项目初始化时常见的“安装依赖任务 + 运行当前文件任务 + preLaunchTask 调试入口 + 基础类型检查”联动配置需求
- **预置资源**：创建 `/home/user/data-pipeline`，并写入 `requirements.txt`
- **评估函数**：多指标 `[`compare_config`, `compare_config`, `check_json_settings`]`，`conj: and`
- **result**：
  - `vm_file` -> `/home/user/data-pipeline/.vscode/tasks.json`
  - `vm_file` -> `/home/user/data-pipeline/.vscode/launch.json`
  - `vm_file` -> `/home/user/data-pipeline/.vscode/settings.json`
- **expected**：
  - `rule` -> `tasks.json` 中包含 `Install Requirements` 和 `Run Current File`
  - `rule` -> `launch.json` 中包含 `Debug Current File`，并使用 `preLaunchTask`
  - `rule` -> `{"python.analysis.typeCheckingMode":"basic"}`
- **验证逻辑**：验证任务、调试配置、Python 分析设置三者联动。
- **操作步骤数**：6+（打开项目 -> 写两个 task -> 写一个 launch configuration -> 写 settings）
- **需要新评估函数**：❌

---

#### 任务 L3-5：frontend-app 项目脚手架包

- **ID**：`c46a7eb6-c0ed-4ef9-9987-a8254815df1d`
- **指令**：Please open /home/user/frontend-app in VS Code and scaffold the project workspace. Create .vscode/extensions.json recommending dbaeumer.vscode-eslint and esbenp.prettier-vscode. Create .vscode/tasks.json with two shell tasks named npm: build running `npm run build` and npm: test running `npm test`. Also create .vscode/settings.json so editor.formatOnSave is true, editor.defaultFormatter is esbenp.prettier-vscode, and files.associations maps *.css to tailwindcss.
- **能力分类**：`Project Scaffold Configuration`
- **来源**：`https://code.visualstudio.com/docs/debugtest/tasks`；`https://code.visualstudio.com/docs/editor/extension-marketplace`；`https://code.visualstudio.com/docs/getstarted/settings`；现实场景构造来源：前端项目开工时常见的“推荐 ESLint/Prettier + 预置 build/test 任务 + 默认格式器与文件关联”脚手架需求
- **预置资源**：创建 `/home/user/frontend-app`
- **评估函数**：多指标 `[`compare_config`, `compare_config`, `check_json_settings`]`，`conj: and`
- **result**：
  - `vm_file` -> `/home/user/frontend-app/.vscode/extensions.json`
  - `vm_file` -> `/home/user/frontend-app/.vscode/tasks.json`
  - `vm_file` -> `/home/user/frontend-app/.vscode/settings.json`
- **expected**：
  - `rule` -> `extensions.json` 推荐 ESLint 与 Prettier
  - `rule` -> `tasks.json` 中包含 `npm: build` 与 `npm: test`
  - `rule` -> `{"editor.formatOnSave":true,"editor.defaultFormatter":"esbenp.prettier-vscode","files.associations":{"*.css":"tailwindcss"}}`
- **验证逻辑**：验证前端项目中扩展、任务、格式化器和文件关联四类配置是否成套落地。
- **操作步骤数**：5+（打开项目 -> 建 extensions -> 建 tasks -> 建 settings）
- **需要新评估函数**：❌

---

#### 任务 L3-6：research 工作区与研究辅助配置包

- **ID**：`cf058642-f90e-469a-9aef-d065c5717ba1`
- **指令**：Please open /home/user/research-core in VS Code, add /home/user/notebooks and /home/user/reports into the same workspace, and save it as /home/user/research.code-workspace. In that workspace, configure settings so editor.rulers is [88], files.exclude hides .ipynb_checkpoints and __pycache__, and search.exclude hides data/cache. Also add workspace extension recommendations for ms-python.python and ms-toolsai.jupyter. Then create .vscode/tasks.json inside /home/user/research-core with two shell tasks named Index Notebooks running `find ../notebooks -maxdepth 1 -name '*.ipynb'` and List Reports running `find ../reports -maxdepth 1 -type f`, and create .vscode/settings.json so editor.formatOnSave is true, files.trimTrailingWhitespace is true, and search.exclude hides outputs.
- **能力分类**：`Project Scaffold Configuration`
- **来源**：`https://code.visualstudio.com/docs/editor/multi-root-workspaces`；`https://code.visualstudio.com/docs/debugtest/tasks`；`https://code.visualstudio.com/docs/getstarted/settings`；`https://code.visualstudio.com/docs/editor/extension-marketplace`；现实场景构造来源：研究型项目常见的“代码目录 + notebook 目录 + 报告目录”联合工作区，以及为检索、格式化和产物排除预置协作配置的需求
- **预置资源**：创建 `/home/user/research-core`、`/home/user/research-core/outputs`、`/home/user/notebooks`、`/home/user/reports`、`/home/user/data/cache`
- **评估函数**：多指标 `[`compare_config`, `compare_config`, `check_json_settings`]`，`conj: and`
- **result**：
  - `vm_file` -> `/home/user/research.code-workspace`
  - `vm_file` -> `/home/user/research-core/.vscode/tasks.json`
  - `vm_file` -> `/home/user/research-core/.vscode/settings.json`
- **expected**：
  - `rule` -> 工作区文件中包含多根目录、ruler、排除规则和扩展推荐
  - `rule` -> `tasks.json` 中包含 `Index Notebooks` 与 `List Reports`
  - `rule` -> `{"editor.formatOnSave":true,"files.trimTrailingWhitespace":true,"search.exclude":{"outputs":true}}`
- **验证逻辑**：同时验证研究工作区结构、工作区级设置、项目任务和项目级编辑设置。
- **操作步骤数**：6+（打开项目 -> 添加两个目录 -> 保存工作区 -> 写工作区配置 -> 建 tasks -> 建 settings）
- **需要新评估函数**：❌

---

### 5.2 L3 任务汇总

| # | 任务名称 | 主要产物 | 评估函数 | 步骤数 |
|---|---|---|---|---|
| 1 | ops-toolkit 工作区与任务脚手架 | `.code-workspace` + `tasks.json` | `compare_config` + `compare_config` | 5+ |
| 2 | Python 效率套装配置包 | `keybindings.json` + `python.json` + `settings.json` | 4 项联合验证 | 5+ |
| 3 | 已有工作区扩展为 Python 多目录工作区 | `.code-workspace` + `extensions.json` | `compare_config` + `compare_config` | 5+ |
| 4 | 数据管线项目的 tasks + launch + Python 分析设置 | `tasks.json` + `launch.json` + `settings.json` | 3 项联合验证 | 6+ |
| 5 | frontend-app 项目脚手架包 | `extensions.json` + `tasks.json` + `settings.json` | 3 项联合验证 | 5+ |
| 6 | research 工作区与研究辅助配置包 | `.code-workspace` + `tasks.json` + `settings.json` | 3 项联合验证 | 6+ |

**L3 统计**：
- 总任务数：**6**
- 至少 2 个产物联合验证：**6**
- 涉及 `.code-workspace`：**4**
- 涉及 `tasks.json`：**4**
- 涉及 `launch.json`：**1**
- 涉及项目级 `extensions.json`：**2**
- 含工作区级扩展推荐：**2**

### 5.3 L3 检查结论与必要修改

本轮检查结论如下：

1. **整体上，L3 的方向是对的**
   - 当前 L3 已经覆盖工作区 bundle、项目脚手架、调试配置联动、用户级效率配置包等场景。

2. **原始数据存在两道偏轻且同质化的题目**
   - `6ed0a554-cbee-4b44-84ea-fd6c042f4fe1`
   - `cf058642-f90e-469a-9aef-d065c5717ba1`

   这两题原本都主要验证单个 `.code-workspace` 文件，虽然 instruction 较长，但产物数量和联动复杂度更接近加强版 L2，不够像真正的 L3。

3. **已完成的必要修改**
   - `6ed0...` 现已升级为：已有工作区扩展 + 工作区隐藏规则 + 项目级扩展推荐。
   - `cf058...` 现已升级为：研究工作区文件 + 项目任务 + 项目设置的三产物 bundle。

### 5.4 L3 的当前能力覆盖

当前 L3 相比 L2，已经更稳定地覆盖以下能力：

- 工作区文件与项目级 `.vscode/*` 的联动配置
- 调试配置与任务依赖链
- 工作区级扩展推荐与项目级扩展推荐的区分
- 用户级效率配置包的多文件一致性维护
- 基于已有工作区继续扩展而不是从零开始创建

在当前 evaluator 体系不执行 task / launch 运行结果的前提下，这一版 L3 已经基本符合“高阶配置工作流”定位，且同质化问题已明显缓解。

### 5.5 L3 任务来源标注

> 标注原则：L3 以“工作区 bundle / 项目脚手架 bundle”为核心，来源不再是单页功能文档，而是多页官方文档与真实团队交接配置模式的组合。

| 任务 | 来源类型 | 具体来源 | 标注理由 |
|---|---|---|---|
| ops-toolkit / research / 既有工作区扩展类任务 | 官方文档组合 | [Multi-root Workspaces](https://code.visualstudio.com/docs/editor/multi-root-workspaces) + [Tasks](https://code.visualstudio.com/docs/editor/tasks) + [Extension Marketplace](https://code.visualstudio.com/docs/editor/extension-marketplace) | 对应多目录工作区、交接工作区、推荐扩展和常用任务的组合式交付 |
| Python 效率套装配置包 | 官方文档组合 | [Settings](https://code.visualstudio.com/docs/getstarted/settings) + [Key Bindings for Visual Studio Code](https://code.visualstudio.com/docs/getstarted/keybindings) + [User Defined Snippets](https://code.visualstudio.com/docs/editor/userdefinedsnippets) + [Python Settings Reference](https://code.visualstudio.com/docs/python/settings-reference) | 对应个人 Python 开发环境在设置、快捷键、snippet 三个面的联合定制 |
| 数据管线项目的 tasks + launch + Python 分析设置 | 官方文档组合 | [Tasks](https://code.visualstudio.com/docs/editor/tasks) + [Debugging](https://code.visualstudio.com/docs/debugtest/debugging) + [Python Settings Reference](https://code.visualstudio.com/docs/python/settings-reference) | 对应项目执行入口、调试入口和分析器设置的联动脚手架 |
| frontend-app 项目脚手架包 | 官方文档组合 | [Tasks](https://code.visualstudio.com/docs/editor/tasks) + [Settings](https://code.visualstudio.com/docs/getstarted/settings) + [Extension Marketplace](https://code.visualstudio.com/docs/editor/extension-marketplace) | 对应前端项目最常见的 formatter、测试命令和扩展推荐组合 |

---

## 6. Interactive 任务设计

### 6.1 当前状态与数据概览

VS Code 的交互式任务并非空缺，而是已经落在 `evaluation_examples/examples/interactive_xt/` 下，共 **16 个任务**。它们与 `vs_code_new` 的静态配置任务形成互补：静态任务强调一次性交付，Interactive 任务强调澄清、返工、纠错和中断后的收敛。

| 场景类型 | 数量 | 代表任务 | 主要考点 |
|---|---:|---|---|
| `ambiguous_instruction` | 3 | `interactive_vscode_ambiguous_101` | 是否会先澄清再执行 |
| `requirement_change` | 3 | `interactive_vscode_requirement_change_112` | 是否按最新要求覆盖旧计划 |
| `progressive_refinement` | 4 | `interactive_vscode_progressive_113` | 是否能在多轮追加需求下保持连续一致 |
| `correction` | 3 | `interactive_vscode_correction_114` | 是否能按纠正后的目标收敛，并撤销旧目标 |
| `interruption` | 3 | `interactive_vscode_interruption_115` | 是否能在执行中途响应插入的新约束 |

当前分布特征如下：

- 任务总数：**16**
- phase 分布：**2-phase = 1**，**3-phase = 14**，**4-phase = 1**
- trigger 覆盖：`agent_asks` 3 个任务，`step_count` 3 个任务，其余通过 `agent_done` 推进
- evaluator 分布：`exact_match` 12 个，`check_json_settings` 4 个
- 主要产物：用户设置 / 键绑定 / snippet、Markdown 文档、`.code-workspace`、项目级 `.vscode/*`

### 6.2 交互式任务清单

| ID | 场景 | 核心目标 | 最终产物 | 难度 |
|---|---|---|---|---|
| `interactive_vscode_ambiguous_101` | 模糊需求 | 先澄清“写笔记更省心”具体指什么，再补自动保存、换行和保存清理 | `settings.json` | 低 |
| `interactive_vscode_ambiguous_106` | 模糊需求 | 先追问“交接整理”具体交付，再补 `HANDOFF.md` 与用户设置 | `HANDOFF.md` + `settings.json` | 中 |
| `interactive_vscode_ambiguous_111` | 模糊需求 | 将运维项目整理为交接多根工作区，并补扩展推荐与项目任务 | `.code-workspace` + `tasks.json` | 中高 |
| `interactive_vscode_requirement_change_102` | 需求变更 | 先做大字体阅读模式，再改回较小字号并补相对行号和 ruler | `settings.json` | 低 |
| `interactive_vscode_requirement_change_107` | 需求变更 | 在同一份发布手册里按新结构重排步骤并补 owner 行 | `release_runbook.md` | 中 |
| `interactive_vscode_requirement_change_112` | 需求变更 | 前端项目脚手架在中途改任务命名、测试命令和隐藏目录要求 | `extensions.json` + `tasks.json` + `settings.json` | 中高 |
| `interactive_vscode_progressive_103` | 逐步追加 | 连续三轮编辑同一份会议纪要 | `meeting_notes.md` | 低 |
| `interactive_vscode_progressive_108` | 逐步追加 | 连续完善事故简报并补表格 | `incident_brief.md` | 中 |
| `interactive_vscode_progressive_113` | 逐步追加 | 逐步搭好 Python 高频开发环境：settings + keybindings + snippets | `settings.json` + `keybindings.json` + `python.json` | 中高 |
| `interactive_vscode_progressive_116` | 逐步追加 | 逐步把 analytics 项目补成 `.vscode` 脚手架：settings + tasks + extensions | `.vscode/settings.json` + `.vscode/tasks.json` + `.vscode/extensions.json` | 中 |
| `interactive_vscode_correction_104` | 纠错 | 将内容从错误文件迁移到正确文件，并保持原文件空白 | `ideas.md` + 空白 `status.md` | 低 |
| `interactive_vscode_correction_109` | 纠错 | 工作区审稿配置中更正 tab size 和 ruler，并追加保存规则 | `.vscode/settings.json` | 中 |
| `interactive_vscode_correction_114` | 纠错 | 纠正终端导航快捷键并处理 Explorer 查找冲突 | `keybindings.json` | 中高 |
| `interactive_vscode_interruption_105` | 中断插入 | 显示模式配置过程中切换为审稿模式，要求废弃原阅读方案并按新偏好收敛 | `settings.json` | 中 |
| `interactive_vscode_interruption_110` | 中断插入 | 起草事故报告时突然改成客户说明，并删除旧草稿 | `customer_update.md` | 中 |
| `interactive_vscode_interruption_115` | 中断插入 | 多根工作区搭建中途改目录组合和保存目标，并补最终工作区配置 | `.code-workspace` | 中高 |

### 6.3 可行性评估

这 16 个交互式任务整体上是**可执行且可验证的**，原因有三点：

1. **最终验收都落在静态产物上**
  - 不是检查“用户是不是点到了某个 UI”，而是检查最终文件内容或命令输出，因此只要 Agent 最终把配置或文档写对，就可稳定验证。

2. **几乎不依赖外部运行时**
  - 没有要求真正运行 build、test、debug session 或联网安装扩展；绝大多数任务只涉及编辑器文件创建、JSON 改写和工作区保存。

3. **触发器与场景语义基本一致**
  - `agent_asks` 用在模糊需求题上，能真实测到“先澄清再执行”；
  - `step_count` 只用于 interruption 类任务，能模拟“做着做着被插话改需求”；
  - `agent_done` 适合 requirement change / correction / progressive refinement 这类“上一步完成后再给下一步”的场景。

### 6.4 难度与同质化评估

本轮检查后的结论如下：

1. **整体难度结构基本合理**
  - 低难度任务主要是单文件设置或单文档连续编辑，如 `101`、`103`、`104`；
  - 中难度任务开始要求在同一产物上返工、重排或完成双产物交付，如 `106`、`107`、`108`、`109`、`110`；
  - 中高难度任务集中在多根工作区、多文件 `.vscode` 脚手架和多类型配置联动，如 `111`、`112`、`113`、`114`、`115`。

2. **原始数据确实存在局部同质化**
  - `interactive_vscode_ambiguous_101`、`interactive_vscode_interruption_105`、`interactive_vscode_progressive_116` 原先都过于接近“基础 settings 连续改动”，区分度不足。

3. **已完成两项必要修改**
  - `interactive_vscode_progressive_116` 已从“极轻量的三步 settings 调整”升级为“analytics 项目的 `.vscode/settings.json` + `.vscode/tasks.json` + `.vscode/extensions.json` 逐步搭建”。
  - `interactive_vscode_interruption_105` 已增强为“阅读模式切换到审稿模式”的中断场景，并把中断时机调整为 `step_count=2`，减少过早打断带来的脆弱性。

4. **剩余同质化仍有，但在可接受范围内**
  - Markdown 连续编辑类任务有 5 个，确实形成一个子簇；
  - 但它们分别覆盖 progressive / correction / requirement change / interruption，不只是换文本内容，交互机制不同；
  - 与工作区/脚手架/键绑定/用户设置类任务合并后，整体分布仍然足够多样。

因此，当前 VS Code Interactive 任务可以视为**可直接纳入正式文档的有效子集**，无需再额外增题。

### 6.5 Interactive 任务来源映射

> 说明：Interactive 任务的来源不应只写官方文档，而应标注“真实工作流模式 + 官方功能页”。前者解释为什么会出现多轮对话，后者解释它依赖哪些 VS Code 功能。

| 场景族 | 真实工作来源（Primary Source） | 证据包（最小） | Task JSON `source` 建议写法 |
|---|---|---|---|
| `ambiguous_instruction` | 新人或非技术同事给出模糊需求，如“整理成适合交接”或“配置得顺手一点” | ① 模糊原始需求摘录 ② 澄清问答记录 ③ 澄清后最终交付清单 | `vscode_interactive;source_type=clarification_required;source_ref=<id_or_url>;evidence=ambiguous_brief` |
| `requirement_change` | 文档或项目脚手架已经起草，但用户在第一版后改标题、步骤顺序、命名或命令 | ① 初始需求 ② 变更后需求 ③ 新旧差异对照 | `vscode_interactive;source_type=change_request;source_ref=<id_or_url>;evidence=requirement_change` |
| `progressive_refinement` | 真实交付常见的“先给可用版本，再逐步补全”流程 | ① 阶段性指令 ② 每轮确认语句 ③ 最终交付验收项 | `vscode_interactive;source_type=iterative_delivery;source_ref=<id_or_url>;evidence=progressive_refinement` |
| `correction` | 用户说错文件名、说错快捷键或说错参数，随后要求按纠正后的目标收敛 | ① 首轮错误指令 ② 纠正语句 ③ 最终正确版本验收记录 | `vscode_interactive;source_type=user_correction;source_ref=<id_or_url>;evidence=target_correction` |
| `interruption` | Agent 执行到一半时，用户临时插入新约束或改保存目标 | ① 初始计划 ② 中断时点记录 ③ 中断后最终标准 | `vscode_interactive;source_type=mid_process_interrupt;source_ref=<id_or_url>;evidence=interruption` |

#### 来源证据落地字段（建议统一）

- **source_type**：`clarification_required` / `change_request` / `iterative_delivery` / `user_correction` / `mid_process_interrupt`
- **source_ref**：匿名化 URL、工单号、访谈编号或课程作业编号
- **captured_at**：取证日期（`YYYY-MM-DD`）
- **anonymized_excerpt**：匿名化原文摘录（1-3 句）
- **mapping_note**：原始交互如何映射到 `phases` 与 `trigger`
- **reviewers**：双人审核与仲裁记录

---

## 7. Task JSON 模板

### 7.1 单文件 User Settings 任务模板

```json
{
  "id": "<uuid4>",
  "snapshot": "vscode",
  "instruction": "Please update VS Code User Settings so that ...",
  "source": [
    "https://code.visualstudio.com/docs/getstarted/settings"
  ],
  "config": [
    {
      "type": "launch",
      "parameters": {
        "command": ["code"]
      }
    },
    {
      "type": "activate_window",
      "parameters": {
        "window_name": "Visual Studio Code"
      }
    }
  ],
  "trajectory": "trajectories/",
  "related_apps": ["vscode"],
  "evaluator": {
    "func": "check_json_settings",
    "expected": {
      "type": "rule",
      "rules": {
        "expected": {
          "files.autoSave": "afterDelay",
          "files.autoSaveDelay": 700
        }
      }
    },
    "result": {
      "type": "vm_file",
      "path": "/home/user/.config/Code/User/settings.json",
      "dest": "settings.json"
    }
  },
  "proxy": false,
  "fixed_ip": false,
  "possibility_of_env_change": "low"
}
```

### 7.2 多文件项目配置任务模板

```json
{
  "id": "<uuid4>",
  "snapshot": "vscode",
  "instruction": "Please open /home/user/project in VS Code and create .vscode/tasks.json and .vscode/settings.json ...",
  "source": [
    "https://code.visualstudio.com/docs/debugtest/tasks"
  ],
  "config": [
    {
      "type": "command",
      "parameters": {
        "command": ["mkdir", "-p", "/home/user/project"]
      }
    },
    {
      "type": "launch",
      "parameters": {
        "command": ["code", "/home/user/project"]
      }
    },
    {
      "type": "activate_window",
      "parameters": {
        "window_name": "Visual Studio Code"
      }
    }
  ],
  "trajectory": "trajectories/",
  "related_apps": ["vscode"],
  "evaluator": {
    "func": ["compare_config", "check_json_settings"],
    "conj": "and",
    "result": [
      {
        "type": "vm_file",
        "path": "/home/user/project/.vscode/tasks.json",
        "dest": "tasks.json"
      },
      {
        "type": "vm_file",
        "path": "/home/user/project/.vscode/settings.json",
        "dest": "settings.json"
      }
    ],
    "expected": [
      {
        "type": "rule",
        "rules": {
          "expected": "{\n  \"version\": \"2.0.0\", ... }"
        }
      },
      {
        "type": "rule",
        "rules": {
          "expected": {
            "python.testing.pytestEnabled": true
          }
        }
      }
    ]
  }
}
```

### 7.3 工作区与扩展推荐模板

```json
{
  "id": "<uuid4>",
  "snapshot": "vscode",
  "instruction": "Please open /home/user/project in VS Code, add extra folders, save the workspace, and add workspace settings and extension recommendations.",
  "source": [
    "https://code.visualstudio.com/docs/editor/multi-root-workspaces"
  ],
  "config": [
    {
      "type": "command",
      "parameters": {
        "command": ["mkdir", "-p", "/home/user/project", "/home/user/data1", "/home/user/data2"]
      }
    },
    {
      "type": "launch",
      "parameters": {
        "command": ["code", "/home/user/project"]
      }
    },
    {
      "type": "activate_window",
      "parameters": {
        "window_name": "Visual Studio Code"
      }
    }
  ],
  "evaluator": {
    "func": "compare_config",
    "result": {
      "type": "vm_file",
      "path": "/home/user/project.code-workspace",
      "dest": "project.code-workspace"
    },
    "expected": {
      "type": "rule",
      "rules": {
        "expected": "{\n  \"folders\": [...],\n  \"settings\": {...},\n  \"extensions\": {...}\n}"
      }
    }
  }
}
```

---

## 8. Docker / 镜像要求

### 必备组件

- Visual Studio Code GUI
- `code` CLI 可用
- 用户配置目录存在：`/home/user/.config/Code/User/`
- 常规 shell 命令可用：`mkdir`、`bash`、`grep`

### 对 Python 相关任务的建议

以下任务涉及 Python 专属设置或命令：

- `python.execInTerminal`
- `python.analysis.*`
- `[python].editor.defaultFormatter`

如果希望智能体主要通过 VS Code UI 完成，而不是直接编辑 JSON，建议镜像预装：

- `ms-python.python`
- `ms-python.black-formatter`

否则即使 evaluator 可通过，只靠 Settings UI 搜索时用户体验会不稳定。

### 对扩展安装任务的要求

- `code --list-extensions` 需要可用。
- 本地安装 VSIX 的 UI 流程和 CLI 行为应与当前 VS Code 版本一致。

---

## 9. L1 覆盖性检查与修改建议

### 9.1 当前结论

**结论分两层：**

1. **数据正确性层面**：现有 L1 任务没有明显错误，任务目标、结果路径和评估函数基本匹配，**不需要为了“能否验证”而立即修改现有 JSON**。
2. **数据集设计层面**：L1 覆盖并不全面，且有一定重复，**建议下一轮迭代做结构性调整**。

### 9.2 L1 的优点

- 已覆盖用户设置的多个子域：
  - 保存行为
  - 自动换行
  - Python 编辑体验
  - 调试体验
  - 外观
  - 文件树隐藏规则
  - 基础键绑定
- 全部都是低环境风险、可稳定拉取结果文件的任务。
- `check_json_settings` 足以覆盖当前 L1 中出现的嵌套结构。

### 9.3 L1 的主要问题

#### 问题 1：任务类型过度集中在 `settings.json`

- 15 个 L1 中，13 个都在改 `settings.json`。
- 这导致 L1 更像“用户偏好设置数据集”，而不是“VS Code 基础能力数据集”。

#### 问题 2：存在明显重复簇

重复最明显的两组：

1. 自动保存簇
   - `0ed39f63-6049-43d4-ba4d-5fa2fe04a951`
   - `70745df8-f2f5-42bd-8074-fbc10334fcc5`

   两者都在测：
   - `files.autoSave=afterDelay`
   - `files.autoSaveDelay`
   - `files.trimTrailingWhitespace=true`
   - `files.insertFinalNewline=true`

   差异只有：
   - 一个多测了 `editor.wordWrap`
   - delay 值不同

2. Python 新文件/草稿簇
   - `57242fad-77ca-454f-b71b-f187181a9f23`
   - `971cbb5b-3cbf-4ff7-9e24-b5c84fcebfa6`

   两者都在测：
   - `files.defaultLanguage=python`
   - 自动保存相关行为

   差异仅体现在：
   - 一个测 `editor.renderWhitespace`
   - 一个测 `workbench.startupEditor`

#### 问题 3：缺少几个很自然的 L1 基础能力

当前 L1 缺失但完全可以做成单文件低风险任务的类型包括：

- 单个 user snippet 创建任务
- 单个项目级 `.vscode/settings.json` 写入任务
- 单个 `tasks.json` 创建任务
- 单个 `extensions.json` 推荐任务
- 更丰富的键绑定任务（尤其是与导航、命令面板、终端相关的基础操作）

### 9.4 是否需要修改

**建议：需要改，但属于“优化覆盖面”的修改，不是“修 bug”式修改。**

更具体地说：

- **不建议**现在直接推翻现有 15 个 L1。
- **建议**下一版对其中 2 到 4 个任务做替换或重构。

### 9.5 具体修改建议

#### 建议 A：保留 1 个自动保存簇任务，替换另 1 个

建议保留：

- `0ed39f63-6049-43d4-ba4d-5fa2fe04a951`

建议替换：

- `70745df8-f2f5-42bd-8074-fbc10334fcc5`

可替换为：

- 新建一个简单的 `tasks.json` 任务，例如创建 `Run Tests` shell task。

#### 建议 B：保留 1 个 Python 新文件簇任务，替换另 1 个

建议保留：

- `971cbb5b-3cbf-4ff7-9e24-b5c84fcebfa6`

建议替换：

- `57242fad-77ca-454f-b71b-f187181a9f23`

可替换为：

- 单个 Python snippet 创建任务，例如 `main_guard` 或 `pytest_func`。

#### 建议 C：把 1 个 L2 能力下沉到 L1

最适合下沉的类型：

- 单文件 `extensions.json` 推荐任务
- 单文件 `python.json` snippet 任务

理由：

- 它们本身仍然是单一产物。
- 风险不高。
- 比重复的 `settings.json` 任务更能增加能力面。

#### 建议 D：在补新键绑定任务前，先考虑增强 evaluator

如果后续想加入“删除冲突快捷键”“覆盖已有绑定”这类 L1 任务，建议先增强：

- `check_json_keybindings` 支持“必须不存在”的负向检查。

否则新任务容易出现“新增成功但旧冲突仍在”的漏判。

### 9.6 最终判断

| 维度 | 结论 |
|---|---|
| 现有 L1 是否可用 | 可用 |
| 现有 L1 是否有明显错误 | 没有明显错误 |
| 现有 L1 是否功能全面 | 不全面 |
| 是否需要立即修正现有 JSON | 不需要 |
| 是否建议下一轮做结构性优化 | 建议 |
