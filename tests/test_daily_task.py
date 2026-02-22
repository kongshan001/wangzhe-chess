"""
王者之奕 - 每日任务系统测试

测试每日任务系统的核心功能：
- 任务模板加载
- 每日任务生成
- 任务进度更新
- 任务奖励领取
- 任务刷新功能
"""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import patch, MagicMock

from src.server.daily_task.models import (
    DailyTask,
    TaskProgress,
    TaskRequirement,
    TaskReward,
    TaskTemplate,
    TaskType,
    TaskDifficulty,
)
from src.server.daily_task.manager import DailyTaskManager, get_daily_task_manager


class TestTaskModels:
    """测试任务数据模型"""

    def test_task_type_enum(self):
        """测试任务类型枚举"""
        assert TaskType.PLAY_GAMES.value == "play_games"
        assert TaskType.WIN_GAMES.value == "win_games"
        assert TaskType.DEAL_DAMAGE.value == "deal_damage"
        assert TaskType.FIRST_PLACE.value == "first_place"

    def test_task_difficulty_enum(self):
        """测试任务难度枚举"""
        assert TaskDifficulty.EASY.display_name == "简单"
        assert TaskDifficulty.NORMAL.display_name == "普通"
        assert TaskDifficulty.HARD.display_name == "困难"
        
        assert TaskDifficulty.EASY.refresh_cost == 50
        assert TaskDifficulty.NORMAL.refresh_cost == 100
        assert TaskDifficulty.HARD.refresh_cost == 200

    def test_task_requirement_creation(self):
        """测试任务需求创建"""
        req = TaskRequirement(
            type=TaskType.PLAY_GAMES,
            target=3,
        )
        assert req.type == TaskType.PLAY_GAMES
        assert req.target == 3
        assert req.conditions == {}

    def test_task_requirement_check_progress(self):
        """测试任务进度检查"""
        req = TaskRequirement(
            type=TaskType.PLAY_GAMES,
            target=5,
        )
        
        # 检查进度
        assert req.check_progress(3) == 3
        assert req.check_progress(5) == 5
        assert req.check_progress(10) == 5  # 不超过目标

    def test_task_requirement_is_completed(self):
        """测试任务完成检查"""
        req = TaskRequirement(
            type=TaskType.PLAY_GAMES,
            target=3,
        )
        
        assert not req.is_completed(2)
        assert req.is_completed(3)
        assert req.is_completed(5)

    def test_task_requirement_with_conditions(self):
        """测试带条件的任务需求"""
        req = TaskRequirement(
            type=TaskType.USE_SYNERGY,
            target=3,
            conditions={"synergy_name": "战士"},
        )
        
        # 不满足条件
        assert req.check_progress(3, synergy_name="法师") == 0
        
        # 满足条件
        assert req.check_progress(3, synergy_name="战士") == 3

    def test_task_requirement_description(self):
        """测试任务描述生成"""
        req = TaskRequirement(type=TaskType.PLAY_GAMES, target=5)
        assert "5" in req.get_description()
        assert "对局" in req.get_description()

    def test_task_requirement_serialization(self):
        """测试任务需求序列化"""
        req = TaskRequirement(
            type=TaskType.WIN_GAMES,
            target=3,
            conditions={"rank": 4},
        )
        
        data = req.to_dict()
        assert data["type"] == "win_games"
        assert data["target"] == 3
        assert data["conditions"] == {"rank": 4}
        
        # 反序列化
        req2 = TaskRequirement.from_dict(data)
        assert req2.type == TaskType.WIN_GAMES
        assert req2.target == 3
        assert req2.conditions == {"rank": 4}

    def test_task_reward_creation(self):
        """测试任务奖励创建"""
        reward = TaskReward(
            gold=100,
            exp=50,
            equipment_shards={"attack": 1},
        )
        assert reward.gold == 100
        assert reward.exp == 50
        assert reward.equipment_shards == {"attack": 1}

    def test_task_reward_total_value(self):
        """测试奖励总价值计算"""
        reward = TaskReward(
            gold=100,
            exp=100,
            equipment_shards={"attack": 2},
            hero_shards={"hero1": 1},
        )
        # 100 + 10 + 20 + 20 = 150
        assert reward.total_value == 150

    def test_task_reward_serialization(self):
        """测试任务奖励序列化"""
        reward = TaskReward(
            gold=200,
            exp=100,
            equipment_shards={"defense": 1},
        )
        
        data = reward.to_dict()
        assert data["gold"] == 200
        assert data["exp"] == 100
        
        reward2 = TaskReward.from_dict(data)
        assert reward2.gold == 200
        assert reward2.exp == 100

    def test_daily_task_creation(self):
        """测试每日任务创建"""
        task = DailyTask(
            task_id="test_task_1",
            template_id="play_3_games",
            name="日常对战",
            description="参与3次对局",
            requirement=TaskRequirement(type=TaskType.PLAY_GAMES, target=3),
            rewards=TaskReward(gold=100),
            difficulty=TaskDifficulty.EASY,
        )
        
        assert task.task_id == "test_task_1"
        assert task.name == "日常对战"
        assert task.difficulty == TaskDifficulty.EASY

    def test_task_progress_creation(self):
        """测试任务进度创建"""
        progress = TaskProgress(
            player_id="player1",
            task_id="task1",
            task_date=date.today(),
        )
        
        assert progress.player_id == "player1"
        assert progress.progress == 0
        assert not progress.completed
        assert not progress.claimed

    def test_task_progress_update(self):
        """测试任务进度更新"""
        progress = TaskProgress(
            player_id="player1",
            task_id="task1",
            task_date=date.today(),
        )
        
        # 更新进度
        just_completed = progress.update_progress(3, 5)
        assert progress.progress == 3
        assert not progress.completed
        assert not just_completed
        
        # 完成任务
        just_completed = progress.update_progress(5, 5)
        assert progress.progress == 5
        assert progress.completed
        assert just_completed

    def test_task_progress_add(self):
        """测试任务进度增量更新"""
        progress = TaskProgress(
            player_id="player1",
            task_id="task1",
            task_date=date.today(),
        )
        
        progress.add_progress(2, 5)
        assert progress.progress == 2
        
        progress.add_progress(2, 5)
        assert progress.progress == 4

    def test_task_progress_claim(self):
        """测试任务奖励领取"""
        progress = TaskProgress(
            player_id="player1",
            task_id="task1",
            task_date=date.today(),
        )
        
        # 未完成无法领取
        assert not progress.claim_reward()
        
        # 完成后领取
        progress.update_progress(5, 5)
        assert progress.claim_reward()
        assert progress.claimed
        
        # 已领取无法再次领取
        assert not progress.claim_reward()

    def test_task_progress_is_claimable(self):
        """测试任务是否可领取"""
        progress = TaskProgress(
            player_id="player1",
            task_id="task1",
            task_date=date.today(),
        )
        
        assert not progress.is_claimable
        
        progress.update_progress(5, 5)
        assert progress.is_claimable
        
        progress.claim_reward()
        assert not progress.is_claimable

    def test_task_progress_reset(self):
        """测试任务进度重置"""
        progress = TaskProgress(
            player_id="player1",
            task_id="task1",
            task_date=date.today(),
            progress=5,
            completed=True,
            claimed=True,
        )
        
        progress.reset()
        
        assert progress.progress == 0
        assert not progress.completed
        assert not progress.claimed

    def test_task_template_generate_task(self):
        """测试任务模板生成任务"""
        template = TaskTemplate(
            template_id="play_3_games",
            name="日常对战",
            description="参与3次对局",
            requirement=TaskRequirement(type=TaskType.PLAY_GAMES, target=3),
            rewards=TaskReward(gold=100, exp=50),
            difficulty=TaskDifficulty.EASY,
            weight=100,
        )
        
        task = template.generate_task("task_123", difficulty_multiplier=1.5)
        
        assert task.task_id == "task_123"
        assert task.template_id == "play_3_games"
        assert task.name == "日常对战"
        assert task.requirement.target == 4  # 3 * 1.5 = 4.5 -> 4
        assert task.rewards.gold == 150  # 100 * 1.5


