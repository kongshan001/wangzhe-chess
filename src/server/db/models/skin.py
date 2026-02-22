"""
王者之奕 - 皮肤数据库模型

本模块定义皮肤系统的数据库持久化模型：
- SkinDB: 玩家拥有的皮肤记录

用于存储皮肤相关的持久化数据。
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
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.server.models.base import Base, IdMixin, TimestampMixin


class SkinDB(Base, IdMixin, TimestampMixin):
    """
    玩家皮肤数据模型
    
    存储玩家拥有的皮肤信息。
    
    Attributes:
        id: 主键ID
        player_id: 玩家ID
        skin_id: 皮肤ID（对应 skins.json 中的 skin_id）
        hero_id: 英雄ID
        acquired_at: 获得时间
        acquire_type: 获得方式（buy/reward/achievement/event）
        is_equipped: 是否已装备
        equipped_at: 装备时间
        is_favorite: 是否收藏
        purchase_currency: 购买货币类型（gold/diamond/free）
        purchase_cost: 购买价格
        source_event: 来源活动ID（活动限定皮肤）
    """
    
    __tablename__ = "player_skins"
    __table_args__ = (
        UniqueConstraint("player_id", "skin_id", name="uq_player_skin"),
        Index("ix_player_skins_player_id", "player_id"),
        Index("ix_player_skins_skin_id", "skin_id"),
        Index("ix_player_skins_hero_id", "hero_id"),
        Index("ix_player_skins_player_hero", "player_id", "hero_id"),
        Index("ix_player_skins_equipped", "player_id", "is_equipped"),
        {"comment": "玩家皮肤表"},
    )
    
    player_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="玩家ID",
    )
    
    skin_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="皮肤ID",
    )
    
    hero_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="英雄ID",
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
    
    is_equipped: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否已装备",
    )
    
    equipped_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="装备时间",
    )
    
    is_favorite: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否收藏",
    )
    
    purchase_currency: Mapped[Optional[str]] = mapped_column(
        String(16),
        nullable=True,
        comment="购买货币类型",
    )
    
    purchase_cost: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="购买价格",
    )
    
    source_event: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="来源活动ID",
    )
    
    def __repr__(self) -> str:
        return f"<SkinDB(player_id='{self.player_id}', skin_id='{self.skin_id}', equipped={self.is_equipped})>"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        data = super().to_dict()
        data["acquired_at"] = self.acquired_at.isoformat() if self.acquired_at else None
        data["equipped_at"] = self.equipped_at.isoformat() if self.equipped_at else None
        return data
    
    def equip(self) -> None:
        """装备皮肤"""
        self.is_equipped = True
        self.equipped_at = datetime.now()
    
    def unequip(self) -> None:
        """卸下皮肤"""
        self.is_equipped = False
        self.equipped_at = None
    
    def mark_favorite(self, is_favorite: bool = True) -> None:
        """标记收藏"""
        self.is_favorite = is_favorite


class EquippedSkinDB(Base, IdMixin, TimestampMixin):
    """
    玩家装备皮肤数据模型
    
    存储玩家当前装备的皮肤（每个英雄只能装备一个）。
    
    Attributes:
        id: 主键ID
        player_id: 玩家ID
        hero_id: 英雄ID
        skin_id: 装备的皮肤ID
        equipped_at: 装备时间
    """
    
    __tablename__ = "equipped_skins"
    __table_args__ = (
        UniqueConstraint("player_id", "hero_id", name="uq_player_hero_skin"),
        Index("ix_equipped_skins_player_id", "player_id"),
        Index("ix_equipped_skins_hero_id", "hero_id"),
        {"comment": "玩家装备皮肤表"},
    )
    
    player_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="玩家ID",
    )
    
    hero_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="英雄ID",
    )
    
    skin_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="装备的皮肤ID",
    )
    
    equipped_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False,
        comment="装备时间",
    )
    
    def __repr__(self) -> str:
        return f"<EquippedSkinDB(player_id='{self.player_id}', hero_id='{self.hero_id}', skin_id='{self.skin_id}')>"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        data = super().to_dict()
        data["equipped_at"] = self.equipped_at.isoformat() if self.equipped_at else None
        return data


class SkinPurchaseLogDB(Base, IdMixin, TimestampMixin):
    """
    皮肤购买日志数据模型
    
    记录皮肤购买历史，用于统计和分析。
    
    Attributes:
        id: 主键ID
        player_id: 玩家ID
        skin_id: 皮肤ID
        hero_id: 英雄ID
        currency: 货币类型
        cost: 花费
        balance_before: 购买前余额
        balance_after: 购买后余额
    """
    
    __tablename__ = "skin_purchase_logs"
    __table_args__ = (
        Index("ix_skin_purchase_logs_player_id", "player_id"),
        Index("ix_skin_purchase_logs_skin_id", "skin_id"),
        Index("ix_skin_purchase_logs_created_at", "created_at"),
        {"comment": "皮肤购买日志表"},
    )
    
    player_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="玩家ID",
    )
    
    skin_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="皮肤ID",
    )
    
    hero_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="英雄ID",
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
        return f"<SkinPurchaseLogDB(player_id='{self.player_id}', skin_id='{self.skin_id}', cost={self.cost})>"
