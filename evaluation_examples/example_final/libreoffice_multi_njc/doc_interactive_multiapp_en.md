# Cross-Application Interactive Task Design Document

## 0. Overview

This document covers cross-application (Multi-App) interactive tasks.
The core characteristic of these tasks is the need to transfer information and collaborate across multiple applications.

**Total Tasks**: 25

### Task Distribution

| Category | Count | Applications |
|----------|-------|-------------|
| Writer to Calc (w2c) | 11 | LibreOffice Writer + Calc |
| Writer to Impress (w2i) | 0 | LibreOffice Writer + Impress |
| Calc to Writer (c2w) | 14 | LibreOffice Calc + Writer |
| Calc to Impress (c2i) | 0 | LibreOffice Calc + Impress |

## 1. Verification Strategy

Cross-application tasks use `check_include_exclude`,
checking whether output file content on the VM contains expected keywords.

## 2. Evaluation Functions

| Function | Description | Usage Count |
|----------|-------------|-------------|
| `check_include_exclude` | Verify CLI output contains/excludes specified strings | 25 |

## 3. Task Definitions

### Writer to Calc (w2c) -- 11 tasks

> **Source Type**: Real-World Scenario | **Real-World Source**: Extracting meeting notes/text to spreadsheets
> **Evidence**: Project managers extract action items and budget data from meeting records into Excel

#### interactive_multiapp_w2c_001 (L3)

- **Overview Instruction**: Help me fill the Q2 targets from the meeting minutes into the spreadsheet
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me fill the Q2 targets from the meeting minutes into the spreadsheet
  - Phase 2 (trigger: `agent_done`): Fill the Q2 target information from /home/user/Desktop/meeting_record.txt into /home/user/Desktop/q2_targets.xlsx row 2: A2='Q2 Sales Target', B2='Zha

#### interactive_multiapp_w2c_002 (L3)

- **Overview Instruction**: Help me register the project information in the spreadsheet
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me register the project information in the spreadsheet
  - Phase 2 (trigger: `agent_done`): Fill the project information from /home/user/Desktop/project_brief.txt into /home/user/Desktop/project_register.xlsx row 2: A2='PRJ-2025-008', B2='Sma

#### interactive_multiapp_w2c_003 (L3)

- **Overview Instruction**: Fill the telesales data into the statistics table
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Fill the telesales data into the statistics table
  - Phase 2 (trigger: `agent_done`): Fill the data from /home/user/Desktop/sales_calls.txt into /home/user/Desktop/call_stats.xlsx row 2: A2='Chen Jing', B2=128, C2=89, D2=69.5, E2=8, F2=

#### interactive_multiapp_w2c_005 (L3)

- **Overview Instruction**: Help me enter the new employee information into the roster
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me enter the new employee information into the roster
  - Phase 2 (trigger: `agent_done`): Fill the onboarding information from /home/user/Desktop/employee_onboard.txt into /home/user/Desktop/employee_roster.xlsx row 2: A2='EMP20250316', B2=

#### interactive_multiapp_w2c_007 (L3)

- **Overview Instruction**: Help me enter the order information into the tracker
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me enter the order information into the tracker
  - Phase 2 (trigger: `agent_done`): Fill the order information from /home/user/Desktop/order_detail.txt into /home/user/Desktop/order_tracker.xlsx row 2: A2='SO-20250315-0088', B2='Shang

#### interactive_multiapp_w2c_009 (L3)

- **Overview Instruction**: Help me register the IT asset in the asset ledger
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me register the IT asset in the asset ledger
  - Phase 2 (trigger: `agent_done`): Fill the asset information from /home/user/Desktop/it_asset.txt into /home/user/Desktop/asset_register.xlsx row 2: A2='IT-2025-00456', B2='Laptop', C2

#### interactive_multiapp_w2c_010 (L3)

- **Overview Instruction**: Enter the supplier audit results into the ledger
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Enter the supplier audit results into the ledger
  - Phase 2 (trigger: `agent_done`): Fill the audit results from /home/user/Desktop/supplier_audit.txt into /home/user/Desktop/supplier_audit_log.xlsx row 2: A2='Eastern Precision Parts C

#### interactive_multiapp_w2c_012 (L3)

- **Overview Instruction**: Help me enter the bug information into the bug tracker
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me enter the bug information into the bug tracker
  - Phase 2 (trigger: `agent_done`): Fill the bug information from /home/user/Desktop/bug_report.txt into /home/user/Desktop/bug_tracker.xlsx row 2: A2='BUG-2025-0312', B2='User Center - 

#### interactive_multiapp_w2c_015 (L3)

- **Overview Instruction**: Help me enter the marketing campaign into the campaign tracker
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me enter the marketing campaign into the campaign tracker
  - Phase 2 (trigger: `agent_done`): Fill the campaign information from /home/user/Desktop/marketing_event.txt into /home/user/Desktop/campaign_tracker.xlsx row 2: A2='MKT-2025-S03', B2='

#### interactive_multiapp_w2c_016 (L3)

