"""
王者之奕 - CRUD 操作模块

导出所有 CRUD 操作类。

使用方式:
    from src.server.crud import PlayerCRUD, MatchCRUD, HeroConfigCRUD
"""

from .player import PlayerCRUD

__all__ = [
    "PlayerCRUD",
]
