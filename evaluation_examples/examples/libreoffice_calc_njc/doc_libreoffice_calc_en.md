# LibreOffice Calc Task Design Document

## 0. Verification Strategy

### Core Approach

LibreOffice Calc verification downloads the user-edited `.xlsx` file from the VM and performs structured comparison against a pre-built gold standard file.

1. **Table Structure Comparison** (`compare_table`): Uses `openpyxl` to parse `.xlsx` files, supporting multi-dimensional comparison -- cell data, worksheet names, frozen panes, styles (bold/color/merge), data validation rules, charts, etc.
2. **CSV Export Comparison** (`compare_csv`): For CSV export tasks, directly compares text content line by line.

**Evaluator Architecture**: All evaluation functions download result files from VM via `vm_file` getter and load gold files from cache, performing comparison locally.

### Evaluator Pattern

```python
def compare_table(result: str, expected: str, **options) -> float:
    """
    Args:
        result: Path to user-edited .xlsx file downloaded from VM
        expected: Path to pre-built gold standard .xlsx file
        options["rules"]: List of comparison rules, each specifying a check dimension
    Returns:
        1.0 (all rules pass) or 0.0 (any rule fails)
    """
```

---

## 1. Available Resources

Total: **50** initial files + corresponding gold standard files

### calc_new Materials (30 tasks)

| # | Initial File | Gold File | Task Summary |
|---|-------------|-----------|-------------|
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

### calc_hard Materials (20 tasks)

| # | Initial File | Gold File | Task Summary |
|---|-------------|-----------|-------------|
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

## 2. Evaluation Function Design

File: `desktop_env/evaluators/metrics/table.py`

### 2.1 Main Evaluation Functions

| Function | Description | Usage Count |
|----------|-------------|-------------|
| `compare_table` | Structured comparison of two .xlsx files by rule list | 49 |
| `compare_csv` | Line-by-line CSV file comparison | 1 |

### 2.2 Rule Type Details

| Rule Type | Description | Usage Count |
|-----------|-------------|-------------|
| `sheet_data` | Compare cell data on specified worksheets | 71 |
| `sheet_name` | Verify worksheet name list matches | 20 |
| `style` | Compare cell styles (bold/color/merge) | 14 |
| `freeze` | Verify frozen pane position | 12 |
| `chart` | Compare embedded charts (type/data range/title) | 2 |
| `data_validation` | Verify data validation rules (dropdowns/range limits) | 1 |

---

## 3. Task Definitions


### 3.1 Level 1 (L1) -- Basic Operations -- 3 tasks

> Tasks completed by agent within 10 steps with score 1.0

#### Task L1-1: Financial_Data_CopyCol

- **ID**: `79872a2b-ef63-4bda-96e5-790310f5be45`
- **Source**: `calc_new`
- **Instruction**: Copy the "Expenses ($)" column along with its header to a new sheet named "Sheet2".
- **Material File**: `Financial_Data_CopyCol.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_data`
- **Gold File**: `Financial_Data_CopyCol_gold.xlsx`

#### Task L1-2: Employee_Name_Concat

- **ID**: `86a0574a-367d-4611-9c8e-748fc82b412e`
- **Source**: `calc_new`
- **Instruction**: Create a "Full Name" column by concatenating "First Name" and "Last Name" with a space in between for each employee. Finish the work and don't touch irrelevant regions.
- **Material File**: `Employee_Name_Concat.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_data`
- **Gold File**: `Employee_Name_Concat_gold.xlsx`

#### Task L1-3: Inventory_Freeze_Row

