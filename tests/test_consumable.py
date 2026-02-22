"""
王者之奕 - 道具系统测试

测试道具系统的核心功能：
- 道具配置加载
- 道具管理器
- 道具获取、使用、购买
- 道具效果计算
"""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta
from typing import Dict, List

from src.server.consumable.models import (
    ActiveConsumableEffect,
    ConsumableEffect,
    ConsumableEffectConfig,
    ConsumableItem,
    ConsumablePrice,
    ConsumableRarity,
    ConsumableType,
    ConsumableUsage,
    PlayerConsumable,
)
from src.server.consumable.manager import ConsumableManager


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_rank_protect_card() -> ConsumableItem:
    """创建段位保护卡"""
    return ConsumableItem(
        consumable_id="rank_protect_card",
        name="段位保护卡",
        description="输掉对局不扣星",
        consumable_type=ConsumableType.RANK_PROTECT,
        rarity=ConsumableRarity.RARE,
        effects=[
            ConsumableEffectConfig(
                effect_type=ConsumableEffect.RANK_PROTECT,
                value=1.0,
                duration_type="instant",
                duration_value=1,
            )
        ],
        price=ConsumablePrice(gold=500, diamond=50),
        max_stack=10,
        auto_use=True,
    )


@pytest.fixture
def sample_gold_double_card() -> ConsumableItem:
    """创建双倍金币卡"""
    return ConsumableItem(
        consumable_id="gold_double_card",
        name="双倍金币卡",
        description="金币翻倍",
        consumable_type=ConsumableType.GOLD_DOUBLE,
        rarity=ConsumableRarity.RARE,
        effects=[
            ConsumableEffectConfig(
                effect_type=ConsumableEffect.GOLD_MULTIPLIER,
                value=2.0,
                duration_type="rounds",
                duration_value=3,
            )
        ],
        price=ConsumablePrice(gold=300, diamond=30),
        max_stack=20,
    )


@pytest.fixture
def sample_exp_boost_card() -> ConsumableItem:
    """创建经验加成卡"""
    return ConsumableItem(
        consumable_id="exp_boost_card",
        name="经验加成卡",
        description="经验+50%",
        consumable_type=ConsumableType.EXP_BOOST,
        rarity=ConsumableRarity.COMMON,
        effects=[
            ConsumableEffectConfig(
                effect_type=ConsumableEffect.EXP_MULTIPLIER,
                value=1.5,
                duration_type="rounds",
                duration_value=5,
            )
        ],
        price=ConsumablePrice(gold=200, diamond=20),
        max_stack=30,
    )


@pytest.fixture
def sample_shop_discount_card() -> ConsumableItem:
    """创建刷新折扣卡"""
    return ConsumableItem(
        consumable_id="shop_discount_card",
        name="刷新折扣卡",
        description="商店刷新-1金币",
        consumable_type=ConsumableType.SHOP_DISCOUNT,
        rarity=ConsumableRarity.COMMON,
        effects=[
            ConsumableEffectConfig(
                effect_type=ConsumableEffect.SHOP_REFRESH_DISCOUNT,
                value=1.0,
                duration_type="rounds",
                duration_value=3,
            )
        ],
        price=ConsumablePrice(gold=150, diamond=15),
        max_stack=30,
    )


@pytest.fixture
def empty_manager() -> ConsumableManager:
    """创建空的道具管理器"""
    return ConsumableManager()


@pytest.fixture
def manager_with_items(
    sample_rank_protect_card: ConsumableItem,
    sample_gold_double_card: ConsumableItem,
    sample_exp_boost_card: ConsumableItem,
    sample_shop_discount_card: ConsumableItem,
) -> ConsumableManager:
    """创建带有道具配置的管理器"""
    manager = ConsumableManager()
    manager.consumables = {
        sample_rank_protect_card.consumable_id: sample_rank_protect_card,
        sample_gold_double_card.consumable_id: sample_gold_double_card,
        sample_exp_boost_card.consumable_id: sample_exp_boost_card,
        sample_shop_discount_card.consumable_id: sample_shop_discount_card,
    }
    return manager


