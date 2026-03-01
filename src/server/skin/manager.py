"""
王者之奕 - 皮肤管理器

本模块提供皮肤系统的管理功能：
- SkinManager: 皮肤管理器类
- 皮肤配置加载
- 皮肤获取、装备、购买
- 属性加成计算
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import (
    PlayerSkin,
    Skin,
    SkinEffectType,
    SkinRarity,
    SkinType,
)

logger = logging.getLogger(__name__)


class SkinManager:
    """
    皮肤管理器

    负责管理所有皮肤相关的操作：
    - 皮肤配置加载
    - 获取皮肤列表
    - 装备/卸下皮肤
    - 购买皮肤
    - 解锁皮肤
    - 皮肤属性加成计算

    Attributes:
        skins: 所有皮肤配置 (skin_id -> Skin)
        hero_skins: 按英雄分组的皮肤 (hero_id -> List[Skin])
        player_skins: 玩家拥有的皮肤 (player_id -> Dict[skin_id, PlayerSkin])
        equipped_skins: 玩家装备的皮肤 (player_id -> Dict[hero_id, skin_id])
        config_path: 配置文件路径
    """

    def __init__(self, config_path: str | None = None):
        """
        初始化皮肤管理器

        Args:
            config_path: 皮肤配置文件路径
        """
        self.skins: dict[str, Skin] = {}
        self.hero_skins: dict[str, list[Skin]] = {}
        self.player_skins: dict[str, dict[str, PlayerSkin]] = {}
        self.equipped_skins: dict[str, dict[str, str]] = {}
        self.config_path = config_path

        # 加载配置
        if config_path:
            self.load_config(config_path)

        logger.info(f"SkinManager initialized with {len(self.skins)} skins")

    def load_config(self, config_path: str) -> None:
        """
        从配置文件加载皮肤配置

        Args:
            config_path: 配置文件路径
        """
        path = Path(config_path)
        if not path.exists():
            logger.warning(f"Skin config file not found: {config_path}")
            return

        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)

            # 加载皮肤
            for skin_data in data.get("skins", []):
                skin = Skin.from_dict(skin_data)
                self.skins[skin.skin_id] = skin

                # 按英雄分组
                if skin.hero_id not in self.hero_skins:
                    self.hero_skins[skin.hero_id] = []
                self.hero_skins[skin.hero_id].append(skin)

            logger.info(f"Loaded {len(self.skins)} skins from {config_path}")

        except Exception as e:
            logger.error(f"Failed to load skin config: {e}")

    def save_config(self, config_path: str | None = None) -> None:
        """
        保存皮肤配置到文件

        Args:
            config_path: 配置文件路径
        """
        path = Path(config_path or self.config_path)
        if not path:
            logger.warning("No config path specified for saving")
            return

        try:
            data = {
                "version": "1.0.0",
                "last_updated": datetime.now().isoformat(),
                "skins": [skin.to_dict() for skin in self.skins.values()],
            }

            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"Saved skin config to {path}")

        except Exception as e:
            logger.error(f"Failed to save skin config: {e}")

    # ========================================================================
    # 皮肤查询
    # ========================================================================

    def get_skin(self, skin_id: str) -> Skin | None:
        """
        获取皮肤配置

        Args:
            skin_id: 皮肤ID

        Returns:
            皮肤配置，不存在返回None
        """
        return self.skins.get(skin_id)

    def get_all_skins(self) -> list[Skin]:
        """
        获取所有皮肤

        Returns:
            皮肤列表
        """
        return list(self.skins.values())

    def get_skins_by_hero(self, hero_id: str) -> list[Skin]:
        """
        获取英雄的所有皮肤

        Args:
            hero_id: 英雄ID

        Returns:
            皮肤列表
        """
        return self.hero_skins.get(hero_id, [])

    def get_skins_by_rarity(self, rarity: SkinRarity) -> list[Skin]:
        """
        获取指定稀有度的皮肤

        Args:
            rarity: 皮肤稀有度

        Returns:
            皮肤列表
        """
        return [skin for skin in self.skins.values() if skin.rarity == rarity]

    def get_skins_by_type(self, skin_type: SkinType) -> list[Skin]:
        """
        获取指定类型的皮肤

        Args:
            skin_type: 皮肤类型

        Returns:
            皮肤列表
        """
        return [skin for skin in self.skins.values() if skin.skin_type == skin_type]

    def get_available_skins(self, hero_id: str, player_id: str) -> list[Skin]:
        """
        获取玩家可用的皮肤列表（包括已拥有和可购买的）

        Args:
            hero_id: 英雄ID
            player_id: 玩家ID

        Returns:
            皮肤列表
        """
        all_skins = self.get_skins_by_hero(hero_id)
        available = []

        for skin in all_skins:
            if skin.is_available and not skin.is_expired():
                available.append(skin)

        return available

    # ========================================================================
    # 玩家皮肤管理
    # ========================================================================

    def get_player_skins(self, player_id: str) -> list[PlayerSkin]:
        """
        获取玩家拥有的所有皮肤

        Args:
            player_id: 玩家ID

        Returns:
            皮肤列表
        """
        player_skin_dict = self.player_skins.get(player_id, {})
        return list(player_skin_dict.values())

    def get_player_skins_by_hero(self, player_id: str, hero_id: str) -> list[PlayerSkin]:
        """
        获取玩家拥有的指定英雄的皮肤

        Args:
            player_id: 玩家ID
            hero_id: 英雄ID

        Returns:
            皮肤列表
        """
        player_skin_dict = self.player_skins.get(player_id, {})
        return [ps for ps in player_skin_dict.values() if ps.hero_id == hero_id]

    def has_skin(self, player_id: str, skin_id: str) -> bool:
        """
        检查玩家是否拥有皮肤

        Args:
            player_id: 玩家ID
            skin_id: 皮肤ID

        Returns:
            是否拥有
        """
        player_skin_dict = self.player_skins.get(player_id, {})
        return skin_id in player_skin_dict

    def get_equipped_skin(self, player_id: str, hero_id: str) -> str | None:
        """
        获取玩家装备的皮肤

        Args:
            player_id: 玩家ID
            hero_id: 英雄ID

        Returns:
            装备的皮肤ID，未装备返回None
        """
        equipped = self.equipped_skins.get(player_id, {})
        return equipped.get(hero_id)

    def get_equipped_skin_config(self, player_id: str, hero_id: str) -> Skin | None:
        """
        获取玩家装备的皮肤配置

        Args:
            player_id: 玩家ID
            hero_id: 英雄ID

        Returns:
            装备的皮肤配置，未装备返回None
        """
        skin_id = self.get_equipped_skin(player_id, hero_id)
        if skin_id:
            return self.get_skin(skin_id)
        return None

    # ========================================================================
    # 皮肤操作
    # ========================================================================

    def equip_skin(
        self,
        player_id: str,
        skin_id: str,
    ) -> tuple[bool, str | None]:
        """
        装备皮肤

        Args:
            player_id: 玩家ID
            skin_id: 皮肤ID

        Returns:
            (是否成功, 错误信息)
        """
        # 检查皮肤是否存在
        skin = self.get_skin(skin_id)
        if not skin:
            return False, "皮肤不存在"

        # 检查玩家是否拥有
        if not self.has_skin(player_id, skin_id):
            return False, "未拥有该皮肤"

        # 获取玩家皮肤
        player_skin = self.player_skins[player_id][skin_id]

        # 卸下当前装备的皮肤
        current_equipped = self.get_equipped_skin(player_id, skin.hero_id)
        if current_equipped and current_equipped in self.player_skins.get(player_id, {}):
            self.player_skins[player_id][current_equipped].unequip()

        # 装备新皮肤
        player_skin.equip()

        # 更新装备记录
        if player_id not in self.equipped_skins:
            self.equipped_skins[player_id] = {}
        self.equipped_skins[player_id][skin.hero_id] = skin_id

        logger.info(f"Player {player_id} equipped skin {skin_id}")

        return True, None

    def unequip_skin(
        self,
        player_id: str,
        hero_id: str,
    ) -> tuple[bool, str | None]:
        """
        卸下皮肤（恢复默认皮肤）

        Args:
            player_id: 玩家ID
            hero_id: 英雄ID

        Returns:
            (是否成功, 错误信息)
        """
        skin_id = self.get_equipped_skin(player_id, hero_id)
        if not skin_id:
            return False, "该英雄未装备皮肤"

        # 卸下皮肤
        if skin_id in self.player_skins.get(player_id, {}):
            self.player_skins[player_id][skin_id].unequip()

        # 移除装备记录
        if player_id in self.equipped_skins:
            self.equipped_skins[player_id].pop(hero_id, None)

        logger.info(f"Player {player_id} unequipped skin for hero {hero_id}")

        return True, None

    def buy_skin(
        self,
        player_id: str,
        skin_id: str,
        gold: int,
        diamond: int,
        use_currency: str = "auto",
    ) -> tuple[PlayerSkin | None, str, int, str | None]:
        """
        购买皮肤

        Args:
            player_id: 玩家ID
            skin_id: 皮肤ID
            gold: 玩家金币
            diamond: 玩家钻石
            use_currency: 使用的货币类型（auto/gold/diamond）

        Returns:
            (玩家皮肤, 消耗货币类型, 消耗数量, 错误信息)
        """
        # 检查皮肤是否存在
        skin = self.get_skin(skin_id)
        if not skin:
            return None, "", 0, "皮肤不存在"

        # 检查皮肤是否可购买
        if skin.skin_type != SkinType.SHOP:
            return None, "", 0, "该皮肤不可购买"

        # 检查皮肤是否可用
        if not skin.is_available or skin.is_expired():
            return None, "", 0, "该皮肤已下架"

        # 检查是否已拥有
        if self.has_skin(player_id, skin_id):
            return None, "", 0, "已拥有该皮肤"

        # 检查价格
        if not skin.price:
            return None, "", 0, "皮肤价格配置错误"

        # 选择货币
        if use_currency == "auto":
            currency, cost = skin.price.get_cheapest_option()
        elif use_currency == "gold":
            if skin.price.gold is None:
                return None, "", 0, "该皮肤不支持金币购买"
            currency, cost = "gold", skin.price.gold
        elif use_currency == "diamond":
            if skin.price.diamond is None:
                return None, "", 0, "该皮肤不支持钻石购买"
            currency, cost = "diamond", skin.price.diamond
        else:
            return None, "", 0, "无效的货币类型"

        # 检查余额
        if currency == "gold" and gold < cost:
            return None, "", 0, f"金币不足，需要{cost}金币"
        if currency == "diamond" and diamond < cost:
            return None, "", 0, f"钻石不足，需要{cost}钻石"

        # 创建玩家皮肤
        player_skin = PlayerSkin(
            player_id=player_id,
            skin_id=skin_id,
            hero_id=skin.hero_id,
            acquired_at=datetime.now(),
            acquire_type="buy",
        )

        # 保存
        if player_id not in self.player_skins:
            self.player_skins[player_id] = {}
        self.player_skins[player_id][skin_id] = player_skin

        logger.info(f"Player {player_id} bought skin {skin_id} with {cost} {currency}")

        return player_skin, currency, cost, None

    def unlock_skin(
        self,
        player_id: str,
        skin_id: str,
        unlock_type: str = "reward",
    ) -> tuple[PlayerSkin | None, str | None]:
        """
        解锁皮肤（奖励、成就、活动等）

        Args:
            player_id: 玩家ID
            skin_id: 皮肤ID
            unlock_type: 解锁类型（reward/achievement/event）

        Returns:
            (玩家皮肤, 错误信息)
        """
        # 检查皮肤是否存在
        skin = self.get_skin(skin_id)
        if not skin:
            return None, "皮肤不存在"

        # 检查是否已拥有
        if self.has_skin(player_id, skin_id):
            return None, "已拥有该皮肤"

        # 创建玩家皮肤
        player_skin = PlayerSkin(
            player_id=player_id,
            skin_id=skin_id,
            hero_id=skin.hero_id,
            acquired_at=datetime.now(),
            acquire_type=unlock_type,
        )

        # 保存
        if player_id not in self.player_skins:
            self.player_skins[player_id] = {}
        self.player_skins[player_id][skin_id] = player_skin

        logger.info(f"Player {player_id} unlocked skin {skin_id} via {unlock_type}")

        return player_skin, None

    # ========================================================================
    # 属性加成计算
    # ========================================================================

    def calculate_stat_bonuses(
        self,
        player_id: str,
        hero_id: str,
        base_stats: dict[str, float],
    ) -> dict[str, float]:
        """
        计算皮肤带来的属性加成

        Args:
            player_id: 玩家ID
            hero_id: 英雄ID
            base_stats: 英雄基础属性

        Returns:
            加成后的属性
        """
        # 获取装备的皮肤
        skin = self.get_equipped_skin_config(player_id, hero_id)
        if not skin:
            return base_stats.copy()

        # 应用皮肤加成
        return skin.apply_stat_bonuses(base_stats)

    def get_stat_bonus_description(self, skin_id: str) -> str:
        """
        获取皮肤属性加成描述

        Args:
            skin_id: 皮肤ID

        Returns:
            属性加成描述文本
        """
        skin = self.get_skin(skin_id)
        if not skin or not skin.stat_bonuses:
            return "无属性加成"

        descriptions = []
        stat_names = {
            "hp": "生命值",
            "attack": "攻击力",
            "armor": "护甲",
            "magic_resist": "魔抗",
            "attack_speed": "攻击速度",
            "range": "攻击距离",
        }

        for bonus in skin.stat_bonuses:
            stat_name = stat_names.get(bonus.stat_name, bonus.stat_name)
            descriptions.append(f"{stat_name}+{bonus.bonus_percent}%")

        return "，".join(descriptions)

    def get_effect_description(self, skin_id: str) -> str:
        """
        获取皮肤特效描述

        Args:
            skin_id: 皮肤ID

        Returns:
            特效描述文本
        """
        skin = self.get_skin(skin_id)
        if not skin or not skin.effects:
            return "无特效"

        effect_names = {
            SkinEffectType.MODEL: "模型",
            SkinEffectType.PARTICLE: "粒子",
            SkinEffectType.SKILL: "技能",
            SkinEffectType.SOUND: "音效",
            SkinEffectType.EMOTE: "表情",
            SkinEffectType.PORTRAIT: "肖像",
        }

        descriptions = []
        for effect in skin.effects:
            effect_name = effect_names.get(effect.effect_type, "特效")
            if effect.description:
                descriptions.append(f"{effect_name}:{effect.description}")
            else:
                descriptions.append(f"{effect_name}特效")

        return "，".join(descriptions)

    # ========================================================================
    # 皮肤数据持久化（内存实现，实际应使用数据库）
    # ========================================================================

    def load_player_skins(self, player_id: str, skins_data: list[dict[str, Any]]) -> None:
        """
        加载玩家皮肤数据

        Args:
            player_id: 玩家ID
            skins_data: 皮肤数据列表
        """
        self.player_skins[player_id] = {}
        self.equipped_skins[player_id] = {}

        for data in skins_data:
            player_skin = PlayerSkin.from_dict(data)
            self.player_skins[player_id][player_skin.skin_id] = player_skin

            if player_skin.is_equipped:
                self.equipped_skins[player_id][player_skin.hero_id] = player_skin.skin_id

        logger.info(f"Loaded {len(skins_data)} skins for player {player_id}")

    def get_player_skins_data(self, player_id: str) -> list[dict[str, Any]]:
        """
        获取玩家皮肤数据（用于保存）

        Args:
            player_id: 玩家ID

        Returns:
            皮肤数据列表
        """
        player_skin_dict = self.player_skins.get(player_id, {})
        return [ps.to_dict() for ps in player_skin_dict.values()]

    def clear_cache(self, player_id: str | None = None) -> None:
        """
        清除缓存

        Args:
            player_id: 玩家ID（None表示清除所有）
        """
        if player_id:
            self.player_skins.pop(player_id, None)
            self.equipped_skins.pop(player_id, None)
        else:
            self.player_skins.clear()
            self.equipped_skins.clear()


# 全局单例
_skin_manager: SkinManager | None = None


def get_skin_manager(config_path: str | None = None) -> SkinManager:
    """
    获取皮肤管理器单例

    Args:
        config_path: 配置文件路径

    Returns:
        皮肤管理器实例
    """
    global _skin_manager
    if _skin_manager is None:
        _skin_manager = SkinManager(config_path)
    return _skin_manager
