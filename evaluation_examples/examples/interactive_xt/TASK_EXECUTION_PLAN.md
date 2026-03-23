# interactive_xt 交互式任务生成执行计划

## 1. 项目理解总结

本项目是在 OSWorld 基础上扩展的 **Interactive 多轮交互评测**。
核心特点不是单条 `instruction`，而是：

- 使用 `"interactive": true` 标记交互任务
- 使用 `phases` 定义多阶段用户需求演进
- 每个 phase 通过 `trigger` 控制何时由 `UserSimulator` 介入
- Agent 可以在 `agent_asks` 场景中通过 `call_user` 主动提问
- 评估仍然主要看 **最终状态**，不是每一步过程

当前代码链路已经具备：

- `lib_run_interactive.py`：多 phase 主循环
- `mm_agents/user_simulator.py`：用户模拟与触发逻辑
- `mm_agents/evocua/evocua_agent.py`：支持 `call_user`、注入追加消息、清理 `DONE`
- `evaluation_examples/examples/interactive/`：已有交互式样例

因此，后续工作重点不是改框架，而是**稳定地产出高质量交互式任务 JSON**。

---

## 2. 本次任务目标

我们后续要面向以下 3 个系统生成交互式任务：

- `vscode`
- `chrome`
- `os`

目标不是简单把单轮任务拆成多句，而是构造**真实用户会发生的需求变化、澄清、打断、纠错、渐进细化**。

---

## 3. 现有素材与可复用基线

现有非交互案例位于：

- `evaluation_examples/examples/interactive_xt/case`

当前已看到的 3 个基线任务：

1. `vscode`：修改 User Settings
2. `chrome`：访问网页并加入书签栏
3. `os`：调整无障碍/可读性设置

这 3 类都非常适合改造为交互式任务：

- `vscode` 适合做 **渐进细化 / 纠错 / 需求变更**
- `chrome` 适合做 **导航后变更目标 / 标签页管理 / 收藏整理 / 下载确认**
- `os` 适合做 **模糊指令 / 打断 / 设置修正 / 文件整理**

---

## 4. 总体生成策略

采用“两层分类 + 一套统一生产流程”。

### 4.1 第一层：按系统分类

#### A. VS Code
适合的任务母题：
- Settings 修改
- 编辑器行为配置
- 文件创建/编辑/格式化
- 工作区整理
- 扩展/主题/视图切换

#### B. Chrome
适合的任务母题：
- 搜索与导航
- 收藏夹/书签栏管理
- 多标签页整理
- 下载文件与保存位置确认
- 表单填写前后的要求变更

#### C. OS
适合的任务母题：
- 系统设置调整
- 文件/文件夹整理
- 应用启动与基础配置
- 无障碍/显示/输入设置
- 桌面环境清理与确认

### 4.2 第二层：按交互模式分类

建议固定 5 大交互 archetype：

1. **ambiguous_instruction**
   - 用户起始描述模糊
   - 适用 trigger：`agent_asks`
   - 适合：`vscode` / `os` / `chrome`

2. **requirement_change**
   - Agent 已开始或完成一部分后，用户改需求
   - 适用 trigger：`agent_done` 或 `step_count`
   - 适合：三类系统都适用

3. **progressive_refinement**
   - 用户逐步补充限制条件
   - 适用 trigger：`agent_done`
   - 最适合：`vscode`、`chrome`

4. **interruption**
   - 执行中途被打断
   - 适用 trigger：`step_count`
   - 最适合：`os`、`chrome`

5. **correction**
   - 用户纠正错误对象/错误目标/错误参数
   - 适用 trigger：`agent_done`
   - 最适合：`vscode`、`os`

---

## 5. 推荐的任务分类矩阵

建议先做一个小而稳的首批集合：**每个系统 6 个任务，共 18 个**。

### 5.1 VS Code 首批 6 类

1. **设置渐进细化**
   - 例：先开自动保存，再补充延迟、换行、保存行为
2. **设置需求变更**
   - 例：先开 `wordWrap`，后改成只在特定方式下换行或关闭某项设置
