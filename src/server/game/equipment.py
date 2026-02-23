"""
王者之奕 - 装备系统实现
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from shared.models import Hero

# ============================================================================
# 装备稀有度枚举
# ============================================================================


class Rarity(Enum):
    """装备稀有度"""

    COMMON = "common"  # 普通 - 白色
    RARE = "rare"  # 稀有 - 绿色
    EPIC = "epic"  # 史诗 - 紫色
    LEGENDARY = "legendary"  # 传说 - 橙色

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

    BURN = "burn"  # 灼烧
    FREEZE = "freeze"  # 减速
    LIFESTEAL = "lifesteal"  # 吸血
    CRIT = "crit"  # 暴击
    SHIELD = "shield"  # 护盾
    REFLECT = "reflect"  # 反伤
    PIERCE = "pierce"  # 穿透
    HEAL = "heal"  # 回复

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

    def to_dict(self) -> dict[str, Any]:
        return {
            "effect_type": self.effect_type.value if self.effect_type else None,
            "value": self.value,
            "duration": self.duration,
            "trigger_chance": self.trigger_chance,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SpecialEffect | None:
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

    def to_dict(self) -> dict[str, Any]:
        return {
            "attack": self.attack,
            "armor": self.armor,
            "spell_power": self.spell_power,
            "hp": self.hp,
            "attack_speed": self.attack_speed,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EquipmentStats:
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
    recipe: list[str] = field(default_factory=list)
    special_effects: list[SpecialEffect] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
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
    def from_dict(cls, data: dict[str, Any]) -> Equipment:
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

    def __init__(self, config_path: str | None = None) -> None:
        """
        初始化装备管理器

        Args:
            config_path: 装备配置文件路径
        """
        self.equipment_config: dict[str, Equipment] = {}

        if config_path:
            self.load_from_file(config_path)

    def load_from_file(self, config_path: str) -> None:
        """从JSON文件加载装备配置"""
        path = Path(config_path)
        if not path.exists():
            return

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        for eq_data in data.get("equipment", []):
            eq = Equipment.from_dict(eq_data)
            self.equipment_config[eq.equipment_id] = eq

    def get_equipment(self, equipment_id: str) -> Equipment | None:
        """获取装备"""
        return self.equipment_config.get(equipment_id)

    def can_craft(self, recipe: list[str]) -> str | None:
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

    def get_all_equipment(self, tier: int | None = None) -> list[Equipment]:
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

    def apply_equipment(self, hero: Hero, equipment_ids: list[str]) -> None:
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
        hero.attack_speed *= 1.0 + total_stats.attack_speed


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


# ============================================================================
# 装备实例数据类
# ============================================================================


@dataclass
class EquipmentInstance:
    """
    装备实例

    代表玩家背包中或英雄身上的一个具体装备。

    Attributes:
        instance_id: 装备实例唯一ID
        equipment_id: 装备配置ID（指向Equipment）
        equipped_to: 装备给哪个英雄（hero_instance_id），None表示在背包中
        acquired_at: 获取时间戳
    """

    instance_id: str
    equipment_id: str
    equipped_to: str | None = None
    acquired_at: int = 0

    def to_dict(self) -> dict[str, Any]:
        """序列化为字典"""
        return {
            "instance_id": self.instance_id,
            "equipment_id": self.equipment_id,
            "equipped_to": self.equipped_to,
            "acquired_at": self.acquired_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EquipmentInstance:
        """从字典反序列化"""
        return cls(
            instance_id=data["instance_id"],
            equipment_id=data["equipment_id"],
            equipped_to=data.get("equipped_to"),
            acquired_at=data.get("acquired_at", 0),
        )

    def is_equipped(self) -> bool:
        """检查装备是否已被穿戴"""
        return self.equipped_to is not None


# ============================================================================
# 装备操作结果类
# ============================================================================


@dataclass
class EquipResult:
    """装备穿戴结果"""

    success: bool
    error_code: int = 0
    error_message: str = ""
    hero: Hero | None = None
    equipment_instance: EquipmentInstance | None = None


@dataclass
class UnequipResult:
    """装备卸下结果"""

    success: bool
    error_code: int = 0
    error_message: str = ""
    hero: Hero | None = None
    equipment_instance: EquipmentInstance | None = None


@dataclass
class CraftResult:
    """装备合成结果"""

    success: bool
    error_code: int = 0
    error_message: str = ""
    consumed_ids: list[str] = field(default_factory=list)
    new_equipment: EquipmentInstance | None = None


# ============================================================================
# 装备错误码
# ============================================================================


class EquipmentErrorCode:
    """装备操作错误码"""

    SUCCESS = 0
    EQUIPMENT_NOT_FOUND = 2001
    EQUIPMENT_ALREADY_EQUIPPED = 2002
    HERO_EQUIPMENT_FULL = 2003
    INVALID_RECIPE = 2004
    HERO_NOT_FOUND = 2005
    INSUFFICIENT_EQUIPMENT = 2006
    EQUIPMENT_NOT_EQUIPPED = 2007
    PERMISSION_DENIED = 2008


# ============================================================================
# 装备服务类
# ============================================================================

# 英雄最大装备槽位
MAX_EQUIPMENT_SLOTS = 3


class EquipmentService:
    """
    装备业务服务

    提供装备穿戴、卸下、合成等核心功能。
    """

    def __init__(self, equipment_manager: EquipmentManager) -> None:
        """
        初始化装备服务

        Args:
            equipment_manager: 装备管理器实例
        """
        self.equipment_manager = equipment_manager
        self._instance_counter = 0

    def _generate_instance_id(self) -> str:
        """生成装备实例ID"""
        import time

        self._instance_counter += 1
        return f"eq_inst_{int(time.time() * 1000)}_{self._instance_counter}"

    def _get_equipment_instance(
        self, player_equipment_bag: list[dict[str, Any]], instance_id: str
    ) -> EquipmentInstance | None:
        """从玩家背包获取装备实例"""
        for eq_data in player_equipment_bag:
            if eq_data.get("instance_id") == instance_id:
                return EquipmentInstance.from_dict(eq_data)
        return None

    def _update_equipment_instance(
        self, player_equipment_bag: list[dict[str, Any]], instance: EquipmentInstance
    ) -> None:
        """更新玩家背包中的装备实例"""
        for i, eq_data in enumerate(player_equipment_bag):
            if eq_data.get("instance_id") == instance.instance_id:
                player_equipment_bag[i] = instance.to_dict()
                return

    def _remove_equipment_instance(
        self, player_equipment_bag: list[dict[str, Any]], instance_id: str
    ) -> EquipmentInstance | None:
        """从玩家背包移除装备实例"""
        for i, eq_data in enumerate(player_equipment_bag):
            if eq_data.get("instance_id") == instance_id:
                instance = EquipmentInstance.from_dict(eq_data)
                player_equipment_bag.pop(i)
                return instance
        return None

    def _find_hero_by_instance_id(self, heroes: list[Hero], instance_id: str) -> Hero | None:
        """根据实例ID查找英雄"""
        for hero in heroes:
            if hero.instance_id == instance_id:
                return hero
        return None

    def equip_item(
        self,
        player_equipment_bag: list[dict[str, Any]],
        heroes: list[Hero],
        equipment_instance_id: str,
        hero_instance_id: str,
    ) -> EquipResult:
        """
        装备穿戴

        将背包装备穿戴到指定英雄身上。

        Args:
            player_equipment_bag: 玩家装备背包
            heroes: 玩家所有英雄列表（场上+备战席）
            equipment_instance_id: 装备实例ID
            hero_instance_id: 英雄实例ID

        Returns:
            EquipResult: 穿戴结果
        """
        # 1. 检查装备是否存在
        equipment_instance = self._get_equipment_instance(
            player_equipment_bag, equipment_instance_id
        )
        if equipment_instance is None:
            return EquipResult(
                success=False,
                error_code=EquipmentErrorCode.EQUIPMENT_NOT_FOUND,
                error_message="装备不存在",
            )

        # 2. 检查装备是否已被穿戴
        if equipment_instance.is_equipped():
            return EquipResult(
                success=False,
                error_code=EquipmentErrorCode.EQUIPMENT_ALREADY_EQUIPPED,
                error_message="装备已被穿戴",
            )

        # 3. 检查英雄是否存在
        hero = self._find_hero_by_instance_id(heroes, hero_instance_id)
        if hero is None:
            return EquipResult(
                success=False,
                error_code=EquipmentErrorCode.HERO_NOT_FOUND,
                error_message="英雄不存在",
            )

        # 4. 检查英雄装备槽位是否已满
        if len(hero.equipment) >= MAX_EQUIPMENT_SLOTS:
            return EquipResult(
                success=False,
                error_code=EquipmentErrorCode.HERO_EQUIPMENT_FULL,
                error_message="英雄装备槽已满",
            )

        # 5. 执行穿戴
        equipment_instance.equipped_to = hero_instance_id
        hero.equipment.append(equipment_instance_id)

        # 6. 更新背包中的装备实例
        self._update_equipment_instance(player_equipment_bag, equipment_instance)

        # 7. 重新计算英雄属性
        self.recalculate_hero_stats(hero)

        return EquipResult(success=True, hero=hero, equipment_instance=equipment_instance)

    def unequip_item(
        self,
        player_equipment_bag: list[dict[str, Any]],
        heroes: list[Hero],
        equipment_instance_id: str,
    ) -> UnequipResult:
        """
        装备卸下

        将英雄身上的装备卸下到背包。

        Args:
            player_equipment_bag: 玩家装备背包
            heroes: 玩家所有英雄列表（场上+备战席）
            equipment_instance_id: 装备实例ID

        Returns:
            UnequipResult: 卸下结果
        """
        # 1. 检查装备是否存在
        equipment_instance = self._get_equipment_instance(
            player_equipment_bag, equipment_instance_id
        )
        if equipment_instance is None:
            return UnequipResult(
                success=False,
                error_code=EquipmentErrorCode.EQUIPMENT_NOT_FOUND,
                error_message="装备不存在",
            )

        # 2. 检查装备是否已被穿戴
        if not equipment_instance.is_equipped():
            return UnequipResult(
                success=False,
                error_code=EquipmentErrorCode.EQUIPMENT_NOT_EQUIPPED,
                error_message="装备未被穿戴",
            )

        # 3. 找到穿戴该装备的英雄
        hero = self._find_hero_by_instance_id(heroes, equipment_instance.equipped_to)
        if hero is None:
            return UnequipResult(
                success=False,
                error_code=EquipmentErrorCode.HERO_NOT_FOUND,
                error_message="穿戴该装备的英雄不存在",
            )

        # 4. 从英雄装备列表中移除
        if equipment_instance_id in hero.equipment:
            hero.equipment.remove(equipment_instance_id)

        # 5. 更新装备实例
        equipment_instance.equipped_to = None
        self._update_equipment_instance(player_equipment_bag, equipment_instance)

        # 6. 重新计算英雄属性
        self.recalculate_hero_stats(hero)

        return UnequipResult(success=True, hero=hero, equipment_instance=equipment_instance)

    def craft_equipment(
        self, player_equipment_bag: list[dict[str, Any]], equipment_instance_ids: list[str]
    ) -> CraftResult:
        """
        装备合成

        将多件装备合成为更高级的装备。

        Args:
            player_equipment_bag: 玩家装备背包
            equipment_instance_ids: 要合成的装备实例ID列表

        Returns:
            CraftResult: 合成结果
        """
        if len(equipment_instance_ids) < 2:
            return CraftResult(
                success=False,
                error_code=EquipmentErrorCode.INVALID_RECIPE,
                error_message="合成需要至少两件装备",
            )

        # 1. 获取所有要合成的装备实例
        instances: list[EquipmentInstance] = []
        for inst_id in equipment_instance_ids:
            instance = self._get_equipment_instance(player_equipment_bag, inst_id)
            if instance is None:
                return CraftResult(
                    success=False,
                    error_code=EquipmentErrorCode.INSUFFICIENT_EQUIPMENT,
                    error_message=f"装备 {inst_id} 不存在",
                )
            if instance.is_equipped():
                return CraftResult(
                    success=False,
                    error_code=EquipmentErrorCode.EQUIPMENT_ALREADY_EQUIPPED,
                    error_message="不能合成已穿戴的装备",
                )
            instances.append(instance)

        # 2. 获取装备配置ID列表（用于匹配配方）
        equipment_ids = [inst.equipment_id for inst in instances]

        # 3. 检查是否有匹配的配方
        # 尝试所有可能的排列组合
        new_equipment_id = self._find_matching_recipe(equipment_ids)
        if new_equipment_id is None:
            return CraftResult(
                success=False,
                error_code=EquipmentErrorCode.INVALID_RECIPE,
                error_message="无效的合成配方",
            )

        # 4. 获取新装备配置
        new_equipment_config = self.equipment_manager.get_equipment(new_equipment_id)
        if new_equipment_config is None:
            return CraftResult(
                success=False,
                error_code=EquipmentErrorCode.EQUIPMENT_NOT_FOUND,
                error_message="合成目标装备不存在",
            )

        # 5. 移除消耗的装备
        import time

        for inst_id in equipment_instance_ids:
            self._remove_equipment_instance(player_equipment_bag, inst_id)

        # 6. 创建新装备实例
        new_instance = EquipmentInstance(
            instance_id=self._generate_instance_id(),
            equipment_id=new_equipment_id,
            equipped_to=None,
            acquired_at=int(time.time() * 1000),
        )

        # 7. 添加新装备到背包
        player_equipment_bag.append(new_instance.to_dict())

        return CraftResult(
            success=True, consumed_ids=equipment_instance_ids, new_equipment=new_instance
        )

    def _find_matching_recipe(self, equipment_ids: list[str]) -> str | None:
        """
        查找匹配的合成配方

        Args:
            equipment_ids: 装备ID列表

        Returns:
            合成后的装备ID，如果没有匹配返回None
        """
        # 首先尝试精确匹配
        result = self.equipment_manager.can_craft(equipment_ids)
        if result:
            return result

        # 尝试排序后匹配
        sorted_ids = sorted(equipment_ids)
        result = self.equipment_manager.can_craft(sorted_ids)
        if result:
            return result

        return None

    def recalculate_hero_stats(self, hero: Hero) -> None:
        """
        重新计算英雄属性（基于装备）

        注意：这个方法会修改英雄的属性值。
        假设英雄的基础属性已经正确设置，此方法只添加装备加成。

        Args:
            hero: 英雄实例
        """
        # 这里只计算装备加成，不修改基础属性
        # 在实际应用中，可能需要先重置到基础属性再计算
        # 但为了简化，我们假设调用者会处理基础属性
        pass

    def get_equipment_stats_for_hero(
        self, hero: Hero, player_equipment_bag: list[dict[str, Any]]
    ) -> EquipmentStats:
        """
        获取英雄身上所有装备的属性总和

        Args:
            hero: 英雄实例
            player_equipment_bag: 玩家装备背包

        Returns:
            EquipmentStats: 装备属性总和
        """
        total_stats = EquipmentStats()

        for eq_instance_id in hero.equipment:
            instance = self._get_equipment_instance(player_equipment_bag, eq_instance_id)
            if instance:
                eq_config = self.equipment_manager.get_equipment(instance.equipment_id)
                if eq_config:
                    total_stats = total_stats + eq_config.stats

        return total_stats

    def add_equipment_to_bag(
        self, player_equipment_bag: list[dict[str, Any]], equipment_id: str
    ) -> EquipmentInstance:
        """
        添加装备到背包

        Args:
            player_equipment_bag: 玩家装备背包
            equipment_id: 装备配置ID

        Returns:
            EquipmentInstance: 新创建的装备实例
        """
        import time

        instance = EquipmentInstance(
            instance_id=self._generate_instance_id(),
            equipment_id=equipment_id,
            equipped_to=None,
            acquired_at=int(time.time() * 1000),
        )
        player_equipment_bag.append(instance.to_dict())
        return instance


# ============================================================================
# 便捷函数
# ============================================================================


def create_equipment_service(config_path: str | None = None) -> EquipmentService:
    """
    创建装备服务实例

    Args:
        config_path: 装备配置文件路径

    Returns:
        EquipmentService: 装备服务实例
    """
    manager = EquipmentManager(config_path)
    return EquipmentService(manager)
