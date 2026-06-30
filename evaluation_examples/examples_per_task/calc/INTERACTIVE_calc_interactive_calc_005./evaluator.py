"""Evaluator for interactive_calc_005: check pivot table promotion type breakdown.

Checks that the saved Excel file contains a pivot table sheet with
promotion type breakdown (Promotion rows + Sum - Revenue data column).
Flexible about sheet name and exact column naming conventions.
"""
import logging
import pandas as pd

logger = logging.getLogger("desktopenv.metric.interactive_calc_005")


def check_pivot_table(result_path: str, **options) -> float:
    """Check that the Excel file contains a pivot table with promotion-type revenue summary.

    Iterates over all sheets and looks for a sheet that has both:
    - A column whose name contains 'promotion' (case-insensitive)
    - A column whose name contains 'sum - revenue' (case-insensitive)

    This matches LibreOffice Calc's default pivot table column naming
    ('Sum - Revenue') and tolerates agent-renamed sheet names like
    'Promotion Type Breakdown' instead of requiring 'Sheet2'.

    Args:
        result_path: Local path to the Excel file (provided by vm_file getter).
        **options: Additional keyword options (unused, reserved for framework).

    Returns:
        1.0 if a pivot table sheet with promotion breakdown is found, 0.0 otherwise.
    """
    if result_path is None:
        logger.warning("result_path is None, returning 0.0")
        return 0.0

    try:
        xl = pd.ExcelFile(result_path)
    except Exception as e:
        logger.error(f"Failed to open Excel file {result_path}: {e}")
        return 0.0

    for sheet in xl.sheet_names:
        try:
            df = pd.read_excel(result_path, sheet_name=sheet)
            cols = [str(c).strip().lower() for c in df.columns]
            has_promotion = any('promotion' in c for c in cols)
            has_sum_revenue = any('sum - revenue' in c for c in cols)
            if has_promotion and has_sum_revenue:
                logger.info(f"Found pivot table in sheet '{sheet}': columns={list(df.columns)}")
                return 1.0
        except Exception:
            # Skip sheets that can't be read (e.g., empty or malformed)
            continue

    logger.warning(f"No pivot table with promotion breakdown found in {result_path}")
    return 0.0
