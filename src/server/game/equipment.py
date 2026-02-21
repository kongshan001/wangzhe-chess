"""
王者之奕 - 装备系统实现
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from shared.models import Hero


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


@dataclass
class Equipment:
    """装备类"""
    equipment_id: str
    name: str
    tier: int
    stats: EquipmentStats
    recipe: List[str] = field(default_factory=list)
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "equipment_id": self.equipment_id,
            "name": self.name,
            "tier": self.tier,
            "stats": self.stats.to_dict(),
            "recipe": self.recipe.copy(),
            "description": self.description,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Equipment:
        return cls(
            equipment_id=data["equipment_id"],
            name=data["name"],
            tier=data["tier"],
            stats=EquipmentStats.from_dict(data.get("stats", {})),
            recipe=data.get("recipe", []),
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
