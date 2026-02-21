"""
王者之奕 - 羁绊系统测试

测试羁绊系统的核心功能：
- 羁绊计数
- 激活羁绊计算
- 羁绊加成获取
- 加成应用
- 羁绊等级递进
"""

import pytest
from typing import Any

from shared.constants import RACES, PROFESSIONS
from shared.models import (
    ActiveSynergy,
    Hero,
    HeroTemplate,
    Position,
    Skill,
    Synergy,
    SynergyLevel,
    SynergyType,
    DamageType,
)
from server.game.synergy import (
    SynergyManager,
    RACE_SYNERGIES,
    PROFESSION_SYNERGIES,
    create_synergy_manager,
    get_all_synergy_names,
)


# ============================================================================
# 测试 Fixtures
# ============================================================================

@pytest.fixture
def synergy_manager() -> SynergyManager:
    """创建羁绊管理器"""
    return SynergyManager()


@pytest.fixture
def create_hero():
    """创建测试英雄的工厂函数"""
    counter = 0
    
    def _create(
        name: str,
        race: str = "人族",
        profession: str = "战士",
        hp: int = 500,
        attack: int = 50,
        defense: int = 30,
    ) -> Hero:
        nonlocal counter
        counter += 1
        
        skill = Skill(
            name=f"{name}技能",
            mana_cost=50,
            damage=100,
            damage_type=DamageType.MAGICAL,
        )
        template = HeroTemplate(
            hero_id=f"hero_{counter}",
            name=name,
            cost=1,
            race=race,
            profession=profession,
            base_hp=hp,
            base_attack=attack,
            base_defense=defense,
            attack_speed=1.0,
            skill=skill,
        )
        return Hero.create_from_template(template, f"instance_{counter}", star=1)
    
    return _create


@pytest.fixture
def create_heroes_with_synergy(create_hero):
    """创建具有特定羁绊的英雄组"""
    def _create(race: str, profession: str, count: int) -> list[Hero]:
        heroes = []
        for i in range(count):
            hero = create_hero(
                name=f"{race}_{profession}_{i}",
                race=race,
                profession=profession,
            )
            heroes.append(hero)
        return heroes
    
    return _create


# ============================================================================
# test_count_heroes_by_synergy - 测试羁绊计数
# ============================================================================

class TestCountHeroesBySynergy:
    """羁绊计数测试"""

    def test_count_empty_list(self, synergy_manager: SynergyManager):
        """测试空英雄列表的羁绊计数"""
        counts = synergy_manager.count_heroes_by_synergy([])
        assert counts == {}

    def test_count_single_hero(self, synergy_manager: SynergyManager, create_hero):
        """测试单个英雄的羁绊计数"""
        hero = create_hero(name="单英雄", race="人族", profession="战士")
        counts = synergy_manager.count_heroes_by_synergy([hero])
        
        assert counts.get("人族") == 1
        assert counts.get("战士") == 1

    def test_count_multiple_heroes_same_synergy(
        self, synergy_manager: SynergyManager, create_heroes_with_synergy
    ):
        """测试多个相同羁绊英雄的计数"""
        heroes = create_heroes_with_synergy("人族", "战士", 5)
        counts = synergy_manager.count_heroes_by_synergy(heroes)
        
        assert counts.get("人族") == 5
        assert counts.get("战士") == 5

    def test_count_mixed_races(self, synergy_manager: SynergyManager, create_hero):
        """测试混合种族的羁绊计数"""
        heroes = [
            create_hero(name="人族1", race="人族", profession="战士"),
            create_hero(name="人族2", race="人族", profession="法师"),
            create_hero(name="神族1", race="神族", profession="战士"),
            create_hero(name="魔种1", race="魔种", profession="刺客"),
        ]
        counts = synergy_manager.count_heroes_by_synergy(heroes)
        
        assert counts.get("人族") == 2
        assert counts.get("神族") == 1
        assert counts.get("魔种") == 1
        assert counts.get("战士") == 2
        assert counts.get("法师") == 1
        assert counts.get("刺客") == 1

    def test_count_all_races(self, synergy_manager: SynergyManager, create_hero):
        """测试所有种族的计数"""
        heroes = []
        for race in RACES[:5]:  # 测试前5个种族
            heroes.append(create_hero(name=f"{race}英雄", race=race, profession="战士"))
        
        counts = synergy_manager.count_heroes_by_synergy(heroes)
        
        for race in RACES[:5]:
            assert counts.get(race) == 1

    def test_count_all_professions(self, synergy_manager: SynergyManager, create_hero):
        """测试所有职业的计数"""
        heroes = []
        for profession in PROFESSIONS[:5]:  # 测试前5个职业
            heroes.append(create_hero(name=f"{profession}英雄", race="人族", profession=profession))
        
        counts = synergy_manager.count_heroes_by_synergy(heroes)
        
        for profession in PROFESSIONS[:5]:
            assert counts.get(profession) == 1

    def test_count_with_dead_heroes(self, synergy_manager: SynergyManager, create_hero):
        """测试包含死亡英雄的计数"""
        heroes = [
            create_hero(name="存活1", race="人族", profession="战士"),
            create_hero(name="存活2", race="人族", profession="战士"),
        ]
        # 死亡英雄
        dead_hero = create_hero(name="死亡", race="人族", profession="战士")
        dead_hero.hp = 0
        heroes.append(dead_hero)
        
        # count_heroes_by_synergy 默认不过滤死亡
        counts = synergy_manager.count_heroes_by_synergy(heroes)
        assert counts.get("人族") == 3


