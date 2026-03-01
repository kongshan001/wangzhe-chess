"""
王者之奕 - 段位系统

本模块实现了游戏的段位系统，包括：
- 段位定义（青铜/白银/黄金/铂金/钻石/大师/王者）
- 星级系统
- 保级/降级规则
- 赛季重置

段位系统是玩家实力的直观体现，通过星级和段位
来展示玩家在当前赛季的竞技水平。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class Tier(Enum):
    """
    段位枚举

    从低到高定义了所有段位等级。
    每个段位对应一个数值，用于比较和计算。
    """

    BRONZE = 1  # 青铜
    SILVER = 2  # 白银
    GOLD = 3  # 黄金
    PLATINUM = 4  # 铂金
    DIAMOND = 5  # 钻石
    MASTER = 6  # 大师
    KING = 7  # 王者

    def get_display_name(self) -> str:
        """获取段位显示名称"""
        names = {
            Tier.BRONZE: "青铜",
            Tier.SILVER: "白银",
            Tier.GOLD: "黄金",
            Tier.PLATINUM: "铂金",
            Tier.DIAMOND: "钻石",
            Tier.MASTER: "大师",
            Tier.KING: "王者",
        }
        return names[self]

    def get_icon(self) -> str:
        """获取段位图标标识"""
        icons = {
            Tier.BRONZE: "🥉",
            Tier.SILVER: "🥈",
            Tier.GOLD: "🥇",
            Tier.PLATINUM: "💎",
            Tier.DIAMOND: "💠",
            Tier.MASTER: "🏆",
            Tier.KING: "👑",
        }
        return icons[self]


@dataclass
class TierConfig:
    """
    段位配置

    定义单个段位的详细配置参数。

    Attributes:
        tier: 段位枚举值
        min_stars: 该段位最低星级
        max_stars: 该段位最高星级
        demotion_protection_games: 降级保护场次
        promotion_bonus_stars: 晋级奖励星级
    """

    tier: Tier
    min_stars: int
    max_stars: int
    demotion_protection_games: int = 0
    promotion_bonus_stars: int = 0

    def get_star_range(self) -> int:
        """获取该段位的星级范围"""
        return self.max_stars - self.min_stars + 1


# 段位配置表
TIER_CONFIGS: dict[Tier, TierConfig] = {
    Tier.BRONZE: TierConfig(
        tier=Tier.BRONZE,
        min_stars=0,
        max_stars=9,
        demotion_protection_games=0,  # 最低段位无需保护
        promotion_bonus_stars=0,
    ),
    Tier.SILVER: TierConfig(
        tier=Tier.SILVER,
        min_stars=10,
        max_stars=19,
        demotion_protection_games=3,
        promotion_bonus_stars=0,
    ),
    Tier.GOLD: TierConfig(
        tier=Tier.GOLD,
        min_stars=20,
        max_stars=29,
        demotion_protection_games=3,
        promotion_bonus_stars=0,
    ),
    Tier.PLATINUM: TierConfig(
        tier=Tier.PLATINUM,
        min_stars=30,
        max_stars=39,
        demotion_protection_games=3,
        promotion_bonus_stars=0,
    ),
    Tier.DIAMOND: TierConfig(
        tier=Tier.DIAMOND,
        min_stars=40,
        max_stars=49,
        demotion_protection_games=3,
        promotion_bonus_stars=1,
    ),
    Tier.MASTER: TierConfig(
        tier=Tier.MASTER,
        min_stars=50,
        max_stars=74,
        demotion_protection_games=5,
        promotion_bonus_stars=2,
    ),
    Tier.KING: TierConfig(
        tier=Tier.KING,
        min_stars=75,
        max_stars=999,  # 王者没有上限
        demotion_protection_games=5,
        promotion_bonus_stars=3,
    ),
}


@dataclass
class PlayerRating:
    """
    玩家段位信息

    存储玩家的完整段位数据，包括当前段位、星级、
    保级状态等。

    Attributes:
        player_id: 玩家ID
        tier: 当前段位
        stars: 当前星级（绝对星级，0-based）
        highest_tier: 历史最高段位
        highest_stars: 历史最高星级
        demotion_counter: 降级计数器（连续失败场次）
        season_games: 本赛季总场次
        season_wins: 本赛季胜场
        win_streak: 当前连胜
        lose_streak: 当前连败
        last_season_tier: 上赛季段位（用于赛季重置）
        last_season_stars: 上赛季星级
    """

    player_id: str
    tier: Tier = Tier.BRONZE
    stars: int = 0
    highest_tier: Tier = Tier.BRONZE
    highest_stars: int = 0
    demotion_counter: int = 0
    season_games: int = 0
    season_wins: int = 0
    win_streak: int = 0
    lose_streak: int = 0
    last_season_tier: Tier | None = None
    last_season_stars: int = 0

    def __post_init__(self) -> None:
        """初始化后验证数据"""
        self._validate_and_fix()

    def _validate_and_fix(self) -> None:
        """验证并修复数据一致性"""
        config = TIER_CONFIGS.get(self.tier)
        if config:
            # 确保星级在合理范围内
            if self.stars < config.min_stars:
                self.stars = config.min_stars
            elif self.tier != Tier.KING and self.stars > config.max_stars:
                self.stars = config.max_stars

    def get_tier_stars(self) -> int:
        """
        获取当前段位内的相对星级

        Returns:
            在当前段位内的星级数（0-based）
        """
        config = TIER_CONFIGS.get(self.tier)
        if config:
            return self.stars - config.min_stars
        return 0

    def get_tier_progress(self) -> float:
        """
        获取当前段位的进度（0.0 - 1.0）

        Returns:
            当前段位进度百分比
        """
        config = TIER_CONFIGS.get(self.tier)
        if config:
            if self.tier == Tier.KING:
                # 王者段位没有固定上限
                return 1.0
            total_stars = config.get_star_range()
            current_stars = self.get_tier_stars()
            return current_stars / total_stars if total_stars > 0 else 0.0
        return 0.0

    def get_display_info(self) -> dict[str, Any]:
        """
        获取用于显示的段位信息

        Returns:
            包含显示信息的字典
        """
        return {
            "tier": self.tier.value,
            "tier_name": self.tier.get_display_name(),
            "tier_icon": self.tier.get_icon(),
            "stars": self.get_tier_stars(),
            "total_stars": TIER_CONFIGS[self.tier].get_star_range()
            if self.tier != Tier.KING
            else 999,
            "progress": self.get_tier_progress(),
            "highest_tier_name": self.highest_tier.get_display_name(),
            "win_rate": self.season_wins / self.season_games if self.season_games > 0 else 0.0,
        }

    def has_demotion_protection(self) -> bool:
        """
        检查是否有降级保护

        Returns:
            是否有降级保护
        """
        config = TIER_CONFIGS.get(self.tier)
        if config and config.demotion_protection_games > 0:
            return self.demotion_counter < config.demotion_protection_games
        return False

    def is_at_tier_bottom(self) -> bool:
        """
        检查是否处于段位底部（可能降级）

        Returns:
            是否处于段位底部
        """
        config = TIER_CONFIGS.get(self.tier)
        if config:
            return self.stars <= config.min_stars
        return False

    def record_game(self, is_win: bool) -> None:
        """
        记录一局游戏结果

        Args:
            is_win: 是否获胜
        """
        self.season_games += 1
        if is_win:
            self.season_wins += 1
            self.win_streak += 1
            self.lose_streak = 0
            # 胜利重置降级计数器
            self.demotion_counter = 0
        else:
            self.lose_streak += 1
            self.win_streak = 0
            # 失败增加降级计数器
            if self.is_at_tier_bottom():
                self.demotion_counter += 1

    def add_stars(self, amount: int) -> dict[str, Any]:
        """
        增加星级

        处理晋级逻辑，包括晋级奖励。

        Args:
            amount: 增加的星级数

        Returns:
            包含变化信息的字典
        """
        old_tier = self.tier
        old_stars = self.stars

        self.stars += amount

        # 更新历史最高
        if self.stars > self.highest_stars:
            self.highest_stars = self.stars
            self.highest_tier = self.tier

        # 检查晋级
        promotion = None
        if self.tier != Tier.KING:
            current_config = TIER_CONFIGS[self.tier]
            if self.stars > current_config.max_stars:
                # 晋级到下一段位
                next_tier = Tier(self.tier.value + 1)
                next_config = TIER_CONFIGS.get(next_tier)
                if next_config:
                    # 应用晋级奖励
                    bonus = next_config.promotion_bonus_stars
                    self.stars = next_config.min_stars + bonus
                    self.tier = next_tier
                    self.demotion_counter = 0
                    promotion = {
                        "promoted": True,
                        "new_tier": next_tier.get_display_name(),
                        "bonus_stars": bonus,
                    }

        # 更新历史最高段位
        if self.tier.value > self.highest_tier.value:
            self.highest_tier = self.tier

        return {
            "old_tier": old_tier.get_display_name(),
            "old_stars": old_stars,
            "new_tier": self.tier.get_display_name(),
            "new_stars": self.stars,
            "stars_change": amount,
            "promotion": promotion,
        }

    def remove_stars(self, amount: int) -> dict[str, Any]:
        """
        减少星级

        处理降级逻辑，包括保级检查。

        Args:
            amount: 减少的星级数

        Returns:
            包含变化信息的字典
        """
        old_tier = self.tier
        old_stars = self.stars

        # 检查保级保护
        if self.has_demotion_protection() and self.is_at_tier_bottom():
            # 触发保级保护，不扣星
            return {
                "old_tier": old_tier.get_display_name(),
                "old_stars": old_stars,
                "new_tier": self.tier.get_display_name(),
                "new_stars": self.stars,
                "stars_change": 0,
                "demotion_protection_triggered": True,
                "demotion": None,
            }

        self.stars = max(0, self.stars - amount)

        # 检查降级
        demotion = None
        config = TIER_CONFIGS.get(self.tier)
        if config and self.stars < config.min_stars:
            if self.tier != Tier.BRONZE:
                # 降级到上一段位
                prev_tier = Tier(self.tier.value - 1)
                prev_config = TIER_CONFIGS.get(prev_tier)
                if prev_config:
                    self.tier = prev_tier
                    self.stars = prev_config.max_stars
                    self.demotion_counter = 0
                    demotion = {
                        "demoted": True,
                        "new_tier": prev_tier.get_display_name(),
                    }

        return {
            "old_tier": old_tier.get_display_name(),
            "old_stars": old_stars,
            "new_tier": self.tier.get_display_name(),
            "new_stars": self.stars,
            "stars_change": -amount if not demotion else 0,
            "demotion_protection_triggered": False,
            "demotion": demotion,
        }

    def calculate_season_reset(self) -> PlayerRating:
        """
        计算赛季重置后的段位

        根据上赛季段位计算新赛季初始段位。
        赛季重置通常会让玩家降到一个合理的段位，
        但不会完全归零。

        Returns:
            重置后的新段位信息
        """
        # 保存上赛季数据
        last_tier = self.tier
        last_stars = self.stars

        # 计算降级幅度
        # 王者 -> 钻石
        # 大师 -> 铂金
        # 钻石 -> 铂金
        # 铂金 -> 黄金
        # 黄金 -> 白银
        # 白银 -> 青铜
        # 青铜 -> 青铜
        tier_drop = {
            Tier.KING: Tier.DIAMOND,
            Tier.MASTER: Tier.PLATINUM,
            Tier.DIAMOND: Tier.PLATINUM,
            Tier.PLATINUM: Tier.GOLD,
            Tier.GOLD: Tier.SILVER,
            Tier.SILVER: Tier.BRONZE,
            Tier.BRONZE: Tier.BRONZE,
        }

        new_tier = tier_drop.get(self.tier, Tier.BRONZE)
        new_config = TIER_CONFIGS[new_tier]

        # 新赛季从该段位的中间位置开始
        new_stars = new_config.min_stars + new_config.get_star_range() // 2

        return PlayerRating(
            player_id=self.player_id,
            tier=new_tier,
            stars=new_stars,
            highest_tier=self.highest_tier,
            highest_stars=self.highest_stars,
            demotion_counter=0,
            season_games=0,
            season_wins=0,
            win_streak=0,
            lose_streak=0,
            last_season_tier=last_tier,
            last_season_stars=last_stars,
        )

    def to_dict(self) -> dict[str, Any]:
        """序列化为字典"""
        return {
            "player_id": self.player_id,
            "tier": self.tier.value,
            "stars": self.stars,
            "highest_tier": self.highest_tier.value,
            "highest_stars": self.highest_stars,
            "demotion_counter": self.demotion_counter,
            "season_games": self.season_games,
            "season_wins": self.season_wins,
            "win_streak": self.win_streak,
            "lose_streak": self.lose_streak,
            "last_season_tier": self.last_season_tier.value if self.last_season_tier else None,
            "last_season_stars": self.last_season_stars,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PlayerRating:
        """从字典反序列化"""
        return cls(
            player_id=data["player_id"],
            tier=Tier(data.get("tier", 1)),
            stars=data.get("stars", 0),
            highest_tier=Tier(data.get("highest_tier", 1)),
            highest_stars=data.get("highest_stars", 0),
            demotion_counter=data.get("demotion_counter", 0),
            season_games=data.get("season_games", 0),
            season_wins=data.get("season_wins", 0),
            win_streak=data.get("win_streak", 0),
            lose_streak=data.get("lose_streak", 0),
            last_season_tier=Tier(data["last_season_tier"])
            if data.get("last_season_tier")
            else None,
            last_season_stars=data.get("last_season_stars", 0),
        )

    @classmethod
    def create_new(cls, player_id: str) -> PlayerRating:
        """
        创建新玩家的段位信息

        Args:
            player_id: 玩家ID

        Returns:
            初始段位信息（青铜0星）
        """
        return cls(player_id=player_id)


class SeasonManager:
    """
    赛季管理器

    管理赛季相关的全局操作。
    """

    @staticmethod
    def get_tier_from_elo(elo: int) -> Tier:
        """
        根据 ELO 分数获取对应段位

        Args:
            elo: ELO 分数

        Returns:
            对应的段位
        """
        # ELO 到段位的映射
        if elo < 1200:
            return Tier.BRONZE
        elif elo < 1400:
            return Tier.SILVER
        elif elo < 1600:
            return Tier.GOLD
        elif elo < 1800:
            return Tier.PLATINUM
        elif elo < 2000:
            return Tier.DIAMOND
        elif elo < 2200:
            return Tier.MASTER
        else:
            return Tier.KING

    @staticmethod
    def get_stars_from_elo(elo: int, tier: Tier) -> int:
        """
        根据 ELO 和段位计算星级

        Args:
            elo: ELO 分数
            tier: 段位

        Returns:
            星级数
        """
        config = TIER_CONFIGS[tier]

        # 在段位内的相对分数
        tier_ranges = {
            Tier.BRONZE: (0, 1200),
            Tier.SILVER: (1200, 1400),
            Tier.GOLD: (1400, 1600),
            Tier.PLATINUM: (1600, 1800),
            Tier.DIAMOND: (1800, 2000),
            Tier.MASTER: (2000, 2200),
            Tier.KING: (2200, 3000),
        }

        min_elo, max_elo = tier_ranges.get(tier, (0, 1200))
        elo_range = max_elo - min_elo
        elo_in_tier = max(0, elo - min_elo)

        # 按比例计算星级
        if elo_range > 0:
            progress = elo_in_tier / elo_range
            star_range = config.get_star_range()
            stars = config.min_stars + int(progress * star_range)
        else:
            stars = config.min_stars

        return stars


def get_tier_config(tier: Tier) -> TierConfig:
    """
    获取段位配置

    Args:
        tier: 段位枚举值

    Returns:
        段位配置
    """
    return TIER_CONFIGS.get(tier, TIER_CONFIGS[Tier.BRONZE])


def compare_ratings(rating_a: PlayerRating, rating_b: PlayerRating) -> int:
    """
    比较两个玩家的段位

    Args:
        rating_a: 玩家A的段位
        rating_b: 玩家B的段位

    Returns:
        正数表示A高，负数表示B高，0表示相同
    """
    star_diff = rating_a.stars - rating_b.stars
    if star_diff != 0:
        return star_diff

    # 星级相同则比较连胜
    return rating_a.win_streak - rating_b.win_streak
