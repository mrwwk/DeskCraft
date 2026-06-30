import logging
import os

logger = logging.getLogger("desktopenv.metric.general")


def check_order_tracker_xlsx(result: str, expected: dict, **options) -> float:
    """
    Check that order_tracker.xlsx row 2 has all required fields filled correctly.

    Reads the xlsx file pulled from the VM via vm_file getter, then compares
    each cell (A2-G2) against the expected values provided via expected getter.

    Args:
        result: Local file path to the xlsx file (from vm_file getter).
        expected: Dict with key 'cells' mapping cell references to expected
                  string values. All values are compared as strings so that
                  LibreOffice Calc's numeric storage (int/float) is handled.
    Returns:
        1.0 if all cells match, 0.0 otherwise.
    """
    if result is None:
        logger.warning("check_order_tracker_xlsx: result path is None")
        return 0.0

    if not os.path.exists(result):
        logger.warning(
            "check_order_tracker_xlsx: result file not found: %s", result
        )
        return 0.0

    try:
        import openpyxl
    except ImportError:
        logger.error(
            "check_order_tracker_xlsx: openpyxl not installed, cannot evaluate"
        )
        return 0.0

    try:
        wb = openpyxl.load_workbook(result, data_only=True)
        ws = wb.active
    except Exception as e:
        logger.error(
            "check_order_tracker_xlsx: failed to open workbook %s: %s", result, e
        )
        return 0.0

    cells = expected.get("cells", {}) if isinstance(expected, dict) else {}
    if not cells:
        logger.warning("check_order_tracker_xlsx: no cell expectations provided")
        return 0.0

    for cell_ref, expected_value in cells.items():
        try:
            actual_value = ws[cell_ref].value
        except Exception as e:
            logger.warning(
                "check_order_tracker_xlsx: cannot read cell %s: %s", cell_ref, e
            )
            return 0.0

        # Compare as strings to handle mixed int/float/str from LibreOffice Calc
        if str(actual_value) != str(expected_value):
            logger.warning(
                "check_order_tracker_xlsx: cell %s mismatch: expected=%r, actual=%r",
                cell_ref,
                expected_value,
                actual_value,
            )
            return 0.0

    logger.info("check_order_tracker_xlsx: all %d cells match", len(cells))
    return 1.0
