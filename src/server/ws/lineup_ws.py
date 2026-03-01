"""
王者之奕 - 阵容预设 WebSocket 处理器

本模块提供阵容预设相关的 WebSocket 消息处理：
- 保存预设
- 加载预设
- 删除预设
- 重命名预设
- 获取预设列表
- 应用预设

与主 WebSocket 处理器集成。
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..ws.handler import ws_handler
from ..lineup import (
    LineupManager,
    LineupPreset,
    LineupSlot,
    TargetSynergy,
    MAX_PRESETS_PER_PLAYER,
)
from ..lineup.models import EquipmentAssignment
from ...shared.protocol import (
    BaseMessage,
    ErrorMessage,
    LineupAppliedMessage,
    LineupApplyMessage,
    LineupDeletedMessage,
    LineupDeleteMessage,
    LineupLoadedMessage,
    LineupLoadMessage,
    LineupListMessage,
    LineupListResultMessage,
    LineupPresetData,
    LineupRenamedMessage,
    LineupRenameMessage,
    LineupSavedMessage,
    LineupSaveMessage,
    LineupSlotData,
    LineupSynergyData,
    MessageType,
)

from ..ws.handler import ws_handler
if TYPE_CHECKING:
    from ..ws.handler import Session

logger = logging.getLogger(__name__)


class LineupWSHandler:
    """
    阵容预设 WebSocket 处理器
    
    处理所有阵容预设相关的 WebSocket 消息。
    
    使用方式:
        handler = LineupWSHandler()
        
        @ws_handler.on_message(MessageType.LINEUP_SAVE)
        async def handle_lineup_save(session, message):
            return await lineup_handler.handle_save(session, message, db_session)
    """
    
    def __init__(self) -> None:
        """初始化处理器"""
        pass
    
    async def handle_save(
        self,
        session: "Session",
        message: LineupSaveMessage,
        db_session: AsyncSession,
    ) -> Optional[BaseMessage]:
        """
        处理保存预设请求
        
        Args:
            session: WebSocket 会话
            message: 保存预设消息
            db_session: 数据库会话
            
        Returns:
            响应消息
        """
        player_id = session.player_id
        
        try:
            manager = LineupManager(db_session)
            
            # 转换消息数据为内部模型
            slots = self._convert_slots(message.slots)
            synergies = self._convert_synergies(message.target_synergies)
            
            # 保存预设
            preset = await manager.save_preset(
                player_id=player_id,
                name=message.name,
                slots=slots,
                target_synergies=synergies,
                description=message.description,
                notes=message.notes,
            )
            
            logger.info(
                "保存阵容预设成功",
                player_id=player_id,
                preset_id=preset.preset_id,
                name=preset.name,
            )
            
            return LineupSavedMessage(
                preset=self._preset_to_data(preset),
                seq=message.seq,
            )
        
        except ValueError as e:
            logger.warning(
                "保存阵容预设失败",
                player_id=player_id,
                error=str(e),
            )
            return ErrorMessage(
                code=3001,
                message=str(e),
                seq=message.seq,
            )
        except Exception as e:
            logger.exception(
                "保存阵容预设异常",
                player_id=player_id,
                error=str(e),
            )
            return ErrorMessage(
                code=3000,
                message="保存预设失败",
                details={"error": str(e)},
                seq=message.seq,
            )
    
    async def handle_load(
        self,
        session: "Session",
        message: LineupLoadMessage,
        db_session: AsyncSession,
    ) -> Optional[BaseMessage]:
        """
        处理加载预设请求
        
        Args:
            session: WebSocket 会话
            message: 加载预设消息
            db_session: 数据库会话
            
        Returns:
            响应消息
        """
        player_id = session.player_id
        
        try:
            manager = LineupManager(db_session)
            preset = await manager.get_preset(message.preset_id, player_id)
            
            if preset is None:
                return ErrorMessage(
                    code=3002,
                    message="预设不存在",
                    seq=message.seq,
                )
            
            logger.info(
                "加载阵容预设成功",
                player_id=player_id,
                preset_id=preset.preset_id,
            )
            
            return LineupLoadedMessage(
                preset=self._preset_to_data(preset),
                seq=message.seq,
            )
        
        except Exception as e:
            logger.exception(
                "加载阵容预设异常",
                player_id=player_id,
                error=str(e),
            )
            return ErrorMessage(
                code=3000,
                message="加载预设失败",
                details={"error": str(e)},
                seq=message.seq,
            )
    
    async def handle_delete(
        self,
        session: "Session",
        message: LineupDeleteMessage,
        db_session: AsyncSession,
    ) -> Optional[BaseMessage]:
        """
        处理删除预设请求
        
        Args:
            session: WebSocket 会话
            message: 删除预设消息
            db_session: 数据库会话
            
        Returns:
            响应消息
        """
        player_id = session.player_id
        
        try:
            manager = LineupManager(db_session)
            success = await manager.delete_preset(message.preset_id, player_id)
            
            if not success:
                return ErrorMessage(
                    code=3002,
                    message="预设不存在或无权删除",
                    seq=message.seq,
                )
            
            logger.info(
                "删除阵容预设成功",
                player_id=player_id,
                preset_id=message.preset_id,
            )
            
            return LineupDeletedMessage(
                preset_id=message.preset_id,
                seq=message.seq,
            )
        
        except Exception as e:
            logger.exception(
                "删除阵容预设异常",
                player_id=player_id,
                error=str(e),
            )
            return ErrorMessage(
                code=3000,
                message="删除预设失败",
                details={"error": str(e)},
                seq=message.seq,
            )
    
    async def handle_rename(
        self,
        session: "Session",
        message: LineupRenameMessage,
        db_session: AsyncSession,
    ) -> Optional[BaseMessage]:
        """
        处理重命名预设请求
        
        Args:
            session: WebSocket 会话
            message: 重命名预设消息
            db_session: 数据库会话
            
        Returns:
            响应消息
        """
        player_id = session.player_id
        
        try:
            manager = LineupManager(db_session)
            preset = await manager.rename_preset(
                message.preset_id,
                player_id,
                message.new_name,
            )
            
            if preset is None:
                return ErrorMessage(
                    code=3002,
                    message="预设不存在或无权修改",
                    seq=message.seq,
                )
            
            logger.info(
                "重命名阵容预设成功",
                player_id=player_id,
                preset_id=message.preset_id,
                new_name=message.new_name,
            )
            
            return LineupRenamedMessage(
                preset_id=message.preset_id,
                new_name=message.new_name,
                seq=message.seq,
            )
        
        except Exception as e:
            logger.exception(
                "重命名阵容预设异常",
                player_id=player_id,
                error=str(e),
            )
            return ErrorMessage(
                code=3000,
                message="重命名预设失败",
                details={"error": str(e)},
                seq=message.seq,
            )
    
    async def handle_list(
        self,
        session: "Session",
        message: LineupListMessage,
        db_session: AsyncSession,
    ) -> Optional[BaseMessage]:
        """
        处理获取预设列表请求
        
        Args:
            session: WebSocket 会话
            message: 获取预设列表消息
            db_session: 数据库会话
            
        Returns:
            响应消息
        """
        player_id = session.player_id
        
        try:
            manager = LineupManager(db_session)
            presets = await manager.get_player_presets(player_id)
            
            preset_data_list = [self._preset_to_data(p) for p in presets]
            
            logger.info(
                "获取阵容预设列表",
                player_id=player_id,
                count=len(presets),
            )
            
            return LineupListResultMessage(
                presets=preset_data_list,
                max_presets=MAX_PRESETS_PER_PLAYER,
                seq=message.seq,
            )
        
        except Exception as e:
            logger.exception(
                "获取阵容预设列表异常",
                player_id=player_id,
                error=str(e),
            )
            return ErrorMessage(
                code=3000,
                message="获取预设列表失败",
                details={"error": str(e)},
                seq=message.seq,
            )
    
    async def handle_apply(
        self,
        session: "Session",
        message: LineupApplyMessage,
        db_session: AsyncSession,
    ) -> Optional[BaseMessage]:
        """
        处理应用预设请求
        
        Args:
            session: WebSocket 会话
            message: 应用预设消息
            db_session: 数据库会话
            
        Returns:
            响应消息
        """
        player_id = session.player_id
        
        try:
            manager = LineupManager(db_session)
            preset = await manager.get_preset(message.preset_id, player_id)
            
            if preset is None:
                return ErrorMessage(
                    code=3002,
                    message="预设不存在",
                    seq=message.seq,
                )
            
            # 应用预设，生成建议
            board_suggestion = manager.apply_preset_to_board(preset)
            
            # 转换槽位数据
            slots = [
                LineupSlotData(
                    hero_id=slot["hero_id"],
                    row=slot["row"],
                    col=slot["col"],
                    equipment=slot.get("equipment", []),
                    star_level=slot.get("star_level", 1),
                )
                for slot in board_suggestion.get("slots", [])
            ]
            
            logger.info(
                "应用阵容预设",
                player_id=player_id,
                preset_id=preset.preset_id,
                preset_name=preset.name,
            )
            
            return LineupAppliedMessage(
                preset_id=preset.preset_id,
                preset_name=preset.name,
                heroes_to_buy=board_suggestion.get("heroes_to_buy", []),
                slots=slots,
                seq=message.seq,
            )
        
        except Exception as e:
            logger.exception(
                "应用阵容预设异常",
                player_id=player_id,
                error=str(e),
            )
            return ErrorMessage(
                code=3000,
                message="应用预设失败",
                details={"error": str(e)},
                seq=message.seq,
            )
    
    # ========================================================================
    # 辅助方法
    # ========================================================================
    
    def _convert_slots(self, slot_data_list: list[LineupSlotData]) -> list[LineupSlot]:
        """转换消息数据为内部模型"""
        slots = []
        for data in slot_data_list:
            equipment = [
                EquipmentAssignment(equipment_id=eq_id, slot=i)
                for i, eq_id in enumerate(data.equipment)
            ]
            slot = LineupSlot(
                hero_id=data.hero_id,
                row=data.row,
                col=data.col,
                equipment=equipment,
                star_level=data.star_level,
            )
            slots.append(slot)
        return slots
    
    def _convert_synergies(
        self,
        synergy_data_list: list[LineupSynergyData],
    ) -> list[TargetSynergy]:
        """转换消息数据为内部模型"""
        return [
            TargetSynergy(
                synergy_id=data.synergy_id,
                target_count=data.target_count,
                priority=data.priority,
            )
            for data in synergy_data_list
        ]
    
    def _preset_to_data(self, preset: LineupPreset) -> LineupPresetData:
        """将内部模型转换为消息数据"""
        slots = [
            LineupSlotData(
                hero_id=slot.hero_id,
                row=slot.row,
                col=slot.col,
                equipment=[eq.equipment_id for eq in slot.equipment],
                star_level=slot.star_level,
            )
            for slot in preset.slots
        ]
        
        synergies = [
            LineupSynergyData(
                synergy_id=s.synergy_id,
                target_count=s.target_count,
                priority=s.priority,
            )
            for s in preset.target_synergies
        ]
        
        return LineupPresetData(
            preset_id=preset.preset_id,
            name=preset.name,
            description=preset.description,
            slots=slots,
            target_synergies=synergies,
            notes=preset.notes,
            created_at=preset.created_at.isoformat() if preset.created_at else None,
            updated_at=preset.updated_at.isoformat() if preset.updated_at else None,
        )


# 全局处理器实例
lineup_ws_handler = LineupWSHandler()
