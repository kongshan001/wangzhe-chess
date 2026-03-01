"""
王者之奕 - 观战系统数据模型

本模块定义观战系统的核心数据类：
- SpectatorSession: 观战会话
- SpectatorData: 观战数据
- SpectatorChat: 观战弹幕/聊天
- SpectatorGameState: 观战游戏状态快照

用于观战功能的内存数据管理。
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class SpectatorStatus(StrEnum):
    """观战状态枚举"""

    WATCHING = "watching"  # 观战中
    PAUSED = "paused"  # 已暂停
    ENDED = "ended"  # 已结束


class GameVisibility(StrEnum):
    """对局可见性枚举"""

    PUBLIC = "public"  # 公开观战
    FRIENDS = "friends"  # 好友可见
    PRIVATE = "private"  # 私密（不可观战）


@dataclass
class SpectatorGameState:
    """
    观战游戏状态快照

    存储某个时间点的游戏状态，用于延迟同步。

    Attributes:
        snapshot_time: 快照时间戳（毫秒）
        game_id: 对局ID
        round_num: 当前回合
        phase: 当前阶段 (preparation/battle)
        player_states: 所有玩家状态
        timestamp: 实际游戏时间戳（毫秒）
    """

    snapshot_time: int
    game_id: str
    round_num: int
    phase: str
    player_states: dict[str, Any]
    timestamp: int

    # 可选的详细状态
    shop_slots: dict[str, list[Any]] | None = None
    board_states: dict[str, Any] | None = None
    battle_state: dict[str, Any] | None = None
    synergy_states: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "snapshot_time": self.snapshot_time,
            "game_id": self.game_id,
            "round_num": self.round_num,
            "phase": self.phase,
            "player_states": self.player_states,
            "timestamp": self.timestamp,
            "shop_slots": self.shop_slots,
            "board_states": self.board_states,
            "battle_state": self.battle_state,
            "synergy_states": self.synergy_states,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SpectatorGameState:
        """从字典创建"""
        return cls(
            snapshot_time=data["snapshot_time"],
            game_id=data["game_id"],
            round_num=data["round_num"],
            phase=data["phase"],
            player_states=data["player_states"],
            timestamp=data["timestamp"],
            shop_slots=data.get("shop_slots"),
            board_states=data.get("board_states"),
            battle_state=data.get("battle_state"),
            synergy_states=data.get("synergy_states"),
        )


@dataclass
class SpectatorSession:
    """
    观战会话

    管理单个观众的观战状态。

    Attributes:
        session_id: 观战会话ID
        spectator_id: 观众玩家ID
        game_id: 观战的对局ID
        watching_player_id: 当前观看的玩家ID（可切换）
        status: 观战状态
        joined_at: 加入时间
        last_sync_time: 最后同步时间
        metadata: 额外元数据
    """

    session_id: str
    spectator_id: str
    game_id: str
    watching_player_id: str
    status: SpectatorStatus = SpectatorStatus.WATCHING
    joined_at: int = field(default_factory=lambda: int(time.time() * 1000))
    last_sync_time: int = field(default_factory=lambda: int(time.time() * 1000))
    metadata: dict[str, Any] = field(default_factory=dict)

    # 弹幕相关
    chat_enabled: bool = True
    muted_players: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "spectator_id": self.spectator_id,
            "game_id": self.game_id,
            "watching_player_id": self.watching_player_id,
            "status": self.status.value,
            "joined_at": self.joined_at,
            "last_sync_time": self.last_sync_time,
            "metadata": self.metadata,
            "chat_enabled": self.chat_enabled,
            "muted_players": self.muted_players,
        }

    def is_active(self) -> bool:
        """检查会话是否活跃"""
        return self.status == SpectatorStatus.WATCHING

    def update_sync_time(self) -> None:
        """更新最后同步时间"""
        self.last_sync_time = int(time.time() * 1000)

    def switch_player(self, player_id: str) -> None:
        """切换观看的玩家"""
        self.watching_player_id = player_id
        self.update_sync_time()


@dataclass
class SpectatorData:
    """
    观战数据

    管理单个对局的观战信息。

    Attributes:
        game_id: 对局ID
        visibility: 可见性
        spectators: 观众列表 (session_id -> SpectatorSession)
        state_history: 游戏状态历史（用于延迟同步）
        created_at: 创建时间
        max_spectators: 最大观众数
        delay_seconds: 延迟秒数（防作弊）
    """

    game_id: str
    visibility: GameVisibility = GameVisibility.PUBLIC
    spectators: dict[str, SpectatorSession] = field(default_factory=dict)
    state_history: list[SpectatorGameState] = field(default_factory=list)
    created_at: int = field(default_factory=lambda: int(time.time() * 1000))
    max_spectators: int = 100
    delay_seconds: int = 30  # 默认延迟30秒

    # 允许观战的玩家ID列表（用于好友观战）
    allowed_spectators: list[str] = field(default_factory=list)

    # 额外元数据（存储玩家信息、精选标记等）
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "game_id": self.game_id,
            "visibility": self.visibility.value,
            "spectators": {sid: session.to_dict() for sid, session in self.spectators.items()},
            "spectator_count": len(self.spectators),
            "created_at": self.created_at,
            "max_spectators": self.max_spectators,
            "delay_seconds": self.delay_seconds,
        }

    def add_spectator(self, session: SpectatorSession) -> bool:
        """
        添加观众

        Args:
            session: 观战会话

        Returns:
            是否成功
        """
        if len(self.spectators) >= self.max_spectators:
            return False

        # 检查权限
        if self.visibility == GameVisibility.PRIVATE:
            return False
        elif self.visibility == GameVisibility.FRIENDS:
            if session.spectator_id not in self.allowed_spectators:
                return False

        self.spectators[session.session_id] = session
        return True

    def remove_spectator(self, session_id: str) -> SpectatorSession | None:
        """
        移除观众

        Args:
            session_id: 观战会话ID

        Returns:
            被移除的会话
        """
        return self.spectators.pop(session_id, None)

    def get_spectator_count(self) -> int:
        """获取观众数量"""
        return len(self.spectators)

    def is_full(self) -> bool:
        """检查是否已满"""
        return len(self.spectators) >= self.max_spectators

    def push_state(self, state: SpectatorGameState) -> None:
        """
        推送新的游戏状态

        Args:
            state: 游戏状态快照
        """
        self.state_history.append(state)

        # 只保留最近5分钟的状态（用于延迟同步）
        cutoff_time = int(time.time() * 1000) - 5 * 60 * 1000
        self.state_history = [s for s in self.state_history if s.snapshot_time > cutoff_time]

    def get_delayed_state(self) -> SpectatorGameState | None:
        """
        获取延迟后的游戏状态

        Returns:
            延迟的游戏状态
        """
        if not self.state_history:
            return None

        # 计算目标时间
        target_time = int(time.time() * 1000) - self.delay_seconds * 1000

        # 查找最接近且不超过目标时间的状态
        delayed_state = None
        for state in self.state_history:
            if state.snapshot_time <= target_time:
                delayed_state = state
            else:
                break

        return delayed_state


@dataclass
class SpectatorChat:
    """
    观战弹幕/聊天消息

    观众可以发送弹幕与主播和其他观众互动。

    Attributes:
        chat_id: 聊天ID
        game_id: 对局ID
        sender_id: 发送者ID
        sender_name: 发送者昵称
        content: 消息内容
        sent_at: 发送时间
        message_type: 消息类型 (text/emoji/system)
    """

    chat_id: str
    game_id: str
    sender_id: str
    sender_name: str
    content: str
    sent_at: int = field(default_factory=lambda: int(time.time() * 1000))
    message_type: str = "text"  # text/emoji/system

    # 可选的额外信息
    avatar: str | None = None
    tier: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "chat_id": self.chat_id,
            "game_id": self.game_id,
            "sender_id": self.sender_id,
            "sender_name": self.sender_name,
            "content": self.content,
            "sent_at": self.sent_at,
            "message_type": self.message_type,
            "avatar": self.avatar,
            "tier": self.tier,
        }

    def is_valid(self) -> bool:
        """检查消息是否有效"""
        if not self.content or not self.content.strip():
            return False
        if len(self.content) > 200:  # 限制消息长度
            return False
        return True


@dataclass
class SpectatableGame:
    """
    可观战对局信息

    用于展示在观战列表中。

    Attributes:
        game_id: 对局ID
        players: 玩家列表信息
        created_at: 创建时间
        current_round: 当前回合
        spectator_count: 观众数量
        visibility: 可见性
    """

    game_id: str
    players: list[dict[str, Any]]
    created_at: int
    current_round: int = 0
    spectator_count: int = 0
    visibility: GameVisibility = GameVisibility.PUBLIC
    is_featured: bool = False  # 是否为精选对局

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "game_id": self.game_id,
            "players": self.players,
            "created_at": self.created_at,
            "current_round": self.current_round,
            "spectator_count": self.spectator_count,
            "visibility": self.visibility.value,
            "is_featured": self.is_featured,
        }