# ============================================================================
# test_calculate_active_synergies - 测试激活羁绊计算
# ============================================================================

class TestCalculateActiveSynergies:
    """激活羁绊计算测试"""

    def test_no_active_synergies(self, synergy_manager: SynergyManager, create_hero):
        """测试无激活羁绊（数量不足）"""
        hero = create_hero(name="单人", race="人族", profession="战士")
        active = synergy_manager.calculate_active_synergies([hero])
        
        # 人族需要2个才激活
        # 战士需要2个才激活
        # 单个英雄不会激活任何羁绊
        assert all(not s.is_active() for s in active)

    def test_single_synergy_activation(
        self, synergy_manager: SynergyManager, create_heroes_with_synergy
    ):
        """测试单个羁绊激活"""
        heroes = create_heroes_with_synergy("人族", "战士", 2)
        active = synergy_manager.calculate_active_synergies(heroes)
        
        # 找到人族羁绊
        human_synergy = next((s for s in active if s.synergy_name == "人族"), None)
        assert human_synergy is not None
        assert human_synergy.is_active()
        assert human_synergy.count == 2

    def test_multiple_synergy_levels(
        self, synergy_manager: SynergyManager, create_heroes_with_synergy
    ):
        """测试羁绊多个等级"""
        # 测试人族羁绊：2/4/6个等级
        heroes_2 = create_heroes_with_synergy("人族", "战士", 2)
        active_2 = synergy_manager.calculate_active_synergies(heroes_2)
        human_2 = next((s for s in active_2 if s.synergy_name == "人族"), None)
        assert human_2.is_active()
        assert "10%" in human_2.active_level.effect_description  # 第一级效果
        
        heroes_4 = create_heroes_with_synergy("人族", "战士", 4)
        active_4 = synergy_manager.calculate_active_synergies(heroes_4)
        human_4 = next((s for s in active_4 if s.synergy_name == "人族"), None)
        assert human_4.is_active()
        assert "25%" in human_4.active_level.effect_description  # 第二级效果
        
        heroes_6 = create_heroes_with_synergy("人族", "战士", 6)
        active_6 = synergy_manager.calculate_active_synergies(heroes_6)
        human_6 = next((s for s in active_6 if s.synergy_name == "人族"), None)
        assert human_6.is_active()
        assert "45%" in human_6.active_level.effect_description  # 第三级效果

    def test_race_and_profession_together(
        self, synergy_manager: SynergyManager, create_hero
    ):
        """测试种族和职业同时激活"""
        heroes = [
            create_hero(name="人族战士1", race="人族", profession="战士"),
            create_hero(name="人族战士2", race="人族", profession="战士"),
        ]
        active = synergy_manager.calculate_active_synergies(heroes)
        
        # 两个羁绊都应该激活
        active_names = {s.synergy_name for s in active if s.is_active()}
        assert "人族" in active_names
        assert "战士" in active_names

    def test_alive_only_filter(self, synergy_manager: SynergyManager, create_hero):
        """测试只计算存活英雄"""
        heroes = [
            create_hero(name="存活1", race="人族", profession="战士"),
            create_hero(name="存活2", race="人族", profession="战士"),
        ]
        dead_hero = create_hero(name="死亡", race="神族", profession="法师")
        dead_hero.hp = 0
        heroes.append(dead_hero)
        
        # alive_only=True
        active = synergy_manager.calculate_active_synergies(heroes, alive_only=True)
        active_names = {s.synergy_name for s in active}
        assert "神族" not in active_names  # 死亡英雄不计入
        
        # alive_only=False
        active_all = synergy_manager.calculate_active_synergies(heroes, alive_only=False)
        active_all_names = {s.synergy_name for s in active_all}
        assert "神族" in active_all_names  # 死亡英雄也计入

    def test_mixed_synergies(self, synergy_manager: SynergyManager, create_hero):
        """测试混合羁绊场景"""
        heroes = [
            create_hero(name="人族战士1", race="人族", profession="战士"),
            create_hero(name="人族战士2", race="人族", profession="战士"),
            create_hero(name="人族法师1", race="人族", profession="法师"),
            create_hero(name="人族法师2", race="人族", profession="法师"),
            create_hero(name="神族战士1", race="神族", profession="战士"),
            create_hero(name="魔种刺客1", race="魔种", profession="刺客"),
            create_hero(name="魔种刺客2", race="魔种", profession="刺客"),
        ]
        active = synergy_manager.calculate_active_synergies(heroes)
        
        # 人族4个 -> 激活
        human = next((s for s in active if s.synergy_name == "人族"), None)
        assert human.is_active()
        assert human.count == 4
        
        # 战士3个 -> 激活第一级(2个)
        warrior = next((s for s in active if s.synergy_name == "战士"), None)
        assert warrior.is_active()
        assert warrior.count == 3
        
        # 法师2个 -> 激活第一级
        mage = next((s for s in active if s.synergy_name == "法师"), None)
        assert mage.is_active()
        assert mage.count == 2
        
        # 神族1个 -> 未激活
        divine = next((s for s in active if s.synergy_name == "神族"), None)
        assert not divine.is_active()
        
        # 魔种2个 -> 激活
        demon = next((s for s in active if s.synergy_name == "魔种"), None)
        assert demon.is_active()
        
        # 刺客2个 -> 激活
        assassin = next((s for s in active if s.synergy_name == "刺客"), None)
        assert assassin.is_active()


