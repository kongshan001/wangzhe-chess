"""
王者之奕 - 新手引导数据库模型

本模块定义新手引导系统的数据库持久化模型：
- TutorialProgressDB: 玩家引导进度
- TutorialStatsDB: 玩家引导统计

用于存储新手引导相关的持久化数据。
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

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


class TutorialProgressDB(Base, IdMixin, TimestampMixin):
    """
    玩家引导进度数据模型
    
    存储玩家在新手引导中的进度状态。
    
    Attributes:
        id: 主键ID
        player_id: 玩家ID
        tutorial_id: 引导ID
        current_step: 当前步骤序号
        current_step_id: 当前步骤ID
        completed_steps: 已完成的步骤ID列表 (JSON)
        completed: 是否已完成
        completed_at: 完成时间
        claimed: 是否已领取奖励
        claimed_at: 领取时间
        skipped: 是否已跳过
        skipped_at: 跳过时间
        started_at: 引导开始时间
        duration_seconds: 引导完成耗时 (秒)
        attempts: 引导尝试次数
    """
    
    __tablename__ = "tutorial_progress"
    __table_args__ = (
        UniqueConstraint("player_id", "tutorial_id", name="uq_tutorial_progress_player_tutorial"),
        Index("ix_tutorial_progress_player_id", "player_id"),
        Index("ix_tutorial_progress_tutorial_id", "tutorial_id"),
        Index("ix_tutorial_progress_completed", "completed"),
        Index("ix_tutorial_progress_claimed", "claimed"),
        Index("ix_tutorial_progress_player_completed", "player_id", "completed"),
        {"comment": "玩家引导进度表"},
    )
    
    player_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="玩家ID",
    )
    
    tutorial_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="引导ID",
    )
    
    current_step: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="当前步骤序号",
    )
    
    current_step_id: Mapped[str] = mapped_column(
        String(64),
        default="",
        nullable=False,
        comment="当前步骤ID",
    )
    
    completed_steps: Mapped[Optional[list]] = mapped_column(
        JSON,
        nullable=True,
        comment="已完成的步骤ID列表 (JSON)",
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
    
    skipped: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否已跳过",
    )
    
    skipped_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="跳过时间",
    )
    
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="引导开始时间",
    )
    
    duration_seconds: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="引导完成耗时 (秒)",
    )
    
    attempts: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="引导尝试次数",
    )
    
    def __repr__(self) -> str:
        return f"<TutorialProgressDB(player_id='{self.player_id}', tutorial_id='{self.tutorial_id}', current_step={self.current_step})>"
    
    @property
    def is_claimable(self) -> bool:
        """是否可领取奖励"""
        return (self.completed or self.skipped) and not self.claimed
    
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
    
    def mark_skipped(self) -> None:
        """标记为已跳过"""
        if not self.skipped:
            self.skipped = True
            self.skipped_at = datetime.now()
    
    def to_dict(self) -> dict:
        """转换为字典"""
        data = super().to_dict()
        # 处理时间字段
        if self.completed_at:
            data["completed_at"] = self.completed_at.isoformat()
        if self.claimed_at:
            data["claimed_at"] = self.claimed_at.isoformat()
        if self.skipped_at:
            data["skipped_at"] = self.skipped_at.isoformat()
        if self.started_at:
            data["started_at"] = self.started_at.isoformat()
        # 添加计算属性
        data["is_claimable"] = self.is_claimable
        return data


class TutorialStatsDB(Base, IdMixin, TimestampMixin):
    """
    玩家引导统计数据模型
    
    存储玩家的引导完成统计。
    
    Attributes:
        id: 主键ID
        player_id: 玩家ID
        total_tutorials: 总引导数
        completed_tutorials: 已完成引导数
        skipped_tutorials: 已跳过引导数
        total_rewards_gold: 累计获得金币奖励
        total_rewards_exp: 累计获得经验奖励
        total_duration_seconds: 累计引导耗时
        last_tutorial_id: 最后完成的引导ID
        first_tutorial_at: 第一次完成引导时间
    """
    
    __tablename__ = "tutorial_stats"
    __table_args__ = (
        UniqueConstraint("player_id", name="uq_tutorial_stats_player"),
        Index("ix_tutorial_stats_player_id", "player_id"),
        Index("ix_tutorial_stats_completed", "completed_tutorials"),
        {"comment": "玩家引导统计表"},
    )
    
    player_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="玩家ID",
    )
    
    total_tutorials: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总引导数",
    )
    
    completed_tutorials: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="已完成引导数",
    )
    
    skipped_tutorials: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="已跳过引导数",
    )
    
    total_rewards_gold: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="累计获得金币奖励",
    )
    
    total_rewards_exp: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="累计获得经验奖励",
    )
    
    total_duration_seconds: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="累计引导耗时",
    )
    
    last_tutorial_id: Mapped[str] = mapped_column(
        String(64),
        default="",
        nullable=False,
        comment="最后完成的引导ID",
    )
    
    first_tutorial_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="第一次完成引导时间",
    )
    
    def __repr__(self) -> str:
        return f"<TutorialStatsDB(player_id='{self.player_id}', completed={self.completed_tutorials}/{self.total_tutorials})>"
    
    @property
    def completion_rate(self) -> float:
        """计算完成率"""
        if self.total_tutorials == 0:
            return 0.0
        return round(self.completed_tutorials / self.total_tutorials * 100, 2)
    
    def update_from_completion(
        self,
        tutorial_id: str,
        reward_gold: int = 0,
        reward_exp: int = 0,
        duration_seconds: int = 0,
        skipped: bool = False,
    ) -> None:
        """
        根据完成情况更新统计
        
        Args:
            tutorial_id: 引导ID
            reward_gold: 奖励金币
            reward_exp: 奖励经验
            duration_seconds: 耗时
            skipped: 是否跳过
        """
        if skipped:
            self.skipped_tutorials += 1
        else:
            self.completed_tutorials += 1
            self.total_rewards_gold += reward_gold
            self.total_rewards_exp += reward_exp
            self.total_duration_seconds += duration_seconds
        
        self.last_tutorial_id = tutorial_id
        
        if not self.first_tutorial_at:
            self.first_tutorial_at = datetime.now()
    
    def to_dict(self) -> dict:
        """转换为字典"""
        data = super().to_dict()
        if self.first_tutorial_at:
            data["first_tutorial_at"] = self.first_tutorial_at.isoformat()
        data["completion_rate"] = self.completion_rate
        return data
