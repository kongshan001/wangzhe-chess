"""
王者之奕 - 投票系统数据模型

本模块定义投票系统的数据类：
- VotingPoll: 投票主题
- VotingOption: 投票选项
- PlayerVote: 玩家投票记录
- VotingReward: 投票奖励
- VotingType: 投票类型枚举
- VotingStatus: 投票状态枚举

用于投票系统的数据处理和传输。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class VotingType(str, Enum):
    """投票类型枚举"""

    NEW_HERO = "new_hero"  # 新英雄投票
    BALANCE = "balance"  # 平衡性调整投票
    EVENT_THEME = "event_theme"  # 活动主题投票
    SKIN_DESIGN = "skin_design"  # 皮肤设计投票
    CUSTOM = "custom"  # 自定义投票


class VotingStatus(str, Enum):
    """投票状态枚举"""

    DRAFT = "draft"  # 草稿
    ONGOING = "ongoing"  # 进行中
    ENDED = "ended"  # 已结束
    CANCELLED = "cancelled"  # 已取消


class RewardType(str, Enum):
    """奖励类型枚举"""

    GOLD = "gold"  # 金币
    DIAMOND = "diamond"  # 钻石
    HERO_FRAGMENT = "hero_fragment"  # 英雄碎片
    ITEM = "item"  # 道具
    SKIN = "skin"  # 皮肤
    EXP = "exp"  # 经验


@dataclass
class VotingOption:
    """
    投票选项数据类

    存储单个投票选项的信息。

    Attributes:
        option_id: 选项唯一ID
        poll_id: 所属投票ID
        title: 选项标题
        description: 选项描述
        icon: 选项图标
        extra_data: 额外数据（如新英雄属性等）
        vote_count: 当前票数
        percentage: 得票百分比
    """

    option_id: str
    poll_id: str
    title: str
    description: str = ""
    icon: str | None = None
    extra_data: dict[str, Any] = field(default_factory=dict)
    vote_count: int = 0
    percentage: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "option_id": self.option_id,
            "poll_id": self.poll_id,
            "title": self.title,
            "description": self.description,
            "icon": self.icon,
            "extra_data": self.extra_data,
            "vote_count": self.vote_count,
            "percentage": round(self.percentage, 2),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VotingOption:
        """从字典创建"""
        return cls(
            option_id=data["option_id"],
            poll_id=data["poll_id"],
            title=data["title"],
            description=data.get("description", ""),
            icon=data.get("icon"),
            extra_data=data.get("extra_data", {}),
            vote_count=data.get("vote_count", 0),
            percentage=data.get("percentage", 0.0),
        )


@dataclass
class VotingReward:
    """
    投票奖励数据类

    存储投票奖励的信息。

    Attributes:
        reward_id: 奖励唯一ID
        reward_type: 奖励类型
        item_id: 物品ID（如英雄ID、皮肤ID等）
        quantity: 数量
        is_bonus: 是否为投中额外奖励
        extra_data: 额外数据
    """

    reward_id: str
    reward_type: RewardType
    item_id: str | None = None
    quantity: int = 1
    is_bonus: bool = False
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
            "is_bonus": self.is_bonus,
            "extra_data": self.extra_data,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VotingReward:
        """从字典创建"""
        return cls(
            reward_id=data["reward_id"],
            reward_type=RewardType(data["reward_type"]),
            item_id=data.get("item_id"),
            quantity=data.get("quantity", 1),
            is_bonus=data.get("is_bonus", False),
            extra_data=data.get("extra_data", {}),
        )


@dataclass
class PlayerVote:
    """
    玩家投票记录数据类

    存储玩家的投票记录信息。

    Attributes:
        vote_id: 投票记录唯一ID
        poll_id: 投票ID
        player_id: 玩家ID
        option_id: 选择的选项ID
        vote_weight: 投票权重（VIP额外票数）
        vote_time: 投票时间
        is_vip: 是否为VIP玩家
        rewards_claimed: 是否已领取奖励
        rewards_claimed_at: 奖励领取时间
    """

    vote_id: str
    poll_id: str
    player_id: str
    option_id: str
    vote_weight: int = 1
    vote_time: datetime = field(default_factory=datetime.now)
    is_vip: bool = False
    rewards_claimed: bool = False
    rewards_claimed_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "vote_id": self.vote_id,
            "poll_id": self.poll_id,
            "player_id": self.player_id,
            "option_id": self.option_id,
            "vote_weight": self.vote_weight,
            "vote_time": self.vote_time.isoformat(),
            "is_vip": self.is_vip,
            "rewards_claimed": self.rewards_claimed,
            "rewards_claimed_at": self.rewards_claimed_at.isoformat()
            if self.rewards_claimed_at
            else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PlayerVote:
        """从字典创建"""
        return cls(
            vote_id=data["vote_id"],
            poll_id=data["poll_id"],
            player_id=data["player_id"],
            option_id=data["option_id"],
            vote_weight=data.get("vote_weight", 1),
            vote_time=datetime.fromisoformat(data["vote_time"])
            if data.get("vote_time")
            else datetime.now(),
            is_vip=data.get("is_vip", False),
            rewards_claimed=data.get("rewards_claimed", False),
            rewards_claimed_at=datetime.fromisoformat(data["rewards_claimed_at"])
            if data.get("rewards_claimed_at")
            else None,
        )


@dataclass
class VotingPoll:
    """
    投票主题数据类

    存储投票主题的完整信息。

    Attributes:
        poll_id: 投票唯一ID
        title: 投票标题
        description: 投票描述
        voting_type: 投票类型
        status: 投票状态
        options: 投票选项列表
        start_time: 开始时间
        end_time: 结束时间
        participation_reward: 参与奖励
        win_bonus_reward: 投中额外奖励
        total_votes: 总票数
        total_voters: 参与人数
        min_vip_level: 最低VIP等级要求（0表示无限制）
        created_by: 创建者ID
        created_at: 创建时间
        updated_at: 更新时间
        winning_option_id: 获胜选项ID（投票结束后设置）
        tags: 标签列表
        extra_data: 额外数据
    """

    poll_id: str
    title: str
    description: str = ""
    voting_type: VotingType = VotingType.CUSTOM
    status: VotingStatus = VotingStatus.DRAFT
    options: list[VotingOption] = field(default_factory=list)
    start_time: datetime | None = None
    end_time: datetime | None = None
    participation_reward: list[VotingReward] = field(default_factory=list)
    win_bonus_reward: list[VotingReward] = field(default_factory=list)
    total_votes: int = 0
    total_voters: int = 0
    min_vip_level: int = 0
    created_by: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    winning_option_id: str | None = None
    tags: list[str] = field(default_factory=list)
    extra_data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "poll_id": self.poll_id,
            "title": self.title,
            "description": self.description,
            "voting_type": self.voting_type.value
            if isinstance(self.voting_type, VotingType)
            else self.voting_type,
            "status": self.status.value if isinstance(self.status, VotingStatus) else self.status,
            "options": [o.to_dict() for o in self.options],
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "participation_reward": [r.to_dict() for r in self.participation_reward],
            "win_bonus_reward": [r.to_dict() for r in self.win_bonus_reward],
            "total_votes": self.total_votes,
            "total_voters": self.total_voters,
            "min_vip_level": self.min_vip_level,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "winning_option_id": self.winning_option_id,
            "tags": self.tags,
            "extra_data": self.extra_data,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VotingPoll:
        """从字典创建"""
        return cls(
            poll_id=data["poll_id"],
            title=data["title"],
            description=data.get("description", ""),
            voting_type=VotingType(data["voting_type"])
            if data.get("voting_type")
            else VotingType.CUSTOM,
            status=VotingStatus(data["status"]) if data.get("status") else VotingStatus.DRAFT,
            options=[VotingOption.from_dict(o) for o in data.get("options", [])],
            start_time=datetime.fromisoformat(data["start_time"])
            if data.get("start_time")
            else None,
            end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            participation_reward=[
                VotingReward.from_dict(r) for r in data.get("participation_reward", [])
            ],
            win_bonus_reward=[VotingReward.from_dict(r) for r in data.get("win_bonus_reward", [])],
            total_votes=data.get("total_votes", 0),
            total_voters=data.get("total_voters", 0),
            min_vip_level=data.get("min_vip_level", 0),
            created_by=data.get("created_by"),
            created_at=datetime.fromisoformat(data["created_at"])
            if data.get("created_at")
            else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"])
            if data.get("updated_at")
            else datetime.now(),
            winning_option_id=data.get("winning_option_id"),
            tags=data.get("tags", []),
            extra_data=data.get("extra_data", {}),
        )

    def is_active(self) -> bool:
        """检查投票是否进行中"""
        if self.status != VotingStatus.ONGOING:
            return False

        now = datetime.now()
        if self.start_time and now < self.start_time:
            return False
        if self.end_time and now > self.end_time:
            return False

        return True

    def is_ended(self) -> bool:
        """检查投票是否已结束"""
        return self.status == VotingStatus.ENDED

    def get_option(self, option_id: str) -> VotingOption | None:
        """获取指定选项"""
        for option in self.options:
            if option.option_id == option_id:
                return option
        return None

    def update_percentages(self) -> None:
        """更新各选项得票百分比"""
        if self.total_votes == 0:
            for option in self.options:
                option.percentage = 0.0
            return

        for option in self.options:
            option.percentage = (option.vote_count / self.total_votes) * 100

    def get_winning_option(self) -> VotingOption | None:
        """获取获胜选项"""
        if not self.options:
            return None

        return max(self.options, key=lambda o: o.vote_count)


@dataclass
class VotingResult:
    """
    投票结果数据类

    存储投票的最终结果信息。

    Attributes:
        poll_id: 投票ID
        winning_option: 获胜选项
        total_votes: 总票数
        total_voters: 参与人数
        results: 各选项结果列表
        ended_at: 结束时间
    """

    poll_id: str
    winning_option: VotingOption | None = None
    total_votes: int = 0
    total_voters: int = 0
    results: list[dict[str, Any]] = field(default_factory=list)
    ended_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "poll_id": self.poll_id,
            "winning_option": self.winning_option.to_dict() if self.winning_option else None,
            "total_votes": self.total_votes,
            "total_voters": self.total_voters,
            "results": self.results,
            "ended_at": self.ended_at.isoformat(),
        }


@dataclass
class VotingInfo:
    """
    投票信息数据类（用于返回给客户端）

    Attributes:
        poll: 投票详情
        player_voted: 玩家是否已投票
        player_vote: 玩家投票记录（如果已投票）
        can_vote: 是否可以投票
        reason: 不能投票的原因
    """

    poll: VotingPoll
    player_voted: bool = False
    player_vote: PlayerVote | None = None
    can_vote: bool = True
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "poll": self.poll.to_dict(),
            "player_voted": self.player_voted,
            "player_vote": self.player_vote.to_dict() if self.player_vote else None,
            "can_vote": self.can_vote,
            "reason": self.reason,
        }


# VIP投票权重配置
VIP_VOTE_WEIGHTS: dict[int, int] = {
    0: 1,  # 普通玩家：1票
    1: 2,  # VIP1：2票
    2: 3,  # VIP2：3票
    3: 4,  # VIP3：4票
    4: 5,  # VIP4：5票
    5: 7,  # VIP5：7票
    6: 10,  # VIP6：10票
}

DEFAULT_PARTICIPATION_REWARDS = [
    VotingReward(
        reward_id="participation_gold",
        reward_type=RewardType.GOLD,
        quantity=50,
    ),
]

DEFAULT_WIN_BONUS_REWARDS = [
    VotingReward(
        reward_id="win_bonus_gold",
        reward_type=RewardType.GOLD,
        quantity=100,
        is_bonus=True,
    ),
    VotingReward(
        reward_id="win_bonus_fragment",
        reward_type=RewardType.HERO_FRAGMENT,
        quantity=10,
        is_bonus=True,
    ),
]
