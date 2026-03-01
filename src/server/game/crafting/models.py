"""
王者之奕 - 装备合成数据模型
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Rarity(Enum):
    """装备稀有度枚举"""

    COMMON = "common"  # 普通 - 白色
    RARE = "rare"  # 稀有 - 绿色
    EPIC = "epic"  # 史诗 - 紫色
    LEGENDARY = "legendary"  # 传说 - 橙色

    @classmethod
    def from_tier(cls, tier: int) -> Rarity:
        """根据装备等级推断稀有度"""
        if tier <= 1:
            return cls.COMMON
        elif tier == 2:
            return cls.RARE
        elif tier == 3:
            return cls.EPIC
        else:
            return cls.LEGENDARY

    def get_color_code(self) -> str:
        """获取稀有度对应的颜色代码（用于显示）"""
        colors = {
            Rarity.COMMON: "#FFFFFF",  # 白色
            Rarity.RARE: "#1EFF00",  # 绿色
            Rarity.EPIC: "#A335EE",  # 紫色
            Rarity.LEGENDARY: "#FF8000",  # 橙色
        }
        return colors.get(self, "#FFFFFF")


class SpecialEffectType(Enum):
    """特殊效果类型"""

    BURN = "burn"  # 灼烧 - 每秒造成法术伤害
    FREEZE = "freeze"  # 减速 - 降低攻击速度
    LIFESTEAL = "lifesteal"  # 吸血 - 攻击回血
    CRIT = "crit"  # 暴击 - 增加暴击率
    SHIELD = "shield"  # 护盾 - 生命值低于阈值时生成护盾
    REFLECT = "reflect"  # 反伤 - 受到攻击时反弹伤害
    PIERCE = "pierce"  # 穿透 - 无视部分护甲
    HEAL = "heal"  # 回复 - 每秒回复生命


@dataclass
class SpecialEffect:
    """装备特殊效果"""

    effect_type: SpecialEffectType
    value: float = 0.0  # 效果数值（百分比或固定值）
    duration: float = 0.0  # 持续时间（秒）
    trigger_chance: float = 1.0  # 触发概率

    def to_dict(self) -> dict[str, Any]:
        return {
            "effect_type": self.effect_type.value,
            "value": self.value,
            "duration": self.duration,
            "trigger_chance": self.trigger_chance,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SpecialEffect:
        return cls(
            effect_type=SpecialEffectType(data["effect_type"]),
            value=data.get("value", 0.0),
            duration=data.get("duration", 0.0),
            trigger_chance=data.get("trigger_chance", 1.0),
        )


@dataclass
class CraftingMaterial:
    """合成材料"""

    equipment_id: str
    quantity: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "equipment_id": self.equipment_id,
            "quantity": self.quantity,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CraftingMaterial:
        return cls(
            equipment_id=data["equipment_id"],
            quantity=data.get("quantity", 1),
        )


@dataclass
class CraftingRecipe:
    """
    合成配方

    定义如何将多个装备合成为新装备
    """

    recipe_id: str  # 配方ID
    result_id: str  # 合成结果装备ID
    materials: list[CraftingMaterial]  # 所需材料
    gold_cost: int = 0  # 金币消耗
    success_rate: float = 1.0  # 成功率（默认100%）

    def to_dict(self) -> dict[str, Any]:
        return {
            "recipe_id": self.recipe_id,
            "result_id": self.result_id,
            "materials": [m.to_dict() for m in self.materials],
            "gold_cost": self.gold_cost,
            "success_rate": self.success_rate,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CraftingRecipe:
        return cls(
            recipe_id=data["recipe_id"],
            result_id=data["result_id"],
            materials=[CraftingMaterial.from_dict(m) for m in data.get("materials", [])],
            gold_cost=data.get("gold_cost", 0),
            success_rate=data.get("success_rate", 1.0),
        )

    def get_material_ids(self) -> list[str]:
        """获取所有材料ID列表（展开数量）"""
        result = []
        for material in self.materials:
            result.extend([material.equipment_id] * material.quantity)
        return result

    def matches_materials(self, equipment_ids: list[str]) -> bool:
        """
        检查提供的装备列表是否匹配此配方

        Args:
            equipment_ids: 装备ID列表（不考虑顺序）

        Returns:
            是否匹配
        """
        # 排序后比较
        required = sorted(self.get_material_ids())
        provided = sorted(equipment_ids)
        return required == provided


@dataclass
class CraftingResult:
    """合成结果"""

    success: bool
    result_equipment_id: str | None = None
    gold_spent: int = 0
    materials_consumed: list[str] = field(default_factory=list)
    error_message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "result_equipment_id": self.result_equipment_id,
            "gold_spent": self.gold_spent,
            "materials_consumed": self.materials_consumed,
            "error_message": self.error_message,
        }


@dataclass
class CraftingHistoryEntry:
    """合成历史记录条目"""

    recipe_id: str
    result_id: str
    materials: list[str]
    gold_cost: int
    timestamp: float = 0.0  # Unix时间戳
    success: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "recipe_id": self.recipe_id,
            "result_id": self.result_id,
            "materials": self.materials.copy(),
            "gold_cost": self.gold_cost,
            "timestamp": self.timestamp,
            "success": self.success,
        }
