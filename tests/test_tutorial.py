"""
王者之奕 - 新手引导系统测试

测试新手引导系统的核心功能：
- 引导配置加载
- 引导进度管理
- 引导步骤推进
- 引导奖励发放
"""

import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from src.server.tutorial import (
    TutorialManager,
    TutorialType,
    TutorialStep,
    TutorialStepAction,
    TutorialReward,
    Tutorial,
    PlayerTutorialProgress,
    TutorialHighlight,
)
from src.server.tutorial.models import TutorialType as TT


class TestTutorialModels(unittest.TestCase):
    """测试引导数据模型"""
    
    def test_tutorial_type_enum(self):
        """测试引导类型枚举"""
        self.assertEqual(TutorialType.BASIC_OPERATION.value, "basic_operation")
        self.assertEqual(TutorialType.SYNERGY_CONCEPT.value, "synergy_concept")
        self.assertEqual(TutorialType.ECONOMY_MANAGEMENT.value, "economy_management")
        self.assertEqual(TutorialType.POSITIONING.value, "positioning")
        self.assertEqual(TutorialType.EQUIPMENT_CRAFTING.value, "equipment_crafting")
    
    def test_tutorial_type_display_name(self):
        """测试引导类型显示名称"""
        self.assertEqual(TutorialType.BASIC_OPERATION.get_display_name(), "基础操作")
        self.assertEqual(TutorialType.SYNERGY_CONCEPT.get_display_name(), "羁绊概念")
        self.assertEqual(TutorialType.ECONOMY_MANAGEMENT.get_display_name(), "经济管理")
    
    def test_tutorial_highlight(self):
        """测试高亮区域"""
        highlight = TutorialHighlight(
            target="shop_panel",
            shape="rect",
            animation="pulse",
            tip_text="点击商店",
            tip_position="bottom",
        )
        
        data = highlight.to_dict()
        self.assertEqual(data["target"], "shop_panel")
        self.assertEqual(data["shape"], "rect")
        self.assertEqual(data["animation"], "pulse")
        
        # 测试从字典创建
        restored = TutorialHighlight.from_dict(data)
        self.assertEqual(restored.target, highlight.target)
        self.assertEqual(restored.shape, highlight.shape)
    
    def test_tutorial_step(self):
        """测试引导步骤"""
        step = TutorialStep(
            step_id="step_1",
            order=1,
            title="第一步",
            description="这是第一步",
            action=TutorialStepAction.CLICK,
            action_target="btn_start",
            highlights=[
                TutorialHighlight(target="btn_start", tip_text="点击开始")
            ],
        )
        
        data = step.to_dict()
        self.assertEqual(data["step_id"], "step_1")
        self.assertEqual(data["order"], 1)
        self.assertEqual(data["action"], "click")
        
        # 测试从字典创建
        restored = TutorialStep.from_dict(data)
        self.assertEqual(restored.step_id, step.step_id)
        self.assertEqual(restored.order, step.order)
    
    def test_tutorial_reward(self):
        """测试引导奖励"""
        reward = TutorialReward(
            gold=500,
            exp=300,
            heroes=[{"hero_id": "hero_001", "star": 1, "count": 1}],
            title="新手",
        )
        
        data = reward.to_dict()
        self.assertEqual(data["gold"], 500)
        self.assertEqual(data["exp"], 300)
        self.assertEqual(len(data["heroes"]), 1)
        
        # 测试价值计算
        value = reward.get_total_value()
        self.assertGreater(value, 500)
        
        # 测试空奖励
        empty_reward = TutorialReward()
        self.assertTrue(empty_reward.is_empty())
        
        non_empty = TutorialReward(gold=100)
        self.assertFalse(non_empty.is_empty())
    
    def test_tutorial(self):
        """测试引导配置"""
        tutorial = Tutorial(
            tutorial_id="tutorial_test",
            tutorial_type=TutorialType.BASIC_OPERATION,
            name="测试引导",
            description="这是一个测试引导",
            steps=[
                TutorialStep(step_id="s1", order=1, title="步骤1", description="描述1"),
                TutorialStep(step_id="s2", order=2, title="步骤2", description="描述2"),
            ],
            completion_reward=TutorialReward(gold=100),
            prerequisites=["tutorial_basic"],
        )
        
        self.assertEqual(tutorial.tutorial_id, "tutorial_test")
        self.assertEqual(tutorial.total_steps, 2)
        
        # 测试获取步骤
        step = tutorial.get_step("s1")
        self.assertIsNotNone(step)
        self.assertEqual(step.title, "步骤1")
        
        step_by_order = tutorial.get_step_by_order(2)
        self.assertIsNotNone(step_by_order)
        self.assertEqual(step_by_order.title, "步骤2")
        
        # 测试序列化
        data = tutorial.to_dict()
        restored = Tutorial.from_dict(data)
        self.assertEqual(restored.tutorial_id, tutorial.tutorial_id)
        self.assertEqual(len(restored.steps), 2)
    
    def test_player_tutorial_progress(self):
        """测试玩家引导进度"""
        progress = PlayerTutorialProgress(
            player_id="player_001",
            tutorial_id="tutorial_basic",
        )
        
        # 初始状态
        self.assertEqual(progress.current_step, 0)
        self.assertFalse(progress.completed)
        self.assertFalse(progress.is_claimable)
        
        # 开始引导
        progress.start()
        self.assertEqual(progress.current_step, 1)
        self.assertIsNotNone(progress.started_at)
        
        # 推进步骤
        progress.advance_step("s1")
        self.assertIn("s1", progress.completed_steps)
        self.assertEqual(progress.current_step, 2)
        
        # 完成引导
        progress.complete()
        self.assertTrue(progress.completed)
        self.assertIsNotNone(progress.completed_at)
        # duration_seconds 可能是0如果执行太快
        self.assertGreaterEqual(progress.duration_seconds, 0)
        
        # 领取奖励
        self.assertTrue(progress.is_claimable)
        progress.claim()
        self.assertTrue(progress.claimed)
        self.assertFalse(progress.is_claimable)
        
        # 重置进度
        progress.reset()
        self.assertEqual(progress.current_step, 0)
        self.assertFalse(progress.completed)
        self.assertEqual(progress.attempts, 2)


