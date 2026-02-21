"""
王者之奕 - 赛季系统数据模型

本模块定义赛季系统的核心数据类：
- Season: 赛季信息
- SeasonReward: 赛季奖励配置
- PlayerSeasonData: 玩家赛季数据
- SeasonStatus: 赛季状态枚举

用于存储和管理赛季相关的数据。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class SeasonStatus(Enum):
    """赛季状态枚举"""
    UPCOMING = "upcoming"      # 即将开始
    ACTIVE = "active"          # 进行中
    ENDING = "ending"          # 即将结束(最后3天)
    ENDED = "ended"            # 已结束


class Tier(int, Enum):
    """段位枚举"""
    BRONZE = 1       # 青铜
    SILVER = 2       # 白银
    GOLD = 3         # 黄金
    PLATINUM = 4     # 铂金
    DIAMOND = 5      # 钻石
    MASTER = 6       # 大师
    GRANDMASTER = 7  # 宗师
    KING = 8         # 王者

    @classmethod
    def from_name(cls, name: str) -> "Tier":
        """从名称获取段位"""
        name_map = {
            "bronze": cls.BRONZE,
            "silver": cls.SILVER,
            "gold": cls.GOLD,
            "platinum": cls.PLATINUM,
            "diamond": cls.DIAMOND,
            "master": cls.MASTER,
            "grandmaster": cls.GRANDMASTER,
            "king": cls.KING,
        }
        return name_map.get(name.lower(), cls.BRONZE)

    @property
    def display_name(self) -> str:
        """获取显示名称"""
        names = {
            Tier.BRONZE: "青铜",
            Tier.SILVER: "白银",
            Tier.GOLD: "黄金",
            Tier.PLATINUM: "铂金",
            Tier.DIAMOND: "钻石",
            Tier.MASTER: "大师",
            Tier.GRANDMASTER: "宗师",
            Tier.KING: "王者",
        }
        return names[self]


@dataclass
class SeasonReward:
    """
    赛季奖励配置
    
    根据玩家最终段位发放的奖励。
    
    Attributes:
        tier: 达到的段位
        avatar_frame: 头像框ID（可选）
        skin: 皮肤ID（可选）
        title: 称号ID（可选）
        gold: 金币奖励
        exp: 经验值奖励
        items: 其他物品奖励列表
    """
    tier: Tier
    avatar_frame: Optional[str] = None
    skin: Optional[str] = None
    title: Optional[str] = None
    gold: int = 0
    exp: int = 0
    items: list[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "tier": self.tier.value,
            "tier_name": self.tier.display_name,
            "avatar_frame": self.avatar_frame,
            "skin": self.skin,
            "title": self.title,
            "gold": self.gold,
            "exp": self.exp,
            "items": self.items,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SeasonReward":
        """从字典创建"""
        tier = data.get("tier", 1)
        if isinstance(tier, int):
            tier = Tier(tier)
        elif isinstance(tier, str):
            tier = Tier.from_name(tier)
        
        return cls(
            tier=tier,
            avatar_frame=data.get("avatar_frame"),
            skin=data.get("skin"),
            title=data.get("title"),
            gold=data.get("gold", 0),
            exp=data.get("exp", 0),
            items=data.get("items", []),
        )


@dataclass
class Season:
    """
    赛季信息
    
    定义一个赛季的基本信息和奖励配置。
    
    Attributes:
        season_id: 赛季唯一ID
        name: 赛季名称
        start_time: 开始时间
        end_time: 结束时间
        is_active: 是否为当前活跃赛季
        description: 赛季描述
        rewards: 段位奖励配置 (tier -> reward)
        pass_free_rewards: 免费通行证奖励
        pass_premium_rewards: 付费通行证奖励
    """
    season_id: str
    name: str
    start_time: datetime
    end_time: datetime
    is_active: bool = True
    description: str = ""
    rewards: Dict[int, SeasonReward] = field(default_factory=dict)
    pass_free_rewards: list[Dict[str, Any]] = field(default_factory=list)
    pass_premium_rewards: list[Dict[str, Any]] = field(default_factory=list)

    @property
    def status(self) -> SeasonStatus:
        """获取赛季状态"""
        now = datetime.now()
        if now < self.start_time:
            return SeasonStatus.UPCOMING
        elif now > self.end_time:
            return SeasonStatus.ENDED
        elif (self.end_time - now).days <= 3:
            return SeasonStatus.ENDING
        else:
            return SeasonStatus.ACTIVE

    @property
    def duration_days(self) -> int:
        """获取赛季持续天数"""
        return (self.end_time - self.start_time).days

    @property
    def days_remaining(self) -> int:
        """获取剩余天数"""
        remaining = (self.end_time - datetime.now()).days
        return max(0, remaining)

    @property
    def progress(self) -> float:
        """获取赛季进度(0-1)"""
        total = (self.end_time - self.start_time).total_seconds()
        elapsed = (datetime.now() - self.start_time).total_seconds()
        return min(1.0, max(0.0, elapsed / total))

    def get_reward_for_tier(self, tier: Tier) -> Optional[SeasonReward]:
        """获取指定段位的奖励"""
        return self.rewards.get(tier.value)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "season_id": self.season_id,
            "name": self.name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "is_active": self.is_active,
            "description": self.description,
            "status": self.status.value,
            "duration_days": self.duration_days,
            "days_remaining": self.days_remaining,
            "progress": round(self.progress * 100, 2),
            "rewards": {k: v.to_dict() for k, v in self.rewards.items()},
            "pass_free_rewards": self.pass_free_rewards,
            "pass_premium_rewards": self.pass_premium_rewards,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Season":
        """从字典创建"""
        rewards = {}
        for tier_val, reward_data in data.get("rewards", {}).items():
            rewards[int(tier_val)] = SeasonReward.from_dict(reward_data)
        
        return cls(
            season_id=data["season_id"],
            name=data["name"],
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(data["end_time"]),
            is_active=data.get("is_active", True),
            description=data.get("description", ""),
            rewards=rewards,
            pass_free_rewards=data.get("pass_free_rewards", []),
            pass_premium_rewards=data.get("pass_premium_rewards", []),
        )


@dataclass
class PlayerSeasonData:
    """
    玩家赛季数据
    
    记录玩家在一个赛季中的表现和进度。
    
    Attributes:
        player_id: 玩家ID
        season_id: 赛季ID
        highest_tier: 历史最高段位
        final_tier: 最终段位
        total_games: 总对局数
        total_wins: 总胜场(第1名)
        total_top4: 总前四场数
        first_place_count: 第一名次数
        top4_rate: 前四率
        
        # 通行证
        pass_level: 通行证等级
        pass_exp: 通行证经验
        pass_premium: 是否购买付费通行证
        
        # 定位赛
        placement_done: 是否完成定位赛
        placement_matches: 定位赛场次
        placement_wins: 定位赛胜场
    """
    player_id: str
    season_id: str
    highest_tier: Tier = Tier.BRONZE
    final_tier: Tier = Tier.BRONZE
    total_games: int = 0
    total_wins: int = 0
    total_top4: int = 0
    first_place_count: int = 0
    top4_rate: float = 0.0
    
    # 通行证
    pass_level: int = 1
    pass_exp: int = 0
    pass_premium: bool = False
    
    # 定位赛
    placement_done: bool = False
    placement_matches: int = 0
    placement_wins: int = 0

    @property
    def win_rate(self) -> float:
        """计算胜率"""
        if self.total_games == 0:
            return 0.0
        return round(self.total_wins / self.total_games * 100, 2)

    @property
    def avg_rank(self) -> float:
        """估算平均排名(简化计算)"""
        if self.total_games == 0:
            return 0.0
        # 基于胜率和前四率估算
        return round(4.5 - (self.top4_rate / 100 * 2.5), 2)

    def add_game_result(self, rank: int) -> None:
        """
        添加对局结果
        
        Args:
            rank: 本局排名 (1-8)
        """
        self.total_games += 1
        if rank == 1:
            self.total_wins += 1
            self.first_place_count += 1
        if rank <= 4:
            self.total_top4 += 1
        
        # 更新前四率
        self.top4_rate = round(self.total_top4 / self.total_games * 100, 2)

    def add_pass_exp(self, exp: int) -> int:
        """
        添加通行证经验并升级
        
        Args:
            exp: 获得的经验值
            
        Returns:
            升级后的等级
        """
        self.pass_exp += exp
        # 每100经验升一级
        new_level = 1 + self.pass_exp // 100
        self.pass_level = new_level
        return self.pass_level

    def update_tier(self, new_tier: Tier) -> None:
        """
        更新段位
        
        Args:
            new_tier: 新段位
        """
        self.final_tier = new_tier
        if new_tier > self.highest_tier:
            self.highest_tier = new_tier

    def record_placement_match(self, won: bool) -> bool:
        """
        记录定位赛结果
        
        Args:
            won: 是否获胜
            
        Returns:
            是否完成定位赛
        """
        self.placement_matches += 1
        if won:
            self.placement_wins += 1
        
        if self.placement_matches >= 10:
            self.placement_done = True
        
        return self.placement_done

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "player_id": self.player_id,
            "season_id": self.season_id,
            "highest_tier": self.highest_tier.value,
            "highest_tier_name": self.highest_tier.display_name,
            "final_tier": self.final_tier.value,
            "final_tier_name": self.final_tier.display_name,
            "total_games": self.total_games,
            "total_wins": self.total_wins,
            "total_top4": self.total_top4,
            "first_place_count": self.first_place_count,
            "top4_rate": self.top4_rate,
            "win_rate": self.win_rate,
            "avg_rank": self.avg_rank,
            "pass_level": self.pass_level,
            "pass_exp": self.pass_exp,
            "pass_premium": self.pass_premium,
            "placement_done": self.placement_done,
            "placement_matches": self.placement_matches,
            "placement_wins": self.placement_wins,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlayerSeasonData":
        """从字典创建"""
        highest_tier = data.get("highest_tier", 1)
        final_tier = data.get("final_tier", 1)
        
        if isinstance(highest_tier, int):
            highest_tier = Tier(highest_tier)
        elif isinstance(highest_tier, str):
            highest_tier = Tier.from_name(highest_tier)
        
        if isinstance(final_tier, int):
            final_tier = Tier(final_tier)
        elif isinstance(final_tier, str):
            final_tier = Tier.from_name(final_tier)
        
        return cls(
            player_id=data["player_id"],
            season_id=data["season_id"],
            highest_tier=highest_tier,
            final_tier=final_tier,
            total_games=data.get("total_games", 0),
            total_wins=data.get("total_wins", 0),
            total_top4=data.get("total_top4", 0),
            first_place_count=data.get("first_place_count", 0),
            top4_rate=data.get("top4_rate", 0.0),
            pass_level=data.get("pass_level", 1),
            pass_exp=data.get("pass_exp", 0),
            pass_premium=data.get("pass_premium", False),
            placement_done=data.get("placement_done", False),
            placement_matches=data.get("placement_matches", 0),
            placement_wins=data.get("placement_wins", 0),
        )
