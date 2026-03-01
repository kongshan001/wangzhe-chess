"""
王者之奕 - 道具管理器

本模块提供道具系统的管理功能：
- ConsumableManager: 道具管理器类
- 道具配置加载
- 道具获取、使用、添加
- 道具效果计算
- 道具历史记录
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import (
    ActiveConsumableEffect,
    ConsumableEffect,
    ConsumableItem,
    ConsumableRarity,
    ConsumableType,
    ConsumableUsage,
    PlayerConsumable,
)

logger = logging.getLogger(__name__)


class ConsumableManager:
    """
    道具管理器

    负责管理所有道具相关的操作：
    - 道具配置加载
    - 获取道具列表
    - 使用/添加道具
    - 道具效果计算
    - 道具使用历史

    Attributes:
        consumables: 所有道具配置 (consumable_id -> ConsumableItem)
        player_consumables: 玩家拥有的道具 (player_id -> Dict[consumable_id, PlayerConsumable])
        active_effects: 玩家激活的道具效果 (player_id -> List[ActiveConsumableEffect])
        usage_history: 道具使用历史 (player_id -> List[ConsumableUsage])
        config_path: 配置文件路径
    """

    def __init__(self, config_path: str | None = None):
        """
        初始化道具管理器

        Args:
            config_path: 道具配置文件路径
        """
        self.consumables: dict[str, ConsumableItem] = {}
        self.player_consumables: dict[str, dict[str, PlayerConsumable]] = {}
        self.active_effects: dict[str, list[ActiveConsumableEffect]] = {}
        self.usage_history: dict[str, list[ConsumableUsage]] = {}
        self.config_path = config_path

        # 加载配置
        if config_path:
            self.load_config(config_path)

        logger.info(f"ConsumableManager initialized with {len(self.consumables)} consumables")

    def load_config(self, config_path: str) -> None:
        """
        从配置文件加载道具配置

        Args:
            config_path: 配置文件路径
        """
        path = Path(config_path)
        if not path.exists():
            logger.warning(f"Consumable config file not found: {config_path}")
            return

        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)

            # 加载道具
            for consumable_data in data.get("consumables", []):
                consumable = ConsumableItem.from_dict(consumable_data)
                self.consumables[consumable.consumable_id] = consumable

            logger.info(f"Loaded {len(self.consumables)} consumables from {config_path}")

        except Exception as e:
            logger.error(f"Failed to load consumable config: {e}")

    def save_config(self, config_path: str | None = None) -> None:
        """
        保存道具配置到文件

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
                "consumables": [c.to_dict() for c in self.consumables.values()],
            }

            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"Saved consumable config to {path}")

        except Exception as e:
            logger.error(f"Failed to save consumable config: {e}")

    # ========================================================================
    # 道具查询
    # ========================================================================

    def get_consumable(self, consumable_id: str) -> ConsumableItem | None:
        """
        获取道具配置

        Args:
            consumable_id: 道具ID

        Returns:
            道具配置，不存在返回None
        """
        return self.consumables.get(consumable_id)

    def get_all_consumables(self) -> list[ConsumableItem]:
        """
        获取所有道具

        Returns:
            道具列表
        """
        return list(self.consumables.values())

    def get_consumables_by_type(self, ctype: ConsumableType) -> list[ConsumableItem]:
        """
        获取指定类型的道具

        Args:
            ctype: 道具类型

        Returns:
            道具列表
        """
        return [c for c in self.consumables.values() if c.consumable_type == ctype]

    def get_consumables_by_rarity(self, rarity: ConsumableRarity) -> list[ConsumableItem]:
        """
        获取指定稀有度的道具

        Args:
            rarity: 道具稀有度

        Returns:
            道具列表
        """
        return [c for c in self.consumables.values() if c.rarity == rarity]

    # ========================================================================
    # 玩家道具管理
    # ========================================================================

    def get_player_consumables(self, player_id: str) -> list[PlayerConsumable]:
        """
        获取玩家的所有道具

        Args:
            player_id: 玩家ID

        Returns:
            道具列表
        """
        player_dict = self.player_consumables.get(player_id, {})
        # 过滤过期道具
        valid = [pc for pc in player_dict.values() if not pc.is_expired()]
        return valid

    def get_player_consumable(
        self,
        player_id: str,
        consumable_id: str,
    ) -> PlayerConsumable | None:
        """
        获取玩家指定的道具

        Args:
            player_id: 玩家ID
            consumable_id: 道具ID

        Returns:
            道具，不存在或过期返回None
        """
        player_dict = self.player_consumables.get(player_id, {})
        pc = player_dict.get(consumable_id)
        if pc and pc.is_expired():
            return None
        return pc

    def has_consumable(
        self,
        player_id: str,
        consumable_id: str,
        quantity: int = 1,
    ) -> bool:
        """
        检查玩家是否拥有指定数量的道具

        Args:
            player_id: 玩家ID
            consumable_id: 道具ID
            quantity: 所需数量

        Returns:
            是否拥有
        """
        pc = self.get_player_consumable(player_id, consumable_id)
        return pc is not None and pc.quantity >= quantity

    def get_consumable_quantity(
        self,
        player_id: str,
        consumable_id: str,
    ) -> int:
        """
        获取玩家道具数量

        Args:
            player_id: 玩家ID
            consumable_id: 道具ID

        Returns:
            道具数量
        """
        pc = self.get_player_consumable(player_id, consumable_id)
        return pc.quantity if pc else 0

    # ========================================================================
    # 道具操作
    # ========================================================================

    def add_consumable(
        self,
        player_id: str,
        consumable_id: str,
        quantity: int = 1,
        acquire_type: str = "reward",
        expire_days: int | None = None,
    ) -> tuple[PlayerConsumable | None, str | None]:
        """
        添加道具给玩家

        Args:
            player_id: 玩家ID
            consumable_id: 道具ID
            quantity: 数量
            acquire_type: 获得方式
            expire_days: 过期天数（None表示永不过期）

        Returns:
            (玩家道具, 错误信息)
        """
        # 检查道具是否存在
        consumable = self.get_consumable(consumable_id)
        if not consumable:
            return None, "道具不存在"

        # 计算过期时间
        expire_at = None
        if expire_days:
            from datetime import timedelta

            expire_at = datetime.now() + timedelta(days=expire_days)

        # 初始化玩家道具字典
        if player_id not in self.player_consumables:
            self.player_consumables[player_id] = {}

        # 添加或更新道具
        if consumable_id in self.player_consumables[player_id]:
            pc = self.player_consumables[player_id][consumable_id]
            pc.add_quantity(quantity, consumable.max_stack)
            # 更新过期时间（取较晚的）
            if expire_at and (not pc.expire_at or expire_at > pc.expire_at):
                pc.expire_at = expire_at
        else:
            pc = PlayerConsumable(
                player_id=player_id,
                consumable_id=consumable_id,
                quantity=quantity,
                acquired_at=datetime.now(),
                acquire_type=acquire_type,
                expire_at=expire_at,
            )
            self.player_consumables[player_id][consumable_id] = pc

        logger.info(f"Player {player_id} obtained {quantity} {consumable_id} via {acquire_type}")

        return pc, None

    def use_consumable(
        self,
        player_id: str,
        consumable_id: str,
        quantity: int = 1,
        context: str = "match",
        context_id: str | None = None,
    ) -> tuple[bool, ConsumableUsage | None, str | None]:
        """
        使用道具

        Args:
            player_id: 玩家ID
            consumable_id: 道具ID
            quantity: 使用数量
            context: 使用场景
            context_id: 场景ID

        Returns:
            (是否成功, 使用记录, 错误信息)
        """
        # 检查道具是否存在
        consumable = self.get_consumable(consumable_id)
        if not consumable:
            return False, None, "道具不存在"

        # 检查玩家是否拥有
        pc = self.get_player_consumable(player_id, consumable_id)
        if not pc:
            return False, None, "未拥有该道具"

        # 检查数量
        if pc.quantity < quantity:
            return False, None, f"道具数量不足，当前{pc.quantity}个"

        # 扣除道具
        pc.use_quantity(quantity)

        # 如果数量为0，从背包移除
        if pc.quantity <= 0:
            self.player_consumables[player_id].pop(consumable_id, None)

        # 创建使用记录
        usage = ConsumableUsage(
            player_id=player_id,
            consumable_id=consumable_id,
            used_at=datetime.now(),
            quantity=quantity,
            context=context,
            context_id=context_id,
            effect_applied=True,
            effect_data={},
        )

        # 记录历史
        if player_id not in self.usage_history:
            self.usage_history[player_id] = []
        self.usage_history[player_id].append(usage)

        logger.info(f"Player {player_id} used {quantity} {consumable_id} in {context}")

        return True, usage, None

    def buy_consumable(
        self,
        player_id: str,
        consumable_id: str,
        gold: int,
        diamond: int,
        quantity: int = 1,
        use_currency: str = "auto",
    ) -> tuple[PlayerConsumable | None, str, int, str | None]:
        """
        购买道具

        Args:
            player_id: 玩家ID
            consumable_id: 道具ID
            gold: 玩家金币
            diamond: 玩家钻石
            quantity: 购买数量
            use_currency: 使用的货币类型（auto/gold/diamond）

        Returns:
            (玩家道具, 消耗货币类型, 消耗数量, 错误信息)
        """
        # 检查道具是否存在
        consumable = self.get_consumable(consumable_id)
        if not consumable:
            return None, "", 0, "道具不存在"

        # 检查是否可购买
        if not consumable.is_active:
            return None, "", 0, "该道具已下架"

        # 检查价格
        if not consumable.price:
            return None, "", 0, "道具价格配置错误"

        # 选择货币
        price = consumable.price
        if use_currency == "auto":
            if price.gold and gold >= price.gold * quantity:
                currency, cost = "gold", price.gold * quantity
            elif price.diamond and diamond >= price.diamond * quantity:
                currency, cost = "diamond", price.diamond * quantity
            else:
                return None, "", 0, "余额不足"
        elif use_currency == "gold":
            if not price.gold:
                return None, "", 0, "该道具不支持金币购买"
            if gold < price.gold * quantity:
                return None, "", 0, f"金币不足，需要{price.gold * quantity}金币"
            currency, cost = "gold", price.gold * quantity
        elif use_currency == "diamond":
            if not price.diamond:
                return None, "", 0, "该道具不支持钻石购买"
            if diamond < price.diamond * quantity:
                return None, "", 0, f"钻石不足，需要{price.diamond * quantity}钻石"
            currency, cost = "diamond", price.diamond * quantity
        else:
            return None, "", 0, "无效的货币类型"

        # 添加道具
        pc, error = self.add_consumable(
            player_id=player_id,
            consumable_id=consumable_id,
            quantity=quantity,
            acquire_type="buy",
        )

        if error:
            return None, "", 0, error

        logger.info(f"Player {player_id} bought {quantity} {consumable_id} with {cost} {currency}")

        return pc, currency, cost, None

    # ========================================================================
    # 道具效果计算
    # ========================================================================

    def apply_effect(
        self,
        player_id: str,
        consumable_id: str,
        context: str = "match",
        context_id: str | None = None,
    ) -> tuple[bool, ActiveConsumableEffect | None, str | None]:
        """
        应用道具效果

        Args:
            player_id: 玩家ID
            consumable_id: 道具ID
            context: 使用场景
            context_id: 场景ID

        Returns:
            (是否成功, 激活的效果, 错误信息)
        """
        # 使用道具
        success, usage, error = self.use_consumable(
            player_id=player_id,
            consumable_id=consumable_id,
            context=context,
            context_id=context_id,
        )

        if not success:
            return False, None, error

        # 获取道具配置
        consumable = self.get_consumable(consumable_id)
        if not consumable or not consumable.effects:
            return True, None, None  # 使用成功但无效果

        # 激活效果
        effect_config = consumable.effects[0]  # 取第一个效果
        active_effect = ActiveConsumableEffect(
            player_id=player_id,
            consumable_id=consumable_id,
            effect_type=effect_config.effect_type,
            value=effect_config.value,
            activated_at=datetime.now(),
            remaining_rounds=effect_config.duration_value
            if effect_config.duration_type == "rounds"
            else -1,
            context=context,
        )

        # 保存激活效果
        if player_id not in self.active_effects:
            self.active_effects[player_id] = []
        self.active_effects[player_id].append(active_effect)

        return True, active_effect, None

    def get_active_effects(
        self,
        player_id: str,
        effect_type: ConsumableEffect | None = None,
    ) -> list[ActiveConsumableEffect]:
        """
        获取玩家激活的效果

        Args:
            player_id: 玩家ID
            effect_type: 效果类型（None表示所有）

        Returns:
            激活的效果列表
        """
        effects = self.active_effects.get(player_id, [])

        # 过滤过期效果
        valid = [e for e in effects if not e.is_expired()]

        # 按类型过滤
        if effect_type:
            valid = [e for e in valid if e.effect_type == effect_type]

        return valid

    def has_active_effect(
        self,
        player_id: str,
        effect_type: ConsumableEffect,
    ) -> bool:
        """
        检查玩家是否有激活的效果

        Args:
            player_id: 玩家ID
            effect_type: 效果类型

        Returns:
            是否有激活效果
        """
        return len(self.get_active_effects(player_id, effect_type)) > 0

    def get_effect_value(
        self,
        player_id: str,
        effect_type: ConsumableEffect,
        default: float = 1.0,
    ) -> float:
        """
        获取效果数值（支持叠加）

        Args:
            player_id: 玩家ID
            effect_type: 效果类型
            default: 默认值

        Returns:
            效果数值
        """
        effects = self.get_active_effects(player_id, effect_type)
        if not effects:
            return default

        # 叠加效果（取最大值或累加，根据效果类型决定）
        if effect_type == ConsumableEffect.GOLD_MULTIPLIER:
            # 金币翻倍取最大
            return max(e.value for e in effects)
        elif effect_type == ConsumableEffect.EXP_MULTIPLIER:
            # 经验加成取最大
            return max(e.value for e in effects)
        elif effect_type == ConsumableEffect.RANK_PROTECT:
            # 段位保护返回1.0（已激活）
            return 1.0
        elif effect_type == ConsumableEffect.SHOP_REFRESH_DISCOUNT:
            # 刷新折扣累加
            return sum(e.value for e in effects)

        return default

    def consume_effect(
        self,
        player_id: str,
        effect_type: ConsumableEffect,
    ) -> bool:
        """
        消耗一次性效果（如段位保护）

        Args:
            player_id: 玩家ID
            effect_type: 效果类型

        Returns:
            是否成功消耗
        """
        effects = self.get_active_effects(player_id, effect_type)
        if not effects:
            return False

        # 移除一个效果
        effect = effects[0]
        if player_id in self.active_effects:
            self.active_effects[player_id] = [
                e for e in self.active_effects[player_id] if e != effect
            ]

        logger.info(
            f"Player {player_id} consumed {effect_type.value} effect from {effect.consumable_id}"
        )

        return True

    def decrement_rounds(self, player_id: str) -> None:
        """
        减少所有效果的剩余回合数

        Args:
            player_id: 玩家ID
        """
        if player_id not in self.active_effects:
            return

        # 过滤掉过期的效果
        self.active_effects[player_id] = [
            e for e in self.active_effects[player_id] if e.decrement_rounds()
        ]

    # ========================================================================
    # 特定效果辅助方法
    # ========================================================================

    def has_rank_protection(self, player_id: str) -> bool:
        """
        检查玩家是否有段位保护

        Args:
            player_id: 玩家ID

        Returns:
            是否有段位保护
        """
        return self.has_active_effect(player_id, ConsumableEffect.RANK_PROTECT)

    def use_rank_protection(self, player_id: str) -> bool:
        """
        使用段位保护（输掉对局时调用）

        Args:
            player_id: 玩家ID

        Returns:
            是否成功消耗
        """
        return self.consume_effect(player_id, ConsumableEffect.RANK_PROTECT)

    def get_gold_multiplier(self, player_id: str) -> float:
        """
        获取金币倍率

        Args:
            player_id: 玩家ID

        Returns:
            金币倍率（默认1.0）
        """
        return self.get_effect_value(player_id, ConsumableEffect.GOLD_MULTIPLIER, 1.0)

    def get_exp_multiplier(self, player_id: str) -> float:
        """
        获取经验倍率

        Args:
            player_id: 玩家ID

        Returns:
            经验倍率（默认1.0）
        """
        return self.get_effect_value(player_id, ConsumableEffect.EXP_MULTIPLIER, 1.0)

    def get_shop_discount(self, player_id: str) -> int:
        """
        获取商店刷新折扣

        Args:
            player_id: 玩家ID

        Returns:
            折扣金额（金币）
        """
        return int(self.get_effect_value(player_id, ConsumableEffect.SHOP_REFRESH_DISCOUNT, 0))

    def apply_rank_protect_card(
        self,
        player_id: str,
        match_id: str,
    ) -> tuple[bool, str | None]:
        """
        使用段位保护卡（自动使用）

        Args:
            player_id: 玩家ID
            match_id: 对局ID

        Returns:
            (是否成功, 错误信息)
        """
        # 查找段位保护卡
        rank_protect_items = self.get_consumables_by_type(ConsumableType.RANK_PROTECT)

        for item in rank_protect_items:
            if self.has_consumable(player_id, item.consumable_id):
                # 应用效果
                success, effect, error = self.apply_effect(
                    player_id=player_id,
                    consumable_id=item.consumable_id,
                    context="match",
                    context_id=match_id,
                )
                if success:
                    return True, None

        return False, "没有可用的段位保护卡"

    # ========================================================================
    # 历史记录
    # ========================================================================

    def get_usage_history(
        self,
        player_id: str,
        limit: int = 50,
    ) -> list[ConsumableUsage]:
        """
        获取道具使用历史

        Args:
            player_id: 玩家ID
            limit: 最大返回数量

        Returns:
            使用历史列表（按时间倒序）
        """
        history = self.usage_history.get(player_id, [])
        return sorted(history, key=lambda x: x.used_at, reverse=True)[:limit]

    # ========================================================================
    # 数据持久化（内存实现，实际应使用数据库）
    # ========================================================================

    def load_player_data(
        self,
        player_id: str,
        consumables_data: list[dict[str, Any]],
        effects_data: list[dict[str, Any]] | None = None,
    ) -> None:
        """
        加载玩家道具数据

        Args:
            player_id: 玩家ID
            consumables_data: 道具数据列表
            effects_data: 激活效果数据列表
        """
        # 加载道具
        self.player_consumables[player_id] = {}
        for data in consumables_data:
            pc = PlayerConsumable.from_dict(data)
            self.player_consumables[player_id][pc.consumable_id] = pc

        # 加载激活效果
        if effects_data:
            self.active_effects[player_id] = [
                ActiveConsumableEffect.from_dict(e) for e in effects_data
            ]

        logger.info(f"Loaded {len(consumables_data)} consumables for player {player_id}")

    def get_player_data(self, player_id: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """
        获取玩家道具数据（用于保存）

        Args:
            player_id: 玩家ID

        Returns:
            (道具数据列表, 激活效果数据列表)
        """
        consumables_data = [
            pc.to_dict() for pc in self.player_consumables.get(player_id, {}).values()
        ]
        effects_data = [e.to_dict() for e in self.active_effects.get(player_id, [])]
        return consumables_data, effects_data

    def clear_cache(self, player_id: str | None = None) -> None:
        """
        清除缓存

        Args:
            player_id: 玩家ID（None表示清除所有）
        """
        if player_id:
            self.player_consumables.pop(player_id, None)
            self.active_effects.pop(player_id, None)
            self.usage_history.pop(player_id, None)
        else:
            self.player_consumables.clear()
            self.active_effects.clear()
            self.usage_history.clear()


# 全局单例
_consumable_manager: ConsumableManager | None = None


def get_consumable_manager(config_path: str | None = None) -> ConsumableManager:
    """
    获取道具管理器单例

    Args:
        config_path: 配置文件路径

    Returns:
        道具管理器实例
    """
    global _consumable_manager
    if _consumable_manager is None:
        _consumable_manager = ConsumableManager(config_path)
    return _consumable_manager
