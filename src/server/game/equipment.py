"""
王者之奕 - 装备系统实现
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from shared.models import Hero


# ============================================================================
# 装备稀有度枚举
# ============================================================================

class Rarity(Enum):
    """装备稀有度"""
    COMMON = "common"       # 普通 - 白色
    RARE = "rare"           # 稀有 - 绿色
    EPIC = "epic"           # 史诗 - 紫色
    LEGENDARY = "legendary" # 传说 - 橙色
    
    @classmethod
    def from_string(cls, value: str) -> Rarity:
        """从字符串创建稀有度"""
        try:
            return cls(value.lower())
        except ValueError:
            return cls.COMMON
    
    def get_color_code(self) -> str:
        """获取稀有度对应的颜色代码"""
        colors = {
            Rarity.COMMON: "#FFFFFF",
            Rarity.RARE: "#1EFF00",
            Rarity.EPIC: "#A335EE",
            Rarity.LEGENDARY: "#FF8000",
        }
        return colors.get(self, "#FFFFFF")


# ============================================================================
# 特殊效果类型枚举
# ============================================================================

class SpecialEffectType(Enum):
    """装备特殊效果类型"""
    BURN = "burn"           # 灼烧
    FREEZE = "freeze"       # 减速
    LIFESTEAL = "lifesteal" # 吸血
    CRIT = "crit"           # 暴击
    SHIELD = "shield"       # 护盾
    REFLECT = "reflect"     # 反伤
    PIERCE = "pierce"       # 穿透
    HEAL = "heal"           # 回复
    
    @classmethod
    def from_string(cls, value: str) -> SpecialEffectType:
        """从字符串创建效果类型"""
        try:
            return cls(value.lower())
        except ValueError:
            return None


@dataclass
class SpecialEffect:
    """装备特殊效果"""
    effect_type: SpecialEffectType
    value: float = 0.0
    duration: float = 0.0
    trigger_chance: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "effect_type": self.effect_type.value if self.effect_type else None,
            "value": self.value,
            "duration": self.duration,
            "trigger_chance": self.trigger_chance,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Optional[SpecialEffect]:
        if not data or not data.get("effect_type"):
            return None
        effect_type = SpecialEffectType.from_string(data.get("effect_type", ""))
        if effect_type is None:
            return None
        return cls(
            effect_type=effect_type,
            value=data.get("value", 0.0),
            duration=data.get("duration", 0.0),
            trigger_chance=data.get("trigger_chance", 1.0),
        )


# ============================================================================
# 装备数据类
# ============================================================================

@dataclass
class EquipmentStats:
    """装备属性"""
    attack: int = 0
    armor: int = 0
    spell_power: int = 0
    hp: int = 0
    attack_speed: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "attack": self.attack,
            "armor": self.armor,
            "spell_power": self.spell_power,
            "hp": self.hp,
            "attack_speed": self.attack_speed,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EquipmentStats:
        return cls(
            attack=data.get("attack", 0),
            armor=data.get("armor", 0),
            spell_power=data.get("spell_power", 0),
            hp=data.get("hp", 0),
            attack_speed=data.get("attack_speed", 0.0),
        )
    
    def __add__(self, other: EquipmentStats) -> EquipmentStats:
        """合并两个属性"""
        return EquipmentStats(
            attack=self.attack + other.attack,
            armor=self.armor + other.armor,
            spell_power=self.spell_power + other.spell_power,
            hp=self.hp + other.hp,
            attack_speed=self.attack_speed + other.attack_speed,
        )


@dataclass
class Equipment:
    """装备类"""
    equipment_id: str
    name: str
    tier: int
    stats: EquipmentStats
    rarity: Rarity = Rarity.COMMON
    recipe: List[str] = field(default_factory=list)
    special_effects: List[SpecialEffect] = field(default_factory=list)
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "equipment_id": self.equipment_id,
            "name": self.name,
            "tier": self.tier,
            "rarity": self.rarity.value,
            "stats": self.stats.to_dict(),
            "recipe": self.recipe.copy(),
            "special_effects": [e.to_dict() for e in self.special_effects if e],
            "description": self.description,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Equipment:
        # 解析稀有度
        rarity_str = data.get("rarity", "common")
        rarity = Rarity.from_string(rarity_str)
        
        # 解析特殊效果
        effects = []
        for effect_data in data.get("special_effects", []):
            effect = SpecialEffect.from_dict(effect_data)
            if effect:
                effects.append(effect)
        
        return cls(
            equipment_id=data["equipment_id"] if "equipment_id" in data else data.get("id", ""),
            name=data["name"],
            tier=data["tier"],
            rarity=rarity,
            stats=EquipmentStats.from_dict(data.get("stats", {})),
            recipe=data.get("recipe", []),
            special_effects=effects,
            description=data.get("description", ""),
        )


# ============================================================================
# 装备管理器
# ============================================================================

class EquipmentManager:
    """
    装备管理器
    
    管理装备配置、合成和属性应用。
    """
    
    def __init__(self, config_path: Optional[str] = None) -> None:
        """
        初始化装备管理器
        
        Args:
            config_path: 装备配置文件路径
        """
        self.equipment_config: Dict[str, Equipment] = {}
        
        if config_path:
            self.load_from_file(config_path)
    
    def load_from_file(self, config_path: str) -> None:
        """从JSON文件加载装备配置"""
        path = Path(config_path)
        if not path.exists():
            return
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        for eq_data in data.get("equipment", []):
            eq = Equipment.from_dict(eq_data)
            self.equipment_config[eq.equipment_id] = eq
    
    def get_equipment(self, equipment_id: str) -> Optional[Equipment]:
        """获取装备"""
        return self.equipment_config.get(equipment_id)
    
    def can_craft(self, recipe: List[str]) -> Optional[str]:
        """
        检查是否可以合成
        
        Args:
            recipe: 合成配方
            
        Returns:
            可以合成的装备ID，如果不能合成返回None
        """
        for eq_id, eq in self.equipment_config.items():
            if eq.recipe == recipe:
                return eq_id
        return None
    
    def get_all_equipment(self, tier: Optional[int] = None) -> List[Equipment]:
        """
        获取所有装备
        
        Args:
            tier: 等级过滤
            
        Returns:
            装备列表
        """
        equipment = list(self.equipment_config.values())
        if tier is not None:
            equipment = [eq for eq in equipment if eq.tier == tier]
        return equipment
    
    def apply_equipment(self, hero: Hero, equipment_ids: List[str]) -> None:
        """
        应用装备到英雄
        
        Args:
            hero: 英雄实例（会被修改）
            equipment_ids: 装备ID列表
        """
        total_stats = EquipmentStats()
        
        for eq_id in equipment_ids:
            eq = self.get_equipment(eq_id)
            if eq:
                total_stats.attack += eq.stats.attack
                total_stats.armor += eq.stats.armor
                total_stats.spell_power += eq.stats.spell_power
                total_stats.hp += eq.stats.hp
                total_stats.attack_speed += eq.stats.attack_speed
        
        # 应用属性加成到英雄
        hero.attack += total_stats.attack
        hero.defense += total_stats.armor
        hero.max_hp += total_stats.hp
        hero.hp += total_stats.hp
        # 攻速使用乘法
        hero.attack_speed *= (1.0 + total_stats.attack_speed)


# ============================================================================
# 工厂函数
# ============================================================================

def create_equipment_manager() -> EquipmentManager:
    """
    创建装备管理器（使用默认配置）
    
    Returns:
        装备管理器实例
    """
    return EquipmentManager(config_path=None)
