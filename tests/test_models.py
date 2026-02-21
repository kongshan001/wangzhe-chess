"""
王者之奕 - 数据模型测试

测试所有核心数据模型的功能：
- Hero 创建和序列化
- Board 操作
- Player 状态管理
- 边界条件测试
"""

import copy
import pytest

from shared.constants import (
    BOARD_HEIGHT,
    BOARD_WIDTH,
    BENCH_SIZE,
    INITIAL_MANA,
    INITIAL_PLAYER_HP,
    MAX_MANA,
)
from shared.models import (
    Board,
    DamageType,
    Hero,
    HeroState,
    HeroTemplate,
    Player,
    PlayerState,
    Position,
    Shop,
    ShopSlot,
    Skill,
    Synergy,
    SynergyLevel,
    SynergyType,
    BattleResult,
    DamageEvent,
    DeathEvent,
    SkillEvent,
)


# ============================================================================
# Skill 测试
# ============================================================================

class TestSkill:
    """技能模型测试"""

    def test_skill_creation(self, sample_skill: Skill):
        """测试技能创建"""
        assert sample_skill.name == "火球术"
        assert sample_skill.description == "发射一枚火球"
        assert sample_skill.mana_cost == 50
        assert sample_skill.damage == 100
        assert sample_skill.damage_type == DamageType.MAGICAL
        assert sample_skill.target_type == "single"

    def test_skill_serialization(self, sample_skill: Skill):
        """测试技能序列化和反序列化"""
        data = sample_skill.to_dict()
        assert data["name"] == "火球术"
        assert data["damage_type"] == "magical"
        
        restored = Skill.from_dict(data)
        assert restored.name == sample_skill.name
        assert restored.mana_cost == sample_skill.mana_cost
        assert restored.damage_type == sample_skill.damage_type

    def test_skill_default_values(self):
        """测试技能默认值"""
        skill = Skill(name="测试技能")
        assert skill.mana_cost == 50
        assert skill.damage == 0
        assert skill.damage_type == DamageType.MAGICAL
        assert skill.target_type == "single"

    def test_skill_all_damage_types(self):
        """测试所有伤害类型"""
        for damage_type in DamageType:
            skill = Skill(
                name=f"技能_{damage_type.value}",
                damage_type=damage_type,
            )
            assert skill.damage_type == damage_type
            
            # 测试序列化
            data = skill.to_dict()
            restored = Skill.from_dict(data)
            assert restored.damage_type == damage_type

    def test_skill_all_target_types(self):
        """测试所有目标类型"""
        target_types = ["single", "area", "all", "self"]
        for target_type in target_types:
            skill = Skill(
                name=f"技能_{target_type}",
                target_type=target_type,
            )
            assert skill.target_type == target_type


# ============================================================================
# HeroTemplate 测试
# ============================================================================

class TestHeroTemplate:
    """英雄模板测试"""

    def test_template_creation(self, sample_hero_template: HeroTemplate):
        """测试英雄模板创建"""
        assert sample_hero_template.hero_id == "test_hero_001"
        assert sample_hero_template.name == "测试英雄"
        assert sample_hero_template.cost == 1
        assert sample_hero_template.race == "人族"
        assert sample_hero_template.profession == "战士"
        assert sample_hero_template.base_hp == 500
        assert sample_hero_template.base_attack == 50
        assert sample_hero_template.base_defense == 30
        assert sample_hero_template.attack_speed == 0.7

    def test_template_serialization(self, sample_hero_template: HeroTemplate):
        """测试英雄模板序列化"""
        data = sample_hero_template.to_dict()
        assert data["hero_id"] == "test_hero_001"
        assert data["skill"]["name"] == "火球术"
        
        restored = HeroTemplate.from_dict(data)
        assert restored.hero_id == sample_hero_template.hero_id
        assert restored.skill.name == sample_hero_template.skill.name

    def test_template_without_skill(self):
        """测试没有技能的英雄模板"""
        template = HeroTemplate(
            hero_id="no_skill_hero",
            name="无技能英雄",
            cost=1,
            race="人族",
            profession="战士",
            base_hp=500,
            base_attack=50,
            base_defense=30,
            attack_speed=0.7,
        )
        assert template.skill is None
        
        # 测试序列化
        data = template.to_dict()
        assert data["skill"] is None
        
        restored = HeroTemplate.from_dict(data)
        assert restored.skill is None

    def test_template_different_costs(self, sample_hero_templates: list[HeroTemplate]):
        """测试不同费用的英雄模板"""
        costs = [1, 2, 3, 4, 5]
        for template, expected_cost in zip(sample_hero_templates, costs):
            assert template.cost == expected_cost


