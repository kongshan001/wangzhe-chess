"""
王者之奕 - 交易系统数据模型

本模块定义交易系统的数据类：
- TradeItem: 交易物品
- TradeStatus: 交易状态枚举
- TradeRequest: 交易请求
- TradeResult: 交易结果
- TradeTax: 交易税配置

用于玩家之间的物品交易。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class TradeStatus(str, Enum):
    """交易状态枚举"""
    PENDING = "pending"              # 等待对方响应
    ACCEPTED = "accepted"            # 对方已接受，等待双方确认
    REJECTED = "rejected"            # 对方已拒绝
    CANCELLED = "cancelled"          # 发起方已取消
    CONFIRMING = "confirming"        # 双方确认中
    CONFIRMED_SENDER = "confirmed_sender"    # 发起方已确认
    CONFIRMED_RECEIVER = "confirmed_receiver"  # 接收方已确认
    EXECUTED = "executed"            # 交易已执行
    FAILED = "failed"                # 交易失败
    EXPIRED = "expired"              # 交易过期


class TradeItemType(str, Enum):
    """交易物品类型枚举"""
    HERO_SHARD = "hero_shard"        # 英雄碎片
    EQUIPMENT = "equipment"          # 装备
    CONSUMABLE = "consumable"        # 道具
    GOLD = "gold"                    # 金币


# 交易配置常量
TRADE_TAX_RATE = 0.10  # 交易税率 10%
MAX_GOLD_PER_TRADE = 10000  # 每笔交易最大金币数
MAX_DAILY_TRADES = 10  # 每日最大交易次数
TRADE_EXPIRE_HOURS = 24  # 交易过期时间（小时）


@dataclass
class TradeItem:
    """
    交易物品数据类
    
    Attributes:
        item_type: 物品类型
        item_id: 物品ID
        item_name: 物品名称
        quantity: 数量
        extra_data: 额外数据（如星级、品质等）
    """
    
    item_type: TradeItemType
    item_id: str
    item_name: str = ""
    quantity: int = 1
    extra_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "item_type": self.item_type.value if isinstance(self.item_type, TradeItemType) else self.item_type,
            "item_id": self.item_id,
            "item_name": self.item_name,
            "quantity": self.quantity,
            "extra_data": self.extra_data,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TradeItem":
        """从字典创建"""
        item_type = data.get("item_type", "hero_shard")
        if isinstance(item_type, str):
            item_type = TradeItemType(item_type)
        
        return cls(
            item_type=item_type,
            item_id=data["item_id"],
            item_name=data.get("item_name", ""),
            quantity=data.get("quantity", 1),
            extra_data=data.get("extra_data", {}),
        )
    
    def calculate_tax(self) -> int:
        """
        计算交易税
        
        金币交易按税率计算，其他物品按价值估算
        （这里简化处理，实际应该根据物品价值计算）
        
        Returns:
            税额
        """
        if self.item_type == TradeItemType.GOLD:
            return int(self.quantity * TRADE_TAX_RATE)
        else:
            # 非金币物品，简单估算（实际应该根据物品价值计算）
            return max(1, self.quantity)


@dataclass
class TradeOffer:
    """
    交易报价数据类
    
    一方提供的交易物品列表。
    
    Attributes:
        player_id: 玩家ID
        player_name: 玩家名称
        items: 物品列表
        confirmed: 是否已确认
        confirmed_at: 确认时间
    """
    
    player_id: str
    player_name: str = ""
    items: List[TradeItem] = field(default_factory=list)
    confirmed: bool = False
    confirmed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "player_id": self.player_id,
            "player_name": self.player_name,
            "items": [item.to_dict() for item in self.items],
            "confirmed": self.confirmed,
            "confirmed_at": self.confirmed_at.isoformat() if self.confirmed_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TradeOffer":
        """从字典创建"""
        items = [TradeItem.from_dict(item) for item in data.get("items", [])]
        return cls(
            player_id=data["player_id"],
            player_name=data.get("player_name", ""),
            items=items,
            confirmed=data.get("confirmed", False),
            confirmed_at=datetime.fromisoformat(data["confirmed_at"]) if data.get("confirmed_at") else None,
        )
    
    def get_gold_amount(self) -> int:
        """获取金币数量"""
        for item in self.items:
            if item.item_type == TradeItemType.GOLD:
                return item.quantity
        return 0
    
    def get_total_tax(self) -> int:
        """获取总税额"""
        return sum(item.calculate_tax() for item in self.items)
    
    def confirm(self) -> None:
        """确认报价"""
        self.confirmed = True
        self.confirmed_at = datetime.now()


@dataclass
class TradeRequest:
    """
    交易请求数据类
    
    Attributes:
        trade_id: 交易唯一ID
        sender_offer: 发起方报价
        receiver_id: 接收方ID（交易发送目标）
        receiver_offer: 接收方报价（初始为空，对方接受后填充）
        status: 交易状态
        created_at: 创建时间
        updated_at: 更新时间
        expires_at: 过期时间
        message: 附带消息
        reject_reason: 拒绝原因
        error_message: 错误信息
    """
    
    trade_id: str
    sender_offer: TradeOffer
    receiver_id: Optional[str] = None
    receiver_offer: Optional[TradeOffer] = None
    status: TradeStatus = TradeStatus.PENDING
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    message: Optional[str] = None
    reject_reason: Optional[str] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        """初始化后处理"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = self.created_at
        if self.expires_at is None:
            from datetime import timedelta
            self.expires_at = self.created_at + timedelta(hours=TRADE_EXPIRE_HOURS)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "trade_id": self.trade_id,
            "sender_offer": self.sender_offer.to_dict(),
            "receiver_id": self.receiver_id,
            "receiver_offer": self.receiver_offer.to_dict() if self.receiver_offer else None,
            "status": self.status.value if isinstance(self.status, TradeStatus) else self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "message": self.message,
            "reject_reason": self.reject_reason,
            "error_message": self.error_message,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TradeRequest":
        """从字典创建"""
        status = data.get("status", "pending")
        if isinstance(status, str):
            status = TradeStatus(status)
        
        sender_offer = TradeOffer.from_dict(data["sender_offer"])
        receiver_offer = None
        if data.get("receiver_offer"):
            receiver_offer = TradeOffer.from_dict(data["receiver_offer"])
        
        return cls(
            trade_id=data["trade_id"],
            sender_offer=sender_offer,
            receiver_id=data.get("receiver_id"),
            receiver_offer=receiver_offer,
            status=status,
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            message=data.get("message"),
            reject_reason=data.get("reject_reason"),
            error_message=data.get("error_message"),
        )
    
    @property
    def sender_id(self) -> str:
        """获取发起方ID"""
        return self.sender_offer.player_id
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def is_both_confirmed(self) -> bool:
        """检查双方是否都已确认"""
        sender_confirmed = self.sender_offer.confirmed
        receiver_confirmed = self.receiver_offer.confirmed if self.receiver_offer else False
        return sender_confirmed and receiver_confirmed
    
    def update_status(self, status: TradeStatus) -> None:
        """更新状态"""
        self.status = status
        self.updated_at = datetime.now()
    
    def accept(self, receiver_offer: TradeOffer) -> None:
        """接受交易"""
        self.receiver_offer = receiver_offer
        self.update_status(TradeStatus.ACCEPTED)
    
    def reject(self, reason: Optional[str] = None) -> None:
        """拒绝交易"""
        self.reject_reason = reason
        self.update_status(TradeStatus.REJECTED)
    
    def cancel(self) -> None:
        """取消交易"""
        self.update_status(TradeStatus.CANCELLED)
    
    def confirm_sender(self) -> None:
        """发起方确认"""
        self.sender_offer.confirm()
        self._update_confirm_status()
    
    def confirm_receiver(self) -> None:
        """接收方确认"""
        if self.receiver_offer:
            self.receiver_offer.confirm()
        self._update_confirm_status()
    
    def _update_confirm_status(self) -> None:
        """更新确认状态"""
        if self.is_both_confirmed():
            self.update_status(TradeStatus.CONFIRMING)
        self.updated_at = datetime.now()