- **Overview Instruction**: Record the client visit information in the ledger
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Record the client visit information in the ledger
  - Phase 2 (trigger: `agent_done`): Fill the visit information from /home/user/Desktop/client_visit.txt into /home/user/Desktop/visit_record.xlsx row 2: A2='2025-03-14', B2='North China 

#### interactive_multiapp_w2c_020 (L3)

- **Overview Instruction**: Help me enter the sales forecast data into the forecast table
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me enter the sales forecast data into the forecast table
  - Phase 2 (trigger: `agent_done`): Fill the forecast data from /home/user/Desktop/sales_forecast.txt into /home/user/Desktop/forecast_table.xlsx rows 2-4: A2='North Region', B2=480, C2=

### Writer to Impress (w2i) -- 0 tasks

> **Source Type**: Real-World Scenario | **Real-World Source**: Converting text materials to presentation summaries
> **Evidence**: Extracting key points from team reports to create presentation slides

### Calc to Writer (c2w) -- 14 tasks

> **Source Type**: Real-World Scenario | **Real-World Source**: Summarizing spreadsheet data into text reports
> **Evidence**: Generating text-based sales summaries from sales data tables

#### interactive_multiapp_c2w_001 (L3)

- **Overview Instruction**: Help me summarize the sales data
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me summarize the sales data
  - Phase 2 (trigger: `agent_done`): Find the employee with the highest total sales across three months from /home/user/Desktop/q1_sales.xlsx, append a line to /home/user/Desktop/sales_su

#### interactive_multiapp_c2w_002 (L1)

- **Overview Instruction**: Help me record the monthly revenue
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me record the monthly revenue
  - Phase 2 (trigger: `agent_done`): Find the month with the highest revenue from /home/user/Desktop/monthly_revenue.xlsx, append to /home/user/Desktop/revenue_report.txt: 'Highest Revenu

#### interactive_multiapp_c2w_003 (L1)

- **Overview Instruction**: Record the employee evaluation results
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Record the employee evaluation results
  - Phase 2 (trigger: `agent_done`): Find employees rated 'Excellent' from /home/user/Desktop/employee_kpi.xlsx, append to /home/user/Desktop/kpi_record.txt: 'Excellent Employees: Liu Yan

#### interactive_multiapp_c2w_005 (L3)

- **Overview Instruction**: Help me organize the inventory status
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me organize the inventory status
  - Phase 2 (trigger: `agent_done`): Find products with stock below safety stock from /home/user/Desktop/inventory.xlsx, append to /home/user/Desktop/stock_alert.txt: 'Stock Alert: Phone 

#### interactive_multiapp_c2w_006 (L2)

- **Overview Instruction**: Help me record the contract information
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me record the contract information
  - Phase 2 (trigger: `agent_done`): Find the contract with the largest amount from /home/user/Desktop/contract_list.xlsx, append to /home/user/Desktop/contract_notes.txt: 'Largest Contra

#### interactive_multiapp_c2w_008 (L2)

- **Overview Instruction**: Help me record the training results
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me record the training results
  - Phase 2 (trigger: `agent_done`): Find the course with the highest pass rate from /home/user/Desktop/training_scores.xlsx, append to /home/user/Desktop/training_summary.txt: 'Highest P

#### interactive_multiapp_c2w_009 (L3)

- **Overview Instruction**: Help me organize the customer feedback
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me organize the customer feedback
  - Phase 2 (trigger: `agent_done`): Count the number of customers with a score >= 4 from /home/user/Desktop/customer_feedback.xlsx, append to /home/user/Desktop/feedback_digest.txt: 'Hig

#### interactive_multiapp_c2w_010 (L2)

- **Overview Instruction**: Help me record the sales channel performance
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me record the sales channel performance
  - Phase 2 (trigger: `agent_done`): Find the channel with the highest conversion rate from /home/user/Desktop/sales_channels.xlsx, append to /home/user/Desktop/channel_report.txt: 'Highe

#### interactive_multiapp_c2w_012 (L3)

- **Overview Instruction**: Help me organize the department expenses
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me organize the department expenses
  - Phase 2 (trigger: `agent_done`): Calculate the total expense for Marketing Dept from /home/user/Desktop/expense_report.xlsx, append to /home/user/Desktop/expense_memo.txt: 'Marketing 

#### interactive_multiapp_c2w_013 (L2)

- **Overview Instruction**: Help me record the product sales data
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me record the product sales data
  - Phase 2 (trigger: `agent_done`): Find the product with the lowest return rate from /home/user/Desktop/product_sales.xlsx, append to /home/user/Desktop/product_summary.txt: 'Lowest Ret

#### interactive_multiapp_c2w_015 (L2)

- **Overview Instruction**: Help me record the store performance
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me record the store performance
  - Phase 2 (trigger: `agent_done`): Find the store with the highest monthly sales from /home/user/Desktop/store_data.xlsx, append to /home/user/Desktop/store_report.txt: 'Top Sales Store

#### interactive_multiapp_c2w_016 (L3)

- **Overview Instruction**: Help me summarize the HR headcount
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me summarize the HR headcount
  - Phase 2 (trigger: `agent_done`): Find the department with the highest net headcount increase (hires minus departures) from /home/user/Desktop/hr_headcount.xlsx, append to /home/user/D

