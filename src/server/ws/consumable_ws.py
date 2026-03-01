"""
王者之奕 - 道具 WebSocket 处理器

本模块提供道具系统相关的 WebSocket 消息处理：
- 获取道具列表
- 获取玩家道具
- 使用道具
- 购买道具
- 获取使用历史

与主 WebSocket 处理器集成。
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Optional

from ..ws.handler import ws_handler

from ..consumable import (
    ConsumableManager,
    ConsumableEffect,
    get_consumable_manager,
)
from ...shared.protocol import (
    BaseMessage,
    BuyConsumableMessage,
    ConsumablesListMessage,
    ConsumableBoughtMessage,
    ConsumableData,
    ConsumableEffectAppliedMessage,
    ConsumableEffectData,
    ConsumableHistoryMessage,
    ConsumableUsageData,
    ConsumableUsedMessage,
    ErrorMessage,
    GetConsumablesMessage,
    GetConsumableHistoryMessage,
    GetPlayerConsumablesMessage,
    MessageType,
    PlayerConsumableData,
    PlayerConsumablesListMessage,
)

if TYPE_CHECKING:
    from ..ws.handler import Session

logger = logging.getLogger(__name__)


class ConsumableWSHandler:
    """
    道具 WebSocket 处理器
    
    处理所有道具相关的 WebSocket 消息。
    
    使用方式:
        handler = ConsumableWSHandler()
        
        @ws_handler.on_message(MessageType.GET_CONSUMABLES)
        async def handle_get_consumables(session, message):
            return await consumable_handler.handle_get_consumables(session, message)
    """
    
    def __init__(self, config_path: Optional[str] = None) -> None:
        """初始化处理器"""
        self._manager: Optional[ConsumableManager] = None
        self._config_path = config_path
    
    @property
    def manager(self) -> ConsumableManager:
        """获取道具管理器"""
        if self._manager is None:
            self._manager = get_consumable_manager(self._config_path)
        return self._manager
    
    async def handle_get_consumables(
        self,
        session: "Session",
        message: GetConsumablesMessage,
    ) -> Optional[BaseMessage]:
        """
        处理获取道具列表请求
        
        Args:
            session: WebSocket 会话
            message: 获取道具列表消息
            
        Returns:
            响应消息
        """
        player_id = session.player_id
        
        try:
            # 获取所有道具
            consumables = self.manager.get_all_consumables()
            
            # 转换为消息格式
            consumable_data_list = [
                ConsumableData(
                    consumable_id=c.consumable_id,
                    name=c.name,
                    description=c.description,
                    consumable_type=c.consumable_type.value,
                    rarity=c.rarity.value,
                    effects=[e.to_dict() for e in c.effects],
                    price=c.price.to_dict() if c.price else None,
                    max_stack=c.max_stack,
                    icon=c.icon,
                    auto_use=c.auto_use,
                )
                for c in consumables
            ]
            
            logger.info(
                "获取道具列表",
                player_id=player_id,
                count=len(consumable_data_list),
            )
            
            return ConsumablesListMessage(
                consumables=consumable_data_list,
                total_count=len(consumable_data_list),
                seq=message.seq,
            )
        
        except Exception as e:
            logger.error(f"获取道具列表失败: {e}", exc_info=True)
            return ErrorMessage(
                code=5001,
                message=f"获取道具列表失败: {str(e)}",
                seq=message.seq,
            )
    
    async def handle_get_player_consumables(
        self,
        session: "Session",
        message: GetPlayerConsumablesMessage,
    ) -> Optional[BaseMessage]:
        """
        处理获取玩家道具请求
        
        Args:
            session: WebSocket 会话
            message: 获取玩家道具消息
            
        Returns:
            响应消息
        """
        player_id = session.player_id
        
        try:
            # 获取玩家道具
            consumables = self.manager.get_player_consumables(player_id)
            
            # 获取激活的效果
            active_effects = self.manager.get_active_effects(player_id)
            
            # 转换为消息格式
            consumable_data_list = [
                PlayerConsumableData(
                    consumable_id=pc.consumable_id,
                    quantity=pc.quantity,
                    acquired_at=pc.acquired_at.isoformat(),
                    acquire_type=pc.acquire_type,
                    expire_at=pc.expire_at.isoformat() if pc.expire_at else None,
                )
                for pc in consumables
            ]
            
            effect_data_list = [
                ConsumableEffectData(
                    consumable_id=e.consumable_id,
                    effect_type=e.effect_type.value,
                    value=e.value,
                    activated_at=e.activated_at.isoformat(),
                    remaining_rounds=e.remaining_rounds,
                )
                for e in active_effects
            ]
            
            logger.info(
                "获取玩家道具",
                player_id=player_id,
                consumable_count=len(consumable_data_list),
                effect_count=len(effect_data_list),
            )
            
            return PlayerConsumablesListMessage(
                consumables=consumable_data_list,
                active_effects=effect_data_list,
                total_count=len(consumable_data_list),
                seq=message.seq,
            )
        
        except Exception as e:
            logger.error(f"获取玩家道具失败: {e}", exc_info=True)
            return ErrorMessage(
                code=5002,
                message=f"获取玩家道具失败: {str(e)}",
                seq=message.seq,
            )
    
    async def handle_use_consumable(
        self,
        session: "Session",
        message: UseConsumableMessage,
    ) -> Optional[BaseMessage]:
        """
        处理使用道具请求
        
        Args:
            session: WebSocket 会话
            message: 使用道具消息
            
        Returns:
            响应消息
        """
        player_id = session.player_id
        consumable_id = message.consumable_id
        quantity = message.quantity
        context = message.context
        context_id = message.context_id
        
        try:
            # 应用道具效果
            success, active_effect, error = self.manager.apply_effect(
                player_id=player_id,
                consumable_id=consumable_id,
                context=context,
                context_id=context_id,
            )
            
            if not success:
                return ErrorMessage(
                    code=5003,
                    message=error or "使用道具失败",
                    seq=message.seq,
                )
            
            # 获取剩余数量
            remaining = self.manager.get_consumable_quantity(player_id, consumable_id)
            
            # 转换激活效果
            effect_data = None
            if active_effect:
                effect_data = ConsumableEffectData(
                    consumable_id=active_effect.consumable_id,
                    effect_type=active_effect.effect_type.value,
                    value=active_effect.value,
                    activated_at=active_effect.activated_at.isoformat(),
                    remaining_rounds=active_effect.remaining_rounds,
                )
            
            logger.info(
                "使用道具成功",
                player_id=player_id,
                consumable_id=consumable_id,
                quantity=quantity,
                remaining=remaining,
            )
            
            return ConsumableUsedMessage(
                consumable_id=consumable_id,
                quantity=quantity,
                remaining=remaining,
                effect=effect_data,
                seq=message.seq,
            )
        
        except Exception as e:
            logger.error(f"使用道具失败: {e}", exc_info=True)
            return ErrorMessage(
                code=5004,
                message=f"使用道具失败: {str(e)}",
                seq=message.seq,
            )
    
    async def handle_buy_consumable(
        self,
        session: "Session",
        message: BuyConsumableMessage,
    ) -> Optional[BaseMessage]:
        """
        处理购买道具请求
        
        Args:
            session: WebSocket 会话
            message: 购买道具消息
            
        Returns:
            响应消息
        """
        player_id = session.player_id
        consumable_id = message.consumable_id
        quantity = message.quantity
        use_currency = message.use_currency
        
        try:
            # 获取玩家金币和钻石（实际应从数据库获取）
            # 这里暂时使用模拟值
            gold = getattr(session, "gold", 10000)
            diamond = getattr(session, "diamond", 1000)
            
            # 购买道具
            pc, currency, cost, error = self.manager.buy_consumable(
                player_id=player_id,
                consumable_id=consumable_id,
                gold=gold,
                diamond=diamond,
                quantity=quantity,
                use_currency=use_currency,
            )
            
            if error:
                return ErrorMessage(
                    code=5005,
                    message=error,
                    seq=message.seq,
                )
            
            # 获取总数量
            total_quantity = self.manager.get_consumable_quantity(player_id, consumable_id)
            
            logger.info(
                "购买道具成功",
                player_id=player_id,
                consumable_id=consumable_id,
                quantity=quantity,
                total_quantity=total_quantity,
                currency=currency,
                cost=cost,
            )
            
            return ConsumableBoughtMessage(
                consumable_id=consumable_id,
                quantity=quantity,
                total_quantity=total_quantity,
                currency=currency,
                cost=cost,
                seq=message.seq,
            )
        
        except Exception as e:
            logger.error(f"购买道具失败: {e}", exc_info=True)
            return ErrorMessage(
                code=5006,
                message=f"购买道具失败: {str(e)}",
                seq=message.seq,
            )
    
    async def handle_get_consumable_history(
        self,
        session: "Session",
        message: GetConsumableHistoryMessage,
    ) -> Optional[BaseMessage]:
        """
        处理获取道具使用历史请求
        
        Args:
            session: WebSocket 会话
            message: 获取历史消息
            
        Returns:
            响应消息
        """
        player_id = session.player_id
        limit = message.limit
        
        try:
            # 获取使用历史
            history = self.manager.get_usage_history(player_id, limit)
            
            # 转换为消息格式
            history_data_list = [
                ConsumableUsageData(
                    consumable_id=h.consumable_id,
                    used_at=h.used_at.isoformat(),
                    quantity=h.quantity,
                    context=h.context,
                    context_id=h.context_id,
                    effect_applied=h.effect_applied,
                )
                for h in history
            ]
            
            logger.info(
                "获取道具使用历史",
                player_id=player_id,
                count=len(history_data_list),
            )
            
            return ConsumableHistoryMessage(
                history=history_data_list,
                total_count=len(history_data_list),
                seq=message.seq,
            )
        
        except Exception as e:
            logger.error(f"获取道具使用历史失败: {e}", exc_info=True)
            return ErrorMessage(
                code=5007,
                message=f"获取道具使用历史失败: {str(e)}",
                seq=message.seq,
            )


# 全局处理器实例
_consumable_ws_handler: Optional[ConsumableWSHandler] = None


def get_consumable_ws_handler(config_path: Optional[str] = None) -> ConsumableWSHandler:
    """
    获取道具 WebSocket 处理器单例
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        道具 WebSocket 处理器实例
    """
    global _consumable_ws_handler
    if _consumable_ws_handler is None:
        _consumable_ws_handler = ConsumableWSHandler(config_path)
    return _consumable_ws_handler


# ============================================================================
# 消息处理器注册
# ============================================================================

# 创建处理器实例
_consumable_handler_instance = ConsumableWSHandler()

# 注册消息处理器
@ws_handler.on_message(MessageType.GET_CONSUMABLES)
async def handle_get_consumables(session, message):
    return await _consumable_handler_instance.handle_get_consumables(session, message)

@ws_handler.on_message(MessageType.GET_PLAYER_CONSUMABLES)
async def handle_get_player_consumables(session, message):
    return await _consumable_handler_instance.handle_get_player_consumables(session, message)

@ws_handler.on_message(MessageType.BUY_CONSUMABLE)
async def handle_buy_consumable(session, message):
    return await _consumable_handler_instance.handle_buy_consumable(session, message)
