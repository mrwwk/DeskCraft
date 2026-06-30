import logging

logger = logging.getLogger("desktopenv.metric.chrome_debug_ready")


def check_chrome_debug_ready(result, rules, **options):
    """
    检查 Chrome 是否已处于可调试本地扩展的就绪状态。

    核心验证条件：当前活跃标签页 URL 为 chrome://extensions。
    这等价于确认 agent 已成功导航到扩展管理页面，
    该页面是加载未打包扩展、管理扩展和启用 Developer mode 的唯一入口。

    Args:
        result: active_url_from_accessTree getter 返回的 URL 字符串（或含 url 字段的 dict）
        rules:  dict，含 "url" 键指向期望的 URL "chrome://extensions"
        **options: 额外参数（本 metric 不使用）

    Returns:
        float: 1.0 表示 URL 匹配 chrome://extensions，0.0 表示不匹配或结果为空
    """
    if result is None:
        logger.warning("check_chrome_debug_ready: result is None, returning 0.0")
        return 0.

    # 从 getter 返回值中提取 URL 字符串
    if isinstance(result, str):
        url = result.strip()
    elif isinstance(result, dict):
        url = str(result.get("url", result.get("name", ""))).strip()
    else:
        url = str(result).strip()

    if not url:
        logger.warning("check_chrome_debug_ready: empty URL extracted from result, returning 0.0")
        return 0.

    # 从 rules 中提取期望 URL
    if isinstance(rules, dict):
        expected = rules.get("url", rules.get("expected", ""))
    else:
        expected = str(rules) if rules else ""

    expected = str(expected).strip()
    if not expected:
        logger.warning("check_chrome_debug_ready: empty expected URL, returning 0.0")
        return 0.

    # 标准化：去除末尾斜杠以便比较
    url_norm = url.rstrip('/')
    expected_norm = expected.rstrip('/')

    # 精确匹配或期望 URL 作为前缀（如 chrome://extensions 匹配 chrome://extensions/?id=...）
    if url_norm == expected_norm:
        logger.info("check_chrome_debug_ready: URL '%s' exact match with expected '%s', returning 1.0", url, expected)
        return 1.

    if url_norm.startswith(expected_norm + '/'):
        logger.info("check_chrome_debug_ready: URL '%s' starts with expected '%s/', returning 1.0", url, expected)
        return 1.

    logger.info("check_chrome_debug_ready: URL '%s' does not match expected '%s', returning 0.0", url, expected)
    return 0.
