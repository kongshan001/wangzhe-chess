"""
王者之奕 - 核心数据模型

本模块定义了游戏中所有核心数据结构，使用 dataclass 实现：
- Hero: 英雄实例
- Board: 棋盘
- Player: 玩家状态
- Synergy: 羁绊定义
- BattleResult: 战斗结果

所有模型都支持序列化和反序列化，便于网络传输。

优化记录:
- 2026-02-21: find_nearest_enemy 性能优化 O(n log n) -> O(n) (M-003)
- 2026-02-21: from_dict 添加输入验证 (M-007)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .constants import (
    BENCH_SIZE,
    BOARD_HEIGHT,
    BOARD_WIDTH,
    INITIAL_MANA,
    INITIAL_PLAYER_HP,
    MAX_MANA,
)

# ============================================================================
# 枚举类型
# ============================================================================


class HeroState(Enum):
    """英雄战斗状态"""

    IDLE = "idle"  # 空闲
    MOVING = "moving"  # 移动中
    ATTACKING = "attacking"  # 攻击中
    CASTING = "casting"  # 释放技能中
    DEAD = "dead"  # 死亡


class PlayerState(Enum):
    """玩家状态"""

    WAITING = "waiting"  # 等待中
    PREPARING = "preparing"  # 准备阶段
    BATTLING = "battling"  # 战斗阶段
    ELIMINATED = "eliminated"  # 已淘汰


class RoomState(Enum):
    """房间状态"""

    WAITING = "waiting"  # 等待玩家加入
    PREPARING = "preparing"  # 准备阶段
    BATTLING = "battling"  # 战斗阶段
    SETTLING = "settling"  # 结算阶段
    GAME_OVER = "game_over"  # 游戏结束


class SynergyType(Enum):
    """羁绊类型"""

    RACE = "race"  # 种族羁绊
    CLASS = "class"  # 职业羁绊


class DamageType(Enum):
    """伤害类型"""

    PHYSICAL = "physical"  # 物理伤害
    MAGICAL = "magical"  # 法术伤害
    TRUE = "true"  # 真实伤害


# ============================================================================
# 英雄相关模型
# ============================================================================


@dataclass
class Skill:
    """
    英雄技能定义

    Attributes:
        name: 技能名称
        description: 技能描述
        mana_cost: 技能蓝耗
        damage: 技能伤害值
        damage_type: 伤害类型
        target_type: 目标类型 (single/area/all)
        cooldown: 冷却时间（毫秒）
        effect_data: 额外效果数据
    """

    name: str
    description: str = ""
    mana_cost: int = 50
    damage: int = 0
    damage_type: DamageType = DamageType.MAGICAL
    target_type: str = "single"  # single, area, all, self
    cooldown: int = 0
    effect_data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """序列化为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "mana_cost": self.mana_cost,
            "damage": self.damage,
            "damage_type": self.damage_type.value,
            "target_type": self.target_type,
            "cooldown": self.cooldown,
            "effect_data": self.effect_data,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Skill:
        """从字典反序列化"""
        # 输入验证
        if not isinstance(data, dict):
            raise TypeError("data must be a dictionary")
        if "name" not in data:
            raise KeyError("missing required field: name")

        # 验证数值范围
        mana_cost = data.get("mana_cost", 50)
        if not isinstance(mana_cost, int) or mana_cost < 0:
            raise ValueError("mana_cost must be a non-negative integer")

        damage = data.get("damage", 0)
        if not isinstance(damage, int) or damage < 0:
            raise ValueError("damage must be a non-negative integer")

        cooldown = data.get("cooldown", 0)
        if not isinstance(cooldown, int) or cooldown < 0:
            raise ValueError("cooldown must be a non-negative integer")

        return cls(
            name=data["name"],
            description=data.get("description", ""),
            mana_cost=mana_cost,
            damage=damage,
            damage_type=DamageType(data.get("damage_type", "magical")),
            target_type=data.get("target_type", "single"),
            cooldown=cooldown,
            effect_data=data.get("effect_data", {}),
        )


