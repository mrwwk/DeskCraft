# LibreOffice Writer Task Design Document

## 0. Verification Strategy

### Core Approach

LibreOffice Writer verification downloads the user-edited `.docx` file from the VM and performs full-text comparison against a pre-built gold standard file.

1. **Document Full-Text Comparison** (`compare_docx_files`): Uses `python-docx` to parse `.docx` files, comparing text content paragraph by paragraph. Defaults to `ignore_blanks` (ignore extra whitespace), with optional fuzzy matching, case-insensitive, and order-independent modes.

**Evaluator Architecture**: Downloads edited file from VM via `vm_file` getter, loads `_gold.docx` from cache, and performs comparison locally.

### Evaluator Pattern

```python
def compare_docx_files(file1, file2, **options):
    """
    Args:
        file1: Path to user-edited .docx file from VM
        file2: Path to gold standard .docx file
        options: ignore_blanks=True, ignore_case, ignore_order, content_only, fuzzy_match
    Returns:
        1.0 (match) or 0.0 (mismatch)
    """
```

---

## 1. Available Resources

Total: **20** initial files + corresponding gold standard files

### writer_hard Materials (20 tasks)

| # | Initial File | Gold File | Task Summary |
|---|-------------|-----------|-------------|
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

## 2. Evaluation Function Design

File: `desktop_env/evaluators/metrics/docs.py`

### 2.1 Main Evaluation Functions

| Function | Description | Usage Count |
|----------|-------------|-------------|
| `compare_docx_files` | Structured comparison of two .docx files (text content, paragraph formatting) | 20 |

---

## 3. Task Definitions


### 3.1 Level 1 (L1) -- Basic Operations -- 2 tasks

> Tasks completed by agent within 10 steps with score 1.0

#### Task L1-1: Meeting_L2_03

- **ID**: `0348a68c-a33e-47e9-9e07-d189c43e9bec`
- **Source**: `writer_hard`
- **Instruction**: Open "Meeting_L2_03.docx". Apply strikethrough formatting to the last action item (the one starting with "Tom:"). Then add the following paragraph at the end of the document: "Summary: All Q1 targets were met or exceeded. The team will focus on scaling operations and executing the Q2 product roadmap. Next review meeting scheduled for April 25."
- **Material File**: `Meeting_L2_03.docx`
- **Evaluation Function**: `compare_docx_files`
- **Gold File**: `Meeting_L2_03_gold.docx`

#### Task L1-2: Proposal_L2_02

- **ID**: `aaa6abac-4bde-47ea-805a-08da32e7a1e1`
- **Source**: `writer_hard`
- **Instruction**: Open "Proposal_L2_02.docx". Center-align the document title (first line). Insert a page break immediately before the "Budget" heading.
- **Material File**: `Proposal_L2_02.docx`
- **Evaluation Function**: `compare_docx_files`
- **Gold File**: `Proposal_L2_02_gold.docx`

#### L1 Task Source Annotations

