"""
王者之奕 - 成就系统数据模型

本模块定义成就系统的核心数据类：
- Achievement: 成就信息
- AchievementRequirement: 成就需求条件
- AchievementReward: 成就奖励
- PlayerAchievement: 玩家成就进度

用于存储和管理成就相关的数据。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class AchievementCategory(Enum):
    """成就类别枚举"""

    COLLECTION = "collection"  # 收集成就
    BATTLE = "battle"  # 对局成就
    COMBAT = "combat"  # 战斗成就
    SOCIAL = "social"  # 社交成就
    SPECIAL = "special"  # 特殊成就


class AchievementTier(Enum):
    """成就等级枚举"""

    BRONZE = 1  # 铜牌成就
    SILVER = 2  # 银牌成就
    GOLD = 3  # 金牌成就
    DIAMOND = 4  # 钻石成就

    @property
    def display_name(self) -> str:
        """获取显示名称"""
        names = {
            AchievementTier.BRONZE: "铜牌",
            AchievementTier.SILVER: "银牌",
            AchievementTier.GOLD: "金牌",
            AchievementTier.DIAMOND: "钻石",
        }
        return names[self]


class RequirementType(Enum):
    """成就需求类型枚举"""

    # 收集类
    COLLECT_HEROES = "collect_heroes"  # 收集英雄
    COLLECT_1STAR_HEROES = "collect_1star_heroes"  # 收集1星英雄
    COLLECT_2STAR_HEROES = "collect_2star_heroes"  # 收集2星英雄
    COLLECT_3STAR_HEROES = "collect_3star_heroes"  # 收集3星英雄
    ACTIVATE_SYNERGIES = "activate_synergies"  # 激活羁绊
    COLLECT_SKINS = "collect_skins"  # 收集皮肤

    # 对局类
    WIN_GAMES = "win_games"  # 获胜场数
    PLAY_GAMES = "play_games"  # 游戏场数
    WIN_STREAK = "win_streak"  # 连胜次数
    LOSE_STREAK = "lose_streak"  # 连败次数
    FIRST_PLACE = "first_place"  # 第一名次数
    TOP4_FINISH = "top4_finish"  # 前四次数

    # 战斗类
    DEAL_DAMAGE = "deal_damage"  # 造成伤害
    TAKE_DAMAGE = "take_damage"  # 承受伤害
    KILL_HEROES = "kill_heroes"  # 击杀英雄
    PERFECT_WIN = "perfect_win"  # 完美胜利(零损失)
    LOW_HP_WIN = "low_hp_win"  # 低血量获胜
    FAST_WIN = "fast_win"  # 快速获胜

    # 社交类
    ADD_FRIENDS = "add_friends"  # 添加好友
    TEAM_PLAY = "team_play"  # 组队游戏
    SHARE_RESULT = "share_result"  # 分享结果

    # 特殊类
    REACH_TIER = "reach_tier"  # 达到段位
    EARN_GOLD = "earn_gold"  # 获得金币
    REFRESH_SHOP = "refresh_shop"  # 刷新商店
    BUY_HEROES = "buy_heroes"  # 购买英雄
    UPGRADE_HEROES = "upgrade_heroes"  # 升级英雄


@dataclass
class AchievementRequirement:
    """
    成就需求条件

    定义完成成就所需满足的条件。

    Attributes:
        type: 需求类型
        target: 目标数值
        conditions: 附加条件 (如特定英雄、羁绊等)
    """

    type: RequirementType
    target: int
    conditions: dict[str, Any] = field(default_factory=dict)

    def check_progress(self, current_value: int, **kwargs) -> int:
        """
        检查进度

        Args:
            current_value: 当前值
            **kwargs: 附加参数用于条件检查

        Returns:
            当前进度（可用于显示进度条）
        """
        # 检查附加条件
        if self.conditions:
            for key, required_value in self.conditions.items():
                actual_value = kwargs.get(key)
                if actual_value != required_value:
                    return 0

        return min(current_value, self.target)

    def is_completed(self, current_value: int, **kwargs) -> bool:
        """
        检查是否完成

        Args:
            current_value: 当前值
            **kwargs: 附加参数

        Returns:
            是否完成
        """
        return self.check_progress(current_value, **kwargs) >= self.target

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "type": self.type.value,
            "target": self.target,
            "conditions": self.conditions,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AchievementRequirement:
        """从字典创建"""
        req_type = data.get("type", "play_games")
        if isinstance(req_type, str):
            req_type = RequirementType(req_type)

        return cls(
            type=req_type,
            target=data.get("target", 1),
            conditions=data.get("conditions", {}),
        )


@dataclass
class AchievementReward:
    """
    成就奖励

    定义完成成就后获得的奖励。

    Attributes:
        gold: 金币奖励
        exp: 经验值奖励
        avatar_frame: 头像框ID（可选）
        title: 称号ID（可选）
        skin: 皮肤ID（可选）
        items: 其他物品奖励列表
    """

    gold: int = 0
    exp: int = 0
    avatar_frame: str | None = None
    title: str | None = None
    skin: str | None = None
    items: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "gold": self.gold,
            "exp": self.exp,
            "avatar_frame": self.avatar_frame,
            "title": self.title,
            "skin": self.skin,
            "items": self.items,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AchievementReward:
        """从字典创建"""
        return cls(
            gold=data.get("gold", 0),
            exp=data.get("exp", 0),
            avatar_frame=data.get("avatar_frame"),
            title=data.get("title"),
            skin=data.get("skin"),
            items=data.get("items", []),
        )


@dataclass
class Achievement:
    """
    成就信息

    定义一个成就的完整信息。

    Attributes:
        achievement_id: 成就唯一ID
        name: 成就名称
        description: 成就描述
        category: 成就类别
        tier: 成就等级(铜/银/金/钻石)
        requirement: 完成需求
        rewards: 完成奖励
        icon: 图标ID
        hidden: 是否为隐藏成就
        prerequisite: 前置成就ID（可选）
    """

    achievement_id: str
    name: str
    description: str
    category: AchievementCategory
    tier: AchievementTier
    requirement: AchievementRequirement
    rewards: AchievementReward
    icon: str = ""
    hidden: bool = False
    prerequisite: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "achievement_id": self.achievement_id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "category_name": self.category.name,
            "tier": self.tier.value,
            "tier_name": self.tier.display_name,
            "requirement": self.requirement.to_dict(),
            "rewards": self.rewards.to_dict(),
            "icon": self.icon,
            "hidden": self.hidden,
            "prerequisite": self.prerequisite,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Achievement:
        """从字典创建"""
        category = data.get("category", "special")
        if isinstance(category, str):
            category = AchievementCategory(category)

        tier = data.get("tier", 1)
        if isinstance(tier, int):
            tier = AchievementTier(tier)
        elif isinstance(tier, str):
            tier_map = {"bronze": 1, "silver": 2, "gold": 3, "diamond": 4}
            tier = AchievementTier(tier_map.get(tier, 1))

        requirement_data = data.get("requirement", {})
        if isinstance(requirement_data, dict):
            requirement = AchievementRequirement.from_dict(requirement_data)
        else:
            requirement = requirement_data

        rewards_data = data.get("rewards", {})
        if isinstance(rewards_data, dict):
            rewards = AchievementReward.from_dict(rewards_data)
        else:
            rewards = rewards_data

        return cls(
            achievement_id=data["achievement_id"],
            name=data["name"],
            description=data["description"],
            category=category,
            tier=tier,
            requirement=requirement,
            rewards=rewards,
            icon=data.get("icon", ""),
            hidden=data.get("hidden", False),
            prerequisite=data.get("prerequisite"),
        )


@dataclass
class PlayerAchievement:
    """
    玩家成就进度

    记录玩家在某个成就上的进度。

    Attributes:
        player_id: 玩家ID
        achievement_id: 成就ID
        progress: 当前进度值
        completed: 是否已完成
        completed_at: 完成时间（可选）
        claimed: 是否已领取奖励
        claimed_at: 领取时间（可选）
    """

    player_id: str
    achievement_id: str
    progress: int = 0
    completed: bool = False
    completed_at: datetime | None = None
    claimed: bool = False
    claimed_at: datetime | None = None

    def update_progress(self, value: int, target: int) -> bool:
        """
        更新进度

        Args:
            value: 新的进度值
            target: 目标值

        Returns:
            是否刚完成
        """
        self.progress = value

        if not self.completed and self.progress >= target:
            self.completed = True
            self.completed_at = datetime.now()
            return True

        return False

    def claim_reward(self) -> bool:
        """
        领取奖励

        Returns:
            是否成功领取
        """
        if not self.completed or self.claimed:
            return False

        self.claimed = True
        self.claimed_at = datetime.now()
        return True

    @property
    def is_claimable(self) -> bool:
        """是否可领取奖励"""
        return self.completed and not self.claimed

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "player_id": self.player_id,
            "achievement_id": self.achievement_id,
            "progress": self.progress,
            "completed": self.completed,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "claimed": self.claimed,
            "claimed_at": self.claimed_at.isoformat() if self.claimed_at else None,
            "is_claimable": self.is_claimable,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PlayerAchievement:
        """从字典创建"""
        completed_at = data.get("completed_at")
        if completed_at and isinstance(completed_at, str):
            completed_at = datetime.fromisoformat(completed_at)

        claimed_at = data.get("claimed_at")
        if claimed_at and isinstance(claimed_at, str):
            claimed_at = datetime.fromisoformat(claimed_at)

        return cls(
            player_id=data["player_id"],
            achievement_id=data["achievement_id"],
            progress=data.get("progress", 0),
            completed=data.get("completed", False),
            completed_at=completed_at,
            claimed=data.get("claimed", False),
            claimed_at=claimed_at,
        )
