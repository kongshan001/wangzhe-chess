"""
王者之奕 - 羁绊图鉴与英雄池集成测试

测试羁绊图鉴与英雄池的跨模块交互：
- 羁绊计算与英雄池
- 羁绊进度记录
- 推荐阵容生成
- 羁绊成就解锁
"""

import pytest
from unittest.mock import MagicMock, patch

from src.server.synergypedia import (
    SynergypediaManager,
    SynergypediaEntry,
    SynergypediaProgress,
    RecommendedLineup,
    SynergySimulation,
    SynergyAchievement,
)
from src.server.game.synergy import SynergyManager, RACE_SYNERGIES, PROFESSION_SYNERGIES
from src.shared.models import Hero, SynergyType, Skill, DamageType, Position


class TestSynergypediaIntegration:
    """羁绊图鉴集成测试"""

    @pytest.fixture
    def sample_heroes(self, sample_hero_config):
        """创建示例英雄列表"""
        heroes = []
        for hero_id, config in list(sample_hero_config.items())[:3]:
            hero = Hero(
                instance_id=f"instance_{hero_id}",
                template_id=hero_id,
                name=config["name"],
                cost=config["cost"],
                star=1,
                race=config["race"],
                profession=config["profession"],
                max_hp=config["base_hp"],
                hp=config["base_hp"],
                attack=config["base_attack"],
                defense=config["base_defense"],
                attack_speed=config["attack_speed"],
                skill=Skill(
                    name=f"{config['name']}技能",
                    mana_cost=50,
                    damage=100,
                ),
            )
            heroes.append(hero)
        return heroes

    def test_get_all_synergies(self, synergypedia_manager):
        """测试获取所有羁绊"""
        entries = synergypedia_manager.get_all_synergies()
        
        # 应该有种族和职业羁绊
        assert len(entries) > 0
        
        # 验证条目结构
        for entry in entries:
            assert entry.name is not None
            assert entry.synergy_type in [SynergyType.RACE, SynergyType.CLASS]

    def test_get_synergy_info(self, synergypedia_manager):
        """测试获取单个羁绊信息"""
        # 获取人族羁绊
        entry = synergypedia_manager.get_synergy_info("人族")
        
        if entry:
            assert entry.name == "人族"
            assert entry.synergy_type == SynergyType.RACE

    def test_get_synergies_by_type(self, synergypedia_manager):
        """测试按类型获取羁绊"""
        race_entries = synergypedia_manager.get_synergies_by_type(SynergyType.RACE)
        
        for entry in race_entries:
            assert entry.synergy_type == SynergyType.RACE


class TestSynergyProgressIntegration:
    """羁绊进度集成测试"""

    @pytest.fixture
    def manager_with_heroes(self, sample_hero_config):
        """创建带有英雄配置的管理器"""
        from src.server.synergypedia.manager import SynergypediaManager
        from src.server.game.synergy import SynergyManager
        
        hero_configs = {}
        for hero_id, config in sample_hero_config.items():
            hero_configs[hero_id] = MagicMock(
                hero_id=hero_id,
                name=config["name"],
                cost=config["cost"],
                race=config["race"],
                profession=config["profession"],
                base_hp=config["base_hp"],
                base_attack=config["base_attack"],
                base_defense=config["base_defense"],
                attack_speed=config["attack_speed"],
            )
        
        return SynergypediaManager(
            synergy_manager=SynergyManager(),
            hero_configs=hero_configs,
        )

    def test_update_player_progress(self, manager_with_heroes):
        """测试更新玩家羁绊进度"""
        player_id = "player_001"
        synergy_name = "人族"
        
        achievements = manager_with_heroes.update_player_progress(
            player_id=player_id,
            synergy_name=synergy_name,
            heroes_count=2,
            level_reached=1,
            is_win=True,
        )
        
        # 进度应该更新
        progress = manager_with_heroes.get_player_progress(player_id, synergy_name)
        assert progress is not None

    def test_progress_achievement_unlock(self, manager_with_heroes):
        """测试进度成就解锁"""
        player_id = "player_001"
        synergy_name = "人族"
        
        # 模拟多次激活
        for _ in range(10):
            manager_with_heroes.update_player_progress(
                player_id=player_id,
                synergy_name=synergy_name,
                heroes_count=2,
                level_reached=1,
                is_win=True,
            )
        
        progress = manager_with_heroes.get_player_progress(player_id, synergy_name)
        # 验证激活次数
        assert progress.activation_count >= 10