class TestDailyTaskManager:
    """测试每日任务管理器"""

    @pytest.fixture
    def manager(self):
        """创建测试用的管理器"""
        return DailyTaskManager(
            daily_task_count=3,
            free_refresh_count=1,
        )

    def test_manager_initialization(self, manager):
        """测试管理器初始化"""
        assert manager.daily_task_count == 3
        assert manager.free_refresh_count == 1
        assert len(manager.templates) > 0

    def test_default_templates(self, manager):
        """测试默认模板加载"""
        assert "play_3_games" in manager.templates
        assert "win_2_games" in manager.templates
        assert "first_place_1" in manager.templates

    def test_get_player_tasks_new_player(self, manager):
        """测试新玩家获取任务"""
        tasks = manager.get_player_tasks("player1")
        
        assert len(tasks) == 3
        for task in tasks:
            assert task.task_id.startswith("daily_")

    def test_get_player_tasks_same_day(self, manager):
        """测试同一天获取任务（应返回相同任务）"""
        tasks1 = manager.get_player_tasks("player1")
        tasks2 = manager.get_player_tasks("player1")
        
        # 同一天应该返回相同的任务
        assert len(tasks1) == len(tasks2)
        task_ids1 = {t.task_id for t in tasks1}
        task_ids2 = {t.task_id for t in tasks2}
        assert task_ids1 == task_ids2

    def test_get_task(self, manager):
        """测试获取单个任务"""
        tasks = manager.get_player_tasks("player1")
        task_id = tasks[0].task_id
        
        task = manager.get_task("player1", task_id)
        assert task is not None
        assert task.task_id == task_id

    def test_get_task_not_exists(self, manager):
        """测试获取不存在的任务"""
        task = manager.get_task("player1", "nonexistent_task")
        assert task is None

    def test_update_progress(self, manager):
        """测试更新任务进度"""
        tasks = manager.get_player_tasks("player1")
        task = tasks[0]
        
        progress = manager.update_progress(
            "player1", task.task_id, task.requirement.target
        )
        
        assert progress is not None
        assert progress.completed

    def test_update_progress_task_not_found(self, manager):
        """测试更新不存在任务的进度"""
        progress = manager.update_progress("player1", "nonexistent", 10)
        assert progress is None

    def test_update_progress_by_type(self, manager):
        """测试按类型更新任务进度"""
        manager.get_player_tasks("player1")
        
        # 更新所有 PLAY_GAMES 类型的任务
        updated = manager.update_progress_by_type(
            "player1", TaskType.PLAY_GAMES, 10
        )
        
        # 应该更新了相关任务
        for task, progress in updated:
            assert task.requirement.type == TaskType.PLAY_GAMES

    def test_add_progress_by_type(self, manager):
        """测试按类型增加任务进度"""
        manager.get_player_tasks("player1")
        
        # 先增加一些进度
        manager.add_progress_by_type("player1", TaskType.PLAY_GAMES, 3)
        
        # 再增加一些
        updated = manager.add_progress_by_type(
            "player1", TaskType.PLAY_GAMES, 2
        )
        
        # 检查进度累加
        for task, progress in updated:
            if task.requirement.type == TaskType.PLAY_GAMES:
                # 进度应该是5（3+2）
                assert progress.progress >= 5

    def test_claim_reward(self, manager):
        """测试领取任务奖励"""
        tasks = manager.get_player_tasks("player1")
        task = tasks[0]
        
        # 先完成任务
        manager.update_progress(
            "player1", task.task_id, task.requirement.target
        )
        
        # 领取奖励
        reward = manager.claim_reward("player1", task.task_id)
        
        assert reward is not None
        assert reward.gold > 0

    def test_claim_reward_not_completed(self, manager):
        """测试领取未完成任务的奖励"""
        tasks = manager.get_player_tasks("player1")
        task = tasks[0]
        
        # 不完成任务直接领取
        reward = manager.claim_reward("player1", task.task_id)
        
        assert reward is None

    def test_claim_reward_already_claimed(self, manager):
        """测试重复领取奖励"""
        tasks = manager.get_player_tasks("player1")
        task = tasks[0]
        
        # 完成并领取
        manager.update_progress(
            "player1", task.task_id, task.requirement.target
        )
        manager.claim_reward("player1", task.task_id)
        
        # 再次领取
        reward = manager.claim_reward("player1", task.task_id)
        
        assert reward is None

    def test_refresh_task_free(self, manager):
        """测试免费刷新任务"""
        tasks = manager.get_player_tasks("player1")
        old_task = tasks[0]
        
        # 第一次刷新应该免费
        new_task, cost, error = manager.refresh_task(
            "player1", old_task.task_id, player_gold=0
        )
        
        assert new_task is not None
        assert cost == 0
        assert error == ""
        assert manager.get_remaining_free_refresh("player1") == 0

    def test_refresh_task_with_cost(self, manager):
        """测试付费刷新任务"""
        tasks = manager.get_player_tasks("player1")
        old_task = tasks[0]
        
        # 用掉免费刷新
        manager.refresh_task("player1", old_task.task_id, player_gold=0)
        
        # 获取新任务再刷新
        tasks = manager.get_player_tasks("player1")
        old_task = tasks[0]
        
        # 第二次刷新需要花费金币
        new_task, cost, error = manager.refresh_task(
            "player1", old_task.task_id, player_gold=1000
        )
        
        assert new_task is not None
        assert cost > 0
        assert error == ""

    def test_refresh_task_not_enough_gold(self, manager):
        """测试金币不足刷新任务"""
        tasks = manager.get_player_tasks("player1")
        old_task = tasks[0]
        
        # 用掉免费刷新
        manager.refresh_task("player1", old_task.task_id, player_gold=0)
        
        # 获取新任务再刷新
        tasks = manager.get_player_tasks("player1")
        old_task = tasks[0]
        
        # 金币不足
        new_task, cost, error = manager.refresh_task(
            "player1", old_task.task_id, player_gold=0
        )
        
        assert new_task is None
        assert "金币不足" in error

    def test_refresh_task_not_exists(self, manager):
        """测试刷新不存在的任务"""
        new_task, cost, error = manager.refresh_task(
            "player1", "nonexistent", player_gold=1000
        )
        
        assert new_task is None
        assert "不存在" in error

    def test_get_player_task_summary(self, manager):
        """测试获取玩家任务摘要"""
        manager.get_player_tasks("player1")
        
        summary = manager.get_player_task_summary("player1")
        
        assert summary["player_id"] == "player1"
        assert summary["total_tasks"] == 3
        assert summary["completed_tasks"] >= 0
        assert summary["remaining_free_refresh"] == 1

    def test_get_full_task_info(self, manager):
        """测试获取完整任务信息"""
        manager.get_player_tasks("player1")
        
        info = manager.get_full_task_info("player1")
        
        assert len(info) == 3
        for task_info in info:
            assert "task_id" in task_info
            assert "name" in task_info
            assert "progress" in task_info
            assert "progress_percent" in task_info
            assert "refresh_cost" in task_info

    def test_daily_reset(self, manager):
        """测试每日重置"""
        # 第一天获取任务
        tasks_day1 = manager.get_player_tasks("player1")
        
        # 模拟第二天
        tomorrow = date.today() + timedelta(days=1)
        manager._last_refresh_date["player1"] = date.today()
        
        with patch('src.server.daily_task.manager.date') as mock_date:
            mock_date.today.return_value = tomorrow
            mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)
            
            # 获取新一天的任务
            tasks_day2 = manager.get_player_tasks("player1")
            
            # 任务应该不同
            task_ids_day1 = {t.task_id for t in tasks_day1}
            task_ids_day2 = {t.task_id for t in tasks_day2}
            assert task_ids_day1 != task_ids_day2