# ============================================================================
# test_get_synergy_bonuses - 测试羁绊加成获取
# ============================================================================

class TestGetSynergyBonuses:
    """羁绊加成获取测试"""

    def test_no_bonuses_without_activation(
        self, synergy_manager: SynergyManager, create_hero
    ):
        """测试未激活羁绊时无加成"""
        hero = create_hero(name="单人", race="人族", profession="战士")
        bonuses = synergy_manager.get_synergy_bonuses([hero])
        
        assert bonuses == {}

    def test_single_synergy_bonus(
        self, synergy_manager: SynergyManager, create_heroes_with_synergy
    ):
        """测试单个羁绊的加成"""
        heroes = create_heroes_with_synergy("人族", "战士", 2)
        bonuses = synergy_manager.get_synergy_bonuses(heroes)
        
        assert "人族" in bonuses
        assert "attack_percent" in bonuses["人族"]
        assert bonuses["人族"]["attack_percent"] == 0.10

    def test_multiple_synergy_bonuses(self, synergy_manager: SynergyManager, create_hero):
        """测试多个羁绊的加成"""
        heroes = [
            create_hero(name="人族战士1", race="人族", profession="战士"),
            create_hero(name="人族战士2", race="人族", profession="战士"),
        ]
        bonuses = synergy_manager.get_synergy_bonuses(heroes)
        
        # 人族加成
        assert "人族" in bonuses
        assert bonuses["人族"]["attack_percent"] == 0.10
        assert bonuses["人族"]["spell_power"] == 0.10
        
        # 战士加成
        assert "战士" in bonuses
        assert bonuses["战士"]["armor_flat"] == 15

    def test_higher_level_bonuses(
        self, synergy_manager: SynergyManager, create_heroes_with_synergy
    ):
        """测试高级别羁绊加成"""
        # 人族6个 -> 最高级
        heroes = create_heroes_with_synergy("人族", "战士", 6)
        bonuses = synergy_manager.get_synergy_bonuses(heroes)
        
        assert "人族" in bonuses
        assert bonuses["人族"]["attack_percent"] == 0.45
        assert bonuses["人族"]["spell_power"] == 0.45
        
        # 战士6个 -> 最高级
        assert bonuses["战士"]["armor_flat"] == 60

    def test_bonuses_with_dead_heroes(self, synergy_manager: SynergyManager, create_hero):
        """测试死亡英雄不影响加成计算"""
        heroes = [
            create_hero(name="存活1", race="人族", profession="战士"),
            create_hero(name="存活2", race="人族", profession="战士"),
        ]
        dead_hero = create_hero(name="死亡", race="人族", profession="战士")
        dead_hero.hp = 0
        heroes.append(dead_hero)
        
        # alive_only=True，只计算存活的2个
        bonuses = synergy_manager.get_synergy_bonuses(heroes, alive_only=True)
        assert "人族" in bonuses  # 2个激活第一级

    def test_special_effects_not_in_bonuses(
        self, synergy_manager: SynergyManager, create_heroes_with_synergy
    ):
        """测试特殊效果不在常规加成中"""
        # 亡灵羁绊有特殊效果
        heroes = create_heroes_with_synergy("亡灵", "战士", 2)
        bonuses = synergy_manager.get_synergy_bonuses(heroes)
        
        # 亡灵的加成应该是空的（因为效果是减少敌方护甲）
        if "亡灵" in bonuses:
            assert bonuses["亡灵"] == {}


