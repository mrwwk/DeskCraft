# LibreOffice Writer Task Design Document

## 0. Verification Strategy

LibreOffice Writer tasks are evaluated by downloading the user-edited file from the VM and comparing it against a reference result.

1. Static `.docx` tasks use `compare_docx_files` from `desktop_env/evaluators/metrics/docs.py`.
2. Interactive text-based tasks use `check_include_exclude` against the saved VM text file.

Current scope after cleanup:

- Static tasks kept in this directory: `20`
- Interactive tasks kept in this directory: `11`
- Tasks moved to backup: `25`
- Backup location: `evaluation_examples/examples/libreoffice_writ_njc/backup/`

The cleanup removed low-quality prompts and repetitive interaction patterns first, while keeping the remaining overall difficulty mix close to balanced.

---

## 1. Static Task Inventory

### 1.1 Level 1 (L1) -- 4 tasks

| ID | Material File | Summary |
|---|---|---|
| `1edb1468-53dd-47d5-a713-005fdd910c87` | `InternalMemo_L1_02.docx` | Center-align the document title. |
| `54c085b5-02be-4258-9b96-f1e9528b2533` | `AnnualReport_L1_04.docx` | Replace all occurrences of `2024` with `2025`. |
| `7ad5f702-1121-43f8-8707-b57a0f2f643a` | `RemotePolicy_L1_03.docx` | Change all body text font to `Arial`. |
| `c1e0cd7a-e112-446b-a855-563a3aa9be0f` | `AnnualReport_L1_01.docx` | Make all section headings bold. |

### 1.2 Level 2 (L2) -- 7 tasks

| ID | Material File | Summary |
|---|---|---|
| `0348a68c-a33e-47e9-9e07-d189c43e9bec` | `Meeting_L2_03.docx` | Strikethrough the last action item and append a summary paragraph. |
| `1cd80191-f69d-4d57-9197-e10d0c8fbbce` | `Policy_L2_04.docx` | Set all body text to `12pt` and italicize section `5. Communication Standards`. |
| `247db8e9-9fd2-49a6-85f9-b53854f64c47` | `Policy_L2_09.docx` | Insert a disclaimer paragraph at the beginning and uppercase all section headings. |
| `7e3f78c5-9230-47cd-909f-5063da80ae89` | `Proposal_L2_07.docx` | Turn all headings dark blue and underline the body text under `Objectives`. |
| `916c6ea4-3099-4aa8-b968-485ff5b03fb9` | `Report_L2_06.docx` | Center the title and insert a `4 x 3` metrics table after the revenue paragraph. |
| `aaa6abac-4bde-47ea-805a-08da32e7a1e1` | `Proposal_L2_02.docx` | Center the title and insert a page break before `Budget`. |
| `ddc06ab7-075d-47e8-8d70-c88b88605ddf` | `Guide_L2_10.docx` | Set the title to `24pt` and append the HR contact paragraph. |

### 1.3 Level 3 (L3) -- 9 tasks

| ID | Material File | Summary |
|---|---|---|
| `2b672d35-1c0f-4a71-bb85-f32b5ad8b46d` | `Report_L3_06.docx` | Multi-step report formatting with title styling, heading styling, body font normalization, emphasis, and closing line. |
| `3cf4aa78-196b-4654-a632-7f8c0b52c8e1` | `Meeting_L3_08.docx` | Multi-step meeting-minutes cleanup with title, attendees, headings, action items, body font, and footer line. |
| `3dad2051-0596-4886-93c5-9ed78df81f99` | `Guide_L3_10.docx` | Global replacement plus title, heading, body, section emphasis, and trailing metadata edits. |
| `409f8738-31ec-406f-898f-01ed419b74b4` | `Meeting_L3_03.docx` | Title edit, global quarter replacements, attendee formatting, action-item italics, heading color, and ending marker. |
| `43b0833a-2da6-43e7-a8e3-93790bc2579a` | `Proposal_L3_07.docx` | Multiple date-text replacements, title formatting, heading color change, body font change, and final approval note. |
| `5186c84c-c3c2-4792-8349-61572a1ab7b3` | `Policy_L3_09.docx` | Title styling, heading styling, body font change, section italics, prefix warning, and footer metadata. |
| `5cc2c306-2768-4e26-8f19-2717b474694b` | `Proposal_L3_02.docx` | Title block alignment, heading color/bold, body sizing, section italics, and approval line insertion. |
| `cd8b1536-0d23-4ffc-b4d1-2e534ac4bf9e` | `Policy_L3_04.docx` | Title styling, uppercase headings, body font normalization, targeted bolding, first-paragraph warning, and trailing control line. |
| `f0e1ab09-6fbd-4b2c-a67f-ebc8717462c3` | `Guide_L3_05.docx` | Company replacement, title/heading formatting, body sizing, targeted italics, and final contact note. |