# ============================================================================
# Hero 测试
# ============================================================================

class TestHero:
    """英雄实例测试"""

    def test_hero_creation(self, sample_hero: Hero):
        """测试英雄创建"""
        assert sample_hero.instance_id == "test_instance_001"
        assert sample_hero.template_id == "test_hero_001"
        assert sample_hero.star == 1
        assert sample_hero.hp == sample_hero.max_hp
        assert sample_hero.mana == INITIAL_MANA

    def test_hero_from_template(self, sample_hero_template: HeroTemplate):
        """测试从模板创建英雄"""
        hero = Hero.create_from_template(
            sample_hero_template,
            instance_id="new_hero",
            star=1,
        )
        assert hero.template_id == sample_hero_template.hero_id
        assert hero.name == sample_hero_template.name
        assert hero.max_hp == sample_hero_template.base_hp
        assert hero.attack == sample_hero_template.base_attack

    def test_hero_star_multiplier(self, sample_hero_template: HeroTemplate):
        """测试英雄星级加成"""
        # 1星
        hero_1 = Hero.create_from_template(sample_hero_template, "h1", star=1)
        
        # 2星 (1.8倍属性)
        hero_2 = Hero.create_from_template(sample_hero_template, "h2", star=2)
        assert hero_2.max_hp == int(hero_1.max_hp / 1.0 * 1.8)
        assert hero_2.attack == int(hero_1.attack / 1.0 * 1.8)
        
        # 3星 (3.24倍属性)
        hero_3 = Hero.create_from_template(sample_hero_template, "h3", star=3)
        assert hero_3.max_hp == int(hero_1.max_hp / 1.0 * 3.24)

    def test_hero_is_alive(self, sample_hero: Hero):
        """测试英雄存活状态"""
        assert sample_hero.is_alive() is True
        
        sample_hero.hp = 0
        assert sample_hero.is_alive() is False
        
        sample_hero.hp = -10
        assert sample_hero.is_alive() is False

    def test_hero_is_on_board(self, sample_hero: Hero):
        """测试英雄是否在棋盘上"""
        assert sample_hero.is_on_board() is False
        
        sample_hero.position = Position(x=0, y=0)
        assert sample_hero.is_on_board() is True

    def test_hero_take_damage_physical(self, sample_hero: Hero):
        """测试英雄受到物理伤害"""
        initial_hp = sample_hero.hp
        damage = 100
        
        actual_damage = sample_hero.take_damage(damage, DamageType.PHYSICAL)
        
        # 物理伤害受防御减免
        # 实际伤害 = 伤害 * 100 / (100 + 防御)
        expected_damage = int(100 * 100 / (100 + sample_hero.defense))
        assert actual_damage == expected_damage
        assert sample_hero.hp == initial_hp - actual_damage

    def test_hero_take_damage_magical(self, sample_hero: Hero):
        """测试英雄受到魔法伤害"""
        initial_hp = sample_hero.hp
        damage = 100
        
        actual_damage = sample_hero.take_damage(damage, DamageType.MAGICAL)
        
        # 魔法伤害也受防御减免（简化模型）
        expected_damage = int(100 * 100 / (100 + sample_hero.defense))
        assert actual_damage == expected_damage

    def test_hero_take_damage_true(self, sample_hero: Hero):
        """测试英雄受到真实伤害"""
        initial_hp = sample_hero.hp
        damage = 100
        
        actual_damage = sample_hero.take_damage(damage, DamageType.TRUE)
        
        # 真实伤害无视防御
        assert actual_damage == 100
        assert sample_hero.hp == initial_hp - 100

    def test_hero_take_damage_to_death(self, sample_hero: Hero):
        """测试英雄受到致命伤害"""
        huge_damage = 10000
        sample_hero.take_damage(huge_damage, DamageType.TRUE)
        
        assert sample_hero.hp == 0
        assert sample_hero.state == HeroState.DEAD
        assert not sample_hero.is_alive()

    def test_hero_heal(self, sample_hero: Hero):
        """测试英雄治疗"""
        sample_hero.hp = 100
        initial_hp = sample_hero.hp
        
        heal_amount = sample_hero.heal(200)
        
        expected_hp = min(sample_hero.max_hp, initial_hp + 200)
        assert sample_hero.hp == expected_hp

    def test_hero_heal_over_max(self, sample_hero: Hero):
        """测试英雄治疗不超过最大生命值"""
        sample_hero.hp = 400
        heal_amount = sample_hero.heal(1000)
        
        assert sample_hero.hp == sample_hero.max_hp
        assert heal_amount == sample_hero.max_hp - 400

    def test_hero_mana_operations(self, sample_hero: Hero):
        """测试英雄蓝量操作"""
        # 初始蓝量
        assert sample_hero.mana == INITIAL_MANA
        
        # 获得蓝量
        gained = sample_hero.gain_mana(30)
        assert gained == 30
        assert sample_hero.mana == INITIAL_MANA + 30
        
        # 蓝量上限
        gained = sample_hero.gain_mana(200)
        assert sample_hero.mana == MAX_MANA
        assert gained == MAX_MANA - (INITIAL_MANA + 30)

    def test_hero_can_cast_skill(self, sample_hero: Hero):
        """测试英雄是否可以释放技能"""
        # 蓝量不足
        assert sample_hero.can_cast_skill() is False
        
        # 获得足够蓝量
        sample_hero.gain_mana(sample_hero.skill.mana_cost)
        assert sample_hero.can_cast_skill() is True
        
        # 死亡后不能释放
        sample_hero.hp = 0
        sample_hero.state = HeroState.DEAD
        assert sample_hero.can_cast_skill() is False

    def test_hero_use_skill(self, sample_hero: Hero):
        """测试英雄使用技能"""
        sample_hero.gain_mana(sample_hero.skill.mana_cost)
        mana_before = sample_hero.mana
        
        result = sample_hero.use_skill()
        
        assert result is True
        assert sample_hero.mana == mana_before - sample_hero.skill.mana_cost

    def test_hero_use_skill_insufficient_mana(self, sample_hero: Hero):
        """测试蓝量不足时使用技能"""
        result = sample_hero.use_skill()
        assert result is False

    def test_hero_serialization(self, sample_hero: Hero):
        """测试英雄序列化"""
        data = sample_hero.to_dict()
        
        assert data["instance_id"] == sample_hero.instance_id
        assert data["template_id"] == sample_hero.template_id
        assert data["state"] == "idle"
        
        restored = Hero.from_dict(data)
        assert restored.instance_id == sample_hero.instance_id
        assert restored.hp == sample_hero.hp
        assert restored.mana == sample_hero.mana

    def test_hero_serialization_with_position(self, sample_hero: Hero):
        """测试带位置的英雄序列化"""
        sample_hero.position = Position(x=3, y=4)
        data = sample_hero.to_dict()
        
        assert data["position"]["x"] == 3
        assert data["position"]["y"] == 4
        
        restored = Hero.from_dict(data)
        assert restored.position.x == 3
        assert restored.position.y == 4


