"""
王者之奕 - 对局记录模型

本模块定义对局相关的数据库模型：
- MatchRecord: 对局记录
- MatchPlayer: 对局玩家信息
- MatchSnapshot: 对局快照
- MatchReplay: 回放数据
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.mysql import JSON, LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .player import Player


class MatchStatus(str, PyEnum):
    """对局状态枚举"""
    WAITING = "waiting"       # 等待中
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"    # 已完成
    ABORTED = "aborted"        # 已中断


class MatchType(str, PyEnum):
    """对局类型枚举"""
    RANKED = "ranked"         # 排位赛
    CASUAL = "casual"         # 匹配赛
    CUSTOM = "custom"         # 自定义
    TOURNAMENT = "tournament"  # 锦标赛


class MatchRecord(BaseModel):
    """
    对局记录模型
    
    存储每局游戏的基本信息和结果。
    
    Attributes:
        id: 主键ID
        match_id: 对局唯一ID（业务ID）
        match_type: 对局类型
        status: 对局状态
        season_id: 赛季ID
        total_rounds: 总回合数
        duration_seconds: 对局时长（秒）
        started_at: 开始时间
        ended_at: 结束时间
        server_region: 服务器区域
        game_version: 游戏版本
        config_data: 配置数据（JSON）
        created_at: 创建时间
        updated_at: 更新时间
    """
    
    __tablename__ = "match_records"
    __table_args__ = (
        Index("ix_match_records_match_id", "match_id", unique=True),
        Index("ix_match_records_match_type", "match_type"),
        Index("ix_match_records_season_id", "season_id"),
        Index("ix_match_records_started_at", "started_at"),
        Index("ix_match_records_status", "status"),
        {"comment": "对局记录表"},
    )
    
    # 基本信息
    match_id: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        comment="对局唯一ID",
    )
    match_type: Mapped[str] = mapped_column(
        String(20),
        default=MatchType.RANKED.value,
        nullable=False,
        comment="对局类型",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default=MatchStatus.WAITING.value,
        nullable=False,
        comment="对局状态",
    )
    
    # 赛季信息
    season_id: Mapped[str] = mapped_column(
        String(20),
        default="S1",
        nullable=False,
        comment="赛季ID",
    )
    
    # 对局详情
    total_rounds: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总回合数",
    )
    duration_seconds: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="对局时长(秒)",
    )
    
    # 时间信息
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="开始时间",
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="结束时间",
    )
    
    # 其他信息
    server_region: Mapped[str] = mapped_column(
        String(10),
        default="cn",
        nullable=False,
        comment="服务器区域",
    )
    game_version: Mapped[str] = mapped_column(
        String(20),
        default="1.0.0",
        nullable=False,
        comment="游戏版本",
    )
    config_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        comment="配置数据",
    )
    
    # 关联关系
    players: Mapped[list[MatchPlayer]] = relationship(
        "MatchPlayer",
        back_populates="match",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    snapshots: Mapped[list[MatchSnapshot]] = relationship(
        "MatchSnapshot",
        back_populates="match",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    replay: Mapped[MatchReplay | None] = relationship(
        "MatchReplay",
        back_populates="match",
        uselist=False,
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    
    @property
    def duration_minutes(self) -> float:
        """获取对局时长（分钟）"""
        return round(self.duration_seconds / 60, 1)
    
    @property
    def is_completed(self) -> bool:
        """是否已完成"""
        return self.status == MatchStatus.COMPLETED.value


class MatchPlayer(BaseModel):
    """
    对局玩家模型
    
    存储每局游戏中玩家的详细信息。
    
    Attributes:
        id: 主键ID
        match_id: 对局记录ID（外键）
        player_id: 玩家ID（外键）
        final_rank: 最终排名
        final_hp: 最终血量
        is_winner: 是否获胜
        eliminated_round: 被淘汰回合（0表示未淘汰）
        total_damage_dealt: 总造成伤害
        total_damage_taken: 总受到伤害
        total_kills: 总击杀数
        total_gold_earned: 总获得金币
        total_shop_refreshes: 总刷新商店次数
        max_win_streak: 最大连胜
        max_lose_streak: 最大连败
        final_level: 最终等级
        final_synergies: 最终羁绊（JSON）
        heroes_used: 使用的英雄（JSON）
        rank_change: 段位变化
        point_change: 积分变化
        created_at: 创建时间
        updated_at: 更新时间
    """
    
    __tablename__ = "match_players"
    __table_args__ = (
        UniqueConstraint("match_id", "player_id", name="uq_match_player"),
        Index("ix_match_players_player_id", "player_id"),
        Index("ix_match_players_final_rank", "final_rank"),
        Index("ix_match_players_is_winner", "is_winner"),
        {"comment": "对局玩家表"},
    )
    
    # 关联信息
    match_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("match_records.id", ondelete="CASCADE"),
        nullable=False,
        comment="对局记录ID",
    )
    player_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
        comment="玩家ID",
    )
    
    # 排名信息
    final_rank: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="最终排名",
    )
    final_hp: Mapped[int] = mapped_column(
        Integer,
        default=100,
        nullable=False,
        comment="最终血量",
    )
    is_winner: Mapped[bool] = mapped_column(
        Integer,
        default=False,
        nullable=False,
        comment="是否获胜",
    )
    eliminated_round: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="被淘汰回合",
    )
    
    # 战斗统计
    total_damage_dealt: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总造成伤害",
    )
    total_damage_taken: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总受到伤害",
    )
    total_kills: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总击杀数",
    )
    
    # 经济统计
    total_gold_earned: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总获得金币",
    )
    total_shop_refreshes: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总刷新商店次数",
    )
    
    # 连胜/连败
    max_win_streak: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="最大连胜",
    )
    max_lose_streak: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="最大连败",
    )
    
    # 阵容信息
    final_level: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="最终等级",
    )
    final_synergies: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        comment="最终羁绊",
    )
    heroes_used: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        comment="使用的英雄",
    )
    
    # 段位变化
    rank_before: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="赛前段位",
    )
    rank_after: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="赛后段位",
    )
    point_change: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="积分变化",
    )
    
    # 关联关系
    match: Mapped[MatchRecord] = relationship(
        "MatchRecord",
        back_populates="players",
    )
    player: Mapped[Player] = relationship(
        "Player",
        foreign_keys=[player_id],
    )
    
    @property
    def is_top4(self) -> bool:
        """是否前四"""
        return self.final_rank <= 4


class MatchSnapshot(BaseModel):
    """
    对局快照模型
    
    存储对局过程中关键节点的状态快照。
    
    Attributes:
        id: 主键ID
        match_id: 对局记录ID（外键）
        round_number: 回合数
        snapshot_type: 快照类型
        player_states: 玩家状态快照（JSON）
        hero_pool_state: 英雄池状态（JSON）
        timestamp: 快照时间
        created_at: 创建时间
        updated_at: 更新时间
    """
    
    __tablename__ = "match_snapshots"
    __table_args__ = (
        Index("ix_match_snapshots_match_id", "match_id"),
        Index("ix_match_snapshots_round", "round_number"),
        {"comment": "对局快照表"},
    )
    
    match_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("match_records.id", ondelete="CASCADE"),
        nullable=False,
        comment="对局记录ID",
    )
    
    round_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="回合数",
    )
    snapshot_type: Mapped[str] = mapped_column(
        String(20),
        default="round_end",
        nullable=False,
        comment="快照类型",
    )
    
    player_states: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        comment="玩家状态快照",
    )
    hero_pool_state: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        comment="英雄池状态",
    )
    
    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        comment="快照时间",
    )
    
    # 关联关系
    match: Mapped[MatchRecord] = relationship(
        "MatchRecord",
        back_populates="snapshots",
    )


class MatchReplay(BaseModel):
    """
    对局回放模型
    
    存储完整的对局回放数据。
    
    Attributes:
        id: 主键ID
        match_id: 对局记录ID（外键）
        replay_data: 回放数据（JSON，压缩后存储）
        compressed: 是否压缩
        data_size: 数据大小（字节）
        valid_until: 有效期（过期后可清理）
        view_count: 观看次数
        created_at: 创建时间
        updated_at: 更新时间
    """
    
    __tablename__ = "match_replays"
    __table_args__ = (
        Index("ix_match_replays_match_id", "match_id", unique=True),
        Index("ix_match_replays_valid_until", "valid_until"),
        {"comment": "对局回放表"},
    )
    
    match_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("match_records.id", ondelete="CASCADE"),
        nullable=False,
        comment="对局记录ID",
    )
    
    replay_data: Mapped[str | None] = mapped_column(
        LONGTEXT,
        nullable=True,
        comment="回放数据(JSON)",
    )
    
    compressed: Mapped[bool] = mapped_column(
        Integer,
        default=False,
        nullable=False,
        comment="是否压缩",
    )
    data_size: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="数据大小(字节)",
    )
    
    valid_until: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="有效期",
    )
    view_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="观看次数",
    )
    
    # 关联关系
    match: Mapped[MatchRecord] = relationship(
        "MatchRecord",
        back_populates="replay",
    )


class BattleLog(BaseModel):
    """
    战斗日志模型
    
    存储每回合玩家之间的战斗日志。
    
    Attributes:
        id: 主键ID
        match_id: 对局记录ID（外键）
        round_number: 回合数
        attacker_id: 进攻方玩家ID
        defender_id: 防守方玩家ID
        winner_id: 获胜方玩家ID
        damage_dealt: 造成伤害
        attacker_survivors: 进攻方存活英雄数
        defender_survivors: 防守方存活英雄数
        battle_duration_ms: 战斗时长（毫秒）
        battle_events: 战斗事件（JSON）
        created_at: 创建时间
        updated_at: 更新时间
    """
    
    __tablename__ = "battle_logs"
    __table_args__ = (
        Index("ix_battle_logs_match_id", "match_id"),
        Index("ix_battle_logs_round", "round_number"),
        {"comment": "战斗日志表"},
    )
    
    match_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("match_records.id", ondelete="CASCADE"),
        nullable=False,
        comment="对局记录ID",
    )
    
    round_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="回合数",
    )
    
    attacker_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("players.id", ondelete="SET NULL"),
        nullable=True,
        comment="进攻方玩家ID",
    )
    defender_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("players.id", ondelete="SET NULL"),
        nullable=True,
        comment="防守方玩家ID",
    )
    winner_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("players.id", ondelete="SET NULL"),
        nullable=True,
        comment="获胜方玩家ID",
    )
    
    damage_dealt: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="造成伤害",
    )
    
    attacker_survivors: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="进攻方存活英雄数",
    )
    defender_survivors: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="防守方存活英雄数",
    )
    
    battle_duration_ms: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="战斗时长(毫秒)",
    )
    
    battle_events: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        comment="战斗事件",
    )