# ============================================================================
# test_apply_synergy_bonuses - 测试加成应用
# ============================================================================

class TestApplySynergyBonuses:
    """羁绊加成应用测试"""

    def test_apply_bonuses_returns_copies(
        self, synergy_manager: SynergyManager, create_heroes_with_synergy
    ):
        """测试应用加成返回副本而不修改原对象"""
        heroes = create_heroes_with_synergy("人族", "战士", 2)
        original_attack = heroes[0].attack
        original_defense = heroes[0].defense
        
        result = synergy_manager.apply_synergy_bonuses(heroes)
        
        # 原对象未修改
        assert heroes[0].attack == original_attack
        assert heroes[0].defense == original_defense
        
        # 返回的是副本
        assert result is not heroes
        assert len(result) == 2

    def test_apply_attack_percent_bonus(
        self, synergy_manager: SynergyManager, create_heroes_with_synergy
    ):
        """测试百分比攻击力加成应用"""
        heroes = create_heroes_with_synergy("人族", "战士", 2)
        original_attack = heroes[0].attack
        
        result = synergy_manager.apply_synergy_bonuses(heroes)
        
        # 人族2个 -> 攻击力+10%
        expected_attack = int(original_attack * 1.10)
        assert result[heroes[0].instance_id].attack == expected_attack

    def test_apply_armor_flat_bonus(
        self, synergy_manager: SynergyManager, create_heroes_with_synergy
    ):
        """测试固定护甲加成应用"""
        heroes = create_heroes_with_synergy("人族", "战士", 2)
        original_defense = heroes[0].defense
        
        result = synergy_manager.apply_synergy_bonuses(heroes)
        
        # 战士2个 -> 护甲+15
        expected_defense = original_defense + 15
        assert result[heroes[0].instance_id].defense == expected_defense

    def test_apply_multiple_bonuses(
        self, synergy_manager: SynergyManager, create_hero
    ):
        """测试多个羁绊加成叠加"""
        heroes = [
            create_hero(name="人族战士1", race="人族", profession="战士", attack=100, defense=50),
            create_hero(name="人族战士2", race="人族", profession="战士", attack=100, defense=50),
        ]
        
        result = synergy_manager.apply_synergy_bonuses(heroes)
        enhanced = result[heroes[0].instance_id]
        
        # 人族2个 -> 攻击+10% = 110
        # 战士2个 -> 护甲+15 = 65
        assert enhanced.attack == 110
        assert enhanced.defense == 65

    def test_apply_hp_percent_bonus(
        self, synergy_manager: SynergyManager, create_heroes_with_synergy
    ):
        """测试百分比生命值加成应用"""
        heroes = create_heroes_with_synergy("龙族", "坦克", 2)
        # 修改英雄使其触发坦克羁绊
        for hero in heroes:
            hero.profession = "坦克"
        
        result = synergy_manager.apply_synergy_bonuses(heroes)
        
        # 坦克2个 -> 生命值+15%
        # 检查生命值增加
        for hero in heroes:
            enhanced = result[hero.instance_id]
            assert enhanced.max_hp > hero.max_hp

    def test_apply_hp_flat_bonus(
        self, synergy_manager: SynergyManager, create_heroes_with_synergy
    ):
        """测试固定生命值加成应用"""
        heroes = create_heroes_with_synergy("兽族", "战士", 2)
        original_max_hp = heroes[0].max_hp
        
        result = synergy_manager.apply_synergy_bonuses(heroes)
        enhanced = result[heroes[0].instance_id]
        
        # 兽族2个 -> 生命值+200
        assert enhanced.max_hp == original_max_hp + 200

    def test_apply_attack_speed_bonus(
        self, synergy_manager: SynergyManager, create_heroes_with_synergy
    ):
        """测试攻速加成应用"""
        heroes = create_heroes_with_synergy("妖精", "战士", 2)
        original_speed = heroes[0].attack_speed
        
        result = synergy_manager.apply_synergy_bonuses(heroes)
        enhanced = result[heroes[0].instance_id]
        
        # 妖精2个 -> 攻速+20%
        expected_speed = original_speed * 1.20
        assert abs(enhanced.attack_speed - expected_speed) < 0.01


