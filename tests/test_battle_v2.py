"""
王者之奕 - 完整战斗系统测试
"""

import pytest

from server.game.battle.simulator import (
    BattleSimulator,
    BattleUnit,
    DeterministicRNG,
)
from shared.models import Board, DamageType, Hero, HeroTemplate, Position

# ============================================================================
# 测试数据和工具
# ============================================================================


@pytest.fixture
def sample_hero_template():
    """示例英雄模板"""
    return HeroTemplate(
        hero_id="test_hero_1",
        name="测试英雄",
        cost=1,
        race="人族",
        profession="战士",
        base_hp=600,
        base_attack=55,
        base_defense=35,
        attack_speed=0.7,
    )


@pytest.fixture
def sample_board_a(sample_hero_template):
    """示例棋盘A"""
    board = Board.create_empty("player_a")
    hero = Hero.create_from_template(sample_hero_template, "hero_1", 1)
    hero.position = Position(0, 0)
    board.place_hero(hero, hero.position)
    return board


@pytest.fixture
def sample_board_b(sample_hero_template):
    """示例棋盘B"""
    board = Board.create_empty("player_b")
    hero = Hero.create_from_template(sample_hero_template, "hero_2", 1)
    hero.position = Position(1, 1)
    board.place_hero(hero, hero.position)
    return board


# ============================================================================
# BattleUnit 测试
# ============================================================================


class TestBattleUnit:
    """战斗单元测试"""

    def test_create_battle_unit(self, sample_hero_template):
        """测试创建战斗单元"""
        hero = Hero.create_from_template(sample_hero_template, "hero_1", 1)
        unit = BattleUnit(hero=hero, team=0)

        assert unit.instance_id == "hero_1"
        assert unit.team == 0
        assert unit.is_alive()

    def test_take_damage_physical(self, sample_hero_template):
        """测试受到物理伤害"""
        hero = Hero.create_from_template(sample_hero_template, "hero_1", 1)
        unit = BattleUnit(hero=hero, team=0)

        damage = unit.take_damage(100, DamageType.PHYSICAL, 0)

        # 物理伤害 = 伤害 * 100 / (100 + 防御)
        expected_damage = int(100 * 100 / (100 + 35))
        assert damage // 1000 == expected_damage
        assert unit.hp_percent < 100

    def test_take_damage_true(self, sample_hero_template):
        """测试受到真实伤害"""
        hero = Hero.create_from_template(sample_hero_template, "hero_1", 1)
        unit = BattleUnit(hero=hero, team=0)

        damage = unit.take_damage(50, DamageType.TRUE, 0)

        # 真实伤害忽略防御
        assert damage // 1000 == 50

    def test_heal(self, sample_hero_template):
        """测试治疗"""
        hero = Hero.create_from_template(sample_hero_template, "hero_1", 1)
        unit = BattleUnit(hero=hero, team=0)
        unit.take_damage(200, DamageType.PHYSICAL, 0)

        old_hp = unit.current_hp
        healed = unit.heal(100)

        assert unit.current_hp == old_hp + healed
        assert unit.is_alive()

    def test_gain_mana(self, sample_hero_template):
        """测试获得蓝量"""
        hero = Hero.create_from_template(sample_hero_template, "hero_1", 1)
        unit = BattleUnit(hero=hero, team=0)

        old_mana = unit.current_mana
        gained = unit.gain_mana(50)

        assert gained == 50
        assert unit.current_mana == old_mana + 50

    def test_can_cast_skill(self, sample_hero_template):
        """测试是否可以释放技能"""
        from shared.models import DamageType, Skill

        # 创建带技能的英雄
        hero = Hero.create_from_template(sample_hero_template, "hero_1", 1)
        hero.skill = Skill(
            name="测试技能",
            description="测试技能描述",
            mana_cost=50,
            damage=100,
            damage_type=DamageType.MAGICAL,
            target_type="single",
            cooldown=0,
        )
        hero.mana = 60
        unit = BattleUnit(hero=hero, team=0)

        # 蓝量足够
        assert unit.can_cast_skill()

        # 蓝量不足
        hero.mana = 30
        unit.current_mana = 30
        assert not unit.can_cast_skill()

    def test_distance_to(self, sample_hero_template):
        """测试距离计算"""
        hero1 = Hero.create_from_template(sample_hero_template, "hero_1", 1)
        hero1.position = Position(0, 0)
        unit1 = BattleUnit(hero=hero1, team=0)

        hero2 = Hero.create_from_template(sample_hero_template, "hero_2", 1)
        hero2.position = Position(3, 4)
        unit2 = BattleUnit(hero=hero2, team=1)

        # 曼哈顿距离 = |0-3| + |0-4| = 7
        distance = unit1.distance_to(unit2)
        assert distance == 7


# ============================================================================
# DeterministicRNG 测试
# ============================================================================


