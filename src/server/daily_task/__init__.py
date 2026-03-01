"""
王者之奕 - 每日任务系统

本模块提供每日任务系统功能：
- 每日任务刷新
- 任务进度追踪
- 任务奖励领取
- 金币刷新任务
"""

from .manager import DailyTaskManager, get_daily_task_manager
from .models import (
    DailyTask,
    TaskDifficulty,
    TaskProgress,
    TaskRequirement,
    TaskReward,
    TaskType,
)

__all__ = [
    "DailyTask",
    "TaskProgress",
    "TaskRequirement",
    "TaskReward",
    "TaskType",
    "TaskDifficulty",
    "DailyTaskManager",
    "get_daily_task_manager",
]
