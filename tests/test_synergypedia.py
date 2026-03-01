"""
王者之奕 - 羁绊图鉴系统测试

测试羁绊图鉴系统的核心功能：
- 羁绊信息获取
- 羁绊进度追踪
- 阵容推荐
- 羁绊模拟器
- 成就系统
"""

from dataclasses import dataclass

import pytest

from src.server.synergypedia.manager import SynergypediaManager
from src.server.synergypedia.models import (
    RecommendedLineup,
    SynergyAchievement,
    SynergypediaEntry,
    SynergypediaProgress,
    SynergySimulation,
)
from src.shared.models import Synergy, SynergyLevel, SynergyType

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_synergy():
    """创建示例羁绊定义"""
    return Synergy(
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
    )


@pytest.fixture
def sample_hero_configs():
    """创建示例英雄配置"""

    @dataclass
    class MockHeroConfig:
        hero_id: str
        name: str
        cost: int
        race: str
        profession: str
        base_hp: int
        base_attack: int
        base_defense: int
        attack_speed: float

    return {
        "warrior_1": MockHeroConfig(
            hero_id="warrior_1",
            name="战士A",
            cost=1,
            race="人族",
            profession="战士",
            base_hp=800,
            base_attack=60,
            base_defense=30,
            attack_speed=0.8,
        ),
        "warrior_2": MockHeroConfig(
            hero_id="warrior_2",
            name="战士B",
            cost=2,
            race="兽族",
            profession="战士",
            base_hp=900,
            base_attack=55,
            base_defense=35,
            attack_speed=0.7,
        ),
        "warrior_3": MockHeroConfig(
            hero_id="warrior_3",
            name="战士C",
            cost=3,
            race="亡灵",
            profession="战士",
            base_hp=850,
            base_attack=65,
            base_defense=40,
            attack_speed=0.75,
        ),
        "mage_1": MockHeroConfig(
            hero_id="mage_1",
            name="法师A",
            cost=3,
            race="人族",
            profession="法师",
            base_hp=600,
            base_attack=80,
            base_defense=20,
            attack_speed=0.6,
        ),
        "mage_2": MockHeroConfig(
            hero_id="mage_2",
            name="法师B",
            cost=4,
            race="神族",
            profession="法师",
            base_hp=550,
            base_attack=90,
            base_defense=15,
            attack_speed=0.55,
        ),
    }


@pytest.fixture
def manager(sample_hero_configs):
    """创建羁绊图鉴管理器"""
    return SynergypediaManager(hero_configs=sample_hero_configs)


# ============================================================================
# 模型测试
# ============================================================================


class TestSynergypediaEntry:
    """测试羁绊图鉴条目"""

    def test_from_synergy(self, sample_synergy, sample_hero_configs):
        """测试从 Synergy 创建图鉴条目"""
        related_heroes = ["warrior_1", "warrior_2", "warrior_3"]
        entry = SynergypediaEntry.from_synergy(sample_synergy, related_heroes)

        assert entry.name == "战士"
        assert entry.synergy_type == SynergyType.CLASS
        assert entry.description == "战士获得额外护甲"
        assert len(entry.levels) == 3
        assert len(entry.related_heroes) == 3
        assert entry.icon != ""
        assert entry.tips != ""

    def test_to_dict(self, sample_synergy):
        """测试序列化为字典"""
        entry = SynergypediaEntry.from_synergy(sample_synergy, ["hero_1"])
        data = entry.to_dict()

        assert data["name"] == "战士"
        assert data["synergy_type"] == "class"
        assert len(data["levels"]) == 3

    def test_get_level_for_count(self, sample_synergy):
        """测试根据数量获取羁绊等级"""
        entry = SynergypediaEntry.from_synergy(sample_synergy, [])

        # 未激活
        level = entry.get_level_for_count(1)
        assert level is None

        # 激活1级
        level = entry.get_level_for_count(2)
        assert level is not None
        assert level["required_count"] == 2

        # 激活2级
        level = entry.get_level_for_count(4)
        assert level is not None
        assert level["required_count"] == 4

        # 激活3级
        level = entry.get_level_for_count(6)
        assert level is not None
        assert level["required_count"] == 6


