"""
王者之奕 - 表情系统 WebSocket 处理器

本模块提供表情系统相关的 WebSocket 消息处理：
- 获取表情列表
- 获取已拥有表情
- 发送表情
- 设置快捷键
- 获取表情历史

与主 WebSocket 处理器集成。
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ...shared.protocol import (
    BaseMessage,
    EmoteData,
    EmoteHistoryItemData,
    EmoteHistoryMessage,
    EmoteHotkeySetMessage,
    EmoteReceivedMessage,
    EmoteSentData,
    EmoteSentMessage,
    EmotesListMessage,
    ErrorMessage,
    GetEmoteHistoryMessage,
    GetEmotesMessage,
    GetOwnedEmotesMessage,
    OwnedEmotesListMessage,
    PlayerEmoteData,
    SendEmoteMessage,
    SetEmoteHotkeyMessage,
)
from ..emote import (
    EmoteManager,
    get_emote_manager,
)

if TYPE_CHECKING:
    from ..ws.handler import Session, WebSocketHandler

logger = logging.getLogger(__name__)


class EmoteWSHandler:
    """
    表情系统 WebSocket 处理器

    处理所有表情相关的 WebSocket 消息。

    使用方式:
        handler = EmoteWSHandler()

        @ws_handler.on_message(MessageType.GET_EMOTES)
        async def handle_get_emotes(session, message):
            return await emote_handler.handle_get_emotes(session, message)
    """

    def __init__(self, ws_handler: WebSocketHandler | None = None) -> None:
        """
        初始化处理器

        Args:
            ws_handler: WebSocket 处理器（用于广播）
        """
        self._ws_handler = ws_handler
        self._manager: EmoteManager | None = None

    @property
    def manager(self) -> EmoteManager:
        """获取表情管理器"""
        if self._manager is None:
            self._manager = get_emote_manager()
            if self._ws_handler:
                self._manager.set_ws_handler(self._ws_handler)
        return self._manager

    def set_ws_handler(self, handler: WebSocketHandler) -> None:
        """设置 WebSocket 处理器"""
        self._ws_handler = handler
        if self._manager:
            self._manager.set_ws_handler(handler)

    async def handle_get_emotes(
        self,
        session: Session,
        message: GetEmotesMessage,
    ) -> BaseMessage | None:
        """
        处理获取表情列表请求

        Args:
            session: WebSocket 会话
            message: 获取表情列表消息

        Returns:
            响应消息
        """
        player_id = session.player_id

        try:
            manager = self.manager

            # 获取所有表情
            if message.category:
                from ..emote.models import EmoteCategory

                category = EmoteCategory(message.category)
                emotes = manager.get_emotes_by_category(category)
            else:
                emotes = manager.get_all_emotes()

            # 转换为消息数据
            emote_data_list = [
                EmoteData(
                    emote_id=e.emote_id,
                    name=e.name,
                    description=e.description,
                    category=e.category.value,
                    emote_type=e.emote_type.value,
                    asset_url=e.asset_url,
                    thumbnail_url=e.thumbnail_url,
                    sound_url=e.sound_url,
                    unlock_condition=e.unlock_condition,
                    is_free=e.is_free,
                    sort_order=e.sort_order,
                )
                for e in emotes
            ]

            return EmotesListMessage(
                emotes=emote_data_list,
                total_count=len(emote_data_list),
                seq=message.seq,
            )

        except Exception as e:
            logger.exception(
                "获取表情列表失败",
                player_id=player_id,
                error=str(e),
            )
            return ErrorMessage(
                code=4001,
                message="获取表情列表失败",
                details={"error": str(e)},
                seq=message.seq,
            )

    async def handle_get_owned_emotes(
        self,
        session: Session,
        message: GetOwnedEmotesMessage,
    ) -> BaseMessage | None:
        """
        处理获取已拥有表情请求

        Args:
            session: WebSocket 会话
            message: 获取已拥有表情消息

        Returns:
            响应消息
        """
        player_id = session.player_id

        try:
            manager = self.manager

            # TODO: 从数据库获取玩家统计数据
            player_stats = {}

            # 获取已解锁表情
            emotes_data = manager.get_unlocked_emotes_data(player_id, player_stats)

            # 转换为消息数据
            emote_list = [
                PlayerEmoteData(
                    emote_id=e["emote_id"],
                    name=e["name"],
                    asset_url=e["asset_url"],
                    thumbnail_url=e.get("thumbnail_url", ""),
                    category=e["category"],
                    emote_type=e["emote_type"],
                    hotkey=e.get("hotkey"),
                    use_count=e.get("use_count", 0),
                )
                for e in emotes_data
            ]

            # 获取快捷键映射
            hotkeys = manager.get_player_hotkeys(player_id)

            return OwnedEmotesListMessage(
                emotes=emote_list,
                hotkeys=hotkeys,
                total_count=len(emote_list),
                seq=message.seq,
            )

        except Exception as e:
            logger.exception(
                "获取已拥有表情失败",
                player_id=player_id,
                error=str(e),
            )
            return ErrorMessage(
                code=4002,
                message="获取已拥有表情失败",
                details={"error": str(e)},
                seq=message.seq,
            )

    async def handle_send_emote(
        self,
        session: Session,
        message: SendEmoteMessage,
    ) -> BaseMessage | None:
        """
        处理发送表情请求

        Args:
            session: WebSocket 会话
            message: 发送表情消息

        Returns:
            响应消息
        """
        player_id = session.player_id
        room_id = session.room_id or message.room_id

        if not room_id:
            return ErrorMessage(
                code=4003,
                message="不在房间中，无法发送表情",
                seq=message.seq,
            )

        try:
            manager = self.manager

            # 发送表情
            history = await manager.send_emote(
                room_id=room_id,
                from_player_id=player_id,
                emote_id=message.emote_id,
                to_player_id=message.to_player_id,
                round_number=message.round_number,
                from_nickname="",  # TODO: 获取玩家昵称
            )

            if history is None:
                # 检查是否冷却中
                remaining = manager.get_cooldown_remaining(player_id)
                if remaining > 0:
                    return ErrorMessage(
                        code=4004,
                        message=f"表情冷却中，请等待 {remaining:.1f} 秒",
                        details={"cooldown_remaining": remaining},
                        seq=message.seq,
                    )

                return ErrorMessage(
                    code=4005,
                    message="发送表情失败",
                    seq=message.seq,
                )

            # 获取表情对象
            emote = manager.get_emote(message.emote_id)
            if not emote:
                return ErrorMessage(
                    code=4006,
                    message="表情不存在",
                    seq=message.seq,
                )

            # 构建发送数据
            emote_sent_data = EmoteSentData(
                emote_id=emote.emote_id,
                name=emote.name,
                asset_url=emote.asset_url,
                thumbnail_url=emote.thumbnail_url,
                emote_type=emote.emote_type.value,
                from_player_id=player_id,
                from_nickname="",  # TODO: 获取玩家昵称
                to_player_id=message.to_player_id,
                room_id=room_id,
                round_number=message.round_number,
                timestamp=history.created_at.isoformat() if history.created_at else "",
            )

            # 广播给房间内其他玩家
            await self._broadcast_emote(room_id, player_id, message.to_player_id, emote_sent_data)

            logger.info(
                "表情发送成功",
                player_id=player_id,
                emote_id=message.emote_id,
                room_id=room_id,
                to_player_id=message.to_player_id,
            )

            return EmoteSentMessage(
                emote=emote_sent_data,
                cooldown_remaining=manager.get_cooldown_remaining(player_id),
                seq=message.seq,
            )

        except Exception as e:
            logger.exception(
                "发送表情失败",
                player_id=player_id,
                error=str(e),
            )
            return ErrorMessage(
                code=4000,
                message="发送表情失败",
                details={"error": str(e)},
                seq=message.seq,
            )

    async def _broadcast_emote(
        self,
        room_id: str,
        from_player_id: str,
        to_player_id: str | None,
        emote_data: EmoteSentData,
    ) -> None:
        """
        广播表情给房间内玩家

        Args:
            room_id: 房间ID
            from_player_id: 发送者ID
            to_player_id: 目标玩家ID
            emote_data: 表情数据
        """
        if not self._ws_handler:
            return

        # 构建广播消息
        broadcast_msg = EmoteReceivedMessage(emote=emote_data)

        if to_player_id:
            # 发送给特定玩家
            await self._ws_handler.send_to_player(to_player_id, broadcast_msg)
        else:
            # 发送给房间内所有其他玩家
            # TODO: 获取房间内玩家列表并广播
            pass

    async def handle_set_hotkey(
        self,
        session: Session,
        message: SetEmoteHotkeyMessage,
    ) -> BaseMessage | None:
        """
        处理设置快捷键请求

        Args:
            session: WebSocket 会话
            message: 设置快捷键消息

        Returns:
            响应消息
        """
        player_id = session.player_id

        try:
            manager = self.manager

            # 获取之前的快捷键
            player_emote = manager.get_player_emote(player_id, message.emote_id)
            previous_hotkey = player_emote.hotkey if player_emote else None

            # 设置快捷键
            success = manager.set_emote_hotkey(
                player_id=player_id,
                emote_id=message.emote_id,
                hotkey=message.hotkey,
            )

            if not success:
                return ErrorMessage(
                    code=4007,
                    message="设置快捷键失败",
                    seq=message.seq,
                )

            logger.info(
                "设置表情快捷键成功",
                player_id=player_id,
                emote_id=message.emote_id,
                hotkey=message.hotkey,
            )

            return EmoteHotkeySetMessage(
                emote_id=message.emote_id,
                hotkey=message.hotkey,
                previous_hotkey=previous_hotkey,
                seq=message.seq,
            )

        except Exception as e:
            logger.exception(
                "设置快捷键失败",
                player_id=player_id,
                error=str(e),
            )
            return ErrorMessage(
                code=4008,
                message="设置快捷键失败",
                details={"error": str(e)},
                seq=message.seq,
            )

    async def handle_get_history(
        self,
        session: Session,
        message: GetEmoteHistoryMessage,
    ) -> BaseMessage | None:
        """
        处理获取表情历史请求

        Args:
            session: WebSocket 会话
            message: 获取表情历史消息

        Returns:
            响应消息
        """
        player_id = session.player_id

        try:
            manager = self.manager

            # 获取历史记录
            if message.room_id:
                history_list = manager.get_room_emote_history(
                    message.room_id,
                    limit=message.limit,
                )
            else:
                history_list = manager.get_player_emote_history(
                    player_id,
                    limit=message.limit,
                )

            # 转换为消息数据
            history_data = []
            for h in history_list:
                emote = manager.get_emote(h.emote_id)
                if emote:
                    history_data.append(
                        EmoteHistoryItemData(
                            history_id=h.history_id,
                            emote_id=h.emote_id,
                            name=emote.name,
                            asset_url=emote.asset_url,
                            from_player_id=h.from_player_id,
                            from_nickname="",  # TODO: 获取昵称
                            to_player_id=h.to_player_id,
                            to_nickname="",  # TODO: 获取昵称
                            room_id=h.room_id,
                            round_number=h.round_number,
                            created_at=h.created_at.isoformat() if h.created_at else None,
                        )
                    )

            return EmoteHistoryMessage(
                history=history_data,
                room_id=message.room_id,
                total_count=len(history_data),
                seq=message.seq,
            )

        except Exception as e:
            logger.exception(
                "获取表情历史失败",
                player_id=player_id,
                error=str(e),
            )
            return ErrorMessage(
                code=4009,
                message="获取表情历史失败",
                details={"error": str(e)},
                seq=message.seq,
            )


# 全局处理器实例
_emote_ws_handler: EmoteWSHandler | None = None


def get_emote_ws_handler() -> EmoteWSHandler:
    """获取表情 WebSocket 处理器单例"""
    global _emote_ws_handler
    if _emote_ws_handler is None:
        _emote_ws_handler = EmoteWSHandler()
    return _emote_ws_handler
