# LibreOffice Calc 任务设计文档

## 0. LibreOffice Calc 验证策略

### Calc 路径

评测虚拟机中 LibreOffice Calc 通过系统预装，**启动方式为 `libreoffice --calc <文件路径>`** 或通过 config 中 `open` 动作直接打开指定 `.xlsx` 文件。所有 task JSON 中的 `config` 都使用 `upload_file` + `open` 组合。

### 核心思路

LibreOffice Calc 的验证通过将 VM 中用户编辑后的 `.xlsx` 文件下载到本地，与预制的 gold 标准文件进行结构化对比实现。

1. **表格结构对比**（`compare_table`）：使用 `openpyxl` 解析 `.xlsx` 文件，支持多维度比较——单元格数据、工作表名称、冻结窗格、样式（粗体/颜色/合并）、数据验证规则、图表等。
2. **CSV 导出对比**（`compare_csv`）：对 CSV 导出任务，直接逐行比较文本内容。

**评估器架构**：所有评估函数通过 `vm_file` getter 从 VM 下载结果文件，从 `cache` 目录加载 gold 标准文件，在本地进行对比判定。不需要在 VM 上运行额外脚本。

### 评估器通用模式

```python
def compare_table(result: str, expected: str, **options) -> float:
    """
    参数：
        result: 从 VM 下载的用户编辑后 .xlsx 文件路径
        expected: 预制的 gold 标准 .xlsx 文件路径
        options["rules"]: 比较规则列表，每条规则指定一个检查维度
    返回：
        1.0（所有规则通过）或 0.0（任一规则失败）
    """
    try:
        # ... 按 rules 逐条检查
        return 1.0
    except:
        return 0.0
```

### 与其他应用验证方式的对比

| 特性 | Calc | Writer | Impress |
|------|------|--------|---------|
| 文件格式 | `.xlsx`（OpenXML 电子表格）| `.docx`（OpenXML 文档）| `.pptx`（OpenXML 演示）|
| 验证方式 | `vm_file` → 下载后 `openpyxl` 结构化对比 | `vm_file` → 下载后 `python-docx` 对比 | `vm_file` → 下载后 `python-pptx` 对比 |
| 核心函数 | `compare_table`（多规则组合） | `compare_docx_files` | `compare_pptx_files` |
| 验证维度 | 数据/样式/冻结/图表/数据验证/工作表结构 | 文本内容/段落格式/字体 | 幻灯片内容/形状/过渡/方向 |
| 依赖库 | `openpyxl`（第三方） | `python-docx`（第三方） | `python-pptx`（第三方） |
| 额外脚本 | 不需要 | 不需要 | 不需要 |

---

## 1. 可用资源

总计：**50** 个初始文件 + 对应 gold 标准文件

### calc_new 素材（30 个任务）

| # | 初始文件 | Gold 文件 | 任务概要 |
|---|---------|----------|--------|
| 1 | `Order_Sequence_Number.xlsx` | `Order_Sequence_Number_gold.xlsx` | Fill the Sequence Numbers as "No. #" (e.g. No. 1, No. 2, ...) in the "... |
| 2 | `Employee_Name_Split.xlsx` | `Employee_Name_Split_gold.xlsx` | The "Full Name" column contains names in "Last, First" format. Please ... |
| 3 | `Customer_Deduplicate.xlsx` | `Customer_Deduplicate_gold.xlsx` | Check the names in the "Customer Names with Duplicates" column and put... |
| 4 | `Product_Name_Clean.xlsx` | `Product_Name_Clean_gold.xlsx` | I want to copy the product names in the "Raw Name" column to the "Clea... |
| 5 | `Loan_Due_Date.xlsx` | `Loan_Due_Date_gold.xlsx` | Calculate the due date for each loan by adding the "Term (Days)" to th... |
| 6 | `WeeklyRevenue_AddProfit.xlsx` | `WeeklyRevenue_AddProfit_gold.xlsx` | Add a new column named "Profit" right after the "Cost" column and calc... |
| 7 | `Dept_Budget_Summary.xlsx` | `Dept_Budget_Summary_gold.xlsx` | Create a table in a new sheet named "Sheet2" with two column headers "... |
| 8 | `Temperature_Sort_Chart.xlsx` | `Temperature_Sort_Chart_gold.xlsx` | Sort the data by the "Date" column in ascending order and then create ... |
| 9 | `Monthly_Total_LineChart.xlsx` | `Monthly_Total_LineChart_gold.xlsx` | Work out the monthly total sales in a new row called "Total" and then ... |
| 10 | `Monthly_Sales_TotalRow.xlsx` | `Monthly_Sales_TotalRow_gold.xlsx` | Work out the monthly total sales in a new row called "Total" at the bo... |
| 11 | `Financial_Data_CopyCol.xlsx` | `Financial_Data_CopyCol_gold.xlsx` | Copy the "Expenses ($)" column along with its header to a new sheet na... |
| 12 | `Export_to_CSV.xlsx` | `Export_to_CSV.csv` | Could you help me to export the current sheet to a CSV file? Export th... |
| 13 | `Report_Header_Merge.xlsx` | `Report_Header_Merge_gold.xlsx` | Create a new sheet named "Sheet2" and merge cells A1:D1 to write the h... |
| 14 | `Employee_Name_Concat.xlsx` | `Employee_Name_Concat_gold.xlsx` | Create a "Full Name" column by concatenating "First Name" and "Last Na... |
| 15 | `Product_Gross_Margin.xlsx` | `Product_Gross_Margin_gold.xlsx` | Calculate the gross margin percentage for each product using the formu... |
| 16 | `Exam_Score_Highlight.xlsx` | `Exam_Score_Highlight_gold.xlsx` | Please highlight all the cells in the "Score" column that have a value... |
| 17 | `Zone_Quarterly_Sales.xlsx` | `Zone_Quarterly_Sales_gold.xlsx` | Fill the missing values in the "Total" column and the "Total" row with... |
| 18 | `Finance_Sheet2_Sum.xlsx` | `Finance_Sheet2_Sum_gold.xlsx` | Compute the sum of the "Revenue ($)" and "Expenses ($)" columns and pu... |
| 19 | `Order_Code_Pad.xlsx` | `Order_Code_Pad_gold.xlsx` | Copy the numbers in the "Old Code" column to the "Padded Code (8 digit... |
| 20 | `Annual_Revenue_Growth.xlsx` | `Annual_Revenue_Growth_gold.xlsx` | In a new sheet named "Sheet2" with two column headers "Year" and "Grow... |
| 21 | `Project_Tasks_Validation.xlsx` | `Project_Tasks_Validation_gold.xlsx` | In the "Status" column, enable data validation for cells F2:F16 so tha... |
| 22 | `Transactions_Sort_Amount.xlsx` | `Transactions_Sort_Amount_gold.xlsx` | Could you help me sort the records according to the "Amount ($)" colum... |
| 23 | `Branch_Manager_Lookup.xlsx` | `Branch_Manager_Lookup_gold.xlsx` | There is a lookup table in the "Lookup" sheet listing the manager for ... |
| 24 | `Online_Orders_Summary.xlsx` | `Online_Orders_Summary_gold.xlsx` | Create two tables in a new sheet named "Sheet2": the first table has h... |
| 25 | `Sales_Log_Sort_Date.xlsx` | `Sales_Log_Sort_Date_gold.xlsx` | Sort the data according to the "Date" column in ascending order. |
| 26 | `Support_Tickets_Count.xlsx` | `Support_Tickets_Count_gold.xlsx` | Create a new sheet named "Sheet2" with two column headers "Agent" and ... |
| 27 | `Inventory_Freeze_Row.xlsx` | `Inventory_Freeze_Row_gold.xlsx` | Help me freeze the first row on this sheet to keep the headers always ... |
| 28 | `Region_SalesVsTarget_Chart.xlsx` | `Region_SalesVsTarget_Chart_gold.xlsx` | Create a clustered column chart showing the "Sales ($)" and "Target ($... |
| 29 | `Staff_Records_Reorder.xlsx` | `Staff_Records_Reorder_gold.xlsx` | Reorder the columns to be "ID", "Name", "Department", "Join Date", "Sa... |
| 30 | `Employee_Dept_Fill_Blank.xlsx` | `Employee_Dept_Fill_Blank_gold.xlsx` | Fill all the blank cells in the "Department" column (B2:B26) with the ... |

### calc_hard 素材（20 个任务）

