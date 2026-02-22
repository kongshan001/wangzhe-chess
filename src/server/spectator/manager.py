"""
王者之奕 - 观战系统管理器

本模块提供观战系统的核心管理功能：
- SpectatorManager: 观战管理器类
- 创建/销毁观战会话
- 管理观众加入/离开
- 延迟同步游戏状态
- 处理弹幕/聊天

使用内存存储实现高性能。
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional

from .models import (
    GameVisibility,
    SpectatableGame,
    SpectatorChat,
    SpectatorData,
    SpectatorGameState,
    SpectatorSession,
    SpectatorStatus,
)

logger = logging.getLogger(__name__)


class SpectatorManager:
    """
    观战管理器
    
    负责管理所有观战相关的操作：
    - 观战会话管理
    - 游戏状态同步（延迟机制）
    - 弹幕/聊天管理
    - 可观战对局列表
    
    Attributes:
        games: 对局观战数据 (game_id -> SpectatorData)
        sessions: 观战会话 (session_id -> SpectatorSession)
        player_sessions: 玩家的观战会话 (player_id -> session_id)
        chat_history: 聊天历史 (game_id -> List[SpectatorChat])
    """
    
    # 延迟同步配置
    DEFAULT_DELAY_SECONDS = 30  # 默认延迟30秒
    MAX_CHAT_HISTORY = 100  # 每个对局最多保留100条聊天
    MAX_SPECTATORS = 100  # 每个对局最多100个观众
    
    def __init__(self) -> None:
        """初始化观战管理器"""
        # 对局观战数据
        self._games: Dict[str, SpectatorData] = {}
        # 所有观战会话
        self._sessions: Dict[str, SpectatorSession] = {}
        # 玩家的观战会话映射
        self._player_sessions: Dict[str, str] = {}
        # 聊天历史
        self._chat_history: Dict[str, List[SpectatorChat]] = defaultdict(list)
        # 状态更新回调
        self._on_state_update: Optional[Callable[[str, SpectatorGameState], None]] = None
        # 聊天回调
        self._on_chat: Optional[Callable[[SpectatorChat], None]] = None
        # 计数器
        self._session_counter = 0
        self._chat_counter = 0
        
        logger.info("SpectatorManager initialized")
    
    # ========================================================================
    # 会话ID生成
    # ========================================================================
    
    def _generate_session_id(self) -> str:
        """生成会话ID"""
        self._session_counter += 1
        return f"spec_sess_{int(time.time() * 1000)}_{self._session_counter}"
    
    def _generate_chat_id(self) -> str:
        """生成聊天ID"""
        self._chat_counter += 1
        return f"chat_{int(time.time() * 1000)}_{self._chat_counter}"
    
    # ========================================================================
    # 对局观战管理
    # ========================================================================
    
    def create_spectatable_game(
        self,
        game_id: str,
        visibility: GameVisibility = GameVisibility.PUBLIC,
        allowed_spectators: Optional[List[str]] = None,
        delay_seconds: int = DEFAULT_DELAY_SECONDS,
    ) -> SpectatorData:
        """
        创建可观战对局
        
        Args:
            game_id: 对局ID
            visibility: 可见性
            allowed_spectators: 允许观战的玩家列表（好友观战）
            delay_seconds: 延迟秒数
            
        Returns:
            观战数据
        """
        if game_id in self._games:
            logger.warning(f"Game {game_id} already spectatable, returning existing")
            return self._games[game_id]
        
        spectator_data = SpectatorData(
            game_id=game_id,
            visibility=visibility,
            allowed_spectators=allowed_spectators or [],
            delay_seconds=delay_seconds,
        )
        
        self._games[game_id] = spectator_data
        
        logger.info(
            f"Created spectatable game: {game_id}",
            extra={
                "game_id": game_id,
                "visibility": visibility.value,
                "delay_seconds": delay_seconds,
            }
        )
        
        return spectator_data
    
    def remove_spectatable_game(self, game_id: str) -> Optional[SpectatorData]:
        """
        移除可观战对局
        
        Args:
            game_id: 对局ID
            
        Returns:
            被移除的观战数据
        """
        spectator_data = self._games.pop(game_id, None)
        
        if spectator_data is None:
            return None
        
        # 移除所有观众的会话
        for session_id in list(spectator_data.spectators.keys()):
            session = spectator_data.spectators[session_id]
            self._sessions.pop(session_id, None)
            self._player_sessions.pop(session.spectator_id, None)
        
        # 清理聊天历史
        self._chat_history.pop(game_id, None)
        
        logger.info(
            f"Removed spectatable game: {game_id}",
            extra={"game_id": game_id}
        )
        
        return spectator_data
    
    def get_spectatable_game(self, game_id: str) -> Optional[SpectatorData]:
        """
        获取可观战对局
        
        Args:
            game_id: 对局ID
            
        Returns:
            观战数据
        """
        return self._games.get(game_id)
    
    def is_spectatable(self, game_id: str) -> bool:
        """
        检查对局是否可观战
        
        Args:
            game_id: 对局ID
            
        Returns:
            是否可观战
        """
        return game_id in self._games
    
    # ========================================================================
    # 观战会话管理
    # ========================================================================
    
    def create_session(
        self,
        spectator_id: str,
        game_id: str,
        watching_player_id: str,
    ) -> Optional[SpectatorSession]:
        """
        创建观战会话
        
        Args:
            spectator_id: 观众ID
            game_id: 对局ID
            watching_player_id: 观看的玩家ID
            
        Returns:
            观战会话，失败返回 None
        """
        # 检查对局是否存在
        spectator_data = self._games.get(game_id)
        if spectator_data is None:
            logger.warning(f"Game {game_id} not found for spectator {spectator_id}")
            return None
        
        # 检查是否已在观战中
        if spectator_id in self._player_sessions:
            old_session_id = self._player_sessions[spectator_id]
            old_session = self._sessions.get(old_session_id)
            if old_session:
                # 离开旧的观战
                self.leave_spectate(old_session_id)
        
        # 创建会话
        session_id = self._generate_session_id()
        session = SpectatorSession(
            session_id=session_id,
            spectator_id=spectator_id,
            game_id=game_id,
            watching_player_id=watching_player_id,
        )
        
        # 添加到对局
        if not spectator_data.add_spectator(session):
            logger.warning(f"Failed to add spectator {spectator_id} to game {game_id}")
            return None
        
        # 记录会话
        self._sessions[session_id] = session
        self._player_sessions[spectator_id] = session_id
        
        logger.info(
            f"Spectator session created: {session_id}",
            extra={
                "session_id": session_id,
                "spectator_id": spectator_id,
                "game_id": game_id,
                "watching_player_id": watching_player_id,
            }
        )
        
        return session
    
    def leave_spectate(self, session_id: str) -> Optional[SpectatorSession]:
        """
        离开观战
        
        Args:
            session_id: 会话ID
            
        Returns:
            被移除的会话
        """
        session = self._sessions.pop(session_id, None)
        
        if session is None:
            return None
        
        # 从对局中移除
        spectator_data = self._games.get(session.game_id)
        if spectator_data:
            spectator_data.remove_spectator(session_id)
        
        # 移除玩家映射
        self._player_sessions.pop(session.spectator_id, None)
        
        logger.info(
            f"Spectator left: {session_id}",
            extra={
                "session_id": session_id,
                "spectator_id": session.spectator_id,
                "game_id": session.game_id,
            }
        )
        
        return session
    
    def get_session(self, session_id: str) -> Optional[SpectatorSession]:
        """
        获取观战会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            观战会话
        """
        return self._sessions.get(session_id)
    
    def get_session_by_player(self, player_id: str) -> Optional[SpectatorSession]:
        """
        根据玩家ID获取会话
        
        Args:
            player_id: 玩家ID
            
        Returns:
            观战会话
        """
        session_id = self._player_sessions.get(player_id)
        if session_id is None:
            return None
        return self._sessions.get(session_id)
    
    def switch_watching_player(
        self,
        session_id: str,
        new_player_id: str,
    ) -> Optional[SpectatorSession]:
        """
        切换观战对象
        
        Args:
            session_id: 会话ID
            new_player_id: 新的观看玩家ID
            
        Returns:
            更新后的会话
        """
        session = self._sessions.get(session_id)
        if session is None:
            return None
        
        session.switch_player(new_player_id)
        
        logger.info(
            f"Spectator switched player: {session_id} -> {new_player_id}",
            extra={
                "session_id": session_id,
                "new_player_id": new_player_id,
            }
        )
        
        return session
    
    # ========================================================================
    # 可观战对局列表
    # ========================================================================
    
    def get_spectatable_games(
        self,
        page: int = 1,
        page_size: int = 20,
        include_private: bool = False,
    ) -> List[SpectatableGame]:
        """
        获取可观战对局列表
        
        Args:
            page: 页码
            page_size: 每页大小
            include_private: 是否包含私密对局
            
        Returns:
            可观战对局列表
        """
        result = []
        
        for game_id, spectator_data in self._games.items():
            # 过滤私密对局
            if not include_private and spectator_data.visibility == GameVisibility.PRIVATE:
                continue
            
            # 构建玩家信息（需要从外部获取）
            # 这里使用占位符，实际应从游戏管理器获取
            players = spectator_data.metadata.get("players", [])
            
            # 获取最新状态中的回合数
            current_round = 0
            if spectator_data.state_history:
                current_round = spectator_data.state_history[-1].round_num
            
            game_info = SpectatableGame(
                game_id=game_id,
                players=players,
                created_at=spectator_data.created_at,
                current_round=current_round,
                spectator_count=spectator_data.get_spectator_count(),
                visibility=spectator_data.visibility,
                is_featured=spectator_data.metadata.get("is_featured", False),
            )
            
            result.append(game_info)
        
        # 按观众数量排序（热门对局在前）
        result.sort(key=lambda x: x.spectator_count, reverse=True)
        
        # 分页
        start = (page - 1) * page_size
        end = start + page_size
        
        return result[start:end]
    
    def update_game_players(
        self,
        game_id: str,
        players: List[Dict[str, Any]],
    ) -> None:
        """
        更新对局玩家信息
        
        Args:
            game_id: 对局ID
            players: 玩家信息列表
        """
        spectator_data = self._games.get(game_id)
        if spectator_data:
            spectator_data.metadata["players"] = players
    
    def set_game_featured(self, game_id: str, featured: bool) -> None:
        """
        设置对局为精选
        
        Args:
            game_id: 对局ID
            featured: 是否精选
        """
        spectator_data = self._games.get(game_id)
        if spectator_data:
            spectator_data.metadata["is_featured"] = featured
    
    # ========================================================================
    # 延迟同步机制
    # ========================================================================
    
    def push_game_state(
        self,
        game_id: str,
        round_num: int,
        phase: str,
        player_states: Dict[str, Any],
        **kwargs: Any,
    ) -> Optional[SpectatorGameState]:
        """
        推送游戏状态（用于延迟同步）
        
        Args:
            game_id: 对局ID
            round_num: 当前回合
            phase: 当前阶段
            player_states: 玩家状态
            **kwargs: 额外状态信息
            
        Returns:
            创建的状态快照
        """
        spectator_data = self._games.get(game_id)
        if spectator_data is None:
            logger.warning(f"Game {game_id} not found for state push")
            return None
        
        # 创建状态快照
        snapshot_time = int(time.time() * 1000)
        state = SpectatorGameState(
            snapshot_time=snapshot_time,
            game_id=game_id,
            round_num=round_num,
            phase=phase,
            player_states=player_states,
            timestamp=snapshot_time,
            **kwargs,
        )
        
        # 推送到历史
        spectator_data.push_state(state)
        
        logger.debug(
            f"Pushed game state for {game_id}",
            extra={
                "game_id": game_id,
                "round_num": round_num,
                "phase": phase,
                "snapshot_time": snapshot_time,
            }
        )
        
        # 触发回调
        if self._on_state_update:
            self._on_state_update(game_id, state)
        
        return state
    
    def get_delayed_state(
        self,
        game_id: str,
    ) -> Optional[SpectatorGameState]:
        """
        获取延迟后的游戏状态
        
        Args:
            game_id: 对局ID
            
        Returns:
            延迟的游戏状态
        """
        spectator_data = self._games.get(game_id)
        if spectator_data is None:
            return None
        
        return spectator_data.get_delayed_state()
    
    def get_state_for_spectator(
        self,
        session_id: str,
    ) -> Optional[SpectatorGameState]:
        """
        为观众获取延迟状态
        
        Args:
            session_id: 会话ID
            
        Returns:
            延迟的游戏状态
        """
        session = self._sessions.get(session_id)
        if session is None:
            return None
        
        state = self.get_delayed_state(session.game_id)
        if state:
            session.update_sync_time()
        
        return state
    
    def set_state_update_callback(
        self,
        callback: Callable[[str, SpectatorGameState], None],
    ) -> None:
        """
        设置状态更新回调
        
        Args:
            callback: 回调函数 (game_id, state)
        """
        self._on_state_update = callback
    
    # ========================================================================
    # 弹幕/聊天管理
    # ========================================================================
    
    def send_chat(
        self,
        game_id: str,
        sender_id: str,
        sender_name: str,
        content: str,
        message_type: str = "text",
        avatar: Optional[str] = None,
        tier: Optional[str] = None,
    ) -> Optional[SpectatorChat]:
        """
        发送弹幕/聊天消息
        
        Args:
            game_id: 对局ID
            sender_id: 发送者ID
            sender_name: 发送者昵称
            content: 消息内容
            message_type: 消息类型
            avatar: 头像
            tier: 段位
            
        Returns:
            聊天消息
        """
        # 检查对局是否存在
        spectator_data = self._games.get(game_id)
        if spectator_data is None:
            logger.warning(f"Game {game_id} not found for chat")
            return None
        
        # 创建消息
        chat = SpectatorChat(
            chat_id=self._generate_chat_id(),
            game_id=game_id,
            sender_id=sender_id,
            sender_name=sender_name,
            content=content,
            message_type=message_type,
            avatar=avatar,
            tier=tier,
        )
        
        # 验证消息
        if not chat.is_valid():
            logger.warning(f"Invalid chat message from {sender_id}")
            return None
        
        # 添加到历史
        self._chat_history[game_id].append(chat)
        
        # 限制历史长度
        if len(self._chat_history[game_id]) > self.MAX_CHAT_HISTORY:
            self._chat_history[game_id] = self._chat_history[game_id][-self.MAX_CHAT_HISTORY:]
        
        logger.debug(
            f"Chat message sent in {game_id}",
            extra={
                "game_id": game_id,
                "sender_id": sender_id,
                "content": content[:50],
            }
        )
        
        # 触发回调
        if self._on_chat:
            self._on_chat(chat)
        
        return chat
    
    def get_chat_history(
        self,
        game_id: str,
        limit: int = 50,
        before: Optional[int] = None,
    ) -> List[SpectatorChat]:
        """
        获取聊天历史
        
        Args:
            game_id: 对局ID
            limit: 返回数量
            before: 在此时间之前的消息
            
        Returns:
            聊天消息列表
        """
        history = self._chat_history.get(game_id, [])
        
        if before:
            history = [c for c in history if c.sent_at < before]
        
        # 按时间倒序，取最新的
        return history[-limit:]
    
    def clear_chat_history(self, game_id: str) -> None:
        """
        清空聊天历史
        
        Args:
            game_id: 对局ID
        """
        self._chat_history[game_id] = []
    
    def set_chat_callback(
        self,
        callback: Callable[[SpectatorChat], None],
    ) -> None:
        """
        设置聊天回调
        
        Args:
            callback: 回调函数
        """
        self._on_chat = callback
    
    # ========================================================================
    # 统计信息
    # ========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计信息
        """
        total_spectators = len(self._sessions)
        total_games = len(self._games)
        total_chats = sum(len(chats) for chats in self._chat_history.values())
        
        return {
            "total_spectators": total_spectators,
            "total_games": total_games,
            "total_chats": total_chats,
            "games": {
                game_id: data.get_spectator_count()
                for game_id, data in self._games.items()
            },
        }
    
    # ========================================================================
    # 批量操作
    # ========================================================================
    
    def get_spectators_in_game(self, game_id: str) -> List[SpectatorSession]:
        """
        获取对局中的所有观众
        
        Args:
            game_id: 对局ID
            
        Returns:
            观众会话列表
        """
        spectator_data = self._games.get(game_id)
        if spectator_data is None:
            return []
        
        return list(spectator_data.spectators.values())
    
    def broadcast_to_game_spectators(
        self,
        game_id: str,
        message: Any,
    ) -> int:
        """
        向对局的所有观众广播消息
        
        Args:
            game_id: 对局ID
            message: 消息
            
        Returns:
            成功发送数量
        """
        # 这个方法需要与 WebSocket 处理器集成
        # 返回观众数量，实际发送由 WebSocket 处理器完成
        spectators = self.get_spectators_in_game(game_id)
        return len(spectators)


# ========================================================================
# 全局单例
# ========================================================================

_spectator_manager: Optional[SpectatorManager] = None


def get_spectator_manager() -> SpectatorManager:
    """
    获取观战管理器单例
    
    Returns:
        观战管理器实例
    """
    global _spectator_manager
    if _spectator_manager is None:
        _spectator_manager = SpectatorManager()
    return _spectator_manager
