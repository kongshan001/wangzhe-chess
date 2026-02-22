"""
王者之奕 - 每日任务与对局集成测试

测试每日任务与对局的跨模块交互：
- 对局完成触发任务进度
- 任务奖励发放
- 任务刷新机制
- 任务完成验证
"""

import pytest
from datetime import datetime, date
from unittest.mock import MagicMock, patch

from src.server.daily_task import (
    DailyTaskManager,
    DailyTask,
    TaskProgress,
    TaskRequirement,
    TaskReward,
    TaskType,
    TaskDifficulty,
)


class TestDailyTaskIntegration:
    """每日任务集成测试"""

    @pytest.fixture
    def daily_task_manager(self):
        """创建每日任务管理器"""
        manager = DailyTaskManager()
        return manager

    @pytest.fixture
    def sample_tasks(self) -> list[DailyTask]:
        """创建示例任务"""
        return [
            DailyTask(
                task_id="task_play_3",
                template_id="tpl_play",
                name="参与对局",
                description="参与3场对局",
                requirement=TaskRequirement(type=TaskType.PLAY_GAMES, target=3),
                rewards=TaskReward(gold=100, exp=50),
                difficulty=TaskDifficulty.EASY,
            ),
            DailyTask(
                task_id="task_win_1",
                template_id="tpl_win",
                name="取得胜利",
                description="赢得1场对局",
                requirement=TaskRequirement(type=TaskType.WIN_GAMES, target=1),
                rewards=TaskReward(gold=200, exp=100),
                difficulty=TaskDifficulty.NORMAL,
            ),
            DailyTask(
                task_id="task_top_3",
                template_id="tpl_top",
                name="进入前三",
                description="在3场对局中进入前三名",
                requirement=TaskRequirement(type=TaskType.TOP_FINISH, target=3),
                rewards=TaskReward(gold=150, exp=75),
                difficulty=TaskDifficulty.NORMAL,
            ),
            DailyTask(
                task_id="task_first_place",
                template_id="tpl_first",
                name="吃鸡",
                description="获得1次第一名",
                requirement=TaskRequirement(type=TaskType.FIRST_PLACE, target=1),
                rewards=TaskReward(gold=500, exp=200),
                difficulty=TaskDifficulty.HARD,
            ),
            DailyTask(
                task_id="task_collect_3star",
                template_id="tpl_3star",
                name="三星英雄",
                description="合成一个三星英雄",
                requirement=TaskRequirement(type=TaskType.COLLECT_3STAR, target=1),
                rewards=TaskReward(gold=500, exp=200),
                difficulty=TaskDifficulty.HARD,
            ),
        ]

    def test_create_daily_task(self, sample_tasks):
        """测试创建每日任务"""
        task = sample_tasks[0]
        
        assert task.task_id == "task_play_3"
        assert task.requirement.type == TaskType.PLAY_GAMES
        assert task.rewards.gold == 100

    def test_task_progress_update(self, daily_task_manager, sample_tasks):
        """测试任务进度更新"""
        player_id = "player_001"
        task = sample_tasks[0]
        
        # 初始化进度
        progress = TaskProgress(
            player_id=player_id,
            task_id=task.task_id,
            task_date=date.today(),
        )
        
        # 更新进度
        progress.update_progress(1, 3)
        assert progress.progress == 1
        
        progress.update_progress(2, 3)
        assert progress.progress == 2
        
        progress.update_progress(3, 3)
        assert progress.progress == 3
        
        # 检查是否完成
        assert progress.completed is True

    def test_task_completion_check(self, sample_tasks):
        """测试任务完成检查"""
        task = sample_tasks[0]
        progress = TaskProgress(
            player_id="player_001",
            task_id=task.task_id,
            task_date=date.today(),
        )
        
        # 未完成
        progress.update_progress(2, 3)
        assert not progress.completed
        
        # 完成
        progress.update_progress(3, 3)
        assert progress.completed


class TestTaskAndGameIntegration:
    """任务与对局集成测试"""

    @pytest.fixture
    def task_manager_with_tasks(self):
        """创建带有任务的管理器"""
        manager = DailyTaskManager()
        return manager

    def test_task_requirement_description(self):
        """测试任务要求描述"""
        req = TaskRequirement(type=TaskType.PLAY_GAMES, target=3)
        desc = req.get_description()
        assert "3" in desc
        assert "对局" in desc

    def test_task_reward_total_value(self):
        """测试任务奖励总价值"""
        reward = TaskReward(
            gold=100,
            exp=50,
            hero_shards={"hero_001": 5},
        )
        
        value = reward.total_value
        assert value > 100  # 应该包含金币和其他价值


