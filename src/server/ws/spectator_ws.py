"""
王者之奕 - 观战系统 WebSocket 处理器

本模块提供观战系统相关的 WebSocket 消息处理：
- 获取可观战对局列表
- 加入/离开观战
- 切换观战对象
- 同步对局状态
- 处理弹幕/聊天

与主 WebSocket 处理器集成。
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Optional

from ..spectator import (
    GameVisibility,
    SpectatableGame,
    SpectatorManager,
    SpectatorChat,
    get_spectator_manager,
)
from ...shared.protocol import (
    BaseMessage,
    ErrorMessage,
    GetSpectatableGamesMessage,
    JoinSpectateMessage,
    LeaveSpectateMessage,
    SpectatableGameData,
    SpectatableGamesListMessage,
    SpectateChatData,
    SpectateChatMessage,
    SpectateChatReceivedMessage,
    SpectateEndedMessage,
    SpectateJoinedMessage,
    SpectateLeftMessage,
    SpectateStateMessage,
    SpectateSwitchMessage,
    SpectateSyncMessage,
    SpectatorPlayerStateData,
    MessageType,
)

if TYPE_CHECKING:
    from ..ws.handler import Session

logger = logging.getLogger(__name__)


class SpectatorWSHandler:
    """
    观战系统 WebSocket 处理器
    
    处理所有观战相关的 WebSocket 消息。
    
    使用方式:
        handler = SpectatorWSHandler()
        
        @ws_handler.on_message(MessageType.GET_SPECTATABLE_GAMES)
        async def handle_get_spectatable_games(session, message):
            return await spectator_handler.handle_get_spectatable_games(session, message)
    """
    
    def __init__(self) -> None:
        """初始化处理器"""
        self._manager: Optional[SpectatorManager] = None
        # WebSocket 广播回调
        self._broadcast_callback: Optional[Any] = None
    
    @property
    def manager(self) -> SpectatorManager:
        """获取观战管理器"""
        if self._manager is None:
            self._manager = get_spectator_manager()
        return self._manager
    
    def set_broadcast_callback(self, callback: Any) -> None:
        """
        设置广播回调
        
        Args:
            callback: 广播函数 (player_ids, message) -> None
        """
        self._broadcast_callback = callback
    
    async def _broadcast_to_game_spectators(
        self,
        game_id: str,
        message: BaseMessage,
    ) -> int:
        """
        向对局的所有观众广播消息
        
        Args:
            game_id: 对局ID
            message: 消息
            
        Returns:
            成功发送数量
        """
        if self._broadcast_callback is None:
            return 0
        
        # 获取所有观众
        spectators = self.manager.get_spectators_in_game(game_id)
        player_ids = [s.spectator_id for s in spectators]
        
        if not player_ids:
            return 0
        
        # 广播
        count = await self._broadcast_callback(player_ids, message)
        return count
    
    # ========================================================================
    # 消息处理
    # ========================================================================
    
    async def handle_get_spectatable_games(
        self,
        session: "Session",
        message: GetSpectatableGamesMessage,
    ) -> Optional[BaseMessage]:
        """
        处理获取可观战对局列表请求
        
        Args:
            session: WebSocket 会话
            message: 获取可观战对局列表消息
            
        Returns:
            响应消息
        """
        player_id = session.player_id
        
        try:
            # 获取可观战对局列表
            games = self.manager.get_spectatable_games(
                page=message.page,
                page_size=message.page_size,
            )
            
            # 转换为消息格式
            game_data_list = [
                SpectatableGameData(
                    game_id=game.game_id,
                    players=game.players,
                    created_at=game.created_at,
                    current_round=game.current_round,
                    spectator_count=game.spectator_count,
                    visibility=game.visibility.value,
                    is_featured=game.is_featured,
                )
                for game in games
            ]
            
            logger.info(
                "获取可观战对局列表",
                extra={
                    "player_id": player_id,
                    "page": message.page,
                    "count": len(game_data_list),
                }
            )
            
            return SpectatableGamesListMessage(
                games=game_data_list,
                page=message.page,
                page_size=message.page_size,
                total_count=len(game_data_list),  # 实际应获取总数
                seq=message.seq,
            )
        
        except Exception as e:
            logger.exception(
                "获取可观战对局列表异常",
                extra={"player_id": player_id, "error": str(e)},
            )
            return ErrorMessage(
                code=5000,
                message="获取可观战对局列表失败",
                details={"error": str(e)},
                seq=message.seq,
            )
    
    async def handle_join_spectate(
        self,
        session: "Session",
        message: JoinSpectateMessage,
    ) -> Optional[BaseMessage]:
        """
        处理加入观战请求
        
        Args:
            session: WebSocket 会话
            message: 加入观战消息
            
        Returns:
            响应消息
        """
        player_id = session.player_id
        
        try:
            # 检查对局是否存在
            spectator_data = self.manager.get_spectatable_game(message.game_id)
            if spectator_data is None:
                return ErrorMessage(
                    code=5001,
                    message="对局不存在或不可观战",
                    seq=message.seq,
                )
            
            # 检查是否已满
            if spectator_data.is_full():
                return ErrorMessage(
                    code=5002,
                    message="观众已满",
                    seq=message.seq,
                )
            
            # 检查权限
            if spectator_data.visibility == GameVisibility.PRIVATE:
                return ErrorMessage(
                    code=5003,
                    message="该对局不可观战",
                    seq=message.seq,
                )
            elif spectator_data.visibility == GameVisibility.FRIENDS:
                # TODO: 检查好友关系
                pass
            
            # 创建观战会话
            spectator_session = self.manager.create_session(
                spectator_id=player_id,
                game_id=message.game_id,
                watching_player_id=message.watching_player_id,
            )
            
            if spectator_session is None:
                return ErrorMessage(
                    code=5004,
                    message="加入观战失败",
                    seq=message.seq,
                )
            
            logger.info(
                "加入观战成功",
                extra={
                    "player_id": player_id,
                    "game_id": message.game_id,
                    "session_id": spectator_session.session_id,
                    "watching_player_id": message.watching_player_id,
                }
            )
            
            return SpectateJoinedMessage(
                game_id=message.game_id,
                session_id=spectator_session.session_id,
                watching_player_id=message.watching_player_id,
                delay_seconds=spectator_data.delay_seconds,
                spectator_count=spectator_data.get_spectator_count(),
                seq=message.seq,
            )
        
        except Exception as e:
            logger.exception(
                "加入观战异常",
                extra={"player_id": player_id, "error": str(e)},
            )
            return ErrorMessage(
                code=5000,
                message="加入观战失败",
                details={"error": str(e)},
                seq=message.seq,
            )
    
    async def handle_leave_spectate(
        self,
        session: "Session",
        message: LeaveSpectateMessage,
    ) -> Optional[BaseMessage]:
        """
        处理离开观战请求
        
        Args:
            session: WebSocket 会话
            message: 离开观战消息
            
        Returns:
            响应消息
        """
        player_id = session.player_id
        
        try:
            # 获取当前观战会话
            spectator_session = self.manager.get_session_by_player(player_id)
            if spectator_session is None:
                return SpectateLeftMessage(
                    game_id=message.game_id,
                    session_id=None,
                    seq=message.seq,
                )
            
            # 离开观战
            removed_session = self.manager.leave_spectate(spectator_session.session_id)
            
            logger.info(
                "离开观战成功",
                extra={
                    "player_id": player_id,
                    "game_id": message.game_id,
                    "session_id": spectator_session.session_id,
                }
            )
            
            return SpectateLeftMessage(
                game_id=message.game_id,
                session_id=spectator_session.session_id if removed_session else None,
                seq=message.seq,
            )
        
        except Exception as e:
            logger.exception(
                "离开观战异常",
                extra={"player_id": player_id, "error": str(e)},
            )
            return ErrorMessage(
                code=5000,
                message="离开观战失败",
                details={"error": str(e)},
                seq=message.seq,
            )
    
    async def handle_spectate_switch(
        self,
        session: "Session",
        message: SpectateSwitchMessage,
    ) -> Optional[BaseMessage]:
        """
        处理切换观战对象请求
        
        Args:
            session: WebSocket 会话
            message: 切换观战对象消息
            
        Returns:
            响应消息（返回更新后的状态）
        """
        player_id = session.player_id
        
        try:
            # 获取当前观战会话
            spectator_session = self.manager.get_session_by_player(player_id)
            if spectator_session is None:
                return ErrorMessage(
                    code=5005,
                    message="未在观战中",
                    seq=message.seq,
                )
            
            # 切换观战对象
            updated_session = self.manager.switch_watching_player(
                spectator_session.session_id,
                message.new_player_id,
            )
            
            if updated_session is None:
                return ErrorMessage(
                    code=5006,
                    message="切换观战对象失败",
                    seq=message.seq,
                )
            
            logger.info(
                "切换观战对象成功",
                extra={
                    "player_id": player_id,
                    "game_id": message.game_id,
                    "new_player_id": message.new_player_id,
                }
            )
            
            # 返回更新后的状态
            return await self.handle_spectate_sync(
                session,
                SpectateSyncMessage(game_id=message.game_id, seq=message.seq),
            )
        
        except Exception as e:
            logger.exception(
                "切换观战对象异常",
                extra={"player_id": player_id, "error": str(e)},
            )
            return ErrorMessage(
                code=5000,
                message="切换观战对象失败",
                details={"error": str(e)},
                seq=message.seq,
            )
    
    async def handle_spectate_sync(
        self,
        session: "Session",
        message: SpectateSyncMessage,
    ) -> Optional[BaseMessage]:
        """
        处理同步观战状态请求
        
        Args:
            session: WebSocket 会话
            message: 同步观战状态消息
            
        Returns:
            响应消息
        """
        player_id = session.player_id
        
        try:
            # 获取延迟后的游戏状态
            delayed_state = self.manager.get_delayed_state(message.game_id)
            
            if delayed_state is None:
                # 没有可用状态
                return SpectateStateMessage(
                    game_id=message.game_id,
                    round_num=0,
                    phase="",
                    player_states=[],
                    snapshot_time=0,
                    delay_seconds=30,
                    seq=message.seq,
                )
            
            # 转换玩家状态
            player_states = []
            for pid, state in delayed_state.player_states.items():
                player_states.append(SpectatorPlayerStateData(
                    player_id=pid,
                    nickname=state.get("nickname", ""),
                    avatar=state.get("avatar"),
                    tier=state.get("tier"),
                    hp=state.get("hp", 100),
                    gold=state.get("gold", 0),
                    level=state.get("level", 1),
                    board=state.get("board", []),
                    bench=state.get("bench", []),
                    synergies=state.get("synergies", {}),
                ))
            
            # 获取延迟配置
            spectator_data = self.manager.get_spectatable_game(message.game_id)
            delay_seconds = spectator_data.delay_seconds if spectator_data else 30
            
            logger.debug(
                "同步观战状态",
                extra={
                    "player_id": player_id,
                    "game_id": message.game_id,
                    "round_num": delayed_state.round_num,
                }
            )
            
            return SpectateStateMessage(
                game_id=message.game_id,
                round_num=delayed_state.round_num,
                phase=delayed_state.phase,
                player_states=player_states,
                snapshot_time=delayed_state.snapshot_time,
                delay_seconds=delay_seconds,
                seq=message.seq,
            )
        
        except Exception as e:
            logger.exception(
                "同步观战状态异常",
                extra={"player_id": player_id, "error": str(e)},
            )
            return ErrorMessage(
                code=5000,
                message="同步观战状态失败",
                details={"error": str(e)},
                seq=message.seq,
            )
    
    async def handle_spectate_chat(
        self,
        session: "Session",
        message: SpectateChatMessage,
    ) -> Optional[BaseMessage]:
        """
        处理发送弹幕请求
        
        Args:
            session: WebSocket 会话
            message: 发送弹幕消息
            
        Returns:
            响应消息（广播给所有观众）
        """
        player_id = session.player_id
        
        try:
            # 获取观战会话
            spectator_session = self.manager.get_session_by_player(player_id)
            if spectator_session is None:
                return ErrorMessage(
                    code=5005,
                    message="未在观战中",
                    seq=message.seq,
                )
            
            # 检查弹幕是否启用
            if not spectator_session.chat_enabled:
                return ErrorMessage(
                    code=5007,
                    message="弹幕功能已禁用",
                    seq=message.seq,
                )
            
            # 获取玩家信息（应从数据库获取）
            # 这里使用 session 中的信息
            sender_name = session.metadata.get("nickname", player_id)
            avatar = session.metadata.get("avatar")
            tier = session.metadata.get("tier")
            
            # 发送弹幕
            chat = self.manager.send_chat(
                game_id=message.game_id,
                sender_id=player_id,
                sender_name=sender_name,
                content=message.content,
                message_type=message.message_type,
                avatar=avatar,
                tier=tier,
            )
            
            if chat is None:
                return ErrorMessage(
                    code=5008,
                    message="发送弹幕失败",
                    seq=message.seq,
                )
            
            logger.debug(
                "发送弹幕成功",
                extra={
                    "player_id": player_id,
                    "game_id": message.game_id,
                    "content": message.content[:50],
                }
            )
            
            # 广播给所有观众
            chat_data = SpectateChatData(
                chat_id=chat.chat_id,
                sender_id=chat.sender_id,
                sender_name=chat.sender_name,
                content=chat.content,
                sent_at=chat.sent_at,
                message_type=chat.message_type,
                avatar=chat.avatar,
                tier=chat.tier,
            )
            
            broadcast_msg = SpectateChatReceivedMessage(
                game_id=message.game_id,
                chat=chat_data,
            )
            
            # 异步广播
            await self._broadcast_to_game_spectators(message.game_id, broadcast_msg)
            
            # 返回确认（可选）
            return None
        
        except Exception as e:
            logger.exception(
                "发送弹幕异常",
                extra={"player_id": player_id, "error": str(e)},
            )
            return ErrorMessage(
                code=5000,
                message="发送弹幕失败",
                details={"error": str(e)},
                seq=message.seq,
            )
    
    # ========================================================================
    # 事件通知
    # ========================================================================
    
    async def notify_game_ended(self, game_id: str, reason: str = "game_ended") -> None:
        """
        通知对局结束
        
        Args:
            game_id: 对局ID
            reason: 结束原因
        """
        message = SpectateEndedMessage(
            game_id=game_id,
            reason=reason,
        )
        
        await self._broadcast_to_game_spectators(game_id, message)
        
        # 清理观战数据
        self.manager.remove_spectatable_game(game_id)
        
        logger.info(
            "对局结束，通知观众",
            extra={"game_id": game_id, "reason": reason},
        )
    
    async def broadcast_state_update(self, game_id: str) -> None:
        """
        广播状态更新
        
        Args:
            game_id: 对局ID
        """
        # 获取延迟状态
        state = self.manager.get_delayed_state(game_id)
        if state is None:
            return
        
        # 构建消息
        player_states = []
        for pid, pstate in state.player_states.items():
            player_states.append(SpectatorPlayerStateData(
                player_id=pid,
                nickname=pstate.get("nickname", ""),
                avatar=pstate.get("avatar"),
                tier=pstate.get("tier"),
                hp=pstate.get("hp", 100),
                gold=pstate.get("gold", 0),
                level=pstate.get("level", 1),
                board=pstate.get("board", []),
                bench=pstate.get("bench", []),
                synergies=pstate.get("synergies", {}),
            ))
        
        spectator_data = self.manager.get_spectatable_game(game_id)
        delay_seconds = spectator_data.delay_seconds if spectator_data else 30
        
        message = SpectateStateMessage(
            game_id=game_id,
            round_num=state.round_num,
            phase=state.phase,
            player_states=player_states,
            snapshot_time=state.snapshot_time,
            delay_seconds=delay_seconds,
        )
        
        await self._broadcast_to_game_spectators(game_id, message)


# 全局处理器实例
spectator_ws_handler = SpectatorWSHandler()
