"""
王者之奕 - 投票数据库模型

本模块定义投票系统的数据库持久化模型：
- VotingPollDB: 投票主题
- VotingOptionDB: 投票选项
- PlayerVoteDB: 玩家投票记录
- VotingRewardClaimDB: 奖励领取记录

用于存储投票相关的持久化数据。
"""

from __future__ import annotations

from datetime import datetime

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
    func,
)
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.server.models.base import Base, IdMixin, TimestampMixin


class VotingPollDB(Base, IdMixin, TimestampMixin):
    """
    投票主题数据模型

    存储投票主题的完整信息。

    Attributes:
        id: 主键ID
        poll_id: 投票唯一ID
        title: 投票标题
        description: 投票描述
        voting_type: 投票类型
        status: 投票状态
        start_time: 开始时间
        end_time: 结束时间
        total_votes: 总票数
        total_voters: 参与人数
        min_vip_level: 最低VIP等级要求
        created_by: 创建者ID
        winning_option_id: 获胜选项ID
        tags: 标签列表
        participation_reward_config: 参与奖励配置
        win_bonus_reward_config: 投中额外奖励配置
        extra_data: 额外数据
    """

    __tablename__ = "voting_polls"
    __table_args__ = (
        UniqueConstraint("poll_id", name="uq_voting_poll_id"),
        Index("ix_voting_polls_type", "voting_type"),
        Index("ix_voting_polls_status", "status"),
        Index("ix_voting_polls_time", "start_time", "end_time"),
        {"comment": "投票主题表"},
    )

    poll_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        comment="投票唯一ID",
    )

    title: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="投票标题",
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment="投票描述",
    )

    voting_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="投票类型",
    )

    status: Mapped[str] = mapped_column(
        String(16),
        default="ongoing",
        nullable=False,
        comment="投票状态",
    )

    start_time: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="开始时间",
    )

    end_time: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="结束时间",
    )

    total_votes: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总票数",
    )

    total_voters: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="参与人数",
    )

    min_vip_level: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="最低VIP等级要求",
    )

    created_by: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="创建者ID",
    )

    winning_option_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="获胜选项ID",
    )

    tags: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="标签列表",
    )

    participation_reward_config: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="参与奖励配置",
    )

    win_bonus_reward_config: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="投中额外奖励配置",
    )

    extra_data: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="额外数据",
    )

    # 关系
    options: Mapped[list[VotingOptionDB]] = relationship(
        "VotingOptionDB",
        back_populates="poll",
        cascade="all, delete-orphan",
    )

    votes: Mapped[list[PlayerVoteDB]] = relationship(
        "PlayerVoteDB",
        back_populates="poll",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<VotingPollDB(poll_id='{self.poll_id}', title='{self.title}', status='{self.status}')>"

    def to_dict(self) -> dict:
        """转换为字典"""
        data = super().to_dict()
        data["start_time"] = self.start_time.isoformat() if self.start_time else None
        data["end_time"] = self.end_time.isoformat() if self.end_time else None
        return data


class VotingOptionDB(Base, IdMixin, TimestampMixin):
    """
    投票选项数据模型

    存储投票选项的信息。

    Attributes:
        id: 主键ID
        option_id: 选项唯一ID
        poll_id: 所属投票ID
        title: 选项标题
        description: 选项描述
        icon: 选项图标
        vote_count: 当前票数
        percentage: 得票百分比
        extra_data: 额外数据
    """

    __tablename__ = "voting_options"
    __table_args__ = (
        UniqueConstraint("option_id", name="uq_voting_option_id"),
        Index("ix_voting_options_poll_id", "poll_id"),
        Index("ix_voting_options_votes", "vote_count"),
        {"comment": "投票选项表"},
    )

    option_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        comment="选项唯一ID",
    )

    poll_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("voting_polls.poll_id", ondelete="CASCADE"),
        nullable=False,
        comment="所属投票ID",
    )

    title: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="选项标题",
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment="选项描述",
    )

    icon: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="选项图标",
    )

    vote_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="当前票数",
    )

    percentage: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="得票百分比",
    )

    extra_data: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="额外数据",
    )

    # 关系
    poll: Mapped[VotingPollDB] = relationship(
        "VotingPollDB",
        back_populates="options",
    )

    def __repr__(self) -> str:
        return f"<VotingOptionDB(option_id='{self.option_id}', title='{self.title}', votes={self.vote_count})>"

    def to_dict(self) -> dict:
        """转换为字典"""
        data = super().to_dict()
        data["percentage"] = round(self.percentage, 2)
        return data


