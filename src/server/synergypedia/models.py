"""
王者之奕 - 羁绊图鉴数据模型

本模块定义羁绊图鉴系统的数据类：
- SynergypediaEntry: 羁绊图鉴条目
- SynergypediaProgress: 羁绊进度
- RecommendedLineup: 推荐阵容
- SynergySimulation: 羁绊模拟结果
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from src.shared.models import Synergy, SynergyType


@dataclass
class SynergypediaEntry:
    """
    羁绊图鉴条目
    
    包含羁绊的完整信息，用于图鉴展示。
    
    Attributes:
        name: 羁绊名称
        synergy_type: 羁绊类型（种族/职业）
        description: 羁绊描述
        levels: 羁绊等级列表
        related_heroes: 关联英雄ID列表
        icon: 羁绊图标
        tips: 使用技巧
    """
    name: str
    synergy_type: SynergyType
    description: str
    levels: list[dict[str, Any]]
    related_heroes: list[str] = field(default_factory=list)
    icon: str = ""
    tips: str = ""
    
    def to_dict(self) -> dict[str, Any]:
        """序列化为字典"""
        return {
            "name": self.name,
            "synergy_type": self.synergy_type.value,
            "description": self.description,
            "levels": self.levels,
            "related_heroes": self.related_heroes,
            "icon": self.icon,
            "tips": self.tips,
        }
    
    @classmethod
    def from_synergy(cls, synergy: Synergy, related_heroes: list[str]) -> SynergypediaEntry:
        """
        从 Synergy 对象创建图鉴条目
        
        Args:
            synergy: 羁绊定义对象
            related_heroes: 关联英雄列表
            
        Returns:
            图鉴条目
        """
        levels = [
            {
                "required_count": level.required_count,
                "effect_description": level.effect_description,
                "stat_bonuses": level.stat_bonuses,
                "special_effects": level.special_effects,
            }
            for level in synergy.levels
        ]
        
        # 根据羁绊类型设置图标和技巧
        icon = cls._get_icon(synergy.name, synergy.synergy_type)
        tips = cls._get_tips(synergy.name)
        
        return cls(
            name=synergy.name,
            synergy_type=synergy.synergy_type,
            description=synergy.description,
            levels=levels,
            related_heroes=related_heroes,
            icon=icon,
            tips=tips,
        )
    
    @staticmethod
    def _get_icon(name: str, synergy_type: SynergyType) -> str:
        """获取羁绊图标"""
        # 简单的图标命名规则
        prefix = "race" if synergy_type == SynergyType.RACE else "class"
        return f"synergy_{prefix}_{name}.png"
    
    @staticmethod
    def _get_tips(name: str) -> str:
        """获取羁绊使用技巧"""
        tips_map = {
            "人族": "人族羁绊适合搭配法师或射手，增加输出能力。推荐搭配4人族获得25%攻击加成。",
            "神族": "神族羁绊大幅减少技能冷却，适合技能伤害高的英雄。2神族即可获得20%冷却缩减。",
            "魔种": "魔种羁绊提供吸血效果，增加持续作战能力。适合前排坦克英雄。",
            "亡灵": "亡灵羁绊减少敌方护甲，适合物理输出阵容。4亡灵可减少15点护甲。",
            "精灵": "精灵羁绊提供闪避，适合对抗物理攻击。4精灵可获得40%闪避率。",
            "兽族": "兽族羁绊增加生命值，提高生存能力。适合前排抗压。",
            "机械": "机械羁绊增加护甲，对抗物理伤害效果好。2机械即可获得15护甲。",
            "龙族": "龙族羁绊让英雄开局满蓝，可以快速释放技能。3龙族效果最佳。",
            "妖精": "妖精羁绊增加攻速，适合射手和攻速流英雄。",
            "战士": "战士羁绊增加护甲，适合构建前排肉盾阵容。6战士可获得60点护甲。",
            "法师": "法师羁绊降低敌方魔抗，大幅提高法术伤害。4法师效果显著。",
            "刺客": "刺客羁绊增加暴击，适合切后排。4刺客可获得30%暴击率。",
            "射手": "射手羁绊提供额外攻击次数，大幅提高输出。4射手可50%双重打击。",
            "坦克": "坦克羁绊增加生命值百分比，适合构建高血量前排。",
            "辅助": "辅助羁绊增加魔抗，对抗法师阵容效果好。",
            "游侠": "游侠羁绊提供攻速叠加，战斗时间越长越强。",
            "术士": "术士羁绊提供技能吸血，增加法术英雄的续航能力。",
        }
        return tips_map.get(name, "合理搭配羁绊可以获得强大效果。")
    
    def get_level_for_count(self, count: int) -> Optional[dict[str, Any]]:
        """
        根据英雄数量获取对应的羁绊等级
        
        Args:
            count: 英雄数量
            
        Returns:
            羁绊等级信息，未激活返回 None
        """
        active_level = None
        for level in self.levels:
            if count >= level["required_count"]:
                active_level = level
            else:
                break
        return active_level


@dataclass
class SynergypediaProgress:
    """
    羁绊进度
    
    记录玩家对某个羁绊的使用进度和成就。
    
    Attributes:
        synergy_name: 羁绊名称
        activation_count: 总激活次数
        max_heroes_used: 单局最多使用该羁绊英雄数
        highest_level_reached: 达到的最高羁绊等级
        total_games: 使用该羁绊的对局数
        win_rate: 胜率
        achievements: 已解锁的成就列表
    """
    synergy_name: str
    activation_count: int = 0
    max_heroes_used: int = 0
    highest_level_reached: int = 0
    total_games: int = 0
    win_count: int = 0
    achievements: list[str] = field(default_factory=list)
    
    @property
    def win_rate(self) -> float:
        """计算胜率"""
        if self.total_games == 0:
            return 0.0
        return round(self.win_count / self.total_games * 100, 1)
    
    def to_dict(self) -> dict[str, Any]:
        """序列化为字典"""
        return {
            "synergy_name": self.synergy_name,
            "activation_count": self.activation_count,
            "max_heroes_used": self.max_heroes_used,
            "highest_level_reached": self.highest_level_reached,
            "total_games": self.total_games,
            "win_rate": self.win_rate,
            "achievements": self.achievements,
        }
    
    def update_with_game_result(
        self,
        heroes_count: int,
        level_reached: int,
        is_win: bool,
    ) -> list[str]:
        """
        根据对局结果更新进度
        
        Args:
            heroes_count: 该羁绊使用的英雄数
            level_reached: 达到的羁绊等级
            is_win: 是否获胜
            
        Returns:
            新解锁的成就列表
        """
        new_achievements = []
        
        # 更新统计
        self.activation_count += 1
        self.total_games += 1
        if is_win:
            self.win_count += 1
        
        if heroes_count > self.max_heroes_used:
            self.max_heroes_used = heroes_count
        
        if level_reached > self.highest_level_reached:
            self.highest_level_reached = level_reached
        
        # 检查成就
        new_achievements.extend(self._check_achievements(heroes_count, level_reached))
        
        return new_achievements
    
    def _check_achievements(self, heroes_count: int, level_reached: int) -> list[str]:
        """检查并解锁成就"""
        new_achievements = []
        
        # 激活次数成就
        count_achievements = [
            (10, f"{self.synergy_name}入门者"),
            (50, f"{self.synergy_name}熟练者"),
            (100, f"{self.synergy_name}大师"),
            (500, f"{self.synergy_name}宗师"),
        ]
        for count, achievement in count_achievements:
            if self.activation_count >= count and achievement not in self.achievements:
                self.achievements.append(achievement)
                new_achievements.append(achievement)
        
        # 等级成就
        level_achievements = [
            (1, f"{self.synergy_name}初窥门径"),
            (2, f"{self.synergy_name}炉火纯青"),
            (3, f"{self.synergy_name}登峰造极"),
        ]
        for level, achievement in level_achievements:
            if level_reached >= level and achievement not in self.achievements:
                self.achievements.append(achievement)
                new_achievements.append(achievement)
        
        return new_achievements


@dataclass
class RecommendedLineup:
    """
    推荐阵容
    
    包含基于羁绊的推荐阵容信息。
    
    Attributes:
        name: 阵容名称
        description: 阵容描述
        core_synergies: 核心羁绊列表
        hero_recommendations: 英雄推荐列表
        priority: 推荐优先级 (1-5, 5最高)
        difficulty: 难度等级 (easy/medium/hard)
        playstyle: 玩法风格
        early_game: 前期过渡建议
        mid_game: 中期发展方向
        late_game: 后期成型目标
    """
    name: str
    description: str
    core_synergies: list[str]
    hero_recommendations: list[dict[str, Any]]
    priority: int = 3
    difficulty: str = "medium"
    playstyle: str = "balanced"
    early_game: str = ""
    mid_game: str = ""
    late_game: str = ""
    
    def to_dict(self) -> dict[str, Any]:
        """序列化为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "core_synergies": self.core_synergies,
            "hero_recommendations": self.hero_recommendations,
            "priority": self.priority,
            "difficulty": self.difficulty,
            "playstyle": self.playstyle,
            "early_game": self.early_game,
            "mid_game": self.mid_game,
            "late_game": self.late_game,
        }


