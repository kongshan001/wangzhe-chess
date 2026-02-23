"""
王者之奕 - 数据库连接管理

本模块提供 SQLAlchemy 异步数据库连接管理：
- 异步引擎配置
- 连接池管理
- 会话工厂
- 生命周期管理

使用方式:
    from src.server.db.database import get_session, init_db, close_db

    # 初始化数据库
    await init_db("mysql+aiomysql://user:pass@localhost/wangzhe")

    # 使用会话
    async with get_session() as session:
        # 执行数据库操作
        pass

    # 关闭数据库连接
    await close_db()
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

logger = logging.getLogger(__name__)

# 全局引擎实例
_engine: AsyncEngine | None = None

# 全局会话工厂
_session_factory: async_sessionmaker[AsyncSession] | None = None


class DatabaseConfig:
    """
    数据库配置

    Attributes:
        database_url: 数据库连接URL
        pool_size: 连接池大小
        max_overflow: 最大溢出连接数
        pool_timeout: 获取连接超时时间（秒）
        pool_recycle: 连接回收时间（秒）
        echo: 是否打印SQL语句
        echo_pool: 是否打印连接池日志
    """

    def __init__(
        self,
        database_url: str = "mysql+aiomysql://root:password@localhost/wangzhe",
        pool_size: int = 10,
        max_overflow: int = 20,
        pool_timeout: float = 30.0,
        pool_recycle: int = 3600,
        echo: bool = False,
        echo_pool: bool = False,
    ) -> None:
        """
        初始化数据库配置

        Args:
            database_url: 数据库连接URL
            pool_size: 连接池大小（默认10）
            max_overflow: 最大溢出连接数（默认20）
            pool_timeout: 获取连接超时时间（默认30秒）
            pool_recycle: 连接回收时间（默认1小时）
            echo: 是否打印SQL语句（调试用）
            echo_pool: 是否打印连接池日志
        """
        self.database_url = database_url
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        self.echo = echo
        self.echo_pool = echo_pool


async def init_db(
    config: DatabaseConfig | None = None,
    database_url: str | None = None,
) -> AsyncEngine:
    """
    初始化数据库连接

    创建异步引擎和会话工厂。支持两种调用方式：
    1. 传入 DatabaseConfig 对象
    2. 直接传入 database_url 字符串

    Args:
        config: 数据库配置对象
        database_url: 数据库连接URL（简化调用）

    Returns:
        初始化后的异步引擎

    Example:
        # 方式1：使用配置对象
        config = DatabaseConfig(
            database_url="mysql+aiomysql://user:pass@localhost/db",
            pool_size=20,
        )
        await init_db(config)

        # 方式2：简化调用
        await init_db(database_url="mysql+aiomysql://user:pass@localhost/db")
    """
    global _engine, _session_factory

    # 参数处理
    if config is None:
        config = DatabaseConfig(
            database_url=database_url or "mysql+aiomysql://root:password@localhost/wangzhe"
        )
    elif database_url is not None:
        config.database_url = database_url

    # 判断是否使用连接池
    # SQLite 不支持连接池，使用 NullPool
    use_pool = not config.database_url.startswith("sqlite")

    # 创建异步引擎
    engine_kwargs = {
        "echo": config.echo,
        "echo_pool": config.echo_pool,
    }

    if use_pool:
        engine_kwargs.update(
            {
                "pool_size": config.pool_size,
                "max_overflow": config.max_overflow,
                "pool_timeout": config.pool_timeout,
                "pool_recycle": config.pool_recycle,
                "pool_pre_ping": True,
            }
        )
    else:
        engine_kwargs["poolclass"] = NullPool

    _engine = create_async_engine(config.database_url, **engine_kwargs)

    # 创建会话工厂
    _session_factory = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,  # 提交后不使对象过期
        autoflush=False,  # 手动控制flush
    )

    logger.info(
        f"数据库连接已初始化: {config.database_url.split('@')[-1] if '@' in config.database_url else config.database_url}"
    )

    return _engine


async def close_db() -> None:
    """
    关闭数据库连接

    清理引擎和会话工厂，释放所有连接池资源。
    应在应用关闭时调用。
    """
    global _engine, _session_factory

    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("数据库连接已关闭")


def get_engine() -> AsyncEngine:
    """
    获取当前数据库引擎

    Returns:
        异步数据库引擎

    Raises:
        RuntimeError: 如果数据库未初始化
    """
    if _engine is None:
        raise RuntimeError("数据库未初始化，请先调用 init_db()")
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    获取会话工厂

    Returns:
        异步会话工厂

    Raises:
        RuntimeError: 如果数据库未初始化
    """
    if _session_factory is None:
        raise RuntimeError("数据库未初始化，请先调用 init_db()")
    return _session_factory


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话上下文管理器

    自动管理会话的生命周期，包括提交和回滚。

    Yields:
        异步数据库会话

    Example:
        async with get_session() as session:
            player = await session.get(Player, 1)
            session.add(new_player)
            # 退出时自动提交
    """
    if _session_factory is None:
        raise RuntimeError("数据库未初始化，请先调用 init_db()")

    session = _session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def get_session_dep() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI 依赖注入用的会话生成器

    与 get_session 类似，但设计为 FastAPI 依赖注入使用。

    Yields:
        异步数据库会话
    """
    async with get_session() as session:
        yield session


async def create_tables() -> None:
    """
    创建所有数据表

    仅用于开发测试，生产环境应使用 Alembic 迁移。
    """
    from ..models.base import Base

    if _engine is None:
        raise RuntimeError("数据库未初始化，请先调用 init_db()")

    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("数据表创建完成")


async def drop_tables() -> None:
    """
    删除所有数据表

    警告：此操作不可逆，仅用于开发测试！
    """
    from ..models.base import Base

    if _engine is None:
        raise RuntimeError("数据库未初始化，请先调用 init_db()")

    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    logger.warning("所有数据表已删除")
