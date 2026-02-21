"""
王者之奕 - 玩家数据模型

本模块定义玩家的数据库持久化模型：
- PlayerDB: 玩家账户数据
- PlayerStatsDB: 玩家统计数据

用于存储玩家的账户信息和游戏统计数据。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, Integer, String, Text, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, IdMixin, TimestampMixin


class PlayerDB(Base, IdMixin, TimestampMixin):
    """
    玩家账户数据模型
    
    存储玩家的基本账户信息，包括：
    - 登录凭证
    - 基本信息
    - 游戏货币
    
    Attributes:
        id: 玩家唯一ID（主键）
        user_id: 用户唯一标识（用于登录）
        nickname: 玩家昵称
        avatar: 头像URL
        gold: 金币余额
        diamond: 钻石余额
        level: 玩家等级
        exp: 当前经验值
        is_online: 是否在线
        last_login_at: 最后登录时间
        stats: 关联的统计数据
    """
    
    __tablename__ = "players"
    
    # 基本信息
    user_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        comment="用户唯一标识",
    )
    nickname: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="玩家昵称",
    )
    avatar: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="头像URL",
    )
    
    # 游戏货币
    gold: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="金币余额",
    )
    diamond: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="钻石余额",
    )
    
    # 等级系统
    level: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="玩家等级",
    )
    exp: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="当前经验值",
    )
    
    # 状态信息
    is_online: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否在线",
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="最后登录时间",
    )
    last_logout_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="最后登出时间",
    )
    
    # 关联统计数据（一对一）
    stats: Mapped[Optional["PlayerStatsDB"]] = relationship(
        "PlayerStatsDB",
        back_populates="player",
        uselist=False,
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<PlayerDB(id={self.id}, nickname='{self.nickname}', level={self.level})>"
    
    def to_dict(self) -> dict[str, Any]:
        """
        转换为字典
        
        Returns:
            包含玩家信息的字典
        """
        data = super().to_dict()
        # 添加统计数据
        if self.stats:
            data["stats"] = self.stats.to_dict()
        return data


class PlayerStatsDB(Base, TimestampMixin):
    """
    玩家统计数据模型
    
    存储玩家的游戏统计数据，包括：
    - 对局统计
    - 排名统计
    - 成就数据
    
    Attributes:
        id: 统计记录ID（主键）
        player_id: 关联的玩家ID（外键）
        total_matches: 总对局数
        wins: 胜利场次
        losses: 失败场次
        draws: 平局场次
        first_place_count: 第一名次数
        top4_count: 前四名次数
        total_damage_dealt: 总伤害输出
        total_damage_taken: 总承受伤害
        total_gold_earned: 总获得金币
        total_heroes_purchased: 总购买英雄数
        best_win_streak: 最高连胜
        current_win_streak: 当前连胜
        favorite_synergy: 最常用羁绊
    """
    
    __tablename__ = "player_stats"
    
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    player_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        unique=True,
        index=True,
        comment="关联玩家ID",
    )
    
    # 对局统计
    total_matches: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总对局数",
    )
    wins: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="胜利场次",
    )
    losses: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="失败场次",
    )
    draws: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="平局场次",
    )
    
    # 排名统计
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
        comment="前四名次数",
    )
    average_rank: Mapped[float] = mapped_column(
        Integer,
        default=0.0,
        nullable=False,
        comment="平均排名（乘以100存储）",
    )
    
    # 游戏数据统计
    total_damage_dealt: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总伤害输出",
    )
    total_damage_taken: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总承受伤害",
    )
    total_gold_earned: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总获得金币",
    )
    total_heroes_purchased: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总购买英雄数",
    )
    
    # 连胜记录
    best_win_streak: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="最高连胜",
    )
    current_win_streak: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="当前连胜",
    )
    
    # 其他统计
    favorite_synergy: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="最常用羁绊",
    )
    total_play_time_seconds: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总游戏时长（秒）",
    )
    
    # 关联玩家
    player: Mapped["PlayerDB"] = relationship(
        "PlayerDB",
        back_populates="stats",
    )
    
    def __repr__(self) -> str:
        return f"<PlayerStatsDB(player_id={self.player_id}, total_matches={self.total_matches})>"
    
    @property
    def win_rate(self) -> float:
        """
        计算胜率
        
        Returns:
            胜率（0-1之间）
        """
        if self.total_matches == 0:
            return 0.0
        return self.wins / self.total_matches
    
    @property
    def top4_rate(self) -> float:
        """
        计算前四率
        
        Returns:
            前四率（0-1之间）
        """
        if self.total_matches == 0:
            return 0.0
        return self.top4_count / self.total_matches
    
    def to_dict(self) -> dict[str, Any]:
        """
        转换为字典
        
        Returns:
            包含统计数据的字典
        """
        data = super().to_dict()
        # 添加计算字段
        data["win_rate"] = round(self.win_rate, 4)
        data["top4_rate"] = round(self.top4_rate, 4)
        # 转换平均排名
        data["average_rank"] = self.average_rank / 100
        return data
    
    def update_after_match(
        self,
        rank: int,
        is_win: bool,
        damage_dealt: int = 0,
        damage_taken: int = 0,
        gold_earned: int = 0,
        heroes_purchased: int = 0,
    ) -> None:
        """
        对局结束后更新统计数据
        
        Args:
            rank: 本局排名
            is_win: 是否获胜
            damage_dealt: 造成的伤害
            damage_taken: 承受的伤害
            gold_earned: 获得的金币
            heroes_purchased: 购买的英雄数
        """
        self.total_matches += 1
        
        if is_win:
            self.wins += 1
            self.current_win_streak += 1
            if self.current_win_streak > self.best_win_streak:
                self.best_win_streak = self.current_win_streak
        else:
            self.losses += 1
            self.current_win_streak = 0
        
        # 更新排名统计
        if rank == 1:
            self.first_place_count += 1
        if rank <= 4:
            self.top4_count += 1
        
        # 更新平均排名（使用加权平均）
        if self.total_matches == 1:
            self.average_rank = rank * 100
        else:
            old_total = (self.total_matches - 1) * self.average_rank
            self.average_rank = (old_total + rank * 100) / self.total_matches
        
        # 更新其他统计
        self.total_damage_dealt += damage_dealt
        self.total_damage_taken += damage_taken
        self.total_gold_earned += gold_earned
        self.total_heroes_purchased += heroes_purchased
