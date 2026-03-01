"""
王者之奕 - 自定义房间数据模型

本模块实现自定义房间系统的数据类：
- RoomSettings: 房间设置（特殊规则）
- RoomPlayer: 房间内玩家数据
- CustomRoom: 自定义房间

根据需求 #16 实现特殊规则支持：
- 随机英雄池
- 固定费用英雄
- 双倍经济
- 快速模式
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class CustomRoomState(StrEnum):
    """
    自定义房间状态枚举

    - WAITING: 等待玩家加入
    - READY: 所有人准备，可以开始
    - PLAYING: 游戏进行中
    - FINISHED: 游戏已结束
    """

    WAITING = "waiting"
    READY = "ready"
    PLAYING = "playing"
    FINISHED = "finished"


class RoomPlayerState(StrEnum):
    """
    房间内玩家状态

    - NOT_READY: 未准备
    - READY: 已准备
    - PLAYING: 游戏中
    - DISCONNECTED: 断开连接
    - ELIMINATED: 已淘汰
    """

    NOT_READY = "not_ready"
    READY = "ready"
    PLAYING = "playing"
    DISCONNECTED = "disconnected"
    ELIMINATED = "eliminated"


class SpecialRuleType(StrEnum):
    """
    特殊规则类型枚举

    根据需求 #16 定义的规则：
    - RANDOM_POOL: 随机英雄池
    - FIXED_COST: 固定费用英雄
    - DOUBLE_ECONOMY: 双倍经济
    - FAST_MODE: 快速模式
    """

    RANDOM_POOL = "random_pool"  # 随机英雄池
    FIXED_COST = "fixed_cost"  # 固定费用英雄
    DOUBLE_ECONOMY = "double_economy"  # 双倍经济
    FAST_MODE = "fast_mode"  # 快速模式


@dataclass
class RoomSettings:
    """
    房间设置

    包含房间的所有配置选项和特殊规则。

    Attributes:
        max_players: 最大玩家数 (2-8)
        password: 房间密码（可选）
        special_rules: 启用的特殊规则列表
        round_time: 回合时间（秒）
        prepare_time: 准备时间（秒）
        starting_gold: 初始金币
        starting_hp: 初始生命值
        random_pool_size: 随机英雄池大小（仅在 RANDOM_POOL 规则下生效）
        fixed_cost: 固定费用（仅在 FIXED_COST 规则下生效）
        ai_fill: 是否允许 AI 填充空位
        ai_fill_delay: AI 填充延迟（秒）
    """

    max_players: int = 8
    password: str | None = None
    special_rules: list[SpecialRuleType] = field(default_factory=list)

    # 时间配置
    round_time: int = 30  # 回合时间（秒）
    prepare_time: int = 30  # 准备时间（秒）

    # 游戏配置
    starting_gold: int = 10
    starting_hp: int = 100

    # 特殊规则参数
    random_pool_size: int = 30  # 随机英雄池大小
    fixed_cost: int = 3  # 固定费用

    # AI 填充配置
    ai_fill: bool = True
    ai_fill_delay: int = 30  # AI 填充延迟（秒）

    def __post_init__(self):
        """验证设置参数"""
        # 限制玩家数量
        if not 2 <= self.max_players <= 8:
            raise ValueError("玩家数量必须在 2-8 之间")

        # 快速模式调整
        if SpecialRuleType.FAST_MODE in self.special_rules:
            self.round_time = 15
            self.prepare_time = 15

        # 双倍经济调整
        if SpecialRuleType.DOUBLE_ECONOMY in self.special_rules:
            self.starting_gold *= 2

    def has_rule(self, rule: SpecialRuleType) -> bool:
        """检查是否启用了指定规则"""
        return rule in self.special_rules

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "max_players": self.max_players,
            "has_password": self.password is not None,
            "special_rules": [r.value for r in self.special_rules],
            "round_time": self.round_time,
            "prepare_time": self.prepare_time,
            "starting_gold": self.starting_gold,
            "starting_hp": self.starting_hp,
            "random_pool_size": self.random_pool_size,
            "fixed_cost": self.fixed_cost,
            "ai_fill": self.ai_fill,
            "ai_fill_delay": self.ai_fill_delay,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RoomSettings:
        """从字典创建"""
        special_rules = [SpecialRuleType(r) for r in data.get("special_rules", [])]
        return cls(
            max_players=data.get("max_players", 8),
            password=data.get("password"),
            special_rules=special_rules,
            round_time=data.get("round_time", 30),
            prepare_time=data.get("prepare_time", 30),
            starting_gold=data.get("starting_gold", 10),
            starting_hp=data.get("starting_hp", 100),
            random_pool_size=data.get("random_pool_size", 30),
            fixed_cost=data.get("fixed_cost", 3),
            ai_fill=data.get("ai_fill", True),
            ai_fill_delay=data.get("ai_fill_delay", 30),
        )


@dataclass
class RoomPlayer:
    """
    房间内玩家数据

    存储玩家在自定义房间中的状态。

    Attributes:
        player_id: 玩家ID
        nickname: 玩家昵称
        avatar: 头像URL
        slot: 房间内位置 (0-7)
        state: 玩家状态
        is_host: 是否是房主
        is_ai: 是否是 AI
        joined_at: 加入时间
        ready_at: 准备时间
    """

    player_id: str
    nickname: str
    avatar: str | None = None
    slot: int = 0
    state: RoomPlayerState = RoomPlayerState.NOT_READY
    is_host: bool = False
    is_ai: bool = False
    joined_at: datetime = field(default_factory=datetime.now)
    ready_at: datetime | None = None

    @property
    def is_ready(self) -> bool:
        """检查玩家是否已准备"""
        return self.state == RoomPlayerState.READY

    @property
    def is_connected(self) -> bool:
        """检查玩家是否在线"""
        return self.state not in [
            RoomPlayerState.DISCONNECTED,
            RoomPlayerState.ELIMINATED,
        ]

    def set_ready(self, ready: bool = True) -> None:
        """设置准备状态"""
        if ready:
            self.state = RoomPlayerState.READY
            self.ready_at = datetime.now()
        else:
            self.state = RoomPlayerState.NOT_READY
            self.ready_at = None

    def set_playing(self) -> None:
        """设置为游戏中状态"""
        self.state = RoomPlayerState.PLAYING

    def set_disconnected(self) -> None:
        """设置为断开连接状态"""
        self.state = RoomPlayerState.DISCONNECTED

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "player_id": self.player_id,
            "nickname": self.nickname,
            "avatar": self.avatar,
            "slot": self.slot,
            "state": self.state.value,
            "is_host": self.is_host,
            "is_ai": self.is_ai,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "ready_at": self.ready_at.isoformat() if self.ready_at else None,
        }


@dataclass
class CustomRoom:
    """
    自定义房间

    管理自定义房间的完整状态。

    Attributes:
        room_id: 房间唯一ID
        name: 房间名称
        host_id: 房主ID
        settings: 房间设置
        players: 玩家列表
        state: 房间状态
        created_at: 创建时间
        game_started_at: 游戏开始时间
        game_ended_at: 游戏结束时间
    """

    room_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    host_id: str | None = None
    settings: RoomSettings = field(default_factory=RoomSettings)
    players: dict[str, RoomPlayer] = field(default_factory=dict)
    state: CustomRoomState = CustomRoomState.WAITING
    created_at: datetime = field(default_factory=datetime.now)
    game_started_at: datetime | None = None
    game_ended_at: datetime | None = None

    # 随机英雄池（仅在 RANDOM_POOL 规则下使用）
    random_hero_pool: list[str] = field(default_factory=list)

    def __post_init__(self):
        """初始化房间名"""
        if not self.name:
            self.name = f"房间-{self.room_id}"

    # ========================================================================
    # 属性访问
    # ========================================================================

    @property
    def player_count(self) -> int:
        """当前玩家数量"""
        return len(self.players)

    @property
    def human_count(self) -> int:
        """真人玩家数量（排除AI）"""
        return sum(1 for p in self.players.values() if not p.is_ai)

    @property
    def ai_count(self) -> int:
        """AI 玩家数量"""
        return sum(1 for p in self.players.values() if p.is_ai)

    @property
    def ready_count(self) -> int:
        """已准备玩家数量"""
        return sum(1 for p in self.players.values() if p.is_ready)

    @property
    def is_full(self) -> bool:
        """房间是否已满"""
        return self.player_count >= self.settings.max_players

    @property
    def is_empty(self) -> bool:
        """房间是否为空"""
        return self.player_count == 0

    @property
    def has_password(self) -> bool:
        """房间是否有密码"""
        return self.settings.password is not None

    @property
    def can_start(self) -> bool:
        """检查是否可以开始游戏"""
        # 至少2人，所有真人玩家已准备
        human_players = [p for p in self.players.values() if not p.is_ai]
        if len(human_players) < 1:
            return False

        all_ready = all(p.is_ready for p in human_players)
        return all_ready and self.player_count >= 2 and self.state == CustomRoomState.WAITING

    # ========================================================================
    # 玩家管理
    # ========================================================================

    def get_available_slot(self) -> int | None:
        """获取可用位置"""
        used_slots = {p.slot for p in self.players.values()}
        for i in range(self.settings.max_players):
            if i not in used_slots:
                return i
        return None

    def add_player(
        self,
        player_id: str,
        nickname: str,
        avatar: str | None = None,
        slot: int | None = None,
        is_ai: bool = False,
    ) -> RoomPlayer | None:
        """
        添加玩家到房间

        Args:
            player_id: 玩家ID
            nickname: 玩家昵称
            avatar: 头像URL
            slot: 指定位置（可选）
            is_ai: 是否是AI

        Returns:
            玩家实例，失败返回None
        """
        # 检查是否已在房间
        if player_id in self.players:
            return None

        # 检查房间状态
        if self.state != CustomRoomState.WAITING:
            return None

        # 检查房间是否已满
        if self.is_full:
            return None

        # 分配位置
        if slot is None:
            slot = self.get_available_slot()
            if slot is None:
                return None

        # 创建玩家
        player = RoomPlayer(
            player_id=player_id,
            nickname=nickname,
            avatar=avatar,
            slot=slot,
            is_ai=is_ai,
            is_host=(self.host_id == player_id),
        )

        self.players[player_id] = player

        # 如果是第一个玩家且没有房主，设为房主
        if self.host_id is None and not is_ai:
            self.host_id = player_id
            player.is_host = True

        return player

    def remove_player(self, player_id: str) -> RoomPlayer | None:
        """
        从房间移除玩家

        Args:
            player_id: 玩家ID

        Returns:
            被移除的玩家，不存在返回None
        """
        player = self.players.pop(player_id, None)
        if player is None:
            return None

        # 如果是房主离开，转让房主
        if player.is_host and self.players:
            # 优先选择真人玩家
            new_host = None
            for p in self.players.values():
                if not p.is_ai:
                    new_host = p
                    break

            # 如果没有真人，选择第一个AI
            if new_host is None and self.players:
                new_host = next(iter(self.players.values()))

            if new_host:
                new_host.is_host = True
                self.host_id = new_host.player_id

        return player

    def get_player(self, player_id: str) -> RoomPlayer | None:
        """获取玩家"""
        return self.players.get(player_id)

    def get_player_by_slot(self, slot: int) -> RoomPlayer | None:
        """根据位置获取玩家"""
        for player in self.players.values():
            if player.slot == slot:
                return player
        return None

    def set_player_ready(self, player_id: str, ready: bool = True) -> bool:
        """
        设置玩家准备状态

        Args:
            player_id: 玩家ID
            ready: 是否准备

        Returns:
            是否成功
        """
        player = self.players.get(player_id)
        if player is None or player.is_ai:
            return False

        player.set_ready(ready)
        return True

    # ========================================================================
    # AI 填充
    # ========================================================================

    def get_empty_slots(self) -> list[int]:
        """获取空位置列表"""
        used_slots = {p.slot for p in self.players.values()}
        return [i for i in range(self.settings.max_players) if i not in used_slots]

    def fill_with_ai(self, count: int | None = None) -> list[RoomPlayer]:
        """
        用 AI 填充空位

        Args:
            count: 填充数量（None 表示填满）

        Returns:
            添加的 AI 玩家列表
        """
        empty_slots = self.get_empty_slots()
        if count is not None:
            empty_slots = empty_slots[:count]

        added_players = []
        for i, slot in enumerate(empty_slots):
            ai_id = f"ai_{self.room_id}_{i}"
            ai_name = f"AI-{i + 1}"

            player = self.add_player(
                player_id=ai_id,
                nickname=ai_name,
                slot=slot,
                is_ai=True,
            )

            if player:
                # AI 自动准备
                player.set_ready(True)
                added_players.append(player)

        return added_players

    # ========================================================================
    # 游戏控制
    # ========================================================================

    def start_game(self) -> bool:
        """
        开始游戏

        Returns:
            是否成功开始
        """
        if not self.can_start:
            return False

        self.state = CustomRoomState.PLAYING
        self.game_started_at = datetime.now()

        # 所有玩家进入游戏中状态
        for player in self.players.values():
            player.set_playing()

        return True

    def end_game(self) -> None:
        """结束游戏"""
        self.state = CustomRoomState.FINISHED
        self.game_ended_at = datetime.now()

    # ========================================================================
    # 随机英雄池
    # ========================================================================

    def set_random_hero_pool(self, hero_ids: list[str]) -> None:
        """
        设置随机英雄池

        Args:
            hero_ids: 英雄ID列表
        """
        self.random_hero_pool = hero_ids

    def is_hero_available(self, hero_id: str) -> bool:
        """
        检查英雄是否可用（在随机池规则下）

        Args:
            hero_id: 英雄ID

        Returns:
            是否可用
        """
        if not self.settings.has_rule(SpecialRuleType.RANDOM_POOL):
            return True

        return hero_id in self.random_hero_pool

    # ========================================================================
    # 序列化
    # ========================================================================

    def to_dict(self, include_password: bool = False) -> dict[str, Any]:
        """
        转换为字典

        Args:
            include_password: 是否包含密码

        Returns:
            房间状态字典
        """
        result = {
            "room_id": self.room_id,
            "name": self.name,
            "host_id": self.host_id,
            "settings": self.settings.to_dict(),
            "players": [
                p.to_dict()
                for p in sorted(
                    self.players.values(),
                    key=lambda p: p.slot,
                )
            ],
            "state": self.state.value,
            "player_count": self.player_count,
            "human_count": self.human_count,
            "ai_count": self.ai_count,
            "created_at": self.created_at.isoformat(),
            "game_started_at": self.game_started_at.isoformat() if self.game_started_at else None,
            "game_ended_at": self.game_ended_at.isoformat() if self.game_ended_at else None,
        }

        if include_password and self.settings.password:
            result["password"] = self.settings.password

        return result

    def to_summary(self) -> dict[str, Any]:
        """
        转换为简要信息（用于房间列表）

        Returns:
            房间简要信息
        """
        return {
            "room_id": self.room_id,
            "name": self.name,
            "host_name": self.players[self.host_id].nickname
            if self.host_id and self.host_id in self.players
            else "未知",
            "player_count": self.player_count,
            "max_players": self.settings.max_players,
            "has_password": self.has_password,
            "state": self.state.value,
            "special_rules": [r.value for r in self.settings.special_rules],
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self) -> str:
        return (
            f"<CustomRoom(id={self.room_id}, name={self.name}, "
            f"players={self.player_count}/{self.settings.max_players}, "
            f"state={self.state.value})>"
        )
