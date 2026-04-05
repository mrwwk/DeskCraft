# Chrome New 任务设计文档

## 0. Chrome 验证策略

### Chrome 启动方式

评测虚拟机中 Chrome 通过 `google-chrome --remote-debugging-port=1337` 启动，并通过 `socat tcp-listen:9222,fork tcp:localhost:1337` 转发调试端口。所有 Chrome task JSON 的 `config` 都必须包含这两条 `launch` 指令，评测框架通过 CDP（Chrome DevTools Protocol）连接浏览器并读取状态。

### 核心思路

Chrome 的验证依赖四类互补机制：

1. **浏览器设置状态检查**：读取 Preferences / Local State，验证 Do Not Track、安全浏览、默认搜索引擎、字体大小、启动页、Profile 名称等持久化设置。
2. **标签页与页面状态检查**：通过 CDP 或 accessTree 读取当前活跃标签 URL、标题、HTML 内容和 URL 参数，验证是否到达目标页面并保持正确结果页状态。
3. **浏览器数据状态检查**：直接读取 Bookmarks、Cookies、History 等本地数据文件或数据库，验证书签、Cookie、历史记录、扩展等状态变化。
4. **文件系统与导出产物检查**：通过 `vm_file`、桌面快捷方式扫描等方式验证 PDF、快捷方式、扩展路径等文件系统产物。

### 评估器架构

Chrome 评估采用 **getter + metric** 两层架构：

- getter 定义在 `desktop_env/evaluators/getters/chrome.py`，负责从 VM 提取 URL、HTML、设置、数据库或文件。
- metric 定义在 `desktop_env/evaluators/metrics/chrome.py` 与 `desktop_env/evaluators/metrics/general.py`，负责对提取结果和期望规则做本地比对。

这一架构保证了评测逻辑尽量不依赖 VM 内额外脚本，便于复用和调试。

### 评估器通用模式

```python
def metric_function(result, rule) -> float:
  """
  参数：
    result: getter 从 VM 提取的实际数据（URL / JSON / 设置值 / 文件路径等）
    rule: 包含期望值的字典
  返回：
    1.0（通过）或 0.0（失败）
  """
```

### 多指标联合评估

Chrome 任务大量采用多指标联合评估。典型模式是“网站操作验证 + 设置或持久化状态验证”，即 `evaluator.func` 为列表，`conj: "and"` 表示所有指标都必须通过。

### 与 Audacity / OS 验证方式的对比

| 验证类型 | Chrome | Audacity | OS / Multi-app |
|----------|--------|----------|----------------|
| 主要验证入口 | CDP getter + 本地分析 | `vm_file` 下载后本地分析 | `vm_command_line` 或文件状态 |
| 页面 / 应用状态读取 | CDP / accessTree / Playwright | N/A | shell / GUI 状态混合 |
| 数据库验证 | History / Cookies / Bookmarks / Local State | `.aup3` SQLite | 少量使用 |
| 文件验证 | PDF、快捷方式、扩展路径 | WAV / `.aup3` | 文件或命令输出 |
| 额外依赖 | `rapidfuzz`, `bs4`, `fitz`, `imagehash`, `borb`, `playwright` | 以标准库为主 | 依场景而定 |

---

## 1. 任务集总览

### 1.1 基本统计

- **任务总数**：**46 个**
- **难度分布**：**L1 = 15，L2 = 21，L3 = 10**
- **快照**：全部为 **`chrome`**
- **相关应用**：全部为 **`chrome`**
- **网络代理需求**（`proxy: true`）：**25 个**（L1: 8，L2: 10，L3: 7）
- **环境变化风险**：`low = 39`，`medium = 5`，`high = 2`

### 1.2 任务类别说明

| 类别 | 描述 | 代表任务 |
|------|------|---------|
| **Chrome 设置类** | 在 Chrome 内置设置页修改隐私、安全、外观和启动行为 | Do Not Track、Safe Browsing、字体大小、搜索引擎、启动页 |
| **书签管理类** | 创建书签文件夹、添加网页到书签栏、组合书签与标签操作 | 创建书签文件夹、收藏指定网页 |
| **标签页管理类** | 恢复关闭标签、验证多个标签页同时存在 | 恢复误关标签、启动页多标签 |
| **在线导航与筛选类** | 在公共信息、旅行、开发者文档或消费网站完成多步导航、搜索、筛选和结果页保持 | PubMed、arXiv、Delta、Recreation.gov |
| **隐私数据管理类** | 删除站点 Cookie、删除部分历史记录、验证浏览数据变化 | 删除 Amazon/eBay/Walmart Cookie、清除 YouTube 历史 |
| **高级浏览器功能类** | 扩展安装、桌面快捷方式创建、PDF 导出、跨重启持久化配置 | 加载 unpacked 扩展、导出 PDF、配置启动页 |

### 1.3 Getter / result 类型概览

#### 1.3.1 设置类 Getter（读取 Preferences / Local State）

| Getter 类型 | 对应函数 | 描述 | 验证方式 |
|-------------|----------|------|----------|
| `enable_do_not_track` | `get_enable_do_not_track` | Do Not Track 开关 | 读 Preferences → `enable_do_not_track` |
| `enable_safe_browsing` | `get_enable_safe_browsing` | 安全浏览开关 | 读 Preferences → `safebrowsing.enabled` |
| `enable_enhanced_safety_browsing` | `get_enable_enhanced_safety_browsing` | 增强保护开关 | 读 Preferences → `safebrowsing.enhanced` |
| `data_delete_automacally` | `get_data_delete_automacally` | 关闭时自动清除 Cookie | 读 Preferences 中 cookie 相关字段 |
| `default_search_engine` | `get_default_search_engine` | 默认搜索引擎 | 读 Preferences 中 search provider 字段 |
| `chrome_font_size` | `get_chrome_font_size` | 默认字体大小 | 读 `webkit.webprefs.default_font_size` |
| `profile_name` | `get_profile_name` | Profile 名称 | 读 Preferences / Local State |
| `new_startup_page` | `get_new_startup_page` | 启动页 URL 列表 | 读 Preferences → `session.startup_urls` |
| `enabled_experiments` | `get_enabled_experiments` | Chrome flags 实验项 | 读 Local State → `browser.enabled_labs_experiments` |

#### 1.3.2 导航 / 内容类 Getter（通过 CDP / accessTree / Playwright）

| Getter 类型 | 对应函数 | 描述 | 验证方式 |
|------------|----------|------|----------|
| `active_tab_info` | `get_active_tab_info` | 当前标签的 URL 和标题 | CDP 直接读取活动页信息 |
| `active_url_from_accessTree` | `get_active_url_from_accessTree` | 从无障碍树解析活动标签 URL | 作为 CDP 的备选 URL 读取方式 |
| `active_tab_url_parse` | `get_active_tab_url_parse` | 解析活动标签 URL 的 query 参数 | 将查询参数拆成 JSON 对象 |
| `active_tab_html_parse` | `get_active_tab_html_parse` | 解析活动标签 HTML 内容 | 按 class / xpath / input 等规则提取字段 |
| `url_path_parse` | `get_url_path_parse` | 解析 URL path | 用于路径片段校验 |
| `url_dashPart` | `get_url_dashPart` | 提取以 dash 分隔的 URL 段 | 用于城市 / 页面标识校验 |
| `page_info` | `get_page_info` | 获取指定 URL 的页面内容 | 适合购物车或静态内容校验 |
| `open_tabs_info` | `get_open_tabs_info` | 获取全部打开标签页 | 用于多启动页 / 恢复标签场景 |

#### 1.3.3 数据状态类 Getter（读 Chrome 数据库 / 文件系统）

| Getter 类型 | 对应函数 | 描述 | 验证方式 |
|-------------|----------|------|----------|
| `bookmarks` | `get_bookmarks` | 书签数据 | 读 `Default/Bookmarks` JSON |
| `cookie_data` | `get_cookie_data` | Cookie 数据 | 读 `Default/Cookies` SQLite 数据库 |
| `history` | `get_history` | 浏览历史数据 | 读 `Default/History` SQLite 数据库 |
| `shortcuts_on_desktop` | `get_shortcuts_on_desktop` | 桌面快捷方式 | 扫描桌面 `.desktop` 文件 |
| `find_unpacked_extension_path` | `get_find_unpacked_extension_path` | 已安装 unpacked 扩展路径 | 读扩展相关配置 |
| `vm_file` | 通用 getter | 从 VM 下载文件到本地 | PDF、导出文件等离线验证 |

---

## 2. 评估函数设计

文件：`desktop_env/evaluators/metrics/chrome.py`

### 2.1 标签页与 URL 验证

| 函数名 | 描述 | result 类型 | expected 规则参数 |
|--------|------|-------------|-------------------|
| `is_expected_active_tab` | 精确匹配当前活跃标签页 URL | `active_tab_info` / `active_url_from_accessTree` | `{"type": "url", "url": "https://..."}` |
| `is_expected_active_tab_approximate` | 近似匹配活跃标签页 URL（忽略 query） | `active_url_from_accessTree` | `{"type": "url", "url": "https://..."}` |
| `is_expected_url_pattern_match` | 使用正则匹配活跃标签页 URL | `active_tab_info` / `active_url_from_accessTree` | `{"expected": ["regex1", "regex2"]}` |
| `is_expected_tabs` | 验证所有打开标签页的 URL 列表（顺序敏感） | `open_tabs_info` | `{"type": "url", "urls": [...]}` |
| `check_direct_json_object` | 对解析出的 JSON 对象做字段级校验 | `active_tab_url_parse` / `active_tab_html_parse` / `url_path_parse` / `url_dashPart` | `{"expected": {...}, "expect_in_result": bool}` |

### 2.2 书签与扩展验证

| 函数名 | 描述 | result 类型 | expected 规则参数 |
|--------|------|-------------|-------------------|
| `is_expected_bookmarks` | 验证书签栏文件夹或 URL 集合 | `bookmarks` | `{"type": "bookmark_bar_folders_names" / "bookmark_bar_websites_urls" / "liked_authors_websites_urls", ...}` |
| `is_expected_installed_extensions` | 验证已安装扩展集合（子集匹配） | `installed_extensions` | `{"expected": ["extension_id1", ...]}` |
| `is_in_list` | 验证某个值存在于列表中 | `find_unpacked_extension_path` | `{"expected": "/path/to/extension"}` |

### 2.3 Chrome 设置验证

| 函数名 | 描述 | result 类型 | expected 规则参数 |
|--------|------|-------------|-------------------|
| `exact_match` | 精确匹配持久化设置值 | `enable_do_not_track` / `enable_safe_browsing` / `enable_enhanced_safety_browsing` / `profile_name` 等 | `{"expected": "true" / "false" / "WorkProfile"}` |
| `match_in_list` | 验证设置值在允许集合内 | `default_search_engine` | `{"expected": ["DuckDuckGo", ...]}` |
| `check_font_size` | 验证默认字体大小 | `chrome_font_size` | `{"type": "value", "value": 20}` 或 `{"type": "range", "min": 16, "max": 24}` |
| `check_enabled_experiments` | 验证 `chrome://flags` 中的实验项 | `enabled_experiments` | `{"type": "names", "names": [...]}` |

### 2.4 隐私数据验证

| 函数名 | 描述 | result 类型 | expected 规则参数 |
|--------|------|-------------|-------------------|
| `is_cookie_deleted` | 验证指定域名 Cookie 已删除 | `cookie_data` | `{"type": "domains", "domains": [".amazon.com", ...]}` |
| `check_history_deleted` | 验证历史记录中不含指定关键词 | `history` | `{"type": "keywords", "keywords": [...]}` |
| `check_history_keywords_absent_and_present` | 验证部分历史已删且部分历史保留 | `history` | `{"type": "keywords_absent_present", "absent_keywords": [...], "present_keywords": [...]}` |
| `is_expected_search_query` | 验证搜索查询参数模式 | `active_tab_info` | `{"expect": {"pattern": "regex"}}` |

### 2.5 文件与桌面验证

| 函数名 | 描述 | result 类型 | expected 规则参数 |
|--------|------|-------------|-------------------|
| `compare_pdfs` | 提取 PDF 文本并比较相似度 | `vm_file`（PDF） | `pdf_from_url` |
| `compare_pdf_images` | 比较 PDF 内嵌图片 | `vm_file`（PDF） | `pdf_from_url` |
| `is_shortcut_on_desktop` | 验证桌面快捷方式存在 | `shortcuts_on_desktop` | `{"expected": "name"}` |

