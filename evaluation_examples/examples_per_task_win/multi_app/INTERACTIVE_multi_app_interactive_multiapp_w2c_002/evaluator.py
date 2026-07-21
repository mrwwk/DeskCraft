"""
Evaluator for interactive_multiapp_w2c_002:
Check that project_register.xlsx contains all five required fields in row 2.
"""
import logging
import os

logger = logging.getLogger("desktopenv.metric.project_register")


def check_project_register(result_path, expected=None, **options):
    """
    Verify that the project_register.xlsx file contains correct data in row 2.

    Args:
        result_path: Local path to the xlsx file (pulled from VM via vm_file getter).
        expected: Dict with "cells" key containing {cell_ref: expected_value} mapping.
        **options: Additional options (unused).

    Returns:
        float: 1.0 if all cells match, 0.0 otherwise.
    """
    if result_path is None:
        logger.warning("result_path is None, returning 0.0")
        return 0.0

    if not os.path.exists(result_path):
        logger.warning(f"File not found: {result_path}, returning 0.0")
        return 0.0

    # Default expected cell values (used when expected is None or empty)
    default_cells = {
        "A2": "PRJ-2025-008",
        "B2": "Smart Customer Service System Upgrade",
        "C2": "Lin Zhiwei",
        "D2": "85",
        "E2": "High",
    }

    # Merge with provided expected values
    cells = dict(default_cells)
    if expected and isinstance(expected, dict):
        ext_cells = expected.get("cells", {})
        if ext_cells:
            cells.update(ext_cells)

    try:
        import openpyxl
        wb = openpyxl.load_workbook(result_path)
        ws = wb.active

        for cell_ref, expected_val in cells.items():
            actual_val = ws[cell_ref].value
            # Normalize to string for robust comparison (handles int/float/str)
            actual_str = str(actual_val).strip() if actual_val is not None else ""
            expected_str = str(expected_val).strip()
            if actual_str != expected_str:
                logger.warning(
                    "Cell %s mismatch: expected=%r, actual=%r",
                    cell_ref, expected_str, actual_str,
                )
                return 0.0

        return 1.0
    except ImportError:
        logger.error("openpyxl is not installed, returning 0.0")
        return 0.0
    except Exception as e:
        logger.error("Error reading/checking %s: %s", result_path, e)
        return 0.0
