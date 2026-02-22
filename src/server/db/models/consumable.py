"""
王者之奕 - 道具数据库模型

本模块定义道具系统的数据库持久化模型：
- ConsumableDB: 玩家拥有的道具记录
- ConsumableEffectDB: 激活的道具效果记录
- ConsumableUsageDB: 道具使用历史记录

用于存储道具相关的持久化数据。
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.server.models.base import Base, IdMixin, TimestampMixin


class ConsumableDB(Base, IdMixin, TimestampMixin):
    """
    玩家道具数据模型
    
    存储玩家拥有的道具信息。
    
    Attributes:
        id: 主键ID
        player_id: 玩家ID
        consumable_id: 道具ID（对应 consumables.json 中的 consumable_id）
        quantity: 数量
        acquired_at: 获得时间
        acquire_type: 获得方式（buy/reward/achievement/checkin/event）
        expire_at: 过期时间（NULL表示永不过期）
    """
    
    __tablename__ = "player_consumables"
    __table_args__ = (
        UniqueConstraint("player_id", "consumable_id", name="uq_player_consumable"),
        Index("ix_player_consumables_player_id", "player_id"),
        Index("ix_player_consumables_consumable_id", "consumable_id"),
        Index("ix_player_consumables_expire_at", "expire_at"),
        {"comment": "玩家道具表"},
    )
    
    player_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="玩家ID",
    )
    
    consumable_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="道具ID",
    )
    
    quantity: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="数量",
    )
    
    acquired_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False,
        comment="获得时间",
    )
    
    acquire_type: Mapped[str] = mapped_column(
        String(32),
        default="buy",
        nullable=False,
        comment="获得方式",
    )
    
    expire_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="过期时间",
    )
    
    def __repr__(self) -> str:
        return f"<ConsumableDB(player_id='{self.player_id}', consumable_id='{self.consumable_id}', qty={self.quantity})>"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        data = super().to_dict()
        data["acquired_at"] = self.acquired_at.isoformat() if self.acquired_at else None
        data["expire_at"] = self.expire_at.isoformat() if self.expire_at else None
        return data
    
    def is_expired(self) -> bool:
        """检查是否已过期"""
        if self.expire_at is None:
            return False
        return datetime.now() > self.expire_at
    
    def add_quantity(self, amount: int, max_stack: int = 99) -> int:
        """增加数量，返回实际增加数量"""
        old_qty = self.quantity
        self.quantity = min(self.quantity + amount, max_stack)
        return self.quantity - old_qty
    
    def use_quantity(self, amount: int = 1) -> bool:
        """使用道具（减少数量）"""
        if self.quantity < amount:
            return False
        self.quantity -= amount
        return True


class ConsumableEffectDB(Base, IdMixin, TimestampMixin):
    """
    激活的道具效果数据模型
    
    存储玩家当前激活的道具效果。
    
    Attributes:
        id: 主键ID
        player_id: 玩家ID
        consumable_id: 道具ID
        effect_type: 效果类型
        value: 效果数值
        activated_at: 激活时间
        remaining_rounds: 剩余回合数（-1表示无限）
        context: 激活场景
        context_id: 场景ID
    """
    
    __tablename__ = "consumable_effects"
    __table_args__ = (
        Index("ix_consumable_effects_player_id", "player_id"),
        Index("ix_consumable_effects_type", "effect_type"),
        Index("ix_consumable_effects_remaining", "remaining_rounds"),
        {"comment": "激活道具效果表"},
    )
    
    player_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="玩家ID",
    )
    
    consumable_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="道具ID",
    )
    
    effect_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="效果类型",
    )
    
    value: Mapped[float] = mapped_column(
        Integer,
        default=1.0,
        nullable=False,
        comment="效果数值",
    )
    
    activated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False,
        comment="激活时间",
    )
    
    remaining_rounds: Mapped[int] = mapped_column(
        Integer,
        default=-1,
        nullable=False,
        comment="剩余回合数(-1无限)",
    )
    
    context: Mapped[str] = mapped_column(
        String(32),
        default="match",
        nullable=False,
        comment="激活场景",
    )
    
    context_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="场景ID",
    )
    
    def __repr__(self) -> str:
        return f"<ConsumableEffectDB(player_id='{self.player_id}', type='{self.effect_type}', rounds={self.remaining_rounds})>"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        data = super().to_dict()
        data["activated_at"] = self.activated_at.isoformat() if self.activated_at else None
        return data
    
    def decrement_rounds(self) -> bool:
        """减少剩余回合数，返回效果是否仍有效"""
        if self.remaining_rounds <= 0:
            return True  # 无限持续
        self.remaining_rounds -= 1
        return self.remaining_rounds > 0
    
    def is_expired(self) -> bool:
        """检查效果是否已过期"""
        if self.remaining_rounds < 0:
            return False  # 无限持续
        return self.remaining_rounds <= 0


class ConsumableUsageDB(Base, IdMixin, TimestampMixin):
    """
    道具使用历史数据模型
    
    记录道具使用历史，用于统计和分析。
    
    Attributes:
        id: 主键ID
        player_id: 玩家ID
        consumable_id: 道具ID
        used_at: 使用时间
        quantity: 使用数量
        context: 使用场景
        context_id: 场景ID
        effect_applied: 效果是否生效
        effect_data: 效果数据
    """
    
    __tablename__ = "consumable_usage_logs"
    __table_args__ = (
        Index("ix_consumable_usage_logs_player_id", "player_id"),
        Index("ix_consumable_usage_logs_consumable_id", "consumable_id"),
        Index("ix_consumable_usage_logs_used_at", "used_at"),
        {"comment": "道具使用日志表"},
    )
    
    player_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="玩家ID",
    )
    
    consumable_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="道具ID",
    )
    
    used_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False,
        comment="使用时间",
    )
    
    quantity: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="使用数量",
    )
    
    context: Mapped[str] = mapped_column(
        String(32),
        default="match",
        nullable=False,
        comment="使用场景",
    )
    
    context_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="场景ID",
    )
    
    effect_applied: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="效果是否生效",
    )
    
    effect_data: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="效果数据",
    )
    
    def __repr__(self) -> str:
        return f"<ConsumableUsageDB(player_id='{self.player_id}', consumable_id='{self.consumable_id}', qty={self.quantity})>"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        data = super().to_dict()
        data["used_at"] = self.used_at.isoformat() if self.used_at else None
        return data


class ConsumablePurchaseLogDB(Base, IdMixin, TimestampMixin):
    """
    道具购买日志数据模型
    
    记录道具购买历史，用于统计和分析。
    
    Attributes:
        id: 主键ID
        player_id: 玩家ID
        consumable_id: 道具ID
        quantity: 购买数量
        currency: 货币类型
        cost: 花费
        balance_before: 购买前余额
        balance_after: 购买后余额
    """
    
    __tablename__ = "consumable_purchase_logs"
    __table_args__ = (
        Index("ix_consumable_purchase_logs_player_id", "player_id"),
        Index("ix_consumable_purchase_logs_consumable_id", "consumable_id"),
        Index("ix_consumable_purchase_logs_created_at", "created_at"),
        {"comment": "道具购买日志表"},
    )
    
    player_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="玩家ID",
    )
    
    consumable_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="道具ID",
    )
    
    quantity: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="购买数量",
    )
    
    currency: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        comment="货币类型",
    )
    
    cost: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="花费",
    )
    
    balance_before: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="购买前余额",
    )
    
    balance_after: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="购买后余额",
    )
    
    def __repr__(self) -> str:
        return f"<ConsumablePurchaseLogDB(player_id='{self.player_id}', consumable_id='{self.consumable_id}', cost={self.cost})>"