# ============================================================================
# Position 测试
# ============================================================================

class TestPosition:
    """位置测试"""

    def test_position_creation(self):
        """测试位置创建"""
        pos = Position(x=3, y=5)
        assert pos.x == 3
        assert pos.y == 5

    def test_position_invalid(self):
        """测试无效位置"""
        with pytest.raises(ValueError):
            Position(x=-1, y=0)
        
        with pytest.raises(ValueError):
            Position(x=BOARD_WIDTH, y=0)
        
        with pytest.raises(ValueError):
            Position(x=0, y=-1)
        
        with pytest.raises(ValueError):
            Position(x=0, y=BOARD_HEIGHT)

    def test_position_boundary(self):
        """测试边界位置"""
        # 最小边界
        pos_min = Position(x=0, y=0)
        assert pos_min.x == 0
        assert pos_min.y == 0
        
        # 最大边界
        pos_max = Position(x=BOARD_WIDTH - 1, y=BOARD_HEIGHT - 1)
        assert pos_max.x == BOARD_WIDTH - 1
        assert pos_max.y == BOARD_HEIGHT - 1

    def test_position_distance(self):
        """测试位置距离计算"""
        pos1 = Position(x=0, y=0)
        pos2 = Position(x=3, y=4)
        
        # 曼哈顿距离
        assert pos1.distance_to(pos2) == 7
        assert pos2.distance_to(pos1) == 7
        
        # 欧几里得距离
        euclidean = pos1.euclidean_distance(pos2)
        assert 4.9 < euclidean < 5.1  # sqrt(3^2 + 4^2) = 5

    def test_position_to_tuple(self):
        """测试位置转元组"""
        pos = Position(x=3, y=5)
        assert pos.to_tuple() == (3, 5)

    def test_position_serialization(self):
        """测试位置序列化"""
        pos = Position(x=3, y=5)
        data = pos.to_dict()
        
        assert data["x"] == 3
        assert data["y"] == 5
        
        restored = Position.from_dict(data)
        assert restored.x == pos.x
        assert restored.y == pos.y