- **ID**: `f6b1639f-d2b2-4078-98dd-dd9f3ce35237`
- **Source**: `calc_new`
- **Instruction**: Help me freeze the first row on this sheet to keep the headers always visible when scrolling.
- **Material File**: `Inventory_Freeze_Row.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `freeze`, `sheet_data`
- **Gold File**: `Inventory_Freeze_Row_gold.xlsx`

#### L1 Task Source Annotations

| Task | Source Type | Specific Source | Annotation Reason |
|------|-----------|-----------------|-------------------|
| L1-1 | Official Help | [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Copy the "Expenses ($)" column along with its header to a new sheet named "Sheet |
| L1-2 | Official Help | [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Create a "Full Name" column by concatenating "First Name" and "Last Name" with a |
| L1-3 | Official Help | [Freezing Rows/Columns](https://help.libreoffice.org/latest/en-US/text/scalc/guide/line_fix.html) | Help me freeze the first row on this sheet to keep the headers always visible wh |

#### L1 Task Summary Table

| # | Task Name | Material File | Evaluation Function |
|---|-----------|---------------|---------------------|
| 1 | Financial_Data_CopyCol | `Financial_Data_CopyCol.xlsx` | `compare_table` (sheet_data) |
| 2 | Employee_Name_Concat | `Employee_Name_Concat.xlsx` | `compare_table` (sheet_data) |
| 3 | Inventory_Freeze_Row | `Inventory_Freeze_Row.xlsx` | `compare_table` (freeze, sheet_data) |


### 3.2 Level 2 (L2) -- Compound Operations -- 6 tasks

> Tasks completed within 25 steps (score 1.0) or failed within 10 steps

#### Task L2-1: Loan_Due_Date

- **ID**: `3fd989e0-61f2-4f77-a604-a0c0ae0f8c7b`
- **Source**: `calc_new`
- **Instruction**: Calculate the due date for each loan by adding the "Term (Days)" to the "Issue Date" and fill in the "Due Date" column.
- **Material File**: `Loan_Due_Date.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_data`
- **Gold File**: `Loan_Due_Date_gold.xlsx`

#### Task L2-2: WeeklyRevenue_AddProfit

- **ID**: `55b85705-22a1-4ed1-abf4-686015978529`
- **Source**: `calc_new`
- **Instruction**: Add a new column named "Profit" right after the "Cost" column and calculate the profit for each week by subtracting "Cost" from "Revenue".
- **Material File**: `WeeklyRevenue_AddProfit.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_data`
- **Gold File**: `WeeklyRevenue_AddProfit_gold.xlsx`

#### Task L2-3: Finance_Sheet2_Sum

- **ID**: `b8185158-1fda-4729-ad1a-b76a8afa9ecf`
- **Source**: `calc_new`
- **Instruction**: Compute the sum of the "Revenue ($)" and "Expenses ($)" columns and put the results under two column headers named "Total Revenue ($)" and "Total Expenses ($)" in a new sheet named "Sheet2".
- **Material File**: `Finance_Sheet2_Sum.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_data`
- **Gold File**: `Finance_Sheet2_Sum_gold.xlsx`

#### Task L2-4: Project_Tasks_Validation

- **ID**: `d8ddb9e1-06aa-4181-ae78-e70d07be83e9`
- **Source**: `calc_new`
- **Instruction**: In the "Status" column, enable data validation for cells F2:F16 so that the values can be directly selected from a drop down list with options "Open", "In Progress", and "Done". Finish the work and don't touch irrelevant regions, even if they are blank.
- **Material File**: `Project_Tasks_Validation.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_data`, `data_validation`
- **Gold File**: `Project_Tasks_Validation_gold.xlsx`

#### Task L2-5: Branch_Manager_Lookup

- **ID**: `df47cfc4-b12a-4e1c-89f5-94fda600b12e`
- **Source**: `calc_new`
- **Instruction**: There is a lookup table in the "Lookup" sheet listing the manager for each city. Please fill in the "Manager" column in Sheet1 for each branch office according to its city.
- **Material File**: `Branch_Manager_Lookup.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_data`
- **Gold File**: `Branch_Manager_Lookup_gold.xlsx`

#### Task L2-6: Employee_Dept_Fill_Blank

- **ID**: `ff761a9f-28ed-4178-b3fc-1e91fe8096db`
- **Source**: `calc_new`
- **Instruction**: Fill all the blank cells in the "Department" column (B2:B26) with the value in the cell above it. Finish the work and don't touch irrelevant regions, even if they are blank.
- **Material File**: `Employee_Dept_Fill_Blank.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_data`
- **Gold File**: `Employee_Dept_Fill_Blank_gold.xlsx`

#### L2 Task Source Annotations

| Task | Source Type | Specific Source | Annotation Reason |
|------|-----------|-----------------|-------------------|
| L2-1 | Official Help | [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) | Calculate the due date for each loan by adding the "Term (Days)" to the "Issue D |
| L2-2 | Official Help | [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) | Add a new column named "Profit" right after the "Cost" column and calculate the  |
| L2-3 | Official Help | [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Compute the sum of the "Revenue ($)" and "Expenses ($)" columns and put the resu |
| L2-4 | Official Help | [Data Validation](https://help.libreoffice.org/latest/en-US/text/scalc/guide/validity.html) | In the "Status" column, enable data validation for cells F2:F16 so that the valu |
| L2-5 | Official Help | [VLOOKUP](https://help.libreoffice.org/latest/en-US/text/scalc/01/04060109.html) | There is a lookup table in the "Lookup" sheet listing the manager for each city. |
| L2-6 | Official Help | [Spreadsheet Operations](https://help.libreoffice.org/latest/en-US/text/scalc/guide/main.html) | Fill all the blank cells in the "Department" column (B2:B26) with the value in t |

#### L2 Task Summary Table

| # | Task Name | Material File | Evaluation Function |
|---|-----------|---------------|---------------------|
| 1 | Loan_Due_Date | `Loan_Due_Date.xlsx` | `compare_table` (sheet_data) |
| 2 | WeeklyRevenue_AddProfit | `WeeklyRevenue_AddProfit.xlsx` | `compare_table` (sheet_data) |
| 3 | Finance_Sheet2_Sum | `Finance_Sheet2_Sum.xlsx` | `compare_table` (sheet_data) |
| 4 | Project_Tasks_Validation | `Project_Tasks_Validation.xlsx` | `compare_table` (sheet_data, data_validation) |
| 5 | Branch_Manager_Lookup | `Branch_Manager_Lookup.xlsx` | `compare_table` (sheet_data) |
| 6 | Employee_Dept_Fill_Blank | `Employee_Dept_Fill_Blank.xlsx` | `compare_table` (sheet_data) |


### 3.3 Level 3 (L3) -- Advanced Workflows -- 41 tasks

> Tasks agent cannot complete or requiring >25 steps

#### Task L3-1: Order_Sequence_Number

- **ID**: `0de46e41-e54a-44f9-8655-96b5d017f587`
- **Source**: `calc_new`
- **Instruction**: Fill the Sequence Numbers as "No. #" (e.g. No. 1, No. 2, ...) in the "Seq No." column. Finish the work and don't touch irrelevant regions, even if they are blank.
- **Material File**: `Order_Sequence_Number.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_data`
- **Gold File**: `Order_Sequence_Number_gold.xlsx`

#### Task L3-2: Employee_Name_Split

- **ID**: `146b595a-9dcc-4637-b5f3-d347deff6859`
- **Source**: `calc_new`
- **Instruction**: The "Full Name" column contains names in "Last, First" format. Please split them and fill in the "First Name" and "Last Name" columns. Finish the work and don't touch the original data.
- **Material File**: `Employee_Name_Split.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_data`
- **Gold File**: `Employee_Name_Split_gold.xlsx`

#### Task L3-3: Customer_Deduplicate

- **ID**: `27fdf845-4947-48cf-a282-8163a3941abf`
- **Source**: `calc_new`
- **Instruction**: Check the names in the "Customer Names with Duplicates" column and put the unique ones in the "Unique Customers" column. Keep the original order of first occurrences. Finish the work and don't touch irrelevant regions, even if they are blank.
- **Material File**: `Customer_Deduplicate.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_data`
- **Gold File**: `Customer_Deduplicate_gold.xlsx`

#### Task L3-4: Product_Name_Clean

- **ID**: `32faea23-58b3-471f-957a-f8798afde48a`
- **Source**: `calc_new`
- **Instruction**: I want to copy the product names in the "Raw Name" column to the "Clean Name" column. Please remove redundant whitespaces and canonicalize the letter cases by capitalizing the first letter of each word and leaving other letters as lower case. Finish the work and don't touch irrelevant regions, even if they are blank.
- **Material File**: `Product_Name_Clean.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_data`
- **Gold File**: `Product_Name_Clean_gold.xlsx`

#### Task L3-5: Dept_Budget_Summary

- **ID**: `700c6067-8428-4975-92d9-b06f6147b894`
- **Source**: `calc_new`
- **Instruction**: Create a table in a new sheet named "Sheet2" with two column headers "Department" and "Total Budget ($)", showing the total budget amount for each department in alphabetical order.
- **Material File**: `Dept_Budget_Summary.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_data`
- **Gold File**: `Dept_Budget_Summary_gold.xlsx`

#### Task L3-6: Temperature_Sort_Chart

- **ID**: `7412aed6-5083-441b-a86a-9b7da14fa46b`
- **Source**: `calc_new`
- **Instruction**: Sort the data by the "Date" column in ascending order and then create a line chart with "Date" on the x-axis and "Temperature (°C)" on the y-axis. Set the chart title as "Daily Temperature".
- **Material File**: `Temperature_Sort_Chart.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_data`, `chart`
- **Gold File**: `Temperature_Sort_Chart_gold.xlsx`

#### Task L3-7: Monthly_Total_LineChart

- **ID**: `76e0f722-3cf0-41bb-92d6-a9a9f6f8afb7`
- **Source**: `calc_new`
- **Instruction**: Work out the monthly total sales in a new row called "Total" and then create a line chart to show the results (x-axis should be the months).
- **Material File**: `Monthly_Total_LineChart.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_data`
- **Gold File**: `Monthly_Total_LineChart_gold.xlsx`

#### Task L3-8: Monthly_Sales_TotalRow

- **ID**: `787f1683-8624-47ec-b1fa-f449c4e4c993`
- **Source**: `calc_new`
- **Instruction**: Work out the monthly total sales in a new row called "Total" at the bottom of the table.
- **Material File**: `Monthly_Sales_TotalRow.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_data`
- **Gold File**: `Monthly_Sales_TotalRow_gold.xlsx`

#### Task L3-9: Export_to_CSV

- **ID**: `7bc32014-b9a0-4ed0-8979-1bf946fd40f8`
- **Source**: `calc_new`
- **Instruction**: Could you help me to export the current sheet to a CSV file? Export the contents just as they are shown on the screen. Keep the other options untouched. The CSV file should share the same file name as the spreadsheet (without the .xlsx extension).
- **Material File**: `Export_to_CSV.xlsx`
- **Evaluation Function**: `compare_csv`
- **Gold File**: `Export_to_CSV.csv`

#### Task L3-10: Report_Header_Merge

- **ID**: `84e17652-f3f2-4475-98b2-ab92cbd00cc8`
- **Source**: `calc_new`
- **Instruction**: Create a new sheet named "Sheet2" and merge cells A1:D1 to write the header "Q1 & Q2 Sales Report" with a blue (#0000ff) background fill and bold white text.
- **Material File**: `Report_Header_Merge.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_data`, `style`
- **Gold File**: `Report_Header_Merge_gold.xlsx`

#### Task L3-11: Product_Gross_Margin

- **ID**: `8c891b4d-2e1e-4a79-9a4d-2e326c6d5ae9`
- **Source**: `calc_new`
- **Instruction**: Calculate the gross margin percentage for each product using the formula (Revenue - COGS) / Revenue × 100, rounded to 2 decimal places, and fill in the "Gross Margin (%)" column.
- **Material File**: `Product_Gross_Margin.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_data`
- **Gold File**: `Product_Gross_Margin_gold.xlsx`

#### Task L3-12: Exam_Score_Highlight

- **ID**: `9d33210e-6323-4fdf-ab60-8a4904e41081`
- **Source**: `calc_new`
- **Instruction**: Please highlight all the cells in the "Score" column that have a value greater than 90 by setting the cell background to green (#00ff00). Finish the work and don't touch irrelevant regions, even if they are blank.
- **Material File**: `Exam_Score_Highlight.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_data`, `style`
- **Gold File**: `Exam_Score_Highlight_gold.xlsx`

#### Task L3-13: Zone_Quarterly_Sales

- **ID**: `a1d243af-6773-487a-a46b-b46211de2902`
- **Source**: `calc_new`
- **Instruction**: Fill the missing values in the "Total" column and the "Total" row with the correct sums.
- **Material File**: `Zone_Quarterly_Sales.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_data`
- **Gold File**: `Zone_Quarterly_Sales_gold.xlsx`

#### Task L3-14: Order_Code_Pad

- **ID**: `bff35d23-fc7e-4f5f-9a7f-d40deefa7202`
- **Source**: `calc_new`
- **Instruction**: Copy the numbers in the "Old Code" column to the "Padded Code (8 digits)" column, padding them with leading zeros to fill up to 8 digits. Finish the work and don't touch irrelevant regions, even if they are blank.
- **Material File**: `Order_Code_Pad.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_data`
- **Gold File**: `Order_Code_Pad_gold.xlsx`

#### Task L3-15: Annual_Revenue_Growth

- **ID**: `c8bfd197-8faa-4c62-baca-943c0907b9dd`
- **Source**: `calc_new`
- **Instruction**: In a new sheet named "Sheet2" with two column headers "Year" and "Growth (%)", calculate the year-over-year revenue growth percentage compared to the previous year for 2019 to 2023. Round to 2 decimal places.
- **Material File**: `Annual_Revenue_Growth.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_data`
- **Gold File**: `Annual_Revenue_Growth_gold.xlsx`

#### Task L3-16: Transactions_Sort_Amount

- **ID**: `df0fa9c2-938d-451e-98be-bb16611738b8`
- **Source**: `calc_new`
- **Instruction**: Could you help me sort the records according to the "Amount ($)" column in ascending order?
- **Material File**: `Transactions_Sort_Amount.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_data`
- **Gold File**: `Transactions_Sort_Amount_gold.xlsx`

#### Task L3-17: Online_Orders_Summary

- **ID**: `e2fd8f2b-ee87-422d-a4e5-31db82d367bf`
- **Source**: `calc_new`
- **Instruction**: Create two tables in a new sheet named "Sheet2": the first table has headers "Region" and "Total Revenue ($)" showing total revenue per region (in alphabetical order), and the second table (separated by one blank row) has headers "Category" and "Total Revenue ($)" showing total revenue per category (in alphabetical order).
- **Material File**: `Online_Orders_Summary.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_data`
- **Gold File**: `Online_Orders_Summary_gold.xlsx`

#### Task L3-18: Sales_Log_Sort_Date

- **ID**: `e333e868-6c77-429b-8540-bfab9ff3b2ad`
- **Source**: `calc_new`
- **Instruction**: Sort the data according to the "Date" column in ascending order.
- **Material File**: `Sales_Log_Sort_Date.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_data`
- **Gold File**: `Sales_Log_Sort_Date_gold.xlsx`

#### Task L3-19: Support_Tickets_Count

- **ID**: `ee2233cb-4bb3-44ad-be3e-d719f11718de`
- **Source**: `calc_new`
- **Instruction**: Create a new sheet named "Sheet2" with two column headers "Agent" and "Ticket Count", showing how many tickets each agent has handled. List the agents in alphabetical order.
- **Material File**: `Support_Tickets_Count.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_data`
- **Gold File**: `Support_Tickets_Count_gold.xlsx`

#### Task L3-20: Region_SalesVsTarget_Chart

- **ID**: `f7c9725b-9f02-4131-a007-68de65161a3c`
- **Source**: `calc_new`
- **Instruction**: Create a clustered column chart showing the "Sales ($)" and "Target ($)" data for each region in a new sheet named "Sheet2". Set the chart title as "Sales vs Target".
- **Material File**: `Region_SalesVsTarget_Chart.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `chart`
- **Gold File**: `Region_SalesVsTarget_Chart_gold.xlsx`