3. **工作区文件整理 + 纠错**
   - 例：创建/重命名文件后，用户纠正目标文件名
4. **搜索替换后追加要求**
   - 例：先替换文本，再要求仅限当前文件/保存全部
5. **模糊指令场景**
   - 例：“帮我把这个编辑环境整理一下”→ Agent 应主动问要整理侧边栏、设置还是文件
6. **主题/界面偏好逐步明确**
   - 例：先“看着舒服一点”，再指定主题、字体大小、迷你地图开关

### 5.2 Chrome 首批 6 类

1. **导航 + 书签保存 + 书签调整**
2. **搜索结果选择 + 用户中途改站点**
3. **多标签页打开后整理标签**
4. **下载文件后要求移动或确认文件名**
5. **模糊浏览任务**
   - 例：“帮我把这个网站留着以后用”→ Agent 需询问是收藏、固定标签页还是保存链接
6. **表单/筛选条件渐进细化**
   - 例：先搜索商品/页面，再补充筛选条件

### 5.3 OS 首批 6 类

1. **文件整理模糊指令**
2. **文件夹创建中途打断**
3. **系统设置逐步细化**
   - 例：先调易读性，再补充字号、缩放、光标
4. **设置纠错**
   - 例：用户说“不是这个选项，是另一个开关”
5. **桌面清理 + 最终确认**
6. **应用启动与简单配置变更**

---

## 6. 触发器使用规则

为保证任务稳定，优先使用以下规则：

### 6.1 默认优先级

1. `agent_done`
2. `agent_asks`
3. `step_count`
4. `agent_idle`
5. `llm_judge`

### 6.2 具体建议

- **模糊任务**：优先 `agent_asks`
- **明确的阶段切换**：优先 `agent_done`
- **需要中途打断**：使用 `step_count`
- **涉及等待下载/加载**：必要时才使用 `agent_idle`
- **只能靠截图看结果**：最后才用 `llm_judge`

### 6.3 稳定性原则

尽量让 evaluator 基于：
- 文件内容
- 路径存在性
- JSON 配置值
- `gsettings`
- Chrome 书签/当前 URL

避免过度依赖视觉判断。

---

## 7. 各系统的 evaluator 设计原则

### 7.1 VS Code
优先检查：
- `/home/user/.config/Code/User/settings.json`
- 工作区文件内容
- 文件是否存在/重命名是否成功
- JSON 精确字段值

适合使用：
- `check_json_settings`
- `exact_match`
- `check_include_exclude`
- `vm_file`
- `vm_command_line`

### 7.2 Chrome
优先检查：
- 当前活动标签 URL
- bookmark bar 内容
- 下载结果文件
- 本地文件是否存在

适合使用：
- `is_expected_active_tab`
- `is_expected_bookmarks`
- `check_include_exclude`
- `vm_command_line`

### 7.3 OS
优先检查：
- 文件系统状态
- `gsettings`
- 桌面目录内容
- 应用生成文件

适合使用：
- `exact_match`
- `check_include_exclude`
- `vm_command_line`

---

## 8. 从非交互案例到交互案例的改造方法

### 8.1 改造模板

把原始单轮目标拆成：

- Phase 1：初始目标
- Phase 2：补充、修正或改变要求
- Phase 3：保存、确认或收尾

### 8.2 当前 3 个基线任务的直接改造方向

#### A. VS Code settings 基线
原任务：一次性修改多个设置。

可改造成：
- Phase 1：先开启 Auto Save + Delay
- Phase 2：再补充 trim trailing whitespace / final newline
- Phase 3：用户说“另外再把自动换行打开”

或：
- Phase 1：先按原要求配置
- Phase 2：用户改口，把 `700ms` 改成 `1000ms`

#### B. Chrome bookmark 基线
原任务：进入目标页并加入书签栏。

可改造成：
- Phase 1：先找到目标数据库页面
- Phase 2：用户要求加入书签栏
- Phase 3：用户追加“把书签名字改短一点”