# ============================================================================
# 模型测试
# ============================================================================

class TestConsumableModels:
    """道具模型测试"""
    
    def test_consumable_type_display_name(self):
        """测试道具类型显示名称"""
        assert ConsumableType.get_display_name("rank_protect") == "段位保护卡"
        assert ConsumableType.get_display_name("gold_double") == "双倍金币卡"
        assert ConsumableType.get_display_name("exp_boost") == "经验加成卡"
        assert ConsumableType.get_display_name("shop_discount") == "刷新折扣卡"
        assert ConsumableType.get_display_name("unknown") == "未知道具"
    
    def test_consumable_type_description(self):
        """测试道具类型描述"""
        assert "不扣星" in ConsumableType.get_description("rank_protect")
        assert "翻倍" in ConsumableType.get_description("gold_double")
        assert "+50%" in ConsumableType.get_description("exp_boost")
        assert "-1" in ConsumableType.get_description("shop_discount")
    
    def test_consumable_effect_value(self):
        """测试道具效果数值"""
        assert ConsumableEffect.get_effect_value("rank_protect") == 1.0
        assert ConsumableEffect.get_effect_value("gold_multiplier") == 2.0
        assert ConsumableEffect.get_effect_value("exp_multiplier") == 1.5
        assert ConsumableEffect.get_effect_value("shop_refresh_discount") == 1.0
    
    def test_consumable_rarity_color(self):
        """测试道具稀有度颜色"""
        assert ConsumableRarity.get_color("common") == "#FFFFFF"
        assert ConsumableRarity.get_color("rare") == "#1EFF00"
        assert ConsumableRarity.get_color("epic") == "#A335EE"
    
    def test_consumable_price_to_dict(self):
        """测试道具价格序列化"""
        price = ConsumablePrice(gold=500, diamond=50)
        data = price.to_dict()
        
        assert data["gold"] == 500
        assert data["diamond"] == 50
    
    def test_consumable_price_from_dict(self):
        """测试道具价格反序列化"""
        data = {"gold": 300, "diamond": 30}
        price = ConsumablePrice.from_dict(data)
        
        assert price.gold == 300
        assert price.diamond == 30
    
    def test_consumable_item_to_dict(self, sample_rank_protect_card: ConsumableItem):
        """测试道具序列化"""
        data = sample_rank_protect_card.to_dict()
        
        assert data["consumable_id"] == "rank_protect_card"
        assert data["name"] == "段位保护卡"
        assert data["consumable_type"] == "rank_protect"
        assert data["rarity"] == "rare"
        assert len(data["effects"]) == 1
        assert data["auto_use"] is True
    
    def test_consumable_item_from_dict(self):
        """测试道具反序列化"""
        data = {
            "consumable_id": "test_card",
            "name": "测试道具",
            "consumable_type": "rank_protect",
            "rarity": "rare",
            "effects": [
                {
                    "effect_type": "rank_protect",
                    "value": 1.0,
                    "duration_type": "instant",
                    "duration_value": 1,
                }
            ],
            "price": {"gold": 100},
            "auto_use": True,
        }
        
        item = ConsumableItem.from_dict(data)
        
        assert item.consumable_id == "test_card"
        assert item.name == "测试道具"
        assert item.consumable_type == ConsumableType.RANK_PROTECT
        assert item.rarity == ConsumableRarity.RARE
        assert len(item.effects) == 1
        assert item.price.gold == 100
        assert item.auto_use is True
    
    def test_player_consumable_is_expired(self):
        """测试玩家道具过期检查"""
        # 未过期
        pc1 = PlayerConsumable(
            player_id="player1",
            consumable_id="test",
            quantity=1,
            acquired_at=datetime.now(),
            expire_at=datetime.now() + timedelta(days=1),
        )
        assert pc1.is_expired() is False
        
        # 已过期
        pc2 = PlayerConsumable(
            player_id="player1",
            consumable_id="test",
            quantity=1,
            acquired_at=datetime.now() - timedelta(days=2),
            expire_at=datetime.now() - timedelta(days=1),
        )
        assert pc2.is_expired() is True
        
        # 无过期时间
        pc3 = PlayerConsumable(
            player_id="player1",
            consumable_id="test",
            quantity=1,
            acquired_at=datetime.now(),
        )
        assert pc3.is_expired() is False
    
    def test_player_consumable_use_quantity(self):
        """测试玩家道具使用数量"""
        pc = PlayerConsumable(
            player_id="player1",
            consumable_id="test",
            quantity=5,
            acquired_at=datetime.now(),
        )
        
        # 使用1个
        assert pc.use_quantity(1) is True
        assert pc.quantity == 4
        
        # 使用多个
        assert pc.use_quantity(2) is True
        assert pc.quantity == 2
        
        # 数量不足
        assert pc.use_quantity(3) is False
        assert pc.quantity == 2