#### Task L3-21: Staff_Records_Reorder

- **ID**: `fb0f694e-fc10-46f9-9fcd-169630844996`
- **Source**: `calc_new`
- **Instruction**: Reorder the columns to be "ID", "Name", "Department", "Join Date", "Salary". Finish the work and don't touch irrelevant regions, even if they are blank.
- **Material File**: `Staff_Records_Reorder.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_data`
- **Gold File**: `Staff_Records_Reorder_gold.xlsx`

#### Task L3-22: SalesData_L2_01

- **ID**: `136de85a-2050-4137-a831-8bb56ff006f0`
- **Source**: `calc_hard`
- **Instruction**: Open "SalesData_L2_01.xlsx". Add a new column "Profit" (column H) that calculates Revenue minus Cost for each row. Then sort all data rows by the "Revenue" column in descending order (largest first).
- **Material File**: `SalesData_L2_01.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_name`, `sheet_data`
- **Gold File**: `SalesData_L2_01_gold.xlsx`

#### Task L3-23: InvRestock_L3_08

- **ID**: `2364b616-c254-40d2-ac46-29b63af72326`
- **Source**: `calc_hard`
- **Instruction**: Open "InvRestock_L3_08.xlsx" and do ALL: (1) Add "Total Value" (H) = Quantity * Unit Cost (2 dec). (2) Add "Restock Qty" (I) = max(0, Reorder Level * 2 - Quantity). (3) Add "Restock Cost" (J) = Restock Qty * Unit Cost (2 dec). (4) Sort by Category A-Z then Product Name A-Z. (5) Bold header row. (6) Create "SupplierOrders" sheet: Supplier, Items to Restock, Total Restock Cost (2 dec). Only suppliers with items needing restock. Sorted alphabetically. (7) Create "CategoryBreakdown" sheet: Category, Items, Total Qty, Total Value (2 dec), Restock Items, Restock Cost (2 dec). Sorted by Category. (8) Freeze header row on Inventory sheet.
- **Material File**: `InvRestock_L3_08.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_name`, `sheet_data`, `sheet_data`, `sheet_data`, `freeze`, `style`
- **Gold File**: `InvRestock_L3_08_gold.xlsx`

#### Task L3-24: EmpComprehensive_L3_02

- **ID**: `30f6d4dc-f47d-4fb7-8309-8f2d3a2c9cd5`
- **Source**: `calc_hard`
- **Instruction**: Open "EmpComprehensive_L3_02.xlsx" and perform ALL: (1) Add a "Salary Rank" column (H) ranking employees by salary (highest=1). (2) Sort all data by Department (A-Z) then Name (A-Z). (3) Bold the entire header row. (4) Create "DeptSummary" sheet: Department, Headcount, Avg Salary (2 decimals), Avg Performance (2 decimals), Total Salary. Sorted by department. (5) Freeze the header row on the Employees sheet. (6) Create "TopEarners" sheet: Name, Department, Salary, Performance for the top 5 highest-paid employees.
- **Material File**: `EmpComprehensive_L3_02.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_name`, `sheet_data`, `sheet_data`, `sheet_data`, `freeze`, `style`
- **Gold File**: `EmpComprehensive_L3_02_gold.xlsx`

#### Task L3-25: ProjTimeline_L3_09

- **ID**: `3281db55-73e1-4889-bff4-829581706ec6`
- **Source**: `calc_hard`
- **Instruction**: Open "ProjTimeline_L3_09.xlsx" and do ALL: (1) Add "Remaining Budget" (J), "% Spent" (K) = Spent/Budget*100 (1 dec), "Budget Status" (L): "Critical" if % >= 90, "Warning" if >= 70, "On Track" otherwise. (2) Sort by Budget Status (Critical first, Warning, On Track) then % Spent descending. (3) Bold header row. (4) Create "TeamWorkload" sheet: Team Lead, Projects (count), Total Budget, Total Remaining. Sorted by Team Lead name. (5) Create "BudgetOverview" sheet: Budget Status, Count, Total Budget, Avg % Spent (1 dec). Order: Critical, Warning, On Track. (6) Freeze header row on Projects sheet.
- **Material File**: `ProjTimeline_L3_09.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_name`, `sheet_data`, `sheet_data`, `sheet_data`, `freeze`, `style`
- **Gold File**: `ProjTimeline_L3_09_gold.xlsx`

#### Task L3-26: SalesRegion_L2_06

- **ID**: `35df2269-b1c3-42e8-857d-38ca5f594bb6`
- **Source**: `calc_hard`
- **Instruction**: Open "SalesRegion_L2_06.xlsx". Create a new sheet "Summary" with headers: "Region", "Total Units", "Total Revenue", "Total Cost", "Total Profit". Aggregate the data from the Sales sheet by Region (alphabetically sorted), calculating the sum of Units, Revenue, and Cost, and computing Profit as Revenue minus Cost.
- **Material File**: `SalesRegion_L2_06.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_name`, `sheet_data`, `sheet_data`
- **Gold File**: `SalesRegion_L2_06_gold.xlsx`

#### Task L3-27: ProjectData_L2_04

- **ID**: `3d7fe243-5501-48e4-a6e6-0ed818568793`
- **Source**: `calc_hard`
- **Instruction**: Open "ProjectData_L2_04.xlsx". Add two new columns: "Remaining" (Budget - Spent) in column J, and "% Spent" (Spent/Budget * 100, rounded to 1 decimal place) in column K. Then sort all data rows by "% Spent" in descending order.
- **Material File**: `ProjectData_L2_04.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_name`, `sheet_data`
- **Gold File**: `ProjectData_L2_04_gold.xlsx`

#### Task L3-28: EmpStats_L2_07

- **ID**: `4f989467-8112-445d-8f1d-d0b905bd6d74`
- **Source**: `calc_hard`
- **Instruction**: Open "EmpStats_L2_07.xlsx". Create a new sheet "Stats" with headers "Metric" and "Value". Calculate these salary statistics from the Employees sheet: Count (number of employees), Average (rounded to 2 decimal places), Min, Max, and Total. List them in separate rows.
- **Material File**: `EmpStats_L2_07.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_name`, `sheet_data`, `sheet_data`
- **Gold File**: `EmpStats_L2_07_gold.xlsx`

#### Task L3-29: InvReorder_L2_08

