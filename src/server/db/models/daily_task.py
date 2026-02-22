"""
王者之奕 - 每日任务数据库模型

本模块定义每日任务系统的数据库持久化模型：
- DailyTaskDB: 每日任务实例
- TaskProgressDB: 任务进度记录

用于存储每日任务相关的持久化数据。
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
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


class DailyTaskDB(Base, IdMixin, TimestampMixin):
    """
    每日任务实例数据模型
    
    存储玩家每日生成的任务实例。
    
    Attributes:
        id: 主键ID
        player_id: 玩家ID
        task_id: 任务唯一ID
        template_id: 任务模板ID
        task_date: 任务日期
        name: 任务名称
        description: 任务描述
        requirement: 任务需求 (JSON)
        rewards: 任务奖励 (JSON)
        difficulty: 任务难度 (1=简单, 2=普通, 3=困难)
        icon: 图标ID
        refreshed: 是否被刷新过
    """
    
    __tablename__ = "daily_tasks"
    __table_args__ = (
        UniqueConstraint("player_id", "task_id", name="uq_daily_task_player_task"),
        Index("ix_daily_tasks_player_id", "player_id"),
        Index("ix_daily_tasks_task_date", "task_date"),
        Index("ix_daily_tasks_player_date", "player_id", "task_date"),
        {"comment": "每日任务表"},
    )
    
    player_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="玩家ID",
    )
    
    task_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="任务唯一ID",
    )
    
    template_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="任务模板ID",
    )
    
    task_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="任务日期",
    )
    
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="任务名称",
    )
    
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        default="",
        comment="任务描述",
    )
    
    requirement: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="任务需求 (JSON)",
    )
    
    rewards: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="任务奖励 (JSON)",
    )
    
    difficulty: Mapped[int] = mapped_column(
        Integer,
        default=2,
        nullable=False,
        comment="任务难度 (1=简单, 2=普通, 3=困难)",
    )
    
    icon: Mapped[str] = mapped_column(
        String(50),
        default="",
        nullable=False,
        comment="图标ID",
    )
    
    refreshed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否被刷新过",
    )
    
    def __repr__(self) -> str:
        return f"<DailyTaskDB(player_id='{self.player_id}', task_id='{self.task_id}', name='{self.name}')>"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        data = super().to_dict()
        # 处理日期
        if self.task_date:
            data["task_date"] = self.task_date.isoformat()
        return data


class TaskProgressDB(Base, IdMixin, TimestampMixin):
    """
    任务进度数据模型
    
    存储玩家的任务进度记录。
    
    Attributes:
        id: 主键ID
        player_id: 玩家ID
        task_id: 任务ID
        task_date: 任务日期
        progress: 当前进度值
        completed: 是否已完成
        completed_at: 完成时间
        claimed: 是否已领取奖励
        claimed_at: 领取时间
    """
    
    __tablename__ = "task_progress"
    __table_args__ = (
        UniqueConstraint("player_id", "task_id", name="uq_task_progress_player_task"),
        Index("ix_task_progress_player_id", "player_id"),
        Index("ix_task_progress_task_date", "task_date"),
        Index("ix_task_progress_player_date", "player_id", "task_date"),
        Index("ix_task_progress_completed", "completed"),
        Index("ix_task_progress_claimed", "claimed"),
        {"comment": "任务进度表"},
    )
    
    player_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="玩家ID",
    )
    
    task_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="任务ID",
    )
    
    task_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="任务日期",
    )
    
    progress: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="当前进度值",
    )
    
    completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否已完成",
    )
    
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="完成时间",
    )
    
    claimed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否已领取奖励",
    )
    
    claimed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="领取时间",
    )
    
    def __repr__(self) -> str:
        return f"<TaskProgressDB(player_id='{self.player_id}', task_id='{self.task_id}', progress={self.progress})>"
    
    @property
    def is_claimable(self) -> bool:
        """是否可领取奖励"""
        return self.completed and not self.claimed
    
    def mark_completed(self) -> None:
        """标记为已完成"""
        if not self.completed:
            self.completed = True
            self.completed_at = datetime.now()
    
    def mark_claimed(self) -> None:
        """标记为已领取"""
        if not self.claimed:
            self.claimed = True
            self.claimed_at = datetime.now()
    
    def to_dict(self) -> dict:
        """转换为字典"""
        data = super().to_dict()
        # 处理日期
        if self.task_date:
            data["task_date"] = self.task_date.isoformat()
        # 处理时间
        if self.completed_at:
            data["completed_at"] = self.completed_at.isoformat()
        if self.claimed_at:
            data["claimed_at"] = self.claimed_at.isoformat()
        # 添加计算属性
        data["is_claimable"] = self.is_claimable
        return data


class PlayerDailyStatsDB(Base, IdMixin, TimestampMixin):
    """
    玩家每日统计数据模型
    
    存储玩家每日的游戏统计数据，用于任务进度计算。
    
    Attributes:
        id: 主键ID
        player_id: 玩家ID
        stat_date: 统计日期
        games_played: 对局次数
        games_won: 获胜次数
        first_place_count: 第一名次数
        top4_count: 前4名次数
        damage_dealt: 造成伤害
        heroes_killed: 击杀英雄数
        gold_earned: 获得金币
        gold_spent: 花费金币
        max_gold_saved: 单局最大保留金币
        heroes_2star_collected: 2星英雄合成数
        heroes_3star_collected: 3星英雄合成数
        heroes_bought: 购买英雄数
        team_games: 组队游戏次数
        perfect_wins: 完美胜利次数
        refresh_count: 任务刷新次数
    """
    
    __tablename__ = "player_daily_stats"
    __table_args__ = (
        UniqueConstraint("player_id", "stat_date", name="uq_player_daily_stats"),
        Index("ix_player_daily_stats_player_id", "player_id"),
        Index("ix_player_daily_stats_stat_date", "stat_date"),
        Index("ix_player_daily_stats_player_date", "player_id", "stat_date"),
        {"comment": "玩家每日统计表"},
    )
    
    player_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="玩家ID",
    )
    
    stat_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="统计日期",
    )
    
    games_played: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="对局次数",
    )
    
    games_won: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="获胜次数",
    )
    
    first_place_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="第一名次数",
    )
    
    top4_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="前4名次数",
    )
    
    damage_dealt: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="造成伤害",
    )
    
    heroes_killed: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="击杀英雄数",
    )
    
    gold_earned: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="获得金币",
    )
    
    gold_spent: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="花费金币",
    )
    
    max_gold_saved: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="单局最大保留金币",
    )
    
    heroes_2star_collected: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="2星英雄合成数",
    )
    
    heroes_3star_collected: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="3星英雄合成数",
    )
    
    heroes_bought: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="购买英雄数",
    )
    
    team_games: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="组队游戏次数",
    )
    
    perfect_wins: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="完美胜利次数",
    )
    
    refresh_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="任务刷新次数",
    )
    
    def __repr__(self) -> str:
        return f"<PlayerDailyStatsDB(player_id='{self.player_id}', date='{self.stat_date}')>"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        data = super().to_dict()
        if self.stat_date:
            data["stat_date"] = self.stat_date.isoformat()
        return data
    
    def increment(self, field: str, value: int = 1) -> None:
        """
        增加指定字段的值
        
        Args:
            field: 字段名
            value: 增量值
        """
        if hasattr(self, field):
            current = getattr(self, field, 0)
            setattr(self, field, current + value)
    
    def update_max(self, field: str, value: int) -> None:
        """
        更新最大值字段
        
        Args:
            field: 字段名
            value: 新值
        """
        if hasattr(self, field):
            current = getattr(self, field, 0)
            if value > current:
                setattr(self, field, value)
