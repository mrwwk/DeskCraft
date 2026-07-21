"""
Kdenlive Evaluator Functions for L1 snapshot + project save task.

Evaluator functions:
- check_kdenlive_snapshot_exists: Verify snapshot PNG file(s) exist in Videos/
- check_kdenlive_file_exists: Verify project .kdenlive file exists and is valid XML
"""

import os
import re
import logging
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


# ============================================================================
# Evaluator Function: Check Snapshot Exists
# ============================================================================

def check_kdenlive_snapshot_exists(command_output, rule):
    """
    Evaluator for Kdenlive task: Verify snapshot PNG file(s) exist.

    This function receives the output of a shell command (e.g., `ls *.png | wc -l`)
    as a string and checks that the count meets the minimum requirement.

    Args:
        command_output: String output from the vm_command_line command
                        (e.g., "3\n" meaning 3 PNG files found)
        rule: Dictionary with validation rules.
              Expected format: {"min_count": 1}

    Returns:
        float: 1.0 if the file count meets the minimum, 0.0 otherwise
    """
    try:
        min_count = rule.get("min_count", 1)

        if command_output is None:
            logger.error("command_output is None")
            return 0.0

        # Parse the count from command output
        count_str = str(command_output).strip()
        try:
            count = int(count_str)
        except ValueError:
            # Try to extract first number from output
            numbers = re.findall(r'\d+', count_str)
            if numbers:
                count = int(numbers[0])
            else:
                logger.error(f"Cannot parse count from output: '{count_str}'")
                return 0.0

        logger.info(f"Snapshot count: {count}, required min: {min_count}")

        if count >= min_count:
            logger.info(f"Snapshot check passed: {count} >= {min_count}")
            return 1.0
        else:
            logger.warning(f"Snapshot check failed: {count} < {min_count}")
            return 0.0

    except Exception as e:
        logger.error(f"check_kdenlive_snapshot_exists error: {e}")
        return 0.0


# ============================================================================
# Evaluator Function: Check Project File Exists
# ============================================================================

def check_kdenlive_file_exists(project_file_path, rule):
    """
    Evaluator for Kdenlive task: Verify a project file exists and is valid.

    Checks that the file was retrieved (not None), exists on disk,
    and optionally validates it is a well-formed XML file.

    Args:
        project_file_path: Path to the .kdenlive project file (from vm_file getter)
        rule: Dictionary with validation rules.
              Optional keys:
              - "valid_xml": bool, if True also validate XML structure (default True)

    Returns:
        float: 1.0 if file exists (and is valid XML if required), 0.0 otherwise
    """
    try:
        if project_file_path is None or not os.path.exists(project_file_path):
            logger.error(f"Project file not found: {project_file_path}")
            return 0.0

        file_size = os.path.getsize(project_file_path)
        if file_size == 0:
            logger.error(f"Project file is empty: {project_file_path}")
            return 0.0

        logger.info(f"Project file exists, size: {file_size} bytes")

        check_xml = rule.get("valid_xml", True)
        if check_xml:
            try:
                tree = ET.parse(project_file_path)
                root = tree.getroot()
                if root is None:
                    logger.error("XML has no root element")
                    return 0.0
                logger.info(f"Valid XML with root element: <{root.tag}>")
            except ET.ParseError as e:
                logger.error(f"Invalid XML: {e}")
                return 0.0

        logger.info("check_kdenlive_file_exists: File exists and is valid")
        return 1.0

    except Exception as e:
        logger.error(f"check_kdenlive_file_exists error: {e}")
        return 0.0