| # | 初始文件 | Gold 文件 | 任务概要 |
|---|---------|----------|--------|
| 1 | `SalesData_L2_01.xlsx` | `SalesData_L2_01_gold.xlsx` | Open "SalesData_L2_01.xlsx". Add a new column "Profit" (column H) that... |
| 2 | `InvRestock_L3_08.xlsx` | `InvRestock_L3_08_gold.xlsx` | Open "InvRestock_L3_08.xlsx" and do ALL: (1) Add "Total Value" (H) = Q... |
| 3 | `EmpComprehensive_L3_02.xlsx` | `EmpComprehensive_L3_02_gold.xlsx` | Open "EmpComprehensive_L3_02.xlsx" and perform ALL: (1) Add a "Salary ... |
| 4 | `ProjTimeline_L3_09.xlsx` | `ProjTimeline_L3_09_gold.xlsx` | Open "ProjTimeline_L3_09.xlsx" and do ALL: (1) Add "Remaining Budget" ... |
| 5 | `SalesRegion_L2_06.xlsx` | `SalesRegion_L2_06_gold.xlsx` | Open "SalesRegion_L2_06.xlsx". Create a new sheet "Summary" with heade... |
| 6 | `ProjectData_L2_04.xlsx` | `ProjectData_L2_04_gold.xlsx` | Open "ProjectData_L2_04.xlsx". Add two new columns: "Remaining" (Budge... |
| 7 | `EmpStats_L2_07.xlsx` | `EmpStats_L2_07_gold.xlsx` | Open "EmpStats_L2_07.xlsx". Create a new sheet "Stats" with headers "M... |
| 8 | `InvReorder_L2_08.xlsx` | `InvReorder_L2_08_gold.xlsx` | Open "InvReorder_L2_08.xlsx". Sort all data rows by Category (A-Z) the... |
| 9 | `QtrComprehensive_L3_05.xlsx` | `QtrComprehensive_L3_05_gold.xlsx` | Open "QtrComprehensive_L3_05.xlsx" and do ALL: (1) Add columns: "Annua... |
| 10 | `InvAnalysis_L3_03.xlsx` | `InvAnalysis_L3_03_gold.xlsx` | Open "InvAnalysis_L3_03.xlsx" and do ALL: (1) Add "Total Value" column... |
| 11 | `QtrFullYear_L3_10.xlsx` | `QtrFullYear_L3_10_gold.xlsx` | Open "QtrFullYear_L3_10.xlsx" and do ALL: (1) Add columns: Annual Reve... |
| 12 | `QtrAnnual_L2_10.xlsx` | `QtrAnnual_L2_10_gold.xlsx` | Open "QtrAnnual_L2_10.xlsx". Add two columns: "Annual Revenue" (J) sum... |
| 13 | `SalesProduct_L3_06.xlsx` | `SalesProduct_L3_06_gold.xlsx` | Open "SalesProduct_L3_06.xlsx" and do ALL: (1) Add "Profit" (H) = Reve... |
| 14 | `EmpBudget_L3_07.xlsx` | `EmpBudget_L3_07_gold.xlsx` | Open "EmpBudget_L3_07.xlsx" and do ALL: (1) Add "Salary Band" (H): "Se... |
| 15 | `ProjAnalysis_L3_04.xlsx` | `ProjAnalysis_L3_04_gold.xlsx` | Open "ProjAnalysis_L3_04.xlsx" and do ALL: (1) Add "Remaining" (J) = B... |
| 16 | `Inventory_L2_03.xlsx` | `Inventory_L2_03_gold.xlsx` | Open "Inventory_L2_03.xlsx". Add a "Total Value" column (H) that calcu... |
| 17 | `ProjStatus_L2_09.xlsx` | `ProjStatus_L2_09_gold.xlsx` | Open "ProjStatus_L2_09.xlsx". Create a new sheet "StatusSummary" with ... |
| 18 | `Quarterly_L2_05.xlsx` | `Quarterly_L2_05_gold.xlsx` | Open "Quarterly_L2_05.xlsx". Add a "Total" row (row 7) that sums each ... |
| 19 | `SalesAnalysis_L3_01.xlsx` | `SalesAnalysis_L3_01_gold.xlsx` | Open "SalesAnalysis_L3_01.xlsx" and perform ALL of the following: (1) ... |
| 20 | `EmployeeData_L2_02.xlsx` | `EmployeeData_L2_02_gold.xlsx` | Open "EmployeeData_L2_02.xlsx". Create a new sheet "HighPerformers" an... |

---

## 2. 评估函数设计

文件：`desktop_env/evaluators/metrics/table.py`

### 2.1 主评估函数

| 函数名 | 描述 | 使用次数 |
|--------|------|---------|
| `compare_table` | 按规则列表结构化对比两个 .xlsx 文件 | 49 |
| `compare_csv` | 逐行对比 CSV 文件内容 | 1 |

### 2.2 规则类型详情

| 规则类型 | 描述 | 使用次数 |
|---------|------|---------|
| `sheet_data` | 对比指定工作表的单元格数据 | 71 |
| `sheet_name` | 验证工作表名称列表匹配 | 20 |
| `style` | 对比单元格样式（粗体/颜色/合并等） | 14 |
| `freeze` | 验证冻结窗格位置 | 12 |
| `chart` | 对比嵌入图表（类型/数据范围/标题） | 2 |
| `data_validation` | 验证数据验证规则（下拉列表/范围限制等） | 1 |

---

## 3. 任务定义


### 3.1 第一级（L1）—— 基础操作 —— 3 个

> agent 在实测中 10 步内完成且得分 1.0 的任务

#### 任务 L1-1：Financial_Data_CopyCol

- **ID**：`79872a2b-ef63-4bda-96e5-790310f5be45`
- **来源**：`calc_new`
- **指令**：Copy the "Expenses ($)" column along with its header to a new sheet named "Sheet2".
- **素材文件**：`Financial_Data_CopyCol.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_data`
- **Gold 文件**：`Financial_Data_CopyCol_gold.xlsx`

#### 任务 L1-2：Employee_Name_Concat

- **ID**：`86a0574a-367d-4611-9c8e-748fc82b412e`
- **来源**：`calc_new`
- **指令**：Create a "Full Name" column by concatenating "First Name" and "Last Name" with a space in between for each employee. Finish the work and don't touch irrelevant regions.
- **素材文件**：`Employee_Name_Concat.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_data`
- **Gold 文件**：`Employee_Name_Concat_gold.xlsx`

#### 任务 L1-3：Inventory_Freeze_Row

- **ID**：`f6b1639f-d2b2-4078-98dd-dd9f3ce35237`
- **来源**：`calc_new`
- **指令**：Help me freeze the first row on this sheet to keep the headers always visible when scrolling.
- **素材文件**：`Inventory_Freeze_Row.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`freeze`, `sheet_data`
- **Gold 文件**：`Inventory_Freeze_Row_gold.xlsx`

#### L1 任务来源标注

| 任务 | 来源类型 | 具体来源 | 标注理由 |
|------|---------|---------|---------|
| L1-1 | 官方帮助 | [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) + [Copying Cells](https://help.libreoffice.org/latest/en-US/text/scalc/guide/cellcopy.html) | Copy the "Expenses ($)" column along with its header to a new sheet named "Sheet |
| L1-2 | 官方帮助 | [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Create a "Full Name" column by concatenating "First Name" and "Last Name" with a |
| L1-3 | 官方帮助 | [Freezing Rows/Columns](https://help.libreoffice.org/latest/en-US/text/scalc/guide/line_fix.html) | Help me freeze the first row on this sheet to keep the headers always visible wh |

#### L1 任务汇总表

| # | 任务名称 | 素材文件 | 评估函数 |
|---|---------|---------|---------|
| 1 | Financial_Data_CopyCol | `Financial_Data_CopyCol.xlsx` | `compare_table` (sheet_data) |
| 2 | Employee_Name_Concat | `Employee_Name_Concat.xlsx` | `compare_table` (sheet_data) |
| 3 | Inventory_Freeze_Row | `Inventory_Freeze_Row.xlsx` | `compare_table` (freeze, sheet_data) |


### 3.2 第二级（L2）—— 复合操作 —— 6 个

> agent 在 25 步内完成（得分 1.0）或 10 步内失败的任务

#### 任务 L2-1：Loan_Due_Date

- **ID**：`3fd989e0-61f2-4f77-a604-a0c0ae0f8c7b`
- **来源**：`calc_new`
- **指令**：Calculate the due date for each loan by adding the "Term (Days)" to the "Issue Date" and fill in the "Due Date" column.
- **素材文件**：`Loan_Due_Date.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_data`
- **Gold 文件**：`Loan_Due_Date_gold.xlsx`

#### 任务 L2-2：WeeklyRevenue_AddProfit

- **ID**：`55b85705-22a1-4ed1-abf4-686015978529`
- **来源**：`calc_new`
- **指令**：Add a new column named "Profit" right after the "Cost" column and calculate the profit for each week by subtracting "Cost" from "Revenue".
- **素材文件**：`WeeklyRevenue_AddProfit.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_data`
- **Gold 文件**：`WeeklyRevenue_AddProfit_gold.xlsx`

#### 任务 L2-3：Finance_Sheet2_Sum

- **ID**：`b8185158-1fda-4729-ad1a-b76a8afa9ecf`
- **来源**：`calc_new`
- **指令**：Compute the sum of the "Revenue ($)" and "Expenses ($)" columns and put the results under two column headers named "Total Revenue ($)" and "Total Expenses ($)" in a new sheet named "Sheet2".
- **素材文件**：`Finance_Sheet2_Sum.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_data`
- **Gold 文件**：`Finance_Sheet2_Sum_gold.xlsx`

#### 任务 L2-4：Project_Tasks_Validation

- **ID**：`d8ddb9e1-06aa-4181-ae78-e70d07be83e9`
- **来源**：`calc_new`
- **指令**：In the "Status" column, enable data validation for cells F2:F16 so that the values can be directly selected from a drop down list with options "Open", "In Progress", and "Done". Finish the work and don't touch irrelevant regions, even if they are blank.
- **素材文件**：`Project_Tasks_Validation.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_data`, `data_validation`
- **Gold 文件**：`Project_Tasks_Validation_gold.xlsx`

#### 任务 L2-5：Branch_Manager_Lookup

- **ID**：`df47cfc4-b12a-4e1c-89f5-94fda600b12e`
- **来源**：`calc_new`
- **指令**：There is a lookup table in the "Lookup" sheet listing the manager for each city. Please fill in the "Manager" column in Sheet1 for each branch office according to its city.
- **素材文件**：`Branch_Manager_Lookup.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_data`
- **Gold 文件**：`Branch_Manager_Lookup_gold.xlsx`

#### 任务 L2-6：Employee_Dept_Fill_Blank

- **ID**：`ff761a9f-28ed-4178-b3fc-1e91fe8096db`
- **来源**：`calc_new`
- **指令**：Fill all the blank cells in the "Department" column (B2:B26) with the value in the cell above it. Finish the work and don't touch irrelevant regions, even if they are blank.
- **素材文件**：`Employee_Dept_Fill_Blank.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_data`
- **Gold 文件**：`Employee_Dept_Fill_Blank_gold.xlsx`

#### L2 任务来源标注

| 任务 | 来源类型 | 具体来源 | 标注理由 |
|------|---------|---------|---------|
| L2-1 | 官方帮助 | [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) | Calculate the due date for each loan by adding the "Term (Days)" to the "Issue D |
| L2-2 | 官方帮助 | [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) | Add a new column named "Profit" right after the "Cost" column and calculate the  |
| L2-3 | 官方帮助 | [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Compute the sum of the "Revenue ($)" and "Expenses ($)" columns and put the resu |
| L2-4 | 官方帮助 | [Data Validation](https://help.libreoffice.org/latest/en-US/text/scalc/guide/validity.html) | In the "Status" column, enable data validation for cells F2:F16 so that the valu |
| L2-5 | 官方帮助 | [VLOOKUP](https://help.libreoffice.org/latest/en-US/text/scalc/01/04060109.html) | There is a lookup table in the "Lookup" sheet listing the manager for each city. |
| L2-6 | 官方帮助 | [Spreadsheet Operations](https://help.libreoffice.org/latest/en-US/text/scalc/guide/main.html) | Fill all the blank cells in the "Department" column (B2:B26) with the value in t |

#### L2 任务汇总表

| # | 任务名称 | 素材文件 | 评估函数 |
|---|---------|---------|---------|
| 1 | Loan_Due_Date | `Loan_Due_Date.xlsx` | `compare_table` (sheet_data) |
| 2 | WeeklyRevenue_AddProfit | `WeeklyRevenue_AddProfit.xlsx` | `compare_table` (sheet_data) |
| 3 | Finance_Sheet2_Sum | `Finance_Sheet2_Sum.xlsx` | `compare_table` (sheet_data) |
| 4 | Project_Tasks_Validation | `Project_Tasks_Validation.xlsx` | `compare_table` (sheet_data, data_validation) |
| 5 | Branch_Manager_Lookup | `Branch_Manager_Lookup.xlsx` | `compare_table` (sheet_data) |
| 6 | Employee_Dept_Fill_Blank | `Employee_Dept_Fill_Blank.xlsx` | `compare_table` (sheet_data) |


### 3.3 第三级（L3）—— 高级工作流 —— 41 个

> agent 无法完成或需要大量步骤（>25 步）的任务

#### 任务 L3-1：Order_Sequence_Number

- **ID**：`0de46e41-e54a-44f9-8655-96b5d017f587`
- **来源**：`calc_new`
- **指令**：Fill the Sequence Numbers as "No. #" (e.g. No. 1, No. 2, ...) in the "Seq No." column. Finish the work and don't touch irrelevant regions, even if they are blank.
- **素材文件**：`Order_Sequence_Number.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_data`
- **Gold 文件**：`Order_Sequence_Number_gold.xlsx`

#### 任务 L3-2：Employee_Name_Split

- **ID**：`146b595a-9dcc-4637-b5f3-d347deff6859`
- **来源**：`calc_new`
- **指令**：The "Full Name" column contains names in "Last, First" format. Please split them and fill in the "First Name" and "Last Name" columns. Finish the work and don't touch the original data.
- **素材文件**：`Employee_Name_Split.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_data`
- **Gold 文件**：`Employee_Name_Split_gold.xlsx`

#### 任务 L3-3：Customer_Deduplicate

- **ID**：`27fdf845-4947-48cf-a282-8163a3941abf`
- **来源**：`calc_new`
- **指令**：Check the names in the "Customer Names with Duplicates" column and put the unique ones in the "Unique Customers" column. Keep the original order of first occurrences. Finish the work and don't touch irrelevant regions, even if they are blank.
- **素材文件**：`Customer_Deduplicate.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_data`
- **Gold 文件**：`Customer_Deduplicate_gold.xlsx`

#### 任务 L3-4：Product_Name_Clean

- **ID**：`32faea23-58b3-471f-957a-f8798afde48a`
- **来源**：`calc_new`
- **指令**：I want to copy the product names in the "Raw Name" column to the "Clean Name" column. Please remove redundant whitespaces and canonicalize the letter cases by capitalizing the first letter of each word and leaving other letters as lower case. Finish the work and don't touch irrelevant regions, even if they are blank.
- **素材文件**：`Product_Name_Clean.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_data`
- **Gold 文件**：`Product_Name_Clean_gold.xlsx`

#### 任务 L3-5：Dept_Budget_Summary

- **ID**：`700c6067-8428-4975-92d9-b06f6147b894`
- **来源**：`calc_new`
- **指令**：Create a table in a new sheet named "Sheet2" with two column headers "Department" and "Total Budget ($)", showing the total budget amount for each department in alphabetical order.
- **素材文件**：`Dept_Budget_Summary.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_data`
- **Gold 文件**：`Dept_Budget_Summary_gold.xlsx`

#### 任务 L3-6：Temperature_Sort_Chart

- **ID**：`7412aed6-5083-441b-a86a-9b7da14fa46b`
- **来源**：`calc_new`
- **指令**：Sort the data by the "Date" column in ascending order and then create a line chart with "Date" on the x-axis and "Temperature (°C)" on the y-axis. Set the chart title as "Daily Temperature".
- **素材文件**：`Temperature_Sort_Chart.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_data`, `chart`
- **Gold 文件**：`Temperature_Sort_Chart_gold.xlsx`

#### 任务 L3-7：Monthly_Total_LineChart

- **ID**：`76e0f722-3cf0-41bb-92d6-a9a9f6f8afb7`
- **来源**：`calc_new`
- **指令**：Work out the monthly total sales in a new row called "Total" and then create a line chart to show the results (x-axis should be the months).
- **素材文件**：`Monthly_Total_LineChart.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_data`
- **Gold 文件**：`Monthly_Total_LineChart_gold.xlsx`

#### 任务 L3-8：Monthly_Sales_TotalRow

- **ID**：`787f1683-8624-47ec-b1fa-f449c4e4c993`
- **来源**：`calc_new`
- **指令**：Work out the monthly total sales in a new row called "Total" at the bottom of the table.
- **素材文件**：`Monthly_Sales_TotalRow.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_data`
- **Gold 文件**：`Monthly_Sales_TotalRow_gold.xlsx`

#### 任务 L3-9：Export_to_CSV

- **ID**：`7bc32014-b9a0-4ed0-8979-1bf946fd40f8`
- **来源**：`calc_new`
- **指令**：Could you help me to export the current sheet to a CSV file? Export the contents just as they are shown on the screen. Keep the other options untouched. The CSV file should share the same file name as the spreadsheet (without the .xlsx extension).
- **素材文件**：`Export_to_CSV.xlsx`
- **评估函数**：`compare_csv`
- **Gold 文件**：`Export_to_CSV.csv`

#### 任务 L3-10：Report_Header_Merge

- **ID**：`84e17652-f3f2-4475-98b2-ab92cbd00cc8`
- **来源**：`calc_new`
- **指令**：Create a new sheet named "Sheet2" and merge cells A1:D1 to write the header "Q1 & Q2 Sales Report" with a blue (#0000ff) background fill and bold white text.
- **素材文件**：`Report_Header_Merge.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_data`, `style`
- **Gold 文件**：`Report_Header_Merge_gold.xlsx`

#### 任务 L3-11：Product_Gross_Margin

- **ID**：`8c891b4d-2e1e-4a79-9a4d-2e326c6d5ae9`
- **来源**：`calc_new`
- **指令**：Calculate the gross margin percentage for each product using the formula (Revenue - COGS) / Revenue × 100, rounded to 2 decimal places, and fill in the "Gross Margin (%)" column.
- **素材文件**：`Product_Gross_Margin.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_data`
- **Gold 文件**：`Product_Gross_Margin_gold.xlsx`

#### 任务 L3-12：Exam_Score_Highlight

- **ID**：`9d33210e-6323-4fdf-ab60-8a4904e41081`
- **来源**：`calc_new`
- **指令**：Please highlight all the cells in the "Score" column that have a value greater than 90 by setting the cell background to green (#00ff00). Finish the work and don't touch irrelevant regions, even if they are blank.
- **素材文件**：`Exam_Score_Highlight.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_data`, `style`
- **Gold 文件**：`Exam_Score_Highlight_gold.xlsx`

#### 任务 L3-13：Zone_Quarterly_Sales

- **ID**：`a1d243af-6773-487a-a46b-b46211de2902`
- **来源**：`calc_new`
- **指令**：Fill the missing values in the "Total" column and the "Total" row with the correct sums.
- **素材文件**：`Zone_Quarterly_Sales.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_data`
- **Gold 文件**：`Zone_Quarterly_Sales_gold.xlsx`

#### 任务 L3-14：Order_Code_Pad

- **ID**：`bff35d23-fc7e-4f5f-9a7f-d40deefa7202`
- **来源**：`calc_new`
- **指令**：Copy the numbers in the "Old Code" column to the "Padded Code (8 digits)" column, padding them with leading zeros to fill up to 8 digits. Finish the work and don't touch irrelevant regions, even if they are blank.
- **素材文件**：`Order_Code_Pad.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_data`
- **Gold 文件**：`Order_Code_Pad_gold.xlsx`

#### 任务 L3-15：Annual_Revenue_Growth

- **ID**：`c8bfd197-8faa-4c62-baca-943c0907b9dd`
- **来源**：`calc_new`
- **指令**：In a new sheet named "Sheet2" with two column headers "Year" and "Growth (%)", calculate the year-over-year revenue growth percentage compared to the previous year for 2019 to 2023. Round to 2 decimal places.
- **素材文件**：`Annual_Revenue_Growth.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_data`
- **Gold 文件**：`Annual_Revenue_Growth_gold.xlsx`

#### 任务 L3-16：Transactions_Sort_Amount

- **ID**：`df0fa9c2-938d-451e-98be-bb16611738b8`
- **来源**：`calc_new`
- **指令**：Could you help me sort the records according to the "Amount ($)" column in ascending order?
- **素材文件**：`Transactions_Sort_Amount.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_data`
- **Gold 文件**：`Transactions_Sort_Amount_gold.xlsx`

#### 任务 L3-17：Online_Orders_Summary

- **ID**：`e2fd8f2b-ee87-422d-a4e5-31db82d367bf`
- **来源**：`calc_new`
- **指令**：Create two tables in a new sheet named "Sheet2": the first table has headers "Region" and "Total Revenue ($)" showing total revenue per region (in alphabetical order), and the second table (separated by one blank row) has headers "Category" and "Total Revenue ($)" showing total revenue per category (in alphabetical order).
- **素材文件**：`Online_Orders_Summary.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_data`
- **Gold 文件**：`Online_Orders_Summary_gold.xlsx`

#### 任务 L3-18：Sales_Log_Sort_Date

- **ID**：`e333e868-6c77-429b-8540-bfab9ff3b2ad`
- **来源**：`calc_new`
- **指令**：Sort the data according to the "Date" column in ascending order.
- **素材文件**：`Sales_Log_Sort_Date.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_data`
- **Gold 文件**：`Sales_Log_Sort_Date_gold.xlsx`

#### 任务 L3-19：Support_Tickets_Count

- **ID**：`ee2233cb-4bb3-44ad-be3e-d719f11718de`
- **来源**：`calc_new`
- **指令**：Create a new sheet named "Sheet2" with two column headers "Agent" and "Ticket Count", showing how many tickets each agent has handled. List the agents in alphabetical order.
- **素材文件**：`Support_Tickets_Count.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_data`
- **Gold 文件**：`Support_Tickets_Count_gold.xlsx`

#### 任务 L3-20：Region_SalesVsTarget_Chart

- **ID**：`f7c9725b-9f02-4131-a007-68de65161a3c`
- **来源**：`calc_new`
- **指令**：Create a clustered column chart showing the "Sales ($)" and "Target ($)" data for each region in a new sheet named "Sheet2". Set the chart title as "Sales vs Target".
- **素材文件**：`Region_SalesVsTarget_Chart.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`chart`
- **Gold 文件**：`Region_SalesVsTarget_Chart_gold.xlsx`

#### 任务 L3-21：Staff_Records_Reorder

- **ID**：`fb0f694e-fc10-46f9-9fcd-169630844996`
- **来源**：`calc_new`
- **指令**：Reorder the columns to be "ID", "Name", "Department", "Join Date", "Salary". Finish the work and don't touch irrelevant regions, even if they are blank.
- **素材文件**：`Staff_Records_Reorder.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_data`
- **Gold 文件**：`Staff_Records_Reorder_gold.xlsx`

#### 任务 L3-22：SalesData_L2_01

- **ID**：`136de85a-2050-4137-a831-8bb56ff006f0`
- **来源**：`calc_hard`
- **指令**：Open "SalesData_L2_01.xlsx". Add a new column "Profit" (column H) that calculates Revenue minus Cost for each row. Then sort all data rows by the "Revenue" column in descending order (largest first).
- **素材文件**：`SalesData_L2_01.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_name`, `sheet_data`
- **Gold 文件**：`SalesData_L2_01_gold.xlsx`

#### 任务 L3-23：InvRestock_L3_08

- **ID**：`2364b616-c254-40d2-ac46-29b63af72326`
- **来源**：`calc_hard`
- **指令**：Open "InvRestock_L3_08.xlsx" and do ALL: (1) Add "Total Value" (H) = Quantity * Unit Cost (2 dec). (2) Add "Restock Qty" (I) = max(0, Reorder Level * 2 - Quantity). (3) Add "Restock Cost" (J) = Restock Qty * Unit Cost (2 dec). (4) Sort by Category A-Z then Product Name A-Z. (5) Bold header row. (6) Create "SupplierOrders" sheet: Supplier, Items to Restock, Total Restock Cost (2 dec). Only suppliers with items needing restock. Sorted alphabetically. (7) Create "CategoryBreakdown" sheet: Category, Items, Total Qty, Total Value (2 dec), Restock Items, Restock Cost (2 dec). Sorted by Category. (8) Freeze header row on Inventory sheet.
- **素材文件**：`InvRestock_L3_08.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_name`, `sheet_data`, `sheet_data`, `sheet_data`, `freeze`, `style`
- **Gold 文件**：`InvRestock_L3_08_gold.xlsx`

#### 任务 L3-24：EmpComprehensive_L3_02

- **ID**：`30f6d4dc-f47d-4fb7-8309-8f2d3a2c9cd5`
- **来源**：`calc_hard`
- **指令**：Open "EmpComprehensive_L3_02.xlsx" and perform ALL: (1) Add a "Salary Rank" column (H) ranking employees by salary (highest=1). (2) Sort all data by Department (A-Z) then Name (A-Z). (3) Bold the entire header row. (4) Create "DeptSummary" sheet: Department, Headcount, Avg Salary (2 decimals), Avg Performance (2 decimals), Total Salary. Sorted by department. (5) Freeze the header row on the Employees sheet. (6) Create "TopEarners" sheet: Name, Department, Salary, Performance for the top 5 highest-paid employees.
- **素材文件**：`EmpComprehensive_L3_02.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_name`, `sheet_data`, `sheet_data`, `sheet_data`, `freeze`, `style`
- **Gold 文件**：`EmpComprehensive_L3_02_gold.xlsx`

#### 任务 L3-25：ProjTimeline_L3_09

- **ID**：`3281db55-73e1-4889-bff4-829581706ec6`
- **来源**：`calc_hard`
- **指令**：Open "ProjTimeline_L3_09.xlsx" and do ALL: (1) Add "Remaining Budget" (J), "% Spent" (K) = Spent/Budget*100 (1 dec), "Budget Status" (L): "Critical" if % >= 90, "Warning" if >= 70, "On Track" otherwise. (2) Sort by Budget Status (Critical first, Warning, On Track) then % Spent descending. (3) Bold header row. (4) Create "TeamWorkload" sheet: Team Lead, Projects (count), Total Budget, Total Remaining. Sorted by Team Lead name. (5) Create "BudgetOverview" sheet: Budget Status, Count, Total Budget, Avg % Spent (1 dec). Order: Critical, Warning, On Track. (6) Freeze header row on Projects sheet.
- **素材文件**：`ProjTimeline_L3_09.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_name`, `sheet_data`, `sheet_data`, `sheet_data`, `freeze`, `style`
- **Gold 文件**：`ProjTimeline_L3_09_gold.xlsx`

#### 任务 L3-26：SalesRegion_L2_06

- **ID**：`35df2269-b1c3-42e8-857d-38ca5f594bb6`
- **来源**：`calc_hard`
- **指令**：Open "SalesRegion_L2_06.xlsx". Create a new sheet "Summary" with headers: "Region", "Total Units", "Total Revenue", "Total Cost", "Total Profit". Aggregate the data from the Sales sheet by Region (alphabetically sorted), calculating the sum of Units, Revenue, and Cost, and computing Profit as Revenue minus Cost.
- **素材文件**：`SalesRegion_L2_06.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_name`, `sheet_data`, `sheet_data`
- **Gold 文件**：`SalesRegion_L2_06_gold.xlsx`

#### 任务 L3-27：ProjectData_L2_04

- **ID**：`3d7fe243-5501-48e4-a6e6-0ed818568793`
- **来源**：`calc_hard`
- **指令**：Open "ProjectData_L2_04.xlsx". Add two new columns: "Remaining" (Budget - Spent) in column J, and "% Spent" (Spent/Budget * 100, rounded to 1 decimal place) in column K. Then sort all data rows by "% Spent" in descending order.
- **素材文件**：`ProjectData_L2_04.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_name`, `sheet_data`
- **Gold 文件**：`ProjectData_L2_04_gold.xlsx`

#### 任务 L3-28：EmpStats_L2_07

- **ID**：`4f989467-8112-445d-8f1d-d0b905bd6d74`
- **来源**：`calc_hard`
- **指令**：Open "EmpStats_L2_07.xlsx". Create a new sheet "Stats" with headers "Metric" and "Value". Calculate these salary statistics from the Employees sheet: Count (number of employees), Average (rounded to 2 decimal places), Min, Max, and Total. List them in separate rows.
- **素材文件**：`EmpStats_L2_07.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_name`, `sheet_data`, `sheet_data`
- **Gold 文件**：`EmpStats_L2_07_gold.xlsx`

#### 任务 L3-29：InvReorder_L2_08

- **ID**：`53a2611a-d01f-4c82-a5d1-78631c737568`
- **来源**：`calc_hard`
- **指令**：Open "InvReorder_L2_08.xlsx". Sort all data rows by Category (A-Z) then by Product Name (A-Z). Create a new sheet "NeedReorder" with headers: SKU, Product Name, Category, Quantity, Reorder Level, Deficit. List only items where Quantity <= Reorder Level. Deficit = Reorder Level - Quantity.
- **素材文件**：`InvReorder_L2_08.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_name`, `sheet_data`, `sheet_data`
- **Gold 文件**：`InvReorder_L2_08_gold.xlsx`

#### 任务 L3-30：QtrComprehensive_L3_05

- **ID**：`696790a0-8164-4b34-b5b6-223a2495f530`
- **来源**：`calc_hard`
- **指令**：Open "QtrComprehensive_L3_05.xlsx" and do ALL: (1) Add columns: "Annual Revenue" (J), "Annual Cost" (K), "Annual Profit" (L) = Revenue - Cost, "Profit Margin %" (M) = Profit/Revenue*100 (1 decimal). (2) Add a "Total" row (row 7) summing all columns (for Margin %, compute from the totals). (3) Sort data rows (not Total) by Annual Profit descending. (4) Bold header row. (5) Create "QoQ_Growth" sheet: Department, Q1-Q2 Growth %, Q2-Q3 Growth %, Q3-Q4 Growth % (all Revenue-based, 1 decimal). Dept order matches sorted data. (6) Freeze header row on Q1-Q4 sheet.
- **素材文件**：`QtrComprehensive_L3_05.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_name`, `sheet_data`, `sheet_data`, `freeze`, `style`
- **Gold 文件**：`QtrComprehensive_L3_05_gold.xlsx`

#### 任务 L3-31：InvAnalysis_L3_03

- **ID**：`6a92d8ed-3ec6-4540-aa82-bb635d57a79d`
- **来源**：`calc_hard`
- **指令**：Open "InvAnalysis_L3_03.xlsx" and do ALL: (1) Add "Total Value" column (H) = Quantity * Unit Cost (rounded to 2 decimals). (2) Add "Stock Status" column (I): "LOW" if Quantity <= Reorder Level, "OK" if Quantity <= 2x Reorder Level, "HIGH" otherwise. (3) Sort by Total Value descending. (4) Bold the header row. (5) Create "CategorySummary" sheet: Category, Item Count, Total Quantity, Total Value, Avg Unit Cost (2 decimals). Sorted by Category. (6) Create "SupplierSummary" sheet: Supplier, Item Count, Total Value (2 decimals). Sorted by Supplier. (7) Freeze the header row on the Inventory sheet.
- **素材文件**：`InvAnalysis_L3_03.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_name`, `sheet_data`, `sheet_data`, `sheet_data`, `freeze`, `style`
- **Gold 文件**：`InvAnalysis_L3_03_gold.xlsx`

#### 任务 L3-32：QtrFullYear_L3_10

- **ID**：`6e50aca3-551a-4948-83a2-ae8a1c5c4867`
- **来源**：`calc_hard`
- **指令**：Open "QtrFullYear_L3_10.xlsx" and do ALL: (1) Add columns: Annual Revenue (J), Annual Cost (K), Annual Profit (L), Margin % (M, 1 dec), Revenue Rank (N, highest=1). (2) Sort data rows by Annual Profit descending. (3) Add "Total" row (row 7) summing all numeric columns. For Margin %, compute from totals. Leave Revenue Rank empty. (4) Bold both header row and Total row. (5) Create "RevenueGrowth" sheet: Department, Q1→Q2 %, Q2→Q3 %, Q3→Q4 %, Full Year Growth %. All percentages 1 decimal. Dept order matches sorted data. (6) Freeze header row on Q1-Q4 sheet.
- **素材文件**：`QtrFullYear_L3_10.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_name`, `sheet_data`, `sheet_data`, `freeze`, `style`
- **Gold 文件**：`QtrFullYear_L3_10_gold.xlsx`

#### 任务 L3-33：QtrAnnual_L2_10

- **ID**：`7232142e-4f9c-4994-a12a-ab2d8feef1ea`
- **来源**：`calc_hard`
- **指令**：Open "QtrAnnual_L2_10.xlsx". Add two columns: "Annual Revenue" (J) summing Q1-Q4 Revenue, and "Annual Cost" (K) summing Q1-Q4 Cost for each department. Make the entire header row bold.
- **素材文件**：`QtrAnnual_L2_10.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_name`, `sheet_data`, `style`
- **Gold 文件**：`QtrAnnual_L2_10_gold.xlsx`

#### 任务 L3-34：SalesProduct_L3_06

- **ID**：`75911c73-370d-441e-9c04-b36e2d7efcc8`
- **来源**：`calc_hard`
- **指令**：Open "SalesProduct_L3_06.xlsx" and do ALL: (1) Add "Profit" (H) = Revenue - Cost and "Margin %" (I) = Profit/Revenue*100 (1 decimal). (2) Bold the header row. (3) Create "ProductSummary" sheet: Product, Total Units, Total Revenue, Total Profit, Avg Price (2 decimals). Sorted by Product name. (4) Create "MonthlyTrend" sheet: Month, Widget A Units, Widget B Units, Total Units. Months Jan-Jun in order. (5) Freeze header row on the Sales sheet.
- **素材文件**：`SalesProduct_L3_06.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_name`, `sheet_data`, `sheet_data`, `sheet_data`, `freeze`, `style`
- **Gold 文件**：`SalesProduct_L3_06_gold.xlsx`

#### 任务 L3-35：EmpBudget_L3_07

- **ID**：`77ede3e2-4168-4e30-b390-428f1ebd63e7`
- **来源**：`calc_hard`
- **指令**：Open "EmpBudget_L3_07.xlsx" and do ALL: (1) Add "Salary Band" (H): "Senior" if Salary >= 100000, "Mid" if >= 75000, "Junior" otherwise. (2) Sort by Performance descending, then Salary descending. (3) Bold header row. (4) Create "BandSummary" sheet: Salary Band, Count, Avg Salary (2 dec), Avg Performance (2 dec). Order: Senior, Mid, Junior. (5) Create "LowPerformers" sheet: Name, Department, Performance, Salary Band for employees with Performance < 3.5. (6) Freeze header row on Employees sheet.
- **素材文件**：`EmpBudget_L3_07.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_name`, `sheet_data`, `sheet_data`, `sheet_data`, `freeze`, `style`
- **Gold 文件**：`EmpBudget_L3_07_gold.xlsx`

#### 任务 L3-36：ProjAnalysis_L3_04

- **ID**：`86a64145-9680-480a-a603-b8455f7befd7`
- **来源**：`calc_hard`
- **指令**：Open "ProjAnalysis_L3_04.xlsx" and do ALL: (1) Add "Remaining" (J) = Budget - Spent. "% Spent" (K) = Spent/Budget*100 (1 decimal). "On Budget" (L) = "Yes" if % Spent <= 100, else "No". (2) Sort by Priority (Critical first, then High, Medium, Low), then by % Spent descending within each priority. (3) Bold the header row. (4) Create "PrioritySummary" sheet: Priority, Count, Total Budget, Total Spent, Avg % Spent (1 decimal). Order: Critical, High, Medium, Low. (5) Create "AtRisk" sheet: Project Name, Team Lead, Priority, % Spent, Remaining for projects with % Spent >= 80. (6) Freeze the header row on the Projects sheet.
- **素材文件**：`ProjAnalysis_L3_04.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_name`, `sheet_data`, `sheet_data`, `sheet_data`, `freeze`, `style`
- **Gold 文件**：`ProjAnalysis_L3_04_gold.xlsx`

#### 任务 L3-37：Inventory_L2_03

- **ID**：`8bae8f17-fe56-49ef-a561-f9761e9c72a6`
- **来源**：`calc_hard`
- **指令**：Open "Inventory_L2_03.xlsx". Add a "Total Value" column (H) that calculates Quantity times Unit Cost. Make the entire header row (row 1) bold. Freeze the first row so headers stay visible when scrolling.
- **素材文件**：`Inventory_L2_03.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_name`, `sheet_data`, `freeze`, `style`
- **Gold 文件**：`Inventory_L2_03_gold.xlsx`

#### 任务 L3-38：ProjStatus_L2_09

- **ID**：`8ffd2449-cdc1-46a5-8c8d-e909fbe3fc70`
- **来源**：`calc_hard`
- **指令**：Open "ProjStatus_L2_09.xlsx". Create a new sheet "StatusSummary" with headers: "Status", "Count", "Total Budget", "Total Spent". Aggregate projects by Status (sorted alphabetically), counting how many projects have each status and summing their Budget and Spent amounts.
- **素材文件**：`ProjStatus_L2_09.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_name`, `sheet_data`, `sheet_data`
- **Gold 文件**：`ProjStatus_L2_09_gold.xlsx`

#### 任务 L3-39：Quarterly_L2_05

- **ID**：`af1c2993-6d6c-4109-95c0-fbd6ba904ed1`
- **来源**：`calc_hard`
- **指令**：Open "Quarterly_L2_05.xlsx". Add a "Total" row (row 7) that sums each column (Q1-Q4 Revenue and Cost) across all departments. Then add a "Profit" row (row 8) that shows Total Revenue minus Total Cost for each quarter (in the Revenue columns; leave Cost columns empty).
- **素材文件**：`Quarterly_L2_05.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_name`, `sheet_data`
- **Gold 文件**：`Quarterly_L2_05_gold.xlsx`

#### 任务 L3-40：SalesAnalysis_L3_01

- **ID**：`dfb46a6b-3f2d-4e4a-b4ef-20997ea21563`
- **来源**：`calc_hard`
- **指令**：Open "SalesAnalysis_L3_01.xlsx" and perform ALL of the following: (1) Add a "Profit" column (H) = Revenue - Cost. (2) Add a "Margin %" column (I) = Profit/Revenue * 100, rounded to 1 decimal. (3) Make the entire header row bold. (4) Sort all data rows by Profit in descending order. (5) Freeze the first row. (6) Create a "MonthSummary" sheet with headers: Month, Total Revenue, Total Cost, Total Profit, Avg Margin %. Aggregate by month (Jan through Jun in order), with average Margin % rounded to 1 decimal.
- **素材文件**：`SalesAnalysis_L3_01.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_name`, `sheet_data`, `sheet_data`, `freeze`, `style`
- **Gold 文件**：`SalesAnalysis_L3_01_gold.xlsx`

#### 任务 L3-41：EmployeeData_L2_02

- **ID**：`e71a3d3b-bf53-4454-b871-89156eb037d3`
- **来源**：`calc_hard`
- **指令**：Open "EmployeeData_L2_02.xlsx". Create a new sheet "HighPerformers" and copy all employees with Performance >= 4.0 (columns ID, Name, Department, Title, Salary, Performance). Also create a sheet "DeptCount" with headers "Department" and "Count" showing the number of employees per department (sorted alphabetically by department).
- **素材文件**：`EmployeeData_L2_02.xlsx`
- **评估函数**：`compare_table`
- **规则类型**：`sheet_name`, `sheet_data`, `sheet_data`, `sheet_data`
- **Gold 文件**：`EmployeeData_L2_02_gold.xlsx`

#### L3 任务来源标注

| 任务 | 来源类型 | 具体来源 | 标注理由 |
|------|---------|---------|---------|
| L3-1 | 官方帮助 | [Spreadsheet Operations](https://help.libreoffice.org/latest/en-US/text/scalc/guide/main.html) | Fill the Sequence Numbers as "No. #" (e.g. No. 1, No. 2, ...) in the "Seq No." c |
| L3-2 | 官方帮助 | [Spreadsheet Operations](https://help.libreoffice.org/latest/en-US/text/scalc/guide/main.html) | The "Full Name" column contains names in "Last, First" format. Please split them |
| L3-3 | 官方帮助 | [Spreadsheet Operations](https://help.libreoffice.org/latest/en-US/text/scalc/guide/main.html) | Check the names in the "Customer Names with Duplicates" column and put the uniqu |
| L3-4 | 官方帮助 | [Copying Cells](https://help.libreoffice.org/latest/en-US/text/scalc/guide/cellcopy.html) | I want to copy the product names in the "Raw Name" column to the "Clean Name" co |
| L3-5 | 官方帮助 | [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Create a table in a new sheet named "Sheet2" with two column headers "Department |
| L3-6 | 官方帮助 | [Sorting Data](https://help.libreoffice.org/latest/en-US/text/scalc/guide/sorted_list.html) + [Inserting Charts](https://help.libreoffice.org/latest/en-US/text/schart/main0000.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Sort the data by the "Date" column in ascending order and then create a line cha |
| L3-7 | 官方帮助 | [Inserting Charts](https://help.libreoffice.org/latest/en-US/text/schart/main0000.html) + [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Work out the monthly total sales in a new row called "Total" and then create a l |
| L3-8 | 官方帮助 | [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) | Work out the monthly total sales in a new row called "Total" at the bottom of th |
| L3-9 | 官方帮助 | [Saving as CSV](https://help.libreoffice.org/latest/en-US/text/scalc/guide/csv_files.html) | Could you help me to export the current sheet to a CSV file? Export the contents |
| L3-10 | 官方帮助 | [Cell Formatting](https://help.libreoffice.org/latest/en-US/text/scalc/guide/format_value.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Create a new sheet named "Sheet2" and merge cells A1:D1 to write the header "Q1  |
| L3-11 | 官方帮助 | [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) | Calculate the gross margin percentage for each product using the formula (Revenu |
| L3-12 | 官方帮助 | [Cell Formatting](https://help.libreoffice.org/latest/en-US/text/scalc/guide/format_value.html) | Please highlight all the cells in the "Score" column that have a value greater t |
| L3-13 | 官方帮助 | [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) | Fill the missing values in the "Total" column and the "Total" row with the corre |
| L3-14 | 官方帮助 | [Copying Cells](https://help.libreoffice.org/latest/en-US/text/scalc/guide/cellcopy.html) | Copy the numbers in the "Old Code" column to the "Padded Code (8 digits)" column |
| L3-15 | 官方帮助 | [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | In a new sheet named "Sheet2" with two column headers "Year" and "Growth (%)", c |
| L3-16 | 官方帮助 | [Sorting Data](https://help.libreoffice.org/latest/en-US/text/scalc/guide/sorted_list.html) | Could you help me sort the records according to the "Amount ($)" column in ascen |
| L3-17 | 官方帮助 | [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Create two tables in a new sheet named "Sheet2": the first table has headers "Re |
| L3-18 | 官方帮助 | [Sorting Data](https://help.libreoffice.org/latest/en-US/text/scalc/guide/sorted_list.html) | Sort the data according to the "Date" column in ascending order. |
| L3-19 | 官方帮助 | [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Create a new sheet named "Sheet2" with two column headers "Agent" and "Ticket Co |
| L3-20 | 官方帮助 | [Inserting Charts](https://help.libreoffice.org/latest/en-US/text/schart/main0000.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Create a clustered column chart showing the "Sales ($)" and "Target ($)" data fo |
| L3-21 | 官方帮助 | [Spreadsheet Operations](https://help.libreoffice.org/latest/en-US/text/scalc/guide/main.html) | Reorder the columns to be "ID", "Name", "Department", "Join Date", "Salary". Fin |
| L3-22 | 官方帮助 | [Sorting Data](https://help.libreoffice.org/latest/en-US/text/scalc/guide/sorted_list.html) + [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) | Open "SalesData_L2_01.xlsx". Add a new column "Profit" (column H) that calculate |
| L3-23 | 官方帮助 | [Sorting Data](https://help.libreoffice.org/latest/en-US/text/scalc/guide/sorted_list.html) + [Freezing Rows/Columns](https://help.libreoffice.org/latest/en-US/text/scalc/guide/line_fix.html) + [Cell Formatting](https://help.libreoffice.org/latest/en-US/text/scalc/guide/format_value.html) + [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Open "InvRestock_L3_08.xlsx" and do ALL: (1) Add "Total Value" (H) = Quantity *  |
| L3-24 | 官方帮助 | [Sorting Data](https://help.libreoffice.org/latest/en-US/text/scalc/guide/sorted_list.html) + [Freezing Rows/Columns](https://help.libreoffice.org/latest/en-US/text/scalc/guide/line_fix.html) + [Cell Formatting](https://help.libreoffice.org/latest/en-US/text/scalc/guide/format_value.html) + [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Open "EmpComprehensive_L3_02.xlsx" and perform ALL: (1) Add a "Salary Rank" colu |
| L3-25 | 官方帮助 | [Sorting Data](https://help.libreoffice.org/latest/en-US/text/scalc/guide/sorted_list.html) + [Freezing Rows/Columns](https://help.libreoffice.org/latest/en-US/text/scalc/guide/line_fix.html) + [Cell Formatting](https://help.libreoffice.org/latest/en-US/text/scalc/guide/format_value.html) + [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Open "ProjTimeline_L3_09.xlsx" and do ALL: (1) Add "Remaining Budget" (J), "% Sp |
| L3-26 | 官方帮助 | [Sorting Data](https://help.libreoffice.org/latest/en-US/text/scalc/guide/sorted_list.html) + [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Open "SalesRegion_L2_06.xlsx". Create a new sheet "Summary" with headers: "Regio |
| L3-27 | 官方帮助 | [Sorting Data](https://help.libreoffice.org/latest/en-US/text/scalc/guide/sorted_list.html) | Open "ProjectData_L2_04.xlsx". Add two new columns: "Remaining" (Budget - Spent) |
| L3-28 | 官方帮助 | [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Open "EmpStats_L2_07.xlsx". Create a new sheet "Stats" with headers "Metric" and |
| L3-29 | 官方帮助 | [Sorting Data](https://help.libreoffice.org/latest/en-US/text/scalc/guide/sorted_list.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Open "InvReorder_L2_08.xlsx". Sort all data rows by Category (A-Z) then by Produ |
| L3-30 | 官方帮助 | [Sorting Data](https://help.libreoffice.org/latest/en-US/text/scalc/guide/sorted_list.html) + [Freezing Rows/Columns](https://help.libreoffice.org/latest/en-US/text/scalc/guide/line_fix.html) + [Cell Formatting](https://help.libreoffice.org/latest/en-US/text/scalc/guide/format_value.html) + [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Open "QtrComprehensive_L3_05.xlsx" and do ALL: (1) Add columns: "Annual Revenue" |
| L3-31 | 官方帮助 | [Sorting Data](https://help.libreoffice.org/latest/en-US/text/scalc/guide/sorted_list.html) + [Freezing Rows/Columns](https://help.libreoffice.org/latest/en-US/text/scalc/guide/line_fix.html) + [Cell Formatting](https://help.libreoffice.org/latest/en-US/text/scalc/guide/format_value.html) + [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Open "InvAnalysis_L3_03.xlsx" and do ALL: (1) Add "Total Value" column (H) = Qua |
| L3-32 | 官方帮助 | [Sorting Data](https://help.libreoffice.org/latest/en-US/text/scalc/guide/sorted_list.html) + [Freezing Rows/Columns](https://help.libreoffice.org/latest/en-US/text/scalc/guide/line_fix.html) + [Cell Formatting](https://help.libreoffice.org/latest/en-US/text/scalc/guide/format_value.html) + [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Open "QtrFullYear_L3_10.xlsx" and do ALL: (1) Add columns: Annual Revenue (J), A |
| L3-33 | 官方帮助 | [Cell Formatting](https://help.libreoffice.org/latest/en-US/text/scalc/guide/format_value.html) + [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) | Open "QtrAnnual_L2_10.xlsx". Add two columns: "Annual Revenue" (J) summing Q1-Q4 |
| L3-34 | 官方帮助 | [Sorting Data](https://help.libreoffice.org/latest/en-US/text/scalc/guide/sorted_list.html) + [Freezing Rows/Columns](https://help.libreoffice.org/latest/en-US/text/scalc/guide/line_fix.html) + [Cell Formatting](https://help.libreoffice.org/latest/en-US/text/scalc/guide/format_value.html) + [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Open "SalesProduct_L3_06.xlsx" and do ALL: (1) Add "Profit" (H) = Revenue - Cost |
| L3-35 | 官方帮助 | [Sorting Data](https://help.libreoffice.org/latest/en-US/text/scalc/guide/sorted_list.html) + [Freezing Rows/Columns](https://help.libreoffice.org/latest/en-US/text/scalc/guide/line_fix.html) + [Cell Formatting](https://help.libreoffice.org/latest/en-US/text/scalc/guide/format_value.html) + [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Open "EmpBudget_L3_07.xlsx" and do ALL: (1) Add "Salary Band" (H): "Senior" if S |
| L3-36 | 官方帮助 | [Sorting Data](https://help.libreoffice.org/latest/en-US/text/scalc/guide/sorted_list.html) + [Freezing Rows/Columns](https://help.libreoffice.org/latest/en-US/text/scalc/guide/line_fix.html) + [Cell Formatting](https://help.libreoffice.org/latest/en-US/text/scalc/guide/format_value.html) + [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Open "ProjAnalysis_L3_04.xlsx" and do ALL: (1) Add "Remaining" (J) = Budget - Sp |
| L3-37 | 官方帮助 | [Freezing Rows/Columns](https://help.libreoffice.org/latest/en-US/text/scalc/guide/line_fix.html) + [Cell Formatting](https://help.libreoffice.org/latest/en-US/text/scalc/guide/format_value.html) + [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) | Open "Inventory_L2_03.xlsx". Add a "Total Value" column (H) that calculates Quan |
| L3-38 | 官方帮助 | [Sorting Data](https://help.libreoffice.org/latest/en-US/text/scalc/guide/sorted_list.html) + [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Open "ProjStatus_L2_09.xlsx". Create a new sheet "StatusSummary" with headers: " |
| L3-39 | 官方帮助 | [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) | Open "Quarterly_L2_05.xlsx". Add a "Total" row (row 7) that sums each column (Q1 |
| L3-40 | 官方帮助 | [Sorting Data](https://help.libreoffice.org/latest/en-US/text/scalc/guide/sorted_list.html) + [Freezing Rows/Columns](https://help.libreoffice.org/latest/en-US/text/scalc/guide/line_fix.html) + [Cell Formatting](https://help.libreoffice.org/latest/en-US/text/scalc/guide/format_value.html) + [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Open "SalesAnalysis_L3_01.xlsx" and perform ALL of the following: (1) Add a "Pro |
| L3-41 | 官方帮助 | [Sorting Data](https://help.libreoffice.org/latest/en-US/text/scalc/guide/sorted_list.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) + [Copying Cells](https://help.libreoffice.org/latest/en-US/text/scalc/guide/cellcopy.html) | Open "EmployeeData_L2_02.xlsx". Create a new sheet "HighPerformers" and copy all |

#### L3 任务汇总表

| # | 任务名称 | 素材文件 | 评估函数 |
|---|---------|---------|---------|
| 1 | Order_Sequence_Number | `Order_Sequence_Number.xlsx` | `compare_table` (sheet_data) |
| 2 | Employee_Name_Split | `Employee_Name_Split.xlsx` | `compare_table` (sheet_data) |
| 3 | Customer_Deduplicate | `Customer_Deduplicate.xlsx` | `compare_table` (sheet_data) |
| 4 | Product_Name_Clean | `Product_Name_Clean.xlsx` | `compare_table` (sheet_data) |
| 5 | Dept_Budget_Summary | `Dept_Budget_Summary.xlsx` | `compare_table` (sheet_data) |
| 6 | Temperature_Sort_Chart | `Temperature_Sort_Chart.xlsx` | `compare_table` (sheet_data, chart) |
| 7 | Monthly_Total_LineChart | `Monthly_Total_LineChart.xlsx` | `compare_table` (sheet_data) |
| 8 | Monthly_Sales_TotalRow | `Monthly_Sales_TotalRow.xlsx` | `compare_table` (sheet_data) |
| 9 | Export_to_CSV | `Export_to_CSV.xlsx` | `compare_csv`  |
| 10 | Report_Header_Merge | `Report_Header_Merge.xlsx` | `compare_table` (sheet_data, style) |
| 11 | Product_Gross_Margin | `Product_Gross_Margin.xlsx` | `compare_table` (sheet_data) |
| 12 | Exam_Score_Highlight | `Exam_Score_Highlight.xlsx` | `compare_table` (sheet_data, style) |
| 13 | Zone_Quarterly_Sales | `Zone_Quarterly_Sales.xlsx` | `compare_table` (sheet_data) |
| 14 | Order_Code_Pad | `Order_Code_Pad.xlsx` | `compare_table` (sheet_data) |
| 15 | Annual_Revenue_Growth | `Annual_Revenue_Growth.xlsx` | `compare_table` (sheet_data) |
| 16 | Transactions_Sort_Amount | `Transactions_Sort_Amount.xlsx` | `compare_table` (sheet_data) |
| 17 | Online_Orders_Summary | `Online_Orders_Summary.xlsx` | `compare_table` (sheet_data) |
| 18 | Sales_Log_Sort_Date | `Sales_Log_Sort_Date.xlsx` | `compare_table` (sheet_data) |
| 19 | Support_Tickets_Count | `Support_Tickets_Count.xlsx` | `compare_table` (sheet_data) |
| 20 | Region_SalesVsTarget_Chart | `Region_SalesVsTarget_Chart.xlsx` | `compare_table` (chart) |
| 21 | Staff_Records_Reorder | `Staff_Records_Reorder.xlsx` | `compare_table` (sheet_data) |
| 22 | SalesData_L2_01 | `SalesData_L2_01.xlsx` | `compare_table` (sheet_name, sheet_data) |
| 23 | InvRestock_L3_08 | `InvRestock_L3_08.xlsx` | `compare_table` (sheet_name, sheet_data, sheet_data, sheet_data, freeze, style) |
| 24 | EmpComprehensive_L3_02 | `EmpComprehensive_L3_02.xlsx` | `compare_table` (sheet_name, sheet_data, sheet_data, sheet_data, freeze, style) |
| 25 | ProjTimeline_L3_09 | `ProjTimeline_L3_09.xlsx` | `compare_table` (sheet_name, sheet_data, sheet_data, sheet_data, freeze, style) |
| 26 | SalesRegion_L2_06 | `SalesRegion_L2_06.xlsx` | `compare_table` (sheet_name, sheet_data, sheet_data) |
| 27 | ProjectData_L2_04 | `ProjectData_L2_04.xlsx` | `compare_table` (sheet_name, sheet_data) |
| 28 | EmpStats_L2_07 | `EmpStats_L2_07.xlsx` | `compare_table` (sheet_name, sheet_data, sheet_data) |
| 29 | InvReorder_L2_08 | `InvReorder_L2_08.xlsx` | `compare_table` (sheet_name, sheet_data, sheet_data) |
| 30 | QtrComprehensive_L3_05 | `QtrComprehensive_L3_05.xlsx` | `compare_table` (sheet_name, sheet_data, sheet_data, freeze, style) |
| 31 | InvAnalysis_L3_03 | `InvAnalysis_L3_03.xlsx` | `compare_table` (sheet_name, sheet_data, sheet_data, sheet_data, freeze, style) |
| 32 | QtrFullYear_L3_10 | `QtrFullYear_L3_10.xlsx` | `compare_table` (sheet_name, sheet_data, sheet_data, freeze, style) |
| 33 | QtrAnnual_L2_10 | `QtrAnnual_L2_10.xlsx` | `compare_table` (sheet_name, sheet_data, style) |
| 34 | SalesProduct_L3_06 | `SalesProduct_L3_06.xlsx` | `compare_table` (sheet_name, sheet_data, sheet_data, sheet_data, freeze, style) |
| 35 | EmpBudget_L3_07 | `EmpBudget_L3_07.xlsx` | `compare_table` (sheet_name, sheet_data, sheet_data, sheet_data, freeze, style) |
| 36 | ProjAnalysis_L3_04 | `ProjAnalysis_L3_04.xlsx` | `compare_table` (sheet_name, sheet_data, sheet_data, sheet_data, freeze, style) |
| 37 | Inventory_L2_03 | `Inventory_L2_03.xlsx` | `compare_table` (sheet_name, sheet_data, freeze, style) |
| 38 | ProjStatus_L2_09 | `ProjStatus_L2_09.xlsx` | `compare_table` (sheet_name, sheet_data, sheet_data) |
| 39 | Quarterly_L2_05 | `Quarterly_L2_05.xlsx` | `compare_table` (sheet_name, sheet_data) |
| 40 | SalesAnalysis_L3_01 | `SalesAnalysis_L3_01.xlsx` | `compare_table` (sheet_name, sheet_data, sheet_data, freeze, style) |
| 41 | EmployeeData_L2_02 | `EmployeeData_L2_02.xlsx` | `compare_table` (sheet_name, sheet_data, sheet_data, sheet_data) |

---

### 3.4 Interactive 任务（Calc 交互式）—— 27 个

> 交互式任务使用多阶段 phase 设计，通过 `trigger` 控制阶段切换。


#### 场景类型：`ambiguous_detail`（模糊细节）—— 4 个

> **来源类型**：现实场景构造 | **真实工作来源**：财务报表细节不明确
> **证据描述**：财务人员收到"帮我做个汇总"但未指定汇总维度和格式，需要澄清后执行

##### interactive_calc_005（L3）

- **场景描述**：The user wants a promotion-type breakdown but doesn't specify the target column or output format. The agent asks, then summarizes Revenue by Promotion Type on Sheet2.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `agent_asks`）：Help me create a promotion type breakdown
  - Phase 2（trigger: `agent_done`）：On Sheet2, summarize total Revenue by Promotion Type, with columns named 'Promotion Type' and 'Total Revenue', then save

##### interactive_calc_006（L3）

- **场景描述**：The user wants to analyze the invoice data but doesn't specify what metric. The agent asks, then counts occurrences of each Invoice No. on Sheet2.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `agent_asks`）：Help me analyze the invoice data
  - Phase 2（trigger: `agent_done`）：On Sheet2, count the occurrences of each Invoice No., with columns named 'Invoice No.' and 'Count', then save

##### interactive_calc_007（L3）

- **场景描述**：The user says to fill in the profit column but doesn't specify the formula. The agent asks, then fills the Gross profit column with revenue minus expenses.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `agent_asks`）：Help me fill in the profit column
  - Phase 2（trigger: `agent_done`）：Fill the Gross profit column with a formula (revenue minus all expenses) for every row, then save

##### interactive_calc_008（L3）

- **场景描述**：The user wants to add grade levels but doesn't specify the grading criteria or column name. The agent asks, then adds A/B/C/D grades based on score ranges.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `agent_asks`）：Help me add the grades
  - Phase 2（trigger: `agent_done`）：Use an IF formula: 90+ is A, 80-89 is B, 70-79 is C, below 70 is D. Put the results in a 'Grade' column, then save


#### 场景类型：`ambiguous_scope`（模糊范围）—— 4 个

> **来源类型**：现实场景构造 | **真实工作来源**：数据清洗范围不确定
> **证据描述**：数据工程师收到"清理一下这些数据"但未指定清洗哪些列和规则

##### interactive_calc_009（L3）

- **场景描述**：The user says to add a title note to a cell but doesn't say which one. The agent asks, then only modifies cell A1.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `agent_asks`）：Help me add a title note to the spreadsheet
  - Phase 2（trigger: `agent_done`）：Only change cell A1 to '2025 Summer Promotion Data', leave all other cells unchanged, then save

##### interactive_calc_010（L2）

- **场景描述**：The user says to add a note but doesn't specify the cell. The agent asks, then only modifies cell A1.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `agent_asks`）：Help me add a note to the spreadsheet
  - Phase 2（trigger: `agent_done`）：Only change cell A1 to 'Net Income Statement 2025', leave everything else unchanged, then save

##### interactive_calc_011（L3）

- **场景描述**：The user says to back up some data but doesn't specify how many rows. The agent asks, then only copies the first 3 data rows (excluding header) to Sheet2.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `agent_asks`）：Help me back up some of the data to a new sheet
  - Phase 2（trigger: `agent_done`）：Only copy the first 3 data rows (excluding the header row) to Sheet2, do not copy the rest, then save

##### interactive_calc_012（L2）

- **场景描述**：The user says to change the spreadsheet title but doesn't say what to change it to. The agent asks, then only changes A1.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `agent_asks`）：Help me change the spreadsheet title
  - Phase 2（trigger: `agent_done`）：Only change cell A1 to 'Sales Report 2025', leave all other rows unchanged, then save


#### 场景类型：`ambiguous_target`（模糊目标）—— 4 个

> **来源类型**：现实场景构造 | **真实工作来源**：数据分析师处理模糊需求
> **证据描述**：数据分析师收到模糊的"帮我算一下总数"等指令，需要先追问具体列/范围后再执行

##### interactive_calc_001（L3）

- **场景描述**：The user wants to calculate a total for the sales spreadsheet but doesn't specify which column or row. The agent asks, then adds a Total row with SUM formulas at the bottom.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `agent_asks`）：Help me calculate the total for this data
  - Phase 2（trigger: `agent_done`）：Add a new row at the bottom: write "Total" in the first column, and use SUM formulas for each month column, then save

##### interactive_calc_002（L3）

- **场景描述**：The user wants to copy a column to a new sheet but doesn't specify which one. The agent asks, then copies the Revenue column to Sheet2.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `agent_asks`）：Help me copy a column to a new sheet
  - Phase 2（trigger: `agent_done`）：Copy the Revenue column (including the header) to a new Sheet2, starting at A1, then save

##### interactive_calc_003（L3）

- **场景描述**：The user says to calculate profit but doesn't specify the column names or formula. The agent asks, then adds a Profit=Sales-COGS column.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `agent_asks`）：Help me add the profit data
  - Phase 2（trigger: `agent_done`）：Add a new Profit column to the right of the existing columns, with the formula Sales - COGS, then save

##### interactive_calc_004（L2）

- **场景描述**：The user says to back up the data but doesn't specify where. The agent asks, then copies all data to Sheet2.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `agent_asks`）：Help me back up this data
  - Phase 2（trigger: `agent_done`）：Copy all data from Sheet1 (including headers) to a new Sheet2, then save


#### 场景类型：`error_correction`（错误纠正）—— 2 个

> **来源类型**：现实场景构造 | **真实工作来源**：排序/公式错误修正
> **证据描述**：用户提交后发现排序方向错误或公式遗漏，要求回滚并纠正

##### interactive_calc_error_correction_001（L3）

- **场景描述**：User asks to sort by a column, but the instruction is ambiguous. After agent sorts by the wrong column, user clarifies the correct one.
- **阶段数**：3
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=5））：Sort the data by the highest numbers
  - Phase 2（trigger: `agent_done`）：No, that's the wrong column! I meant sort by the March column specifically, from highest to lowest. Please undo what you did and redo it correctly.
  - Phase 3（trigger: `agent_done`）：Good, now also add a Total row at the bottom with SUM for each column, and save.

##### interactive_calc_error_correction_002（L3）

- **场景描述**：User asks agent to create a summary in Sheet2, but agent misunderstands and modifies Sheet1. User corrects.
- **阶段数**：3
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=5））：Create a summary of total sales somewhere in the spreadsheet
  - Phase 2（trigger: `agent_done`）：That's not what I wanted. Please undo that. I need the summary on a NEW sheet called 'Summary', not on the existing sheet. Put 'Total Sales' in A1 and
  - Phase 3（trigger: `agent_done`）：Also add 'Total COGS' in A2 and the sum of COGS in B2 on the Summary sheet. Save the file.


#### 场景类型：`multi_step_workflow`（多步工作流）—— 2 个

> **来源类型**：现实场景构造 | **真实工作来源**：季度报告完整工作流
> **证据描述**：从添加计算列、排序、新建汇总表到格式化的完整链路

##### interactive_calc_workflow_001（L3）

- **场景描述**：Sequential 4-step workflow: sort data, add formulas, create summary sheet, format headers.
- **阶段数**：4
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `agent_done`）：First, add a 'Total' column at the end that sums all monthly values for each sales rep.
  - Phase 2（trigger: `agent_done`）：Now sort the entire table by the Total column from highest to lowest.
  - Phase 3（trigger: `agent_done`）：Create a new sheet called 'Summary'. In A1 write 'Top Performer', in B1 write the name of the sales rep with the highest total.
  - Phase 4（trigger: `agent_done`）：Go back to Sheet1, make the header row bold, then save the file.

##### interactive_calc_workflow_002（L3）

- **场景描述**：Sequential 4-step workflow: rename sheet, add computed column, filter and copy, add summary.
- **阶段数**：4
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `agent_done`）：Rename the first sheet from 'Sheet1' to 'Income Data'.
  - Phase 2（trigger: `agent_done`）：Add a column called 'Margin' that calculates Revenue minus Expenses for each row.
  - Phase 3（trigger: `agent_done`）：Create a new sheet called 'High Margin'. Copy all rows where Margin is positive to this new sheet.
  - Phase 4（trigger: `agent_done`）：In the 'High Margin' sheet, add a Total row at the bottom summing the Margin column. Save the file.


#### 场景类型：`progressive_refinement`（渐进精化）—— 4 个

> **来源类型**：现实场景构造 | **真实工作来源**：分阶段数据报告
> **证据描述**：先做初步汇总让经理确认，再逐步加入排序/格式化/新建汇总表

##### interactive_calc_013（L3）

- **场景描述**：The user first asks the agent to add a Total row, then after confirmation asks to also add an Average row.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me add a Total row at the bottom that sums each month's data
  - Phase 2（trigger: `agent_done`）：The Total row is done. Now add an Average row right below it that calculates the mean for each month column, then save

##### interactive_calc_014（L3）

- **场景描述**：The user first asks to copy Revenue to Sheet2, then asks to add a percentage column.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me copy the Revenue column to Sheet2
  - Phase 2（trigger: `agent_done`）：Sheet2 has data now. Add a 'Percentage' column next to Revenue that calculates each row's share of the total Revenue, then save

##### interactive_calc_015（L3）

- **场景描述**：The user first asks to add a Profit column, then after confirmation asks to add an Average summary row.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me add a Profit column with formula Sales - COGS
  - Phase 2（trigger: `agent_done`）：Profit column is done. Now add a row at the bottom: write 'Average' in the first cell, and calculate the mean for each numeric column, then save

##### interactive_calc_016（L3）

- **场景描述**：The user first asks to create a product summary on Sheet2, then asks to add a ranking column.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me summarize Total Revenue by Product on Sheet2
  - Phase 2（trigger: `agent_done`）：Summary is done. Now add a 'Rank' column on Sheet2 that ranks by Revenue from highest to lowest, then save


#### 场景类型：`requirement_change`（需求变更）—— 5 个

> **来源类型**：现实场景构造 | **真实工作来源**：需求变更的报表任务
> **证据描述**：财务主管先要求做利润列，中途改为按利润率排序并添加汇总表

##### interactive_calc_017（L3）

- **场景描述**：The user first asks to sort by January ascending, then changes their mind and wants February descending instead.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me sort by the January column from smallest to largest
  - Phase 2（trigger: `agent_done`）：Changed my mind. Sort by the February column from largest to smallest instead. Undo the previous sort first, then save

##### interactive_calc_018（L3）

- **场景描述**：The user first asks to put Revenue total on Sheet2, then changes their mind and wants it at the bottom of Sheet1 instead, and to delete Sheet2.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me put the Revenue total on Sheet2
  - Phase 2（trigger: `agent_done`）：Wrong location. Put the total at the bottom of the Revenue column on Sheet1 instead, and delete Sheet2, then save

##### interactive_calc_019（L3）

- **场景描述**：The user first asks to count Invoice No. occurrences on Sheet2, then changes to summing amounts instead.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me count each Invoice No.'s occurrences on Sheet2
  - Phase 2（trigger: `agent_done`）：Don't count occurrences anymore. Instead, sum up the amount for each Invoice No., and rename the column to 'Total Amount', then save

##### interactive_calc_020（L3）

- **场景描述**：The user first asks to sort by Promotion Type, then changes to sorting by Revenue descending.
- **阶段数**：2
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Help me sort by the Promotion Type column
  - Phase 2（trigger: `agent_done`）：Don't sort by that column. Sort by the Revenue column from largest to smallest instead. Undo the previous sort first, then save

##### interactive_calc_requirement_change_001（L3）

- **场景描述**：The user changes a requirement mid-task after the agent has already acted on earlier instructions.
- **阶段数**：3
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `agent_done`）：Help me spreadsheetFirstcolumn
  - Phase 2（trigger: `agent_done`）：, change , Firstcolumn, Help me Secondcolumn, 's
  - Phase 3（trigger: `agent_done`）：'s , Help me save the file


#### 场景类型：`task_interruption`（任务中断）—— 2 个

> **来源类型**：现实场景构造 | **真实工作来源**：工作中断追加约束
> **证据描述**：正在创建汇总表时被告知需要额外添加新列或调整格式

##### interactive_calc_interruption_001（L3）

- **场景描述**：User asks agent to add formulas to a spreadsheet, then interrupts to check system disk space, then asks to continue the spreadsheet work.
- **阶段数**：3
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Add a Total row at the bottom of the spreadsheet with SUM formulas for each month column
  - Phase 2（trigger: `agent_done`）：Wait, before you continue - can you quickly check the disk space on the system? Run 'df -h' in a terminal and tell me how much space is left on the ro
  - Phase 3（trigger: `agent_done`）：OK thanks. Now go back to the spreadsheet and also add an Average row below the Total row, calculating the average for each month column. Save the fil

##### interactive_calc_interruption_002（L3）

- **场景描述**：User asks agent to sort data, then interrupts to create a backup copy of the file, then asks to continue with conditional formatting.
- **阶段数**：3
- **评估函数**：`check_include_exclude`
- **Phase 设计**：
  - Phase 1（trigger: `step_count`（value=3））：Sort the spreadsheet by the Sales column from highest to lowest
  - Phase 2（trigger: `agent_done`）：Hold on - before you do anything else, please save a backup copy of this file as WeeklySales_backup.xlsx on the Desktop
  - Phase 3（trigger: `agent_done`）：Great. Now in the original WeeklySales.xlsx, add a Profit column (Sales minus COGS) and save.

#### Interactive 任务来源映射

> 目标：为每个 Interactive 场景补齐"来源证据链"，用于论文中证明任务来自真实工作流并经过人工筛选。
> 说明：`source_ref` 可填写匿名化 URL、工单号或访谈记录编号；`evidence_pack` 建议与任务 JSON 同步归档。

| 场景类型 | 任务数 | 真实工作来源（Primary Source） | 证据包（最小） | Task JSON `source` 建议写法 |
|---------|-------|---------------------------|-------------|--------------------------|
| `ambiguous_target`（模糊目标） | 4 | 数据分析师处理模糊需求（"帮我算总数"→追问→执行） | ① 原始模糊需求摘录 ② agent 追问记录 ③ 澄清后执行确认 | `libreoffice_calc_interactive;source_type=data_analysis_request;evidence=ambiguous_target` |
| `ambiguous_detail`（模糊细节） | 4 | 财务报表细节不明确（"做个汇总"→澄清维度→执行） | ① 原始需求 ② 细节缺失分析 ③ 补充后完整指令 | `libreoffice_calc_interactive;source_type=financial_report;evidence=detail_clarification` |
| `ambiguous_scope`（模糊范围） | 4 | 数据清洗范围不确定（"清理数据"→确认列→执行） | ① 原始清洗需求 ② 范围确认对话 ③ 最终操作列表 | `libreoffice_calc_interactive;source_type=data_cleaning;evidence=scope_clarification` |
| `progressive_refinement`（渐进精化） | 4 | 分阶段数据报告（初版汇总→确认→精化排序/格式） | ① 初版汇总确认 ② 第二轮精化指令 ③ 最终交付确认 | `libreoffice_calc_interactive;source_type=staged_delivery;evidence=progressive_refinement` |
| `requirement_change`（需求变更） | 5 | 需求变更的报表任务（先做利润列→改为按利润率排序） | ① 初始需求 ② 变更时间点和新指令 ③ 前后差异记录 | `libreoffice_calc_interactive;source_type=report_revision;evidence=requirement_change` |
| `error_correction`（错误纠正） | 2 | 排序/公式错误修正（发现方向错→回滚纠正） | ① 错误描述 ② 纠正指令 ③ 修正后验证记录 | `libreoffice_calc_interactive;source_type=error_fix;evidence=error_correction` |
| `task_interruption`（任务中断） | 2 | 工作中断追加约束（做汇总表→临时追加新列） | ① 中断前进度 ② 追加约束内容 ③ 最终合并结果 | `libreoffice_calc_interactive;source_type=work_interruption;evidence=constraint_addition` |
| `multi_step_workflow`（多步工作流） | 2 | 季度报告完整工作流（计算列→排序→汇总表→格式化） | ① 各阶段指令序列 ② 中间产物确认 ③ 最终交付验收 | `libreoffice_calc_interactive;source_type=quarterly_report;evidence=full_workflow` |

#### 来源证据落地字段（建议统一）

- **source_type**：`data_analysis_request` / `financial_report` / `data_cleaning` / `staged_delivery` / `report_revision` / `error_fix` / `work_interruption` / `quarterly_report`
- **source_ref**：来源标识（匿名化 URL、工单号、访谈记录编号）
- **captured_at**：取证日期（`YYYY-MM-DD`）
- **anonymized_excerpt**：匿名化原文摘录（1~3 句）
- **mapping_note**：原始需求如何映射到 `phases` 与 `trigger`
- **reviewers**：双人审核与仲裁记录（`reviewer_a/reviewer_b/adjudicator`）

#### Interactive 触发类型分布

| 触发类型 | 中文 | 出现次数 | 说明 |
|---------|------|---------|------|
| `agent_done` | 代理完成 | 39 | 上一阶段完成后自动进入下一阶段 |
| `agent_asks` | 代理追问 | 12 | agent 主动向用户追问澄清后触发 |
| `step_count` | 步数触发 | 12 | 达到指定步数后注入新指令 |

---

## 4. 评估函数汇总

文件：`desktop_env/evaluators/metrics/table.py`

| # | 函数名 | 类别 | 描述 | 使用次数 | 复杂度 |
|---|--------|------|------|---------|--------|
| 1 | `compare_table` | 静态任务 | 多规则结构化对比 .xlsx 文件（支持 15+ 种规则组合） | 49 | 中 |
| 2 | `compare_csv` | 静态任务 | 逐行逐字符对比 CSV 文件 | 1 | 低 |
| 3 | `check_include_exclude` | 交互任务 | 验证 VM 命令行输出包含/排除指定字符串 | 27 | 低 |

**总计**：3 个评估函数，覆盖 50 个静态任务 + 27 个交互任务 = **77** 个任务。全部已实现，无需新增。

---

## 5. 素材说明

所有电子表格素材均为人工设计的合成数据（非真实业务数据），覆盖典型业务场景。

### 技术规格

| 属性 | 值 |
|------|-----|
| 文件格式 | `.xlsx`（Office Open XML Spreadsheet） |
| 静态任务文件总数 | 50 个初始文件 + 50 个 gold 文件（含 1 个 `.csv` gold） |
| 语言 | 所有列名和数据均为英文 |
| 数据规模（典型） | 5-30 行 × 5-12 列 |

### 数据领域分布

| 领域 | 约任务数 | 示例文件 |
|------|---------|---------|
| 销售数据 | ~15 | SalesData, SalesRegion, SalesProduct, Monthly_Sales, Transactions |
| 员工信息 | ~10 | EmployeeData, EmpComprehensive, EmpBudget, Employee_Name_Split |
| 库存管理 | ~6 | Inventory, InvRestock, InvReorder, InvAnalysis |
| 项目管理 | ~8 | ProjectData, ProjTimeline, ProjAnalysis, ProjStatus |
| 财务报表 | ~6 | Financial_Data, Annual_Revenue, Quarterly, Zone_Quarterly_Sales |
| 其他 | ~5 | Customer_Deduplicate, Product_Name_Clean, Loan_Due_Date, Temperature |

---

## 6. Task JSON 模板

### 单规则评估（大部分 L1 任务）

```json
{
  "id": "<uuid4>",
  "snapshot": "libreoffice_calc",
  "instruction": "<操作指令>",
  "config": [
    {
      "type": "upload_file",
      "parameters": {
        "files": [
          {"local_path": "cache/<id>/<file>.xlsx", "path": "/home/user/<file>.xlsx"}
        ]
      }
    },
    {
      "type": "open",
      "parameters": {"path": "/home/user/<file>.xlsx"}
    }
  ],
  "evaluator": {
    "postconfig": [
      {"type": "activate_window", "parameters": {"window_name": "<file>.xlsx - LibreOffice Calc", "strict": true}},
      {"type": "sleep", "parameters": {"seconds": 0.5}},
      {"type": "execute", "parameters": {"command": ["python", "-c", "import pyautogui, time; pyautogui.hotkey('ctrl','s'); time.sleep(1.5); pyautogui.press('return');"]}},
      {"type": "sleep", "parameters": {"seconds": 0.5}}
    ],
    "func": "compare_table",
    "expected": {"type": "cache_file", "path": "<file>_gold.xlsx"},
    "result": {"type": "vm_file", "path": "/home/user/<file>.xlsx", "dest": "<file>.xlsx"},
    "options": {"rules": [{"type": "sheet_data", "sheet_idx0": 0, "sheet_idx1": "EI0"}]}
  },
  "difficulty": "L1"
}
```

### 多规则评估（大部分 L2/L3 任务）

```json
{
  "id": "<uuid4>",
  "snapshot": "libreoffice_calc",
  "instruction": "<多步操作描述>",
  "config": ["...同上..."],
  "evaluator": {
    "postconfig": ["...同上..."],
    "func": "compare_table",
    "expected": {"type": "cache_file", "path": "<file>_gold.xlsx"},
    "result": {"type": "vm_file", "path": "/home/user/Desktop/<file>.xlsx", "dest": "<file>.xlsx"},
    "options": {"rules": [
      {"type": "sheet_name"},
      {"type": "sheet_data", "sheet_idx0": 0, "sheet_idx1": 0},
      {"type": "sheet_data", "sheet_idx0": 1, "sheet_idx1": 1},
      {"type": "freeze", "sheet_idx0": 0, "sheet_idx1": 0},
      {"type": "style", "sheet_idx0": 0, "sheet_idx1": 0, "props": ["font_bold"]}
    ]}
  },
  "difficulty": "L3"
}
```

### CSV 导出评估

```json
{
  "evaluator": {
    "func": "compare_csv",
    "expected": {"type": "cache_file", "path": "Export_to_CSV.csv"},
    "result": {"type": "vm_file", "path": "/home/user/Export_to_CSV.csv", "dest": "Export_to_CSV.csv"}
  }
}
```

---

## 7. Docker 镜像要求

VM/Docker 镜像需要预装：

- **LibreOffice**（推荐 7.x+，支持 `.xlsx` 读写）
  ```bash
  apt-get install libreoffice-calc
  ```
- **X11 显示环境**（LibreOffice 需要 GUI）
- **Python 3 + openpyxl**（评估器运行环境）
  ```bash
  pip install openpyxl
  ```
- **PyAutoGUI**（postconfig 中自动保存操作）
  ```bash
  pip install pyautogui
  ```

验证安装：
```bash
libreoffice --version
python3 -c "import openpyxl; print(openpyxl.__version__)"
```

**注意**：评估器使用 `openpyxl` 进行 `.xlsx` 文件对比，需确保在评估环境中安装。VM 上仅需 LibreOffice GUI 和 PyAutoGUI。

---

## 8. 任务难度分布总结

| 级别 | 数量 | 指令长度 | 操作步骤 | 描述 | 示例 |
|------|------|---------|---------|------|------|
| L1 | 7 | 64-119 字符 | 1-2 步 | 单步原子操作 | 排序、冻结行、复制列到新表、计算合计行 |
| L2 | 13 | 138-318 字符 | 2-4 步 | 多步复合操作 | 新增公式列+重排列、VLOOKUP 填充、条件高亮+样式、数据验证 |
| L3 | 10 | 444-638 字符 | 5-8 步 | 复杂工作流（带编号子步骤） | 多表创建+排序+公式+样式+冻结全组合、8 步综合分析报表 |
| **总计** | **30** | | | | |

### 可验证性保证

所有任务的验证基于以下可靠机制：

1. **`.xlsx` 结构化对比**：使用 `openpyxl` 逐单元格/逐工作表对比数据值、格式属性、图表结构等客观指标。不依赖截图对比、OCR 或其他不可靠的视觉检查方法。
2. **CSV 文本对比**：直接逐行字符级比较，零误差容忍。
3. **多维度规则组合**：L2/L3 任务同时验证数据、样式、冻结、工作表名称等多个维度，确保全面覆盖。
4. **交互任务命令行验证**：通过 `check_include_exclude` 在 VM 上执行命令行检查输出文件内容，验证关键字存在性。

> 难度标签基于 kimi-k2.5 模型在 max_steps=50（静态）/ max_steps=80（交互）条件下的实际执行结果。
> L1 = score=1.0 且 steps<=10；L2 = score=1.0 且 steps<=25 或 score<1.0 且 steps<=10；L3 = 其余。

---

## 9. 常见陷阱

### LibreOffice 保存对话框

- **格式保存提示**：当文件为 `.xlsx` 格式时，`Ctrl+S` 会弹出"Keep Current Format?"对话框。`postconfig` 中需要在 `Ctrl+S` 后额外按 `Enter` 确认。
- **延时要求**：`Ctrl+S` 后需等待 **1.5 秒** 才能按 `Enter`，否则对话框可能尚未弹出导致保存失败。
- **评分影响**：若保存未完成（对话框未关闭），下载的文件将是旧版本，导致评估得分为 0.0。

### openpyxl 对比注意事项

- **日期格式**：LibreOffice 可能将日期存储为浮点数（Excel 序列号）或字符串格式，与直接在 Excel 中操作的格式略有差异。评估时需统一处理。
- **公式 vs 值**：`openpyxl` 默认读取公式文本而非计算后的值。评估器使用 `data_only=True` 模式读取缓存值。但 LibreOffice 保存的 `.xlsx` 中缓存值可能不存在，需确保保存时触发重新计算。
- **空单元格**：LibreOffice 可能在空单元格中写入空字符串（`""`）而非 `None`，对比时需统一处理为相同值。
- **样式继承**：粗体/颜色等样式可能通过行/列默认样式继承而非直接设置在单元格上，检查样式时需考虑继承链。

### Gold 文件管理

- **双目录存放**：gold 文件必须同时存在于 `OSWorld/cache/<task_id>/` 和 `desktopworld/cache/<task_id>/` 两个目录。缺少任一位置会导致评估器 `AssertionError`。
- **命名约定**：静态任务 gold 文件命名为 `<原始文件名>_gold.xlsx`（如 `SalesData_L2_01_gold.xlsx`）。

### Task JSON 常见问题

- **文件路径差异**：`calc_new` 任务文件路径为 `/home/user/<file>.xlsx`；`calc_hard` 任务文件路径为 `/home/user/Desktop/<file>.xlsx`。混用会导致文件找不到。
- **工作表索引**：`sheet_idx0` 指 result 文件中的工作表索引，`sheet_idx1` 指 gold 文件中的索引。特殊值 `"EI0"` 表示按名称匹配而非按位置。
- **多表任务**：需要为每个新建的工作表分别添加 `sheet_data` 规则，否则只检查第一个工作表。
