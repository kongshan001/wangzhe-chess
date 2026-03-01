"""
王者之奕 - 玩家数据模型

本模块定义玩家的数据库持久化模型：
- PlayerDB: 玩家账户数据
- PlayerRankDB: 玩家段位数据
- PlayerStatsDB: 玩家统计数据
- PlayerLoginLogDB: 玩家登录记录
- PlayerInventoryDB: 玩家背包

用于存储玩家的账户信息和游戏统计数据。
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum as PyEnum
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, IdMixin, TimestampMixin


class RankTier(str, PyEnum):
    """段位枚举"""

    BRONZE = "bronze"  # 青铜
    SILVER = "silver"  # 白银
    GOLD = "gold"  # 黄金
    PLATINUM = "platinum"  # 铂金
    DIAMOND = "diamond"  # 钻石
    MASTER = "master"  # 大师
    GRANDMASTER = "grandmaster"  # 宗师
    KING = "king"  # 王者


class PlayerDB(Base, IdMixin, TimestampMixin):
    """
    玩家账户数据模型

    存储玩家的基本账户信息，包括：
    - 登录凭证
    - 基本信息
    - 账号状态

    Attributes:
        id: 玩家唯一ID（主键）
        user_id: 用户唯一标识（用于登录）
        username: 用户名（可选，用于账号密码登录）
        password_hash: 密码哈希
        nickname: 玩家昵称
        avatar: 头像URL
        device_id: 设备ID（用于设备绑定）
        is_active: 是否激活
        is_banned: 是否封禁
        ban_until: 封禁截止时间
        last_login_at: 最后登录时间
        last_login_ip: 最后登录IP
        rank: 关联的段位信息
        stats: 关联的统计数据
        login_logs: 关联的登录记录
    """

    __tablename__ = "players"
    __table_args__ = (
        Index("ix_players_user_id", "user_id", unique=True),
        Index("ix_players_username", "username", unique=True),
        Index("ix_players_device_id", "device_id"),
        Index("ix_players_last_login", "last_login_at"),
        {"comment": "玩家账户表"},
    )

    # 登录信息
    user_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        comment="用户唯一标识",
    )
    username: Mapped[str | None] = mapped_column(
        String(50),
        unique=True,
        nullable=True,
        comment="用户名",
    )
    password_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="密码哈希",
    )

    # 基本信息
    nickname: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="昵称",
    )
    avatar: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="头像URL",
    )
    device_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="设备ID",
    )

    # 状态字段
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否激活",
    )
    is_banned: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否封禁",
    )
    ban_until: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="封禁截止时间",
    )

    # 登录信息
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="最后登录时间",
    )
    last_login_ip: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
        comment="最后登录IP",
    )

    # 关联关系
    rank: Mapped[PlayerRankDB] = relationship(
        "PlayerRankDB",
        back_populates="player",
        uselist=False,
        lazy="selectin",
    )
    stats: Mapped[PlayerStatsDB] = relationship(
        "PlayerStatsDB",
        back_populates="player",
        uselist=False,
        lazy="selectin",
    )
    login_logs: Mapped[list[PlayerLoginLogDB]] = relationship(
        "PlayerLoginLogDB",
        back_populates="player",
        lazy="dynamic",
    )
    inventory: Mapped[list[PlayerInventoryDB]] = relationship(
        "PlayerInventoryDB",
        back_populates="player",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"<PlayerDB(id={self.id}, user_id='{self.user_id}', nickname='{self.nickname}')>"

    @property
    def display_name(self) -> str:
        """获取显示名称"""
        return self.nickname or self.user_id

    def to_dict(self) -> dict[str, Any]:
        """转换为字典（隐藏敏感信息）"""
        data = super().to_dict()
        data.pop("password_hash", None)
        return data


class PlayerRankDB(Base, IdMixin, TimestampMixin):
    """
    玩家段位数据模型

    存储玩家的排位赛段位信息。

    Attributes:
        id: 主键ID
        player_id: 玩家ID（外键）
        tier: 段位
        sub_tier: 子段位（1-5）
        stars: 当前星数
        points: 当前积分
        max_tier: 历史最高段位
        max_points: 历史最高积分
        season_id: 赛季ID
        placement_matches: 定位赛场次
        placement_wins: 定位赛胜场
    """

    __tablename__ = "player_ranks"
    __table_args__ = (
        UniqueConstraint("player_id", "season_id", name="uq_player_rank_season"),
        Index("ix_player_ranks_tier", "tier"),
        Index("ix_player_ranks_points", "points"),
        {"comment": "玩家段位表"},
    )

    player_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
        comment="玩家ID",
    )

    # 段位信息
    tier: Mapped[str] = mapped_column(
        String(20),
        default=RankTier.BRONZE.value,
        nullable=False,
        comment="段位",
    )
    sub_tier: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="子段位(1-5)",
    )
    stars: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="当前星数",
    )
    points: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="当前积分",
    )

    # 历史记录
    max_tier: Mapped[str] = mapped_column(
        String(20),
        default=RankTier.BRONZE.value,
        nullable=False,
        comment="历史最高段位",
    )
    max_points: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="历史最高积分",
    )

    # 赛季相关
    season_id: Mapped[str] = mapped_column(
        String(20),
        default="S1",
        nullable=False,
        comment="赛季ID",
    )
    placement_matches: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="定位赛场次",
    )
    placement_wins: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="定位赛胜场",
    )

    # 关联关系
    player: Mapped[PlayerDB] = relationship(
        "PlayerDB",
        back_populates="rank",
    )

    def __repr__(self) -> str:
        return (
            f"<PlayerRankDB(player_id={self.player_id}, tier='{self.tier}', points={self.points})>"
        )

    @property
    def display_rank(self) -> str:
        """获取段位显示文本"""
        if self.tier in [RankTier.MASTER.value, RankTier.GRANDMASTER.value, RankTier.KING.value]:
            return f"{self.tier} {self.stars}星"
        return f"{self.tier}{self.sub_tier} {self.stars}星"

    @property
    def is_placed(self) -> bool:
        """是否完成定位赛"""
        return self.placement_matches >= 10


class PlayerStatsDB(Base, IdMixin, TimestampMixin):
    """
    玩家统计数据模型

    存储玩家的游戏统计数据。

    Attributes:
        id: 主键ID
        player_id: 玩家ID（外键）
        total_matches: 总对局数
        total_wins: 总胜场
        total_top4: 总前四场数
        total_gold_earned: 总获得金币
        total_damage_dealt: 总造成伤害
        total_kills: 总击杀数
        avg_rank: 平均排名
        max_win_streak: 最大连胜
        max_lose_streak: 最大连败
        fastest_win_round: 最快获胜回合
        favorite_synergy: 最常用羁绊
        season_id: 赛季ID
    """

    __tablename__ = "player_stats"
    __table_args__ = (
        UniqueConstraint("player_id", "season_id", name="uq_player_stats_season"),
        Index("ix_player_stats_total_wins", "total_wins"),
        Index("ix_player_stats_avg_rank", "avg_rank"),
        {"comment": "玩家统计表"},
    )

    player_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
        comment="玩家ID",
    )

    # 对局统计
    total_matches: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总对局数",
    )
    total_wins: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总胜场(第1名)",
    )
    total_top4: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总前四场数",
    )
    avg_rank: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="平均排名",
    )

    # 战斗统计
    total_damage_dealt: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总造成伤害",
    )
    total_kills: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总击杀英雄数",
    )

    # 经济统计
    total_gold_earned: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总获得金币",
    )

    # 记录统计
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
    fastest_win_round: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="最快获胜回合",
    )

    # 英雄统计
    favorite_synergy: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="最常用羁绊",
    )
    heroes_played: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="使用过的英雄统计",
    )

    # 赛季相关
    season_id: Mapped[str] = mapped_column(
        String(20),
        default="S1",
        nullable=False,
        comment="赛季ID",
    )

    # 关联关系
    player: Mapped[PlayerDB] = relationship(
        "PlayerDB",
        back_populates="stats",
    )

    def __repr__(self) -> str:
        return f"<PlayerStatsDB(player_id={self.player_id}, matches={self.total_matches})>"

    @property
    def win_rate(self) -> float:
        """计算胜率"""
        if self.total_matches == 0:
            return 0.0
        return round(self.total_wins / self.total_matches * 100, 2)

    @property
    def top4_rate(self) -> float:
        """计算前四率"""
        if self.total_matches == 0:
            return 0.0
        return round(self.total_top4 / self.total_matches * 100, 2)


class PlayerLoginLogDB(Base, IdMixin, TimestampMixin):
    """
    玩家登录记录模型

    记录玩家的登录历史，用于安全审计。

    Attributes:
        id: 主键ID
        player_id: 玩家ID（外键）
        login_time: 登录时间
        logout_time: 登出时间
        login_ip: 登录IP
        device_id: 设备ID
        device_type: 设备类型
        client_version: 客户端版本
        location: 登录地点（IP解析）
        is_suspicious: 是否可疑登录
    """

    __tablename__ = "player_login_logs"
    __table_args__ = (
        Index("ix_player_login_logs_player_id", "player_id"),
        Index("ix_player_login_logs_login_time", "login_time"),
        Index("ix_player_login_logs_ip", "login_ip"),
        {"comment": "玩家登录记录表"},
    )

    player_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
        comment="玩家ID",
    )

    login_time: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        comment="登录时间",
    )
    logout_time: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="登出时间",
    )

    login_ip: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
        comment="登录IP",
    )
    device_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="设备ID",
    )
    device_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="设备类型",
    )
    client_version: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="客户端版本",
    )
    location: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="登录地点",
    )

    is_suspicious: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否可疑登录",
    )

    # 关联关系
    player: Mapped[PlayerDB] = relationship(
        "PlayerDB",
        back_populates="login_logs",
    )

    def __repr__(self) -> str:
        return f"<PlayerLoginLogDB(player_id={self.player_id}, ip='{self.login_ip}')>"

    @property
    def session_duration(self) -> int | None:
        """计算会话时长（秒）"""
        if self.logout_time is None:
            return None
        return int((self.logout_time - self.login_time).total_seconds())


class PlayerInventoryDB(Base, IdMixin, TimestampMixin):
    """
    玩家背包模型

    存储玩家的道具、皮肤等物品。

    Attributes:
        id: 主键ID
        player_id: 玩家ID（外键）
        item_type: 物品类型
        item_id: 物品ID
        quantity: 数量
        extra_data: 额外数据（JSON）
        expires_at: 过期时间
    """

    __tablename__ = "player_inventory"
    __table_args__ = (
        UniqueConstraint("player_id", "item_type", "item_id", name="uq_player_item"),
        Index("ix_player_inventory_item_type", "item_type"),
        Index("ix_player_inventory_expires", "expires_at"),
        {"comment": "玩家背包表"},
    )

    player_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
        comment="玩家ID",
    )

    item_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="物品类型",
    )
    item_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="物品ID",
    )
    quantity: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="数量",
    )
    extra_data: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="额外数据",
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="过期时间",
    )

    # 关联关系
    player: Mapped[PlayerDB] = relationship(
        "PlayerDB",
        back_populates="inventory",
    )

    def __repr__(self) -> str:
        return f"<PlayerInventoryDB(player_id={self.player_id}, item='{self.item_type}:{self.item_id}')>"

    @property
    def is_expired(self) -> bool:
        """检查是否已过期"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
