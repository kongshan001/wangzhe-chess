"""
王者之奕 - 交易系统测试

本模块测试交易系统的功能：
- 交易请求创建
- 交易接受/拒绝
- 交易取消
- 交易确认
- 交易执行
- 交易税计算
- 每日交易限制
"""

from datetime import datetime, timedelta

import pytest

from src.server.trading.manager import TradingManager
from src.server.trading.models import (
    MAX_DAILY_TRADES,
    MAX_GOLD_PER_TRADE,
    TRADE_EXPIRE_HOURS,
    TRADE_TAX_RATE,
    TradeHistory,
    TradeItem,
    TradeItemType,
    TradeOffer,
    TradeRequest,
    TradeResult,
    TradeStatus,
)


class TestTradeItem:
    """交易物品测试"""

    def test_create_trade_item(self):
        """测试创建交易物品"""
        item = TradeItem(
            item_type=TradeItemType.HERO_SHARD,
            item_id="hero_001",
            item_name="亚瑟",
            quantity=100,
        )

        assert item.item_type == TradeItemType.HERO_SHARD
        assert item.item_id == "hero_001"
        assert item.item_name == "亚瑟"
        assert item.quantity == 100

    def test_trade_item_to_dict(self):
        """测试交易物品转字典"""
        item = TradeItem(
            item_type=TradeItemType.GOLD,
            item_id="gold",
            item_name="金币",
            quantity=1000,
        )

        data = item.to_dict()
        assert data["item_type"] == "gold"
        assert data["item_id"] == "gold"
        assert data["quantity"] == 1000

    def test_trade_item_from_dict(self):
        """测试从字典创建交易物品"""
        data = {
            "item_type": "equipment",
            "item_id": "equip_001",
            "item_name": "破军",
            "quantity": 1,
        }

        item = TradeItem.from_dict(data)
        assert item.item_type == TradeItemType.EQUIPMENT
        assert item.item_id == "equip_001"
        assert item.quantity == 1

    def test_calculate_tax_gold(self):
        """测试金币税额计算"""
        item = TradeItem(
            item_type=TradeItemType.GOLD,
            item_id="gold",
            quantity=1000,
        )

        tax = item.calculate_tax()
        expected = int(1000 * TRADE_TAX_RATE)  # 10% = 100
        assert tax == expected

    def test_calculate_tax_non_gold(self):
        """测试非金币物品税额计算"""
        item = TradeItem(
            item_type=TradeItemType.HERO_SHARD,
            item_id="hero_001",
            quantity=100,
        )

        tax = item.calculate_tax()
        # 非金币物品简单估算
        assert tax >= 1


class TestTradeOffer:
    """交易报价测试"""

    def test_create_trade_offer(self):
        """测试创建交易报价"""
        items = [
            TradeItem(item_type=TradeItemType.HERO_SHARD, item_id="hero_001", quantity=50),
            TradeItem(item_type=TradeItemType.GOLD, item_id="gold", quantity=500),
        ]

        offer = TradeOffer(
            player_id="player_001",
            player_name="玩家1",
            items=items,
        )

        assert offer.player_id == "player_001"
        assert len(offer.items) == 2
        assert not offer.confirmed

    def test_get_gold_amount(self):
        """测试获取金币数量"""
        items = [
            TradeItem(item_type=TradeItemType.HERO_SHARD, item_id="hero_001", quantity=50),
            TradeItem(item_type=TradeItemType.GOLD, item_id="gold", quantity=500),
        ]

        offer = TradeOffer(
            player_id="player_001",
            items=items,
        )

        assert offer.get_gold_amount() == 500

    def test_confirm_offer(self):
        """测试确认报价"""
        offer = TradeOffer(
            player_id="player_001",
            items=[],
        )

        assert not offer.confirmed
        offer.confirm()
        assert offer.confirmed
        assert offer.confirmed_at is not None


