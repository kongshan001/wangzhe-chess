"""
王者之奕 - 交易系统模块

本模块实现玩家之间的交易功能：
- 英雄碎片交易
- 装备交易
- 道具交易
- 金币交易（有限制）

交易流程：
1. 发起方发送交易请求
2. 接收方接受并提供自己的物品
3. 双方都确认
4. 执行交易，扣除10%交易税
"""

from .manager import (
    TradingManager,
    get_trading_manager,
)
from .models import (
    MAX_DAILY_TRADES,
    MAX_GOLD_PER_TRADE,
    TRADE_EXPIRE_HOURS,
    TRADE_TAX_RATE,
    DailyTradeStats,
    TradeHistory,
    TradeItem,
    TradeItemType,
    TradeOffer,
    TradeRequest,
    TradeResult,
    TradeStatus,
)
from .ws_handler import (
    AcceptTradeRequestMessage,
    CancelTradeMessage,
    ConfirmTradeMessage,
    ExecuteTradeMessage,
    GetPendingTradesMessage,
    GetTradeHistoryMessage,
    GetTradeStatusMessage,
    PendingTradesMessage,
    RejectTradeRequestMessage,
    # 消息类
    SendTradeRequestMessage,
    TradeCancelledMessage,
    TradeConfirmedMessage,
    TradeExecutedMessage,
    TradeHistoryMessage,
    TradeItemData,
    TradeRequestAcceptedMessage,
    TradeRequestRejectedMessage,
    TradeRequestSentMessage,
    TradeStatusMessage,
    TradingWSHandler,
    register_trading_handlers,
)

__all__ = [
    # 常量
    "TRADE_TAX_RATE",
    "MAX_GOLD_PER_TRADE",
    "MAX_DAILY_TRADES",
    "TRADE_EXPIRE_HOURS",
    # 数据类
    "TradeItemType",
    "TradeItem",
    "TradeOffer",
    "TradeRequest",
    "TradeResult",
    "TradeStatus",
    "TradeHistory",
    "DailyTradeStats",
    # 管理器
    "TradingManager",
    "get_trading_manager",
    # WebSocket处理器
    "TradingWSHandler",
    "register_trading_handlers",
    # 消息类
    "SendTradeRequestMessage",
    "TradeRequestSentMessage",
    "AcceptTradeRequestMessage",
    "TradeRequestAcceptedMessage",
    "RejectTradeRequestMessage",
    "TradeRequestRejectedMessage",
    "CancelTradeMessage",
    "TradeCancelledMessage",
    "ConfirmTradeMessage",
    "TradeConfirmedMessage",
    "ExecuteTradeMessage",
    "TradeExecutedMessage",
    "GetTradeHistoryMessage",
    "TradeHistoryMessage",
    "GetPendingTradesMessage",
    "PendingTradesMessage",
    "GetTradeStatusMessage",
    "TradeStatusMessage",
    "TradeItemData",
]
