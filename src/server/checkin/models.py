"""
王者之奕 - 签到系统数据模型

本模块定义签到系统的数据类：
- CheckinReward: 签到奖励数据类
- CheckinRecord: 签到记录数据类
- CheckinStreak: 连续签到数据类
- RewardType: 奖励类型枚举

用于签到系统的数据处理和传输。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any


class RewardType(str, Enum):
    """奖励类型枚举"""

    GOLD = "gold"  # 金币
    DIAMOND = "diamond"  # 钻石
    HERO_FRAGMENT = "hero_fragment"  # 英雄碎片
    EQUIPMENT = "equipment"  # 装备
    ITEM = "item"  # 道具
    SKIN = "skin"  # 皮肤
    EXP = "exp"  # 经验
    TITLE = "title"  # 称号


@dataclass
class CheckinReward:
    """
    签到奖励数据类

    存储单个签到奖励的信息。

    Attributes:
        reward_id: 奖励唯一ID
        reward_type: 奖励类型
        item_id: 物品ID（如英雄ID、皮肤ID等）
        quantity: 数量
        extra_data: 额外数据
    """

    reward_id: str
    reward_type: RewardType
    item_id: str | None = None
    quantity: int = 1
    extra_data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "reward_id": self.reward_id,
            "reward_type": self.reward_type.value
            if isinstance(self.reward_type, RewardType)
            else self.reward_type,
            "item_id": self.item_id,
            "quantity": self.quantity,
            "extra_data": self.extra_data,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CheckinReward:
        """从字典创建"""
        return cls(
            reward_id=data["reward_id"],
            reward_type=RewardType(data["reward_type"]),
            item_id=data.get("item_id"),
            quantity=data.get("quantity", 1),
            extra_data=data.get("extra_data", {}),
        )


@dataclass
class CheckinRecord:
    """
    签到记录数据类

    存储单次签到记录的信息。

    Attributes:
        record_id: 记录唯一ID
        player_id: 玩家ID
        checkin_date: 签到日期
        checkin_time: 签到时间
        day_in_cycle: 周期内的第几天（1-7）
        streak_days: 连续签到天数
        rewards: 获得的奖励列表
        is_supplement: 是否补签
        supplement_cost: 补签消耗钻石
    """

    record_id: str
    player_id: str
    checkin_date: date
    checkin_time: datetime
    day_in_cycle: int = 1
    streak_days: int = 1
    rewards: list[CheckinReward] = field(default_factory=list)
    is_supplement: bool = False
    supplement_cost: int = 0

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "record_id": self.record_id,
            "player_id": self.player_id,
            "checkin_date": self.checkin_date.isoformat(),
            "checkin_time": self.checkin_time.isoformat(),
            "day_in_cycle": self.day_in_cycle,
            "streak_days": self.streak_days,
            "rewards": [r.to_dict() for r in self.rewards],
            "is_supplement": self.is_supplement,
            "supplement_cost": self.supplement_cost,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CheckinRecord:
        """从字典创建"""
        return cls(
            record_id=data["record_id"],
            player_id=data["player_id"],
            checkin_date=date.fromisoformat(data["checkin_date"]),
            checkin_time=datetime.fromisoformat(data["checkin_time"]),
            day_in_cycle=data.get("day_in_cycle", 1),
            streak_days=data.get("streak_days", 1),
            rewards=[CheckinReward.from_dict(r) for r in data.get("rewards", [])],
            is_supplement=data.get("is_supplement", False),
            supplement_cost=data.get("supplement_cost", 0),
        )


@dataclass
class CheckinStreak:
    """
    连续签到数据类

    存储玩家的连续签到信息。

    Attributes:
        player_id: 玩家ID
        current_streak: 当前连续签到天数
        max_streak: 历史最大连续签到天数
        last_checkin_date: 最后签到日期
        monthly_count: 本月签到天数
        total_count: 总签到天数
        cycle_start_date: 当前周期开始日期
    """

    player_id: str
    current_streak: int = 0
    max_streak: int = 0
    last_checkin_date: date | None = None
    monthly_count: int = 0
    total_count: int = 0
    cycle_start_date: date | None = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "player_id": self.player_id,
            "current_streak": self.current_streak,
            "max_streak": self.max_streak,
            "last_checkin_date": self.last_checkin_date.isoformat()
            if self.last_checkin_date
            else None,
            "monthly_count": self.monthly_count,
            "total_count": self.total_count,
            "cycle_start_date": self.cycle_start_date.isoformat()
            if self.cycle_start_date
            else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CheckinStreak:
        """从字典创建"""
        return cls(
            player_id=data["player_id"],
            current_streak=data.get("current_streak", 0),
            max_streak=data.get("max_streak", 0),
            last_checkin_date=date.fromisoformat(data["last_checkin_date"])
            if data.get("last_checkin_date")
            else None,
            monthly_count=data.get("monthly_count", 0),
            total_count=data.get("total_count", 0),
            cycle_start_date=date.fromisoformat(data["cycle_start_date"])
            if data.get("cycle_start_date")
            else None,
        )

    def update_streak(self, checkin_date: date) -> bool:
        """
        更新连续签到天数

        Args:
            checkin_date: 签到日期

        Returns:
            是否为连续签到
        """
        is_continuous = False

        if self.last_checkin_date is None:
            # 首次签到
            self.current_streak = 1
            self.cycle_start_date = checkin_date
        elif checkin_date == self.last_checkin_date:
            # 同一天，不更新
            return False
        elif checkin_date == self._get_next_day(self.last_checkin_date):
            # 连续签到
            self.current_streak += 1
            is_continuous = True
        else:
            # 中断，重新开始
            self.current_streak = 1
            self.cycle_start_date = checkin_date

        self.last_checkin_date = checkin_date
        self.total_count += 1

        # 更新月签到数
        if checkin_date.month != (self.last_checkin_date.month if self.last_checkin_date else 0):
            self.monthly_count = 1
        else:
            self.monthly_count += 1

        # 更新最大连续签到
        if self.current_streak > self.max_streak:
            self.max_streak = self.current_streak

        return is_continuous

    @staticmethod
    def _get_next_day(d: date) -> date:
        """获取下一天"""
        from datetime import timedelta

        return d + timedelta(days=1)


@dataclass
class DailyRewardConfig:
    """
    每日奖励配置数据类

    Attributes:
        day: 天数（1-7 或 30）
        day_type: 类型（cycle=7天循环，monthly=月累计）
        base_rewards: 基础奖励
        bonus_rewards: 加成奖励（连续签到额外奖励）
    """

    day: int
    day_type: str = "cycle"  # cycle | monthly
    base_rewards: list[CheckinReward] = field(default_factory=list)
    bonus_rewards: list[CheckinReward] = field(default_factory=list)
    streak_bonus: dict[str, int] = field(default_factory=dict)  # {streak_days: bonus_percent}

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "day": self.day,
            "day_type": self.day_type,
            "base_rewards": [r.to_dict() for r in self.base_rewards],
            "bonus_rewards": [r.to_dict() for r in self.bonus_rewards],
            "streak_bonus": self.streak_bonus,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DailyRewardConfig:
        """从字典创建"""
        return cls(
            day=data["day"],
            day_type=data.get("day_type", "cycle"),
            base_rewards=[CheckinReward.from_dict(r) for r in data.get("base_rewards", [])],
            bonus_rewards=[CheckinReward.from_dict(r) for r in data.get("bonus_rewards", [])],
            streak_bonus=data.get("streak_bonus", {}),
        )


@dataclass
class CheckinInfo:
    """
    签到信息数据类（用于返回给客户端）

    Attributes:
        can_checkin: 今日是否可签到
        today_checked: 今日是否已签到
        streak_info: 连续签到信息
        today_rewards: 今日签到奖励预览
        cycle_day: 当前周期天数
        monthly_count: 本月签到次数
        supplement_days: 可补签天数
    """

    can_checkin: bool
    today_checked: bool
    streak_info: CheckinStreak
    today_rewards: list[CheckinReward] = field(default_factory=list)
    cycle_day: int = 1
    monthly_count: int = 0
    supplement_days: int = 0
    next_checkin_time: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "can_checkin": self.can_checkin,
            "today_checked": self.today_checked,
            "streak_info": self.streak_info.to_dict(),
            "today_rewards": [r.to_dict() for r in self.today_rewards],
            "cycle_day": self.cycle_day,
            "monthly_count": self.monthly_count,
            "supplement_days": self.supplement_days,
            "next_checkin_time": self.next_checkin_time.isoformat()
            if self.next_checkin_time
            else None,
        }