class TestTradeRequest:
    """交易请求测试"""

    def test_create_trade_request(self):
        """测试创建交易请求"""
        sender_offer = TradeOffer(
            player_id="player_001",
            player_name="玩家1",
            items=[
                TradeItem(item_type=TradeItemType.HERO_SHARD, item_id="hero_001", quantity=50),
            ],
        )

        request = TradeRequest(
            trade_id="trade_001",
            sender_offer=sender_offer,
            message="想交换亚瑟碎片",
        )

        assert request.trade_id == "trade_001"
        assert request.sender_id == "player_001"
        assert request.status == TradeStatus.PENDING
        assert request.message == "想交换亚瑟碎片"
        assert not request.is_expired()

    def test_trade_request_accept(self):
        """测试接受交易请求"""
        sender_offer = TradeOffer(
            player_id="player_001",
            items=[],
        )

        request = TradeRequest(
            trade_id="trade_001",
            sender_offer=sender_offer,
            receiver_id="player_002",  # 设置接收方ID
        )

        receiver_offer = TradeOffer(
            player_id="player_002",
            items=[
                TradeItem(item_type=TradeItemType.GOLD, item_id="gold", quantity=100),
            ],
        )

        request.accept(receiver_offer)

        assert request.status == TradeStatus.ACCEPTED
        assert request.receiver_id == "player_002"
        assert request.receiver_offer.player_id == "player_002"

    def test_trade_request_reject(self):
        """测试拒绝交易请求"""
        sender_offer = TradeOffer(
            player_id="player_001",
            items=[],
        )

        request = TradeRequest(
            trade_id="trade_001",
            sender_offer=sender_offer,
        )

        request.reject("价格不合适")

        assert request.status == TradeStatus.REJECTED
        assert request.reject_reason == "价格不合适"

    def test_trade_request_cancel(self):
        """测试取消交易请求"""
        sender_offer = TradeOffer(
            player_id="player_001",
            items=[],
        )

        request = TradeRequest(
            trade_id="trade_001",
            sender_offer=sender_offer,
        )

        request.cancel()

        assert request.status == TradeStatus.CANCELLED

    def test_trade_request_confirm_both(self):
        """测试双方确认"""
        sender_offer = TradeOffer(
            player_id="player_001",
            items=[],
        )

        receiver_offer = TradeOffer(
            player_id="player_002",
            items=[],
        )

        request = TradeRequest(
            trade_id="trade_001",
            sender_offer=sender_offer,
            receiver_offer=receiver_offer,
            status=TradeStatus.ACCEPTED,
        )

        # 发起方确认
        request.confirm_sender()
        assert request.sender_offer.confirmed
        assert not request.is_both_confirmed()

        # 接收方确认
        request.confirm_receiver()
        assert request.receiver_offer.confirmed
        assert request.is_both_confirmed()

    def test_trade_request_expire(self):
        """测试交易过期"""
        sender_offer = TradeOffer(
            player_id="player_001",
            items=[],
        )

        # 创建一个已过期的交易
        request = TradeRequest(
            trade_id="trade_001",
            sender_offer=sender_offer,
            created_at=datetime.now() - timedelta(hours=TRADE_EXPIRE_HOURS + 1),
            expires_at=datetime.now() - timedelta(hours=1),
        )

        assert request.is_expired()