@dataclass
class HeroTemplate:
    """
    英雄模板（配置数据）

    定义英雄的基础属性，不包含实例状态。
    从配置文件加载后创建 HeroTemplate 实例。

    Attributes:
        hero_id: 英雄唯一ID（配置ID）
        name: 英雄名称
        cost: 购买费用 (1-5)
        race: 种族（羁绊）
        profession: 职业（羁绊）
        base_hp: 基础生命值
        base_attack: 基础攻击力
        base_defense: 基础防御力
        attack_speed: 攻击速度（每秒攻击次数）
        skill: 技能定义
    """

    hero_id: str
    name: str
    cost: int
    race: str
    profession: str
    base_hp: int
    base_attack: int
    base_defense: int
    attack_speed: float
    skill: Skill | None = None

    def to_dict(self) -> dict[str, Any]:
        """序列化为字典"""
        return {
            "hero_id": self.hero_id,
            "name": self.name,
            "cost": self.cost,
            "race": self.race,
            "profession": self.profession,
            "base_hp": self.base_hp,
            "base_attack": self.base_attack,
            "base_defense": self.base_defense,
            "attack_speed": self.attack_speed,
            "skill": self.skill.to_dict() if self.skill else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HeroTemplate:
        """从字典反序列化"""
        # 输入验证
        if not isinstance(data, dict):
            raise TypeError("data must be a dictionary")

        required_fields = [
            "hero_id",
            "name",
            "cost",
            "race",
            "profession",
            "base_hp",
            "base_attack",
            "base_defense",
            "attack_speed",
        ]
        for field_name in required_fields:
            if field_name not in data:
                raise KeyError(f"missing required field: {field_name}")

        # 验证数值范围
        cost = data["cost"]
        if not isinstance(cost, int) or not (1 <= cost <= 5):
            raise ValueError("cost must be an integer between 1 and 5")

        for stat_field in ["base_hp", "base_attack", "base_defense"]:
            value = data[stat_field]
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"{stat_field} must be a non-negative integer")

        attack_speed = data["attack_speed"]
        if not isinstance(attack_speed, (int, float)) or attack_speed <= 0:
            raise ValueError("attack_speed must be a positive number")

        skill_data = data.get("skill")
        skill = Skill.from_dict(skill_data) if skill_data else None
        return cls(
            hero_id=data["hero_id"],
            name=data["name"],
            cost=cost,
            race=data["race"],
            profession=data["profession"],
            base_hp=data["base_hp"],
            base_attack=data["base_attack"],
            base_defense=data["base_defense"],
            attack_speed=attack_speed,
            skill=skill,
        )


@dataclass
class Position:
    """
    棋盘位置

    Attributes:
        x: 横坐标 (0-7)
        y: 纵坐标 (0-7)
    """

    x: int
    y: int

    def __post_init__(self) -> None:
        if not (0 <= self.x < BOARD_WIDTH and 0 <= self.y < BOARD_HEIGHT):
            raise ValueError(f"Invalid position: ({self.x}, {self.y})")

    def to_tuple(self) -> tuple[int, int]:
        """转换为元组"""
        return (self.x, self.y)

    def distance_to(self, other: Position) -> int:
        """计算到另一个位置的曼哈顿距离"""
        return abs(self.x - other.x) + abs(self.y - other.y)

    def euclidean_distance(self, other: Position) -> float:
        """计算欧几里得距离"""
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5

    def to_dict(self) -> dict[str, int]:
        """序列化为字典"""
        return {"x": self.x, "y": self.y}

    @classmethod
    def from_dict(cls, data: dict[str, int]) -> Position:
        """从字典反序列化"""
        return cls(x=data["x"], y=data["y"])


