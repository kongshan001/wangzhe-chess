"""
王者之奕 - 道具数据模型

本模块定义道具系统相关的数据模型：
- ConsumableType: 道具类型枚举
- ConsumableEffect: 道具效果枚举
- ConsumableItem: 道具配置
- PlayerConsumable: 玩家拥有的道具
- ConsumableUsage: 道具使用记录
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class ConsumableType(StrEnum):
    """道具类型枚举"""

    RANK_PROTECT = "rank_protect"  # 段位保护卡
    GOLD_DOUBLE = "gold_double"  # 双倍金币卡
    EXP_BOOST = "exp_boost"  # 经验加成卡
    SHOP_DISCOUNT = "shop_discount"  # 刷新折扣卡

    @classmethod
    def get_display_name(cls, ctype: str) -> str:
        """获取道具类型显示名称"""
        display_names = {
            cls.RANK_PROTECT.value: "段位保护卡",
            cls.GOLD_DOUBLE.value: "双倍金币卡",
            cls.EXP_BOOST.value: "经验加成卡",
            cls.SHOP_DISCOUNT.value: "刷新折扣卡",
        }
        return display_names.get(ctype, "未知道具")

    @classmethod
    def get_description(cls, ctype: str) -> str:
        """获取道具描述"""
        descriptions = {
            cls.RANK_PROTECT.value: "输掉对局不扣星，自动消耗",
            cls.GOLD_DOUBLE.value: "对局金币收益翻倍",
            cls.EXP_BOOST.value: "经验获取+50%",
            cls.SHOP_DISCOUNT.value: "商店刷新费用-1金币",
        }
        return descriptions.get(ctype, "未知效果")


class ConsumableEffect(StrEnum):
    """道具效果类型枚举"""

    RANK_PROTECT = "rank_protect"  # 段位保护：输掉对局不扣星
    GOLD_MULTIPLIER = "gold_multiplier"  # 金币翻倍
    EXP_MULTIPLIER = "exp_multiplier"  # 经验加成
    SHOP_REFRESH_DISCOUNT = "shop_refresh_discount"  # 刷新折扣

    @classmethod
    def get_effect_value(cls, effect: str) -> float:
        """获取效果数值"""
        effect_values = {
            cls.RANK_PROTECT.value: 1.0,  # 1次保护
            cls.GOLD_MULTIPLIER.value: 2.0,  # 2倍金币
            cls.EXP_MULTIPLIER.value: 1.5,  # 1.5倍经验
            cls.SHOP_REFRESH_DISCOUNT.value: 1.0,  # -1金币
        }
        return effect_values.get(effect, 1.0)


class ConsumableRarity(StrEnum):
    """道具稀有度枚举"""

    COMMON = "common"  # 普通
    RARE = "rare"  # 稀有
    EPIC = "epic"  # 史诗

    @classmethod
    def get_color(cls, rarity: str) -> str:
        """获取稀有度颜色"""
        colors = {
            cls.COMMON.value: "#FFFFFF",  # 白色
            cls.RARE.value: "#1EFF00",  # 绿色
            cls.EPIC.value: "#A335EE",  # 紫色
        }
        return colors.get(rarity, "#FFFFFF")


@dataclass
class ConsumablePrice:
    """
    道具价格

    定义道具的购买价格。

    Attributes:
        gold: 金币价格
        diamond: 钻石价格
    """

    gold: int | None = None
    diamond: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "gold": self.gold,
            "diamond": self.diamond,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConsumablePrice:
        """从字典创建"""
        return cls(
            gold=data.get("gold"),
            diamond=data.get("diamond"),
        )


@dataclass
class ConsumableEffectConfig:
    """
    道具效果配置

    定义道具的具体效果。

    Attributes:
        effect_type: 效果类型
        value: 效果数值
        duration_type: 持续类型（instant: 即时消耗, rounds: 持续回合数）
        duration_value: 持续值
    """

    effect_type: ConsumableEffect
    value: float = 1.0
    duration_type: str = "instant"  # instant, rounds
    duration_value: int = 1

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "effect_type": self.effect_type.value,
            "value": self.value,
            "duration_type": self.duration_type,
            "duration_value": self.duration_value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConsumableEffectConfig:
        """从字典创建"""
        return cls(
            effect_type=ConsumableEffect(data["effect_type"]),
            value=data.get("value", 1.0),
            duration_type=data.get("duration_type", "instant"),
            duration_value=data.get("duration_value", 1),
        )


@dataclass
class ConsumableItem:
    """
    道具配置

    定义一个完整的道具配置。

    Attributes:
        consumable_id: 道具唯一ID
        name: 道具名称
        description: 道具描述
        consumable_type: 道具类型
        rarity: 道具稀有度
        effects: 效果列表
        price: 购买价格
        max_stack: 最大堆叠数量
        is_active: 是否启用
        icon: 图标路径
        auto_use: 是否自动使用（如段位保护卡）
    """

    consumable_id: str
    name: str
    consumable_type: ConsumableType
    description: str = ""
    rarity: ConsumableRarity = ConsumableRarity.COMMON
    effects: list[ConsumableEffectConfig] = field(default_factory=list)
    price: ConsumablePrice | None = None
    max_stack: int = 99
    is_active: bool = True
    icon: str = ""
    auto_use: bool = False

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "consumable_id": self.consumable_id,
            "name": self.name,
            "description": self.description,
            "consumable_type": self.consumable_type.value,
            "rarity": self.rarity.value,
            "effects": [e.to_dict() for e in self.effects],
            "price": self.price.to_dict() if self.price else None,
            "max_stack": self.max_stack,
            "is_active": self.is_active,
            "icon": self.icon,
            "auto_use": self.auto_use,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConsumableItem:
        """从字典创建"""
        price_data = data.get("price")
        price = ConsumablePrice.from_dict(price_data) if price_data else None

        return cls(
            consumable_id=data["consumable_id"],
            name=data["name"],
            description=data.get("description", ""),
            consumable_type=ConsumableType(data["consumable_type"]),
            rarity=ConsumableRarity(data.get("rarity", "common")),
            effects=[ConsumableEffectConfig.from_dict(e) for e in data.get("effects", [])],
            price=price,
            max_stack=data.get("max_stack", 99),
            is_active=data.get("is_active", True),
            icon=data.get("icon", ""),
            auto_use=data.get("auto_use", False),
        )

    def get_effect_value(self, effect_type: ConsumableEffect) -> float:
        """
        获取指定效果的数值

        Args:
            effect_type: 效果类型

        Returns:
            效果数值，不存在返回0
        """
        for effect in self.effects:
            if effect.effect_type == effect_type:
                return effect.value
        return 0.0

    def has_effect(self, effect_type: ConsumableEffect) -> bool:
        """
        检查是否有指定效果

        Args:
            effect_type: 效果类型

        Returns:
            是否有该效果
        """
        return any(e.effect_type == effect_type for e in self.effects)


@dataclass
class PlayerConsumable:
    """
    玩家拥有的道具

    记录玩家拥有的道具信息。

    Attributes:
        player_id: 玩家ID
        consumable_id: 道具ID
        quantity: 数量
        acquired_at: 获得时间
        acquire_type: 获得方式
        expire_at: 过期时间（None表示永不过期）
    """

    player_id: str
    consumable_id: str
    quantity: int
    acquired_at: datetime
    acquire_type: str = "buy"  # buy, reward, achievement, checkin, event
    expire_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "player_id": self.player_id,
            "consumable_id": self.consumable_id,
            "quantity": self.quantity,
            "acquired_at": self.acquired_at.isoformat(),
            "acquire_type": self.acquire_type,
            "expire_at": self.expire_at.isoformat() if self.expire_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PlayerConsumable:
        """从字典创建"""
        return cls(
            player_id=data["player_id"],
            consumable_id=data["consumable_id"],
            quantity=data["quantity"],
            acquired_at=datetime.fromisoformat(data["acquired_at"]),
            acquire_type=data.get("acquire_type", "buy"),
            expire_at=datetime.fromisoformat(data["expire_at"]) if data.get("expire_at") else None,
        )

    def is_expired(self) -> bool:
        """检查是否已过期"""
        if self.expire_at is None:
            return False
        return datetime.now() > self.expire_at

    def add_quantity(self, amount: int, max_stack: int = 99) -> int:
        """
        增加数量

        Args:
            amount: 增加数量
            max_stack: 最大堆叠数

        Returns:
            实际增加数量
        """
        old_qty = self.quantity
        self.quantity = min(self.quantity + amount, max_stack)
        return self.quantity - old_qty

    def use_quantity(self, amount: int = 1) -> bool:
        """
        使用道具（减少数量）

        Args:
            amount: 使用数量

        Returns:
            是否成功
        """
        if self.quantity < amount:
            return False
        self.quantity -= amount
        return True


@dataclass
class ConsumableUsage:
    """
    道具使用记录

    记录道具使用历史。

    Attributes:
        player_id: 玩家ID
        consumable_id: 道具ID
        used_at: 使用时间
        quantity: 使用数量
        context: 使用场景（match, shop等）
        context_id: 场景ID（如对局ID）
        effect_applied: 是否生效
        effect_data: 效果数据
    """

    player_id: str
    consumable_id: str
    used_at: datetime
    quantity: int = 1
    context: str = "match"
    context_id: str | None = None
    effect_applied: bool = True
    effect_data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "player_id": self.player_id,
            "consumable_id": self.consumable_id,
            "used_at": self.used_at.isoformat(),
            "quantity": self.quantity,
            "context": self.context,
            "context_id": self.context_id,
            "effect_applied": self.effect_applied,
            "effect_data": self.effect_data,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConsumableUsage:
        """从字典创建"""
        return cls(
            player_id=data["player_id"],
            consumable_id=data["consumable_id"],
            used_at=datetime.fromisoformat(data["used_at"]),
            quantity=data.get("quantity", 1),
            context=data.get("context", "match"),
            context_id=data.get("context_id"),
            effect_applied=data.get("effect_applied", True),
            effect_data=data.get("effect_data", {}),
        )


@dataclass
class ActiveConsumableEffect:
    """
    激活中的道具效果

    记录当前激活的道具效果（用于持续效果）。

    Attributes:
        player_id: 玩家ID
        consumable_id: 道具ID
        effect_type: 效果类型
        value: 效果数值
        activated_at: 激活时间
        remaining_rounds: 剩余回合数（-1表示无限）
        context: 激活场景
    """

    player_id: str
    consumable_id: str
    effect_type: ConsumableEffect
    value: float
    activated_at: datetime
    remaining_rounds: int = -1
    context: str = "match"

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "player_id": self.player_id,
            "consumable_id": self.consumable_id,
            "effect_type": self.effect_type.value,
            "value": self.value,
            "activated_at": self.activated_at.isoformat(),
            "remaining_rounds": self.remaining_rounds,
            "context": self.context,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ActiveConsumableEffect:
        """从字典创建"""
        return cls(
            player_id=data["player_id"],
            consumable_id=data["consumable_id"],
            effect_type=ConsumableEffect(data["effect_type"]),
            value=data["value"],
            activated_at=datetime.fromisoformat(data["activated_at"]),
            remaining_rounds=data.get("remaining_rounds", -1),
            context=data.get("context", "match"),
        )

    def decrement_rounds(self) -> bool:
        """
        减少剩余回合数

        Returns:
            效果是否仍然有效
        """
        if self.remaining_rounds <= 0:
            return True  # 无限持续
        self.remaining_rounds -= 1
        return self.remaining_rounds > 0

    def is_expired(self) -> bool:
        """检查效果是否已过期"""
        if self.remaining_rounds < 0:
            return False  # 无限持续
        return self.remaining_rounds <= 0
