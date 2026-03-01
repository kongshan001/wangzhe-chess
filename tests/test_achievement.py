"""
王者之奕 - 成就系统测试

测试成就系统的核心功能：
- Achievement 数据类
- AchievementRequirement 数据类
- AchievementReward 数据类
- PlayerAchievement 数据类
- AchievementManager 管理器
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from src.server.achievement.manager import AchievementManager
from src.server.achievement.models import (
    Achievement,
    AchievementCategory,
    AchievementRequirement,
    AchievementReward,
    AchievementTier,
    PlayerAchievement,
    RequirementType,
)

# ============================================================================
# AchievementCategory 测试
# ============================================================================


class TestAchievementCategory:
    """成就类别枚举测试"""

    def test_category_values(self):
        """测试类别值"""
        assert AchievementCategory.COLLECTION.value == "collection"
        assert AchievementCategory.BATTLE.value == "battle"
        assert AchievementCategory.COMBAT.value == "combat"
        assert AchievementCategory.SOCIAL.value == "social"
        assert AchievementCategory.SPECIAL.value == "special"


# ============================================================================
# AchievementTier 测试
# ============================================================================


class TestAchievementTier:
    """成就等级枚举测试"""

    def test_tier_values(self):
        """测试等级值"""
        assert AchievementTier.BRONZE.value == 1
        assert AchievementTier.SILVER.value == 2
        assert AchievementTier.GOLD.value == 3
        assert AchievementTier.DIAMOND.value == 4

    def test_tier_display_name(self):
        """测试等级显示名称"""
        assert AchievementTier.BRONZE.display_name == "铜牌"
        assert AchievementTier.SILVER.display_name == "银牌"
        assert AchievementTier.GOLD.display_name == "金牌"
        assert AchievementTier.DIAMOND.display_name == "钻石"


# ============================================================================
# RequirementType 测试
# ============================================================================


class TestRequirementType:
    """需求类型枚举测试"""

    def test_requirement_types(self):
        """测试需求类型"""
        assert RequirementType.COLLECT_HEROES.value == "collect_heroes"
        assert RequirementType.WIN_GAMES.value == "win_games"
        assert RequirementType.WIN_STREAK.value == "win_streak"
        assert RequirementType.DEAL_DAMAGE.value == "deal_damage"


# ============================================================================
# AchievementRequirement 测试
# ============================================================================


class TestAchievementRequirement:
    """成就需求测试"""

    def test_requirement_creation(self):
        """测试需求创建"""
        req = AchievementRequirement(
            type=RequirementType.WIN_GAMES,
            target=100,
        )
        assert req.type == RequirementType.WIN_GAMES
        assert req.target == 100
        assert req.conditions == {}

    def test_requirement_with_conditions(self):
        """测试带条件的需求"""
        req = AchievementRequirement(
            type=RequirementType.LOW_HP_WIN,
            target=1,
            conditions={"hp_threshold": 10},
        )
        assert req.conditions == {"hp_threshold": 10}

    def test_check_progress(self):
        """测试进度检查"""
        req = AchievementRequirement(
            type=RequirementType.WIN_GAMES,
            target=100,
        )

        assert req.check_progress(50) == 50
        assert req.check_progress(100) == 100
        assert req.check_progress(150) == 100  # 不超过目标

    def test_is_completed(self):
        """测试完成检查"""
        req = AchievementRequirement(
            type=RequirementType.WIN_GAMES,
            target=100,
        )

        assert req.is_completed(50) is False
        assert req.is_completed(100) is True
        assert req.is_completed(150) is True

    def test_requirement_serialization(self):
        """测试需求序列化"""
        req = AchievementRequirement(
            type=RequirementType.WIN_STREAK,
            target=10,
            conditions={"mode": "ranked"},
        )

        data = req.to_dict()
        assert data["type"] == "win_streak"
        assert data["target"] == 10
        assert data["conditions"] == {"mode": "ranked"}

        restored = AchievementRequirement.from_dict(data)
        assert restored.type == req.type
        assert restored.target == req.target


# ============================================================================
# AchievementReward 测试
# ============================================================================


class TestAchievementReward:
    """成就奖励测试"""

    def test_reward_creation(self):
        """测试奖励创建"""
        reward = AchievementReward(
            gold=500,
            exp=1000,
        )
        assert reward.gold == 500
        assert reward.exp == 1000
        assert reward.avatar_frame is None
        assert reward.title is None

    def test_reward_with_all_fields(self):
        """测试完整奖励"""
        reward = AchievementReward(
            gold=1000,
            exp=2000,
            avatar_frame="gold_frame",
            title="大师",
            skin="rare_skin",
            items=[{"item_id": "chest", "quantity": 1}],
        )
        assert reward.avatar_frame == "gold_frame"
        assert reward.title == "大师"
        assert reward.skin == "rare_skin"
        assert len(reward.items) == 1

    def test_reward_serialization(self):
        """测试奖励序列化"""
        reward = AchievementReward(
            gold=500,
            exp=1000,
            title="测试称号",
        )

        data = reward.to_dict()
        assert data["gold"] == 500
        assert data["exp"] == 1000
        assert data["title"] == "测试称号"

        restored = AchievementReward.from_dict(data)
        assert restored.gold == reward.gold
        assert restored.title == reward.title


# ============================================================================
# Achievement 测试
# ============================================================================


class TestAchievement:
    """成就测试"""

    @pytest.fixture
    def sample_achievement(self):
        """创建示例成就"""
        return Achievement(
            achievement_id="test_achievement",
            name="测试成就",
            description="这是一个测试成就",
            category=AchievementCategory.BATTLE,
            tier=AchievementTier.GOLD,
            requirement=AchievementRequirement(
                type=RequirementType.WIN_GAMES,
                target=100,
            ),
            rewards=AchievementReward(gold=500),
            icon="test_icon",
        )

    def test_achievement_creation(self, sample_achievement):
        """测试成就创建"""
        assert sample_achievement.achievement_id == "test_achievement"
        assert sample_achievement.name == "测试成就"
        assert sample_achievement.category == AchievementCategory.BATTLE
        assert sample_achievement.tier == AchievementTier.GOLD
        assert sample_achievement.hidden is False
        assert sample_achievement.prerequisite is None

    def test_achievement_with_prerequisite(self):
        """测试有前置的成就"""
        achievement = Achievement(
            achievement_id="advanced",
            name="高级成就",
            description="需要完成基础成就",
            category=AchievementCategory.COLLECTION,
            tier=AchievementTier.DIAMOND,
            requirement=AchievementRequirement(
                type=RequirementType.COLLECT_3STAR_HEROES,
                target=10,
            ),
            rewards=AchievementReward(gold=2000),
            prerequisite="basic",
        )
        assert achievement.prerequisite == "basic"

    def test_achievement_hidden(self):
        """测试隐藏成就"""
        achievement = Achievement(
            achievement_id="secret",
            name="隐藏成就",
            description="秘密成就",
            category=AchievementCategory.SPECIAL,
            tier=AchievementTier.DIAMOND,
            requirement=AchievementRequirement(
                type=RequirementType.WIN_GAMES,
                target=1,
            ),
            rewards=AchievementReward(gold=10000),
            hidden=True,
        )
        assert achievement.hidden is True

    def test_achievement_serialization(self, sample_achievement):
        """测试成就序列化"""
        data = sample_achievement.to_dict()

        assert data["achievement_id"] == "test_achievement"
        assert data["name"] == "测试成就"
        assert data["category"] == "battle"
        assert data["tier"] == 3
        assert data["tier_name"] == "金牌"

        restored = Achievement.from_dict(data)
        assert restored.achievement_id == sample_achievement.achievement_id
        assert restored.name == sample_achievement.name
        assert restored.tier == sample_achievement.tier


# ============================================================================
# PlayerAchievement 测试
# ============================================================================


class TestPlayerAchievement:
    """玩家成就测试"""

    def test_player_achievement_creation(self):
        """测试玩家成就创建"""
        pa = PlayerAchievement(
            player_id="player_001",
            achievement_id="win_100",
        )
        assert pa.player_id == "player_001"
        assert pa.achievement_id == "win_100"
        assert pa.progress == 0
        assert pa.completed is False
        assert pa.completed_at is None
        assert pa.claimed is False

    def test_update_progress(self):
        """测试更新进度"""
        pa = PlayerAchievement(
            player_id="player_001",
            achievement_id="win_100",
        )

        # 更新进度但未完成
        just_completed = pa.update_progress(50, 100)
        assert pa.progress == 50
        assert pa.completed is False
        assert just_completed is False

        # 完成成就
        just_completed = pa.update_progress(100, 100)
        assert pa.progress == 100
        assert pa.completed is True
        assert pa.completed_at is not None
        assert just_completed is True

    def test_claim_reward(self):
        """测试领取奖励"""
        pa = PlayerAchievement(
            player_id="player_001",
            achievement_id="win_100",
            progress=100,
            completed=True,
            completed_at=datetime.now(),
        )

        assert pa.is_claimable is True

        result = pa.claim_reward()
        assert result is True
        assert pa.claimed is True
        assert pa.claimed_at is not None
        assert pa.is_claimable is False

    def test_claim_reward_not_completed(self):
        """测试未完成时领取奖励"""
        pa = PlayerAchievement(
            player_id="player_001",
            achievement_id="win_100",
            progress=50,
        )

        result = pa.claim_reward()
        assert result is False
        assert pa.claimed is False

    def test_claim_reward_already_claimed(self):
        """测试重复领取奖励"""
        pa = PlayerAchievement(
            player_id="player_001",
            achievement_id="win_100",
            progress=100,
            completed=True,
            completed_at=datetime.now(),
            claimed=True,
            claimed_at=datetime.now(),
        )

        result = pa.claim_reward()
        assert result is False

    def test_player_achievement_serialization(self):
        """测试玩家成就序列化"""
        pa = PlayerAchievement(
            player_id="player_001",
            achievement_id="win_100",
            progress=75,
            completed=False,
        )

        data = pa.to_dict()
        assert data["player_id"] == "player_001"
        assert data["progress"] == 75
        assert data["completed"] is False
        assert data["is_claimable"] is False

        restored = PlayerAchievement.from_dict(data)
        assert restored.player_id == pa.player_id
        assert restored.progress == pa.progress


# ============================================================================
# AchievementManager 测试
# ============================================================================


class TestAchievementManager:
    """成就管理器测试"""

    @pytest.fixture
    def manager(self):
        """创建管理器实例"""
        return AchievementManager()

    def test_manager_initialization(self, manager):
        """测试管理器初始化"""
        assert manager is not None
        assert len(manager.achievements) > 0  # 应有默认成就

    def test_default_achievements(self, manager):
        """测试默认成就加载"""
        achievements = manager.get_all_achievements()
        assert len(achievements) >= 15  # 至少15个默认成就

    def test_get_achievement(self, manager):
        """测试获取成就"""
        achievement = manager.get_achievement("win_100")
        assert achievement is not None
        assert achievement.name == "百战勇士"

    def test_get_nonexistent_achievement(self, manager):
        """测试获取不存在的成就"""
        achievement = manager.get_achievement("nonexistent")
        assert achievement is None

    def test_get_achievements_by_category(self, manager):
        """测试按类别获取成就"""
        battle_achievements = manager.get_achievements_by_category(AchievementCategory.BATTLE)
        assert len(battle_achievements) > 0

        for a in battle_achievements:
            assert a.category == AchievementCategory.BATTLE

    def test_get_achievements_by_tier(self, manager):
        """测试按等级获取成就"""
        gold_achievements = manager.get_achievements_by_tier(AchievementTier.GOLD)
        assert len(gold_achievements) > 0

        for a in gold_achievements:
            assert a.tier == AchievementTier.GOLD

    def test_update_progress(self, manager):
        """测试更新成就进度"""
        result = manager.update_progress(
            "player_001",
            "win_100",
            50,
        )

        assert result is not None
        assert result.progress == 50
        assert result.completed is False

    def test_update_progress_complete(self, manager):
        """测试完成成就"""
        # 先完成前置成就
        manager.update_progress("player_001", "streak_5", 5)

        result = manager.update_progress(
            "player_001",
            "streak_5",
            5,
        )

        assert result.completed is True
        assert result.completed_at is not None

    def test_check_prerequisite(self, manager):
        """测试前置成就检查"""
        # 未完成前置成就
        achievement = manager.get_achievement("streak_10")
        assert manager.check_prerequisite("player_001", achievement) is False

        # 完成前置成就
        manager.update_progress("player_001", "streak_5", 5)
        assert manager.check_prerequisite("player_001", achievement) is True

    def test_check_and_update_by_type(self, manager):
        """测试按类型更新成就"""
        updated = manager.check_and_update_by_type(
            "player_001",
            RequirementType.WIN_GAMES,
            100,
        )

        assert len(updated) > 0

        # 检查 win_100 是否完成
        win_100 = manager.get_player_achievement("player_001", "win_100")
        assert win_100.completed is True

    def test_claim_reward(self, manager):
        """测试领取奖励"""
        # 完成成就
        manager.update_progress("player_001", "streak_5", 5)

        reward = manager.claim_reward("player_001", "streak_5")
        assert reward is not None
        assert reward.gold == 300

    def test_claim_reward_not_completed(self, manager):
        """测试未完成时领取奖励"""
        manager.update_progress("player_001", "win_100", 50)

        reward = manager.claim_reward("player_001", "win_100")
        assert reward is None

    def test_get_player_achievements(self, manager):
        """测试获取玩家所有成就"""
        manager.update_progress("player_001", "win_100", 50)

        achievements = manager.get_player_achievements("player_001")
        assert len(achievements) > 0

        # 检查进度信息
        for a in achievements:
            assert "player_progress" in a
            assert "progress_percent" in a

    def test_get_player_achievements_completed_only(self, manager):
        """测试只获取已完成的成就"""
        manager.update_progress("player_001", "win_100", 100)

        all_achievements = manager.get_player_achievements("player_001")
        completed = manager.get_player_achievements("player_001", completed_only=True)

        assert len(completed) < len(all_achievements)
        assert len(completed) >= 1

    def test_get_player_stats(self, manager):
        """测试获取玩家统计"""
        manager.update_progress("player_001", "win_100", 100)

        stats = manager.get_player_stats("player_001")

        assert "total_achievements" in stats
        assert "completed_achievements" in stats
        assert "completion_rate" in stats
        assert "by_category" in stats
        assert "by_tier" in stats
        assert stats["completed_achievements"] >= 1

    def test_get_recently_completed(self, manager):
        """测试获取最近完成的成就"""
        manager.update_progress("player_001", "win_100", 100)

        recent = manager.get_recently_completed("player_001")
        assert len(recent) >= 1
        assert "achievement" in recent[0]
        assert "completed_at" in recent[0]

    def test_load_config(self):
        """测试从配置文件加载"""
        # 创建临时配置文件
        config = {
            "achievements": [
                {
                    "achievement_id": "custom_1",
                    "name": "自定义成就",
                    "description": "测试",
                    "category": "special",
                    "tier": 1,
                    "requirement": {"type": "win_games", "target": 1},
                    "rewards": {"gold": 100},
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config, f)
            config_path = f.name

        try:
            manager = AchievementManager(config_path)
            achievement = manager.get_achievement("custom_1")
            assert achievement is not None
            assert achievement.name == "自定义成就"
        finally:
            Path(config_path).unlink()

    def test_save_config(self, manager):
        """测试保存配置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "achievements.json"
            manager.save_config(str(config_path))

            assert config_path.exists()

            with open(config_path) as f:
                data = json.load(f)

            assert "achievements" in data


