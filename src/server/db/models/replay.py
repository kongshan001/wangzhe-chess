"""
王者之奕 - 回放系统数据库模型

本模块定义回放相关的数据库模型：
- ReplayDB: 回放记录

用于持久化回放数据。
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.mysql import JSON, LongText
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.server.models.base import Base, IdMixin, TimestampMixin


class ReplayDB(Base, IdMixin, TimestampMixin):
    """
    回放记录模型
    
    存储玩家的对局回放数据。
    
    Attributes:
        id: 主键ID
        replay_id: 回放业务ID（UUID）
        player_id: 玩家ID
        match_id: 对局ID
        player_nickname: 玩家昵称
        final_rank: 最终排名
        total_rounds: 总回合数
        duration_seconds: 对局时长（秒）
        player_count: 参与人数
        game_version: 游戏版本
        frames: 回放帧数据（JSON）
        initial_state: 初始状态（JSON）
        final_rankings: 最终排名（JSON）
        is_shared: 是否已分享
        share_code: 分享码
        created_at: 创建时间
    """
    
    __tablename__ = "replays"
    __table_args__ = (
        Index("ix_replays_player_id", "player_id"),
        Index("ix_replays_match_id", "match_id"),
        Index("ix_replays_created_at", "created_at"),
        Index("ix_replays_share_code", "share_code"),
        Index("ix_replays_player_created", "player_id", "created_at"),
        {"comment": "回放记录表"},
    )
    
    replay_id: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        comment="回放业务ID（UUID）",
    )
    
    player_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="玩家ID",
    )
    
    match_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        comment="对局ID",
    )
    
    player_nickname: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="玩家昵称",
    )
    
    final_rank: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="最终排名",
    )
    
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
        comment="对局时长（秒）",
    )
    
    player_count: Mapped[int] = mapped_column(
        Integer,
        default=8,
        nullable=False,
        comment="参与人数",
    )
    
    game_version: Mapped[str] = mapped_column(
        String(20),
        default="1.0.0",
        nullable=False,
        comment="游戏版本",
    )
    
    frames: Mapped[Optional[str]] = mapped_column(
        LongText,
        nullable=True,
        comment="回放帧数据（JSON）",
    )
    
    initial_state: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="初始状态（JSON）",
    )
    
    final_rankings: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="最终排名（JSON）",
    )
    
    is_shared: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否已分享",
    )
    
    share_code: Mapped[Optional[str]] = mapped_column(
        String(8),
        nullable=True,
        unique=True,
        comment="分享码",
    )
    
    def __repr__(self) -> str:
        return f"<ReplayDB(id={self.id}, replay_id='{self.replay_id}', player_id={self.player_id})>"
    
    @property
    def duration_minutes(self) -> float:
        """获取对局时长（分钟）"""
        return round(self.duration_seconds / 60, 2)
    
    @property
    def is_winner(self) -> bool:
        """是否获胜（第一名）"""
        return self.final_rank == 1
    
    @property
    def is_top4(self) -> bool:
        """是否前四"""
        return self.final_rank <= 4
    
    def to_dict(self) -> dict:
        """转换为字典"""
        data = super().to_dict()
        data["duration_minutes"] = self.duration_minutes
        data["is_winner"] = self.is_winner
        data["is_top4"] = self.is_top4
        # 不返回大型字段
        data.pop("frames", None)
        data.pop("initial_state", None)
        data.pop("final_rankings", None)
        return data
    
    @classmethod
    def create_from_replay_data(
        cls,
        replay_id: str,
        player_id: int,
        match_id: str,
        player_nickname: str,
        final_rank: int,
        total_rounds: int,
        duration_seconds: int,
        frames_json: str,
        player_count: int = 8,
        game_version: str = "1.0.0",
        initial_state: Optional[dict] = None,
        final_rankings: Optional[dict] = None,
    ) -> "ReplayDB":
        """
        从回放数据创建记录
        
        Args:
            replay_id: 回放ID
            player_id: 玩家ID
            match_id: 对局ID
            player_nickname: 玩家昵称
            final_rank: 最终排名
            total_rounds: 总回合数
            duration_seconds: 对局时长
            frames_json: 帧数据JSON
            player_count: 参与人数
            game_version: 游戏版本
            initial_state: 初始状态
            final_rankings: 最终排名
            
        Returns:
            回放记录
        """
        return cls(
            replay_id=replay_id,
            player_id=player_id,
            match_id=match_id,
            player_nickname=player_nickname,
            final_rank=final_rank,
            total_rounds=total_rounds,
            duration_seconds=duration_seconds,
            frames=frames_json,
            player_count=player_count,
            game_version=game_version,
            initial_state=initial_state,
            final_rankings=final_rankings,
        )
