"""
王者之奕 - 排行榜数据模型

本模块定义排行榜系统的核心数据类：
- LeaderboardType: 排行榜类型枚举
- LeaderboardPeriod: 排行榜周期枚举
- LeaderboardEntry: 排行榜条目
- LeaderboardReward: 排行榜奖励
- PlayerRankInfo: 玩家排名信息

用于存储和管理排行榜相关的数据。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class LeaderboardType(str, Enum):
    """排行榜类型枚举"""
    
    TIER = "tier"              # 段位排行（按段位积分）
    WIN_RATE = "win_rate"      # 胜率排行
    FIRST_PLACE = "first_place"  # 吃鸡排行（第一名次数）
    DAMAGE = "damage"          # 伤害排行（单局最高伤害）
    WEALTH = "wealth"          # 财富排行（累计金币）
    
    @property
    def display_name(self) -> str:
        """获取显示名称"""
        names = {
            LeaderboardType.TIER: "段位排行",
            LeaderboardType.WIN_RATE: "胜率排行",
            LeaderboardType.FIRST_PLACE: "吃鸡排行",
            LeaderboardType.DAMAGE: "伤害排行",
            LeaderboardType.WEALTH: "财富排行",
        }
        return names[self]


class LeaderboardPeriod(str, Enum):
    """排行榜周期枚举"""
    
    WEEKLY = "weekly"     # 周榜
    MONTHLY = "monthly"   # 月榜
    SEASON = "season"     # 赛季榜
    
    @property
    def display_name(self) -> str:
        """获取显示名称"""
        names = {
            LeaderboardPeriod.WEEKLY: "周榜",
            LeaderboardPeriod.MONTHLY: "月榜",
            LeaderboardPeriod.SEASON: "赛季榜",
        }
        return names[self]


@dataclass
class LeaderboardReward:
    """
    排行榜奖励
    
    定义排行榜结束后发放的奖励。
    
    Attributes:
        rank_start: 起始排名（包含）
        rank_end: 结束排名（包含）
        gold: 金币奖励
        exp: 经验值奖励
        title: 称号奖励ID（可选）
        avatar_frame: 头像框ID（可选）
        items: 其他物品奖励列表
    """
    
    rank_start: int
    rank_end: int
    gold: int = 0
    exp: int = 0
    title: Optional[str] = None
    avatar_frame: Optional[str] = None
    items: List[Dict[str, Any]] = field(default_factory=list)
    
    def contains_rank(self, rank: int) -> bool:
        """检查排名是否在奖励范围内"""
        return self.rank_start <= rank <= self.rank_end
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "rank_start": self.rank_start,
            "rank_end": self.rank_end,
            "gold": self.gold,
            "exp": self.exp,
            "title": self.title,
            "avatar_frame": self.avatar_frame,
            "items": self.items,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LeaderboardReward":
        """从字典创建"""
        return cls(
            rank_start=data["rank_start"],
            rank_end=data["rank_end"],
            gold=data.get("gold", 0),
            exp=data.get("exp", 0),
            title=data.get("title"),
            avatar_frame=data.get("avatar_frame"),
            items=data.get("items", []),
        )


@dataclass
class LeaderboardEntry:
    """
    排行榜条目
    
    表示排行榜中的一条记录。
    
    Attributes:
        player_id: 玩家ID
        nickname: 玩家昵称
        avatar: 玩家头像
        rank: 排名
        score: 分数/数值
        tier: 段位（用于段位榜）
        stars: 星数（用于段位榜）
        extra_data: 额外数据
    """
    
    player_id: str
    nickname: str
    avatar: str
    rank: int
    score: float
    tier: str = "bronze"
    stars: int = 0
    extra_data: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def display_rank(self) -> str:
        """获取段位显示"""
        tier_names = {
            "bronze": "青铜",
            "silver": "白银",
            "gold": "黄金",
            "platinum": "铂金",
            "diamond": "钻石",
            "master": "大师",
            "grandmaster": "宗师",
            "challenger": "王者",
        }
        return f"{tier_names.get(self.tier, self.tier)} {self.stars}星"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "player_id": self.player_id,
            "nickname": self.nickname,
            "avatar": self.avatar,
            "rank": self.rank,
            "score": self.score,
            "tier": self.tier,
            "stars": self.stars,
            "display_rank": self.display_rank,
            "extra_data": self.extra_data,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LeaderboardEntry":
        """从字典创建"""
        return cls(
            player_id=data["player_id"],
            nickname=data.get("nickname", ""),
            avatar=data.get("avatar", ""),
            rank=data.get("rank", 0),
            score=data.get("score", 0),
            tier=data.get("tier", "bronze"),
            stars=data.get("stars", 0),
            extra_data=data.get("extra_data", {}),
        )


@dataclass
class PlayerRankInfo:
    """
    玩家排名信息
    
    表示玩家在某个排行榜中的排名详情。
    
    Attributes:
        player_id: 玩家ID
        leaderboard_type: 排行榜类型
        period: 排行榜周期
        rank: 当前排名（0表示未上榜）
        score: 当前分数
        total_players: 总参与人数
        percentile: 百分位排名
        history_rank: 历史排名变化（正数上升，负数下降）
        rewards_claimed: 是否已领取奖励
        best_rank: 历史最佳排名
    """
    
    player_id: str
    leaderboard_type: LeaderboardType
    period: LeaderboardPeriod
    rank: int = 0
    score: float = 0.0
    total_players: int = 0
    percentile: float = 100.0
    history_rank: int = 0
    rewards_claimed: bool = False
    best_rank: int = 0
    
    @property
    def is_ranked(self) -> bool:
        """是否上榜"""
        return self.rank > 0
    
    @property
    def rank_change_text(self) -> str:
        """排名变化文本"""
        if self.history_rank == 0:
            return "新上榜"
        elif self.history_rank > 0:
            return f"↑{self.history_rank}"
        elif self.history_rank < 0:
            return f"↓{abs(self.history_rank)}"
        return "不变"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "player_id": self.player_id,
            "leaderboard_type": self.leaderboard_type.value,
            "leaderboard_type_name": self.leaderboard_type.display_name,
            "period": self.period.value,
            "period_name": self.period.display_name,
            "rank": self.rank,
            "score": self.score,
            "total_players": self.total_players,
            "percentile": self.percentile,
            "history_rank": self.history_rank,
            "rank_change_text": self.rank_change_text,
            "rewards_claimed": self.rewards_claimed,
            "best_rank": self.best_rank,
            "is_ranked": self.is_ranked,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlayerRankInfo":
        """从字典创建"""
        leaderboard_type = data.get("leaderboard_type", "tier")
        if isinstance(leaderboard_type, str):
            leaderboard_type = LeaderboardType(leaderboard_type)
        
        period = data.get("period", "weekly")
        if isinstance(period, str):
            period = LeaderboardPeriod(period)
        
        return cls(
            player_id=data["player_id"],
            leaderboard_type=leaderboard_type,
            period=period,
            rank=data.get("rank", 0),
            score=data.get("score", 0),
            total_players=data.get("total_players", 0),
            percentile=data.get("percentile", 100.0),
            history_rank=data.get("history_rank", 0),
            rewards_claimed=data.get("rewards_claimed", False),
            best_rank=data.get("best_rank", 0),
        )


@dataclass
class LeaderboardData:
    """
    排行榜数据
    
    表示完整的排行榜数据。
    
    Attributes:
        leaderboard_type: 排行榜类型
        period: 排行榜周期
        entries: 排行榜条目列表
        total_count: 总记录数
        page: 当前页码
        page_size: 每页大小
        updated_at: 更新时间
        period_start: 周期开始时间
        period_end: 周期结束时间
    """
    
    leaderboard_type: LeaderboardType
    period: LeaderboardPeriod
    entries: List[LeaderboardEntry] = field(default_factory=list)
    total_count: int = 0
    page: int = 1
    page_size: int = 50
    updated_at: Optional[datetime] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "leaderboard_type": self.leaderboard_type.value,
            "leaderboard_type_name": self.leaderboard_type.display_name,
            "period": self.period.value,
            "period_name": self.period.display_name,
            "entries": [e.to_dict() for e in self.entries],
            "total_count": self.total_count,
            "page": self.page,
            "page_size": self.page_size,
            "total_pages": (self.total_count + self.page_size - 1) // self.page_size if self.page_size > 0 else 0,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LeaderboardData":
        """从字典创建"""
        leaderboard_type = data.get("leaderboard_type", "tier")
        if isinstance(leaderboard_type, str):
            leaderboard_type = LeaderboardType(leaderboard_type)
        
        period = data.get("period", "weekly")
        if isinstance(period, str):
            period = LeaderboardPeriod(period)
        
        entries_data = data.get("entries", [])
        entries = [LeaderboardEntry.from_dict(e) for e in entries_data]
        
        updated_at = data.get("updated_at")
        if updated_at and isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        
        period_start = data.get("period_start")
        if period_start and isinstance(period_start, str):
            period_start = datetime.fromisoformat(period_start)
        
        period_end = data.get("period_end")
        if period_end and isinstance(period_end, str):
            period_end = datetime.fromisoformat(period_end)
        
        return cls(
            leaderboard_type=leaderboard_type,
            period=period,
            entries=entries,
            total_count=data.get("total_count", 0),
            page=data.get("page", 1),
            page_size=data.get("page_size", 50),
            updated_at=updated_at,
            period_start=period_start,
            period_end=period_end,
        )
