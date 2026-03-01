"""
王者之奕 - 交易数据库模型

本模块定义交易系统的数据库持久化模型：
- TradeDB: 交易记录
- TradeItemDB: 交易物品
- TradeHistoryDB: 交易历史

用于存储交易相关的持久化数据。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from src.server.models.base import Base, IdMixin, TimestampMixin


class TradeDB(Base, IdMixin, TimestampMixin):
    """
    交易记录数据模型

    存储所有交易记录，包括进行中和已完成的交易。

    Attributes:
        id: 主键ID
        trade_id: 交易唯一ID
        sender_id: 发起方ID
        sender_name: 发起方名称
        receiver_id: 接收方ID
        receiver_name: 接收方名称
        status: 交易状态
        sender_items: 发起方物品 (JSON)
        receiver_items: 接收方物品 (JSON)
        sender_confirmed: 发起方是否确认
        receiver_confirmed: 接收方是否确认
        tax_amount: 税额
        message: 附带消息
        reject_reason: 拒绝原因
        error_message: 错误信息
        expires_at: 过期时间
        executed_at: 执行时间
    """

    __tablename__ = "trades"
    __table_args__ = (
        Index("ix_trades_trade_id", "trade_id", unique=True),
        Index("ix_trades_sender_id", "sender_id"),
        Index("ix_trades_receiver_id", "receiver_id"),
        Index("ix_trades_status", "status"),
        Index("ix_trades_created", "created_at"),
        Index("ix_trades_players", "sender_id", "receiver_id"),
        {"comment": "交易记录表"},
    )

    trade_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        comment="交易ID",
    )

    sender_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="发起方ID",
    )

    sender_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="发起方名称",
    )

    receiver_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="接收方ID",
    )

    receiver_name: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="接收方名称",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
        comment="交易状态",
    )

    sender_items: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="发起方物品",
    )

    receiver_items: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="接收方物品",
    )

    sender_confirmed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="发起方是否确认",
    )

    receiver_confirmed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="接收方是否确认",
    )

    tax_amount: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="税额",
    )

    message: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="附带消息",
    )

    reject_reason: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="拒绝原因",
    )

    error_message: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="错误信息",
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="过期时间",
    )

    executed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="执行时间",
    )

    def __repr__(self) -> str:
        return f"<TradeDB(trade_id='{self.trade_id}', status='{self.status}')>"

    def to_dict(self) -> dict:
        """转换为字典"""
        data = super().to_dict()
        return data

    @property
    def is_pending(self) -> bool:
        """是否待处理"""
        return self.status == "pending"

    @property
    def is_executed(self) -> bool:
        """是否已执行"""
        return self.status == "executed"

    @property
    def is_both_confirmed(self) -> bool:
        """双方是否都已确认"""
        return self.sender_confirmed and self.receiver_confirmed


class TradeItemDB(Base, IdMixin, TimestampMixin):
    """
    交易物品数据模型

    存储交易中的具体物品信息。

    Attributes:
        id: 主键ID
        trade_id: 关联的交易ID
        player_id: 物品所有者ID
        item_type: 物品类型
        item_id: 物品ID
        item_name: 物品名称
        quantity: 数量
        tax_applied: 应缴税额
        extra_data: 额外数据
    """

    __tablename__ = "trade_items"
    __table_args__ = (
        Index("ix_trade_items_trade_id", "trade_id"),
        Index("ix_trade_items_player_id", "player_id"),
        Index("ix_trade_items_type", "item_type"),
        {"comment": "交易物品表"},
    )

    trade_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("trades.trade_id", ondelete="CASCADE"),
        nullable=False,
        comment="交易ID",
    )

    player_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="物品所有者ID",
    )

    item_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="物品类型",
    )

    item_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="物品ID",
    )

    item_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="物品名称",
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="数量",
    )

    tax_applied: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="应缴税额",
    )

    extra_data: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="额外数据",
    )

    def __repr__(self) -> str:
        return f"<TradeItemDB(trade_id='{self.trade_id}', item='{self.item_name}')>"

    def to_dict(self) -> dict:
        """转换为字典"""
        data = super().to_dict()
        return data


class TradeHistoryDB(Base, IdMixin, TimestampMixin):
    """
    交易历史数据模型

    存储玩家的交易历史统计。

    Attributes:
        id: 主键ID
        player_id: 玩家ID
        total_trades: 总交易次数
        total_tax_paid: 总缴税
        total_gold_traded: 总金币交易量
        total_items_traded: 总物品交易量
        daily_count: 今日交易次数
        daily_date: 每日计数日期
    """

    __tablename__ = "trade_history"
    __table_args__ = (
        UniqueConstraint("player_id", name="uq_trade_history_player"),
        Index("ix_trade_history_player_id", "player_id"),
        {"comment": "交易历史表"},
    )

    player_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        comment="玩家ID",
    )

    total_trades: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总交易次数",
    )

    total_tax_paid: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总缴税",
    )

    total_gold_traded: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总金币交易量",
    )

    total_items_traded: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总物品交易量",
    )

    daily_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="今日交易次数",
    )

    daily_date: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="每日计数日期",
    )

    def __repr__(self) -> str:
        return f"<TradeHistoryDB(player_id='{self.player_id}', total_trades={self.total_trades})>"

    def to_dict(self) -> dict:
        """转换为字典"""
        data = super().to_dict()
        return data

    def add_trade(self, tax: int = 0, gold: int = 0, items: int = 0) -> None:
        """
        添加交易记录

        Args:
            tax: 税额
            gold: 金币数
            items: 物品数
        """
        today = datetime.now().strftime("%Y-%m-%d")

        # 检查是否需要重置每日计数
        if self.daily_date != today:
            self.daily_count = 0
            self.daily_date = today

        self.total_trades += 1
        self.total_tax_paid += tax
        self.total_gold_traded += gold
        self.total_items_traded += items
        self.daily_count += 1
