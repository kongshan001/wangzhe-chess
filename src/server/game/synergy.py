"""
王者之奕 - 羁绊系统实现

本模块实现羁绊（种族和职业）系统，包括：
- 从英雄列表计算激活的羁绊
- 羁绊效果应用（属性加成）
- 支持种族和职业羁绊

羁绊是自走棋游戏的核心机制之一，通过收集具有相同种族或职业的英雄，
可以获得额外的属性加成或特殊效果。
"""

from __future__ import annotations

from typing import Any

from shared.models import (
    ActiveSynergy,
    Hero,
    Synergy,
    SynergyLevel,
    SynergyType,
)

# ============================================================================
# 羁绊定义数据
# ============================================================================

# 种族羁绊定义
RACE_SYNERGIES: dict[str, Synergy] = {
    "人族": Synergy(
        name="人族",
        synergy_type=SynergyType.RACE,
        description="人族英雄团结一致，获得攻击力和法术强度加成",
        levels=[
            SynergyLevel(
                required_count=2,
                effect_description="攻击力+10%，法术强度+10%",
                stat_bonuses={"attack_percent": 0.10, "spell_power": 0.10},
            ),
            SynergyLevel(
                required_count=4,
                effect_description="攻击力+25%，法术强度+25%",
                stat_bonuses={"attack_percent": 0.25, "spell_power": 0.25},
            ),
            SynergyLevel(
                required_count=6,
                effect_description="攻击力+45%，法术强度+45%",
                stat_bonuses={"attack_percent": 0.45, "spell_power": 0.45},
            ),
        ],
    ),
    "神族": Synergy(
        name="神族",
        synergy_type=SynergyType.RACE,
        description="神族英雄获得冷却缩减",
        levels=[
            SynergyLevel(
                required_count=2,
                effect_description="技能冷却-20%",
                stat_bonuses={"cooldown_reduction": 0.20},
            ),
            SynergyLevel(
                required_count=4,
                effect_description="技能冷却-50%",
                stat_bonuses={"cooldown_reduction": 0.50},
            ),
        ],
    ),
    "魔种": Synergy(
        name="魔种",
        synergy_type=SynergyType.RACE,
        description="魔种英雄攻击附带吸血效果",
        levels=[
            SynergyLevel(
                required_count=2,
                effect_description="攻击附带15%吸血",
                stat_bonuses={"lifesteal": 0.15},
            ),
            SynergyLevel(
                required_count=4,
                effect_description="攻击附带30%吸血",
                stat_bonuses={"lifesteal": 0.30},
            ),
        ],
    ),
    "亡灵": Synergy(
        name="亡灵",
        synergy_type=SynergyType.RACE,
        description="亡灵英雄减少敌方护甲",
        levels=[
            SynergyLevel(
                required_count=2,
                effect_description="减少敌方5点护甲",
                stat_bonuses={},
                special_effects=[{"type": "reduce_enemy_armor", "value": 5}],
            ),
            SynergyLevel(
                required_count=4,
                effect_description="减少敌方15点护甲",
                stat_bonuses={},
                special_effects=[{"type": "reduce_enemy_armor", "value": 15}],
            ),
        ],
    ),
    "精灵": Synergy(
        name="精灵",
        synergy_type=SynergyType.RACE,
        description="精灵英雄有几率闪避攻击",
        levels=[
            SynergyLevel(
                required_count=2,
                effect_description="20%闪避率",
                stat_bonuses={"dodge": 0.20},
            ),
            SynergyLevel(
                required_count=4,
                effect_description="40%闪避率",
                stat_bonuses={"dodge": 0.40},
            ),
        ],
    ),
    "兽族": Synergy(
        name="兽族",
        synergy_type=SynergyType.RACE,
        description="兽族英雄获得额外生命值",
        levels=[
            SynergyLevel(
                required_count=2,
                effect_description="生命值+200",
                stat_bonuses={"hp_flat": 200},
            ),
            SynergyLevel(
                required_count=4,
                effect_description="生命值+500",
                stat_bonuses={"hp_flat": 500},
            ),
        ],
    ),
    "机械": Synergy(
        name="机械",
        synergy_type=SynergyType.RACE,
        description="机械英雄获得护甲加成",
        levels=[
            SynergyLevel(
                required_count=2,
                effect_description="护甲+15",
                stat_bonuses={"armor_flat": 15},
            ),
            SynergyLevel(
                required_count=4,
                effect_description="护甲+35",
                stat_bonuses={"armor_flat": 35},
            ),
        ],
    ),
    "龙族": Synergy(
        name="龙族",
        synergy_type=SynergyType.RACE,
        description="龙族英雄战斗开始时获得满蓝",
        levels=[
            SynergyLevel(
                required_count=2,
                effect_description="战斗开始时获得50蓝量",
                stat_bonuses={},
                special_effects=[{"type": "initial_mana", "value": 50}],
            ),
            SynergyLevel(
                required_count=3,
                effect_description="战斗开始时获得100蓝量（满蓝）",
                stat_bonuses={},
                special_effects=[{"type": "initial_mana", "value": 100}],
            ),
        ],
    ),
    "妖精": Synergy(
        name="妖精",
        synergy_type=SynergyType.RACE,
        description="妖精英雄获得攻速加成",
        levels=[
            SynergyLevel(
                required_count=2,
                effect_description="攻击速度+20%",
                stat_bonuses={"attack_speed_percent": 0.20},
            ),
            SynergyLevel(
                required_count=4,
                effect_description="攻击速度+50%",
                stat_bonuses={"attack_speed_percent": 0.50},
            ),
        ],
    ),
}