@dataclass
class TradeResult:
    """
    交易结果数据类
    
    Attributes:
        success: 是否成功
        trade_id: 交易ID
        sender_id: 发起方ID
        receiver_id: 接收方ID
        sender_received: 发起方收到的物品
        receiver_received: 接收方收到的物品
        tax_collected: 总税额
        error_message: 错误信息
        executed_at: 执行时间
    """
    
    success: bool
    trade_id: str
    sender_id: str
    receiver_id: str
    sender_received: List[TradeItem] = field(default_factory=list)
    receiver_received: List[TradeItem] = field(default_factory=list)
    tax_collected: int = 0
    error_message: Optional[str] = None
    executed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "trade_id": self.trade_id,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "sender_received": [item.to_dict() for item in self.sender_received],
            "receiver_received": [item.to_dict() for item in self.receiver_received],
            "tax_collected": self.tax_collected,
            "error_message": self.error_message,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TradeResult":
        """从字典创建"""
        sender_received = [TradeItem.from_dict(item) for item in data.get("sender_received", [])]
        receiver_received = [TradeItem.from_dict(item) for item in data.get("receiver_received", [])]
        
        return cls(
            success=data.get("success", False),
            trade_id=data["trade_id"],
            sender_id=data["sender_id"],
            receiver_id=data["receiver_id"],
            sender_received=sender_received,
            receiver_received=receiver_received,
            tax_collected=data.get("tax_collected", 0),
            error_message=data.get("error_message"),
            executed_at=datetime.fromisoformat(data["executed_at"]) if data.get("executed_at") else None,
        )


