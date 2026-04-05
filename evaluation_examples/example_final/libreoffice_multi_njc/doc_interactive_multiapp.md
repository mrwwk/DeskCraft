# 跨应用交互任务设计文档

## 0. 概述

本文档覆盖跨应用（Multi-App）交互任务。
这些任务的核心特征是需要在多个应用之间传递信息和协同工作。

**总任务数**：25

### 任务分布

| 类别 | 数量 | 涉及应用 |
|------|------|---------|
| Writer → Calc（w2c） | 11 | LibreOffice Writer + Calc |
| Writer → Impress（w2i） | 0 | LibreOffice Writer + Impress |
| Calc → Writer（c2w） | 14 | LibreOffice Calc + Writer |
| Calc → Impress（c2i） | 0 | LibreOffice Calc + Impress |

## 1. 验证策略

跨应用任务统一使用 `check_include_exclude` 评估函数，
通过在 VM 上执行命令行检查输出文件内容是否包含预期关键字来判定任务完成度。

## 2. 评估函数

| 函数名 | 描述 | 使用次数 |
|--------|------|---------|
| `check_include_exclude` | 验证命令行输出包含/排除指定字符串 | 25 |

## 3. 任务定义

### 3.x Writer → Calc（w2c） —— 11 个

> **来源类型**：现实场景构造 | **真实工作来源**：会议纪要/文本材料提取到表格
> **证据描述**：项目经理将会议记录中的行动项、预算数据提取整理到 Excel 表格中

#### interactive_multiapp_w2c_001（L3）

- **总述指令**：Help me fill the Q2 targets from the meeting minutes into the spreadsheet
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me fill the Q2 targets from the meeting minutes into the spreadsheet
  - Phase 2（trigger: `agent_done`）：Fill the Q2 target information from /home/user/Desktop/meeting_record.txt into /home/user/Desktop/q2_targets.xlsx row 2: A2='Q2 Sales Target', B2='Zha

#### interactive_multiapp_w2c_002（L3）

- **总述指令**：Help me register the project information in the spreadsheet
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me register the project information in the spreadsheet
  - Phase 2（trigger: `agent_done`）：Fill the project information from /home/user/Desktop/project_brief.txt into /home/user/Desktop/project_register.xlsx row 2: A2='PRJ-2025-008', B2='Sma

#### interactive_multiapp_w2c_003（L3）

- **总述指令**：Fill the telesales data into the statistics table
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Fill the telesales data into the statistics table
  - Phase 2（trigger: `agent_done`）：Fill the data from /home/user/Desktop/sales_calls.txt into /home/user/Desktop/call_stats.xlsx row 2: A2='Chen Jing', B2=128, C2=89, D2=69.5, E2=8, F2=

#### interactive_multiapp_w2c_005（L3）

- **总述指令**：Help me enter the new employee information into the roster
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me enter the new employee information into the roster
  - Phase 2（trigger: `agent_done`）：Fill the onboarding information from /home/user/Desktop/employee_onboard.txt into /home/user/Desktop/employee_roster.xlsx row 2: A2='EMP20250316', B2=

#### interactive_multiapp_w2c_007（L3）

- **总述指令**：Help me enter the order information into the tracker
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me enter the order information into the tracker
  - Phase 2（trigger: `agent_done`）：Fill the order information from /home/user/Desktop/order_detail.txt into /home/user/Desktop/order_tracker.xlsx row 2: A2='SO-20250315-0088', B2='Shang

#### interactive_multiapp_w2c_009（L3）

- **总述指令**：Help me register the IT asset in the asset ledger
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me register the IT asset in the asset ledger
  - Phase 2（trigger: `agent_done`）：Fill the asset information from /home/user/Desktop/it_asset.txt into /home/user/Desktop/asset_register.xlsx row 2: A2='IT-2025-00456', B2='Laptop', C2

#### interactive_multiapp_w2c_010（L3）

- **总述指令**：Enter the supplier audit results into the ledger
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Enter the supplier audit results into the ledger
  - Phase 2（trigger: `agent_done`）：Fill the audit results from /home/user/Desktop/supplier_audit.txt into /home/user/Desktop/supplier_audit_log.xlsx row 2: A2='Eastern Precision Parts C

#### interactive_multiapp_w2c_012（L3）

- **总述指令**：Help me enter the bug information into the bug tracker
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me enter the bug information into the bug tracker
  - Phase 2（trigger: `agent_done`）：Fill the bug information from /home/user/Desktop/bug_report.txt into /home/user/Desktop/bug_tracker.xlsx row 2: A2='BUG-2025-0312', B2='User Center - 

#### interactive_multiapp_w2c_015（L3）

- **总述指令**：Help me enter the marketing campaign into the campaign tracker
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me enter the marketing campaign into the campaign tracker
  - Phase 2（trigger: `agent_done`）：Fill the campaign information from /home/user/Desktop/marketing_event.txt into /home/user/Desktop/campaign_tracker.xlsx row 2: A2='MKT-2025-S03', B2='

