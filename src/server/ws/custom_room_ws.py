"""
王者之奕 - 自定义房间 WebSocket 处理器

本模块实现自定义房间系统（需求 #16）的 WebSocket 消息处理：
- CREATE_CUSTOM_ROOM / CUSTOM_ROOM_CREATED
- JOIN_CUSTOM_ROOM / CUSTOM_ROOM_JOINED
- LEAVE_CUSTOM_ROOM / CUSTOM_ROOM_LEFT
- KICK_PLAYER / PLAYER_KICKED
- START_CUSTOM_GAME / CUSTOM_GAME_STARTED
- GET_CUSTOM_ROOM_LIST / CUSTOM_ROOM_LIST
- AI_FILL_ROOM / AI_FILLED

与主 WebSocket 处理器集成。
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from ...shared.protocol import (
    BaseMessage,
    ErrorMessage,
    MessageType,
)
from ..custom_room import (
    CustomRoom,
    CustomRoomState,
    RoomSettings,
    SpecialRuleType,
    custom_room_manager,
)

if TYPE_CHECKING:
    from ..ws.handler import Session

logger = logging.getLogger(__name__)


# ============================================================================
# 自定义房间消息类型扩展
# ============================================================================


# 扩展 MessageType 枚举
class CustomRoomMessageType(str):
    """自定义房间消息类型"""

    # 客户端 -> 服务器
    CREATE_CUSTOM_ROOM = "create_custom_room"  # 创建自定义房间
    JOIN_CUSTOM_ROOM = "join_custom_room"  # 加入自定义房间
    LEAVE_CUSTOM_ROOM = "leave_custom_room"  # 离开自定义房间
    KICK_PLAYER = "kick_player"  # 踢出玩家
    START_CUSTOM_GAME = "start_custom_game"  # 开始自定义游戏
    GET_CUSTOM_ROOM_LIST = "get_custom_room_list"  # 获取自定义房间列表
    AI_FILL_ROOM = "ai_fill_room"  # AI 填充房间
    SET_PLAYER_READY = "set_player_ready"  # 设置准备状态

    # 服务器 -> 客户端
    CUSTOM_ROOM_CREATED = "custom_room_created"  # 房间创建成功
    CUSTOM_ROOM_JOINED = "custom_room_joined"  # 加入房间成功
    CUSTOM_ROOM_LEFT = "custom_room_left"  # 离开房间成功
    PLAYER_KICKED = "player_kicked"  # 玩家被踢出
    CUSTOM_GAME_STARTED = "custom_game_started"  # 游戏开始
    CUSTOM_ROOM_LIST = "custom_room_list"  # 房间列表
    AI_FILLED = "ai_filled"  # AI 填充完成
    CUSTOM_ROOM_UPDATED = "custom_room_updated"  # 房间状态更新


# ============================================================================
# 自定义房间消息数据类
# ============================================================================


class SpecialRuleData(BaseModel):
    """特殊规则数据"""

    rule_type: str = Field(..., description="规则类型")
    params: dict[str, Any] = Field(default_factory=dict, description="规则参数")


class CustomRoomSettingsData(BaseModel):
    """自定义房间设置数据"""

    max_players: int = Field(default=8, ge=2, le=8, description="最大玩家数")
    has_password: bool = Field(default=False, description="是否有密码")
    special_rules: list[str] = Field(default_factory=list, description="特殊规则")
    round_time: int = Field(default=30, description="回合时间")
    prepare_time: int = Field(default=30, description="准备时间")
    starting_gold: int = Field(default=10, description="初始金币")
    starting_hp: int = Field(default=100, description="初始生命值")
    ai_fill: bool = Field(default=True, description="是否允许AI填充")


class CustomRoomPlayerData(BaseModel):
    """自定义房间玩家数据"""

    player_id: str = Field(..., description="玩家ID")
    nickname: str = Field(..., description="昵称")
    avatar: str | None = Field(default=None, description="头像")
    slot: int = Field(..., description="位置")
    state: str = Field(..., description="状态")
    is_host: bool = Field(default=False, description="是否房主")
    is_ai: bool = Field(default=False, description="是否AI")


class CustomRoomInfoData(BaseModel):
    """自定义房间信息数据"""

    room_id: str = Field(..., description="房间ID")
    name: str = Field(..., description="房间名称")
    host_id: str | None = Field(default=None, description="房主ID")
    settings: CustomRoomSettingsData = Field(..., description="房间设置")
    players: list[CustomRoomPlayerData] = Field(default_factory=list, description="玩家列表")
    state: str = Field(..., description="房间状态")
    player_count: int = Field(default=0, description="玩家数量")
    created_at: str = Field(..., description="创建时间")


class CustomRoomSummaryData(BaseModel):
    """自定义房间简要信息（用于列表）"""

    room_id: str = Field(..., description="房间ID")
    name: str = Field(..., description="房间名称")
    host_name: str = Field(..., description="房主昵称")
    player_count: int = Field(default=0, description="玩家数量")
    max_players: int = Field(default=8, description="最大玩家数")
    has_password: bool = Field(default=False, description="是否有密码")
    state: str = Field(..., description="房间状态")
    special_rules: list[str] = Field(default_factory=list, description="特殊规则")


# ============================================================================
# 自定义房间消息类
# ============================================================================


class CreateCustomRoomMessage(BaseMessage):
    """
    创建自定义房间请求

    Attributes:
        room_name: 房间名称
        password: 房间密码
        max_players: 最大玩家数 (2-8)
        special_rules: 特殊规则列表
        ai_fill: 是否允许AI填充
    """

    type: MessageType = Field(default=MessageType(CustomRoomMessageType.CREATE_CUSTOM_ROOM))
    room_name: str = Field(..., description="房间名称")
    password: str | None = Field(default=None, description="房间密码")
    max_players: int = Field(default=8, ge=2, le=8, description="最大玩家数")
    special_rules: list[str] = Field(default_factory=list, description="特殊规则")
    round_time: int = Field(default=30, description="回合时间")
    prepare_time: int = Field(default=30, description="准备时间")
    ai_fill: bool = Field(default=True, description="是否允许AI填充")


class CustomRoomCreatedMessage(BaseMessage):
    """
    房间创建成功响应

    Attributes:
        room_id: 房间ID
        room_info: 房间信息
    """

    type: MessageType = Field(default=MessageType(CustomRoomMessageType.CUSTOM_ROOM_CREATED))
    room_id: str = Field(..., description="房间ID")
    room_info: CustomRoomInfoData = Field(..., description="房间信息")


class JoinCustomRoomMessage(BaseMessage):
    """
    加入自定义房间请求

    Attributes:
        room_id: 房间ID（可选，不提供则自动匹配）
        password: 房间密码
    """

    type: MessageType = Field(default=MessageType(CustomRoomMessageType.JOIN_CUSTOM_ROOM))
    room_id: str | None = Field(default=None, description="房间ID")
    password: str | None = Field(default=None, description="房间密码")


class CustomRoomJoinedMessage(BaseMessage):
    """
    加入房间成功响应

    Attributes:
        room_id: 房间ID
        room_info: 房间信息
        my_slot: 自己的位置
    """

    type: MessageType = Field(default=MessageType(CustomRoomMessageType.CUSTOM_ROOM_JOINED))
    room_id: str = Field(..., description="房间ID")
    room_info: CustomRoomInfoData = Field(..., description="房间信息")
    my_slot: int = Field(..., description="自己的位置")


class LeaveCustomRoomMessage(BaseMessage):
    """离开自定义房间请求"""

    type: MessageType = Field(default=MessageType(CustomRoomMessageType.LEAVE_CUSTOM_ROOM))


class CustomRoomLeftMessage(BaseMessage):
    """
    离开房间成功响应

    Attributes:
        room_id: 房间ID
    """

    type: MessageType = Field(default=MessageType(CustomRoomMessageType.CUSTOM_ROOM_LEFT))
    room_id: str = Field(..., description="房间ID")


class KickPlayerMessage(BaseMessage):
    """
    踢出玩家请求

    Attributes:
        target_id: 被踢玩家ID
    """

    type: MessageType = Field(default=MessageType(CustomRoomMessageType.KICK_PLAYER))
    target_id: str = Field(..., description="被踢玩家ID")


class PlayerKickedMessage(BaseMessage):
    """
    玩家被踢出通知

    Attributes:
        room_id: 房间ID
        player_id: 被踢玩家ID
        player_name: 被踢玩家昵称
    """

    type: MessageType = Field(default=MessageType(CustomRoomMessageType.PLAYER_KICKED))
    room_id: str = Field(..., description="房间ID")
    player_id: str = Field(..., description="被踢玩家ID")
    player_name: str = Field(..., description="被踢玩家昵称")


class StartCustomGameMessage(BaseMessage):
    """开始自定义游戏请求"""

    type: MessageType = Field(default=MessageType(CustomRoomMessageType.START_CUSTOM_GAME))


class CustomGameStartedMessage(BaseMessage):
    """
    游戏开始通知

    Attributes:
        room_id: 房间ID
        room_info: 房间信息
    """

    type: MessageType = Field(default=MessageType(CustomRoomMessageType.CUSTOM_GAME_STARTED))
    room_id: str = Field(..., description="房间ID")
    room_info: CustomRoomInfoData = Field(..., description="房间信息")


class GetCustomRoomListMessage(BaseMessage):
    """获取自定义房间列表请求"""

    type: MessageType = Field(default=MessageType(CustomRoomMessageType.GET_CUSTOM_ROOM_LIST))


class CustomRoomListMessage(BaseMessage):
    """
    房间列表响应

    Attributes:
        rooms: 房间列表
        total_count: 总数量
    """

    type: MessageType = Field(default=MessageType(CustomRoomMessageType.CUSTOM_ROOM_LIST))
    rooms: list[CustomRoomSummaryData] = Field(default_factory=list, description="房间列表")
    total_count: int = Field(default=0, description="总数量")


class AIFillRoomMessage(BaseMessage):
    """
    AI 填充房间请求

    Attributes:
        count: 填充数量（可选，不提供则填满）
    """

    type: MessageType = Field(default=MessageType(CustomRoomMessageType.AI_FILL_ROOM))
    count: int | None = Field(default=None, description="填充数量")


class AIFilledMessage(BaseMessage):
    """
    AI 填充完成通知

    Attributes:
        room_id: 房间ID
        ai_count: 添加的AI数量
        room_info: 更新后的房间信息
    """

    type: MessageType = Field(default=MessageType(CustomRoomMessageType.AI_FILLED))
    room_id: str = Field(..., description="房间ID")
    ai_count: int = Field(default=0, description="添加的AI数量")
    room_info: CustomRoomInfoData = Field(..., description="更新后的房间信息")


class SetPlayerReadyMessage(BaseMessage):
    """
    设置准备状态请求

    Attributes:
        ready: 是否准备
    """

    type: MessageType = Field(default=MessageType(CustomRoomMessageType.SET_PLAYER_READY))
    ready: bool = Field(default=True, description="是否准备")


class CustomRoomUpdatedMessage(BaseMessage):
    """
    房间状态更新通知

    Attributes:
        room_info: 更新后的房间信息
        event: 更新事件类型
        event_data: 事件数据
    """

    type: MessageType = Field(default=MessageType(CustomRoomMessageType.CUSTOM_ROOM_UPDATED))
    room_info: CustomRoomInfoData = Field(..., description="房间信息")
    event: str = Field(..., description="事件类型")
    event_data: dict[str, Any] = Field(default_factory=dict, description="事件数据")


# ============================================================================
# 自定义房间 WebSocket 处理器
# ============================================================================


class CustomRoomWSHandler:
    """
    自定义房间 WebSocket 处理器

    处理所有自定义房间相关的 WebSocket 消息。
    """

    def __init__(self) -> None:
        """初始化处理器"""
        self.manager = custom_room_manager
        self._ws_handler = None

    def set_ws_handler(self, handler: Any) -> None:
        """设置 WebSocket 处理器引用"""
        self._ws_handler = handler

        # 设置回调
        self.manager.on_room_updated(self._on_room_updated)
        self.manager.on_player_join(self._on_player_join)
        self.manager.on_player_leave(self._on_player_leave)
        self.manager.on_player_kicked(self._on_player_kicked)
        self.manager.on_game_start(self._on_game_start)

    # ========================================================================
    # 消息处理方法
    # ========================================================================

    async def handle_create_room(
        self,
        session: Session,
        message: CreateCustomRoomMessage,
    ) -> BaseMessage | None:
        """
        处理创建房间请求
        """
        player_id = session.player_id

        try:
            # 解析特殊规则
            special_rules = []
            for rule_str in message.special_rules:
                try:
                    special_rules.append(SpecialRuleType(rule_str))
                except ValueError:
                    logger.warning(
                        "无效的特殊规则",
                        player_id=player_id,
                        rule=rule_str,
                    )

            # 创建房间设置
            settings = RoomSettings(
                max_players=message.max_players,
                password=message.password,
                special_rules=special_rules,
                round_time=message.round_time,
                prepare_time=message.prepare_time,
                ai_fill=message.ai_fill,
            )

            # 创建房间
            room = await self.manager.create_room(
                host_id=player_id,
                host_name=getattr(session, "nickname", f"玩家{player_id[:6]}"),
                name=message.room_name,
                settings=settings,
            )

            logger.info(
                "自定义房间创建成功",
                player_id=player_id,
                room_id=room.room_id,
                room_name=room.name,
            )

            return CustomRoomCreatedMessage(
                room_id=room.room_id,
                room_info=self._room_to_info_data(room),
                seq=message.seq,
            )

        except Exception as e:
            logger.exception(
                "创建房间失败",
                player_id=player_id,
                error=str(e),
            )
            return ErrorMessage(
                code=5001,
                message="创建房间失败",
                details={"error": str(e)},
                seq=message.seq,
            )

    async def handle_join_room(
        self,
        session: Session,
        message: JoinCustomRoomMessage,
    ) -> BaseMessage | None:
        """
        处理加入房间请求
        """
        player_id = session.player_id
        nickname = getattr(session, "nickname", f"玩家{player_id[:6]}")

        try:
            room = await self.manager.join_room(
                player_id=player_id,
                player_name=nickname,
                room_id=message.room_id,
                password=message.password,
            )

            if room is None:
                if message.room_id:
                    return ErrorMessage(
                        code=5002,
                        message="无法加入房间",
                        details={"reason": "房间不存在、已满、已开始或密码错误"},
                        seq=message.seq,
                    )
                else:
                    return ErrorMessage(
                        code=5003,
                        message="没有可加入的房间",
                        details={"reason": "请创建房间或稍后重试"},
                        seq=message.seq,
                    )

            player = room.get_player(player_id)

            logger.info(
                "加入自定义房间成功",
                player_id=player_id,
                room_id=room.room_id,
            )

            return CustomRoomJoinedMessage(
                room_id=room.room_id,
                room_info=self._room_to_info_data(room),
                my_slot=player.slot if player else 0,
                seq=message.seq,
            )

        except Exception as e:
            logger.exception(
                "加入房间失败",
                player_id=player_id,
                error=str(e),
            )
            return ErrorMessage(
                code=5002,
                message="加入房间失败",
                details={"error": str(e)},
                seq=message.seq,
            )

    async def handle_leave_room(
        self,
        session: Session,
        message: LeaveCustomRoomMessage,
    ) -> BaseMessage | None:
        """
        处理离开房间请求
        """
        player_id = session.player_id

        try:
            room = await self.manager.get_player_room(player_id)
            room_id = room.room_id if room else None

            success = await self.manager.leave_room(player_id)

            if not success:
                return ErrorMessage(
                    code=5004,
                    message="离开房间失败",
                    details={"reason": "玩家不在任何房间中"},
                    seq=message.seq,
                )

            logger.info(
                "离开自定义房间成功",
                player_id=player_id,
                room_id=room_id,
            )

            return CustomRoomLeftMessage(
                room_id=room_id or "",
                seq=message.seq,
            )

        except Exception as e:
            logger.exception(
                "离开房间失败",
                player_id=player_id,
                error=str(e),
            )
            return ErrorMessage(
                code=5004,
                message="离开房间失败",
                details={"error": str(e)},
                seq=message.seq,
            )

    async def handle_kick_player(
        self,
        session: Session,
        message: KickPlayerMessage,
    ) -> BaseMessage | None:
        """
        处理踢出玩家请求
        """
        player_id = session.player_id

        try:
            room = await self.manager.get_player_room(player_id)
            if not room:
                return ErrorMessage(
                    code=5005,
                    message="踢出玩家失败",
                    details={"reason": "玩家不在任何房间中"},
                    seq=message.seq,
                )

            success = await self.manager.kick_player(
                room_id=room.room_id,
                host_id=player_id,
                target_id=message.target_id,
            )

            if not success:
                return ErrorMessage(
                    code=5005,
                    message="踢出玩家失败",
                    details={"reason": "只有房主可以踢人，或目标不在房间中"},
                    seq=message.seq,
                )

            logger.info(
                "踢出玩家成功",
                host_id=player_id,
                target_id=message.target_id,
                room_id=room.room_id,
            )

            # 返回成功响应（实际通知由回调发送）
            return None

        except Exception as e:
            logger.exception(
                "踢出玩家失败",
                player_id=player_id,
                error=str(e),
            )
            return ErrorMessage(
                code=5005,
                message="踢出玩家失败",
                details={"error": str(e)},
                seq=message.seq,
            )

    async def handle_start_game(
        self,
        session: Session,
        message: StartCustomGameMessage,
    ) -> BaseMessage | None:
        """
        处理开始游戏请求
        """
        player_id = session.player_id

        try:
            room = await self.manager.get_player_room(player_id)
            if not room:
                return ErrorMessage(
                    code=5006,
                    message="开始游戏失败",
                    details={"reason": "玩家不在任何房间中"},
                    seq=message.seq,
                )

            success = await self.manager.start_game(
                room_id=room.room_id,
                host_id=player_id,
            )

            if not success:
                return ErrorMessage(
                    code=5006,
                    message="开始游戏失败",
                    details={"reason": "只有房主可以开始游戏，或玩家未全部准备"},
                    seq=message.seq,
                )

            logger.info(
                "自定义游戏开始成功",
                host_id=player_id,
                room_id=room.room_id,
            )

            # 返回成功响应（实际通知由回调发送）
            return CustomGameStartedMessage(
                room_id=room.room_id,
                room_info=self._room_to_info_data(room),
                seq=message.seq,
            )

        except Exception as e:
            logger.exception(
                "开始游戏失败",
                player_id=player_id,
                error=str(e),
            )
            return ErrorMessage(
                code=5006,
                message="开始游戏失败",
                details={"error": str(e)},
                seq=message.seq,
            )

    async def handle_get_room_list(
        self,
        session: Session,
        message: GetCustomRoomListMessage,
    ) -> BaseMessage | None:
        """
        处理获取房间列表请求
        """
        player_id = session.player_id

        try:
            rooms = await self.manager.get_all_rooms()

            # 过滤只返回等待中的房间
            waiting_rooms = [room for room in rooms if room.state == CustomRoomState.WAITING]

            room_summaries = [self._room_to_summary_data(room) for room in waiting_rooms]

            logger.info(
                "获取自定义房间列表",
                player_id=player_id,
                count=len(room_summaries),
            )

            return CustomRoomListMessage(
                rooms=room_summaries,
                total_count=len(room_summaries),
                seq=message.seq,
            )

        except Exception as e:
            logger.exception(
                "获取房间列表失败",
                player_id=player_id,
                error=str(e),
            )
            return ErrorMessage(
                code=5007,
                message="获取房间列表失败",
                details={"error": str(e)},
                seq=message.seq,
            )

    async def handle_ai_fill(
        self,
        session: Session,
        message: AIFillRoomMessage,
    ) -> BaseMessage | None:
        """
        处理 AI 填充请求
        """
        player_id = session.player_id

        try:
            room = await self.manager.get_player_room(player_id)
            if not room:
                return ErrorMessage(
                    code=5008,
                    message="AI 填充失败",
                    details={"reason": "玩家不在任何房间中"},
                    seq=message.seq,
                )

            # 只有房主可以填充 AI
            if room.host_id != player_id:
                return ErrorMessage(
                    code=5008,
                    message="AI 填充失败",
                    details={"reason": "只有房主可以填充 AI"},
                    seq=message.seq,
                )

            # 填充 AI
            added_players = await self.manager.fill_room_with_ai(
                room_id=room.room_id,
                count=message.count,
            )

            logger.info(
                "AI 填充成功",
                player_id=player_id,
                room_id=room.room_id,
                ai_count=len(added_players),
            )

            # 刷新房间信息
            room = await self.manager.get_room(room.room_id)

            return AIFilledMessage(
                room_id=room.room_id,
                ai_count=len(added_players),
                room_info=self._room_to_info_data(room) if room else None,
                seq=message.seq,
            )

        except Exception as e:
            logger.exception(
                "AI 填充失败",
                player_id=player_id,
                error=str(e),
            )
            return ErrorMessage(
                code=5008,
                message="AI 填充失败",
                details={"error": str(e)},
                seq=message.seq,
            )

    async def handle_set_ready(
        self,
        session: Session,
        message: SetPlayerReadyMessage,
    ) -> BaseMessage | None:
        """
        处理设置准备状态请求
        """
        player_id = session.player_id

        try:
            success = await self.manager.set_player_ready(
                player_id=player_id,
                ready=message.ready,
            )

            if not success:
                return ErrorMessage(
                    code=5009,
                    message="设置准备状态失败",
                    details={"reason": "玩家不在任何房间中"},
                    seq=message.seq,
                )

            logger.info(
                "设置准备状态成功",
                player_id=player_id,
                ready=message.ready,
            )

            return None  # 成功，更新通知由回调发送

        except Exception as e:
            logger.exception(
                "设置准备状态失败",
                player_id=player_id,
                error=str(e),
            )
            return ErrorMessage(
                code=5009,
                message="设置准备状态失败",
                details={"error": str(e)},
                seq=message.seq,
            )

    # ========================================================================
    # 回调方法
    # ========================================================================

    def _on_room_updated(self, room: CustomRoom) -> None:
        """房间更新回调"""
        if self._ws_handler is None:
            return

        # 广播给房间内所有玩家
        asyncio.create_task(self._broadcast_room_update(room))

    def _on_player_join(
        self,
        player_id: str,
        player_name: str,
        room: CustomRoom,
    ) -> None:
        """玩家加入回调"""
        if self._ws_handler is None:
            return

        asyncio.create_task(self._notify_player_joined(room, player_id, player_name))

    def _on_player_leave(
        self,
        player_id: str,
        player_name: str,
        room: CustomRoom,
    ) -> None:
        """玩家离开回调"""
        if self._ws_handler is None:
            return

        asyncio.create_task(self._notify_player_left(room, player_id, player_name))

    def _on_player_kicked(
        self,
        player_id: str,
        player_name: str,
        room: CustomRoom,
    ) -> None:
        """玩家被踢回调"""
        if self._ws_handler is None:
            return

        asyncio.create_task(self._notify_player_kicked(room, player_id, player_name))

    def _on_game_start(self, room: CustomRoom) -> None:
        """游戏开始回调"""
        if self._ws_handler is None:
            return

        asyncio.create_task(self._broadcast_game_started(room))

    # ========================================================================
    # 广播方法
    # ========================================================================

    async def _broadcast_room_update(
        self,
        room: CustomRoom,
        event: str = "updated",
        event_data: dict[str, Any] | None = None,
    ) -> None:
        """广播房间更新"""
        message = CustomRoomUpdatedMessage(
            room_info=self._room_to_info_data(room),
            event=event,
            event_data=event_data or {},
        )

        player_ids = list(room.players.keys())
        await self._ws_handler.broadcast_to_players(player_ids, message)

    async def _notify_player_joined(
        self,
        room: CustomRoom,
        player_id: str,
        player_name: str,
    ) -> None:
        """通知玩家加入"""
        player = room.get_player(player_id)
        if not player:
            return

        # 广播给房间内其他玩家
        player_ids = [
            pid for pid in room.players.keys() if pid != player_id and not pid.startswith("ai_")
        ]

        if player_ids:
            await self._broadcast_room_update(
                room,
                event="player_joined",
                event_data={"player": player.to_dict()},
            )

    async def _notify_player_left(
        self,
        room: CustomRoom,
        player_id: str,
        player_name: str,
    ) -> None:
        """通知玩家离开"""
        player_ids = [pid for pid in room.players.keys() if not pid.startswith("ai_")]

        if player_ids:
            await self._broadcast_room_update(
                room,
                event="player_left",
                event_data={"player_id": player_id, "player_name": player_name},
            )

    async def _notify_player_kicked(
        self,
        room: CustomRoom,
        player_id: str,
        player_name: str,
    ) -> None:
        """通知玩家被踢"""
        # 先通知被踢的玩家
        message = PlayerKickedMessage(
            room_id=room.room_id,
            player_id=player_id,
            player_name=player_name,
        )
        await self._ws_handler.send_to_player(player_id, message)

        # 广播给房间内其他玩家
        player_ids = [pid for pid in room.players.keys() if not pid.startswith("ai_")]

        if player_ids:
            await self._broadcast_room_update(
                room,
                event="player_kicked",
                event_data={"player_id": player_id, "player_name": player_name},
            )

    async def _broadcast_game_started(self, room: CustomRoom) -> None:
        """广播游戏开始"""
        message = CustomGameStartedMessage(
            room_id=room.room_id,
            room_info=self._room_to_info_data(room),
        )

        player_ids = [pid for pid in room.players.keys() if not pid.startswith("ai_")]

        await self._ws_handler.broadcast_to_players(player_ids, message)

    # ========================================================================
    # 辅助方法
    # ========================================================================

    def _room_to_info_data(self, room: CustomRoom) -> CustomRoomInfoData:
        """将房间对象转换为信息数据"""
        players = [
            self._player_to_data(p) for p in sorted(room.players.values(), key=lambda p: p.slot)
        ]

        return CustomRoomInfoData(
            room_id=room.room_id,
            name=room.name,
            host_id=room.host_id,
            settings=CustomRoomSettingsData(
                max_players=room.settings.max_players,
                has_password=room.has_password,
                special_rules=[r.value for r in room.settings.special_rules],
                round_time=room.settings.round_time,
                prepare_time=room.settings.prepare_time,
                starting_gold=room.settings.starting_gold,
                starting_hp=room.settings.starting_hp,
                ai_fill=room.settings.ai_fill,
            ),
            players=players,
            state=room.state.value,
            player_count=room.player_count,
            created_at=room.created_at.isoformat(),
        )

    def _room_to_summary_data(self, room: CustomRoom) -> CustomRoomSummaryData:
        """将房间对象转换为简要数据"""
        host_name = "未知"
        if room.host_id and room.host_id in room.players:
            host_name = room.players[room.host_id].nickname

        return CustomRoomSummaryData(
            room_id=room.room_id,
            name=room.name,
            host_name=host_name,
            player_count=room.player_count,
            max_players=room.settings.max_players,
            has_password=room.has_password,
            state=room.state.value,
            special_rules=[r.value for r in room.settings.special_rules],
        )

    def _player_to_data(self, player) -> CustomRoomPlayerData:
        """将玩家对象转换为数据"""
        return CustomRoomPlayerData(
            player_id=player.player_id,
            nickname=player.nickname,
            avatar=player.avatar,
            slot=player.slot,
            state=player.state.value,
            is_host=player.is_host,
            is_ai=player.is_ai,
        )


# 导入 asyncio（用于回调中的异步任务）
import asyncio  # noqa: E402

# 全局处理器实例
custom_room_ws_handler = CustomRoomWSHandler()
