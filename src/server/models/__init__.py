"""
王者之奕 - 数据模型模块

导出所有数据库模型和数据类型。

使用方式:
    from src.server.models import Player, MatchRecord, HeroConfig
"""

from .base import Base, BaseModel, IDMixin, TimestampMixin, JSONEncodedType
from .player import (
    Player,
    PlayerRank,
    PlayerStats,
    PlayerLoginLog,
    PlayerInventory,
    RankTier,
)
from .match import (
    MatchRecord,
    MatchPlayer,
    MatchSnapshot,
    MatchReplay,
    BattleLog,
    MatchStatus,
    MatchType,
)
from .hero_config import (
    HeroConfig,
    HeroVersion,
    SynergyConfig,
    GameConfig,
    SeasonConfig,
    HeroStatus,
    SynergyType,
)

# 导出所有模型类
__all__ = [
    # 基础类
    "Base",
    "BaseModel",
    "IDMixin",
    "TimestampMixin",
    "JSONEncodedType",
    # 玩家相关
    "Player",
    "PlayerRank",
    "PlayerStats",
    "PlayerLoginLog",
    "PlayerInventory",
    "RankTier",
    # 对局相关
    "MatchRecord",
    "MatchPlayer",
    "MatchSnapshot",
    "MatchReplay",
    "BattleLog",
    "MatchStatus",
    "MatchType",
    # 配置相关
    "HeroConfig",
    "HeroVersion",
    "SynergyConfig",
    "GameConfig",
    "SeasonConfig",
    "HeroStatus",
    "SynergyType",
]
