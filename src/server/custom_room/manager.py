"""
王者之奕 - 自定义房间管理器

本模块实现自定义房间系统的核心管理逻辑：
- CustomRoomManager: 自定义房间管理器（单例）
- 房间创建/销毁
- 玩家加入/离开
- AI 填充
- 房间查找
- 数据持久化回调

功能清单：
- 创建房间
- 加入房间
- 离开房间
- 踢出玩家
- 开始游戏
- AI 填充
- 获取房间列表
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import structlog

from .models import (
    CustomRoom,
    CustomRoomState,
    RoomPlayer,
    RoomSettings,
    SpecialRuleType,
)

logger = structlog.get_logger()


@dataclass
class CustomRoomFilter:
    """
    自定义房间过滤条件

    用于查找符合条件的房间。

    Attributes:
        state: 房间状态
        has_space: 是否有空位
        has_password: 是否有密码
        min_players: 最少玩家数
        max_players: 最多玩家数
        special_rules: 包含的特殊规则
        exclude_full: 排除已满房间
        exclude_started: 排除已开始游戏
        exclude_password: 排除有密码房间
    """

    state: CustomRoomState | None = None
    has_space: bool | None = None
    has_password: bool | None = None
    min_players: int | None = None
    max_players: int | None = None
    special_rules: list[SpecialRuleType] | None = None
    exclude_full: bool = True
    exclude_started: bool = True
    exclude_password: bool = False


class CustomRoomManager:
    """
    自定义房间管理器

    单例模式，管理所有自定义房间的生命周期。

    功能：
    - 创建/销毁房间
    - 玩家加入/离开/踢出
    - AI 填充
    - 房间查找和匹配
    - 自动清理空闲房间

    Attributes:
        rooms: 房间字典 {room_id: CustomRoom}
        player_rooms: 玩家所在房间 {player_id: room_id}
        _lock: 异步锁
        _room_counter: 房间计数器
    """

    _instance: CustomRoomManager | None = None
    _initialized: bool = False

    def __new__(cls) -> CustomRoomManager:
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """初始化管理器"""
        if CustomRoomManager._initialized:
            return

        # 房间存储
        self.rooms: dict[str, CustomRoom] = {}
        self.player_rooms: dict[str, str] = {}

        # 统计信息
        self._room_counter: int = 0
        self._total_created: int = 0
        self._total_destroyed: int = 0

        # 异步锁
        self._lock: asyncio.Lock = asyncio.Lock()

        # 清理任务
        self._cleanup_task: asyncio.Task | None = None
        self._cleanup_interval: int = 60  # 清理间隔（秒）
        self._idle_timeout: int = 300  # 空闲超时（秒）

        # AI 填充任务
        self._ai_fill_tasks: dict[str, asyncio.Task] = {}

        # 回调函数
        self._on_room_created: Callable[[CustomRoom], None] | None = None
        self._on_room_destroyed: Callable[[str], None] | None = None
        self._on_player_join: Callable[[str, str, CustomRoom], None] | None = None
        self._on_player_leave: Callable[[str, str, CustomRoom], None] | None = None
        self._on_player_kicked: Callable[[str, str, CustomRoom], None] | None = None
        self._on_game_start: Callable[[CustomRoom], None] | None = None
        self._on_room_updated: Callable[[CustomRoom], None] | None = None

        CustomRoomManager._initialized = True

        logger.info("自定义房间管理器已初始化")

    @classmethod
    def get_instance(cls) -> CustomRoomManager:
        """获取管理器实例"""
        return cls()

    @classmethod
    def reset(cls) -> None:
        """
        重置管理器（仅用于测试）

        警告：此操作会清除所有房间数据！
        """
        if cls._instance:
            # 取消所有 AI 填充任务
            for task in cls._instance._ai_fill_tasks.values():
                task.cancel()
            cls._instance.rooms.clear()
            cls._instance.player_rooms.clear()
            cls._instance._ai_fill_tasks.clear()
        cls._instance = None
        cls._initialized = False

    # ========================================================================
    # 回调设置
    # ========================================================================

    def on_room_created(self, callback: Callable[[CustomRoom], None]) -> None:
        """设置房间创建回调"""
        self._on_room_created = callback

    def on_room_destroyed(self, callback: Callable[[str], None]) -> None:
        """设置房间销毁回调"""
        self._on_room_destroyed = callback

    def on_player_join(
        self,
        callback: Callable[[str, str, CustomRoom], None],
    ) -> None:
        """设置玩家加入回调"""
        self._on_player_join = callback

    def on_player_leave(
        self,
        callback: Callable[[str, str, CustomRoom], None],
    ) -> None:
        """设置玩家离开回调"""
        self._on_player_leave = callback

    def on_player_kicked(
        self,
        callback: Callable[[str, str, CustomRoom], None],
    ) -> None:
        """设置玩家被踢回调"""
        self._on_player_kicked = callback

    def on_game_start(self, callback: Callable[[CustomRoom], None]) -> None:
        """设置游戏开始回调"""
        self._on_game_start = callback

    def on_room_updated(self, callback: Callable[[CustomRoom], None]) -> None:
        """设置房间更新回调"""
        self._on_room_updated = callback

    # ========================================================================
    # 房间创建与销毁
    # ========================================================================

    async def create_room(
        self,
        host_id: str,
        host_name: str,
        name: str | None = None,
        settings: RoomSettings | None = None,
    ) -> CustomRoom:
        """
        创建自定义房间

        Args:
            host_id: 房主ID
            host_name: 房主昵称
            name: 房间名称（可选）
            settings: 房间设置（可选）

        Returns:
            创建的房间实例
        """
        async with self._lock:
            self._room_counter += 1
            self._total_created += 1

            # 创建房间
            room = CustomRoom(
                name=name,
                host_id=host_id,
                settings=settings or RoomSettings(),
            )

            self.rooms[room.room_id] = room

            # 房主加入房间
            player = room.add_player(
                player_id=host_id,
                nickname=host_name,
                slot=0,
            )
            if player:
                player.is_host = True
                self.player_rooms[host_id] = room.room_id

            logger.info(
                "自定义房间已创建",
                room_id=room.room_id,
                name=room.name,
                host_id=host_id,
                total_rooms=len(self.rooms),
            )

            # 回调
            if self._on_room_created:
                try:
                    self._on_room_created(room)
                except Exception as e:
                    logger.error("房间创建回调失败", error=str(e))

            # 如果启用了 AI 填充，启动填充任务
            if room.settings.ai_fill:
                self._schedule_ai_fill(room)

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

            # 取消 AI 填充任务
            if room_id in self._ai_fill_tasks:
                self._ai_fill_tasks[room_id].cancel()
                del self._ai_fill_tasks[room_id]

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

    # ========================================================================
    # 玩家管理
    # ========================================================================

    async def join_room(
        self,
        player_id: str,
        player_name: str,
        room_id: str | None = None,
        password: str | None = None,
        slot: int | None = None,
    ) -> CustomRoom | None:
        """
        玩家加入房间

        Args:
            player_id: 玩家ID
            player_name: 玩家昵称
            room_id: 指定房间ID（可选）
            password: 房间密码（可选）
            slot: 指定位置（可选）

        Returns:
            加入的房间实例，失败返回None
        """
        async with self._lock:
            # 检查玩家是否已在其他房间
            if player_id in self.player_rooms:
                existing_room_id = self.player_rooms[player_id]
                # 如果是同一个房间，返回该房间
                if room_id and existing_room_id == room_id:
                    return self.rooms.get(existing_room_id)
                logger.warning(
                    "玩家已在其他房间",
                    player_id=player_id,
                    existing_room=existing_room_id,
                )
                return None

            # 获取目标房间
            room: CustomRoom | None = None
            if room_id:
                room = self.rooms.get(room_id)
                if not room:
                    logger.warning("房间不存在", room_id=room_id)
                    return None
            else:
                # 自动匹配房间
                room = await self.find_available_room()
                if not room:
                    logger.info("没有可用房间，需要创建")
                    return None

            # 检查房间状态
            if room.state != CustomRoomState.WAITING:
                logger.warning("游戏已开始", room_id=room.room_id)
                return None

            # 检查房间是否已满
            if room.is_full:
                logger.warning("房间已满", room_id=room.room_id)
                return None

            # 检查密码
            if room.has_password:
                if password != room.settings.password:
                    logger.warning("密码错误", room_id=room.room_id)
                    return None

            # 加入房间
            player = room.add_player(
                player_id=player_id,
                nickname=player_name,
                slot=slot,
            )

            if not player:
                return None

            # 记录玩家所在房间
            self.player_rooms[player_id] = room.room_id

            # 如果有 AI 在等待中，取消一个 AI（真人优先）
            await self._maybe_remove_ai_for_human(room)

            logger.info(
                "玩家加入房间",
                player_id=player_id,
                room_id=room.room_id,
            )

            # 回调
            if self._on_player_join:
                try:
                    self._on_player_join(player_id, player_name, room)
                except Exception as e:
                    logger.error("玩家加入回调失败", error=str(e))

            if self._on_room_updated:
                try:
                    self._on_room_updated(room)
                except Exception as e:
                    logger.error("房间更新回调失败", error=str(e))

            return room

    async def leave_room(self, player_id: str) -> bool:
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

            # 移除玩家
            player = room.remove_player(player_id)
            if player:
                del self.player_rooms[player_id]

                logger.info(
                    "玩家离开房间",
                    player_id=player_id,
                    room_id=room_id,
                )

                # 回调
                if self._on_player_leave:
                    try:
                        self._on_player_leave(player_id, player.nickname, room)
                    except Exception as e:
                        logger.error("玩家离开回调失败", error=str(e))

                # 如果房间为空，销毁房间
                if room.is_empty:
                    await self.destroy_room(room_id)
                elif self._on_room_updated:
                    try:
                        self._on_room_updated(room)
                    except Exception as e:
                        logger.error("房间更新回调失败", error=str(e))

            return True

    async def kick_player(
        self,
        room_id: str,
        host_id: str,
        target_id: str,
    ) -> bool:
        """
        房主踢出玩家

        Args:
            room_id: 房间ID
            host_id: 房主ID
            target_id: 被踢玩家ID

        Returns:
            是否成功踢出
        """
        async with self._lock:
            room = self.rooms.get(room_id)
            if not room:
                logger.warning("房间不存在", room_id=room_id)
                return False

            # 检查是否是房主
            if room.host_id != host_id:
                logger.warning("非房主无法踢人", host_id=host_id)
                return False

            # 不能踢自己
            if host_id == target_id:
                logger.warning("不能踢自己")
                return False

            # 检查目标是否在房间
            target = room.get_player(target_id)
            if not target:
                logger.warning("目标玩家不在房间", target_id=target_id)
                return False

            # 移除玩家
            player = room.remove_player(target_id)
            if player:
                self.player_rooms.pop(target_id, None)

                logger.info(
                    "玩家被踢出",
                    target_id=target_id,
                    room_id=room_id,
                    host_id=host_id,
                )

                # 回调
                if self._on_player_kicked:
                    try:
                        self._on_player_kicked(target_id, player.nickname, room)
                    except Exception as e:
                        logger.error("踢人回调失败", error=str(e))

                if self._on_room_updated:
                    try:
                        self._on_room_updated(room)
                    except Exception as e:
                        logger.error("房间更新回调失败", error=str(e))

            return True

    async def set_player_ready(
        self,
        player_id: str,
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

        success = room.set_player_ready(player_id, ready)

        if success and self._on_room_updated:
            try:
                self._on_room_updated(room)
            except Exception as e:
                logger.error("房间更新回调失败", error=str(e))

        return success

    # ========================================================================
    # AI 填充
    # ========================================================================

    def _schedule_ai_fill(self, room: CustomRoom) -> None:
        """
        安排 AI 填充任务

        Args:
            room: 房间实例
        """
        if room.room_id in self._ai_fill_tasks:
            return

        async def fill_task():
            await asyncio.sleep(room.settings.ai_fill_delay)
            await self.fill_room_with_ai(room.room_id)

        self._ai_fill_tasks[room.room_id] = asyncio.create_task(fill_task())
        logger.info("AI 填充任务已安排", room_id=room.room_id)

    async def _maybe_remove_ai_for_human(self, room: CustomRoom) -> None:
        """
        为真人玩家腾出位置（移除一个 AI）

        Args:
            room: 房间实例
        """
        # 如果房间未满，不需要移除
        if not room.is_full:
            return

        # 找到一个 AI 移除
        for player_id, player in list(room.players.items()):
            if player.is_ai:
                room.remove_player(player_id)
                logger.info(
                    "为真人玩家移除 AI",
                    room_id=room.room_id,
                    removed_ai=player_id,
                )
                break

    async def fill_room_with_ai(
        self,
        room_id: str,
        count: int | None = None,
    ) -> list[RoomPlayer]:
        """
        用 AI 填充房间

        Args:
            room_id: 房间ID
            count: 填充数量（None 表示填满）

        Returns:
            添加的 AI 玩家列表
        """
        async with self._lock:
            room = self.rooms.get(room_id)
            if not room:
                logger.warning("房间不存在", room_id=room_id)
                return []

            if room.state != CustomRoomState.WAITING:
                logger.warning("游戏已开始，无法填充 AI")
                return []

            # 填充 AI
            added_players = room.fill_with_ai(count)

            if added_players:
                logger.info(
                    "AI 已填充",
                    room_id=room_id,
                    ai_count=len(added_players),
                )

                if self._on_room_updated:
                    try:
                        self._on_room_updated(room)
                    except Exception as e:
                        logger.error("房间更新回调失败", error=str(e))

            return added_players

    # ========================================================================
    # 游戏控制
    # ========================================================================

    async def start_game(self, room_id: str, host_id: str) -> bool:
        """
        开始游戏

        Args:
            room_id: 房间ID
            host_id: 房主ID

        Returns:
            是否成功开始
        """
        async with self._lock:
            room = self.rooms.get(room_id)
            if not room:
                logger.warning("房间不存在", room_id=room_id)
                return False

            # 检查是否是房主
            if room.host_id != host_id:
                logger.warning("非房主无法开始游戏", host_id=host_id)
                return False

            # 检查是否可以开始
            if not room.can_start:
                logger.warning("无法开始游戏", reason="玩家未全部准备或人数不足")
                return False

            # 取消 AI 填充任务
            if room_id in self._ai_fill_tasks:
                self._ai_fill_tasks[room_id].cancel()
                del self._ai_fill_tasks[room_id]

            # 开始游戏
            success = room.start_game()

            if success:
                logger.info(
                    "游戏已开始",
                    room_id=room_id,
                    player_count=room.player_count,
                )

                # 回调
                if self._on_game_start:
                    try:
                        self._on_game_start(room)
                    except Exception as e:
                        logger.error("游戏开始回调失败", error=str(e))

            return success

    async def end_game(self, room_id: str) -> bool:
        """
        结束游戏

        Args:
            room_id: 房间ID

        Returns:
            是否成功结束
        """
        async with self._lock:
            room = self.rooms.get(room_id)
            if not room:
                return False

            room.end_game()

            logger.info(
                "游戏已结束",
                room_id=room_id,
            )

            return True

    # ========================================================================
    # 房间查询
    # ========================================================================

    async def get_room(self, room_id: str) -> CustomRoom | None:
        """获取指定房间"""
        return self.rooms.get(room_id)

    async def get_all_rooms(self) -> list[CustomRoom]:
        """获取所有房间列表"""
        return list(self.rooms.values())

    async def get_rooms_by_state(
        self,
        state: CustomRoomState,
    ) -> list[CustomRoom]:
        """获取指定状态的房间"""
        return [room for room in self.rooms.values() if room.state == state]

    async def find_rooms(self, filter_: CustomRoomFilter) -> list[CustomRoom]:
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

            # 密码过滤
            if filter_.has_password is not None:
                if filter_.has_password != room.has_password:
                    continue

            # 排除有密码
            if filter_.exclude_password and room.has_password:
                continue

            # 排除已满
            if filter_.exclude_full and room.is_full:
                continue

            # 排除已开始
            if filter_.exclude_started and room.state != CustomRoomState.WAITING:
                continue

            # 最少玩家数
            if filter_.min_players is not None:
                if room.player_count < filter_.min_players:
                    continue

            # 最多玩家数
            if filter_.max_players is not None:
                if room.player_count > filter_.max_players:
                    continue

            # 特殊规则过滤
            if filter_.special_rules:
                for rule in filter_.special_rules:
                    if not room.settings.has_rule(rule):
                        break
                else:
                    result.append(room)
                continue

            result.append(room)

        return result

    async def find_available_room(
        self,
        exclude_password: bool = True,
    ) -> CustomRoom | None:
        """
        查找一个可加入的房间

        优先返回人数较多但未满的房间。

        Args:
            exclude_password: 是否排除有密码的房间

        Returns:
            可加入的房间，如果没有返回None
        """
        filter_ = CustomRoomFilter(
            state=CustomRoomState.WAITING,
            exclude_full=True,
            exclude_password=exclude_password,
        )

        available = await self.find_rooms(filter_)

        if not available:
            return None

        # 按玩家数降序排序，返回人数最多的
        available.sort(key=lambda r: r.player_count, reverse=True)
        return available[0]

    async def get_player_room(self, player_id: str) -> CustomRoom | None:
        """获取玩家所在的房间"""
        room_id = self.player_rooms.get(player_id)
        if not room_id:
            return None
        return self.rooms.get(room_id)

    def is_player_in_room(self, player_id: str) -> bool:
        """检查玩家是否在房间中"""
        return player_id in self.player_rooms

    # ========================================================================
    # 房间清理
    # ========================================================================

    async def start_cleanup_task(self) -> None:
        """启动自动清理任务"""
        if self._cleanup_task:
            return

        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("自定义房间清理任务已启动")

    async def stop_cleanup_task(self) -> None:
        """停止自动清理任务"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("自定义房间清理任务已停止")

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
        time.time()

        async with self._lock:
            rooms_to_remove = []

            for room_id, room in list(self.rooms.items()):
                # 已完成的房间
                if room.state == CustomRoomState.FINISHED:
                    rooms_to_remove.append(room_id)
                    continue

                # 空房间
                if room.is_empty and room.state == CustomRoomState.WAITING:
                    rooms_to_remove.append(room_id)
                    continue

                # 空闲超时（只有 AI 的房间）
                if room.human_count == 0 and room.ai_count > 0:
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

    def get_stats(self) -> dict[str, Any]:
        """获取管理器统计信息"""
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

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "rooms": {room_id: room.to_summary() for room_id, room in self.rooms.items()},
            "stats": self.get_stats(),
        }

    def __repr__(self) -> str:
        return f"<CustomRoomManager(rooms={len(self.rooms)}, players={len(self.player_rooms)})>"


# 全局管理器实例
custom_room_manager = CustomRoomManager.get_instance()
