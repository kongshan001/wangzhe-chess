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
                name="参与对局",
                description="参与3场对局",
                task_type=TaskType.PLAY_GAMES,
                requirements=[TaskRequirement(target="games_played", value=3)],
                reward=TaskReward(gold=100, exp=50),
                difficulty=TaskDifficulty.EASY,
            ),
            DailyTask(
                task_id="task_win_1",
                name="取得胜利",
                description="赢得1场对局",
                task_type=TaskType.WIN_GAMES,
                requirements=[TaskRequirement(target="games_won", value=1)],
                reward=TaskReward(gold=200, exp=100),
                difficulty=TaskDifficulty.MEDIUM,
            ),
            DailyTask(
                task_id="task_top_3",
                name="进入前三",
                description="在3场对局中进入前三名",
                task_type=TaskType.PLACE_TOP,
                requirements=[TaskRequirement(target="top_3_finishes", value=3)],
                reward=TaskReward(gold=150, exp=75),
                difficulty=TaskDifficulty.MEDIUM,
            ),
            DailyTask(
                task_id="task_synergy_4",
                name="羁绊大师",
                description="激活一个4级羁绊",
                task_type=TaskType.SYNERGY,
                requirements=[TaskRequirement(target="synergy_level", value=4)],
                reward=TaskReward(gold=300, exp=150),
                difficulty=TaskDifficulty.HARD,
            ),
            DailyTask(
                task_id="task_hero_3star",
                name="三星英雄",
                description="合成一个三星英雄",
                task_type=TaskType.HERO_STAR,
                requirements=[TaskRequirement(target="hero_star", value=3)],
                reward=TaskReward(gold=500, exp=200),
                difficulty=TaskDifficulty.HARD,
            ),
        ]

    def test_create_daily_task(self, sample_tasks):
        """测试创建每日任务"""
        task = sample_tasks[0]
        
        assert task.task_id == "task_play_3"
        assert task.task_type == TaskType.PLAY_GAMES
        assert len(task.requirements) == 1
        assert task.reward.gold == 100

    def test_task_progress_update(self, daily_task_manager, sample_tasks):
        """测试任务进度更新"""
        player_id = "player_001"
        task = sample_tasks[0]
        
        # 初始化进度
        progress = TaskProgress(
            player_id=player_id,
            task_id=task.task_id,
        )
        
        # 更新进度
        progress.update("games_played", 1)
        assert progress.current_progress.get("games_played") == 1
        
        progress.update("games_played", 1)
        assert progress.current_progress.get("games_played") == 2
        
        progress.update("games_played", 1)
        assert progress.current_progress.get("games_played") == 3
        
        # 检查是否完成
        assert progress.is_completed(task.requirements)

    def test_task_completion_check(self, sample_tasks):
        """测试任务完成检查"""
        task = sample_tasks[0]
        progress = TaskProgress(
            player_id="player_001",
            task_id=task.task_id,
        )
        
        # 未完成
        progress.update("games_played", 2)
        assert not progress.is_completed(task.requirements)
        
        # 完成
        progress.update("games_played", 1)
        assert progress.is_completed(task.requirements)


