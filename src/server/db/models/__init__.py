"""
王者之奕 - 数据库模型模块

本模块包含所有数据库模型：
- friend: 好友相关模型
- leaderboard: 排行榜相关模型
- checkin: 签到相关模型
- synergypedia: 羁绊图鉴模型
- daily_task: 每日任务相关模型
- custom_room: 自定义房间相关模型
- emote: 表情系统相关模型
- consumable: 道具相关模型
"""

from .ai_coach import (
    AICoachDB,
    CoachAnalysisDB,
    LineupRecommendationDB,
    PlayerLearningDB,
)
from .checkin import (
    CheckinDB,
    CheckinStreakDB,
)
from .consumable import (
    ConsumableDB,
    ConsumableEffectDB,
    ConsumablePurchaseLogDB,
    ConsumableUsageDB,
)
from .custom_room import (
    CustomRoomDB,
    CustomRoomPlayerDB,
    CustomRoomStatsDB,
)
from .daily_task import (
    DailyTaskDB,
    PlayerDailyStatsDB,
    TaskProgressDB,
)
from .emote import (
    EmoteDB,
    EmoteHistoryDB,
    EmoteHotkeyDB,
    PlayerEmoteDB,
)
from .friend import (
    BlockedPlayerDB,
    FriendDB,
    FriendRequestDB,
    PrivateMessageDB,
    TeamDB,
)
from .leaderboard import (
    LeaderboardDB,
    LeaderboardHistoryDB,
    LeaderboardRewardDB,
    PlayerLeaderboardStatsDB,
)
from .replay import (
    ReplayDB,
)
from .skin import (
    EquippedSkinDB,
    SkinDB,
    SkinPurchaseLogDB,
)
from .spectator import (
    SpectatorChatDB,
    SpectatorDB,
    SpectatorStatsDB,
)
from .synergypedia import (
    SynergyAchievementDB,
    SynergypediaDB,
)
from .trading import (
    TradeDB,
    TradeHistoryDB,
    TradeItemDB,
)

__all__ = [
    # 好友模型
    "FriendDB",
    "FriendRequestDB",
    "BlockedPlayerDB",
    "PrivateMessageDB",
    "TeamDB",
    # 排行榜模型
    "LeaderboardDB",
    "LeaderboardRewardDB",
    "PlayerLeaderboardStatsDB",
    "LeaderboardHistoryDB",
    # 签到模型
    "CheckinDB",
    "CheckinStreakDB",
    # 羁绊图鉴模型
    "SynergypediaDB",
    "SynergyAchievementDB",
    # 每日任务模型
    "DailyTaskDB",
    "TaskProgressDB",
    "PlayerDailyStatsDB",
    # 自定义房间模型
    "CustomRoomDB",
    "CustomRoomPlayerDB",
    "CustomRoomStatsDB",
    # 观战模型
    "SpectatorDB",
    "SpectatorChatDB",
    "SpectatorStatsDB",
    # 皮肤模型
    "SkinDB",
    "EquippedSkinDB",
    "SkinPurchaseLogDB",
    # 回放模型
    "ReplayDB",
    # 表情模型
    "EmoteDB",
    "PlayerEmoteDB",
    "EmoteHistoryDB",
    "EmoteHotkeyDB",
    # 道具模型
    "ConsumableDB",
    "ConsumableEffectDB",
    "ConsumableUsageDB",
    "ConsumablePurchaseLogDB",
    # 交易模型
    "TradeDB",
    "TradeItemDB",
    "TradeHistoryDB",
    # AI教练模型
    "AICoachDB",
    "CoachAnalysisDB",
    "PlayerLearningDB",
    "LineupRecommendationDB",
]