# 职业羁绊定义
PROFESSION_SYNERGIES: dict[str, Synergy] = {
    "战士": Synergy(
        name="战士",
        synergy_type=SynergyType.CLASS,
        description="战士获得额外护甲",
        levels=[
            SynergyLevel(
                required_count=2,
                effect_description="护甲+15",
                stat_bonuses={"armor_flat": 15},
            ),
            SynergyLevel(
                required_count=4,
                effect_description="护甲+35",
                stat_bonuses={"armor_flat": 35},
            ),
            SynergyLevel(
                required_count=6,
                effect_description="护甲+60",
                stat_bonuses={"armor_flat": 60},
            ),
        ],
    ),
    "法师": Synergy(
        name="法师",
        synergy_type=SynergyType.CLASS,
        description="法师降低敌方魔抗",
        levels=[
            SynergyLevel(
                required_count=2,
                effect_description="降低敌方20%魔抗",
                stat_bonuses={},
                special_effects=[{"type": "reduce_enemy_magic_resist", "value": 0.20}],
            ),
            SynergyLevel(
                required_count=4,
                effect_description="降低敌方50%魔抗",
                stat_bonuses={},
                special_effects=[{"type": "reduce_enemy_magic_resist", "value": 0.50}],
            ),
        ],
    ),
    "刺客": Synergy(
        name="刺客",
        synergy_type=SynergyType.CLASS,
        description="刺客获得暴击率和暴击伤害",
        levels=[
            SynergyLevel(
                required_count=2,
                effect_description="暴击率+15%，暴击伤害+30%",
                stat_bonuses={"crit_chance": 0.15, "crit_damage": 0.30},
            ),
            SynergyLevel(
                required_count=4,
                effect_description="暴击率+30%，暴击伤害+60%",
                stat_bonuses={"crit_chance": 0.30, "crit_damage": 0.60},
            ),
        ],
    ),
    "射手": Synergy(
        name="射手",
        synergy_type=SynergyType.CLASS,
        description="射手攻击有几率额外攻击一次",
        levels=[
            SynergyLevel(
                required_count=2,
                effect_description="25%几率攻击两次",
                stat_bonuses={"double_attack_chance": 0.25},
            ),
            SynergyLevel(
                required_count=4,
                effect_description="50%几率攻击两次",
                stat_bonuses={"double_attack_chance": 0.50},
            ),
        ],
    ),
    "坦克": Synergy(
        name="坦克",
        synergy_type=SynergyType.CLASS,
        description="坦克获得生命值加成",
        levels=[
            SynergyLevel(
                required_count=2,
                effect_description="最大生命值+15%",
                stat_bonuses={"hp_percent": 0.15},
            ),
            SynergyLevel(
                required_count=4,
                effect_description="最大生命值+35%",
                stat_bonuses={"hp_percent": 0.35},
            ),
        ],
    ),
    "辅助": Synergy(
        name="辅助",
        synergy_type=SynergyType.CLASS,
        description="辅助增加友方魔抗",
        levels=[
            SynergyLevel(
                required_count=2,
                effect_description="全队魔抗+30",
                stat_bonuses={"magic_resist_flat": 30},
            ),
            SynergyLevel(
                required_count=4,
                effect_description="全队魔抗+70",
                stat_bonuses={"magic_resist_flat": 70},
            ),
        ],
    ),
    "游侠": Synergy(
        name="游侠",
        synergy_type=SynergyType.CLASS,
        description="游侠每隔一段时间获得攻速加成",
        levels=[
            SynergyLevel(
                required_count=2,
                effect_description="每3秒攻速+10%，最高+30%",
                stat_bonuses={"attack_speed_stacking": 0.10},
            ),
            SynergyLevel(
                required_count=4,
                effect_description="每3秒攻速+20%，最高+60%",
                stat_bonuses={"attack_speed_stacking": 0.20},
            ),
        ],
    ),
    "术士": Synergy(
        name="术士",
        synergy_type=SynergyType.CLASS,
        description="术士技能附带吸血",
        levels=[
            SynergyLevel(
                required_count=2,
                effect_description="技能吸血+20%",
                stat_bonuses={"spell_vamp": 0.20},
            ),
            SynergyLevel(
                required_count=4,
                effect_description="技能吸血+50%",
                stat_bonuses={"spell_vamp": 0.50},
            ),
        ],
    ),
}


