"""
王者之奕 - 天赋系统实现
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from shared.models import Hero, Player


# ============================================================================
# 天赋数据类
# ============================================================================

@dataclass
class Talent:
    """天赋类"""
    talent_id: str
    name: str
    category: str  # economy, battle, synergy, assist
    tier: int
    max_points: int
    required_points: int
    required_talents: List[str] = field(default_factory=list)
    effect_description: str
    effect_data: Dict[str, Any] = field(default_factory=dict)
    
    def is_unlocked(self, unlocked_talents: List[str], points: int) -> bool:
        """检查天赋是否解锁"""
        # 检查前置天赋
        for req_id in self.required_talents:
            if req_id not in unlocked_talents:
                return False
        
        # 检查点数
        if points < self.required_points:
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "talent_id": self.talent_id,
            "name": self.name,
            "category": self.category,
            "tier": self.tier,
            "max_points": self.max_points,
            "required_points": self.required_points,
            "required_talents": self.required_talents,
            "effect_description": self.effect_description,
            "effect_data": self.effect_data,
        }


# ============================================================================
# 玩家天赋数据
# ============================================================================

@dataclass
class PlayerTalents:
    """玩家天赋状态"""
    player_id: str
    unlocked_talents: List[str] = field(default_factory=list)
    talent_points: int = 0
    total_points_earned: int = 0
    
    def unlock(self, talent: Talent) -> bool:
        """解锁天赋"""
        if talent.talent_id in self.unlocked_talents:
            return False
        
        if self.talent_points < talent.required_points:
            return False
        
        self.unlocked_talents.append(talent.talent_id)
        return True
    
    def add_points(self, amount: int) -> int:
        """增加天赋点"""
        old_points = self.talent_points
        self.talent_points += amount
        self.total_points_earned += amount
        return self.talent_points - old_points
    
    def get_available_talents(
        self,
        all_talents: List[Talent],
    ) -> List[Talent]:
        """获取可解锁的天赋"""
        available = []
        for talent in all_talents:
            if (talent.talent_id not in self.unlocked_talents
                    and talent.is_unlocked(self.unlocked_talents, self.talent_points)):
                available.append(talent)
        return available


# ============================================================================
# 天赋效果应用器
# ============================================================================

class TalentEffectApplier:
    """天赋效果应用器"""
    
    @staticmethod
    def apply_to_player(
        player: Player,
        player_talents: PlayerTalents,
        all_talents: List[Talent],
    ) -> None:
        """应用天赋效果到玩家"""
        unlocked_ids = player_talents.unlocked_talents
        
        for talent_id in unlocked_ids:
            talent = next((t for t in all_talents if t.talent_id == talent_id), None)
            if not talent:
                continue
            
            TalentEffectApplier._apply_talent(talent, player)
    
    @staticmethod
    def _apply_talent(talent: Talent, player: Player) -> None:
        """应用单个天赋"""
        category = talent.category
        effect = talent.effect_data
        
        if category == "economy":
            TalentEffectApplier._apply_economy_talent(effect, player)
        elif category == "battle":
            TalentEffectApplier._apply_battle_talent(effect, player)
        elif category == "synergy":
            TalentEffectApplier._apply_synergy_talent(effect, player)
        elif category == "assist":
            TalentEffectApplier._apply_assist_talent(effect, player)
    
    @staticmethod
    def _apply_economy_talent(effect: Dict[str, Any], player: Player) -> None:
        """应用经济天赋"""
        # 利息上限
        if "interest_cap_bonus" in effect:
            pass  # 需要修改经济系统
        
        # 刷新费用
        if "refresh_cost_reduction" in effect:
            pass  # 需要修改经济系统
    
    @staticmethod
    def _apply_battle_talent(effect: Dict[str, Any], player: Player) -> None:
        """应用战斗天赋"""
        # 英雄属性加成
        for hero in player.get_all_heroes():
            if "hp_bonus_percent" in effect:
                hero.max_hp = int(hero.max_hp * (1 + effect["hp_bonus_percent"]))
            if "attack_bonus_percent" in effect:
                hero.attack = int(hero.attack * (1 + effect["attack_bonus_percent"]))
    
    @staticmethod
    def _apply_synergy_talent(effect: Dict[str, Any], player: Player) -> None:
        """应用羁绊天赋"""
        # 羁绊效果加成
        pass  # 需要修改羁绊系统
    
    @staticmethod
    def _apply_assist_talent(effect: Dict[str, Any], player: Player) -> None:
        """应用辅助天赋"""
        # 准备时间延长
        pass  # 需要修改房间系统


# ============================================================================
# 天赋管理器
# ============================================================================

class TalentManager:
    """
    天赋管理器
    
    管理天赋配置、玩家天赋和效果应用。
    """
    
    def __init__(self) -> None:
        """初始化天赋管理器"""
        self.talents: Dict[str, Talent] = {}
        self.player_talents: Dict[str, PlayerTalents] = {}
    
    def load_from_dict(self, data: Dict[str, Any]) -> None:
        """从字典加载天赋配置"""
        talent_data = data.get("talent_tree", {})
        
        for category, talent_list in talent_data.items():
            for talent_info in talent_list:
                talent = Talent(
                    talent_id=talent_info["talent_id"],
                    name=talent_info["name"],
                    category=category,
                    tier=talent_info["tier"],
                    max_points=talent_info.get("max_points", 15),
                    required_points=talent_info.get("required_points", 0),
                    required_talents=talent_info.get("required_talents", []),
                    effect_description=talent_info.get("effect_description", ""),
                    effect_data=talent_info.get("effect_data", {}),
                )
                self.talents[talent.talent_id] = talent
    
    def get_talent(self, talent_id: str) -> Optional[Talent]:
        """获取天赋"""
        return self.talents.get(talent_id)
    
    def get_player_talents(self, player_id: str) -> Optional[PlayerTalents]:
        """获取玩家天赋状态"""
        return self.player_talents.get(player_id)
    
    def create_player_talents(self, player_id: str, initial_points: int = 0) -> PlayerTalents:
        """创建玩家天赋"""
        if player_id in self.player_talents:
            return self.player_talents[player_id]
        
        pt = PlayerTalents(player_id=player_id, talent_points=initial_points)
        self.player_talents[player_id] = pt
        return pt
    
    def unlock_talent(
        self,
        player_id: str,
        talent_id: str,
    ) -> bool:
        """
        解锁天赋
        
        Args:
            player_id: 玩家ID
            talent_id: 天赋ID
            
        Returns:
            是否成功解锁
        """
        talent = self.get_talent(talent_id)
        if not talent:
            return False
        
        pt = self.get_player_talents(player_id)
        if not pt:
            pt = self.create_player_talents(player_id)
        
        return pt.unlock(talent)
    
    def apply_all_effects(self, player: Player) -> None:
        """应用所有天赋效果到玩家"""
        pt = self.get_player_talents(player.player_id)
        if not pt:
            return
        
        all_talents = list(self.talents.values())
        TalentEffectApplier.apply_to_player(player, pt, all_talents)
