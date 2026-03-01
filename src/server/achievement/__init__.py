"""
王者之奕 - 成就系统

本模块提供成就系统功能：
- Achievement: 成就数据类
- AchievementRequirement: 成就需求
- AchievementReward: 成就奖励
- PlayerAchievement: 玩家成就数据
- AchievementManager: 成就管理器
"""

from .manager import AchievementManager
from .models import (
    Achievement,
    AchievementCategory,
    AchievementRequirement,
    AchievementReward,
    AchievementTier,
    PlayerAchievement,
)

__all__ = [
    "Achievement",
    "AchievementRequirement",
    "AchievementReward",
    "PlayerAchievement",
    "AchievementCategory",
    "AchievementTier",
    "AchievementManager",
]
