# LibreOffice Impress 任务设计文档

## 0. LibreOffice Impress 验证策略

### Impress 路径

评测虚拟机中 LibreOffice Impress 通过系统预装，**启动方式为 `libreoffice --impress <文件路径>`** 或通过 config 中 `open` 动作直接打开指定 `.pptx` 文件。

### 核心思路

LibreOffice Impress 的验证通过将 VM 中用户编辑后的 `.pptx` 文件下载到本地，与预制的 gold 标准文件进行结构化对比实现。

1. **演示文稿结构对比**（`compare_pptx_files`）：使用 `python-pptx` 解析 `.pptx` 文件，支持多维度比较——幻灯片数量、形状几何、文本内容、缩进、字体、颜色、项目符号、背景、备注等。
2. **过渡动画检查**（`check_transition`）：验证指定幻灯片是否设置了预期的过渡效果。
3. **页面方向检查**（`check_slide_orientation_Portrait`）：验证幻灯片是否为纵向布局。

**评估器架构**：通过 `vm_file` getter 下载编辑后文件，部分任务与 gold 文件对比，部分任务仅验证特定属性（rule-based）。

### 评估器通用模式

```python
def compare_pptx_files(file1_path, file2_path, **options):
    """
    参数：
        file1_path: 从 VM 下载的 .pptx 文件路径
        file2_path: gold 标准 .pptx 文件路径
        options: examine_shape, examine_text, examine_font 等布尔控制项
    返回：
        1.0（匹配）或 0.0（不匹配）
    """
```

---

## 1. 可用资源

总计：**10** 个初始文件 + 对应 gold 标准文件

### impress_v3 素材（30 个任务）

