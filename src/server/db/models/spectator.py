"""
王者之奕 - 观战系统数据库模型

本模块定义观战相关的数据库模型：
- SpectatorDB: 观战记录
- SpectatorChatDB: 观战聊天记录

用于持久化观战数据。
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
    Text,
    func,
)
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from src.server.models.base import Base, IdMixin, TimestampMixin


class SpectatorDB(Base, IdMixin, TimestampMixin):
    """
    观战记录模型

    记录玩家的观战历史。

    Attributes:
        id: 主键ID
        spectator_id: 观众玩家ID（外键）
        game_id: 观战的对局ID
        watching_player_id: 观看的玩家ID
        joined_at: 加入时间
        left_at: 离开时间
        duration_seconds: 观战时长（秒）
        chat_count: 发送弹幕数量
        visibility: 对局可见性
        metadata: 额外数据
    """

    __tablename__ = "spectator_records"
    __table_args__ = (
        Index("ix_spectator_records_spectator_id", "spectator_id"),
        Index("ix_spectator_records_game_id", "game_id"),
        Index("ix_spectator_records_joined_at", "joined_at"),
        {"comment": "观战记录表"},
    )

    spectator_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
        comment="观众玩家ID",
    )

    game_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="观战的对局ID",
    )

    watching_player_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="观看的玩家ID",
    )

    joined_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        comment="加入时间",
    )

    left_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="离开时间",
    )

    duration_seconds: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="观战时长（秒）",
    )

    chat_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="发送弹幕数量",
    )

    visibility: Mapped[str] = mapped_column(
        String(20),
        default="public",
        nullable=False,
        comment="对局可见性",
    )

    metadata: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="额外数据",
    )

    def __repr__(self) -> str:
        return f"<SpectatorDB(id={self.id}, spectator_id={self.spectator_id}, game_id='{self.game_id}')>"

    @property
    def is_active(self) -> bool:
        """是否正在观战"""
        return self.left_at is None

    def calculate_duration(self) -> int:
        """计算观战时长"""
        if self.left_at is None:
            end_time = datetime.now()
        else:
            end_time = self.left_at
        return int((end_time - self.joined_at).total_seconds())


class SpectatorChatDB(Base, IdMixin, TimestampMixin):
    """
    观战聊天记录模型

    记录观战中的弹幕和聊天消息。

    Attributes:
        id: 主键ID
        game_id: 对局ID
        sender_id: 发送者ID（外键）
        sender_name: 发送者昵称
        content: 消息内容
        sent_at: 发送时间
        message_type: 消息类型
        avatar: 头像
        tier: 段位
        is_deleted: 是否已删除
    """

    __tablename__ = "spectator_chats"
    __table_args__ = (
        Index("ix_spectator_chats_game_id", "game_id"),
        Index("ix_spectator_chats_sender_id", "sender_id"),
        Index("ix_spectator_chats_sent_at", "sent_at"),
        {"comment": "观战聊天记录表"},
    )

    game_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="对局ID",
    )

    sender_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
        comment="发送者ID",
    )

    sender_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="发送者昵称",
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="消息内容",
    )

    sent_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        comment="发送时间",
    )

    message_type: Mapped[str] = mapped_column(
        String(20),
        default="text",
        nullable=False,
        comment="消息类型 (text/emoji/system)",
    )

    avatar: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="头像URL",
    )

    tier: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="段位",
    )

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否已删除",
    )

    def __repr__(self) -> str:
        return (
            f"<SpectatorChatDB(id={self.id}, game_id='{self.game_id}', sender_id={self.sender_id})>"
        )


class SpectatorStatsDB(Base, IdMixin, TimestampMixin):
    """
    观战统计模型

    统计玩家的观战数据。

    Attributes:
        id: 主键ID
        player_id: 玩家ID（外键）
        total_spectate_count: 总观战次数
        total_spectate_time: 总观战时长（秒）
        total_chat_count: 总弹幕数量
        favorite_players: 最常观战的玩家
        created_at: 创建时间
        updated_at: 更新时间
    """

    __tablename__ = "spectator_stats"
    __table_args__ = (
        Index("ix_spectator_stats_player_id", "player_id", unique=True),
        {"comment": "观战统计表"},
    )

    player_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        comment="玩家ID",
    )

    total_spectate_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总观战次数",
    )

    total_spectate_time: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总观战时长（秒）",
    )

    total_chat_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总弹幕数量",
    )

    favorite_players: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="最常观战的玩家统计",
    )

    def __repr__(self) -> str:
        return f"<SpectatorStatsDB(player_id={self.player_id}, count={self.total_spectate_count})>"

    @property
    def avg_spectate_time(self) -> float:
        """平均观战时长（秒）"""
        if self.total_spectate_count == 0:
            return 0.0
        return round(self.total_spectate_time / self.total_spectate_count, 2)