# ============================================================================
# test_synergy_level_progression - 测试羁绊等级递进
# ============================================================================

class TestSynergyLevelProgression:
    """羁绊等级递进测试"""

    def test_synergy_progress_basic(
        self, synergy_manager: SynergyManager, create_heroes_with_synergy
    ):
        """测试基本羁绊进度"""
        heroes = create_heroes_with_synergy("人族", "战士", 3)
        progress = synergy_manager.get_synergy_progress(heroes, "人族")
        
        assert progress["exists"] is True
        assert progress["count"] == 3
        assert progress["next_level_requirement"] == 4

    def test_synergy_progress_at_threshold(
        self, synergy_manager: SynergyManager, create_heroes_with_synergy
    ):
        """测试达到阈值的羁绊进度"""
        heroes = create_heroes_with_synergy("人族", "战士", 4)
        progress = synergy_manager.get_synergy_progress(heroes, "人族")
        
        assert progress["count"] == 4
        assert progress["next_level_requirement"] == 6

    def test_synergy_progress_max_level(
        self, synergy_manager: SynergyManager, create_heroes_with_synergy
    ):
        """测试最高等级羁绊进度"""
        heroes = create_heroes_with_synergy("人族", "战士", 10)
        progress = synergy_manager.get_synergy_progress(heroes, "人族")
        
        assert progress["count"] == 10
        # 6个已满级，没有下一级
        assert progress["next_level_requirement"] is None

    def test_synergy_progress_zero_count(
        self, synergy_manager: SynergyManager, create_heroes_with_synergy
    ):
        """测试零数量羁绊进度"""
        heroes = create_heroes_with_synergy("神族", "法师", 2)
        progress = synergy_manager.get_synergy_progress(heroes, "人族")
        
        assert progress["count"] == 0
        assert progress["current_level"] is None
        assert progress["next_level_requirement"] == 2

    def test_synergy_progress_nonexistent_synergy(
        self, synergy_manager: SynergyManager, create_hero
    ):
        """测试不存在羁绊的进度"""
        heroes = [create_hero(name="测试", race="人族", profession="战士")]
        progress = synergy_manager.get_synergy_progress(heroes, "不存在的羁绊")
        
        assert progress["exists"] is False
        assert progress["count"] == 0

    def test_all_synergy_level_configs(self, synergy_manager: SynergyManager):
        """测试所有羁绊的等级配置"""
        # 验证种族羁绊
        for race_name, synergy in RACE_SYNERGIES.items():
            assert synergy.name == race_name
            assert synergy.synergy_type == SynergyType.RACE
            assert len(synergy.levels) >= 1
            
            # 验证等级递增
            prev_count = 0
            for level in synergy.levels:
                assert level.required_count > prev_count
                prev_count = level.required_count
        
        # 验证职业羁绊
        for prof_name, synergy in PROFESSION_SYNERGIES.items():
            assert synergy.name == prof_name
            assert synergy.synergy_type == SynergyType.CLASS
            assert len(synergy.levels) >= 1

    def test_synergy_activation_sequence(
        self, synergy_manager: SynergyManager, create_heroes_with_synergy
    ):
        """测试羁绊逐级激活序列"""
        for count in range(1, 8):
            heroes = create_heroes_with_synergy("人族", "战士", count)
            active = synergy_manager.calculate_active_synergies(heroes)
            human = next((s for s in active if s.synergy_name == "人族"), None)
            
            if count < 2:
                assert not human.is_active()
            elif count < 4:
                assert human.is_active()
                assert "10%" in human.active_level.effect_description
            elif count < 6:
                assert human.is_active()
                assert "25%" in human.active_level.effect_description
            else:
                assert human.is_active()
                assert "45%" in human.active_level.effect_description

    def test_get_all_synergy_names(self):
        """测试获取所有羁绊名称"""
        names = get_all_synergy_names()
        
        assert "races" in names
        assert "professions" in names
        assert len(names["races"]) == len(RACE_SYNERGIES)
        assert len(names["professions"]) == len(PROFESSION_SYNERGIES)