class PlayerVoteDB(Base, IdMixin, TimestampMixin):
    """
    玩家投票记录数据模型

    存储玩家的投票记录。

    Attributes:
        id: 主键ID
        vote_id: 投票记录唯一ID
        poll_id: 投票ID
        player_id: 玩家ID
        option_id: 选择的选项ID
        vote_weight: 投票权重
        vote_time: 投票时间
        is_vip: 是否为VIP玩家
        rewards_claimed: 是否已领取奖励
        rewards_claimed_at: 奖励领取时间
    """

    __tablename__ = "player_votes"
    __table_args__ = (
        UniqueConstraint("poll_id", "player_id", name="uq_player_poll_vote"),
        UniqueConstraint("vote_id", name="uq_player_vote_id"),
        Index("ix_player_votes_player_id", "player_id"),
        Index("ix_player_votes_poll_id", "poll_id"),
        Index("ix_player_votes_time", "vote_time"),
        {"comment": "玩家投票记录表"},
    )

    vote_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        comment="投票记录唯一ID",
    )

    poll_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("voting_polls.poll_id", ondelete="CASCADE"),
        nullable=False,
        comment="投票ID",
    )

    player_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="玩家ID",
    )

    option_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("voting_options.option_id", ondelete="CASCADE"),
        nullable=False,
        comment="选择的选项ID",
    )

    vote_weight: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="投票权重",
    )

    vote_time: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False,
        comment="投票时间",
    )

    is_vip: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否为VIP玩家",
    )

    rewards_claimed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否已领取奖励",
    )

    rewards_claimed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="奖励领取时间",
    )

    # 关系
    poll: Mapped[VotingPollDB] = relationship(
        "VotingPollDB",
        back_populates="votes",
    )

    def __repr__(self) -> str:
        return f"<PlayerVoteDB(vote_id='{self.vote_id}', player_id='{self.player_id}', poll_id='{self.poll_id}')>"

    def to_dict(self) -> dict:
        """转换为字典"""
        data = super().to_dict()
        data["vote_time"] = self.vote_time.isoformat() if self.vote_time else None
        data["rewards_claimed_at"] = (
            self.rewards_claimed_at.isoformat() if self.rewards_claimed_at else None
        )
        return data


class VotingRewardClaimDB(Base, IdMixin, TimestampMixin):
    """
    投票奖励领取记录数据模型

    存储奖励领取的详细记录。

    Attributes:
        id: 主键ID
        vote_id: 投票记录ID
        player_id: 玩家ID
        poll_id: 投票ID
        reward_type: 奖励类型
        item_id: 物品ID
        quantity: 数量
        is_bonus: 是否为投中额外奖励
        claimed_at: 领取时间
    """

    __tablename__ = "voting_reward_claims"
    __table_args__ = (
        Index("ix_voting_reward_claims_player_id", "player_id"),
        Index("ix_voting_reward_claims_poll_id", "poll_id"),
        Index("ix_voting_reward_claims_time", "claimed_at"),
        {"comment": "投票奖励领取记录表"},
    )

    vote_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="投票记录ID",
    )

    player_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="玩家ID",
    )

    poll_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="投票ID",
    )

    reward_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="奖励类型",
    )

    item_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="物品ID",
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="数量",
    )

    is_bonus: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否为投中额外奖励",
    )

    claimed_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False,
        comment="领取时间",
    )

    def __repr__(self) -> str:
        return f"<VotingRewardClaimDB(player_id='{self.player_id}', poll_id='{self.poll_id}', type='{self.reward_type}')>"
