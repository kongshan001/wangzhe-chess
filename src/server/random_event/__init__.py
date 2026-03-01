"""
王者之奕 - 随机事件系统

本模块实现对局中的随机事件系统：
- 随机触发特殊事件
- 事件效果执行
- 事件历史记录

事件类型：
- 金币雨：所有玩家获得额外金币
- 英雄折扣：商店某费用英雄打折
- 装备掉落：野怪掉落额外装备
- 羁绊祝福：某羁绊效果翻倍
- 幸运轮盘：随机获得奖励
"""

from .manager import (
    RandomEventManager,
    create_random_event_manager,
    get_random_event_manager,
)
from .models import (
    EventEffect,
    EventEffectType,
    EventHistoryEntry,
    EventRarity,
    EventTrigger,
    EventType,
    RandomEvent,
)

__all__ = [
    # 模型
    "RandomEvent",
    "EventEffect",
    "EventEffectType",
    "EventType",
    "EventRarity",
    "EventTrigger",
    "EventHistoryEntry",
    # 管理器
    "RandomEventManager",
    "create_random_event_manager",
    "get_random_event_manager",
]
