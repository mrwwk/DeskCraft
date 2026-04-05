# LibreOffice Writer 任务设计文档

## 0. LibreOffice Writer 验证策略

### Writer 路径

评测虚拟机中 LibreOffice Writer 通过系统预装，**启动方式为 `libreoffice --writer <文件路径>`** 或通过 config 中 `open` 动作直接打开指定 `.docx` 文件。

### 核心思路

LibreOffice Writer 的验证通过将 VM 中用户编辑后的 `.docx` 文件下载到本地，与预制的 gold 标准文件进行全文对比实现。

1. **文档全文对比**（`compare_docx_files`）：使用 `python-docx` 解析 `.docx` 文件，逐段落比较文本内容。默认启用 `ignore_blanks`（忽略多余空白），支持可选的模糊匹配、忽略大小写、忽略顺序等模式。

**评估器架构**：通过 `vm_file` getter 从 VM 下载编辑后文件，从 cache 加载 `_gold.docx` 文件，在本地进行对比判定。

### 评估器通用模式

```python
def compare_docx_files(file1, file2, **options):
    """
    参数：
        file1: 从 VM 下载的用户编辑后 .docx 文件路径
        file2: 预制的 gold 标准 .docx 文件路径
        options: ignore_blanks=True, ignore_case, ignore_order, content_only, fuzzy_match
    返回：
        1.0（匹配）或 0.0（不匹配）
    """
```

---

## 1. 可用资源

总计：**20** 个初始文件 + 对应 gold 标准文件

### writer_hard 素材（20 个任务）

