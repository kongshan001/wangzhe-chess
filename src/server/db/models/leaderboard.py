"""
王者之奕 - 排行榜数据库模型

本模块定义排行榜系统的数据库持久化模型：
- LeaderboardDB: 排行榜数据
- LeaderboardRewardDB: 排行榜奖励记录
- PlayerLeaderboardStatsDB: 玩家排行榜统计

用于存储排行榜相关的持久化数据。
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from src.server.models.base import Base, IdMixin, TimestampMixin


class LeaderboardDB(Base, IdMixin, TimestampMixin):
    """
    排行榜数据模型
    
    存储排行榜快照数据，用于历史查询和数据持久化。
    
    Attributes:
        id: 主键ID
        leaderboard_type: 排行榜类型 (tier/win_rate/first_place/damage/wealth)
        period: 排行榜周期 (weekly/monthly/season)
        period_start: 周期开始时间
        period_end: 周期结束时间
        data: 排行榜数据 (JSON)
        total_count: 总参与人数
        is_final: 是否已结算
    """
    
    __tablename__ = "leaderboards"
    __table_args__ = (
        UniqueConstraint(
            "leaderboard_type", "period", "period_start",
            name="uq_leaderboard_type_period"
        ),
        Index("ix_leaderboards_type", "leaderboard_type"),
        Index("ix_leaderboards_period", "period"),
        Index("ix_leaderboards_period_start", "period_start"),
        {"comment": "排行榜数据表"},
    )
    
    leaderboard_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="排行榜类型",
    )
    
    period: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="排行榜周期",
    )
    
    period_start: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        comment="周期开始时间",
    )
    
    period_end: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        comment="周期结束时间",
    )
    
    data: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="排行榜数据",
    )
    
    total_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总参与人数",
    )
    
    is_final: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否已结算",
    )
    
    def __repr__(self) -> str:
        return f"<LeaderboardDB(type='{self.leaderboard_type}', period='{self.period}')>"


class LeaderboardRewardDB(Base, IdMixin, TimestampMixin):
    """
    排行榜奖励配置模型
    
    存储排行榜的奖励配置。
    
    Attributes:
        id: 主键ID
        leaderboard_type: 排行榜类型
        period: 排行榜周期
        rank_start: 起始排名
        rank_end: 结束排名
        gold: 金币奖励
        exp: 经验值奖励
        title: 称号奖励ID
        avatar_frame: 头像框ID
        items: 其他物品奖励 (JSON)
        is_active: 是否启用
    """
    
    __tablename__ = "leaderboard_rewards"
    __table_args__ = (
        Index("ix_leaderboard_rewards_type", "leaderboard_type"),
        Index("ix_leaderboard_rewards_period", "period"),
        Index("ix_leaderboard_rewards_rank", "rank_start", "rank_end"),
        {"comment": "排行榜奖励配置表"},
    )
    
    leaderboard_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="排行榜类型",
    )
    
    period: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="排行榜周期",
    )
    
    rank_start: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="起始排名",
    )
    
    rank_end: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="结束排名",
    )
    
    gold: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="金币奖励",
    )
    
    exp: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="经验值奖励",
    )
    
    title: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="称号奖励ID",
    )
    
    avatar_frame: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="头像框ID",
    )
    
    items: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="其他物品奖励",
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否启用",
    )
    
    def __repr__(self) -> str:
        return f"<LeaderboardRewardDB(type='{self.leaderboard_type}', rank={self.rank_start}-{self.rank_end})>"


class PlayerLeaderboardStatsDB(Base, IdMixin, TimestampMixin):
    """
    玩家排行榜统计数据模型
    
    存储玩家在各排行榜的统计数据。
    
    Attributes:
        id: 主键ID
        player_id: 玩家ID
        leaderboard_type: 排行榜类型
        period: 排行榜周期
        period_start: 周期开始时间
        rank: 当前排名
        score: 当前分数
        best_rank: 历史最佳排名
        rewards_claimed: 是否已领取奖励
        reward_claimed_at: 领取奖励时间
        extra_data: 额外数据 (JSON)
    """
    
    __tablename__ = "player_leaderboard_stats"
    __table_args__ = (
        UniqueConstraint(
            "player_id", "leaderboard_type", "period", "period_start",
            name="uq_player_leaderboard"
        ),
        Index("ix_player_leaderboard_stats_player", "player_id"),
        Index("ix_player_leaderboard_stats_type", "leaderboard_type"),
        Index("ix_player_leaderboard_stats_rank", "rank"),
        Index("ix_player_leaderboard_stats_score", "score"),
        {"comment": "玩家排行榜统计表"},
    )
    
    player_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="玩家ID",
    )
    
    leaderboard_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="排行榜类型",
    )
    
    period: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="排行榜周期",
    )
    
    period_start: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        comment="周期开始时间",
    )
    
    rank: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="当前排名",
    )
    
    score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="当前分数",
    )
    
    best_rank: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="历史最佳排名",
    )
    
    rewards_claimed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否已领取奖励",
    )
    
    reward_claimed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="领取奖励时间",
    )
    
    extra_data: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="额外数据",
    )
    
    def __repr__(self) -> str:
        return f"<PlayerLeaderboardStatsDB(player='{self.player_id}', type='{self.leaderboard_type}', rank={self.rank})>"
    
    @property
    def is_ranked(self) -> bool:
        """是否上榜"""
        return self.rank > 0
    
    def claim_reward(self) -> None:
        """标记奖励已领取"""
        self.rewards_claimed = True
        self.reward_claimed_at = datetime.now()
    
    def update_rank(self, rank: int, score: float) -> None:
        """
        更新排名和分数
        
        同时更新历史最佳排名。
        """
        self.rank = rank
        self.score = score
        if rank > 0 and (self.best_rank == 0 or rank < self.best_rank):
            self.best_rank = rank


class LeaderboardHistoryDB(Base, IdMixin, TimestampMixin):
    """
    排行榜历史记录模型
    
    存储排行榜的历史快照，用于查看历史排名趋势。
    
    Attributes:
        id: 主键ID
        player_id: 玩家ID
        leaderboard_type: 排行榜类型
        period: 排行榜周期
        snapshot_date: 快照日期
        rank: 排名
        score: 分数
    """
    
    __tablename__ = "leaderboard_history"
    __table_args__ = (
        UniqueConstraint(
            "player_id", "leaderboard_type", "period", "snapshot_date",
            name="uq_leaderboard_history"
        ),
        Index("ix_leaderboard_history_player", "player_id"),
        Index("ix_leaderboard_history_type", "leaderboard_type"),
        Index("ix_leaderboard_history_date", "snapshot_date"),
        {"comment": "排行榜历史记录表"},
    )
    
    player_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="玩家ID",
    )
    
    leaderboard_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="排行榜类型",
    )
    
    period: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="排行榜周期",
    )
    
    snapshot_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        comment="快照日期",
    )
    
    rank: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="排名",
    )
    
    score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="分数",
    )
    
    def __repr__(self) -> str:
        return f"<LeaderboardHistoryDB(player='{self.player_id}', type='{self.leaderboard_type}', rank={self.rank})>"