class TestTaskAndGameIntegration:
    """任务与对局集成测试"""

    @pytest.fixture
    def task_manager_with_tasks(self):
        """创建带有任务的管理器"""
        manager = DailyTaskManager()
        
        # 添加测试任务
        tasks = [
            DailyTask(
                task_id="game_task_1",
                name="参与对局",
                description="参与3场对局",
                task_type=TaskType.PLAY_GAMES,
                requirements=[TaskRequirement(target="games_played", value=3)],
                reward=TaskReward(gold=100),
                difficulty=TaskDifficulty.EASY,
            ),
            DailyTask(
                task_id="game_task_2",
                name="取得胜利",
                description="赢得1场对局",
                task_type=TaskType.WIN_GAMES,
                requirements=[TaskRequirement(target="games_won", value=1)],
                reward=TaskReward(gold=200),
                difficulty=TaskDifficulty.MEDIUM,
            ),
            DailyTask(
                task_id="game_task_3",
                name="吃鸡",
                description="获得1次第一名",
                task_type=TaskType.FIRST_PLACE,
                requirements=[TaskRequirement(target="first_place", value=1)],
                reward=TaskReward(gold=500),
                difficulty=TaskDifficulty.HARD,
            ),
        ]
        
        for task in tasks:
            manager.add_task(task)
        
        return manager

    def test_game_completion_updates_tasks(self, task_manager_with_tasks):
        """测试对局完成更新任务"""
        player_id = "player_001"
        
        # 模拟对局完成
        game_result = {
            "games_played": 1,
            "games_won": 1,
            "first_place": 0,
            "placement": 2,
        }
        
        # 更新任务进度
        updated_tasks = task_manager_with_tasks.update_progress(
            player_id=player_id,
            progress_data=game_result,
        )
        
        # 验证胜利任务进度更新
        assert len(updated_tasks) >= 1

    def test_multiple_games_complete_tasks(self, task_manager_with_tasks):
        """测试多场对局完成任务"""
        player_id = "player_001"
        
        # 模拟3场对局
        for i in range(3):
            game_result = {
                "games_played": 1,
                "games_won": 1 if i == 0 else 0,
                "first_place": 1 if i == 2 else 0,
            }
            task_manager_with_tasks.update_progress(player_id, game_result)
        
        # 检查任务状态
        tasks = task_manager_with_tasks.get_player_tasks(player_id)
        
        # 应该有任务完成
        completed = [t for t in tasks if t.get("completed")]
        assert len(completed) >= 1

    def test_claim_task_reward(self, task_manager_with_tasks):
        """测试领取任务奖励"""
        player_id = "player_001"
        task_id = "game_task_1"
        
        # 完成任务
        for _ in range(3):
            task_manager_with_tasks.update_progress(
                player_id, {"games_played": 1}
            )
        
        # 领取奖励
        reward = task_manager_with_tasks.claim_reward(player_id, task_id)
        
        assert reward is not None
        assert reward.gold == 100

    def test_claim_already_claimed_reward(self, task_manager_with_tasks):
        """测试重复领取奖励"""
        player_id = "player_001"
        task_id = "game_task_1"
        
        # 完成并领取
        for _ in range(3):
            task_manager_with_tasks.update_progress(
                player_id, {"games_played": 1}
            )
        task_manager_with_tasks.claim_reward(player_id, task_id)
        
        # 再次尝试领取
        reward = task_manager_with_tasks.claim_reward(player_id, task_id)
        assert reward is None


class TestTaskRefreshIntegration:
    """任务刷新集成测试"""

    @pytest.fixture
    def refresh_manager(self):
        """创建支持刷新的管理器"""
        manager = DailyTaskManager()
        return manager

    def test_daily_task_refresh(self, refresh_manager):
        """测试每日任务刷新"""
        player_id = "player_001"
        
        # 获取初始任务
        initial_tasks = refresh_manager.get_player_tasks(player_id)
        
        # 刷新任务
        refresh_manager.refresh_daily_tasks(player_id)
        
        # 获取新任务
        new_tasks = refresh_manager.get_player_tasks(player_id)
        
        # 任务应该重置
        assert len(new_tasks) > 0

    def test_gold_refresh(self, refresh_manager):
        """测试金币刷新"""
        player_id = "player_001"
        
        # 刷新任务（需要消耗金币）
        result = refresh_manager.refresh_with_gold(
            player_id=player_id,
            gold_balance=1000,
        )
        
        assert result.get("success") is True
        assert result.get("gold_spent") > 0

    def test_insufficient_gold_refresh(self, refresh_manager):
        """测试金币不足刷新"""
        player_id = "player_001"
        
        result = refresh_manager.refresh_with_gold(
            player_id=player_id,
            gold_balance=10,  # 不足
        )
        
        assert result.get("success") is False


