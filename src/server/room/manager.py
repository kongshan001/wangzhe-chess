"""
王者之奕 - 房间管理器模块

本模块实现游戏房间的集中管理：
- RoomManager: 房间管理器（单例模式）
- 创建/销毁房间
- 玩家加入/离开房间
- 房间查找和匹配
- 线程安全操作

设计模式：
- 使用单例模式确保全局只有一个房间管理器
- 使用 asyncio.Lock 确保并发安全
- 提供丰富的查询接口
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set

import structlog

from .game_room import GameRoom, RoomState, PlayerInRoom


logger = structlog.get_logger()


@dataclass
class RoomFilter:
    """
    房间过滤条件
    
    用于查找符合条件的房间。
    
    Attributes:
        state: 房间状态（可选）
        has_space: 是否有空位
        min_players: 最少玩家数
        max_players: 最多玩家数
        exclude_full: 排除已满房间
        exclude_started: 排除已开始游戏
    """
    
    state: Optional[RoomState] = None
    has_space: Optional[bool] = None
    min_players: Optional[int] = None
    max_players: Optional[int] = None
    exclude_full: bool = True
    exclude_started: bool = True


class RoomManager:
    """
    房间管理器
    
    单例模式，管理所有游戏房间的生命周期。
    
    功能：
    - 创建和销毁房间
    - 玩家加入/离开房间
    - 房间查找和匹配
    - 空闲房间清理
    
    Attributes:
        rooms: 房间字典 {room_id: GameRoom}
        player_rooms: 玩家所在房间映射 {player_id: room_id}
        _lock: 异步锁，确保线程安全
        _room_counter: 房间计数器
    """
    
    _instance: Optional["RoomManager"] = None
    _initialized: bool = False
    
    def __new__(cls) -> "RoomManager":
        """单例模式：确保只有一个实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        """初始化房间管理器"""
        # 避免重复初始化
        if RoomManager._initialized:
            return
        
        # 房间存储
        self.rooms: Dict[str, GameRoom] = {}
        self.player_rooms: Dict[int, str] = {}
        
        # 统计信息
        self._room_counter: int = 0
        self._total_created: int = 0
        self._total_destroyed: int = 0
        
        # 异步锁
        self._lock: asyncio.Lock = asyncio.Lock()
        
        # 清理任务
        self._cleanup_task: Optional[asyncio.Task] = None
        self._cleanup_interval: int = 60  # 清理间隔（秒）
        self._idle_timeout: int = 300  # 空闲超时（秒）
        
        # 回调函数
        self._on_room_created: Optional[Callable[[GameRoom], None]] = None
        self._on_room_destroyed: Optional[Callable[[str], None]] = None
        self._on_player_join_room: Optional[Callable[[int, str], None]] = None
        self._on_player_leave_room: Optional[Callable[[int, str], None]] = None
        
        RoomManager._initialized = True
        
        logger.info("房间管理器已初始化")
    
    @classmethod
    def get_instance(cls) -> "RoomManager":
        """
        获取房间管理器实例
        
        Returns:
            房间管理器单例
        """
        return cls()
    
    @classmethod
    def reset(cls) -> None:
        """
        重置房间管理器（仅用于测试）
        
        警告：此操作会清除所有房间数据！
        """
        if cls._instance:
            cls._instance.rooms.clear()
            cls._instance.player_rooms.clear()
        cls._instance = None
        cls._initialized = False
    
    # ========================================================================
    # 回调设置
    # ========================================================================
    
    def on_room_created(self, callback: Callable[[GameRoom], None]) -> None:
        """设置房间创建回调"""
        self._on_room_created = callback
    
    def on_room_destroyed(self, callback: Callable[[str], None]) -> None:
        """设置房间销毁回调"""
        self._on_room_destroyed = callback
    
    def on_player_join_room(self, callback: Callable[[int, str], None]) -> None:
        """设置玩家加入房间回调"""
        self._on_player_join_room = callback
    
    def on_player_leave_room(self, callback: Callable[[int, str], None]) -> None:
        """设置玩家离开房间回调"""
        self._on_player_leave_room = callback
    
    # ========================================================================
    # 房间创建与销毁
    # ========================================================================
    
    async def create_room(
        self,
        name: Optional[str] = None,
        host_id: Optional[int] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> GameRoom:
        """
        创建新房间
        
        Args:
            name: 房间名称（可选）
            host_id: 房主ID（可选）
            config: 房间配置（可选）
            
        Returns:
            创建的房间实例
        """
        async with self._lock:
            self._room_counter += 1
            self._total_created += 1
            
            # 创建房间
            room = GameRoom(
                name=name,
                host_id=host_id,
                config=config,
            )
            
            self.rooms[room.room_id] = room
            
            logger.info(
                "房间已创建",
                room_id=room.room_id,
                name=room.name,
                total_rooms=len(self.rooms),
            )
            
            # 回调
            if self._on_room_created:
                try:
                    self._on_room_created(room)
                except Exception as e:
                    logger.error("房间创建回调失败", error=str(e))
            
            return room
    
    async def destroy_room(self, room_id: str) -> bool:
        """
        销毁房间
        
        Args:
            room_id: 房间ID
            
        Returns:
            是否成功销毁
        """
        async with self._lock:
            room = self.rooms.get(room_id)
            if not room:
                logger.warning("房间不存在", room_id=room_id)
                return False
            
            # 如果游戏进行中，先结束游戏
            if room.state != RoomState.FINISHED:
                await room.force_end()
            
            # 移除所有玩家映射
            for player_id in list(room.players.keys()):
                self.player_rooms.pop(player_id, None)
            
            # 删除房间
            del self.rooms[room_id]
            self._total_destroyed += 1
            
            logger.info(
                "房间已销毁",
                room_id=room_id,
                total_rooms=len(self.rooms),
            )
            
            # 回调
            if self._on_room_destroyed:
                try:
                    self._on_room_destroyed(room_id)
                except Exception as e:
                    logger.error("房间销毁回调失败", error=str(e))
            
            return True
    
    async def get_or_create_room(
        self,
        player_id: int,
        prefer_room_id: Optional[str] = None,
    ) -> Optional[GameRoom]:
        """
        获取或创建房间
        
        优先尝试加入指定房间，否则创建新房间。
        
        Args:
            player_id: 玩家ID
            prefer_room_id: 优先加入的房间ID
            
        Returns:
            房间实例
        """
        # 尝试加入指定房间
        if prefer_room_id:
            room = await self.get_room(prefer_room_id)
            if room and not room.is_full and room.state == RoomState.WAITING:
                return room
        
        # 查找可加入的房间
        available = await self.find_available_room()
        if available:
            return available
        
        # 创建新房间
        return await self.create_room(host_id=player_id)
    
    # ========================================================================
    # 玩家管理
    # ========================================================================
    
    async def join_room(
        self,
        player_id: int,
        nickname: str,
        room_id: Optional[str] = None,
        slot: Optional[int] = None,
    ) -> Optional[GameRoom]:
        """
        玩家加入房间
        
        Args:
            player_id: 玩家ID
            nickname: 玩家昵称
            room_id: 指定房间ID（可选）
            slot: 指定位置（可选）
            
        Returns:
            加入的房间实例，如果失败返回None
        """
        async with self._lock:
            # 检查玩家是否已在其他房间
            if player_id in self.player_rooms:
                existing_room_id = self.player_rooms[player_id]
                logger.warning(
                    "玩家已在房间中",
                    player_id=player_id,
                    existing_room=existing_room_id,
                )
                # 如果是同一个房间，返回该房间
                if room_id and existing_room_id == room_id:
                    return self.rooms.get(existing_room_id)
                return None
            
            # 获取目标房间
            room: Optional[GameRoom] = None
            if room_id:
                room = self.rooms.get(room_id)
            else:
                # 自动匹配房间
                room = await self.find_available_room()
            
            if not room:
                # 创建新房间
                room = await self.create_room(host_id=player_id)
            elif room.is_full:
                logger.warning("房间已满", room_id=room.room_id)
                return None
            elif room.state != RoomState.WAITING:
                logger.warning("游戏已开始", room_id=room.room_id, state=room.state.value)
                return None
            
            # 加入房间
            player = await room.add_player(player_id, nickname, slot)
            if not player:
                return None
            
            # 记录玩家所在房间
            self.player_rooms[player_id] = room.room_id
            
            logger.info(
                "玩家加入房间",
                player_id=player_id,
                room_id=room.room_id,
            )
            
            # 回调
            if self._on_player_join_room:
                try:
                    self._on_player_join_room(player_id, room.room_id)
                except Exception as e:
                    logger.error("玩家加入房间回调失败", error=str(e))
            
            return room
    
    async def leave_room(self, player_id: int) -> bool:
        """
        玩家离开房间
        
        Args:
            player_id: 玩家ID
            
        Returns:
            是否成功离开
        """
        async with self._lock:
            room_id = self.player_rooms.get(player_id)
            if not room_id:
                logger.warning("玩家不在任何房间", player_id=player_id)
                return False
            
            room = self.rooms.get(room_id)
            if not room:
                # 清理无效映射
                del self.player_rooms[player_id]
                return False
            
            # 从房间移除玩家
            success = await room.remove_player(player_id)
            if success:
                del self.player_rooms[player_id]
                
                logger.info(
                    "玩家离开房间",
                    player_id=player_id,
                    room_id=room_id,
                )
                
                # 回调
                if self._on_player_leave_room:
                    try:
                        self._on_player_leave_room(player_id, room_id)
                    except Exception as e:
                        logger.error("玩家离开房间回调失败", error=str(e))
                
                # 如果房间为空且游戏未开始，销毁房间
                if room.is_empty and room.state == RoomState.WAITING:
                    await self.destroy_room(room_id)
            
            return success
    
    async def set_player_ready(
        self,
        player_id: int,
        ready: bool = True,
    ) -> bool:
        """
        设置玩家准备状态
        
        Args:
            player_id: 玩家ID
            ready: 是否准备
            
        Returns:
            是否成功设置
        """
        room_id = self.player_rooms.get(player_id)
        if not room_id:
            return False
        
        room = self.rooms.get(room_id)
        if not room:
            return False
        
        return await room.set_player_ready(player_id, ready)
    
    async def get_player_room(self, player_id: int) -> Optional[GameRoom]:
        """
        获取玩家所在的房间
        
        Args:
            player_id: 玩家ID
            
        Returns:
            房间实例，如果玩家不在任何房间返回None
        """
        room_id = self.player_rooms.get(player_id)
        if not room_id:
            return None
        return self.rooms.get(room_id)
    
    def is_player_in_room(self, player_id: int) -> bool:
        """
        检查玩家是否在房间中
        
        Args:
            player_id: 玩家ID
            
        Returns:
            是否在房间中
        """
        return player_id in self.player_rooms
    
    # ========================================================================
    # 房间查询
    # ========================================================================
    
    async def get_room(self, room_id: str) -> Optional[GameRoom]:
        """
        获取指定房间
        
        Args:
            room_id: 房间ID
            
        Returns:
            房间实例，如果不存在返回None
        """
        return self.rooms.get(room_id)
    
    async def get_all_rooms(self) -> List[GameRoom]:
        """
        获取所有房间列表
        
        Returns:
            房间列表
        """
        return list(self.rooms.values())
    
    async def get_rooms_by_state(self, state: RoomState) -> List[GameRoom]:
        """
        获取指定状态的房间
        
        Args:
            state: 房间状态
            
        Returns:
            房间列表
        """
        return [room for room in self.rooms.values() if room.state == state]
    
    async def find_rooms(self, filter_: RoomFilter) -> List[GameRoom]:
        """
        根据条件查找房间
        
        Args:
            filter_: 过滤条件
            
        Returns:
            符合条件的房间列表
        """
        result = []
        
        for room in self.rooms.values():
            # 状态过滤
            if filter_.state and room.state != filter_.state:
                continue
            
            # 空位过滤
            if filter_.has_space is not None:
                has_space = not room.is_full
                if filter_.has_space != has_space:
                    continue
            
            # 排除已满
            if filter_.exclude_full and room.is_full:
                continue
            
            # 排除已开始
            if filter_.exclude_started and room.state != RoomState.WAITING:
                continue
            
            # 最少玩家数
            if filter_.min_players is not None:
                if room.player_count < filter_.min_players:
                    continue
            
            # 最多玩家数
            if filter_.max_players is not None:
                if room.player_count > filter_.max_players:
                    continue
            
            result.append(room)
        
        return result
    
    async def find_available_room(self) -> Optional[GameRoom]:
        """
        查找一个可加入的房间
        
        优先返回人数较多但未满的房间。
        
        Returns:
            可加入的房间，如果没有返回None
        """
        filter_ = RoomFilter(
            state=RoomState.WAITING,
            exclude_full=True,
        )
        
        available = await self.find_rooms(filter_)
        
        if not available:
            return None
        
        # 按玩家数降序排序，返回人数最多的
        available.sort(key=lambda r: r.player_count, reverse=True)
        return available[0]
    
    # ========================================================================
    # 房间清理
    # ========================================================================
    
    async def start_cleanup_task(self) -> None:
        """启动自动清理任务"""
        if self._cleanup_task:
            return
        
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("房间清理任务已启动")
    
    async def stop_cleanup_task(self) -> None:
        """停止自动清理任务"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("房间清理任务已停止")
    
    async def _cleanup_loop(self) -> None:
        """清理循环"""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                await self.cleanup_idle_rooms()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("清理任务错误", error=str(e))
    
    async def cleanup_idle_rooms(self) -> int:
        """
        清理空闲房间
        
        Returns:
            清理的房间数量
        """
        cleaned = 0
        now = time.time()
        
        async with self._lock:
            rooms_to_remove = []
            
            for room_id, room in list(self.rooms.items()):
                # 已完成的房间
                if room.state == RoomState.FINISHED:
                    rooms_to_remove.append(room_id)
                    continue
                
                # 空房间
                if room.is_empty and room.state == RoomState.WAITING:
                    rooms_to_remove.append(room_id)
                    continue
                
                # 空闲超时（所有玩家断开连接）
                if room.all_disconnected:
                    rooms_to_remove.append(room_id)
                    continue
            
            for room_id in rooms_to_remove:
                await self.destroy_room(room_id)
                cleaned += 1
        
        if cleaned > 0:
            logger.info("空闲房间清理完成", cleaned=cleaned)
        
        return cleaned
    
    # ========================================================================
    # 统计信息
    # ========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取房间管理器统计信息
        
        Returns:
            统计信息字典
        """
        state_counts = {}
        for room in self.rooms.values():
            state = room.state.value
            state_counts[state] = state_counts.get(state, 0) + 1
        
        return {
            "total_rooms": len(self.rooms),
            "total_players_in_rooms": len(self.player_rooms),
            "total_created": self._total_created,
            "total_destroyed": self._total_destroyed,
            "state_distribution": state_counts,
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "rooms": {room_id: room.to_dict() for room_id, room in self.rooms.items()},
            "stats": self.get_stats(),
        }
    
    def __repr__(self) -> str:
        return (
            f"<RoomManager(rooms={len(self.rooms)}, "
            f"players={len(self.player_rooms)})>"
        )


# 全局房间管理器实例
room_manager = RoomManager.get_instance()
