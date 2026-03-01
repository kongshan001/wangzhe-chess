"""
王者之奕 - 基础模型类

本模块提供 SQLAlchemy ORM 的基础类和工具：
- Base: 所有模型的基类
- TimestampMixin: 时间戳混入类
- 通用字段和工具方法

所有数据模型都应继承 Base 类以获得统一的功能。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Integer, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    SQLAlchemy 声明式基类

    所有 ORM 模型都应继承此类。提供：
    - 统一的元数据管理
    - 通用的 to_dict 方法
    - 类型注解支持

    Example:
        class Player(Base):
            __tablename__ = "players"

            id: Mapped[int] = mapped_column(primary_key=True)
            name: Mapped[str] = mapped_column(String(50))
    """

    def to_dict(self) -> dict[str, Any]:
        """
        将模型实例转换为字典

        Returns:
            包含所有列值的字典

        Note:
            子类可以覆盖此方法以自定义输出格式
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            # 处理 datetime 类型
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result

    def update_from_dict(self, data: dict[str, Any]) -> None:
        """
        从字典更新模型属性

        Args:
            data: 包含更新数据的字典

        Note:
            只更新存在的列，忽略未知字段
        """
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)


class TimestampMixin:
    """
    时间戳混入类

    为模型添加 created_at 和 updated_at 字段。
    updated_at 会在每次提交时自动更新。

    Example:
        class Player(Base, TimestampMixin):
            __tablename__ = "players"
            id: Mapped[int] = mapped_column(primary_key=True)
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False,
        comment="创建时间",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间",
    )


class IdMixin:
    """
    ID 混入类

    为模型添加自增主键 id 字段。

    Example:
        class Player(Base, IdMixin):
            __tablename__ = "players"
            name: Mapped[str] = mapped_column(String(50))
    """

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="主键ID",
    )