- **ID**: `53a2611a-d01f-4c82-a5d1-78631c737568`
- **Source**: `calc_hard`
- **Instruction**: Open "InvReorder_L2_08.xlsx". Sort all data rows by Category (A-Z) then by Product Name (A-Z). Create a new sheet "NeedReorder" with headers: SKU, Product Name, Category, Quantity, Reorder Level, Deficit. List only items where Quantity <= Reorder Level. Deficit = Reorder Level - Quantity.
- **Material File**: `InvReorder_L2_08.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_name`, `sheet_data`, `sheet_data`
- **Gold File**: `InvReorder_L2_08_gold.xlsx`

#### Task L3-30: QtrComprehensive_L3_05

- **ID**: `696790a0-8164-4b34-b5b6-223a2495f530`
- **Source**: `calc_hard`
- **Instruction**: Open "QtrComprehensive_L3_05.xlsx" and do ALL: (1) Add columns: "Annual Revenue" (J), "Annual Cost" (K), "Annual Profit" (L) = Revenue - Cost, "Profit Margin %" (M) = Profit/Revenue*100 (1 decimal). (2) Add a "Total" row (row 7) summing all columns (for Margin %, compute from the totals). (3) Sort data rows (not Total) by Annual Profit descending. (4) Bold header row. (5) Create "QoQ_Growth" sheet: Department, Q1-Q2 Growth %, Q2-Q3 Growth %, Q3-Q4 Growth % (all Revenue-based, 1 decimal). Dept order matches sorted data. (6) Freeze header row on Q1-Q4 sheet.
- **Material File**: `QtrComprehensive_L3_05.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_name`, `sheet_data`, `sheet_data`, `freeze`, `style`
- **Gold File**: `QtrComprehensive_L3_05_gold.xlsx`

#### Task L3-31: InvAnalysis_L3_03

- **ID**: `6a92d8ed-3ec6-4540-aa82-bb635d57a79d`
- **Source**: `calc_hard`
- **Instruction**: Open "InvAnalysis_L3_03.xlsx" and do ALL: (1) Add "Total Value" column (H) = Quantity * Unit Cost (rounded to 2 decimals). (2) Add "Stock Status" column (I): "LOW" if Quantity <= Reorder Level, "OK" if Quantity <= 2x Reorder Level, "HIGH" otherwise. (3) Sort by Total Value descending. (4) Bold the header row. (5) Create "CategorySummary" sheet: Category, Item Count, Total Quantity, Total Value, Avg Unit Cost (2 decimals). Sorted by Category. (6) Create "SupplierSummary" sheet: Supplier, Item Count, Total Value (2 decimals). Sorted by Supplier. (7) Freeze the header row on the Inventory sheet.
- **Material File**: `InvAnalysis_L3_03.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_name`, `sheet_data`, `sheet_data`, `sheet_data`, `freeze`, `style`
- **Gold File**: `InvAnalysis_L3_03_gold.xlsx`

#### Task L3-32: QtrFullYear_L3_10

- **ID**: `6e50aca3-551a-4948-83a2-ae8a1c5c4867`
- **Source**: `calc_hard`
- **Instruction**: Open "QtrFullYear_L3_10.xlsx" and do ALL: (1) Add columns: Annual Revenue (J), Annual Cost (K), Annual Profit (L), Margin % (M, 1 dec), Revenue Rank (N, highest=1). (2) Sort data rows by Annual Profit descending. (3) Add "Total" row (row 7) summing all numeric columns. For Margin %, compute from totals. Leave Revenue Rank empty. (4) Bold both header row and Total row. (5) Create "RevenueGrowth" sheet: Department, Q1→Q2 %, Q2→Q3 %, Q3→Q4 %, Full Year Growth %. All percentages 1 decimal. Dept order matches sorted data. (6) Freeze header row on Q1-Q4 sheet.
- **Material File**: `QtrFullYear_L3_10.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_name`, `sheet_data`, `sheet_data`, `freeze`, `style`
- **Gold File**: `QtrFullYear_L3_10_gold.xlsx`

#### Task L3-33: QtrAnnual_L2_10

- **ID**: `7232142e-4f9c-4994-a12a-ab2d8feef1ea`
- **Source**: `calc_hard`
- **Instruction**: Open "QtrAnnual_L2_10.xlsx". Add two columns: "Annual Revenue" (J) summing Q1-Q4 Revenue, and "Annual Cost" (K) summing Q1-Q4 Cost for each department. Make the entire header row bold.
- **Material File**: `QtrAnnual_L2_10.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_name`, `sheet_data`, `style`
- **Gold File**: `QtrAnnual_L2_10_gold.xlsx`

#### Task L3-34: SalesProduct_L3_06

- **ID**: `75911c73-370d-441e-9c04-b36e2d7efcc8`
- **Source**: `calc_hard`
- **Instruction**: Open "SalesProduct_L3_06.xlsx" and do ALL: (1) Add "Profit" (H) = Revenue - Cost and "Margin %" (I) = Profit/Revenue*100 (1 decimal). (2) Bold the header row. (3) Create "ProductSummary" sheet: Product, Total Units, Total Revenue, Total Profit, Avg Price (2 decimals). Sorted by Product name. (4) Create "MonthlyTrend" sheet: Month, Widget A Units, Widget B Units, Total Units. Months Jan-Jun in order. (5) Freeze header row on the Sales sheet.
- **Material File**: `SalesProduct_L3_06.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_name`, `sheet_data`, `sheet_data`, `sheet_data`, `freeze`, `style`
- **Gold File**: `SalesProduct_L3_06_gold.xlsx`

#### Task L3-35: EmpBudget_L3_07

- **ID**: `77ede3e2-4168-4e30-b390-428f1ebd63e7`
- **Source**: `calc_hard`
- **Instruction**: Open "EmpBudget_L3_07.xlsx" and do ALL: (1) Add "Salary Band" (H): "Senior" if Salary >= 100000, "Mid" if >= 75000, "Junior" otherwise. (2) Sort by Performance descending, then Salary descending. (3) Bold header row. (4) Create "BandSummary" sheet: Salary Band, Count, Avg Salary (2 dec), Avg Performance (2 dec). Order: Senior, Mid, Junior. (5) Create "LowPerformers" sheet: Name, Department, Performance, Salary Band for employees with Performance < 3.5. (6) Freeze header row on Employees sheet.
- **Material File**: `EmpBudget_L3_07.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_name`, `sheet_data`, `sheet_data`, `sheet_data`, `freeze`, `style`
- **Gold File**: `EmpBudget_L3_07_gold.xlsx`

#### Task L3-36: ProjAnalysis_L3_04

- **ID**: `86a64145-9680-480a-a603-b8455f7befd7`
- **Source**: `calc_hard`
- **Instruction**: Open "ProjAnalysis_L3_04.xlsx" and do ALL: (1) Add "Remaining" (J) = Budget - Spent. "% Spent" (K) = Spent/Budget*100 (1 decimal). "On Budget" (L) = "Yes" if % Spent <= 100, else "No". (2) Sort by Priority (Critical first, then High, Medium, Low), then by % Spent descending within each priority. (3) Bold the header row. (4) Create "PrioritySummary" sheet: Priority, Count, Total Budget, Total Spent, Avg % Spent (1 decimal). Order: Critical, High, Medium, Low. (5) Create "AtRisk" sheet: Project Name, Team Lead, Priority, % Spent, Remaining for projects with % Spent >= 80. (6) Freeze the header row on the Projects sheet.
- **Material File**: `ProjAnalysis_L3_04.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_name`, `sheet_data`, `sheet_data`, `sheet_data`, `freeze`, `style`
- **Gold File**: `ProjAnalysis_L3_04_gold.xlsx`

#### Task L3-37: Inventory_L2_03

- **ID**: `8bae8f17-fe56-49ef-a561-f9761e9c72a6`
- **Source**: `calc_hard`
- **Instruction**: Open "Inventory_L2_03.xlsx". Add a "Total Value" column (H) that calculates Quantity times Unit Cost. Make the entire header row (row 1) bold. Freeze the first row so headers stay visible when scrolling.
- **Material File**: `Inventory_L2_03.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_name`, `sheet_data`, `freeze`, `style`
- **Gold File**: `Inventory_L2_03_gold.xlsx`

#### Task L3-38: ProjStatus_L2_09

- **ID**: `8ffd2449-cdc1-46a5-8c8d-e909fbe3fc70`
- **Source**: `calc_hard`
- **Instruction**: Open "ProjStatus_L2_09.xlsx". Create a new sheet "StatusSummary" with headers: "Status", "Count", "Total Budget", "Total Spent". Aggregate projects by Status (sorted alphabetically), counting how many projects have each status and summing their Budget and Spent amounts.
- **Material File**: `ProjStatus_L2_09.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_name`, `sheet_data`, `sheet_data`
- **Gold File**: `ProjStatus_L2_09_gold.xlsx`

#### Task L3-39: Quarterly_L2_05

