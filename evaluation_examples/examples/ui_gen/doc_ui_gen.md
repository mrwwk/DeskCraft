# UI Gen 任务设计文档

## 0. UI Gen 验证策略

### 核心定位

`ui_gen` 是一个面向 **HTML/CSS/JS/manifest 产物生成、修改与预览闭环** 的任务域。它不是纯视觉任务，也不是单纯的 VS Code 文本编辑任务，而是更接近真实前端工作流中的以下链路：

1. 在 VS Code 中创建或修改前端 bundle。
2. 在 Chrome 中查看参考页或预览本地页面。
3. 在 OS 层整理本地素材、数据文件与交付目录。
4. 最终交付 ZIP bundle、页面预览状态或多应用联动结果。

本文以下统计和分布，统一按 **当前已落地任务集** 编写：

- **静态任务**：**30 个**
- **动态任务**：**15 个**
- **总计**：**45 个**
- **静态任务文件命名**：`L{n}_(apps)_{ID}.json`
- **字段化逐项卡片**：见同目录 `doc_ui_gen_task_cards.md`，其中已补充静态能力短语索引与动态任务展开卡片

### 核心思路

UI Gen 的验证采用 **结构化源码检查 + 预览状态检查 + 多应用产物检查** 三层策略：

1. **ZIP bundle 检查**：任务结束后，将目标目录打包为 ZIP，通过 `vm_file` 下载并检查文件、文本、DOM、manifest、资源路径。
2. **Chrome 预览状态检查**：对于需要真实预览闭环的任务，读取活动标签 URL、打开标签集合、书签或本地页面状态，确认 Agent 确实完成“写代码 -> 打开预览 -> 回改/收尾”。
3. **OS / 文件状态检查**：对于三 app 联合任务，验证本地图片、JSON、SVG、打包目录或交付清单是否被正确整理和引用。

### 评估器架构

UI Gen 的核心评估器建议分为两层：

1. `desktop_env/evaluators/metrics/UI_Gen.py`
   - 负责 ZIP bundle、DOM、CSS、manifest、资源引用、本地预览 bundle 等验证。
2. `desktop_env/evaluators/metrics/chrome.py` 与 `desktop_env/evaluators/metrics/general.py`
   - 负责 Chrome 活动页、标签集合、书签、文件路径等状态验证。

这种拆分方式的好处是：

1. 前端源码正确性和浏览器状态正确性分别可解释。
2. 同一个任务可以自然地做 `VS Code -> Chrome` 或 `OS -> Chrome -> VS Code -> Chrome` 联合验证。
3. L2 / L3 可以在不依赖 OCR 的前提下，真正建立“生成 -> 预览 -> 收敛”闭环。

### 与 Chrome / OS 任务的区别

| 维度 | UI Gen | Chrome New | OS / Multi-app |
|---|---|---|---|
| 核心对象 | HTML/CSS/JS/manifest/asset bundle | 浏览器设置、标签页、书签、网站状态 | 文件、目录、命令输出、跨应用产物 |
| 主要验证入口 | ZIP + DOM + Chrome 预览状态 | CDP / accessTree / Chrome 数据文件 | 文件系统 / 命令 / VM 状态 |
| 典型闭环 | 写代码 -> 预览 -> 回改 | 导航 / 设置 / 持久化 | 整理资产 -> 导出 / 移动 / 打包 |
| 最大优势 | 结构稳定、可解释性强 | 浏览器状态读取成熟 | 工程交付链条完整 |
| 主要盲区 | 纯源码任务容易缺失真实预览 | 不直接评估 UI 代码质量 | 不直接评估前端生成能力 |

---

## 1. 任务集总览

### 1.1 当前已落地统计

- **任务总数**：**45 个**
- **静态任务**：**30 个**
- **动态任务**：**15 个**
- **静态难度分布**：**L1 = 10，L2 = 12，L3 = 8**
- **动态结构分布**：**interactive_vscode = 5，interactive_chrome = 5，interactive_multi_app = 5**
- **三 app 联合任务**：静态 **3** 个，动态 **5** 个

### 1.2 调整原则

本次分布调整遵循以下原则：

1. **静态任务扩到 30 个**：把 UI Gen 的主体重心放回可复用、可稳定评测的源码生成任务。
2. **动态任务收敛到 15 个**：不再让动态集合无限扩张，而是严格按 5 个 archetype x 3 个 family 组织。
3. **L2 成为主力层级**：L2 最适合承载“有 starter、有预览、有回改”的真实前端工作流，因此占比最高。
4. **L3 明显增强**：L3 不再只有 1 到 2 个过渡型任务，而是明确覆盖数据驱动、富交互、多文件协同与三 app 联合链路。
5. **引入三 app 联合任务**：让 UI Gen 不再局限于 VS Code 单应用，而是显式覆盖 `OS -> Chrome -> VS Code -> Chrome` 等真实路径。

