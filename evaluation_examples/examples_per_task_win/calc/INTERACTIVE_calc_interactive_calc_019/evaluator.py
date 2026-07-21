import logging
import os

logger = logging.getLogger("desktopenv.metric.calc_invoice_sum")


def check_calc_invoice_sum(result_path, expected=None, **options):
    """
    Verify that Sheet2 in Invoices.xlsx:
    1. Exists in the workbook
    2. Has a 'Total Amount' column (case-insensitive)
    3. Contains all expected unique invoice numbers
    4. Each invoice's Total Amount equals the sum of its Sales from Sheet1

    Args:
        result_path: Local path to Invoices.xlsx (from vm_file getter)
        expected: Dict with 'expected_invoice_numbers' list (from rule getter)
        **options: 'tolerance' for float comparison (default 0.01)
    """
    if result_path is None or not os.path.exists(result_path):
        logger.warning(f"Result file not found: {result_path}")
        return 0.0

    try:
        import pandas as pd
    except ImportError:
        logger.error("pandas is not available in evaluation environment")
        return 0.0

    # Open the workbook
    try:
        xl = pd.ExcelFile(result_path)
    except Exception as e:
        logger.error(f"Failed to open Excel file {result_path}: {e}")
        return 0.0

    # 1. Sheet2 must exist
    if 'Sheet2' not in xl.sheet_names:
        logger.warning("Sheet2 not found in workbook")
        return 0.0

    # Read both sheets
    try:
        df2 = pd.read_excel(xl, sheet_name='Sheet2')
        df1 = pd.read_excel(xl, sheet_name='Sheet1')
    except Exception as e:
        logger.error(f"Failed to read sheets: {e}")
        return 0.0

    # 2. Find 'Total Amount' column (case-insensitive)
    cols_lower = [str(c).strip().lower() for c in df2.columns]
    if 'total amount' not in cols_lower:
        logger.warning(f"'Total Amount' column not found in Sheet2. Columns: {list(df2.columns)}")
        return 0.0

    # Identify actual column names
    ta_col = None
    inv_col = None
    for c in df2.columns:
        cl = str(c).strip().lower()
        if 'total amount' in cl:
            ta_col = c
        if 'invoice' in cl and 'no' in cl:
            inv_col = c

    if ta_col is None:
        logger.warning("Cannot identify 'Total Amount' column in Sheet2")
        return 0.0
    if inv_col is None:
        logger.warning("Cannot identify 'Invoice No.' column in Sheet2")
        return 0.0

    # 3. Check invoice numbers match expected set
    expected_inv_list = None
    if expected and isinstance(expected, dict):
        expected_inv_list = expected.get('expected_invoice_numbers')
    if expected_inv_list is None:
        expected_inv_list = options.get('expected_invoice_numbers', [])

    if expected_inv_list:
        actual_inv = set()
        for v in df2[inv_col].dropna():
            try:
                actual_inv.add(str(int(v)))
            except (ValueError, TypeError):
                actual_inv.add(str(v).strip())

        expected_set = set(str(v).strip() for v in expected_inv_list)

        if actual_inv != expected_set:
            logger.warning(
                f"Invoice number mismatch: expected {sorted(expected_set)}, got {sorted(actual_inv)}"
            )
            return 0.0

    # 4. Compute expected sums from Sheet1 and compare with Sheet2
    # Sheet1: Invoice No. column + Sales column
    inv_col_s1 = None
    sales_col = None
    for c in df1.columns:
        cl = str(c).strip().lower()
        if 'invoice' in cl and 'no' in cl:
            inv_col_s1 = c
        if cl == 'sales':
            sales_col = c

    if inv_col_s1 is None:
        logger.warning("Cannot find 'Invoice No.' column in Sheet1")
        return 0.0
    if sales_col is None:
        logger.warning("Cannot find 'Sales' column in Sheet1")
        return 0.0

    # Build expected sums from Sheet1: {invoice_number: total_sales}
    expected_sums = {}
    for inv_val, grp in df1.groupby(inv_col_s1):
        try:
            inv_key = str(int(inv_val))
        except (ValueError, TypeError):
            inv_key = str(inv_val).strip()
        expected_sums[inv_key] = float(grp[sales_col].sum())

    tolerance = float(options.get('tolerance', 1.0))

    for _, row in df2.iterrows():
        inv_val = row[inv_col]
        if pd.isna(inv_val):
            continue

        try:
            inv_key = str(int(inv_val))
        except (ValueError, TypeError):
            inv_key = str(inv_val).strip()

        ta_val = row[ta_col]
        if pd.isna(ta_val):
            logger.warning(f"Missing Total Amount for invoice {inv_key}")
            return 0.0

        expected_val = expected_sums.get(inv_key)
        if expected_val is None:
            logger.warning(f"Invoice {inv_key} not found in Sheet1 data")
            return 0.0

        if abs(float(ta_val) - expected_val) > tolerance:
            logger.warning(
                f"Sum mismatch for invoice {inv_key}: "
                f"expected {expected_val}, got {float(ta_val)}"
            )
            return 0.0

    return 1.0