@dataclass
class SynergySimulation:
    """
    羁绊模拟结果
    
    包含模拟器选择英雄后的羁绊激活情况。
    
    Attributes:
        selected_heroes: 选中的英雄列表
        active_synergies: 激活的羁绊列表
        inactive_synergies: 未激活但相关的羁绊
        synergy_progress: 各羁绊的进度
        recommendations: 推荐补充的英雄
        total_bonuses: 总属性加成
    """
    selected_heroes: list[str]
    active_synergies: list[dict[str, Any]]
    inactive_synergies: list[dict[str, Any]]
    synergy_progress: dict[str, dict[str, Any]]
    recommendations: list[dict[str, Any]]
    total_bonuses: dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """序列化为字典"""
        return {
            "selected_heroes": self.selected_heroes,
            "active_synergies": self.active_synergies,
            "inactive_synergies": self.inactive_synergies,
            "synergy_progress": self.synergy_progress,
            "recommendations": self.recommendations,
            "total_bonuses": self.total_bonuses,
        }
    
    def is_synergy_active(self, synergy_name: str) -> bool:
        """检查指定羁绊是否激活"""
        for synergy in self.active_synergies:
            if synergy["name"] == synergy_name:
                return True
        return False
    
    def get_synergy_level(self, synergy_name: str) -> int:
        """获取指定羁绊的当前等级"""
        for synergy in self.active_synergies:
            if synergy["name"] == synergy_name:
                return synergy.get("level", 0)
        return 0


