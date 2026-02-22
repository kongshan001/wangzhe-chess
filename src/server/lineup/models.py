"""
王者之奕 - 阵容预设数据模型

本模块定义阵容预设系统的核心数据类：
- LineupSlot: 单个英雄槽位信息
- LineupPreset: 完整阵容预设

用于存储和管理玩家的阵容预设配置。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class EquipmentAssignment:
    """
    装备分配信息
    
    定义装备与英雄的绑定关系。
    
    Attributes:
        equipment_id: 装备ID
        slot: 装备槽位（0-2）
    """
    equipment_id: str
    slot: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "equipment_id": self.equipment_id,
            "slot": self.slot,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EquipmentAssignment":
        """从字典创建"""
        return cls(
            equipment_id=data.get("equipment_id", ""),
            slot=data.get("slot", 0),
        )


@dataclass
class LineupSlot:
    """
    英雄槽位信息
    
    定义单个英雄在阵容中的位置和装备信息。
    
    Attributes:
        hero_id: 英雄ID
        row: 棋盘行位置（0-7）
        col: 棋盘列位置（0-6）
        equipment: 装备分配列表
        star_level: 星级（1-3）
    """
    hero_id: str
    row: int = 0
    col: int = 0
    equipment: List[EquipmentAssignment] = field(default_factory=list)
    star_level: int = 1
    
    @property
    def total_equipment_count(self) -> int:
        """获取装备总数"""
        return len(self.equipment)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "hero_id": self.hero_id,
            "row": self.row,
            "col": self.col,
            "equipment": [e.to_dict() for e in self.equipment],
            "star_level": self.star_level,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LineupSlot":
        """从字典创建"""
        equipment_data = data.get("equipment", [])
        equipment = [
            EquipmentAssignment.from_dict(e) if isinstance(e, dict) else e
            for e in equipment_data
        ]
        
        return cls(
            hero_id=data.get("hero_id", ""),
            row=data.get("row", 0),
            col=data.get("col", 0),
            equipment=equipment,
            star_level=data.get("star_level", 1),
        )
    
    def add_equipment(self, equipment_id: str, slot: int = 0) -> bool:
        """
        添加装备
        
        Args:
            equipment_id: 装备ID
            slot: 装备槽位
            
        Returns:
            是否成功（最多3件装备）
        """
        if len(self.equipment) >= 3:
            return False
        
        # 检查槽位是否已占用
        for eq in self.equipment:
            if eq.slot == slot:
                return False
        
        self.equipment.append(EquipmentAssignment(equipment_id, slot))
        return True
    
    def remove_equipment(self, equipment_id: str) -> bool:
        """
        移除装备
        
        Args:
            equipment_id: 装备ID
            
        Returns:
            是否成功
        """
        for i, eq in enumerate(self.equipment):
            if eq.equipment_id == equipment_id:
                self.equipment.pop(i)
                return True
        return False


@dataclass
class TargetSynergy:
    """
    目标羁绊信息
    
    定义阵容预设中期望激活的羁绊。
    
    Attributes:
        synergy_id: 羁绊ID
        target_count: 目标英雄数量
        priority: 优先级（1-5，5最高）
        note: 备注
    """
    synergy_id: str
    target_count: int = 1
    priority: int = 3
    note: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "synergy_id": self.synergy_id,
            "target_count": self.target_count,
            "priority": self.priority,
            "note": self.note,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TargetSynergy":
        """从字典创建"""
        return cls(
            synergy_id=data.get("synergy_id", ""),
            target_count=data.get("target_count", 1),
            priority=data.get("priority", 3),
            note=data.get("note", ""),
        )


@dataclass
class LineupPreset:
    """
    阵容预设
    
    完整的阵容配置，包括英雄站位、装备分配和目标羁绊。
    
    Attributes:
        preset_id: 预设唯一ID
        player_id: 所属玩家ID
        name: 预设名称
        description: 预设描述
        slots: 英雄槽位列表
        target_synergies: 目标羁绊列表
        notes: 策略备注
        created_at: 创建时间
        updated_at: 更新时间
        version: 版本号
    """
    preset_id: str
    player_id: str
    name: str
    description: str = ""
    slots: List[LineupSlot] = field(default_factory=list)
    target_synergies: List[TargetSynergy] = field(default_factory=list)
    notes: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    version: int = 1
    
    def __post_init__(self):
        """初始化时间戳"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "preset_id": self.preset_id,
            "player_id": self.player_id,
            "name": self.name,
            "description": self.description,
            "slots": [s.to_dict() for s in self.slots],
            "target_synergies": [s.to_dict() for s in self.target_synergies],
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "version": self.version,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LineupPreset":
        """从字典创建"""
        slots_data = data.get("slots", [])
        slots = [
            LineupSlot.from_dict(s) if isinstance(s, dict) else s
            for s in slots_data
        ]
        
        synergies_data = data.get("target_synergies", [])
        target_synergies = [
            TargetSynergy.from_dict(s) if isinstance(s, dict) else s
            for s in synergies_data
        ]
        
        created_at = data.get("created_at")
        if created_at and isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        updated_at = data.get("updated_at")
        if updated_at and isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        
        return cls(
            preset_id=data.get("preset_id", ""),
            player_id=data.get("player_id", ""),
            name=data.get("name", "未命名阵容"),
            description=data.get("description", ""),
            slots=slots,
            target_synergies=target_synergies,
            notes=data.get("notes", ""),
            created_at=created_at,
            updated_at=updated_at,
            version=data.get("version", 1),
        )
    
    def add_slot(self, slot: LineupSlot) -> bool:
        """
        添加英雄槽位
        
        Args:
            slot: 英雄槽位
            
        Returns:
            是否成功（最多9个英雄）
        """
        if len(self.slots) >= 9:
            return False
        
        self.slots.append(slot)
        self._update_timestamp()
        return True
    
    def remove_slot(self, hero_id: str) -> bool:
        """
        移除英雄槽位
        
        Args:
            hero_id: 英雄ID
            
        Returns:
            是否成功
        """
        for i, slot in enumerate(self.slots):
            if slot.hero_id == hero_id:
                self.slots.pop(i)
                self._update_timestamp()
                return True
        return False
    
    def update_slot(self, hero_id: str, **kwargs) -> bool:
        """
        更新英雄槽位信息
        
        Args:
            hero_id: 英雄ID
            **kwargs: 要更新的字段
            
        Returns:
            是否成功
        """
        for slot in self.slots:
            if slot.hero_id == hero_id:
                for key, value in kwargs.items():
                    if hasattr(slot, key):
                        setattr(slot, key, value)
                self._update_timestamp()
                return True
        return False
    
    def get_slot(self, hero_id: str) -> Optional[LineupSlot]:
        """
        获取英雄槽位
        
        Args:
            hero_id: 英雄ID
            
        Returns:
            英雄槽位，不存在返回None
        """
        for slot in self.slots:
            if slot.hero_id == hero_id:
                return slot
        return None
    
    def add_target_synergy(self, synergy: TargetSynergy) -> None:
        """
        添加目标羁绊
        
        Args:
            synergy: 目标羁绊
        """
        self.target_synergies.append(synergy)
        self._update_timestamp()
    
    def remove_target_synergy(self, synergy_id: str) -> bool:
        """
        移除目标羁绊
        
        Args:
            synergy_id: 羁绊ID
            
        Returns:
            是否成功
        """
        for i, synergy in enumerate(self.target_synergies):
            if synergy.synergy_id == synergy_id:
                self.target_synergies.pop(i)
                self._update_timestamp()
                return True
        return False
    
    def _update_timestamp(self) -> None:
        """更新时间戳"""
        self.updated_at = datetime.now()
        self.version += 1
    
    @property
    def hero_count(self) -> int:
        """获取英雄数量"""
        return len(self.slots)
    
    @property
    def hero_ids(self) -> List[str]:
        """获取所有英雄ID"""
        return [slot.hero_id for slot in self.slots]
    
    def get_heroes_at_positions(self) -> Dict[tuple, str]:
        """
        获取位置到英雄ID的映射
        
        Returns:
            (row, col) -> hero_id 的字典
        """
        return {(slot.row, slot.col): slot.hero_id for slot in self.slots}
    
    def is_valid(self) -> bool:
        """
        验证阵容是否有效
        
        Returns:
            是否有效
        """
        # 检查是否有重复位置
        positions = set()
        for slot in self.slots:
            pos = (slot.row, slot.col)
            if pos in positions:
                return False
            positions.add(pos)
        
        # 检查位置是否在有效范围内
        for slot in self.slots:
            if not (0 <= slot.row <= 7 and 0 <= slot.col <= 6):
                return False
        
        return True


# 预设限制常量
MAX_PRESETS_PER_PLAYER = 5
MAX_HEROES_PER_PRESET = 9
MAX_EQUIPMENT_PER_HERO = 3
