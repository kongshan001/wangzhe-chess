"""
王者之奕 - 每日任务数据模型

本模块定义每日任务系统的核心数据类：
- DailyTask: 每日任务信息
- TaskRequirement: 任务需求条件
- TaskReward: 任务奖励
- TaskProgress: 玩家任务进度
- TaskType: 任务类型枚举
- TaskDifficulty: 任务难度枚举

用于存储和管理每日任务相关的数据。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from typing import Any, Dict, List, Optional


class TaskType(Enum):
    """任务类型枚举"""
    # 对局类
    PLAY_GAMES = "play_games"              # 参与对局 X 次
    WIN_GAMES = "win_games"                # 获胜 X 次
    TOP_FINISH = "top_finish"              # 获得前 X 名
    FIRST_PLACE = "first_place"            # 获得第一名

    # 羁绊类
    USE_SYNERGY = "use_synergy"            # 使用某羁绊英雄
    ACTIVATE_SYNERGY = "activate_synergy"  # 激活某羁绊

    # 战斗类
    DEAL_DAMAGE = "deal_damage"            # 累计造成伤害
    KILL_HEROES = "kill_heroes"            # 累计击杀英雄
    PERFECT_WIN = "perfect_win"            # 完美胜利次数

    # 经济类
    EARN_GOLD = "earn_gold"                # 累计获得金币
    SPEND_GOLD = "spend_gold"              # 累计花费金币
    SAVE_GOLD = "save_gold"                # 单局保留金币

    # 收集类
    COLLECT_2STAR = "collect_2star"        # 合成2星英雄
    COLLECT_3STAR = "collect_3star"        # 合成3星英雄
    BUY_HEROES = "buy_heroes"              # 购买英雄

    # 社交类
    TEAM_PLAY = "team_play"                # 组队游戏


class TaskDifficulty(Enum):
    """任务难度枚举"""
    EASY = 1      # 简单任务
    NORMAL = 2    # 普通任务
    HARD = 3      # 困难任务

    @property
    def display_name(self) -> str:
        """获取显示名称"""
        names = {
            TaskDifficulty.EASY: "简单",
            TaskDifficulty.NORMAL: "普通",
            TaskDifficulty.HARD: "困难",
        }
        return names[self]

    @property
    def refresh_cost(self) -> int:
        """刷新消耗金币"""
        costs = {
            TaskDifficulty.EASY: 50,
            TaskDifficulty.NORMAL: 100,
            TaskDifficulty.HARD: 200,
        }
        return costs[self]


@dataclass
class TaskRequirement:
    """
    任务需求条件
    
    定义完成任务所需满足的条件。
    
    Attributes:
        type: 任务类型
        target: 目标数值
        conditions: 附加条件 (如特定英雄、羁绊等)
    """
    type: TaskType
    target: int
    conditions: Dict[str, Any] = field(default_factory=dict)

    def check_progress(self, current_value: int, **kwargs) -> int:
        """
        检查进度
        
        Args:
            current_value: 当前值
            **kwargs: 附加参数用于条件检查
            
        Returns:
            当前进度（可用于显示进度条）
        """
        # 检查附加条件
        if self.conditions:
            for key, required_value in self.conditions.items():
                actual_value = kwargs.get(key)
                if actual_value != required_value:
                    return 0
        
        return min(current_value, self.target)

    def is_completed(self, current_value: int, **kwargs) -> bool:
        """
        检查是否完成
        
        Args:
            current_value: 当前值
            **kwargs: 附加参数
            
        Returns:
            是否完成
        """
        return self.check_progress(current_value, **kwargs) >= self.target

    def get_description(self) -> str:
        """
        获取任务描述
        
        Returns:
            任务描述字符串
        """
        descriptions = {
            TaskType.PLAY_GAMES: f"参与 {self.target} 次对局",
            TaskType.WIN_GAMES: f"获胜 {self.target} 次",
            TaskType.TOP_FINISH: f"获得前 {self.target} 名",
            TaskType.FIRST_PLACE: f"获得 {self.target} 次第一名",
            TaskType.USE_SYNERGY: f"使用 {self.conditions.get('synergy_name', '某')} 羁绊英雄 {self.target} 次",
            TaskType.ACTIVATE_SYNERGY: f"激活 {self.conditions.get('synergy_name', '某')} 羁绊 {self.target} 次",
            TaskType.DEAL_DAMAGE: f"累计造成 {self.target} 点伤害",
            TaskType.KILL_HEROES: f"累计击杀 {self.target} 个英雄",
            TaskType.PERFECT_WIN: f"达成 {self.target} 次完美胜利",
            TaskType.EARN_GOLD: f"累计获得 {self.target} 金币",
            TaskType.SPEND_GOLD: f"累计花费 {self.target} 金币",
            TaskType.SAVE_GOLD: f"单局保留 {self.target} 金币",
            TaskType.COLLECT_2STAR: f"合成 {self.target} 个2星英雄",
            TaskType.COLLECT_3STAR: f"合成 {self.target} 个3星英雄",
            TaskType.BUY_HEROES: f"购买 {self.target} 个英雄",
            TaskType.TEAM_PLAY: f"组队进行 {self.target} 次对局",
        }
        return descriptions.get(self.type, f"完成任务 ({self.type.value})")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "type": self.type.value,
            "target": self.target,
            "conditions": self.conditions,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskRequirement":
        """从字典创建"""
        req_type = data.get("type", "play_games")
        if isinstance(req_type, str):
            req_type = TaskType(req_type)
        
        return cls(
            type=req_type,
            target=data.get("target", 1),
            conditions=data.get("conditions", {}),
        )


@dataclass
class TaskReward:
    """
    任务奖励
    
    定义完成任务后获得的奖励。
    
    Attributes:
        gold: 金币奖励
        exp: 经验值奖励
        equipment_shards: 装备碎片奖励
        hero_shards: 英雄碎片奖励
    """
    gold: int = 0
    exp: int = 0
    equipment_shards: Dict[str, int] = field(default_factory=dict)
    hero_shards: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "gold": self.gold,
            "exp": self.exp,
            "equipment_shards": self.equipment_shards,
            "hero_shards": self.hero_shards,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskReward":
        """从字典创建"""
        return cls(
            gold=data.get("gold", 0),
            exp=data.get("exp", 0),
            equipment_shards=data.get("equipment_shards", {}),
            hero_shards=data.get("hero_shards", {}),
        )

    @property
    def total_value(self) -> int:
        """获取奖励总价值（金币等价）"""
        value = self.gold
        value += self.exp // 10  # 经验按10:1换算
        value += sum(self.equipment_shards.values()) * 10  # 装备碎片按10金币/个换算
        value += sum(self.hero_shards.values()) * 20  # 英雄碎片按20金币/个换算
        return value


@dataclass
class DailyTask:
    """
    每日任务信息
    
    定义一个每日任务的完整信息。
    
    Attributes:
        task_id: 任务唯一ID
        template_id: 任务模板ID
        name: 任务名称
        description: 任务描述
        requirement: 完成需求
        rewards: 完成奖励
        difficulty: 任务难度
        icon: 图标ID
    """
    task_id: str
    template_id: str
    name: str
    description: str
    requirement: TaskRequirement
    rewards: TaskReward
    difficulty: TaskDifficulty = TaskDifficulty.NORMAL
    icon: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "requirement": self.requirement.to_dict(),
            "rewards": self.rewards.to_dict(),
            "difficulty": self.difficulty.value,
            "difficulty_name": self.difficulty.display_name,
            "icon": self.icon,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DailyTask":
        """从字典创建"""
        difficulty = data.get("difficulty", 2)
        if isinstance(difficulty, int):
            difficulty = TaskDifficulty(difficulty)
        elif isinstance(difficulty, str):
            difficulty_map = {"easy": 1, "normal": 2, "hard": 3}
            difficulty = TaskDifficulty(difficulty_map.get(difficulty, 2))
        
        requirement_data = data.get("requirement", {})
        if isinstance(requirement_data, dict):
            requirement = TaskRequirement.from_dict(requirement_data)
        else:
            requirement = requirement_data
        
        rewards_data = data.get("rewards", {})
        if isinstance(rewards_data, dict):
            rewards = TaskReward.from_dict(rewards_data)
        else:
            rewards = rewards_data
        
        return cls(
            task_id=data["task_id"],
            template_id=data.get("template_id", data["task_id"]),
            name=data["name"],
            description=data.get("description", ""),
            requirement=requirement,
            rewards=rewards,
            difficulty=difficulty,
            icon=data.get("icon", ""),
        )


@dataclass
class TaskProgress:
    """
    玩家任务进度
    
    记录玩家在某个任务上的进度。
    
    Attributes:
        player_id: 玩家ID
        task_id: 任务ID
        task_date: 任务日期
        progress: 当前进度值
        completed: 是否已完成
        completed_at: 完成时间（可选）
        claimed: 是否已领取奖励
        claimed_at: 领取时间（可选）
        refreshed: 是否被刷新过
    """
    player_id: str
    task_id: str
    task_date: date
    progress: int = 0
    completed: bool = False
    completed_at: Optional[datetime] = None
    claimed: bool = False
    claimed_at: Optional[datetime] = None
    refreshed: bool = False

    def update_progress(self, value: int, target: int) -> bool:
        """
        更新进度
        
        Args:
            value: 新的进度值
            target: 目标值
            
        Returns:
            是否刚完成
        """
        self.progress = value
        
        if not self.completed and self.progress >= target:
            self.completed = True
            self.completed_at = datetime.now()
            return True
        
        return False

    def add_progress(self, delta: int, target: int) -> bool:
        """
        增加进度
        
        Args:
            delta: 进度增量
            target: 目标值
            
        Returns:
            是否刚完成
        """
        return self.update_progress(self.progress + delta, target)

    def claim_reward(self) -> bool:
        """
        领取奖励
        
        Returns:
            是否成功领取
        """
        if not self.completed or self.claimed:
            return False
        
        self.claimed = True
        self.claimed_at = datetime.now()
        return True

    def reset(self) -> None:
        """
        重置任务进度（新的一天）
        """
        self.progress = 0
        self.completed = False
        self.completed_at = None
        self.claimed = False
        self.claimed_at = None
        self.refreshed = False

    @property
    def is_claimable(self) -> bool:
        """是否可领取奖励"""
        return self.completed and not self.claimed

    @property
    def is_expired(self) -> bool:
        """是否已过期（非当天）"""
        return self.task_date < date.today()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "player_id": self.player_id,
            "task_id": self.task_id,
            "task_date": self.task_date.isoformat(),
            "progress": self.progress,
            "completed": self.completed,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "claimed": self.claimed,
            "claimed_at": self.claimed_at.isoformat() if self.claimed_at else None,
            "refreshed": self.refreshed,
            "is_claimable": self.is_claimable,
            "is_expired": self.is_expired,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskProgress":
        """从字典创建"""
        task_date = data.get("task_date")
        if task_date:
            if isinstance(task_date, str):
                task_date = date.fromisoformat(task_date)
        else:
            task_date = date.today()
        
        completed_at = data.get("completed_at")
        if completed_at and isinstance(completed_at, str):
            completed_at = datetime.fromisoformat(completed_at)
        
        claimed_at = data.get("claimed_at")
        if claimed_at and isinstance(claimed_at, str):
            claimed_at = datetime.fromisoformat(claimed_at)
        
        return cls(
            player_id=data["player_id"],
            task_id=data["task_id"],
            task_date=task_date,
            progress=data.get("progress", 0),
            completed=data.get("completed", False),
            completed_at=completed_at,
            claimed=data.get("claimed", False),
            claimed_at=claimed_at,
            refreshed=data.get("refreshed", False),
        )


@dataclass
class TaskTemplate:
    """
    任务模板
    
    定义用于生成每日任务的模板。
    
    Attributes:
        template_id: 模板唯一ID
        name: 任务名称
        description: 任务描述模板
        requirement: 任务需求模板
        rewards: 基础奖励（会根据难度调整）
        difficulty: 默认难度
        weight: 出现权重
        icon: 图标ID
    """
    template_id: str
    name: str
    description: str
    requirement: TaskRequirement
    rewards: TaskReward
    difficulty: TaskDifficulty = TaskDifficulty.NORMAL
    weight: int = 100
    icon: str = ""

    def generate_task(self, task_id: str, difficulty_multiplier: float = 1.0) -> DailyTask:
        """
        生成具体任务
        
        Args:
            task_id: 任务ID
            difficulty_multiplier: 难度倍数
            
        Returns:
            DailyTask 实例
        """
        # 调整目标值
        adjusted_target = max(1, int(self.requirement.target * difficulty_multiplier))
        
        # 调整奖励
        adjusted_rewards = TaskReward(
            gold=int(self.rewards.gold * difficulty_multiplier),
            exp=int(self.rewards.exp * difficulty_multiplier),
            equipment_shards={
                k: max(1, int(v * difficulty_multiplier))
                for k, v in self.rewards.equipment_shards.items()
            },
            hero_shards={
                k: max(1, int(v * difficulty_multiplier))
                for k, v in self.rewards.hero_shards.items()
            },
        )
        
        # 创建需求
        adjusted_requirement = TaskRequirement(
            type=self.requirement.type,
            target=adjusted_target,
            conditions=self.requirement.conditions.copy(),
        )
        
        return DailyTask(
            task_id=task_id,
            template_id=self.template_id,
            name=self.name,
            description=adjusted_requirement.get_description(),
            requirement=adjusted_requirement,
            rewards=adjusted_rewards,
            difficulty=self.difficulty,
            icon=self.icon,
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "requirement": self.requirement.to_dict(),
            "rewards": self.rewards.to_dict(),
            "difficulty": self.difficulty.value,
            "weight": self.weight,
            "icon": self.icon,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskTemplate":
        """从字典创建"""
        difficulty = data.get("difficulty", 2)
        if isinstance(difficulty, int):
            difficulty = TaskDifficulty(difficulty)
        elif isinstance(difficulty, str):
            difficulty_map = {"easy": 1, "normal": 2, "hard": 3}
            difficulty = TaskDifficulty(difficulty_map.get(difficulty, 2))
        
        requirement_data = data.get("requirement", {})
        if isinstance(requirement_data, dict):
            requirement = TaskRequirement.from_dict(requirement_data)
        else:
            requirement = requirement_data
        
        rewards_data = data.get("rewards", {})
        if isinstance(rewards_data, dict):
            rewards = TaskReward.from_dict(rewards_data)
        else:
            rewards = rewards_data
        
        return cls(
            template_id=data["template_id"],
            name=data["name"],
            description=data.get("description", ""),
            requirement=requirement,
            rewards=rewards,
            difficulty=difficulty,
            weight=data.get("weight", 100),
            icon=data.get("icon", ""),
        )