# ============================================================================
# Board 测试
# ============================================================================

class TestBoard:
    """棋盘测试"""

    def test_board_creation(self, empty_board: Board):
        """测试棋盘创建"""
        assert empty_board.owner_id == "test_player"
        assert len(empty_board.grid) == BOARD_HEIGHT
        assert len(empty_board.grid[0]) == BOARD_WIDTH
        assert empty_board.get_hero_count() == 0

    def test_board_place_hero(self, empty_board: Board, sample_hero: Hero):
        """测试放置英雄"""
        pos = Position(x=2, y=3)
        result = empty_board.place_hero(sample_hero, pos)
        
        assert result is True
        assert empty_board.get_hero_count() == 1
        assert sample_hero.position == pos
        
        # 验证可以通过位置获取英雄
        hero_at_pos = empty_board.get_hero_at(pos)
        assert hero_at_pos is not None
        assert hero_at_pos.instance_id == sample_hero.instance_id

    def test_board_place_hero_occupied(self, empty_board: Board, sample_hero: Hero, sample_heroes: list[Hero]):
        """测试在已有英雄的位置放置英雄"""
        pos = Position(x=2, y=3)
        empty_board.place_hero(sample_hero, pos)
        
        # 尝试在同一位置放置另一个英雄
        another_hero = sample_heroes[1] if len(sample_heroes) > 1 else sample_heroes[0]
        result = empty_board.place_hero(another_hero, pos)
        
        assert result is False

    def test_board_remove_hero(self, empty_board: Board, sample_hero: Hero):
        """测试移除英雄"""
        pos = Position(x=2, y=3)
        empty_board.place_hero(sample_hero, pos)
        
        removed = empty_board.remove_hero(sample_hero.instance_id)
        
        assert removed is not None
        assert removed.instance_id == sample_hero.instance_id
        assert empty_board.get_hero_count() == 0
        assert sample_hero.position is None

    def test_board_remove_nonexistent_hero(self, empty_board: Board):
        """测试移除不存在的英雄"""
        removed = empty_board.remove_hero("nonexistent_id")
        assert removed is None

    def test_board_get_hero_at_empty(self, empty_board: Board):
        """测试获取空位置的英雄"""
        pos = Position(x=0, y=0)
        hero = empty_board.get_hero_at(pos)
        assert hero is None

    def test_board_get_all_heroes(self, sample_board: Board):
        """测试获取所有英雄"""
        heroes = sample_board.get_all_heroes(alive_only=False)
        assert len(heroes) == 5

    def test_board_get_alive_heroes(self, sample_board: Board):
        """测试获取存活英雄"""
        # 杀死一个英雄
        first_hero = sample_board.get_all_heroes(alive_only=False)[0]
        first_hero.hp = 0
        
        alive_heroes = sample_board.get_all_heroes(alive_only=True)
        assert len(alive_heroes) == 4

    def test_board_find_nearest_enemy(self, sample_board: Board):
        """测试寻找最近敌人"""
        # 创建敌方棋盘
        enemy_board = Board.create_empty("enemy")
        
        # 在敌方棋盘放置英雄
        enemy_hero = Hero(
            instance_id="enemy_001",
            template_id="enemy_template",
            name="敌人",
            cost=1,
            star=1,
            race="魔种",
            profession="刺客",
            max_hp=400,
            hp=400,
            attack=60,
            defense=20,
            attack_speed=0.8,
            position=Position(x=7, y=7),
        )
        enemy_board.place_hero(enemy_hero, Position(x=7, y=7))
        
        # 从我方棋盘位置寻找最近敌人
        from_pos = Position(x=0, y=0)
        nearest = sample_board.find_nearest_enemy(from_pos, enemy_board)
        
        assert nearest is not None
        assert nearest.instance_id == "enemy_001"

    def test_board_serialization(self, sample_board: Board):
        """测试棋盘序列化"""
        data = sample_board.to_dict()
        
        assert data["owner_id"] == "test_player"
        assert len(data["heroes"]) == 5
        
        restored = Board.from_dict(data)
        assert restored.owner_id == sample_board.owner_id
        assert restored.get_hero_count() == sample_board.get_hero_count()

    def test_board_place_hero_move(self, empty_board: Board, sample_hero: Hero):
        """测试移动英雄（先在一个位置放置，再移到另一个位置）"""
        pos1 = Position(x=0, y=0)
        pos2 = Position(x=5, y=5)
        
        # 放置英雄
        empty_board.place_hero(sample_hero, pos1)
        assert sample_hero.position == pos1
        assert empty_board.grid[pos1.y][pos1.x] == sample_hero.instance_id
        
        # 移动到新位置
        empty_board.place_hero(sample_hero, pos2)
        assert sample_hero.position == pos2
        assert empty_board.grid[pos1.y][pos1.x] is None  # 原位置为空
        assert empty_board.grid[pos2.y][pos2.x] == sample_hero.instance_id


