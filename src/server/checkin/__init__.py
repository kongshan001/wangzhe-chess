"""
王者之奕 - 签到系统模块

本模块提供签到系统的核心功能：
- 签到数据模型
- 签到管理器
- 奖励配置加载
"""

from .manager import CheckinManager, get_checkin_manager
from .models import (
    CheckinInfo,
    CheckinRecord,
    CheckinReward,
    CheckinStreak,
    DailyRewardConfig,
    RewardType,
)

__all__ = [
    # 数据模型
    "CheckinRecord",
    "CheckinReward",
    "CheckinStreak",
    "DailyRewardConfig",
    "CheckinInfo",
    "RewardType",
    # 管理器
    "CheckinManager",
    "get_checkin_manager",
]
