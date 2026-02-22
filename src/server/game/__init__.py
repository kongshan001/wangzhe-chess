"""
王者之奕 - 游戏核心模块

本模块包含游戏的核心子系统：
- hero_pool: 英雄池管理
- synergy: 羁绊系统
- economy: 经济系统
- battle: 战斗模拟
- crafting: 装备合成系统
"""

from .economy import (
    EconomyManager,
    EconomyState,
    IncomeBreakdown,
    LevelUpResult,
    create_economy_manager,
    get_income_table,
    get_level_table,
    get_streak_bonus_table,
)
from .hero_pool import (
    HeroConfigLoader,
    HeroFactory,
    SharedHeroPool,
    ShopManager,
    create_default_hero_pool,
)
from .synergy import (
    SynergyManager,
    create_synergy_manager,
    get_all_synergy_names,
)
from .crafting import (
    CraftingManager,
    CraftingRecipe,
    CraftingMaterial,
    CraftingResult,
    CraftingHistoryEntry,
    PlayerInventory,
    Rarity,
    SpecialEffect,
    SpecialEffectType,
    create_crafting_manager,
)

# 导出常用类
__all__ = [
    # 英雄池
    "HeroConfigLoader",
    "HeroFactory",
    "SharedHeroPool",
    "ShopManager",
    "create_default_hero_pool",
    # 羁绊系统
    "SynergyManager",
    "create_synergy_manager",
    "get_all_synergy_names",
    # 经济系统
    "EconomyManager",
    "EconomyState",
    "IncomeBreakdown",
    "LevelUpResult",
    "create_economy_manager",
    "get_level_table",
    "get_income_table",
    "get_streak_bonus_table",
    # 装备合成系统
    "CraftingManager",
    "CraftingRecipe",
    "CraftingMaterial",
    "CraftingResult",
    "CraftingHistoryEntry",
    "PlayerInventory",
    "Rarity",
    "SpecialEffect",
    "SpecialEffectType",
    "create_crafting_manager",
]
