"""
王者之奕 - 回放系统数据模型

本模块定义回放系统的核心数据类：
- ReplayFrame: 回放帧（单回合的状态快照）
- ReplaySnapshot: 玩家状态快照
- ReplayMetadata: 回放元数据
- Replay: 完整回放数据

用于回放功能的内存数据管理。
"""

from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ReplayStatus(str, Enum):
    """回放状态枚举"""

    IDLE = "idle"  # 空闲
    PLAYING = "playing"  # 播放中
    PAUSED = "paused"  # 暂停
    ENDED = "ended"  # 已结束


class PlaySpeed(float, Enum):
    """播放速度枚举"""

    SLOW = 0.5  # 慢速
    NORMAL = 1.0  # 正常
    FAST = 2.0  # 快速
    VERY_FAST = 4.0  # 超快


@dataclass
class PlayerSnapshot:
    """
    玩家状态快照

    存储某个玩家在特定时间点的状态。

    Attributes:
        player_id: 玩家ID
        nickname: 玩家昵称
        avatar: 头像
        tier: 段位
        hp: 血量
        gold: 金币
        level: 等级
        exp: 经验值
        board: 棋盘上的英雄
        bench: 备战席上的英雄
        synergies: 当前羁绊
        equipment: 装备信息
    """

    player_id: int
    nickname: str
    avatar: str | None = None
    tier: str | None = None
    hp: int = 100
    gold: int = 0
    level: int = 1
    exp: int = 0
    board: list[dict[str, Any]] = field(default_factory=list)
    bench: list[dict[str, Any]] = field(default_factory=list)
    synergies: dict[str, int] = field(default_factory=dict)
    equipment: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "player_id": self.player_id,
            "nickname": self.nickname,
            "avatar": self.avatar,
            "tier": self.tier,
            "hp": self.hp,
            "gold": self.gold,
            "level": self.level,
            "exp": self.exp,
            "board": self.board,
            "bench": self.bench,
            "synergies": self.synergies,
            "equipment": self.equipment,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PlayerSnapshot:
        """从字典创建"""
        return cls(
            player_id=data["player_id"],
            nickname=data["nickname"],
            avatar=data.get("avatar"),
            tier=data.get("tier"),
            hp=data.get("hp", 100),
            gold=data.get("gold", 0),
            level=data.get("level", 1),
            exp=data.get("exp", 0),
            board=data.get("board", []),
            bench=data.get("bench", []),
            synergies=data.get("synergies", {}),
            equipment=data.get("equipment", []),
        )


@dataclass
class ReplayFrame:
    """
    回放帧

    存储单个回合的完整状态快照。

    Attributes:
        round_num: 回合数
        phase: 阶段 (preparation/battle)
        timestamp: 时间戳（毫秒）
        player_snapshots: 所有玩家的状态快照
        shop_data: 商店数据（可选）
        battle_data: 战斗数据（可选）
        events: 本回合发生的事件列表
    """

    round_num: int
    phase: str
    timestamp: int = field(default_factory=lambda: int(time.time() * 1000))
    player_snapshots: dict[int, PlayerSnapshot] = field(default_factory=dict)
    shop_data: dict[str, Any] | None = None
    battle_data: dict[str, Any] | None = None
    events: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "round_num": self.round_num,
            "phase": self.phase,
            "timestamp": self.timestamp,
            "player_snapshots": {
                str(pid): snapshot.to_dict() for pid, snapshot in self.player_snapshots.items()
            },
            "shop_data": self.shop_data,
            "battle_data": self.battle_data,
            "events": self.events,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ReplayFrame:
        """从字典创建"""
        player_snapshots = {}
        for pid_str, snapshot_data in data.get("player_snapshots", {}).items():
            player_snapshots[int(pid_str)] = PlayerSnapshot.from_dict(snapshot_data)

        return cls(
            round_num=data["round_num"],
            phase=data["phase"],
            timestamp=data.get("timestamp", int(time.time() * 1000)),
            player_snapshots=player_snapshots,
            shop_data=data.get("shop_data"),
            battle_data=data.get("battle_data"),
            events=data.get("events", []),
        )


