"""
王者之奕 - 自定义房间数据库模型

本模块定义自定义房间系统的数据库持久化模型：
- CustomRoomDB: 自定义房间记录
- CustomRoomPlayerDB: 房间玩家记录

用于存储自定义房间的历史记录和统计信息。
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
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.server.models.base import Base, IdMixin, TimestampMixin


class CustomRoomDB(Base, IdMixin, TimestampMixin):
    """
    自定义房间数据模型
    
    存储自定义房间的历史记录。
    
    Attributes:
        id: 主键ID
        room_id: 房间唯一ID
        name: 房间名称
        host_id: 房主ID
        max_players: 最大玩家数
        special_rules: 特殊规则 (JSON)
        has_password: 是否有密码
        state: 房间状态
        player_count: 玩家数量
        game_started_at: 游戏开始时间
        game_ended_at: 游戏结束时间
        duration_seconds: 游戏时长（秒）
    """
    
    __tablename__ = "custom_rooms"
    __table_args__ = (
        Index("ix_custom_rooms_room_id", "room_id", unique=True),
        Index("ix_custom_rooms_host_id", "host_id"),
        Index("ix_custom_rooms_state", "state"),
        Index("ix_custom_rooms_created", "created_at"),
        Index("ix_custom_rooms_game_started", "game_started_at"),
        {"comment": "自定义房间表"},
    )
    
    room_id: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
        comment="房间ID",
    )
    
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="房间名称",
    )
    
    host_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="房主ID",
    )
    
    max_players: Mapped[int] = mapped_column(
        Integer,
        default=8,
        nullable=False,
        comment="最大玩家数",
    )
    
    special_rules: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="特殊规则",
    )
    
    has_password: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否有密码",
    )
    
    state: Mapped[str] = mapped_column(
        String(20),
        default="waiting",
        nullable=False,
        comment="房间状态",
    )
    
    player_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="玩家数量",
    )
    
    game_started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="游戏开始时间",
    )
    
    game_ended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="游戏结束时间",
    )
    
    duration_seconds: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="游戏时长（秒）",
    )
    
    def __repr__(self) -> str:
        return f"<CustomRoomDB(room_id='{self.room_id}', name='{self.name}', state='{self.state}')>"
    
    @property
    def rule_list(self) -> list:
        """获取特殊规则列表"""
        return self.special_rules.get("rules", []) if self.special_rules else []
    
    def set_special_rules(self, rules: list) -> None:
        """设置特殊规则"""
        self.special_rules = {"rules": rules}
    
    def calculate_duration(self) -> None:
        """计算游戏时长"""
        if self.game_started_at and self.game_ended_at:
            delta = self.game_ended_at - self.game_started_at
            self.duration_seconds = int(delta.total_seconds())
    
    def to_dict(self) -> dict:
        """转换为字典"""
        data = super().to_dict()
        # 隐藏敏感信息
        data.pop("has_password", None)
        return data


class CustomRoomPlayerDB(Base, IdMixin, TimestampMixin):
    """
    自定义房间玩家数据模型
    
    存储玩家在房间中的记录。
    
    Attributes:
        id: 主键ID
        room_id: 房间ID
        player_id: 玩家ID
        nickname: 玩家昵称
        slot: 房间内位置
        is_host: 是否是房主
        is_ai: 是否是AI
        final_rank: 最终排名
        final_hp: 最终血量
        is_winner: 是否获胜
    """
    
    __tablename__ = "custom_room_players"
    __table_args__ = (
        Index("ix_custom_room_players_room_id", "room_id"),
        Index("ix_custom_room_players_player_id", "player_id"),
        Index("ix_custom_room_players_room_player", "room_id", "player_id", unique=True),
        {"comment": "自定义房间玩家表"},
    )
    
    room_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("custom_rooms.room_id", ondelete="CASCADE"),
        nullable=False,
        comment="房间ID",
    )
    
    player_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="玩家ID",
    )
    
    nickname: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="玩家昵称",
    )
    
    slot: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="房间内位置",
    )
    
    is_host: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否是房主",
    )
    
    is_ai: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否是AI",
    )
    
    final_rank: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="最终排名",
    )
    
    final_hp: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="最终血量",
    )
    
    is_winner: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否获胜",
    )
    
    def __repr__(self) -> str:
        return f"<CustomRoomPlayerDB(room_id='{self.room_id}', player_id='{self.player_id}')>"
    
    def set_result(self, rank: int, hp: int, is_winner: bool = False) -> None:
        """设置游戏结果"""
        self.final_rank = rank
        self.final_hp = hp
        self.is_winner = is_winner


class CustomRoomStatsDB(Base, IdMixin, TimestampMixin):
    """
    自定义房间统计数据模型
    
    存储玩家的自定义房间统计数据。
    
    Attributes:
        id: 主键ID
        player_id: 玩家ID
        total_rooms: 参与房间总数
        total_host: 创建房间数（房主）
        total_games: 游戏局数
        total_wins: 胜利次数
        total_ai_killed: 击败AI次数
        favorite_rules: 最喜欢的规则 (JSON)
    """
    
    __tablename__ = "custom_room_stats"
    __table_args__ = (
        Index("ix_custom_room_stats_player_id", "player_id", unique=True),
        {"comment": "自定义房间统计表"},
    )
    
    player_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        comment="玩家ID",
    )
    
    total_rooms: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="参与房间总数",
    )
    
    total_host: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="创建房间数",
    )
    
    total_games: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="游戏局数",
    )
    
    total_wins: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="胜利次数",
    )
    
    total_ai_killed: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="击败AI次数",
    )
    
    favorite_rules: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="最喜欢的规则",
    )
    
    def __repr__(self) -> str:
        return f"<CustomRoomStatsDB(player_id='{self.player_id}')>"
    
    @property
    def win_rate(self) -> float:
        """计算胜率"""
        if self.total_games == 0:
            return 0.0
        return self.total_wins / self.total_games
    
    def increment_rooms(self, is_host: bool = False) -> None:
        """增加参与房间数"""
        self.total_rooms += 1
        if is_host:
            self.total_host += 1
    
    def increment_games(self, is_win: bool = False) -> None:
        """增加游戏局数"""
        self.total_games += 1
        if is_win:
            self.total_wins += 1
    
    def update_favorite_rules(self, rule: str) -> None:
        """更新最喜欢的规则"""
        if self.favorite_rules is None:
            self.favorite_rules = {}
        
        count = self.favorite_rules.get(rule, 0)
        self.favorite_rules[rule] = count + 1
    
    def to_dict(self) -> dict:
        """转换为字典"""
        data = super().to_dict()
        data["win_rate"] = round(self.win_rate, 4)
        return data