class TestDailyTaskManagerWithConfig:
    """测试带配置文件的管理器"""

    def test_load_config_file_not_exists(self, tmp_path):
        """测试加载不存在的配置文件"""
        config_path = str(tmp_path / "nonexistent.json")
        manager = DailyTaskManager(config_path=config_path)
        
        # 应该使用默认模板
        assert len(manager.templates) > 0

    def test_load_and_save_config(self, tmp_path):
        """测试加载和保存配置"""
        config_path = str(tmp_path / "daily-tasks.json")
        
        # 创建管理器并保存配置
        manager = DailyTaskManager()
        manager.config_path = config_path
        manager.save_config()
        
        # 从文件加载
        manager2 = DailyTaskManager(config_path=config_path)
        
        assert len(manager2.templates) == len(manager.templates)


class TestGlobalManager:
    """测试全局管理器单例"""

    def test_get_daily_task_manager_singleton(self):
        """测试获取全局管理器单例"""
        # 重置全局单例
        import src.server.daily_task.manager as m
        m._daily_task_manager = None
        
        manager1 = get_daily_task_manager()
        manager2 = get_daily_task_manager()
        
        assert manager1 is manager2


class TestTaskProgressSerialization:
    """测试任务进度序列化"""

    def test_task_progress_to_dict(self):
        """测试任务进度转字典"""
        progress = TaskProgress(
            player_id="player1",
            task_id="task1",
            task_date=date(2026, 2, 22),
            progress=3,
            completed=True,
            claimed=False,
        )
        
        data = progress.to_dict()
        
        assert data["player_id"] == "player1"
        assert data["task_id"] == "task1"
        assert data["task_date"] == "2026-02-22"
        assert data["progress"] == 3
        assert data["completed"] is True
        assert data["claimed"] is False
        assert data["is_claimable"] is True

    def test_task_progress_from_dict(self):
        """测试从字典创建任务进度"""
        data = {
            "player_id": "player1",
            "task_id": "task1",
            "task_date": "2026-02-22",
            "progress": 3,
            "completed": True,
            "claimed": False,
        }
        
        progress = TaskProgress.from_dict(data)
        
        assert progress.player_id == "player1"
        assert progress.task_id == "task1"
        assert progress.task_date == date(2026, 2, 22)
        assert progress.progress == 3
        assert progress.completed is True
        assert progress.claimed is False