@dataclass
class SynergyAchievement:
    """
    羁绊成就
    
    定义羁绊相关的成就。
    
    Attributes:
        achievement_id: 成就ID
        name: 成就名称
        description: 成就描述
        synergy_name: 关联的羁绊名称
        requirement_type: 需求类型 (activation_count/max_heroes/level_reached)
        requirement_value: 需求值
        reward: 奖励信息
        is_unlocked: 是否已解锁
    """
    achievement_id: str
    name: str
    description: str
    synergy_name: str
    requirement_type: str
    requirement_value: int
    reward: dict[str, Any] = field(default_factory=dict)
    is_unlocked: bool = False
    
    def to_dict(self) -> dict[str, Any]:
        """序列化为字典"""
        return {
            "achievement_id": self.achievement_id,
            "name": self.name,
            "description": self.description,
            "synergy_name": self.synergy_name,
            "requirement_type": self.requirement_type,
            "requirement_value": self.requirement_value,
            "reward": self.reward,
            "is_unlocked": self.is_unlocked,
        }
    
    def check_unlock(self, progress: SynergypediaProgress) -> bool:
        """
        检查是否解锁
        
        Args:
            progress: 羁绊进度
            
        Returns:
            是否解锁
        """
        if self.is_unlocked:
            return False
        
        if self.requirement_type == "activation_count":
            if progress.activation_count >= self.requirement_value:
                self.is_unlocked = True
                return True
        elif self.requirement_type == "max_heroes":
            if progress.max_heroes_used >= self.requirement_value:
                self.is_unlocked = True
                return True
        elif self.requirement_type == "level_reached":
            if progress.highest_level_reached >= self.requirement_value:
                self.is_unlocked = True
                return True
        
        return False
