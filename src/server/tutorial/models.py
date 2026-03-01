"""
王者之奕 - 新手引导数据模型

本模块定义新手引导系统的数据类：
- TutorialType: 引导类型枚举
- TutorialStep: 引导步骤
- TutorialStepAction: 步骤动作
- TutorialReward: 引导奖励
- Tutorial: 引导配置
- PlayerTutorialProgress: 玩家引导进度
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class TutorialType(StrEnum):
    """
    引导类型枚举

    定义不同类型的引导关卡。
    """

    BASIC_OPERATION = "basic_operation"  # 基础操作
    SYNERGY_CONCEPT = "synergy_concept"  # 羁绊概念
    ECONOMY_MANAGEMENT = "economy_management"  # 经济管理
    POSITIONING = "positioning"  # 站位技巧
    EQUIPMENT_CRAFTING = "equipment_crafting"  # 装备合成

    def get_display_name(self) -> str:
        """获取显示名称"""
        names = {
            TutorialType.BASIC_OPERATION: "基础操作",
            TutorialType.SYNERGY_CONCEPT: "羁绊概念",
            TutorialType.ECONOMY_MANAGEMENT: "经济管理",
            TutorialType.POSITIONING: "站位技巧",
            TutorialType.EQUIPMENT_CRAFTING: "装备合成",
        }
        return names.get(self, self.value)


class TutorialStepAction(StrEnum):
    """
    引导步骤动作类型枚举

    定义步骤需要玩家执行的动作类型。
    """

    CLICK = "click"  # 点击指定位置
    DRAG = "drag"  # 拖拽操作
    BUY_HERO = "buy_hero"  # 购买英雄
    SELL_HERO = "sell_hero"  # 出售英雄
    REFRESH_SHOP = "refresh_shop"  # 刷新商店
    PLACE_HERO = "place_hero"  # 放置英雄
    UPGRADE_HERO = "upgrade_hero"  # 升级英雄
    SYNTHESIZE_EQUIPMENT = "synthesize_equipment"  # 合成装备
    VIEW_SYNERGY = "view_synergy"  # 查看羁绊
    VIEW_INFO = "view_info"  # 查看信息面板
    WAIT = "wait"  # 等待
    CONFIRM = "confirm"  # 确认操作


@dataclass
class TutorialHighlight:
    """
    引导高亮区域

    定义需要高亮显示的UI区域。
    """

    # 目标元素ID或选择器
    target: str
    # 高亮形状 (rect, circle, highlight)
    shape: str = "rect"
    # 高亮动画 (pulse, glow, bounce)
    animation: str = "pulse"
    # 提示文本
    tip_text: str | None = None
    # 提示位置 (top, bottom, left, right, center)
    tip_position: str = "bottom"
    # 是否遮挡其他区域
    block_others: bool = True
    # 额外参数
    params: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "target": self.target,
            "shape": self.shape,
            "animation": self.animation,
            "tip_text": self.tip_text,
            "tip_position": self.tip_position,
            "block_others": self.block_others,
            "params": self.params,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TutorialHighlight:
        """从字典创建"""
        return cls(
            target=data.get("target", ""),
            shape=data.get("shape", "rect"),
            animation=data.get("animation", "pulse"),
            tip_text=data.get("tip_text"),
            tip_position=data.get("tip_position", "bottom"),
            block_others=data.get("block_others", True),
            params=data.get("params", {}),
        )


@dataclass
class TutorialStep:
    """
    引导步骤

    定义单个引导步骤的所有信息。
    """

    # 步骤ID
    step_id: str
    # 步骤序号
    order: int
    # 步骤标题
    title: str
    # 步骤描述
    description: str
    # 步骤详细说明
    detail: str | None = None
    # 需要执行的动作
    action: TutorialStepAction = TutorialStepAction.CLICK
    # 动作目标 (元素ID或选择器)
    action_target: str = ""
    # 动作参数 (如购买英雄时指定英雄ID)
    action_params: dict[str, Any] = field(default_factory=dict)
    # 高亮区域列表
    highlights: list[TutorialHighlight] = field(default_factory=list)
    # 步骤超时时间 (秒), 0表示不限时
    timeout: int = 0
    # 跳过该步骤的按钮文本
    skip_text: str | None = None
    # 完成后的提示文本
    complete_text: str | None = None
    # 触发条件 (可选, 用于复杂步骤)
    trigger_condition: dict[str, Any] | None = None
    # 步骤图标
    icon: str | None = None
    # 步骤奖励 (可选)
    reward: TutorialReward | None = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "step_id": self.step_id,
            "order": self.order,
            "title": self.title,
            "description": self.description,
            "detail": self.detail,
            "action": self.action.value
            if isinstance(self.action, TutorialStepAction)
            else self.action,
            "action_target": self.action_target,
            "action_params": self.action_params,
            "highlights": [h.to_dict() for h in self.highlights],
            "timeout": self.timeout,
            "skip_text": self.skip_text,
            "complete_text": self.complete_text,
            "trigger_condition": self.trigger_condition,
            "icon": self.icon,
            "reward": self.reward.to_dict() if self.reward else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TutorialStep:
        """从字典创建"""
        highlights = [TutorialHighlight.from_dict(h) for h in data.get("highlights", [])]

        action_str = data.get("action", "click")
        action = TutorialStepAction(action_str) if isinstance(action_str, str) else action_str

        reward_data = data.get("reward")
        reward = TutorialReward.from_dict(reward_data) if reward_data else None

        return cls(
            step_id=data.get("step_id", ""),
            order=data.get("order", 0),
            title=data.get("title", ""),
            description=data.get("description", ""),
            detail=data.get("detail"),
            action=action,
            action_target=data.get("action_target", ""),
            action_params=data.get("action_params", {}),
            highlights=highlights,
            timeout=data.get("timeout", 0),
            skip_text=data.get("skip_text"),
            complete_text=data.get("complete_text"),
            trigger_condition=data.get("trigger_condition"),
            icon=data.get("icon"),
            reward=reward,
        )


@dataclass
class TutorialReward:
    """
    引导奖励

    定义完成引导后获得的奖励。
    """

    # 金币奖励
    gold: int = 0
    # 经验奖励
    exp: int = 0
    # 英雄奖励列表 [{"hero_id": "xxx", "star": 1, "count": 1}]
    heroes: list[dict[str, Any]] = field(default_factory=list)
    # 装备奖励列表 [{"equipment_id": "xxx", "count": 1}]
    equipments: list[dict[str, Any]] = field(default_factory=list)
    # 道具奖励列表 [{"item_id": "xxx", "count": 1}]
    items: list[dict[str, Any]] = field(default_factory=list)
    # 称号奖励
    title: str | None = None
    # 头像框奖励
    avatar_frame: str | None = None
    # 自定义奖励描述
    custom_description: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "gold": self.gold,
            "exp": self.exp,
            "heroes": self.heroes,
            "equipments": self.equipments,
            "items": self.items,
            "title": self.title,
            "avatar_frame": self.avatar_frame,
            "custom_description": self.custom_description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> TutorialReward | None:
        """从字典创建"""
        if not data:
            return None
        return cls(
            gold=data.get("gold", 0),
            exp=data.get("exp", 0),
            heroes=data.get("heroes", []),
            equipments=data.get("equipments", []),
            items=data.get("items", []),
            title=data.get("title"),
            avatar_frame=data.get("avatar_frame"),
            custom_description=data.get("custom_description"),
        )

    def get_total_value(self) -> int:
        """
        计算奖励总价值

        用于排序和展示。
        金币=1, 经验=0.5, 英雄=费用*100, 装备=200
        """
        value = self.gold
        value += int(self.exp * 0.5)

        for hero in self.heroes:
            # 假设英雄基础价值为费用的100倍
            cost = hero.get("cost", 1)
            star = hero.get("star", 1)
            count = hero.get("count", 1)
            value += cost * 100 * star * count

        for equip in self.equipments:
            count = equip.get("count", 1)
            value += 200 * count

        for item in self.items:
            count = item.get("count", 1)
            value += 100 * count

        return value

    def is_empty(self) -> bool:
        """检查是否有实际奖励"""
        return (
            self.gold == 0
            and self.exp == 0
            and not self.heroes
            and not self.equipments
            and not self.items
            and not self.title
            and not self.avatar_frame
        )


@dataclass
class Tutorial:
    """
    引导配置

    定义完整的引导关卡配置。
    """

    # 引导ID
    tutorial_id: str
    # 引导类型
    tutorial_type: TutorialType
    # 引导名称
    name: str
    # 引导描述
    description: str
    # 引导步骤列表
    steps: list[TutorialStep] = field(default_factory=list)
    # 完成奖励
    completion_reward: TutorialReward = field(default_factory=TutorialReward)
    # 解锁条件 (需要完成的其他引导ID)
    prerequisites: list[str] = field(default_factory=list)
    # 是否必须 (无法跳过)
    required: bool = False
    # 推荐等级 (1-5, 5最高)
    recommended_level: int = 1
    # 预计完成时间 (分钟)
    estimated_time: int = 5
    # 引导图标
    icon: str | None = None
    # 引导背景图
    background_image: str | None = None
    # 开始前的提示文本
    intro_text: str | None = None
    # 完成后的提示文本
    complete_text: str | None = None
    # 排序权重
    sort_order: int = 0
    # 是否启用
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "tutorial_id": self.tutorial_id,
            "tutorial_type": self.tutorial_type.value
            if isinstance(self.tutorial_type, TutorialType)
            else self.tutorial_type,
            "name": self.name,
            "description": self.description,
            "steps": [s.to_dict() for s in self.steps],
            "completion_reward": self.completion_reward.to_dict(),
            "prerequisites": self.prerequisites,
            "required": self.required,
            "recommended_level": self.recommended_level,
            "estimated_time": self.estimated_time,
            "icon": self.icon,
            "background_image": self.background_image,
            "intro_text": self.intro_text,
            "complete_text": self.complete_text,
            "sort_order": self.sort_order,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Tutorial:
        """从字典创建"""
        type_str = data.get("tutorial_type", "basic_operation")
        tutorial_type = TutorialType(type_str) if isinstance(type_str, str) else type_str

        steps = [TutorialStep.from_dict(s) for s in data.get("steps", [])]
        reward_data = data.get("completion_reward", {})
        completion_reward = (
            TutorialReward.from_dict(reward_data) if reward_data else TutorialReward()
        )

        return cls(
            tutorial_id=data.get("tutorial_id", ""),
            tutorial_type=tutorial_type,
            name=data.get("name", ""),
            description=data.get("description", ""),
            steps=steps,
            completion_reward=completion_reward,
            prerequisites=data.get("prerequisites", []),
            required=data.get("required", False),
            recommended_level=data.get("recommended_level", 1),
            estimated_time=data.get("estimated_time", 5),
            icon=data.get("icon"),
            background_image=data.get("background_image"),
            intro_text=data.get("intro_text"),
            complete_text=data.get("complete_text"),
            sort_order=data.get("sort_order", 0),
            enabled=data.get("enabled", True),
        )

    def get_step(self, step_id: str) -> TutorialStep | None:
        """
        获取指定步骤

        Args:
            step_id: 步骤ID

        Returns:
            步骤对象，不存在返回None
        """
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None

    def get_step_by_order(self, order: int) -> TutorialStep | None:
        """
        获取指定序号的步骤

        Args:
            order: 步骤序号

        Returns:
            步骤对象，不存在返回None
        """
        for step in self.steps:
            if step.order == order:
                return step
        return None

    @property
    def total_steps(self) -> int:
        """获取总步骤数"""
        return len(self.steps)


@dataclass
class PlayerTutorialProgress:
    """
    玩家引导进度

    记录玩家在引导中的进度状态。
    """

    # 玩家ID
    player_id: str
    # 引导ID
    tutorial_id: str
    # 当前步骤序号
    current_step: int = 0
    # 当前步骤ID
    current_step_id: str = ""
    # 已完成的步骤ID列表
    completed_steps: list[str] = field(default_factory=list)
    # 是否已完成
    completed: bool = False
    # 完成时间
    completed_at: datetime | None = None
    # 是否已领取奖励
    claimed: bool = False
    # 领取时间
    claimed_at: datetime | None = None
    # 是否已跳过
    skipped: bool = False
    # 跳过时间
    skipped_at: datetime | None = None
    # 引导开始时间
    started_at: datetime | None = None
    # 引导完成耗时 (秒)
    duration_seconds: int = 0
    # 引导尝试次数
    attempts: int = 1

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "player_id": self.player_id,
            "tutorial_id": self.tutorial_id,
            "current_step": self.current_step,
            "current_step_id": self.current_step_id,
            "completed_steps": self.completed_steps,
            "completed": self.completed,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "claimed": self.claimed,
            "claimed_at": self.claimed_at.isoformat() if self.claimed_at else None,
            "skipped": self.skipped,
            "skipped_at": self.skipped_at.isoformat() if self.skipped_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "duration_seconds": self.duration_seconds,
            "attempts": self.attempts,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PlayerTutorialProgress:
        """从字典创建"""

        def parse_datetime(dt_str: str | None) -> datetime | None:
            if dt_str:
                try:
                    return datetime.fromisoformat(dt_str)
                except (ValueError, TypeError):
                    pass
            return None

        return cls(
            player_id=data.get("player_id", ""),
            tutorial_id=data.get("tutorial_id", ""),
            current_step=data.get("current_step", 0),
            current_step_id=data.get("current_step_id", ""),
            completed_steps=data.get("completed_steps", []),
            completed=data.get("completed", False),
            completed_at=parse_datetime(data.get("completed_at")),
            claimed=data.get("claimed", False),
            claimed_at=parse_datetime(data.get("claimed_at")),
            skipped=data.get("skipped", False),
            skipped_at=parse_datetime(data.get("skipped_at")),
            started_at=parse_datetime(data.get("started_at")),
            duration_seconds=data.get("duration_seconds", 0),
            attempts=data.get("attempts", 1),
        )

    @property
    def is_claimable(self) -> bool:
        """是否可领取奖励"""
        return (self.completed or self.skipped) and not self.claimed

    def start(self) -> None:
        """开始引导"""
        if not self.started_at:
            self.started_at = datetime.now()
            self.current_step = 1
            self.completed_steps = []

    def advance_step(self, step_id: str) -> bool:
        """
        推进到下一步

        Args:
            step_id: 完成的步骤ID

        Returns:
            是否成功推进
        """
        if self.completed:
            return False

        # 记录完成的步骤
        if step_id not in self.completed_steps:
            self.completed_steps.append(step_id)

        # 推进步骤
        self.current_step += 1

        return True

    def complete(self) -> None:
        """完成引导"""
        if not self.completed:
            self.completed = True
            self.completed_at = datetime.now()

            # 计算耗时
            if self.started_at:
                duration = datetime.now() - self.started_at
                self.duration_seconds = int(duration.total_seconds())

    def claim(self) -> None:
        """领取奖励"""
        if not self.claimed:
            self.claimed = True
            self.claimed_at = datetime.now()

    def skip(self) -> None:
        """跳过引导"""
        if not self.completed and not self.skipped:
            self.skipped = True
            self.skipped_at = datetime.now()

    def reset(self) -> None:
        """重置进度"""
        self.current_step = 0
        self.current_step_id = ""
        self.completed_steps = []
        self.completed = False
        self.completed_at = None
        self.claimed = False
        self.claimed = None
        self.skipped = False
        self.skipped_at = None
        self.started_at = None
        self.duration_seconds = 0
        self.attempts += 1