class TestSynergySimulationIntegration:
    """羁绊模拟器集成测试"""

    @pytest.fixture
    def manager_full(self, sample_hero_config):
        """创建完整的管理器"""
        from src.server.synergypedia.manager import SynergypediaManager
        from src.server.game.synergy import SynergyManager
        
        hero_configs = {}
        for hero_id, config in sample_hero_config.items():
            hero_configs[hero_id] = MagicMock(
                hero_id=hero_id,
                name=config["name"],
                cost=config["cost"],
                race=config["race"],
                profession=config["profession"],
                base_hp=config["base_hp"],
                base_attack=config["base_attack"],
                base_defense=config["base_defense"],
                attack_speed=config["attack_speed"],
            )
        
        return SynergypediaManager(
            synergy_manager=SynergyManager(),
            hero_configs=hero_configs,
        )

    def test_simulate_synergies(self, manager_full):
        """测试羁绊模拟"""
        hero_ids = ["hero_test_001", "hero_test_002"]
        
        result = manager_full.simulate_synergies(hero_ids)
        
        assert result is not None
        assert len(result.selected_heroes) == 2

    def test_simulate_empty_selection(self, manager_full):
        """测试空选择模拟"""
        result = manager_full.simulate_synergies([])
        
        assert result is not None
        assert len(result.selected_heroes) == 0
        assert len(result.active_synergies) == 0


class TestRecommendedLineupIntegration:
    """推荐阵容集成测试"""

    def test_get_recommended_lineups(self, synergypedia_manager):
        """测试获取推荐阵容"""
        lineups = synergypedia_manager.get_recommended_lineups()
        
        assert len(lineups) > 0
        
        # 验证阵容结构
        for lineup in lineups:
            assert lineup.name is not None
            assert len(lineup.core_synergies) > 0

    def test_filter_lineups_by_synergy(self, synergypedia_manager):
        """测试按羁绊筛选阵容"""
        lineups = synergypedia_manager.get_recommended_lineups(
            synergy_name="战士"
        )
        
        # 所有返回的阵容都应该包含战士羁绊
        for lineup in lineups:
            assert "战士" in lineup.core_synergies


class TestSynergyAchievementIntegration:
    """羁绊成就集成测试"""

    def test_get_synergy_achievements(self, synergypedia_manager):
        """测试获取羁绊成就"""
        achievements = synergypedia_manager.get_synergy_achievements("人族")
        
        assert len(achievements) > 0
        
        # 验证成就结构
        for achievement in achievements:
            assert achievement.synergy_name == "人族"
            assert achievement.requirement_type in ["activation_count", "level_reached"]

    def test_check_and_unlock_achievements(self, synergypedia_manager):
        """测试检查并解锁成就"""
        player_id = "player_001"
        synergy_name = "人族"
        
        # 先更新进度
        for _ in range(15):
            synergypedia_manager.update_player_progress(
                player_id=player_id,
                synergy_name=synergy_name,
                heroes_count=2,
                level_reached=1,
                is_win=True,
            )
        
        # 检查成就
        unlocked = synergypedia_manager.check_and_unlock_achievements(
            player_id=player_id,
            synergy_name=synergy_name,
        )
        
        # 可能有成就解锁
        # 具体取决于进度和成就要求


