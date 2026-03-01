"""
王者之奕 - 数据模型模块

导出所有数据库模型。

使用方式:
    from src.server.models import PlayerDB, MatchRecordDB, HeroConfigDB
"""

from .base import Base, IdMixin, TimestampMixin

# 配置相关模型
from .hero_config import (
    GameConfigDB,
    HeroConfigDB,
    HeroStatus,
    HeroVersionDB,
    SeasonConfigDB,
    SynergyConfigDB,
    SynergyType,
)

# 对局相关模型
from .match_record import (
    MatchPlayerResultDB,
    MatchRecordDB,
    MatchStatus,
)

# 玩家相关模型
from .player import (
    PlayerDB,
    PlayerInventoryDB,
    PlayerLoginLogDB,
    PlayerRankDB,
    PlayerStatsDB,
    RankTier,
)

# 导出所有模型类
__all__ = [
    # 基础类
    "Base",
    "IdMixin",
    "TimestampMixin",
    # 玩家相关
    "PlayerDB",
    "PlayerRankDB",
    "PlayerStatsDB",
    "PlayerLoginLogDB",
    "PlayerInventoryDB",
    "RankTier",
    # 对局相关
    "MatchRecordDB",
    "MatchPlayerResultDB",
    "MatchStatus",
    # 配置相关
    "HeroConfigDB",
    "HeroVersionDB",
    "SynergyConfigDB",
    "GameConfigDB",
    "SeasonConfigDB",
    "HeroStatus",
    "SynergyType",
]