---

## 2. Interactive Task Inventory

### 2.1 Remaining Interactive Tasks -- 11 tasks

| Task ID | Level | Scenario Type | Phases | Summary |
|---|---|---|---|---|
| `interactive_writer_010` | `L1` | `ambiguous_scope` | 2 | Clarify which employee record to update, then add the department only for `E001`. |
| `interactive_writer_011` | `L1` | `ambiguous_scope` | 2 | Clarify which task status to update, then only complete the first task. |
| `interactive_writer_013` | `L1` | `progressive_refinement` | 2 | Fill leave-request details after the user later provides reason and duration. |
| `interactive_writer_014` | `L1` | `progressive_refinement` | 2 | Fill meeting time first, then add the meeting location. |
| `interactive_writer_018` | `L1` | `requirement_change` | 2 | Add an initial contract title, then revise it to a more formal version. |
| `interactive_writer_020` | `L1` | `requirement_change` | 2 | Add a Q4 target, then update it from `110%` to `120%`. |
| `interactive_writer_003` | `L2` | `ambiguous_target` | 2 | Ask for Party B details, then fill the contract party line. |
| `interactive_writer_008` | `L2` | `ambiguous_detail` | 2 | Ask what note to add, then insert the requested note under `Important Notes`. |
| `interactive_writer_017` | `L2` | `requirement_change` | 2 | Add a project lead line, then correct the name. |
| `interactive_writer_error_correction_001` | `L3` | `error_correction` | 3 | Recover from a wrong placement by moving the disclaimer to the end and inserting an update line before it. |
| `interactive_writer_workflow_001` | `L3` | `multi_step_workflow` | 4 | Execute a staged document-edit workflow with top insertion, end section, date insertion, and final footer text. |

### 2.2 Interactive Scenario Distribution

| Scenario Type | Count |
|---|---|
| `ambiguous_scope` | 2 |
| `progressive_refinement` | 2 |
| `requirement_change` | 3 |
| `ambiguous_target` | 1 |
| `ambiguous_detail` | 1 |
| `error_correction` | 1 |
| `multi_step_workflow` | 1 |

---

## 3. Evaluation Functions

| Function | Task Type | Usage Count |
|---|---|---|
| `compare_docx_files` | Static Writer tasks | 20 |
| `check_include_exclude` | Interactive Writer tasks | 11 |

---

## 4. Difficulty Distribution

### 4.1 Static Tasks

| Level | Count |
|---|---|
| `L1` | 4 |
| `L2` | 7 |
| `L3` | 9 |

### 4.2 Interactive Tasks

| Level | Count |
|---|---|
| `L1` | 6 |
| `L2` | 3 |
| `L3` | 2 |

### 4.3 Overall Remaining Set

| Level | Count |
|---|---|
| `L1` | 10 |
| `L2` | 10 |
| `L3` | 11 |
| **Total** | **31** |

This remaining set is close to difficulty-balanced overall while still preserving higher-signal Writer coverage.

---

## 5. Notes

- Static task assets remain `.docx` files with paired gold documents.
- Interactive tasks remain text-based and are evaluated through content inclusion/exclusion rules.
- The backup folder is intended to retain removed tasks for later recovery or re-review, not for active sampling.