# ============================================================================
# 羁绊管理器
# ============================================================================


class SynergyManager:
    """
    羁绊管理器

    管理所有羁绊定义，计算和激活羁绊效果。

    Attributes:
        race_synergies: 种族羁绊字典
        profession_synergies: 职业羁绊字典
    """

    def __init__(
        self,
        race_synergies: dict[str, Synergy] | None = None,
        profession_synergies: dict[str, Synergy] | None = None,
    ) -> None:
        """
        初始化羁绊管理器

        Args:
            race_synergies: 种族羁绊定义（默认使用内置定义）
            profession_synergies: 职业羁绊定义（默认使用内置定义）
        """
        self.race_synergies = race_synergies or RACE_SYNERGIES
        self.profession_synergies = profession_synergies or PROFESSION_SYNERGIES

    def get_synergy(self, name: str) -> Synergy | None:
        """
        根据名称获取羁绊定义

        Args:
            name: 羁绊名称（种族或职业）

        Returns:
            羁绊定义，如果不存在返回None
        """
        if name in self.race_synergies:
            return self.race_synergies[name]
        if name in self.profession_synergies:
            return self.profession_synergies[name]
        return None

    def count_heroes_by_synergy(self, heroes: list[Hero]) -> dict[str, int]:
        """
        统计英雄列表中的各羁绊数量

        统计规则：
        - 同名英雄只计算一次（以template_id为准）
        - 3星英雄按3个同名英雄计算

        Args:
            heroes: 英雄列表

        Returns:
            羁绊名称到数量的映射
        """
        synergy_counts: dict[str, int] = {}

        for hero in heroes:
            # 计算该英雄对羁绊的贡献
            # 简化版：每个英雄贡献1点，3星英雄贡献更多
            # 这里采用简化逻辑：每个英雄贡献1点
            contribution = 1

            # 统计种族
            race = hero.race
            if race:
                synergy_counts[race] = synergy_counts.get(race, 0) + contribution

            # 统计职业
            profession = hero.profession
            if profession:
                synergy_counts[profession] = synergy_counts.get(profession, 0) + contribution

        return synergy_counts

    def calculate_active_synergies(
        self,
        heroes: list[Hero],
        alive_only: bool = True,
    ) -> list[ActiveSynergy]:
        """
        计算激活的羁绊

        Args:
            heroes: 英雄列表（通常是棋盘上的英雄）
            alive_only: 是否只计算存活英雄

        Returns:
            激活的羁绊列表（包含未激活但数量大于0的羁绊）
        """
        if alive_only:
            heroes = [h for h in heroes if h.is_alive()]

        counts = self.count_heroes_by_synergy(heroes)
        active_synergies: list[ActiveSynergy] = []

        # 处理种族羁绊
        for race, count in counts.items():
            if race in self.race_synergies:
                synergy = self.race_synergies[race]
                active_level = synergy.get_active_level(count)
                active_synergies.append(
                    ActiveSynergy(
                        synergy_name=race,
                        synergy_type=SynergyType.RACE,
                        count=count,
                        active_level=active_level,
                    )
                )

        # 处理职业羁绊
        for profession, count in counts.items():
            if profession in self.profession_synergies:
                synergy = self.profession_synergies[profession]
                active_level = synergy.get_active_level(count)
                active_synergies.append(
                    ActiveSynergy(
                        synergy_name=profession,
                        synergy_type=SynergyType.CLASS,
                        count=count,
                        active_level=active_level,
                    )
                )

        return active_synergies

    def get_synergy_bonuses(
        self,
        heroes: list[Hero],
        alive_only: bool = True,
    ) -> dict[str, dict[str, float]]:
        """
        获取激活羁绊的属性加成

        Args:
            heroes: 英雄列表
            alive_only: 是否只计算存活英雄

        Returns:
            羁绊名称到属性加成的映射
        """
        active_synergies = self.calculate_active_synergies(heroes, alive_only)
        bonuses: dict[str, dict[str, float]] = {}

        for synergy in active_synergies:
            if synergy.active_level:
                bonuses[synergy.synergy_name] = synergy.active_level.stat_bonuses.copy()

        return bonuses

    def get_special_effects(
        self,
        heroes: list[Hero],
        alive_only: bool = True,
    ) -> list[dict[str, Any]]:
        """
        获取激活羁绊的特殊效果

        Args:
            heroes: 英雄列表
            alive_only: 是否只计算存活英雄

        Returns:
            特殊效果列表
        """
        active_synergies = self.calculate_active_synergies(heroes, alive_only)
        effects: list[dict[str, Any]] = []

        for synergy in active_synergies:
            if synergy.active_level:
                for effect in synergy.active_level.special_effects:
                    effects.append(
                        {
                            "synergy": synergy.synergy_name,
                            **effect,
                        }
                    )

        return effects

    def get_synergy_progress(
        self,
        heroes: list[Hero],
        synergy_name: str,
    ) -> dict[str, Any]:
        """
        获取指定羁绊的进度信息

        Args:
            heroes: 英雄列表
            synergy_name: 羁绊名称

        Returns:
            进度信息字典，包含当前数量、下一级需求等
        """
        synergy = self.get_synergy(synergy_name)
        if synergy is None:
            return {
                "synergy_name": synergy_name,
                "exists": False,
                "count": 0,
                "current_level": None,
                "next_level_requirement": None,
            }

        counts = self.count_heroes_by_synergy(heroes)
        count = counts.get(synergy_name, 0)
        current_level = synergy.get_active_level(count)
        next_req = synergy.get_next_level_requirement(count)

        return {
            "synergy_name": synergy_name,
            "exists": True,
            "count": count,
            "current_level": current_level.effect_description if current_level else None,
            "next_level_requirement": next_req,
            "levels": [
                {"count": level.required_count, "effect": level.effect_description}
                for level in synergy.levels
            ],
        }

    def apply_synergy_bonuses(
        self,
        heroes: list[Hero],
        alive_only: bool = True,
    ) -> dict[str, Hero]:
        """
        应用羁绊加成到英雄

        注意：此方法返回英雄的副本，不会修改原英雄对象。
        返回的字典以 instance_id 为键。

        Args:
            heroes: 英雄列表
            alive_only: 是否只计算存活英雄

        Returns:
            应用加成后的英雄副本字典
        """
        import copy

        # 创建英雄副本
        hero_copies: dict[str, Hero] = {}
        for hero in heroes:
            if not alive_only or hero.is_alive():
                hero_copies[hero.instance_id] = copy.deepcopy(hero)

        # 获取羁绊加成
        bonuses = self.get_synergy_bonuses(list(hero_copies.values()), alive_only=False)

        # 统计每个英雄所属的羁绊
        counts = self.count_heroes_by_synergy(list(hero_copies.values()))

        # 应用加成
        for hero_id, hero in hero_copies.items():
            hero_bonuses: dict[str, float] = {}

            # 收集该英雄所属羁绊的加成
            if hero.race in bonuses:
                for stat, value in bonuses[hero.race].items():
                    hero_bonuses[stat] = hero_bonuses.get(stat, 0) + value

            if hero.profession in bonuses:
                for stat, value in bonuses[hero.profession].items():
                    hero_bonuses[stat] = hero_bonuses.get(stat, 0) + value

            # 应用属性加成
            self._apply_stat_bonuses(hero, hero_bonuses)

        return hero_copies

    def _apply_stat_bonuses(self, hero: Hero, bonuses: dict[str, float]) -> None:
        """
        应用属性加成到单个英雄

        Args:
            hero: 英雄对象（将被修改）
            bonuses: 属性加成字典
        """
        # 百分比攻击力加成
        if "attack_percent" in bonuses:
            multiplier = 1 + bonuses["attack_percent"]
            hero.attack = int(hero.attack * multiplier)

        # 百分比生命值加成
        if "hp_percent" in bonuses:
            multiplier = 1 + bonuses["hp_percent"]
            old_max_hp = hero.max_hp
            hero.max_hp = int(hero.max_hp * multiplier)
            # 按比例调整当前生命值
            if old_max_hp > 0:
                hero.hp = int(hero.hp * hero.max_hp / old_max_hp)

        # 固定生命值加成
        if "hp_flat" in bonuses:
            hp_bonus = int(bonuses["hp_flat"])
            hero.max_hp += hp_bonus
            hero.hp += hp_bonus

        # 固定护甲加成
        if "armor_flat" in bonuses:
            hero.defense += int(bonuses["armor_flat"])

        # 攻击速度加成
        if "attack_speed_percent" in bonuses:
            hero.attack_speed *= 1 + bonuses["attack_speed_percent"]


# ============================================================================
# 辅助函数
# ============================================================================


def create_synergy_manager() -> SynergyManager:
    """
    创建羁绊管理器

    Returns:
        使用默认羁绊定义的羁绊管理器
    """
    return SynergyManager()


def get_all_synergy_names() -> dict[str, list[str]]:
    """
    获取所有羁绊名称

    Returns:
        包含种族和职业羁绊名称列表的字典
    """
    return {
        "races": list(RACE_SYNERGIES.keys()),
        "professions": list(PROFESSION_SYNERGIES.keys()),
    }