- **ID**: `af1c2993-6d6c-4109-95c0-fbd6ba904ed1`
- **Source**: `calc_hard`
- **Instruction**: Open "Quarterly_L2_05.xlsx". Add a "Total" row (row 7) that sums each column (Q1-Q4 Revenue and Cost) across all departments. Then add a "Profit" row (row 8) that shows Total Revenue minus Total Cost for each quarter (in the Revenue columns; leave Cost columns empty).
- **Material File**: `Quarterly_L2_05.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_name`, `sheet_data`
- **Gold File**: `Quarterly_L2_05_gold.xlsx`

#### Task L3-40: SalesAnalysis_L3_01

- **ID**: `dfb46a6b-3f2d-4e4a-b4ef-20997ea21563`
- **Source**: `calc_hard`
- **Instruction**: Open "SalesAnalysis_L3_01.xlsx" and perform ALL of the following: (1) Add a "Profit" column (H) = Revenue - Cost. (2) Add a "Margin %" column (I) = Profit/Revenue * 100, rounded to 1 decimal. (3) Make the entire header row bold. (4) Sort all data rows by Profit in descending order. (5) Freeze the first row. (6) Create a "MonthSummary" sheet with headers: Month, Total Revenue, Total Cost, Total Profit, Avg Margin %. Aggregate by month (Jan through Jun in order), with average Margin % rounded to 1 decimal.
- **Material File**: `SalesAnalysis_L3_01.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_name`, `sheet_data`, `sheet_data`, `freeze`, `style`
- **Gold File**: `SalesAnalysis_L3_01_gold.xlsx`

#### Task L3-41: EmployeeData_L2_02

- **ID**: `e71a3d3b-bf53-4454-b871-89156eb037d3`
- **Source**: `calc_hard`
- **Instruction**: Open "EmployeeData_L2_02.xlsx". Create a new sheet "HighPerformers" and copy all employees with Performance >= 4.0 (columns ID, Name, Department, Title, Salary, Performance). Also create a sheet "DeptCount" with headers "Department" and "Count" showing the number of employees per department (sorted alphabetically by department).
- **Material File**: `EmployeeData_L2_02.xlsx`
- **Evaluation Function**: `compare_table`
- **Rule Types**: `sheet_name`, `sheet_data`, `sheet_data`, `sheet_data`
- **Gold File**: `EmployeeData_L2_02_gold.xlsx`

#### L3 Task Source Annotations

