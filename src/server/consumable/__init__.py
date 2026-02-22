"""
王者之奕 - 道具系统模块

本模块提供道具系统的核心功能：
- 道具数据模型
- 道具管理器
- 道具效果计算
"""

from .models import (
    ActiveConsumableEffect,
    ConsumableEffect,
    ConsumableEffectConfig,
    ConsumableItem,
    ConsumablePrice,
    ConsumableRarity,
    ConsumableType,
    ConsumableUsage,
    PlayerConsumable,
)

from .manager import (
    ConsumableManager,
    get_consumable_manager,
)

__all__ = [
    # 数据模型
    "ConsumableType",
    "ConsumableEffect",
    "ConsumableRarity",
    "ConsumablePrice",
    "ConsumableEffectConfig",
    "ConsumableItem",
    "PlayerConsumable",
    "ConsumableUsage",
    "ActiveConsumableEffect",
    # 管理器
    "ConsumableManager",
    "get_consumable_manager",
]
