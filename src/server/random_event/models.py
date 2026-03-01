"""
王者之奕 - 随机事件数据模型

本模块定义随机事件系统的核心数据类：
- RandomEvent: 事件信息
- EventEffect: 事件效果
- EventType: 事件类型
- EventTrigger: 触发条件
- EventHistoryEntry: 事件历史记录
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class EventType(str, Enum):
    """
    事件类型枚举

    定义所有可能的随机事件类型。
    """

    # 金币相关
    GOLD_RAIN = "gold_rain"  # 金币雨：所有玩家获得额外金币
    GOLD_BONUS = "gold_bonus"  # 金币奖励：特定玩家获得金币

    # 商店相关
    HERO_DISCOUNT = "hero_discount"  # 英雄折扣：商店某费用英雄打折
    SHOP_REFRESH_FREE = "shop_refresh_free"  # 免费刷新

    # 装备相关
    EQUIPMENT_DROP = "equipment_drop"  # 装备掉落：野怪掉落额外装备
    EQUIPMENT_BONUS = "equipment_bonus"  # 装备奖励：获得随机装备

    # 羁绊相关
    SYNERGY_BLESSING = "synergy_blessing"  # 羁绊祝福：某羁绊效果翻倍

    # 随机奖励
    LUCKY_WHEEL = "lucky_wheel"  # 幸运轮盘：随机获得奖励
    MYSTERY_GIFT = "mystery_gift"  # 神秘礼物：获得随机奖励

    # 特殊事件
    DOUBLE_EXP = "double_exp"  # 双倍经验
    LEVEL_UP_BONUS = "level_up_bonus"  # 免费升级

    @property
    def display_name(self) -> str:
        """获取显示名称"""
        names = {
            EventType.GOLD_RAIN: "金币雨",
            EventType.GOLD_BONUS: "金币奖励",
            EventType.HERO_DISCOUNT: "英雄折扣",
            EventType.SHOP_REFRESH_FREE: "免费刷新",
            EventType.EQUIPMENT_DROP: "装备掉落",
            EventType.EQUIPMENT_BONUS: "装备奖励",
            EventType.SYNERGY_BLESSING: "羁绊祝福",
            EventType.LUCKY_WHEEL: "幸运轮盘",
            EventType.MYSTERY_GIFT: "神秘礼物",
            EventType.DOUBLE_EXP: "双倍经验",
            EventType.LEVEL_UP_BONUS: "免费升级",
        }
        return names.get(self, self.value)


class EventEffectType(str, Enum):
    """
    事件效果类型枚举

    定义事件可能产生的效果类型。
    """

    # 金币效果
    GIVE_GOLD = "give_gold"  # 给予金币
    GIVE_GOLD_ALL = "give_gold_all"  # 所有人给予金币

    # 商店效果
    DISCOUNT_HERO_COST = "discount_hero_cost"  # 按费用打折
    DISCOUNT_HERO_RACE = "discount_hero_race"  # 按种族打折
    FREE_REFRESH = "free_refresh"  # 免费刷新

    # 装备效果
    GIVE_EQUIPMENT = "give_equipment"  # 给予装备
    GIVE_EQUIPMENT_ALL = "give_equipment_all"  # 所有人给予装备
    DROP_RATE_BOOST = "drop_rate_boost"  # 掉落率提升

    # 羁绊效果
    SYNERGY_BOOST = "synergy_boost"  # 羁绊效果加成

    # 经验效果
    GIVE_EXP = "give_exp"  # 给予经验
    GIVE_EXP_ALL = "give_exp_all"  # 所有人给予经验
    FREE_LEVEL_UP = "free_level_up"  # 免费升级

    # 随机效果
    RANDOM_REWARD = "random_reward"  # 随机奖励


class EventRarity(str, Enum):
    """
    事件稀有度枚举
    """

    COMMON = "common"  # 普通
    RARE = "rare"  # 稀有
    EPIC = "epic"  # 史诗
    LEGENDARY = "legendary"  # 传说

    @property
    def display_name(self) -> str:
        """获取显示名称"""
        names = {
            EventRarity.COMMON: "普通",
            EventRarity.RARE: "稀有",
            EventRarity.EPIC: "史诗",
            EventRarity.LEGENDARY: "传说",
        }
        return names[self]

    @property
    def base_probability(self) -> float:
        """获取基础触发概率"""
        probs = {
            EventRarity.COMMON: 0.05,
            EventRarity.RARE: 0.03,
            EventRarity.EPIC: 0.015,
            EventRarity.LEGENDARY: 0.005,
        }
        return probs[self]


@dataclass
class EventEffect:
    """
    事件效果

    定义一个事件产生的具体效果。

    Attributes:
        effect_type: 效果类型
        value: 效果数值（如金币数量、折扣比例等）
        target: 目标对象（如特定费用、种族等）
        duration: 持续回合数（0表示立即生效，-1表示永久）
        conditions: 附加条件
    """

    effect_type: EventEffectType
    value: int = 0
    target: str = ""
    duration: int = 0
    conditions: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "effect_type": self.effect_type.value,
            "value": self.value,
            "target": self.target,
            "duration": self.duration,
            "conditions": self.conditions,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EventEffect:
        """从字典创建"""
        effect_type = data.get("effect_type", "give_gold")
        if isinstance(effect_type, str):
            effect_type = EventEffectType(effect_type)

        return cls(
            effect_type=effect_type,
            value=data.get("value", 0),
            target=data.get("target", ""),
            duration=data.get("duration", 0),
            conditions=data.get("conditions", {}),
        )


@dataclass
class EventTrigger:
    """
    事件触发条件

    定义事件如何被触发。

    Attributes:
        probability: 触发概率（0-1）
        fixed_rounds: 固定触发的回合列表
        min_round: 最早触发回合
        max_round: 最晚触发回合
        conditions: 附加触发条件
    """

    probability: float = 0.05
    fixed_rounds: list[int] = field(default_factory=list)
    min_round: int = 1
    max_round: int = 100
    conditions: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "probability": self.probability,
            "fixed_rounds": self.fixed_rounds,
            "min_round": self.min_round,
            "max_round": self.max_round,
            "conditions": self.conditions,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EventTrigger:
        """从字典创建"""
        return cls(
            probability=data.get("probability", 0.05),
            fixed_rounds=data.get("fixed_rounds", []),
            min_round=data.get("min_round", 1),
            max_round=data.get("max_round", 100),
            conditions=data.get("conditions", {}),
        )


@dataclass
class RandomEvent:
    """
    随机事件

    定义一个完整的随机事件。

    Attributes:
        event_id: 事件唯一ID
        name: 事件名称
        description: 事件描述
        event_type: 事件类型
        rarity: 事件稀有度
        effects: 事件效果列表
        trigger: 触发条件
        icon: 图标ID
        animation: 动画ID
        announcement: 广播文本模板
        enabled: 是否启用
    """

    event_id: str
    name: str
    description: str
    event_type: EventType
    rarity: EventRarity
    effects: list[EventEffect] = field(default_factory=list)
    trigger: EventTrigger = field(default_factory=EventTrigger)
    icon: str = ""
    animation: str = ""
    announcement: str = ""
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "event_id": self.event_id,
            "name": self.name,
            "description": self.description,
            "event_type": self.event_type.value,
            "event_type_name": self.event_type.display_name,
            "rarity": self.rarity.value,
            "rarity_name": self.rarity.display_name,
            "effects": [e.to_dict() for e in self.effects],
            "trigger": self.trigger.to_dict(),
            "icon": self.icon,
            "animation": self.animation,
            "announcement": self.announcement,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RandomEvent:
        """从字典创建"""
        event_type = data.get("event_type", "gold_rain")
        if isinstance(event_type, str):
            event_type = EventType(event_type)

        rarity = data.get("rarity", "common")
        if isinstance(rarity, str):
            rarity = EventRarity(rarity)

        effects_data = data.get("effects", [])
        effects = [EventEffect.from_dict(e) if isinstance(e, dict) else e for e in effects_data]

        trigger_data = data.get("trigger", {})
        if isinstance(trigger_data, dict):
            trigger = EventTrigger.from_dict(trigger_data)
        else:
            trigger = trigger_data

        return cls(
            event_id=data["event_id"],
            name=data["name"],
            description=data.get("description", ""),
            event_type=event_type,
            rarity=rarity,
            effects=effects,
            trigger=trigger,
            icon=data.get("icon", ""),
            animation=data.get("animation", ""),
            announcement=data.get("announcement", ""),
            enabled=data.get("enabled", True),
        )


@dataclass
class EventHistoryEntry:
    """
    事件历史记录

    记录一次事件触发的完整信息。

    Attributes:
        entry_id: 记录ID
        room_id: 房间ID
        event: 触发的事件
        round_number: 触发回合
        trigger_time: 触发时间
        affected_players: 受影响的玩家ID列表
        effect_results: 效果执行结果
    """

    entry_id: str
    room_id: str
    event: RandomEvent
    round_number: int
    trigger_time: datetime
    affected_players: list[int] = field(default_factory=list)
    effect_results: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "entry_id": self.entry_id,
            "room_id": self.room_id,
            "event": self.event.to_dict(),
            "round_number": self.round_number,
            "trigger_time": self.trigger_time.isoformat(),
            "affected_players": self.affected_players,
            "effect_results": self.effect_results,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EventHistoryEntry:
        """从字典创建"""
        event_data = data.get("event", {})
        if isinstance(event_data, dict):
            event = RandomEvent.from_dict(event_data)
        else:
            event = event_data

        trigger_time = data.get("trigger_time")
        if isinstance(trigger_time, str):
            trigger_time = datetime.fromisoformat(trigger_time)

        return cls(
            entry_id=data["entry_id"],
            room_id=data["room_id"],
            event=event,
            round_number=data.get("round_number", 1),
            trigger_time=trigger_time or datetime.now(),
            affected_players=data.get("affected_players", []),
            effect_results=data.get("effect_results", []),
        )
