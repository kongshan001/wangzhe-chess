"""
王者之奕 - 阵容预设数据库模型

本模块定义阵容预设的数据库持久化模型：
- LineupPresetDB: 阵容预设数据表

用于存储玩家的阵容预设配置。
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from ..models.base import Base, IdMixin, TimestampMixin


class LineupPresetDB(Base, IdMixin, TimestampMixin):
    """
    阵容预设数据库模型

    存储玩家保存的阵容预设配置。

    Attributes:
        id: 主键ID
        preset_id: 预设唯一ID
        player_id: 玩家ID（外键）
        name: 预设名称
        description: 预设描述
        slots_data: 英雄槽位数据（JSON）
        synergies_data: 目标羁绊数据（JSON）
        notes: 策略备注
        version: 版本号
        is_active: 是否激活
    """

    __tablename__ = "lineup_presets"
    __table_args__ = (
        UniqueConstraint("player_id", "name", name="uq_player_preset_name"),
        Index("ix_lineup_presets_player_id", "player_id"),
        Index("ix_lineup_presets_updated_at", "updated_at"),
        {"comment": "阵容预设表"},
    )

    # 主键和唯一标识
    preset_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        comment="预设唯一ID",
    )

    # 玩家关联
    player_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
        comment="玩家ID",
    )

    # 基本信息
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="预设名称",
    )
    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="预设描述",
    )

    # 阵容数据（JSON格式存储）
    slots_data: Mapped[list[dict]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="英雄槽位数据",
    )
    synergies_data: Mapped[list[dict]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="目标羁绊数据",
    )

    # 策略备注
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="策略备注",
    )

    # 版本控制
    version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="版本号",
    )

    # 状态
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否激活",
    )

    def __repr__(self) -> str:
        return f"<LineupPresetDB(preset_id='{self.preset_id}', player_id={self.player_id}, name='{self.name}')>"

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        data = super().to_dict()
        return data

    @property
    def hero_count(self) -> int:
        """获取英雄数量"""
        return len(self.slots_data) if self.slots_data else 0

    @property
    def synergy_count(self) -> int:
        """获取目标羁绊数量"""
        return len(self.synergies_data) if self.synergies_data else 0