| Task | Source Type | Specific Source | Annotation Reason |
|------|-----------|-----------------|-------------------|
| L3-1 | Official Help | [Spreadsheet Operations](https://help.libreoffice.org/latest/en-US/text/scalc/guide/main.html) | Fill the Sequence Numbers as "No. #" (e.g. No. 1, No. 2, ...) in the "Seq No." c |
| L3-2 | Official Help | [Spreadsheet Operations](https://help.libreoffice.org/latest/en-US/text/scalc/guide/main.html) | The "Full Name" column contains names in "Last, First" format. Please split them |
| L3-3 | Official Help | [Spreadsheet Operations](https://help.libreoffice.org/latest/en-US/text/scalc/guide/main.html) | Check the names in the "Customer Names with Duplicates" column and put the uniqu |
| L3-4 | Official Help | [Spreadsheet Operations](https://help.libreoffice.org/latest/en-US/text/scalc/guide/main.html) | I want to copy the product names in the "Raw Name" column to the "Clean Name" co |
| L3-5 | Official Help | [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Create a table in a new sheet named "Sheet2" with two column headers "Department |
| L3-6 | Official Help | [Sorting Data](https://help.libreoffice.org/latest/en-US/text/scalc/guide/sorted_list.html) + [Inserting Charts](https://help.libreoffice.org/latest/en-US/text/schart/main0000.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Sort the data by the "Date" column in ascending order and then create a line cha |
| L3-7 | Official Help | [Inserting Charts](https://help.libreoffice.org/latest/en-US/text/schart/main0000.html) + [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Work out the monthly total sales in a new row called "Total" and then create a l |
| L3-8 | Official Help | [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) | Work out the monthly total sales in a new row called "Total" at the bottom of th |
| L3-9 | Official Help | [Saving as CSV](https://help.libreoffice.org/latest/en-US/text/scalc/guide/csv_files.html) | Could you help me to export the current sheet to a CSV file? Export the contents |
| L3-10 | Official Help | [Cell Formatting](https://help.libreoffice.org/latest/en-US/text/scalc/guide/format_value.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Create a new sheet named "Sheet2" and merge cells A1:D1 to write the header "Q1  |
| L3-11 | Official Help | [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) | Calculate the gross margin percentage for each product using the formula (Revenu |
| L3-12 | Official Help | [Cell Formatting](https://help.libreoffice.org/latest/en-US/text/scalc/guide/format_value.html) | Please highlight all the cells in the "Score" column that have a value greater t |
| L3-13 | Official Help | [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) | Fill the missing values in the "Total" column and the "Total" row with the corre |
| L3-14 | Official Help | [Spreadsheet Operations](https://help.libreoffice.org/latest/en-US/text/scalc/guide/main.html) | Copy the numbers in the "Old Code" column to the "Padded Code (8 digits)" column |
| L3-15 | Official Help | [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | In a new sheet named "Sheet2" with two column headers "Year" and "Growth (%)", c |
| L3-16 | Official Help | [Sorting Data](https://help.libreoffice.org/latest/en-US/text/scalc/guide/sorted_list.html) | Could you help me sort the records according to the "Amount ($)" column in ascen |
| L3-17 | Official Help | [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Create two tables in a new sheet named "Sheet2": the first table has headers "Re |
| L3-18 | Official Help | [Sorting Data](https://help.libreoffice.org/latest/en-US/text/scalc/guide/sorted_list.html) | Sort the data according to the "Date" column in ascending order. |
| L3-19 | Official Help | [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Create a new sheet named "Sheet2" with two column headers "Agent" and "Ticket Co |
| L3-20 | Official Help | [Inserting Charts](https://help.libreoffice.org/latest/en-US/text/schart/main0000.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Create a clustered column chart showing the "Sales ($)" and "Target ($)" data fo |
| L3-21 | Official Help | [Spreadsheet Operations](https://help.libreoffice.org/latest/en-US/text/scalc/guide/main.html) | Reorder the columns to be "ID", "Name", "Department", "Join Date", "Salary". Fin |
| L3-22 | Official Help | [Sorting Data](https://help.libreoffice.org/latest/en-US/text/scalc/guide/sorted_list.html) + [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) | Open "SalesData_L2_01.xlsx". Add a new column "Profit" (column H) that calculate |
| L3-23 | Official Help | [Sorting Data](https://help.libreoffice.org/latest/en-US/text/scalc/guide/sorted_list.html) + [Freezing Rows/Columns](https://help.libreoffice.org/latest/en-US/text/scalc/guide/line_fix.html) + [Cell Formatting](https://help.libreoffice.org/latest/en-US/text/scalc/guide/format_value.html) + [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Open "InvRestock_L3_08.xlsx" and do ALL: (1) Add "Total Value" (H) = Quantity *  |
| L3-24 | Official Help | [Sorting Data](https://help.libreoffice.org/latest/en-US/text/scalc/guide/sorted_list.html) + [Freezing Rows/Columns](https://help.libreoffice.org/latest/en-US/text/scalc/guide/line_fix.html) + [Cell Formatting](https://help.libreoffice.org/latest/en-US/text/scalc/guide/format_value.html) + [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Open "EmpComprehensive_L3_02.xlsx" and perform ALL: (1) Add a "Salary Rank" colu |
| L3-25 | Official Help | [Sorting Data](https://help.libreoffice.org/latest/en-US/text/scalc/guide/sorted_list.html) + [Freezing Rows/Columns](https://help.libreoffice.org/latest/en-US/text/scalc/guide/line_fix.html) + [Cell Formatting](https://help.libreoffice.org/latest/en-US/text/scalc/guide/format_value.html) + [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Open "ProjTimeline_L3_09.xlsx" and do ALL: (1) Add "Remaining Budget" (J), "% Sp |
| L3-26 | Official Help | [Sorting Data](https://help.libreoffice.org/latest/en-US/text/scalc/guide/sorted_list.html) + [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Open "SalesRegion_L2_06.xlsx". Create a new sheet "Summary" with headers: "Regio |
| L3-27 | Official Help | [Sorting Data](https://help.libreoffice.org/latest/en-US/text/scalc/guide/sorted_list.html) | Open "ProjectData_L2_04.xlsx". Add two new columns: "Remaining" (Budget - Spent) |
| L3-28 | Official Help | [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Open "EmpStats_L2_07.xlsx". Create a new sheet "Stats" with headers "Metric" and |
| L3-29 | Official Help | [Sorting Data](https://help.libreoffice.org/latest/en-US/text/scalc/guide/sorted_list.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Open "InvReorder_L2_08.xlsx". Sort all data rows by Category (A-Z) then by Produ |
| L3-30 | Official Help | [Sorting Data](https://help.libreoffice.org/latest/en-US/text/scalc/guide/sorted_list.html) + [Freezing Rows/Columns](https://help.libreoffice.org/latest/en-US/text/scalc/guide/line_fix.html) + [Cell Formatting](https://help.libreoffice.org/latest/en-US/text/scalc/guide/format_value.html) + [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Open "QtrComprehensive_L3_05.xlsx" and do ALL: (1) Add columns: "Annual Revenue" |
| L3-31 | Official Help | [Sorting Data](https://help.libreoffice.org/latest/en-US/text/scalc/guide/sorted_list.html) + [Freezing Rows/Columns](https://help.libreoffice.org/latest/en-US/text/scalc/guide/line_fix.html) + [Cell Formatting](https://help.libreoffice.org/latest/en-US/text/scalc/guide/format_value.html) + [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Open "InvAnalysis_L3_03.xlsx" and do ALL: (1) Add "Total Value" column (H) = Qua |
| L3-32 | Official Help | [Sorting Data](https://help.libreoffice.org/latest/en-US/text/scalc/guide/sorted_list.html) + [Freezing Rows/Columns](https://help.libreoffice.org/latest/en-US/text/scalc/guide/line_fix.html) + [Cell Formatting](https://help.libreoffice.org/latest/en-US/text/scalc/guide/format_value.html) + [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Open "QtrFullYear_L3_10.xlsx" and do ALL: (1) Add columns: Annual Revenue (J), A |
| L3-33 | Official Help | [Cell Formatting](https://help.libreoffice.org/latest/en-US/text/scalc/guide/format_value.html) + [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) | Open "QtrAnnual_L2_10.xlsx". Add two columns: "Annual Revenue" (J) summing Q1-Q4 |
| L3-34 | Official Help | [Sorting Data](https://help.libreoffice.org/latest/en-US/text/scalc/guide/sorted_list.html) + [Freezing Rows/Columns](https://help.libreoffice.org/latest/en-US/text/scalc/guide/line_fix.html) + [Cell Formatting](https://help.libreoffice.org/latest/en-US/text/scalc/guide/format_value.html) + [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Open "SalesProduct_L3_06.xlsx" and do ALL: (1) Add "Profit" (H) = Revenue - Cost |
| L3-35 | Official Help | [Sorting Data](https://help.libreoffice.org/latest/en-US/text/scalc/guide/sorted_list.html) + [Freezing Rows/Columns](https://help.libreoffice.org/latest/en-US/text/scalc/guide/line_fix.html) + [Cell Formatting](https://help.libreoffice.org/latest/en-US/text/scalc/guide/format_value.html) + [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Open "EmpBudget_L3_07.xlsx" and do ALL: (1) Add "Salary Band" (H): "Senior" if S |
| L3-36 | Official Help | [Sorting Data](https://help.libreoffice.org/latest/en-US/text/scalc/guide/sorted_list.html) + [Freezing Rows/Columns](https://help.libreoffice.org/latest/en-US/text/scalc/guide/line_fix.html) + [Cell Formatting](https://help.libreoffice.org/latest/en-US/text/scalc/guide/format_value.html) + [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Open "ProjAnalysis_L3_04.xlsx" and do ALL: (1) Add "Remaining" (J) = Budget - Sp |
| L3-37 | Official Help | [Freezing Rows/Columns](https://help.libreoffice.org/latest/en-US/text/scalc/guide/line_fix.html) + [Cell Formatting](https://help.libreoffice.org/latest/en-US/text/scalc/guide/format_value.html) + [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) | Open "Inventory_L2_03.xlsx". Add a "Total Value" column (H) that calculates Quan |
| L3-38 | Official Help | [Sorting Data](https://help.libreoffice.org/latest/en-US/text/scalc/guide/sorted_list.html) + [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Open "ProjStatus_L2_09.xlsx". Create a new sheet "StatusSummary" with headers: " |
| L3-39 | Official Help | [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) | Open "Quarterly_L2_05.xlsx". Add a "Total" row (row 7) that sums each column (Q1 |
| L3-40 | Official Help | [Sorting Data](https://help.libreoffice.org/latest/en-US/text/scalc/guide/sorted_list.html) + [Freezing Rows/Columns](https://help.libreoffice.org/latest/en-US/text/scalc/guide/line_fix.html) + [Cell Formatting](https://help.libreoffice.org/latest/en-US/text/scalc/guide/format_value.html) + [Calculating with Formulas](https://help.libreoffice.org/latest/en-US/text/scalc/guide/formulas.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Open "SalesAnalysis_L3_01.xlsx" and perform ALL of the following: (1) Add a "Pro |
| L3-41 | Official Help | [Sorting Data](https://help.libreoffice.org/latest/en-US/text/scalc/guide/sorted_list.html) + [Managing Sheets](https://help.libreoffice.org/latest/en-US/text/scalc/guide/multitables.html) | Open "EmployeeData_L2_02.xlsx". Create a new sheet "HighPerformers" and copy all |

#### L3 Task Summary Table

| # | Task Name | Material File | Evaluation Function |
|---|-----------|---------------|---------------------|
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

### 3.4 Interactive Tasks (Calc) -- 27 tasks

> Interactive tasks use multi-phase design with `trigger` controlling phase transitions.


#### Scenario Type: `ambiguous_detail` (Ambiguous Detail) -- 4 tasks

> **Source Type**: Real-World Scenario | **Real-World Source**: Unclear financial report details
> **Evidence**: Accountant receives "make a summary" without specifying dimensions and format

##### interactive_calc_005 (L3)

- **Scenario Description**: The user wants a promotion-type breakdown but doesn't specify the target column or output format. The agent asks, then summarizes Revenue by Promotion Type on Sheet2.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `agent_asks`): Help me create a promotion type breakdown
  - Phase 2 (trigger: `agent_done`): On Sheet2, summarize total Revenue by Promotion Type, with columns named 'Promotion Type' and 'Total Revenue', then save

##### interactive_calc_006 (L3)

- **Scenario Description**: The user wants to analyze the invoice data but doesn't specify what metric. The agent asks, then counts occurrences of each Invoice No. on Sheet2.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `agent_asks`): Help me analyze the invoice data
  - Phase 2 (trigger: `agent_done`): On Sheet2, count the occurrences of each Invoice No., with columns named 'Invoice No.' and 'Count', then save

##### interactive_calc_007 (L3)

- **Scenario Description**: The user says to fill in the profit column but doesn't specify the formula. The agent asks, then fills the Gross profit column with revenue minus expenses.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `agent_asks`): Help me fill in the profit column
  - Phase 2 (trigger: `agent_done`): Fill the Gross profit column with a formula (revenue minus all expenses) for every row, then save

##### interactive_calc_008 (L3)

- **Scenario Description**: The user wants to add grade levels but doesn't specify the grading criteria or column name. The agent asks, then adds A/B/C/D grades based on score ranges.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `agent_asks`): Help me add the grades
  - Phase 2 (trigger: `agent_done`): Use an IF formula: 90+ is A, 80-89 is B, 70-79 is C, below 70 is D. Put the results in a 'Grade' column, then save


#### Scenario Type: `ambiguous_scope` (Ambiguous Scope) -- 4 tasks

> **Source Type**: Real-World Scenario | **Real-World Source**: Uncertain data cleaning scope
> **Evidence**: Data engineer receives "clean up this data" without specifying columns and rules

##### interactive_calc_009 (L3)

- **Scenario Description**: The user says to add a title note to a cell but doesn't say which one. The agent asks, then only modifies cell A1.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `agent_asks`): Help me add a title note to the spreadsheet
  - Phase 2 (trigger: `agent_done`): Only change cell A1 to '2025 Summer Promotion Data', leave all other cells unchanged, then save

##### interactive_calc_010 (L2)

- **Scenario Description**: The user says to add a note but doesn't specify the cell. The agent asks, then only modifies cell A1.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `agent_asks`): Help me add a note to the spreadsheet
  - Phase 2 (trigger: `agent_done`): Only change cell A1 to 'Net Income Statement 2025', leave everything else unchanged, then save

##### interactive_calc_011 (L3)

- **Scenario Description**: The user says to back up some data but doesn't specify how many rows. The agent asks, then only copies the first 3 data rows (excluding header) to Sheet2.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `agent_asks`): Help me back up some of the data to a new sheet
  - Phase 2 (trigger: `agent_done`): Only copy the first 3 data rows (excluding the header row) to Sheet2, do not copy the rest, then save

##### interactive_calc_012 (L2)

- **Scenario Description**: The user says to change the spreadsheet title but doesn't say what to change it to. The agent asks, then only changes A1.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `agent_asks`): Help me change the spreadsheet title
  - Phase 2 (trigger: `agent_done`): Only change cell A1 to 'Sales Report 2025', leave all other rows unchanged, then save


#### Scenario Type: `ambiguous_target` (Ambiguous Target) -- 4 tasks

> **Source Type**: Real-World Scenario | **Real-World Source**: Data analyst handling vague requests
> **Evidence**: Analyst receives "help me calculate the total" without specifying columns/range

##### interactive_calc_001 (L3)

- **Scenario Description**: The user wants to calculate a total for the sales spreadsheet but doesn't specify which column or row. The agent asks, then adds a Total row with SUM formulas at the bottom.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `agent_asks`): Help me calculate the total for this data
  - Phase 2 (trigger: `agent_done`): Add a new row at the bottom: write "Total" in the first column, and use SUM formulas for each month column, then save

##### interactive_calc_002 (L3)

- **Scenario Description**: The user wants to copy a column to a new sheet but doesn't specify which one. The agent asks, then copies the Revenue column to Sheet2.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `agent_asks`): Help me copy a column to a new sheet
  - Phase 2 (trigger: `agent_done`): Copy the Revenue column (including the header) to a new Sheet2, starting at A1, then save

##### interactive_calc_003 (L3)

- **Scenario Description**: The user says to calculate profit but doesn't specify the column names or formula. The agent asks, then adds a Profit=Sales-COGS column.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `agent_asks`): Help me add the profit data
  - Phase 2 (trigger: `agent_done`): Add a new Profit column to the right of the existing columns, with the formula Sales - COGS, then save

##### interactive_calc_004 (L2)

- **Scenario Description**: The user says to back up the data but doesn't specify where. The agent asks, then copies all data to Sheet2.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `agent_asks`): Help me back up this data
  - Phase 2 (trigger: `agent_done`): Copy all data from Sheet1 (including headers) to a new Sheet2, then save


#### Scenario Type: `error_correction` (Error Correction) -- 2 tasks

> **Source Type**: Real-World Scenario | **Real-World Source**: Sort/formula error correction
> **Evidence**: User discovers wrong sort direction or missing formula after submission, requests fix

##### interactive_calc_error_correction_001 (L3)

- **Scenario Description**: User asks to sort by a column, but the instruction is ambiguous. After agent sorts by the wrong column, user clarifies the correct one.
- **Phases**: 3
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=5)): Sort the data by the highest numbers
  - Phase 2 (trigger: `agent_done`): No, that's the wrong column! I meant sort by the March column specifically, from highest to lowest. Please undo what you did and redo it correctly.
  - Phase 3 (trigger: `agent_done`): Good, now also add a Total row at the bottom with SUM for each column, and save.

##### interactive_calc_error_correction_002 (L3)

- **Scenario Description**: User asks agent to create a summary in Sheet2, but agent misunderstands and modifies Sheet1. User corrects.
- **Phases**: 3
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=5)): Create a summary of total sales somewhere in the spreadsheet
  - Phase 2 (trigger: `agent_done`): That's not what I wanted. Please undo that. I need the summary on a NEW sheet called 'Summary', not on the existing sheet. Put 'Total Sales' in A1 and
  - Phase 3 (trigger: `agent_done`): Also add 'Total COGS' in A2 and the sum of COGS in B2 on the Summary sheet. Save the file.


#### Scenario Type: `multi_step_workflow` (Multi-step Workflow) -- 2 tasks

> **Source Type**: Real-World Scenario | **Real-World Source**: Complete quarterly report workflow
> **Evidence**: Full pipeline: add calculated columns, sort, create summary sheets, format

##### interactive_calc_workflow_001 (L3)

- **Scenario Description**: Sequential 4-step workflow: sort data, add formulas, create summary sheet, format headers.
- **Phases**: 4
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `agent_done`): First, add a 'Total' column at the end that sums all monthly values for each sales rep.
  - Phase 2 (trigger: `agent_done`): Now sort the entire table by the Total column from highest to lowest.
  - Phase 3 (trigger: `agent_done`): Create a new sheet called 'Summary'. In A1 write 'Top Performer', in B1 write the name of the sales rep with the highest total.
  - Phase 4 (trigger: `agent_done`): Go back to Sheet1, make the header row bold, then save the file.

##### interactive_calc_workflow_002 (L3)

- **Scenario Description**: Sequential 4-step workflow: rename sheet, add computed column, filter and copy, add summary.
- **Phases**: 4
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `agent_done`): Rename the first sheet from 'Sheet1' to 'Income Data'.
  - Phase 2 (trigger: `agent_done`): Add a column called 'Margin' that calculates Revenue minus Expenses for each row.
  - Phase 3 (trigger: `agent_done`): Create a new sheet called 'High Margin'. Copy all rows where Margin is positive to this new sheet.
  - Phase 4 (trigger: `agent_done`): In the 'High Margin' sheet, add a Total row at the bottom summing the Margin column. Save the file.


#### Scenario Type: `progressive_refinement` (Progressive Refinement) -- 4 tasks

> **Source Type**: Real-World Scenario | **Real-World Source**: Phased data reporting
> **Evidence**: Start with basic summary for manager approval, then add sorting/formatting/summary sheets

##### interactive_calc_013 (L3)

- **Scenario Description**: The user first asks the agent to add a Total row, then after confirmation asks to also add an Average row.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me add a Total row at the bottom that sums each month's data
  - Phase 2 (trigger: `agent_done`): The Total row is done. Now add an Average row right below it that calculates the mean for each month column, then save

##### interactive_calc_014 (L3)

- **Scenario Description**: The user first asks to copy Revenue to Sheet2, then asks to add a percentage column.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me copy the Revenue column to Sheet2
  - Phase 2 (trigger: `agent_done`): Sheet2 has data now. Add a 'Percentage' column next to Revenue that calculates each row's share of the total Revenue, then save

##### interactive_calc_015 (L3)

- **Scenario Description**: The user first asks to add a Profit column, then after confirmation asks to add an Average summary row.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me add a Profit column with formula Sales - COGS
  - Phase 2 (trigger: `agent_done`): Profit column is done. Now add a row at the bottom: write 'Average' in the first cell, and calculate the mean for each numeric column, then save

##### interactive_calc_016 (L3)

- **Scenario Description**: The user first asks to create a product summary on Sheet2, then asks to add a ranking column.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me summarize Total Revenue by Product on Sheet2
  - Phase 2 (trigger: `agent_done`): Summary is done. Now add a 'Rank' column on Sheet2 that ranks by Revenue from highest to lowest, then save


#### Scenario Type: `requirement_change` (Requirement Change) -- 5 tasks

> **Source Type**: Real-World Scenario | **Real-World Source**: Changing report requirements
> **Evidence**: Manager first requests profit column, then changes to sorting by margin and adding summary

##### interactive_calc_017 (L3)

- **Scenario Description**: The user first asks to sort by January ascending, then changes their mind and wants February descending instead.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me sort by the January column from smallest to largest
  - Phase 2 (trigger: `agent_done`): Changed my mind. Sort by the February column from largest to smallest instead. Undo the previous sort first, then save

##### interactive_calc_018 (L3)

- **Scenario Description**: The user first asks to put Revenue total on Sheet2, then changes their mind and wants it at the bottom of Sheet1 instead, and to delete Sheet2.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me put the Revenue total on Sheet2
  - Phase 2 (trigger: `agent_done`): Wrong location. Put the total at the bottom of the Revenue column on Sheet1 instead, and delete Sheet2, then save

##### interactive_calc_019 (L3)

- **Scenario Description**: The user first asks to count Invoice No. occurrences on Sheet2, then changes to summing amounts instead.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me count each Invoice No.'s occurrences on Sheet2
  - Phase 2 (trigger: `agent_done`): Don't count occurrences anymore. Instead, sum up the amount for each Invoice No., and rename the column to 'Total Amount', then save

##### interactive_calc_020 (L3)

- **Scenario Description**: The user first asks to sort by Promotion Type, then changes to sorting by Revenue descending.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me sort by the Promotion Type column
  - Phase 2 (trigger: `agent_done`): Don't sort by that column. Sort by the Revenue column from largest to smallest instead. Undo the previous sort first, then save

##### interactive_calc_requirement_change_001 (L3)

- **Scenario Description**: The user changes a requirement mid-task after the agent has already acted on earlier instructions.
- **Phases**: 3
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `agent_done`): Help me spreadsheetFirstcolumn
  - Phase 2 (trigger: `agent_done`): , change , Firstcolumn, Help me Secondcolumn, 's
  - Phase 3 (trigger: `agent_done`): 's , Help me save the file


#### Scenario Type: `task_interruption` (Task Interruption) -- 2 tasks

> **Source Type**: Real-World Scenario | **Real-World Source**: Work interruption with new constraints
> **Evidence**: While creating summary sheet, told to add new columns or adjust formatting

##### interactive_calc_interruption_001 (L3)

- **Scenario Description**: User asks agent to add formulas to a spreadsheet, then interrupts to check system disk space, then asks to continue the spreadsheet work.
- **Phases**: 3
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Add a Total row at the bottom of the spreadsheet with SUM formulas for each month column
  - Phase 2 (trigger: `agent_done`): Wait, before you continue - can you quickly check the disk space on the system? Run 'df -h' in a terminal and tell me how much space is left on the ro
  - Phase 3 (trigger: `agent_done`): OK thanks. Now go back to the spreadsheet and also add an Average row below the Total row, calculating the average for each month column. Save the fil

##### interactive_calc_interruption_002 (L3)

- **Scenario Description**: User asks agent to sort data, then interrupts to create a backup copy of the file, then asks to continue with conditional formatting.
- **Phases**: 3
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Sort the spreadsheet by the Sales column from highest to lowest
  - Phase 2 (trigger: `agent_done`): Hold on - before you do anything else, please save a backup copy of this file as WeeklySales_backup.xlsx on the Desktop
  - Phase 3 (trigger: `agent_done`): Great. Now in the original WeeklySales.xlsx, add a Profit column (Sales minus COGS) and save.

#### Interactive Task Source Mapping

| Scenario Type | Count | Real-World Source | Evidence | Trigger Combo |
|--------------|-------|-------------------|----------|---------------|
| `ambiguous_detail` (Ambiguous Detail) | 4 | Unclear financial report details | Accountant receives "make a summary" without specifying dime | agent_asks + agent_done |
| `ambiguous_scope` (Ambiguous Scope) | 4 | Uncertain data cleaning scope | Data engineer receives "clean up this data" without specifyi | agent_asks + agent_done |
| `ambiguous_target` (Ambiguous Target) | 4 | Data analyst handling vague requests | Analyst receives "help me calculate the total" without speci | agent_asks + agent_done |
| `error_correction` (Error Correction) | 2 | Sort/formula error correction | User discovers wrong sort direction or missing formula after | agent_done + step_count |
| `multi_step_workflow` (Multi-step Workflow) | 2 | Complete quarterly report workflow | Full pipeline: add calculated columns, sort, create summary  | agent_done |
| `progressive_refinement` (Progressive Refinement) | 4 | Phased data reporting | Start with basic summary for manager approval, then add sort | agent_done + step_count |
| `requirement_change` (Requirement Change) | 5 | Changing report requirements | Manager first requests profit column, then changes to sortin | agent_done + step_count |
| `task_interruption` (Task Interruption) | 2 | Work interruption with new constraints | While creating summary sheet, told to add new columns or adj | agent_done + step_count |

#### Interactive Trigger Type Distribution

| Trigger Type | Count | Description |
|-------------|-------|-------------|
| `agent_done` | 39 | Automatically enters next phase when previous phase completes |
| `agent_asks` | 12 | Triggered when agent proactively asks user for clarification |
| `step_count` | 12 | Injects new instructions after reaching specified step count |

#### Interactive Task Source Mapping

| Scenario Type | Real-World Source | Evidence Package | Task JSON `source` |
|--------------|-------------------|------------------|--------------------|
| `ambiguous_target` | Vague spreadsheet edit request | ① Original request ② Clarification ③ Execution | `calc_interactive;source_type=spreadsheet_edit;evidence=ambiguous_target` |
| `progressive_refinement` | Staged data analysis (raw data→formulas→charts) | ① Phase confirmation ② Refinement ③ Final | `calc_interactive;source_type=data_analysis;evidence=staged_refinement` |
| `requirement_change` | Mid-task spreadsheet requirement change | ① Initial ② Change order ③ Diff record | `calc_interactive;source_type=change;evidence=requirement_change` |
| `error_correction` | Data/formula error correction | ① Error description ② Correction ③ Verification | `calc_interactive;source_type=data_fix;evidence=error_correction` |

#### Source Evidence Fields

- **source_type**: `spreadsheet_edit` / `data_analysis` / `change` / `data_fix` / `chart_creation` / `validation`
- **source_ref**: Source identifier (anonymized URL, ticket ID, interview record ID)
- **captured_at**: Evidence capture date (`YYYY-MM-DD`)
- **anonymized_excerpt**: Anonymized original text excerpt (1-3 sentences)
- **mapping_note**: How the original requirement maps to `phases` and `trigger`
- **reviewers**: Dual-review and adjudication record (`reviewer_a/reviewer_b/adjudicator`)

---

## 4. Evaluation Function Summary

| # | Function | Category | Usage Count |
|---|----------|----------|-------------|
| 1 | `compare_table` | Static Tasks | 49 |
| 2 | `compare_csv` | Static Tasks | 1 |
| 3 | `check_include_exclude` | Interactive Tasks | 27 |

**Total**: Covering 50 static tasks + 27 interactive tasks = **77** tasks.

---

## 5. Material Description

### Technical Specifications

| Property | Value |
|----------|-------|
| File Format | `.xlsx` (Office Open XML Spreadsheet) |
| Total Static Files | 50 initial files + 50 gold files (including 1 `.csv` gold) |
| Language | All column names and data in English |
| Typical Data Size | 5-30 rows × 5-12 columns |

### Data Domain Distribution

| Domain | ~Tasks | Examples |
|--------|--------|---------|
| Sales Data | ~15 | SalesData, SalesRegion, SalesProduct, Monthly_Sales |
| Employee Info | ~10 | EmployeeData, EmpComprehensive, EmpBudget |
| Inventory | ~6 | Inventory, InvRestock, InvReorder, InvAnalysis |
| Project Mgmt | ~8 | ProjectData, ProjTimeline, ProjAnalysis, ProjStatus |
| Financial | ~6 | Financial_Data, Annual_Revenue, Quarterly |
| Other | ~5 | Customer_Deduplicate, Product_Name_Clean, Loan_Due_Date |

---

## 6. Task JSON Templates

### Single-Rule Evaluation (most L1 tasks)

```json
{
  "id": "<uuid4>",
  "snapshot": "libreoffice_calc",
  "instruction": "<operation instruction>",
  "config": [
    {"type": "upload_file", "parameters": {"files": [{"local_path": "cache/<id>/<file>.xlsx", "path": "/home/user/<file>.xlsx"}]}},
    {"type": "open", "parameters": {"path": "/home/user/<file>.xlsx"}}
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

### Multi-Rule Evaluation (most L2/L3 tasks)

```json
{
  "evaluator": {
    "func": "compare_table",
    "options": {"rules": [
      {"type": "sheet_name"},
      {"type": "sheet_data", "sheet_idx0": 0, "sheet_idx1": 0},
      {"type": "sheet_data", "sheet_idx0": 1, "sheet_idx1": 1},
      {"type": "freeze", "sheet_idx0": 0, "sheet_idx1": 0},
      {"type": "style", "sheet_idx0": 0, "sheet_idx1": 0, "props": ["font_bold"]}
    ]}
  }
}
```

---

## 7. Docker Image Requirements

- **LibreOffice** (7.x+ recommended)
- **X11 display environment**
- **Python 3 + openpyxl + PyAutoGUI**

---

## 8. Difficulty Distribution Summary

| Level | Count | Instruction Length | Operation Steps | Description | Examples |
|-------|-------|-------------------|----------------|-------------|---------|
| L1 | 7 | 64-119 chars | 1-2 steps | Single-step atomic ops | Sort, freeze row, copy column, calculate total row |
| L2 | 13 | 138-318 chars | 2-4 steps | Multi-step compound ops | Add formula column + reorder, VLOOKUP fill, conditional highlight, data validation |
| L3 | 10 | 444-638 chars | 5-8 steps (numbered sub-steps) | Complex workflows | Multi-sheet + sort + formula + style + freeze full combo, 8-step analysis report |
| **Total** | **30** | | | | |

### Verifiability Guarantee

1. **`.xlsx` Structured Comparison**: Uses `openpyxl` for cell-by-cell, sheet-by-sheet comparison. No screenshot or OCR dependency.
2. **CSV Text Comparison**: Character-level line-by-line comparison with zero tolerance.
3. **Multi-Dimension Rule Combination**: L2/L3 tasks verify data, styles, freeze panes, and sheet names simultaneously.

> Difficulty tags based on kimi-k2.5 model execution under max_steps=50 (static) / max_steps=80 (interactive).

---

## 9. Common Pitfalls

### LibreOffice Save Dialog
- `.xlsx` files trigger a "Keep Current Format?" dialog on `Ctrl+S`. Must press `Enter` after 1.5s delay.

### openpyxl Comparison Notes
- **Date formats**: LibreOffice may store dates differently from Excel.
- **Formula vs Value**: Use `data_only=True` to read cached values.
- **Empty cells**: LibreOffice may write `""` instead of `None`.

### Gold File Management
- Gold files must exist in both `OSWorld/cache/<task_id>/` and `desktopworld/cache/<task_id>/`.