#### interactive_multiapp_w2c_016（L3）

- **总述指令**：Record the client visit information in the ledger
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Record the client visit information in the ledger
  - Phase 2（trigger: `agent_done`）：Fill the visit information from /home/user/Desktop/client_visit.txt into /home/user/Desktop/visit_record.xlsx row 2: A2='2025-03-14', B2='North China 

#### interactive_multiapp_w2c_020（L3）

- **总述指令**：Help me enter the sales forecast data into the forecast table
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me enter the sales forecast data into the forecast table
  - Phase 2（trigger: `agent_done`）：Fill the forecast data from /home/user/Desktop/sales_forecast.txt into /home/user/Desktop/forecast_table.xlsx rows 2-4: A2='North Region', B2=480, C2=

### 3.x Writer → Impress（w2i） —— 0 个

> **来源类型**：现实场景构造 | **真实工作来源**：文本材料转演示摘要
> **证据描述**：从团队工作总结或报告中提取要点制作汇报演示

### 3.x Calc → Writer（c2w） —— 14 个

> **来源类型**：现实场景构造 | **真实工作来源**：表格数据汇总为文本报告
> **证据描述**：从销售数据表中提取关键数据生成文字版销售摘要

#### interactive_multiapp_c2w_001（L3）

- **总述指令**：Help me summarize the sales data
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me summarize the sales data
  - Phase 2（trigger: `agent_done`）：Find the employee with the highest total sales across three months from /home/user/Desktop/q1_sales.xlsx, append a line to /home/user/Desktop/sales_su

#### interactive_multiapp_c2w_002（L1）

- **总述指令**：Help me record the monthly revenue
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me record the monthly revenue
  - Phase 2（trigger: `agent_done`）：Find the month with the highest revenue from /home/user/Desktop/monthly_revenue.xlsx, append to /home/user/Desktop/revenue_report.txt: 'Highest Revenu

#### interactive_multiapp_c2w_003（L1）

- **总述指令**：Record the employee evaluation results
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Record the employee evaluation results
  - Phase 2（trigger: `agent_done`）：Find employees rated 'Excellent' from /home/user/Desktop/employee_kpi.xlsx, append to /home/user/Desktop/kpi_record.txt: 'Excellent Employees: Liu Yan

#### interactive_multiapp_c2w_005（L3）

- **总述指令**：Help me organize the inventory status
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me organize the inventory status
  - Phase 2（trigger: `agent_done`）：Find products with stock below safety stock from /home/user/Desktop/inventory.xlsx, append to /home/user/Desktop/stock_alert.txt: 'Stock Alert: Phone 

#### interactive_multiapp_c2w_006（L2）

- **总述指令**：Help me record the contract information
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me record the contract information
  - Phase 2（trigger: `agent_done`）：Find the contract with the largest amount from /home/user/Desktop/contract_list.xlsx, append to /home/user/Desktop/contract_notes.txt: 'Largest Contra

#### interactive_multiapp_c2w_008（L2）

- **总述指令**：Help me record the training results
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me record the training results
  - Phase 2（trigger: `agent_done`）：Find the course with the highest pass rate from /home/user/Desktop/training_scores.xlsx, append to /home/user/Desktop/training_summary.txt: 'Highest P

#### interactive_multiapp_c2w_009（L3）

- **总述指令**：Help me organize the customer feedback
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me organize the customer feedback
  - Phase 2（trigger: `agent_done`）：Count the number of customers with a score >= 4 from /home/user/Desktop/customer_feedback.xlsx, append to /home/user/Desktop/feedback_digest.txt: 'Hig

#### interactive_multiapp_c2w_010（L2）

- **总述指令**：Help me record the sales channel performance
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me record the sales channel performance
  - Phase 2（trigger: `agent_done`）：Find the channel with the highest conversion rate from /home/user/Desktop/sales_channels.xlsx, append to /home/user/Desktop/channel_report.txt: 'Highe

#### interactive_multiapp_c2w_012（L3）

- **总述指令**：Help me organize the department expenses
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me organize the department expenses
  - Phase 2（trigger: `agent_done`）：Calculate the total expense for Marketing Dept from /home/user/Desktop/expense_report.xlsx, append to /home/user/Desktop/expense_memo.txt: 'Marketing 

#### interactive_multiapp_c2w_013（L2）

- **总述指令**：Help me record the product sales data
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me record the product sales data
  - Phase 2（trigger: `agent_done`）：Find the product with the lowest return rate from /home/user/Desktop/product_sales.xlsx, append to /home/user/Desktop/product_summary.txt: 'Lowest Ret

#### interactive_multiapp_c2w_015（L2）

