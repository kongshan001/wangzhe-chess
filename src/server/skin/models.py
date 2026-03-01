"""
王者之奕 - 皮肤数据模型

本模块定义皮肤系统相关的数据模型：
- SkinRarity: 皮肤稀有度枚举
- SkinType: 皮肤类型枚举
- SkinEffect: 皮肤特效
- SkinStatBonus: 皮肤属性加成
- Skin: 皮肤配置
- SkinPrice: 皮肤价格
- PlayerSkin: 玩家拥有的皮肤
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class SkinRarity(StrEnum):
    """皮肤稀有度枚举"""

    NORMAL = "normal"  # 普通皮肤：纯视觉变化
    RARE = "rare"  # 稀有皮肤：+5%某一属性
    EPIC = "epic"  # 史诗皮肤：+5%多属性 + 特效
    LEGENDARY = "legendary"  # 传说皮肤：+8%多属性 + 全新技能特效

    @classmethod
    def get_display_name(cls, rarity: str) -> str:
        """获取稀有度显示名称"""
        display_names = {
            cls.NORMAL.value: "普通",
            cls.RARE.value: "稀有",
            cls.EPIC.value: "史诗",
            cls.LEGENDARY.value: "传说",
        }
        return display_names.get(rarity, "未知")

    @classmethod
    def get_bonus_percent(cls, rarity: str) -> int:
        """获取属性加成百分比"""
        bonus_map = {
            cls.NORMAL.value: 0,  # 普通皮肤无加成
            cls.RARE.value: 5,  # 稀有+5%
            cls.EPIC.value: 5,  # 史诗+5%
            cls.LEGENDARY.value: 8,  # 传说+8%
        }
        return bonus_map.get(rarity, 0)

    @classmethod
    def get_color(cls, rarity: str) -> str:
        """获取稀有度颜色（用于UI显示）"""
        colors = {
            cls.NORMAL.value: "#FFFFFF",  # 白色
            cls.RARE.value: "#1EFF00",  # 绿色
            cls.EPIC.value: "#A335EE",  # 紫色
            cls.LEGENDARY.value: "#FF8000",  # 橙色
        }
        return colors.get(rarity, "#FFFFFF")


class SkinType(StrEnum):
    """皮肤类型枚举"""

    SHOP = "shop"  # 商店购买
    SEASON_REWARD = "season_reward"  # 赛季奖励
    ACHIEVEMENT = "achievement"  # 成就解锁
    EVENT = "event"  # 活动限定
    DEFAULT = "default"  # 默认皮肤


class SkinEffectType(StrEnum):
    """皮肤特效类型枚举"""

    MODEL = "model"  # 模型变化
    PARTICLE = "particle"  # 粒子特效
    SKILL = "skill"  # 技能特效
    SOUND = "sound"  # 音效变化
    EMOTE = "emote"  # 专属表情
    PORTRAIT = "portrait"  # 肖像变化


@dataclass
class SkinEffect:
    """
    皮肤特效

    定义皮肤的视觉和听觉特效。

    Attributes:
        effect_type: 特效类型
        effect_id: 特效ID/资源路径
        description: 特效描述
    """

    effect_type: SkinEffectType
    effect_id: str
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "effect_type": self.effect_type.value,
            "effect_id": self.effect_id,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SkinEffect:
        """从字典创建"""
        return cls(
            effect_type=SkinEffectType(data["effect_type"]),
            effect_id=data["effect_id"],
            description=data.get("description", ""),
        )


@dataclass
class SkinStatBonus:
    """
    皮肤属性加成

    定义皮肤对英雄属性的加成效果。

    Attributes:
        stat_name: 属性名称（hp, attack, armor, magic_resist, attack_speed等）
        bonus_percent: 加成百分比
    """

    stat_name: str
    bonus_percent: float

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "stat_name": self.stat_name,
            "bonus_percent": self.bonus_percent,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SkinStatBonus:
        """从字典创建"""
        return cls(
            stat_name=data["stat_name"],
            bonus_percent=data["bonus_percent"],
        )

    def apply_bonus(self, base_value: float) -> float:
        """
        应用属性加成

        Args:
            base_value: 基础属性值

        Returns:
            加成后的属性值
        """
        return base_value * (1 + self.bonus_percent / 100)


@dataclass
class SkinPrice:
    """
    皮肤价格

    定义皮肤的购买价格。

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
    def from_dict(cls, data: dict[str, Any]) -> SkinPrice:
        """从字典创建"""
        return cls(
            gold=data.get("gold"),
            diamond=data.get("diamond"),
        )

    def can_afford(self, gold: int, diamond: int) -> bool:
        """
        检查是否买得起

        Args:
            gold: 玩家金币
            diamond: 玩家钻石

        Returns:
            是否买得起
        """
        if self.gold is not None and gold >= self.gold:
            return True
        if self.diamond is not None and diamond >= self.diamond:
            return True
        return False

    def get_cheapest_option(self) -> tuple[str, int]:
        """
        获取最便宜的购买方式

        Returns:
            (货币类型, 价格)
        """
        if self.gold is not None and self.diamond is not None:
            # 假设1钻石=10金币的比例
            if self.gold <= self.diamond * 10:
                return ("gold", self.gold)
            return ("diamond", self.diamond)
        elif self.gold is not None:
            return ("gold", self.gold)
        elif self.diamond is not None:
            return ("diamond", self.diamond)
        return ("free", 0)


