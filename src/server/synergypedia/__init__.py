"""
王者之奕 - 羁绊图鉴模块

本模块实现羁绊图鉴系统（需求 #17），包括：
- 羁绊信息展示
- 羁绊进度追踪
- 阵容推荐
- 羁绊模拟器
- 成就系统

模块结构:
- models.py: 数据类定义
- manager.py: 羁绊图鉴管理器
"""

from .manager import SynergypediaManager, synergypedia_manager
from .models import (
    RecommendedLineup,
    SynergyAchievement,
    SynergypediaEntry,
    SynergypediaProgress,
    SynergySimulation,
)

__all__ = [
    "SynergypediaEntry",
    "SynergypediaProgress",
    "RecommendedLineup",
    "SynergySimulation",
    "SynergyAchievement",
    "SynergypediaManager",
    "synergypedia_manager",
]