class TestSynergypediaProgress:
    """测试羁绊进度"""

    def test_initial_state(self):
        """测试初始状态"""
        progress = SynergypediaProgress(synergy_name="战士")

        assert progress.activation_count == 0
        assert progress.max_heroes_used == 0
        assert progress.highest_level_reached == 0
        assert progress.total_games == 0
        assert progress.win_rate == 0.0
        assert len(progress.achievements) == 0

    def test_update_with_game_result(self):
        """测试更新对局结果"""
        progress = SynergypediaProgress(synergy_name="战士")

        # 更新一次胜利
        new_achievements = progress.update_with_game_result(
            heroes_count=4,
            level_reached=2,
            is_win=True,
        )

        assert progress.activation_count == 1
        assert progress.total_games == 1
        assert progress.win_count == 1
        assert progress.max_heroes_used == 4
        assert progress.highest_level_reached == 2
        assert progress.win_rate == 100.0

        # 应该解锁了等级成就
        assert len(new_achievements) > 0

    def test_win_rate_calculation(self):
        """测试胜率计算"""
        progress = SynergypediaProgress(
            synergy_name="战士",
            total_games=10,
            win_count=7,
        )

        assert progress.win_rate == 70.0

    def test_achievement_unlock(self):
        """测试成就解锁"""
        progress = SynergypediaProgress(synergy_name="战士")

        # 模拟10次激活
        for _ in range(10):
            progress.update_with_game_result(
                heroes_count=2,
                level_reached=1,
                is_win=True,
            )

        # 应该解锁入门者成就
        assert "战士入门者" in progress.achievements


class TestRecommendedLineup:
    """测试推荐阵容"""

    def test_to_dict(self):
        """测试序列化"""
        lineup = RecommendedLineup(
            name="战士坦克流",
            description="高护甲阵容",
            core_synergies=["战士", "坦克"],
            hero_recommendations=[
                {"hero_id": "warrior_1", "priority": 5},
            ],
            priority=5,
            difficulty="easy",
        )

        data = lineup.to_dict()

        assert data["name"] == "战士坦克流"
        assert len(data["core_synergies"]) == 2
        assert data["difficulty"] == "easy"


class TestSynergySimulation:
    """测试羁绊模拟"""

    def test_is_synergy_active(self):
        """测试检查羁绊是否激活"""
        simulation = SynergySimulation(
            selected_heroes=["hero_1", "hero_2"],
            active_synergies=[
                {"name": "战士", "level": 1, "count": 2},
            ],
            inactive_synergies=[],
            synergy_progress={},
            recommendations=[],
        )

        assert simulation.is_synergy_active("战士") is True
        assert simulation.is_synergy_active("法师") is False

    def test_get_synergy_level(self):
        """测试获取羁绊等级"""
        simulation = SynergySimulation(
            selected_heroes=["hero_1", "hero_2"],
            active_synergies=[
                {"name": "战士", "level": 2, "count": 4},
            ],
            inactive_synergies=[],
            synergy_progress={},
            recommendations=[],
        )

        assert simulation.get_synergy_level("战士") == 2
        assert simulation.get_synergy_level("法师") == 0


class TestSynergyAchievement:
    """测试羁绊成就"""

    def test_check_unlock_activation_count(self):
        """测试激活次数成就解锁"""
        achievement = SynergyAchievement(
            achievement_id="test_1",
            name="测试成就",
            description="激活10次",
            synergy_name="战士",
            requirement_type="activation_count",
            requirement_value=10,
        )

        progress = SynergypediaProgress(
            synergy_name="战士",
            activation_count=5,
        )

        # 未解锁
        assert achievement.check_unlock(progress) is False

        # 满足条件
        progress.activation_count = 10
        assert achievement.check_unlock(progress) is True
        assert achievement.is_unlocked is True

        # 已经解锁
        assert achievement.check_unlock(progress) is False


# ============================================================================
# 管理器测试
# ============================================================================