#### interactive_multiapp_c2w_017 (L2)

- **Overview Instruction**: Help me organize the logistics information
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me organize the logistics information
  - Phase 2 (trigger: `agent_done`): Find the order with the lowest freight from /home/user/Desktop/logistics.xlsx, append to /home/user/Desktop/logistics_memo.txt: 'Lowest Freight Order:

#### interactive_multiapp_c2w_019 (L3)

- **Overview Instruction**: Help me summarize the supplier evaluation
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me summarize the supplier evaluation
  - Phase 2 (trigger: `agent_done`): Find the A-rated supplier with the highest on-time delivery rate from /home/user/Desktop/supplier_info.xlsx, append to /home/user/Desktop/supplier_not

### Calc to Impress (c2i) -- 0 tasks

> **Source Type**: Real-World Scenario | **Real-World Source**: Converting KPI data to presentation summaries
> **Evidence**: Extracting key metrics from KPI tables for management briefing

## 4. Source Mapping Summary

| Category | Count | Source Type | Real-World Source | Evidence |
|----------|-------|-----------|-------------------|----------|
| Writer to Calc (w2c) | 11 | Real-World Scenario | Extracting meeting notes/text to spreadsheets | Project managers extract action items and budget data from m |
| Writer to Impress (w2i) | 0 | Real-World Scenario | Converting text materials to presentation summaries | Extracting key points from team reports to create presentati |
| Calc to Writer (c2w) | 14 | Real-World Scenario | Summarizing spreadsheet data into text reports | Generating text-based sales summaries from sales data tables |
| Calc to Impress (c2i) | 0 | Real-World Scenario | Converting KPI data to presentation summaries | Extracting key metrics from KPI tables for management briefi |

## 5. Material Description

| Property | Value |
|----------|-------|
| File Formats | `.docx` (Writer), `.xlsx` (Calc), `.pptx` (Impress) |
| Initial Files | Shared from single-app task material files |
| Gold Files | Not used (verification via CLI output keyword matching) |
| Language | English content |
| Scenarios | Meeting extraction, report summarization, KPI visualization |

---

## 6. Task JSON Templates

### Cross-Application Interactive Task

```json
{
  "id": "interactive_multiapp_w2c_01",
  "instruction": "Extract the action items from the meeting notes...",
  "config": [
    {"type": "copyfile_from_host_to_guest", "parameters": {"src": "evaluation_examples/examples/multiapp/w2c_01/meeting_notes.docx", "dest": "/home/user/meeting_notes.docx"}},
    {"type": "open", "parameters": {"path": "/home/user/meeting_notes.docx"}}
  ],
  "evaluator": {
    "func": "check_include_exclude",
    "result": {"type": "vm_command_line", "command": "cat /home/user/output.csv"},
    "expected": {"type": "rule", "rules": {"include": ["Action Item", "Budget"], "exclude": ["DRAFT"]}}
  },
  "scenario_type": "progressive_refinement",
  "phases": [
    {"instruction": "Phase 1: Read the meeting notes and extract action items to a new Calc spreadsheet."},
    {"instruction": "Phase 2: Add a budget column and sort by priority."}
  ],
  "trigger": [
    {"type": "agent_done"},
    {"type": "agent_done"}
  ]
}
```

---

## 7. Source Evidence Fields (Recommended Standard)

- **source_type**: `meeting_extraction` / `report_summarization` / `kpi_visualization`
- **source_ref**: Source identifier (anonymized URL, ticket ID, interview record ID)
- **captured_at**: Evidence capture date (`YYYY-MM-DD`)
- **anonymized_excerpt**: Anonymized original text excerpt (1-3 sentences)
- **mapping_note**: How the original requirement maps to `phases` and `trigger`
- **reviewers**: Dual-review and adjudication record (`reviewer_a/reviewer_b/adjudicator`)

---

## 8. Docker Image Requirements

- **LibreOffice Full Suite** (Calc + Writer + Impress, 7.x+ recommended)
- **X11 display environment**
- **Python 3** (evaluator runtime)

---

## 9. Difficulty Distribution Summary

| L1 | L2 | L3 | Total |
|----|----|----|-------|
| 2 | 6 | 17 | 25 |

### Verifiability Guarantee

1. **CLI Output Verification**: `check_include_exclude` runs commands on the VM (e.g., `cat`/`python3 -c`) to check file content for expected keywords.
2. **No Visual Dependency**: All verification is based on programmatic file content checks — no screenshot or OCR.

> Difficulty tags based on kimi-k2.5 model execution under max_steps=80.

---

## 10. Common Pitfalls

### Cross-Application Data Transfer
- **Path consistency**: File paths written in Phase 1 must exactly match paths read in Phase 2.
- **App switch delay**: Switching from Writer to Calc requires waiting for the new window to fully load.
- **Save timing**: Files must be saved before each phase ends, otherwise the next phase reads stale content.

### UserSimulator Configuration
- Interactive tasks depend on `UserSimulator` (LLM-driven); ensure vLLM service runs on `localhost:8000`.
- The `user_persona` field affects the UserSimulator's reply style and strictness.