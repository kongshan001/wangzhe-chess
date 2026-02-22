"""
王者之奕 - 装备合成系统

本模块提供装备合成功能：
- 合成配方管理
- 材料消耗
- 金币扣除
- 合成历史记录

使用示例:
    from server.game.crafting import CraftingManager, PlayerInventory
    
    # 创建管理器
    manager = CraftingManager()
    
    # 创建玩家背包
    inventory = PlayerInventory()
    inventory.add_equipment("eq_001", 2)  # 添加2个铁剑
    inventory.gold = 100
    
    # 查找可合成的配方
    craftable = manager.get_craftable_recipes(inventory)
    
    # 执行合成
    result = manager.craft(craftable[0], inventory)
"""

from .manager import (
    CraftingManager,
    PlayerInventory,
    create_crafting_manager,
)
from .models import (
    CraftingHistoryEntry,
    CraftingMaterial,
    CraftingRecipe,
    CraftingResult,
    Rarity,
    SpecialEffect,
    SpecialEffectType,
)

__all__ = [
    # 管理器
    "CraftingManager",
    "PlayerInventory",
    "create_crafting_manager",
    # 数据模型
    "CraftingRecipe",
    "CraftingMaterial",
    "CraftingResult",
    "CraftingHistoryEntry",
    "Rarity",
    "SpecialEffect",
    "SpecialEffectType",
]