# ============================================================================
# Shop 测试
# ============================================================================

class TestShop:
    """商店测试"""

    def test_shop_creation(self):
        """测试商店创建"""
        shop = Shop()
        assert len(shop.slots) == 5  # 默认5个槽位
        assert shop.refresh_cost == 2

    def test_shop_slot_creation(self):
        """测试商店槽位创建"""
        slot = ShopSlot(slot_index=0)
        assert slot.slot_index == 0
        assert slot.hero_template_id is None
        assert not slot.is_locked
        assert not slot.is_sold

    def test_shop_slot_is_available(self):
        """测试槽位可用性"""
        slot = ShopSlot(slot_index=0)
        assert not slot.is_available()
        
        slot.hero_template_id = "hero_001"
        assert slot.is_available()
        
        slot.is_sold = True
        assert not slot.is_available()

    def test_shop_slot_serialization(self):
        """测试槽位序列化"""
        slot = ShopSlot(
            slot_index=0,
            hero_template_id="hero_001",
            is_locked=True,
        )
        data = slot.to_dict()
        
        assert data["slot_index"] == 0
        assert data["hero_template_id"] == "hero_001"
        assert data["is_locked"] is True
        
        restored = ShopSlot.from_dict(data)
        assert restored.slot_index == slot.slot_index
        assert restored.hero_template_id == slot.hero_template_id

    def test_shop_get_available_slots(self):
        """测试获取可用槽位"""
        shop = Shop()
        shop.slots[0].hero_template_id = "hero_001"
        shop.slots[1].hero_template_id = "hero_002"
        shop.slots[1].is_sold = True
        shop.slots[2].hero_template_id = None  # 空槽位
        
        available = shop.get_available_slots()
        assert len(available) == 1
        assert available[0].slot_index == 0

    def test_shop_serialization(self):
        """测试商店序列化"""
        shop = Shop()
        shop.slots[0].hero_template_id = "hero_001"
        
        data = shop.to_dict()
        assert len(data["slots"]) == 5
        
        restored = Shop.from_dict(data)
        assert len(restored.slots) == 5


