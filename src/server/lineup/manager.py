"""
王者之奕 - 阵容预设管理器

本模块提供阵容预设的管理功能：
- LineupManager: 阵容预设管理器类
- 保存、加载、删除、重命名预设
- 应用预设到对局

用于管理玩家的阵容预设数据。
"""

from __future__ import annotations

import logging
import secrets
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    LineupPreset,
    LineupSlot,
    TargetSynergy,
    MAX_PRESETS_PER_PLAYER,
)

logger = logging.getLogger(__name__)


class LineupManager:
    """
    阵容预设管理器
    
    提供阵容预设的 CRUD 操作和应用功能。
    
    使用方式:
        async with get_session() as session:
            manager = LineupManager(session)
            
            # 保存预设
            preset = await manager.save_preset(player_id, name, slots)
            
            # 获取预设列表
            presets = await manager.get_player_presets(player_id)
    """
    
    def __init__(self, session: AsyncSession) -> None:
        """
        初始化管理器
        
        Args:
            session: 异步数据库会话
        """
        self.session = session
        # 延迟导入避免循环依赖
        self._model = None
    
    def _get_model(self):
        """延迟获取数据库模型"""
        if self._model is None:
            from ..db.models.lineup import LineupPresetDB
            self._model = LineupPresetDB
        return self._model
    
    def _generate_preset_id(self) -> str:
        """生成预设ID"""
        return f"preset_{secrets.token_hex(8)}"
    
    async def save_preset(
        self,
        player_id: str,
        name: str,
        slots: List[LineupSlot],
        target_synergies: Optional[List[TargetSynergy]] = None,
        description: str = "",
        notes: str = "",
    ) -> LineupPreset:
        """
        保存阵容预设
        
        Args:
            player_id: 玩家ID
            name: 预设名称
            slots: 英雄槽位列表
            target_synergies: 目标羁绊列表
            description: 预设描述
            notes: 策略备注
            
        Returns:
            创建的阵容预设
            
        Raises:
            ValueError: 超过预设数量限制
        """
        model = self._get_model()
        
        # 检查预设数量限制
        count = await self._count_player_presets(player_id)
        if count >= MAX_PRESETS_PER_PLAYER:
            raise ValueError(f"最多只能保存 {MAX_PRESETS_PER_PLAYER} 个预设")
        
        # 创建预设
        preset_id = self._generate_preset_id()
        preset = LineupPreset(
            preset_id=preset_id,
            player_id=player_id,
            name=name,
            description=description,
            slots=slots,
            target_synergies=target_synergies or [],
            notes=notes,
        )
        
        # 保存到数据库
        db_preset = model(
            preset_id=preset_id,
            player_id=player_id,
            name=name,
            description=description,
            slots_data=[s.to_dict() for s in slots],
            synergies_data=[s.to_dict() for s in (target_synergies or [])],
            notes=notes,
            version=1,
        )
        
        self.session.add(db_preset)
        await self.session.flush()
        
        logger.info(
            "保存阵容预设",
            player_id=player_id,
            preset_id=preset_id,
            name=name,
            hero_count=len(slots),
        )
        
        return preset
    
    async def update_preset(
        self,
        preset_id: str,
        player_id: str,
        name: Optional[str] = None,
        slots: Optional[List[LineupSlot]] = None,
        target_synergies: Optional[List[TargetSynergy]] = None,
        description: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Optional[LineupPreset]:
        """
        更新阵容预设
        
        Args:
            preset_id: 预设ID
            player_id: 玩家ID（用于权限验证）
            name: 新名称
            slots: 新英雄槽位
            target_synergies: 新目标羁绊
            description: 新描述
            notes: 新备注
            
        Returns:
            更新后的预设，不存在返回None
        """
        model = self._get_model()
        
        # 获取现有预设
        db_preset = await self._get_db_preset(preset_id, player_id)
        if db_preset is None:
            return None
        
        # 更新字段
        if name is not None:
            db_preset.name = name
        if slots is not None:
            db_preset.slots_data = [s.to_dict() for s in slots]
        if target_synergies is not None:
            db_preset.synergies_data = [s.to_dict() for s in target_synergies]
        if description is not None:
            db_preset.description = description
        if notes is not None:
            db_preset.notes = notes
        
        db_preset.updated_at = datetime.now()
        db_preset.version += 1
        
        await self.session.flush()
        
        logger.info(
            "更新阵容预设",
            player_id=player_id,
            preset_id=preset_id,
            version=db_preset.version,
        )
        
        return self._db_to_preset(db_preset)
    
    async def rename_preset(
        self,
        preset_id: str,
        player_id: str,
        new_name: str,
    ) -> Optional[LineupPreset]:
        """
        重命名预设
        
        Args:
            preset_id: 预设ID
            player_id: 玩家ID
            new_name: 新名称
            
        Returns:
            更新后的预设
        """
        return await self.update_preset(preset_id, player_id, name=new_name)
    
    async def delete_preset(
        self,
        preset_id: str,
        player_id: str,
    ) -> bool:
        """
        删除预设
        
        Args:
            preset_id: 预设ID
            player_id: 玩家ID（用于权限验证）
            
        Returns:
            是否成功
        """
        model = self._get_model()
        
        stmt = (
            delete(model)
            .where(and_(
                model.preset_id == preset_id,
                model.player_id == player_id,
            ))
        )
        
        result = await self.session.execute(stmt)
        
        if result.rowcount > 0:
            logger.info(
                "删除阵容预设",
                player_id=player_id,
                preset_id=preset_id,
            )
            return True
        
        return False
    
    async def get_preset(
        self,
        preset_id: str,
        player_id: str,
    ) -> Optional[LineupPreset]:
        """
        获取单个预设
        
        Args:
            preset_id: 预设ID
            player_id: 玩家ID
            
        Returns:
            阵容预设
        """
        db_preset = await self._get_db_preset(preset_id, player_id)
        if db_preset is None:
            return None
        return self._db_to_preset(db_preset)
    
    async def get_player_presets(
        self,
        player_id: str,
    ) -> List[LineupPreset]:
        """
        获取玩家的所有预设
        
        Args:
            player_id: 玩家ID
            
        Returns:
            预设列表
        """
        model = self._get_model()
        
        stmt = (
            select(model)
            .where(model.player_id == player_id)
            .order_by(model.updated_at.desc())
        )
        
        result = await self.session.scalars(stmt)
        db_presets = result.all()
        
        return [self._db_to_preset(db) for db in db_presets]
    
    async def get_preset_count(self, player_id: str) -> int:
        """
        获取玩家预设数量
        
        Args:
            player_id: 玩家ID
            
        Returns:
            预设数量
        """
        return await self._count_player_presets(player_id)
    
    async def can_save_preset(self, player_id: str) -> bool:
        """
        检查是否可以保存新预设
        
        Args:
            player_id: 玩家ID
            
        Returns:
            是否可以保存
        """
        count = await self._count_player_presets(player_id)
        return count < MAX_PRESETS_PER_PLAYER
    
    def apply_preset_to_board(
        self,
        preset: LineupPreset,
        current_board: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        应用预设到棋盘
        
        注意：此方法仅生成建议的棋盘状态，实际应用需要客户端执行操作。
        
        Args:
            preset: 阵容预设
            current_board: 当前棋盘状态（可选）
            
        Returns:
            应用预设后的棋盘状态建议
        """
        # 获取预设中的英雄位置
        hero_positions = preset.get_heroes_at_positions()
        
        # 构建棋盘状态
        board = {
            "preset_id": preset.preset_id,
            "preset_name": preset.name,
            "slots": [],
            "heroes_to_buy": [],
            "target_synergies": [],
        }
        
        # 添加槽位信息
        for slot in preset.slots:
            board["slots"].append({
                "hero_id": slot.hero_id,
                "row": slot.row,
                "col": slot.col,
                "equipment": [eq.equipment_id for eq in slot.equipment],
                "star_level": slot.star_level,
            })
        
        # 添加目标羁绊
        for synergy in preset.target_synergies:
            board["target_synergies"].append({
                "synergy_id": synergy.synergy_id,
                "target_count": synergy.target_count,
                "priority": synergy.priority,
            })
        
        # 如果提供了当前棋盘，计算需要购买的英雄
        if current_board:
            current_heroes = set()
            for slot_data in current_board.get("slots", []):
                current_heroes.add(slot_data.get("hero_id"))
            
            preset_heroes = set(preset.hero_ids)
            heroes_to_buy = preset_heroes - current_heroes
            board["heroes_to_buy"] = list(heroes_to_buy)
        
        return board
    
    async def _get_db_preset(
        self,
        preset_id: str,
        player_id: str,
    ):
        """获取数据库预设记录"""
        model = self._get_model()
        
        stmt = (
            select(model)
            .where(and_(
                model.preset_id == preset_id,
                model.player_id == player_id,
            ))
        )
        
        return await self.session.scalar(stmt)
    
    async def _count_player_presets(self, player_id: str) -> int:
        """统计玩家预设数量"""
        model = self._get_model()
        
        stmt = (
            select(func.count())
            .select_from(model)
            .where(model.player_id == player_id)
        )
        
        count = await self.session.scalar(stmt)
        return count or 0
    
    def _db_to_preset(self, db_preset) -> LineupPreset:
        """将数据库模型转换为业务模型"""
        slots = [
            LineupSlot.from_dict(s)
            for s in db_preset.slots_data
        ]
        
        synergies = [
            TargetSynergy.from_dict(s)
            for s in db_preset.synergies_data
        ]
        
        return LineupPreset(
            preset_id=db_preset.preset_id,
            player_id=db_preset.player_id,
            name=db_preset.name,
            description=db_preset.description or "",
            slots=slots,
            target_synergies=synergies,
            notes=db_preset.notes or "",
            created_at=db_preset.created_at,
            updated_at=db_preset.updated_at,
            version=db_preset.version,
        )


# 便捷函数
async def create_lineup_manager(session: AsyncSession) -> LineupManager:
    """
    创建阵容预设管理器
    
    Args:
        session: 异步数据库会话
        
    Returns:
        管理器实例
    """
    return LineupManager(session)