# ============================================================================
# 管理器测试
# ============================================================================

class TestConsumableManager:
    """道具管理器测试"""
    
    def test_get_consumable(self, manager_with_items: ConsumableManager):
        """测试获取道具配置"""
        item = manager_with_items.get_consumable("rank_protect_card")
        
        assert item is not None
        assert item.name == "段位保护卡"
    
    def test_get_consumable_not_found(self, empty_manager: ConsumableManager):
        """测试获取不存在的道具"""
        item = empty_manager.get_consumable("not_exist")
        assert item is None
    
    def test_get_all_consumables(self, manager_with_items: ConsumableManager):
        """测试获取所有道具"""
        items = manager_with_items.get_all_consumables()
        
        assert len(items) == 4
    
    def test_get_consumables_by_type(self, manager_with_items: ConsumableManager):
        """测试按类型获取道具"""
        items = manager_with_items.get_consumables_by_type(ConsumableType.RANK_PROTECT)
        
        assert len(items) == 1
        assert items[0].consumable_id == "rank_protect_card"
    
    def test_get_consumables_by_rarity(self, manager_with_items: ConsumableManager):
        """测试按稀有度获取道具"""
        common_items = manager_with_items.get_consumables_by_rarity(ConsumableRarity.COMMON)
        rare_items = manager_with_items.get_consumables_by_rarity(ConsumableRarity.RARE)
        
        assert len(common_items) == 2
        assert len(rare_items) == 2
    
    def test_add_consumable(self, manager_with_items: ConsumableManager):
        """测试添加道具"""
        player_id = "test_player"
        
        pc, error = manager_with_items.add_consumable(
            player_id=player_id,
            consumable_id="rank_protect_card",
            quantity=2,
            acquire_type="reward",
        )
        
        assert error is None
        assert pc is not None
        assert pc.quantity == 2
        assert pc.acquire_type == "reward"
    
    def test_add_consumable_invalid_id(self, manager_with_items: ConsumableManager):
        """测试添加不存在的道具"""
        pc, error = manager_with_items.add_consumable(
            player_id="test_player",
            consumable_id="invalid_id",
            quantity=1,
        )
        
        assert pc is None
        assert error == "道具不存在"
    
    def test_add_consumable_with_expiry(self, manager_with_items: ConsumableManager):
        """测试添加有过期时间的道具"""
        player_id = "test_player"
        
        pc, error = manager_with_items.add_consumable(
            player_id=player_id,
            consumable_id="gold_double_card",
            quantity=1,
            expire_days=7,
        )
        
        assert error is None
        assert pc is not None
        assert pc.expire_at is not None
    
    def test_use_consumable(self, manager_with_items: ConsumableManager):
        """测试使用道具"""
        player_id = "test_player"
        
        # 先添加道具
        manager_with_items.add_consumable(
            player_id=player_id,
            consumable_id="gold_double_card",
            quantity=3,
        )
        
        # 使用道具
        success, usage, error = manager_with_items.use_consumable(
            player_id=player_id,
            consumable_id="gold_double_card",
            quantity=1,
            context="match",
            context_id="match_001",
        )
        
        assert success is True
        assert usage is not None
        assert usage.quantity == 1
        assert error is None
        
        # 检查数量减少
        pc = manager_with_items.get_player_consumable(player_id, "gold_double_card")
        assert pc.quantity == 2
    
    def test_use_consumable_insufficient(self, manager_with_items: ConsumableManager):
        """测试使用数量不足的道具"""
        player_id = "test_player"
        
        # 先添加1个道具
        manager_with_items.add_consumable(
            player_id=player_id,
            consumable_id="rank_protect_card",
            quantity=1,
        )
        
        # 尝试使用2个
        success, usage, error = manager_with_items.use_consumable(
            player_id=player_id,
            consumable_id="rank_protect_card",
            quantity=2,
        )
        
        assert success is False
        assert "不足" in error
    
    def test_buy_consumable_with_gold(self, manager_with_items: ConsumableManager):
        """测试用金币购买道具"""
        player_id = "test_player"
        
        pc, currency, cost, error = manager_with_items.buy_consumable(
            player_id=player_id,
            consumable_id="rank_protect_card",
            gold=1000,
            diamond=0,
            quantity=1,
            use_currency="gold",
        )
        
        assert error is None
        assert pc is not None
        assert currency == "gold"
        assert cost == 500
    
    def test_buy_consumable_insufficient_gold(self, manager_with_items: ConsumableManager):
        """测试金币不足购买道具"""
        player_id = "test_player"
        
        pc, currency, cost, error = manager_with_items.buy_consumable(
            player_id=player_id,
            consumable_id="rank_protect_card",
            gold=100,  # 不够
            diamond=0,
            quantity=1,
            use_currency="gold",
        )
        
        assert pc is None
        assert "不足" in error
    
    def test_apply_effect(self, manager_with_items: ConsumableManager):
        """测试应用道具效果"""
        player_id = "test_player"
        
        # 添加道具
        manager_with_items.add_consumable(
            player_id=player_id,
            consumable_id="gold_double_card",
            quantity=1,
        )
        
        # 应用效果
        success, effect, error = manager_with_items.apply_effect(
            player_id=player_id,
            consumable_id="gold_double_card",
            context="match",
        )
        
        assert success is True
        assert effect is not None
        assert effect.effect_type == ConsumableEffect.GOLD_MULTIPLIER
        assert effect.value == 2.0
        assert effect.remaining_rounds == 3
    
    def test_get_active_effects(self, manager_with_items: ConsumableManager):
        """测试获取激活效果"""
        player_id = "test_player"
        
        # 添加并使用道具
        manager_with_items.add_consumable(
            player_id=player_id,
            consumable_id="gold_double_card",
            quantity=1,
        )
        manager_with_items.add_consumable(
            player_id=player_id,
            consumable_id="exp_boost_card",
            quantity=1,
        )
        
        manager_with_items.apply_effect(
            player_id=player_id,
            consumable_id="gold_double_card",
        )
        manager_with_items.apply_effect(
            player_id=player_id,
            consumable_id="exp_boost_card",
        )
        
        # 获取所有效果
        effects = manager_with_items.get_active_effects(player_id)
        assert len(effects) == 2
        
        # 获取特定类型效果
        gold_effects = manager_with_items.get_active_effects(
            player_id,
            ConsumableEffect.GOLD_MULTIPLIER,
        )
        assert len(gold_effects) == 1
    
    def test_get_effect_value(self, manager_with_items: ConsumableManager):
        """测试获取效果数值"""
        player_id = "test_player"
        
        # 无效果时返回默认值
        multiplier = manager_with_items.get_gold_multiplier(player_id)
        assert multiplier == 1.0
        
        # 添加并使用双倍金币卡
        manager_with_items.add_consumable(
            player_id=player_id,
            consumable_id="gold_double_card",
            quantity=1,
        )
        manager_with_items.apply_effect(
            player_id=player_id,
            consumable_id="gold_double_card",
        )
        
        # 获取金币倍率
        multiplier = manager_with_items.get_gold_multiplier(player_id)
        assert multiplier == 2.0
    
    def test_has_rank_protection(self, manager_with_items: ConsumableManager):
        """测试段位保护检查"""
        player_id = "test_player"
        
        # 无保护
        assert manager_with_items.has_rank_protection(player_id) is False
        
        # 添加并使用保护卡
        manager_with_items.add_consumable(
            player_id=player_id,
            consumable_id="rank_protect_card",
            quantity=1,
        )
        manager_with_items.apply_effect(
            player_id=player_id,
            consumable_id="rank_protect_card",
        )
        
        # 有保护
        assert manager_with_items.has_rank_protection(player_id) is True
    
    def test_use_rank_protection(self, manager_with_items: ConsumableManager):
        """测试使用段位保护"""
        player_id = "test_player"
        
        # 添加并使用保护卡
        manager_with_items.add_consumable(
            player_id=player_id,
            consumable_id="rank_protect_card",
            quantity=1,
        )
        manager_with_items.apply_effect(
            player_id=player_id,
            consumable_id="rank_protect_card",
        )
        
        # 确认有保护
        assert manager_with_items.has_rank_protection(player_id) is True
        
        # 使用保护
        success = manager_with_items.use_rank_protection(player_id)
        assert success is True
        
        # 确认保护已消耗
        assert manager_with_items.has_rank_protection(player_id) is False
    
    def test_get_shop_discount(self, manager_with_items: ConsumableManager):
        """测试商店刷新折扣"""
        player_id = "test_player"
        
        # 无折扣
        assert manager_with_items.get_shop_discount(player_id) == 0
        
        # 添加并使用折扣卡
        manager_with_items.add_consumable(
            player_id=player_id,
            consumable_id="shop_discount_card",
            quantity=1,
        )
        manager_with_items.apply_effect(
            player_id=player_id,
            consumable_id="shop_discount_card",
        )
        
        # 有折扣
        assert manager_with_items.get_shop_discount(player_id) == 1
    
    def test_decrement_rounds(self, manager_with_items: ConsumableManager):
        """测试减少回合数"""
        player_id = "test_player"
        
        # 添加并使用双倍金币卡（3回合）
        manager_with_items.add_consumable(
            player_id=player_id,
            consumable_id="gold_double_card",
            quantity=1,
        )
        manager_with_items.apply_effect(
            player_id=player_id,
            consumable_id="gold_double_card",
        )
        
        # 确认有3回合
        effects = manager_with_items.get_active_effects(player_id)
        assert effects[0].remaining_rounds == 3
        
        # 减少回合
        manager_with_items.decrement_rounds(player_id)
        effects = manager_with_items.get_active_effects(player_id)
        assert effects[0].remaining_rounds == 2
        
        # 继续减少直到过期
        manager_with_items.decrement_rounds(player_id)
        manager_with_items.decrement_rounds(player_id)
        effects = manager_with_items.get_active_effects(player_id)
        assert len(effects) == 0  # 效果已过期移除
    
    def test_get_usage_history(self, manager_with_items: ConsumableManager):
        """测试获取使用历史"""
        player_id = "test_player"
        
        # 添加并使用道具
        manager_with_items.add_consumable(
            player_id=player_id,
            consumable_id="gold_double_card",
            quantity=3,
        )
        manager_with_items.use_consumable(
            player_id=player_id,
            consumable_id="gold_double_card",
            quantity=1,
        )
        manager_with_items.use_consumable(
            player_id=player_id,
            consumable_id="gold_double_card",
            quantity=1,
        )
        
        # 获取历史
        history = manager_with_items.get_usage_history(player_id)
        
        assert len(history) == 2
        assert history[0].consumable_id == "gold_double_card"
    
    def test_max_stack(self, manager_with_items: ConsumableManager):
        """测试最大堆叠数量"""
        player_id = "test_player"
        
        # 添加超过最大堆叠的道具（段位保护卡max_stack=10）
        pc1, _ = manager_with_items.add_consumable(
            player_id=player_id,
            consumable_id="rank_protect_card",
            quantity=8,
        )
        assert pc1.quantity == 8
        
        # 再添加5个，应该只增加2个
        pc2, _ = manager_with_items.add_consumable(
            player_id=player_id,
            consumable_id="rank_protect_card",
            quantity=5,
        )
        assert pc2.quantity == 10  # 到达最大堆叠


