"""
王者之奕 - 英雄配置模型

本模块定义英雄配置相关的数据库模型：
- HeroConfigDB: 英雄基础配置
- HeroVersionDB: 英雄版本历史
- SynergyConfigDB: 羁绊配置
- GameConfigDB: 游戏全局配置
- SeasonConfigDB: 赛季配置

支持热更新和版本管理。
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum as PyEnum
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, IdMixin, TimestampMixin


class HeroStatus(str, PyEnum):
    """英雄状态枚举"""

    ACTIVE = "active"  # 可用
    DISABLED = "disabled"  # 禁用
    UPCOMING = "upcoming"  # 即将上线
    REMOVED = "removed"  # 已移除


class SynergyType(str, PyEnum):
    """羁绊类型枚举"""

    RACE = "race"  # 种族
    CLASS = "class"  # 职业


class HeroConfigDB(Base, IdMixin, TimestampMixin):
    """
    英雄配置模型

    存储英雄的基础配置数据，支持热更新和版本管理。

    Attributes:
        id: 主键ID
        hero_id: 英雄唯一ID（业务ID）
        name: 英雄名称
        description: 英雄描述
        cost: 购买费用（1-5）
        race: 种族
        profession: 职业
        base_hp: 基础生命值
        base_attack: 基础攻击力
        base_defense: 基础防御力
        attack_speed: 攻击速度
        attack_range: 攻击距离
        skill_name: 技能名称
        skill_description: 技能描述
        skill_mana_cost: 技能蓝耗
        skill_damage: 技能伤害
        skill_damage_type: 技能伤害类型
        skill_target_type: 技能目标类型
        skill_effects: 技能效果（JSON）
        star_multipliers: 星级倍率（JSON）
        tags: 标签（JSON数组）
        status: 英雄状态
        is_enabled: 是否启用
        version: 当前版本号
        changelog: 更新日志（JSON）
    """

    __tablename__ = "hero_configs"
    __table_args__ = (
        Index("ix_hero_configs_hero_id", "hero_id", unique=True),
        Index("ix_hero_configs_cost", "cost"),
        Index("ix_hero_configs_race", "race"),
        Index("ix_hero_configs_profession", "profession"),
        Index("ix_hero_configs_status", "status"),
        {"comment": "英雄配置表"},
    )

    # 基本信息
    hero_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        comment="英雄唯一ID",
    )
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="英雄名称",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="英雄描述",
    )
    cost: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="购买费用",
    )

    # 羁绊信息
    race: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="种族",
    )
    profession: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="职业",
    )

    # 基础属性
    base_hp: Mapped[int] = mapped_column(
        Integer,
        default=100,
        nullable=False,
        comment="基础生命值",
    )
    base_attack: Mapped[int] = mapped_column(
        Integer,
        default=10,
        nullable=False,
        comment="基础攻击力",
    )
    base_defense: Mapped[int] = mapped_column(
        Integer,
        default=10,
        nullable=False,
        comment="基础防御力",
    )
    attack_speed: Mapped[float] = mapped_column(
        Float,
        default=1.0,
        nullable=False,
        comment="攻击速度",
    )
    attack_range: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="攻击距离",
    )

    # 技能信息
    skill_name: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="技能名称",
    )
    skill_description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="技能描述",
    )
    skill_mana_cost: Mapped[int] = mapped_column(
        Integer,
        default=50,
        nullable=False,
        comment="技能蓝耗",
    )
    skill_damage: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="技能伤害",
    )
    skill_damage_type: Mapped[str] = mapped_column(
        String(20),
        default="magical",
        nullable=False,
        comment="技能伤害类型",
    )
    skill_target_type: Mapped[str] = mapped_column(
        String(20),
        default="single",
        nullable=False,
        comment="技能目标类型",
    )
    skill_effects: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="技能效果",
    )

    # 其他配置
    star_multipliers: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="星级倍率",
    )
    tags: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="标签",
    )

    # 状态管理
    status: Mapped[str] = mapped_column(
        String(20),
        default=HeroStatus.ACTIVE.value,
        nullable=False,
        comment="英雄状态",
    )
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否启用",
    )

    # 版本管理
    version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="当前版本号",
    )
    changelog: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="更新日志",
    )

    # 关联关系
    versions: Mapped[list[HeroVersionDB]] = relationship(
        "HeroVersionDB",
        back_populates="hero",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<HeroConfigDB(id={self.id}, hero_id='{self.hero_id}', name='{self.name}')>"

    def create_version_snapshot(self, reason: str = "") -> HeroVersionDB:
        """
        创建当前配置的版本快照

        Args:
            reason: 版本说明

        Returns:
            新创建的版本记录
        """
        return HeroVersionDB(
            hero_id=self.id,
            version_number=self.version,
            config_snapshot=self.to_dict(),
            change_reason=reason,
        )

    def apply_update(
        self,
        updates: dict[str, Any],
        reason: str = "",
    ) -> HeroVersionDB:
        """
        应用配置更新并创建版本记录

        Args:
            updates: 更新内容
            reason: 更新原因

        Returns:
            旧版本快照
        """
        # 创建旧版本快照
        old_version = self.create_version_snapshot(reason)

        # 应用更新
        for key, value in updates.items():
            if hasattr(self, key) and key not in {"id", "hero_id", "created_at"}:
                setattr(self, key, value)

        # 更新版本号
        self.version += 1

        # 添加更新日志
        if self.changelog is None:
            self.changelog = []
        self.changelog.append(
            {
                "version": self.version,
                "timestamp": datetime.now().isoformat(),
                "reason": reason,
                "changes": updates,
            }
        )

        return old_version

    def to_game_template(self) -> dict[str, Any]:
        """
        转换为游戏使用的英雄模板格式

        Returns:
            游戏模板字典
        """
        return {
            "hero_id": self.hero_id,
            "name": self.name,
            "cost": self.cost,
            "race": self.race,
            "profession": self.profession,
            "base_hp": self.base_hp,
            "base_attack": self.base_attack,
            "base_defense": self.base_defense,
            "attack_speed": self.attack_speed,
            "skill": {
                "name": self.skill_name,
                "description": self.skill_description or "",
                "mana_cost": self.skill_mana_cost,
                "damage": self.skill_damage,
                "damage_type": self.skill_damage_type,
                "target_type": self.skill_target_type,
                "effect_data": self.skill_effects or {},
            }
            if self.skill_name
            else None,
        }


class HeroVersionDB(Base, IdMixin, TimestampMixin):
    """
    英雄版本历史模型

    存储英雄配置的历史版本，用于回滚和追溯。

    Attributes:
        id: 主键ID
        hero_id: 英雄配置ID（外键）
        version_number: 版本号
        config_snapshot: 配置快照（JSON）
        change_reason: 变更原因
        changed_by: 变更人
    """

    __tablename__ = "hero_versions"
    __table_args__ = (
        UniqueConstraint("hero_id", "version_number", name="uq_hero_version"),
        Index("ix_hero_versions_hero_id", "hero_id"),
        Index("ix_hero_versions_version", "version_number"),
        {"comment": "英雄版本历史表"},
    )

    hero_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("hero_configs.id", ondelete="CASCADE"),
        nullable=False,
        comment="英雄配置ID",
    )

    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="版本号",
    )

    config_snapshot: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        comment="配置快照",
    )

    change_reason: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="变更原因",
    )

    changed_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="变更人",
    )

    # 关联关系
    hero: Mapped[HeroConfigDB] = relationship(
        "HeroConfigDB",
        back_populates="versions",
    )

    def __repr__(self) -> str:
        return f"<HeroVersionDB(hero_id={self.hero_id}, version={self.version_number})>"


class SynergyConfigDB(Base, IdMixin, TimestampMixin):
    """
    羁绊配置模型

    存储羁绊的配置数据。

    Attributes:
        id: 主键ID
        synergy_id: 羁绊唯一ID
        name: 羁绊名称
        synergy_type: 羁绊类型（种族/职业）
        description: 羁绊描述
        levels: 羁绊等级配置（JSON）
        is_enabled: 是否启用
        version: 当前版本号
    """

    __tablename__ = "synergy_configs"
    __table_args__ = (
        Index("ix_synergy_configs_synergy_id", "synergy_id", unique=True),
        Index("ix_synergy_configs_type", "synergy_type"),
        {"comment": "羁绊配置表"},
    )

    synergy_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        comment="羁绊唯一ID",
    )

    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="羁绊名称",
    )

    synergy_type: Mapped[str] = mapped_column(
        String(20),
        default=SynergyType.RACE.value,
        nullable=False,
        comment="羁绊类型",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="羁绊描述",
    )

    levels: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        comment="羁绊等级配置",
    )

    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否启用",
    )

    version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="当前版本号",
    )

    def __repr__(self) -> str:
        return (
            f"<SynergyConfigDB(id={self.id}, synergy_id='{self.synergy_id}', name='{self.name}')>"
        )

    def get_level_for_count(self, count: int) -> dict[str, Any] | None:
        """
        根据英雄数量获取对应的羁绊等级

        Args:
            count: 英雄数量

        Returns:
            羁绊等级配置，如果未激活返回None
        """
        active_level = None
        for level in sorted(self.levels, key=lambda x: x.get("required_count", 0)):
            if count >= level.get("required_count", 0):
                active_level = level
            else:
                break
        return active_level


class GameConfigDB(Base, IdMixin, TimestampMixin):
    """
    游戏全局配置模型

    存储游戏的全局配置参数。

    Attributes:
        id: 主键ID
        config_key: 配置键
        config_value: 配置值（JSON）
        description: 配置描述
        category: 配置分类
        is_active: 是否激活
        valid_from: 生效开始时间
        valid_until: 生效结束时间
    """

    __tablename__ = "game_configs"
    __table_args__ = (
        Index("ix_game_configs_key", "config_key", unique=True),
        Index("ix_game_configs_category", "category"),
        {"comment": "游戏全局配置表"},
    )

    config_key: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        comment="配置键",
    )

    config_value: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        comment="配置值",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="配置描述",
    )

    category: Mapped[str] = mapped_column(
        String(50),
        default="general",
        nullable=False,
        comment="配置分类",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否激活",
    )

    valid_from: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="生效开始时间",
    )

    valid_until: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="生效结束时间",
    )

    def __repr__(self) -> str:
        return f"<GameConfigDB(key='{self.config_key}', category='{self.category}')>"

    @property
    def is_valid(self) -> bool:
        """检查配置是否在有效期内"""
        now = datetime.now()
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        return self.is_active


class SeasonConfigDB(Base, IdMixin, TimestampMixin):
    """
    赛季配置模型

    存储赛季相关的配置数据。

    Attributes:
        id: 主键ID
        season_id: 赛季ID
        season_name: 赛季名称
        start_time: 赛季开始时间
        end_time: 赛季结束时间
        is_current: 是否当前赛季
        rank_reset_rule: 段位重置规则（JSON）
        rewards: 赛季奖励配置（JSON）
        hero_pool: 英雄池配置（JSON）
    """

    __tablename__ = "season_configs"
    __table_args__ = (
        Index("ix_season_configs_season_id", "season_id", unique=True),
        Index("ix_season_configs_is_current", "is_current"),
        Index("ix_season_configs_time_range", "start_time", "end_time"),
        {"comment": "赛季配置表"},
    )

    season_id: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        comment="赛季ID",
    )

    season_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="赛季名称",
    )

    start_time: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        comment="赛季开始时间",
    )

    end_time: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        comment="赛季结束时间",
    )

    is_current: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否当前赛季",
    )

    rank_reset_rule: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="段位重置规则",
    )

    rewards: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="赛季奖励配置",
    )

    hero_pool: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="英雄池配置",
    )

    def __repr__(self) -> str:
        return f"<SeasonConfigDB(season_id='{self.season_id}', name='{self.season_name}')>"

    @property
    def is_active(self) -> bool:
        """检查赛季是否进行中"""
        now = datetime.now()
        return self.start_time <= now <= self.end_time
