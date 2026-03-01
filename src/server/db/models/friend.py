"""
王者之奕 - 好友数据库模型

本模块定义好友系统的数据库持久化模型：
- FriendDB: 好友关系
- FriendRequestDB: 好友请求
- BlockedPlayerDB: 黑名单
- PrivateMessageDB: 私聊消息
- TeamDB: 组队信息

用于存储好友相关的持久化数据。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from src.server.models.base import Base, IdMixin, TimestampMixin


class FriendDB(Base, IdMixin, TimestampMixin):
    """
    好友关系数据模型

    存储玩家之间的好友关系。

    Attributes:
        id: 主键ID
        player_id: 玩家ID
        friend_id: 好友ID
        relation: 关系类型 (friend/blocked)
        remark: 好友备注
        intimacy: 亲密度
    """

    __tablename__ = "friends"
    __table_args__ = (
        UniqueConstraint("player_id", "friend_id", name="uq_friend_relation"),
        Index("ix_friends_player_id", "player_id"),
        Index("ix_friends_friend_id", "friend_id"),
        Index("ix_friends_relation", "relation"),
        {"comment": "好友关系表"},
    )

    player_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="玩家ID",
    )

    friend_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="好友ID",
    )

    relation: Mapped[str] = mapped_column(
        String(20),
        default="friend",
        nullable=False,
        comment="关系类型",
    )

    remark: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="好友备注",
    )

    intimacy: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="亲密度",
    )

    def __repr__(self) -> str:
        return f"<FriendDB(player_id='{self.player_id}', friend_id='{self.friend_id}')>"

    def to_dict(self) -> dict:
        """转换为字典"""
        data = super().to_dict()
        return data


class FriendRequestDB(Base, IdMixin, TimestampMixin):
    """
    好友请求数据模型

    存储好友请求记录。

    Attributes:
        id: 主键ID
        from_player_id: 发送者ID
        to_player_id: 接收者ID
        status: 请求状态 (pending/accepted/rejected/expired)
        message: 附带消息
        expires_at: 过期时间
    """

    __tablename__ = "friend_requests"
    __table_args__ = (
        Index("ix_friend_requests_from", "from_player_id"),
        Index("ix_friend_requests_to", "to_player_id"),
        Index("ix_friend_requests_status", "status"),
        Index("ix_friend_requests_created", "created_at"),
        {"comment": "好友请求表"},
    )

    from_player_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="发送者ID",
    )

    to_player_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="接收者ID",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
        comment="请求状态",
    )

    message: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="附带消息",
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="过期时间",
    )

    def __repr__(self) -> str:
        return f"<FriendRequestDB(from='{self.from_player_id}', to='{self.to_player_id}', status='{self.status}')>"

    @property
    def is_pending(self) -> bool:
        """是否待处理"""
        return self.status == "pending"

    @property
    def is_expired(self) -> bool:
        """是否已过期"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at


class BlockedPlayerDB(Base, IdMixin, TimestampMixin):
    """
    黑名单数据模型

    存储玩家的黑名单。

    Attributes:
        id: 主键ID
        player_id: 玩家ID
        blocked_player_id: 被拉黑的玩家ID
        reason: 拉黑原因
    """

    __tablename__ = "blocked_players"
    __table_args__ = (
        UniqueConstraint("player_id", "blocked_player_id", name="uq_blocked_relation"),
        Index("ix_blocked_players_player_id", "player_id"),
        Index("ix_blocked_players_blocked_id", "blocked_player_id"),
        {"comment": "黑名单表"},
    )

    player_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="玩家ID",
    )

    blocked_player_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="被拉黑的玩家ID",
    )

    reason: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="拉黑原因",
    )

    def __repr__(self) -> str:
        return (
            f"<BlockedPlayerDB(player_id='{self.player_id}', blocked='{self.blocked_player_id}')>"
        )


class PrivateMessageDB(Base, IdMixin, TimestampMixin):
    """
    私聊消息数据模型

    存储玩家之间的私聊消息。

    Attributes:
        id: 主键ID
        from_player_id: 发送者ID
        to_player_id: 接收者ID
        content: 消息内容
        message_type: 消息类型 (text/emoji/system)
        is_read: 是否已读
    """

    __tablename__ = "private_messages"
    __table_args__ = (
        Index("ix_private_messages_from", "from_player_id"),
        Index("ix_private_messages_to", "to_player_id"),
        Index("ix_private_messages_created", "created_at"),
        Index("ix_private_messages_chat", "from_player_id", "to_player_id"),
        {"comment": "私聊消息表"},
    )

    from_player_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="发送者ID",
    )

    to_player_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="接收者ID",
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="消息内容",
    )

    message_type: Mapped[str] = mapped_column(
        String(20),
        default="text",
        nullable=False,
        comment="消息类型",
    )

    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否已读",
    )

    def __repr__(self) -> str:
        return f"<PrivateMessageDB(from='{self.from_player_id}', to='{self.to_player_id}')>"

    def mark_read(self) -> None:
        """标记为已读"""
        self.is_read = True


class TeamDB(Base, IdMixin, TimestampMixin):
    """
    组队数据模型

    存储临时队伍信息。

    Attributes:
        id: 主键ID
        team_id: 队伍唯一ID
        leader_id: 队长ID
        members: 成员列表 (JSON)
        max_members: 最大成员数
        status: 队伍状态 (waiting/playing/disbanded)
    """

    __tablename__ = "teams"
    __table_args__ = (
        Index("ix_teams_team_id", "team_id", unique=True),
        Index("ix_teams_leader_id", "leader_id"),
        Index("ix_teams_status", "status"),
        {"comment": "组队表"},
    )

    team_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        comment="队伍ID",
    )

    leader_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="队长ID",
    )

    members: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="成员列表",
    )

    max_members: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False,
        comment="最大成员数",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="waiting",
        nullable=False,
        comment="队伍状态",
    )

    def __repr__(self) -> str:
        return f"<TeamDB(team_id='{self.team_id}', leader='{self.leader_id}')>"

    @property
    def member_list(self) -> list:
        """获取成员列表"""
        return self.members.get("members", []) if self.members else []

    def set_members(self, members: list) -> None:
        """设置成员列表"""
        self.members = {"members": members}