- **总述指令**：Help me record the store performance
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me record the store performance
  - Phase 2（trigger: `agent_done`）：Find the store with the highest monthly sales from /home/user/Desktop/store_data.xlsx, append to /home/user/Desktop/store_report.txt: 'Top Sales Store

#### interactive_multiapp_c2w_016（L3）

- **总述指令**：Help me summarize the HR headcount
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me summarize the HR headcount
  - Phase 2（trigger: `agent_done`）：Find the department with the highest net headcount increase (hires minus departures) from /home/user/Desktop/hr_headcount.xlsx, append to /home/user/D

#### interactive_multiapp_c2w_017（L2）

- **总述指令**：Help me organize the logistics information
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me organize the logistics information
  - Phase 2（trigger: `agent_done`）：Find the order with the lowest freight from /home/user/Desktop/logistics.xlsx, append to /home/user/Desktop/logistics_memo.txt: 'Lowest Freight Order:

#### interactive_multiapp_c2w_019（L3）

- **总述指令**：Help me summarize the supplier evaluation
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me summarize the supplier evaluation
  - Phase 2（trigger: `agent_done`）：Find the A-rated supplier with the highest on-time delivery rate from /home/user/Desktop/supplier_info.xlsx, append to /home/user/Desktop/supplier_not

### 3.x Calc → Impress（c2i） —— 0 个

> **来源类型**：现实场景构造 | **真实工作来源**：KPI 数据转演示摘要
> **证据描述**：从 KPI 表格中提取关键指标制作管理层汇报要点

## 4. 来源映射总表

| 类别 | 任务数 | 来源类型 | 真实工作来源 | 证据描述 |
|------|-------|---------|------------|---------|
| Writer → Calc（w2c） | 11 | 现实场景构造 | 会议纪要/文本材料提取到表格 | 项目经理将会议记录中的行动项、预算数据提取整理到 Excel 表格中 |
| Writer → Impress（w2i） | 0 | 现实场景构造 | 文本材料转演示摘要 | 从团队工作总结或报告中提取要点制作汇报演示 |
| Calc → Writer（c2w） | 14 | 现实场景构造 | 表格数据汇总为文本报告 | 从销售数据表中提取关键数据生成文字版销售摘要 |
| Calc → Impress（c2i） | 0 | 现实场景构造 | KPI 数据转演示摘要 | 从 KPI 表格中提取关键指标制作管理层汇报要点 |

## 5. 素材说明

| 属性 | 说明 |
|------|------|
| 文件格式 | `.docx`（Writer 材料）、`.xlsx`（Calc 材料）、`.pptx`（Impress 材料） |
| 初始文件 | 跨应用任务共享 Writer/Calc/Impress 单应用任务的素材文件 |
| Gold 文件 | 跨应用任务不使用 gold 文件（通过命令行输出关键字验证） |
| 语言 | 英文内容 |
| 场景 | 会议纪要提取、报告汇总、KPI 可视化 |

---

## 6. Task JSON 模板

### 跨应用交互任务模板

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

## 7. 来源证据落地字段（建议统一）

- **source_type**：`meeting_extraction` / `report_summarization` / `kpi_visualization`
- **source_ref**：来源标识（匿名化 URL、工单号、访谈记录编号）
- **captured_at**：取证日期（`YYYY-MM-DD`）
- **anonymized_excerpt**：匿名化原文摘录（1~3 句）
- **mapping_note**：原始需求如何映射到 `phases` 与 `trigger`
- **reviewers**：双人审核与仲裁记录（`reviewer_a/reviewer_b/adjudicator`）

---

## 8. Docker 镜像要求

- **LibreOffice 全套**（Calc + Writer + Impress，推荐 7.x+）
- **X11 显示环境**
- **Python 3**（评估器运行环境）

---

## 9. 难度分布总结

| L1 | L2 | L3 | 合计 |
|----|----|----|------|
| 2 | 6 | 17 | 25 |

### 可验证性保证

1. **命令行输出验证**：`check_include_exclude` 在 VM 上执行命令（如 `cat`/`python3 -c`），检查输出文件内容是否包含预期关键字、排除干扰内容。
2. **无视觉依赖**：所有验证基于文件内容的程序化检查，不依赖截图对比或 OCR。

> 难度标签基于 kimi-k2.5 模型在 max_steps=80 条件下的实际执行结果。

---

## 10. 常见陷阱

### 跨应用数据传递
- **文件路径一致性**：Phase 1 写入的文件路径必须与 Phase 2 读取的路径完全匹配。
- **应用切换延迟**：从 Writer 切换到 Calc 时，需要等待新应用窗口完全加载。
- **保存时机**：每个 phase 结束前需确保文件已保存，否则下一 phase 读取的是旧内容。

### UserSimulator 配置
- 交互任务依赖 `UserSimulator`（LLM 驱动），需确保 vLLM 服务在 `localhost:8000` 运行。
- `user_persona` 字段影响 UserSimulator 的回复风格和严格程度。