class TestDailyTaskSerialization:
    """测试每日任务序列化"""

    def test_daily_task_to_dict(self):
        """测试每日任务转字典"""
        task = DailyTask(
            task_id="test_task_1",
            template_id="play_3_games",
            name="日常对战",
            description="参与3次对局",
            requirement=TaskRequirement(type=TaskType.PLAY_GAMES, target=3),
            rewards=TaskReward(gold=100, exp=50),
            difficulty=TaskDifficulty.EASY,
            icon="task_play",
        )
        
        data = task.to_dict()
        
        assert data["task_id"] == "test_task_1"
        assert data["template_id"] == "play_3_games"
        assert data["name"] == "日常对战"
        assert data["difficulty"] == 1
        assert data["difficulty_name"] == "简单"
        assert data["requirement"]["type"] == "play_games"
        assert data["rewards"]["gold"] == 100

    def test_daily_task_from_dict(self):
        """测试从字典创建每日任务"""
        data = {
            "task_id": "test_task_1",
            "template_id": "play_3_games",
            "name": "日常对战",
            "description": "参与3次对局",
            "requirement": {
                "type": "play_games",
                "target": 3,
                "conditions": {},
            },
            "rewards": {
                "gold": 100,
                "exp": 50,
                "equipment_shards": {},
                "hero_shards": {},
            },
            "difficulty": 1,
            "icon": "task_play",
        }
        
        task = DailyTask.from_dict(data)
        
        assert task.task_id == "test_task_1"
        assert task.name == "日常对战"
        assert task.difficulty == TaskDifficulty.EASY
        assert task.requirement.type == TaskType.PLAY_GAMES
        assert task.requirement.target == 3
        assert task.rewards.gold == 100