# ============================================================================
# 集成测试
# ============================================================================

class TestConsumableIntegration:
    """道具系统集成测试"""
    
    def test_full_rank_protect_flow(self, manager_with_items: ConsumableManager):
        """测试段位保护卡完整流程"""
        player_id = "test_player"
        
        # 1. 购买保护卡
        pc, currency, cost, error = manager_with_items.buy_consumable(
            player_id=player_id,
            consumable_id="rank_protect_card",
            gold=1000,
            diamond=0,
            quantity=2,
        )
        
        assert error is None
        assert pc.quantity == 2
        
        # 2. 检查有保护卡
        assert manager_with_items.has_consumable(player_id, "rank_protect_card", 2)
        
        # 3. 使用保护卡
        success, effect, error = manager_with_items.apply_effect(
            player_id=player_id,
            consumable_id="rank_protect_card",
            context="match",
            context_id="match_001",
        )
        
        assert success is True
        assert manager_with_items.has_rank_protection(player_id) is True
        
        # 4. 输掉对局，消耗保护
        success = manager_with_items.use_rank_protection(player_id)
        assert success is True
        assert manager_with_items.has_rank_protection(player_id) is False
        
        # 5. 检查剩余数量
        remaining = manager_with_items.get_consumable_quantity(
            player_id, "rank_protect_card"
        )
        assert remaining == 1
    
    def test_multiple_effects_stacking(self, manager_with_items: ConsumableManager):
        """测试多个效果叠加"""
        player_id = "test_player"
        
        # 添加并使用金币卡和经验卡
        manager_with_items.add_consumable(
            player_id=player_id,
            consumable_id="gold_double_card",
            quantity=1,
        )
        manager_with_items.add_consumable(
            player_id=player_id,
            consumable_id="exp_boost_card",
            quantity=1,
        )
        
        manager_with_items.apply_effect(
            player_id=player_id,
            consumable_id="gold_double_card",
        )
        manager_with_items.apply_effect(
            player_id=player_id,
            consumable_id="exp_boost_card",
        )
        
        # 验证两个效果都生效
        assert manager_with_items.get_gold_multiplier(player_id) == 2.0
        assert manager_with_items.get_exp_multiplier(player_id) == 1.5
        
        # 获取所有效果
        effects = manager_with_items.get_active_effects(player_id)
        assert len(effects) == 2
    
    def test_data_persistence(self, manager_with_items: ConsumableManager):
        """测试数据持久化"""
        player_id = "test_player"
        
        # 添加道具
        manager_with_items.add_consumable(
            player_id=player_id,
            consumable_id="gold_double_card",
            quantity=3,
        )
        manager_with_items.apply_effect(
            player_id=player_id,
            consumable_id="gold_double_card",
        )
        
        # 获取数据
        consumables_data, effects_data = manager_with_items.get_player_data(player_id)
        
        assert len(consumables_data) == 1
        assert len(effects_data) == 1
        
        # 清除缓存
        manager_with_items.clear_cache(player_id)
        
        # 重新加载
        manager_with_items.load_player_data(player_id, consumables_data, effects_data)
        
        # 验证数据恢复
        pc = manager_with_items.get_player_consumable(player_id, "gold_double_card")
        assert pc is not None
        # apply_effect 会消耗1个道具
        assert pc.quantity == 2
        
        effects = manager_with_items.get_active_effects(player_id)
        assert len(effects) == 1


# ============================================================================
# 运行测试
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