@dataclass
class ReplayMetadata:
    """
    回放元数据

    存储回放的基本信息。

    Attributes:
        match_id: 对局ID
        player_id: 回放所属玩家ID
        player_nickname: 玩家昵称
        final_rank: 最终排名
        total_rounds: 总回合数
        duration_seconds: 对局时长（秒）
        player_count: 参与人数
        created_at: 创建时间戳
        game_version: 游戏版本
        is_shared: 是否已分享
        share_code: 分享码
        tags: 标签（如"吃鸡"、"前四"等）
    """

    match_id: str
    player_id: int
    player_nickname: str
    final_rank: int = 0
    total_rounds: int = 0
    duration_seconds: int = 0
    player_count: int = 8
    created_at: int = field(default_factory=lambda: int(time.time() * 1000))
    game_version: str = "1.0.0"
    is_shared: bool = False
    share_code: str | None = None
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "match_id": self.match_id,
            "player_id": self.player_id,
            "player_nickname": self.player_nickname,
            "final_rank": self.final_rank,
            "total_rounds": self.total_rounds,
            "duration_seconds": self.duration_seconds,
            "player_count": self.player_count,
            "created_at": self.created_at,
            "game_version": self.game_version,
            "is_shared": self.is_shared,
            "share_code": self.share_code,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ReplayMetadata:
        """从字典创建"""
        return cls(
            match_id=data["match_id"],
            player_id=data["player_id"],
            player_nickname=data["player_nickname"],
            final_rank=data.get("final_rank", 0),
            total_rounds=data.get("total_rounds", 0),
            duration_seconds=data.get("duration_seconds", 0),
            player_count=data.get("player_count", 8),
            created_at=data.get("created_at", int(time.time() * 1000)),
            game_version=data.get("game_version", "1.0.0"),
            is_shared=data.get("is_shared", False),
            share_code=data.get("share_code"),
            tags=data.get("tags", []),
        )


@dataclass
class Replay:
    """
    完整回放数据

    包含回放的所有帧和元数据。

    Attributes:
        replay_id: 回放ID
        metadata: 元数据
        frames: 帧列表
        initial_state: 初始状态（第一帧之前的状态）
        final_rankings: 最终排名列表
    """

    replay_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: ReplayMetadata | None = None
    frames: list[ReplayFrame] = field(default_factory=list)
    initial_state: dict[str, Any] | None = None
    final_rankings: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "replay_id": self.replay_id,
            "metadata": self.metadata.to_dict() if self.metadata else None,
            "frames": [frame.to_dict() for frame in self.frames],
            "initial_state": self.initial_state,
            "final_rankings": self.final_rankings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Replay:
        """从字典创建"""
        metadata = None
        if data.get("metadata"):
            metadata = ReplayMetadata.from_dict(data["metadata"])

        frames = []
        for frame_data in data.get("frames", []):
            frames.append(ReplayFrame.from_dict(frame_data))

        return cls(
            replay_id=data.get("replay_id", str(uuid.uuid4())),
            metadata=metadata,
            frames=frames,
            initial_state=data.get("initial_state"),
            final_rankings=data.get("final_rankings", []),
        )

    def get_frame_count(self) -> int:
        """获取帧数"""
        return len(self.frames)

    def get_frame(self, round_num: int) -> ReplayFrame | None:
        """
        获取指定回合的帧

        Args:
            round_num: 回合数

        Returns:
            帧数据，如果不存在则返回 None
        """
        for frame in self.frames:
            if frame.round_num == round_num:
                return frame
        return None

    def get_duration_minutes(self) -> float:
        """获取回放时长（分钟）"""
        if self.metadata:
            return self.metadata.duration_seconds / 60
        return 0.0

    def compute_data_hash(self) -> str:
        """
        计算回放数据的哈希值

        用于验证数据完整性。

        Returns:
            SHA256 哈希值
        """
        import json

        data_str = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]