### 1.3 类别说明

| 类别 | 描述 | 主要 app 路径 | 归属层级 |
|---|---|---|---|
| 基础从零生成 | 从空目录创建 landing page、card grid、FAQ、表单、数据列表 | VS Code | L1 |
| 受约束 starter 编辑 | 在已有 bundle 上做局部文案、结构、资源、manifest 修改 | VS Code | L1 / L2 |
| 预览闭环任务 | 写完后必须在 Chrome 打开本地页面并收尾 | VS Code -> Chrome | L2 / L3 |
| 参考驱动生成 | 先看 Chrome 参考页，再回 VS Code 实现 | Chrome -> VS Code -> Chrome | L2 / L3 |
| 三 app 联合任务 | 先整理 OS 资产，再看 Chrome 参考，最后在 VS Code 生成并回到 Chrome 预览 | OS -> Chrome -> VS Code -> Chrome | L3 |
| 多轮动态任务 | 用户在多轮对话中模糊、改口、打断、纠错或逐步补充要求 | VS Code / Chrome / Multi-app | Interactive |

### 1.4 动态任务的目标组织方式

动态任务收敛为 **15 个**，统一采用：

- **5 个 archetype**：`ambiguous_instruction`、`requirement_change`、`progressive_refinement`、`correction`、`interruption`
- **3 个 family**：`interactive_vscode_*`、`interactive_chrome_*`、`interactive_multi_app_*`

因此最终结构为：

| Family | 任务数 | 任务角色 |
|---|---:|---|
| `interactive_vscode_*` | 5 | 真正的多轮 UI bundle 生成 / 改稿 |
| `interactive_chrome_*` | 5 | 参考页浏览、标签整理、书签收敛、需求变更 |
| `interactive_multi_app_*` | 5 | OS 资产整理 + Chrome 参考 + VS Code 改稿的联合交互 |

这里不再单独保留 `interactive_os_*` 作为独立统计口径。原因很直接：**纯 OS 资产整理是辅助能力，不应在 UI Gen 动态集合里和真实 UI 生成任务同权重混算。**

---

## 2. 评估函数设计

文件：`desktop_env/evaluators/metrics/UI_Gen.py`

### 2.1 核心 ZIP / DOM 评估器

| 函数名 | 作用 | 典型层级 |
|---|---|---|
| `check_ui_bundle_required_files` | 验证 ZIP 中包含必需文件 | L1 / L2 / L3 |
| `check_ui_bundle_required_keywords` | 验证 HTML/CSS/JS/JSON 中的关键字 | L1 / L2 |
| `check_ui_bundle_html_checks` | 验证 DOM 结构、文本、属性、数量 | L1 / L2 / L3 |
| `check_ui_bundle_manifest_subset` | 验证 manifest 字段和值 | L1 / L2 / L3 |
| `check_ui_bundle_no_remote_image_urls` | 禁止保留远程图片 URL | L2 / L3 |
| `check_ui_bundle_min_file_sizes` | 验证本地资源是否完整 | L3 |
| `check_ui_bundle_required_patterns` | 验证 JS 逻辑模式或复杂正则 | L2 / L3 |
| `check_ui_bundle_section_order` | 验证多 section 页面结构顺序 | L2 / L3 |
| `check_ui_bundle_css_declarations` | 验证关键 CSS 选择器与声明 | L2 / L3 |
| `check_ui_bundle_local_asset_links` | 验证本地资产存在且被引用 | L2 / L3 |
| `check_ui_previewable_generative_bundle` | 一站式验证“bundle + 预览要求” | L3 |

### 2.2 Chrome / 多应用联动评估器

文件：`desktop_env/evaluators/metrics/chrome.py` 与 `desktop_env/evaluators/metrics/general.py`

| 函数名 | 作用 | 典型场景 |
|---|---|---|
| `is_expected_active_tab` | 验证当前预览页或参考页 URL | VS Code -> Chrome / Chrome 参考页 |
| `is_expected_tabs` | 验证打开标签集合 | 多参考页 / 多预览页收敛 |
| `is_expected_bookmarks` | 验证书签栏中保留的参考页 | interactive_chrome |
| `check_direct_json_object` | 验证解析出的结构化状态 | URL 参数、DOM、配置状态 |
| `exact_match` | 验证简单状态值 | 标志位、文件名、模式切换 |

### 2.3 推荐联合验证模式

