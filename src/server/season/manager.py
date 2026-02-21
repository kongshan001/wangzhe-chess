"""
王者之奕 - 赛季管理器

本模块提供赛季系统的管理功能：
- SeasonManager: 赛季管理器类
- 获取当前赛季
- 计算赛季奖励
- 段位软重置逻辑
- 通行证管理
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .models import Season, SeasonReward, PlayerSeasonData, SeasonStatus, Tier

logger = logging.getLogger(__name__)


class SeasonManager:
    """
    赛季管理器
    
    负责管理所有赛季相关的操作：
    - 赛季创建和查询
    - 赛季奖励计算
    - 段位软重置
    - 通行证经验计算
    
    Attributes:
        seasons: 所有赛季缓存 (season_id -> Season)
        player_data: 玩家赛季数据缓存 (player_id + season_id -> PlayerSeasonData)
        current_season_id: 当前活跃赛季ID
    """
    
    DEFAULT_SEASON_DURATION_DAYS = 28
    PASS_EXP_PER_LEVEL = 100
    
    def __init__(self):
        """初始化赛季管理器"""
        self.seasons: Dict[str, Season] = {}
        self.player_data: Dict[str, PlayerSeasonData] = {}  # key: f"{player_id}_{season_id}"
        self.current_season_id: Optional[str] = None
        
        # 初始化默认赛季奖励配置
        self._init_default_rewards()
        
        logger.info("SeasonManager initialized")
    
    def _init_default_rewards(self) -> None:
        """初始化默认赛季奖励配置"""
        self.default_rewards: Dict[int, SeasonReward] = {
            Tier.BRONZE.value: SeasonReward(
                tier=Tier.BRONZE,
                gold=500,
                exp=1000,
            ),
            Tier.SILVER.value: SeasonReward(
                tier=Tier.SILVER,
                gold=800,
                exp=1500,
                avatar_frame="silver_frame_s1",
            ),
            Tier.GOLD.value: SeasonReward(
                tier=Tier.GOLD,
                gold=1200,
                exp=2000,
                avatar_frame="gold_frame_s1",
                title="黄金战士",
            ),
            Tier.PLATINUM.value: SeasonReward(
                tier=Tier.PLATINUM,
                gold=1800,
                exp=3000,
                avatar_frame="platinum_frame_s1",
                title="铂金斗士",
                items=[{"item_id": "rare_chest", "quantity": 1}],
            ),
            Tier.DIAMOND.value: SeasonReward(
                tier=Tier.DIAMOND,
                gold=2500,
                exp=4500,
                avatar_frame="diamond_frame_s1",
                skin="season_skin_diamond_s1",
                title="钻石精英",
                items=[{"item_id": "epic_chest", "quantity": 1}],
            ),
            Tier.MASTER.value: SeasonReward(
                tier=Tier.MASTER,
                gold=3500,
                exp=6000,
                avatar_frame="master_frame_s1",
                skin="season_skin_master_s1",
                title="大师",
                items=[{"item_id": "epic_chest", "quantity": 2}],
            ),
            Tier.GRANDMASTER.value: SeasonReward(
                tier=Tier.GRANDMASTER,
                gold=5000,
                exp=8000,
                avatar_frame="grandmaster_frame_s1",
                skin="season_skin_gm_s1",
                title="宗师",
                items=[{"item_id": "legendary_chest", "quantity": 1}],
            ),
            Tier.KING.value: SeasonReward(
                tier=Tier.KING,
                gold=8000,
                exp=12000,
                avatar_frame="king_frame_s1",
                skin="season_skin_king_s1",
                title="最强王者",
                items=[
                    {"item_id": "legendary_chest", "quantity": 2},
                    {"item_id": "exclusive_emote", "quantity": 1},
                ],
            ),
        }
    
    def create_season(
        self,
        season_id: str,
        name: str,
        start_time: Optional[datetime] = None,
        duration_days: int = DEFAULT_SEASON_DURATION_DAYS,
        description: str = "",
        rewards: Optional[Dict[int, SeasonReward]] = None,
    ) -> Season:
        """
        创建新赛季
        
        Args:
            season_id: 赛季ID
            name: 赛季名称
            start_time: 开始时间（默认当前时间）
            duration_days: 持续天数
            description: 赛季描述
            rewards: 自定义奖励配置
            
        Returns:
            创建的赛季对象
        """
        if start_time is None:
            start_time = datetime.now()
        
        end_time = start_time + timedelta(days=duration_days)
        
        # 使用默认奖励或自定义奖励
        season_rewards = rewards if rewards else self.default_rewards.copy()
        
        season = Season(
            season_id=season_id,
            name=name,
            start_time=start_time,
            end_time=end_time,
            is_active=True,
            description=description,
            rewards=season_rewards,
        )
        
        self.seasons[season_id] = season
        
        # 如果是第一个赛季或没有当前赛季，设为当前赛季
        if self.current_season_id is None:
            self.current_season_id = season_id
        
        logger.info(f"Created season: {season_id} ({name}), duration: {duration_days} days")
        
        return season
    
    def get_season(self, season_id: str) -> Optional[Season]:
        """
        获取指定赛季
        
        Args:
            season_id: 赛季ID
            
        Returns:
            赛季对象，不存在返回None
        """
        return self.seasons.get(season_id)
    
    def get_current_season(self) -> Optional[Season]:
        """
        获取当前活跃赛季
        
        Returns:
            当前赛季对象，不存在返回None
        """
        if self.current_season_id is None:
            return None
        return self.seasons.get(self.current_season_id)
    
    def set_current_season(self, season_id: str) -> bool:
        """
        设置当前赛季
        
        Args:
            season_id: 赛季ID
            
        Returns:
            是否设置成功
        """
        if season_id not in self.seasons:
            logger.warning(f"Season not found: {season_id}")
            return False
        
        # 将之前的赛季设为非活跃
        if self.current_season_id and self.current_season_id in self.seasons:
            self.seasons[self.current_season_id].is_active = False
        
        self.current_season_id = season_id
        self.seasons[season_id].is_active = True
        
        logger.info(f"Set current season to: {season_id}")
        return True
    
    def end_season(self, season_id: str) -> bool:
        """
        结束指定赛季
        
        Args:
            season_id: 赛季ID
            
        Returns:
            是否结束成功
        """
        season = self.seasons.get(season_id)
        if not season:
            logger.warning(f"Season not found: {season_id}")
            return False
        
        season.is_active = False
        season.end_time = datetime.now()
        
        if self.current_season_id == season_id:
            self.current_season_id = None
        
        logger.info(f"Ended season: {season_id}")
        return True
    
    def calculate_season_reward(
        self,
        player_id: str,
        season_id: Optional[str] = None,
    ) -> Optional[SeasonReward]:
        """
        计算玩家赛季奖励
        
        Args:
            player_id: 玩家ID
            season_id: 赛季ID（默认当前赛季）
            
        Returns:
            赛季奖励，无法计算返回None
        """
        if season_id is None:
            season_id = self.current_season_id
        
        if not season_id:
            logger.warning("No current season to calculate reward")
            return None
        
        season = self.seasons.get(season_id)
        if not season:
            logger.warning(f"Season not found: {season_id}")
            return None
        
        player_data = self.get_player_season_data(player_id, season_id)
        if not player_data:
            logger.warning(f"Player season data not found: {player_id}")
            return None
        
        # 根据最终段位获取奖励
        reward = season.get_reward_for_tier(player_data.final_tier)
        
        if reward:
            logger.info(
                f"Calculated season reward for player {player_id}: "
                f"tier={player_data.final_tier.display_name}, gold={reward.gold}"
            )
        
        return reward
    
    def soft_reset_tier(self, current_tier: Tier) -> Tier:
        """
        段位软重置
        
        新赛季初始段位 = (上赛季段位 + 青铜) / 2，向上取整
        
        Args:
            current_tier: 当前段位
            
        Returns:
            重置后的段位
        """
        # 青铜段位保持不变
        if current_tier == Tier.BRONZE:
            return Tier.BRONZE
        
        # 计算软重置后的段位
        # 公式: new_tier = (current + 1) / 2，向上取整
        import math
        new_tier_value = math.ceil((current_tier.value + Tier.BRONZE.value) / 2)
        new_tier = Tier(new_tier_value)
        
        logger.info(
            f"Soft reset tier: {current_tier.display_name} -> {new_tier.display_name}"
        )
        
        return new_tier
    
    def start_new_season_for_player(
        self,
        player_id: str,
        new_season_id: str,
    ) -> PlayerSeasonData:
        """
        为玩家开始新赛季
        
        执行段位软重置，创建新的赛季数据
        
        Args:
            player_id: 玩家ID
            new_season_id: 新赛季ID
            
        Returns:
            新赛季的玩家数据
        """
        # 获取上赛季数据
        old_season = self.get_current_season()
        old_season_id = old_season.season_id if old_season else None
        
        old_data = None
        if old_season_id:
            old_data = self.get_player_season_data(player_id, old_season_id)
        
        # 计算软重置后的段位
        if old_data:
            reset_tier = self.soft_reset_tier(old_data.final_tier)
        else:
            reset_tier = Tier.BRONZE
        
        # 创建新赛季数据
        new_data = PlayerSeasonData(
            player_id=player_id,
            season_id=new_season_id,
            highest_tier=reset_tier,
            final_tier=reset_tier,
        )
        
        # 保存新赛季数据
        key = f"{player_id}_{new_season_id}"
        self.player_data[key] = new_data
        
        logger.info(
            f"Started new season for player {player_id}: "
            f"season={new_season_id}, initial_tier={reset_tier.display_name}"
        )
        
        return new_data
    
    def get_player_season_data(
        self,
        player_id: str,
        season_id: Optional[str] = None,
    ) -> Optional[PlayerSeasonData]:
        """
        获取玩家赛季数据
        
        Args:
            player_id: 玩家ID
            season_id: 赛季ID（默认当前赛季）
            
        Returns:
            玩家赛季数据，不存在返回None
        """
        if season_id is None:
            season_id = self.current_season_id
        
        if not season_id:
            return None
        
        key = f"{player_id}_{season_id}"
        return self.player_data.get(key)
    
    def get_or_create_player_season_data(
        self,
        player_id: str,
        season_id: Optional[str] = None,
    ) -> PlayerSeasonData:
        """
        获取或创建玩家赛季数据
        
        Args:
            player_id: 玩家ID
            season_id: 赛季ID（默认当前赛季）
            
        Returns:
            玩家赛季数据
        """
        if season_id is None:
            season_id = self.current_season_id
        
        if not season_id:
            raise ValueError("No current season")
        
        data = self.get_player_season_data(player_id, season_id)
        if data is None:
            data = PlayerSeasonData(
                player_id=player_id,
                season_id=season_id,
            )
            key = f"{player_id}_{season_id}"
            self.player_data[key] = data
        
        return data
    
    def record_game_result(
        self,
        player_id: str,
        rank: int,
        season_id: Optional[str] = None,
    ) -> PlayerSeasonData:
        """
        记录对局结果
        
        Args:
            player_id: 玩家ID
            rank: 排名 (1-8)
            season_id: 赛季ID（默认当前赛季）
            
        Returns:
            更新后的玩家赛季数据
        """
        data = self.get_or_create_player_season_data(player_id, season_id)
        data.add_game_result(rank)
        
        return data
    
    def add_pass_exp(
        self,
        player_id: str,
        exp: int,
        season_id: Optional[str] = None,
    ) -> int:
        """
        添加通行证经验
        
        Args:
            player_id: 玩家ID
            exp: 获得的经验值
            season_id: 赛季ID（默认当前赛季）
            
        Returns:
            升级后的等级
        """
        data = self.get_or_create_player_season_data(player_id, season_id)
        old_level = data.pass_level
        new_level = data.add_pass_exp(exp)
        
        if new_level > old_level:
            logger.info(
                f"Player {player_id} pass level up: {old_level} -> {new_level}"
            )
        
        return new_level
    
    def get_pass_rewards(
        self,
        player_id: str,
        level: int,
        season_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        获取通行证等级奖励
        
        Args:
            player_id: 玩家ID
            level: 等级
            season_id: 赛季ID（默认当前赛季）
            
        Returns:
            包含免费和付费奖励的字典
        """
        if season_id is None:
            season_id = self.current_season_id
        
        season = self.seasons.get(season_id) if season_id else None
        
        result = {
            "free": None,
            "premium": None,
        }
        
        if not season:
            return result
        
        # 获取免费奖励
        if level <= len(season.pass_free_rewards):
            result["free"] = season.pass_free_rewards[level - 1]
        
        # 获取付费奖励
        player_data = self.get_player_season_data(player_id, season_id)
        if player_data and player_data.pass_premium:
            if level <= len(season.pass_premium_rewards):
                result["premium"] = season.pass_premium_rewards[level - 1]
        
        return result
    
    def get_all_seasons(self, include_ended: bool = True) -> List[Season]:
        """
        获取所有赛季列表
        
        Args:
            include_ended: 是否包含已结束的赛季
            
        Returns:
            赛季列表
        """
        seasons = list(self.seasons.values())
        if not include_ended:
            seasons = [s for s in seasons if s.status != SeasonStatus.ENDED]
        return sorted(seasons, key=lambda s: s.start_time, reverse=True)
    
    def get_season_ranking(
        self,
        season_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        获取赛季排行榜
        
        Args:
            season_id: 赛季ID（默认当前赛季）
            limit: 返回数量限制
            
        Returns:
            排行榜数据列表
        """
        if season_id is None:
            season_id = self.current_season_id
        
        if not season_id:
            return []
        
        # 筛选该赛季的玩家数据
        season_players = [
            data for key, data in self.player_data.items()
            if data.season_id == season_id
        ]
        
        # 按段位和前四率排序
        season_players.sort(
            key=lambda x: (x.final_tier.value, x.top4_rate),
            reverse=True
        )
        
        # 返回前limit名
        ranking = []
        for i, data in enumerate(season_players[:limit]):
            ranking.append({
                "rank": i + 1,
                "player_id": data.player_id,
                "tier": data.final_tier.value,
                "tier_name": data.final_tier.display_name,
                "highest_tier": data.highest_tier.value,
                "highest_tier_name": data.highest_tier.display_name,
                "total_games": data.total_games,
                "total_wins": data.total_wins,
                "top4_rate": data.top4_rate,
            })
        
        return ranking


# 全局单例
_season_manager: Optional[SeasonManager] = None


def get_season_manager() -> SeasonManager:
    """获取赛季管理器单例"""
    global _season_manager
    if _season_manager is None:
        _season_manager = SeasonManager()
    return _season_manager