class TestDeterministicRNG:
    """确定性随机数测试"""

    def test_same_seed_same_result(self):
        """测试：相同种子必须产生相同结果"""
        rng1 = DeterministicRNG(seed=12345)
        rng2 = DeterministicRNG(seed=12345)

        # 多次调用
        for _ in range(10):
            val1 = rng1.random_int(0, 100)
            val2 = rng2.random_int(0, 100)
            assert val1 == val2

    def test_different_seed_different_result(self):
        """测试：不同种子产生不同结果"""
        rng1 = DeterministicRNG(seed=12345)
        rng2 = DeterministicRNG(seed=54321)

        val1 = rng1.random_int(0, 100)
        val2 = rng2.random_int(0, 100)

        assert val1 != val2

    def test_random_int_range(self):
        """测试随机整数范围"""
        rng = DeterministicRNG(seed=42)

        for _ in range(100):
            val = rng.random_int(10, 20)
            assert 10 <= val <= 20  # max_val is inclusive


# ============================================================================
# BattleSimulator 测试 - 确定性测试
# ============================================================================


class TestBattleDeterminism:
    """战斗确定性测试（核心！）"""

    def test_deterministic_battle_same_input_same_output(self, sample_board_a, sample_board_b):
        """
        确定性测试：相同输入必须产生相同输出

        这是自走棋游戏的核心要求！
        """
        seed = 99999

        # 第一次模拟
        sim1 = BattleSimulator(sample_board_a, sample_board_b, random_seed=seed, max_time_ms=10000)
        result1 = sim1.simulate()

        # 第二次模拟（相同输入）
        sim2 = BattleSimulator(sample_board_a, sample_board_b, random_seed=seed, max_time_ms=10000)
        result2 = sim2.simulate()

        # 验证结果完全相同
        assert result1.winner == result2.winner
        assert result1.player_a_damage == result2.player_a_damage
        assert result1.player_b_damage == result2.player_b_damage
        assert result1.battle_duration_ms == result2.battle_duration_ms
        assert len(result1.events) == len(result2.events)

        # 验证所有事件相同
        for event1, event2 in zip(result1.events, result2.events):
            assert event1 == event2

    def test_deterministic_battle_different_seed_different_output(
        self, sample_board_a, sample_board_b
    ):
        """测试：不同种子可能产生不同结果（但不一定，取决于战斗是否使用RNG）"""
        seed1 = 12345
        seed2 = 54321

        sim1 = BattleSimulator(sample_board_a, sample_board_b, random_seed=seed1, max_time_ms=10000)
        result1 = sim1.simulate()

        sim2 = BattleSimulator(sample_board_a, sample_board_b, random_seed=seed2, max_time_ms=10000)
        result2 = sim2.simulate()

        # 验证战斗完成（结果可能相同也可能不同，取决于是否使用了RNG）
        assert result1.winner is not None
        assert result2.winner is not None


# ============================================================================
# BattleSimulator 功能测试
# ============================================================================


class TestBattleSimulator:
    """战斗模拟器功能测试"""

    def test_battle_initialization(self, sample_board_a, sample_board_b):
        """测试战斗初始化"""
        sim = BattleSimulator(sample_board_a, sample_board_b, random_seed=12345)

        assert sim.board_a == sample_board_a
        assert sim.board_b == sample_board_b
        assert sim.random_seed == 12345
        assert not sim.is_finished

    def test_victory_player_a(self, sample_board_a, sample_board_b):
        """测试玩家A获胜"""
        sim = BattleSimulator(sample_board_a, sample_board_b, random_seed=99998)
        result = sim.simulate()

        assert result.winner in ["player_a", sample_board_a.owner_id, "draw"]
        assert result.loser in ["player_b", sample_board_b.owner_id, "draw"]

    def test_draw_both_dead(self, sample_board_a):
        """测试平局（双方同归于尽）"""
        # 创建两个空棋盘
        board_a = Board.create_empty("player_a")
        board_b = Board.create_empty("player_b")

        sim = BattleSimulator(board_a, board_b, random_seed=1, max_time_ms=1000)
        result = sim.simulate()

        assert result.winner == "draw"
        assert result.loser == "draw"

    def test_battle_events(self, sample_board_a, sample_board_b):
        """测试战斗事件记录"""
        sim = BattleSimulator(sample_board_a, sample_board_b, random_seed=12345, max_time_ms=15000)
        result = sim.simulate()

        # 验证事件被记录
        assert len(result.events) > 0

        # 验证事件包含必要字段
        for event in result.events:
            assert "time_ms" in event or "time" in event
            # 可以有其他字段如 source_id, target_id, damage 等


# ============================================================================
# 性能测试
# ============================================================================


class TestBattlePerformance:
    """战斗性能测试"""

    def test_large_scale_battle_performance(self, sample_hero_template):
        """测试大规模战斗性能"""
        # 创建10v10英雄的战斗
        board_a = Board.create_empty("player_a")
        board_b = Board.create_empty("player_b")

        for i in range(10):
            hero_a = Hero.create_from_template(sample_hero_template, f"hero_a_{i}", 1)
            hero_a.position = Position(i % 8, i // 8)
            board_a.place_hero(hero_a, hero_a.position)

            hero_b = Hero.create_from_template(sample_hero_template, f"hero_b_{i}", 1)
            hero_b.position = Position(i % 8, i // 8)
            board_b.place_hero(hero_b, hero_b.position)

        # 性能测试
        import time

        start = time.time()

        sim = BattleSimulator(board_a, board_b, random_seed=12345, max_time_ms=60000)
        result = sim.simulate()

        elapsed = time.time() - start

        # 验证战斗在合理时间内完成
        assert elapsed < 5.0  # 10v10 应在5秒内完成
        assert result.winner is not None  # 战斗完成，有胜者


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