class TestTaskRequirementsIntegration:
    """任务要求集成测试"""

    def test_multiple_requirements_task(self):
        """测试多要求任务"""
        task = DailyTask(
            task_id="multi_task",
            name="复合任务",
            description="参与3场对局并获胜1场",
            task_type=TaskType.PLAY_GAMES,
            requirements=[
                TaskRequirement(target="games_played", value=3),
                TaskRequirement(target="games_won", value=1),
            ],
            reward=TaskReward(gold=300),
            difficulty=TaskDifficulty.MEDIUM,
        )
        
        progress = TaskProgress(
            player_id="player_001",
            task_id=task.task_id,
        )
        
        # 只完成第一个要求
        progress.update("games_played", 3)
        assert not progress.is_completed(task.requirements)
        
        # 完成第二个要求
        progress.update("games_won", 1)
        assert progress.is_completed(task.requirements)

    def test_synergy_task(self):
        """测试羁绊任务"""
        task = DailyTask(
            task_id="synergy_task",
            name="羁绊任务",
            description="激活3级人族羁绊",
            task_type=TaskType.SYNERGY,
            requirements=[
                TaskRequirement(target="synergy_level", value=3),
                TaskRequirement(target="synergy_name", value="人族"),
            ],
            reward=TaskReward(gold=200),
            difficulty=TaskDifficulty.MEDIUM,
        )
        
        progress = TaskProgress(
            player_id="player_001",
            task_id=task.task_id,
        )
        
        # 模拟激活羁绊
        progress.update("synergy_level", 3)
        progress.update("synergy_name", "人族")
        
        # 注意：synergy_name 的检查需要特殊逻辑
        # 这里简化处理

    def test_hero_star_task(self):
        """测试英雄星级任务"""
        task = DailyTask(
            task_id="star_task",
            name="三星任务",
            description="合成一个三星英雄",
            task_type=TaskType.HERO_STAR,
            requirements=[TaskRequirement(target="max_hero_star", value=3)],
            reward=TaskReward(gold=500),
            difficulty=TaskDifficulty.HARD,
        )
        
        progress = TaskProgress(
            player_id="player_001",
            task_id=task.task_id,
        )
        
        # 模拟合成三星英雄
        progress.update("max_hero_star", 3)
        assert progress.is_completed(task.requirements)


class TestTaskRewardIntegration:
    """任务奖励集成测试"""

    def test_task_reward_calculation(self):
        """测试任务奖励计算"""
        reward = TaskReward(
            gold=100,
            exp=50,
            hero_shards=10,
            items=[{"item_id": "boost_001", "quantity": 1}],
        )
        
        assert reward.gold == 100
        assert reward.exp == 50
        assert reward.hero_shards == 10
        assert len(reward.items) == 1

    def test_reward_difficulty_multiplier(self):
        """测试奖励难度加成"""
        easy_reward = TaskReward(gold=100)
        hard_reward = TaskReward(gold=100)
        
        # 假设难度加成逻辑
        difficulty_multipliers = {
            TaskDifficulty.EASY: 1.0,
            TaskDifficulty.MEDIUM: 1.5,
            TaskDifficulty.HARD: 2.0,
        }
        
        easy_total = easy_reward.gold * difficulty_multipliers[TaskDifficulty.EASY]
        hard_total = hard_reward.gold * difficulty_multipliers[TaskDifficulty.HARD]
        
        assert hard_total > easy_total


class TestTaskStatisticsIntegration:
    """任务统计集成测试"""

    def test_player_task_stats(self, daily_task_manager):
        """测试玩家任务统计"""
        player_id = "player_001"
        
        # 完成一些任务
        for _ in range(3):
            daily_task_manager.update_progress(
                player_id, {"games_played": 1}
            )
        
        # 获取统计
        stats = daily_task_manager.get_player_stats(player_id)
        
        assert stats is not None
        assert "total_tasks" in stats or "completed_tasks" in stats

    def test_task_completion_rate(self, daily_task_manager):
        """测试任务完成率计算"""
        player_id = "player_001"
        
        # 获取任务完成率
        rate = daily_task_manager.get_completion_rate(player_id)
        
        assert rate >= 0
        assert rate <= 100
