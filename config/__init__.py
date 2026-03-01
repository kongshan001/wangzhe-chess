"""
王者之奕 - 配置模块
===================

提供配置管理和日志配置。

使用示例：
    from config.settings import settings
    from config.logging import setup_logging, get_logger

    # 初始化日志
    setup_logging()

    # 获取配置
    db_url = settings.database.url

    # 获取日志器
    logger = get_logger(__name__)
    logger.info("应用启动")
"""

from config.logging import (
    LogContext,
    clear_request_id,
    get_logger,
    get_request_id,
    log_performance,
    set_request_id,
    setup_logging,
)
from config.settings import (
    DatabaseSettings,
    GameSettings,
    LogSettings,
    RedisSettings,
    SecuritySettings,
    ServerSettings,
    Settings,
    get_settings,
    settings,
)

__all__ = [
    # 配置
    "settings",
    "get_settings",
    "Settings",
    "DatabaseSettings",
    "RedisSettings",
    "ServerSettings",
    "SecuritySettings",
    "GameSettings",
    "LogSettings",
    # 日志
    "setup_logging",
    "get_logger",
    "log_performance",
    "set_request_id",
    "clear_request_id",
    "get_request_id",
    "LogContext",
]
