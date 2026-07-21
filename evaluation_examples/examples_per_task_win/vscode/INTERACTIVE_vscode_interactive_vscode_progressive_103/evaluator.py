import logging
import os

logger = logging.getLogger("desktopenv.metric.general")


def file_contains(file_path, config):
    """检查文件中是否包含所有期望的文本内容。

    Args:
        file_path: 本地文件路径
        config: dict，包含 "expected" 键，值为需要检查的字符串列表

    Returns:
        float: 1.0 表示文件存在且包含所有期望字符串，0.0 表示缺失
    """
    if not file_path:
        logger.debug("file_contains: file_path is None or empty")
        return 0.
    if not os.path.isfile(file_path):
        logger.debug(f"file_contains: file not found: {file_path}")
        return 0.
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            file_text = f.read()
        for text in config["expected"]:
            if text not in file_text:
                logger.debug(f"file_contains: '{text}' not found in {file_path}")
                return 0.
    except Exception as e:
        logger.debug(f"file_contains: error reading {file_path}: {e}")
        return 0.
    return 1.
