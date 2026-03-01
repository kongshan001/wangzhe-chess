"""
王者之奕 - 新手引导模块

本模块提供新手引导系统功能：
- 引导步骤配置
- 引导进度管理
- 引导奖励发放
"""

from .manager import (
    TutorialManager,
    get_tutorial_manager,
)
from .models import (
    PlayerTutorialProgress,
    Tutorial,
    TutorialHighlight,
    TutorialReward,
    TutorialStep,
    TutorialStepAction,
    TutorialType,
)

__all__ = [
    # 数据类
    "TutorialType",
    "TutorialStep",
    "TutorialStepAction",
    "TutorialReward",
    "Tutorial",
    "PlayerTutorialProgress",
    "TutorialHighlight",
    # 管理器
    "TutorialManager",
    "get_tutorial_manager",
]