class TestSynergypediaManager:
    """测试羁绊图鉴管理器"""

    def test_get_all_synergies(self, manager):
        """测试获取所有羁绊"""
        entries = manager.get_all_synergies()

        # 应该包含种族和职业羁绊
        assert len(entries) > 0

        # 检查是否有种族和职业（使用值比较）
        has_race = any(e.synergy_type.value == "race" for e in entries)
        has_class = any(e.synergy_type.value == "class" for e in entries)
        assert has_race
        assert has_class

    def test_get_synergy_info(self, manager):
        """测试获取单个羁绊信息"""
        entry = manager.get_synergy_info("战士")

        assert entry is not None
        assert entry.name == "战士"
        assert entry.synergy_type.value == "class"

    def test_get_synergy_info_not_found(self, manager):
        """测试获取不存在的羁绊"""
        entry = manager.get_synergy_info("不存在的羁绊")
        assert entry is None

    def test_get_synergies_by_type(self, manager):
        """测试按类型获取羁绊"""
        races = manager.get_synergies_by_type(SynergyType.RACE)
        classes = manager.get_synergies_by_type(SynergyType.CLASS)

        assert all(e.synergy_type.value == "race" for e in races)
        assert all(e.synergy_type.value == "class" for e in classes)

    def test_get_recommended_lineups(self, manager):
        """测试获取推荐阵容"""
        # 获取所有推荐
        all_recommendations = manager.get_recommended_lineups()
        assert len(all_recommendations) > 0

        # 按羁绊筛选
        warrior_recommendations = manager.get_recommended_lineups(
            synergy_name="战士",
        )
        for rec in warrior_recommendations:
            assert "战士" in rec.core_synergies

    def test_simulate_synergies(self, manager):
        """测试羁绊模拟"""
        # 选择3个战士
        hero_ids = ["warrior_1", "warrior_2", "warrior_3"]
        result = manager.simulate_synergies(hero_ids)

        assert len(result.selected_heroes) == 3
        # 战士应该激活（3个战士，激活1级需要2个）
        assert result.is_synergy_active("战士")

    def test_simulate_synergies_multiple_types(self, manager):
        """测试多类型羁绊模拟"""
        # 选择混合英雄
        hero_ids = ["warrior_1", "warrior_2", "mage_1", "mage_2"]
        result = manager.simulate_synergies(hero_ids)

        # 应该激活战士2和法师2
        assert result.is_synergy_active("战士")
        assert result.is_synergy_active("法师")
        # 人族也应该激活（warrior_1和mage_1都是人族）
        assert result.is_synergy_active("人族")

    def test_get_player_progress_new_player(self, manager):
        """测试新玩家的羁绊进度"""
        progress = manager.get_player_progress("new_player", "战士")
        assert progress is None

    def test_update_player_progress(self, manager):
        """测试更新玩家进度"""
        new_achievements = manager.update_player_progress(
            player_id="player_1",
            synergy_name="战士",
            heroes_count=4,
            level_reached=2,
            is_win=True,
        )

        # 获取更新后的进度
        progress = manager.get_player_progress("player_1", "战士")
        assert progress is not None
        assert progress.activation_count == 1
        assert progress.total_games == 1
        assert progress.max_heroes_used == 4
        assert progress.highest_level_reached == 2

    def test_get_synergy_achievements(self, manager):
        """测试获取羁绊成就"""
        achievements = manager.get_synergy_achievements("战士")

        # 应该有激活次数和等级成就
        assert len(achievements) > 0

        # 检查成就类型
        has_count_achievement = any(a.requirement_type == "activation_count" for a in achievements)
        has_level_achievement = any(a.requirement_type == "level_reached" for a in achievements)
        assert has_count_achievement
        assert has_level_achievement


# ============================================================================
# 集成测试
# ============================================================================


class TestSynergypediaIntegration:
    """集成测试"""

    def test_full_game_flow(self, manager):
        """测试完整游戏流程"""
        player_id = "test_player"

        # 1. 查看羁绊图鉴
        entries = manager.get_all_synergies()
        assert len(entries) > 0

        # 2. 选择英雄进行模拟
        hero_ids = ["warrior_1", "warrior_2", "warrior_3"]
        simulation = manager.simulate_synergies(hero_ids)
        assert simulation.is_synergy_active("战士")

        # 3. 查看推荐阵容
        recommendations = manager.get_recommended_lineups("战士")
        assert len(recommendations) > 0

        # 4. 模拟对局结束，更新进度
        manager.update_player_progress(
            player_id=player_id,
            synergy_name="战士",
            heroes_count=3,
            level_reached=1,
            is_win=True,
        )

        # 5. 检查进度
        progress = manager.get_player_progress(player_id, "战士")
        assert progress is not None
        assert progress.activation_count == 1

        # 6. 查看成就
        achievements = manager.get_synergy_achievements("战士")
        assert len(achievements) > 0


# ============================================================================
# 运行测试
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