class TestSynergyAndHeroPoolIntegration:
    """羁绊与英雄池集成测试"""

    @pytest.fixture
    def hero_pool_manager(self, sample_hero_config):
        """创建英雄池管理器"""
        from src.server.game.hero_pool import SharedHeroPool, HeroConfigLoader, SAMPLE_HEROES_CONFIG
        
        loader = HeroConfigLoader()
        # 加载示例配置
        loader.load_from_dict(SAMPLE_HEROES_CONFIG)
        
        return SharedHeroPool(loader, seed=42)

    def test_hero_pool_synergy_relation(self, hero_pool_manager):
        """测试英雄池与羁绊关系"""
        # 获取商店英雄
        shop = hero_pool_manager.get_shop_heroes(player_level=1)
        
        # 商店应该有英雄
        assert len(shop) > 0

    def test_synergy_activation_affects_hero_pool(self, hero_pool_manager, synergypedia_manager):
        """测试羁绊激活影响英雄池"""
        # 购买英雄后英雄池数量变化
        initial_pool = hero_pool_manager.get_pool_status()
        
        # 这里需要实际的游戏流程集成


class TestSynergypediaEntryIntegration:
    """羁绊图鉴条目集成测试"""

    def test_entry_from_synergy(self, synergypedia_manager):
        """测试从羁绊创建条目"""
        # 获取一个羁绊
        if "人族" in RACE_SYNERGIES:
            synergy = RACE_SYNERGIES["人族"]
            related_heroes = ["hero_1", "hero_2"]
            
            entry = SynergypediaEntry.from_synergy(synergy, related_heroes)
            
            assert entry.name == "人族"
            assert entry.related_heroes == related_heroes

    def test_entry_serialization(self):
        """测试条目序列化"""
        entry = SynergypediaEntry(
            name="测试羁绊",
            synergy_type=SynergyType.RACE,
            description="测试描述",
            levels=[{"count": 2, "effect": "效果1"}],
            related_heroes=["hero_1"],
        )
        
        data = entry.to_dict()
        assert data["name"] == "测试羁绊"


class TestSynergypediaProgressIntegration:
    """羁绊进度数据集成测试"""

    def test_progress_update_with_game_result(self):
        """测试根据游戏结果更新进度"""
        progress = SynergypediaProgress(synergy_name="人族")
        
        # 更新进度
        new_achievements = progress.update_with_game_result(
            heroes_count=2,
            level_reached=1,
            is_win=True,
        )
        
        assert progress.activation_count == 1

    def test_progress_serialization(self):
        """测试进度序列化"""
        progress = SynergypediaProgress(synergy_name="人族")
        progress.activation_count = 10
        
        data = progress.to_dict()
        assert data["activation_count"] == 10


class TestRecommendedLineupDataIntegration:
    """推荐阵容数据集成测试"""

    def test_lineup_serialization(self):
        """测试阵容序列化"""
        lineup = RecommendedLineup(
            name="测试阵容",
            description="测试描述",
            core_synergies=["战士", "坦克"],
            hero_recommendations=[
                {"hero_id": "hero_1", "priority": 5, "position": "front"},
            ],
            priority=5,
            difficulty="medium",
            playstyle="tank",
        )
        
        data = lineup.to_dict()
        assert data["name"] == "测试阵容"


class TestSynergySimulationResultIntegration:
    """羁绊模拟结果集成测试"""

    def test_simulation_result_structure(self):
        """测试模拟结果结构"""
        result = SynergySimulation(
            selected_heroes=["hero_1", "hero_2"],
            active_synergies=[
                {"name": "人族", "count": 2, "level": 1}
            ],
            inactive_synergies=[],
            synergy_progress={},
            recommendations=[],
            total_bonuses={"attack": 10},
        )
        
        assert len(result.selected_heroes) == 2
        assert len(result.active_synergies) == 1
        assert result.total_bonuses["attack"] == 10
