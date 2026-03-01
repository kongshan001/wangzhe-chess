"""
王者之奕 - 排行榜模块

本模块提供排行榜系统的核心功能：
- 多维度排行榜（段位/胜率/吃鸡/伤害/财富）
- 周/月/赛季榜
- 排行榜奖励
- 实时更新

使用方式:
    from src.server.leaderboard import (
        LeaderboardManager,
        LeaderboardType,
        LeaderboardPeriod,
        get_leaderboard_manager,
    )

    manager = get_leaderboard_manager()
    leaderboard = manager.get_leaderboard(
        LeaderboardType.TIER,
        LeaderboardPeriod.WEEKLY,
        page=1,
        page_size=50,
    )
"""

from .manager import (
    LeaderboardManager,
    get_leaderboard_manager,
)
from .models import (
    LeaderboardData,
    LeaderboardEntry,
    LeaderboardPeriod,
    LeaderboardReward,
    LeaderboardType,
    PlayerRankInfo,
)

__all__ = [
    # 数据模型
    "LeaderboardType",
    "LeaderboardPeriod",
    "LeaderboardEntry",
    "LeaderboardReward",
    "PlayerRankInfo",
    "LeaderboardData",
    # 管理器
    "LeaderboardManager",
    "get_leaderboard_manager",
]
