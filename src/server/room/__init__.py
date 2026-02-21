"""
王者之奕 - 房间管理模块

本模块提供游戏房间的创建、管理和匹配功能：
- GameRoom: 游戏房间，管理8人对局
- RoomManager: 房间管理器（单例），统一管理所有房间
- RoomState: 房间状态枚举
- PlayerState: 玩家状态枚举
- PlayerInRoom: 房间内的玩家数据
- RoomFilter: 房间过滤条件

使用方式：
    from src.server.room import RoomManager, GameRoom, RoomState
    
    # 获取房间管理器
    manager = RoomManager.get_instance()
    
    # 创建房间
    room = await manager.create_room(name="测试房间")
    
    # 玩家加入
    await manager.join_room(player_id=1, nickname="玩家1", room_id=room.room_id)
    
    # 设置准备
    await manager.set_player_ready(player_id=1, ready=True)
    
    # 查找可加入的房间
    available = await manager.find_available_room()

游戏流程：
1. 玩家加入房间（WAITING 状态）
2. 所有玩家准备（PREPARING 状态）
3. 开始游戏循环：
   - 准备阶段：购买英雄、调整阵容
   - 战斗阶段：自动进行对战
   - 结算阶段：计算结果、更新血量
4. 游戏结束（FINISHED 状态）

线程安全：
- RoomManager 使用 asyncio.Lock 确保并发安全
- 所有公开方法都是异步的
- 建议在 FastAPI 的异步上下文中使用
"""

from .game_room import (
    GameRoom,
    RoomState,
    PlayerState,
    PlayerInRoom,
)

from .manager import (
    RoomManager,
    RoomFilter,
    room_manager,
)


__all__ = [
    # 游戏房间
    "GameRoom",
    "RoomState",
    "PlayerState",
    "PlayerInRoom",
    # 房间管理
    "RoomManager",
    "RoomFilter",
    "room_manager",
]