| # | 初始文件 | Gold 文件 | 任务概要 |
|---|---------|----------|--------|
| 1 | `Meeting_L2_03.docx` | `Meeting_L2_03_gold.docx` | Open "Meeting_L2_03.docx". Apply strikethrough formatting to the last ... |
| 2 | `Policy_L2_04.docx` | `Policy_L2_04_gold.docx` | Open "Policy_L2_04.docx". Set the font size of all body text to 12pt. ... |
| 3 | `Guide_L2_05.docx` | `Guide_L2_05_gold.docx` | Open "Guide_L2_05.docx". Replace all occurrences of "TechVision Inc." ... |
| 4 | `Policy_L2_09.docx` | `Policy_L2_09_gold.docx` | Open "Policy_L2_09.docx". Add the following paragraph at the very begi... |
| 5 | `Report_L2_01.docx` | `Report_L2_01_gold.docx` | Open "Report_L2_01.docx". Change the font of all body text (non-headin... |
| 6 | `Report_L3_06.docx` | `Report_L3_06_gold.docx` | Open "Report_L3_06.docx" and do ALL: (1) Center title, set to 22pt, bo... |
| 7 | `Meeting_L3_08.docx` | `Meeting_L3_08_gold.docx` | Open "Meeting_L3_08.docx" and do ALL: (1) Center the title, 18pt, bold... |
| 8 | `Guide_L3_10.docx` | `Guide_L3_10_gold.docx` | Open "Guide_L3_10.docx" and do ALL: (1) Replace "TechVision Inc." with... |
| 9 | `Meeting_L3_03.docx` | `Meeting_L3_03_gold.docx` | Open "Meeting_L3_03.docx" and do ALL: (1) Center the title and set to ... |
| 10 | `Proposal_L3_07.docx` | `Proposal_L3_07_gold.docx` | Open "Proposal_L3_07.docx" and do ALL: (1) Replace "Q1 2025" with "Fir... |
| 11 | `Policy_L3_09.docx` | `Policy_L3_09_gold.docx` | Open "Policy_L3_09.docx" and do ALL: (1) Center title, 22pt, bold, dar... |
| 12 | `Proposal_L3_02.docx` | `Proposal_L3_02_gold.docx` | Open "Proposal_L3_02.docx" and do ALL: (1) Center-align the title and ... |
| 13 | `Proposal_L2_07.docx` | `Proposal_L2_07_gold.docx` | Open "Proposal_L2_07.docx". Change the color of all heading text to da... |
| 14 | `Report_L2_06.docx` | `Report_L2_06_gold.docx` | Open "Report_L2_06.docx". Center-align the document title. After the p... |
| 15 | `Report_L3_01.docx` | `Report_L3_01_gold.docx` | Open "Report_L3_01.docx" and perform ALL: (1) Center-align the documen... |
| 16 | `Meeting_L2_08.docx` | `Meeting_L2_08_gold.docx` | Open "Meeting_L2_08.docx". Replace all occurrences of "Q1" with "First... |
| 17 | `Proposal_L2_02.docx` | `Proposal_L2_02_gold.docx` | Open "Proposal_L2_02.docx". Center-align the document title (first lin... |
| 18 | `Policy_L3_04.docx` | `Policy_L3_04_gold.docx` | Open "Policy_L3_04.docx" and do ALL: (1) Center title, set to 22pt bol... |
| 19 | `Guide_L2_10.docx` | `Guide_L2_10_gold.docx` | Open "Guide_L2_10.docx". Change the title (first line) font size to 24... |
| 20 | `Guide_L3_05.docx` | `Guide_L3_05_gold.docx` | Open "Guide_L3_05.docx" and do ALL: (1) Replace "TechVision Inc." with... |

---

## 2. 评估函数设计

文件：`desktop_env/evaluators/metrics/docs.py`

### 2.1 主评估函数

| 函数名 | 描述 | 使用次数 |
|--------|------|---------|
| `compare_docx_files` | 结构化对比两个 .docx 文件（文本内容、段落格式） | 20 |

---

## 3. 任务定义


### 3.1 第一级（L1）—— 基础操作 —— 2 个

> agent 在实测中 10 步内完成且得分 1.0 的任务

#### 任务 L1-1：Meeting_L2_03

- **ID**：`0348a68c-a33e-47e9-9e07-d189c43e9bec`
- **来源**：`writer_hard`
- **指令**：Open "Meeting_L2_03.docx". Apply strikethrough formatting to the last action item (the one starting with "Tom:"). Then add the following paragraph at the end of the document: "Summary: All Q1 targets were met or exceeded. The team will focus on scaling operations and executing the Q2 product roadmap. Next review meeting scheduled for April 25."
- **素材文件**：`Meeting_L2_03.docx`
- **评估函数**：`compare_docx_files`
- **Gold 文件**：`Meeting_L2_03_gold.docx`

#### 任务 L1-2：Proposal_L2_02

- **ID**：`aaa6abac-4bde-47ea-805a-08da32e7a1e1`
- **来源**：`writer_hard`
- **指令**：Open "Proposal_L2_02.docx". Center-align the document title (first line). Insert a page break immediately before the "Budget" heading.
- **素材文件**：`Proposal_L2_02.docx`
- **评估函数**：`compare_docx_files`
- **Gold 文件**：`Proposal_L2_02_gold.docx`

#### L1 任务来源标注

| 任务 | 来源类型 | 具体来源 | 标注理由 |
|------|---------|---------|---------|
| L1-1 | 官方帮助 | [Writer Guide](https://help.libreoffice.org/latest/en-US/text/swriter/guide/main.html) | Open "Meeting_L2_03.docx". Apply strikethrough formatting to the last action ite |
| L1-2 | 官方帮助 | [Text Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) + [Paragraph Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) | Open "Proposal_L2_02.docx". Center-align the document title (first line). Insert |

#### L1 任务汇总表

| # | 任务名称 | 素材文件 | 评估函数 |
|---|---------|---------|---------|
| 1 | Meeting_L2_03 | `Meeting_L2_03.docx` | `compare_docx_files`  |
| 2 | Proposal_L2_02 | `Proposal_L2_02.docx` | `compare_docx_files`  |


### 3.2 第二级（L2）—— 复合操作 —— 3 个

> agent 在 25 步内完成（得分 1.0）或 10 步内失败的任务

#### 任务 L2-1：Guide_L2_05

- **ID**：`212c971d-6afa-4d9e-9ad8-11fe74fb692d`
- **来源**：`writer_hard`
- **指令**：Open "Guide_L2_05.docx". Replace all occurrences of "TechVision Inc." with "InnovateTech Corp." Also make all "Week" section headings bold.
- **素材文件**：`Guide_L2_05.docx`
- **评估函数**：`compare_docx_files`
- **Gold 文件**：`Guide_L2_05_gold.docx`

#### 任务 L2-2：Meeting_L2_08

- **ID**：`a10c5680-643f-4446-805f-e2e749efff6e`
- **来源**：`writer_hard`
- **指令**：Open "Meeting_L2_08.docx". Replace all occurrences of "Q1" with "First Quarter" throughout the document. Also make the attendees list paragraph bold.
- **素材文件**：`Meeting_L2_08.docx`
- **评估函数**：`compare_docx_files`
- **Gold 文件**：`Meeting_L2_08_gold.docx`

#### 任务 L2-3：Guide_L2_10

- **ID**：`ddc06ab7-075d-47e8-8d70-c88b88605ddf`
- **来源**：`writer_hard`
- **指令**：Open "Guide_L2_10.docx". Change the title (first line) font size to 24pt. Add this paragraph at the end: "For more information, contact HR at hr@techvision.com or visit the employee portal at https://portal.techvision.com"
- **素材文件**：`Guide_L2_10.docx`
- **评估函数**：`compare_docx_files`
- **Gold 文件**：`Guide_L2_10_gold.docx`

#### L2 任务来源标注

| 任务 | 来源类型 | 具体来源 | 标注理由 |
|------|---------|---------|---------|
| L2-1 | 官方帮助 | [Text Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) | Open "Guide_L2_05.docx". Replace all occurrences of "TechVision Inc." with "Inno |
| L2-2 | 官方帮助 | [Text Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) + [Lists and Numbering](https://help.libreoffice.org/latest/en-US/text/swriter/guide/using_numbering.html) | Open "Meeting_L2_08.docx". Replace all occurrences of "Q1" with "First Quarter"  |
| L2-3 | 官方帮助 | [Text Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) | Open "Guide_L2_10.docx". Change the title (first line) font size to 24pt. Add th |

#### L2 任务汇总表

| # | 任务名称 | 素材文件 | 评估函数 |
|---|---------|---------|---------|
| 1 | Guide_L2_05 | `Guide_L2_05.docx` | `compare_docx_files`  |
| 2 | Meeting_L2_08 | `Meeting_L2_08.docx` | `compare_docx_files`  |
| 3 | Guide_L2_10 | `Guide_L2_10.docx` | `compare_docx_files`  |


### 3.3 第三级（L3）—— 高级工作流 —— 15 个

> agent 无法完成或需要大量步骤（>25 步）的任务

#### 任务 L3-1：Policy_L2_04

- **ID**：`1cd80191-f69d-4d57-9197-e10d0c8fbbce`
- **来源**：`writer_hard`
- **指令**：Open "Policy_L2_04.docx". Set the font size of all body text to 12pt. Additionally, make the body text under section "5. Communication Standards" italic.
- **素材文件**：`Policy_L2_04.docx`
- **评估函数**：`compare_docx_files`
- **Gold 文件**：`Policy_L2_04_gold.docx`

#### 任务 L3-2：Policy_L2_09

- **ID**：`247db8e9-9fd2-49a6-85f9-b53854f64c47`
- **来源**：`writer_hard`
- **指令**：Open "Policy_L2_09.docx". Add the following paragraph at the very beginning of the document: "DISCLAIMER: This policy is subject to change. Employees should check the HR portal for the latest version." Also convert all section heading text to uppercase.
- **素材文件**：`Policy_L2_09.docx`
- **评估函数**：`compare_docx_files`
- **Gold 文件**：`Policy_L2_09_gold.docx`

#### 任务 L3-3：Report_L2_01

- **ID**：`271a9bcb-ce39-4cdb-90ae-569776e78eaa`
- **来源**：`writer_hard`
- **指令**：Open "Report_L2_01.docx". Change the font of all body text (non-heading paragraphs) to "Times New Roman". Also make all heading text bold.
- **素材文件**：`Report_L2_01.docx`
- **评估函数**：`compare_docx_files`
- **Gold 文件**：`Report_L2_01_gold.docx`

#### 任务 L3-4：Report_L3_06

- **ID**：`2b672d35-1c0f-4a71-bb85-f32b5ad8b46d`
- **来源**：`writer_hard`
- **指令**：Open "Report_L3_06.docx" and do ALL: (1) Center title, set to 22pt, bold, dark blue (#003366). (2) Make all section headings bold and underlined. (3) Set all body text to Calibri 11pt. (4) Make the paragraph starting with "For 2026" both bold and italic. (5) Add "--- End of Report ---" as the last paragraph.
- **素材文件**：`Report_L3_06.docx`
- **评估函数**：`compare_docx_files`
- **Gold 文件**：`Report_L3_06_gold.docx`

#### 任务 L3-5：Meeting_L3_08

- **ID**：`3cf4aa78-196b-4654-a632-7f8c0b52c8e1`
- **来源**：`writer_hard`
- **指令**：Open "Meeting_L3_08.docx" and do ALL: (1) Center the title, 18pt, bold. (2) Center-align the attendees list paragraph. (3) Make all section headings underlined and bold. (4) Bold all action item lines (starting with names + colon). (5) Set all body text font to "Arial". (6) Add at end: "Recorded by: Meeting Secretary | Distribution: All attendees + Board"
- **素材文件**：`Meeting_L3_08.docx`
- **评估函数**：`compare_docx_files`
- **Gold 文件**：`Meeting_L3_08_gold.docx`

#### 任务 L3-6：Guide_L3_10

- **ID**：`3dad2051-0596-4886-93c5-9ed78df81f99`
- **来源**：`writer_hard`
- **指令**：Open "Guide_L3_10.docx" and do ALL: (1) Replace "TechVision Inc." with "GlobalTech Solutions". (2) Center title, set to 26pt, bold, dark green (#006400). (3) Make all section headings bold and 16pt. (4) Set all body text to Georgia 11pt. (5) Bold the body text under "Week 1: Getting Started". (6) Add at end: "Last updated: March 2025 | Next revision: September 2025"
- **素材文件**：`Guide_L3_10.docx`
- **评估函数**：`compare_docx_files`
- **Gold 文件**：`Guide_L3_10_gold.docx`

#### 任务 L3-7：Meeting_L3_03

- **ID**：`409f8738-31ec-406f-898f-01ed419b74b4`
- **来源**：`writer_hard`
- **指令**：Open "Meeting_L3_03.docx" and do ALL: (1) Center the title and set to 20pt. (2) Replace "Q1" with "First Quarter" and "Q2" with "Second Quarter" everywhere. (3) Bold the attendees list paragraph. (4) Italic all action item paragraphs (lines starting with names followed by colon). (5) Change all section headings to dark blue (#003366). (6) Add "--- End of Meeting Minutes ---" at the end.
- **素材文件**：`Meeting_L3_03.docx`
- **评估函数**：`compare_docx_files`
- **Gold 文件**：`Meeting_L3_03_gold.docx`

#### 任务 L3-8：Proposal_L3_07

- **ID**：`43b0833a-2da6-43e7-a8e3-93790bc2579a`
- **来源**：`writer_hard`
- **指令**：Open "Proposal_L3_07.docx" and do ALL: (1) Replace "Q1 2025" with "First Quarter 2025", "Q2-Q3 2025" with "Second-Third Quarter 2025", "Q4 2025" with "Fourth Quarter 2025", "Q1 2026" with "First Quarter 2026". (2) Center the title and set to 20pt bold. (3) Change all heading text color to dark blue (#00008B). (4) Set all body text font to "Georgia". (5) Add at end: "This proposal requires executive approval before implementation."
- **素材文件**：`Proposal_L3_07.docx`
- **评估函数**：`compare_docx_files`
- **Gold 文件**：`Proposal_L3_07_gold.docx`

#### 任务 L3-9：Policy_L3_09

- **ID**：`5186c84c-c3c2-4792-8349-61572a1ab7b3`
- **来源**：`writer_hard`
- **指令**：Open "Policy_L3_09.docx" and do ALL: (1) Center title, 22pt, bold, dark red (#8B0000). (2) Make section headings bold and navy blue (#003366). (3) Set all body text to Calibri 11pt. (4) Italic the body under "3. Work Schedule". (5) Add "INTERNAL DOCUMENT - DO NOT DISTRIBUTE" as the first paragraph. (6) Add at end: "Policy Owner: Human Resources Department | Review Cycle: Semi-annual"
- **素材文件**：`Policy_L3_09.docx`
- **评估函数**：`compare_docx_files`
- **Gold 文件**：`Policy_L3_09_gold.docx`

#### 任务 L3-10：Proposal_L3_02

- **ID**：`5cc2c306-2768-4e26-8f19-2717b474694b`
- **来源**：`writer_hard`
- **指令**：Open "Proposal_L3_02.docx" and do ALL: (1) Center-align the title and the two lines below it (Submitted to, Date). (2) Set title to 22pt bold. (3) Make all section headings dark blue (#003366) and bold. (4) Set all body text to 11pt. (5) Italic the body text under "Expected Benefits". (6) Add at the end: "Approved by: _________________ Date: _________________"
- **素材文件**：`Proposal_L3_02.docx`
- **评估函数**：`compare_docx_files`
- **Gold 文件**：`Proposal_L3_02_gold.docx`

#### 任务 L3-11：Proposal_L2_07

- **ID**：`7e3f78c5-9230-47cd-909f-5063da80ae89`
- **来源**：`writer_hard`
- **指令**：Open "Proposal_L2_07.docx". Change the color of all heading text to dark blue (#003366). Also underline the body text under the "Objectives" section.
- **素材文件**：`Proposal_L2_07.docx`
- **评估函数**：`compare_docx_files`
- **Gold 文件**：`Proposal_L2_07_gold.docx`

#### 任务 L3-12：Report_L2_06

- **ID**：`916c6ea4-3099-4aa8-b968-485ff5b03fb9`
- **来源**：`writer_hard`
- **指令**：Open "Report_L2_06.docx". Center-align the document title. After the paragraph starting with "Total revenue reached", insert a table with 4 rows and 3 columns. Headers: "Metric", "2024", "2025". Data rows: Revenue/$38.3M/$45.2M, Net Income/$5.9M/$8.1M, Cash Position/$9.8M/$12.4M.
- **素材文件**：`Report_L2_06.docx`
- **评估函数**：`compare_docx_files`
- **Gold 文件**：`Report_L2_06_gold.docx`

#### 任务 L3-13：Report_L3_01

- **ID**：`97d8736f-8d91-48ef-a299-256e11c742fb`
- **来源**：`writer_hard`
- **指令**：Open "Report_L3_01.docx" and perform ALL: (1) Center-align the document title. (2) Set title font to 24pt bold. (3) Change all body text to Times New Roman 12pt. (4) Make all section headings (Heading 1) dark blue (#003366). (5) Make the body text under "5. Strategic Outlook" bold. (6) Add at the end: "This report was reviewed and approved by the Board of Directors on March 31, 2025."
- **素材文件**：`Report_L3_01.docx`
- **评估函数**：`compare_docx_files`
- **Gold 文件**：`Report_L3_01_gold.docx`

#### 任务 L3-14：Policy_L3_04

- **ID**：`cd8b1536-0d23-4ffc-b4d1-2e534ac4bf9e`
- **来源**：`writer_hard`
- **指令**：Open "Policy_L3_04.docx" and do ALL: (1) Center title, set to 22pt bold. (2) Convert all section heading text to uppercase. (3) Set all body text to Times New Roman 11pt. (4) Bold the body text under "4. Equipment and Security" (after uppercase conversion). (5) Add "CONFIDENTIAL - Internal Use Only" as the very first paragraph. (6) Add at the end: "Document Control: Version 3.0 | Last Updated: January 1, 2025 | Next Review: July 1, 2025"
- **素材文件**：`Policy_L3_04.docx`
- **评估函数**：`compare_docx_files`
- **Gold 文件**：`Policy_L3_04_gold.docx`

#### 任务 L3-15：Guide_L3_05

- **ID**：`f0e1ab09-6fbd-4b2c-a67f-ebc8717462c3`
- **来源**：`writer_hard`
- **指令**：Open "Guide_L3_05.docx" and do ALL: (1) Replace "TechVision Inc." with "InnovateTech Corp." (2) Center title, set to 24pt bold. (3) Make all section headings bold and dark green (#006400). (4) Set all body text to 11pt. (5) Italic the body text under "Week 4: Integration". (6) Add at end: "Questions? Contact your HR representative or email onboarding@innovatetech.com"
- **素材文件**：`Guide_L3_05.docx`
- **评估函数**：`compare_docx_files`
- **Gold 文件**：`Guide_L3_05_gold.docx`

#### L3 任务来源标注

| 任务 | 来源类型 | 具体来源 | 标注理由 |
|------|---------|---------|---------|
| L3-1 | 官方帮助 | [Text Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) | Open "Policy_L2_04.docx". Set the font size of all body text to 12pt. Additional |
| L3-2 | 官方帮助 | [Text Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) | Open "Policy_L2_09.docx". Add the following paragraph at the very beginning of t |
| L3-3 | 官方帮助 | [Text Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) | Open "Report_L2_01.docx". Change the font of all body text (non-heading paragrap |
| L3-4 | 官方帮助 | [Text Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) + [Paragraph Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) | Open "Report_L3_06.docx" and do ALL: (1) Center title, set to 22pt, bold, dark b |
| L3-5 | 官方帮助 | [Text Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) + [Lists and Numbering](https://help.libreoffice.org/latest/en-US/text/swriter/guide/using_numbering.html) + [Paragraph Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) | Open "Meeting_L3_08.docx" and do ALL: (1) Center the title, 18pt, bold. (2) Cent |
| L3-6 | 官方帮助 | [Text Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) + [Paragraph Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) | Open "Guide_L3_10.docx" and do ALL: (1) Replace "TechVision Inc." with "GlobalTe |
| L3-7 | 官方帮助 | [Text Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) + [Lists and Numbering](https://help.libreoffice.org/latest/en-US/text/swriter/guide/using_numbering.html) + [Paragraph Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) | Open "Meeting_L3_03.docx" and do ALL: (1) Center the title and set to 20pt. (2)  |
| L3-8 | 官方帮助 | [Text Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) + [Paragraph Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) | Open "Proposal_L3_07.docx" and do ALL: (1) Replace "Q1 2025" with "First Quarter |
| L3-9 | 官方帮助 | [Text Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) + [Paragraph Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) | Open "Policy_L3_09.docx" and do ALL: (1) Center title, 22pt, bold, dark red (#8B |
| L3-10 | 官方帮助 | [Text Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) + [Paragraph Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) | Open "Proposal_L3_02.docx" and do ALL: (1) Center-align the title and the two li |
| L3-11 | 官方帮助 | [Text Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) | Open "Proposal_L2_07.docx". Change the color of all heading text to dark blue (# |
| L3-12 | 官方帮助 | [Tables in Text](https://help.libreoffice.org/latest/en-US/text/swriter/guide/table_insert.html) + [Headers and Footers](https://help.libreoffice.org/latest/en-US/text/swriter/guide/header_footer.html) + [Paragraph Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) | Open "Report_L2_06.docx". Center-align the document title. After the paragraph s |
| L3-13 | 官方帮助 | [Text Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) + [Paragraph Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) | Open "Report_L3_01.docx" and perform ALL: (1) Center-align the document title. ( |
| L3-14 | 官方帮助 | [Text Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) + [Paragraph Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) | Open "Policy_L3_04.docx" and do ALL: (1) Center title, set to 22pt bold. (2) Con |
| L3-15 | 官方帮助 | [Text Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) + [Paragraph Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) | Open "Guide_L3_05.docx" and do ALL: (1) Replace "TechVision Inc." with "Innovate |

#### L3 任务汇总表

| # | 任务名称 | 素材文件 | 评估函数 |
|---|---------|---------|---------|
| 1 | Policy_L2_04 | `Policy_L2_04.docx` | `compare_docx_files`  |
| 2 | Policy_L2_09 | `Policy_L2_09.docx` | `compare_docx_files`  |
| 3 | Report_L2_01 | `Report_L2_01.docx` | `compare_docx_files`  |
| 4 | Report_L3_06 | `Report_L3_06.docx` | `compare_docx_files`  |
| 5 | Meeting_L3_08 | `Meeting_L3_08.docx` | `compare_docx_files`  |
| 6 | Guide_L3_10 | `Guide_L3_10.docx` | `compare_docx_files`  |
| 7 | Meeting_L3_03 | `Meeting_L3_03.docx` | `compare_docx_files`  |
| 8 | Proposal_L3_07 | `Proposal_L3_07.docx` | `compare_docx_files`  |
| 9 | Policy_L3_09 | `Policy_L3_09.docx` | `compare_docx_files`  |
| 10 | Proposal_L3_02 | `Proposal_L3_02.docx` | `compare_docx_files`  |
| 11 | Proposal_L2_07 | `Proposal_L2_07.docx` | `compare_docx_files`  |
| 12 | Report_L2_06 | `Report_L2_06.docx` | `compare_docx_files`  |
| 13 | Report_L3_01 | `Report_L3_01.docx` | `compare_docx_files`  |
| 14 | Policy_L3_04 | `Policy_L3_04.docx` | `compare_docx_files`  |
| 15 | Guide_L3_05 | `Guide_L3_05.docx` | `compare_docx_files`  |

---

### 3.4 Interactive 任务（Writer 交互式）—— 26 个

> 交互式任务使用多阶段 phase 设计，通过 `trigger` 控制阶段切换。


#### 场景类型：`ambiguous_detail`（模糊细节）—— 4 个

> **来源类型**：现实场景构造 | **真实工作来源**：排版细节不明确
> **证据描述**：收到"把标题弄好看点"但未指定字号、字体、颜色

##### interactive_writer_005（L3）

- **场景描述**：The user wants to add product specifications to the manual but hasn't provided the specific values. The agent asks first.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `agent_asks`）：Help me add the product specs
  - Phase 2（trigger: `agent_done`）：Add "Weight: 250g, Dimensions: 15cm x 10cm x 3cm" at the end of the document, then save

##### interactive_writer_006（L3）

- **场景描述**：The user says to update the completion rate but doesn't specify the new value. The agent asks first.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `agent_asks`）：Help me update the completion rate
  - Phase 2（trigger: `agent_done`）：Change "Completion Rate: 60%%" to "Completion Rate: 85%%", then save

##### interactive_writer_007（L3）

- **场景描述**：The user wants to add a closing statement to the year-end summary but doesn't say what. The agent asks first.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `agent_asks`）：Help me add a closing statement to the document
  - Phase 2（trigger: `agent_done`）：Add "Thank you to all employees for your hard work and dedication this year!" at the very end of the document, then save

##### interactive_writer_008（L2）

- **场景描述**：The user wants to add notes to the training manual but doesn't specify the content. The agent asks first.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `agent_asks`）：Help me add the notes section
  - Phase 2（trigger: `agent_done`）：Under the "Important Notes" heading, add "1. Please back up all data in advance", then save


#### 场景类型：`ambiguous_instruction`（模糊指令）—— 1 个

> **来源类型**：现实场景构造 | **真实工作来源**：模糊的文档修改指令
> **证据描述**：收到"这个文档不够专业"需要 agent 主动澄清

##### interactive_writer_ambiguous_001（L1）

- **场景描述**：The instruction is missing information the agent cannot infer; the agent must ask the user before proceeding.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me add what we agreed earlier to the end of the document
  - Phase 2（trigger: `agent_done`）：in document's the very endtwo rows, add "Author: Zhang San""Reviewer: Li Si", then save the file


#### 场景类型：`ambiguous_scope`（模糊范围）—— 4 个

> **来源类型**：现实场景构造 | **真实工作来源**：文档修改范围不确定
> **证据描述**：收到"改一下这个报告"但未指定改哪些章节

##### interactive_writer_009（L2）

- **场景描述**：The notice contains multiple dates. The user says to update the date but doesn't specify which one. The agent asks, then only changes the publication date.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `agent_asks`）：Help me update the date in the file
  - Phase 2（trigger: `agent_done`）：Only update the Publication Date on the first line to "July 1, 2025", leave all other dates unchanged, then save

##### interactive_writer_010（L1）

- **场景描述**：The user wants to add department info to an employee record but doesn't say which one. The agent asks, then only modifies the first record.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `agent_asks`）：Help me add the department info
  - Phase 2（trigger: `agent_done`）：Only add "Department: Engineering" after the first employee record (E001), then save

##### interactive_writer_011（L1）

- **场景描述**：The task list has multiple tasks. The user says to update the status but doesn't say which one. The agent asks, then only changes the first task.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `agent_asks`）：Help me update the status
  - Phase 2（trigger: `agent_done`）：Only change the first task (Requirements Document Review) status from "In Progress" to "Completed", leave others unchanged, then save

##### interactive_writer_012（L2）

- **场景描述**：The meeting minutes cover multiple agenda items. The user wants to add a resolution but doesn't say which item. The agent asks, then only adds it under the first item.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `agent_asks`）：Help me add a resolution to the minutes
  - Phase 2（trigger: `agent_done`）：Only add "Resolution: Approved Plan A" under Agenda Item 1, then save


#### 场景类型：`ambiguous_target`（模糊目标）—— 4 个

> **来源类型**：现实场景构造 | **真实工作来源**：模糊的文档修改需求
> **证据描述**：收到"帮我改一下格式"但未指定具体段落或样式

##### interactive_writer_001（L3）

- **场景描述**：The user wants to add the recorder's name to the meeting minutes but doesn't say who. The agent must ask for the specific name before filling it in.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `agent_asks`）：Help me add that person's name to the minutes
  - Phase 2（trigger: `agent_done`）：Write "Wang Fang" on the "Recorded by:" line, then save

##### interactive_writer_002（L3）

- **场景描述**：The user wants to change a deadline in the project plan but doesn't say which one. The agent asks before making the change.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `agent_asks`）：Help me change the deadline
  - Phase 2（trigger: `agent_done`）：Change the first deadline to "June 30, 2025", then save

##### interactive_writer_003（L2）

- **场景描述**：The user wants to fill in Party B's information on the contract draft but hasn't provided the company name. The agent asks first.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `agent_asks`）：Help me fill in Party B's info
  - Phase 2（trigger: `agent_done`）：Write "Beijing Tech Solutions Ltd." on the "Party B:" line, then save

##### interactive_writer_004（L2）

- **场景描述**：The user wants to add a contact person at the end of the work report but doesn't say who. The agent asks first.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `agent_asks`）：Help me add that contact person
  - Phase 2（trigger: `agent_done`）：Add "Contact: Chen Gang" at the end of the document, then save


#### 场景类型：`error_correction`（错误纠正）—— 2 个

> **来源类型**：现实场景构造 | **真实工作来源**：格式错误修正
> **证据描述**：发现字体/缩进不一致后要求统一修正

##### interactive_writer_error_correction_001（L3）

- **场景描述**：User asks agent to add a disclaimer at the end, but agent puts it at the beginning. User corrects.
- **阶段数**：3
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Add a disclaimer to the document: 'This policy is subject to annual review.'
  - Phase 2（trigger: `agent_done`）：Wait, I wanted the disclaimer at the END of the document, not where you put it. Please move it to the very last line.
  - Phase 3（trigger: `agent_done`）：Now also add 'Last updated: March 2025' right before the disclaimer. Save.

##### interactive_writer_error_correction_002（L3）

- **场景描述**：User asks agent to add a signoff with a name. Agent writes it but the name is wrong. User corrects.
- **阶段数**：3
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Add 'Regards, the CEO' at the end of the memo
  - Phase 2（trigger: `agent_done`）：Please change that to 'Regards, David Chen, CEO'. I need the actual name there, not just the title.
  - Phase 3（trigger: `agent_done`）：And add 'CC: HR Department, Finance Department' on the next line after the regards. Save.


#### 场景类型：`multi_step_workflow`（多步工作流）—— 2 个

> **来源类型**：现实场景构造 | **真实工作来源**：完整文档排版工作流
> **证据描述**：从标题格式、正文样式到页眉页脚的完整链路

##### interactive_writer_workflow_001（L3）

- **场景描述**：Sequential 4-step workflow: create document structure, add content, format headers, add footer.
- **阶段数**：4
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `agent_done`）：Add the author name 'Prepared by: Marketing Department' at the very top of the document, before the title.
  - Phase 2（trigger: `agent_done`）：Now add a new section at the end titled 'Key Risks' with the text: 'Supply chain disruptions remain the primary concern.'
  - Phase 3（trigger: `agent_done`）：Add the date 'Date: March 2025' right after the author line you added earlier.
  - Phase 4（trigger: `agent_done`）：Finally, add 'CONFIDENTIAL' at the very end of the document. Save the file.

##### interactive_writer_workflow_002（L3）

- **场景描述**：Sequential 4-step workflow: write agenda, add attendees, add action items, add disclaimer.
- **阶段数**：4
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `agent_done`）：Add an 'Agenda' section with three items: '1. Q1 Financial Review', '2. Strategic Initiatives Update', '3. Budget Approval for Q2'
  - Phase 2（trigger: `agent_done`）：Add an 'Attendees' section listing: 'CEO: Robert Chen, CFO: Lisa Wang, CTO: James Liu, COO: Sarah Park'
  - Phase 3（trigger: `agent_done`）：Add an 'Action Items from Previous Meeting' section with: '1. Complete audit report - Status: Done', '2. Finalize vendor contract - Status: Pending'
  - Phase 4（trigger: `agent_done`）：Add 'Note: This document is for internal distribution only.' at the end. Save the file.


#### 场景类型：`progressive_refinement`（渐进精化）—— 4 个

> **来源类型**：现实场景构造 | **真实工作来源**：分阶段文档修订
> **证据描述**：先做初稿排版确认，再逐步加入页眉页脚/样式/目录

##### interactive_writer_013（L1）

- **场景描述**：The user first asks the agent to fill in basic info on the leave request email, then provides the reason and number of days.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me fill in the basic info on the leave request email
  - Phase 2（trigger: `agent_done`）：Fill in the leave reason as: feeling unwell and need rest, and number of days: 3 days, then save

##### interactive_writer_014（L1）

- **场景描述**：The user first provides the meeting time for the agent to fill in, then provides the meeting location.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me fill in the meeting time: August 15, 2025 at 9:00 AM
  - Phase 2（trigger: `agent_done`）：Now add the meeting location: Main Conference Hall, 1st Floor, then save

##### interactive_writer_015（L2）

- **场景描述**：The user first provides the product name for the agent to fill in, then provides the product number.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me fill in the product name: Smart Thermostat Pro
  - Phase 2（trigger: `agent_done`）：Now add the product number: TC-2025-001, then save

##### interactive_writer_016（L2）

- **场景描述**：The user first asks the agent to fill in this year's achievements, then adds next year's work plan.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me add this year's main achievement: Delivered 3 major projects
  - Phase 2（trigger: `agent_done`）：Now add next year's plan: Expand into new markets and add two product lines, then save


#### 场景类型：`requirement_change`（需求变更）—— 4 个

> **来源类型**：现实场景构造 | **真实工作来源**：文档需求变更
> **证据描述**：排版到一半被要求改变标题层级或添加新章节

##### interactive_writer_017（L2）

- **场景描述**：The user first asks the agent to add project lead Zhang Ming, then says the name was wrong and should be Zhang Qiang.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me add "Project Lead: Zhang Ming" at the end of the report
  - Phase 2（trigger: `agent_done`）：The name was wrong, change it to "Project Lead: Zhang Qiang", then save

##### interactive_writer_018（L1）

- **场景描述**：The user first asks the agent to change the contract title to '2025 Procurement Contract', then says it should be more formal: '2025 Annual Strategic Procurement Contract'.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me add a title line: "2025 Procurement Contract"
  - Phase 2（trigger: `agent_done`）：The title should be more formal, change it to "2025 Annual Strategic Procurement Contract", then save

##### interactive_writer_019（L3）

- **场景描述**：The user first asks the agent to add a contact name, then says a phone number should also be included.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me add "Contact: Wang Xiaoming" to the notice
  - Phase 2（trigger: `agent_done`）：Need to add the phone number too, change it to "Contact: Wang Xiaoming, Phone: 010-12345678", then save

##### interactive_writer_020（L1）

- **场景描述**：The user first says Q4 target is 110%%, then changes it to 120%%.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me add the Q4 target to the plan: Achieve 110%% of annual sales
  - Phase 2（trigger: `agent_done`）：Set the target higher, change it to 120%%, then save


#### 场景类型：`task_interruption`（任务中断）—— 1 个

> **来源类型**：现实场景构造 | **真实工作来源**：文档编辑中断
> **证据描述**：编辑过程中被告知需要额外添加表格或修改已完成部分

##### interactive_writer_interruption_001（L3）

- **场景描述**：The user interrupts the main document task for a side request, then returns to continue the original editing task.
- **阶段数**：3
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `agent_done`）：Help me document's title"Overview"change "Project overview"
  - Phase 2（trigger: `agent_done`）：Wait, first Help me check how much disk space is left, openusing df -h
  - Phase 3（trigger: `agent_done`）：OK, , go back to that document, Help me in "Project overview"belowone row write "This report summarizes key 2025 progress", Then save the file

#### Interactive 任务来源映射

| 场景类型 | 任务数 | 真实工作来源 | 证据描述 | trigger 组合 |
|---------|-------|------------|---------|------------|
| `ambiguous_detail`（模糊细节） | 4 | 排版细节不明确 | 收到"把标题弄好看点"但未指定字号、字体、颜色 | agent_asks + agent_done |
| `ambiguous_instruction`（模糊指令） | 1 | 模糊的文档修改指令 | 收到"这个文档不够专业"需要 agent 主动澄清 | agent_done + step_count |
| `ambiguous_scope`（模糊范围） | 4 | 文档修改范围不确定 | 收到"改一下这个报告"但未指定改哪些章节 | agent_asks + agent_done |
| `ambiguous_target`（模糊目标） | 4 | 模糊的文档修改需求 | 收到"帮我改一下格式"但未指定具体段落或样式 | agent_asks + agent_done |
| `error_correction`（错误纠正） | 2 | 格式错误修正 | 发现字体/缩进不一致后要求统一修正 | agent_done + step_count |
| `multi_step_workflow`（多步工作流） | 2 | 完整文档排版工作流 | 从标题格式、正文样式到页眉页脚的完整链路 | agent_done |
| `progressive_refinement`（渐进精化） | 4 | 分阶段文档修订 | 先做初稿排版确认，再逐步加入页眉页脚/样式/目录 | agent_done + step_count |
| `requirement_change`（需求变更） | 4 | 文档需求变更 | 排版到一半被要求改变标题层级或添加新章节 | agent_done + step_count |
| `task_interruption`（任务中断） | 1 | 文档编辑中断 | 编辑过程中被告知需要额外添加表格或修改已完成部分 | agent_done |

#### Interactive 触发类型分布

| 触发类型 | 中文 | 出现次数 | 说明 |
|---------|------|---------|------|
| `agent_done` | 代理完成 | 36 | 上一阶段完成后自动进入下一阶段 |
| `agent_asks` | 代理追问 | 12 | agent 主动向用户追问澄清后触发 |
| `step_count` | 步数触发 | 11 | 达到指定步数后注入新指令 |

#### Interactive 任务来源映射

> 目标：为每个 Interactive 场景补齐"来源证据链"，用于论文中证明任务来自真实工作流并经过人工筛选。

| 场景类型 | 真实工作来源（Primary Source） | 证据包（最小） | Task JSON `source` 建议写法 |
|---------|---------------------------|-------------|--------------------------|
| `ambiguous_target` | 模糊的文档修改需求（"帮我改一下格式"→追问→执行） | ① 原始模糊需求 ② 追问记录 ③ 澄清后执行 | `libreoffice_writer_interactive;source_type=document_edit;evidence=ambiguous_target` |
| `ambiguous_detail` | 排版细节不明确（"把标题弄好看点"→澄清→执行） | ① 原始需求 ② 细节追问 ③ 样式确认 | `libreoffice_writer_interactive;source_type=formatting;evidence=detail_clarification` |
| `progressive_refinement` | 分阶段文档修订（初稿排版→确认→加页眉页脚） | ① 初版确认 ② 精化指令 ③ 最终验收 | `libreoffice_writer_interactive;source_type=document_revision;evidence=staged_refinement` |
| `requirement_change` | 文档需求变更（排版到一半改标题层级） | ① 初始需求 ② 变更指令 ③ 差异记录 | `libreoffice_writer_interactive;source_type=document_change;evidence=requirement_change` |
| `error_correction` | 格式错误修正（字体/缩进不一致→统一修正） | ① 错误描述 ② 纠正指令 ③ 修正验证 | `libreoffice_writer_interactive;source_type=format_fix;evidence=error_correction` |
| `task_interruption` | 文档编辑中断（编辑中追加表格/修改已完成部分） | ① 中断前进度 ② 追加内容 ③ 最终结果 | `libreoffice_writer_interactive;source_type=edit_interruption;evidence=task_interruption` |
| `multi_step_workflow` | 完整文档排版工作流（标题→正文→页眉页脚） | ① 各阶段指令 ② 中间确认 ③ 最终交付 | `libreoffice_writer_interactive;source_type=full_formatting;evidence=workflow` |

#### 来源证据落地字段（建议统一）

- **source_type**：`document_edit` / `formatting` / `document_revision` / `document_change` / `format_fix` / `edit_interruption` / `full_formatting`
- **source_ref**：来源标识（匿名化 URL、工单号、访谈记录编号）
- **captured_at**：取证日期（`YYYY-MM-DD`）
- **anonymized_excerpt**：匿名化原文摘录（1~3 句）
- **mapping_note**：原始需求如何映射到 `phases` 与 `trigger`
- **reviewers**：双人审核与仲裁记录（`reviewer_a/reviewer_b/adjudicator`）

---

## 4. 评估函数汇总

| # | 函数名 | 类别 | 使用次数 |
|---|--------|------|---------|
| 1 | `compare_docx_files` | 静态任务 | 20 |
| 2 | `check_include_exclude` | 交互任务 | 26 |

**总计**：覆盖 20 个静态任务 + 26 个交互任务 = **46** 个任务。

---

## 5. 素材说明

### 技术规格

| 属性 | 值 |
|------|-----|
| 文件格式 | `.docx`（Office Open XML Document） |
| 静态任务文件总数 | 20 个初始文件 + 20 个 gold 文件 |
| 语言 | 所有文档内容均为英文 |
| 文档类型 | 会议纪要、政策文档、指南、提案、报告 |

---

## 6. Task JSON 模板

### 静态任务（compare_docx_files）

```json
{
  "id": "<uuid4>",
  "snapshot": "libreoffice_writer",
  "instruction": "<操作指令>",
  "config": [
    {"type": "upload_file", "parameters": {"files": [{"local_path": "cache/<id>/<file>.docx", "path": "/home/user/Desktop/<file>.docx"}]}},
    {"type": "open", "parameters": {"path": "/home/user/Desktop/<file>.docx"}}
  ],
  "evaluator": {
    "postconfig": [
      {"type": "activate_window", "parameters": {"window_name": "<file>.docx", "strict": false}},
      {"type": "execute", "parameters": {"command": ["python", "-c", "import pyautogui, time; pyautogui.hotkey('ctrl','s'); time.sleep(1.5); pyautogui.press('return');"]}}
    ],
    "func": "compare_docx_files",
    "expected": {"type": "cache_file", "path": "<file>_gold.docx"},
    "result": {"type": "vm_file", "path": "/home/user/Desktop/<file>.docx", "dest": "<file>.docx"}
  },
  "difficulty": "L2"
}
```

---

## 7. Docker 镜像要求

- **LibreOffice Writer**（推荐 7.x+）
- **X11 显示环境**
- **Python 3 + python-docx**（评估器）
  ```bash
  pip install python-docx
  ```

---

## 8. 任务难度分布总结

| 级别 | 数量 | 指令长度 | 操作步骤 | 描述 | 示例 |
|------|------|---------|---------|------|------|
| L1 | 5 | 134-149 字符 | 1-2 步 | 单步格式操作 | 标题居中+分页、字体替换、颜色修改、文本替换+加粗 |
| L2 | 5 | 153-346 字符 | 2-4 步 | 多步复合操作 | 字号设置+斜体、段落插入+大写转换、表格插入+居中、删除线+长段添加 |
| L3 | 10 | 309-441 字符 | 5-6 步（带编号子步骤） | 复杂排版工作流 | 标题居中+22pt+加粗+颜色+正文字体+斜体+尾部添加（6 步组合） |
| **总计** | **20** | | | | |

### 可验证性保证

1. **`.docx` 结构化对比**：使用 `python-docx` 逐段落对比文本内容和格式。不依赖截图或 OCR。
2. **灵活匹配模式**：支持 `ignore_blanks`、`fuzzy_match`、`content_only` 等选项。
3. **交互任务命令行验证**：通过 `check_include_exclude` 验证输出文件关键字。

> 难度标签基于 kimi-k2.5 模型在 max_steps=50（静态）/ max_steps=80（交互）条件下的实际执行结果。

---

## 9. 常见陷阱

### LibreOffice 保存对话框
- `Ctrl+S` 时 `.docx` 文件同样会弹出格式确认对话框，需按 `Enter` 确认。

### python-docx 对比注意事项
- **段落分割**：LibreOffice 与 Word 在空行/换行处理上可能不同，`ignore_blanks` 模式可减少误判。
- **样式名称**：LibreOffice 使用的段落样式名称可能与 Word 不同（如 "Heading 1" vs "标题 1"）。
- **字体回退**：VM 中可能缺少某些字体，LibreOffice 会自动替换，导致字体名称不匹配。

### Gold 文件管理
- gold 文件必须同时存在于 `OSWorld/cache/<task_id>/` 和 `desktopworld/cache/<task_id>/` 两个目录。
