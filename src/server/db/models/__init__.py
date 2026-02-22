"""
王者之奕 - 数据库模型模块

本模块包含所有数据库模型：
- friend: 好友相关模型
"""

from .friend import (
    FriendDB,
    FriendRequestDB,
    BlockedPlayerDB,
    PrivateMessageDB,
    TeamDB,
)

__all__ = [
    "FriendDB",
    "FriendRequestDB",
    "BlockedPlayerDB",
    "PrivateMessageDB",
    "TeamDB",
]