# ============================================================================
# 边界条件测试
# ============================================================================


class TestBoundaryConditions:
    """边界条件测试"""

    def test_zero_progress(self):
        """测试零进度"""
        pa = PlayerAchievement(
            player_id="player_001",
            achievement_id="test",
            progress=0,
        )
        assert pa.progress == 0
        assert pa.completed is False

    def test_progress_exceeds_target(self):
        """测试进度超过目标"""
        pa = PlayerAchievement(
            player_id="player_001",
            achievement_id="test",
        )

        just_completed = pa.update_progress(150, 100)
        assert pa.progress == 150
        assert pa.completed is True
        assert just_completed is True

    def test_empty_manager(self):
        """测试空管理器"""
        manager = AchievementManager()
        achievements = manager.get_all_achievements()
        assert len(achievements) > 0  # 有默认成就

    def test_nonexistent_player(self):
        """测试不存在的玩家"""
        manager = AchievementManager()

        stats = manager.get_player_stats("nonexistent_player")
        assert stats["completed_achievements"] == 0
        assert stats["completion_rate"] == 0

    def test_hidden_achievement_visibility(self):
        """测试隐藏成就可见性"""
        manager = AchievementManager()

        # 获取玩家成就（隐藏成就未完成不显示）
        achievements = manager.get_player_achievements("player_001")

        # 检查没有隐藏成就显示
        for a in achievements:
            achievement = manager.get_achievement(a["achievement_id"])
            if achievement and achievement.hidden:
                # 隐藏成就只有在完成时才显示
                assert a["player_progress"]["completed"] is True
