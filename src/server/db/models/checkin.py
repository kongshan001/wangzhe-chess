"""
王者之奕 - 签到数据库模型

本模块定义签到系统的数据库持久化模型：
- CheckinDB: 签到记录
- CheckinStreakDB: 连续签到数据

用于存储签到相关的持久化数据。
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from src.server.models.base import Base, IdMixin, TimestampMixin


class CheckinDB(Base, IdMixin, TimestampMixin):
    """
    签到记录数据模型

    存储玩家的签到记录。

    Attributes:
        id: 主键ID
        player_id: 玩家ID
        checkin_date: 签到日期
        checkin_time: 签到时间
        day_in_cycle: 周期内的第几天（1-7）
        streak_days: 签到时的连续签到天数
        rewards: 获得的奖励（JSON）
        is_supplement: 是否补签
        supplement_cost: 补签消耗钻石
        is_claimed: 是否已领取奖励
        claimed_at: 领取时间
    """

    __tablename__ = "checkin_records"
    __table_args__ = (
        UniqueConstraint("player_id", "checkin_date", name="uq_player_checkin_date"),
        Index("ix_checkin_records_player_id", "player_id"),
        Index("ix_checkin_records_checkin_date", "checkin_date"),
        Index("ix_checkin_records_player_date", "player_id", "checkin_date"),
        {"comment": "签到记录表"},
    )

    player_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="玩家ID",
    )

    checkin_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="签到日期",
    )

    checkin_time: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False,
        comment="签到时间",
    )

    day_in_cycle: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="周期天数(1-7)",
    )

    streak_days: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="连续签到天数",
    )

    rewards: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="获得的奖励",
    )

    is_supplement: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否补签",
    )

    supplement_cost: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="补签消耗钻石",
    )

    is_claimed: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否已领取奖励",
    )

    claimed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="领取时间",
    )

    def __repr__(self) -> str:
        return f"<CheckinDB(player_id='{self.player_id}', date='{self.checkin_date}')>"

    def to_dict(self) -> dict:
        """转换为字典"""
        data = super().to_dict()
        data["checkin_date"] = self.checkin_date.isoformat()
        data["checkin_time"] = self.checkin_time.isoformat() if self.checkin_time else None
        data["claimed_at"] = self.claimed_at.isoformat() if self.claimed_at else None
        return data

    def set_rewards(self, rewards: list) -> None:
        """设置奖励列表"""
        self.rewards = {"rewards": rewards}

    def get_rewards(self) -> list:
        """获取奖励列表"""
        return self.rewards.get("rewards", []) if self.rewards else []


class CheckinStreakDB(Base, IdMixin, TimestampMixin):
    """
    连续签到数据模型

    存储玩家的连续签到统计信息。

    Attributes:
        id: 主键ID
        player_id: 玩家ID
        current_streak: 当前连续签到天数
        max_streak: 历史最大连续签到天数
        last_checkin_date: 最后签到日期
        monthly_count: 本月签到天数
        total_count: 总签到天数
        cycle_start_date: 当前周期开始日期
        last_reset_month: 上次重置月份
    """

    __tablename__ = "checkin_streaks"
    __table_args__ = (
        UniqueConstraint("player_id", name="uq_player_streak"),
        Index("ix_checkin_streaks_player_id", "player_id"),
        Index("ix_checkin_streaks_current", "current_streak"),
        Index("ix_checkin_streaks_max", "max_streak"),
        {"comment": "连续签到统计表"},
    )

    player_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        comment="玩家ID",
    )

    current_streak: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="当前连续签到天数",
    )

    max_streak: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="历史最大连续签到天数",
    )

    last_checkin_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="最后签到日期",
    )

    monthly_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="本月签到天数",
    )

    total_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总签到天数",
    )

    cycle_start_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="当前周期开始日期",
    )

    last_reset_month: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="上次重置月份(YYYYMM格式)",
    )

    def __repr__(self) -> str:
        return f"<CheckinStreakDB(player_id='{self.player_id}', streak={self.current_streak})>"

    def to_dict(self) -> dict:
        """转换为字典"""
        data = super().to_dict()
        data["last_checkin_date"] = (
            self.last_checkin_date.isoformat() if self.last_checkin_date else None
        )
        data["cycle_start_date"] = (
            self.cycle_start_date.isoformat() if self.cycle_start_date else None
        )
        return data

    def update_streak(self, checkin_date: date) -> bool:
        """
        更新连续签到天数

        Args:
            checkin_date: 签到日期

        Returns:
            是否为连续签到
        """
        from datetime import timedelta

        is_continuous = False

        if self.last_checkin_date is None:
            # 首次签到
            self.current_streak = 1
            self.cycle_start_date = checkin_date
        elif checkin_date == self.last_checkin_date:
            # 同一天，不更新
            return False
        elif checkin_date == self.last_checkin_date + timedelta(days=1):
            # 连续签到
            self.current_streak += 1
            is_continuous = True
        else:
            # 中断，重新开始
            self.current_streak = 1
            self.cycle_start_date = checkin_date

        self.last_checkin_date = checkin_date
        self.total_count += 1

        # 更新月签到数（检查是否需要重置）
        current_month = checkin_date.year * 100 + checkin_date.month
        if self.last_reset_month is None or self.last_reset_month != current_month:
            self.monthly_count = 1
            self.last_reset_month = current_month
        else:
            self.monthly_count += 1

        # 更新最大连续签到
        if self.current_streak > self.max_streak:
            self.max_streak = self.current_streak

        return is_continuous

    def check_and_reset_monthly(self, current_date: date) -> None:
        """
        检查并重置月签到数

        Args:
            current_date: 当前日期
        """
        current_month = current_date.year * 100 + current_date.month
        if self.last_reset_month is None or self.last_reset_month != current_month:
            self.monthly_count = 0
            self.last_reset_month = current_month