class TestTradingManager:
    """交易管理器测试"""

    @pytest.fixture
    def manager(self):
        """创建交易管理器实例"""
        manager = TradingManager()
        # 设置玩家库存
        manager.set_player_inventory(
            player_id="player_001",
            shards={"hero_001": 200, "hero_002": 50},
            equipment={"equip_001": 5},
            consumables={"item_001": 10},
            gold=10000,
        )
        manager.set_player_inventory(
            player_id="player_002",
            shards={"hero_003": 100},
            equipment={},
            consumables={"item_002": 20},
            gold=5000,
        )
        return manager

    def test_create_trade_request_success(self, manager):
        """测试成功创建交易请求"""
        request, error = manager.create_trade_request(
            sender_id="player_001",
            sender_name="玩家1",
            receiver_id="player_002",
            items=[
                {
                    "item_type": "hero_shard",
                    "item_id": "hero_001",
                    "item_name": "亚瑟",
                    "quantity": 50,
                },
            ],
            message="交换碎片",
        )

        assert request is not None
        assert error is None
        assert request.sender_id == "player_001"
        assert request.status == TradeStatus.PENDING

    def test_create_trade_request_self_trade(self, manager):
        """测试不能和自己交易"""
        request, error = manager.create_trade_request(
            sender_id="player_001",
            sender_name="玩家1",
            receiver_id="player_001",
            items=[],
        )

        assert request is None
        assert "自己" in error

    def test_create_trade_request_daily_limit(self, manager):
        """测试每日交易限制"""
        # 先用完今日交易次数（每次交易需要有效物品）
        # 使用不同的接收者来避免"已有未完成的交易"检查
        for i in range(MAX_DAILY_TRADES):
            receiver_id = f"player_{100 + i}"  # 不同的接收者
            # 为每个接收者设置库存
            manager.set_player_inventory(
                player_id=receiver_id,
                shards={},
                equipment={},
                consumables={},
                gold=5000,
            )

            request, error = manager.create_trade_request(
                sender_id="player_001",
                sender_name="玩家1",
                receiver_id=receiver_id,
                items=[
                    {
                        "item_type": "hero_shard",
                        "item_id": "hero_001",
                        "item_name": "亚瑟",
                        "quantity": 1,
                    },
                ],
            )
            if error:
                print(f"Error at iteration {i}: {error}")
            assert request is not None, f"Failed at iteration {i}: {error}"

        # 再尝试创建应该失败
        request, error = manager.create_trade_request(
            sender_id="player_001",
            sender_name="玩家1",
            receiver_id="player_999",  # 新的接收者
            items=[
                {
                    "item_type": "hero_shard",
                    "item_id": "hero_001",
                    "item_name": "亚瑟",
                    "quantity": 1,
                },
            ],
        )

        assert request is None
        assert "上限" in error

    def test_create_trade_request_gold_limit(self, manager):
        """测试单笔金币限制"""
        request, error = manager.create_trade_request(
            sender_id="player_001",
            sender_name="玩家1",
            receiver_id="player_002",
            items=[
                {"item_type": "gold", "item_id": "gold", "quantity": MAX_GOLD_PER_TRADE + 1},
            ],
        )

        assert request is None
        assert "金币" in error

    def test_create_trade_request_insufficient_item(self, manager):
        """测试物品不足"""
        request, error = manager.create_trade_request(
            sender_id="player_001",
            sender_name="玩家1",
            receiver_id="player_002",
            items=[
                {"item_type": "hero_shard", "item_id": "hero_001", "quantity": 99999},
            ],
        )

        assert request is None
        assert "不足" in error

    def test_accept_trade_request(self, manager):
        """测试接受交易请求"""
        # 先创建交易
        request, _ = manager.create_trade_request(
            sender_id="player_001",
            sender_name="玩家1",
            receiver_id="player_002",
            items=[
                {"item_type": "hero_shard", "item_id": "hero_001", "quantity": 50},
            ],
        )

        # 接受交易
        accepted, error = manager.accept_trade(
            trade_id=request.trade_id,
            receiver_id="player_002",
            receiver_name="玩家2",
            items=[
                {"item_type": "gold", "item_id": "gold", "quantity": 500},
            ],
        )

        assert accepted is not None
        assert error is None
        assert accepted.status == TradeStatus.ACCEPTED
        assert accepted.receiver_id == "player_002"

    def test_reject_trade_request(self, manager):
        """测试拒绝交易请求"""
        request, _ = manager.create_trade_request(
            sender_id="player_001",
            sender_name="玩家1",
            receiver_id="player_002",
            items=[],
        )

        success, error = manager.reject_trade(
            trade_id=request.trade_id,
            player_id="player_002",
            reason="不需要",
        )

        assert success
        assert error is None

        # 验证状态
        trade = manager.get_trade(request.trade_id)
        assert trade.status == TradeStatus.REJECTED

    def test_cancel_trade(self, manager):
        """测试取消交易"""
        request, _ = manager.create_trade_request(
            sender_id="player_001",
            sender_name="玩家1",
            receiver_id="player_002",
            items=[],
        )

        # 只有发起方可以取消
        success, error = manager.cancel_trade(
            trade_id=request.trade_id,
            player_id="player_001",
        )

        assert success
        assert error is None

        trade = manager.get_trade(request.trade_id)
        assert trade.status == TradeStatus.CANCELLED

    def test_cancel_trade_not_sender(self, manager):
        """测试非发起方不能取消"""
        request, _ = manager.create_trade_request(
            sender_id="player_001",
            sender_name="玩家1",
            receiver_id="player_002",
            items=[],
        )

        success, error = manager.cancel_trade(
            trade_id=request.trade_id,
            player_id="player_002",
        )

        assert not success
        assert "发起方" in error

    def test_confirm_trade(self, manager):
        """测试确认交易"""
        # 创建并接受交易
        request, _ = manager.create_trade_request(
            sender_id="player_001",
            sender_name="玩家1",
            receiver_id="player_002",
            items=[{"item_type": "hero_shard", "item_id": "hero_001", "quantity": 50}],
        )

        manager.accept_trade(
            trade_id=request.trade_id,
            receiver_id="player_002",
            receiver_name="玩家2",
            items=[{"item_type": "gold", "item_id": "gold", "quantity": 500}],
        )

        # 发起方确认
        confirmed, error = manager.confirm_trade(
            trade_id=request.trade_id,
            player_id="player_001",
        )

        assert confirmed is not None
        assert confirmed.sender_offer.confirmed
        assert not confirmed.is_both_confirmed()

        # 接收方确认
        confirmed, error = manager.confirm_trade(
            trade_id=request.trade_id,
            player_id="player_002",
        )

        assert confirmed is not None
        assert confirmed.is_both_confirmed()

    def test_execute_trade(self, manager):
        """测试执行交易"""
        # 完整流程：创建 -> 接受 -> 确认 -> 执行
        request, _ = manager.create_trade_request(
            sender_id="player_001",
            sender_name="玩家1",
            receiver_id="player_002",
            items=[{"item_type": "gold", "item_id": "gold", "quantity": 1000}],
        )

        manager.accept_trade(
            trade_id=request.trade_id,
            receiver_id="player_002",
            receiver_name="玩家2",
            items=[{"item_type": "hero_shard", "item_id": "hero_003", "quantity": 100}],
        )

        manager.confirm_trade(trade_id=request.trade_id, player_id="player_001")
        manager.confirm_trade(trade_id=request.trade_id, player_id="player_002")

        # 执行交易
        result = manager.execute_trade(trade_id=request.trade_id)

        assert result.success
        assert result.tax_collected > 0
        assert len(result.sender_received) > 0
        assert len(result.receiver_received) > 0

    def test_execute_trade_not_confirmed(self, manager):
        """测试未确认时不能执行"""
        request, _ = manager.create_trade_request(
            sender_id="player_001",
            sender_name="玩家1",
            receiver_id="player_002",
            items=[{"item_type": "gold", "item_id": "gold", "quantity": 1000}],
        )

        manager.accept_trade(
            trade_id=request.trade_id,
            receiver_id="player_002",
            receiver_name="玩家2",
            items=[{"item_type": "hero_shard", "item_id": "hero_003", "quantity": 100}],
        )

        # 不确认直接执行
        result = manager.execute_trade(trade_id=request.trade_id)

        assert not result.success
        assert "确认" in result.error_message

    def test_get_trade_history(self, manager):
        """测试获取交易历史"""
        history = manager.get_trade_history("player_001")

        assert history.player_id == "player_001"
        assert history.total_trades >= 0

    def test_get_pending_trades(self, manager):
        """测试获取待处理交易"""
        request, _ = manager.create_trade_request(
            sender_id="player_001",
            sender_name="玩家1",
            receiver_id="player_002",
            items=[],
        )

        pending = manager.get_player_pending_trades("player_001")
        assert len(pending) >= 1

        pending = manager.get_player_pending_trades("player_002")
        assert len(pending) >= 1

    def test_remaining_daily_trades(self, manager):
        """测试获取剩余交易次数"""
        remaining = manager.get_remaining_trades("player_001")
        assert remaining == MAX_DAILY_TRADES

        # 创建一个交易
        manager.create_trade_request(
            sender_id="player_001",
            sender_name="玩家1",
            receiver_id="player_002",
            items=[{"item_type": "hero_shard", "item_id": "hero_001", "quantity": 1}],
        )

        remaining = manager.get_remaining_trades("player_001")
        assert remaining == MAX_DAILY_TRADES - 1


