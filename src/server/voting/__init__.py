"""
王者之奕 - 投票系统

本模块提供投票系统功能：
- 玩家投票决定游戏内容
- VIP额外票数
- 投票奖励发放
- 结果公示
"""

from .manager import (
    VotingManager,
    get_voting_manager,
)
from .models import (
    DEFAULT_PARTICIPATION_REWARDS,
    DEFAULT_WIN_BONUS_REWARDS,
    VIP_VOTE_WEIGHTS,
    PlayerVote,
    RewardType,
    VotingInfo,
    VotingOption,
    VotingPoll,
    VotingResult,
    VotingReward,
    VotingStatus,
    VotingType,
)

__all__ = [
    # 数据模型
    "PlayerVote",
    "RewardType",
    "VotingInfo",
    "VotingOption",
    "VotingPoll",
    "VotingResult",
    "VotingReward",
    "VotingStatus",
    "VotingType",
    # 常量
    "DEFAULT_PARTICIPATION_REWARDS",
    "DEFAULT_WIN_BONUS_REWARDS",
    "VIP_VOTE_WEIGHTS",
    # 管理器
    "VotingManager",
    "get_voting_manager",
]
