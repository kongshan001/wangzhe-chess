"""
王者之奕 - 阵容预设模块

本模块提供阵容预设系统的核心功能：
- 数据模型（LineupPreset, LineupSlot）
- 管理器（LineupManager）
- 预设操作（保存、加载、删除、重命名）
"""

from .models import (
    EquipmentAssignment,
    LineupPreset,
    LineupSlot,
    TargetSynergy,
    MAX_EQUIPMENT_PER_HERO,
    MAX_HEROES_PER_PRESET,
    MAX_PRESETS_PER_PLAYER,
)
from .manager import (
    LineupManager,
    create_lineup_manager,
)

__all__ = [
    # 数据模型
    "EquipmentAssignment",
    "LineupPreset",
    "LineupSlot",
    "TargetSynergy",
    
    # 管理器
    "LineupManager",
    "create_lineup_manager",
    
    # 常量
    "MAX_EQUIPMENT_PER_HERO",
    "MAX_HEROES_PER_PRESET",
    "MAX_PRESETS_PER_PLAYER",
]