或：
- Phase 1：先打开 Drugs.com 对应页面
- Phase 2：用户改要求为“不要直接留网页，保存到书签栏并固定标签页”

#### C. OS accessibility 基线
原任务：一次性打开多个无障碍设置。

可改造成：
- Phase 1：先让系统更易读
- Phase 2：用户补充“鼠标光标也调大”
- Phase 3：用户再补充“打开放大镜并调高倍率”

或：
- Phase 1：先调大文本
- Phase 2：用户纠正“不是只调文字，是整个阅读体验都要更明显”

---

## 9. 任务生产流程

建议按以下顺序执行：

### 第一步：建立任务清单
为 `vscode/chrome/os` 各列出：
- 任务母题
- 交互模式
- 可验证对象
- 风险点

### 第二步：先出 task design sheet
每个候选任务先写 1 份简版设计，不急着直接写 JSON。
设计表至少包含：
- 任务名
- snapshot
- scenario_type
- 用户 persona
- phases 草案
- trigger 草案
- evaluator 思路
- 风险与回退方案

### 第三步：再落 JSON
只有在 evaluator 明确、phase 合理后，再写正式任务 JSON。

### 第四步：单任务验证
重点检查：
- 会不会因为 trigger 设计不当导致提前推进 phase
- evaluator 是否只检查最终状态
- 配置是否会引入不稳定页面或随机内容
- 是否需要 proxy

### 第五步：批量注册
等一批任务稳定后，再统一加入索引文件。

---

## 10. 命名与目录规划

建议在 `interactive_xt` 下新增以下组织方式：

- `case/`：已有非交互基线
- `drafts/`：任务设计草案
- `vscode/`：正式 VS Code 交互任务
- `chrome/`：正式 Chrome 交互任务
- `os/`：正式 OS 交互任务
- `interactive_xt_all.json`：后续批量索引

正式任务 ID 建议：

- `interactive_vscode_<scenario>_<nnn>`
- `interactive_chrome_<scenario>_<nnn>`
- `interactive_os_<scenario>_<nnn>`

例如：
- `interactive_vscode_progressive_001`
- `interactive_chrome_requirement_change_001`
- `interactive_os_ambiguous_001`

---

## 11. 质量标准

每个交互任务都应满足：

1. **真实**：像真人会临时改口，而不是机械拆句
2. **可执行**：当前 snapshot 下能完成
3. **可验证**：最终状态能稳定检查
4. **多轮必要**：不是单轮任务硬拆成多轮
5. **对模型有区分度**：能检验澄清、记忆、修正、连续执行能力

---

## 12. 首批执行计划

### Phase A：盘点与分类
- 遍历 `case/` 下现有任务
- 标注所属系统、任务母题、可改造的交互类型
- 形成候选池

### Phase B：先做 9 个种子任务
每个系统先做 3 个：
- 1 个 `ambiguous_instruction`
- 1 个 `requirement_change` 或 `interruption`
- 1 个 `progressive_refinement` 或 `correction`

这样能先覆盖最核心交互能力。

### Phase C：扩展到 18 个首批任务
在种子任务稳定后，再补足到每系统 6 个。

### Phase D：回测与清洗
- 去掉 evaluator 不稳定任务
- 去掉外部网页波动过大的任务
- 去掉 phase 切换不自然任务

---

## 13. 后续实际落地时的工作方式

后续建议我按下面节奏继续推进：

1. 先把 `case/` 里的非交互任务全部梳理成表
2. 输出 `vscode/chrome/os` 的候选交互任务池
3. 先写每个系统 3 个 design sheet
4. 再正式生成第一批 JSON
5. 最后补索引与测试

---

## 14. 当前结论

现阶段最合理的做法不是立刻大批量写 JSON，而是：

- 先完成 **分类体系**
- 再完成 **候选任务池**
- 再完成 **小批量种子任务验证**
- 最后再规模化生成

这样可以最大限度减少后续返工，尤其是 `trigger` 和 `evaluator` 不稳定带来的重写成本。