# ============================================================================
# 边界条件测试
# ============================================================================

class TestSynergyBoundaryConditions:
    """羁绊系统边界条件测试"""

    def test_large_hero_count(
        self, synergy_manager: SynergyManager, create_heroes_with_synergy
    ):
        """测试大量英雄计数"""
        heroes = create_heroes_with_synergy("人族", "战士", 50)
        counts = synergy_manager.count_heroes_by_synergy(heroes)
        
        assert counts["人族"] == 50
        assert counts["战士"] == 50

    def test_all_same_race_different_professions(
        self, synergy_manager: SynergyManager, create_hero
    ):
        """测试相同种族不同职业"""
        heroes = []
        for i, profession in enumerate(PROFESSIONS):
            hero = create_hero(
                name=f"人族_{profession}_{i}",
                race="人族",
                profession=profession,
            )
            heroes.append(hero)
        
        counts = synergy_manager.count_heroes_by_synergy(heroes)
        assert counts["人族"] == len(PROFESSIONS)
        
        # 每个职业各1个
        for profession in PROFESSIONS:
            assert counts.get(profession) == 1

    def test_all_different_races_same_profession(
        self, synergy_manager: SynergyManager, create_hero
    ):
        """测试不同种族相同职业"""
        heroes = []
        for i, race in enumerate(RACES):
            hero = create_hero(
                name=f"{race}_战士_{i}",
                race=race,
                profession="战士",
            )
            heroes.append(hero)
        
        counts = synergy_manager.count_heroes_by_synergy(heroes)
        assert counts["战士"] == len(RACES)
        
        # 每个种族各1个
        for race in RACES:
            assert counts.get(race) == 1

    def test_create_synergy_manager_factory(self):
        """测试工厂函数创建羁绊管理器"""
        manager = create_synergy_manager()
        assert isinstance(manager, SynergyManager)
        
        # 验证有默认羁绊
        assert manager.get_synergy("人族") is not None
        assert manager.get_synergy("战士") is not None

    def test_custom_synergies(self):
        """测试自定义羁绊配置"""
        custom_race = Synergy(
            name="自定义种族",
            synergy_type=SynergyType.RACE,
            description="自定义羁绊",
            levels=[
                SynergyLevel(required_count=1, effect_description="1个激活"),
            ],
        )
        
        manager = SynergyManager(
            race_synergies={"自定义种族": custom_race},
            profession_synergies={},
        )
        
        synergy = manager.get_synergy("自定义种族")
        assert synergy is not None
        assert synergy.name == "自定义种族"

    def test_get_nonexistent_synergy(self, synergy_manager: SynergyManager):
        """测试获取不存在的羁绊"""
        result = synergy_manager.get_synergy("不存在的羁绊")
        assert result is None