### 2.6 通用评估函数（来自 `general.py`）

| 函数名 | 描述 |
|--------|------|
| `exact_match` | 精确值匹配 |
| `check_direct_json_object` | JSON 对象字段逐项对比 |
| `match_in_list` | 值在列表中匹配 |
| `is_in_list` | 值包含在列表中 |


## 3. 任务定义

### 3.1 第一级（L1）—— 多元化基础操作 —— 15 个

**V2 改版说明**：原 V1 版本 15 个 L1 任务中有 11 个涉及 Do Not Track，隐私设置三件套高度重复。V2 版仅保留 **1 个** DNT 任务作为代表，其余替换为 Cookie 管理、历史记录、语言设置、自动填充、桌面快捷方式、搜索引擎/字体、用户配置文件、内部页面导航等 **13 个能力维度**。

**共计 15 个任务**
L1 任务为基础操作，覆盖 Chrome 浏览器的多元化功能场景。评估使用 Chrome CDP getter、Preferences 文件读取、SQLite 数据库检查等多种验证方式。

---



#### 任务 L1-1：删除指定网站 Cookie（🍪 隐私数据管理）
- **ID**：`9816acec-d6e8-4287-903d-d12348cc81d0`
- **Slug**：`delete_specific_site_cookies`
- **能力分类**：`Selective Cookie Cleanup`
- **指令**：I've been browsing Amazon and eBay and I want to clear my tracks. Please delete all cookies for amazon.com and ebay.com, but keep cookies for other websites untouched.
- **初始状态**：预先打开 amazon.com、ebay.com、wikipedia.org 三个标签页
- **评估函数**：`is_cookie_deleted`
- **result 类型**：`cookie_data`
- **验证逻辑**：`.amazon.com` 和 `.ebay.com` 域名下 Cookie 全部删除
- **操作步骤数**：2
- **postconfig**：需要重启 Chrome
- **来源**：[Google Chrome 帮助](https://support.google.com/chrome/answer/95647)
- **🆕 替换**：原 `030eeff7`（DNT+增强保护+自动清除三件套）

---

#### 任务 L1-2：恢复误关标签页（🏷️ 标签页管理）⭐ 保留
- **ID**：`06fe7178-4491-4589-810f-2e2bc9502122`
- **Slug**：`restore_closed_tab`
- **能力分类**：`Closed Tab Recovery`
- **指令**：I accidentally closed the last tab. Please restore it so all my travel tabs are back exactly as before.
- **初始状态**：预先打开 5 个旅行网站标签，关闭 kayak 标签
- **评估函数**：`is_expected_tabs`
- **result 类型**：`open_tabs_info`
- **验证逻辑**：5 个标签页 URL 完全匹配（顺序敏感）
- **操作步骤数**：1
- **来源**：[Google Chrome 帮助](https://support.google.com/chrome/answer/157179)

---

#### 任务 L1-3：收藏药品数据库页面（📁 书签管理）⭐ 保留
- **ID**：`0d8b7de3-e8de-4d86-b9fd-dd2dce58a217`
- **Slug**：`bookmark_drug_database`
- **能力分类**：`Reference Page Bookmarking`
- **指令**：Navigate to the Drugs.com natural products database and save that page to your bookmarks bar for quick access.
- **评估函数**：`["is_expected_active_tab", "is_expected_bookmarks"]`，`"conj": "and"`
- **result 类型**：`active_url_from_accessTree` + `bookmarks`
- **验证逻辑**：当前页 URL 匹配 + 书签栏包含对应 URL
- **操作步骤数**：2
- **来源**：[Drugs.com Natural Product Information](https://www.drugs.com/npp/)

---

#### 任务 L1-4：删除 YouTube 浏览历史（📜 历史记录管理）
- **ID**：`997bf712-2953-459c-aec7-cbe1d747fe02`
- **Slug**：`clear_youtube_history_keep_others`
- **能力分类**：`Selective History Cleanup`
- **指令**：Delete all YouTube-related entries from my Chrome browsing history, but make sure history for other websites like nytimes, bbc, and cnn is preserved.
- **初始状态**：预置 7 条历史记录（3 条 YouTube、4 条新闻/其他网站）
- **评估函数**：`check_history_keywords_absent_and_present`
- **result 类型**：`history`
- **验证逻辑**：YouTube 相关 URL 全部消失，nytimes/bbc/cnn 仍然存在
- **操作步骤数**：2
- **postconfig**：需要重启 Chrome
- **来源**：[Google Chrome 帮助](https://support.google.com/chrome/answer/95589)
- **🆕 替换**：原 `12086550`（打开密码管理页+DNT）

---

#### 任务 L1-5：切换 Chrome 界面语言（🌐 语言/国际化）
- **ID**：`7918533b-33a3-4b6c-9ac2-f32b6d3f4034`
- **Slug**：`change_chrome_language_to_french`
- **能力分类**：`Browser Language Switching`
- **指令**：Change Chrome's display language to French (Français). After changing the language, leave Chrome on the Languages settings page.
- **评估函数**：`exact_match`
- **result 类型**：`chrome_language`
- **验证逻辑**：Chrome 语言设置变为 `fr`
- **操作步骤数**：2
- **postconfig**：需要重启 Chrome
- **来源**：[Google Chrome 帮助](https://support.google.com/chrome/answer/173424)
- **🆕 替换**：原 `2ad9387a`（创建书签文件夹+DNT）

---

#### 任务 L1-6：设置多启动页（🏠 启动页配置）
- **ID**：`a3c1882d-b0cc-4b0f-913f-a4e4634ab019`
- **Slug**：`set_startup_multiple_pages`
- **能力分类**：`Multi-Page Startup Setup`
- **指令**：Configure Chrome to open both https://www.wikipedia.org/ and https://github.com/ as startup pages, so both sites open automatically each time Chrome launches.
- **评估函数**：`is_expected_tabs`
- **result 类型**：`open_tabs_info`
- **验证逻辑**：重启后两个标签页同时打开
- **操作步骤数**：2
- **postconfig**：需要重启 Chrome（验证启动页生效）
- **来源**：[Google Chrome 帮助](https://support.google.com/chrome/answer/95314)
- **🆕 替换**：原 `2ae9ba84`（重命名Profile+DNT+SafeBrowsing）

---

#### 任务 L1-7：添加自动填充地址（📋 自动填充管理）
- **ID**：`c0a02003-5f17-4868-8e66-4110d981c923`
- **Slug**：`save_autofill_address`
- **能力分类**：`Autofill Address Entry`
- **指令**：Add a new address to Chrome's autofill settings with the following information: Name 'John Doe', Address '123 Main Street', City 'San Francisco', State 'CA', ZIP '94102'. Leave Chrome on the Addresses settings page when done.
- **评估函数**：`["check_direct_json_object", "is_expected_active_tab_approximate"]`，`"conj": "and"`
- **result 类型**：`chrome_saved_address` + `active_url_from_accessTree`
- **验证逻辑**：地址页面 HTML 中包含所有填写信息 + 停留在地址设置页
- **操作步骤数**：3
- **来源**：[Google Chrome 帮助](https://support.google.com/chrome/answer/142893)
- **🆕 替换**：原 `3299584d`（设置启动页Wikipedia+SafeBrowsing）

---

#### 任务 L1-8：创建网站桌面快捷方式（🖥️ 桌面快捷方式）
- **ID**：`aa4c78e7-70d4-4644-bc37-469b99b7201e`
- **Slug**：`create_website_desktop_shortcut`
- **能力分类**：`Web Shortcut Creation`
- **指令**：Create a desktop shortcut for the currently open Wikipedia page using Chrome's built-in 'Create shortcut' feature. Name it 'Wikipedia Quick Access' and keep the page open when done.
- **初始状态**：预先打开 Wikipedia 页面
- **评估函数**：`["is_shortcut_on_desktop", "is_expected_active_tab"]`，`"conj": "and"`
- **result 类型**：`shortcuts_on_desktop` + `active_tab_info`
- **验证逻辑**：桌面存在名为 `Wikipedia Quick Access` 的快捷方式 + 活动标签正确
- **操作步骤数**：2
- **来源**：[Google Chrome 帮助](https://support.google.com/chrome/answer/15085120)
- **🆕 替换**：原 `3720f614`（设置启动页NASA+DNT）

---

#### 任务 L1-9：禁用 Chrome 2023 UI 实验旗标（🚩 Chrome Flags）⭐ 保留（去除 DNT）
- **ID**：`480bcfea-d68f-4aaa-a0a9-2589ef319381`
- **Slug**：`disable_refresh_ui_flags`
- **能力分类**：`Experimental Flag Control`
- **指令**：Disable Chrome's 2023 refresh UI flags (both 'Chrome Refresh 2023' and 'Chrome WebUI Refresh 2023') and confirm the changes are applied.
- **评估函数**：`check_enabled_experiments`
- **result 类型**：`enabled_experiments`
- **验证逻辑**：指定 flags 已禁用
- **操作步骤数**：2
- **postconfig**：需要重启 Chrome
- **来源**：[Chrome Developers](https://developer.chrome.com/docs/web-platform/chrome-flags)
- **⚠️ 修改说明**：移除了原任务中的 DNT 副任务，聚焦 flags 操作

---

#### 任务 L1-10：添加书签并切换标签（📁 书签+标签管理）⭐ 保留
- **ID**：`7a5a7856-f1b6-42a4-ade9-1ca81ca0f263`
- **Slug**：`bookmark_transformer_switch_tab`
- **能力分类**：`Bookmark-and-Tab Coordination`
- **指令**：Bookmark the Illustrated Transformer page to the bookmarks bar, then switch back so the Rotary Embeddings page is the active tab.
- **初始状态**：预先打开两个标签页
- **评估函数**：`["is_expected_bookmarks", "is_expected_active_tab"]`，`"conj": "and"`
- **result 类型**：`bookmarks` + `active_tab_info`
- **验证逻辑**：书签包含目标 URL + 活动标签正确
- **操作步骤数**：2
- **来源**：[Google Chrome 帮助](https://support.google.com/chrome/answer/188842)

---

#### 任务 L1-11：搜索引擎 DuckDuckGo + 大字体（⚙️ 外观设置组合）
- **ID**：`13a7270a-cd15-468e-8229-61897613a875`
- **Slug**：`duckduckgo_engine_large_font`
- **能力分类**：`Search and Font Personalization`
- **指令**：Change Chrome's default search engine to DuckDuckGo and increase the default font size to 'Very Large' for better readability.
- **评估函数**：`["match_in_list", "check_font_size"]`，`"conj": "and"`
- **result 类型**：`default_search_engine` + `chrome_font_size`
- **验证逻辑**：搜索引擎为 DuckDuckGo + 字体 ≥ 20
- **操作步骤数**：2
- **postconfig**：需要重启 Chrome
- **来源**：[Google Chrome 帮助](https://support.google.com/chrome/answer/95426)
- **🆕 替换**：原 `93eabf48`（Bing+最大字体+SafeBrowsing）

---

#### 任务 L1-12：重命名配置文件并停留在设置页（👤 用户配置）
- **ID**：`84b523c5-de36-4e84-b694-6d00d4928f76`
- **Slug**：`rename_profile_workprofile`
- **能力分类**：`Profile Renaming`
- **指令**：Rename the current Chrome profile to 'WorkProfile' and stay on the profile customization settings page so I can review other options.
- **评估函数**：`["exact_match", "is_expected_active_tab_approximate"]`，`"conj": "and"`
- **result 类型**：`profile_name` + `active_url_from_accessTree`
- **验证逻辑**：配置文件名 == 'WorkProfile' + 停留在 `chrome://settings/manageProfile`
- **操作步骤数**：2
- **postconfig**：需要重启 Chrome
- **来源**：[Google Chrome 帮助](https://support.google.com/chrome/answer/2364824)
- **🆕 替换**：原 `9656a811`（SafeBrowsing+DNT+停留Security页）

---

#### 任务 L1-13：导航到 Chrome 内部版本页（📄 内部页面导航）
- **ID**：`6cf2d275-3ea6-47c3-9715-fe5744848835`
- **Slug**：`navigate_chrome_version_page`
- **能力分类**：`Internal Browser Navigation`
- **指令**：Open Chrome's internal version information page (chrome://version) so I can check the browser version and command-line flags.
- **评估函数**：`is_expected_active_tab`
- **result 类型**：`active_tab_info`
- **验证逻辑**：当前页 URL 为 `chrome://version/`
- **操作步骤数**：1
- **来源**：[Google Chrome 帮助](https://support.google.com/chrome/answer/95414)
- **🆕 替换**：原 `99146c54`（自动清除+DNT+增强保护三件套）

---

#### 任务 L1-14：创建书签文件夹并添加网页（📁 书签管理进阶）
- **ID**：`14bf5be7-f2a1-4d88-abdb-7bcbc0af7654`
- **Slug**：`create_bookmark_folder_tech_news`
- **能力分类**：`Bookmark Folder Organization`
- **指令**：Create a new folder named 'Tech News' on the bookmarks bar and add the currently open Hacker News tab to that folder.
- **初始状态**：预先打开 Hacker News 页面
- **评估函数**：`["is_expected_bookmarks", "is_expected_bookmarks"]`，`"conj": "and"`
- **result 类型**：`bookmarks` × 2
- **验证逻辑**：书签栏包含 'Tech News' 文件夹 + 书签栏包含 HN URL
- **操作步骤数**：2
- **来源**：[Google Chrome 帮助](https://support.google.com/chrome/answer/188842)
- **🆕 替换**：原 `af630914`（最大字体+DNT）

---

#### 任务 L1-15：启用 DNT + 增强保护（🔒 隐私设置代表）
- **ID**：`76840308-38a7-4263-a5b5-224dee202056`
- **Slug**：`enable_dnt_and_enhanced_protection`
- **能力分类**：`Privacy Setting Hardening`
- **指令**：Enable the 'Send a Do Not Track request' setting and switch Safe Browsing to 'Enhanced protection' mode in Chrome.
- **初始状态**：预先禁用 DNT 和增强保护
- **评估函数**：`["exact_match", "exact_match"]`，`"conj": "and"`
- **result 类型**：`enable_do_not_track` + `enable_enhanced_safety_browsing`
- **验证逻辑**：两项设置均为 `true`
- **操作步骤数**：2
- **postconfig**：需要重启 Chrome
- **来源**：[Google Chrome 帮助](https://support.google.com/chrome/answer/9890866)
- **🆕 替换**：原 `bb5e4c0d`（Bing+DNT+增强保护），保留为 L1 中**唯一**的隐私设置任务

---

### L1 任务汇总
| 序号 | Slug | 能力维度 | 核心操作 | 评估函数 | 步骤数 |
|------|------|---------|---------|---------|--------|
| L1-1 | `delete_specific_site_cookies` | 🍪 Cookie 管理 | 删除 Amazon/eBay Cookie | `is_cookie_deleted` | 2 |
| L1-2 | `restore_closed_tab` | 🏷️ 标签页恢复 | 恢复关闭的标签页 | `is_expected_tabs` | 1 |
| L1-3 | `bookmark_drug_database` | 📁 书签管理 | 导航 + 添加书签 | `is_expected_active_tab`+`is_expected_bookmarks` | 2 |
| L1-4 | `clear_youtube_history_keep_others` | 📜 历史记录管理 | 选择性删除历史 | `check_history_keywords_absent_and_present` | 2 |
| L1-5 | `change_chrome_language_to_french` | 🌐 语言/国际化 | 切换为法语 | `exact_match` | 2 |
| L1-6 | `set_startup_multiple_pages` | 🏠 启动页配置 | 设置两个启动页 | `is_expected_tabs` | 2 |
| L1-7 | `save_autofill_address` | 📋 自动填充 | 添加自动填充地址 | `check_direct_json_object`+`is_expected_active_tab_approximate` | 3 |
| L1-8 | `create_website_desktop_shortcut` | 🖥️ 桌面快捷方式 | 创建网站快捷方式 | `is_shortcut_on_desktop`+`is_expected_active_tab` | 2 |
| L1-9 | `disable_refresh_ui_flags` | 🚩 Chrome Flags | 禁用 2023 UI flags | `check_enabled_experiments` | 2 |
| L1-10 | `bookmark_transformer_switch_tab` | 📁 书签+标签 | 添加书签+切换标签 | `is_expected_bookmarks`+`is_expected_active_tab` | 2 |
| L1-11 | `duckduckgo_engine_large_font` | ⚙️ 外观设置 | DuckDuckGo+大字体 | `match_in_list`+`check_font_size` | 2 |
| L1-12 | `rename_profile_workprofile` | 👤 用户配置 | 重命名 Profile | `exact_match`+`is_expected_active_tab_approximate` | 2 |
| L1-13 | `navigate_chrome_version_page` | 📄 内部页面导航 | 打开 chrome://version | `is_expected_active_tab` | 1 |
| L1-14 | `create_bookmark_folder_tech_news` | 📁 书签进阶 | 创建文件夹+添加书签 | `is_expected_bookmarks` × 2 | 2 |
| L1-15 | `enable_dnt_and_enhanced_protection` | 🔒 隐私设置 | DNT + 增强保护 | `exact_match` × 2 | 2 |

---

### L1 统计信息
- 总任务数：**15**
- 需要重启 Chrome（postconfig）：**8** 个
- 需要代理（proxy=true）：**8** 个
- 覆盖 Getter 类型：**13 种**（vs V1 的 8 种）
- 覆盖能力维度：**13 维**（vs V1 的 ~4 维）
- 涉及 Do Not Track 的任务：**1/15**（7%，vs V1 的 11/15 = 73%）

#### V1 → V2 变更对照
| V1 任务 ID | V1 Slug | V2 替换为 | 替换原因 |
|---|---|---|---|
| `030eeff7` | `privacy_hardening_full` | `delete_specific_site_cookies` | DNT三件套 → Cookie管理 |
| `12086550` | `password_manager_dnt` | `clear_youtube_history_keep_others` | DNT副任务 → 历史记录管理 |
| `2ad9387a` | `create_favorites_bookmark_folder` | `change_chrome_language_to_french` | DNT副任务 → 语言设置 |
| `2ae9ba84` | `rename_profile_secure` | `set_startup_multiple_pages` | DNT+SB副任务 → 多启动页 |
| `3299584d` | `set_wikipedia_homepage_safe` | `save_autofill_address` | SB副任务 → 自动填充 |
| `3720f614` | `set_nasa_startup_page` | `create_website_desktop_shortcut` | DNT副任务 → 桌面快捷方式 |
| `480bcfea` | `disable_refresh_ui_flags` | ⭐ 保留（去除DNT） | 聚焦 flags 能力 |
| `93eabf48` | `bing_large_font_safe` | `duckduckgo_engine_large_font` | SB副任务 → 纯外观设置 |
| `9656a811` | `safe_browsing_dnt_review` | `rename_profile_workprofile` | DNT+SB → 纯Profile |
| `99146c54` | `privacy_auto_clear_enhanced` | `navigate_chrome_version_page` | DNT三件套 → 内部导航 |
| `af630914` | `largest_font_size_dnt` | `create_bookmark_folder_tech_news` | DNT副任务 → 书签进阶 |
| `bb5e4c0d` | `bing_dnt_enhanced` | `enable_dnt_and_enhanced_protection` | 保留为唯一DNT任务 |

### 3.2 第二级（L2）—— 网站导航与多步操作 —— 21 个
L2 任务为多步复合操作，当前版本已将 6 个偏购物 / 出行筛选题替换为公共信息 / 文档导航题，以提升内容多样性。现阶段主要分为三类：
1. **公开网站导航 / 搜索类**：在旅行、政务、健康、科技文档等网站完成 2–4 步导航、搜索或定位，最终停留在目标页。
2. **Chrome 设置 / 收藏 / 快捷方式混合类**：同时完成隐私设置调整、书签保存或桌面快捷方式创建。
3. **少量消费场景保留类**：保留少量电商 / 消费类任务，用于覆盖真实用户在 Chrome 中的商业浏览场景。

多数任务使用 `is_expected_url_pattern_match`、`is_expected_active_tab`、`check_direct_json_object`、`exact_match`、`is_expected_bookmarks` 等已有验证器组合完成状态校验。

---

#### 任务 L2-1：Steam Dota 2 免费 DLC 加入购物车
- **ID**：`121ba48f-9e17-48ce-9bc6-a4fb17a7ebba`
- **Slug**：`steam_dota2_dlc_cart`
- **能力分类**：`DLC Cart Assembly`
- **指令**：In Steam, locate Dota 2 and add all available free DLC to cart, then leave the cart page open for review.
- **评估函数**：`["is_added_to_steam_cart", "is_expected_url_pattern_match"]`，`"conj": "and"`
- **result**：`page_info` / `active_tab_info`
- **expected**：购物车页面含 Dota 2 免费 DLC 商品名 + URL 匹配 Steam 购物车路径模式
- **操作步骤数**：3（搜索 Dota 2 → 进入 DLC 列表 → 逐一加入购物车 → 前往购物车）
- **来源**：[Steam Dota 2 DLC 页面](https://store.steampowered.com/dlc/570/Dota_2/)

---

#### 任务 L2-2：PubMed 检索结果页 + 开启 Do Not Track
- **ID**：`1704f00f-79e6-43a7-961b-cedd3724d5fd`
- **Slug**：`pubmed_melatonin_review_dnt`
- **能力分类**：`Scientific Search Filtering`
- **指令**：On PubMed, search for melatonin insomnia, keep the results sorted by date with both Free full text and Review filters applied, and enable Chrome's Do Not Track request before finishing.
- **评估函数**：`["check_direct_json_object", "is_expected_url_pattern_match", "exact_match"]`，`"conj": "and"`
- **result**：`active_tab_url_parse` / `active_tab_info` / `enable_do_not_track`
- **expected**：URL 参数中 `term=melatonin insomnia`、`sort=date`，且结果页 URL 同时保留 `Free full text` 与 `Review` 两个筛选参数 + Do Not Track 为 `true`
- **操作步骤数**：4（输入检索词 → 应用 Free full text 与 Review 筛选 → 按 date 排序 → 开启 Do Not Track）
- **来源**：`https://pubmed.ncbi.nlm.nih.gov/?term=melatonin+insomnia&filter=simsearch2.ffrft&filter=pubt.review&sort=date`

---

#### 任务 L2-3：CDC Flu 症状页 + 开启 Do Not Track
- **ID**：`2888b4e6-5b47-4b57-8bf5-c73827890774`
- **Slug**：`cdc_flu_symptoms_dnt`
- **能力分类**：`Public Health Page Retrieval`
- **指令**：On the CDC website, navigate to the Signs and Symptoms of Flu page and enable Chrome's Do Not Track request before finishing.
- **评估函数**：`["is_expected_url_pattern_match", "exact_match"]`，`"conj": "and"`
- **result**：`active_tab_info` / `enable_do_not_track`
- **expected**：当前页面 URL 精确落在 CDC Flu `signs-symptoms` 页面 + Do Not Track 为 `true`
- **操作步骤数**：3（进入 CDC Flu 专题 → 打开 Signs and Symptoms 页面 → 开启 Do Not Track）
- **来源**：`https://www.cdc.gov/flu/signs-symptoms/index.html`

---

#### 任务 L2-4：创建 2048 游戏桌面快捷方式
- **ID**：`35253b65-1c19-4304-8aa4-6884b8218fc0`
- **Slug**：`create_2048_desktop_shortcut`
- **能力分类**：`Shortcut Creation and Renaming`
- **指令**：Create a desktop shortcut for this website using Chrome's built-in Create shortcut feature, rename it to '2048 Daily Practice', and keep the game page open.
- **初始状态**：预先打开 `https://www.mathsisfun.com/games/2048.html`
- **评估函数**：`["is_shortcut_on_desktop", "is_expected_active_tab"]`，`"conj": "and"`
- **result**：`shortcuts_on_desktop` / `active_tab_info`
- **expected**：桌面上存在名为 `2048 Daily Practice` 的快捷方式 + 当前活跃页为 2048 游戏页
- **操作步骤数**：3（菜单 → 创建快捷方式 → 重命名）
- **来源**：`https://support.google.com/chrome/answer/15085120`

---

#### 任务 L2-5：AccuWeather 曼彻斯特月视图
- **ID**：`368d9ba4-203c-40c1-9fa3-da2f1430ce63`
- **Slug**：`accuweather_monthly_forecast`
- **能力分类**：`Monthly Forecast Navigation`
- **指令**：On AccuWeather, open the monthly forecast view for Manchester, GB for this month and keep that monthly page active.
- **评估函数**：`["check_direct_json_object", "is_expected_url_pattern_match"]`，`"conj": "and"`
- **result**：`url_dashPart` / `active_url_from_accessTree`
- **expected**：URL dash 部分中包含 `manchester-gb` 等关键词 + URL 匹配月视图路径模式
- **操作步骤数**：3（搜索曼彻斯特 → 进入月视图 → 确认当月）
- **来源**：[AccuWeather Manchester Monthly Forecast](https://www.accuweather.com/en/gb/manchester/m15-6/april-weather/329260)

---

#### 任务 L2-6：arXiv 检索结果页 + 开启 Safe Browsing
- **ID**：`47543840-672a-467d-80df-8f7c3b9788c9`
- **Slug**：`arxiv_vision_transformer_recent_safe`
- **能力分类**：`Academic Search Configuration`
- **指令**：On arXiv, search for vision transformer in all fields, keep the results showing abstracts and sorted by announcement date newest first, and enable Chrome's Safe Browsing protection before finishing.
- **评估函数**：`["check_direct_json_object", "is_expected_url_pattern_match", "exact_match"]`，`"conj": "and"`
- **result**：`active_tab_url_parse` / `active_tab_info` / `enable_safe_browsing`
- **expected**：URL 参数中 `query=vision transformer`、`searchtype=all`、`abstracts=show`、`order=-announced_date_first`、`size=50`，且 Safe Browsing 为 `true`
- **操作步骤数**：4（输入检索词 → 保持 All fields 搜索 → 切换为显示摘要并按最新公告排序 → 开启 Safe Browsing）
- **来源**：`https://arxiv.org/search/?query=vision+transformer&searchtype=all&abstracts=show&order=-announced_date_first&size=50`

---

#### 任务 L2-7：BabyCenter 查找名字 Carl 相似名结果页
- **ID**：`59155008-fe71-45ec-8a8f-dc35497b6aa8`
- **Slug**：`babycenter_similar_name_page`
- **能力分类**：`Similar-Name Navigation`
- **指令**：Find the baby name detail page for 'Carl' and then navigate to a similar-name result page for Carl while staying on BabyCenter.
- **评估函数**：`is_expected_url_pattern_match`
- **result**：`active_url_from_accessTree`
- **expected**：URL 匹配 BabyCenter 相似名结果页的正则模式（含 `carl` 关键词）
- **操作步骤数**：2（搜索 Carl → 点击相似名）
- **来源**：[BabyCenter Similar Names for Carl](https://www.babycenter.com/baby-names/similar/carl)

---

#### 任务 L2-8：Delta 航班搜索仅显示里程结果
- **ID**：`6c4c23a1-42a4-43cc-9db1-2f86ff3738cc`
- **Slug**：`delta_miles_search`
- **能力分类**：`Miles-Only Flight Filtering`
- **指令**：On Delta, search flights from Seattle (SEA) to New York (NYC) for the 5th of next month and filter to Miles results only.
- **评估函数**：`check_direct_json_object`
- **result**：`active_tab_html_parse`
- **expected**：页面 HTML 中里程筛选处于激活状态
- **操作步骤数**：3（填写出发地/目的地/日期 → 搜索 → 切换为里程视图）
- **来源**：[Delta 官方订票入口](https://www.delta.com/)

---

#### 任务 L2-9：NASA Artemis II 任务页 + 书签保存
- **ID**：`7f52cab9-535c-4835-ac8c-391ee64dc930`
- **Slug**：`nasa_artemis_ii_bookmark`
- **能力分类**：`Mission Page Bookmarking`
- **指令**：On NASA's website, navigate to the Artemis II mission page, keep it open, and bookmark it to your bookmarks bar.
- **评估函数**：`["is_expected_url_pattern_match", "is_expected_bookmarks"]`，`"conj": "and"`
- **result**：`active_tab_info` / `bookmarks`
- **expected**：活跃页 URL 匹配 NASA Artemis II mission 页面 + 该页面已保存到书签栏
- **操作步骤数**：3（进入 NASA 任务 / Missions 导航 → 打开 Artemis II 页面 → 添加到书签栏）
- **来源**：`https://www.nasa.gov/mission/artemis-ii/`

---

#### 任务 L2-10：Python Docs pathlib 页面 + 开启 Do Not Track
- **ID**：`9f3f70fc-5afc-4958-a7b7-3bb4fcb01805`
- **Slug**：`python_docs_pathlib_dnt`
- **能力分类**：`API Docs Navigation`
- **指令**：In the Python documentation, navigate to the pathlib library reference page and enable Chrome's Do Not Track request before finishing.
- **评估函数**：`["is_expected_url_pattern_match", "exact_match"]`，`"conj": "and"`
- **result**：`active_tab_info` / `enable_do_not_track`
- **expected**：URL 匹配 Python 官方文档 `pathlib` 页面（允许 `/3/` 或 `/3.x/` 版本路径） + Do Not Track 为 `true`
- **操作步骤数**：3（进入 Library Reference / 搜索 pathlib → 打开 pathlib 页面 → 开启 Do Not Track）
- **来源**：`https://docs.python.org/3/library/pathlib.html`

---

#### 任务 L2-11：DOJ 网站 Civil Division 表单筛选页
- **ID**：`9f935cce-0a9f-435f-8007-817732bfc0a5`
- **Slug**：`doj_civil_forms_page`
- **能力分类**：`Government Form Filtering`
- **指令**：On the DOJ website, open the Civil Division forms listing and keep the filtered forms URL with Civil Division component selected.
- **评估函数**：`is_expected_url_pattern_match`
- **result**：`active_url_from_accessTree`
- **expected**：URL 匹配 DOJ 表单筛选页路径（含 Civil Division 参数）
- **操作步骤数**：2（进入表单页面 → 选择 Civil Division 筛选）
- **来源**：[DOJ Forms with Civil Division Filter](https://www.justice.gov/forms?field_component_target_id=431)

---

#### 任务 L2-12：Virginia DMV 驾照资格要求页
- **ID**：`a728a36e-8bf1-4bb6-9a03-ef039a5233f0`
- **Slug**：`dmv_license_eligibility`
- **能力分类**：`Eligibility Page Navigation`
- **指令**：On Virginia DMV, navigate to the Driver License Eligibility Requirements page and keep the exact eligibility path open.
- **评估函数**：`is_expected_url_pattern_match`
- **result**：`active_url_from_accessTree`
- **expected**：URL 精确匹配 Virginia DMV 驾照资格页路径
- **操作步骤数**：2（在 DMV 网站导航至驾照 → 找到资格要求页）
- **来源**：[Virginia DMV Driver License Eligibility Requirements](https://www.dmv.virginia.gov/licenses-ids/license/applying/eligibility)

---

#### 任务 L2-13：FlightAware 论坛最多回复帖 + 开启 Do Not Track
- **ID**：`a96b564e-dbe9-42c3-9ccf-b4498073438a`
- **Slug**：`flightaware_banter_thread`
- **能力分类**：`Forum Thread Discovery`
- **指令**：On FlightAware, find community discussions and open the thread with the most replies (The Banter Thread). Also enable Do Not Track before you finish.
- **评估函数**：`["is_expected_active_tab", "exact_match"]`，`"conj": "and"`
- **result**：`active_tab_info` / `enable_do_not_track`
- **expected**：活跃页精确匹配 Banter Thread URL + Do Not Track 为 `true`
- **操作步骤数**：3（进入社区讨论 → 排序找最多回复帖 → 开启 DoNotTrack）
- **来源**：[FlightAware Discussions: The Banter Thread](https://discussions.flightaware.com/t/the-banter-thread/4412)

---

#### 任务 L2-14：谷歌搜索论文 + 开启 Do Not Track
- **ID**：`ae78f875-5b98-4907-bbb5-9c737fc68c03`
- **Slug**：`google_search_pdf_dnt`
- **能力分类**：`Search Results with Privacy Toggle`
- **指令**：Search Google for 'attention is all you need pdf' and keep the search results page open. Also enable Chrome's 'Do Not Track' request for privacy.
- **评估函数**：`["is_expected_url_pattern_match", "exact_match"]`，`"conj": "and"`
- **result**：`active_tab_info` / `enable_do_not_track`
- **expected**：URL 匹配 Google 搜索结果页模式（含 `attention is all you need` 关键词） + Do Not Track 为 `true`
- **操作步骤数**：2（Google 搜索 → 开启 DoNotTrack）
- **来源**：`https://support.google.com/chrome/answer/2790761`

---

#### 任务 L2-15：Drugs.com Tamiflu 副作用专页 + 开启 Enhanced Safe Browsing
- **ID**：`b070486d-e161-459b-aa2b-ef442d973b92`
- **Slug**：`tamiflu_side_effects_page`
- **能力分类**：`Medical Article Retrieval`
- **指令**：On Drugs.com, find Tamiflu side effects and keep the dedicated side-effects article open (not the generic drug overview page). Also enable Chrome's Enhanced Safe Browsing protection.
- **评估函数**：`["is_expected_url_pattern_match", "exact_match"]`，`"conj": "and"`
- **result**：`active_url_from_accessTree` / `enable_enhanced_safety_browsing`
- **expected**：URL 匹配 Drugs.com 副作用专页路径（含 `tamiflu` 和 `side-effects`） + Enhanced Safe Browsing 为 `true`
- **操作步骤数**：3（搜索 Tamiflu → 进入副作用专页 → 开启 Enhanced Safe Browsing）
- **来源**：[Drugs.com Tamiflu Side Effects](https://www.drugs.com/sfx/tamiflu-side-effects.html)

---

#### 任务 L2-16：Recreation.gov Diamond 营地按下次可订排序
- **ID**：`b4f95342-463e-4179-8c3f-193cd7241fb2`
- **Slug**：`recreation_next_available`
- **能力分类**：`Camp Availability Sorting`
- **指令**：On Recreation.gov, find the Diamond campground page and switch availability sorting to 'Next Available', then keep that sorted availability view open.
- **评估函数**：`["check_direct_json_object", "is_expected_url_pattern_match"]`，`"conj": "and"`
- **result**：`active_tab_html_parse` / `active_tab_info`
- **expected**：HTML 中排序选项显示为 `Next Available` + URL 匹配 Recreation.gov Diamond 营地路径
- **操作步骤数**：3（搜索 Diamond 营地 → 进入营地页 → 切换排序方式）
- **来源**：[Recreation.gov Diamond Campground](https://www.recreation.gov/camping/campgrounds/233869)

---

#### 任务 L2-17：United Airlines 行李费计算器页面
- **ID**：`c1fa57f3-c3db-4596-8f09-020701085416`
- **Slug**：`united_bag_fee_calculator`
- **能力分类**：`Baggage Tool Bookmarking`
- **指令**：On United Airlines, navigate to the Checked Bag Fee Calculator page and keep it open at the calculator section (not the generic baggage policy page). Also bookmark this calculator page to your bookmarks bar for quick access.
- **评估函数**：`["is_expected_url_pattern_match", "is_expected_bookmarks"]`，`"conj": "and"`
- **result**：`active_tab_info` / `bookmarks`
- **expected**：URL 匹配 United Airlines 行李费计算器页面路径 + 该页面已保存到书签栏
- **操作步骤数**：3（在 United 网站找到计算器页 → 确认停留在正确页面 → 添加到书签栏）
- **来源**：[United Checked Bag Fee Calculator](https://www.united.com/en/us/checked-bag-fee-calculator)

---

#### 任务 L2-18：MDN Fetch API 页面 + 书签保存
- **ID**：`cabb3bae-cccb-41bd-9f5d-0f3a9fecd825`
- **Slug**：`mdn_fetch_api_bookmark`
- **能力分类**：`API Reference Bookmarking`
- **指令**：On MDN Web Docs, navigate to the Fetch API reference page, keep it open, and bookmark it to your bookmarks bar.
- **评估函数**：`["is_expected_url_pattern_match", "is_expected_bookmarks"]`，`"conj": "and"`
- **result**：`active_tab_info` / `bookmarks`
- **expected**：当前页面 URL 匹配 MDN Fetch API 页面 + 该页面已保存到书签栏
- **操作步骤数**：3（进入 MDN Web API 文档 → 打开 Fetch API 页面 → 添加到书签栏）
- **来源**：`https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API`

---

#### 任务 L2-19：NFL.com 2019 超级碗比分页面
- **ID**：`f0b971a1-6831-4b9b-a50e-22a6e47f45ba`
- **Slug**：`nfl_super_bowl_2019_page`
- **能力分类**：`Sports Archive Bookmarking`
- **指令**：On NFL.com, find the 2019 season Super Bowl score page, keep the postseason week summary view open, and bookmark this page to your bookmarks bar.
- **评估函数**：`["is_expected_active_tab", "is_expected_bookmarks"]`，`"conj": "and"`
- **result**：`active_url_from_accessTree` / `bookmarks`
- **expected**：活跃页精确匹配 `https://www.nfl.com/scores/2019/post4` + 该页面已保存到书签栏
- **操作步骤数**：4（进入 Scores → 选择 2019 赛季 → 打开季后赛 / 超级碗周 → 添加到书签栏）
- **来源**：[NFL 2019 Super Bowl Scores](https://www.nfl.com/scores/2019/post4)

---

#### 任务 L2-20：Ticketek FAQ 标签页 + 开启 Safe Browsing
- **ID**：`f3b19d1e-2d48-44e9-b4e1-defcae1a0197`
- **Slug**：`ticketek_delivery_faq_safe`
- **能力分类**：`Support FAQ Retrieval`
- **指令**：On Ticketek, locate the FAQ page about ticket delivery, keep that FAQ tab open, and enable Safe Browsing protection.
- **评估函数**：`["is_expected_active_tab", "exact_match"]`，`"conj": "and"`
- **result**：`active_tab_info` / `enable_safe_browsing`
- **expected**：活跃页精确匹配 Ticket Delivery FAQ URL + Safe Browsing 为 `true`
- **操作步骤数**：3（进入 Help/FAQ → 找到配送相关 FAQ → 开启 SafeBrowsing）
- **来源**：[Ticketek Ticket Delivery FAQs](https://help.ticketek.com.au/hc/en-us/articles/360001880488-Ticket-Delivery-FAQs)

---

#### 任务 L2-21：Apple iPhone 三机型对比
- **ID**：`f5d96daf-83a8-4c86-9686-bada31fc66ab`
- **Slug**：`iphone_compare_three_models`
- **能力分类**：`Product Comparison Setup`
- **指令**：On Apple, open the iPhone comparison tool and compare exactly these three models together: iPhone 15 Pro Max, iPhone 14 Pro Max, and iPhone 13 Pro Max.
- **评估函数**：`["check_direct_json_object", "is_expected_url_pattern_match"]`，`"conj": "and"`
- **result**：`active_tab_url_parse` / `active_tab_info`
- **expected**：URL 参数中同时含三款机型 + URL 匹配 Apple 对比页路径模式
- **操作步骤数**：3（进入 iPhone 对比工具 → 选择三款机型 → 发起对比）
- **来源**：[Apple Compare iPhone Models](https://www.apple.com/iphone/compare/)

---

### L2 任务汇总
| # | Slug | 网站 | 评估函数 | proxy |
|---|------|------|----------|-------|
| 1 | `steam_dota2_dlc_cart` | Steam | `is_added_to_steam_cart` + `is_expected_url_pattern_match` | ✅ |
| 2 | `pubmed_melatonin_review_dnt` | PubMed | `check_direct_json_object` + `is_expected_url_pattern_match` + `exact_match` | ❌ |
| 3 | `cdc_flu_symptoms_dnt` | CDC | `is_expected_url_pattern_match` + `exact_match` | ❌ |
| 4 | `create_2048_desktop_shortcut` | 2048 Game | `is_shortcut_on_desktop` + `is_expected_active_tab` | ✅ |
| 5 | `accuweather_monthly_forecast` | AccuWeather | `check_direct_json_object` + `is_expected_url_pattern_match` | ✅ |
| 6 | `arxiv_vision_transformer_recent_safe` | arXiv | `check_direct_json_object` + `is_expected_url_pattern_match` + `exact_match` | ❌ |
| 7 | `babycenter_similar_name_page` | BabyCenter | `is_expected_url_pattern_match` + `is_expected_active_tab_approximate` | ✅ |
| 8 | `delta_miles_search` | Delta | `check_direct_json_object` + `is_expected_url_pattern_match` | ❌ |
| 9 | `nasa_artemis_ii_bookmark` | NASA | `is_expected_url_pattern_match` + `is_expected_bookmarks` | ❌ |
| 10 | `python_docs_pathlib_dnt` | Python Docs | `is_expected_url_pattern_match` + `exact_match` | ❌ |
| 11 | `doj_civil_forms_page` | DOJ | `is_expected_url_pattern_match` | ❌ |
| 12 | `dmv_license_eligibility` | Virginia DMV | `is_expected_url_pattern_match` | ❌ |
| 13 | `flightaware_banter_thread` | FlightAware | `is_expected_active_tab` + `exact_match` | ✅ |
| 14 | `google_search_pdf_dnt` | Google | `is_expected_url_pattern_match` + `exact_match` | ✅ |
| 15 | `tamiflu_side_effects_page` | Drugs.com | `is_expected_url_pattern_match` + `exact_match` | ✅ |
| 16 | `recreation_next_available` | Recreation.gov | `check_direct_json_object` + `is_expected_url_pattern_match` | ❌ |
| 17 | `united_bag_fee_calculator` | United Airlines | `is_expected_url_pattern_match` + `is_expected_bookmarks` | ✅ |
| 18 | `mdn_fetch_api_bookmark` | MDN Web Docs | `is_expected_url_pattern_match` + `is_expected_bookmarks` | ❌ |
| 19 | `nfl_super_bowl_2019_page` | NFL.com | `is_expected_active_tab` + `is_expected_bookmarks` | ✅ |
| 20 | `ticketek_delivery_faq_safe` | Ticketek | `is_expected_active_tab` + `exact_match` | ❌ |
| 21 | `iphone_compare_three_models` | Apple | `check_direct_json_object` + `is_expected_url_pattern_match` | ✅ |

---

### L2 统计信息
- 总任务数：**21**
- 需要代理（proxy=true）：**10** 个
- 需要 postconfig：**0** 个
- 纯网站导航 / 交互：**8** 个
- 网站交互 + 浏览器状态混合（隐私设置 / 书签 / 快捷方式）：**13** 个
- 含严格状态校验（URL 参数 / HTML / 页面内容 / 购物车状态）：**7** 个

---

### L2 任务网站分布
| 网站类别 | 网站 | 任务数 |
|---------|------|--------|
| 电商 / 消费 | Steam, Apple | 2 |
| 旅行 / 交通 | Delta, FlightAware, United Airlines, Ticketek | 4 |
| 公共信息 / 政务 / 健康 / 科学 | PubMed, CDC, AccuWeather, arXiv, BabyCenter, DOJ, Virginia DMV, Drugs.com, Recreation.gov, NASA | 10 |
| 开发者文档 / 浏览器工具 | Google, Python Docs, MDN Web Docs, 2048 Game | 4 |
| 体育 / 赛事 | NFL.com | 1 |

---

### L2 能力覆盖统计（正式版）

说明：以下统计按“一级能力簇”计数，同一任务可同时落入多个能力簇，因此各项合计会超过 21。

- 覆盖一级能力簇：**6 类**
- 公共信息 / 政务 / 健康 / 科学站点：**10 / 21**
- 旅行 / 交通站点：**4 / 21**
- 含浏览器状态持久化（隐私 / 安全 / 书签 / 快捷方式）：**13 / 21**
- 含严格状态校验（URL 参数 / HTML / 页面内容 / 购物车状态）：**7 / 21**
- 含相对时间推理：**2 / 21**

| 一级能力簇 | 任务数 | 代表任务 | 说明 |
|---|---:|---|---|
| 精确目标页导航 | 12 | `cdc_flu_symptoms_dnt`、`ticketek_delivery_faq_safe`、`dmv_license_eligibility` | 重点考察站内层级导航、目标页辨别、避免停留在泛首页 / 总览页 |
| 结果页状态构造 | 9 | `delta_miles_search`、`pubmed_melatonin_review_dnt`、`arxiv_vision_transformer_recent_safe` | 考察搜索、筛选、排序、参数构造和结果页状态保持 |
| 隐私与安全设置 | 8 | `cdc_flu_symptoms_dnt`、`pubmed_melatonin_review_dnt`、`arxiv_vision_transformer_recent_safe` | 考察 Do Not Track、Safe Browsing、Enhanced Safe Browsing 等浏览器设置 |
| 书签与桌面持久化 | 5 | `nasa_artemis_ii_bookmark`、`mdn_fetch_api_bookmark`、`create_2048_desktop_shortcut` | 考察浏览器 / 桌面层面的可持久化产物创建 |
| 相对时间推理 | 2 | `accuweather_monthly_forecast`、`delta_miles_search` | 保留必要的时间推理覆盖，但不再让日期型任务主导 L2 |
| 消费操作闭环 | 2 | `steam_dota2_dlc_cart`、`iphone_compare_three_models` | 保留少量真实消费场景，避免完全失去商业网站操作代表性 |

#### L2 能力覆盖结论

1. 当前 L2 已形成“精确目标页导航 + 参数化结果页构造 + 浏览器状态操作”三足结构，且参数化结果页不再局限于购物或出行站点。
2. 浏览器状态混合题占比已达到 **13 / 21**，严格状态校验题回升到 **7 / 21**，说明 L2 不再只是“找到某个网页”，而是开始稳定覆盖结果页构造与用户偏好操作。
3. 相对时间题已压缩到 **2 / 21**，显著降低了因为日期、时区、外站动态内容引入的不稳定性。

---

### L2 去重建议（正式版）

1. 继续控制“精确目标页 + 隐私 / 安全设置”模式。目前已有 **8** 题带有显式浏览器设置校验，这类模式已经足够代表，不建议继续线性扩张。
2. 继续控制“打开页面 + 添加书签 / 快捷方式”模式。目前已有 **4** 个书签任务和 **1** 个桌面快捷方式任务，持久化能力覆盖已经够用。
3. 公共信息站点的多样性已经明显提升，但“精确落页型”仍然有 **12** 题。下一批新增题更适合继续补充非电商网站上的搜索结果页、表单填写、下载导出、多标签协同等流程型能力。
4. 出行类任务已经从 7 个降到 4 个，建议暂时冻结该类扩充；如果后续还要替换，优先考虑 `flightaware_banter_thread` 或 `ticketek_delivery_faq_safe` 这类“目标页 + 设置”的近邻模式。
5. 相对时间任务现在只剩 2 个，比例已经合理。后续新增题不建议重新引入大量日期推理型站点筛选任务。

---

### 3.3 第三级（L3）—— 高级工作流（复杂多步操作 + 精准状态验证）—— 10 个
L3 任务为复杂多步工作流，涵盖需要精细操作的在线预约填写、浏览器隐私数据精细管理、扩展程序安装、PDF 导出等高难度场景。多数任务要求 **5 个以上 GUI 操作**，并对结果进行多维度验证。

---

#### 任务 L3-1：选择性删除 YouTube 浏览历史（保留其他网站）
- **ID**：`44ee5668-ecd5-4366-a6ce-c1c9b8d4e938`
- **Slug**：`delete_youtube_history_only`
- **能力分类**：`Selective History Pruning`
- **指令**：Remove only YouTube browsing history entries while preserving other websites in history (for example nytimes/cnn/bbc should remain).
- **初始状态**：预置 8 条历史记录（4 条 YouTube、3 条新闻网站、1 条 National Geographic）
- **评估函数**：`check_history_keywords_absent_and_present`
- **result**：`history`（下载 History SQLite 数据库）
- **expected**：`{"type": "keywords_absent_present", "absent_keywords": ["youtube"], "present_keywords": ["nytimes", "bbc", "cnn"]}`
- **验证逻辑**：历史数据库中 YouTube 相关 URL 全部消失，nytimes/bbc/cnn 仍然存在
- **操作步骤数**：5+（进入历史管理 → 按网站筛选/搜索 YouTube → 逐条删除或批量选中删除）
- **postconfig**：需要重启 Chrome
- **来源**：`https://superuser.com/questions/1787991/clear-browsing-history-from-specific-site-on-chrome`

---

#### 任务 L3-2：加载 unpacked Chrome 扩展
- **ID**：`6766f2b8-8a72-417f-a9e5-56fcaa735837`
- **Slug**：`load_unpacked_extension`
- **能力分类**：`Unpacked Extension Loading`
- **指令**：Load the unpacked extension from /home/user/Desktop/helloExtension into Chrome, then keep the Extensions management page open when you are done.
- **初始状态**：预先下载 `helloExtension.zip` 并解压到 `/home/user/Desktop/helloExtension`
- **评估函数**：`["is_in_list", "is_expected_active_tab_approximate"]`，`"conj": "and"`
- **result**：`find_unpacked_extension_path` / `active_url_from_accessTree`
- **expected**：已加载的 unpacked 扩展路径为 `/home/user/Desktop/helloExtension` + 当前页为 `chrome://extensions`
- **验证逻辑**：扩展已安装且路径正确 + 当前停留在扩展管理页
- **操作步骤数**：4（开启开发者模式 → 点击「加载已解压的扩展程序」→ 选择文件夹 → 确认）
- **来源**：`https://developer.chrome.com/docs/extensions/get-started/tutorial/hello-world`

---

#### 任务 L3-3：删除三个购物网站的 Cookie
- **ID**：`7b6c7e24-c58a-49fc-a5bb-d57b80e5b4c3`
- **Slug**：`delete_store_cookies`
- **能力分类**：`Multi-Site Cookie Removal`
- **指令**：I opened shopping pages on multiple stores. Please remove all saved site cookies for Amazon, eBay, and Walmart so none of those websites remember me.
- **初始状态**：预先打开 amazon.com、ebay.com、walmart.com 三个标签页（以触发 Cookie 写入）
- **评估函数**：`is_cookie_deleted`
- **result**：`cookie_data`（下载 Cookies SQLite 数据库）
- **expected**：`{"type": "domains", "domains": [".amazon.com", ".ebay.com", ".walmart.com"]}`
- **验证逻辑**：三个域名下的所有 Cookie 均已删除
- **操作步骤数**：5+（进入各网站设置 → 分别查找并清除站点数据，或通过 `chrome://settings/siteData` 批量处理）
- **postconfig**：需要重启 Chrome
- **来源**：`https://support.google.com/chrome/answer/95647`

---

#### 任务 L3-4：Cars.com 纽约电动车筛选（ZIP + 价格上限）
- **ID**：`82279c77-8fc6-46f6-9622-3ba96f61b477`
- **Slug**：`cars_ev_radius_price_filter`
- **能力分类**：`Multi-Filter Vehicle Search`
- **指令**：On Cars.com, find electric cars within 50 miles of ZIP 10001 and cap max price at $50,000, then keep the filtered result page open.
- **评估函数**：`["check_direct_json_object", "is_expected_url_pattern_match"]`，`"conj": "and"`
- **result**：`active_tab_url_parse` / `active_tab_info`
- **expected**：URL 参数中包含 `stock_type=all&zip=10001&maximum_distance=50&list_price_max=50000&fuel_slugs[]=electric` 等关键字段 + URL 匹配 Cars.com 搜索结果路径
- **操作步骤数**：5+（选择车辆类型 → 输入 ZIP → 选择范围 → 设置最高价格 → 搜索）
- **来源**：[Cars.com Search Results](https://www.cars.com/shopping/results/)

---

#### 任务 L3-5：Qatar Airways 孟买→斯德哥尔摩单程航班 + Do Not Track
- **ID**：`82bc8d6a-36eb-4d2d-8801-ef714fb1e55a`
- **Slug**：`qatar_oneway_search`
- **能力分类**：`One-Way Flight Search`
- **指令**：On Qatar Airways, search a one-way flight from Mumbai (BOM) to Stockholm (STO) for next Monday, then enable Do Not Track before finishing.
- **评估函数**：`["check_direct_json_object", "exact_match"]`，`"conj": "and"`
- **result**：`active_tab_url_parse` / `enable_do_not_track`
- **expected**：URL 参数中包含 `from=BOM`、`to=STO`、单程标志以及正确日期 + Do Not Track 为 `true`
- **操作步骤数**：5+（选择单程 → 填写出发地/目的地 → 选择日期 → 搜索 → 开启 DoNotTrack）
- **来源**：[Qatar Airways Book a Flight](https://www.qatarairways.com/en-hk/homepage.html)

---

#### 任务 L3-6：TripAdvisor 纽约周末酒店按最低价排序
- **ID**：`b7895e80-f4d1-4648-bee0-4eb45a6f1fa8`
- **Slug**：`tripadvisor_hotels_low_price`
- **能力分类**：`Hotel Search Sorting`
- **指令**：On TripAdvisor, find New York City hotels for 2 adults next weekend and sort results by lowest price.
- **评估函数**：`["check_direct_json_object", "check_direct_json_object"]`，`"conj": "and"`
- **result**：`active_tab_html_parse` × 2
- **expected**：HTML 中人数为 2 adults + 排序方式为 lowest price
- **操作步骤数**：5+（搜索 NYC → 选择入住/退房日期 → 设置人数 → 搜索 → 按价格排序）
- **来源**：[Tripadvisor New York City Hotels](https://www.tripadvisor.com/Hotels-g60763-New_York_City_New_York-Hotels.html)

---

#### 任务 L3-7：CharlieCard 预约填写（日期计算 + 表单预填）
- **ID**：`da46d875-6b82-4681-9284-653b0c7ae241`
- **Slug**：`charliecard_appointment_prefill`
- **能力分类**：`Appointment Form Prefill`
- **指令**：Book (without submitting) a CharlieCard Store appointment for TAP application on the first Monday eight months later at 10:15 AM, and prefill applicant name/email as James Smith and james.smith@gmail.com.
- **初始状态**：预先打开 `https://www.mbta.com/`
- **评估函数**：`["is_expected_url_pattern_match", "check_direct_json_object", "check_direct_json_object"]`，`"conj": "and"`
- **result**：`active_tab_info` / `active_tab_html_parse` × 2
- **expected**：
  - URL 含 `book/CharlieCardStoreAppointments@mbta.com/`
  - HTML 中服务内容为 TAP 非自动审批 + 时间为 `{MonthFull} {Day0D}, 10:15 AM`（相对时间规则）
  - 表单中 name 字段为 `James Smith`，mail 字段为 `james.smith@gmail.com`
- **验证逻辑**：URL 路径正确 + 预约时间（相对时间计算）正确 + 表单字段已填入
- **操作步骤数**：7+（MBTA 官网 → CharlieCard → 预约入口 → 选择 TAP 服务 → 选择日期/时间 → 填写姓名邮箱）
- **来源**：[MBTA Reduced Fares / TAP](https://www.mbta.com/fares/reduced)

---

#### 任务 L3-8：导出网页为无边距 PDF
- **ID**：`e1e75309-3ddb-4d09-92ec-de869c928143`
- **Slug**：`export_article_pdf_no_margins`
- **能力分类**：`PDF Export Configuration`
- **指令**：Open the current article and export it as a PDF to Desktop named LLM_Agents_NoMargin.pdf (use no margins). Keep the article tab active when finished.
- **评估函数**：`["compare_pdfs", "is_expected_active_tab"]`，`"conj": "and"`
- **result**：`vm_file` / `active_tab_info`
- **expected**：导出 PDF 与参考 PDF 文本高度匹配 + 无边距设置
- **验证逻辑**：导出的 PDF 与参考 PDF 文本相似度高 + 活动标签停留在文章页
- **操作步骤数**：4+（打开打印 → 设置保存为 PDF → 选择无边距 → 命名并保存到桌面）
- **来源**：`https://in5stepstutorials.com/google-chrome/save-web-page-as-pdf-in-chrome.php`

---

#### 任务 L3-9：Chrome 持久化配置组合（Profile + Search + Font + Startup）
- **ID**：`f79439ad-3ee8-4f99-a518-0eb60e5652b0`
- **Slug**：`workprofile_duckduckgo_startup_bundle`
- **能力分类**：`Persistent Browser Personalization`
- **指令**：In Chrome, rename the current profile to `WorkProfile`, set DuckDuckGo as the default search engine, increase the default font size to Very Large, and configure Chrome to open https://www.wikipedia.org/ and https://www.python.org/ on startup.
- **评估函数**：`["exact_match", "match_in_list", "check_font_size", "is_expected_tabs"]`，`"conj": "and"`
- **result**：`profile_name` / `default_search_engine` / `chrome_font_size` / `open_tabs_info`
- **expected**：Profile 名称为 `WorkProfile` + 默认搜索引擎为 DuckDuckGo + 默认字体尺寸达到 Very Large 范围 + 重启后启动页自动打开 Wikipedia 与 Python 两个标签页
- **验证逻辑**：多项持久化设置在重启后仍保持生效，且启动页行为符合预期
- **操作步骤数**：8+（进入个人资料设置 → 重命名 Profile → 修改默认搜索引擎 → 调整字体大小 → 配置启动页为两站点）
- **postconfig**：需要重启 Chrome
- **来源**：现实场景构造来源：知识工作者首次配置工作浏览器时常见的“重命名工作档案 + 设定搜索引擎 + 放大默认字体 + 固定启动页”组合设置需求

---

#### 任务 L3-10：Delta 航班搜索 + Do Not Track
- **ID**：`fc6d8143-9452-4171-9459-7f515143419a`
- **Slug**：`delta_flight_search_dnt`
- **能力分类**：`Flight Search with Privacy Toggle`
- **指令**：On Delta, search flights from New York (JFK) to Chicago (ORD) for tomorrow, keep the results page open, and enable Do Not Track.
- **评估函数**：`["check_direct_json_object", "exact_match"]`，`"conj": "and"`
- **result**：`active_tab_html_parse` / `enable_do_not_track`
- **验证逻辑**：HTML 解析含正确航线 / 日期 + DNT 开启
- **操作步骤数**：4+（填写航线信息 → 搜索 → 开启 Do Not Track）
- **来源**：[Delta 官方订票入口](https://www.delta.com/)

---

### L3 任务汇总
| # | Slug | 操作类型 | 评估函数 | proxy | postconfig |
|---|------|---------|----------|-------|------------|
| 1 | `delete_youtube_history_only` | 浏览器数据管理 | `check_history_keywords_absent_and_present` | ✅ | ✅ |
| 2 | `load_unpacked_extension` | 扩展安装 | `is_in_list` + `is_expected_active_tab_approximate` | ❌ | ❌ |
| 3 | `delete_store_cookies` | 浏览器数据管理 | `is_cookie_deleted` | ✅ | ✅ |
| 4 | `cars_ev_radius_price_filter` | 网站多条件筛选 | `check_direct_json_object` + `is_expected_url_pattern_match` | ✅ | ❌ |
| 5 | `qatar_oneway_search` | 航班搜索 + 设置 | `check_direct_json_object` + `exact_match` | ✅ | ❌ |
| 6 | `tripadvisor_hotels_low_price` | 酒店搜索排序 | `check_direct_json_object` ×2 | ✅ | ❌ |
| 7 | `charliecard_appointment_prefill` | 预约表单填写 | `is_expected_url_pattern_match` + `check_direct_json_object` ×2 | ✅ | ❌ |
| 8 | `export_article_pdf_no_margins` | 文件导出 | `compare_pdfs` + `is_expected_active_tab` | ✅ | ❌ |
| 9 | `workprofile_duckduckgo_startup_bundle` | 浏览器持久化配置 | `exact_match` + `match_in_list` + `check_font_size` + `is_expected_tabs` | ❌ | ✅ |
| 10 | `delta_flight_search_dnt` | 航班搜索 + 设置 | `check_direct_json_object` + `exact_match` | ❌ | ❌ |

---

### L3 统计信息
- 总任务数：**10**
- 需要代理（proxy=true）：**7** 个
- 需要 postconfig：**3** 个
- 网站复杂交互：**5** 个
- 浏览器数据管理：**2** 个
- 文件导出：**1** 个
- 扩展安装：**1** 个
- 浏览器持久化配置：**1** 个

---

### L3 难度评估与修改建议（正式版）

说明：L3 的重点不是单纯增加步骤数，而是要求任务同时具备更强的状态约束、更高的跨页面或重启后持久化要求，以及更低的“误打误撞成功”概率。

- 当前 L3 中，**8 / 10** 任务为多指标联合验证，仅 **2 / 10** 为单指标数据库类任务。
- 含 HTML / URL 参数 / 文件 / 数据库等严格状态校验的任务为 **10 / 10**，说明 L3 当前整体难度已经达到“强结果约束”要求。
- 出行 / 酒店 / 预约类复杂网页任务仍占 **4 / 10**，但已不再主导全部 L3；本轮通过替换原单指标航班搜索题，补入了 **浏览器持久化配置** 能力。
- 含浏览器设置或重启后持久化验证的任务提升到 **3 / 10**，更符合 L3 对“跨页面配置 + 重启生效”能力的要求。

| 一级能力簇 | 任务数 | 代表任务 | 说明 |
|---|---:|---|---|
| 浏览器数据精细管理 | 2 | `delete_youtube_history_only`、`delete_store_cookies` | 直接验证 History / Cookies 数据库中的精细删除效果 |
| 参数化结果页构造 | 2 | `cars_ev_radius_price_filter`、`qatar_oneway_search` | 依赖 URL 参数精确保持搜索条件，避免只到达泛搜索页 |
| HTML / 表单状态校验 | 3 | `tripadvisor_hotels_low_price`、`charliecard_appointment_prefill`、`delta_flight_search_dnt` | 通过页面结构读取排序、日期、人数、表单内容等状态 |
| 浏览器持久化配置 | 2 | `load_unpacked_extension`、`workprofile_duckduckgo_startup_bundle` | 覆盖扩展安装与跨重启设置持久化两类 Chrome 管理能力 |
| 文件与产物导出 | 1 | `export_article_pdf_no_margins` | 验证 GUI 导出的实体文件与参考结果一致 |
| 相对时间推理 | 4 | `qatar_oneway_search`、`tripadvisor_hotels_low_price`、`charliecard_appointment_prefill` | 保留日期推理，但不再让其成为唯一的高难来源 |

#### L3 结论

1. 当前 L3 的整体难度是足够的，弱点主要不在“太简单”，而在于此前过度集中在出行检索类任务。
2. 本轮替换后，L3 新增了一个稳定且高约束的 Chrome 内部管理工作流，降低了对外站动态搜索页的依赖。
3. 后续如果还要补题，优先方向应是“浏览器持久化配置、多标签恢复/启动、文件下载导出、数据库精细操作”，而不是继续增加航班 / 酒店筛选题。

---

## 4. 评估函数汇总

### 4.1 评估函数使用统计（含多指标中的重复）
| 函数名 | 来源文件 | L1 | L2 | L3 | 总计 |
|--------|----------|----|----|----|-------|
| `exact_match` | `general.py` | 4 | 8 | 3 | **15** |
| `check_direct_json_object` | `general.py` | 1 | 6 | 7 | **14** |
| `is_expected_url_pattern_match` | `chrome.py` | 0 | 17 | 2 | **19** |
| `is_expected_active_tab` | `chrome.py` | 4 | 4 | 1 | **9** |
| `is_expected_bookmarks` | `chrome.py` | 4 | 4 | 0 | **8** |
| `is_expected_active_tab_approximate` | `chrome.py` | 2 | 1 | 1 | **4** |
| `match_in_list` | `general.py` | 1 | 0 | 1 | **2** |
| `check_font_size` | `chrome.py` | 1 | 0 | 1 | **2** |
| `check_enabled_experiments` | `chrome.py` | 1 | 0 | 0 | **1** |
| `is_expected_tabs` | `chrome.py` | 2 | 0 | 1 | **3** |
| `is_added_to_steam_cart` | `chrome.py` | 0 | 1 | 0 | **1** |
| `is_shortcut_on_desktop` | `chrome.py` | 1 | 1 | 0 | **2** |
| `is_cookie_deleted` | `chrome.py` | 1 | 0 | 1 | **2** |
| `check_history_keywords_absent_and_present` | `chrome.py` | 1 | 0 | 1 | **2** |
| `is_in_list` | `general.py` | 0 | 0 | 1 | **1** |
| `compare_pdfs` | `chrome.py` | 0 | 0 | 1 | **1** |

---

### 4.2 Getter 类型使用统计
| Getter 类型 | L1 | L2 | L3 | 总计 |
|-------------|----|----|----|-------|
| `enable_do_not_track` | 1 | 4 | 2 | **7** |
| `active_tab_info` | 3 | 15 | 3 | **21** |
| `active_url_from_accessTree` | 3 | 7 | 1 | **11** |
| `active_tab_html_parse` | 0 | 2 | 5 | **7** |
| `active_tab_url_parse` | 0 | 3 | 2 | **5** |
| `enable_safe_browsing` | 0 | 3 | 0 | **3** |
| `enable_enhanced_safety_browsing` | 1 | 1 | 0 | **2** |
| `bookmarks` | 4 | 4 | 0 | **8** |
| `data_delete_automacally` | 0 | 0 | 0 | **0** |
| `new_startup_page` | 0 | 0 | 0 | **0** |
| `default_search_engine` | 1 | 0 | 1 | **2** |
| `chrome_font_size` | 1 | 0 | 1 | **2** |
| `profile_name` | 1 | 0 | 1 | **2** |
| `enabled_experiments` | 1 | 0 | 0 | **1** |
| `open_tabs_info` | 2 | 0 | 1 | **3** |
| `cookie_data` | 1 | 0 | 1 | **2** |
| `history` | 1 | 0 | 1 | **2** |
| `page_info` | 0 | 1 | 0 | **1** |
| `shortcuts_on_desktop` | 1 | 1 | 0 | **2** |
| `find_unpacked_extension_path` | 0 | 0 | 1 | **1** |
| `url_path_parse` | 0 | 0 | 0 | **0** |
| `url_dashPart` | 0 | 1 | 0 | **1** |
| `vm_file` | 0 | 0 | 1 | **1** |

---

## 5. 验证架构总结

### 5.1 分层验证策略

Chrome 任务的验证形成了比较清晰的分层结构：

```text
L1 设置类  →  读取 Preferences / Local State / open tabs
           →  exact_match / match_in_list / check_font_size / is_expected_tabs

L2 导航类  →  URL / HTML / 书签 / 快捷方式
           →  check_direct_json_object / is_expected_url_pattern_match / is_expected_bookmarks

L3 复杂类  →  多维度（URL + HTML + DB + 文件 + 重启后持久化）
           →  compare_pdfs / is_cookie_deleted / check_history_keywords_absent_and_present / 组合评估
```

### 5.2 与 Audacity / OS 验证方式的核心区别

- **Audacity**：更偏向导出产物的离线分析，验证核心围绕 WAV / `.aup3` 文件。
- **OS / Multi-app**：常依赖 VM 内命令、窗口状态或跨应用产物链条。
- **Chrome**：更依赖 CDP 和本地浏览器数据文件，既要验证页面状态，也要验证配置与数据库状态是否真正持久化。

---

## 6. Config 与 postconfig 模式

### 6.1 标准启动配置

绝大多数 Chrome 任务共用以下启动骨架：

```json
[
  {
    "type": "launch",
    "parameters": {
      "command": ["google-chrome", "--remote-debugging-port=1337"]
    }
  },
  {
    "type": "launch",
    "parameters": {
      "command": ["socat", "tcp-listen:9222,fork", "tcp:localhost:1337"]
    }
  }
]
```

### 6.2 常见 Config 组合

| 模式 | 常见配置 | 典型用途 |
|------|----------|----------|
| 纯内部设置类 | `launch` × 2 | 修改 Chrome 设置、Profile、字体、搜索引擎、flags |
| 网站导航类 | `launch` × 2 + `chrome_open_tabs` + `activate_window` | 预打开网站首页并进入交互 |
| 数据库预置类 | `execute` / `update_browse_history` + 标准启动 | 预写入 History、Cookies 或其他可验证状态 |
| 文件导出类 | `download` 或预置打开页 + 标准启动 | PDF 导出、扩展安装、桌面快捷方式 |

### 6.3 Postconfig 模式

Chrome 中凡是依赖持久化配置或数据库落盘的任务，通常都需要在 `evaluator.postconfig` 中重启浏览器后再评估。统一模式如下：

```json
"postconfig": [
  {
    "type": "launch",
    "parameters": {
      "command": ["pkill", "chrome"]
    }
  },
  {
    "type": "launch",
    "parameters": {
      "command": ["google-chrome", "--remote-debugging-port=1337"]
    }
  },
  {
    "type": "sleep",
    "parameters": {
      "seconds": 3
    }
  }
]
```

这类模式适用于 Do Not Track、Safe Browsing、启动页、多标签恢复、Cookie / History 删除等“必须落盘后才能稳定读取”的任务。

---

## 7. 特殊验证机制

### 7.1 相对时间计算（`rule_relativeTime`）

部分任务的 `expected` 使用 `rule_relativeTime` 类型，允许用自然语言日期表达式生成动态期望值：

```json
{
  "type": "rule_relativeTime",
  "rules": {
    "relativeTime": {
      "from": "next Monday"
    },
    "expected": {
      "time": "{Year}-{Month0D}-{Day0D}"
    }
  }
}
```

当前使用此机制的典型任务如下：

| 任务 | 时间表达式 |
|---|---|
| L2-5 `accuweather_monthly_forecast` | this month |
| L2-8 `delta_miles_search` | 5th next month |
| L3-5 `qatar_oneway_search` | next Monday |
| L3-6 `tripadvisor_hotels_low_price` | next weekend |
| L3-7 `charliecard_appointment_prefill` | first Monday 8 months later |

### 7.2 HTML 内容解析（`active_tab_html_parse`）

复杂任务会直接抓取活动页 HTML，再按结构化规则提取字段。当前常见模式包括：

- **class 模式**：按 CSS class 名提取文本或属性。
- **xpath 模式**：按 XPath 精确定位表单字段、按钮文案或结果摘要。
- **input 模式**：读取 input / textarea 的 `value`，验证表单是否已正确预填。
- **多对象模式**：处理同类元素的多位置匹配，用于排序结果页、乘客数、日期等多字段联合验证。

### 7.3 URL 参数解析（`active_tab_url_parse`）

适合筛选、排序、搜索词这类稳定编码在 URL query 中的场景。典型配置如下：

```json
{
  "type": "active_tab_url_parse",
  "goto_prefix": "https://www.",
  "parse_keys": ["originIata", "destinationIata", "tpAdults", "tpStartDate"],
  "replace": {
    "tpStartDate": "time"
  }
}
```

该机制比纯 URL 正则更强，因为它不仅验证“到了哪一页”，还验证“结果页内部参数是否正确”。

---

## 8. Task JSON 模板

### 8.1 纯设置类任务

```json
{
  "id": "<uuid4>",
  "task_slug": "<slug>",
  "difficulty": "L1",
  "snapshot": "chrome",
  "instruction": "<指令>",
  "source": "<来源 URL>",
  "config": [
    {"type": "launch", "parameters": {"command": ["google-chrome", "--remote-debugging-port=1337"]}},
    {"type": "launch", "parameters": {"command": ["socat", "tcp-listen:9222,fork", "tcp:localhost:1337"]}}
  ],
  "trajectory": "trajectories/",
  "related_apps": ["chrome"],
  "evaluator": {
    "postconfig": [
      {"type": "launch", "parameters": {"command": ["pkill", "chrome"]}},
      {"type": "launch", "parameters": {"command": ["google-chrome", "--remote-debugging-port=1337"]}},
      {"type": "sleep", "parameters": {"seconds": 3}}
    ],
    "func": ["exact_match"],
    "result": [{"type": "enable_do_not_track"}],
    "expected": [{"type": "rule", "rules": {"expected": "true"}}]
  },
  "proxy": false,
  "fixed_ip": false,
  "possibility_of_env_change": "low"
}
```

### 8.2 网站导航 + URL 验证任务

```json
{
  "id": "<uuid4>",
  "task_slug": "<slug>",
  "difficulty": "L2",
  "snapshot": "chrome",
  "instruction": "<指令>",
  "source": "<来源>",
  "config": [
    {"type": "launch", "parameters": {"command": ["google-chrome", "--remote-debugging-port=1337"]}},
    {"type": "launch", "parameters": {"command": ["socat", "tcp-listen:9222,fork", "tcp:localhost:1337"]}},
    {"type": "chrome_open_tabs", "parameters": {"urls_to_open": ["https://www.example.com"]}},
    {"type": "activate_window", "parameters": {"window_name": "Google Chrome"}}
  ],
  "trajectory": "trajectories/",
  "related_apps": ["chrome"],
  "evaluator": {
    "func": ["check_direct_json_object", "is_expected_url_pattern_match"],
    "conj": "and",
    "result": [
      {"type": "active_tab_url_parse", "goto_prefix": "https://www.", "parse_keys": ["key1", "key2"]},
      {"type": "active_tab_info"}
    ],
    "expected": [
      {"type": "rule", "rules": {"expected": {"key1": "value1", "key2": "value2"}}},
      {"type": "rule", "rules": {"expected": ["pattern1", "pattern2"]}}
    ]
  },
  "proxy": true,
  "fixed_ip": false,
  "possibility_of_env_change": "low"
}
```

### 8.3 多指标持久化任务

```json
{
  "id": "<uuid4>",
  "task_slug": "<slug>",
  "difficulty": "L3",
  "snapshot": "chrome",
  "instruction": "<指令>",
  "source": "<来源>",
  "config": [
    {"type": "launch", "parameters": {"command": ["google-chrome", "--remote-debugging-port=1337"]}},
    {"type": "launch", "parameters": {"command": ["socat", "tcp-listen:9222,fork", "tcp:localhost:1337"]}},
    {"type": "activate_window", "parameters": {"window_name": "Google Chrome"}}
  ],
  "trajectory": "trajectories/",
  "related_apps": ["chrome"],
  "evaluator": {
    "postconfig": [
      {"type": "launch", "parameters": {"command": ["pkill", "chrome"]}},
      {"type": "launch", "parameters": {"command": ["google-chrome", "--remote-debugging-port=1337"]}},
      {"type": "sleep", "parameters": {"seconds": 3}}
    ],
    "func": ["exact_match", "match_in_list", "check_font_size", "is_expected_tabs"],
    "conj": "and",
    "result": [
      {"type": "profile_name"},
      {"type": "default_search_engine"},
      {"type": "chrome_font_size"},
      {"type": "open_tabs_info"}
    ],
    "expected": [
      {"type": "rule", "rules": {"expected": "WorkProfile"}},
      {"type": "rule", "rules": {"expected": ["DuckDuckGo", "duckduckgo"]}},
      {"type": "rule", "rules": {"type": "range", "min": 20, "max": 99999}},
      {"type": "rule", "rules": {"type": "url", "urls": ["https://www.wikipedia.org/", "https://www.python.org/"]}}
    ]
  },
  "proxy": false,
  "fixed_ip": false,
  "possibility_of_env_change": "low"
}
```

---

## 9. 任务难度分布总结

| 级别 | 数量 | 主要操作类型 | 典型场景 |
|---|---|---|---|
| L1 | 15 | 浏览器设置修改、书签管理、标签操作 | 启动页配置、Profile 修改、书签操作、字体与搜索引擎设置 |
| L2 | 21 | 外部网站导航、筛选、排序、书签/隐私混合任务 | PubMed / arXiv 检索结果页、开发者文档导航、公共信息站点定位 |
| L3 | 10 | 复杂多步交互、数据管理、文件操作、持久化配置 | 选择性删历史、安装扩展、删 Cookie、填预约表单、导出 PDF、跨重启配置 |
| **总计** | **46** | | |

### 9.1 代理依赖分布

| 级别 | 需要代理 | 不需要代理 |
|---|---|---|
| L1 | 8 (53%) | 7 (47%) |
| L2 | 10 (48%) | 11 (52%) |
| L3 | 7 (70%) | 3 (30%) |
| **总计** | **25 (54%)** | **21 (46%)** |

### 9.2 可验证性保证

Chrome 任务的可验证性主要来自以下机制：

1. **Preferences / Local State 读取**：直接解析浏览器配置文件，确定性强。
2. **CDP 实时读取**：直接获取活动标签 URL、标题和 HTML，不依赖截图或 OCR。
3. **无障碍树回退机制**：当 CDP URL 读取不稳定时，可通过 accessTree 补充验证。
4. **SQLite 数据库验证**：直接读取 Cookies / History，验证删除和保留是否真实发生。
5. **文件系统检查**：验证 PDF、桌面快捷方式、扩展路径等外显产物。

文档中的任务设计均以这些稳定信号为核心，不依赖截图比对、OCR 或其他高噪声视觉检查方法。

---

## 10. 常见陷阱

### 10.1 Chrome 设置验证注意事项

- 部分设置必须在重启 Chrome 后才会稳定写入磁盘，因此设置类任务应优先考虑 `postconfig`。
- Preferences 中的布尔值是 JSON boolean，但 `exact_match` 规则中通常用字符串 `"true"` / `"false"` 表达。
- 不同平台的 Chrome 数据目录不同，getter 必须使用跨平台路径逻辑。

### 10.2 URL / HTML 验证注意事项

- 外站 URL 往往包含动态参数，正则规则应只保留稳定部分。
- URL 编码可能使用 `%20` 或 `+` 表示空格，规则中需要兼容两种写法。
- SPA 页面存在延迟渲染问题，HTML 解析类 getter 需要等待页面稳定后再抓取。

### 10.3 外部网站依赖风险

- 网站结构调整会直接影响 XPath、class 名和路径规则。
- 部分网站存在地域限制或反爬逻辑，因此 `proxy` 和 `possibility_of_env_change` 需要单独评估。
- 高频变动站点更适合做 URL 参数或浏览器状态校验，不适合依赖脆弱的 DOM 文案。

### 10.4 相对时间验证

- `rule_relativeTime` 依赖 VM 时区，日期类任务设计时要明确时区假设。
- 不同网站的日期格式差异很大，模板应尽量显式约束输出格式。

---

## 11. Docker 镜像要求

VM / Docker 镜像需要预装：

- **Google Chrome**（推荐稳定版）
- **socat**（用于调试端口转发）
- **X11 / GUI 环境**（Chrome 需要可见桌面）
- **Python 3**（评估器运行环境）

评估器依赖的第三方库：

| 库 | 用途 | 安装方式 |
|---|---|---|
| `rapidfuzz` | 模糊文本匹配 | `pip install rapidfuzz` |
| `beautifulsoup4` + `lxml` | HTML 解析 | `pip install beautifulsoup4 lxml` |
| `PyMuPDF` (`fitz`) | PDF 文本提取 | `pip install PyMuPDF` |
| `Pillow` | 图片处理 | `pip install Pillow` |
| `borb` | PDF 处理 | `pip install borb` |
| `imagehash` | 图片哈希对比 | `pip install imagehash` |
| `playwright` | 页面内容获取 | `pip install playwright` |

---

## 12. Interactive XT Chrome 参考

本节对应目录 `evaluation_examples/examples/interactive_xt` 中的 Chrome 可交互任务，目标不是替代前面的静态 Chrome task 主集，而是作为 **多轮用户需求演进** 的补充参考。

### 12.1 数据集概览

- **任务数**：15 个
- **任务入口**：全部使用 `"interactive": true`
- **快照**：全部为 `chrome`
- **风险与网络**：全部为 `proxy=false`、`possibility_of_env_change=low`
- **场景原型**：5 类交互 archetype，每类 3 个任务
- **phase 结构**：14 个任务为 3 phase，1 个任务为 2 phase

| 交互 archetype | 数量 | 代表任务 | 典型触发方式 |
|---|---:|---|---|
| ambiguous_instruction | 3 | `interactive_chrome_ambiguous_101` | `agent_asks` |
| requirement_change | 3 | `interactive_chrome_requirement_change_102` | `agent_done` |
| progressive_refinement | 3 | `interactive_chrome_progressive_108` | `agent_done` |
| interruption | 3 | `interactive_chrome_interruption_109` | `step_count` + `agent_done` |
| correction | 3 | `interactive_chrome_correction_110` | `agent_done` |

当前 Chrome interactive 集合的最终状态验证分布如下：

- `active_url_from_accessTree`：15 / 15
- `bookmarks`：12 / 15
- `open_tabs_info`：6 / 15
- `find_unpacked_extension_path`：2 / 15
- 浏览器设置持久化项：3 个任务涉及 `enable_do_not_track`，其中 1 个任务进一步叠加 `enable_enhanced_safety_browsing` 与 `data_delete_automacally`

### 12.2 质量评估

**总体结论**：当前 `interactive_xt` 的 Chrome 子集整体质量处于 **中上水平**，适合作为低风险、可稳定复现的多轮交互基线；但它更偏向“本地文档保留 / 书签整理 / 标签页收尾”型任务，尚不能代表完整的 Chrome 交互能力空间。

**主要优点**：

1. **稳定性高**：大量任务使用本地 HTML 页面而非外部站点，显著降低了 DOM 漂移、区域限制、登录态和网络波动风险。
2. **交互模式覆盖完整**：5 种 archetype 均有覆盖，且 `agent_asks`、`step_count`、`agent_done` 三类核心触发器都被实际使用。
3. **最终状态可验证**：绝大多数任务都落在已有 Chrome getter / metric 能稳定支撑的状态空间内，如当前页 URL、书签栏、标签页集合、扩展路径、隐私设置等。
4. **对话负担真实**：模糊、改口、打断、渐进细化、纠错都不是单纯改写 instruction，而是确实要求 Agent 调整执行方向。

**主要问题**：

1. **验证模板偏同质化**：修改前有 12 / 15 题都主要依赖“当前页 + 书签栏”这一套最终约束，容易把不同交互模式压缩成相似的收尾状态。
2. **局部约束弱于用户表述**：少数 requirement change / correction 题在文案里要求“撤销旧目标”，但 evaluator 只验证“新目标存在”，没有同步约束标签页清理。
3. **浏览器能力覆盖仍偏窄**：当前任务更偏向本地知识页导航和保留动作，较少覆盖下载确认、外部检索结果页、跨标签整理后的设置持久化、表单变更等更复杂的 Chrome 交互流程。

### 12.3 本轮修正

本轮对 4 个 Chrome interactive 任务做了针对性修正，目的是让“多轮交互要求”与“最终可验证状态”更一致：

| 任务 | 问题 | 修正 |
|---|---|---|
| `interactive_chrome_requirement_change_102` | 改口后只验证最终页面与书签，未强制清理旧标签 | 新增 1 个收尾 phase，并加入 `open_tabs_info`，要求最终只保留 `Incident Runbook` |
| `interactive_chrome_correction_105` | 纠错后未约束旧总览页标签是否关闭 | 新增“只保留认证页标签”约束，并加入 `open_tabs_info` |
| `interactive_chrome_interruption_109` | 打断后只验证书签与活动页，无法区分是否正确整理标签页 | 将最终状态升级为“只保留 Parking + Agenda 两个文档标签”，并加入 `open_tabs_info` |
| `interactive_chrome_correction_114` | 任务文案暗示需要纠正错误扩展，但 evaluator 只能验证正确扩展已加载 | 收紧文案表述，使其与当前 `find_unpacked_extension_path` 的正向存在性验证保持一致 |

修正后，带有 `open_tabs_info` 的 Chrome interactive 任务从 **3 / 15** 提升到 **6 / 15**，使 requirement change / correction / interruption 三类任务中更多样本具备“旧标签页必须被清理”的显式约束。

### 12.4 设计建议

后续如果继续扩展 Chrome interactive 子集，优先建议沿下面几个方向补题：

1. **下载与产物确认**：例如下载 PDF / 图片后，用户中途改文件名、改保存位置、改是否保留下载页。
2. **外部搜索结果页改口**：例如先在公共信息站搜索 A，后改成搜索 B，并要求保留正确筛选状态而不是仅到达某个页面。
3. **标签整理 + 设置混合**：例如用户先要求保留多个标签，后追加“顺便开启 DNT / Safe Browsing / 启动页恢复”。
4. **表单预填与需求变更**：例如用户先要求打开报名页，后改字段、改人数、改日期，并最终停留在未提交状态。

同时建议继续遵守以下原则：

- 优先使用 **本地可控页面或稳定公共页面**，不要为了“更像真实网页”牺牲评测可重复性。
- 当用户明确说“不要旧目标 / 只保留新目标”时，尽量把要求落到 `open_tabs_info`、`bookmarks` 这类**精确集合验证**上。
- 对扩展、设置、Cookie / History 这类状态任务，要确保任务文案不超出当前 getter / metric 的实际可验证边界。
- `step_count` 只适合真正需要“执行中途被打断”的任务；若阶段切换可由完成前一要求稳定触发，优先使用 `agent_done`。


