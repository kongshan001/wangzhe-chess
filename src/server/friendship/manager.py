"""
王者之奕 - 好友系统管理器

本模块提供好友系统的管理功能：
- FriendshipManager: 好友管理器类
- 添加/删除好友
- 好友请求处理
- 黑名单管理
- 私聊消息
- 组队功能
- 在线状态管理
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Callable, TYPE_CHECKING

from .models import (
    BlockedPlayer,
    FriendInfo,
    FriendRelation,
    FriendRequest,
    FriendRequestData,
    FriendRequestStatus,
    FriendStatus,
    PrivateMessage,
    PrivateMessageData,
    TeamInfo,
)

if TYPE_CHECKING:
    from src.server.ws.handler import WebSocketHandler

logger = logging.getLogger(__name__)


class FriendshipManager:
    """
    好友系统管理器
    
    负责管理所有好友相关的操作：
    - 好友关系管理
    - 好友请求处理
    - 黑名单管理
    - 私聊消息
    - 组队功能
    - 在线状态管理
    
    Attributes:
        friends: 好友关系 (player_id -> {friend_id: FriendInfo})
        requests: 好友请求 (request_id -> FriendRequest)
        pending_requests: 待处理的请求 (player_id -> {request_ids})
        sent_requests: 发送的请求 (player_id -> {request_ids})
        blocked_players: 黑名单 (player_id -> {blocked_player_ids})
        private_messages: 私聊消息 (聊天对 -> [PrivateMessage])
        teams: 队伍 (team_id -> TeamInfo)
        player_teams: 玩家所在队伍 (player_id -> team_id)
        online_players: 在线状态 (player_id -> FriendStatus)
        player_game_info: 玩家游戏信息 (player_id -> 游戏信息)
    """
    
    def __init__(self, ws_handler: Optional["WebSocketHandler"] = None):
        """
        初始化好友管理器
        
        Args:
            ws_handler: WebSocket处理器（用于发送实时消息）
        """
        # WebSocket处理器
        self._ws_handler = ws_handler
        
        # 好友关系
        self.friends: Dict[str, Dict[str, FriendInfo]] = {}
        
        # 好友请求
        self.requests: Dict[str, FriendRequest] = {}
        self.pending_requests: Dict[str, Set[str]] = {}  # 接收到的请求
        self.sent_requests: Dict[str, Set[str]] = {}     # 发送的请求
        
        # 黑名单
        self.blocked_players: Dict[str, Set[str]] = {}   # 我拉黑的人
        self.blocked_by_players: Dict[str, Set[str]] = {}  # 拉黑我的人
        
        # 私聊消息（最近的消息）
        self.private_messages: Dict[str, List[PrivateMessage]] = {}  # key: "id1_id2" (sorted)
        self._max_messages_per_chat = 100
        
        # 队伍
        self.teams: Dict[str, TeamInfo] = {}
        self.player_teams: Dict[str, str] = {}  # player_id -> team_id
        
        # 在线状态
        self.online_players: Dict[str, FriendStatus] = {}
        self.player_game_info: Dict[str, Dict[str, Any]] = {}
        
        # 玩家信息缓存
        self._player_cache: Dict[str, Dict[str, Any]] = {}
        
        # 好友数量限制
        self.max_friends = 100
        self.max_pending_requests = 50
        
        logger.info("FriendshipManager initialized")
    
    def set_ws_handler(self, handler: "WebSocketHandler") -> None:
        """设置WebSocket处理器"""
        self._ws_handler = handler
    
    # ========================================================================
    # 玩家信息缓存
    # ========================================================================
    
    def update_player_cache(
        self,
        player_id: str,
        nickname: str = "",
        avatar: str = "",
        tier: str = "bronze",
        stars: int = 0,
    ) -> None:
        """
        更新玩家信息缓存
        
        Args:
            player_id: 玩家ID
            nickname: 昵称
            avatar: 头像
            tier: 段位
            stars: 星数
        """
        self._player_cache[player_id] = {
            "player_id": player_id,
            "nickname": nickname,
            "avatar": avatar,
            "tier": tier,
            "stars": stars,
        }
    
    def _get_player_info(self, player_id: str) -> Dict[str, Any]:
        """获取玩家信息"""
        return self._player_cache.get(player_id, {
            "player_id": player_id,
            "nickname": player_id,
            "avatar": "",
            "tier": "bronze",
            "stars": 0,
        })
    
    # ========================================================================
    # 在线状态管理
    # ========================================================================
    
    def set_player_online(self, player_id: str) -> None:
        """设置玩家在线"""
        self.online_players[player_id] = FriendStatus.ONLINE
        self._broadcast_status_change(player_id, FriendStatus.ONLINE)
        logger.debug(f"Player {player_id} is now online")
    
    def set_player_offline(self, player_id: str) -> None:
        """设置玩家离线"""
        self.online_players.pop(player_id, None)
        self.player_game_info.pop(player_id, None)
        self._broadcast_status_change(player_id, FriendStatus.OFFLINE)
        logger.debug(f"Player {player_id} is now offline")
    
    def set_player_status(
        self,
        player_id: str,
        status: FriendStatus,
        game_info: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        设置玩家状态
        
        Args:
            player_id: 玩家ID
            status: 状态
            game_info: 游戏信息（如果游戏中）
        """
        self.online_players[player_id] = status
        if game_info:
            self.player_game_info[player_id] = game_info
        else:
            self.player_game_info.pop(player_id, None)
        self._broadcast_status_change(player_id, status, game_info)
        logger.debug(f"Player {player_id} status changed to {status.value}")
    
    def get_player_status(self, player_id: str) -> FriendStatus:
        """获取玩家状态"""
        return self.online_players.get(player_id, FriendStatus.OFFLINE)
    
    def _broadcast_status_change(
        self,
        player_id: str,
        status: FriendStatus,
        game_info: Optional[Dict[str, Any]] = None,
    ) -> None:
        """广播状态变化给好友"""
        # TODO: 通过WebSocket通知好友
        pass
    
    # ========================================================================
    # 好友关系管理
    # ========================================================================
    
    def get_friends(self, player_id: str) -> List[FriendInfo]:
        """
        获取玩家好友列表
        
        Args:
            player_id: 玩家ID
            
        Returns:
            好友信息列表
        """
        friends = self.friends.get(player_id, {})
        return list(friends.values())
    
    def get_friend(self, player_id: str, friend_id: str) -> Optional[FriendInfo]:
        """
        获取单个好友信息
        
        Args:
            player_id: 玩家ID
            friend_id: 好友ID
            
        Returns:
            好友信息，不存在返回None
        """
        friends = self.friends.get(player_id, {})
        return friends.get(friend_id)
    
    def is_friend(self, player_id: str, other_id: str) -> bool:
        """
        检查是否为好友
        
        Args:
            player_id: 玩家ID
            other_id: 另一个玩家ID
            
        Returns:
            是否为好友
        """
        friends = self.friends.get(player_id, {})
        friend = friends.get(other_id)
        return friend is not None and friend.relation == FriendRelation.FRIEND
    
    def _add_friend_relation(
        self,
        player_id: str,
        friend_id: str,
        relation: FriendRelation = FriendRelation.FRIEND,
    ) -> None:
        """
        添加好友关系（内部方法）
        
        Args:
            player_id: 玩家ID
            friend_id: 好友ID
            relation: 关系类型
        """
        # 初始化好友字典
        if player_id not in self.friends:
            self.friends[player_id] = {}
        
        # 获取好友信息
        friend_info = self._get_player_info(friend_id)
        status = self.get_player_status(friend_id)
        game_info = self.player_game_info.get(friend_id)
        
        # 创建FriendInfo
        friend = FriendInfo(
            player_id=friend_id,
            nickname=friend_info.get("nickname", friend_id),
            avatar=friend_info.get("avatar", ""),
            status=status,
            tier=friend_info.get("tier", "bronze"),
            stars=friend_info.get("stars", 0),
            relation=relation,
            last_online_at=datetime.now() if status != FriendStatus.OFFLINE else None,
            in_game_info=game_info,
        )
        
        self.friends[player_id][friend_id] = friend
    
    def _remove_friend_relation(self, player_id: str, friend_id: str) -> bool:
        """
        移除好友关系（内部方法）
        
        Args:
            player_id: 玩家ID
            friend_id: 好友ID
            
        Returns:
            是否成功移除
        """
        friends = self.friends.get(player_id, {})
        if friend_id in friends:
            del friends[friend_id]
            return True
        return False
    
    # ========================================================================
    # 好友请求管理
    # ========================================================================
    
    def send_friend_request(
        self,
        from_player_id: str,
        to_player_id: str,
        message: str = "",
    ) -> Optional[FriendRequest]:
        """
        发送好友请求
        
        Args:
            from_player_id: 发送者ID
            to_player_id: 接收者ID
            message: 附带消息
            
        Returns:
            创建的好友请求，失败返回None
        """
        # 不能添加自己
        if from_player_id == to_player_id:
            logger.warning(f"Player {from_player_id} tried to add themselves")
            return None
        
        # 检查是否已是好友
        if self.is_friend(from_player_id, to_player_id):
            logger.warning(f"Players {from_player_id} and {to_player_id} are already friends")
            return None
        
        # 检查是否被拉黑
        if self.is_blocked(from_player_id, to_player_id):
            logger.warning(f"Player {from_player_id} is blocked by {to_player_id}")
            return None
        
        # 检查是否已有待处理的请求
        pending = self.pending_requests.get(to_player_id, set())
        for req_id in pending:
            req = self.requests.get(req_id)
            if req and req.from_player_id == from_player_id and req.is_pending:
                logger.debug(f"Friend request already exists: {req_id}")
                return req
        
        # 检查好友数量限制
        friends = self.friends.get(from_player_id, {})
        if len(friends) >= self.max_friends:
            logger.warning(f"Player {from_player_id} has reached max friends limit")
            return None
        
        # 创建请求
        request_id = f"req_{uuid.uuid4().hex[:12]}"
        request = FriendRequest(
            request_id=request_id,
            from_player_id=from_player_id,
            to_player_id=to_player_id,
            message=message,
        )
        
        # 存储请求
        self.requests[request_id] = request
        
        # 更新索引
        if to_player_id not in self.pending_requests:
            self.pending_requests[to_player_id] = set()
        self.pending_requests[to_player_id].add(request_id)
        
        if from_player_id not in self.sent_requests:
            self.sent_requests[from_player_id] = set()
        self.sent_requests[from_player_id].add(request_id)
        
        logger.info(
            f"Friend request sent: {from_player_id} -> {to_player_id} ({request_id})"
        )
        
        # 通知接收者
        self._notify_friend_request(request)
        
        return request
    
    def accept_friend_request(self, request_id: str) -> bool:
        """
        接受好友请求
        
        Args:
            request_id: 请求ID
            
        Returns:
            是否成功
        """
        request = self.requests.get(request_id)
        if not request or not request.accept():
            return False
        
        from_id = request.from_player_id
        to_id = request.to_player_id
        
        # 双向添加好友
        self._add_friend_relation(from_id, to_id, FriendRelation.FRIEND)
        self._add_friend_relation(to_id, from_id, FriendRelation.FRIEND)
        
        # 清理请求索引
        self._cleanup_request(request)
        
        logger.info(f"Friend request accepted: {from_id} <-> {to_id}")
        
        # 通知双方
        self._notify_friend_request_result(request, accepted=True)
        
        return True
    
    def reject_friend_request(self, request_id: str) -> bool:
        """
        拒绝好友请求
        
        Args:
            request_id: 请求ID
            
        Returns:
            是否成功
        """
        request = self.requests.get(request_id)
        if not request or not request.reject():
            return False
        
        # 清理请求索引
        self._cleanup_request(request)
        
        logger.info(
            f"Friend request rejected: {request.from_player_id} -> {request.to_player_id}"
        )
        
        # 通知发送者
        self._notify_friend_request_result(request, accepted=False)
        
        return True
    
    def get_pending_requests(self, player_id: str) -> List[FriendRequest]:
        """
        获取待处理的好友请求
        
        Args:
            player_id: 玩家ID
            
        Returns:
            待处理的请求列表
        """
        request_ids = self.pending_requests.get(player_id, set())
        requests = []
        
        for req_id in request_ids:
            req = self.requests.get(req_id)
            if req and req.is_pending:
                # 检查是否过期
                if req.is_expired:
                    req.expire()
                    self._cleanup_request(req)
                else:
                    requests.append(req)
        
        return requests
    
    def get_sent_requests(self, player_id: str) -> List[FriendRequest]:
        """
        获取已发送的好友请求
        
        Args:
            player_id: 玩家ID
            
        Returns:
            已发送的请求列表
        """
        request_ids = self.sent_requests.get(player_id, set())
        requests = []
        
        for req_id in request_ids:
            req = self.requests.get(req_id)
            if req:
                requests.append(req)
        
        return requests
    
    def cancel_friend_request(self, request_id: str) -> bool:
        """
        取消好友请求
        
        Args:
            request_id: 请求ID
            
        Returns:
            是否成功
        """
        request = self.requests.get(request_id)
        if not request or not request.is_pending:
            return False
        
        # 标记为过期
        request.expire()
        
        # 清理
        self._cleanup_request(request)
        
        logger.info(f"Friend request cancelled: {request_id}")
        
        return True
    
    def _cleanup_request(self, request: FriendRequest) -> None:
        """清理请求索引"""
        request_id = request.request_id
        from_id = request.from_player_id
        to_id = request.to_player_id
        
        # 从索引中移除
        if to_id in self.pending_requests:
            self.pending_requests[to_id].discard(request_id)
        
        if from_id in self.sent_requests:
            self.sent_requests[from_id].discard(request_id)
    
    def _notify_friend_request(self, request: FriendRequest) -> None:
        """通知好友请求"""
        # TODO: 通过WebSocket通知
        pass
    
    def _notify_friend_request_result(
        self,
        request: FriendRequest,
        accepted: bool,
    ) -> None:
        """通知请求结果"""
        # TODO: 通过WebSocket通知
        pass
    
    # ========================================================================
    # 删除好友
    # ========================================================================
    
    def remove_friend(self, player_id: str, friend_id: str) -> bool:
        """
        删除好友
        
        Args:
            player_id: 玩家ID
            friend_id: 好友ID
            
        Returns:
            是否成功
        """
        # 双向删除
        removed1 = self._remove_friend_relation(player_id, friend_id)
        removed2 = self._remove_friend_relation(friend_id, player_id)
        
        if removed1 or removed2:
            logger.info(f"Friend removed: {player_id} <-> {friend_id}")
            return True
        
        return False
    
    # ========================================================================
    # 黑名单管理
    # ========================================================================
    
    def block_player(
        self,
        player_id: str,
        blocked_id: str,
        reason: str = "",
    ) -> bool:
        """
        拉黑玩家
        
        Args:
            player_id: 玩家ID
            blocked_id: 被拉黑的玩家ID
            reason: 拉黑原因
            
        Returns:
            是否成功
        """
        if player_id == blocked_id:
            return False
        
        # 初始化黑名单
        if player_id not in self.blocked_players:
            self.blocked_players[player_id] = set()
        if blocked_id not in self.blocked_by_players:
            self.blocked_by_players[blocked_id] = set()
        
        # 添加到黑名单
        self.blocked_players[player_id].add(blocked_id)
        self.blocked_by_players[blocked_id].add(player_id)
        
        # 如果是好友，自动删除好友关系
        if self.is_friend(player_id, blocked_id):
            self.remove_friend(player_id, blocked_id)
        
        logger.info(f"Player {player_id} blocked {blocked_id}")
        
        return True
    
    def unblock_player(self, player_id: str, blocked_id: str) -> bool:
        """
        取消拉黑
        
        Args:
            player_id: 玩家ID
            blocked_id: 被拉黑的玩家ID
            
        Returns:
            是否成功
        """
        if player_id in self.blocked_players:
            self.blocked_players[player_id].discard(blocked_id)
        
        if blocked_id in self.blocked_by_players:
            self.blocked_by_players[blocked_id].discard(player_id)
        
        logger.info(f"Player {player_id} unblocked {blocked_id}")
        
        return True
    
    def is_blocked(self, player_id: str, by_player_id: str) -> bool:
        """
        检查是否被拉黑
        
        Args:
            player_id: 玩家ID
            by_player_id: 可能拉黑者ID
            
        Returns:
            是否被拉黑
        """
        blocked_set = self.blocked_players.get(by_player_id, set())
        return player_id in blocked_set
    
    def get_blocked_players(self, player_id: str) -> List[str]:
        """
        获取黑名单列表
        
        Args:
            player_id: 玩家ID
            
        Returns:
            被拉黑的玩家ID列表
        """
        return list(self.blocked_players.get(player_id, set()))
    
    # ========================================================================
    # 私聊消息
    # ========================================================================
    
    def _get_chat_key(self, player_id1: str, player_id2: str) -> str:
        """获取聊天键（保证顺序一致）"""
        ids = sorted([player_id1, player_id2])
        return f"{ids[0]}_{ids[1]}"
    
    def send_private_message(
        self,
        from_player_id: str,
        to_player_id: str,
        content: str,
        message_type: str = "text",
    ) -> Optional[PrivateMessage]:
        """
        发送私聊消息
        
        Args:
            from_player_id: 发送者ID
            to_player_id: 接收者ID
            content: 消息内容
            message_type: 消息类型
            
        Returns:
            创建的消息，失败返回None
        """
        # 不能给自己发消息
        if from_player_id == to_player_id:
            return None
        
        # 检查是否被拉黑
        if self.is_blocked(from_player_id, to_player_id):
            logger.warning(f"Player {from_player_id} is blocked by {to_player_id}")
            return None
        
        # 检查是否拉黑了对方
        if self.is_blocked(to_player_id, from_player_id):
            logger.warning(f"Player {from_player_id} has blocked {to_player_id}")
            return None
        
        # 创建消息
        message_id = f"msg_{uuid.uuid4().hex[:12]}"
        message = PrivateMessage(
            message_id=message_id,
            from_player_id=from_player_id,
            to_player_id=to_player_id,
            content=content,
            message_type=message_type,
        )
        
        # 存储消息
        chat_key = self._get_chat_key(from_player_id, to_player_id)
        if chat_key not in self.private_messages:
            self.private_messages[chat_key] = []
        
        self.private_messages[chat_key].append(message)
        
        # 限制消息数量
        if len(self.private_messages[chat_key]) > self._max_messages_per_chat:
            self.private_messages[chat_key] = self.private_messages[chat_key][-self._max_messages_per_chat:]
        
        logger.debug(f"Private message: {from_player_id} -> {to_player_id}")
        
        # 通知接收者
        self._notify_private_message(message)
        
        return message
    
    def get_private_messages(
        self,
        player_id: str,
        friend_id: str,
        limit: int = 50,
        before_id: Optional[str] = None,
    ) -> List[PrivateMessage]:
        """
        获取私聊消息历史
        
        Args:
            player_id: 玩家ID
            friend_id: 好友ID
            limit: 返回数量限制
            before_id: 获取此ID之前的消息
            
        Returns:
            消息列表
        """
        chat_key = self._get_chat_key(player_id, friend_id)
        messages = self.private_messages.get(chat_key, [])
        
        if before_id:
            # 找到before_id的位置
            for i, msg in enumerate(messages):
                if msg.message_id == before_id:
                    messages = messages[:i]
                    break
        
        return messages[-limit:]
    
    def mark_messages_read(self, player_id: str, friend_id: str) -> int:
        """
        标记消息为已读
        
        Args:
            player_id: 玩家ID
            friend_id: 好友ID
            
        Returns:
            标记的消息数量
        """
        chat_key = self._get_chat_key(player_id, friend_id)
        messages = self.private_messages.get(chat_key, [])
        
        count = 0
        for msg in messages:
            if msg.to_player_id == player_id and not msg.is_read:
                msg.mark_read()
                count += 1
        
        return count
    
    def get_unread_count(self, player_id: str) -> int:
        """
        获取未读消息数量
        
        Args:
            player_id: 玩家ID
            
        Returns:
            未读消息总数
        """
        count = 0
        for chat_key, messages in self.private_messages.items():
            if player_id in chat_key:
                for msg in messages:
                    if msg.to_player_id == player_id and not msg.is_read:
                        count += 1
        return count
    
    def _notify_private_message(self, message: PrivateMessage) -> None:
        """通知私聊消息"""
        # TODO: 通过WebSocket通知
        pass
    
    # ========================================================================
    # 组队功能
    # ========================================================================
    
    def create_team(self, leader_id: str, max_members: int = 3) -> TeamInfo:
        """
        创建队伍
        
        Args:
            leader_id: 队长ID
            max_members: 最大成员数
            
        Returns:
            创建的队伍
        """
        # 如果已在队伍中，先离开
        if leader_id in self.player_teams:
            self.leave_team(leader_id)
        
        # 创建队伍
        team_id = f"team_{uuid.uuid4().hex[:12]}"
        team = TeamInfo(
            team_id=team_id,
            leader_id=leader_id,
            max_members=max_members,
        )
        
        self.teams[team_id] = team
        self.player_teams[leader_id] = team_id
        
        logger.info(f"Team created: {team_id} by {leader_id}")
        
        return team
    
    def get_team(self, team_id: str) -> Optional[TeamInfo]:
        """获取队伍信息"""
        return self.teams.get(team_id)
    
    def get_player_team(self, player_id: str) -> Optional[TeamInfo]:
        """获取玩家所在队伍"""
        team_id = self.player_teams.get(player_id)
        if team_id:
            return self.teams.get(team_id)
        return None
    
    def join_team(self, player_id: str, team_id: str) -> bool:
        """
        加入队伍
        
        Args:
            player_id: 玩家ID
            team_id: 队伍ID
            
        Returns:
            是否成功
        """
        team = self.teams.get(team_id)
        if not team:
            return False
        
        # 如果已在队伍中
        if player_id in self.player_teams:
            return False
        
        # 添加到队伍
        if not team.add_member(player_id):
            return False
        
        self.player_teams[player_id] = team_id
        
        logger.info(f"Player {player_id} joined team {team_id}")
        
        # 通知队伍成员
        self._notify_team_update(team)
        
        return True
    
    def leave_team(self, player_id: str) -> bool:
        """
        离开队伍
        
        Args:
            player_id: 玩家ID
            
        Returns:
            是否成功
        """
        team_id = self.player_teams.get(player_id)
        if not team_id:
            return False
        
        team = self.teams.get(team_id)
        if not team:
            self.player_teams.pop(player_id, None)
            return False
        
        # 如果是队长，解散队伍
        if team.is_leader(player_id):
            self._disband_team(team)
            return True
        
        # 普通成员离开
        team.remove_member(player_id)
        self.player_teams.pop(player_id, None)
        
        logger.info(f"Player {player_id} left team {team_id}")
        
        # 通知队伍成员
        self._notify_team_update(team)
        
        return True
    
    def kick_from_team(self, leader_id: str, player_id: str) -> bool:
        """
        踢出队伍成员
        
        Args:
            leader_id: 队长ID
            player_id: 要踢出的玩家ID
            
        Returns:
            是否成功
        """
        team = self.get_player_team(leader_id)
        if not team or not team.is_leader(leader_id):
            return False
        
        if team.is_leader(player_id):
            return False  # 不能踢出队长
        
        team.remove_member(player_id)
        self.player_teams.pop(player_id, None)
        
        logger.info(f"Player {player_id} kicked from team by {leader_id}")
        
        # 通知队伍成员
        self._notify_team_update(team)
        
        return True
    
    def _disband_team(self, team: TeamInfo) -> None:
        """解散队伍"""
        team_id = team.team_id
        
        # 移除所有成员的队伍关联
        for member_id in team.members:
            self.player_teams.pop(member_id, None)
        
        # 删除队伍
        self.teams.pop(team_id, None)
        
        logger.info(f"Team {team_id} disbanded")
    
    def invite_to_team(
        self,
        inviter_id: str,
        invitee_id: str,
    ) -> bool:
        """
        邀请好友加入队伍
        
        Args:
            inviter_id: 邀请者ID
            invitee_id: 被邀请者ID
            
        Returns:
            是否成功发送邀请
        """
        team = self.get_player_team(inviter_id)
        if not team:
            return False
        
        # 检查是否为好友
        if not self.is_friend(inviter_id, invitee_id):
            return False
        
        # 检查队伍是否已满
        if team.is_full:
            return False
        
        # 检查被邀请者是否已在队伍中
        if invitee_id in self.player_teams:
            return False
        
        # TODO: 发送邀请通知
        
        logger.info(f"Team invite: {inviter_id} -> {invitee_id} for team {team.team_id}")
        
        return True
    
    def _notify_team_update(self, team: TeamInfo) -> None:
        """通知队伍更新"""
        # TODO: 通过WebSocket通知
        pass
    
    # ========================================================================
    # 搜索好友
    # ========================================================================
    
    def search_players(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        搜索玩家（用于添加好友）
        
        Args:
            query: 搜索关键词
            limit: 返回数量限制
            
        Returns:
            玩家信息列表
        """
        results = []
        query_lower = query.lower()
        
        for player_id, info in self._player_cache.items():
            nickname = info.get("nickname", "")
            if query_lower in player_id.lower() or query_lower in nickname.lower():
                results.append({
                    "player_id": player_id,
                    "nickname": nickname,
                    "avatar": info.get("avatar", ""),
                    "tier": info.get("tier", "bronze"),
                    "stars": info.get("stars", 0),
                })
                
                if len(results) >= limit:
                    break
        
        return results
    
    # ========================================================================
    # 数据持久化（占位）
    # ========================================================================
    
    def load_from_db(self) -> None:
        """从数据库加载数据"""
        # TODO: 实现数据库加载
        pass
    
    def save_to_db(self) -> None:
        """保存数据到数据库"""
        # TODO: 实现数据库保存
        pass


# 全局单例
_friendship_manager: Optional[FriendshipManager] = None


def get_friendship_manager() -> FriendshipManager:
    """获取好友管理器单例"""
    global _friendship_manager
    if _friendship_manager is None:
        _friendship_manager = FriendshipManager()
    return _friendship_manager
