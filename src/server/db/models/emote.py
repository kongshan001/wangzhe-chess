"""
王者之奕 - 表情数据库模型

本模块定义表情系统的数据库持久化模型：
- EmoteDB: 表情定义（系统预定义）
- PlayerEmoteDB: 玩家拥有的表情
- EmoteHistoryDB: 表情发送历史
- EmoteHotkeyDB: 表情快捷键设置

用于存储表情相关的持久化数据。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from src.server.models.base import Base, IdMixin, TimestampMixin


class EmoteDB(Base, IdMixin, TimestampMixin):
    """
    表情定义数据模型

    存储系统预定义的表情信息。

    Attributes:
        id: 主键ID
        emote_id: 表情唯一ID
        name: 表情名称
        description: 表情描述
        category: 表情分类 (default/unlock/premium/special)
        emote_type: 表情类型 (static/animated/sound)
        asset_url: 表情资源URL
        thumbnail_url: 缩略图URL
        sound_url: 音效URL
        unlock_condition: 解锁条件 (JSON)
        is_free: 是否免费
        sort_order: 排序顺序
        is_active: 是否启用
    """

    __tablename__ = "emotes"
    __table_args__ = (
        UniqueConstraint("emote_id", name="uq_emotes_emote_id"),
        Index("ix_emotes_category", "category"),
        Index("ix_emotes_sort_order", "sort_order"),
        {"comment": "表情定义表"},
    )

    emote_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        comment="表情唯一ID",
    )

    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="表情名称",
    )

    description: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="表情描述",
    )

    category: Mapped[str] = mapped_column(
        String(20),
        default="default",
        nullable=False,
        comment="表情分类",
    )

    emote_type: Mapped[str] = mapped_column(
        String(20),
        default="static",
        nullable=False,
        comment="表情类型",
    )

    asset_url: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="",
        comment="表情资源URL",
    )

    thumbnail_url: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="缩略图URL",
    )

    sound_url: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="音效URL",
    )

    unlock_condition: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="解锁条件",
    )

    is_free: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否免费",
    )

    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="排序顺序",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否启用",
    )

    def __repr__(self) -> str:
        return f"<EmoteDB(emote_id='{self.emote_id}', name='{self.name}')>"

    def to_dict(self) -> dict:
        """转换为字典"""
        data = super().to_dict()
        return data


class PlayerEmoteDB(Base, IdMixin, TimestampMixin):
    """
    玩家表情数据模型

    存储玩家拥有的表情信息。

    Attributes:
        id: 主键ID
        player_id: 玩家ID
        emote_id: 表情ID
        unlocked_at: 解锁时间
        use_count: 使用次数
    """

    __tablename__ = "player_emotes"
    __table_args__ = (
        UniqueConstraint("player_id", "emote_id", name="uq_player_emote"),
        Index("ix_player_emotes_player_id", "player_id"),
        Index("ix_player_emotes_emote_id", "emote_id"),
        {"comment": "玩家表情表"},
    )

    player_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="玩家ID",
    )

    emote_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="表情ID",
    )

    unlocked_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        comment="解锁时间",
    )

    use_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="使用次数",
    )

    def __repr__(self) -> str:
        return f"<PlayerEmoteDB(player_id='{self.player_id}', emote_id='{self.emote_id}')>"


class EmoteHistoryDB(Base, IdMixin, TimestampMixin):
    """
    表情发送历史数据模型

    存储表情发送记录。

    Attributes:
        id: 主键ID
        history_id: 历史记录唯一ID
        room_id: 房间ID
        from_player_id: 发送者ID
        to_player_id: 目标玩家ID（NULL表示发送给所有玩家）
        emote_id: 表情ID
        round_number: 回合数
    """

    __tablename__ = "emote_history"
    __table_args__ = (
        Index("ix_emote_history_room_id", "room_id"),
        Index("ix_emote_history_from_player", "from_player_id"),
        Index("ix_emote_history_to_player", "to_player_id"),
        Index("ix_emote_history_created", "created_at"),
        Index("ix_emote_history_room_round", "room_id", "round_number"),
        {"comment": "表情发送历史表"},
    )

    history_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        comment="历史记录唯一ID",
    )

    room_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="房间ID",
    )

    from_player_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="发送者ID",
    )

    to_player_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="目标玩家ID（NULL表示所有玩家）",
    )

    emote_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="表情ID",
    )

    round_number: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="回合数",
    )

    def __repr__(self) -> str:
        return f"<EmoteHistoryDB(history_id='{self.history_id}', room_id='{self.room_id}')>"


class EmoteHotkeyDB(Base, IdMixin, TimestampMixin):
    """
    表情快捷键数据模型

    存储玩家设置的表情快捷键。

    Attributes:
        id: 主键ID
        player_id: 玩家ID
        emote_id: 表情ID
        hotkey: 快捷键
    """

    __tablename__ = "emote_hotkeys"
    __table_args__ = (
        UniqueConstraint("player_id", "hotkey", name="uq_player_hotkey"),
        Index("ix_emote_hotkeys_player_id", "player_id"),
        {"comment": "表情快捷键表"},
    )

    player_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="玩家ID",
    )

    emote_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="表情ID",
    )

    hotkey: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="快捷键",
    )

    def __repr__(self) -> str:
        return f"<EmoteHotkeyDB(player_id='{self.player_id}', hotkey='{self.hotkey}', emote_id='{self.emote_id}')>"
