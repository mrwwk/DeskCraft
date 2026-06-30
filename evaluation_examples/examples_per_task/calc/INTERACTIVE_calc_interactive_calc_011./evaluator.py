import logging
import os

logger = logging.getLogger("desktopenv.metric.check_sheet_backup")


def check_sheet_backup(result_path, expected=None, **options):
    """
    Check that WeeklySales.xlsx has Sheet2 with correct columns and data,
    and that Sheet1 original data remains intact.

    Called by the mini-osworld evaluator framework:
      - result_path: local path to the xlsx file (pulled from VM via vm_file getter)
      - expected: dict with expected_columns, expected_sheets, min_data_rows (from rule getter)
      - **options: reserved for future options

    Returns:
        float: 1.0 if all checks pass, 0.0 otherwise
    """
    if result_path is None or not os.path.exists(result_path):
        logger.warning(f"Result file not found or path is None: {result_path}")
        return 0.0

    try:
        import pandas as pd
    except ImportError:
        logger.error("pandas not available for check_sheet_backup")
        return 0.0

    try:
        if expected is None:
            expected = {}

        expected_columns = expected.get("expected_columns", ["Week", "Sales", "COGS"])
        expected_sheets = expected.get("expected_sheets", ["Sheet1", "Sheet2"])
        min_data_rows = expected.get("min_data_rows", 1)

        # Open the Excel file
        xl = pd.ExcelFile(result_path)

        # 1. Check that all expected sheets exist
        for sheet in expected_sheets:
            if sheet not in xl.sheet_names:
                logger.warning(f"Sheet '{sheet}' not found in workbook. Available: {xl.sheet_names}")
                return 0.0

        # 2. Read both sheets
        df1 = pd.read_excel(result_path, sheet_name="Sheet1")
        df2 = pd.read_excel(result_path, sheet_name="Sheet2")

        # 3. Check Sheet2 has the expected columns (3 columns: Week, Sales, COGS)
        if list(df2.columns) != expected_columns:
            logger.warning(
                f"Sheet2 columns mismatch: got {list(df2.columns)}, expected {expected_columns}"
            )
            return 0.0

        # 4. Check Sheet2 has at least the minimum number of data rows
        if len(df2) < min_data_rows:
            logger.warning(f"Sheet2 has {len(df2)} data rows, minimum required: {min_data_rows}")
            return 0.0

        # 5. Check Sheet1 data integrity: expected columns and has data
        if list(df1.columns) != expected_columns:
            logger.warning(
                f"Sheet1 columns mismatch: got {list(df1.columns)}, expected {expected_columns}"
            )
            return 0.0

        if len(df1) < min_data_rows:
            logger.warning(f"Sheet1 has {len(df1)} data rows, minimum required: {min_data_rows}")
            return 0.0

        # 6. Basic data consistency: verify that values in Sheet2 exist in Sheet1
        #    (the backup data should be a subset of the original)
        for col in expected_columns:
            if col in df1.columns and col in df2.columns:
                sheet1_values = set(df1[col].dropna().values)
                sheet2_values = set(df2[col].dropna().values)
                if not sheet2_values.issubset(sheet1_values):
                    extra = sheet2_values - sheet1_values
                    logger.warning(
                        f"Sheet2 column '{col}' contains values not in Sheet1: {extra}"
                    )
                    return 0.0

        return 1.0

    except Exception as e:
        logger.error(f"check_sheet_backup error: {e}")
        return 0.0