# ============================================================================
# Player 测试
# ============================================================================

class TestPlayer:
    """玩家测试"""

    def test_player_creation(self, sample_player: Player):
        """测试玩家创建"""
        assert sample_player.player_id == "test_player_001"
        assert sample_player.hp == INITIAL_PLAYER_HP
        assert sample_player.gold == 10
        assert sample_player.level == 1
        assert sample_player.state == PlayerState.WAITING

    def test_player_is_alive(self, sample_player: Player):
        """测试玩家存活状态"""
        assert sample_player.is_alive() is True
        
        sample_player.hp = 0
        assert sample_player.is_alive() is False

    def test_player_can_afford(self, sample_player: Player):
        """测试玩家金币是否足够"""
        assert sample_player.can_afford(5) is True
        assert sample_player.can_afford(10) is True
        assert sample_player.can_afford(15) is False

    def test_player_spend_gold(self, sample_player: Player):
        """测试玩家花费金币"""
        initial_gold = sample_player.gold
        
        result = sample_player.spend_gold(5)
        assert result is True
        assert sample_player.gold == initial_gold - 5
        
        # 金币不足
        result = sample_player.spend_gold(100)
        assert result is False
        assert sample_player.gold == initial_gold - 5

    def test_player_earn_gold(self, sample_player: Player):
        """测试玩家获得金币"""
        initial_gold = sample_player.gold
        sample_player.earn_gold(5)
        
        assert sample_player.gold == initial_gold + 5

    def test_player_bench_operations(self, sample_player: Player, sample_heroes: list[Hero]):
        """测试玩家备战席操作"""
        # 添加英雄
        result = sample_player.add_to_bench(sample_heroes[0])
        assert result is True
        assert sample_player.get_bench_hero_count() == 1
        
        result = sample_player.add_to_bench(sample_heroes[1])
        assert result is True
        assert sample_player.get_bench_hero_count() == 2
        
        # 移除英雄
        removed = sample_player.remove_from_bench(sample_heroes[0].instance_id)
        assert removed is not None
        assert sample_player.get_bench_hero_count() == 1
        
        # 移除不存在的英雄
        removed = sample_player.remove_from_bench("nonexistent")
        assert removed is None

    def test_player_bench_full(self, sample_player: Player, sample_heroes: list[Hero]):
        """测试备战席已满"""
        # 填满备战席
        for i in range(BENCH_SIZE):
            hero = copy.deepcopy(sample_heroes[0])
            hero.instance_id = f"hero_{i}"
            result = sample_player.add_to_bench(hero)
            assert result is True
        
        assert sample_player.can_add_to_bench() is False
        
        # 尝试再添加
        another_hero = copy.deepcopy(sample_heroes[0])
        another_hero.instance_id = "hero_extra"
        result = sample_player.add_to_bench(another_hero)
        assert result is False

    def test_player_take_damage(self, sample_player: Player):
        """测试玩家受到伤害"""
        initial_hp = sample_player.hp
        damage = 20
        
        actual_damage = sample_player.take_damage(damage)
        assert actual_damage == damage
        assert sample_player.hp == initial_hp - damage

    def test_player_take_fatal_damage(self, sample_player: Player):
        """测试玩家受到致命伤害"""
        sample_player.take_damage(INITIAL_PLAYER_HP + 100)
        
        assert sample_player.hp == 0
        assert sample_player.state == PlayerState.ELIMINATED
        assert not sample_player.is_alive()

    def test_player_serialization(self, sample_player: Player):
        """测试玩家序列化"""
        sample_player.gold = 50
        sample_player.level = 5
        sample_player.win_streak = 3
        
        data = sample_player.to_dict()
        
        assert data["player_id"] == sample_player.player_id
        assert data["gold"] == 50
        assert data["level"] == 5
        assert data["win_streak"] == 3
        
        restored = Player.from_dict(data)
        assert restored.player_id == sample_player.player_id
        assert restored.gold == sample_player.gold
        assert restored.level == sample_player.level

    def test_player_get_all_heroes(self, player_with_heroes: Player):
        """测试获取玩家所有英雄"""
        all_heroes = player_with_heroes.get_all_heroes()
        
        # 备战席3个 + 场上2个 = 5个
        assert len(all_heroes) == 5


