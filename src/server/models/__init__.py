"""
王者之奕 - 数据模型模块

本模块导出所有 SQLAlchemy ORM 模型：
- Base: 声明式基类
- PlayerDB: 玩家账户模型
- PlayerStatsDB: 玩家统计模型
- MatchRecordDB: 对局记录模型
- MatchPlayerResultDB: 玩家对局结果模型

使用方式:
    from src.server.models import Base, PlayerDB, PlayerStatsDB
    from src.server.models import MatchRecordDB, MatchPlayerResultDB
"""

from .base import Base, IdMixin, TimestampMixin
from .player import PlayerDB, PlayerStatsDB
from .match_record import MatchRecordDB, MatchPlayerResultDB, MatchStatus

__all__ = [
    # 基础类
    "Base",
    "IdMixin",
    "TimestampMixin",
    # 玩家模型
    "PlayerDB",
    "PlayerStatsDB",
    # 对局模型
    "MatchRecordDB",
    "MatchPlayerResultDB",
    "MatchStatus",
]
