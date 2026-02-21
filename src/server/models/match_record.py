"""
王者之奕 - 对局记录模型

本模块定义对局记录的数据库持久化模型：
- MatchRecordDB: 对局记录
- MatchPlayerResultDB: 玩家对局结果

用于记录游戏对局的详细信息和结果。
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional, List

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Boolean,
    JSON,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, IdMixin, TimestampMixin


class MatchStatus(str, Enum):
    """对局状态枚举"""
    WAITING = "waiting"      # 等待玩家
    IN_PROGRESS = "in_progress"  # 进行中
    FINISHED = "finished"    # 已结束
    CANCELLED = "cancelled"  # 已取消


class MatchRecordDB(Base, IdMixin):
    """
    对局记录模型
    
    存储每局游戏的基本信息：
    - 对局ID
    - 开始/结束时间
    - 对局状态
    - 游戏配置
    
    Attributes:
        id: 对局唯一ID（主键）
        match_id: 对局业务ID（UUID）
        room_id: 房间ID
        status: 对局状态
        total_rounds: 总回合数
        start_time: 开始时间
        end_time: 结束时间
        duration_seconds: 对局时长（秒）
        config: 游戏配置（JSON）
        player_results: 关联的玩家结果列表
    """
    
    __tablename__ = "match_records"
    
    # 基本信息
    match_id: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        index=True,
        comment="对局业务ID（UUID）",
    )
    room_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,
        index=True,
        comment="房间ID",
    )
    
    # 状态信息
    status: Mapped[str] = mapped_column(
        String(20),
        default=MatchStatus.WAITING.value,
        nullable=False,
        comment="对局状态",
    )
    total_rounds: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总回合数",
    )
    
    # 时间信息
    start_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="开始时间",
    )
    end_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="结束时间",
    )
    duration_seconds: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="对局时长（秒）",
    )
    
    # 游戏配置
    config: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="游戏配置",
    )
    
    # 关联玩家结果（一对多）
    player_results: Mapped[List["MatchPlayerResultDB"]] = relationship(
        "MatchPlayerResultDB",
        back_populates="match",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return f"<MatchRecordDB(id={self.id}, match_id='{self.match_id}', status='{self.status}')>"
    
    @property
    def is_finished(self) -> bool:
        """检查对局是否已结束"""
        return self.status == MatchStatus.FINISHED.value
    
    @property
    def duration_minutes(self) -> float:
        """获取对局时长（分钟）"""
        return self.duration_seconds / 60
    
    def start(self) -> None:
        """开始对局"""
        self.status = MatchStatus.IN_PROGRESS.value
        self.start_time = func.now()
    
    def finish(self, total_rounds: int) -> None:
        """
        结束对局
        
        Args:
            total_rounds: 总回合数
        """
        self.status = MatchStatus.FINISHED.value
        self.end_time = func.now()
        self.total_rounds = total_rounds
        
        # 计算时长
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            self.duration_seconds = int(delta.total_seconds())
    
    def cancel(self) -> None:
        """取消对局"""
        self.status = MatchStatus.CANCELLED.value
        self.end_time = func.now()
    
    def to_dict(self) -> dict[str, Any]:
        """
        转换为字典
        
        Returns:
            包含对局信息的字典
        """
        data = super().to_dict()
        # 添加玩家结果
        data["player_results"] = [
            result.to_dict() for result in self.player_results
        ]
        # 添加计算字段
        data["duration_minutes"] = round(self.duration_minutes, 2)
        return data


class MatchPlayerResultDB(Base, IdMixin):
    """
    玩家对局结果模型
    
    存储每个玩家在对局中的详细结果：
    - 排名和分数
    - 战斗统计
    - 阵容信息
    
    Attributes:
        id: 结果记录ID（主键）
        match_id: 关联的对局记录ID（外键）
        player_id: 玩家ID
        rank: 最终排名
        final_hp: 最终血量
        damage_dealt: 总伤害输出
        damage_taken: 总承受伤害
        gold_earned: 总获得金币
        heroes_purchased: 购买英雄数
        win_count: 胜利场次
        lose_count: 失败场次
        final_synergies: 最终羁绊（JSON）
        final_heroes: 最终阵容（JSON）
    """
    
    __tablename__ = "match_player_results"
    
    # 关联信息
    match_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("match_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="关联对局ID",
    )
    player_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="玩家ID",
    )
    
    # 排名信息
    rank: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="最终排名",
    )
    final_hp: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="最终血量",
    )
    
    # 战斗统计
    damage_dealt: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总伤害输出",
    )
    damage_taken: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总承受伤害",
    )
    kills: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="击杀英雄数",
    )
    
    # 经济统计
    gold_earned: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总获得金币",
    )
    gold_spent: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总消费金币",
    )
    heroes_purchased: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="购买英雄数",
    )
    
    # 对战统计
    win_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="胜利场次",
    )
    lose_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="失败场次",
    )
    draw_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="平局场次",
    )
    
    # 阵容信息
    final_level: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="最终等级",
    )
    final_synergies: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="最终羁绊",
    )
    final_heroes: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="最终阵容",
    )
    
    # 关联对局记录
    match: Mapped["MatchRecordDB"] = relationship(
        "MatchRecordDB",
        back_populates="player_results",
    )
    
    def __repr__(self) -> str:
        return f"<MatchPlayerResultDB(match_id={self.match_id}, player_id={self.player_id}, rank={self.rank})>"
    
    @property
    def is_winner(self) -> bool:
        """检查是否获胜（第一名）"""
        return self.rank == 1
    
    @property
    def is_top4(self) -> bool:
        """检查是否前四"""
        return self.rank <= 4
    
    @property
    def total_battles(self) -> int:
        """获取总对战数"""
        return self.win_count + self.lose_count + self.draw_count
    
    @property
    def win_rate(self) -> float:
        """计算胜率"""
        if self.total_battles == 0:
            return 0.0
        return self.win_count / self.total_battles
    
    def to_dict(self) -> dict[str, Any]:
        """
        转换为字典
        
        Returns:
            包含玩家结果的字典
        """
        data = super().to_dict()
        # 添加计算字段
        data["is_winner"] = self.is_winner
        data["is_top4"] = self.is_top4
        data["win_rate"] = round(self.win_rate, 4)
        return data
    
    @classmethod
    def create_from_game_data(
        cls,
        match_id: int,
        player_id: int,
        rank: int,
        final_hp: int,
        game_data: dict[str, Any],
    ) -> "MatchPlayerResultDB":
        """
        从游戏数据创建结果记录
        
        Args:
            match_id: 对局ID
            player_id: 玩家ID
            rank: 最终排名
            final_hp: 最终血量
            game_data: 游戏数据字典
            
        Returns:
            玩家结果记录
        """
        return cls(
            match_id=match_id,
            player_id=player_id,
            rank=rank,
            final_hp=final_hp,
            damage_dealt=game_data.get("damage_dealt", 0),
            damage_taken=game_data.get("damage_taken", 0),
            kills=game_data.get("kills", 0),
            gold_earned=game_data.get("gold_earned", 0),
            gold_spent=game_data.get("gold_spent", 0),
            heroes_purchased=game_data.get("heroes_purchased", 0),
            win_count=game_data.get("win_count", 0),
            lose_count=game_data.get("lose_count", 0),
            draw_count=game_data.get("draw_count", 0),
            final_level=game_data.get("final_level", 1),
            final_synergies=game_data.get("final_synergies"),
            final_heroes=game_data.get("final_heroes"),
        )