#### 模式 A：VS Code 单应用静态任务

- `vm_file` + `check_ui_bundle_required_files`
- `vm_file` + `check_ui_bundle_html_checks`
- `vm_file` + `check_ui_bundle_manifest_subset`

#### 模式 B：VS Code -> Chrome 预览闭环任务

- `vm_file` + `check_ui_previewable_generative_bundle`
- `active_url_from_accessTree` + `is_expected_active_tab`

#### 模式 C：OS -> Chrome -> VS Code -> Chrome 三 app 任务

- `vm_file` + `check_ui_bundle_local_asset_links`
- `vm_file` + `check_ui_bundle_required_patterns`
- `open_tabs_info` 或 `active_url_from_accessTree`
- 必要时叠加文件 getter，验证资产目录或交付包

---

## 3. 任务定义

静态与动态任务的字段化卡片、英文能力短语索引、以及适合论文附录使用的任务摘要，统一维护在 `doc_ui_gen_task_cards.md`。

### 3.1 第一级（L1）—— 基础源码生成与轻量编辑 —— 10 个

L1 的目标不是堆太多超简单页面，而是覆盖 **最小可用前端 bundle** 的关键基本面。调整后建议为 **10 个**：

| 任务簇 | 数量 | 说明 |
|---|---:|---|
| 基础 landing / hero / card 页面 | 3 | HTML 骨架、按钮、卡片、基本 CSS |
| FAQ / tabs / disclosure 小交互 | 2 | 轻量 JS 行为 + DOM 结构 |
| 基础表单 / 校验页面 | 2 | 表单字段、错误提示、成功反馈 |
| JSON / list 渲染页面 | 2 | 本地数据读取与列表渲染 |
| smoke / sanity bundle | 1 | 仅作回归检查，不再代表正式能力上限 |

#### 任务簇 L1-A：基础 landing / hero / card 页面（3 个）

