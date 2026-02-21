"""
王者之奕 - Alembic 环境配置

本模块配置 Alembic 迁移环境，支持：
- 异步数据库迁移
- 自动生成迁移脚本
- 在线/离线迁移模式

使用方式:
    # 生成迁移脚本
    alembic revision --autogenerate -m "添加新表"
    
    # 执行迁移
    alembic upgrade head
"""

from __future__ import annotations

import asyncio
import logging
import os
from logging.config import fileConfig
from typing import Any

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy.sql import text

# Alembic Config 对象
config = context.config

# 设置日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 导入所有模型以支持自动生成
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入 Base 和所有模型
from src.server.models import Base
from src.server.models import (
    # 玩家相关
    PlayerDB,
    PlayerRankDB,
    PlayerStatsDB,
    PlayerLoginLogDB,
    PlayerInventoryDB,
    # 对局相关
    MatchRecordDB,
    MatchPlayerResultDB,
    # 配置相关
    HeroConfigDB,
    HeroVersionDB,
    SynergyConfigDB,
    GameConfigDB,
    SeasonConfigDB,
)

# 设置 MetaData
target_metadata = Base.metadata

# 日志
logger = logging.getLogger(__name__)


def get_url() -> str:
    """
    获取数据库连接 URL
    
    优先级：
    1. 环境变量 DATABASE_URL
    2. alembic.ini 中的 sqlalchemy.url
    3. 默认值
    
    Returns:
        数据库连接 URL
    """
    # 优先从环境变量获取
    url = os.getenv("DATABASE_URL")
    if url:
        # 如果是同步 URL，转换为异步 URL
        if url.startswith("mysql://"):
            url = url.replace("mysql://", "mysql+aiomysql://")
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://")
        return url
    
    # 从配置文件获取
    url = config.get_main_option("sqlalchemy.url")
    if url:
        return url
    
    # 默认值
    return "mysql+aiomysql://root:password@localhost/wangzhe"


def run_migrations_offline() -> None:
    """
    离线模式运行迁移
    
    在不连接数据库的情况下生成 SQL 脚本。
    适用于：
    - 生成 SQL 脚本供 DBA 审核
    - 在无法直接连接生产数据库时
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # 比较类型和服务器默认值
        compare_type=True,
        compare_server_default=True,
        # 事务模式
        transaction_per_migration=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """
    执行迁移
    
    Args:
        connection: 数据库连接
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # 比较类型和服务器默认值
        compare_type=True,
        compare_server_default=True,
        # 事务模式
        transaction_per_migration=True,
        # 渲染 item（用于自定义类型）
        render_item=render_item,
        # 包含对象（用于自定义过滤）
        include_object=include_object,
        # 事务 DDL（MySQL 不支持）
        transactional_ddl=False,
    )

    with context.begin_transaction():
        context.run_migrations()


def render_item(
    type_: Any,
    obj: Any,
    autogen_context: Any,
) -> Any:
    """
    自定义类型渲染
    
    用于处理自定义的 SQLAlchemy 类型。
    
    Args:
        type_: 类型名称
        obj: 类型对象
        autogen_context: 自动生成上下文
        
    Returns:
        渲染结果（返回 False 使用默认渲染）
    """
    return False


def include_object(
    object: Any,
    name: str | None,
    type_: str,
    reflected: bool,
    compare_to: Any,
) -> bool:
    """
    过滤要包含在迁移中的对象
    
    Args:
        object: 数据库对象
        name: 对象名称
        type_: 对象类型（table, column, etc.）
        reflected: 是否从数据库反射
        compare_to: 比较目标
        
    Returns:
        是否包含该对象
    """
    # 排除特定的表（如第三方库的表）
    # if type_ == "table" and name and name.startswith("third_party_"):
    #     return False
    return True


async def run_async_migrations() -> None:
    """
    异步模式运行迁移
    
    使用异步引擎连接数据库并执行迁移。
    """
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_url()
    
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        # 测试连接
        try:
            await connection.execute(text("SELECT 1"))
            logger.info("数据库连接成功")
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            raise
        
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """
    在线模式运行迁移
    
    连接数据库并执行迁移。
    """
    asyncio.run(run_async_migrations())


# 根据模式选择运行方式
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
