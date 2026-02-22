"""
王者之奕 - 每日任务管理器

本模块提供每日任务系统的管理功能：
- DailyTaskManager: 每日任务管理器类
- 每日任务刷新（0点）
- 检查任务进度
- 完成任务并领取奖励
- 消耗金币刷新任务
- 获取今日任务列表
"""

from __future__ import annotations

import json
import logging
import random
import uuid
from datetime import datetime, date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .models import (
    DailyTask,
    TaskDifficulty,
    TaskProgress,
    TaskRequirement,
    TaskReward,
    TaskTemplate,
    TaskType,
)

logger = logging.getLogger(__name__)


class DailyTaskManager:
    """
    每日任务管理器
    
    负责管理所有每日任务相关的操作：
    - 任务配置加载
    - 每日任务刷新
    - 任务进度检查
    - 任务奖励发放
    - 任务刷新（金币）
    
    Attributes:
        templates: 任务模板列表
        player_tasks: 玩家今日任务 (player_id -> [DailyTask])
        player_progress: 玩家任务进度 (player_id + task_id -> TaskProgress)
        config_path: 配置文件路径
        daily_task_count: 每日任务数量
        free_refresh_count: 免费刷新次数
    """
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        daily_task_count: int = 3,
        free_refresh_count: int = 1,
    ):
        """
        初始化每日任务管理器
        
        Args:
            config_path: 任务配置文件路径
            daily_task_count: 每日任务数量（默认3个）
            free_refresh_count: 免费刷新次数（默认1次）
        """
        self.templates: Dict[str, TaskTemplate] = {}
        self.player_tasks: Dict[str, Dict[str, DailyTask]] = {}  # player_id -> {task_id -> DailyTask}
        self.player_progress: Dict[str, TaskProgress] = {}  # f"{player_id}_{task_id}" -> TaskProgress
        self.player_refresh_count: Dict[str, int] = {}  # player_id -> 今日已刷新次数
        self.config_path = config_path
        self.daily_task_count = daily_task_count
        self.free_refresh_count = free_refresh_count
        self._last_refresh_date: Dict[str, date] = {}  # player_id -> last refresh date
        
        # 加载配置
        if config_path:
            self.load_config(config_path)
        else:
            self._init_default_templates()
        
        logger.info(f"DailyTaskManager initialized with {len(self.templates)} templates")
    
    def _init_default_templates(self) -> None:
        """初始化默认任务模板"""
        default_templates = [
            # 简单任务
            TaskTemplate(
                template_id="play_3_games",
                name="日常对战",
                description="参与3次对局",
                requirement=TaskRequirement(type=TaskType.PLAY_GAMES, target=3),
                rewards=TaskReward(gold=100, exp=50),
                difficulty=TaskDifficulty.EASY,
                weight=100,
                icon="task_play",
            ),
            TaskTemplate(
                template_id="play_5_games",
                name="活跃玩家",
                description="参与5次对局",
                requirement=TaskRequirement(type=TaskType.PLAY_GAMES, target=5),
                rewards=TaskReward(gold=150, exp=80),
                difficulty=TaskDifficulty.EASY,
                weight=80,
                icon="task_play",
            ),
            TaskTemplate(
                template_id="win_2_games",
                name="胜利之路",
                description="获胜2次",
                requirement=TaskRequirement(type=TaskType.WIN_GAMES, target=2),
                rewards=TaskReward(gold=200, exp=100),
                difficulty=TaskDifficulty.NORMAL,
                weight=90,
                icon="task_win",
            ),
            TaskTemplate(
                template_id="top4_3_times",
                name="稳定发挥",
                description="获得前4名3次",
                requirement=TaskRequirement(type=TaskType.TOP_FINISH, target=3, conditions={"rank": 4}),
                rewards=TaskReward(gold=150, exp=80),
                difficulty=TaskDifficulty.EASY,
                weight=85,
                icon="task_rank",
            ),
            TaskTemplate(
                template_id="first_place_1",
                name="吃鸡达人",
                description="获得1次第一名",
                requirement=TaskRequirement(type=TaskType.FIRST_PLACE, target=1),
                rewards=TaskReward(gold=300, exp=150, equipment_shards={"random": 1}),
                difficulty=TaskDifficulty.HARD,
                weight=60,
                icon="task_chicken",
            ),
            TaskTemplate(
                template_id="deal_3000_damage",
                name="伤害输出",
                description="累计造成3000点伤害",
                requirement=TaskRequirement(type=TaskType.DEAL_DAMAGE, target=3000),
                rewards=TaskReward(gold=120, exp=60),
                difficulty=TaskDifficulty.EASY,
                weight=95,
                icon="task_damage",
            ),
            TaskTemplate(
                template_id="deal_8000_damage",
                name="火力全开",
                description="累计造成8000点伤害",
                requirement=TaskRequirement(type=TaskType.DEAL_DAMAGE, target=8000),
                rewards=TaskReward(gold=250, exp=120, equipment_shards={"attack": 1}),
                difficulty=TaskDifficulty.NORMAL,
                weight=70,
                icon="task_damage",
            ),
            TaskTemplate(
                template_id="earn_100_gold",
                name="财富积累",
                description="累计获得100金币",
                requirement=TaskRequirement(type=TaskType.EARN_GOLD, target=100),
                rewards=TaskReward(gold=50, exp=30),
                difficulty=TaskDifficulty.EASY,
                weight=100,
                icon="task_gold",
            ),
            TaskTemplate(
                template_id="earn_200_gold",
                name="金币大师",
                description="累计获得200金币",
                requirement=TaskRequirement(type=TaskType.EARN_GOLD, target=200),
                rewards=TaskReward(gold=100, exp=50),
                difficulty=TaskDifficulty.NORMAL,
                weight=80,
                icon="task_gold",
            ),
            TaskTemplate(
                template_id="collect_2star_2",
                name="英雄进阶",
                description="合成2个2星英雄",
                requirement=TaskRequirement(type=TaskType.COLLECT_2STAR, target=2),
                rewards=TaskReward(gold=150, exp=80),
                difficulty=TaskDifficulty.NORMAL,
                weight=85,
                icon="task_upgrade",
            ),
            TaskTemplate(
                template_id="collect_3star_1",
                name="三星传说",
                description="合成1个3星英雄",
                requirement=TaskRequirement(type=TaskType.COLLECT_3STAR, target=1),
                rewards=TaskReward(gold=400, exp=200, hero_shards={"random": 1}),
                difficulty=TaskDifficulty.HARD,
                weight=50,
                icon="task_3star",
            ),
            TaskTemplate(
                template_id="buy_10_heroes",
                name="购物达人",
                description="购买10个英雄",
                requirement=TaskRequirement(type=TaskType.BUY_HEROES, target=10),
                rewards=TaskReward(gold=100, exp=50),
                difficulty=TaskDifficulty.EASY,
                weight=90,
                icon="task_buy",
            ),
            TaskTemplate(
                template_id="kill_50_heroes",
                name="战场杀手",
                description="累计击杀50个英雄",
                requirement=TaskRequirement(type=TaskType.KILL_HEROES, target=50),
                rewards=TaskReward(gold=180, exp=90),
                difficulty=TaskDifficulty.NORMAL,
                weight=75,
                icon="task_kill",
            ),
            TaskTemplate(
                template_id="team_play_2",
                name="团队协作",
                description="组队进行2次对局",
                requirement=TaskRequirement(type=TaskType.TEAM_PLAY, target=2),
                rewards=TaskReward(gold=150, exp=80),
                difficulty=TaskDifficulty.NORMAL,
                weight=70,
                icon="task_team",
            ),
            TaskTemplate(
                template_id="perfect_win_1",
                name="完美胜利",
                description="达成1次完美胜利（零损失）",
                requirement=TaskRequirement(type=TaskType.PERFECT_WIN, target=1),
                rewards=TaskReward(gold=300, exp=150, equipment_shards={"defense": 1}),
                difficulty=TaskDifficulty.HARD,
                weight=40,
                icon="task_perfect",
            ),
        ]
        
        for template in default_templates:
            self.templates[template.template_id] = template
    
    def load_config(self, config_path: str) -> None:
        """
        从配置文件加载任务模板
        
        Args:
            config_path: 配置文件路径
        """
        path = Path(config_path)
        if not path.exists():
            logger.warning(f"Daily task config file not found: {config_path}")
            self._init_default_templates()
            return
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            templates_data = data.get("templates", [])
            for template_data in templates_data:
                template = TaskTemplate.from_dict(template_data)
                self.templates[template.template_id] = template
            
            # 更新配置
            self.daily_task_count = data.get("daily_task_count", self.daily_task_count)
            self.free_refresh_count = data.get("free_refresh_count", self.free_refresh_count)
            
            logger.info(f"Loaded {len(self.templates)} task templates from {config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load daily task config: {e}")
            self._init_default_templates()
    
    def save_config(self, config_path: Optional[str] = None) -> None:
        """
        保存任务配置到文件
        
        Args:
            config_path: 配置文件路径（默认使用初始化时的路径）
        """
        path = Path(config_path or self.config_path)
        if not path:
            logger.warning("No config path specified for saving")
            return
        
        try:
            data = {
                "version": "1.0.0",
                "last_updated": datetime.now().isoformat(),
                "daily_task_count": self.daily_task_count,
                "free_refresh_count": self.free_refresh_count,
                "templates": [t.to_dict() for t in self.templates.values()],
            }
            
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved {len(self.templates)} task templates to {path}")
            
        except Exception as e:
            logger.error(f"Failed to save daily task config: {e}")
    
    def _generate_task_id(self) -> str:
        """生成唯一任务ID"""
        return f"daily_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}"
    
    def _select_random_templates(self, count: int, exclude_ids: List[str] = None) -> List[TaskTemplate]:
        """
        根据权重随机选择任务模板
        
        Args:
            count: 需要选择的数量
            exclude_ids: 排除的模板ID列表
            
        Returns:
            选中的模板列表
        """
        exclude_ids = exclude_ids or []
        
        # 筛选可用模板
        available = [
            t for t in self.templates.values()
            if t.template_id not in exclude_ids
        ]
        
        if not available:
            logger.warning("No available templates for selection")
            return []
        
        # 按权重选择（不放回）
        selected = []
        weights = [t.weight for t in available]
        
        for _ in range(min(count, len(available))):
            # 使用随机权重选择
            total_weight = sum(weights)
            if total_weight <= 0:
                # 权重都为0，随机选择
                idx = random.randint(0, len(available) - 1)
            else:
                r = random.uniform(0, total_weight)
                cumulative = 0
                idx = 0
                for i, w in enumerate(weights):
                    cumulative += w
                    if r <= cumulative:
                        idx = i
                        break
            
            selected.append(available.pop(idx))
            weights.pop(idx)
        
        return selected
    
    def _check_daily_reset(self, player_id: str) -> bool:
        """
        检查是否需要每日重置
        
        Args:
            player_id: 玩家ID
            
        Returns:
            是否需要重置
        """
        last_date = self._last_refresh_date.get(player_id)
        today = date.today()
        
        if last_date is None or last_date < today:
            return True
        
        return False
    
    def _do_daily_reset(self, player_id: str) -> None:
        """
        执行每日重置
        
        Args:
            player_id: 玩家ID
        """
        # 清除旧任务
        if player_id in self.player_tasks:
            old_tasks = self.player_tasks[player_id]
            # 清除对应的进度记录
            for task_id in old_tasks:
                key = f"{player_id}_{task_id}"
                if key in self.player_progress:
                    del self.player_progress[key]
            del self.player_tasks[player_id]
        
        # 重置刷新次数
        self.player_refresh_count[player_id] = 0
        
        # 更新日期
        self._last_refresh_date[player_id] = date.today()
        
        logger.info(f"Daily reset for player {player_id}")
    
    def get_player_tasks(self, player_id: str) -> List[DailyTask]:
        """
        获取玩家今日任务列表
        
        如果是新的一天或首次获取，会自动刷新任务。
        
        Args:
            player_id: 玩家ID
            
        Returns:
            今日任务列表
        """
        # 检查是否需要重置
        if self._check_daily_reset(player_id):
            self._do_daily_reset(player_id)
            self._generate_daily_tasks(player_id)
        
        # 返回任务列表
        tasks = self.player_tasks.get(player_id, {})
        return list(tasks.values())
    
    def _generate_daily_tasks(self, player_id: str) -> List[DailyTask]:
        """
        为玩家生成每日任务
        
        Args:
            player_id: 玩家ID
            
        Returns:
            生成的任务列表
        """
        # 选择模板
        templates = self._select_random_templates(self.daily_task_count)
        
        # 生成任务
        tasks = []
        for template in templates:
            task_id = self._generate_task_id()
            task = template.generate_task(task_id)
            tasks.append(task)
            
            # 存储
            if player_id not in self.player_tasks:
                self.player_tasks[player_id] = {}
            self.player_tasks[player_id][task_id] = task
            
            # 初始化进度
            key = f"{player_id}_{task_id}"
            self.player_progress[key] = TaskProgress(
                player_id=player_id,
                task_id=task_id,
                task_date=date.today(),
            )
        
        logger.info(f"Generated {len(tasks)} daily tasks for player {player_id}")
        return tasks
    
    def get_task(self, player_id: str, task_id: str) -> Optional[DailyTask]:
        """
        获取指定任务
        
        Args:
            player_id: 玩家ID
            task_id: 任务ID
            
        Returns:
            任务对象，不存在返回None
        """
        tasks = self.player_tasks.get(player_id, {})
        return tasks.get(task_id)
    
    def get_task_progress(self, player_id: str, task_id: str) -> Optional[TaskProgress]:
        """
        获取任务进度
        
        Args:
            player_id: 玩家ID
            task_id: 任务ID
            
        Returns:
            任务进度，不存在返回None
        """
        key = f"{player_id}_{task_id}"
        return self.player_progress.get(key)
    
    def get_or_create_progress(self, player_id: str, task_id: str) -> TaskProgress:
        """
        获取或创建任务进度
        
        Args:
            player_id: 玩家ID
            task_id: 任务ID
            
        Returns:
            任务进度
        """
        key = f"{player_id}_{task_id}"
        if key not in self.player_progress:
            self.player_progress[key] = TaskProgress(
                player_id=player_id,
                task_id=task_id,
                task_date=date.today(),
            )
        return self.player_progress[key]
    
    def update_progress(
        self,
        player_id: str,
        task_id: str,
        value: int,
        **kwargs,
    ) -> Optional[TaskProgress]:
        """
        更新任务进度
        
        Args:
            player_id: 玩家ID
            task_id: 任务ID
            value: 新的进度值
            **kwargs: 附加参数
            
        Returns:
            更新后的任务进度，任务不存在返回None
        """
        task = self.get_task(player_id, task_id)
        if not task:
            logger.warning(f"Task not found: {task_id} for player {player_id}")
            return None
        
        progress = self.get_or_create_progress(player_id, task_id)
        
        # 如果已完成，不再更新
        if progress.completed:
            return progress
        
        # 检查条件
        actual_value = task.requirement.check_progress(value, **kwargs)
        
        # 更新进度
        just_completed = progress.update_progress(actual_value, task.requirement.target)
        
        if just_completed:
            logger.info(
                f"Player {player_id} completed daily task: {task.name}"
            )
        
        return progress
    
    def add_progress(
        self,
        player_id: str,
        task_id: str,
        delta: int,
        **kwargs,
    ) -> Optional[TaskProgress]:
        """
        增加任务进度
        
        Args:
            player_id: 玩家ID
            task_id: 任务ID
            delta: 进度增量
            **kwargs: 附加参数
            
        Returns:
            更新后的任务进度，任务不存在返回None
        """
        progress = self.get_task_progress(player_id, task_id)
        if progress is None:
            return self.update_progress(player_id, task_id, delta, **kwargs)
        
        return self.update_progress(
            player_id, task_id, progress.progress + delta, **kwargs
        )
    
    def update_progress_by_type(
        self,
        player_id: str,
        task_type: TaskType,
        value: int,
        **kwargs,
    ) -> List[Tuple[DailyTask, TaskProgress]]:
        """
        根据任务类型更新所有相关任务进度
        
        Args:
            player_id: 玩家ID
            task_type: 任务类型
            value: 进度值（如果是增量，使用add_progress_by_type）
            **kwargs: 附加参数
            
        Returns:
            更新的任务和进度列表
        """
        updated = []
        
        tasks = self.player_tasks.get(player_id, {})
        for task in tasks.values():
            if task.requirement.type == task_type:
                progress = self.update_progress(
                    player_id, task.task_id, value, **kwargs
                )
                if progress:
                    updated.append((task, progress))
        
        return updated
    
    def add_progress_by_type(
        self,
        player_id: str,
        task_type: TaskType,
        delta: int,
        **kwargs,
    ) -> List[Tuple[DailyTask, TaskProgress]]:
        """
        根据任务类型增加所有相关任务进度
        
        Args:
            player_id: 玩家ID
            task_type: 任务类型
            delta: 进度增量
            **kwargs: 附加参数
            
        Returns:
            更新的任务和进度列表
        """
        updated = []
        
        tasks = self.player_tasks.get(player_id, {})
        for task in tasks.values():
            if task.requirement.type == task_type:
                progress = self.add_progress(
                    player_id, task.task_id, delta, **kwargs
                )
                if progress:
                    updated.append((task, progress))
        
        return updated
    
    def claim_reward(
        self,
        player_id: str,
        task_id: str,
    ) -> Optional[TaskReward]:
        """
        领取任务奖励
        
        Args:
            player_id: 玩家ID
            task_id: 任务ID
            
        Returns:
            奖励内容，无法领取返回None
        """
        progress = self.get_task_progress(player_id, task_id)
        if not progress or not progress.is_claimable:
            return None
        
        task = self.get_task(player_id, task_id)
        if not task:
            return None
        
        if progress.claim_reward():
            logger.info(
                f"Player {player_id} claimed reward for daily task: {task.name}"
            )
            return task.rewards
        
        return None
    
    def refresh_task(
        self,
        player_id: str,
        task_id: str,
        player_gold: int,
    ) -> Tuple[Optional[DailyTask], int, str]:
        """
        刷新单个任务（消耗金币）
        
        Args:
            player_id: 玩家ID
            task_id: 要刷新的任务ID
            player_gold: 玩家当前金币数
            
        Returns:
            (新任务, 消耗金币, 错误信息) 元组
            成功时错误信息为空字符串
        """
        # 检查任务是否存在
        old_task = self.get_task(player_id, task_id)
        if not old_task:
            return None, 0, "任务不存在"
        
        # 计算刷新消耗
        refresh_count = self.player_refresh_count.get(player_id, 0)
        free_refresh_remaining = max(0, self.free_refresh_count - refresh_count)
        
        if free_refresh_remaining > 0:
            cost = 0
        else:
            cost = old_task.difficulty.refresh_cost
            # 每次刷新后价格翻倍
            cost = cost * (2 ** max(0, refresh_count - self.free_refresh_count))
        
        # 检查金币是否足够
        if player_gold < cost:
            return None, 0, f"金币不足，需要 {cost} 金币"
        
        # 获取已使用的模板ID
        current_tasks = self.player_tasks.get(player_id, {})
        used_template_ids = [t.template_id for t in current_tasks.values()]
        
        # 选择新模板
        new_templates = self._select_random_templates(1, used_template_ids)
        if not new_templates:
            return None, 0, "没有可用的任务模板"
        
        new_template = new_templates[0]
        
        # 生成新任务
        new_task_id = self._generate_task_id()
        new_task = new_template.generate_task(new_task_id)
        
        # 删除旧任务和进度
        if player_id in self.player_tasks and task_id in self.player_tasks[player_id]:
            del self.player_tasks[player_id][task_id]
        
        old_key = f"{player_id}_{task_id}"
        if old_key in self.player_progress:
            del self.player_progress[old_key]
        
        # 添加新任务
        if player_id not in self.player_tasks:
            self.player_tasks[player_id] = {}
        self.player_tasks[player_id][new_task_id] = new_task
        
        # 初始化新进度
        new_key = f"{player_id}_{new_task_id}"
        self.player_progress[new_key] = TaskProgress(
            player_id=player_id,
            task_id=new_task_id,
            task_date=date.today(),
            refreshed=True,
        )
        
        # 更新刷新次数
        self.player_refresh_count[player_id] = refresh_count + 1
        
        logger.info(
            f"Player {player_id} refreshed task from {old_task.name} to {new_task.name}, cost: {cost}"
        )
        
        return new_task, cost, ""
    
    def get_remaining_free_refresh(self, player_id: str) -> int:
        """
        获取剩余免费刷新次数
        
        Args:
            player_id: 玩家ID
            
        Returns:
            剩余免费刷新次数
        """
        refresh_count = self.player_refresh_count.get(player_id, 0)
        return max(0, self.free_refresh_count - refresh_count)
    
    def get_player_task_summary(self, player_id: str) -> Dict[str, Any]:
        """
        获取玩家任务摘要
        
        Args:
            player_id: 玩家ID
            
        Returns:
            任务摘要数据
        """
        tasks = self.get_player_tasks(player_id)
        
        total = len(tasks)
        completed = 0
        claimed = 0
        claimable = 0
        total_rewards = TaskReward()
        
        for task in tasks:
            progress = self.get_task_progress(player_id, task.task_id)
            if progress:
                if progress.completed:
                    completed += 1
                if progress.claimed:
                    claimed += 1
                if progress.is_claimable:
                    claimable += 1
                    total_rewards.gold += task.rewards.gold
                    total_rewards.exp += task.rewards.exp
        
        return {
            "player_id": player_id,
            "total_tasks": total,
            "completed_tasks": completed,
            "claimed_tasks": claimed,
            "claimable_tasks": claimable,
            "remaining_free_refresh": self.get_remaining_free_refresh(player_id),
            "pending_rewards": total_rewards.to_dict(),
        }
    
    def get_full_task_info(self, player_id: str) -> List[Dict[str, Any]]:
        """
        获取玩家任务的完整信息（包含进度）
        
        Args:
            player_id: 玩家ID
            
        Returns:
            任务完整信息列表
        """
        tasks = self.get_player_tasks(player_id)
        result = []
        
        for task in tasks:
            progress = self.get_task_progress(player_id, task.task_id)
            
            task_data = task.to_dict()
            task_data["progress"] = progress.to_dict() if progress else {
                "progress": 0,
                "completed": False,
                "claimed": False,
            }
            task_data["progress_percent"] = (
                min(100, (progress.progress / task.requirement.target) * 100)
                if progress else 0
            )
            task_data["refresh_cost"] = (
                0 if self.get_remaining_free_refresh(player_id) > 0
                else task.difficulty.refresh_cost
            )
            
            result.append(task_data)
        
        return result


# 全局单例
_daily_task_manager: Optional[DailyTaskManager] = None


def get_daily_task_manager(config_path: Optional[str] = None) -> DailyTaskManager:
    """
    获取每日任务管理器单例
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        每日任务管理器实例
    """
    global _daily_task_manager
    if _daily_task_manager is None:
        _daily_task_manager = DailyTaskManager(config_path)
    return _daily_task_manager
