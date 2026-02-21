"""
王者之奕 - 成就管理器

本模块提供成就系统的管理功能：
- AchievementManager: 成就管理器类
- 检查成就进度
- 完成成就奖励
- 加载成就配置
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .models import (
    Achievement,
    AchievementCategory,
    AchievementRequirement,
    AchievementReward,
    AchievementTier,
    PlayerAchievement,
    RequirementType,
)

logger = logging.getLogger(__name__)


class AchievementManager:
    """
    成就管理器
    
    负责管理所有成就相关的操作：
    - 成就配置加载
    - 成就进度检查
    - 成就完成奖励发放
    - 成就统计查询
    
    Attributes:
        achievements: 所有成就配置 (achievement_id -> Achievement)
        player_achievements: 玩家成就数据 (player_id + achievement_id -> PlayerAchievement)
        config_path: 配置文件路径
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化成就管理器
        
        Args:
            config_path: 成就配置文件路径
        """
        self.achievements: Dict[str, Achievement] = {}
        self.player_achievements: Dict[str, PlayerAchievement] = {}  # key: f"{player_id}_{achievement_id}"
        self.config_path = config_path
        
        # 加载配置
        if config_path:
            self.load_config(config_path)
        else:
            self._init_default_achievements()
        
        logger.info(f"AchievementManager initialized with {len(self.achievements)} achievements")
    
    def _init_default_achievements(self) -> None:
        """初始化默认成就配置"""
        default_achievements = [
            # 收集成就
            Achievement(
                achievement_id="collect_all_1star",
                name="收集家·初",
                description="累计收集30个1星英雄",
                category=AchievementCategory.COLLECTION,
                tier=AchievementTier.BRONZE,
                requirement=AchievementRequirement(
                    type=RequirementType.COLLECT_1STAR_HEROES,
                    target=30,
                ),
                rewards=AchievementReward(gold=500, exp=1000),
                icon="achievement_collect_1",
            ),
            Achievement(
                achievement_id="collect_all_2star",
                name="收集家·进",
                description="累计收集20个2星英雄",
                category=AchievementCategory.COLLECTION,
                tier=AchievementTier.SILVER,
                requirement=AchievementRequirement(
                    type=RequirementType.COLLECT_2STAR_HEROES,
                    target=20,
                ),
                rewards=AchievementReward(gold=1000, exp=2000),
                icon="achievement_collect_2",
                prerequisite="collect_all_1star",
            ),
            Achievement(
                achievement_id="collect_all_3star",
                name="收集家·极",
                description="累计收集10个3星英雄",
                category=AchievementCategory.COLLECTION,
                tier=AchievementTier.GOLD,
                requirement=AchievementRequirement(
                    type=RequirementType.COLLECT_3STAR_HEROES,
                    target=10,
                ),
                rewards=AchievementReward(gold=2000, exp=4000, title="收藏大师"),
                icon="achievement_collect_3",
                prerequisite="collect_all_2star",
            ),
            Achievement(
                achievement_id="synergy_master",
                name="羁绊大师",
                description="激活所有羁绊至少一次",
                category=AchievementCategory.COLLECTION,
                tier=AchievementTier.SILVER,
                requirement=AchievementRequirement(
                    type=RequirementType.ACTIVATE_SYNERGIES,
                    target=16,  # 总羁绊数
                ),
                rewards=AchievementReward(gold=800, exp=1500, avatar_frame="synergy_master_frame"),
                icon="achievement_synergy",
            ),
            
            # 对局成就
            Achievement(
                achievement_id="win_100",
                name="百战勇士",
                description="累计获胜100场",
                category=AchievementCategory.BATTLE,
                tier=AchievementTier.BRONZE,
                requirement=AchievementRequirement(
                    type=RequirementType.WIN_GAMES,
                    target=100,
                ),
                rewards=AchievementReward(gold=1000, exp=2000),
                icon="achievement_win_100",
            ),
            Achievement(
                achievement_id="win_500",
                name="千胜将军",
                description="累计获胜500场",
                category=AchievementCategory.BATTLE,
                tier=AchievementTier.GOLD,
                requirement=AchievementRequirement(
                    type=RequirementType.WIN_GAMES,
                    target=500,
                ),
                rewards=AchievementReward(gold=5000, exp=10000, title="千胜将军"),
                icon="achievement_win_500",
                prerequisite="win_100",
            ),
            Achievement(
                achievement_id="streak_5",
                name="五连胜",
                description="单次达成5连胜",
                category=AchievementCategory.BATTLE,
                tier=AchievementTier.BRONZE,
                requirement=AchievementRequirement(
                    type=RequirementType.WIN_STREAK,
                    target=5,
                ),
                rewards=AchievementReward(gold=300, exp=500),
                icon="achievement_streak_5",
            ),
            Achievement(
                achievement_id="streak_10",
                name="十连胜",
                description="单次达成10连胜",
                category=AchievementCategory.BATTLE,
                tier=AchievementTier.GOLD,
                requirement=AchievementRequirement(
                    type=RequirementType.WIN_STREAK,
                    target=10,
                ),
                rewards=AchievementReward(gold=1000, exp=2000, title="连胜王者"),
                icon="achievement_streak_10",
                prerequisite="streak_5",
            ),
            Achievement(
                achievement_id="first_place_50",
                name="吃鸡达人",
                description="累计获得50次第一名",
                category=AchievementCategory.BATTLE,
                tier=AchievementTier.SILVER,
                requirement=AchievementRequirement(
                    type=RequirementType.FIRST_PLACE,
                    target=50,
                ),
                rewards=AchievementReward(gold=1500, exp=3000, avatar_frame="chicken_dinner_frame"),
                icon="achievement_first_50",
            ),
            
            # 战斗成就
            Achievement(
                achievement_id="damage_10000",
                name="伤害大师",
                description="单局造成10000点伤害",
                category=AchievementCategory.COMBAT,
                tier=AchievementTier.BRONZE,
                requirement=AchievementRequirement(
                    type=RequirementType.DEAL_DAMAGE,
                    target=10000,
                ),
                rewards=AchievementReward(gold=200, exp=400),
                icon="achievement_damage_10k",
            ),
            Achievement(
                achievement_id="damage_50000",
                name="伤害传说",
                description="单局造成50000点伤害",
                category=AchievementCategory.COMBAT,
                tier=AchievementTier.GOLD,
                requirement=AchievementRequirement(
                    type=RequirementType.DEAL_DAMAGE,
                    target=50000,
                ),
                rewards=AchievementReward(gold=1000, exp=2000, title="毁灭者"),
                icon="achievement_damage_50k",
                prerequisite="damage_10000",
            ),
            Achievement(
                achievement_id="perfect_win",
                name="完美胜利",
                description="零损失获胜（所有英雄存活）",
                category=AchievementCategory.COMBAT,
                tier=AchievementTier.SILVER,
                requirement=AchievementRequirement(
                    type=RequirementType.PERFECT_WIN,
                    target=1,
                ),
                rewards=AchievementReward(gold=500, exp=1000),
                icon="achievement_perfect",
            ),
            Achievement(
                achievement_id="comeback_king",
                name="逆袭之王",
                description="血量低于10时获得第一名",
                category=AchievementCategory.COMBAT,
                tier=AchievementTier.GOLD,
                requirement=AchievementRequirement(
                    type=RequirementType.LOW_HP_WIN,
                    target=1,
                    conditions={"hp_threshold": 10},
                ),
                rewards=AchievementReward(gold=800, exp=1500, title="逆袭之王"),
                icon="achievement_comeback",
            ),
            
            # 社交成就
            Achievement(
                achievement_id="friend_10",
                name="社交达人",
                description="添加10个好友",
                category=AchievementCategory.SOCIAL,
                tier=AchievementTier.BRONZE,
                requirement=AchievementRequirement(
                    type=RequirementType.ADD_FRIENDS,
                    target=10,
                ),
                rewards=AchievementReward(gold=200, exp=400),
                icon="achievement_friend_10",
            ),
            Achievement(
                achievement_id="team_50",
                name="团队玩家",
                description="组队进行50场对局",
                category=AchievementCategory.SOCIAL,
                tier=AchievementTier.SILVER,
                requirement=AchievementRequirement(
                    type=RequirementType.TEAM_PLAY,
                    target=50,
                ),
                rewards=AchievementReward(gold=500, exp=1000),
                icon="achievement_team_50",
            ),
        ]
        
        for achievement in default_achievements:
            self.achievements[achievement.achievement_id] = achievement
    
    def load_config(self, config_path: str) -> None:
        """
        从配置文件加载成就
        
        Args:
            config_path: 配置文件路径
        """
        path = Path(config_path)
        if not path.exists():
            logger.warning(f"Achievement config file not found: {config_path}")
            self._init_default_achievements()
            return
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            achievements_data = data.get("achievements", [])
            for achievement_data in achievements_data:
                achievement = Achievement.from_dict(achievement_data)
                self.achievements[achievement.achievement_id] = achievement
            
            logger.info(f"Loaded {len(self.achievements)} achievements from {config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load achievement config: {e}")
            self._init_default_achievements()
    
    def save_config(self, config_path: Optional[str] = None) -> None:
        """
        保存成就配置到文件
        
        Args:
            config_path: 配置文件路径（默认使用初始化时的路径）
        """
        path = Path(config_path or self.config_path)
        if not path:
            logger.warning("No config path specified for saving")
            return
        
        try:
            data = {
                "version": "1.0.0",
                "last_updated": datetime.now().isoformat(),
                "achievements": [a.to_dict() for a in self.achievements.values()],
            }
            
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved {len(self.achievements)} achievements to {path}")
            
        except Exception as e:
            logger.error(f"Failed to save achievement config: {e}")
    
    def get_achievement(self, achievement_id: str) -> Optional[Achievement]:
        """
        获取指定成就
        
        Args:
            achievement_id: 成就ID
            
        Returns:
            成就对象，不存在返回None
        """
        return self.achievements.get(achievement_id)
    
    def get_all_achievements(self) -> List[Achievement]:
        """
        获取所有成就列表
        
        Returns:
            成就列表
        """
        return list(self.achievements.values())
    
    def get_achievements_by_category(self, category: AchievementCategory) -> List[Achievement]:
        """
        获取指定类别的成就
        
        Args:
            category: 成就类别
            
        Returns:
            该类别的成就列表
        """
        return [a for a in self.achievements.values() if a.category == category]
    
    def get_achievements_by_tier(self, tier: AchievementTier) -> List[Achievement]:
        """
        获取指定等级的成就
        
        Args:
            tier: 成就等级
            
        Returns:
            该等级的成就列表
        """
        return [a for a in self.achievements.values() if a.tier == tier]
    
    def get_player_achievement(
        self,
        player_id: str,
        achievement_id: str,
    ) -> Optional[PlayerAchievement]:
        """
        获取玩家成就进度
        
        Args:
            player_id: 玩家ID
            achievement_id: 成就ID
            
        Returns:
            玩家成就数据，不存在返回None
        """
        key = f"{player_id}_{achievement_id}"
        return self.player_achievements.get(key)
    
    def get_or_create_player_achievement(
        self,
        player_id: str,
        achievement_id: str,
    ) -> PlayerAchievement:
        """
        获取或创建玩家成就进度
        
        Args:
            player_id: 玩家ID
            achievement_id: 成就ID
            
        Returns:
            玩家成就数据
        """
        key = f"{player_id}_{achievement_id}"
        if key not in self.player_achievements:
            self.player_achievements[key] = PlayerAchievement(
                player_id=player_id,
                achievement_id=achievement_id,
            )
        return self.player_achievements[key]
    
    def check_prerequisite(
        self,
        player_id: str,
        achievement: Achievement,
    ) -> bool:
        """
        检查前置成就是否完成
        
        Args:
            player_id: 玩家ID
            achievement: 成就对象
            
        Returns:
            是否满足前置条件
        """
        if not achievement.prerequisite:
            return True
        
        prereq = self.get_player_achievement(player_id, achievement.prerequisite)
        return prereq is not None and prereq.completed
    
    def update_progress(
        self,
        player_id: str,
        achievement_id: str,
        current_value: int,
        **kwargs,
    ) -> Optional[PlayerAchievement]:
        """
        更新成就进度
        
        Args:
            player_id: 玩家ID
            achievement_id: 成就ID
            current_value: 当前进度值
            **kwargs: 附加参数
            
        Returns:
            更新后的玩家成就数据，不满足前置条件返回None
        """
        achievement = self.get_achievement(achievement_id)
        if not achievement:
            logger.warning(f"Achievement not found: {achievement_id}")
            return None
        
        # 检查前置成就
        if not self.check_prerequisite(player_id, achievement):
            return None
        
        player_achievement = self.get_or_create_player_achievement(player_id, achievement_id)
        
        # 如果已完成，不再更新
        if player_achievement.completed:
            return player_achievement
        
        # 更新进度
        just_completed = player_achievement.update_progress(
            current_value,
            achievement.requirement.target,
        )
        
        if just_completed:
            logger.info(
                f"Player {player_id} completed achievement: {achievement.name}"
            )
        
        return player_achievement
    
    def check_and_update_by_type(
        self,
        player_id: str,
        requirement_type: RequirementType,
        value: int,
        **kwargs,
    ) -> List[PlayerAchievement]:
        """
        根据需求类型检查并更新所有相关成就
        
        Args:
            player_id: 玩家ID
            requirement_type: 需求类型
            value: 当前值
            **kwargs: 附加参数
            
        Returns:
            更新的玩家成就列表
        """
        updated = []
        
        for achievement in self.achievements.values():
            if achievement.requirement.type == requirement_type:
                result = self.update_progress(
                    player_id,
                    achievement.achievement_id,
                    value,
                    **kwargs,
                )
                if result:
                    updated.append(result)
        
        return updated
    
    def claim_reward(
        self,
        player_id: str,
        achievement_id: str,
    ) -> Optional[AchievementReward]:
        """
        领取成就奖励
        
        Args:
            player_id: 玩家ID
            achievement_id: 成就ID
            
        Returns:
            奖励内容，无法领取返回None
        """
        player_achievement = self.get_player_achievement(player_id, achievement_id)
        if not player_achievement or not player_achievement.is_claimable:
            return None
        
        achievement = self.get_achievement(achievement_id)
        if not achievement:
            return None
        
        if player_achievement.claim_reward():
            logger.info(
                f"Player {player_id} claimed reward for achievement: {achievement.name}"
            )
            return achievement.rewards
        
        return None
    
    def get_player_achievements(
        self,
        player_id: str,
        category: Optional[AchievementCategory] = None,
        completed_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        获取玩家所有成就进度
        
        Args:
            player_id: 玩家ID
            category: 筛选类别（可选）
            completed_only: 只返回已完成的
            
        Returns:
            成就进度列表
        """
        result = []
        
        for achievement in self.achievements.values():
            # 筛选类别
            if category and achievement.category != category:
                continue
            
            # 获取玩家进度
            player_achievement = self.get_player_achievement(player_id, achievement.achievement_id)
            
            # 筛选已完成
            if completed_only and (not player_achievement or not player_achievement.completed):
                continue
            
            # 隐藏成就未完成不显示
            if achievement.hidden and (not player_achievement or not player_achievement.completed):
                continue
            
            achievement_data = achievement.to_dict()
            achievement_data["player_progress"] = player_achievement.to_dict() if player_achievement else {
                "progress": 0,
                "completed": False,
            }
            achievement_data["progress_percent"] = (
                min(100, (player_achievement.progress / achievement.requirement.target) * 100)
                if player_achievement else 0
            )
            
            result.append(achievement_data)
        
        return result
    
    def get_player_stats(self, player_id: str) -> Dict[str, Any]:
        """
        获取玩家成就统计
        
        Args:
            player_id: 玩家ID
            
        Returns:
            统计数据字典
        """
        total = len(self.achievements)
        completed = 0
        by_category: Dict[str, int] = {cat.value: 0 for cat in AchievementCategory}
        by_tier: Dict[int, int] = {tier.value: 0 for tier in AchievementTier}
        
        for achievement in self.achievements.values():
            player_achievement = self.get_player_achievement(player_id, achievement.achievement_id)
            if player_achievement and player_achievement.completed:
                completed += 1
                by_category[achievement.category.value] += 1
                by_tier[achievement.tier.value] += 1
        
        return {
            "player_id": player_id,
            "total_achievements": total,
            "completed_achievements": completed,
            "completion_rate": round(completed / total * 100, 2) if total > 0 else 0,
            "by_category": by_category,
            "by_tier": by_tier,
        }
    
    def get_recently_completed(
        self,
        player_id: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        获取最近完成的成就
        
        Args:
            player_id: 玩家ID
            limit: 返回数量限制
            
        Returns:
            最近完成的成就列表
        """
        completed = []
        
        for achievement in self.achievements.values():
            player_achievement = self.get_player_achievement(player_id, achievement.achievement_id)
            if player_achievement and player_achievement.completed and player_achievement.completed_at:
                completed.append({
                    "achievement": achievement.to_dict(),
                    "completed_at": player_achievement.completed_at.isoformat(),
                })
        
        # 按完成时间倒序排序
        completed.sort(key=lambda x: x["completed_at"], reverse=True)
        
        return completed[:limit]


# 全局单例
_achievement_manager: Optional[AchievementManager] = None


def get_achievement_manager(config_path: Optional[str] = None) -> AchievementManager:
    """
    获取成就管理器单例
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        成就管理器实例
    """
    global _achievement_manager
    if _achievement_manager is None:
        _achievement_manager = AchievementManager(config_path)
    return _achievement_manager
