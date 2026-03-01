"""
王者之奕 - 表情系统数据模型

本模块定义表情系统的核心数据类：
- EmoteCategory: 表情分类
- Emote: 表情定义
- PlayerEmote: 玩家拥有的表情
- EmoteHistory: 表情发送历史
- EmoteData: WebSocket消息数据

用于存储和管理表情相关的数据。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any


class EmoteCategory(StrEnum):
    """
    表情分类枚举

    定义表情的分类类型：
    - DEFAULT: 默认表情（免费）
    - UNLOCK: 解锁表情（需要达成条件）
    - PREMIUM: 高级表情（付费/活动）
    - SPECIAL: 特殊表情（限定）
    """

    DEFAULT = "default"  # 默认表情
    UNLOCK = "unlock"  # 解锁表情
    PREMIUM = "premium"  # 高级表情
    SPECIAL = "special"  # 特殊表情


class EmoteType(StrEnum):
    """
    表情类型枚举

    定义表情的展示类型：
    - STATIC: 静态表情
    - ANIMATED: 动态表情
    - SOUND: 带音效表情
    """

    STATIC = "static"  # 静态
    ANIMATED = "animated"  # 动态
    SOUND = "sound"  # 带音效


@dataclass
class Emote:
    """
    表情定义

    存储单个表情的配置信息。

    Attributes:
        emote_id: 表情唯一ID
        name: 表情名称
        description: 表情描述
        category: 表情分类
        emote_type: 表情类型
        asset_url: 表情资源URL
        thumbnail_url: 缩略图URL
        sound_url: 音效URL（可选）
        unlock_condition: 解锁条件（可选）
        is_free: 是否免费
        sort_order: 排序顺序
    """

    emote_id: str
    name: str
    description: str = ""
    category: EmoteCategory = EmoteCategory.DEFAULT
    emote_type: EmoteType = EmoteType.STATIC
    asset_url: str = ""
    thumbnail_url: str = ""
    sound_url: str | None = None
    unlock_condition: dict[str, Any] | None = None
    is_free: bool = True
    sort_order: int = 0

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "emote_id": self.emote_id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "emote_type": self.emote_type.value,
            "asset_url": self.asset_url,
            "thumbnail_url": self.thumbnail_url,
            "sound_url": self.sound_url,
            "unlock_condition": self.unlock_condition,
            "is_free": self.is_free,
            "sort_order": self.sort_order,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Emote:
        """从字典创建"""
        category = data.get("category", "default")
        if isinstance(category, str):
            category = EmoteCategory(category)

        emote_type = data.get("emote_type", "static")
        if isinstance(emote_type, str):
            emote_type = EmoteType(emote_type)

        return cls(
            emote_id=data["emote_id"],
            name=data.get("name", data["emote_id"]),
            description=data.get("description", ""),
            category=category,
            emote_type=emote_type,
            asset_url=data.get("asset_url", ""),
            thumbnail_url=data.get("thumbnail_url", ""),
            sound_url=data.get("sound_url"),
            unlock_condition=data.get("unlock_condition"),
            is_free=data.get("is_free", True),
            sort_order=data.get("sort_order", 0),
        )

    def check_unlock(self, player_stats: dict[str, Any]) -> bool:
        """
        检查玩家是否满足解锁条件

        Args:
            player_stats: 玩家统计数据

        Returns:
            是否满足解锁条件
        """
        if self.is_free:
            return True

        if not self.unlock_condition:
            return False

        condition_type = self.unlock_condition.get("type")

        if condition_type == "wins":
            # 需要胜利次数
            required = self.unlock_condition.get("count", 0)
            actual = player_stats.get("total_wins", 0)
            return actual >= required

        elif condition_type == "rank":
            # 需要达到段位
            required_tier = self.unlock_condition.get("tier", "bronze")
            tier_order = [
                "bronze",
                "silver",
                "gold",
                "platinum",
                "diamond",
                "master",
                "grandmaster",
            ]
            current_tier = player_stats.get("tier", "bronze")
            try:
                return tier_order.index(current_tier) >= tier_order.index(required_tier)
            except ValueError:
                return False

        elif condition_type == "achievement":
            # 需要达成成就
            achievement_id = self.unlock_condition.get("achievement_id")
            achievements = player_stats.get("achievements", [])
            return achievement_id in achievements

        elif condition_type == "level":
            # 需要玩家等级
            required = self.unlock_condition.get("level", 1)
            actual = player_stats.get("level", 1)
            return actual >= required

        elif condition_type == "premium":
            # 需要会员/付费
            return player_stats.get("is_premium", False)

        return False


@dataclass
class PlayerEmote:
    """
    玩家拥有的表情

    存储玩家对某个表情的拥有状态和快捷键配置。

    Attributes:
        player_id: 玩家ID
        emote_id: 表情ID
        unlocked_at: 解锁时间
        hotkey: 快捷键设置（可选，如 "1", "2", "ctrl+1" 等）
        use_count: 使用次数
    """

    player_id: str
    emote_id: str
    unlocked_at: datetime | None = None
    hotkey: str | None = None
    use_count: int = 0

    def __post_init__(self):
        """初始化时间"""
        if self.unlocked_at is None:
            self.unlocked_at = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "player_id": self.player_id,
            "emote_id": self.emote_id,
            "unlocked_at": self.unlocked_at.isoformat() if self.unlocked_at else None,
            "hotkey": self.hotkey,
            "use_count": self.use_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PlayerEmote:
        """从字典创建"""
        unlocked_at = data.get("unlocked_at")
        if unlocked_at and isinstance(unlocked_at, str):
            unlocked_at = datetime.fromisoformat(unlocked_at)

        return cls(
            player_id=data["player_id"],
            emote_id=data["emote_id"],
            unlocked_at=unlocked_at,
            hotkey=data.get("hotkey"),
            use_count=data.get("use_count", 0),
        )


@dataclass
class EmoteHistory:
    """
    表情发送历史

    存储表情发送记录。

    Attributes:
        history_id: 历史记录ID
        room_id: 房间ID
        from_player_id: 发送者ID
        to_player_id: 目标玩家ID（None表示发送给所有玩家）
        emote_id: 表情ID
        round_number: 回合数
        created_at: 发送时间
    """

    history_id: str
    room_id: str
    from_player_id: str
    emote_id: str
    to_player_id: str | None = None  # None = 发送给所有玩家
    round_number: int = 0
    created_at: datetime | None = None

    def __post_init__(self):
        """初始化时间"""
        if self.created_at is None:
            self.created_at = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "history_id": self.history_id,
            "room_id": self.room_id,
            "from_player_id": self.from_player_id,
            "to_player_id": self.to_player_id,
            "emote_id": self.emote_id,
            "round_number": self.round_number,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EmoteHistory:
        """从字典创建"""
        created_at = data.get("created_at")
        if created_at and isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        return cls(
            history_id=data["history_id"],
            room_id=data["room_id"],
            from_player_id=data["from_player_id"],
            to_player_id=data.get("to_player_id"),
            emote_id=data["emote_id"],
            round_number=data.get("round_number", 0),
            created_at=created_at,
        )


class EmoteData:
    """
    表情数据（用于WebSocket消息）

    提供表情发送时的消息数据格式化。
    """

    @staticmethod
    def from_emote(
        emote: Emote,
        from_player_id: str,
        from_nickname: str = "",
        to_player_id: str | None = None,
        room_id: str = "",
        round_number: int = 0,
    ) -> dict[str, Any]:
        """
        从Emote创建消息数据

        Args:
            emote: 表情对象
            from_player_id: 发送者ID
            from_nickname: 发送者昵称
            to_player_id: 目标玩家ID（None=所有玩家）
            room_id: 房间ID
            round_number: 回合数

        Returns:
            消息数据字典
        """
        return {
            "emote_id": emote.emote_id,
            "name": emote.name,
            "asset_url": emote.asset_url,
            "thumbnail_url": emote.thumbnail_url,
            "sound_url": emote.sound_url,
            "emote_type": emote.emote_type.value,
            "from_player_id": from_player_id,
            "from_nickname": from_nickname,
            "to_player_id": to_player_id,
            "room_id": room_id,
            "round_number": round_number,
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    def from_history(
        history: EmoteHistory,
        emote: Emote,
        from_nickname: str = "",
        to_nickname: str = "",
    ) -> dict[str, Any]:
        """
        从历史记录创建数据

        Args:
            history: 历史记录
            emote: 表情对象
            from_nickname: 发送者昵称
            to_nickname: 目标玩家昵称

        Returns:
            消息数据字典
        """
        return {
            "history_id": history.history_id,
            "emote_id": emote.emote_id,
            "name": emote.name,
            "asset_url": emote.asset_url,
            "thumbnail_url": emote.thumbnail_url,
            "from_player_id": history.from_player_id,
            "from_nickname": from_nickname,
            "to_player_id": history.to_player_id,
            "to_nickname": to_nickname,
            "room_id": history.room_id,
            "round_number": history.round_number,
            "created_at": history.created_at.isoformat() if history.created_at else None,
        }
