"""
王者之奕 - ELO 等级分系统

本模块实现了基于 ELO 算法的等级分系统，包括：
- ELO 计算公式
- K 值动态调整
- 段位划分映射
- 升降级逻辑

ELO 系统用于量化评估玩家的竞技水平，
通过比赛结果动态调整分数，使匹配更加公平。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Optional

from .rating import Tier, PlayerRating, SeasonManager


@dataclass
class EloConfig:
    """
    ELO 系统配置
    
    定义 ELO 计算的各项参数。
    
    Attributes:
        initial_elo: 初始 ELO 分数
        min_elo: 最低 ELO 分数
        max_elo: 最高 ELO 分数
        base_k: 基础 K 值
        new_player_k: 新玩家 K 值（更高，快速定位）
        new_player_games: 新玩家场次阈值
        high_elo_k: 高分段 K 值（较低，减少波动）
        high_elo_threshold: 高分段阈值
        low_elo_k: 低分段 K 值（可以稍高，帮助上升）
        low_elo_threshold: 低分段阈值
    """
    initial_elo: int = 1200
    min_elo: int = 100
    max_elo: int = 3000
    base_k: int = 32
    new_player_k: int = 50
    new_player_games: int = 20
    high_elo_k: int = 24
    high_elo_threshold: int = 2000
    low_elo_k: int = 40
    low_elo_threshold: int = 1000


# 默认配置
DEFAULT_ELO_CONFIG = EloConfig()


@dataclass
class PlayerElo:
    """
    玩家 ELO 数据
    
    存储玩家的 ELO 分数及相关统计。
    
    Attributes:
        player_id: 玩家ID
        current_elo: 当前 ELO 分数
        peak_elo: 历史最高 ELO
        total_games: 总场次
        ranked_games: 排位场次
        wins: 胜场
        losses: 败场
        draws: 平场
        win_streak: 当前连胜
        max_win_streak: 历史最高连胜
        lose_streak: 当前连败
        recent_results: 最近比赛结果（用于趋势分析）
    """
    player_id: str
    current_elo: int = 1200
    peak_elo: int = 1200
    total_games: int = 0
    ranked_games: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0
    win_streak: int = 0
    max_win_streak: int = 0
    lose_streak: int = 0
    recent_results: list[bool] = field(default_factory=list)  # True = win
    
    # 最近结果保留数量
    MAX_RECENT_RESULTS: int = 20
    
    def get_win_rate(self) -> float:
        """
        计算胜率
        
        Returns:
            胜率（0.0 - 1.0）
        """
        if self.total_games == 0:
            return 0.0
        return self.wins / self.total_games
    
    def get_ranked_win_rate(self) -> float:
        """
        计算排位胜率
        
        Returns:
            排位胜率（0.0 - 1.0）
        """
        if self.ranked_games == 0:
            return 0.0
        return self.wins / self.ranked_games
    
    def is_new_player(self, threshold: int = 20) -> bool:
        """
        判断是否为新玩家
        
        Args:
            threshold: 新玩家场次阈值
            
        Returns:
            是否为新玩家
        """
        return self.total_games < threshold
    
    def get_trend(self) -> str:
        """
        分析最近战绩趋势
        
        Returns:
            趋势描述：'rising' / 'falling' / 'stable'
        """
        if len(self.recent_results) < 5:
            return 'stable'
        
        # 分析最近10场
        recent = self.recent_results[-10:]
        wins = sum(recent)
        
        if wins >= 7:
            return 'rising'
        elif wins <= 3:
            return 'falling'
        else:
            return 'stable'
    
    def record_game(self, is_win: bool, is_draw: bool = False) -> None:
        """
        记录一局比赛结果
        
        Args:
            is_win: 是否获胜
            is_draw: 是否平局
        """
        self.total_games += 1
        self.ranked_games += 1
        
        if is_draw:
            self.draws += 1
            self.win_streak = 0
            self.lose_streak = 0
        elif is_win:
            self.wins += 1
            self.win_streak += 1
            self.lose_streak = 0
            if self.win_streak > self.max_win_streak:
                self.max_win_streak = self.win_streak
        else:
            self.losses += 1
            self.lose_streak += 1
            self.win_streak = 0
        
        # 更新最近结果
        self.recent_results.append(is_win or is_draw)
        if len(self.recent_results) > self.MAX_RECENT_RESULTS:
            self.recent_results.pop(0)
    
    def to_dict(self) -> dict[str, Any]:
        """序列化为字典"""
        return {
            "player_id": self.player_id,
            "current_elo": self.current_elo,
            "peak_elo": self.peak_elo,
            "total_games": self.total_games,
            "ranked_games": self.ranked_games,
            "wins": self.wins,
            "losses": self.losses,
            "draws": self.draws,
            "win_streak": self.win_streak,
            "max_win_streak": self.max_win_streak,
            "lose_streak": self.lose_streak,
            "recent_results": self.recent_results,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PlayerElo:
        """从字典反序列化"""
        return cls(
            player_id=data["player_id"],
            current_elo=data.get("current_elo", 1200),
            peak_elo=data.get("peak_elo", 1200),
            total_games=data.get("total_games", 0),
            ranked_games=data.get("ranked_games", 0),
            wins=data.get("wins", 0),
            losses=data.get("losses", 0),
            draws=data.get("draws", 0),
            win_streak=data.get("win_streak", 0),
            max_win_streak=data.get("max_win_streak", 0),
            lose_streak=data.get("lose_streak", 0),
            recent_results=data.get("recent_results", []),
        )
    
    @classmethod
    def create_new(cls, player_id: str, initial_elo: int = 1200) -> PlayerElo:
        """
        创建新玩家 ELO 数据
        
        Args:
            player_id: 玩家ID
            initial_elo: 初始 ELO 分数
            
        Returns:
            新玩家的 ELO 数据
        """
        return cls(
            player_id=player_id,
            current_elo=initial_elo,
            peak_elo=initial_elo,
        )


class EloCalculator:
    """
    ELO 计算器
    
    实现 ELO 分数计算的核心逻辑。
    """
    
    def __init__(self, config: Optional[EloConfig] = None):
        """
        初始化计算器
        
        Args:
            config: ELO 配置，默认使用 DEFAULT_ELO_CONFIG
        """
        self.config = config or DEFAULT_ELO_CONFIG
    
    def calculate_expected_score(self, player_elo: int, opponent_elo: int) -> float:
        """
        计算预期胜率
        
        使用标准 ELO 公式计算期望得分。
        
        E = 1 / (1 + 10^((Rb - Ra) / 400))
        
        Args:
            player_elo: 玩家 ELO
            opponent_elo: 对手 ELO
            
        Returns:
            预期胜率（0.0 - 1.0）
        """
        exponent = (opponent_elo - player_elo) / 400.0
        return 1.0 / (1.0 + math.pow(10, exponent))
    
    def get_dynamic_k(
        self,
        player_elo: PlayerElo,
        player_rating: Optional[PlayerRating] = None
    ) -> int:
        """
        获取动态 K 值
        
        根据玩家情况调整 K 值：
        - 新玩家使用更大的 K 值，快速定位真实水平
        - 高分段使用较小的 K 值，减少波动
        - 低分段可以适当提高 K 值
        
        Args:
            player_elo: 玩家 ELO 数据
            player_rating: 玩家段位数据（可选）
            
        Returns:
            动态调整后的 K 值
        """
        k = self.config.base_k
        
        # 新玩家使用高 K 值
        if player_elo.total_games < self.config.new_player_games:
            progress = player_elo.total_games / self.config.new_player_games
            # 线性过渡从 new_player_k 到 base_k
            k = int(self.config.new_player_k - 
                   (self.config.new_player_k - self.config.base_k) * progress)
        
        # 高分段降低 K 值
        elif player_elo.current_elo >= self.config.high_elo_threshold:
            # ELO 越高，K 值越低
            excess = player_elo.current_elo - self.config.high_elo_threshold
            reduction = min(16, excess // 50)  # 每高50分减少1，最多减少16
            k = self.config.high_elo_k - reduction
            k = max(16, k)  # 最低 K 值
        
        # 低分段可以稍微提高 K 值
        elif player_elo.current_elo <= self.config.low_elo_threshold:
            k = self.config.low_elo_k
        
        # 连胜/连败调整
        if player_elo.win_streak >= 5:
            # 连胜时增加 K 值，加速上升
            k = int(k * 1.1)
        elif player_elo.lose_streak >= 5:
            # 连败时也增加 K 值，加速下降到合适位置
            k = int(k * 1.1)
        
        return k
    
    def calculate_elo_change(
        self,
        player_elo: PlayerElo,
        opponent_elo: PlayerElo,
        score: float,  # 1 = 胜, 0 = 负, 0.5 = 平
        player_rating: Optional[PlayerRating] = None
    ) -> int:
        """
        计算 ELO 变化值
        
        使用公式：R' = R + K * (S - E)
        其中：
        - R' 是新分数
        - R 是当前分数
        - K 是 K 值
        - S 是实际得分（1/0/0.5）
        - E 是预期得分
        
        Args:
            player_elo: 玩家 ELO 数据
            opponent_elo: 对手 ELO 数据
            score: 实际得分（1=胜，0=负，0.5=平）
            player_rating: 玩家段位数据（可选）
            
        Returns:
            ELO 变化值（正数表示增加）
        """
        k = self.get_dynamic_k(player_elo, player_rating)
        expected = self.calculate_expected_score(
            player_elo.current_elo,
            opponent_elo.current_elo
        )
        change = k * (score - expected)
        return round(change)
    
    def update_elo(
        self,
        player_elo: PlayerElo,
        opponent_elo: PlayerElo,
        is_win: bool,
        is_draw: bool = False,
        player_rating: Optional[PlayerRating] = None
    ) -> dict[str, Any]:
        """
        更新玩家 ELO
        
        Args:
            player_elo: 玩家 ELO 数据
            opponent_elo: 对手 ELO 数据
            is_win: 是否获胜
            is_draw: 是否平局
            player_rating: 玩家段位数据
            
        Returns:
            包含更新信息的字典
        """
        old_elo = player_elo.current_elo
        
        # 计算实际得分
        if is_draw:
            score = 0.5
        elif is_win:
            score = 1.0
        else:
            score = 0.0
        
        # 计算 ELO 变化
        change = self.calculate_elo_change(
            player_elo, opponent_elo, score, player_rating
        )
        
        # 应用变化
        new_elo = player_elo.current_elo + change
        new_elo = max(self.config.min_elo, min(self.config.max_elo, new_elo))
        
        # 更新数据
        player_elo.current_elo = new_elo
        player_elo.record_game(is_win, is_draw)
        
        # 更新历史最高
        if new_elo > player_elo.peak_elo:
            player_elo.peak_elo = new_elo
        
        return {
            "old_elo": old_elo,
            "new_elo": new_elo,
            "change": new_elo - old_elo,
            "k_value": self.get_dynamic_k(player_elo, player_rating),
            "expected_score": self.calculate_expected_score(old_elo, opponent_elo.current_elo),
            "actual_score": score,
            "trend": player_elo.get_trend(),
        }
    
    def batch_update(
        self,
        results: list[tuple[PlayerElo, PlayerElo, float]]
    ) -> list[dict[str, Any]]:
        """
        批量更新 ELO
        
        用于处理多人的比赛结果（如自走棋的前4/后4名）。
        
        Args:
            results: 结果列表，每个元素是 (玩家, 对手, 得分)
            
        Returns:
            更新结果列表
        """
        updates = []
        for player_elo, opponent_elo, score in results:
            is_win = score > 0.5
            is_draw = score == 0.5
            update = self.update_elo(player_elo, opponent_elo, is_win, is_draw)
            updates.append(update)
        return updates


class EloBasedRatingUpdater:
    """
    基于 ELO 的段位更新器
    
    根据 ELO 变化同步更新玩家段位。
    """
    
    def __init__(self, calculator: Optional[EloCalculator] = None):
        """
        初始化更新器
        
        Args:
            calculator: ELO 计算器
        """
        self.calculator = calculator or EloCalculator()
    
    def update_rating_from_elo(
        self,
        player_elo: PlayerElo,
        player_rating: PlayerRating,
        elo_change: int
    ) -> dict[str, Any]:
        """
        根据 ELO 变化更新段位
        
        将 ELO 变换转换为星级变化。
        
        Args:
            player_elo: 玩家 ELO 数据
            player_rating: 玩家段位数据
            elo_change: ELO 变化值
            
        Returns:
            段位更新结果
        """
        # ELO 变化转换为星级
        # 简单映射：每 25 ELO = 1 星
        star_change = elo_change // 25
        
        if star_change > 0:
            # 增加（可能晋级）
            result = player_rating.add_stars(star_change)
            result["elo_change"] = elo_change
        elif star_change < 0:
            # 减少（可能降级）
            result = player_rating.remove_stars(abs(star_change))
            result["elo_change"] = elo_change
        else:
            # ELO 变化不足以改变星级
            result = {
                "old_tier": player_rating.tier.get_display_name(),
                "new_tier": player_rating.tier.get_display_name(),
                "stars_change": 0,
                "elo_change": elo_change,
                "no_star_change": True,
            }
        
        # 根据当前 ELO 同步段位（确保一致性）
        expected_tier = SeasonManager.get_tier_from_elo(player_elo.current_elo)
        if expected_tier != player_rating.tier:
            # ELO 与段位不一致，需要同步
            player_rating.tier = expected_tier
            player_rating.stars = SeasonManager.get_stars_from_elo(
                player_elo.current_elo, expected_tier
            )
            result["tier_synced"] = True
            result["synced_tier"] = expected_tier.get_display_name()
        
        return result
    
    def process_game_result(
        self,
        player_elo: PlayerElo,
        opponent_elo: PlayerElo,
        player_rating: PlayerRating,
        is_win: bool,
        is_draw: bool = False,
        placement: int = 0  # 排名（1-8），用于自走棋
    ) -> dict[str, Any]:
        """
        处理一局游戏结果
        
        综合更新 ELO 和段位。
        
        Args:
            player_elo: 玩家 ELO 数据
            opponent_elo: 对手 ELO 数据
            player_rating: 玩家段位数据
            is_win: 是否获胜
            is_draw: 是否平局
            placement: 排名（自走棋模式）
            
        Returns:
            完整的更新结果
        """
        # 更新 ELO
        elo_result = self.calculator.update_elo(
            player_elo, opponent_elo, is_win, is_draw, player_rating
        )
        
        # 更新段位
        rating_result = self.update_rating_from_elo(
            player_elo, player_rating, elo_result["change"]
        )
        
        # 记录段位统计
        player_rating.record_game(is_win)
        
        return {
            "elo": elo_result,
            "rating": rating_result,
            "placement": placement,
            "is_win": is_win,
        }


def get_elo_tier_range(tier: Tier) -> tuple[int, int]:
    """
    获取段位对应的 ELO 范围
    
    Args:
        tier: 段位
        
    Returns:
        (最低ELO, 最高ELO)
    """
    ranges = {
        Tier.BRONZE: (100, 1200),
        Tier.SILVER: (1200, 1400),
        Tier.GOLD: (1400, 1600),
        Tier.PLATINUM: (1600, 1800),
        Tier.DIAMOND: (1800, 2000),
        Tier.MASTER: (2000, 2200),
        Tier.KING: (2200, 3000),
    }
    return ranges.get(tier, (100, 1200))


def compare_elo(elo_a: int, elo_b: int) -> float:
    """
    比较两个 ELO 分数，返回实力差距描述
    
    Args:
        elo_a: 玩家A的 ELO
        elo_b: 玩家B的 ELO
        
    Returns:
        差距描述 (-1 到 1)
    """
    diff = elo_a - elo_b
    # 标准化到 -1 到 1
    normalized = diff / 400.0
    return max(-1.0, min(1.0, normalized))
