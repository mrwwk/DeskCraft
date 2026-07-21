import json
import logging

logger = logging.getLogger("desktopenv.metric.handoff")


def check_handoff_workspace(result, rules, **options):
    """检查工作区是否已被整理为适合交接的状态。

    不依赖特定文件名或精确内容，而是检查工作区中是否存在足够多的
    文档文件（.txt/.md），且内容总量达到合理阈值，以此判断 Agent
    是否完成了有意义的交接整理工作。

    Args:
        result: vm_command_line 输出的 JSON 字符串，包含 file_count 和 total_chars
        rules: expected getter 传入的规则字典，包含 min_files 和 min_total_chars 阈值
        **options: 额外选项（未使用，保留兼容性）

    Returns:
        float: 1.0 表示工作区已整理好，0.0 表示未完成整理
    """
    if result is None:
        logger.warning("Result is None, returning 0.0")
        return 0.0

    # 解析 vm_command_line 输出的 JSON
    try:
        if isinstance(result, str):
            data = json.loads(result.strip())
        else:
            data = result
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        logger.warning(f"Failed to parse result JSON: {e}")
        return 0.0

    min_files = rules.get("min_files", 2)
    min_total_chars = rules.get("min_total_chars", 200)

    file_count = data.get("file_count", 0)
    total_chars = data.get("total_chars", 0)

    logger.info(
        f"Handoff workspace check: {file_count} files, "
        f"{total_chars} chars (need >= {min_files} files, "
        f">= {min_total_chars} chars)"
    )

    if file_count >= min_files and total_chars >= min_total_chars:
        return 1.0

    return 0.0