class TestTaskProgressIntegration:
    """任务进度集成测试"""

    def test_progress_claim_reward(self):
        """测试领取奖励"""
        progress = TaskProgress(
            player_id="player_001",
            task_id="task_001",
            task_date=date.today(),
        )
        
        # 未完成时不能领取
        assert not progress.claim_reward()
        
        # 完成后可以领取
        progress.update_progress(3, 3)
        assert progress.completed
        assert progress.claim_reward()
        
        # 已领取不能重复领取
        assert not progress.claim_reward()

    def test_progress_reset(self):
        """测试进度重置"""
        progress = TaskProgress(
            player_id="player_001",
            task_id="task_001",
            task_date=date.today(),
            progress=3,
            completed=True,
            claimed=True,
        )
        
        progress.reset()
        
        assert progress.progress == 0
        assert not progress.completed
        assert not progress.claimed

    def test_progress_serialization(self):
        """测试进度序列化"""
        progress = TaskProgress(
            player_id="player_001",
            task_id="task_001",
            task_date=date.today(),
            progress=2,
        )
        
        data = progress.to_dict()
        assert data["player_id"] == "player_001"
        assert data["progress"] == 2
        
        loaded = TaskProgress.from_dict(data)
        assert loaded.player_id == "player_001"
        assert loaded.progress == 2


class TestTaskDifficultyIntegration:
    """任务难度集成测试"""

    def test_difficulty_properties(self):
        """测试难度属性"""
        assert TaskDifficulty.EASY.display_name == "简单"
        assert TaskDifficulty.NORMAL.display_name == "普通"
        assert TaskDifficulty.HARD.display_name == "困难"

    def test_difficulty_refresh_cost(self):
        """测试难度刷新消耗"""
        assert TaskDifficulty.EASY.refresh_cost == 50
        assert TaskDifficulty.NORMAL.refresh_cost == 100
        assert TaskDifficulty.HARD.refresh_cost == 200


class TestTaskTypeIntegration:
    """任务类型集成测试"""

    def test_task_types_exist(self):
        """测试任务类型存在"""
        assert TaskType.PLAY_GAMES.value == "play_games"
        assert TaskType.WIN_GAMES.value == "win_games"
        assert TaskType.FIRST_PLACE.value == "first_place"
        assert TaskType.DEAL_DAMAGE.value == "deal_damage"
        assert TaskType.EARN_GOLD.value == "earn_gold"
        assert TaskType.COLLECT_2STAR.value == "collect_2star"
        assert TaskType.COLLECT_3STAR.value == "collect_3star"

    def test_task_requirement_with_conditions(self):
        """测试带条件的任务要求"""
        req = TaskRequirement(
            type=TaskType.USE_SYNERGY,
            target=5,
            conditions={"synergy_name": "战士"},
        )
        
        desc = req.get_description()
        assert "战士" in desc


class TestDailyTaskSerialization:
    """每日任务序列化测试"""

    def test_task_serialization(self):
        """测试任务序列化"""
        task = DailyTask(
            task_id="task_001",
            template_id="tpl_001",
            name="测试任务",
            description="测试描述",
            requirement=TaskRequirement(type=TaskType.PLAY_GAMES, target=3),
            rewards=TaskReward(gold=100),
            difficulty=TaskDifficulty.NORMAL,
        )
        
        data = task.to_dict()
        assert data["task_id"] == "task_001"
        assert data["name"] == "测试任务"
        
        loaded = DailyTask.from_dict(data)
        assert loaded.task_id == "task_001"
        assert loaded.name == "测试任务"

    def test_task_reward_serialization(self):
        """测试任务奖励序列化"""
        reward = TaskReward(
            gold=100,
            exp=50,
            hero_shards={"hero_001": 5},
        )
        
        data = reward.to_dict()
        assert data["gold"] == 100
        
        loaded = TaskReward.from_dict(data)
        assert loaded.gold == 100
        assert loaded.hero_shards == {"hero_001": 5}
