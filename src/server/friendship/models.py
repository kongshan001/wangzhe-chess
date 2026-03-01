"""
王者之奕 - 好友系统数据模型

本模块定义好友系统的核心数据类：
- FriendRelation: 好友关系类型
- FriendStatus: 好友在线状态
- Friend: 好友信息
- FriendRequest: 好友请求
- PrivateMessage: 私聊消息

用于存储和管理好友相关的数据。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class FriendRelation(StrEnum):
    """好友关系类型枚举"""

    FRIEND = "friend"  # 正常好友
    BLOCKED = "blocked"  # 黑名单（对方被拉黑）
    BLOCKED_BY = "blocked_by"  # 被对方拉黑


class FriendStatus(StrEnum):
    """好友在线状态枚举"""

    ONLINE = "online"  # 在线
    OFFLINE = "offline"  # 离线
    IN_GAME = "in_game"  # 游戏中
    IN_QUEUE = "in_queue"  # 匹配中
    IN_ROOM = "in_room"  # 房间中（等待开始）


class FriendRequestStatus(StrEnum):
    """好友请求状态枚举"""

    PENDING = "pending"  # 等待处理
    ACCEPTED = "accepted"  # 已接受
    REJECTED = "rejected"  # 已拒绝
    EXPIRED = "expired"  # 已过期


@dataclass
class FriendInfo:
    """
    好友信息

    存储好友的基本信息和状态。

    Attributes:
        player_id: 玩家ID
        nickname: 昵称
        avatar: 头像URL
        status: 在线状态
        tier: 当前段位
        stars: 星数
        relation: 关系类型
        last_online_at: 最后在线时间
        in_game_info: 游戏中信息（如果游戏中）
    """

    player_id: str
    nickname: str = ""
    avatar: str = ""
    status: FriendStatus = FriendStatus.OFFLINE
    tier: str = "bronze"
    stars: int = 0
    relation: FriendRelation = FriendRelation.FRIEND
    last_online_at: datetime | None = None
    in_game_info: dict[str, Any] | None = None

    @property
    def is_online(self) -> bool:
        """是否在线"""
        return self.status != FriendStatus.OFFLINE

    @property
    def is_in_game(self) -> bool:
        """是否游戏中"""
        return self.status == FriendStatus.IN_GAME

    @property
    def display_status(self) -> str:
        """显示状态文本"""
        status_texts = {
            FriendStatus.ONLINE: "在线",
            FriendStatus.OFFLINE: "离线",
            FriendStatus.IN_GAME: "游戏中",
            FriendStatus.IN_QUEUE: "匹配中",
            FriendStatus.IN_ROOM: "房间中",
        }
        return status_texts.get(self.status, "离线")

    @property
    def display_rank(self) -> str:
        """显示段位"""
        return f"{self.tier} {self.stars}星"

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "player_id": self.player_id,
            "nickname": self.nickname,
            "avatar": self.avatar,
            "status": self.status.value,
            "status_text": self.display_status,
            "tier": self.tier,
            "stars": self.stars,
            "display_rank": self.display_rank,
            "relation": self.relation.value,
            "last_online_at": self.last_online_at.isoformat() if self.last_online_at else None,
            "is_online": self.is_online,
            "in_game_info": self.in_game_info,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FriendInfo:
        """从字典创建"""
        status = data.get("status", "offline")
        if isinstance(status, str):
            status = FriendStatus(status)

        relation = data.get("relation", "friend")
        if isinstance(relation, str):
            relation = FriendRelation(relation)

        last_online_at = data.get("last_online_at")
        if last_online_at and isinstance(last_online_at, str):
            last_online_at = datetime.fromisoformat(last_online_at)

        return cls(
            player_id=data["player_id"],
            nickname=data.get("nickname", ""),
            avatar=data.get("avatar", ""),
            status=status,
            tier=data.get("tier", "bronze"),
            stars=data.get("stars", 0),
            relation=relation,
            last_online_at=last_online_at,
            in_game_info=data.get("in_game_info"),
        )


@dataclass
class FriendRequest:
    """
    好友请求

    存储好友请求信息。

    Attributes:
        request_id: 请求唯一ID
        from_player_id: 发送者ID
        to_player_id: 接收者ID
        status: 请求状态
        message: 附带消息
        created_at: 创建时间
        updated_at: 更新时间
        expires_at: 过期时间
    """

    request_id: str
    from_player_id: str
    to_player_id: str
    status: FriendRequestStatus = FriendRequestStatus.PENDING
    message: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None
    expires_at: datetime | None = None

    def __post_init__(self):
        """初始化时间"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.expires_at is None:
            # 默认7天过期
            from datetime import timedelta

            self.expires_at = self.created_at + timedelta(days=7)

    @property
    def is_pending(self) -> bool:
        """是否待处理"""
        return self.status == FriendRequestStatus.PENDING

    @property
    def is_expired(self) -> bool:
        """是否已过期"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    @property
    def can_accept(self) -> bool:
        """是否可以接受"""
        return self.is_pending and not self.is_expired

    def accept(self) -> bool:
        """接受请求"""
        if not self.can_accept:
            return False
        self.status = FriendRequestStatus.ACCEPTED
        self.updated_at = datetime.now()
        return True

    def reject(self) -> bool:
        """拒绝请求"""
        if not self.is_pending:
            return False
        self.status = FriendRequestStatus.REJECTED
        self.updated_at = datetime.now()
        return True

    def expire(self) -> None:
        """标记为过期"""
        self.status = FriendRequestStatus.EXPIRED
        self.updated_at = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "request_id": self.request_id,
            "from_player_id": self.from_player_id,
            "to_player_id": self.to_player_id,
            "status": self.status.value,
            "message": self.message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_pending": self.is_pending,
            "is_expired": self.is_expired,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FriendRequest:
        """从字典创建"""
        status = data.get("status", "pending")
        if isinstance(status, str):
            status = FriendRequestStatus(status)

        created_at = data.get("created_at")
        if created_at and isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        updated_at = data.get("updated_at")
        if updated_at and isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)

        expires_at = data.get("expires_at")
        if expires_at and isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at)

        return cls(
            request_id=data["request_id"],
            from_player_id=data["from_player_id"],
            to_player_id=data["to_player_id"],
            status=status,
            message=data.get("message", ""),
            created_at=created_at,
            updated_at=updated_at,
            expires_at=expires_at,
        )


@dataclass
class PrivateMessage:
    """
    私聊消息

    存储玩家之间的私聊消息。

    Attributes:
        message_id: 消息唯一ID
        from_player_id: 发送者ID
        to_player_id: 接收者ID
        content: 消息内容
        message_type: 消息类型 (text/emoji/system)
        is_read: 是否已读
        created_at: 创建时间
    """

    message_id: str
    from_player_id: str
    to_player_id: str
    content: str
    message_type: str = "text"
    is_read: bool = False
    created_at: datetime | None = None

    def __post_init__(self):
        """初始化时间"""
        if self.created_at is None:
            self.created_at = datetime.now()

    def mark_read(self) -> None:
        """标记为已读"""
        self.is_read = True

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "message_id": self.message_id,
            "from_player_id": self.from_player_id,
            "to_player_id": self.to_player_id,
            "content": self.content,
            "message_type": self.message_type,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PrivateMessage:
        """从字典创建"""
        created_at = data.get("created_at")
        if created_at and isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        return cls(
            message_id=data["message_id"],
            from_player_id=data["from_player_id"],
            to_player_id=data["to_player_id"],
            content=data["content"],
            message_type=data.get("message_type", "text"),
            is_read=data.get("is_read", False),
            created_at=created_at,
        )


@dataclass
class BlockedPlayer:
    """
    黑名单玩家

    存储被拉黑的玩家信息。

    Attributes:
        player_id: 被拉黑的玩家ID
        blocked_by: 拉黑者ID
        reason: 拉黑原因（可选）
        created_at: 拉黑时间
    """

    player_id: str
    blocked_by: str
    reason: str = ""
    created_at: datetime | None = None

    def __post_init__(self):
        """初始化时间"""
        if self.created_at is None:
            self.created_at = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "player_id": self.player_id,
            "blocked_by": self.blocked_by,
            "reason": self.reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BlockedPlayer:
        """从字典创建"""
        created_at = data.get("created_at")
        if created_at and isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        return cls(
            player_id=data["player_id"],
            blocked_by=data["blocked_by"],
            reason=data.get("reason", ""),
            created_at=created_at,
        )


@dataclass
class TeamInfo:
    """
    组队信息

    存储队伍信息。

    Attributes:
        team_id: 队伍ID
        leader_id: 队长ID
        members: 成员ID列表
        max_members: 最大成员数
        created_at: 创建时间
    """

    team_id: str
    leader_id: str
    members: list[str] = field(default_factory=list)
    max_members: int = 3
    created_at: datetime | None = None

    def __post_init__(self):
        """初始化"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.leader_id not in self.members:
            self.members.insert(0, self.leader_id)

    @property
    def is_full(self) -> bool:
        """队伍是否已满"""
        return len(self.members) >= self.max_members

    @property
    def member_count(self) -> int:
        """当前成员数"""
        return len(self.members)

    def is_member(self, player_id: str) -> bool:
        """检查是否为队伍成员"""
        return player_id in self.members

    def is_leader(self, player_id: str) -> bool:
        """检查是否为队长"""
        return player_id == self.leader_id

    def add_member(self, player_id: str) -> bool:
        """添加成员"""
        if self.is_full or self.is_member(player_id):
            return False
        self.members.append(player_id)
        return True

    def remove_member(self, player_id: str) -> bool:
        """移除成员"""
        if player_id == self.leader_id:
            return False  # 队长不能离开，只能解散队伍
        if player_id in self.members:
            self.members.remove(player_id)
            return True
        return False

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "team_id": self.team_id,
            "leader_id": self.leader_id,
            "members": self.members,
            "member_count": self.member_count,
            "max_members": self.max_members,
            "is_full": self.is_full,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TeamInfo:
        """从字典创建"""
        created_at = data.get("created_at")
        if created_at and isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        return cls(
            team_id=data["team_id"],
            leader_id=data["leader_id"],
            members=data.get("members", []),
            max_members=data.get("max_members", 3),
            created_at=created_at,
        )


# 消息数据类型（用于WebSocket）
class FriendRequestData:
    """好友请求数据（用于WebSocket消息）"""

    @staticmethod
    def from_request(
        request: FriendRequest, from_nickname: str = "", from_avatar: str = ""
    ) -> dict[str, Any]:
        """从FriendRequest创建消息数据"""
        return {
            "request_id": request.request_id,
            "from_player_id": request.from_player_id,
            "to_player_id": request.to_player_id,
            "from_nickname": from_nickname,
            "from_avatar": from_avatar,
            "message": request.message,
            "created_at": request.created_at.isoformat() if request.created_at else None,
        }


class PrivateMessageData:
    """私聊消息数据（用于WebSocket消息）"""

    @staticmethod
    def from_message(
        msg: PrivateMessage, from_nickname: str = "", from_avatar: str = ""
    ) -> dict[str, Any]:
        """从PrivateMessage创建消息数据"""
        return {
            "message_id": msg.message_id,
            "from_player_id": msg.from_player_id,
            "to_player_id": msg.to_player_id,
            "from_nickname": from_nickname,
            "from_avatar": from_avatar,
            "content": msg.content,
            "message_type": msg.message_type,
            "created_at": msg.created_at.isoformat() if msg.created_at else None,
        }
