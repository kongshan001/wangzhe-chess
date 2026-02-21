"""
王者之奕 - CRUD 操作模块

本模块导出所有 CRUD 操作类：
- PlayerCRUD: 玩家 CRUD 操作
- PlayerStatsCRUD: 玩家统计 CRUD 操作

使用方式:
    from src.server.crud import PlayerCRUD, PlayerStatsCRUD
    
    async with get_session() as session:
        player = await PlayerCRUD.get_by_id(session, 1)
"""

from .player import PlayerCRUD, PlayerStatsCRUD

__all__ = [
    "PlayerCRUD",
    "PlayerStatsCRUD",
]