# ============================================================================
# Synergy 测试
# ============================================================================

class TestSynergyModels:
    """羁绊模型测试"""

    def test_synergy_level_creation(self):
        """测试羁绊等级创建"""
        level = SynergyLevel(
            required_count=2,
            effect_description="2人族效果",
            stat_bonuses={"attack": 10},
        )
        assert level.required_count == 2
        assert level.stat_bonuses == {"attack": 10}

    def test_synergy_creation(self, sample_synergies: list[Synergy]):
        """测试羁绊创建"""
        human_synergy = sample_synergies[0]
        assert human_synergy.name == "人族"
        assert human_synergy.synergy_type == SynergyType.RACE
        assert len(human_synergy.levels) == 2

    def test_synergy_get_active_level(self, sample_synergies: list[Synergy]):
        """测试获取激活的羁绊等级"""
        human_synergy = sample_synergies[0]
        
        # 1个英雄，未激活
        level = human_synergy.get_active_level(1)
        assert level is None
        
        # 2个英雄，激活第一级
        level = human_synergy.get_active_level(2)
        assert level is not None
        assert level.required_count == 2
        
        # 4个英雄，激活第二级
        level = human_synergy.get_active_level(4)
        assert level is not None
        assert level.required_count == 4
        
        # 5个英雄，仍然是第二级
        level = human_synergy.get_active_level(5)
        assert level.required_count == 4

    def test_synergy_get_next_level_requirement(self, sample_synergies: list[Synergy]):
        """测试获取下一级所需数量"""
        human_synergy = sample_synergies[0]
        
        assert human_synergy.get_next_level_requirement(1) == 2
        assert human_synergy.get_next_level_requirement(2) == 4
        assert human_synergy.get_next_level_requirement(4) is None  # 已满级
        assert human_synergy.get_next_level_requirement(10) is None

    def test_synergy_serialization(self, sample_synergies: list[Synergy]):
        """测试羁绊序列化"""
        synergy = sample_synergies[0]
        data = synergy.to_dict()
        
        assert data["name"] == "人族"
        assert data["synergy_type"] == "race"
        assert len(data["levels"]) == 2
        
        restored = Synergy.from_dict(data)
        assert restored.name == synergy.name
        assert restored.synergy_type == synergy.synergy_type


# ============================================================================
# BattleResult 测试
# ============================================================================