class TestTutorialManager(unittest.TestCase):
    """测试引导管理器"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建临时配置文件
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "tutorials.json"
        
        config_data = {
            "version": "1.0.0",
            "tutorials": [
                {
                    "tutorial_id": "tutorial_basic",
                    "tutorial_type": "basic_operation",
                    "name": "基础操作",
                    "description": "学习基础操作",
                    "steps": [
                        {
                            "step_id": "basic_1",
                            "order": 1,
                            "title": "欢迎",
                            "description": "欢迎来到游戏",
                            "action": "click",
                            "action_target": "btn_start",
                        },
                        {
                            "step_id": "basic_2",
                            "order": 2,
                            "title": "购买英雄",
                            "description": "购买一个英雄",
                            "action": "buy_hero",
                            "action_target": "shop_panel",
                        },
                    ],
                    "completion_reward": {
                        "gold": 500,
                        "exp": 300,
                    },
                    "prerequisites": [],
                    "required": True,
                    "sort_order": 1,
                    "enabled": True,
                },
                {
                    "tutorial_id": "tutorial_synergy",
                    "tutorial_type": "synergy_concept",
                    "name": "羁绊概念",
                    "description": "学习羁绊",
                    "steps": [
                        {
                            "step_id": "synergy_1",
                            "order": 1,
                            "title": "羁绊介绍",
                            "description": "什么是羁绊",
                            "action": "click",
                            "action_target": "btn_next",
                        },
                    ],
                    "completion_reward": {
                        "gold": 300,
                    },
                    "prerequisites": ["tutorial_basic"],
                    "required": False,
                    "sort_order": 2,
                    "enabled": True,
                },
            ],
        }
        
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
        
        self.manager = TutorialManager(str(self.config_path))
    
    def tearDown(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_load_config(self):
        """测试配置加载"""
        self.assertEqual(len(self.manager.tutorials), 2)
        
        tutorial = self.manager.get_tutorial("tutorial_basic")
        self.assertIsNotNone(tutorial)
        self.assertEqual(tutorial.name, "基础操作")
        self.assertEqual(tutorial.total_steps, 2)
    
    def test_get_tutorials_by_type(self):
        """测试按类型获取引导"""
        tutorials = self.manager.get_tutorials_by_type(TutorialType.BASIC_OPERATION)
        self.assertEqual(len(tutorials), 1)
        self.assertEqual(tutorials[0].tutorial_id, "tutorial_basic")
    
    def test_start_tutorial(self):
        """测试开始引导"""
        # 开始基础引导
        result = self.manager.start_tutorial("player_001", "tutorial_basic")
        
        self.assertIsNotNone(result)
        self.assertIn("tutorial", result)
        self.assertIn("progress", result)
        self.assertIn("current_step", result)
        
        self.assertEqual(result["progress"]["current_step"], 1)
        self.assertIsNotNone(result["progress"]["started_at"])
        
        # 重复开始应该返回当前进度（已经开始但未完成）
        result2 = self.manager.start_tutorial("player_001", "tutorial_basic")
        self.assertIsNotNone(result2)
        self.assertEqual(result2["progress"]["current_step"], 1)
    
    def test_prerequisites(self):
        """测试前置条件"""
        # 未完成基础引导时，羁绊引导应该锁定
        tutorials = self.manager.get_tutorials_for_player("player_001")
        synergy_tutorial = next(
            (t for t in tutorials if t["tutorial_id"] == "tutorial_synergy"),
            None
        )
        self.assertIsNotNone(synergy_tutorial)
        self.assertFalse(synergy_tutorial["unlocked"])
    
    def test_update_progress(self):
        """测试更新进度"""
        # 开始引导
        self.manager.start_tutorial("player_001", "tutorial_basic")
        
        # 完成第一步
        result = self.manager.update_progress(
            "player_001", "tutorial_basic", "basic_1"
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result["progress"]["current_step"], 2)
        self.assertIn("basic_1", result["progress"]["completed_steps"])
        
        # 完成第二步（最后一步）
        result = self.manager.update_progress(
            "player_001", "tutorial_basic", "basic_2"
        )
        
        self.assertIsNotNone(result)
        self.assertTrue(result["just_completed"])
        self.assertTrue(result["progress"]["completed"])
    
    def test_complete_tutorial(self):
        """测试完成引导"""
        # 开始并完成引导
        self.manager.start_tutorial("player_001", "tutorial_basic")
        self.manager.update_progress("player_001", "tutorial_basic", "basic_1")
        self.manager.update_progress("player_001", "tutorial_basic", "basic_2")
        
        # 检查完成状态
        progress = self.manager.get_player_progress("player_001", "tutorial_basic")
        self.assertIsNotNone(progress)
        self.assertTrue(progress.completed)
        
        # 检查羁绊引导解锁
        tutorials = self.manager.get_tutorials_for_player("player_001")
        synergy_tutorial = next(
            (t for t in tutorials if t["tutorial_id"] == "tutorial_synergy"),
            None
        )
        self.assertTrue(synergy_tutorial["unlocked"])
    
    def test_claim_reward(self):
        """测试领取奖励"""
        # 开始并完成引导
        self.manager.start_tutorial("player_001", "tutorial_basic")
        self.manager.update_progress("player_001", "tutorial_basic", "basic_1")
        self.manager.update_progress("player_001", "tutorial_basic", "basic_2")
        
        # 领取奖励
        reward = self.manager.claim_reward("player_001", "tutorial_basic")
        
        self.assertIsNotNone(reward)
        self.assertEqual(reward.gold, 500)
        self.assertEqual(reward.exp, 300)
        
        # 再次领取应该失败
        reward2 = self.manager.claim_reward("player_001", "tutorial_basic")
        self.assertIsNone(reward2)
    
    def test_skip_tutorial(self):
        """测试跳过引导"""
        # 跳过羁绊引导（非必须）
        result = self.manager.skip_tutorial("player_001", "tutorial_synergy")
        
        self.assertIsNotNone(result)
        self.assertTrue(result["progress"]["skipped"])
        
        # 跳过的引导没有奖励
        reward = self.manager.claim_reward("player_001", "tutorial_synergy")
        self.assertIsNone(reward)
        
        # 尝试跳过必须的引导应该失败
        result2 = self.manager.skip_tutorial("player_002", "tutorial_basic")
        self.assertIsNone(result2)  # 必须引导不能跳过
    
    def test_get_player_stats(self):
        """测试玩家统计"""
        # 完成基础引导
        self.manager.start_tutorial("player_001", "tutorial_basic")
        self.manager.update_progress("player_001", "tutorial_basic", "basic_1")
        self.manager.update_progress("player_001", "tutorial_basic", "basic_2")
        
        stats = self.manager.get_player_stats("player_001")
        
        self.assertEqual(stats["total_tutorials"], 2)
        self.assertEqual(stats["completed_tutorials"], 1)
        self.assertEqual(stats["skipped_tutorials"], 0)
        self.assertEqual(stats["completion_rate"], 50.0)
    
    def test_get_unclaimed_rewards(self):
        """测试未领取奖励列表"""
        # 完成基础引导
        self.manager.start_tutorial("player_001", "tutorial_basic")
        self.manager.update_progress("player_001", "tutorial_basic", "basic_1")
        self.manager.update_progress("player_001", "tutorial_basic", "basic_2")
        
        unclaimed = self.manager.get_unclaimed_rewards("player_001")
        
        self.assertEqual(len(unclaimed), 1)
        self.assertEqual(unclaimed[0]["tutorial_id"], "tutorial_basic")
        self.assertEqual(unclaimed[0]["reward"]["gold"], 500)
        
        # 领取后应该为空
        self.manager.claim_reward("player_001", "tutorial_basic")
        unclaimed = self.manager.get_unclaimed_rewards("player_001")
        self.assertEqual(len(unclaimed), 0)
    
    def test_reset_progress(self):
        """测试重置进度"""
        # 开始并完成引导
        self.manager.start_tutorial("player_001", "tutorial_basic")
        self.manager.update_progress("player_001", "tutorial_basic", "basic_1")
        
        # 重置进度
        result = self.manager.reset_progress("player_001", "tutorial_basic")
        self.assertTrue(result)
        
        progress = self.manager.get_player_progress("player_001", "tutorial_basic")
        self.assertEqual(progress.current_step, 0)
        self.assertFalse(progress.completed)
        self.assertEqual(progress.attempts, 2)


class TestTutorialSerialization(unittest.TestCase):
    """测试引导序列化"""
    
    def test_full_tutorial_serialization(self):
        """测试完整引导序列化"""
        tutorial = Tutorial(
            tutorial_id="test_tutorial",
            tutorial_type=TutorialType.BASIC_OPERATION,
            name="测试引导",
            description="测试描述",
            steps=[
                TutorialStep(
                    step_id="s1",
                    order=1,
                    title="步骤1",
                    description="描述1",
                    action=TutorialStepAction.BUY_HERO,
                    action_target="shop_panel",
                    highlights=[
                        TutorialHighlight(
                            target="shop_panel",
                            tip_text="点击这里",
                        )
                    ],
                    reward=TutorialReward(gold=100),
                ),
            ],
            completion_reward=TutorialReward(
                gold=500,
                exp=300,
                heroes=[{"hero_id": "hero_001", "star": 2, "count": 1}],
            ),
            prerequisites=["tutorial_prev"],
            required=False,
            recommended_level=3,
            estimated_time=5,
            intro_text="欢迎",
            complete_text="完成",
        )
        
        # 序列化
        data = tutorial.to_dict()
        
        # 验证
        self.assertEqual(data["tutorial_id"], "test_tutorial")
        self.assertEqual(data["tutorial_type"], "basic_operation")
        self.assertEqual(len(data["steps"]), 1)
        self.assertEqual(data["completion_reward"]["gold"], 500)
        self.assertEqual(len(data["prerequisites"]), 1)
        
        # 反序列化
        restored = Tutorial.from_dict(data)
        
        self.assertEqual(restored.tutorial_id, tutorial.tutorial_id)
        self.assertEqual(restored.tutorial_type, tutorial.tutorial_type)
        self.assertEqual(len(restored.steps), len(tutorial.steps))
        self.assertEqual(restored.completion_reward.gold, tutorial.completion_reward.gold)
    
    def test_progress_serialization(self):
        """测试进度序列化"""
        progress = PlayerTutorialProgress(
            player_id="player_001",
            tutorial_id="tutorial_001",
            current_step=3,
            completed_steps=["s1", "s2"],
            completed=True,
            claimed=True,
        )
        
        data = progress.to_dict()
        restored = PlayerTutorialProgress.from_dict(data)
        
        self.assertEqual(restored.player_id, progress.player_id)
        self.assertEqual(restored.current_step, progress.current_step)
        self.assertEqual(restored.completed_steps, progress.completed_steps)
        self.assertEqual(restored.completed, progress.completed)


if __name__ == "__main__":
    unittest.main()