@dataclass
class TradeHistory:
    """
    交易历史数据类
    
    Attributes:
        player_id: 玩家ID
        trades: 交易记录列表
        total_trades: 总交易数
        total_tax_paid: 总缴税
        daily_count: 今日交易次数
        daily_reset_at: 每日重置时间
    """
    
    player_id: str
    trades: List[TradeRequest] = field(default_factory=list)
    total_trades: int = 0
    total_tax_paid: int = 0
    daily_count: int = 0
    daily_reset_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "player_id": self.player_id,
            "trades": [t.to_dict() for t in self.trades],
            "total_trades": self.total_trades,
            "total_tax_paid": self.total_tax_paid,
            "daily_count": self.daily_count,
            "daily_reset_at": self.daily_reset_at.isoformat() if self.daily_reset_at else None,
        }
    
    def can_trade_today(self) -> bool:
        """检查今日是否还能交易"""
        self._check_daily_reset()
        return self.daily_count < MAX_DAILY_TRADES
    
    def remaining_daily_trades(self) -> int:
        """获取今日剩余交易次数"""
        self._check_daily_reset()
        return max(0, MAX_DAILY_TRADES - self.daily_count)
    
    def _check_daily_reset(self) -> None:
        """检查每日重置"""
        now = datetime.now()
        if self.daily_reset_at is None or now.date() > self.daily_reset_at.date():
            self.daily_count = 0
            self.daily_reset_at = now
    
    def add_trade(self, trade: TradeRequest, tax: int = 0) -> None:
        """添加交易记录"""
        self.trades.append(trade)
        self.total_trades += 1
        self.total_tax_paid += tax
        self._check_daily_reset()
        self.daily_count += 1


@dataclass
class DailyTradeStats:
    """
    每日交易统计数据类
    
    Attributes:
        player_id: 玩家ID
        date: 日期
        trade_count: 交易次数
        tax_paid: 缴纳税款
        gold_traded: 金币交易量
        items_traded: 物品交易量
    """
    
    player_id: str
    date: str
    trade_count: int = 0
    tax_paid: int = 0
    gold_traded: int = 0
    items_traded: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "player_id": self.player_id,
            "date": self.date,
            "trade_count": self.trade_count,
            "tax_paid": self.tax_paid,
            "gold_traded": self.gold_traded,
            "items_traded": self.items_traded,
        }
