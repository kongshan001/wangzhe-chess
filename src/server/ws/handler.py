"""
王者之奕 - WebSocket 处理器

本模块实现 WebSocket 连接的核心处理逻辑：
- 连接管理（建立、断开、重连）
- 消息路由（根据消息类型分发到对应处理器）
- 心跳检测（保持连接活跃）
- 断线重连支持（会话恢复）

使用 asyncio 实现异步处理。
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Any, Callable, Optional

from fastapi import WebSocket, WebSocketDisconnect
import structlog

from src.shared.protocol import (
    BaseMessage,
    ConnectMessage,
    ConnectedMessage,
    DisconnectMessage,
    ErrorMessage,
    HeartbeatAckMessage,
    HeartbeatMessage,
    MessageCodecError,
    MessageType,
    ReconnectMessage,
    ReconnectedMessage,
    decode_message,
    encode_message,
)

if TYPE_CHECKING:
    from .room_ws import RoomWSHandler

logger = structlog.get_logger()


# ============================================================================
# 错误码定义
# ============================================================================

class WSErrorCode:
    """WebSocket 错误码"""
    
    # 连接相关 (2000-2099)
    INVALID_TOKEN = 2001
    PLAYER_NOT_FOUND = 2002
    SESSION_EXPIRED = 2003
    ALREADY_CONNECTED = 2004
    CONNECTION_LIMIT = 2005
    
    # 消息相关 (2100-2199)
    INVALID_MESSAGE = 2101
    UNKNOWN_MESSAGE_TYPE = 2102
    PARSE_ERROR = 2103
    
    # 房间相关 (2200-2299)
    ROOM_NOT_FOUND = 2201
    ROOM_FULL = 2202
    NOT_IN_ROOM = 2203
    
    # 游戏相关 (2300-2399)
    GAME_NOT_STARTED = 2301
    INVALID_OPERATION = 2302
    NOT_YOUR_TURN = 2303


# ============================================================================
# 心跳配置
# ============================================================================

class HeartbeatConfig:
    """心跳配置"""
    
    # 心跳间隔（秒）
    INTERVAL: int = 30
    
    # 心跳超时（秒）
    TIMEOUT: int = 60
    
    # 最大连续超时次数
    MAX_MISSED_HEARTBEATS: int = 3


# ============================================================================
# 会话管理
# ============================================================================

class Session:
    """
    WebSocket 会话
    
    存储单个 WebSocket 连接的会话信息。
    
    Attributes:
        session_id: 会话唯一ID
        player_id: 玩家ID
        websocket: WebSocket 连接对象
        connected_at: 连接时间戳
        last_heartbeat: 最后心跳时间
        missed_heartbeats: 连续未响应心跳次数
        room_id: 当前所在房间ID
        is_authenticated: 是否已认证
        metadata: 额外元数据
    """
    
    def __init__(
        self,
        session_id: str,
        player_id: str,
        websocket: WebSocket,
    ) -> None:
        """
        初始化会话
        
        Args:
            session_id: 会话ID
            player_id: 玩家ID
            websocket: WebSocket 连接
        """
        self.session_id = session_id
        self.player_id = player_id
        self.websocket = websocket
        self.connected_at = int(time.time() * 1000)
        self.last_heartbeat = int(time.time() * 1000)
        self.missed_heartbeats: int = 0
        self.room_id: Optional[str] = None
        self.is_authenticated: bool = False
        self.metadata: dict[str, Any] = {}
    
    def update_heartbeat(self) -> None:
        """更新心跳时间"""
        self.last_heartbeat = int(time.time() * 1000)
        self.missed_heartbeats = 0
    
    def is_heartbeat_timeout(self) -> bool:
        """检查心跳是否超时"""
        elapsed = (time.time() * 1000 - self.last_heartbeat) / 1000
        return elapsed > HeartbeatConfig.TIMEOUT
    
    def should_disconnect(self) -> bool:
        """检查是否应该断开连接"""
        return self.missed_heartbeats >= HeartbeatConfig.MAX_MISSED_HEARTBEATS


class SessionManager:
    """
    会话管理器
    
    管理所有活跃的 WebSocket 会话。
    
    使用方式:
        manager = SessionManager()
        session = manager.create_session(player_id, websocket)
    """
    
    def __init__(self) -> None:
        """初始化会话管理器"""
        # session_id -> Session
        self._sessions: dict[str, Session] = {}
        # player_id -> session_id (用于快速查找)
        self._player_sessions: dict[str, str] = {}
        # 用于生成会话ID
        self._session_counter: int = 0
    
    def _generate_session_id(self) -> str:
        """生成会话ID"""
        self._session_counter += 1
        return f"sess_{int(time.time() * 1000)}_{self._session_counter}"
    
    def create_session(
        self,
        player_id: str,
        websocket: WebSocket,
    ) -> Session:
        """
        创建新会话
        
        Args:
            player_id: 玩家ID
            websocket: WebSocket 连接
            
        Returns:
            创建的会话对象
            
        Raises:
            ValueError: 玩家已连接
        """
        # 检查是否已连接
        if player_id in self._player_sessions:
            old_session_id = self._player_sessions[player_id]
            if old_session_id in self._sessions:
                # 强制断开旧连接
                old_session = self._sessions[old_session_id]
                asyncio.create_task(self._close_session(old_session))
        
        # 创建新会话
        session_id = self._generate_session_id()
        session = Session(
            session_id=session_id,
            player_id=player_id,
            websocket=websocket,
        )
        
        self._sessions[session_id] = session
        self._player_sessions[player_id] = session_id
        
        logger.info(
            "会话创建",
            session_id=session_id,
            player_id=player_id,
            total_sessions=len(self._sessions),
        )
        
        return session
    
    async def _close_session(self, session: Session) -> None:
        """关闭会话（内部方法）"""
        try:
            await session.websocket.close(code=1000, reason="新连接建立")
        except Exception:
            pass
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """
        获取会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话对象，如果不存在返回 None
        """
        return self._sessions.get(session_id)
    
    def get_session_by_player(self, player_id: str) -> Optional[Session]:
        """
        根据玩家ID获取会话
        
        Args:
            player_id: 玩家ID
            
        Returns:
            会话对象，如果不存在返回 None
        """
        session_id = self._player_sessions.get(player_id)
        if session_id is None:
            return None
        return self._sessions.get(session_id)
    
    def remove_session(self, session_id: str) -> Optional[Session]:
        """
        移除会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            被移除的会话对象
        """
        session = self._sessions.pop(session_id, None)
        if session is not None:
            self._player_sessions.pop(session.player_id, None)
            logger.info(
                "会话移除",
                session_id=session_id,
                player_id=session.player_id,
                total_sessions=len(self._sessions),
            )
        return session
    
    def get_all_sessions(self) -> list[Session]:
        """获取所有会话"""
        return list(self._sessions.values())
    
    def get_sessions_in_room(self, room_id: str) -> list[Session]:
        """
        获取房间内的所有会话
        
        Args:
            room_id: 房间ID
            
        Returns:
            会话列表
        """
        return [
            session for session in self._sessions.values()
            if session.room_id == room_id
        ]
    
    def set_player_room(self, player_id: str, room_id: Optional[str]) -> None:
        """
        设置玩家所在房间
        
        Args:
            player_id: 玩家ID
            room_id: 房间ID（None 表示离开房间）
        """
        session = self.get_session_by_player(player_id)
        if session is not None:
            session.room_id = room_id


# ============================================================================
# 消息处理器类型
# ============================================================================

# 消息处理器函数类型
MessageHandler = Callable[[Session, BaseMessage], Any]


# ============================================================================
# WebSocket 处理器
# ============================================================================

class WebSocketHandler:
    """
    WebSocket 处理器
    
    管理 WebSocket 连接和消息处理。
    
    使用方式:
        handler = WebSocketHandler()
        
        @handler.on_message(MessageType.SHOP_REFRESH)
        async def handle_shop_refresh(session: Session, message: ShopRefreshMessage):
            ...
    """
    
    def __init__(self) -> None:
        """初始化处理器"""
        self.session_manager = SessionManager()
        self._handlers: dict[MessageType, MessageHandler] = {}
        self._heartbeat_task: Optional[asyncio.Task[None]] = None
        self._room_handler: Optional[RoomWSHandler] = None
        
        # 注册内置处理器
        self._register_builtin_handlers()
    
    def set_room_handler(self, handler: RoomWSHandler) -> None:
        """
        设置房间处理器
        
        Args:
            handler: 房间 WebSocket 处理器
        """
        self._room_handler = handler
    
    def _register_builtin_handlers(self) -> None:
        """注册内置消息处理器"""
        self._handlers[MessageType.HEARTBEAT] = self._handle_heartbeat
        self._handlers[MessageType.CONNECT] = self._handle_connect
        self._handlers[MessageType.RECONNECT] = self._handle_reconnect
        self._handlers[MessageType.DISCONNECT] = self._handle_disconnect
    
    def on_message(self, message_type: MessageType) -> Callable[[MessageHandler], MessageHandler]:
        """
        注册消息处理器装饰器
        
        Args:
            message_type: 消息类型
            
        Returns:
            装饰器函数
            
        使用示例:
            @handler.on_message(MessageType.SHOP_REFRESH)
            async def handle_shop_refresh(session, message):
                ...
        """
        def decorator(func: MessageHandler) -> MessageHandler:
            self._handlers[message_type] = func
            return func
        return decorator
    
    async def handle_connection(self, websocket: WebSocket) -> None:
        """
        处理 WebSocket 连接
        
        这是 WebSocket 路由的入口点。
        
        Args:
            websocket: WebSocket 连接
        """
        session: Optional[Session] = None
        
        try:
            # 等待连接消息
            data = await websocket.receive_text()
            
            try:
                message = decode_message(data)
            except MessageCodecError as e:
                await self._send_error(websocket, e.code, str(e))
                await websocket.close(code=1008, reason="Invalid message")
                return
            
            # 处理连接/重连
            if message.type == MessageType.CONNECT:
                connect_msg = message
                if not isinstance(connect_msg, ConnectMessage):
                    await self._send_error(websocket, WSErrorCode.INVALID_MESSAGE, "无效的连接消息")
                    return
                
                session = await self._process_connect(websocket, connect_msg)
                if session is None:
                    return
            
            elif message.type == MessageType.RECONNECT:
                reconnect_msg = message
                if not isinstance(reconnect_msg, ReconnectMessage):
                    await self._send_error(websocket, WSErrorCode.INVALID_MESSAGE, "无效的重连消息")
                    return
                
                session = await self._process_reconnect(websocket, reconnect_msg)
                if session is None:
                    return
            
            else:
                await self._send_error(websocket, WSErrorCode.INVALID_MESSAGE, "请先发送连接消息")
                await websocket.close(code=1008, reason="Connection required")
                return
            
            # 开始心跳任务
            if self._heartbeat_task is None or self._heartbeat_task.done():
                self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
            # 消息处理循环
            await self._message_loop(websocket, session)
        
        except WebSocketDisconnect:
            logger.info("WebSocket 断开", player_id=session.player_id if session else None)
        except Exception as e:
            logger.exception("WebSocket 错误", error=str(e))
        finally:
            # 清理会话
            if session is not None:
                await self._cleanup_session(session)
    
    async def _process_connect(
        self,
        websocket: WebSocket,
        message: ConnectMessage,
    ) -> Optional[Session]:
        """
        处理连接请求
        
        Args:
            websocket: WebSocket 连接
            message: 连接消息
            
        Returns:
            会话对象，失败返回 None
        """
        player_id = message.player_id
        token = message.token
        
        # TODO: 验证 token
        # if not await self._verify_token(player_id, token):
        #     await self._send_error(websocket, WSErrorCode.INVALID_TOKEN, "无效的认证令牌")
        #     return None
        
        # 创建会话
        session = self.session_manager.create_session(player_id, websocket)
        session.is_authenticated = True
        session.metadata["version"] = message.version
        
        # 发送连接成功消息
        response = ConnectedMessage(
            player_id=player_id,
            session_id=session.session_id,
            server_time=int(time.time() * 1000),
        )
        await self._send_message(websocket, response)
        
        logger.info(
            "玩家连接成功",
            player_id=player_id,
            session_id=session.session_id,
            version=message.version,
        )
        
        return session
    
    async def _process_reconnect(
        self,
        websocket: WebSocket,
        message: ReconnectMessage,
    ) -> Optional[Session]:
        """
        处理重连请求
        
        Args:
            websocket: WebSocket 连接
            message: 重连消息
            
        Returns:
            会话对象，失败返回 None
        """
        old_session = self.session_manager.get_session(message.session_id)
        
        if old_session is None:
            await self._send_error(websocket, WSErrorCode.SESSION_EXPIRED, "会话已过期")
            return None
        
        if old_session.player_id != message.player_id:
            await self._send_error(websocket, WSErrorCode.INVALID_TOKEN, "玩家ID不匹配")
            return None
        
        # 更新会话
        old_session.websocket = websocket
        old_session.update_heartbeat()
        
        # 发送重连成功消息
        game_state = None
        if self._room_handler is not None and old_session.room_id:
            # 获取游戏状态
            game_state = await self._room_handler.get_player_game_state(
                old_session.room_id,
                old_session.player_id,
            )
        
        response = ReconnectedMessage(
            player_id=old_session.player_id,
            room_id=old_session.room_id,
            game_state=game_state,
        )
        await self._send_message(websocket, response)
        
        logger.info(
            "玩家重连成功",
            player_id=old_session.player_id,
            session_id=old_session.session_id,
            room_id=old_session.room_id,
        )
        
        return old_session
    
    async def _message_loop(self, websocket: WebSocket, session: Session) -> None:
        """
        消息处理循环
        
        Args:
            websocket: WebSocket 连接
            session: 会话对象
        """
        while True:
            try:
                data = await websocket.receive_text()
                
                try:
                    message = decode_message(data)
                except MessageCodecError as e:
                    await self._send_error(
                        websocket,
                        WSErrorCode.PARSE_ERROR,
                        str(e),
                        seq=None,
                    )
                    continue
                
                # 更新心跳
                session.update_heartbeat()
                
                # 路由消息
                await self._route_message(session, message)
            
            except WebSocketDisconnect:
                raise
            except Exception as e:
                logger.exception(
                    "消息处理错误",
                    player_id=session.player_id,
                    error=str(e),
                )
    
    async def _route_message(self, session: Session, message: BaseMessage) -> None:
        """
        路由消息到对应处理器
        
        Args:
            session: 会话对象
            message: 消息对象
        """
        handler = self._handlers.get(message.type)
        
        if handler is None:
            logger.warning(
                "未知的消息类型",
                player_id=session.player_id,
                message_type=message.type,
            )
            await self._send_error(
                session.websocket,
                WSErrorCode.UNKNOWN_MESSAGE_TYPE,
                f"未知的消息类型: {message.type}",
                seq=message.seq,
            )
            return
        
        try:
            result = handler(session, message)
            if asyncio.iscoroutine(result):
                await result
        except Exception as e:
            logger.exception(
                "消息处理失败",
                player_id=session.player_id,
                message_type=message.type,
                error=str(e),
            )
            await self._send_error(
                session.websocket,
                WSErrorCode.INVALID_OPERATION,
                str(e),
                seq=message.seq,
            )
    
    async def _handle_heartbeat(self, session: Session, message: HeartbeatMessage) -> None:
        """处理心跳消息"""
        session.update_heartbeat()
        response = HeartbeatAckMessage(
            server_time=int(time.time() * 1000),
            seq=message.seq,
        )
        await self._send_message(session.websocket, response)
    
    async def _handle_connect(self, session: Session, message: ConnectMessage) -> None:
        """处理连接消息（已在连接阶段处理）"""
        # 连接消息在连接阶段已经处理，这里忽略
        pass
    
    async def _handle_reconnect(self, session: Session, message: ReconnectMessage) -> None:
        """处理重连消息（已在连接阶段处理）"""
        # 重连消息在连接阶段已经处理，这里忽略
        pass
    
    async def _handle_disconnect(self, session: Session, message: DisconnectMessage) -> None:
        """处理断开连接消息"""
        logger.info(
            "玩家主动断开",
            player_id=session.player_id,
            reason=message.reason,
        )
        await session.websocket.close(code=1000, reason=message.reason or "Normal closure")
    
    async def _heartbeat_loop(self) -> None:
        """心跳检测循环"""
        while True:
            try:
                await asyncio.sleep(HeartbeatConfig.INTERVAL)
                
                now = time.time() * 1000
                sessions_to_remove: list[str] = []
                
                for session in self.session_manager.get_all_sessions():
                    # 检查心跳超时
                    if session.is_heartbeat_timeout():
                        session.missed_heartbeats += 1
                        logger.warning(
                            "心跳超时",
                            player_id=session.player_id,
                            missed_heartbeats=session.missed_heartbeats,
                        )
                    
                    # 检查是否需要断开
                    if session.should_disconnect():
                        sessions_to_remove.append(session.session_id)
                        logger.info(
                            "心跳超时断开",
                            player_id=session.player_id,
                        )
                        try:
                            await session.websocket.close(
                                code=1001,
                                reason="Heartbeat timeout",
                            )
                        except Exception:
                            pass
                
                # 移除超时会话
                for session_id in sessions_to_remove:
                    self.session_manager.remove_session(session_id)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception("心跳循环错误", error=str(e))
    
    async def _cleanup_session(self, session: Session) -> None:
        """
        清理会话
        
        Args:
            session: 会话对象
        """
        # 如果在房间中，通知房间处理器
        if session.room_id and self._room_handler is not None:
            await self._room_handler.handle_player_disconnect(
                session.room_id,
                session.player_id,
            )
        
        # 移除会话
        self.session_manager.remove_session(session.session_id)
        
        logger.info(
            "会话清理完成",
            session_id=session.session_id,
            player_id=session.player_id,
        )
    
    async def _send_message(self, websocket: WebSocket, message: BaseMessage) -> None:
        """
        发送消息
        
        Args:
            websocket: WebSocket 连接
            message: 消息对象
        """
        try:
            data = encode_message(message)
            await websocket.send_text(data)
        except Exception as e:
            logger.warning("发送消息失败", error=str(e))
    
    async def _send_error(
        self,
        websocket: WebSocket,
        code: int,
        message: str,
        details: Optional[dict[str, Any]] = None,
        seq: Optional[int] = None,
    ) -> None:
        """
        发送错误消息
        
        Args:
            websocket: WebSocket 连接
            code: 错误码
            message: 错误描述
            details: 错误详情
            seq: 消息序列号
        """
        error_msg = ErrorMessage(
            code=code,
            message=message,
            details=details,
            seq=seq,
        )
        await self._send_message(websocket, error_msg)
    
    # ========================================================================
    # 公共方法（供外部调用）
    # ========================================================================
    
    async def send_to_player(self, player_id: str, message: BaseMessage) -> bool:
        """
        向指定玩家发送消息
        
        Args:
            player_id: 玩家ID
            message: 消息对象
            
        Returns:
            是否发送成功
        """
        session = self.session_manager.get_session_by_player(player_id)
        if session is None:
            logger.warning("玩家不在线", player_id=player_id)
            return False
        
        await self._send_message(session.websocket, message)
        return True
    
    async def broadcast_to_players(
        self,
        player_ids: list[str],
        message: BaseMessage,
    ) -> int:
        """
        向多个玩家广播消息
        
        Args:
            player_ids: 玩家ID列表
            message: 消息对象
            
        Returns:
            成功发送数量
        """
        success_count = 0
        for player_id in player_ids:
            if await self.send_to_player(player_id, message):
                success_count += 1
        return success_count
    
    def is_player_online(self, player_id: str) -> bool:
        """
        检查玩家是否在线
        
        Args:
            player_id: 玩家ID
            
        Returns:
            是否在线
        """
        return self.session_manager.get_session_by_player(player_id) is not None
    
    def get_online_players(self) -> list[str]:
        """
        获取所有在线玩家ID
        
        Returns:
            玩家ID列表
        """
        return list(self.session_manager._player_sessions.keys())


# ============================================================================
# 全局处理器实例
# ============================================================================

# 全局 WebSocket 处理器
ws_handler = WebSocketHandler()
