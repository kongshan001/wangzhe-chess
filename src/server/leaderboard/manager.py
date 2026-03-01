"""
王者之奕 - 排行榜管理器

本模块提供排行榜系统的管理功能：
- LeaderboardManager: 排行榜管理器类
- 更新排行榜数据
- 获取排行榜列表
- 按不同类型查询（段位/胜率/吃鸡/伤害/财富）
- 周/月/赛季榜切换
- 发放排行榜奖励
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from .models import (
    LeaderboardData,
    LeaderboardEntry,
    LeaderboardPeriod,
    LeaderboardReward,
    LeaderboardType,
    PlayerRankInfo,
)

logger = logging.getLogger(__name__)


class LeaderboardManager:
    """
    排行榜管理器

    负责管理所有排行榜相关的操作：
    - 排行榜数据更新
    - 排行榜查询
    - 排行榜奖励发放
    - 周期管理

    Attributes:
        entries: 排行榜数据缓存 (type_period -> {player_id -> data})
        rewards: 排行榜奖励配置
        player_ranks: 玩家排名缓存
    """

    # 默认奖励配置
    DEFAULT_REWARDS: list[LeaderboardReward] = [
        # 第1名
        LeaderboardReward(
            rank_start=1,
            rank_end=1,
            gold=5000,
            exp=10000,
            title="荣耀王者",
            avatar_frame="rank_1_frame",
        ),
        # 第2-3名
        LeaderboardReward(
            rank_start=2,
            rank_end=3,
            gold=3000,
            exp=6000,
            title="最强王者",
            avatar_frame="rank_2_3_frame",
        ),
        # 第4-10名
        LeaderboardReward(
            rank_start=4,
            rank_end=10,
            gold=2000,
            exp=4000,
            title="至尊王者",
            avatar_frame="rank_4_10_frame",
        ),
        # 第11-50名
        LeaderboardReward(rank_start=11, rank_end=50, gold=1000, exp=2000),
        # 第51-100名
        LeaderboardReward(rank_start=51, rank_end=100, gold=500, exp=1000),
    ]

    # 每页默认大小
    DEFAULT_PAGE_SIZE = 50
    # 最大每页大小
    MAX_PAGE_SIZE = 100

    def __init__(self) -> None:
        """初始化排行榜管理器"""
        # 排行榜数据缓存: f"{type}_{period}" -> {player_id -> entry_dict}
        self._entries: dict[str, dict[str, dict[str, Any]]] = {}
        # 排行榜更新时间
        self._updated_at: dict[str, datetime] = {}
        # 奖励配置
        self._rewards: dict[str, list[LeaderboardReward]] = {}
        # 玩家已领取奖励记录: f"{type}_{period}_{player_id}" -> True
        self._claimed_rewards: dict[str, bool] = {}
        # 玩家最佳排名记录
        self._best_ranks: dict[str, int] = {}
        # 上一次排名（用于计算变化）
        self._prev_ranks: dict[str, int] = {}

        # 初始化默认奖励
        for lb_type in LeaderboardType:
            key = f"{lb_type.value}_weekly"
            self._rewards[key] = self.DEFAULT_REWARDS.copy()

        logger.info("LeaderboardManager initialized")

    def _get_cache_key(
        self,
        leaderboard_type: LeaderboardType,
        period: LeaderboardPeriod,
    ) -> str:
        """获取缓存键"""
        return f"{leaderboard_type.value}_{period.value}"

    def _get_period_range(
        self,
        period: LeaderboardPeriod,
    ) -> tuple[datetime, datetime]:
        """
        获取周期时间范围

        Args:
            period: 排行榜周期

        Returns:
            (开始时间, 结束时间)
        """
        now = datetime.now()

        if period == LeaderboardPeriod.WEEKLY:
            # 本周一到周日
            start = now - timedelta(days=now.weekday())
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=7)
        elif period == LeaderboardPeriod.MONTHLY:
            # 本月1日到月末
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if now.month == 12:
                end = start.replace(year=now.year + 1, month=1)
            else:
                end = start.replace(month=now.month + 1)
        else:  # SEASON
            # 赛季暂定为3个月
            season_month = ((now.month - 1) // 3) * 3 + 1
            start = now.replace(
                month=season_month, day=1, hour=0, minute=0, second=0, microsecond=0
            )
            end = start.replace(month=season_month + 3)

        return start, end

    def update_player_data(
        self,
        player_id: str,
        nickname: str,
        avatar: str,
        tier: str,
        stars: int,
        tier_score: int,
        win_count: int,
        total_count: int,
        first_place_count: int,
        max_damage: int,
        total_gold: int,
        extra_data: dict[str, Any] | None = None,
    ) -> None:
        """
        更新玩家排行榜数据

        实时更新玩家在各个排行榜的数据。

        Args:
            player_id: 玩家ID
            nickname: 玩家昵称
            avatar: 玩家头像
            tier: 段位
            stars: 星数
            tier_score: 段位积分
            win_count: 胜利场数
            total_count: 总场数
            first_place_count: 第一名次数
            max_damage: 单局最高伤害
            total_gold: 累计金币
            extra_data: 额外数据
        """
        # 计算胜率
        win_rate = (win_count / total_count * 100) if total_count > 0 else 0

        # 更新各类型排行榜
        updates = {
            LeaderboardType.TIER: tier_score,
            LeaderboardType.WIN_RATE: win_rate,
            LeaderboardType.FIRST_PLACE: first_place_count,
            LeaderboardType.DAMAGE: max_damage,
            LeaderboardType.WEALTH: total_gold,
        }

        for lb_type, score in updates.items():
            # 更新所有周期
            for period in LeaderboardPeriod:
                key = self._get_cache_key(lb_type, period)

                if key not in self._entries:
                    self._entries[key] = {}

                entry_data = {
                    "player_id": player_id,
                    "nickname": nickname,
                    "avatar": avatar,
                    "tier": tier,
                    "stars": stars,
                    "score": score,
                    "extra_data": extra_data or {},
                }

                self._entries[key][player_id] = entry_data
                self._updated_at[key] = datetime.now()

        logger.debug(
            f"Updated leaderboard data for player {player_id}", extra={"player_id": player_id}
        )

    def get_leaderboard(
        self,
        leaderboard_type: LeaderboardType,
        period: LeaderboardPeriod,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> LeaderboardData:
        """
        获取排行榜数据

        Args:
            leaderboard_type: 排行榜类型
            period: 排行榜周期
            page: 页码（从1开始）
            page_size: 每页大小

        Returns:
            排行榜数据
        """
        key = self._get_cache_key(leaderboard_type, period)
        page_size = min(page_size, self.MAX_PAGE_SIZE)

        # 获取所有条目并按分数排序
        all_entries = list(self._entries.get(key, {}).values())
        all_entries.sort(key=lambda x: x.get("score", 0), reverse=True)

        total_count = len(all_entries)

        # 分页
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_entries = all_entries[start_idx:end_idx]

        # 构建条目列表
        entries = []
        for idx, entry_data in enumerate(page_entries, start=start_idx + 1):
            entry = LeaderboardEntry(
                player_id=entry_data["player_id"],
                nickname=entry_data.get("nickname", ""),
                avatar=entry_data.get("avatar", ""),
                rank=idx,
                score=entry_data.get("score", 0),
                tier=entry_data.get("tier", "bronze"),
                stars=entry_data.get("stars", 0),
                extra_data=entry_data.get("extra_data", {}),
            )
            entries.append(entry)

        # 获取周期时间范围
        period_start, period_end = self._get_period_range(period)

        return LeaderboardData(
            leaderboard_type=leaderboard_type,
            period=period,
            entries=entries,
            total_count=total_count,
            page=page,
            page_size=page_size,
            updated_at=self._updated_at.get(key),
            period_start=period_start,
            period_end=period_end,
        )

    def get_player_rank(
        self,
        player_id: str,
        leaderboard_type: LeaderboardType,
        period: LeaderboardPeriod,
    ) -> PlayerRankInfo:
        """
        获取玩家排名信息

        Args:
            player_id: 玩家ID
            leaderboard_type: 排行榜类型
            period: 排行榜周期

        Returns:
            玩家排名信息
        """
        key = self._get_cache_key(leaderboard_type, period)

        # 获取所有条目并排序
        all_entries = list(self._entries.get(key, {}).values())
        all_entries.sort(key=lambda x: x.get("score", 0), reverse=True)

        total_count = len(all_entries)
        rank = 0
        score = 0.0
        percentile = 100.0

        # 查找玩家排名
        player_entry = self._entries.get(key, {}).get(player_id)
        if player_entry:
            score = player_entry.get("score", 0)
            for idx, entry in enumerate(all_entries, start=1):
                if entry["player_id"] == player_id:
                    rank = idx
                    percentile = (rank / total_count * 100) if total_count > 0 else 100.0
                    break

        # 获取历史排名变化
        prev_key = f"{key}_{player_id}"
        prev_rank = self._prev_ranks.get(prev_key, 0)
        history_rank = prev_rank - rank if prev_rank > 0 and rank > 0 else 0

        # 获取最佳排名
        best_key = f"{key}_best"
        best_rank = self._best_ranks.get(best_key, 0)
        if rank > 0 and (best_rank == 0 or rank < best_rank):
            best_rank = rank
            self._best_ranks[best_key] = best_rank

        # 检查是否已领取奖励
        claim_key = f"{key}_{player_id}"
        rewards_claimed = self._claimed_rewards.get(claim_key, False)

        return PlayerRankInfo(
            player_id=player_id,
            leaderboard_type=leaderboard_type,
            period=period,
            rank=rank,
            score=score,
            total_players=total_count,
            percentile=percentile,
            history_rank=history_rank,
            rewards_claimed=rewards_claimed,
            best_rank=best_rank,
        )

    def get_player_all_ranks(
        self,
        player_id: str,
    ) -> dict[str, PlayerRankInfo]:
        """
        获取玩家在所有排行榜的排名

        Args:
            player_id: 玩家ID

        Returns:
            排行榜类型周期 -> 排名信息
        """
        result = {}

        for lb_type in LeaderboardType:
            for period in LeaderboardPeriod:
                key = f"{lb_type.value}_{period.value}"
                result[key] = self.get_player_rank(player_id, lb_type, period)

        return result

    def get_leaderboard_list(
        self,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> dict[str, Any]:
        """
        获取所有排行榜概览

        Args:
            page: 页码
            page_size: 每页大小

        Returns:
            排行榜列表概览
        """
        leaderboards = []

        for lb_type in LeaderboardType:
            for period in LeaderboardPeriod:
                key = self._get_cache_key(lb_type, period)
                entries = self._entries.get(key, {})

                # 获取前三名
                sorted_entries = sorted(
                    entries.values(), key=lambda x: x.get("score", 0), reverse=True
                )[:3]

                top_players = [
                    {
                        "player_id": e["player_id"],
                        "nickname": e.get("nickname", ""),
                        "avatar": e.get("avatar", ""),
                        "score": e.get("score", 0),
                    }
                    for e in sorted_entries
                ]

                leaderboards.append(
                    {
                        "type": lb_type.value,
                        "type_name": lb_type.display_name,
                        "period": period.value,
                        "period_name": period.display_name,
                        "total_count": len(entries),
                        "top_players": top_players,
                        "updated_at": self._updated_at.get(key).isoformat()
                        if self._updated_at.get(key)
                        else None,
                    }
                )

        return {
            "leaderboards": leaderboards,
            "page": page,
            "page_size": page_size,
            "total_count": len(leaderboards),
        }

    def set_rewards(
        self,
        leaderboard_type: LeaderboardType,
        period: LeaderboardPeriod,
        rewards: list[LeaderboardReward],
    ) -> None:
        """
        设置排行榜奖励配置

        Args:
            leaderboard_type: 排行榜类型
            period: 排行榜周期
            rewards: 奖励列表
        """
        key = self._get_cache_key(leaderboard_type, period)
        self._rewards[key] = rewards
        logger.info(f"Set rewards for {key}: {len(rewards)} reward tiers")

    def get_rewards(
        self,
        leaderboard_type: LeaderboardType,
        period: LeaderboardPeriod,
    ) -> list[LeaderboardReward]:
        """
        获取排行榜奖励配置

        Args:
            leaderboard_type: 排行榜类型
            period: 排行榜周期

        Returns:
            奖励列表
        """
        key = self._get_cache_key(leaderboard_type, period)
        return self._rewards.get(key, self.DEFAULT_REWARDS.copy())

    def get_player_reward(
        self,
        player_id: str,
        leaderboard_type: LeaderboardType,
        period: LeaderboardPeriod,
    ) -> LeaderboardReward | None:
        """
        获取玩家可领取的奖励

        Args:
            player_id: 玩家ID
            leaderboard_type: 排行榜类型
            period: 排行榜周期

        Returns:
            奖励内容，无可领取返回None
        """
        # 检查是否已领取
        claim_key = f"{self._get_cache_key(leaderboard_type, period)}_{player_id}"
        if self._claimed_rewards.get(claim_key, False):
            return None

        # 获取玩家排名
        rank_info = self.get_player_rank(player_id, leaderboard_type, period)
        if not rank_info.is_ranked:
            return None

        # 查找对应奖励
        rewards = self.get_rewards(leaderboard_type, period)
        for reward in rewards:
            if reward.contains_rank(rank_info.rank):
                return reward

        return None

    def claim_reward(
        self,
        player_id: str,
        leaderboard_type: LeaderboardType,
        period: LeaderboardPeriod,
    ) -> LeaderboardReward | None:
        """
        领取排行榜奖励

        Args:
            player_id: 玩家ID
            leaderboard_type: 排行榜类型
            period: 排行榜周期

        Returns:
            奖励内容，无法领取返回None
        """
        reward = self.get_player_reward(player_id, leaderboard_type, period)
        if reward is None:
            return None

        # 标记已领取
        claim_key = f"{self._get_cache_key(leaderboard_type, period)}_{player_id}"
        self._claimed_rewards[claim_key] = True

        logger.info(
            f"Player {player_id} claimed reward for {leaderboard_type.value} {period.value}"
        )

        return reward

    def clear_period(
        self,
        period: LeaderboardPeriod,
    ) -> None:
        """
        清除指定周期的排行榜数据

        用于周期结束时重置排行榜。

        Args:
            period: 排行榜周期
        """
        for lb_type in LeaderboardType:
            key = self._get_cache_key(lb_type, period)
            self._entries[key] = {}
            self._updated_at[key] = None

        logger.info(f"Cleared leaderboard data for period: {period.value}")

    def snapshot_current_ranks(self) -> None:
        """
        快照当前排名

        在周期结束前调用，用于计算排名变化。
        """
        for lb_type in LeaderboardType:
            for period in LeaderboardPeriod:
                key = self._get_cache_key(lb_type, period)
                entries = self._entries.get(key, {})

                sorted_entries = sorted(
                    entries.values(), key=lambda x: x.get("score", 0), reverse=True
                )

                for idx, entry in enumerate(sorted_entries, start=1):
                    prev_key = f"{key}_{entry['player_id']}"
                    self._prev_ranks[prev_key] = idx

        logger.info("Snapshot current ranks completed")

    def remove_player(
        self,
        player_id: str,
    ) -> None:
        """
        从排行榜中移除玩家

        Args:
            player_id: 玩家ID
        """
        for lb_type in LeaderboardType:
            for period in LeaderboardPeriod:
                key = self._get_cache_key(lb_type, period)
                if key in self._entries and player_id in self._entries[key]:
                    del self._entries[key][player_id]

        logger.info(f"Removed player {player_id} from all leaderboards")


# 全局单例
_leaderboard_manager: LeaderboardManager | None = None


def get_leaderboard_manager() -> LeaderboardManager:
    """
    获取排行榜管理器单例

    Returns:
        排行榜管理器实例
    """
    global _leaderboard_manager
    if _leaderboard_manager is None:
        _leaderboard_manager = LeaderboardManager()
    return _leaderboard_manager
