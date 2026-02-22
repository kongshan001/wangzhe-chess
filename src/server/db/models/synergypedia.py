"""
王者之奕 - 羁绊图鉴数据库模型

本模块定义羁绊图鉴系统的数据库持久化模型：
- SynergypediaDB: 羁绊进度记录

用于存储玩家羁绊相关的持久化数据。
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


class SynergypediaDB(Base, IdMixin, TimestampMixin):
    """
    羁绊图鉴数据模型
    
    存储玩家的羁绊使用进度和成就。
    
    Attributes:
        id: 主键ID
        player_id: 玩家ID
        synergy_name: 羁绊名称
        synergy_type: 羁绊类型 (race/class)
        activation_count: 总激活次数
        max_heroes_used: 单局最多使用该羁绊英雄数
        highest_level_reached: 达到的最高羁绊等级
        total_games: 使用该羁绊的对局数
        win_count: 胜利次数
        achievements: 已解锁的成就列表 (JSON)
        last_activated_at: 最后激活时间
    """
    
    __tablename__ = "synergypedia"
    __table_args__ = (
        UniqueConstraint("player_id", "synergy_name", name="uq_player_synergy"),
        Index("ix_synergypedia_player_id", "player_id"),
        Index("ix_synergypedia_synergy_name", "synergy_name"),
        Index("ix_synergypedia_type", "synergy_type"),
        Index("ix_synergypedia_activation_count", "activation_count"),
        {"comment": "羁绊图鉴表"},
    )
    
    player_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="玩家ID",
    )
    
    synergy_name: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="羁绊名称",
    )
    
    synergy_type: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        comment="羁绊类型 (race/class)",
    )
    
    activation_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总激活次数",
    )
    
    max_heroes_used: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="单局最多使用该羁绊英雄数",
    )
    
    highest_level_reached: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="达到的最高羁绊等级",
    )
    
    total_games: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="使用该羁绊的对局数",
    )
    
    win_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="胜利次数",
    )
    
    achievements: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="已解锁的成就列表",
    )
    
    last_activated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="最后激活时间",
    )
    
    def __repr__(self) -> str:
        return f"<SynergypediaDB(player='{self.player_id}', synergy='{self.synergy_name}', count={self.activation_count})>"
    
    @property
    def win_rate(self) -> float:
        """计算胜率"""
        if self.total_games == 0:
            return 0.0
        return round(self.win_count / self.total_games * 100, 1)
    
    @property
    def achievement_list(self) -> list[str]:
        """获取成就列表"""
        if self.achievements is None:
            return []
        return self.achievements.get("list", [])
    
    def add_achievement(self, achievement_name: str) -> bool:
        """
        添加成就
        
        Args:
            achievement_name: 成就名称
            
        Returns:
            是否是新成就
        """
        if self.achievements is None:
            self.achievements = {"list": []}
        
        if achievement_name in self.achievements["list"]:
            return False
        
        self.achievements["list"].append(achievement_name)
        return True
    
    def update_stats(
        self,
        heroes_count: int,
        level_reached: int,
        is_win: bool,
    ) -> None:
        """
        更新统计数据
        
        Args:
            heroes_count: 使用的该羁绊英雄数
            level_reached: 达到的羁绊等级
            is_win: 是否获胜
        """
        self.activation_count += 1
        self.total_games += 1
        self.last_activated_at = datetime.now()
        
        if is_win:
            self.win_count += 1
        
        if heroes_count > self.max_heroes_used:
            self.max_heroes_used = heroes_count
        
        if level_reached > self.highest_level_reached:
            self.highest_level_reached = level_reached
    
    def to_progress_dict(self) -> dict:
        """
        转换为进度字典格式
        
        Returns:
            进度信息字典
        """
        return {
            "synergy_name": self.synergy_name,
            "synergy_type": self.synergy_type,
            "activation_count": self.activation_count,
            "max_heroes_used": self.max_heroes_used,
            "highest_level_reached": self.highest_level_reached,
            "total_games": self.total_games,
            "win_rate": self.win_rate,
            "achievements": self.achievement_list,
            "last_activated_at": self.last_activated_at.isoformat() if self.last_activated_at else None,
        }


class SynergyAchievementDB(Base, IdMixin, TimestampMixin):
    """
    羁绊成就数据模型
    
    存储玩家已解锁的羁绊成就。
    
    Attributes:
        id: 主键ID
        player_id: 玩家ID
        achievement_id: 成就ID
        synergy_name: 羁绊名称
        achievement_name: 成就名称
        reward_claimed: 奖励是否已领取
    """
    
    __tablename__ = "synergy_achievements"
    __table_args__ = (
        UniqueConstraint("player_id", "achievement_id", name="uq_player_achievement"),
        Index("ix_synergy_achievements_player_id", "player_id"),
        Index("ix_synergy_achievements_synergy_name", "synergy_name"),
        {"comment": "羁绊成就表"},
    )
    
    player_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="玩家ID",
    )
    
    achievement_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="成就ID",
    )
    
    synergy_name: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="羁绊名称",
    )
    
    achievement_name: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="成就名称",
    )
    
    reward_claimed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="奖励是否已领取",
    )
    
    def __repr__(self) -> str:
        return f"<SynergyAchievementDB(player='{self.player_id}', achievement='{self.achievement_id}')>"