@dataclass
class ReplaySession:
    """
    回放播放会话

    管理回放播放状态。

    Attributes:
        session_id: 会话ID
        replay_id: 回放ID
        current_frame_index: 当前帧索引
        status: 播放状态
        speed: 播放速度
        started_at: 开始播放时间
        last_update_time: 最后更新时间
        current_round: 当前回合
    """

    session_id: str
    replay_id: str
    current_frame_index: int = 0
    status: ReplayStatus = ReplayStatus.IDLE
    speed: PlaySpeed = PlaySpeed.NORMAL
    started_at: int = field(default_factory=lambda: int(time.time() * 1000))
    last_update_time: int = field(default_factory=lambda: int(time.time() * 1000))
    current_round: int = 1

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "replay_id": self.replay_id,
            "current_frame_index": self.current_frame_index,
            "status": self.status.value,
            "speed": self.speed.value,
            "started_at": self.started_at,
            "last_update_time": self.last_update_time,
            "current_round": self.current_round,
        }

    def play(self) -> None:
        """开始/继续播放"""
        self.status = ReplayStatus.PLAYING
        self.last_update_time = int(time.time() * 1000)

    def pause(self) -> None:
        """暂停播放"""
        self.status = ReplayStatus.PAUSED
        self.last_update_time = int(time.time() * 1000)

    def stop(self) -> None:
        """停止播放"""
        self.status = ReplayStatus.ENDED
        self.current_frame_index = 0
        self.last_update_time = int(time.time() * 1000)

    def set_speed(self, speed: PlaySpeed) -> None:
        """设置播放速度"""
        self.speed = speed
        self.last_update_time = int(time.time() * 1000)

    def seek_to_frame(self, frame_index: int) -> None:
        """跳转到指定帧"""
        self.current_frame_index = max(0, frame_index)
        self.last_update_time = int(time.time() * 1000)

    def seek_to_round(self, round_num: int, total_frames: int) -> None:
        """跳转到指定回合"""
        # 找到对应的帧索引
        # 这里假设帧索引与回合数对应
        self.current_round = round_num
        self.current_frame_index = min(round_num - 1, total_frames - 1)
        self.current_frame_index = max(0, self.current_frame_index)
        self.last_update_time = int(time.time() * 1000)

    def advance_frame(self, total_frames: int) -> bool:
        """
        前进一帧

        Args:
            total_frames: 总帧数

        Returns:
            是否成功前进
        """
        if self.current_frame_index < total_frames - 1:
            self.current_frame_index += 1
            self.current_round = self.current_frame_index + 1
            self.last_update_time = int(time.time() * 1000)
            return True
        else:
            self.status = ReplayStatus.ENDED
            return False


@dataclass
class ReplayListItem:
    """
    回放列表项

    用于回放列表展示的简化数据。

    Attributes:
        replay_id: 回放ID
        match_id: 对局ID
        player_nickname: 玩家昵称
        final_rank: 最终排名
        total_rounds: 总回合数
        duration_seconds: 对局时长
        created_at: 创建时间
        is_shared: 是否已分享
        share_code: 分享码
    """

    replay_id: str
    match_id: str
    player_nickname: str
    final_rank: int = 0
    total_rounds: int = 0
    duration_seconds: int = 0
    created_at: int = 0
    is_shared: bool = False
    share_code: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "replay_id": self.replay_id,
            "match_id": self.match_id,
            "player_nickname": self.player_nickname,
            "final_rank": self.final_rank,
            "total_rounds": self.total_rounds,
            "duration_seconds": self.duration_seconds,
            "duration_minutes": round(self.duration_seconds / 60, 1),
            "created_at": self.created_at,
            "is_shared": self.is_shared,
            "share_code": self.share_code,
        }

    @classmethod
    def from_replay(cls, replay: Replay) -> ReplayListItem:
        """从回放创建列表项"""
        metadata = replay.metadata or ReplayMetadata(
            match_id="",
            player_id=0,
            player_nickname="Unknown",
        )
        return cls(
            replay_id=replay.replay_id,
            match_id=metadata.match_id,
            player_nickname=metadata.player_nickname,
            final_rank=metadata.final_rank,
            total_rounds=metadata.total_rounds,
            duration_seconds=metadata.duration_seconds,
            created_at=metadata.created_at,
            is_shared=metadata.is_shared,
            share_code=metadata.share_code,
        )
