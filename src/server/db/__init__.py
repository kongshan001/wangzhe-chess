"""
王者之奕 - 数据库模块

导出数据库连接管理相关功能。

使用方式:
    from src.server.db import init_db, close_db, get_session
"""

from .database import (
    AsyncEngine,
    AsyncSession,
    DatabaseConfig,
    close_db,
    create_tables,
    drop_tables,
    get_engine,
    get_session,
    get_session_dep,
    get_session_factory,
    init_db,
)

__all__ = [
    # 配置类
    "DatabaseConfig",
    # 类型导出
    "AsyncEngine",
    "AsyncSession",
    # 核心函数
    "init_db",
    "close_db",
    "get_engine",
    "get_session",
    "get_session_factory",
    "get_session_dep",
    # 工具函数
    "create_tables",
    "drop_tables",
]
