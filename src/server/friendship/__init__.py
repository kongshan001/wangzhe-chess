"""
王者之奕 - 好友系统模块

本模块提供完整的社交功能：
- 好友管理（添加、删除、搜索）
- 好友请求处理
- 黑名单管理
- 私聊系统
- 组队功能
- 在线状态管理

使用方式:
    from src.server.friendship import get_friendship_manager
    
    manager = get_friendship_manager()
    
    # 发送好友请求
    manager.send_friend_request(player_id, friend_id, "Hi!")
    
    # 接受好友请求
    manager.accept_friend_request(request_id)
    
    # 发送私聊消息
    manager.send_private_message(from_id, to_id, "Hello!")
    
    # 创建队伍
    team = manager.create_team(leader_id)
"""

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
from .manager import (
    FriendshipManager,
    get_friendship_manager,
)

__all__ = [
    # 数据模型
    "BlockedPlayer",
    "FriendInfo",
    "FriendRelation",
    "FriendRequest",
    "FriendRequestData",
    "FriendRequestStatus",
    "FriendStatus",
    "PrivateMessage",
    "PrivateMessageData",
    "TeamInfo",
    # 管理器
    "FriendshipManager",
    "get_friendship_manager",
]
