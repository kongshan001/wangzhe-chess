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

from .friend import (
    FriendDB,
    FriendRequestDB,
    BlockedPlayerDB,
    PrivateMessageDB,
    TeamDB,
)

from .leaderboard import (
    LeaderboardDB,
    LeaderboardRewardDB,
    PlayerLeaderboardStatsDB,
    LeaderboardHistoryDB,
)

from .checkin import (
    CheckinDB,
    CheckinStreakDB,
)

from .synergypedia import (
    SynergypediaDB,
    SynergyAchievementDB,
)

from .daily_task import (
    DailyTaskDB,
    TaskProgressDB,
    PlayerDailyStatsDB,
)

from .custom_room import (
    CustomRoomDB,
    CustomRoomPlayerDB,
    CustomRoomStatsDB,
)

from .spectator import (
    SpectatorDB,
    SpectatorChatDB,
    SpectatorStatsDB,
)

from .skin import (
    SkinDB,
    EquippedSkinDB,
    SkinPurchaseLogDB,
)

from .emote import (
    EmoteDB,
    PlayerEmoteDB,
    EmoteHistoryDB,
    EmoteHotkeyDB,
)

from .replay import (
    ReplayDB,
)

from .consumable import (
    ConsumableDB,
    ConsumableEffectDB,
    ConsumableUsageDB,
    ConsumablePurchaseLogDB,
)

from .trading import (
    TradeDB,
    TradeItemDB,
    TradeHistoryDB,
)

from .ai_coach import (
    AICoachDB,
    CoachAnalysisDB,
    PlayerLearningDB,
    LineupRecommendationDB,
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
