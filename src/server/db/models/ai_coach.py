"""
王者之奕 - AI教练系统数据库模型

本模块定义AI教练相关的数据库模型：
- AICoachDB: AI教练会话记录
- CoachAnalysisDB: 对局分析记录
- PlayerLearningDB: 玩家学习数据

用于持久化AI教练数据。
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
    func,
)
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, IdMixin, TimestampMixin


class AICoachDB(Base, IdMixin, TimestampMixin):
    """
    AI教练会话模型

    记录玩家使用AI教练的会话信息。

    Attributes:
        id: 主键ID
        player_id: 玩家ID（外键）
        game_id: 对局ID
        session_type: 会话类型 (realtime / post_game / training)
        started_at: 开始时间
        ended_at: 结束时间
        suggestion_count: 建议数量
        suggestions_followed: 采纳建议数量
        final_rank: 最终排名
        is_helpful: 玩家是否认为有帮助
        feedback: 玩家反馈
        metadata: 额外数据
    """

    __tablename__ = "ai_coach_sessions"
    __table_args__ = (
        Index("ix_ai_coach_sessions_player_id", "player_id"),
        Index("ix_ai_coach_sessions_game_id", "game_id"),
        Index("ix_ai_coach_sessions_started_at", "started_at"),
        {"comment": "AI教练会话表"},
    )

    player_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
        comment="玩家ID",
    )

    game_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="对局ID",
    )

    session_type: Mapped[str] = mapped_column(
        String(20),
        default="realtime",
        nullable=False,
        comment="会话类型",
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        comment="开始时间",
    )

    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="结束时间",
    )

    suggestion_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="建议数量",
    )

    suggestions_followed: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="采纳建议数量",
    )

    final_rank: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="最终排名",
    )

    is_helpful: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
        comment="玩家是否认为有帮助",
    )

    feedback: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="玩家反馈",
    )

    metadata: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="额外数据",
    )

    def __repr__(self) -> str:
        return f"<AICoachDB(id={self.id}, player_id={self.player_id}, type='{self.session_type}')>"

    @property
    def follow_rate(self) -> float:
        """建议采纳率"""
        if self.suggestion_count == 0:
            return 0.0
        return round(self.suggestions_followed / self.suggestion_count, 2)

    @property
    def duration_seconds(self) -> int:
        """会话时长（秒）"""
        if self.ended_at is None:
            return 0
        return int((self.ended_at - self.started_at).total_seconds())


class CoachAnalysisDB(Base, IdMixin, TimestampMixin):
    """
    对局分析记录模型

    存储AI教练对对局的分析结果。

    Attributes:
        id: 主键ID
        player_id: 玩家ID（外键）
        game_id: 对局ID
        analysis_id: 分析ID（业务ID）
        analysis_type: 分析类型
        round_num: 分析时的回合数
        lineup_score: 阵容评分
        economy_score: 经济评分
        synergy_score: 羁绊评分
        position_score: 站位评分
        overall_score: 综合评分
        strengths: 优势列表（JSON）
        weaknesses: 劣势列表（JSON）
        suggestions: 建议列表（JSON）
        win_rate_prediction: 胜率预测（JSON）
        is_post_game: 是否赛后分析
        created_at: 创建时间
    """

    __tablename__ = "coach_analyses"
    __table_args__ = (
        Index("ix_coach_analyses_player_id", "player_id"),
        Index("ix_coach_analyses_game_id", "game_id"),
        Index("ix_coach_analyses_analysis_id", "analysis_id", unique=True),
        Index("ix_coach_analyses_created_at", "created_at"),
        {"comment": "对局分析记录表"},
    )

    player_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
        comment="玩家ID",
    )

    game_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="对局ID",
    )

    analysis_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        comment="分析ID",
    )

    analysis_type: Mapped[str] = mapped_column(
        String(20),
        default="mid_game",
        nullable=False,
        comment="分析类型",
    )

    round_num: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="分析时的回合数",
    )

    lineup_score: Mapped[float] = mapped_column(
        Float,
        default=50.0,
        nullable=False,
        comment="阵容评分",
    )

    economy_score: Mapped[float] = mapped_column(
        Float,
        default=50.0,
        nullable=False,
        comment="经济评分",
    )

    synergy_score: Mapped[float] = mapped_column(
        Float,
        default=50.0,
        nullable=False,
        comment="羁绊评分",
    )

    position_score: Mapped[float] = mapped_column(
        Float,
        default=50.0,
        nullable=False,
        comment="站位评分",
    )

    overall_score: Mapped[float] = mapped_column(
        Float,
        default=50.0,
        nullable=False,
        comment="综合评分",
    )

    strengths: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="优势列表",
    )

    weaknesses: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="劣势列表",
    )

    suggestions: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="建议列表",
    )

    win_rate_prediction: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="胜率预测",
    )

    is_post_game: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否赛后分析",
    )

    def __repr__(self) -> str:
        return f"<CoachAnalysisDB(id={self.id}, player_id={self.player_id}, score={self.overall_score})>"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "player_id": self.player_id,
            "game_id": self.game_id,
            "analysis_id": self.analysis_id,
            "analysis_type": self.analysis_type,
            "round_num": self.round_num,
            "lineup_score": self.lineup_score,
            "economy_score": self.economy_score,
            "synergy_score": self.synergy_score,
            "position_score": self.position_score,
            "overall_score": self.overall_score,
            "strengths": self.strengths or [],
            "weaknesses": self.weaknesses or [],
            "suggestions": self.suggestions or [],
            "win_rate_prediction": self.win_rate_prediction,
            "is_post_game": self.is_post_game,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PlayerLearningDB(Base, IdMixin, TimestampMixin):
    """
    玩家学习数据模型

    存储玩家的AI教练学习统计数据。

    Attributes:
        id: 主键ID
        player_id: 玩家ID（外键，唯一）
        total_coach_sessions: 教练会话总数
        total_suggestions: 收到的建议总数
        suggestions_followed: 采纳的建议数
        total_analyses: 分析记录数
        avg_overall_score: 平均综合评分
        best_score: 最高综合评分
        improvement_areas: 待改进领域（JSON）
        favorite_synergies: 常用羁绊（JSON）
        learning_progress: 学习进度（JSON）
        last_coach_at: 最后使用教练时间
    """

    __tablename__ = "player_learning"
    __table_args__ = (
        Index("ix_player_learning_player_id", "player_id", unique=True),
        Index("ix_player_learning_last_coach_at", "last_coach_at"),
        {"comment": "玩家学习数据表"},
    )

    player_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        comment="玩家ID",
    )

    total_coach_sessions: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="教练会话总数",
    )

    total_suggestions: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="收到的建议总数",
    )

    suggestions_followed: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="采纳的建议数",
    )

    total_analyses: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="分析记录数",
    )

    avg_overall_score: Mapped[float] = mapped_column(
        Float,
        default=50.0,
        nullable=False,
        comment="平均综合评分",
    )

    best_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="最高综合评分",
    )

    improvement_areas: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="待改进领域",
    )

    favorite_synergies: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="常用羁绊",
    )

    learning_progress: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="学习进度",
    )

    last_coach_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="最后使用教练时间",
    )

    def __repr__(self) -> str:
        return (
            f"<PlayerLearningDB(player_id={self.player_id}, sessions={self.total_coach_sessions})>"
        )

    @property
    def follow_rate(self) -> float:
        """建议采纳率"""
        if self.total_suggestions == 0:
            return 0.0
        return round(self.suggestions_followed / self.total_suggestions, 2)

    def update_stats(
        self,
        overall_score: float,
        suggestions_count: int,
        followed_count: int,
    ) -> None:
        """
        更新统计数据

        Args:
            overall_score: 本次综合评分
            suggestions_count: 本次建议数
            followed_count: 本次采纳数
        """
        # 更新会话数
        self.total_coach_sessions += 1

        # 更新建议统计
        self.total_suggestions += suggestions_count
        self.suggestions_followed += followed_count

        # 更新分析数
        self.total_analyses += 1

        # 更新平均分
        old_avg = self.avg_overall_score
        old_count = self.total_analyses - 1
        if old_count > 0:
            self.avg_overall_score = (old_avg * old_count + overall_score) / self.total_analyses
        else:
            self.avg_overall_score = overall_score

        # 更新最高分
        if overall_score > self.best_score:
            self.best_score = overall_score

        # 更新时间
        self.last_coach_at = datetime.now()

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "player_id": self.player_id,
            "total_coach_sessions": self.total_coach_sessions,
            "total_suggestions": self.total_suggestions,
            "suggestions_followed": self.suggestions_followed,
            "follow_rate": self.follow_rate,
            "total_analyses": self.total_analyses,
            "avg_overall_score": round(self.avg_overall_score, 1),
            "best_score": round(self.best_score, 1),
            "improvement_areas": self.improvement_areas or [],
            "favorite_synergies": self.favorite_synergies or {},
            "learning_progress": self.learning_progress or {},
            "last_coach_at": self.last_coach_at.isoformat() if self.last_coach_at else None,
        }


class LineupRecommendationDB(Base, IdMixin, TimestampMixin):
    """
    阵容推荐模型

    存储预设的阵容推荐数据。

    Attributes:
        id: 主键ID
        lineup_id: 阵容ID（业务ID，唯一）
        name: 阵容名称
        description: 阵容描述
        difficulty: 难度等级（1-5）
        core_heroes: 核心英雄列表（JSON）
        optional_heroes: 可选英雄列表（JSON）
        synergies: 激活的羁绊（JSON）
        play_style: 玩法风格
        early_game: 前期过渡阵容（JSON）
        mid_game: 中期成型阵容（JSON）
        late_game: 后期最终阵容（JSON）
        key_items: 核心装备（JSON）
        tips: 玩法提示（JSON）
        win_rate: 历史胜率
        popularity: 流行度
        is_meta: 是否当前版本强势
        is_enabled: 是否启用
        version: 版本号
    """

    __tablename__ = "lineup_recommendations"
    __table_args__ = (
        Index("ix_lineup_recommendations_lineup_id", "lineup_id", unique=True),
        Index("ix_lineup_recommendations_is_meta", "is_meta"),
        Index("ix_lineup_recommendations_win_rate", "win_rate"),
        {"comment": "阵容推荐表"},
    )

    lineup_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        comment="阵容ID",
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="阵容名称",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="阵容描述",
    )

    difficulty: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False,
        comment="难度等级（1-5）",
    )

    core_heroes: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="核心英雄列表",
    )

    optional_heroes: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="可选英雄列表",
    )

    synergies: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="激活的羁绊",
    )

    play_style: Mapped[str] = mapped_column(
        String(20),
        default="balanced",
        nullable=False,
        comment="玩法风格",
    )

    early_game: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="前期过渡阵容",
    )

    mid_game: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="中期成型阵容",
    )

    late_game: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="后期最终阵容",
    )

    key_items: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="核心装备",
    )

    tips: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="玩法提示",
    )

    win_rate: Mapped[float] = mapped_column(
        Float,
        default=0.5,
        nullable=False,
        comment="历史胜率",
    )

    popularity: Mapped[float] = mapped_column(
        Float,
        default=0.5,
        nullable=False,
        comment="流行度",
    )

    is_meta: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否当前版本强势",
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
        comment="版本号",
    )

    def __repr__(self) -> str:
        return f"<LineupRecommendationDB(id={self.id}, name='{self.name}')>"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "lineup_id": self.lineup_id,
            "name": self.name,
            "description": self.description,
            "difficulty": self.difficulty,
            "core_heroes": self.core_heroes or [],
            "optional_heroes": self.optional_heroes or [],
            "synergies": self.synergies or {},
            "play_style": self.play_style,
            "early_game": self.early_game or [],
            "mid_game": self.mid_game or [],
            "late_game": self.late_game or [],
            "key_items": self.key_items or [],
            "tips": self.tips or [],
            "win_rate": self.win_rate,
            "popularity": self.popularity,
            "is_meta": self.is_meta,
            "is_enabled": self.is_enabled,
            "version": self.version,
        }
