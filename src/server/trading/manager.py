"""
王者之奕 - 交易管理器

本模块提供交易系统的管理功能：
- TradingManager: 交易管理器类
- 发起交易请求
- 接受/拒绝交易
- 取消交易
- 确认交易（双方）
- 执行交易
- 交易税计算
- 交易历史记录

用于玩家之间的安全交易。
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from .models import (
    DailyTradeStats,
    MAX_DAILY_TRADES,
    MAX_GOLD_PER_TRADE,
    TRADE_TAX_RATE,
    TradeHistory,
    TradeItem,
    TradeItemType,
    TradeOffer,
    TradeRequest,
    TradeResult,
    TradeStatus,
)

logger = logging.getLogger(__name__)


class TradingManager:
    """
    交易管理器
    
    负责管理所有交易相关的操作：
    - 发起/接受/拒绝/取消交易
    - 双方确认机制
    - 交易执行
    - 交易税计算
    - 交易历史记录
    - 每日交易限制
    
    Attributes:
        pending_trades: 待处理的交易 (trade_id -> TradeRequest)
        player_trades: 玩家交易历史 (player_id -> TradeHistory)
        player_inventories: 玩家库存缓存 (用于验证)
    """
    
    def __init__(self):
        """初始化交易管理器"""
        self.pending_trades: Dict[str, TradeRequest] = {}
        self.player_trades: Dict[str, TradeHistory] = {}
        self.player_inventories: Dict[str, Dict[str, Any]] = {}
        self.player_gold: Dict[str, int] = {}
        
        logger.info("TradingManager initialized")
    
    # ==================== 交易请求管理 ====================
    
    def create_trade_request(
        self,
        sender_id: str,
        sender_name: str,
        receiver_id: str,
        items: List[Dict[str, Any]],
        message: Optional[str] = None,
    ) -> Tuple[Optional[TradeRequest], Optional[str]]:
        """
        创建交易请求
        
        Args:
            sender_id: 发起方ID
            sender_name: 发起方名称
            receiver_id: 接收方ID
            items: 发起方提供的物品列表
            message: 附带消息
            
        Returns:
            (交易请求, 错误信息)
        """
        # 检查每日交易限制
        sender_history = self._get_or_create_history(sender_id)
        if not sender_history.can_trade_today():
            remaining = sender_history.remaining_daily_trades()
            return None, f"今日交易次数已达上限，请明天再来"
        
        # 不能和自己交易
        if sender_id == receiver_id:
            return None, "不能和自己交易"
        
        # 检查是否有未完成的交易
        for trade in self.pending_trades.values():
            if trade.status in [TradeStatus.PENDING, TradeStatus.ACCEPTED, TradeStatus.CONFIRMING]:
                if trade.sender_id == sender_id or trade.receiver_id == sender_id:
                    if trade.receiver_id == receiver_id or trade.sender_id == receiver_id:
                        return None, "与该玩家已有未完成的交易"
        
        # 验证物品
        trade_items = []
        for item_data in items:
            item = TradeItem.from_dict(item_data)
            
            # 验证金币限制
            if item.item_type == TradeItemType.GOLD and item.quantity > MAX_GOLD_PER_TRADE:
                return None, f"单笔交易金币不能超过 {MAX_GOLD_PER_TRADE}"
            
            # 验证玩家是否拥有该物品
            if not self._validate_player_item(sender_id, item):
                return None, f"物品 {item.item_name} 数量不足"
            
            trade_items.append(item)
        
        # 创建交易请求
        trade_id = self._generate_trade_id()
        sender_offer = TradeOffer(
            player_id=sender_id,
            player_name=sender_name,
            items=trade_items,
        )
        
        trade_request = TradeRequest(
            trade_id=trade_id,
            sender_offer=sender_offer,
            message=message,
        )
        
        # 存储交易
        self.pending_trades[trade_id] = trade_request
        
        logger.info(
            f"Trade request created: {trade_id} from {sender_id} to {receiver_id}"
        )
        
        return trade_request, None
    
    def accept_trade(
        self,
        trade_id: str,
        receiver_id: str,
        receiver_name: str,
        items: List[Dict[str, Any]],
    ) -> Tuple[Optional[TradeRequest], Optional[str]]:
        """
        接受交易请求
        
        Args:
            trade_id: 交易ID
            receiver_id: 接收方ID
            receiver_name: 接收方名称
            items: 接收方提供的物品列表
            
        Returns:
            (更新后的交易请求, 错误信息)
        """
        trade = self.pending_trades.get(trade_id)
        if not trade:
            return None, "交易不存在"
        
        if trade.status != TradeStatus.PENDING:
            return None, f"交易状态不正确: {trade.status.value}"
        
        if trade.is_expired():
            trade.update_status(TradeStatus.EXPIRED)
            return None, "交易已过期"
        
        # 检查每日交易限制
        receiver_history = self._get_or_create_history(receiver_id)
        if not receiver_history.can_trade_today():
            return None, "今日交易次数已达上限"
        
        # 验证物品
        trade_items = []
        for item_data in items:
            item = TradeItem.from_dict(item_data)
            
            # 验证金币限制
            if item.item_type == TradeItemType.GOLD and item.quantity > MAX_GOLD_PER_TRADE:
                return None, f"单笔交易金币不能超过 {MAX_GOLD_PER_TRADE}"
            
            # 验证玩家是否拥有该物品
            if not self._validate_player_item(receiver_id, item):
                return None, f"物品 {item.item_name} 数量不足"
            
            trade_items.append(item)
        
        # 创建接收方报价
        receiver_offer = TradeOffer(
            player_id=receiver_id,
            player_name=receiver_name,
            items=trade_items,
        )
        
        # 接受交易
        trade.accept(receiver_offer)
        
        logger.info(
            f"Trade accepted: {trade_id} by {receiver_id}"
        )
        
        return trade, None
    
    def reject_trade(
        self,
        trade_id: str,
        player_id: str,
        reason: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        拒绝交易请求
        
        Args:
            trade_id: 交易ID
            player_id: 玩家ID（必须是接收方）
            reason: 拒绝原因
            
        Returns:
            (是否成功, 错误信息)
        """
        trade = self.pending_trades.get(trade_id)
        if not trade:
            return False, "交易不存在"
        
        if trade.status != TradeStatus.PENDING:
            return False, f"交易状态不正确: {trade.status.value}"
        
        # 只有接收方可以拒绝
        if trade.sender_id == player_id:
            return False, "发起方不能拒绝交易，只能取消"
        
        trade.reject(reason)
        
        logger.info(
            f"Trade rejected: {trade_id} by {player_id}, reason: {reason}"
        )
        
        return True, None
    
    def cancel_trade(
        self,
        trade_id: str,
        player_id: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        取消交易
        
        Args:
            trade_id: 交易ID
            player_id: 玩家ID（必须是发起方）
            
        Returns:
            (是否成功, 错误信息)
        """
        trade = self.pending_trades.get(trade_id)
        if not trade:
            return False, "交易不存在"
        
        # 只有发起方可以取消
        if trade.sender_id != player_id:
            return False, "只有发起方可以取消交易"
        
        if trade.status not in [TradeStatus.PENDING, TradeStatus.ACCEPTED]:
            return False, f"交易状态不允许取消: {trade.status.value}"
        
        trade.cancel()
        
        logger.info(
            f"Trade cancelled: {trade_id} by {player_id}"
        )
        
        return True, None
    
    def confirm_trade(
        self,
        trade_id: str,
        player_id: str,
    ) -> Tuple[Optional[TradeRequest], Optional[str]]:
        """
        确认交易
        
        双方都需要确认才能执行交易。
        
        Args:
            trade_id: 交易ID
            player_id: 玩家ID
            
        Returns:
            (更新后的交易请求, 错误信息)
        """
        trade = self.pending_trades.get(trade_id)
        if not trade:
            return None, "交易不存在"
        
        if trade.status not in [TradeStatus.ACCEPTED, TradeStatus.CONFIRMING]:
            return None, f"交易状态不正确: {trade.status.value}"
        
        if trade.is_expired():
            trade.update_status(TradeStatus.EXPIRED)
            return None, "交易已过期"
        
        # 根据玩家身份确认
        if player_id == trade.sender_id:
            if trade.sender_offer.confirmed:
                return None, "您已确认过"
            trade.confirm_sender()
        elif trade.receiver_id and player_id == trade.receiver_id:
            if trade.receiver_offer and trade.receiver_offer.confirmed:
                return None, "您已确认过"
            trade.confirm_receiver()
        else:
            return None, "您不是此交易的参与方"
        
        logger.info(
            f"Trade confirmed: {trade_id} by {player_id}"
        )
        
        return trade, None
    
    def execute_trade(
        self,
        trade_id: str,
    ) -> TradeResult:
        """
        执行交易
        
        双方都确认后才能执行。
        
        Args:
            trade_id: 交易ID
            
        Returns:
            交易结果
        """
        trade = self.pending_trades.get(trade_id)
        if not trade:
            return TradeResult(
                success=False,
                trade_id=trade_id,
                sender_id="",
                receiver_id="",
                error_message="交易不存在",
            )
        
        if not trade.is_both_confirmed():
            return TradeResult(
                success=False,
                trade_id=trade_id,
                sender_id=trade.sender_id,
                receiver_id=trade.receiver_id or "",
                error_message="双方尚未全部确认",
            )
        
        # 计算税额
        sender_tax = trade.sender_offer.get_total_tax()
        receiver_tax = trade.receiver_offer.get_total_tax() if trade.receiver_offer else 0
        total_tax = sender_tax + receiver_tax
        
        # 执行物品转移
        sender_received = []
        receiver_received = []
        
        # 发起方收到接收方的物品
        if trade.receiver_offer:
            for item in trade.receiver_offer.items:
                # 扣税（仅金币）
                actual_item = TradeItem(
                    item_type=item.item_type,
                    item_id=item.item_id,
                    item_name=item.item_name,
                    quantity=item.quantity,
                    extra_data=item.extra_data,
                )
                
                if item.item_type == TradeItemType.GOLD:
                    # 金币扣税
                    tax = item.calculate_tax()
                    actual_item.quantity = item.quantity - tax
                
                sender_received.append(actual_item)
        
        # 接收方收到发起方的物品
        for item in trade.sender_offer.items:
            actual_item = TradeItem(
                item_type=item.item_type,
                item_id=item.item_id,
                item_name=item.item_name,
                quantity=item.quantity,
                extra_data=item.extra_data,
            )
            
            if item.item_type == TradeItemType.GOLD:
                # 金币扣税
                tax = item.calculate_tax()
                actual_item.quantity = item.quantity - tax
            
            receiver_received.append(actual_item)
        
        # 更新玩家库存（实际应该调用库存管理器）
        self._transfer_items(trade.sender_id, trade.receiver_id or "", 
                            sender_received, receiver_received)
        
        # 更新交易状态
        trade.update_status(TradeStatus.EXECUTED)
        
        # 更新交易历史
        sender_history = self._get_or_create_history(trade.sender_id)
        sender_history.add_trade(trade, sender_tax)
        
        if trade.receiver_id:
            receiver_history = self._get_or_create_history(trade.receiver_id)
            receiver_history.add_trade(trade, receiver_tax)
        
        # 移除待处理交易
        # 保留一段时间用于查询历史
        
        logger.info(
            f"Trade executed: {trade_id}, tax: {total_tax}"
        )
        
        return TradeResult(
            success=True,
            trade_id=trade_id,
            sender_id=trade.sender_id,
            receiver_id=trade.receiver_id or "",
            sender_received=sender_received,
            receiver_received=receiver_received,
            tax_collected=total_tax,
            executed_at=datetime.now(),
        )
    
    # ==================== 查询方法 ====================
    
    def get_trade(self, trade_id: str) -> Optional[TradeRequest]:
        """
        获取交易请求
        
        Args:
            trade_id: 交易ID
            
        Returns:
            交易请求
        """
        return self.pending_trades.get(trade_id)
    
    def get_player_pending_trades(self, player_id: str) -> List[TradeRequest]:
        """
        获取玩家的待处理交易
        
        Args:
            player_id: 玩家ID
            
        Returns:
            待处理交易列表
        """
        result = []
        for trade in self.pending_trades.values():
            if trade.status in [TradeStatus.PENDING, TradeStatus.ACCEPTED, TradeStatus.CONFIRMING]:
                if trade.sender_id == player_id or trade.receiver_id == player_id:
                    result.append(trade)
        return result
    
    def get_trade_history(
        self,
        player_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> TradeHistory:
        """
        获取玩家交易历史
        
        Args:
            player_id: 玩家ID
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            交易历史
        """
        history = self._get_or_create_history(player_id)
        
        # 返回分页后的历史
        result = TradeHistory(
            player_id=player_id,
            trades=history.trades[offset:offset + limit],
            total_trades=history.total_trades,
            total_tax_paid=history.total_tax_paid,
            daily_count=history.daily_count,
            daily_reset_at=history.daily_reset_at,
        )
        
        return result
    
    def get_daily_stats(self, player_id: str) -> DailyTradeStats:
        """
        获取每日交易统计
        
        Args:
            player_id: 玩家ID
            
        Returns:
            每日统计
        """
        history = self._get_or_create_history(player_id)
        today = datetime.now().strftime("%Y-%m-%d")
        
        return DailyTradeStats(
            player_id=player_id,
            date=today,
            trade_count=history.daily_count,
            remaining_trades=history.remaining_daily_trades(),
        )
    
    def can_player_trade(self, player_id: str) -> Tuple[bool, Optional[str]]:
        """
        检查玩家是否可以交易
        
        Args:
            player_id: 玩家ID
            
        Returns:
            (是否可以交易, 错误信息)
        """
        history = self._get_or_create_history(player_id)
        
        if not history.can_trade_today():
            return False, f"今日交易次数已达上限（{MAX_DAILY_TRADES}次）"
        
        return True, None
    
    def get_remaining_trades(self, player_id: str) -> int:
        """
        获取今日剩余交易次数
        
        Args:
            player_id: 玩家ID
            
        Returns:
            剩余次数
        """
        history = self._get_or_create_history(player_id)
        return history.remaining_daily_trades()
    
    # ==================== 库存管理（内部方法） ====================
    
    def set_player_inventory(
        self,
        player_id: str,
        shards: Dict[str, int],
        equipment: Dict[str, int],
        consumables: Dict[str, int],
        gold: int,
    ) -> None:
        """
        设置玩家库存（用于同步）
        
        Args:
            player_id: 玩家ID
            shards: 英雄碎片 {hero_id: quantity}
            equipment: 装备 {equip_id: quantity}
            consumables: 道具 {item_id: quantity}
            gold: 金币
        """
        self.player_inventories[player_id] = {
            "shards": shards,
            "equipment": equipment,
            "consumables": consumables,
        }
        self.player_gold[player_id] = gold
    
    def get_player_gold(self, player_id: str) -> int:
        """
        获取玩家金币
        
        Args:
            player_id: 玩家ID
            
        Returns:
            金币数量
        """
        return self.player_gold.get(player_id, 0)
    
    def _validate_player_item(self, player_id: str, item: TradeItem) -> bool:
        """
        验证玩家是否拥有物品
        
        Args:
            player_id: 玩家ID
            item: 物品
            
        Returns:
            是否拥有
        """
        inventory = self.player_inventories.get(player_id, {})
        
        if item.item_type == TradeItemType.GOLD:
            return self.player_gold.get(player_id, 0) >= item.quantity
        elif item.item_type == TradeItemType.HERO_SHARD:
            shards = inventory.get("shards", {})
            return shards.get(item.item_id, 0) >= item.quantity
        elif item.item_type == TradeItemType.EQUIPMENT:
            equipment = inventory.get("equipment", {})
            return equipment.get(item.item_id, 0) >= item.quantity
        elif item.item_type == TradeItemType.CONSUMABLE:
            consumables = inventory.get("consumables", {})
            return consumables.get(item.item_id, 0) >= item.quantity
        
        return False
    
    def _transfer_items(
        self,
        sender_id: str,
        receiver_id: str,
        sender_received: List[TradeItem],
        receiver_received: List[TradeItem],
    ) -> None:
        """
        转移物品（内部方法）
        
        实际应该调用库存管理器，这里只是更新缓存。
        
        Args:
            sender_id: 发起方ID
            receiver_id: 接收方ID
            sender_received: 发起方收到的
            receiver_received: 接收方收到的
        """
        # 更新发起方库存
        sender_inv = self.player_inventories.get(sender_id, {
            "shards": {},
            "equipment": {},
            "consumables": {},
        })
        sender_gold = self.player_gold.get(sender_id, 0)
        
        # 发起方收到物品
        for item in sender_received:
            if item.item_type == TradeItemType.GOLD:
                sender_gold += item.quantity
            elif item.item_type == TradeItemType.HERO_SHARD:
                sender_inv["shards"][item.item_id] = \
                    sender_inv["shards"].get(item.item_id, 0) + item.quantity
            elif item.item_type == TradeItemType.EQUIPMENT:
                sender_inv["equipment"][item.item_id] = \
                    sender_inv["equipment"].get(item.item_id, 0) + item.quantity
            elif item.item_type == TradeItemType.CONSUMABLE:
                sender_inv["consumables"][item.item_id] = \
                    sender_inv["consumables"].get(item.item_id, 0) + item.quantity
        
        # 发起方发出物品
        if receiver_received:
            for item in receiver_received:
                # 这里 quantity 已经是扣税后的
                original = item.quantity + item.calculate_tax()
                if item.item_type == TradeItemType.GOLD:
                    sender_gold -= original
                elif item.item_type == TradeItemType.HERO_SHARD:
                    sender_inv["shards"][item.item_id] = \
                        sender_inv["shards"].get(item.item_id, 0) - original
                elif item.item_type == TradeItemType.EQUIPMENT:
                    sender_inv["equipment"][item.item_id] = \
                        sender_inv["equipment"].get(item.item_id, 0) - original
                elif item.item_type == TradeItemType.CONSUMABLE:
                    sender_inv["consumables"][item.item_id] = \
                        sender_inv["consumables"].get(item.item_id, 0) - original
        
        self.player_inventories[sender_id] = sender_inv
        self.player_gold[sender_id] = sender_gold
        
        # 更新接收方库存
        if receiver_id:
            receiver_inv = self.player_inventories.get(receiver_id, {
                "shards": {},
                "equipment": {},
                "consumables": {},
            })
            receiver_gold = self.player_gold.get(receiver_id, 0)
            
            # 接收方收到物品
            for item in receiver_received:
                if item.item_type == TradeItemType.GOLD:
                    receiver_gold += item.quantity
                elif item.item_type == TradeItemType.HERO_SHARD:
                    receiver_inv["shards"][item.item_id] = \
                        receiver_inv["shards"].get(item.item_id, 0) + item.quantity
                elif item.item_type == TradeItemType.EQUIPMENT:
                    receiver_inv["equipment"][item.item_id] = \
                        receiver_inv["equipment"].get(item.item_id, 0) + item.quantity
                elif item.item_type == TradeItemType.CONSUMABLE:
                    receiver_inv["consumables"][item.item_id] = \
                        receiver_inv["consumables"].get(item.item_id, 0) + item.quantity
            
            # 接收方发出物品
            if sender_received:
                for item in sender_received:
                    original = item.quantity + item.calculate_tax()
                    if item.item_type == TradeItemType.GOLD:
                        receiver_gold -= original
                    elif item.item_type == TradeItemType.HERO_SHARD:
                        receiver_inv["shards"][item.item_id] = \
                            receiver_inv["shards"].get(item.item_id, 0) - original
                    elif item.item_type == TradeItemType.EQUIPMENT:
                        receiver_inv["equipment"][item.item_id] = \
                            receiver_inv["equipment"].get(item.item_id, 0) - original
                    elif item.item_type == TradeItemType.CONSUMABLE:
                        receiver_inv["consumables"][item.item_id] = \
                            receiver_inv["consumables"].get(item.item_id, 0) - original
            
            self.player_inventories[receiver_id] = receiver_inv
            self.player_gold[receiver_id] = receiver_gold
    
    # ==================== 辅助方法 ====================
    
    def _generate_trade_id(self) -> str:
        """生成交易ID"""
        return f"trade_{uuid.uuid4().hex[:16]}"
    
    def _get_or_create_history(self, player_id: str) -> TradeHistory:
        """
        获取或创建玩家交易历史
        
        Args:
            player_id: 玩家ID
            
        Returns:
            交易历史
        """
        if player_id not in self.player_trades:
            self.player_trades[player_id] = TradeHistory(player_id=player_id)
        return self.player_trades[player_id]
    
    def clear_cache(self, player_id: Optional[str] = None) -> None:
        """
        清除缓存
        
        Args:
            player_id: 玩家ID（None表示清除所有）
        """
        if player_id:
            self.pending_trades = {
                k: v for k, v in self.pending_trades.items()
                if v.sender_id != player_id and v.receiver_id != player_id
            }
            self.player_trades.pop(player_id, None)
            self.player_inventories.pop(player_id, None)
            self.player_gold.pop(player_id, None)
        else:
            self.pending_trades.clear()
            self.player_trades.clear()
            self.player_inventories.clear()
            self.player_gold.clear()


# 全局单例
_trading_manager: Optional[TradingManager] = None


def get_trading_manager() -> TradingManager:
    """
    获取交易管理器单例
    
    Returns:
        交易管理器实例
    """
    global _trading_manager
    if _trading_manager is None:
        _trading_manager = TradingManager()
    return _trading_manager