- **代表任务**：`mint_hero_page`、`team_members_grid`、`pricing_table_page`
- **主要考察**：HTML 语义结构、CTA、卡片布局、基础样式组织、manifest 最小字段
- **建议评估函数**：`check_ui_bundle_required_files` + `check_ui_bundle_required_keywords` + `check_ui_bundle_html_checks`
- **来源**：[Frontend Mentor Challenges](https://www.frontendmentor.io/challenges)

#### 任务簇 L1-B：FAQ / tabs / disclosure 小交互（2 个）

- **代表任务**：`faq_accordion_basic`、`simple_tabs_switcher`
- **主要考察**：折叠 / 展开、active state、简易事件绑定、可解释的 JS 模式
- **建议评估函数**：`check_ui_bundle_required_patterns` + `check_ui_bundle_html_checks`
- **来源**：[Frontend Mentor FAQ Accordion](https://www.frontendmentor.io/challenges/faq-accordion-wyfFdeBwBz)

#### 任务簇 L1-C：基础表单 / 校验页面（2 个）

- **代表任务**：`signup_form_basic`、`newsletter_inline_validation`
- **主要考察**：表单结构、错误提示、success message、字段级校验逻辑
- **建议评估函数**：`check_ui_bundle_required_keywords` + `check_ui_bundle_html_checks`
- **来源**：[MDN Client-side form validation](https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Forms/Form_validation)
- **来源**：[W3C WAI Validating Input](https://www.w3.org/WAI/tutorials/forms/validation/)

#### 任务簇 L1-D：JSON / list 渲染页面（2 个）

- **代表任务**：`product_feature_list`、`simple_release_notes_feed`
- **主要考察**：本地 JSON 读取、容器渲染、列表 / 卡片生成、空态处理
- **建议评估函数**：`check_ui_bundle_required_files` + `check_ui_bundle_required_patterns` + `check_ui_bundle_html_checks`
- **来源**：[MDN Using the Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch)

#### 任务簇 L1-E：Smoke / sanity bundle（1 个）

- **代表任务**：`generative_ui_quick_check`
- **主要考察**：最小 bundle 完整性、manifest、交付目录约定
- **建议定位**：只作为 sanity task，不再承担正式 L1 难度代表作用
- **来源**：authors

### L1 汇总

| 维度 | 数值 |
|---|---:|
| 任务数 | 10 |
| 单应用 VS Code | 10 |
| 需要 Chrome 预览闭环 | 0 |
| 来源以公开 challenge / MDN 为主 | 8 |
| smoke / sanity | 1 |

---

### 3.2 第二级（L2）—— 受约束编辑、参考驱动与预览闭环 —— 12 个

L2 是 UI Gen 的主力层级，建议扩到 **12 个**。重点不再是“写出代码就结束”，而是 **在约束下编辑、预览、回改、保持原结构**。

| 任务簇 | 数量 | 说明 |
|---|---:|---|
| starter 局部编辑 / 文案 / section 增删 | 3 | 保留原结构，只改指定区域 |
| 资源路径修复 / manifest / 本地化 | 2 | 工程修补与交付一致性 |
| 预览闭环改版任务 | 3 | VS Code 写完后必须在 Chrome 打开本地预览 |
| 可访问性强化任务 | 2 | 表单、dialog、焦点、错误反馈 |
| 参考驱动风格迁移 | 2 | 先看 Chrome 参考，再实现自己的版本 |

#### 任务簇 L2-A：starter 局部编辑 / 文案 / section 增删（3 个）

- **代表任务**：`edit_landing_copy`、`add_cta_section`、`feature_block_relayout`
- **主要考察**：保留原结构、定点修改、增量插入、样式补齐、避免粗暴重写
- **建议评估函数**：`check_ui_bundle_html_checks` + `check_ui_bundle_section_order` + `check_ui_bundle_css_declarations`
- **来源**：[Frontend Mentor Bookmark Landing Page](https://www.frontendmentor.io/challenges/bookmark-landing-page-5d0b588a9edda32581d29158)

#### 任务簇 L2-B：资源路径修复 / manifest / 本地化（2 个）

- **代表任务**：`fix_image_refs`、`theme_badge_manifest_sync`
- **主要考察**：本地资源链接、manifest 同步修改、禁止远程 URL、保持文案与资产一致
- **建议评估函数**：`check_ui_bundle_no_remote_image_urls` + `check_ui_bundle_local_asset_links` + `check_ui_bundle_manifest_subset`
- **来源**：authors

#### 任务簇 L2-C：预览闭环改版任务（3 个）

- **代表任务**：`brand_refresh_preview_loop`、`accessible_signup_preview_loop`、`marketing_cards_rebalance`
- **主要考察**：本地 server / 本地 HTML 预览、Chrome 打开本地页、收尾停留在正确预览页、必要时回改
- **建议评估函数**：`check_ui_previewable_generative_bundle` + `is_expected_active_tab`
- **来源**：[Frontend Mentor Social Proof Section](https://www.frontendmentor.io/challenges/social-proof-section-6e0qTv_bA)
- **来源**：[Frontend Mentor Contact Form](https://www.frontendmentor.io/challenges/contact-form--G-hYlqKJj)

#### 任务簇 L2-D：可访问性强化任务（2 个）

- **代表任务**：`dialog_focus_repair`、`form_error_accessibility_upgrade`
- **主要考察**：`dialog`、`aria-*`、错误提示、焦点顺序、键盘关闭 / 提交逻辑
- **建议评估函数**：`check_ui_bundle_required_patterns` + `check_ui_bundle_html_checks` + `check_ui_bundle_css_declarations`
- **来源**：[MDN HTML dialog element](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/dialog)
- **来源**：[W3C WAI Validating Input](https://www.w3.org/WAI/tutorials/forms/validation/)

#### 任务簇 L2-E：参考驱动风格迁移（2 个）

- **代表任务**：`reference_to_dashboard_shell`、`reference_to_story_cards`
- **主要考察**：先在 Chrome 查看参考页，再用自己的文案 / 数据 / 图标重做，不允许直接照搬
- **建议 app 路径**：`Chrome -> VS Code -> Chrome`
- **建议评估函数**：`check_ui_bundle_section_order` + `check_ui_bundle_css_declarations` + `is_expected_active_tab`
- **来源**：[Frontend Mentor Challenges](https://www.frontendmentor.io/challenges)

### L2 汇总

| 维度 | 数值 |
|---|---:|
| 任务数 | 12 |
| 纯 VS Code | 4 |
| VS Code -> Chrome | 6 |
| Chrome -> VS Code -> Chrome | 2 |
| 显式预览闭环 | 5 |

---

### 3.3 第三级（L3）—— 富交互生成与三 app 联合工作流 —— 8 个

L3 的目标是把 UI Gen 拉到真正接近 PDF 所描述的 **生成式富内容 UI benchmark**。建议为 **8 个**：

| 任务簇 | 数量 | 说明 |
|---|---:|---|
| JSON / state 驱动 dashboard | 2 | 多 section、筛选、图表、状态切换 |
| 富内容 story / launch lab | 1 | 时间线、dialog、insight grid、canvas |
| 多模块交互页面 | 2 | form + modal + tabs + chart 等多模块联动 |
| 三 app 联合任务 | 3 | OS 资产整理 + Chrome 参考 + VS Code 生成 + Chrome 预览 |

#### 任务簇 L3-A：JSON / state 驱动 dashboard（2 个）

- **代表任务**：`ops_signal_board`、`team_health_control_center`
- **主要考察**：本地 JSON、筛选器、KPI 卡片、timeline、canvas 或 SVG 图表、切换状态
- **建议评估函数**：`check_ui_bundle_required_patterns` + `check_ui_bundle_section_order` + `check_ui_bundle_local_asset_links`
- **来源**：[MDN Using the Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch)
- **来源**：[MDN Canvas tutorial](https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API/Tutorial)
- **来源**：[Frontend Mentor Time Tracking Dashboard](https://www.frontendmentor.io/challenges/time-tracking-dashboard-UIQ7167Jw)

#### 任务簇 L3-B：富内容 story / launch lab（1 个）

- **代表任务**：`launch_story_lab`
- **主要考察**：insight grid、milestone dialog、数据驱动内容组织、多 section 编排、canvas 视觉模块
- **建议评估函数**：`check_ui_previewable_generative_bundle`
- **来源**：[Frontend Mentor Bento Grid](https://www.frontendmentor.io/challenges/bento-grid-RMydElrlOj)
- **来源**：[MDN Canvas tutorial](https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API/Tutorial)

#### 任务簇 L3-C：多模块交互页面（2 个）

- **代表任务**：`checkout_guardrails_workspace`、`waitlist_modal_handoff`
- **主要考察**：多模块状态联动、表单 + modal + tabs + validation 的组合逻辑、section 顺序与交互脚本模式
- **建议评估函数**：`check_ui_bundle_required_patterns` + `check_ui_bundle_html_checks` + `check_ui_bundle_css_declarations`
- **来源**：[Frontend Mentor Multi-step Form](https://www.frontendmentor.io/challenges/multistep-form-YVAnSdqQBJ)
- **来源**：[MDN HTML dialog element](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/dialog)

#### 任务簇 L3-D：三 app 联合任务（3 个）

这 3 个任务是本轮分布调整中最重要的新增点。它们不再把 Chrome 只当成“打开一下本地页”，而是把 `OS / Chrome / VS Code` 真正串起来。

##### 任务 L3-D1：Campaign Asset Handoff Microsite

- **Slug**：`campaign_asset_handoff_microsite`
- **app 路径**：`OS -> Chrome -> VS Code -> Chrome`
- **指令概述**：先在 OS 中整理海报图、头像 SVG 和 copy brief；再在 Chrome 查看参考 landing page；最后在 VS Code 中生成 microsite，并在 Chrome 打开本地预览页收尾。
- **主要考察**：资产重命名、本地引用、section 组织、hero + proof + CTA 组合、预览闭环。
- **建议评估函数**：`check_ui_bundle_local_asset_links` + `check_ui_bundle_section_order` + `is_expected_active_tab`
- **来源**：[Frontend Mentor Social Proof Section](https://www.frontendmentor.io/challenges/social-proof-section-6e0qTv_bA)
- **来源**：[Frontend Mentor Bookmark Landing Page](https://www.frontendmentor.io/challenges/bookmark-landing-page-5d0b588a9edda32581d29158)

##### 任务 L3-D2：Reference-to-Ops Dashboard

- **Slug**：`reference_to_ops_dashboard`
- **app 路径**：`Chrome -> OS -> VS Code -> Chrome`
- **指令概述**：先在 Chrome 查看 dashboard 参考页与图表文档；再在 OS 中整理数据 JSON 和 badge SVG；最后在 VS Code 中生成 dashboard，并在 Chrome 验证本地预览页。
- **主要考察**：参考提炼、资产整理、JSON 驱动渲染、图表绘制、过滤栏和 active state。
- **建议评估函数**：`check_ui_previewable_generative_bundle` + `check_ui_bundle_required_patterns`
- **来源**：[Frontend Mentor Time Tracking Dashboard](https://www.frontendmentor.io/challenges/time-tracking-dashboard-UIQ7167Jw)
- **来源**：[MDN Using the Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch)
- **来源**：[MDN Canvas tutorial](https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API/Tutorial)

##### 任务 L3-D3：Launch Story Studio with Asset Triaging

- **Slug**：`launch_story_studio_asset_triage`
- **app 路径**：`OS -> Chrome -> VS Code -> Chrome`
- **指令概述**：先在 OS 中筛选可用图片和故事 JSON；在 Chrome 查看 story / bento / modal 参考；再在 VS Code 中组装 launch story 页面，最后在 Chrome 预览并停留在正确页面。
- **主要考察**：资产筛选、内容组织、dialog 交互、section 编排、视觉一致性与最终预览。
- **建议评估函数**：`check_ui_previewable_generative_bundle` + `check_ui_bundle_local_asset_links` + `is_expected_active_tab`
- **来源**：[Frontend Mentor Bento Grid](https://www.frontendmentor.io/challenges/bento-grid-RMydElrlOj)
- **来源**：[MDN HTML dialog element](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/dialog)
- **来源**：authors

### L3 汇总

| 维度 | 数值 |
|---|---:|
| 任务数 | 8 |
| 包含 Chrome 预览闭环 | 8 |
| 包含本地 JSON / 数据驱动 | 4 |
| 包含 canvas / 图表 / 富内容模块 | 5 |
| 三 app 联合任务 | 3 |

---

### 3.4 动态任务 —— 15 个

动态任务统一收敛为 **15 个**。设计上不再追求“动态任务越多越好”，而是追求 **每个 archetype 在每个 family 各有一个代表任务**。

#### 3.4.1 动态任务分布

| Family | `ambiguous_instruction` | `requirement_change` | `progressive_refinement` | `correction` | `interruption` | 小计 |
|---|---:|---:|---:|---:|---:|---:|
| `interactive_vscode_*` | 1 | 1 | 1 | 1 | 1 | 5 |
| `interactive_chrome_*` | 1 | 1 | 1 | 1 | 1 | 5 |
| `interactive_multi_app_*` | 1 | 1 | 1 | 1 | 1 | 5 |
| **总计** | **3** | **3** | **3** | **3** | **3** | **15** |

这里的 **15 个** 是论文主分析口径。仓库当前实际动态 JSON 文件仍是 **18 个**：`interactive_vscode_*` 5 个、`interactive_chrome_*` 8 个、`interactive_os_*` 5 个。建议在论文中将 `interactive_os_*` 视为 `interactive_multi_app_*` 的低阶代理，而将 `interactive_chrome_requirement_change_206`、`interactive_chrome_progressive_207`、`interactive_chrome_interruption_208` 作为扩展 Chrome 样本单列分析。对应的完整字段化展开已写入 `doc_ui_gen_task_cards.md`。

#### 3.4.2 `interactive_vscode_*`（5 个）

- **任务角色**：多轮 UI bundle 生成 / 改稿 / 增量修复。
- **核心价值**：验证 Agent 是否能在多轮对话后持续维护同一份前端 bundle，而不是每轮都推倒重写。
- **来源**：[Frontend Mentor Pricing Component with Toggle](https://www.frontendmentor.io/challenges/pricing-component-with-toggle-8vPwRMIC)
- **来源**：[Frontend Mentor Newsletter Signup](https://www.frontendmentor.io/challenges/newsletter-signup-form-with-success-message-3FC1AZbNrv)
- **来源**：[MDN Canvas tutorial](https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API/Tutorial)

#### 3.4.3 `interactive_chrome_*`（5 个）

- **任务角色**：参考页浏览、标签页保留、书签收敛、用户改口后清理旧目标。
- **核心价值**：把 Chrome 从“附属预览工具”提升为真实的参考整理工具。
- **要求**：尽量对 `open_tabs_info`、`bookmarks`、`active_url_from_accessTree` 做集合级约束，而不是只验证“新目标存在”。
- **来源**：[Frontend Mentor Challenges](https://www.frontendmentor.io/challenges)
- **来源**：[MDN HTML dialog element](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/dialog)

#### 3.4.4 `interactive_multi_app_*`（5 个）

- **任务角色**：OS 资产整理 + Chrome 参考 + VS Code 修改。
- **核心价值**：这是 UI Gen 动态集合里最接近真实前端协作链路的一类任务。
- **建议替代关系**：原 `interactive_os_*` 不再单独保留为 family，而是升级并吸收进 `interactive_multi_app_*`。
- **来源**：authors
- **来源**：[Frontend Mentor Challenges](https://www.frontendmentor.io/challenges)

### 动态任务汇总

| 维度 | 数值 |
|---|---:|
| 任务数 | 15 |
| `interactive_vscode_*` | 5 |
| `interactive_chrome_*` | 5 |
| `interactive_multi_app_*` | 5 |
| 三 app 联合动态任务 | 5 |

---

## 4. 任务来源汇总

### 4.1 公开来源主表

| 来源类别 | 对应任务簇 | 说明 |
|---|---|---|
| [Frontend Mentor Challenges](https://www.frontendmentor.io/challenges) | landing、card、FAQ、pricing、story、dashboard、reference-driven 任务 | 作为结构、布局和 challenge 风格的主要公开来源 |
| [Frontend Mentor FAQ Accordion](https://www.frontendmentor.io/challenges/faq-accordion-wyfFdeBwBz) | FAQ / disclosure 类任务 | 适合映射折叠、问答与小交互 |
| [Frontend Mentor Bookmark Landing Page](https://www.frontendmentor.io/challenges/bookmark-landing-page-5d0b588a9edda32581d29158) | starter 编辑、marketing 改版、参考页收敛 | 适合映射 landing page 改稿与参考保留 |
| [Frontend Mentor Social Proof Section](https://www.frontendmentor.io/challenges/social-proof-section-6e0qTv_bA) | marketing card / proof / CTA 组合页面 | 适合映射 brand refresh 与信息组织 |
| [Frontend Mentor Contact Form](https://www.frontendmentor.io/challenges/contact-form--G-hYlqKJj) | 表单与可访问性强化任务 | 适合映射错误提示、提交反馈和布局要求 |
| [Frontend Mentor Pricing Component with Toggle](https://www.frontendmentor.io/challenges/pricing-component-with-toggle-8vPwRMIC) | pricing / toggle / dynamic copy 任务 | 适合映射 starter 编辑和 dynamic 改稿 |
| [Frontend Mentor Time Tracking Dashboard](https://www.frontendmentor.io/challenges/time-tracking-dashboard-UIQ7167Jw) | dashboard / KPI / state-driven 任务 | 适合映射卡片、时间维度与数据切换 |
| [Frontend Mentor Bento Grid](https://www.frontendmentor.io/challenges/bento-grid-RMydElrlOj) | story / launch / insight 页面 | 适合映射富内容 section 编排 |
| [Frontend Mentor Multi-step Form](https://www.frontendmentor.io/challenges/multistep-form-YVAnSdqQBJ) | 多模块交互 / validation / step state | 适合映射复杂表单与流程任务 |
| [MDN Using the Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch) | JSON / fetch / 数据驱动任务 | 适合映射客户端读取本地数据 |
| [MDN Canvas tutorial](https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API/Tutorial) | 图表、canvas、视觉模块任务 | 适合映射富内容图形生成 |
| [MDN Client-side form validation](https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Forms/Form_validation) | 表单校验与错误反馈 | 适合映射表单基本语义与浏览器校验 |
| [MDN HTML dialog element](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/dialog) | modal / dialog / overlay 任务 | 适合映射 `dialog` 语义与交互 |
| [W3C WAI Validating Input](https://www.w3.org/WAI/tutorials/forms/validation/) | 可访问性强化任务 | 适合映射错误提示与可访问性要求 |
| [Chrome Extension Hello World](https://developer.chrome.com/docs/extensions/get-started/tutorial/hello-world) | 仅在参考页 / dynamic chrome 中作为扩展类参考 | 不作为 UI Gen 静态主体来源 |

### 4.2 专业构造场景的使用边界

以下类型更适合标为 `authors` 或“专业构造场景”，而不是硬找一条一一对应的公开模板：

1. 资产重命名、本地化、交付包整理。
2. 页面文案与 manifest 同步修改。
3. 基于多个公开参考混合生成一个新页面。
4. 三 app 联合任务中的 OS 资产筛选和 handoff 流程。

### 4.3 文档内来源引用规范

本文件统一采用和 Chrome 文档一致的引用方式：

- `- **来源**：[站点 / 文档名称](URL)`
- 如有多个来源，则连续列出多条 `- **来源**：...`
- 如果是专业构造场景，则直接写 `- **来源**：authors`

---

## 5. 难度与能力覆盖总结

### 5.1 静态难度分布是否合理

结论：**`10 / 12 / 8` 比当前 UI Gen 的库存分布更合理。**

原因如下：

1. **L1 不能过多**：UI Gen 的基础页面生成很容易变成关键词 smoke test，所以 L1 控制在 10 个比较稳妥。
2. **L2 应该最多**：真实前端工作更常见的是“在 starter 上编辑、看参考、做预览闭环”，这正是 L2 最适合承载的能力。
3. **L3 必须显著增强**：L3 至少要覆盖富内容页面、数据驱动页面和三 app 联合工作流，8 个是比较健康的规模。

### 5.2 能力覆盖表

| 能力维度 | L1 | L2 | L3 | 总体结论 |
|---|---|---|---|---|
| HTML 语义结构生成 | 强 | 强 | 强 | 基础能力稳定覆盖 |
| CSS 布局与 section 编排 | 中 | 强 | 强 | L2 开始真正有结构约束 |
| 简单 JS 事件逻辑 | 中 | 中 | 强 | L3 才真正进入模块联动 |
| JSON / fetch 数据驱动 | 中 | 中 | 强 | 需要靠 dashboard 类任务拉高 |
| manifest / 工程配置 | 中 | 中 | 中 | 作为 bundle 交付细节存在 |
| 本地资源与交付目录 | 弱 | 强 | 强 | 受约束编辑和三 app 任务会显著提升这项覆盖 |
| Chrome 预览闭环 | 无 | 强 | 强 | 本轮调整后成为核心能力 |
| 参考驱动生成 | 无 | 中 | 强 | Chrome 参考页任务是关键补齐点 |
| 多轮修正 / 收敛 | 无 | 中 | 强 | 主要由 dynamic 15 承担 |
| 三 app 联合工作流 | 无 | 弱 | 强 | 本轮新增的关键能力 |

### 5.3 为什么要把动态从 18 缩到 15

原因不是削弱动态，而是**去冗余**：

1. 18 个动态里，纯 Chrome 或纯 OS 的边缘任务容易重复“保留页面 / 整理文件”模式。
2. 15 个正好可以做成 `5 archetype x 3 family` 的整齐矩阵，覆盖更清晰。
3. `interactive_multi_app_*` 能比旧 `interactive_os_*` 更贴近 UI Gen 主目标，因此更值得保留。

---

## 6. Base 环境要求

### 6.1 最低必备能力

UI Gen 的 base 环境至少要稳定支持：

1. VS Code 编辑 HTML / CSS / JS / JSON / manifest。
2. Chrome 打开本地预览页和参考页。
3. OS 层读写本地素材、ZIP、SVG、PNG、JSON。
4. Python 评估器读取 ZIP、DOM、文件与浏览器状态。

### 6.2 系统级软件

**必装**：

- `code` 或 `code-insiders`
- `google-chrome-stable` 或 `chromium`
- `python3`
- `python3-pip`
- `git`
- `zip`
- `unzip`
- `curl`
- `wget`
- `socat`
- `xdg-utils`
- `jq`
- `file`

**强烈建议安装**：

- `nodejs`
- `npm`
- `dbus-x11`
- `xvfb`

### 6.3 Chrome / Chromium 常见运行依赖

- GTK: `gtk3`
- NSS/NSPR: `nss`, `nspr`
- 音频: `alsa-lib`
- 图形: `libdrm`, `mesa-libgbm`, `libxkbcommon`
- X11: `libX11`, `libXcomposite`, `libXdamage`, `libXext`, `libXfixes`, `libXi`, `libXrandr`, `libXrender`, `libXScrnSaver`, `libXtst`, `libxshmfence`
- 字体与排版: `pango`, `cairo`, `liberation-fonts`
- 辅助功能桥: `atk`, `at-spi2-atk`
- 打印 / 系统库: `cups-libs`, `dbus-libs`

### 6.4 Python 侧依赖

| 库 | 用途 |
|---|---|
| `beautifulsoup4` | 解析 HTML / DOM |
| `lxml` | 加速 DOM 解析 |
| `PyPDF2` | 其他文档 / ZIP 相关评估复用 |

### 6.5 推荐安装的 VS Code 扩展

- `ritwickdey.LiveServer`
- `esbenp.prettier-vscode`
- `dbaeumer.vscode-eslint`
- `bradlc.vscode-tailwindcss`

---

## 7. 落地建议

### 7.1 静态任务落地顺序

建议按下面顺序补齐到 30 个：

1. 先补 L2 的预览闭环任务和参考驱动任务。
2. 再补 L3 的 dashboard / story / multi-module 任务。
3. 最后补 3 个三 app 联合静态任务。

### 7.2 动态任务收敛顺序

建议把动态集合整理成：

1. `interactive_vscode_*` 保留 5 个 archetype。
2. `interactive_chrome_*` 收敛到 5 个 archetype。
3. 原 `interactive_os_*` 吸收并升级为 `interactive_multi_app_*` 5 个 archetype。

### 7.3 数据与资源侧建议

1. 将所有 starter、JSON、SVG、PNG 统一沉淀到 `assets/ui_gen/`。
2. 尽量把仍依赖远程下载的任务改成 `upload_file`。
3. 三 app 联合任务所需素材也应优先本地化，避免外网波动。

### 7.4 文档维护建议

1. 后续 `doc_ui_gen.md` 继续沿用本文件的格式：统计先行、分层清晰、来源统一用 `- **来源**：...`。
2. 如果任务文件真正扩容到 30 静态 / 15 动态，再把本文件中的“目标集”表述切到“当前集”。
3. 在真正落地新任务前，不要再把“当前库存”和“建议分布”混写在同一节里。
