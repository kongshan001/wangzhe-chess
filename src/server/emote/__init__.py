"""
王者之奕 - 表情系统模块

本模块提供游戏中表情发送和管理功能：
- 表情分类和列表
- 表情发送/接收
- 表情解锁
- 快捷键设置
- 表情历史记录
"""

from .models import (
    EmoteCategory,
    Emote,
    PlayerEmote,
    EmoteHistory,
    EmoteData,
)
from .manager import (
    EmoteManager,
    get_emote_manager,
)

__all__ = [
    # 数据模型
    "EmoteCategory",
    "Emote",
    "PlayerEmote",
    "EmoteHistory",
    "EmoteData",
    
    # 管理器
    "EmoteManager",
    "get_emote_manager",
]