| Task | Source Type | Specific Source | Annotation Reason |
|------|-----------|-----------------|-------------------|
| L1-1 | Official Help | [Writer Guide](https://help.libreoffice.org/latest/en-US/text/swriter/guide/main.html) | Open "Meeting_L2_03.docx". Apply strikethrough formatting to the last action ite |
| L1-2 | Official Help | [Text Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) | Open "Proposal_L2_02.docx". Center-align the document title (first line). Insert |

#### L1 Task Summary Table

| # | Task Name | Material File | Evaluation Function |
|---|-----------|---------------|---------------------|
| 1 | Meeting_L2_03 | `Meeting_L2_03.docx` | `compare_docx_files`  |
| 2 | Proposal_L2_02 | `Proposal_L2_02.docx` | `compare_docx_files`  |


### 3.2 Level 2 (L2) -- Compound Operations -- 3 tasks

> Tasks completed within 25 steps (score 1.0) or failed within 10 steps

#### Task L2-1: Guide_L2_05

- **ID**: `212c971d-6afa-4d9e-9ad8-11fe74fb692d`
- **Source**: `writer_hard`
- **Instruction**: Open "Guide_L2_05.docx". Replace all occurrences of "TechVision Inc." with "InnovateTech Corp." Also make all "Week" section headings bold.
- **Material File**: `Guide_L2_05.docx`
- **Evaluation Function**: `compare_docx_files`
- **Gold File**: `Guide_L2_05_gold.docx`

#### Task L2-2: Meeting_L2_08

- **ID**: `a10c5680-643f-4446-805f-e2e749efff6e`
- **Source**: `writer_hard`
- **Instruction**: Open "Meeting_L2_08.docx". Replace all occurrences of "Q1" with "First Quarter" throughout the document. Also make the attendees list paragraph bold.
- **Material File**: `Meeting_L2_08.docx`
- **Evaluation Function**: `compare_docx_files`
- **Gold File**: `Meeting_L2_08_gold.docx`

#### Task L2-3: Guide_L2_10

- **ID**: `ddc06ab7-075d-47e8-8d70-c88b88605ddf`
- **Source**: `writer_hard`
- **Instruction**: Open "Guide_L2_10.docx". Change the title (first line) font size to 24pt. Add this paragraph at the end: "For more information, contact HR at hr@techvision.com or visit the employee portal at https://portal.techvision.com"
- **Material File**: `Guide_L2_10.docx`
- **Evaluation Function**: `compare_docx_files`
- **Gold File**: `Guide_L2_10_gold.docx`

#### L2 Task Source Annotations

| Task | Source Type | Specific Source | Annotation Reason |
|------|-----------|-----------------|-------------------|
| L2-1 | Official Help | [Text Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) | Open "Guide_L2_05.docx". Replace all occurrences of "TechVision Inc." with "Inno |
| L2-2 | Official Help | [Text Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) | Open "Meeting_L2_08.docx". Replace all occurrences of "Q1" with "First Quarter"  |
| L2-3 | Official Help | [Text Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) | Open "Guide_L2_10.docx". Change the title (first line) font size to 24pt. Add th |

#### L2 Task Summary Table

| # | Task Name | Material File | Evaluation Function |
|---|-----------|---------------|---------------------|
| 1 | Guide_L2_05 | `Guide_L2_05.docx` | `compare_docx_files`  |
| 2 | Meeting_L2_08 | `Meeting_L2_08.docx` | `compare_docx_files`  |
| 3 | Guide_L2_10 | `Guide_L2_10.docx` | `compare_docx_files`  |


### 3.3 Level 3 (L3) -- Advanced Workflows -- 15 tasks

> Tasks agent cannot complete or requiring >25 steps

#### Task L3-1: Policy_L2_04

- **ID**: `1cd80191-f69d-4d57-9197-e10d0c8fbbce`
- **Source**: `writer_hard`
- **Instruction**: Open "Policy_L2_04.docx". Set the font size of all body text to 12pt. Additionally, make the body text under section "5. Communication Standards" italic.
- **Material File**: `Policy_L2_04.docx`
- **Evaluation Function**: `compare_docx_files`
- **Gold File**: `Policy_L2_04_gold.docx`

#### Task L3-2: Policy_L2_09

- **ID**: `247db8e9-9fd2-49a6-85f9-b53854f64c47`
- **Source**: `writer_hard`
- **Instruction**: Open "Policy_L2_09.docx". Add the following paragraph at the very beginning of the document: "DISCLAIMER: This policy is subject to change. Employees should check the HR portal for the latest version." Also convert all section heading text to uppercase.
- **Material File**: `Policy_L2_09.docx`
- **Evaluation Function**: `compare_docx_files`
- **Gold File**: `Policy_L2_09_gold.docx`

#### Task L3-3: Report_L2_01

- **ID**: `271a9bcb-ce39-4cdb-90ae-569776e78eaa`
- **Source**: `writer_hard`
- **Instruction**: Open "Report_L2_01.docx". Change the font of all body text (non-heading paragraphs) to "Times New Roman". Also make all heading text bold.
- **Material File**: `Report_L2_01.docx`
- **Evaluation Function**: `compare_docx_files`
- **Gold File**: `Report_L2_01_gold.docx`

#### Task L3-4: Report_L3_06

- **ID**: `2b672d35-1c0f-4a71-bb85-f32b5ad8b46d`
- **Source**: `writer_hard`
- **Instruction**: Open "Report_L3_06.docx" and do ALL: (1) Center title, set to 22pt, bold, dark blue (#003366). (2) Make all section headings bold and underlined. (3) Set all body text to Calibri 11pt. (4) Make the paragraph starting with "For 2026" both bold and italic. (5) Add "--- End of Report ---" as the last paragraph.
- **Material File**: `Report_L3_06.docx`
- **Evaluation Function**: `compare_docx_files`
- **Gold File**: `Report_L3_06_gold.docx`

#### Task L3-5: Meeting_L3_08

- **ID**: `3cf4aa78-196b-4654-a632-7f8c0b52c8e1`
- **Source**: `writer_hard`
- **Instruction**: Open "Meeting_L3_08.docx" and do ALL: (1) Center the title, 18pt, bold. (2) Center-align the attendees list paragraph. (3) Make all section headings underlined and bold. (4) Bold all action item lines (starting with names + colon). (5) Set all body text font to "Arial". (6) Add at end: "Recorded by: Meeting Secretary | Distribution: All attendees + Board"
- **Material File**: `Meeting_L3_08.docx`
- **Evaluation Function**: `compare_docx_files`
- **Gold File**: `Meeting_L3_08_gold.docx`

#### Task L3-6: Guide_L3_10

- **ID**: `3dad2051-0596-4886-93c5-9ed78df81f99`
- **Source**: `writer_hard`
- **Instruction**: Open "Guide_L3_10.docx" and do ALL: (1) Replace "TechVision Inc." with "GlobalTech Solutions". (2) Center title, set to 26pt, bold, dark green (#006400). (3) Make all section headings bold and 16pt. (4) Set all body text to Georgia 11pt. (5) Bold the body text under "Week 1: Getting Started". (6) Add at end: "Last updated: March 2025 | Next revision: September 2025"
- **Material File**: `Guide_L3_10.docx`
- **Evaluation Function**: `compare_docx_files`
- **Gold File**: `Guide_L3_10_gold.docx`

#### Task L3-7: Meeting_L3_03

- **ID**: `409f8738-31ec-406f-898f-01ed419b74b4`
- **Source**: `writer_hard`
- **Instruction**: Open "Meeting_L3_03.docx" and do ALL: (1) Center the title and set to 20pt. (2) Replace "Q1" with "First Quarter" and "Q2" with "Second Quarter" everywhere. (3) Bold the attendees list paragraph. (4) Italic all action item paragraphs (lines starting with names followed by colon). (5) Change all section headings to dark blue (#003366). (6) Add "--- End of Meeting Minutes ---" at the end.
- **Material File**: `Meeting_L3_03.docx`
- **Evaluation Function**: `compare_docx_files`
- **Gold File**: `Meeting_L3_03_gold.docx`

#### Task L3-8: Proposal_L3_07

- **ID**: `43b0833a-2da6-43e7-a8e3-93790bc2579a`
- **Source**: `writer_hard`
- **Instruction**: Open "Proposal_L3_07.docx" and do ALL: (1) Replace "Q1 2025" with "First Quarter 2025", "Q2-Q3 2025" with "Second-Third Quarter 2025", "Q4 2025" with "Fourth Quarter 2025", "Q1 2026" with "First Quarter 2026". (2) Center the title and set to 20pt bold. (3) Change all heading text color to dark blue (#00008B). (4) Set all body text font to "Georgia". (5) Add at end: "This proposal requires executive approval before implementation."
- **Material File**: `Proposal_L3_07.docx`
- **Evaluation Function**: `compare_docx_files`
- **Gold File**: `Proposal_L3_07_gold.docx`

#### Task L3-9: Policy_L3_09

- **ID**: `5186c84c-c3c2-4792-8349-61572a1ab7b3`
- **Source**: `writer_hard`
- **Instruction**: Open "Policy_L3_09.docx" and do ALL: (1) Center title, 22pt, bold, dark red (#8B0000). (2) Make section headings bold and navy blue (#003366). (3) Set all body text to Calibri 11pt. (4) Italic the body under "3. Work Schedule". (5) Add "INTERNAL DOCUMENT - DO NOT DISTRIBUTE" as the first paragraph. (6) Add at end: "Policy Owner: Human Resources Department | Review Cycle: Semi-annual"
- **Material File**: `Policy_L3_09.docx`
- **Evaluation Function**: `compare_docx_files`
- **Gold File**: `Policy_L3_09_gold.docx`

#### Task L3-10: Proposal_L3_02

- **ID**: `5cc2c306-2768-4e26-8f19-2717b474694b`
- **Source**: `writer_hard`
- **Instruction**: Open "Proposal_L3_02.docx" and do ALL: (1) Center-align the title and the two lines below it (Submitted to, Date). (2) Set title to 22pt bold. (3) Make all section headings dark blue (#003366) and bold. (4) Set all body text to 11pt. (5) Italic the body text under "Expected Benefits". (6) Add at the end: "Approved by: _________________ Date: _________________"
- **Material File**: `Proposal_L3_02.docx`
- **Evaluation Function**: `compare_docx_files`
- **Gold File**: `Proposal_L3_02_gold.docx`

#### Task L3-11: Proposal_L2_07

- **ID**: `7e3f78c5-9230-47cd-909f-5063da80ae89`
- **Source**: `writer_hard`
- **Instruction**: Open "Proposal_L2_07.docx". Change the color of all heading text to dark blue (#003366). Also underline the body text under the "Objectives" section.
- **Material File**: `Proposal_L2_07.docx`
- **Evaluation Function**: `compare_docx_files`
- **Gold File**: `Proposal_L2_07_gold.docx`

#### Task L3-12: Report_L2_06

- **ID**: `916c6ea4-3099-4aa8-b968-485ff5b03fb9`
- **Source**: `writer_hard`
- **Instruction**: Open "Report_L2_06.docx". Center-align the document title. After the paragraph starting with "Total revenue reached", insert a table with 4 rows and 3 columns. Headers: "Metric", "2024", "2025". Data rows: Revenue/$38.3M/$45.2M, Net Income/$5.9M/$8.1M, Cash Position/$9.8M/$12.4M.
- **Material File**: `Report_L2_06.docx`
- **Evaluation Function**: `compare_docx_files`
- **Gold File**: `Report_L2_06_gold.docx`

#### Task L3-13: Report_L3_01

- **ID**: `97d8736f-8d91-48ef-a299-256e11c742fb`
- **Source**: `writer_hard`
- **Instruction**: Open "Report_L3_01.docx" and perform ALL: (1) Center-align the document title. (2) Set title font to 24pt bold. (3) Change all body text to Times New Roman 12pt. (4) Make all section headings (Heading 1) dark blue (#003366). (5) Make the body text under "5. Strategic Outlook" bold. (6) Add at the end: "This report was reviewed and approved by the Board of Directors on March 31, 2025."
- **Material File**: `Report_L3_01.docx`
- **Evaluation Function**: `compare_docx_files`
- **Gold File**: `Report_L3_01_gold.docx`

#### Task L3-14: Policy_L3_04

- **ID**: `cd8b1536-0d23-4ffc-b4d1-2e534ac4bf9e`
- **Source**: `writer_hard`
- **Instruction**: Open "Policy_L3_04.docx" and do ALL: (1) Center title, set to 22pt bold. (2) Convert all section heading text to uppercase. (3) Set all body text to Times New Roman 11pt. (4) Bold the body text under "4. Equipment and Security" (after uppercase conversion). (5) Add "CONFIDENTIAL - Internal Use Only" as the very first paragraph. (6) Add at the end: "Document Control: Version 3.0 | Last Updated: January 1, 2025 | Next Review: July 1, 2025"
- **Material File**: `Policy_L3_04.docx`
- **Evaluation Function**: `compare_docx_files`
- **Gold File**: `Policy_L3_04_gold.docx`

#### Task L3-15: Guide_L3_05

- **ID**: `f0e1ab09-6fbd-4b2c-a67f-ebc8717462c3`
- **Source**: `writer_hard`
- **Instruction**: Open "Guide_L3_05.docx" and do ALL: (1) Replace "TechVision Inc." with "InnovateTech Corp." (2) Center title, set to 24pt bold. (3) Make all section headings bold and dark green (#006400). (4) Set all body text to 11pt. (5) Italic the body text under "Week 4: Integration". (6) Add at end: "Questions? Contact your HR representative or email onboarding@innovatetech.com"
- **Material File**: `Guide_L3_05.docx`
- **Evaluation Function**: `compare_docx_files`
- **Gold File**: `Guide_L3_05_gold.docx`

#### L3 Task Source Annotations

| Task | Source Type | Specific Source | Annotation Reason |
|------|-----------|-----------------|-------------------|
| L3-1 | Official Help | [Text Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) | Open "Policy_L2_04.docx". Set the font size of all body text to 12pt. Additional |
| L3-2 | Official Help | [Text Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) | Open "Policy_L2_09.docx". Add the following paragraph at the very beginning of t |
| L3-3 | Official Help | [Text Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) | Open "Report_L2_01.docx". Change the font of all body text (non-heading paragrap |
| L3-4 | Official Help | [Text Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) | Open "Report_L3_06.docx" and do ALL: (1) Center title, set to 22pt, bold, dark b |
| L3-5 | Official Help | [Text Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) | Open "Meeting_L3_08.docx" and do ALL: (1) Center the title, 18pt, bold. (2) Cent |
| L3-6 | Official Help | [Text Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) | Open "Guide_L3_10.docx" and do ALL: (1) Replace "TechVision Inc." with "GlobalTe |
| L3-7 | Official Help | [Text Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) | Open "Meeting_L3_03.docx" and do ALL: (1) Center the title and set to 20pt. (2)  |
| L3-8 | Official Help | [Text Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) | Open "Proposal_L3_07.docx" and do ALL: (1) Replace "Q1 2025" with "First Quarter |
| L3-9 | Official Help | [Text Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) | Open "Policy_L3_09.docx" and do ALL: (1) Center title, 22pt, bold, dark red (#8B |
| L3-10 | Official Help | [Text Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) | Open "Proposal_L3_02.docx" and do ALL: (1) Center-align the title and the two li |
| L3-11 | Official Help | [Text Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) | Open "Proposal_L2_07.docx". Change the color of all heading text to dark blue (# |
| L3-12 | Official Help | [Tables in Text](https://help.libreoffice.org/latest/en-US/text/swriter/guide/table_insert.html) + [Headers and Footers](https://help.libreoffice.org/latest/en-US/text/swriter/guide/header_footer.html) | Open "Report_L2_06.docx". Center-align the document title. After the paragraph s |
| L3-13 | Official Help | [Text Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) | Open "Report_L3_01.docx" and perform ALL: (1) Center-align the document title. ( |
| L3-14 | Official Help | [Text Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) | Open "Policy_L3_04.docx" and do ALL: (1) Center title, set to 22pt bold. (2) Con |
| L3-15 | Official Help | [Text Formatting](https://help.libreoffice.org/latest/en-US/text/swriter/guide/text_formatting.html) | Open "Guide_L3_05.docx" and do ALL: (1) Replace "TechVision Inc." with "Innovate |

#### L3 Task Summary Table

| # | Task Name | Material File | Evaluation Function |
|---|-----------|---------------|---------------------|
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

### 3.4 Interactive Tasks (Writer) -- 26 tasks

> Interactive tasks use multi-phase design with `trigger` controlling phase transitions.


#### Scenario Type: `ambiguous_detail` (Ambiguous Detail) -- 4 tasks

> **Source Type**: Real-World Scenario | **Real-World Source**: Unclear layout details
> **Evidence**: Receives "make the title look better" without specifying font size/family/color

##### interactive_writer_005 (L3)

- **Scenario Description**: The user wants to add product specifications to the manual but hasn't provided the specific values. The agent asks first.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `agent_asks`): Help me add the product specs
  - Phase 2 (trigger: `agent_done`): Add "Weight: 250g, Dimensions: 15cm x 10cm x 3cm" at the end of the document, then save

##### interactive_writer_006 (L3)

- **Scenario Description**: The user says to update the completion rate but doesn't specify the new value. The agent asks first.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `agent_asks`): Help me update the completion rate
  - Phase 2 (trigger: `agent_done`): Change "Completion Rate: 60%%" to "Completion Rate: 85%%", then save

##### interactive_writer_007 (L3)

- **Scenario Description**: The user wants to add a closing statement to the year-end summary but doesn't say what. The agent asks first.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `agent_asks`): Help me add a closing statement to the document
  - Phase 2 (trigger: `agent_done`): Add "Thank you to all employees for your hard work and dedication this year!" at the very end of the document, then save

##### interactive_writer_008 (L2)

- **Scenario Description**: The user wants to add notes to the training manual but doesn't specify the content. The agent asks first.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `agent_asks`): Help me add the notes section
  - Phase 2 (trigger: `agent_done`): Under the "Important Notes" heading, add "1. Please back up all data in advance", then save


#### Scenario Type: `ambiguous_instruction` (Ambiguous Instruction) -- 1 tasks

> **Source Type**: Real-World Scenario | **Real-World Source**: Vague document instructions
> **Evidence**: Receives "this document is not professional enough", agent must clarify

##### interactive_writer_ambiguous_001 (L1)

- **Scenario Description**: The instruction is missing information the agent cannot infer; the agent must ask the user before proceeding.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me add what we agreed earlier to the end of the document
  - Phase 2 (trigger: `agent_done`): in document's the very endtwo rows, add "Author: Zhang San""Reviewer: Li Si", then save the file


#### Scenario Type: `ambiguous_scope` (Ambiguous Scope) -- 4 tasks

> **Source Type**: Real-World Scenario | **Real-World Source**: Uncertain document edit scope
> **Evidence**: Receives "edit this report" without specifying which sections

##### interactive_writer_009 (L2)

- **Scenario Description**: The notice contains multiple dates. The user says to update the date but doesn't specify which one. The agent asks, then only changes the publication date.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `agent_asks`): Help me update the date in the file
  - Phase 2 (trigger: `agent_done`): Only update the Publication Date on the first line to "July 1, 2025", leave all other dates unchanged, then save

##### interactive_writer_010 (L1)

- **Scenario Description**: The user wants to add department info to an employee record but doesn't say which one. The agent asks, then only modifies the first record.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `agent_asks`): Help me add the department info
  - Phase 2 (trigger: `agent_done`): Only add "Department: Engineering" after the first employee record (E001), then save

##### interactive_writer_011 (L1)

- **Scenario Description**: The task list has multiple tasks. The user says to update the status but doesn't say which one. The agent asks, then only changes the first task.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `agent_asks`): Help me update the status
  - Phase 2 (trigger: `agent_done`): Only change the first task (Requirements Document Review) status from "In Progress" to "Completed", leave others unchanged, then save

##### interactive_writer_012 (L2)

- **Scenario Description**: The meeting minutes cover multiple agenda items. The user wants to add a resolution but doesn't say which item. The agent asks, then only adds it under the first item.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `agent_asks`): Help me add a resolution to the minutes
  - Phase 2 (trigger: `agent_done`): Only add "Resolution: Approved Plan A" under Agenda Item 1, then save


#### Scenario Type: `ambiguous_target` (Ambiguous Target) -- 4 tasks

> **Source Type**: Real-World Scenario | **Real-World Source**: Vague document editing requests
> **Evidence**: Receives "fix the formatting" without specifying paragraphs or styles

##### interactive_writer_001 (L3)

- **Scenario Description**: The user wants to add the recorder's name to the meeting minutes but doesn't say who. The agent must ask for the specific name before filling it in.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `agent_asks`): Help me add that person's name to the minutes
  - Phase 2 (trigger: `agent_done`): Write "Wang Fang" on the "Recorded by:" line, then save

##### interactive_writer_002 (L3)

- **Scenario Description**: The user wants to change a deadline in the project plan but doesn't say which one. The agent asks before making the change.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `agent_asks`): Help me change the deadline
  - Phase 2 (trigger: `agent_done`): Change the first deadline to "June 30, 2025", then save

##### interactive_writer_003 (L2)

- **Scenario Description**: The user wants to fill in Party B's information on the contract draft but hasn't provided the company name. The agent asks first.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `agent_asks`): Help me fill in Party B's info
  - Phase 2 (trigger: `agent_done`): Write "Beijing Tech Solutions Ltd." on the "Party B:" line, then save

##### interactive_writer_004 (L2)

- **Scenario Description**: The user wants to add a contact person at the end of the work report but doesn't say who. The agent asks first.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `agent_asks`): Help me add that contact person
  - Phase 2 (trigger: `agent_done`): Add "Contact: Chen Gang" at the end of the document, then save


#### Scenario Type: `error_correction` (Error Correction) -- 2 tasks

> **Source Type**: Real-World Scenario | **Real-World Source**: Format error correction
> **Evidence**: Font/indent inconsistencies found, requiring uniform correction

##### interactive_writer_error_correction_001 (L3)

- **Scenario Description**: User asks agent to add a disclaimer at the end, but agent puts it at the beginning. User corrects.
- **Phases**: 3
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Add a disclaimer to the document: 'This policy is subject to annual review.'
  - Phase 2 (trigger: `agent_done`): Wait, I wanted the disclaimer at the END of the document, not where you put it. Please move it to the very last line.
  - Phase 3 (trigger: `agent_done`): Now also add 'Last updated: March 2025' right before the disclaimer. Save.

##### interactive_writer_error_correction_002 (L3)

- **Scenario Description**: User asks agent to add a signoff with a name. Agent writes it but the name is wrong. User corrects.
- **Phases**: 3
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Add 'Regards, the CEO' at the end of the memo
  - Phase 2 (trigger: `agent_done`): Please change that to 'Regards, David Chen, CEO'. I need the actual name there, not just the title.
  - Phase 3 (trigger: `agent_done`): And add 'CC: HR Department, Finance Department' on the next line after the regards. Save.


#### Scenario Type: `multi_step_workflow` (Multi-step Workflow) -- 2 tasks

> **Source Type**: Real-World Scenario | **Real-World Source**: Complete document formatting workflow
> **Evidence**: Full pipeline: title formatting, body styles, headers/footers

##### interactive_writer_workflow_001 (L3)

- **Scenario Description**: Sequential 4-step workflow: create document structure, add content, format headers, add footer.
- **Phases**: 4
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `agent_done`): Add the author name 'Prepared by: Marketing Department' at the very top of the document, before the title.
  - Phase 2 (trigger: `agent_done`): Now add a new section at the end titled 'Key Risks' with the text: 'Supply chain disruptions remain the primary concern.'
  - Phase 3 (trigger: `agent_done`): Add the date 'Date: March 2025' right after the author line you added earlier.
  - Phase 4 (trigger: `agent_done`): Finally, add 'CONFIDENTIAL' at the very end of the document. Save the file.

##### interactive_writer_workflow_002 (L3)

- **Scenario Description**: Sequential 4-step workflow: write agenda, add attendees, add action items, add disclaimer.
- **Phases**: 4
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `agent_done`): Add an 'Agenda' section with three items: '1. Q1 Financial Review', '2. Strategic Initiatives Update', '3. Budget Approval for Q2'
  - Phase 2 (trigger: `agent_done`): Add an 'Attendees' section listing: 'CEO: Robert Chen, CFO: Lisa Wang, CTO: James Liu, COO: Sarah Park'
  - Phase 3 (trigger: `agent_done`): Add an 'Action Items from Previous Meeting' section with: '1. Complete audit report - Status: Done', '2. Finalize vendor contract - Status: Pending'
  - Phase 4 (trigger: `agent_done`): Add 'Note: This document is for internal distribution only.' at the end. Save the file.


#### Scenario Type: `progressive_refinement` (Progressive Refinement) -- 4 tasks

> **Source Type**: Real-World Scenario | **Real-World Source**: Phased document revision
> **Evidence**: Start with draft formatting confirmation, then add headers/footers/styles/TOC

##### interactive_writer_013 (L1)

- **Scenario Description**: The user first asks the agent to fill in basic info on the leave request email, then provides the reason and number of days.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me fill in the basic info on the leave request email
  - Phase 2 (trigger: `agent_done`): Fill in the leave reason as: feeling unwell and need rest, and number of days: 3 days, then save

##### interactive_writer_014 (L1)

- **Scenario Description**: The user first provides the meeting time for the agent to fill in, then provides the meeting location.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me fill in the meeting time: August 15, 2025 at 9:00 AM
  - Phase 2 (trigger: `agent_done`): Now add the meeting location: Main Conference Hall, 1st Floor, then save

##### interactive_writer_015 (L2)

- **Scenario Description**: The user first provides the product name for the agent to fill in, then provides the product number.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me fill in the product name: Smart Thermostat Pro
  - Phase 2 (trigger: `agent_done`): Now add the product number: TC-2025-001, then save

##### interactive_writer_016 (L2)

- **Scenario Description**: The user first asks the agent to fill in this year's achievements, then adds next year's work plan.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me add this year's main achievement: Delivered 3 major projects
  - Phase 2 (trigger: `agent_done`): Now add next year's plan: Expand into new markets and add two product lines, then save


#### Scenario Type: `requirement_change` (Requirement Change) -- 4 tasks

> **Source Type**: Real-World Scenario | **Real-World Source**: Document requirement change
> **Evidence**: Mid-formatting request to change heading levels or add new sections

##### interactive_writer_017 (L2)

- **Scenario Description**: The user first asks the agent to add project lead Zhang Ming, then says the name was wrong and should be Zhang Qiang.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me add "Project Lead: Zhang Ming" at the end of the report
  - Phase 2 (trigger: `agent_done`): The name was wrong, change it to "Project Lead: Zhang Qiang", then save

##### interactive_writer_018 (L1)

- **Scenario Description**: The user first asks the agent to change the contract title to '2025 Procurement Contract', then says it should be more formal: '2025 Annual Strategic Procurement Contract'.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me add a title line: "2025 Procurement Contract"
  - Phase 2 (trigger: `agent_done`): The title should be more formal, change it to "2025 Annual Strategic Procurement Contract", then save

##### interactive_writer_019 (L3)

- **Scenario Description**: The user first asks the agent to add a contact name, then says a phone number should also be included.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me add "Contact: Wang Xiaoming" to the notice
  - Phase 2 (trigger: `agent_done`): Need to add the phone number too, change it to "Contact: Wang Xiaoming, Phone: 010-12345678", then save

##### interactive_writer_020 (L1)

- **Scenario Description**: The user first says Q4 target is 110%%, then changes it to 120%%.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me add the Q4 target to the plan: Achieve 110%% of annual sales
  - Phase 2 (trigger: `agent_done`): Set the target higher, change it to 120%%, then save


#### Scenario Type: `task_interruption` (Task Interruption) -- 1 tasks

> **Source Type**: Real-World Scenario | **Real-World Source**: Document editing interruption
> **Evidence**: During editing told to add table or modify completed sections

##### interactive_writer_interruption_001 (L3)

- **Scenario Description**: The user interrupts the main document task for a side request, then returns to continue the original editing task.
- **Phases**: 3
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `agent_done`): Help me document's title"Overview"change "Project overview"
  - Phase 2 (trigger: `agent_done`): Wait, first Help me check how much disk space is left, openusing df -h
  - Phase 3 (trigger: `agent_done`): OK, , go back to that document, Help me in "Project overview"belowone row write "This report summarizes key 2025 progress", Then save the file

#### Interactive Task Source Mapping

| Scenario Type | Count | Real-World Source | Evidence | Trigger Combo |
|--------------|-------|-------------------|----------|---------------|
| `ambiguous_detail` (Ambiguous Detail) | 4 | Unclear layout details | Receives "make the title look better" without specifying fon | agent_asks + agent_done |
| `ambiguous_instruction` (Ambiguous Instruction) | 1 | Vague document instructions | Receives "this document is not professional enough", agent m | agent_done + step_count |
| `ambiguous_scope` (Ambiguous Scope) | 4 | Uncertain document edit scope | Receives "edit this report" without specifying which section | agent_asks + agent_done |
| `ambiguous_target` (Ambiguous Target) | 4 | Vague document editing requests | Receives "fix the formatting" without specifying paragraphs  | agent_asks + agent_done |
| `error_correction` (Error Correction) | 2 | Format error correction | Font/indent inconsistencies found, requiring uniform correct | agent_done + step_count |
| `multi_step_workflow` (Multi-step Workflow) | 2 | Complete document formatting workflow | Full pipeline: title formatting, body styles, headers/footer | agent_done |
| `progressive_refinement` (Progressive Refinement) | 4 | Phased document revision | Start with draft formatting confirmation, then add headers/f | agent_done + step_count |
| `requirement_change` (Requirement Change) | 4 | Document requirement change | Mid-formatting request to change heading levels or add new s | agent_done + step_count |
| `task_interruption` (Task Interruption) | 1 | Document editing interruption | During editing told to add table or modify completed section | agent_done |

#### Interactive Trigger Type Distribution

| Trigger Type | Count | Description |
|-------------|-------|-------------|
| `agent_done` | 36 | Automatically enters next phase when previous phase completes |
| `agent_asks` | 12 | Triggered when agent proactively asks user for clarification |
| `step_count` | 11 | Injects new instructions after reaching specified step count |

#### Interactive Task Source Mapping

| Scenario Type | Real-World Source | Evidence Package | Task JSON `source` |
|--------------|-------------------|------------------|--------------------|
| `ambiguous_target` | Vague document edit request | ① Original request ② Clarification ③ Execution | `writer_interactive;source_type=document_edit;evidence=ambiguous_target` |
| `ambiguous_detail` | Unclear formatting details | ① Request ② Detail Q&A ③ Confirmation | `writer_interactive;source_type=formatting;evidence=detail_clarification` |
| `progressive_refinement` | Staged document revision | ① Draft ② Confirmation ③ Refinement | `writer_interactive;source_type=revision;evidence=staged_refinement` |
| `requirement_change` | Mid-task requirement change | ① Initial ② Change order ③ Diff record | `writer_interactive;source_type=change;evidence=requirement_change` |

#### Source Evidence Fields

- **source_type**: `document_edit` / `formatting` / `revision` / `change` / `format_fix` / `workflow`
- **source_ref**: Source identifier (anonymized URL, ticket ID, interview record ID)
- **captured_at**: Evidence capture date (`YYYY-MM-DD`)
- **anonymized_excerpt**: Anonymized original text excerpt (1-3 sentences)
- **mapping_note**: How the original requirement maps to `phases` and `trigger`
- **reviewers**: Dual-review and adjudication record (`reviewer_a/reviewer_b/adjudicator`)

---

## 4. Evaluation Function Summary

| # | Function | Category | Usage Count |
|---|----------|----------|-------------|
| 1 | `compare_docx_files` | Static Tasks | 20 |
| 2 | `check_include_exclude` | Interactive Tasks | 26 |

**Total**: Covering 20 static tasks + 26 interactive tasks = **46** tasks.

---

## 5. Material Description

| Property | Value |
|----------|-------|
| File Format | `.docx` (Office Open XML Document) |
| Total Files | 20 initial + 20 gold files |
| Language | English content |
| Doc Types | Meeting notes, policies, guides, proposals, reports |

---

## 6. Task JSON Template

```json
{
  "evaluator": {
    "func": "compare_docx_files",
    "expected": {"type": "cache_file", "path": "<file>_gold.docx"},
    "result": {"type": "vm_file", "path": "/home/user/Desktop/<file>.docx", "dest": "<file>.docx"}
  }
}
```

---

## 7. Docker Image Requirements

- **LibreOffice Writer** (7.x+), **X11**, **Python 3 + python-docx**

---

## 8. Difficulty Distribution Summary

| Level | Count | Instruction Length | Operation Steps | Description | Examples |
|-------|-------|-------------------|----------------|-------------|---------|
| L1 | 5 | 134-149 chars | 1-2 steps | Single format ops | Center-align + page break, font replace, color change, text replace + bold |
| L2 | 5 | 153-346 chars | 2-4 steps | Multi-step compound ops | Font size + italic section, paragraph insert + uppercase, table insert + center |
| L3 | 10 | 309-441 chars | 5-6 steps (numbered sub-steps) | Complex workflows | Title center+22pt+bold+color+body font+italic+footer (6-step combo) |
| **Total** | **20** | | | | |

### Verifiability Guarantee

1. **`.docx` structured comparison** via `python-docx`. No screenshot/OCR dependency.
2. Flexible matching: `ignore_blanks`, `fuzzy_match`, `content_only`.

> Difficulty tags based on kimi-k2.5 model execution results.

---

## 9. Common Pitfalls

- **Save dialog**: `.docx` also triggers "Keep Current Format?" — press `Enter` after `Ctrl+S`.
- **Paragraph splitting**: LibreOffice and Word may handle blank lines differently.
- **Gold files**: Must exist in both `OSWorld/cache/` and `desktopworld/cache/`.