class TestTradeHistory:
    """交易历史测试"""

    def test_trade_history_daily_limit(self):
        """测试每日交易限制"""
        history = TradeHistory(player_id="player_001")

        assert history.can_trade_today()
        assert history.remaining_daily_trades() == MAX_DAILY_TRADES

        # 模拟完成一些交易
        for i in range(MAX_DAILY_TRADES):
            history.daily_count += 1

        assert not history.can_trade_today()
        assert history.remaining_daily_trades() == 0


class TestTradeResult:
    """交易结果测试"""

    def test_trade_result_success(self):
        """测试成功交易结果"""
        result = TradeResult(
            success=True,
            trade_id="trade_001",
            sender_id="player_001",
            receiver_id="player_002",
            sender_received=[
                TradeItem(item_type=TradeItemType.GOLD, item_id="gold", quantity=450),
            ],
            receiver_received=[
                TradeItem(item_type=TradeItemType.HERO_SHARD, item_id="hero_001", quantity=50),
            ],
            tax_collected=100,
        )

        assert result.success
        assert result.tax_collected == 100
        assert len(result.sender_received) == 1
        assert len(result.receiver_received) == 1

    def test_trade_result_to_dict(self):
        """测试交易结果转字典"""
        result = TradeResult(
            success=False,
            trade_id="trade_001",
            sender_id="player_001",
            receiver_id="player_002",
            error_message="双方尚未全部确认",
        )

        data = result.to_dict()
        assert not data["success"]
        assert data["error_message"] == "双方尚未全部确认"


class TestTaxCalculation:
    """税额计算测试"""

    def test_gold_tax(self):
        """测试金币税额"""
        # 1000金币，10%税率 = 100税
        item = TradeItem(
            item_type=TradeItemType.GOLD,
            item_id="gold",
            quantity=1000,
        )

        tax = item.calculate_tax()
        assert tax == 100

    def test_different_gold_amounts(self):
        """测试不同金币数量的税额"""
        amounts = [100, 500, 1000, 5000, 10000]

        for amount in amounts:
            item = TradeItem(
                item_type=TradeItemType.GOLD,
                item_id="gold",
                quantity=amount,
            )
            tax = item.calculate_tax()
            expected = int(amount * TRADE_TAX_RATE)
            assert tax == expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