class TestBattleResult:
    """战斗结果测试"""

    def test_battle_result_creation(self):
        """测试战斗结果创建"""
        result = BattleResult(
            winner="player_a",
            loser="player_b",
            player_a_damage=0,
            player_b_damage=10,
        )
        assert result.winner == "player_a"
        assert result.loser == "player_b"
        assert not result.is_draw()

    def test_battle_result_draw(self):
        """测试平局结果"""
        result = BattleResult(winner="draw", loser="draw")
        assert result.is_draw()

    def test_battle_result_serialization(self):
        """测试战斗结果序列化"""
        result = BattleResult(
            winner="player_a",
            loser="player_b",
            player_a_damage=0,
            player_b_damage=15,
            survivors_a=["hero_001"],
            survivors_b=[],
            battle_duration_ms=30000,
            random_seed=42,
        )
        
        data = result.to_dict()
        
        assert data["winner"] == "player_a"
        assert data["battle_duration_ms"] == 30000
        
        restored = BattleResult.from_dict(data)
        assert restored.winner == result.winner
        assert restored.battle_duration_ms == result.battle_duration_ms


# ============================================================================
# 边界条件测试
# ============================================================================

class TestBoundaryConditions:
    """边界条件测试"""

    def test_hero_zero_hp(self, sample_hero: Hero):
        """测试英雄零生命值"""
        sample_hero.hp = 0
        assert not sample_hero.is_alive()
        assert sample_hero.take_damage(100) == 0  # 已死亡不再受伤

    def test_hero_negative_hp(self, sample_hero_template: HeroTemplate):
        """测试英雄负生命值（不应该发生）"""
        hero = Hero.create_from_template(sample_hero_template, "test", star=1)
        # 尝试设置负生命值
        hero.hp = -100
        assert hero.hp == -100  # 数据类不会阻止这个
        assert not hero.is_alive()

    def test_hero_max_hp_constraint(self, sample_hero_template: HeroTemplate):
        """测试英雄生命值不超过最大值"""
        hero = Hero(
            instance_id="test",
            template_id="test",
            name="test",
            cost=1,
            star=1,
            race="人族",
            profession="战士",
            max_hp=500,
            hp=1000,  # 尝试设置超过最大值
            attack=50,
            defense=30,
            attack_speed=1.0,
        )
        # __post_init__ 会限制 hp 不超过 max_hp
        assert hero.hp == 500

    def test_hero_mana_constraint(self, sample_hero: Hero):
        """测试英雄蓝量不超过上限"""
        sample_hero.gain_mana(1000)
        assert sample_hero.mana == MAX_MANA

    def test_board_all_positions(self):
        """测试棋盘所有位置"""
        board = Board.create_empty("test")
        
        for y in range(BOARD_HEIGHT):
            for x in range(BOARD_WIDTH):
                pos = Position(x=x, y=y)
                assert board.grid[y][x] is None

    def test_position_all_corners(self):
        """测试位置所有角落"""
        corners = [
            (0, 0),
            (0, BOARD_HEIGHT - 1),
            (BOARD_WIDTH - 1, 0),
            (BOARD_WIDTH - 1, BOARD_HEIGHT - 1),
        ]
        
        for x, y in corners:
            pos = Position(x=x, y=y)
            assert pos.x == x
            assert pos.y == y

    def test_damage_zero(self, sample_hero: Hero):
        """测试零伤害"""
        initial_hp = sample_hero.hp
        actual_damage = sample_hero.take_damage(0, DamageType.TRUE)
        
        assert actual_damage == 0
        assert sample_hero.hp == initial_hp

    def test_damage_negative(self, sample_hero: Hero):
        """测试负伤害（治疗效果）"""
        sample_hero.hp = 100
        initial_hp = sample_hero.hp
        
        # 负伤害不会治疗
        sample_hero.take_damage(-50, DamageType.TRUE)
        
        # 行为取决于实现，这里检查不会崩溃
        assert sample_hero.hp >= 0
