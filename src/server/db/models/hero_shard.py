"""
王者之奕 - 英雄碎片数据库模型

本模块定义英雄碎片系统的数据库持久化模型：
- HeroShardDB: 玩家英雄碎片记录
- ShardHistoryDB: 碎片变动历史记录

用于存储碎片相关的持久化数据。
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


class HeroShardDB(Base, IdMixin, TimestampMixin):
    """
    英雄碎片数据模型
    
    存储玩家的英雄碎片数量。
    
    Attributes:
        id: 主键ID
        player_id: 玩家ID
        hero_id: 英雄ID
        hero_name: 英雄名称
        quantity: 碎片数量
        hero_cost: 英雄费用
        acquired_sources: 各来源获得的碎片数量（JSON）
        last_acquired_at: 最后获得时间
        is_notified: 是否已通知玩家可合成
    """
    
    __tablename__ = "hero_shards"
    __table_args__ = (
        UniqueConstraint("player_id", "hero_id", name="uq_player_hero_shard"),
        Index("ix_hero_shards_player_id", "player_id"),
        Index("ix_hero_shards_hero_id", "hero_id"),
        Index("ix_hero_shards_quantity", "quantity"),
        Index("ix_hero_shards_player_hero", "player_id", "hero_id"),
        {"comment": "英雄碎片表"},
    )
    
    player_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="玩家ID",
    )
    
    hero_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="英雄ID",
    )
    
    hero_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="",
        comment="英雄名称",
    )
    
    quantity: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="碎片数量",
    )
    
    hero_cost: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="英雄费用",
    )
    
    acquired_sources: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="各来源获得的碎片数量",
    )
    
    last_acquired_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="最后获得时间",
    )
    
    is_notified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否已通知可合成",
    )
    
    def __repr__(self) -> str:
        return f"<HeroShardDB(player_id='{self.player_id}', hero_id='{self.hero_id}', quantity={self.quantity})>"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        data = super().to_dict()
        data["last_acquired_at"] = self.last_acquired_at.isoformat() if self.last_acquired_at else None
        return data
    
    def add_shards(self, amount: int, source: str) -> None:
        """
        增加碎片
        
        Args:
            amount: 数量
            source: 来源
        """
        self.quantity += amount
        self.last_acquired_at = datetime.now()
        self.is_notified = False
        
        if self.acquired_sources is None:
            self.acquired_sources = {}
        self.acquired_sources[source] = self.acquired_sources.get(source, 0) + amount
    
    def remove_shards(self, amount: int) -> bool:
        """
        减少碎片
        
        Args:
            amount: 数量
            
        Returns:
            是否成功
        """
        if self.quantity < amount:
            return False
        self.quantity -= amount
        return True
    
    def can_compose_one_star(self) -> bool:
        """检查是否可以合成1星英雄"""
        return self.quantity >= 100


class ShardHistoryDB(Base, IdMixin, TimestampMixin):
    """
    碎片变动历史记录
    
    存储碎片变动的详细记录。
    
    Attributes:
        id: 主键ID
        player_id: 玩家ID
        hero_id: 英雄ID
        change_type: 变动类型（add/remove）
        amount: 变动数量
        source: 变动来源
        reason: 变动原因
        balance_before: 变动前余额
        balance_after: 变动后余额
        related_id: 关联ID（如合成/分解记录ID）
    """
    
    __tablename__ = "shard_history"
    __table_args__ = (
        Index("ix_shard_history_player_id", "player_id"),
        Index("ix_shard_history_hero_id", "hero_id"),
        Index("ix_shard_history_change_type", "change_type"),
        Index("ix_shard_history_created_at", "created_at"),
        Index("ix_shard_history_player_time", "player_id", "created_at"),
        {"comment": "碎片变动历史表"},
    )
    
    player_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="玩家ID",
    )
    
    hero_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="英雄ID",
    )
    
    change_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="变动类型",
    )
    
    amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="变动数量",
    )
    
    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="变动来源",
    )
    
    reason: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="变动原因",
    )
    
    balance_before: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="变动前余额",
    )
    
    balance_after: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="变动后余额",
    )
    
    related_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="关联ID",
    )
    
    def __repr__(self) -> str:
        return f"<ShardHistoryDB(player_id='{self.player_id}', hero_id='{self.hero_id}', change={self.change_type}:{self.amount})>"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        data = super().to_dict()
        return data


class ComposeRecordDB(Base, IdMixin, TimestampMixin):
    """
    英雄合成记录
    
    存储英雄合成的详细记录。
    
    Attributes:
        id: 主键ID
        player_id: 玩家ID
        hero_id: 英雄ID
        hero_name: 英雄名称
        target_star: 目标星级
        shards_used: 消耗碎片数
        heroes_used: 消耗英雄数
        is_success: 是否成功
        error_message: 错误信息
    """
    
    __tablename__ = "compose_records"
    __table_args__ = (
        Index("ix_compose_records_player_id", "player_id"),
        Index("ix_compose_records_hero_id", "hero_id"),
        Index("ix_compose_records_created_at", "created_at"),
        Index("ix_compose_records_player_time", "player_id", "created_at"),
        {"comment": "英雄合成记录表"},
    )
    
    player_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="玩家ID",
    )
    
    hero_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="英雄ID",
    )
    
    hero_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="",
        comment="英雄名称",
    )
    
    target_star: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="目标星级",
    )
    
    shards_used: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="消耗碎片数",
    )
    
    heroes_used: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="消耗英雄数",
    )
    
    is_success: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否成功",
    )
    
    error_message: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="错误信息",
    )
    
    def __repr__(self) -> str:
        return f"<ComposeRecordDB(player_id='{self.player_id}', hero_id='{self.hero_id}', star={self.target_star})>"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return super().to_dict()


class DecomposeRecordDB(Base, IdMixin, TimestampMixin):
    """
    英雄分解记录
    
    存储英雄分解的详细记录。
    
    Attributes:
        id: 主键ID
        player_id: 玩家ID
        hero_id: 英雄ID
        hero_name: 英雄名称
        star_level: 英雄星级
        shards_gained: 获得碎片数
        is_success: 是否成功
        error_message: 错误信息
    """
    
    __tablename__ = "decompose_records"
    __table_args__ = (
        Index("ix_decompose_records_player_id", "player_id"),
        Index("ix_decompose_records_hero_id", "hero_id"),
        Index("ix_decompose_records_created_at", "created_at"),
        Index("ix_decompose_records_player_time", "player_id", "created_at"),
        {"comment": "英雄分解记录表"},
    )
    
    player_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="玩家ID",
    )
    
    hero_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="英雄ID",
    )
    
    hero_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="",
        comment="英雄名称",
    )
    
    star_level: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="英雄星级",
    )
    
    shards_gained: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="获得碎片数",
    )
    
    is_success: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否成功",
    )
    
    error_message: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="错误信息",
    )
    
    def __repr__(self) -> str:
        return f"<DecomposeRecordDB(player_id='{self.player_id}', hero_id='{self.hero_id}', star={self.star_level})>"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return super().to_dict()
