"""
王者之奕 - 交易系统 WebSocket 处理器

本模块实现交易系统的 WebSocket 消息处理：
- 发起交易请求
- 接受/拒绝交易
- 取消交易
- 确认交易（双方）
- 执行交易
- 获取交易历史
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from src.shared.protocol import (
    BaseMessage,
    ErrorMessage,
    MessageType,
)
from .manager import TradingManager, get_trading_manager
from .models import TradeItem, TradeItemType

if TYPE_CHECKING:
    from src.server.ws.handler import Session

import structlog

logger = structlog.get_logger()


class TradingWSHandler:
    """
    交易系统 WebSocket 处理器
    
    处理所有交易相关的 WebSocket 消息。
    
    Attributes:
        trading_manager: 交易管理器
    """
    
    def __init__(self, trading_manager: Optional[TradingManager] = None):
        """
        初始化交易 WebSocket 处理器
        
        Args:
            trading_manager: 交易管理器（可选，默认使用全局单例）
        """
        self.trading_manager = trading_manager or get_trading_manager()
    
    async def handle_send_trade_request(
        self,
        session: Session,
        message: "SendTradeRequestMessage",
    ) -> BaseMessage:
        """
        处理发起交易请求
        
        Args:
            session: 会话
            message: 请求消息
            
        Returns:
            交易请求已发送响应或错误消息
        """
        player_id = session.player_id
        player_name = getattr(session, 'player_name', player_id)
        receiver_id = message.receiver_id
        items = message.items
        msg = message.message
        
        # 创建交易请求
        trade_request, error = self.trading_manager.create_trade_request(
            sender_id=player_id,
            sender_name=player_name,
            receiver_id=receiver_id,
            items=items,
            message=msg,
        )
        
        if error:
            return ErrorMessage(
                code=6001,
                message=error,
                seq=message.seq,
            )
        
        logger.info(
            "Trade request sent",
            player_id=player_id,
            receiver_id=receiver_id,
            trade_id=trade_request.trade_id,
        )
        
        # 返回交易请求已发送消息
        return TradeRequestSentMessage(
            trade_id=trade_request.trade_id,
            receiver_id=receiver_id,
            items=items,
            status=trade_request.status.value,
            created_at=trade_request.created_at.isoformat() if trade_request.created_at else None,
            seq=message.seq,
        )
    
    async def handle_accept_trade_request(
        self,
        session: Session,
        message: "AcceptTradeRequestMessage",
    ) -> BaseMessage:
        """
        处理接受交易请求
        
        Args:
            session: 会话
            message: 请求消息
            
        Returns:
            交易已接受响应或错误消息
        """
        player_id = session.player_id
        player_name = getattr(session, 'player_name', player_id)
        trade_id = message.trade_id
        items = message.items
        
        # 接受交易
        trade_request, error = self.trading_manager.accept_trade(
            trade_id=trade_id,
            receiver_id=player_id,
            receiver_name=player_name,
            items=items,
        )
        
        if error:
            return ErrorMessage(
                code=6002,
                message=error,
                seq=message.seq,
            )
        
        logger.info(
            "Trade request accepted",
            player_id=player_id,
            trade_id=trade_id,
        )
        
        return TradeRequestAcceptedMessage(
            trade_id=trade_id,
            sender_id=trade_request.sender_id,
            sender_items=[item.to_dict() for item in trade_request.sender_offer.items],
            receiver_items=items,
            status=trade_request.status.value,
            seq=message.seq,
        )
    
    async def handle_reject_trade_request(
        self,
        session: Session,
        message: "RejectTradeRequestMessage",
    ) -> BaseMessage:
        """
        处理拒绝交易请求
        
        Args:
            session: 会话
            message: 请求消息
            
        Returns:
            交易已拒绝响应或错误消息
        """
        player_id = session.player_id
        trade_id = message.trade_id
        reason = message.reason
        
        # 拒绝交易
        success, error = self.trading_manager.reject_trade(
            trade_id=trade_id,
            player_id=player_id,
            reason=reason,
        )
        
        if not success:
            return ErrorMessage(
                code=6003,
                message=error,
                seq=message.seq,
            )
        
        logger.info(
            "Trade request rejected",
            player_id=player_id,
            trade_id=trade_id,
            reason=reason,
        )
        
        return TradeRequestRejectedMessage(
            trade_id=trade_id,
            reason=reason,
            seq=message.seq,
        )
    
    async def handle_cancel_trade(
        self,
        session: Session,
        message: "CancelTradeMessage",
    ) -> BaseMessage:
        """
        处理取消交易
        
        Args:
            session: 会话
            message: 请求消息
            
        Returns:
            交易已取消响应或错误消息
        """
        player_id = session.player_id
        trade_id = message.trade_id
        
        # 取消交易
        success, error = self.trading_manager.cancel_trade(
            trade_id=trade_id,
            player_id=player_id,
        )
        
        if not success:
            return ErrorMessage(
                code=6004,
                message=error,
                seq=message.seq,
            )
        
        logger.info(
            "Trade cancelled",
            player_id=player_id,
            trade_id=trade_id,
        )
        
        return TradeCancelledMessage(
            trade_id=trade_id,
            seq=message.seq,
        )
    
    async def handle_confirm_trade(
        self,
        session: Session,
        message: "ConfirmTradeMessage",
    ) -> BaseMessage:
        """
        处理确认交易
        
        Args:
            session: 会话
            message: 请求消息
            
        Returns:
            交易已确认响应或错误消息
        """
        player_id = session.player_id
        trade_id = message.trade_id
        
        # 确认交易
        trade_request, error = self.trading_manager.confirm_trade(
            trade_id=trade_id,
            player_id=player_id,
        )
        
        if error:
            return ErrorMessage(
                code=6005,
                message=error,
                seq=message.seq,
            )
        
        logger.info(
            "Trade confirmed",
            player_id=player_id,
            trade_id=trade_id,
            both_confirmed=trade_request.is_both_confirmed(),
        )
        
        return TradeConfirmedMessage(
            trade_id=trade_id,
            player_id=player_id,
            sender_confirmed=trade_request.sender_offer.confirmed,
            receiver_confirmed=trade_request.receiver_offer.confirmed if trade_request.receiver_offer else False,
            both_confirmed=trade_request.is_both_confirmed(),
            status=trade_request.status.value,
            seq=message.seq,
        )
    
    async def handle_execute_trade(
        self,
        session: Session,
        message: "ExecuteTradeMessage",
    ) -> BaseMessage:
        """
        处理执行交易
        
        Args:
            session: 会话
            message: 请求消息
            
        Returns:
            交易执行结果或错误消息
        """
        trade_id = message.trade_id
        
        # 执行交易
        result = self.trading_manager.execute_trade(trade_id)
        
        if not result.success:
            return ErrorMessage(
                code=6006,
                message=result.error_message or "交易执行失败",
                seq=message.seq,
            )
        
        logger.info(
            "Trade executed",
            trade_id=trade_id,
            tax=result.tax_collected,
        )
        
        return TradeExecutedMessage(
            trade_id=trade_id,
            sender_id=result.sender_id,
            receiver_id=result.receiver_id,
            sender_received=[item.to_dict() for item in result.sender_received],
            receiver_received=[item.to_dict() for item in result.receiver_received],
            tax_collected=result.tax_collected,
            executed_at=result.executed_at.isoformat() if result.executed_at else None,
            seq=message.seq,
        )
    
    async def handle_get_trade_history(
        self,
        session: Session,
        message: "GetTradeHistoryMessage",
    ) -> "TradeHistoryMessage":
        """
        处理获取交易历史请求
        
        Args:
            session: 会话
            message: 请求消息
            
        Returns:
            交易历史响应
        """
        player_id = session.player_id
        limit = message.limit or 20
        offset = message.offset or 0
        
        # 获取交易历史
        history = self.trading_manager.get_trade_history(
            player_id=player_id,
            limit=limit,
            offset=offset,
        )
        
        return TradeHistoryMessage(
            player_id=player_id,
            trades=[trade.to_dict() for trade in history.trades],
            total_trades=history.total_trades,
            total_tax_paid=history.total_tax_paid,
            daily_count=history.daily_count,
            remaining_trades=history.remaining_daily_trades(),
            seq=message.seq,
        )
    
    async def handle_get_pending_trades(
        self,
        session: Session,
        message: "GetPendingTradesMessage",
    ) -> "PendingTradesMessage":
        """
        处理获取待处理交易请求
        
        Args:
            session: 会话
            message: 请求消息
            
        Returns:
            待处理交易响应
        """
        player_id = session.player_id
        
        # 获取待处理交易
        trades = self.trading_manager.get_player_pending_trades(player_id)
        
        return PendingTradesMessage(
            trades=[trade.to_dict() for trade in trades],
            count=len(trades),
            seq=message.seq,
        )
    
    async def handle_get_trade_status(
        self,
        session: Session,
        message: "GetTradeStatusMessage",
    ) -> "TradeStatusMessage":
        """
        处理获取交易状态请求
        
        Args:
            session: 会话
            message: 请求消息
            
        Returns:
            交易状态响应
        """
        trade_id = message.trade_id
        
        # 获取交易
        trade = self.trading_manager.get_trade(trade_id)
        
        if not trade:
            return ErrorMessage(
                code=6007,
                message="交易不存在",
                seq=message.seq,
            )
        
        return TradeStatusMessage(
            trade_id=trade_id,
            status=trade.status.value,
            sender_confirmed=trade.sender_offer.confirmed,
            receiver_confirmed=trade.receiver_offer.confirmed if trade.receiver_offer else False,
            sender_items=[item.to_dict() for item in trade.sender_offer.items],
            receiver_items=[item.to_dict() for item in trade.receiver_offer.items] if trade.receiver_offer else [],
            seq=message.seq,
        )


# ============================================================================
# 交易相关消息类定义
# ============================================================================

from pydantic import BaseModel, Field
from typing import Any, Optional


class TradeItemData(BaseModel):
    """交易物品数据"""
    item_type: str = Field(..., description="物品类型")
    item_id: str = Field(..., description="物品ID")
    item_name: str = Field(default="", description="物品名称")
    quantity: int = Field(default=1, description="数量")
    extra_data: dict = Field(default_factory=dict, description="额外数据")


class SendTradeRequestMessage(BaseMessage):
    """发送交易请求消息"""
    type: MessageType = MessageType.SEND_TRADE_REQUEST
    receiver_id: str = Field(..., description="接收方ID")
    items: List[dict] = Field(..., description="交易物品列表")
    message: Optional[str] = Field(default=None, description="附带消息")


class TradeRequestSentMessage(BaseMessage):
    """交易请求已发送消息"""
    type: MessageType = MessageType.TRADE_REQUEST_SENT
    trade_id: str = Field(..., description="交易ID")
    receiver_id: str = Field(..., description="接收方ID")
    items: List[dict] = Field(..., description="交易物品列表")
    status: str = Field(..., description="交易状态")
    created_at: Optional[str] = Field(default=None, description="创建时间")


class AcceptTradeRequestMessage(BaseMessage):
    """接受交易请求消息"""
    type: MessageType = MessageType.ACCEPT_TRADE_REQUEST
    trade_id: str = Field(..., description="交易ID")
    items: List[dict] = Field(..., description="提供的物品列表")


class TradeRequestAcceptedMessage(BaseMessage):
    """交易已接受消息"""
    type: MessageType = MessageType.TRADE_REQUEST_ACCEPTED
    trade_id: str = Field(..., description="交易ID")
    sender_id: str = Field(..., description="发起方ID")
    sender_items: List[dict] = Field(..., description="发起方物品")
    receiver_items: List[dict] = Field(..., description="接收方物品")
    status: str = Field(..., description="交易状态")


class RejectTradeRequestMessage(BaseMessage):
    """拒绝交易请求消息"""
    type: MessageType = MessageType.REJECT_TRADE_REQUEST
    trade_id: str = Field(..., description="交易ID")
    reason: Optional[str] = Field(default=None, description="拒绝原因")


class TradeRequestRejectedMessage(BaseMessage):
    """交易已拒绝消息"""
    type: MessageType = MessageType.TRADE_REQUEST_REJECTED
    trade_id: str = Field(..., description="交易ID")
    reason: Optional[str] = Field(default=None, description="拒绝原因")


class CancelTradeMessage(BaseMessage):
    """取消交易消息"""
    type: MessageType = MessageType.CANCEL_TRADE
    trade_id: str = Field(..., description="交易ID")


class TradeCancelledMessage(BaseMessage):
    """交易已取消消息"""
    type: MessageType = MessageType.TRADE_CANCELLED
    trade_id: str = Field(..., description="交易ID")


class ConfirmTradeMessage(BaseMessage):
    """确认交易消息"""
    type: MessageType = MessageType.CONFIRM_TRADE
    trade_id: str = Field(..., description="交易ID")


class TradeConfirmedMessage(BaseMessage):
    """交易已确认消息"""
    type: MessageType = MessageType.TRADE_CONFIRMED
    trade_id: str = Field(..., description="交易ID")
    player_id: str = Field(..., description="确认玩家ID")
    sender_confirmed: bool = Field(..., description="发起方是否确认")
    receiver_confirmed: bool = Field(..., description="接收方是否确认")
    both_confirmed: bool = Field(..., description="双方是否都已确认")
    status: str = Field(..., description="交易状态")


class ExecuteTradeMessage(BaseMessage):
    """执行交易消息"""
    type: MessageType = MessageType.EXECUTE_TRADE
    trade_id: str = Field(..., description="交易ID")


class TradeExecutedMessage(BaseMessage):
    """交易已执行消息"""
    type: MessageType = MessageType.TRADE_EXECUTED
    trade_id: str = Field(..., description="交易ID")
    sender_id: str = Field(..., description="发起方ID")
    receiver_id: str = Field(..., description="接收方ID")
    sender_received: List[dict] = Field(..., description="发起方收到")
    receiver_received: List[dict] = Field(..., description="接收方收到")
    tax_collected: int = Field(..., description="税额")
    executed_at: Optional[str] = Field(default=None, description="执行时间")


class GetTradeHistoryMessage(BaseMessage):
    """获取交易历史消息"""
    type: MessageType = MessageType.GET_TRADE_HISTORY
    limit: Optional[int] = Field(default=20, description="数量限制")
    offset: Optional[int] = Field(default=0, description="偏移量")


class TradeHistoryMessage(BaseMessage):
    """交易历史响应消息"""
    type: MessageType = MessageType.TRADE_HISTORY
    player_id: str = Field(..., description="玩家ID")
    trades: List[dict] = Field(..., description="交易列表")
    total_trades: int = Field(..., description="总交易数")
    total_tax_paid: int = Field(..., description="总缴税")
    daily_count: int = Field(..., description="今日交易数")
    remaining_trades: int = Field(..., description="剩余交易次数")


class GetPendingTradesMessage(BaseMessage):
    """获取待处理交易消息"""
    type: MessageType = MessageType.GET_PENDING_TRADES


class PendingTradesMessage(BaseMessage):
    """待处理交易响应消息"""
    type: MessageType = MessageType.PENDING_TRADES
    trades: List[dict] = Field(..., description="交易列表")
    count: int = Field(..., description="数量")


class GetTradeStatusMessage(BaseMessage):
    """获取交易状态消息"""
    type: MessageType = MessageType.GET_TRADE_STATUS
    trade_id: str = Field(..., description="交易ID")


class TradeStatusMessage(BaseMessage):
    """交易状态响应消息"""
    type: MessageType = MessageType.TRADE_STATUS
    trade_id: str = Field(..., description="交易ID")
    status: str = Field(..., description="交易状态")
    sender_confirmed: bool = Field(..., description="发起方是否确认")
    receiver_confirmed: bool = Field(..., description="接收方是否确认")
    sender_items: List[dict] = Field(..., description="发起方物品")
    receiver_items: List[dict] = Field(..., description="接收方物品")


def register_trading_handlers(ws_handler: Any) -> None:
    """
    注册交易系统的 WebSocket 处理器
    
    Args:
        ws_handler: WebSocket 处理器实例
    """
    trading_handler = TradingWSHandler()
    
    @ws_handler.on_message(MessageType.SEND_TRADE_REQUEST)
    async def handle_send_trade_request(session: Session, message: SendTradeRequestMessage):
        return await trading_handler.handle_send_trade_request(session, message)
    
    @ws_handler.on_message(MessageType.ACCEPT_TRADE_REQUEST)
    async def handle_accept_trade_request(session: Session, message: AcceptTradeRequestMessage):
        return await trading_handler.handle_accept_trade_request(session, message)
    
    @ws_handler.on_message(MessageType.REJECT_TRADE_REQUEST)
    async def handle_reject_trade_request(session: Session, message: RejectTradeRequestMessage):
        return await trading_handler.handle_reject_trade_request(session, message)
    
    @ws_handler.on_message(MessageType.CANCEL_TRADE)
    async def handle_cancel_trade(session: Session, message: CancelTradeMessage):
        return await trading_handler.handle_cancel_trade(session, message)
    
    @ws_handler.on_message(MessageType.CONFIRM_TRADE)
    async def handle_confirm_trade(session: Session, message: ConfirmTradeMessage):
        return await trading_handler.handle_confirm_trade(session, message)
    
    @ws_handler.on_message(MessageType.EXECUTE_TRADE)
    async def handle_execute_trade(session: Session, message: ExecuteTradeMessage):
        return await trading_handler.handle_execute_trade(session, message)
    
    @ws_handler.on_message(MessageType.GET_TRADE_HISTORY)
    async def handle_get_trade_history(session: Session, message: GetTradeHistoryMessage):
        return await trading_handler.handle_get_trade_history(session, message)
    
    @ws_handler.on_message(MessageType.GET_PENDING_TRADES)
    async def handle_get_pending_trades(session: Session, message: GetPendingTradesMessage):
        return await trading_handler.handle_get_pending_trades(session, message)
    
    @ws_handler.on_message(MessageType.GET_TRADE_STATUS)
    async def handle_get_trade_status(session: Session, message: GetTradeStatusMessage):
        return await trading_handler.handle_get_trade_status(session, message)
    
    logger.info("Trading WebSocket handlers registered")