class TestEdgeCases:
    """测试边缘情况"""

    @pytest.fixture
    def manager(self):
        """创建测试用的管理器"""
        return DailyTaskManager(daily_task_count=3)

    def test_update_completed_task(self, manager):
        """测试更新已完成的任务"""
        tasks = manager.get_player_tasks("player1")
        task = tasks[0]
        
        # 完成任务
        manager.update_progress(
            "player1", task.task_id, task.requirement.target
        )
        
        # 再次更新进度
        progress = manager.update_progress(
            "player1", task.task_id, task.requirement.target + 10
        )
        
        # 进度不应该变化
        assert progress.progress == task.requirement.target

    def test_get_tasks_for_different_players(self, manager):
        """测试获取不同玩家的任务"""
        tasks1 = manager.get_player_tasks("player1")
        tasks2 = manager.get_player_tasks("player2")
        
        # 不同玩家应该有各自的任务
        task_ids1 = {t.task_id for t in tasks1}
        task_ids2 = {t.task_id for t in tasks2}
        
        # 任务ID应该不同
        assert task_ids1 != task_ids2

    def test_progress_for_wrong_player(self, manager):
        """测试为错误玩家更新进度"""
        tasks = manager.get_player_tasks("player1")
        task = tasks[0]
        
        # 为player2更新player1的任务进度
        progress = manager.update_progress("player2", task.task_id, 10)
        
        # 应该返回None，因为player2没有这个任务
        assert progress is None

    def test_excessive_progress(self, manager):
        """测试超额完成进度"""
        tasks = manager.get_player_tasks("player1")
        task = tasks[0]
        
        # 完成超过目标的进度
        progress = manager.update_progress(
            "player1", task.task_id, task.requirement.target * 100
        )
        
        assert progress.completed

    def test_zero_target_requirement(self):
        """测试目标为0的需求"""
        req = TaskRequirement(type=TaskType.PLAY_GAMES, target=0)
        
        # 任何进度都应该完成
        assert req.is_completed(0)
        assert req.is_completed(1)

    def test_negative_progress(self, manager):
        """测试负进度"""
        tasks = manager.get_player_tasks("player1")
        task = tasks[0]
        
        # 负进度应该被接受（虽然不合理）
        progress = manager.update_progress("player1", task.task_id, -5)
        
        # 进度应该是负数或0
        assert progress.progress == -5
