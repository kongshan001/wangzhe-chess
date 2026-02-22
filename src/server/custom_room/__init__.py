"""
王者之奕 - 自定义房间模块

本模块实现自定义房间系统（需求 #16）：

功能:
- 创建自定义房间（设置房间名、密码、人数、规则）
- 特殊规则支持（随机英雄池、固定费用、双倍经济、快速模式）
- 房间管理（房主踢人、AI填充、房间列表浏览）
- 快速加入

使用方式:
    from src.server.custom_room import (
        custom_room_manager,
        CustomRoom,
        RoomSettings,
        SpecialRuleType,
    )
    
    # 创建房间
    settings = RoomSettings(
        max_players=4,
        special_rules=[SpecialRuleType.FAST_MODE],
    )
    room = await custom_room_manager.create_room(
        host_id="player1",
        host_name="玩家1",
        settings=settings,
    )
    
    # 加入房间
    room = await custom_room_manager.join_room(
        player_id="player2",
        player_name="玩家2",
        room_id=room.room_id,
    )
    
    # 开始游戏
    await custom_room_manager.start_game(room.room_id, host_id)
"""

from .models import (
    CustomRoom,
    CustomRoomState,
    RoomPlayer,
    RoomPlayerState,
    RoomSettings,
    SpecialRuleType,
)

from .manager import (
    CustomRoomFilter,
    CustomRoomManager,
    custom_room_manager,
)


__all__ = [
    # 数据模型
    "CustomRoom",
    "CustomRoomState",
    "RoomPlayer",
    "RoomPlayerState",
    "RoomSettings",
    "SpecialRuleType",
    # 管理器
    "CustomRoomManager",
    "CustomRoomFilter",
    "custom_room_manager",
]