@dataclass
class Hero:
    """
    英雄实例

    代表棋盘上的一个具体英雄，包含运行时状态。

    Attributes:
        instance_id: 英雄实例唯一ID（游戏中唯一）
        template_id: 英雄模板ID（指向HeroTemplate）
        name: 英雄名称
        cost: 购买费用
        star: 星级 (1-3)
        race: 种族
        profession: 职业
        max_hp: 最大生命值
        hp: 当前生命值
        attack: 攻击力
        defense: 防御力
        attack_speed: 攻击速度
        skill: 技能
        position: 棋盘位置（None表示在备战席）
        mana: 当前蓝量
        state: 战斗状态
    """

    instance_id: str
    template_id: str
    name: str
    cost: int
    star: int
    race: str
    profession: str
    max_hp: int
    hp: int
    attack: int
    defense: int
    attack_speed: float
    skill: Skill | None = None
    position: Position | None = None
    mana: int = INITIAL_MANA
    state: HeroState = HeroState.IDLE
    equipment: list[str] = field(default_factory=list)  # 装备实例ID列表（最多3个）

    def __post_init__(self) -> None:
        if self.hp > self.max_hp:
            self.hp = self.max_hp
        if self.mana > MAX_MANA:
            self.mana = MAX_MANA

    def is_alive(self) -> bool:
        """检查英雄是否存活"""
        return self.hp > 0

    def is_on_board(self) -> bool:
        """检查英雄是否在棋盘上"""
        return self.position is not None

    def take_damage(self, damage: int, damage_type: DamageType = DamageType.PHYSICAL) -> int:
        """
        受到伤害

        Args:
            damage: 原始伤害值
            damage_type: 伤害类型

        Returns:
            实际受到的伤害值
        """
        # 已死亡的英雄不再受伤
        if self.hp <= 0 or self.state == HeroState.DEAD:
            return 0

        if damage_type == DamageType.TRUE:
            # 真实伤害无视防御
            actual_damage = damage
        else:
            # 物理和魔法伤害受防御减免
            # 简化公式：实际伤害 = 伤害 * 100 / (100 + 防御)
            actual_damage = int(damage * 100 / (100 + self.defense))

        self.hp = max(0, self.hp - actual_damage)
        if self.hp <= 0:
            self.state = HeroState.DEAD

        return actual_damage

    def heal(self, amount: int) -> int:
        """
        治疗

        Args:
            amount: 治疗量

        Returns:
            实际治疗量
        """
        old_hp = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - old_hp

    def gain_mana(self, amount: int) -> int:
        """
        获得蓝量

        Args:
            amount: 蓝量增加量

        Returns:
            实际获得的蓝量（考虑上限）
        """
        old_mana = self.mana
        self.mana = min(MAX_MANA, self.mana + amount)
        return self.mana - old_mana

    def can_cast_skill(self) -> bool:
        """检查是否可以释放技能"""
        if self.skill is None:
            return False
        return self.mana >= self.skill.mana_cost and self.is_alive()

    def use_skill(self) -> bool:
        """
        使用技能（消耗蓝量）

        Returns:
            是否成功使用
        """
        if not self.can_cast_skill():
            return False
        self.mana -= self.skill.mana_cost
        return True

    def to_dict(self) -> dict[str, Any]:
        """序列化为字典"""
        return {
            "instance_id": self.instance_id,
            "template_id": self.template_id,
            "name": self.name,
            "cost": self.cost,
            "star": self.star,
            "race": self.race,
            "profession": self.profession,
            "max_hp": self.max_hp,
            "hp": self.hp,
            "attack": self.attack,
            "defense": self.defense,
            "attack_speed": self.attack_speed,
            "skill": self.skill.to_dict() if self.skill else None,
            "position": self.position.to_dict() if self.position else None,
            "mana": self.mana,
            "state": self.state.value,
            "equipment": self.equipment.copy(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Hero:
        """从字典反序列化"""
        # 输入验证
        if not isinstance(data, dict):
            raise TypeError("data must be a dictionary")

        required_fields = [
            "instance_id",
            "template_id",
            "name",
            "cost",
            "star",
            "race",
            "profession",
            "max_hp",
            "hp",
            "attack",
            "defense",
            "attack_speed",
        ]
        for field_name in required_fields:
            if field_name not in data:
                raise KeyError(f"missing required field: {field_name}")

        # 验证数值范围
        cost = data["cost"]
        if not isinstance(cost, int) or not (1 <= cost <= 5):
            raise ValueError("cost must be an integer between 1 and 5")

        star = data["star"]
        if not isinstance(star, int) or not (1 <= star <= 3):
            raise ValueError("star must be an integer between 1 and 3")

        for stat_field in ["max_hp", "hp", "attack", "defense"]:
            value = data[stat_field]
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"{stat_field} must be a non-negative integer")

        attack_speed = data["attack_speed"]
        if not isinstance(attack_speed, (int, float)) or attack_speed <= 0:
            raise ValueError("attack_speed must be a positive number")

        skill_data = data.get("skill")
        skill = Skill.from_dict(skill_data) if skill_data else None

        position_data = data.get("position")
        position = Position.from_dict(position_data) if position_data else None

        return cls(
            instance_id=data["instance_id"],
            template_id=data["template_id"],
            name=data["name"],
            cost=cost,
            star=star,
            race=data["race"],
            profession=data["profession"],
            max_hp=data["max_hp"],
            hp=data["hp"],
            attack=data["attack"],
            defense=data["defense"],
            attack_speed=attack_speed,
            skill=skill,
            position=position,
            mana=data.get("mana", INITIAL_MANA),
            state=HeroState(data.get("state", "idle")),
            equipment=data.get("equipment", []),
        )

    @classmethod
    def create_from_template(
        cls,
        template: HeroTemplate,
        instance_id: str,
        star: int = 1,
        position: Position | None = None,
    ) -> Hero:
        """
        从模板创建英雄实例

        Args:
            template: 英雄模板
            instance_id: 实例ID
            star: 星级
            position: 初始位置

        Returns:
            英雄实例
        """
        # 星级加成计算
        star_multiplier = {
            1: 1.0,
            2: 1.8,
            3: 3.24,  # 1.8 * 1.8
        }.get(star, 1.0)

        return cls(
            instance_id=instance_id,
            template_id=template.hero_id,
            name=template.name,
            cost=template.cost,
            star=star,
            race=template.race,
            profession=template.profession,
            max_hp=int(template.base_hp * star_multiplier),
            hp=int(template.base_hp * star_multiplier),
            attack=int(template.base_attack * star_multiplier),
            defense=int(template.base_defense * star_multiplier),
            attack_speed=template.attack_speed,
            skill=template.skill,
            position=position,
            equipment=[],
        )


# ============================================================================
# 棋盘模型
# ============================================================================


@dataclass
class Board:
    """
    战斗棋盘

    8x8 格子的棋盘，用于放置英雄进行战斗。

    Attributes:
        grid: 二维数组，存储每个格子上的英雄实例ID
        heroes: 英雄实例字典 {instance_id: Hero}
        owner_id: 棋盘所有者ID
    """

    grid: list[list[str | None]] = field(
        default_factory=lambda: [[None for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
    )
    heroes: dict[str, Hero] = field(default_factory=dict)
    owner_id: str = ""

    def __post_init__(self) -> None:
        if len(self.grid) != BOARD_HEIGHT or len(self.grid[0]) != BOARD_WIDTH:
            self.grid = [[None for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]

    def place_hero(self, hero: Hero, pos: Position) -> bool:
        """
        在指定位置放置英雄

        Args:
            hero: 英雄实例
            pos: 目标位置

        Returns:
            是否成功放置
        """
        if self.grid[pos.y][pos.x] is not None:
            return False

        # 如果英雄已在棋盘上其他位置，先移除
        if hero.position is not None:
            self.remove_hero(hero.instance_id)

        self.grid[pos.y][pos.x] = hero.instance_id
        hero.position = pos
        self.heroes[hero.instance_id] = hero
        return True

    def remove_hero(self, instance_id: str) -> Hero | None:
        """
        移除英雄

        Args:
            instance_id: 英雄实例ID

        Returns:
            被移除的英雄，如果不存在返回None
        """
        hero = self.heroes.pop(instance_id, None)
        if hero is None:
            return None

        if hero.position is not None:
            self.grid[hero.position.y][hero.position.x] = None
            hero.position = None

        return hero

    def get_hero_at(self, pos: Position) -> Hero | None:
        """
        获取指定位置的英雄

        Args:
            pos: 位置

        Returns:
            英雄实例，如果位置为空返回None
        """
        instance_id = self.grid[pos.y][pos.x]
        if instance_id is None:
            return None
        return self.heroes.get(instance_id)

    def get_all_heroes(self, alive_only: bool = True) -> list[Hero]:
        """
        获取所有英雄

        Args:
            alive_only: 是否只返回存活英雄

        Returns:
            英雄列表
        """
        heroes = list(self.heroes.values())
        if alive_only:
            heroes = [h for h in heroes if h.is_alive()]
        return heroes

    def get_hero_count(self, alive_only: bool = True) -> int:
        """
        获取英雄数量

        Args:
            alive_only: 是否只计算存活英雄

        Returns:
            英雄数量
        """
        return len(self.get_all_heroes(alive_only))

    def find_nearest_enemy(self, from_pos: Position, enemy_board: Board) -> Hero | None:
        """
        寻找最近的敌人

        Args:
            from_pos: 起始位置
            enemy_board: 敌方棋盘

        Returns:
            最近的敌方英雄，如果没有返回None

        Note:
            性能优化: 使用 min() 替代 sort()，复杂度从 O(n log n) 降为 O(n)
        """
        enemies = enemy_board.get_all_heroes(alive_only=True)
        if not enemies:
            return None

        # 使用 min() 只找最近的一个，O(n) 复杂度
        return min(
            enemies,
            key=lambda e: from_pos.distance_to(e.position) if e.position else float("inf"),
            default=None,
        )

    def to_dict(self) -> dict[str, Any]:
        """序列化为字典"""
        return {
            "grid": self.grid,
            "heroes": {k: v.to_dict() for k, v in self.heroes.items()},
            "owner_id": self.owner_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Board:
        """从字典反序列化"""
        heroes_data = data.get("heroes", {})
        heroes = {k: Hero.from_dict(v) for k, v in heroes_data.items()}

        board = cls(
            grid=data.get("grid", [[None] * BOARD_WIDTH for _ in range(BOARD_HEIGHT)]),
            heroes=heroes,
            owner_id=data.get("owner_id", ""),
        )
        return board

    @classmethod
    def create_empty(cls, owner_id: str = "") -> Board:
        """创建空棋盘"""
        return cls(owner_id=owner_id)


# ============================================================================
# 商店模型
# ============================================================================


@dataclass
class ShopSlot:
    """
    商店槽位

    Attributes:
        slot_index: 槽位索引 (0-4)
        hero_template_id: 英雄模板ID（None表示空槽位或已购买）
        is_locked: 是否被锁定
        is_sold: 是否已售出
    """

    slot_index: int
    hero_template_id: str | None = None
    is_locked: bool = False
    is_sold: bool = False

    def is_available(self) -> bool:
        """检查槽位是否可购买"""
        return self.hero_template_id is not None and not self.is_sold

    def to_dict(self) -> dict[str, Any]:
        """序列化为字典"""
        return {
            "slot_index": self.slot_index,
            "hero_template_id": self.hero_template_id,
            "is_locked": self.is_locked,
            "is_sold": self.is_sold,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ShopSlot:
        """从字典反序列化"""
        return cls(
            slot_index=data["slot_index"],
            hero_template_id=data.get("hero_template_id"),
            is_locked=data.get("is_locked", False),
            is_sold=data.get("is_sold", False),
        )


@dataclass
class Shop:
    """
    商店

    管理玩家的商店状态。

    Attributes:
        slots: 商店槽位列表
        refresh_cost: 刷新费用
    """

    slots: list[ShopSlot] = field(default_factory=list)
    refresh_cost: int = 2

    def __post_init__(self) -> None:
        if not self.slots:
            from .constants import SHOP_SLOT_COUNT

            self.slots = [ShopSlot(slot_index=i) for i in range(SHOP_SLOT_COUNT)]

    def get_available_slots(self) -> list[ShopSlot]:
        """获取可购买的槽位"""
        return [s for s in self.slots if s.is_available()]

    def get_slot(self, index: int) -> ShopSlot | None:
        """获取指定槽位"""
        if 0 <= index < len(self.slots):
            return self.slots[index]
        return None

    def clear_slot(self, index: int) -> None:
        """清空指定槽位"""
        if 0 <= index < len(self.slots):
            self.slots[index].hero_template_id = None
            self.slots[index].is_sold = False

    def to_dict(self) -> dict[str, Any]:
        """序列化为字典"""
        return {
            "slots": [s.to_dict() for s in self.slots],
            "refresh_cost": self.refresh_cost,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Shop:
        """从字典反序列化"""
        slots_data = data.get("slots", [])
        slots = [ShopSlot.from_dict(s) for s in slots_data]
        return cls(
            slots=slots,
            refresh_cost=data.get("refresh_cost", 2),
        )


# ============================================================================
# 玩家模型
# ============================================================================


@dataclass
class Player:
    """
    玩家状态

    存储玩家的完整游戏状态。

    Attributes:
        player_id: 玩家ID
        hp: 当前生命值
        gold: 当前金币
        level: 当前等级
        exp: 当前经验值
        board: 战斗棋盘
        bench: 备战席（英雄列表）
        hand: 手牌区（待出售的英雄）
        shop: 商店状态
        state: 玩家状态
        win_streak: 连胜场次
        lose_streak: 连败场次
        current_round: 当前回合数
        equipment_bag: 装备背包（存储未穿戴的装备）
    """

    player_id: str
    hp: int = INITIAL_PLAYER_HP
    gold: int = 0
    level: int = 1
    exp: int = 0
    board: Board = field(default_factory=Board.create_empty)
    bench: list[Hero] = field(default_factory=list)
    hand: list[Hero] = field(default_factory=list)
    shop: Shop = field(default_factory=Shop)
    state: PlayerState = PlayerState.WAITING
    win_streak: int = 0
    lose_streak: int = 0
    current_round: int = 1
    equipment_bag: list[dict[str, Any]] = field(default_factory=list)

    def is_alive(self) -> bool:
        """检查玩家是否存活"""
        return self.hp > 0

    def can_afford(self, cost: int) -> bool:
        """检查是否有足够金币"""
        return self.gold >= cost

    def spend_gold(self, amount: int) -> bool:
        """
        花费金币

        Args:
            amount: 花费金额

        Returns:
            是否成功
        """
        if not self.can_afford(amount):
            return False
        self.gold -= amount
        return True

    def earn_gold(self, amount: int) -> None:
        """获得金币"""
        self.gold += amount

    def get_field_hero_count(self) -> int:
        """获取场上英雄数量"""
        return self.board.get_hero_count(alive_only=False)

    def get_bench_hero_count(self) -> int:
        """获取备战席英雄数量"""
        return len(self.bench)

    def can_add_to_bench(self) -> bool:
        """检查是否可以向备战席添加英雄"""
        return len(self.bench) < BENCH_SIZE

    def add_to_bench(self, hero: Hero) -> bool:
        """
        将英雄添加到备战席

        Args:
            hero: 英雄实例

        Returns:
            是否成功
        """
        if not self.can_add_to_bench():
            return False
        hero.position = None
        self.bench.append(hero)
        return True

    def remove_from_bench(self, instance_id: str) -> Hero | None:
        """
        从备战席移除英雄

        Args:
            instance_id: 英雄实例ID

        Returns:
            被移除的英雄
        """
        for i, hero in enumerate(self.bench):
            if hero.instance_id == instance_id:
                return self.bench.pop(i)
        return None

    def take_damage(self, damage: int) -> int:
        """
        受到伤害

        Args:
            damage: 伤害值

        Returns:
            实际受到的伤害
        """
        old_hp = self.hp
        self.hp = max(0, self.hp - damage)
        if self.hp <= 0:
            self.state = PlayerState.ELIMINATED
        return old_hp - self.hp

    def get_all_heroes(self) -> list[Hero]:
        """获取玩家所有英雄（场上+备战席）"""
        heroes = self.board.get_all_heroes(alive_only=False)
        heroes.extend(self.bench)
        return heroes

    def to_dict(self) -> dict[str, Any]:
        """序列化为字典"""
        return {
            "player_id": self.player_id,
            "hp": self.hp,
            "gold": self.gold,
            "level": self.level,
            "exp": self.exp,
            "board": self.board.to_dict(),
            "bench": [h.to_dict() for h in self.bench],
            "hand": [h.to_dict() for h in self.hand],
            "shop": self.shop.to_dict(),
            "state": self.state.value,
            "win_streak": self.win_streak,
            "lose_streak": self.lose_streak,
            "current_round": self.current_round,
            "equipment_bag": self.equipment_bag.copy(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Player:
        """从字典反序列化"""
        board_data = data.get("board", {})
        board = Board.from_dict(board_data)

        bench_data = data.get("bench", [])
        bench = [Hero.from_dict(h) for h in bench_data]

        hand_data = data.get("hand", [])
        hand = [Hero.from_dict(h) for h in hand_data]

        shop_data = data.get("shop", {})
        shop = Shop.from_dict(shop_data)

        return cls(
            player_id=data["player_id"],
            hp=data.get("hp", INITIAL_PLAYER_HP),
            gold=data.get("gold", 0),
            level=data.get("level", 1),
            exp=data.get("exp", 0),
            board=board,
            bench=bench,
            hand=hand,
            shop=shop,
            state=PlayerState(data.get("state", "waiting")),
            win_streak=data.get("win_streak", 0),
            lose_streak=data.get("lose_streak", 0),
            current_round=data.get("current_round", 1),
            equipment_bag=data.get("equipment_bag", []),
        )


# ============================================================================
# 羁绊模型
# ============================================================================


@dataclass
class SynergyLevel:
    """
    羁绊等级定义

    Attributes:
        required_count: 激活所需数量
        effect_description: 效果描述
        stat_bonuses: 属性加成 {属性名: 加成值}
        special_effects: 特殊效果列表
    """

    required_count: int
    effect_description: str = ""
    stat_bonuses: dict[str, float] = field(default_factory=dict)
    special_effects: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """序列化为字典"""
        return {
            "required_count": self.required_count,
            "effect_description": self.effect_description,
            "stat_bonuses": self.stat_bonuses,
            "special_effects": self.special_effects,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SynergyLevel:
        """从字典反序列化"""
        return cls(
            required_count=data["required_count"],
            effect_description=data.get("effect_description", ""),
            stat_bonuses=data.get("stat_bonuses", {}),
            special_effects=data.get("special_effects", []),
        )


@dataclass
class Synergy:
    """
    羁绊定义

    定义种族或职业羁绊的效果和激活条件。

    Attributes:
        name: 羁绊名称
        synergy_type: 羁绊类型（种族/职业）
        levels: 羁绊等级列表（按激活数量递增）
        description: 羁绊描述
    """

    name: str
    synergy_type: SynergyType
    levels: list[SynergyLevel]
    description: str = ""

    def get_active_level(self, count: int) -> SynergyLevel | None:
        """
        根据数量获取激活的羁绊等级

        Args:
            count: 英雄数量

        Returns:
            激活的羁绊等级，如果未激活返回None
        """
        active_level = None
        for level in self.levels:
            if count >= level.required_count:
                active_level = level
            else:
                break
        return active_level

    def get_next_level_requirement(self, count: int) -> int | None:
        """
        获取下一级所需数量

        Args:
            count: 当前数量

        Returns:
            下一级所需数量，如果已满级返回None
        """
        for level in self.levels:
            if level.required_count > count:
                return level.required_count
        return None

    def to_dict(self) -> dict[str, Any]:
        """序列化为字典"""
        return {
            "name": self.name,
            "synergy_type": self.synergy_type.value,
            "levels": [lvl.to_dict() for lvl in self.levels],
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Synergy:
        """从字典反序列化"""
        levels_data = data.get("levels", [])
        levels = [SynergyLevel.from_dict(lvl) for lvl in levels_data]

        return cls(
            name=data["name"],
            synergy_type=SynergyType(data["synergy_type"]),
            levels=levels,
            description=data.get("description", ""),
        )


@dataclass
class ActiveSynergy:
    """
    已激活的羁绊状态

    Attributes:
        synergy_name: 羁绊名称
        synergy_type: 羁绊类型
        count: 当前数量
        active_level: 当前激活等级（None表示未激活）
    """

    synergy_name: str
    synergy_type: SynergyType
    count: int
    active_level: SynergyLevel | None = None

    def is_active(self) -> bool:
        """检查羁绊是否激活"""
        return self.active_level is not None

    def to_dict(self) -> dict[str, Any]:
        """序列化为字典"""
        return {
            "synergy_name": self.synergy_name,
            "synergy_type": self.synergy_type.value,
            "count": self.count,
            "active_level": self.active_levelevel.to_dict() if self.active_level else None,
        }


# ============================================================================
# 战斗结果模型
# ============================================================================


@dataclass
class DamageEvent:
    """
    伤害事件

    记录战斗中的单次伤害。

    Attributes:
        time_ms: 事件时间（毫秒）
        source_id: 伤害来源英雄ID
        target_id: 目标英雄ID
        damage: 伤害值
        damage_type: 伤害类型
        is_skill: 是否为技能伤害
    """

    time_ms: int
    source_id: str
    target_id: str
    damage: int
    damage_type: DamageType
    is_skill: bool = False

    def to_dict(self) -> dict[str, Any]:
        """序列化为字典"""
        return {
            "time_ms": self.time_ms,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "damage": self.damage,
            "damage_type": self.damage_type.value,
            "is_skill": self.is_skill,
        }


@dataclass
class DeathEvent:
    """
    死亡事件

    Attributes:
        time_ms: 事件时间
        hero_id: 死亡英雄ID
        killer_id: 击杀者英雄ID
    """

    time_ms: int
    hero_id: str
    killer_id: str

    def to_dict(self) -> dict[str, Any]:
        """序列化为字典"""
        return {
            "time_ms": self.time_ms,
            "hero_id": self.hero_id,
            "killer_id": self.killer_id,
        }


@dataclass
class SkillEvent:
    """
    技能释放事件

    Attributes:
        time_ms: 事件时间
        hero_id: 释放技能的英雄ID
        skill_name: 技能名称
        targets: 目标英雄ID列表
    """

    time_ms: int
    hero_id: str
    skill_name: str
    targets: list[str]

    def to_dict(self) -> dict[str, Any]:
        """序列化为字典"""
        return {
            "time_ms": self.time_ms,
            "hero_id": self.hero_id,
            "skill_name": self.skill_name,
            "targets": self.targets,
        }


@dataclass
class BattleResult:
    """
    战斗结果

    包含战斗的所有结果信息。

    Attributes:
        winner: 获胜方ID（"draw"表示平局）
        loser: 失败方ID
        player_a_damage: 玩家A受到的伤害
        player_b_damage: 玩家B受到的伤害
        survivors_a: 玩家A存活英雄ID列表
        survivors_b: 玩家B存活英雄ID列表
        battle_duration_ms: 战斗时长（毫秒）
        events: 战斗事件列表（用于回放）
        random_seed: 使用的随机种子
    """

    winner: str  # player_a_id, player_b_id, or "draw"
    loser: str
    player_a_damage: int = 0
    player_b_damage: int = 0
    survivors_a: list[str] = field(default_factory=list)
    survivors_b: list[str] = field(default_factory=list)
    battle_duration_ms: int = 0
    events: list[dict[str, Any]] = field(default_factory=list)
    random_seed: int = 0

    def is_draw(self) -> bool:
        """检查是否平局"""
        return self.winner == "draw"

    def add_event(self, event: dict[str, Any]) -> None:
        """添加战斗事件"""
        self.events.append(event)

    def to_dict(self) -> dict[str, Any]:
        """序列化为字典"""
        return {
            "winner": self.winner,
            "loser": self.loser,
            "player_a_damage": self.player_a_damage,
            "player_b_damage": self.player_b_damage,
            "survivors_a": self.survivors_a,
            "survivors_b": self.survivors_b,
            "battle_duration_ms": self.battle_duration_ms,
            "events": self.events,
            "random_seed": self.random_seed,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BattleResult:
        """从字典反序列化"""
        return cls(
            winner=data["winner"],
            loser=data["loser"],
            player_a_damage=data.get("player_a_damage", 0),
            player_b_damage=data.get("player_b_damage", 0),
            survivors_a=data.get("survivors_a", []),
            survivors_b=data.get("survivors_b", []),
            battle_duration_ms=data.get("battle_duration_ms", 0),
            events=data.get("events", []),
            random_seed=data.get("random_seed", 0),
        )


# ============================================================================
# 辅助函数
# ============================================================================


def create_uuid() -> str:
    """生成唯一ID"""
    import uuid

    return str(uuid.uuid4())
