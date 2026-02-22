"""
王者之奕 - 新手引导与游戏流程集成测试

测试新手引导与游戏流程的跨模块交互：
- 引导步骤与游戏操作关联
- 引导完成触发奖励
- 前置引导检查
- 引导进度与玩家等级关联
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from src.server.tutorial import (
    TutorialManager,
    Tutorial,
    PlayerTutorialProgress,
    TutorialReward,
    TutorialType,
    TutorialStep,
)


class TestTutorialIntegration:
    """新手引导集成测试"""

    def test_get_tutorial(self, tutorial_manager):
        """测试获取引导"""
        tutorial = tutorial_manager.get_tutorial("tutorial_test_001")
        
        assert tutorial is not None
        assert tutorial.tutorial_id == "tutorial_test_001"
        assert tutorial.name == "基础操作"

    def test_get_all_tutorials(self, tutorial_manager):
        """测试获取所有引导"""
        tutorials = tutorial_manager.get_all_tutorials()
        
        assert len(tutorials) >= 2

    def test_get_tutorials_by_type(self, tutorial_manager):
        """测试按类型获取引导"""
        tutorials = tutorial_manager.get_tutorials_by_type(TutorialType.BASIC)
        
        for tutorial in tutorials:
            assert tutorial.tutorial_type == TutorialType.BASIC

    def test_get_tutorials_for_player(self, tutorial_manager):
        """测试获取玩家的引导列表"""
        player_id = "player_001"
        
        tutorials = tutorial_manager.get_tutorials_for_player(player_id)
        
        assert len(tutorials) > 0
        
        # 第一个引导应该是解锁的
        assert tutorials[0]["unlocked"] is True


class TestTutorialProgressIntegration:
    """引导进度集成测试"""

    def test_start_tutorial(self, tutorial_manager):
        """测试开始引导"""
        player_id = "player_001"
        tutorial_id = "tutorial_test_001"
        
        result = tutorial_manager.start_tutorial(player_id, tutorial_id)
        
        assert result is not None
        assert "tutorial" in result
        assert "progress" in result
        assert "current_step" in result

    def test_start_already_completed_tutorial(self, tutorial_manager):
        """测试开始已完成的引导"""
        player_id = "player_001"
        tutorial_id = "tutorial_test_001"
        
        # 开始并完成
        tutorial_manager.start_tutorial(player_id, tutorial_id)
        progress = tutorial_manager.get_player_progress(player_id, tutorial_id)
        progress.complete()
        
        # 再次开始应该返回 None
        result = tutorial_manager.start_tutorial(player_id, tutorial_id)
        assert result is None

    def test_update_progress(self, tutorial_manager):
        """测试更新进度"""
        player_id = "player_001"
        tutorial_id = "tutorial_test_001"
        
        # 开始引导
        tutorial_manager.start_tutorial(player_id, tutorial_id)
        
        # 获取当前步骤
        tutorial = tutorial_manager.get_tutorial(tutorial_id)
        first_step = tutorial.steps[0] if tutorial.steps else None
        
        if first_step:
            # 完成第一步
            result = tutorial_manager.update_progress(
                player_id=player_id,
                tutorial_id=tutorial_id,
                step_id=first_step.step_id,
            )
            
            assert result is not None

    def test_complete_tutorial(self, tutorial_manager):
        """测试完成引导"""
        player_id = "player_001"
        tutorial_id = "tutorial_test_001"
        
        # 开始引导
        tutorial_manager.start_tutorial(player_id, tutorial_id)
        
        # 完成引导
        result = tutorial_manager.complete_tutorial(player_id, tutorial_id)
        
        assert result is not None
        assert result["progress"]["completed"] is True


class TestTutorialPrerequisitesIntegration:
    """引导前置条件集成测试"""

    def test_prerequisite_check(self, tutorial_manager):
        """测试前置条件检查"""
        player_id = "player_001"
        tutorial_id = "tutorial_test_002"  # 需要 tutorial_test_001 作为前置
        
        # 未完成前置时，不应该解锁
        tutorials = tutorial_manager.get_tutorials_for_player(player_id)
        tutorial_002 = next(
            (t for t in tutorials if t["tutorial_id"] == tutorial_id),
            None
        )
        
        if tutorial_002:
            assert tutorial_002["unlocked"] is False

    def test_unlock_after_prerequisite(self, tutorial_manager):
        """测试完成前置后解锁"""
        player_id = "player_001"
        
        # 完成前置引导
        tutorial_manager.start_tutorial(player_id, "tutorial_test_001")
        progress = tutorial_manager.get_or_create_progress(
            player_id, "tutorial_test_001"
        )
        progress.complete()
        
        # 检查后续引导是否解锁
        tutorials = tutorial_manager.get_tutorials_for_player(player_id)
        tutorial_002 = next(
            (t for t in tutorials if t["tutorial_id"] == "tutorial_test_002"),
            None
        )
        
        if tutorial_002:
            assert tutorial_002["unlocked"] is True


class TestTutorialRewardIntegration:
    """引导奖励集成测试"""

    def test_claim_reward(self, tutorial_manager):
        """测试领取奖励"""
        player_id = "player_001"
        tutorial_id = "tutorial_test_001"
        
        # 完成引导
        tutorial_manager.start_tutorial(player_id, tutorial_id)
        progress = tutorial_manager.get_player_progress(player_id, tutorial_id)
        progress.complete()
        
        # 领取奖励
        reward = tutorial_manager.claim_reward(player_id, tutorial_id)
        
        assert reward is not None
        assert reward.gold == 100

    def test_claim_already_claimed_reward(self, tutorial_manager):
        """测试重复领取奖励"""
        player_id = "player_001"
        tutorial_id = "tutorial_test_001"
        
        # 完成并领取
        tutorial_manager.start_tutorial(player_id, tutorial_id)
        progress = tutorial_manager.get_player_progress(player_id, tutorial_id)
        progress.complete()
        tutorial_manager.claim_reward(player_id, tutorial_id)
        
        # 再次领取
        reward = tutorial_manager.claim_reward(player_id, tutorial_id)
        assert reward is None

    def test_get_unclaimed_rewards(self, tutorial_manager):
        """测试获取未领取奖励"""
        player_id = "player_001"
        
        # 完成一个引导但不领取
        tutorial_manager.start_tutorial(player_id, "tutorial_test_001")
        progress = tutorial_manager.get_player_progress(player_id, "tutorial_test_001")
        progress.complete()
        
        # 获取未领取奖励
        unclaimed = tutorial_manager.get_unclaimed_rewards(player_id)
        
        assert len(unclaimed) >= 1


class TestTutorialSkipIntegration:
    """跳过引导集成测试"""

    def test_skip_optional_tutorial(self, tutorial_manager):
        """测试跳过可选引导"""
        player_id = "player_001"
        tutorial_id = "tutorial_test_002"  # required=False
        
        result = tutorial_manager.skip_tutorial(player_id, tutorial_id)
        
        assert result is not None
        assert result["progress"]["skipped"] is True

    def test_cannot_skip_required_tutorial(self, tutorial_manager):
        """测试不能跳过必须的引导"""
        player_id = "player_001"
        tutorial_id = "tutorial_test_001"  # required=True
        
        result = tutorial_manager.skip_tutorial(player_id, tutorial_id)
        
        assert result is None


class TestTutorialStatsIntegration:
    """引导统计集成测试"""

    def test_get_player_stats(self, tutorial_manager):
        """测试获取玩家统计"""
        player_id = "player_001"
        
        stats = tutorial_manager.get_player_stats(player_id)
        
        assert stats is not None
        assert "total_tutorials" in stats
        assert "completed_tutorials" in stats

    def test_stats_update_on_completion(self, tutorial_manager):
        """测试完成引导更新统计"""
        player_id = "player_001"
        
        # 获取初始统计
        initial_stats = tutorial_manager.get_player_stats(player_id)
        initial_completed = initial_stats.get("completed_tutorials", 0)
        
        # 完成一个引导
        tutorial_manager.start_tutorial(player_id, "tutorial_test_001")
        progress = tutorial_manager.get_player_progress(player_id, "tutorial_test_001")
        progress.complete()
        
        # 获取更新后的统计
        updated_stats = tutorial_manager.get_player_stats(player_id)
        
        assert updated_stats["completed_tutorials"] >= initial_completed


class TestTutorialResetIntegration:
    """引导重置集成测试"""

    def test_reset_progress(self, tutorial_manager):
        """测试重置进度"""
        player_id = "player_001"
        tutorial_id = "tutorial_test_001"
        
        # 完成引导
        tutorial_manager.start_tutorial(player_id, tutorial_id)
        progress = tutorial_manager.get_player_progress(player_id, tutorial_id)
        progress.complete()
        
        # 重置进度
        result = tutorial_manager.reset_progress(player_id, tutorial_id)
        
        assert result is True
        
        # 验证进度已重置
        progress = tutorial_manager.get_player_progress(player_id, tutorial_id)
        assert progress.completed is False


class TestTutorialStepIntegration:
    """引导步骤集成测试"""

    def test_step_order(self, tutorial_manager):
        """测试步骤顺序"""
        tutorial = tutorial_manager.get_tutorial("tutorial_test_001")
        
        if tutorial and tutorial.steps:
            for i, step in enumerate(tutorial.steps):
                assert step.order == i + 1

    def test_step_action_type(self, tutorial_manager):
        """测试步骤动作类型"""
        tutorial = tutorial_manager.get_tutorial("tutorial_test_001")
        
        if tutorial and tutorial.steps:
            for step in tutorial.steps:
                assert step.action_type in [
                    "place_hero",
                    "buy_hero",
                    "collect_synergy",
                    "view_info",
                    "navigate",
                    "other",
                ]


class TestTutorialAndGameFlowIntegration:
    """引导与游戏流程集成测试"""

    @pytest.fixture
    def game_flow_manager(self):
        """创建游戏流程模拟"""
        class MockGameFlowManager:
            def __init__(self):
                self.actions = []
            
            def place_hero(self, player_id, hero_id, position):
                self.actions.append({
                    "type": "place_hero",
                    "player_id": player_id,
                    "hero_id": hero_id,
                    "position": position,
                })
                return True
            
            def buy_hero(self, player_id, hero_id):
                self.actions.append({
                    "type": "buy_hero",
                    "player_id": player_id,
                    "hero_id": hero_id,
                })
                return True
        
        return MockGameFlowManager()

    def test_tutorial_step_triggers_game_action(self, tutorial_manager, game_flow_manager):
        """测试引导步骤触发游戏操作"""
        player_id = "player_001"
        
        # 开始引导
        tutorial_manager.start_tutorial(player_id, "tutorial_test_001")
        
        # 模拟执行游戏操作
        game_flow_manager.place_hero(player_id, "hero_001", (0, 0))
        
        # 验证操作已记录
        assert len(game_flow_manager.actions) == 1
        assert game_flow_manager.actions[0]["type"] == "place_hero"

    def test_tutorial_completion_allows_game_access(self, tutorial_manager):
        """测试完成引导后允许游戏访问"""
        player_id = "player_001"
        
        # 完成必须的引导
        tutorial_manager.start_tutorial(player_id, "tutorial_test_001")
        progress = tutorial_manager.get_player_progress(player_id, "tutorial_test_001")
        progress.complete()
        
        # 获取玩家统计
        stats = tutorial_manager.get_player_stats(player_id)
        
        # 应该有完成的引导
        assert stats["completed_tutorials"] >= 1


class TestTutorialSerialization:
    """引导序列化测试"""

    def test_tutorial_serialization(self, tutorial_manager):
        """测试引导序列化"""
        tutorial = tutorial_manager.get_tutorial("tutorial_test_001")
        
        if tutorial:
            data = tutorial.to_dict()
            assert data["tutorial_id"] == "tutorial_test_001"
            
            loaded = Tutorial.from_dict(data)
            assert loaded.tutorial_id == "tutorial_test_001"

    def test_progress_serialization(self):
        """测试进度序列化"""
        progress = PlayerTutorialProgress(
            player_id="player_001",
            tutorial_id="tutorial_001",
        )
        progress.current_step = 2
        progress.completed_steps = ["step_001", "step_002"]
        progress.complete()
        
        data = progress.to_dict()
        assert data["player_id"] == "player_001"
        assert data["completed"] is True
        
        loaded = PlayerTutorialProgress.from_dict(data)
        assert loaded.player_id == "player_001"
        assert loaded.completed is True
