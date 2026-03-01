"""
王者之奕 - 英雄池管理

本模块管理游戏中的英雄池，包括：
- 英雄配置加载
- 共享英雄池抽取
- 商店刷新逻辑
- 概率表管理（根据等级调整刷新概率）

英雄池是8人游戏共享的，所有玩家从同一个池中抽取英雄。
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

from shared.constants import (
    HERO_POOL_COUNTS,
    MAX_HERO_COST,
    MIN_HERO_COST,
    REFRESH_PROBABILITY,
)
from shared.models import (
    Hero,
    HeroTemplate,
    Shop,
    create_uuid,
)


class HeroPoolError(Exception):
    """英雄池操作错误"""

    pass


class HeroConfigLoader:
    """
    英雄配置加载器

    从配置文件加载英雄模板数据。

    Attributes:
        templates: 英雄模板字典 {hero_id: HeroTemplate}
        templates_by_cost: 按费用分组的模板 {cost: [HeroTemplate]}
        templates_by_race: 按种族分组的模板 {race: [HeroTemplate]}
        templates_by_profession: 按职业分组的模板 {profession: [HeroTemplate]}
    """

    def __init__(self) -> None:
        self.templates: dict[str, HeroTemplate] = {}
        self.templates_by_cost: dict[int, list[HeroTemplate]] = {
            i: [] for i in range(MIN_HERO_COST, MAX_HERO_COST + 1)
        }
        self.templates_by_race: dict[str, list[HeroTemplate]] = {}
        self.templates_by_profession: dict[str, list[HeroTemplate]] = {}

    def load_from_file(self, config_path: str | Path) -> None:
        """
        从JSON文件加载英雄配置

        Args:
            config_path: 配置文件路径

        Raises:
            FileNotFoundError: 配置文件不存在
            json.JSONDecodeError: JSON解析错误
        """
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Hero config file not found: {config_path}")

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        self.load_from_dict(data)

    def load_from_dict(self, data: dict[str, Any] | list[dict[str, Any]]) -> None:
        """
        从字典数据加载英雄配置

        Args:
            data: 配置数据，可以是字典或列表格式
        """
        # 支持列表格式或字典格式
        heroes_data = data if isinstance(data, list) else data.get("heroes", [])

        for hero_data in heroes_data:
            template = HeroTemplate.from_dict(hero_data)
            self.add_template(template)

    def add_template(self, template: HeroTemplate) -> None:
        """
        添加英雄模板

        Args:
            template: 英雄模板
        """
        self.templates[template.hero_id] = template

        # 按费用分组
        if template.cost in self.templates_by_cost:
            self.templates_by_cost[template.cost].append(template)

        # 按种族分组
        if template.race not in self.templates_by_race:
            self.templates_by_race[template.race] = []
        self.templates_by_race[template.race].append(template)

        # 按职业分组
        if template.profession not in self.templates_by_profession:
            self.templates_by_profession[template.profession] = []
        self.templates_by_profession[template.profession].append(template)

    def get_template(self, hero_id: str) -> HeroTemplate | None:
        """
        获取英雄模板

        Args:
            hero_id: 英雄ID

        Returns:
            英雄模板，如果不存在返回None
        """
        return self.templates.get(hero_id)

    def get_templates_by_cost(self, cost: int) -> list[HeroTemplate]:
        """
        获取指定费用的英雄模板

        Args:
            cost: 费用 (1-5)

        Returns:
            英雄模板列表
        """
        return self.templates_by_cost.get(cost, [])

    def get_templates_by_race(self, race: str) -> list[HeroTemplate]:
        """获取指定种族的英雄模板"""
        return self.templates_by_race.get(race, [])

    def get_templates_by_profession(self, profession: str) -> list[HeroTemplate]:
        """获取指定职业的英雄模板"""
        return self.templates_by_profession.get(profession, [])

    def get_all_templates(self) -> list[HeroTemplate]:
        """获取所有英雄模板"""
        return list(self.templates.values())


class SharedHeroPool:
    """
    共享英雄池

    8人游戏共享的英雄池，管理所有可用英雄的数量。

    每个英雄的可用数量由费用决定：
    - 1费英雄：45张
    - 2费英雄：30张
    - 3费英雄：25张
    - 4费英雄：15张
    - 5费英雄：10张

    Attributes:
        config_loader: 英雄配置加载器
        pool: 英雄池 {hero_id: 剩余数量}
        rng: 随机数生成器
    """

    def __init__(self, config_loader: HeroConfigLoader, seed: int | None = None) -> None:
        """
        初始化共享英雄池

        Args:
            config_loader: 英雄配置加载器
            seed: 随机种子（用于确定性测试）
        """
        self.config_loader = config_loader
        self.pool: dict[str, int] = {}
        self.rng = random.Random(seed)

        self._initialize_pool()

    def _initialize_pool(self) -> None:
        """初始化英雄池"""
        for template in self.config_loader.get_all_templates():
            # 根据费用确定数量
            count = HERO_POOL_COUNTS.get(template.cost, 0)
            self.pool[template.hero_id] = count

    def set_seed(self, seed: int) -> None:
        """
        设置随机种子

        Args:
            seed: 随机种子
        """
        self.rng.seed(seed)

    def get_available_count(self, hero_id: str) -> int:
        """
        获取指定英雄的可用数量

        Args:
            hero_id: 英雄ID

        Returns:
            可用数量
        """
        return self.pool.get(hero_id, 0)

    def draw_hero(self, hero_id: str) -> HeroTemplate | None:
        """
        从池中抽取指定英雄

        Args:
            hero_id: 英雄ID

        Returns:
            英雄模板，如果池中已空返回None
        """
        if self.pool.get(hero_id, 0) <= 0:
            return None

        self.pool[hero_id] -= 1
        return self.config_loader.get_template(hero_id)

    def return_hero(self, hero_id: str) -> None:
        """
        将英雄返还到池中

        Args:
            hero_id: 英雄ID
        """
        if hero_id in self.pool:
            self.pool[hero_id] += 1
        else:
            # 英雄ID不存在时，需要知道其费用来确定数量
            template = self.config_loader.get_template(hero_id)
            if template:
                max_count = HERO_POOL_COUNTS.get(template.cost, 0)
                self.pool[hero_id] = min(1, max_count)

    def draw_random_hero(self, cost: int) -> HeroTemplate | None:
        """
        随机抽取指定费用的英雄

        Args:
            cost: 费用 (1-5)

        Returns:
            英雄模板，如果池中已空返回None
        """
        templates = self.config_loader.get_templates_by_cost(cost)
        available = [t for t in templates if self.pool.get(t.hero_id, 0) > 0]

        if not available:
            return None

        template = self.rng.choice(available)
        return self.draw_hero(template.hero_id)

    def get_pool_snapshot(self) -> dict[str, int]:
        """
        获取英雄池快照

        Returns:
            英雄ID到剩余数量的映射
        """
        return dict(self.pool)

    def restore_from_snapshot(self, snapshot: dict[str, int]) -> None:
        """
        从快照恢复英雄池状态

        Args:
            snapshot: 英雄池快照
        """
        self.pool = dict(snapshot)


class ShopManager:
    """
    商店管理器

    管理玩家的商店刷新和购买逻辑。

    Attributes:
        hero_pool: 共享英雄池
        shop: 玩家商店
        player_level: 玩家等级（影响刷新概率）
        rng: 随机数生成器
    """

    def __init__(
        self,
        hero_pool: SharedHeroPool,
        player_level: int = 1,
        seed: int | None = None,
    ) -> None:
        """
        初始化商店管理器

        Args:
            hero_pool: 共享英雄池
            player_level: 玩家等级
            seed: 随机种子
        """
        self.hero_pool = hero_pool
        self.player_level = min(max(player_level, 1), 10)
        self.rng = random.Random(seed)
        self.shop = Shop()

    def set_seed(self, seed: int) -> None:
        """设置随机种子"""
        self.rng.seed(seed)

    def set_player_level(self, level: int) -> None:
        """设置玩家等级"""
        self.player_level = min(max(level, 1), 10)

    def get_refresh_probabilities(self) -> dict[int, float]:
        """
        获取当前等级的刷新概率

        Returns:
            费用到概率的映射
        """
        return REFRESH_PROBABILITY.get(self.player_level, REFRESH_PROBABILITY[1])

    def _select_random_cost(self) -> int:
        """
        根据概率表随机选择英雄费用

        Returns:
            选中的费用 (1-5)
        """
        probabilities = self.get_refresh_probabilities()

        # 使用累积概率选择
        roll = self.rng.random()
        cumulative = 0.0

        for cost in range(MIN_HERO_COST, MAX_HERO_COST + 1):
            prob = probabilities.get(cost, 0.0)
            cumulative += prob
            if roll < cumulative:
                return cost

        # 默认返回1费（防止浮点精度问题）
        return MIN_HERO_COST

    def refresh_shop(self, keep_locked: bool = True) -> Shop:
        """
        刷新商店

        Args:
            keep_locked: 是否保留锁定的槽位

        Returns:
            刷新后的商店
        """
        # 先将非锁定的英雄返还到池中
        for slot in self.shop.slots:
            if not (keep_locked and slot.is_locked):
                if slot.hero_template_id and not slot.is_sold:
                    self.hero_pool.return_hero(slot.hero_template_id)
                slot.hero_template_id = None
                slot.is_sold = False

        # 为每个槽位抽取新英雄
        for slot in self.shop.slots:
            if keep_locked and slot.is_locked:
                continue

            if slot.is_sold:
                continue

            # 根据概率选择费用
            cost = self._select_random_cost()

            # 从池中抽取该费用的随机英雄
            template = self.hero_pool.draw_random_hero(cost)

            if template:
                slot.hero_template_id = template.hero_id
            else:
                # 如果该费用的英雄池已空，尝试抽取其他费用的英雄
                for fallback_cost in range(MIN_HERO_COST, MAX_HERO_COST + 1):
                    if fallback_cost != cost:
                        template = self.hero_pool.draw_random_hero(fallback_cost)
                        if template:
                            slot.hero_template_id = template.hero_id
                            break
                else:
                    slot.hero_template_id = None

        return self.shop

    def full_refresh(self) -> Shop:
        """
        完全刷新商店（不保留任何槽位）

        Returns:
            刷新后的商店
        """
        for slot in self.shop.slots:
            slot.is_locked = False
        return self.refresh_shop(keep_locked=False)

    def buy_hero(self, slot_index: int, cost: int) -> HeroTemplate | None:
        """
        购买商店槽位中的英雄

        Args:
            slot_index: 槽位索引 (0-4)
            cost: 购买费用

        Returns:
            英雄模板，如果购买失败返回None
        """
        slot = self.shop.get_slot(slot_index)
        if slot is None or not slot.is_available():
            return None

        template_id = slot.hero_template_id
        template = self.hero_pool.config_loader.get_template(template_id)

        if template is None:
            return None

        # 标记为已售出
        slot.is_sold = True

        return template

    def lock_slot(self, slot_index: int) -> bool:
        """
        锁定商店槽位

        Args:
            slot_index: 槽位索引

        Returns:
            是否成功
        """
        slot = self.shop.get_slot(slot_index)
        if slot is None:
            return False
        slot.is_locked = True
        return True

    def unlock_slot(self, slot_index: int) -> bool:
        """
        解锁商店槽位

        Args:
            slot_index: 槽位索引

        Returns:
            是否成功
        """
        slot = self.shop.get_slot(slot_index)
        if slot is None:
            return False
        slot.is_locked = False
        return True

    def toggle_slot_lock(self, slot_index: int) -> bool:
        """
        切换槽位锁定状态

        Args:
            slot_index: 槽位索引

        Returns:
            新的锁定状态
        """
        slot = self.shop.get_slot(slot_index)
        if slot is None:
            return False
        slot.is_locked = not slot.is_locked
        return slot.is_locked


class HeroFactory:
    """
    英雄工厂

    创建英雄实例的工厂类。

    Attributes:
        config_loader: 英雄配置加载器
        instance_counter: 实例ID计数器
    """

    def __init__(self, config_loader: HeroConfigLoader) -> None:
        self.config_loader = config_loader
        self._instance_counter = 0

    def _generate_instance_id(self) -> str:
        """生成唯一实例ID"""
        self._instance_counter += 1
        return f"hero_{self._instance_counter}_{create_uuid()[:8]}"

    def create_hero(self, template_id: str, star: int = 1) -> Hero | None:
        """
        创建英雄实例

        Args:
            template_id: 英雄模板ID
            star: 星级 (1-3)

        Returns:
            英雄实例，如果模板不存在返回None
        """
        template = self.config_loader.get_template(template_id)
        if template is None:
            return None

        instance_id = self._generate_instance_id()
        return Hero.create_from_template(template, instance_id, star)

    def create_hero_from_template(
        self,
        template: HeroTemplate,
        star: int = 1,
    ) -> Hero:
        """
        从模板创建英雄实例

        Args:
            template: 英雄模板
            star: 星级

        Returns:
            英雄实例
        """
        instance_id = self._generate_instance_id()
        return Hero.create_from_template(template, instance_id, star)


# ============================================================================
# 示例英雄配置
# ============================================================================

SAMPLE_HEROES_CONFIG: list[dict[str, Any]] = [
    # 1费英雄
    {
        "hero_id": "hero_001",
        "name": "步兵",
        "cost": 1,
        "race": "人族",
        "profession": "战士",
        "base_hp": 600,
        "base_attack": 55,
        "base_defense": 35,
        "attack_speed": 0.7,
        "skill": {
            "name": "盾击",
            "description": "用盾牌重击敌人，造成物理伤害并眩晕",
            "mana_cost": 60,
            "damage": 120,
            "damage_type": "physical",
            "target_type": "single",
        },
    },
    {
        "hero_id": "hero_002",
        "name": "弓箭手",
        "cost": 1,
        "race": "精灵",
        "profession": "射手",
        "base_hp": 450,
        "base_attack": 65,
        "base_defense": 20,
        "attack_speed": 0.8,
        "skill": {
            "name": "穿透射击",
            "description": "射出穿透敌人的箭矢",
            "mana_cost": 50,
            "damage": 100,
            "damage_type": "physical",
            "target_type": "area",
        },
    },
    {
        "hero_id": "hero_003",
        "name": "法师学徒",
        "cost": 1,
        "race": "人族",
        "profession": "法师",
        "base_hp": 400,
        "base_attack": 50,
        "base_defense": 15,
        "attack_speed": 0.6,
        "skill": {
            "name": "火球术",
            "description": "发射一枚火球",
            "mana_cost": 40,
            "damage": 150,
            "damage_type": "magical",
            "target_type": "single",
        },
    },
    # 2费英雄
    {
        "hero_id": "hero_004",
        "name": "骑士",
        "cost": 2,
        "race": "人族",
        "profession": "战士",
        "base_hp": 750,
        "base_attack": 70,
        "base_defense": 45,
        "attack_speed": 0.65,
        "skill": {
            "name": "冲锋",
            "description": "向敌人冲锋",
            "mana_cost": 70,
            "damage": 180,
            "damage_type": "physical",
            "target_type": "single",
        },
    },
    {
        "hero_id": "hero_005",
        "name": "暗影刺客",
        "cost": 2,
        "race": "魔种",
        "profession": "刺客",
        "base_hp": 500,
        "base_attack": 85,
        "base_defense": 25,
        "attack_speed": 0.9,
        "skill": {
            "name": "暗影突袭",
            "description": "瞬移到敌人背后攻击",
            "mana_cost": 60,
            "damage": 200,
            "damage_type": "physical",
            "target_type": "single",
        },
    },
    # 3费英雄
    {
        "hero_id": "hero_006",
        "name": "神圣牧师",
        "cost": 3,
        "race": "神族",
        "profession": "辅助",
        "base_hp": 600,
        "base_attack": 55,
        "base_defense": 30,
        "attack_speed": 0.7,
        "skill": {
            "name": "神圣治愈",
            "description": "治愈友方单位",
            "mana_cost": 80,
            "damage": 0,
            "damage_type": "magical",
            "target_type": "all",
        },
    },
    {
        "hero_id": "hero_007",
        "name": "兽王",
        "cost": 3,
        "race": "兽族",
        "profession": "战士",
        "base_hp": 900,
        "base_attack": 90,
        "base_defense": 50,
        "attack_speed": 0.6,
        "skill": {
            "name": "狂暴",
            "description": "进入狂暴状态",
            "mana_cost": 70,
            "damage": 250,
            "damage_type": "physical",
            "target_type": "area",
        },
    },
    # 4费英雄
    {
        "hero_id": "hero_008",
        "name": "死灵法师",
        "cost": 4,
        "race": "亡灵",
        "profession": "术士",
        "base_hp": 700,
        "base_attack": 80,
        "base_defense": 35,
        "attack_speed": 0.65,
        "skill": {
            "name": "死亡凋零",
            "description": "召唤死亡之力",
            "mana_cost": 90,
            "damage": 400,
            "damage_type": "magical",
            "target_type": "area",
        },
    },
    # 5费英雄
    {
        "hero_id": "hero_009",
        "name": "龙骑士",
        "cost": 5,
        "race": "龙族",
        "profession": "战士",
        "base_hp": 1100,
        "base_attack": 120,
        "base_defense": 60,
        "attack_speed": 0.7,
        "skill": {
            "name": "龙息",
            "description": "喷出龙焰",
            "mana_cost": 100,
            "damage": 600,
            "damage_type": "magical",
            "target_type": "area",
        },
    },
    {
        "hero_id": "hero_010",
        "name": "天神",
        "cost": 5,
        "race": "神族",
        "profession": "法师",
        "base_hp": 800,
        "base_attack": 100,
        "base_defense": 40,
        "attack_speed": 0.6,
        "skill": {
            "name": "天罚",
            "description": "召唤天罚",
            "mana_cost": 120,
            "damage": 800,
            "damage_type": "magical",
            "target_type": "all",
        },
    },
]


def create_default_hero_pool(
    seed: int | None = None,
) -> tuple[HeroConfigLoader, SharedHeroPool, HeroFactory]:
    """
    创建默认的英雄池系统

    Returns:
        (配置加载器, 共享英雄池, 英雄工厂)
    """
    config_loader = HeroConfigLoader()
    config_loader.load_from_dict(SAMPLE_HEROES_CONFIG)

    hero_pool = SharedHeroPool(config_loader, seed=seed)
    factory = HeroFactory(config_loader)

    return config_loader, hero_pool, factory