@dataclass
class Skin:
    """
    皮肤配置

    定义一个完整的皮肤配置。

    Attributes:
        skin_id: 皮肤唯一ID
        hero_id: 所属英雄ID
        name: 皮肤名称
        description: 皮肤描述
        rarity: 皮肤稀有度
        skin_type: 皮肤类型
        price: 购买价格
        stat_bonuses: 属性加成列表
        effects: 特效列表
        preview_image: 预览图片路径
        model_path: 模型资源路径
        is_available: 是否可获取
        release_date: 发布日期
        expire_date: 过期日期（限时皮肤）
    """

    skin_id: str
    hero_id: str
    name: str
    rarity: SkinRarity
    skin_type: SkinType
    description: str = ""
    price: SkinPrice | None = None
    stat_bonuses: list[SkinStatBonus] = field(default_factory=list)
    effects: list[SkinEffect] = field(default_factory=list)
    preview_image: str = ""
    model_path: str = ""
    is_available: bool = True
    release_date: datetime | None = None
    expire_date: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "skin_id": self.skin_id,
            "hero_id": self.hero_id,
            "name": self.name,
            "description": self.description,
            "rarity": self.rarity.value,
            "skin_type": self.skin_type.value,
            "price": self.price.to_dict() if self.price else None,
            "stat_bonuses": [b.to_dict() for b in self.stat_bonuses],
            "effects": [e.to_dict() for e in self.effects],
            "preview_image": self.preview_image,
            "model_path": self.model_path,
            "is_available": self.is_available,
            "release_date": self.release_date.isoformat() if self.release_date else None,
            "expire_date": self.expire_date.isoformat() if self.expire_date else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Skin:
        """从字典创建"""
        price_data = data.get("price")
        price = SkinPrice.from_dict(price_data) if price_data else None

        return cls(
            skin_id=data["skin_id"],
            hero_id=data["hero_id"],
            name=data["name"],
            description=data.get("description", ""),
            rarity=SkinRarity(data["rarity"]),
            skin_type=SkinType(data.get("skin_type", "shop")),
            price=price,
            stat_bonuses=[SkinStatBonus.from_dict(b) for b in data.get("stat_bonuses", [])],
            effects=[SkinEffect.from_dict(e) for e in data.get("effects", [])],
            preview_image=data.get("preview_image", ""),
            model_path=data.get("model_path", ""),
            is_available=data.get("is_available", True),
            release_date=datetime.fromisoformat(data["release_date"])
            if data.get("release_date")
            else None,
            expire_date=datetime.fromisoformat(data["expire_date"])
            if data.get("expire_date")
            else None,
        )

    def get_total_bonus(self, stat_name: str) -> float:
        """
        获取指定属性的总加成百分比

        Args:
            stat_name: 属性名称

        Returns:
            总加成百分比
        """
        total = 0.0
        for bonus in self.stat_bonuses:
            if bonus.stat_name == stat_name:
                total += bonus.bonus_percent
        return total

    def apply_stat_bonuses(self, base_stats: dict[str, float]) -> dict[str, float]:
        """
        应用所有属性加成

        Args:
            base_stats: 基础属性字典

        Returns:
            加成后的属性字典
        """
        result = base_stats.copy()
        for bonus in self.stat_bonuses:
            if bonus.stat_name in result:
                result[bonus.stat_name] = bonus.apply_bonus(result[bonus.stat_name])
        return result

    def has_effect(self, effect_type: SkinEffectType) -> bool:
        """
        检查是否有指定类型的特效

        Args:
            effect_type: 特效类型

        Returns:
            是否有该特效
        """
        return any(e.effect_type == effect_type for e in self.effects)

    def get_effects_by_type(self, effect_type: SkinEffectType) -> list[SkinEffect]:
        """
        获取指定类型的所有特效

        Args:
            effect_type: 特效类型

        Returns:
            特效列表
        """
        return [e for e in self.effects if e.effect_type == effect_type]

    def is_limited_time(self) -> bool:
        """检查是否为限时皮肤"""
        return self.expire_date is not None

    def is_expired(self) -> bool:
        """检查皮肤是否已过期"""
        if self.expire_date is None:
            return False
        return datetime.now() > self.expire_date


@dataclass
class PlayerSkin:
    """
    玩家拥有的皮肤

    记录玩家拥有的皮肤信息。

    Attributes:
        player_id: 玩家ID
        skin_id: 皮肤ID
        hero_id: 英雄ID
        acquired_at: 获得时间
        acquire_type: 获得方式
        is_equipped: 是否已装备
        equipped_at: 装备时间
    """

    player_id: str
    skin_id: str
    hero_id: str
    acquired_at: datetime
    acquire_type: str = "buy"  # buy, reward, achievement, event
    is_equipped: bool = False
    equipped_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "player_id": self.player_id,
            "skin_id": self.skin_id,
            "hero_id": self.hero_id,
            "acquired_at": self.acquired_at.isoformat(),
            "acquire_type": self.acquire_type,
            "is_equipped": self.is_equipped,
            "equipped_at": self.equipped_at.isoformat() if self.equipped_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PlayerSkin:
        """从字典创建"""
        return cls(
            player_id=data["player_id"],
            skin_id=data["skin_id"],
            hero_id=data["hero_id"],
            acquired_at=datetime.fromisoformat(data["acquired_at"]),
            acquire_type=data.get("acquire_type", "buy"),
            is_equipped=data.get("is_equipped", False),
            equipped_at=datetime.fromisoformat(data["equipped_at"])
            if data.get("equipped_at")
            else None,
        )

    def equip(self) -> None:
        """装备皮肤"""
        self.is_equipped = True
        self.equipped_at = datetime.now()

    def unequip(self) -> None:
        """卸下皮肤"""
        self.is_equipped = False
        self.equipped_at = None