| # | 初始文件 | Gold 文件 | 任务概要 |
|---|---------|----------|--------|
| 1 | `Bitcoin_ The Digital Revolution.pptx` | `Bitcoin_L1.pptx` | Open "Bitcoin_ The Digital Revolution.pptx". On slide 1, change the co... |
| 2 | `Game Theory.pptx` | `GameTheory_L3.pptx` | Open "Game Theory.pptx" and perform all of the following: (1) On slide... |
| 3 | `The Evolution of Rock Music.pptx` | `RockMusic_L3.pptx` | Open "The Evolution of Rock Music.pptx" and perform: (1) Slide 1: back... |
| 4 | `Ecosystem Mechanisms for Maintaining Biodiversity in Natural Forests.pptx` | `Ecosystem_L3.pptx` | Open "Ecosystem Mechanisms for Maintaining Biodiversity in Natural For... |
| 5 | `The Golden Age of Arcade Games.pptx` | `ArcadeGames_L1.pptx` | Open "The Golden Age of Arcade Games.pptx". On slide 1, make all text ... |
| 6 | `The Evolution of Rock Music.pptx` | `RockMusic_L1.pptx` | Open "The Evolution of Rock Music.pptx". Change the title font size on... |
| 7 | `black_concise_work_report_template_english.pptx` | `BlackWorkReport_L3.pptx` | Open "black_concise_work_report_template_english.pptx" and apply: (1) ... |
| 8 | `The Golden Age of Arcade Games.pptx` | `ArcadeGames_L2.pptx` | In "The Golden Age of Arcade Games.pptx": (1) Set ALL slides backgroun... |
| 9 | `work_summary_template_english.pptx` | `WorkSummary_L3.pptx` | Open "work_summary_template_english.pptx" and apply all changes: (1) S... |
| 10 | `Game Theory.pptx` | `GameTheory_L2.pptx` | In "Game Theory.pptx": (1) On slide 4, change all body text to italic ... |
| 11 | `The Birthday Paradox.pptx` | `BirthdayParadox_L2.pptx` | In "The Birthday Paradox.pptx": (1) On slide 1, change all text to "Ti... |
| 12 | `Tencent Holdings Limited - 2025 Interim Report.pptx` | `` | In "Tencent Holdings Limited - 2025 Interim Report.pptx", change the s... |
| 13 | `Ecosystem Mechanisms for Maintaining Biodiversity in Natural Forests.pptx` | `Ecosystem_L1.pptx` | Open "Ecosystem Mechanisms for Maintaining Biodiversity in Natural For... |
| 14 | `Vincent van Gogh_ A Life of Passion and Color.pptx` | `VanGogh_L1.pptx` | Open "Vincent van Gogh_ A Life of Passion and Color.pptx". Make all ti... |
| 15 | `Game Theory.pptx` | `GameTheory_L1.pptx` | Open "Game Theory.pptx". On slide 1, set the background to dark blue (... |
| 16 | `Bitcoin_ The Digital Revolution.pptx` | `Bitcoin_L2.pptx` | In "Bitcoin_ The Digital Revolution.pptx": (1) On slide 1, set the bac... |
| 17 | `work_summary_template_english.pptx` | `WorkSummary_L1.pptx` | Open "work_summary_template_english.pptx". On slide 1, make the title ... |
| 18 | `Bitcoin_ The Digital Revolution.pptx` | `Bitcoin_L3.pptx` | Open "Bitcoin_ The Digital Revolution.pptx" and perform the following ... |
| 19 | `black_concise_work_report_template_english.pptx` | `BlackWorkReport_L1.pptx` | Open "black_concise_work_report_template_english.pptx". On slide 1, ch... |
| 20 | `The Birthday Paradox.pptx` | `` | In "The Birthday Paradox.pptx", add a "Fade" slide transition effect t... |
| 21 | `The Birthday Paradox.pptx` | `BirthdayParadox_L3.pptx` | Open "The Birthday Paradox.pptx" and perform all changes: (1) On slide... |
| 22 | `Tencent Holdings Limited - 2025 Interim Report.pptx` | `Tencent_L3.pptx` | Open the Tencent 2025 Interim Report and perform these changes: (1) On... |
| 23 | `work_summary_template_english.pptx` | `WorkSummary_L2.pptx` | In "work_summary_template_english.pptx": (1) On slide 2, center-align ... |
| 24 | `Ecosystem Mechanisms for Maintaining Biodiversity in Natural Forests.pptx` | `Ecosystem_L2.pptx` | In the Ecosystem Biodiversity presentation: (1) On slide 3, make the t... |
| 25 | `Tencent Holdings Limited - 2025 Interim Report.pptx` | `Tencent_L2.pptx` | In "Tencent Holdings Limited - 2025 Interim Report.pptx": (1) On slide... |
| 26 | `Vincent van Gogh_ A Life of Passion and Color.pptx` | `VanGogh_L2.pptx` | In the Van Gogh presentation: (1) Slide 5: body text dark red (#8B0000... |
| 27 | `The Evolution of Rock Music.pptx` | `RockMusic_L2.pptx` | In "The Evolution of Rock Music.pptx": (1) Right-align the title on AL... |
| 28 | `black_concise_work_report_template_english.pptx` | `BlackWorkReport_L2.pptx` | In "black_concise_work_report_template_english.pptx": (1) On ALL slide... |
| 29 | `Vincent van Gogh_ A Life of Passion and Color.pptx` | `VanGogh_L3.pptx` | Open the Van Gogh presentation and do all of the following: (1) Slide ... |
| 30 | `The Golden Age of Arcade Games.pptx` | `ArcadeGames_L3.pptx` | Open "The Golden Age of Arcade Games.pptx" and apply: (1) ALL slides: ... |

---

## 2. 评估函数设计

文件：`desktop_env/evaluators/metrics/slides.py`

### 2.1 主评估函数

| 函数名 | 描述 | 使用次数 |
|--------|------|---------|
| `compare_pptx_files` | 结构化对比两个 .pptx 文件（幻灯片内容/形状/文本/格式） | 28 |
| `check_transition` | 验证幻灯片过渡动画类型 | 1 |
| `check_slide_orientation_Portrait` | 验证幻灯片方向为纵向 | 1 |

---

## 3. 任务定义


### 3.1 第一级（L1）—— 基础操作 —— 1 个

> agent 在实测中 10 步内完成且得分 1.0 的任务

#### 任务 L1-1：The Birthday Paradox

- **ID**：`bd3f03cd-3ca8-4c8a-85d7-deb04c98a0d8`
- **来源**：`impress_v3`
- **指令**：In "The Birthday Paradox.pptx", add a "Fade" slide transition effect to slide 1.
- **素材文件**：`The Birthday Paradox.pptx`
- **评估函数**：`check_transition`
- **Gold 文件**：``

#### L1 任务来源标注

| 任务 | 来源类型 | 具体来源 | 标注理由 |
|------|---------|---------|---------|
| L1-1 | 官方帮助 | [Slide Transitions](https://help.libreoffice.org/latest/en-US/text/simpress/guide/animated_slidechange.html) + [Slide Management](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | In "The Birthday Paradox.pptx", add a "Fade" slide transition effect to slide 1. |

#### L1 任务汇总表

| # | 任务名称 | 素材文件 | 评估函数 |
|---|---------|---------|---------|
| 1 | The Birthday Paradox | `The Birthday Paradox.pptx` | `check_transition`  |


### 3.2 第二级（L2）—— 复合操作 —— 1 个

> agent 在 25 步内完成（得分 1.0）或 10 步内失败的任务

#### 任务 L2-1：Tencent Holdings Limited - 2025 Interim Report

- **ID**：`5361ce1b-58bf-4218-a03f-00497a3ce6f8`
- **来源**：`impress_v3`
- **指令**：In "Tencent Holdings Limited - 2025 Interim Report.pptx", change the slide orientation to portrait (vertical).
- **素材文件**：`Tencent Holdings Limited - 2025 Interim Report.pptx`
- **评估函数**：`check_slide_orientation_Portrait`
- **Gold 文件**：``

#### L2 任务来源标注

| 任务 | 来源类型 | 具体来源 | 标注理由 |
|------|---------|---------|---------|
| L2-1 | 官方帮助 | [Slide Management](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) + [Slide Orientation](https://help.libreoffice.org/latest/en-US/text/simpress/guide/change_scale.html) | In "Tencent Holdings Limited - 2025 Interim Report.pptx", change the slide orien |

#### L2 任务汇总表

| # | 任务名称 | 素材文件 | 评估函数 |
|---|---------|---------|---------|
| 1 | Tencent Holdings Limited - 2025 Interim Report | `Tencent Holdings Limited - 2025 Interim Report.pptx` | `check_slide_orientation_Portrait`  |


### 3.3 第三级（L3）—— 高级工作流 —— 28 个

> agent 无法完成或需要大量步骤（>25 步）的任务

#### 任务 L3-1：Bitcoin_ The Digital Revolution

- **ID**：`03e0e85a-bfbf-4155-b706-dc5bd60fb8a0`
- **来源**：`impress_v3`
- **指令**：Open "Bitcoin_ The Digital Revolution.pptx". On slide 1, change the color of all text to orange (#FF7F00) and make all text bold.
- **素材文件**：`Bitcoin_ The Digital Revolution.pptx`
- **评估函数**：`compare_pptx_files`
- **Gold 文件**：`Bitcoin_L1.pptx`

#### 任务 L3-2：Game Theory

- **ID**：`06706431-3011-417a-bd22-36869b25d1fe`
- **来源**：`impress_v3`
- **指令**：Open "Game Theory.pptx" and perform all of the following: (1) On slide 1, set background to dark blue (#00008B) and make all text white and bold. (2) On ALL slides, set title font size to 36pt. (3) On slide 4, make body text italic and dark blue (#00008B). (4) On slide 5, add this note: "Key concept: Nash Equilibrium occurs when no player can improve their payoff by unilaterally changing their strategy, given other players' strategies remain fixed." (5) On slide 6, set background to light gray (#D3D3D3). (6) On slide 9, change the table second row to: "Firm A: Lower Prices", "(4, 4)", "(9, 2)". (7) Delete the last 2 slides. Save.
- **素材文件**：`Game Theory.pptx`
- **评估函数**：`compare_pptx_files`
- **Gold 文件**：`GameTheory_L3.pptx`

#### 任务 L3-3：The Evolution of Rock Music

- **ID**：`0c7343ab-f0d9-4529-9097-5c101ac8bc74`
- **来源**：`impress_v3`
- **指令**：Open "The Evolution of Rock Music.pptx" and perform: (1) Slide 1: background black (#000000), all text red (#FF0000), bold, 44pt. (2) ALL slides: titles 36pt and bold. (3) ALL slides: right-align titles. (4) Slide 3: body text italic and dark gray (#404040). (5) Slide 4: add note: "Legacy: Rock music's influence extends beyond sound — it shaped fashion, politics, and social movements across multiple generations." (6) Slide 6: background dark gray (#404040), all text white. (7) Delete the last 4 slides. Save.
- **素材文件**：`The Evolution of Rock Music.pptx`
- **评估函数**：`compare_pptx_files`
- **Gold 文件**：`RockMusic_L3.pptx`

#### 任务 L3-4：Ecosystem Mechanisms for Maintaining Biodiversity in Natural Forests

- **ID**：`12776aaa-e48d-4423-856c-fd59e9f72887`
- **来源**：`impress_v3`
- **指令**：Open "Ecosystem Mechanisms for Maintaining Biodiversity in Natural Forests.pptx" and perform these changes: (1) On ALL slides, make title text bold and set to 32pt. (2) On slide 1, set the background to dark green (#006400) and all text to white (#FFFFFF). (3) On slide 2, make body text italic and forest green (#228B22). (4) On slide 3, center-align the title and add this note: "Conclusion: Preserving forest ecosystems requires integrated approaches combining conservation biology, sustainable forestry, and climate change mitigation strategies." (5) On slide 5, set background to light gray (#D3D3D3). (6) On slide 6, make all body text bold and underlined. Save.
- **素材文件**：`Ecosystem Mechanisms for Maintaining Biodiversity in Natural Forests.pptx`
- **评估函数**：`compare_pptx_files`
- **Gold 文件**：`Ecosystem_L3.pptx`

#### 任务 L3-5：The Golden Age of Arcade Games

- **ID**：`12fd9a81-7fdf-4f21-b6ce-7388cd2f840c`
- **来源**：`impress_v3`
- **指令**：Open "The Golden Age of Arcade Games.pptx". On slide 1, make all text bold, underlined, and yellow (#FFFF00).
- **素材文件**：`The Golden Age of Arcade Games.pptx`
- **评估函数**：`compare_pptx_files`
- **Gold 文件**：`ArcadeGames_L1.pptx`

#### 任务 L3-6：The Evolution of Rock Music

- **ID**：`16008ca9-7091-48b2-a22a-7a1ca1509109`
- **来源**：`impress_v3`
- **指令**：Open "The Evolution of Rock Music.pptx". Change the title font size on ALL slides to 36pt.
- **素材文件**：`The Evolution of Rock Music.pptx`
- **评估函数**：`compare_pptx_files`
- **Gold 文件**：`RockMusic_L1.pptx`

#### 任务 L3-7：black_concise_work_report_template_english

- **ID**：`16847518-ad96-4cdc-a639-c101bbeb6a23`
- **来源**：`impress_v3`
- **指令**：Open "black_concise_work_report_template_english.pptx" and apply: (1) Slide 1: Times New Roman, bold, 36pt. Background navy (#003366), text white. (2) ALL slides: titles 32pt and bold. (3) Slide 2: background dark gray (#404040). (4) Slide 3: body text italic and light gray (#D3D3D3). (5) Slide 4: add note: "Action items: Review budget allocation for Q3, prepare department performance metrics, schedule follow-up meeting with stakeholders." (6) Slide 5: center-align the title. (7) Slide 6: body text bold and underlined. Save.
- **素材文件**：`black_concise_work_report_template_english.pptx`
- **评估函数**：`compare_pptx_files`
- **Gold 文件**：`BlackWorkReport_L3.pptx`

#### 任务 L3-8：The Golden Age of Arcade Games

- **ID**：`209c3917-259e-4329-9f94-bb7a849e679c`
- **来源**：`impress_v3`
- **指令**：In "The Golden Age of Arcade Games.pptx": (1) Set ALL slides background to black (#000000). (2) On slide 1, make all text bold, underlined, and yellow (#FFFF00).
- **素材文件**：`The Golden Age of Arcade Games.pptx`
- **评估函数**：`compare_pptx_files`
- **Gold 文件**：`ArcadeGames_L2.pptx`

#### 任务 L3-9：work_summary_template_english

- **ID**：`2593a83c-f6b7-484e-91ad-3b0743c3058e`
- **来源**：`impress_v3`
- **指令**：Open "work_summary_template_english.pptx" and apply all changes: (1) Slide 1: title bold, 48pt, underlined. Background navy (#003366), text white. (2) ALL slides: background navy (#003366). (3) Slide 2: body text center-aligned and italic. (4) ALL slides: titles bold and white (#FFFFFF). (5) Slide 4: body text bold, underlined, yellow (#FFFF00). (6) Slide 5: add note: "Next steps: Finalize annual targets, distribute responsibility matrix to team leads, and set up monthly progress review cadence." (7) Slide 7: body text italic and teal (#008080). Save.
- **素材文件**：`work_summary_template_english.pptx`
- **评估函数**：`compare_pptx_files`
- **Gold 文件**：`WorkSummary_L3.pptx`

#### 任务 L3-10：Game Theory

- **ID**：`3be4747b-a8aa-4b79-8f0c-0c7326a3d169`
- **来源**：`impress_v3`
- **指令**：In "Game Theory.pptx": (1) On slide 4, change all body text to italic and dark blue (#00008B). (2) On slide 9, find the Pricing Game table and change the second row to: "Firm A: Lower Prices", "(4, 4)", "(9, 2)".
- **素材文件**：`Game Theory.pptx`
- **评估函数**：`compare_pptx_files`
- **Gold 文件**：`GameTheory_L2.pptx`

#### 任务 L3-11：The Birthday Paradox

- **ID**：`456c4488-c4c4-475f-b671-0556dac8696a`
- **来源**：`impress_v3`
- **指令**：In "The Birthday Paradox.pptx": (1) On slide 1, change all text to "Times New Roman" and italic. (2) On slide 4, make the title purple (#800080), bold, and underlined.
- **素材文件**：`The Birthday Paradox.pptx`
- **评估函数**：`compare_pptx_files`
- **Gold 文件**：`BirthdayParadox_L2.pptx`

#### 任务 L3-12：Ecosystem Mechanisms for Maintaining Biodiversity in Natural Forests

- **ID**：`59d057dc-fc2c-48b2-b7f2-b7c146be1496`
- **来源**：`impress_v3`
- **指令**：Open "Ecosystem Mechanisms for Maintaining Biodiversity in Natural Forests.pptx". On slide 1, change the title font to "Georgia" and set the font size to 40pt.
- **素材文件**：`Ecosystem Mechanisms for Maintaining Biodiversity in Natural Forests.pptx`
- **评估函数**：`compare_pptx_files`
- **Gold 文件**：`Ecosystem_L1.pptx`

#### 任务 L3-13：Vincent van Gogh_ A Life of Passion and Color

- **ID**：`74393e18-c452-44bb-a7df-08c2b73718cd`
- **来源**：`impress_v3`
- **指令**：Open "Vincent van Gogh_ A Life of Passion and Color.pptx". Make all title text bold AND italic across ALL slides.
- **素材文件**：`Vincent van Gogh_ A Life of Passion and Color.pptx`
- **评估函数**：`compare_pptx_files`
- **Gold 文件**：`VanGogh_L1.pptx`

#### 任务 L3-14：Game Theory

- **ID**：`8a9fd669-2142-46d4-bd0c-32cd6323b57f`
- **来源**：`impress_v3`
- **指令**：Open "Game Theory.pptx". On slide 1, set the background to dark blue (#00008B) and change all text to white (#FFFFFF).
- **素材文件**：`Game Theory.pptx`
- **评估函数**：`compare_pptx_files`
- **Gold 文件**：`GameTheory_L1.pptx`

#### 任务 L3-15：Bitcoin_ The Digital Revolution

- **ID**：`929e152a-b43a-4ad0-a9e5-b01f1a20b910`
- **来源**：`impress_v3`
- **指令**：In "Bitcoin_ The Digital Revolution.pptx": (1) On slide 1, set the background color to dark blue (#00008B) and change all text to white (#FFFFFF). (2) On slide 4 (THE BIRTH OF BITCOIN), add this speaker note: "Key talking point: The Genesis Block was mined on January 3rd, 2009, embedding a headline about bank bailouts as a political statement by Satoshi Nakamoto."
- **素材文件**：`Bitcoin_ The Digital Revolution.pptx`
- **评估函数**：`compare_pptx_files`
- **Gold 文件**：`Bitcoin_L2.pptx`

#### 任务 L3-16：work_summary_template_english

- **ID**：`9f172a30-0f37-4155-87b3-2ab704912166`
- **来源**：`impress_v3`
- **指令**：Open "work_summary_template_english.pptx". On slide 1, make the title bold, 48pt, and underlined.
- **素材文件**：`work_summary_template_english.pptx`
- **评估函数**：`compare_pptx_files`
- **Gold 文件**：`WorkSummary_L1.pptx`

#### 任务 L3-17：Bitcoin_ The Digital Revolution

- **ID**：`9fadf13a-c7f5-483c-a6e4-84dbe342ec6f`
- **来源**：`impress_v3`
- **指令**：Open "Bitcoin_ The Digital Revolution.pptx" and perform the following changes: (1) On slide 1, set the background to navy blue (#003366) and make all text white (#FFFFFF), bold, and 36pt. (2) On slide 2, make the title text orange (#FF7F00) and bold. (3) On slide 3, make all body/content text (not the title) italic and dark blue (#00008B). (4) On slide 5, set the background color to light gray (#D3D3D3). (5) On slide 6, add this speaker note: "Summary: Bitcoin has fundamentally changed how we think about money, trust, and decentralized systems." (6) Delete the last 3 slides from the presentation. Save the file.
- **素材文件**：`Bitcoin_ The Digital Revolution.pptx`
- **评估函数**：`compare_pptx_files`
- **Gold 文件**：`Bitcoin_L3.pptx`

#### 任务 L3-18：black_concise_work_report_template_english

- **ID**：`ac961eb2-aaee-41c1-941a-0277373c7831`
- **来源**：`impress_v3`
- **指令**：Open "black_concise_work_report_template_english.pptx". On slide 1, change all text to "Times New Roman" font.
- **素材文件**：`black_concise_work_report_template_english.pptx`
- **评估函数**：`compare_pptx_files`
- **Gold 文件**：`BlackWorkReport_L1.pptx`

#### 任务 L3-19：The Birthday Paradox

- **ID**：`bde97a2f-56de-4c6c-acd6-3aec3d25caff`
- **来源**：`impress_v3`
- **指令**：Open "The Birthday Paradox.pptx" and perform all changes: (1) On slide 1, set all text to Times New Roman, italic, bold. Set background to purple (#800080) and text color to white. (2) On slide 4, make title purple (#800080), bold, underlined. (3) On slide 5, make body text dark blue (#00008B) and italic. (4) On slide 6, add note: "The birthday paradox illustrates how human intuition about probability often fails when dealing with combinatorial problems." (5) On slide 7, set background to light gray (#D3D3D3). (6) On slide 8, make title bold, 36pt, maroon (#800000). Save.
- **素材文件**：`The Birthday Paradox.pptx`
- **评估函数**：`compare_pptx_files`
- **Gold 文件**：`BirthdayParadox_L3.pptx`

#### 任务 L3-20：Tencent Holdings Limited - 2025 Interim Report

- **ID**：`c425a255-7bcd-4840-a1c7-042ca352d969`
- **来源**：`impress_v3`
- **指令**：Open the Tencent 2025 Interim Report and perform these changes: (1) On slide 1, set background to navy (#003366), all text white, bold, 40pt. (2) On ALL slides, make titles bold and 32pt. (3) On slide 3, make body text italic. (4) On slide 4, add this note: "Board recommendation: Approve the proposed final dividend of HK$4.40 per share for the fiscal year ending June 2025." (5) On slide 6, set background to light gray (#D3D3D3) and all text to dark blue (#00008B). Save.
- **素材文件**：`Tencent Holdings Limited - 2025 Interim Report.pptx`
- **评估函数**：`compare_pptx_files`
- **Gold 文件**：`Tencent_L3.pptx`

#### 任务 L3-21：work_summary_template_english

- **ID**：`c9f5b0bf-a7b9-401a-b713-304b06ab75de`
- **来源**：`impress_v3`
- **指令**：In "work_summary_template_english.pptx": (1) On slide 2, center-align body text and make it italic. (2) Set ALL slides background to navy blue (#003366).
- **素材文件**：`work_summary_template_english.pptx`
- **评估函数**：`compare_pptx_files`
- **Gold 文件**：`WorkSummary_L2.pptx`

#### 任务 L3-22：Ecosystem Mechanisms for Maintaining Biodiversity in Natural Forests

- **ID**：`d1a5c9cc-e8d7-45a4-9539-6d9946d645f6`
- **来源**：`impress_v3`
- **指令**：In the Ecosystem Biodiversity presentation: (1) On slide 3, make the title bold and dark green (#006400), and add this note: "Forests cover approximately 31% of the Earth's land surface and host over 80% of terrestrial biodiversity." (2) Set the background of ALL slides to light gray (#D3D3D3).
- **素材文件**：`Ecosystem Mechanisms for Maintaining Biodiversity in Natural Forests.pptx`
- **评估函数**：`compare_pptx_files`
- **Gold 文件**：`Ecosystem_L2.pptx`

#### 任务 L3-23：Tencent Holdings Limited - 2025 Interim Report

- **ID**：`d6ba6b61-5ce3-46c0-90c0-f635d3a1a8eb`
- **来源**：`impress_v3`
- **指令**：In "Tencent Holdings Limited - 2025 Interim Report.pptx": (1) On slide 1, make all text bold, 44pt, and dark blue (#00008B). (2) On slide 3, add this note: "Emphasis: 15% revenue growth demonstrates continued monetization strength. WeChat MAU milestone of 1.41 billion users."
- **素材文件**：`Tencent Holdings Limited - 2025 Interim Report.pptx`
- **评估函数**：`compare_pptx_files`
- **Gold 文件**：`Tencent_L2.pptx`

#### 任务 L3-24：Vincent van Gogh_ A Life of Passion and Color

- **ID**：`d9a2dcc0-9880-4df2-9ee3-b5294f099cb8`
- **来源**：`impress_v3`
- **指令**：In the Van Gogh presentation: (1) Slide 5: body text dark red (#8B0000) and italic. (2) Slide 4: title bold and underlined. (3) Slide 4: add note: "Van Gogh began his artistic career at 27 and produced over 860 oil paintings in just 10 years."
- **素材文件**：`Vincent van Gogh_ A Life of Passion and Color.pptx`
- **评估函数**：`compare_pptx_files`
- **Gold 文件**：`VanGogh_L2.pptx`

#### 任务 L3-25：The Evolution of Rock Music

- **ID**：`dc7809c8-2255-4684-9ac8-d4ebcfcd35be`
- **来源**：`impress_v3`
- **指令**：In "The Evolution of Rock Music.pptx": (1) Right-align the title on ALL slides. (2) On slide 2, add this note: "This presentation covers five major eras of rock: 1950s origins, British Invasion, psychedelic era, heavy metal and punk, and the 90s alternative revolution."
- **素材文件**：`The Evolution of Rock Music.pptx`
- **评估函数**：`compare_pptx_files`
- **Gold 文件**：`RockMusic_L2.pptx`

#### 任务 L3-26：black_concise_work_report_template_english

- **ID**：`dde1349a-4c95-49ee-a1a5-87b1c3529864`
- **来源**：`impress_v3`
- **指令**：In "black_concise_work_report_template_english.pptx": (1) On ALL slides, set titles to 32pt and bold. (2) On slide 2, set background to dark gray (#404040).
- **素材文件**：`black_concise_work_report_template_english.pptx`
- **评估函数**：`compare_pptx_files`
- **Gold 文件**：`BlackWorkReport_L2.pptx`

#### 任务 L3-27：Vincent van Gogh_ A Life of Passion and Color

- **ID**：`eafdd9ea-74a1-47cb-af7d-e8b8a2463111`
- **来源**：`impress_v3`
- **指令**：Open the Van Gogh presentation and do all of the following: (1) Slide 1: background dark blue (#00008B), all text yellow (#FFFF00), bold, 36pt. (2) ALL slides: titles bold and italic. (3) Slide 5: body text dark red (#8B0000) and italic. (4) Slide 4: title underlined (in addition to bold+italic from step 2). (5) Slide 6: add note: "Art historians consider Starry Night, painted during Van Gogh's time at Saint-Remy asylum in June 1889, as one of the most recognized paintings in Western culture." (6) Slide 8: background light gray (#D3D3D3). (7) Slide 9: body text bold and purple (#800080). Save.
- **素材文件**：`Vincent van Gogh_ A Life of Passion and Color.pptx`
- **评估函数**：`compare_pptx_files`
- **Gold 文件**：`VanGogh_L3.pptx`

#### 任务 L3-28：The Golden Age of Arcade Games

- **ID**：`ff469fdc-409b-4ed4-a544-46cb1dfb24c2`
- **来源**：`impress_v3`
- **指令**：Open "The Golden Age of Arcade Games.pptx" and apply: (1) ALL slides: background black (#000000). (2) Slide 1: all text bold, underlined, yellow (#FFFF00), 40pt. (3) ALL slides: title text yellow and bold. (4) Slide 3: body text white (#FFFFFF) and italic. (5) Slide 4: add note: "The arcade industry generated over $8 billion in quarters alone during its peak year of 1982, equivalent to roughly $25 billion in today's currency." (6) Slide 6: body text teal (#008080) and bold. (7) Slide 10: background dark gray (#404040) instead of black. Save.
- **素材文件**：`The Golden Age of Arcade Games.pptx`
- **评估函数**：`compare_pptx_files`
- **Gold 文件**：`ArcadeGames_L3.pptx`

#### L3 任务来源标注

| 任务 | 来源类型 | 具体来源 | 标注理由 |
|------|---------|---------|---------|
| L3-1 | 官方帮助 | [Slide Management](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) + [Editing Text](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | Open "Bitcoin_ The Digital Revolution.pptx". On slide 1, change the color of all |
| L3-2 | 官方帮助 | [Slide Management](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) + [Editing Text](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | Open "Game Theory.pptx" and perform all of the following: (1) On slide 1, set ba |
| L3-3 | 官方帮助 | [Slide Management](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) + [Editing Text](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | Open "The Evolution of Rock Music.pptx" and perform: (1) Slide 1: background bla |
| L3-4 | 官方帮助 | [Slide Management](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) + [Editing Text](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | Open "Ecosystem Mechanisms for Maintaining Biodiversity in Natural Forests.pptx" |
| L3-5 | 官方帮助 | [Slide Management](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) + [Editing Text](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | Open "The Golden Age of Arcade Games.pptx". On slide 1, make all text bold, unde |
| L3-6 | 官方帮助 | [Slide Management](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) + [Editing Text](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | Open "The Evolution of Rock Music.pptx". Change the title font size on ALL slide |
| L3-7 | 官方帮助 | [Slide Management](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) + [Editing Text](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | Open "black_concise_work_report_template_english.pptx" and apply: (1) Slide 1: T |
| L3-8 | 官方帮助 | [Slide Management](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) + [Editing Text](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | In "The Golden Age of Arcade Games.pptx": (1) Set ALL slides background to black |
| L3-9 | 官方帮助 | [Slide Management](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) + [Editing Text](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | Open "work_summary_template_english.pptx" and apply all changes: (1) Slide 1: ti |
| L3-10 | 官方帮助 | [Slide Management](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) + [Editing Text](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | In "Game Theory.pptx": (1) On slide 4, change all body text to italic and dark b |
| L3-11 | 官方帮助 | [Slide Management](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) + [Editing Text](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | In "The Birthday Paradox.pptx": (1) On slide 1, change all text to "Times New Ro |
| L3-12 | 官方帮助 | [Slide Management](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) + [Editing Text](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | Open "Ecosystem Mechanisms for Maintaining Biodiversity in Natural Forests.pptx" |
| L3-13 | 官方帮助 | [Slide Management](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) + [Editing Text](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | Open "Vincent van Gogh_ A Life of Passion and Color.pptx". Make all title text b |
| L3-14 | 官方帮助 | [Slide Management](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) + [Editing Text](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | Open "Game Theory.pptx". On slide 1, set the background to dark blue (#00008B) a |
| L3-15 | 官方帮助 | [Slide Management](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) + [Editing Text](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | In "Bitcoin_ The Digital Revolution.pptx": (1) On slide 1, set the background co |
| L3-16 | 官方帮助 | [Slide Management](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) + [Editing Text](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | Open "work_summary_template_english.pptx". On slide 1, make the title bold, 48pt |
| L3-17 | 官方帮助 | [Slide Management](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) + [Editing Text](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | Open "Bitcoin_ The Digital Revolution.pptx" and perform the following changes: ( |
| L3-18 | 官方帮助 | [Slide Management](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) + [Editing Text](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | Open "black_concise_work_report_template_english.pptx". On slide 1, change all t |
| L3-19 | 官方帮助 | [Slide Management](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) + [Editing Text](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | Open "The Birthday Paradox.pptx" and perform all changes: (1) On slide 1, set al |
| L3-20 | 官方帮助 | [Slide Management](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) + [Editing Text](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | Open the Tencent 2025 Interim Report and perform these changes: (1) On slide 1,  |
| L3-21 | 官方帮助 | [Slide Management](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) + [Editing Text](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | In "work_summary_template_english.pptx": (1) On slide 2, center-align body text  |
| L3-22 | 官方帮助 | [Slide Management](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) + [Editing Text](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | In the Ecosystem Biodiversity presentation: (1) On slide 3, make the title bold  |
| L3-23 | 官方帮助 | [Slide Management](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) + [Editing Text](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | In "Tencent Holdings Limited - 2025 Interim Report.pptx": (1) On slide 1, make a |
| L3-24 | 官方帮助 | [Slide Management](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) + [Editing Text](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | In the Van Gogh presentation: (1) Slide 5: body text dark red (#8B0000) and ital |
| L3-25 | 官方帮助 | [Slide Management](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) + [Editing Text](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | In "The Evolution of Rock Music.pptx": (1) Right-align the title on ALL slides.  |
| L3-26 | 官方帮助 | [Slide Management](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) + [Editing Text](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | In "black_concise_work_report_template_english.pptx": (1) On ALL slides, set tit |
| L3-27 | 官方帮助 | [Slide Management](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) + [Editing Text](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | Open the Van Gogh presentation and do all of the following: (1) Slide 1: backgro |
| L3-28 | 官方帮助 | [Slide Management](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) + [Editing Text](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | Open "The Golden Age of Arcade Games.pptx" and apply: (1) ALL slides: background |

#### L3 任务汇总表

| # | 任务名称 | 素材文件 | 评估函数 |
|---|---------|---------|---------|
| 1 | Bitcoin_ The Digital Revolution | `Bitcoin_ The Digital Revolution.pptx` | `compare_pptx_files`  |
| 2 | Game Theory | `Game Theory.pptx` | `compare_pptx_files`  |
| 3 | The Evolution of Rock Music | `The Evolution of Rock Music.pptx` | `compare_pptx_files`  |
| 4 | Ecosystem Mechanisms for Maintaining Biodiversity in Natural Forests | `Ecosystem Mechanisms for Maintaining Biodiversity in Natural Forests.pptx` | `compare_pptx_files`  |
| 5 | The Golden Age of Arcade Games | `The Golden Age of Arcade Games.pptx` | `compare_pptx_files`  |
| 6 | The Evolution of Rock Music | `The Evolution of Rock Music.pptx` | `compare_pptx_files`  |
| 7 | black_concise_work_report_template_english | `black_concise_work_report_template_english.pptx` | `compare_pptx_files`  |
| 8 | The Golden Age of Arcade Games | `The Golden Age of Arcade Games.pptx` | `compare_pptx_files`  |
| 9 | work_summary_template_english | `work_summary_template_english.pptx` | `compare_pptx_files`  |
| 10 | Game Theory | `Game Theory.pptx` | `compare_pptx_files`  |
| 11 | The Birthday Paradox | `The Birthday Paradox.pptx` | `compare_pptx_files`  |
| 12 | Ecosystem Mechanisms for Maintaining Biodiversity in Natural Forests | `Ecosystem Mechanisms for Maintaining Biodiversity in Natural Forests.pptx` | `compare_pptx_files`  |
| 13 | Vincent van Gogh_ A Life of Passion and Color | `Vincent van Gogh_ A Life of Passion and Color.pptx` | `compare_pptx_files`  |
| 14 | Game Theory | `Game Theory.pptx` | `compare_pptx_files`  |
| 15 | Bitcoin_ The Digital Revolution | `Bitcoin_ The Digital Revolution.pptx` | `compare_pptx_files`  |
| 16 | work_summary_template_english | `work_summary_template_english.pptx` | `compare_pptx_files`  |
| 17 | Bitcoin_ The Digital Revolution | `Bitcoin_ The Digital Revolution.pptx` | `compare_pptx_files`  |
| 18 | black_concise_work_report_template_english | `black_concise_work_report_template_english.pptx` | `compare_pptx_files`  |
| 19 | The Birthday Paradox | `The Birthday Paradox.pptx` | `compare_pptx_files`  |
| 20 | Tencent Holdings Limited - 2025 Interim Report | `Tencent Holdings Limited - 2025 Interim Report.pptx` | `compare_pptx_files`  |
| 21 | work_summary_template_english | `work_summary_template_english.pptx` | `compare_pptx_files`  |
| 22 | Ecosystem Mechanisms for Maintaining Biodiversity in Natural Forests | `Ecosystem Mechanisms for Maintaining Biodiversity in Natural Forests.pptx` | `compare_pptx_files`  |
| 23 | Tencent Holdings Limited - 2025 Interim Report | `Tencent Holdings Limited - 2025 Interim Report.pptx` | `compare_pptx_files`  |
| 24 | Vincent van Gogh_ A Life of Passion and Color | `Vincent van Gogh_ A Life of Passion and Color.pptx` | `compare_pptx_files`  |
| 25 | The Evolution of Rock Music | `The Evolution of Rock Music.pptx` | `compare_pptx_files`  |
| 26 | black_concise_work_report_template_english | `black_concise_work_report_template_english.pptx` | `compare_pptx_files`  |
| 27 | Vincent van Gogh_ A Life of Passion and Color | `Vincent van Gogh_ A Life of Passion and Color.pptx` | `compare_pptx_files`  |
| 28 | The Golden Age of Arcade Games | `The Golden Age of Arcade Games.pptx` | `compare_pptx_files`  |

---

### 3.4 Interactive 任务（Impress 交互式）—— 25 个

> 交互式任务使用多阶段 phase 设计，通过 `trigger` 控制阶段切换。


#### 场景类型：`ambiguous_detail`（模糊细节）—— 4 个

> **来源类型**：现实场景构造 | **真实工作来源**：演示设计细节不明
> **证据描述**：收到"让这个演示看起来更好"但未指定颜色/字体/布局

##### interactive_impress_003（L3）

- **场景描述**：The user says to update the cover page but doesn't specify what. The agent asks, then changes the year from '2019' to '2025'.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `agent_asks`）：Help me update the cover page
  - Phase 2（trigger: `agent_done`）：Change the year '2019' on the cover to '2025', then save

##### interactive_impress_009（L3）

- **场景描述**：The user says to add a conclusion but doesn't specify the content. The agent asks, then appends text to the last slide.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `agent_asks`）：Help me add a conclusion
  - Phase 2（trigger: `agent_done`）：At the end of the last slide, add 'Game theory provides tools for strategic decision-making.', then save

##### interactive_impress_015（L3）

- **场景描述**：The user says to add presenter info but doesn't specify the content. The agent asks, then adds the department name on the last slide.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `agent_asks`）：Help me add presenter info
  - Phase 2（trigger: `agent_done`）：On the last slide, add 'Presented by: Music History Department', then save

##### interactive_impress_017（L3）

- **场景描述**：The user says to add some key information but doesn't specify what. The agent asks, then adds a summary statement on the last slide.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `agent_asks`）：Help me add some key info to the slides
  - Phase 2（trigger: `agent_done`）：On the last slide, add 'The arcade era transformed gaming culture forever.', then save


#### 场景类型：`ambiguous_scope`（模糊范围）—— 3 个

> **来源类型**：现实场景构造 | **真实工作来源**：演示修改范围不确定
> **证据描述**：收到"调整一下内容"但未指定涉及哪些页面

##### interactive_impress_007（L2）

- **场景描述**：The user says to add a reference on some slide but doesn't specify which. The agent asks, then adds it only on the last slide.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `agent_asks`）：Help me add a reference on one of the slides
  - Phase 2（trigger: `agent_done`）：Only add 'Reference: Smith et al., 2024' on the last slide, leave other slides unchanged, then save

##### interactive_impress_013（L2）

- **场景描述**：The user says to add author info but doesn't specify which slide. The agent asks, then adds it only on the first slide.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `agent_asks`）：Help me add author info to the slides
  - Phase 2（trigger: `agent_done`）：Only add 'Author: Dr. Sarah Chen' on the first slide, leave other slides unchanged, then save

##### interactive_impress_019（L3）

- **场景描述**：The user says to add copyright info but doesn't specify which slide. The agent asks, then adds it only on the last slide.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `agent_asks`）：Help me add copyright info to one of the slides
  - Phase 2（trigger: `agent_done`）：Only add '(c) Art History Department 2025' on the last slide, leave other slides unchanged, then save


#### 场景类型：`ambiguous_target`（模糊目标）—— 3 个

> **来源类型**：现实场景构造 | **真实工作来源**：模糊的演示文稿修改
> **证据描述**：收到"帮我改下这个 PPT"但未指定改哪些幻灯片

##### interactive_impress_001（L2）

- **场景描述**：The user says to change a title but doesn't say which one. The agent asks, then changes the first slide's 'Fashion Summary' to 'Annual Work Summary'.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `agent_asks`）：Help me change that title
  - Phase 2（trigger: `agent_done`）：Change 'Fashion Summary' on the first slide to 'Annual Work Summary', then save

##### interactive_impress_005（L3）

- **场景描述**：The user says to add a note on some slide but doesn't specify which. The agent asks, then adds a disclaimer on the last slide.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `agent_asks`）：Help me add a note on one of the slides
  - Phase 2（trigger: `agent_done`）：On the last slide, add 'This presentation is for educational purposes only.', then save

##### interactive_impress_011（L3）

- **场景描述**：The user says to change the report type but doesn't specify the field. The agent asks, then changes 'Interim Report' to 'Annual Report' on the cover.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `agent_asks`）：Help me change that report type
  - Phase 2（trigger: `agent_done`）：Change 'Interim Report' on the cover to 'Annual Report', then save


#### 场景类型：`error_correction`（错误纠正）—— 2 个

> **来源类型**：现实场景构造 | **真实工作来源**：演示错误修正
> **证据描述**：发现标题/内容/排版错误后要求修正

##### interactive_impress_error_correction_001（L3）

- **场景描述**：User asks to modify text on 'the last slide' but agent modifies the wrong one. User corrects with the specific slide number.
- **阶段数**：3
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=5））：Add the text 'Presented by: Music History Dept.' on the last slide
  - Phase 2（trigger: `agent_done`）：Hmm, that doesn't look right. I think you added it to the wrong place. Please make sure 'Presented by: Music History Dept.' appears as a text box at t
  - Phase 3（trigger: `agent_done`）：Now also add 'Thank You!' as the main title text on that same last slide. Save the file.

##### interactive_impress_error_correction_002（L3）

- **场景描述**：User asks agent to add a slide. Agent adds it but with wrong content. User provides the correct text.
- **阶段数**：3
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=5））：Add a new slide at the end with some conclusion text
  - Phase 2（trigger: `agent_done`）：That conclusion doesn't capture what I want. Please replace it with: Title: 'Legacy of Arcade Gaming', Content: 'The arcade era established the founda
  - Phase 3（trigger: `agent_done`）：Good. Now also add 'Sources: ESA Annual Report 2024' at the bottom of that slide. Save.


#### 场景类型：`multi_step_workflow`（多步工作流）—— 1 个

> **来源类型**：现实场景构造 | **真实工作来源**：完整演示制作工作流
> **证据描述**：从内容编辑、格式设置到过渡动画的完整链路

##### interactive_impress_workflow_001（L3）

- **场景描述**：Multi-step workflow: the user guides the agent through several coordinated actions or phases.
- **阶段数**：4
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `agent_done`）：Please open MyPresentation.pptx on the desktop and change the title of the first slide to "Project Report"
  - Phase 2（trigger: `agent_done`）：Okay, now add a subtitle below the title on the first slide, writing "Q1 2025"
  - Phase 3（trigger: `agent_done`）：Then create a new slide and give it the title "Project Progress"
  - Phase 4（trigger: `agent_done`）：Finally, please save the entire presentation


#### 场景类型：`progressive_refinement`（渐进精化）—— 6 个

> **来源类型**：现实场景构造 | **真实工作来源**：分阶段演示制作
> **证据描述**：先做内容确认，再逐步加入设计/动画/过渡

##### interactive_impress_002（L2）

- **场景描述**：The user first asks to add a summary slide at the end, then asks to fill in specific content.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me add a summary slide at the end
  - Phase 2（trigger: `agent_done`）：On the new slide, add the title 'Q4 Summary' and the content 'Revenue target achieved.', then save

##### interactive_impress_008（L3）

- **场景描述**：The user first asks to add a new slide at the end, then asks to fill in the title and content.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me add a new slide at the end
  - Phase 2（trigger: `agent_done`）：On the new slide, add the title 'Conservation Implications' and the content 'Protecting biodiversity is essential.', then save

##### interactive_impress_010（L3）

- **场景描述**：The user first asks to change the first slide's title, then asks to change the subtitle.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me change the first slide's title from 'Game Theory' to 'Introduction to Game Theory'
  - Phase 2（trigger: `agent_done`）：Done. Now change the subtitle to 'A Mathematical Approach to Strategy', then save

##### interactive_impress_014（L3）

- **场景描述**：The user first asks to add a summary slide at the end, then asks to fill in the key takeaway.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me add a summary slide at the end
  - Phase 2（trigger: `agent_done`）：On the summary slide, add 'Key Takeaway: Even unlikely events become probable over many trials.', then save

##### interactive_impress_016（L3）

- **场景描述**：The user first asks to add an ending slide, then asks to fill in the closing statement.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me add an ending slide at the end
  - Phase 2（trigger: `agent_done`）：On the ending slide, add 'Rock music remains a powerful force in modern culture.', then save

##### interactive_impress_020（L3）

- **场景描述**：The user first asks to add a 'Legacy' slide, then asks to fill in the body text.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me add a new slide at the end with the title 'Legacy'
  - Phase 2（trigger: `agent_done`）：On the Legacy slide, add the body text 'Van Gogh influenced generations of artists.', then save


#### 场景类型：`requirement_change`（需求变更）—— 4 个

> **来源类型**：现实场景构造 | **真实工作来源**：演示需求变更
> **证据描述**：制作到一半被要求调整配色方案或增删幻灯片

##### interactive_impress_004（L2）

- **场景描述**：The user first asks to add 'Prepared by: Team A' on the first slide, then changes it to the more detailed 'Prepared by: Analytics Team A'.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me add 'Prepared by: Team A' on the first slide
  - Phase 2（trigger: `agent_done`）：Change it to 'Prepared by: Analytics Team A' instead, that's more complete, then save

##### interactive_impress_006（L3）

- **场景描述**：The user first adds 'Prepared by: Research Team', then changes it to the more detailed 'Prepared by: Blockchain Research Team'.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me add 'Prepared by: Research Team' on the last slide
  - Phase 2（trigger: `agent_done`）：Change it to 'Prepared by: Blockchain Research Team' instead, more specific, then save

##### interactive_impress_012（L3）

- **场景描述**：The user first asks to add 'For internal use only.' on the last slide, then changes it to the more professional 'For authorized personnel only.'.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me add 'For internal use only.' on the last slide
  - Phase 2（trigger: `agent_done`）：Make it more professional, change it to 'For authorized personnel only.', then save

##### interactive_impress_018（L3）

- **场景描述**：The user first asks to add 'The End', then changes it to the more formal 'Thank You for Your Attention'.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me add 'The End' on the last slide
  - Phase 2（trigger: `agent_done`）：Change it to 'Thank You for Your Attention' instead, more formal, then save


#### 场景类型：`task_interruption`（任务中断）—— 2 个

> **来源类型**：现实场景构造 | **真实工作来源**：演示编辑中断
> **证据描述**：编辑过程中被告知需要额外添加备注或修改已完成部分

##### interactive_impress_interruption_001（L3）

- **场景描述**：User asks agent to modify slide titles, then interrupts to check the file size, then asks to continue adding content.
- **阶段数**：3
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Change the title on slide 1 to 'Introduction to Game Theory'
  - Phase 2（trigger: `agent_done`）：Wait - can you check the file size of this presentation? Use 'ls -lh' in a terminal to see how big the file is on Desktop
  - Phase 3（trigger: `agent_done`）：OK, now go back to the presentation and add a new slide at the end with the title 'Key Takeaways' and the text 'Game theory helps us understand strate

##### interactive_impress_interruption_002（L3）

- **场景描述**：User asks agent to add speaker notes, then interrupts to organize files on Desktop, then asks to continue with slide transitions.
- **阶段数**：3
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Add speaker notes to slide 1: 'Welcome the audience and introduce the topic of probability.'
  - Phase 2（trigger: `agent_done`）：Actually, before continuing - can you create a folder called 'Presentations' on the Desktop and move this pptx file there?
  - Phase 3（trigger: `agent_done`）：Now open the file from its new location and add 'Author: Dr. Sarah Chen' as text on the first slide. Save.

#### Interactive 任务来源映射

| 场景类型 | 任务数 | 真实工作来源 | 证据描述 | trigger 组合 |
|---------|-------|------------|---------|------------|
| `ambiguous_detail`（模糊细节） | 4 | 演示设计细节不明 | 收到"让这个演示看起来更好"但未指定颜色/字体/布局 | agent_asks + agent_done |
| `ambiguous_scope`（模糊范围） | 3 | 演示修改范围不确定 | 收到"调整一下内容"但未指定涉及哪些页面 | agent_asks + agent_done |
| `ambiguous_target`（模糊目标） | 3 | 模糊的演示文稿修改 | 收到"帮我改下这个 PPT"但未指定改哪些幻灯片 | agent_asks + agent_done |
| `error_correction`（错误纠正） | 2 | 演示错误修正 | 发现标题/内容/排版错误后要求修正 | agent_done + step_count |
| `multi_step_workflow`（多步工作流） | 1 | 完整演示制作工作流 | 从内容编辑、格式设置到过渡动画的完整链路 | agent_done |
| `progressive_refinement`（渐进精化） | 6 | 分阶段演示制作 | 先做内容确认，再逐步加入设计/动画/过渡 | agent_done + step_count |
| `requirement_change`（需求变更） | 4 | 演示需求变更 | 制作到一半被要求调整配色方案或增删幻灯片 | agent_done + step_count |
| `task_interruption`（任务中断） | 2 | 演示编辑中断 | 编辑过程中被告知需要额外添加备注或修改已完成部分 | agent_done + step_count |

#### Interactive 触发类型分布

| 触发类型 | 中文 | 出现次数 | 说明 |
|---------|------|---------|------|
| `agent_done` | 代理完成 | 32 | 上一阶段完成后自动进入下一阶段 |
| `step_count` | 步数触发 | 14 | 达到指定步数后注入新指令 |
| `agent_asks` | 代理追问 | 10 | agent 主动向用户追问澄清后触发 |

#### Interactive 任务来源映射

| 场景类型 | 真实工作来源 | 证据包（最小） | Task JSON `source` 建议写法 |
|---------|-------------|-------------|--------------------------|
| `ambiguous_target` | 模糊的 PPT 修改需求 | ① 原始需求 ② 追问记录 ③ 执行 | `impress_interactive;source_type=slide_edit;evidence=ambiguous_target` |
| `progressive_refinement` | 分阶段 PPT 制作（先大纲→再排版→最后动画） | ① 阶段确认 ② 精化指令 ③ 最终验收 | `impress_interactive;source_type=presentation;evidence=staged_refinement` |
| `requirement_change` | PPT 制作中途需求变更 | ① 初始需求 ② 变更指令 ③ 差异记录 | `impress_interactive;source_type=change;evidence=requirement_change` |
| `error_correction` | 幻灯片格式纠正 | ① 错误描述 ② 纠正指令 ③ 验证 | `impress_interactive;source_type=format_fix;evidence=error_correction` |

#### 来源证据落地字段（建议统一）

- **source_type**：`slide_edit` / `presentation` / `change` / `format_fix` / `animation` / `transition`
- **source_ref**：来源标识（匿名化 URL、工单号、访谈记录编号）
- **captured_at**：取证日期（`YYYY-MM-DD`）
- **anonymized_excerpt**：匿名化原文摘录（1~3 句）
- **mapping_note**：原始需求如何映射到 `phases` 与 `trigger`
- **reviewers**：双人审核与仲裁记录（`reviewer_a/reviewer_b/adjudicator`）

---

## 4. 评估函数汇总

| # | 函数名 | 类别 | 使用次数 |
|---|--------|------|---------|
| 1 | `compare_pptx_files` | 静态任务 | 28 |
| 2 | `check_transition` | 静态任务 | 1 |
| 3 | `check_slide_orientation_Portrait` | 静态任务 | 1 |
| 4 | `check_include_exclude` | 交互任务 | 25 |

**总计**：覆盖 30 个静态任务 + 25 个交互任务 = **55** 个任务。

---

## 5. 素材说明

### 技术规格

| 属性 | 值 |
|------|-----|
| 文件格式 | `.pptx`（Office Open XML Presentation） |
| 静态任务初始文件 | 10 个独立 `.pptx` 模板（部分共享） |
| Gold 文件 | 30 个 gold `.pptx` 文件（含不同难度变体） |
| 语言 | 英文内容为主 |
| 主题 | Bitcoin、Game Theory、Rock Music、Arcade Games、Ecosystem、Work Report 等 |

---

## 6. Task JSON 模板

### 静态任务（compare_pptx_files）

```json
{
  "id": "<uuid4>",
  "snapshot": "libreoffice_impress",
  "instruction": "<操作指令>",
  "config": [
    {"type": "upload_file", "parameters": {"files": [{"local_path": "cache/<id>/<file>.pptx", "path": "/home/user/<file>.pptx"}]}},
    {"type": "open", "parameters": {"path": "/home/user/<file>.pptx"}}
  ],
  "evaluator": {
    "postconfig": [
      {"type": "activate_window", "parameters": {"window_name": "<file>.pptx", "strict": false}},
      {"type": "execute", "parameters": {"command": ["python", "-c", "import pyautogui, time; pyautogui.hotkey('ctrl','s'); time.sleep(1.5); pyautogui.press('return');"]}}
    ],
    "func": "compare_pptx_files",
    "expected": {"type": "cache_file", "path": "<gold>.pptx"},
    "result": {"type": "vm_file", "path": "/home/user/<file>.pptx", "dest": "<file>.pptx"},
    "options": {"examine_shape": true}
  },
  "difficulty": "L3"
}
```

### 属性检查任务（check_transition / check_slide_orientation）

```json
{
  "evaluator": {
    "func": "check_transition",
    "result": {"type": "vm_file", "path": "/home/user/<file>.pptx", "dest": "<file>.pptx"},
    "expected": {"type": "rule", "rules": {"transition_type": "fade", "slide_index": 0}}
  }
}
```

---

## 7. Docker 镜像要求

- **LibreOffice Impress**（推荐 7.x+）
- **X11 显示环境**
- **Python 3 + python-pptx**（评估器）
  ```bash
  pip install python-pptx
  ```

---

## 8. 任务难度分布总结

| 级别 | 数量 | 指令长度 | 操作步骤 | 描述 | 示例 |
|------|------|---------|---------|------|------|
| L1 | 9 | 80-129 字符 | 1-2 步 | 单步操作 | 添加过渡效果、标题字号修改、单页字体/颜色、幻灯片方向 |
| L2 | 9 | 153-295 字符 | 2-3 步（带 2 子步骤） | 多步操作 | 正文居中+标题设置、全片标题+单页背景、双操作组合 |
| L3 | 12 | 243-668 字符 | 5-7 步（带编号子步骤） | 复杂工作流 | 多页修改+背景+字体+颜色+备注+删除页面（7 步组合） |
| **总计** | **30** | | | | |

### 可验证性保证

1. **`.pptx` 结构化对比**：使用 `python-pptx` 对比幻灯片数量、形状几何、文本内容、字体、颜色等。不依赖截图或 OCR。
2. **属性级验证**：`check_transition` 和 `check_slide_orientation_Portrait` 直接验证 XML 属性。
3. **多维度检查**：`examine_shape`/`examine_text`/`examine_font` 等选项提供细粒度控制。

> 难度标签基于 kimi-k2.5 模型在 max_steps=50（静态）/ max_steps=80（交互）条件下的实际执行结果。

---

## 9. 常见陷阱

### LibreOffice Impress 特有问题
- **形状 ID 变化**：LibreOffice 保存后可能重新分配形状 ID，评估需使用位置/内容匹配而非 ID 匹配。
- **过渡效果名称**：LibreOffice 与 PowerPoint 使用不同的过渡效果内部名称。
- **背景颜色格式**：RGB 值可能存在 `#RRGGBB` vs `(R,G,B)` 的格式差异。

### 保存对话框
- `.pptx` 保存时同样需要处理格式确认对话框（`Ctrl+S` + `Enter`）。

### Gold 文件管理
- Impress gold 文件必须同时存在于 `OSWorld/cache/<task_id>/` 和 `desktopworld/cache/<task_id>/`。
- 部分任务使用同一初始文件但不同 gold 文件（如 `The Evolution of Rock Music.pptx` 有 L1/L3 两个 gold 变体）。
