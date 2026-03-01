"""
王者之奕 - AI教练系统数据模型

本模块定义AI教练系统的核心数据类：
- AISuggestion: AI建议
- CoachAnalysis: 对局分析
- LineupRecommendation: 阵容推荐
- EquipmentAdvice: 装备建议
- PositionAdvice: 站位建议
- RoundStrategy: 回合策略
- WinRatePrediction: 胜率预测
- MatchHistoryItem: 对局历史记录

用于AI教练功能的内存数据管理。
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SuggestionType(str, Enum):
    """建议类型枚举"""

    LINEUP = "lineup"  # 阵容建议
    EQUIPMENT = "equipment"  # 装备建议
    POSITION = "position"  # 站位建议
    ECONOMY = "economy"  # 经济建议
    HERO_BUY = "hero_buy"  # 英雄购买建议
    HERO_SELL = "hero_sell"  # 英雄出售建议
    LEVEL_UP = "level_up"  # 升级建议
    SYNERGY = "synergy"  # 羁绊建议


class Priority(str, Enum):
    """建议优先级"""

    LOW = "low"  # 低优先级
    MEDIUM = "medium"  # 中优先级
    HIGH = "high"  # 高优先级
    CRITICAL = "critical"  # 关键/紧急


class AnalysisType(str, Enum):
    """分析类型"""

    EARLY_GAME = "early_game"  # 前期（1-10回合）
    MID_GAME = "mid_game"  # 中期（11-20回合）
    LATE_GAME = "late_game"  # 后期（21+回合）
    POST_GAME = "post_game"  # 赛后分析


@dataclass
class AISuggestion:
    """
    AI建议

    代表AI教练给出的一条建议。

    Attributes:
        suggestion_id: 建议ID
        suggestion_type: 建议类型
        priority: 优先级
        title: 建议标题
        description: 建议详细描述
        reason: 建议原因
        action: 建议采取的行动
        expected_benefit: 预期收益
        confidence: 置信度（0-1）
        created_at: 创建时间
        metadata: 额外元数据
    """

    suggestion_id: str
    suggestion_type: SuggestionType
    priority: Priority
    title: str
    description: str
    reason: str
    action: dict[str, Any]
    expected_benefit: str
    confidence: float = 0.8
    created_at: int = field(default_factory=lambda: int(time.time() * 1000))
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "suggestion_id": self.suggestion_id,
            "suggestion_type": self.suggestion_type.value,
            "priority": self.priority.value,
            "title": self.title,
            "description": self.description,
            "reason": self.reason,
            "action": self.action,
            "expected_benefit": self.expected_benefit,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AISuggestion:
        """从字典创建"""
        return cls(
            suggestion_id=data["suggestion_id"],
            suggestion_type=SuggestionType(data["suggestion_type"]),
            priority=Priority(data["priority"]),
            title=data["title"],
            description=data["description"],
            reason=data["reason"],
            action=data["action"],
            expected_benefit=data["expected_benefit"],
            confidence=data.get("confidence", 0.8),
            created_at=data.get("created_at", int(time.time() * 1000)),
            metadata=data.get("metadata", {}),
        )


@dataclass
class EquipmentAdvice:
    """
    装备建议

    关于装备合成和分配的建议。

    Attributes:
        equipment_id: 装备ID
        equipment_name: 装备名称
        target_hero_id: 目标英雄ID
        reason: 建议原因
        recipe: 合成配方（如果需要合成）
        priority: 优先级
        expected_stat_boost: 预期属性提升
    """

    equipment_id: str
    equipment_name: str
    target_hero_id: str | None
    reason: str
    recipe: list[str] | None = None
    priority: Priority = Priority.MEDIUM
    expected_stat_boost: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "equipment_id": self.equipment_id,
            "equipment_name": self.equipment_name,
            "target_hero_id": self.target_hero_id,
            "reason": self.reason,
            "recipe": self.recipe,
            "priority": self.priority.value,
            "expected_stat_boost": self.expected_stat_boost,
        }


@dataclass
class PositionAdvice:
    """
    站位建议

    关于英雄在棋盘上的站位建议。

    Attributes:
        hero_id: 英雄ID
        hero_name: 英雄名称
        current_position: 当前位置
        recommended_position: 推荐位置
        reason: 建议原因
        priority: 优先级
        tactical_role: 战术角色（坦克/输出/辅助等）
    """

    hero_id: str
    hero_name: str
    current_position: dict[str, int] | None
    recommended_position: dict[str, int]
    reason: str
    priority: Priority = Priority.MEDIUM
    tactical_role: str = "fighter"

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "hero_id": self.hero_id,
            "hero_name": self.hero_name,
            "current_position": self.current_position,
            "recommended_position": self.recommended_position,
            "reason": self.reason,
            "priority": self.priority.value,
            "tactical_role": self.tactical_role,
        }


@dataclass
class RoundStrategy:
    """
    回合策略

    针对特定回合的策略建议。

    Attributes:
        round_num: 回合数
        phase: 游戏阶段
        strategy_type: 策略类型
        description: 策略描述
        key_actions: 关键行动列表
        focus_synergies: 重点羁绊
        economy_advice: 经济建议
        risk_level: 风险等级
        win_condition: 获胜条件
    """

    round_num: int
    phase: AnalysisType
    strategy_type: str  # aggressive / defensive / balanced / economic
    description: str
    key_actions: list[str] = field(default_factory=list)
    focus_synergies: list[str] = field(default_factory=list)
    economy_advice: str | None = None
    risk_level: str = "medium"  # low / medium / high
    win_condition: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "round_num": self.round_num,
            "phase": self.phase.value,
            "strategy_type": self.strategy_type,
            "description": self.description,
            "key_actions": self.key_actions,
            "focus_synergies": self.focus_synergies,
            "economy_advice": self.economy_advice,
            "risk_level": self.risk_level,
            "win_condition": self.win_condition,
        }


@dataclass
class WinRatePrediction:
    """
    胜率预测

    基于当前局势的胜率预测。

    Attributes:
        predicted_win_rate: 预测胜率（0-1）
        confidence: 置信度
        factors: 影响因素
        comparison_rank: 相比其他玩家的排名预测
        key_advantages: 关键优势
        key_weaknesses: 关键劣势
        improvement_suggestions: 改进建议
    """

    predicted_win_rate: float
    confidence: float
    factors: dict[str, float] = field(default_factory=dict)
    comparison_rank: int = 4
    key_advantages: list[str] = field(default_factory=list)
    key_weaknesses: list[str] = field(default_factory=list)
    improvement_suggestions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "predicted_win_rate": self.predicted_win_rate,
            "confidence": self.confidence,
            "factors": self.factors,
            "comparison_rank": self.comparison_rank,
            "key_advantages": self.key_advantages,
            "key_weaknesses": self.key_weaknesses,
            "improvement_suggestions": self.improvement_suggestions,
        }


@dataclass
class CoachAnalysis:
    """
    对局分析

    AI教练对对局的完整分析结果。

    Attributes:
        analysis_id: 分析ID
        player_id: 玩家ID
        game_id: 对局ID
        analysis_type: 分析类型
        round_num: 分析时的回合数
        lineup_score: 阵容评分（0-100）
        economy_score: 经济评分（0-100）
        synergy_score: 羁绊评分（0-100）
        position_score: 站位评分（0-100）
        overall_score: 综合评分（0-100）
        strengths: 优势列表
        weaknesses: 劣势列表
        suggestions: 建议列表
        win_rate_prediction: 胜率预测
        created_at: 创建时间
    """

    analysis_id: str
    player_id: int
    game_id: str
    analysis_type: AnalysisType
    round_num: int
    lineup_score: float = 50.0
    economy_score: float = 50.0
    synergy_score: float = 50.0
    position_score: float = 50.0
    overall_score: float = 50.0
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    suggestions: list[AISuggestion] = field(default_factory=list)
    win_rate_prediction: WinRatePrediction | None = None
    created_at: int = field(default_factory=lambda: int(time.time() * 1000))

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "analysis_id": self.analysis_id,
            "player_id": self.player_id,
            "game_id": self.game_id,
            "analysis_type": self.analysis_type.value,
            "round_num": self.round_num,
            "lineup_score": self.lineup_score,
            "economy_score": self.economy_score,
            "synergy_score": self.synergy_score,
            "position_score": self.position_score,
            "overall_score": self.overall_score,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "suggestions": [s.to_dict() for s in self.suggestions],
            "win_rate_prediction": self.win_rate_prediction.to_dict()
            if self.win_rate_prediction
            else None,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CoachAnalysis:
        """从字典创建"""
        suggestions = [AISuggestion.from_dict(s) for s in data.get("suggestions", [])]
        win_rate_data = data.get("win_rate_prediction")
        win_rate = WinRatePrediction(**win_rate_data) if win_rate_data else None

        return cls(
            analysis_id=data["analysis_id"],
            player_id=data["player_id"],
            game_id=data["game_id"],
            analysis_type=AnalysisType(data["analysis_type"]),
            round_num=data["round_num"],
            lineup_score=data.get("lineup_score", 50.0),
            economy_score=data.get("economy_score", 50.0),
            synergy_score=data.get("synergy_score", 50.0),
            position_score=data.get("position_score", 50.0),
            overall_score=data.get("overall_score", 50.0),
            strengths=data.get("strengths", []),
            weaknesses=data.get("weaknesses", []),
            suggestions=suggestions,
            win_rate_prediction=win_rate,
            created_at=data.get("created_at", int(time.time() * 1000)),
        )


@dataclass
class LineupRecommendation:
    """
    阵容推荐

    AI推荐的阵容配置。

    Attributes:
        lineup_id: 阵容ID
        name: 阵容名称
        description: 阵容描述
        difficulty: 难度等级（1-5）
        core_heroes: 核心英雄列表
        optional_heroes: 可选英雄列表
        synergies: 激活的羁绊
        play_style: 玩法风格
        early_game: 前期过渡阵容
        mid_game: 中期成型阵容
        late_game: 后期最终阵容
        key_items: 核心装备
        tips: 玩法提示
        win_rate: 该阵容的历史胜率
        popularity: 流行度
    """

    lineup_id: str
    name: str
    description: str
    difficulty: int = 3
    core_heroes: list[str] = field(default_factory=list)
    optional_heroes: list[str] = field(default_factory=list)
    synergies: dict[str, int] = field(default_factory=dict)  # 羁绊名 -> 等级
    play_style: str = "balanced"  # aggressive / defensive / balanced
    early_game: list[str] = field(default_factory=list)
    mid_game: list[str] = field(default_factory=list)
    late_game: list[str] = field(default_factory=list)
    key_items: list[str] = field(default_factory=list)
    tips: list[str] = field(default_factory=list)
    win_rate: float = 0.5
    popularity: float = 0.5

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "lineup_id": self.lineup_id,
            "name": self.name,
            "description": self.description,
            "difficulty": self.difficulty,
            "core_heroes": self.core_heroes,
            "optional_heroes": self.optional_heroes,
            "synergies": self.synergies,
            "play_style": self.play_style,
            "early_game": self.early_game,
            "mid_game": self.mid_game,
            "late_game": self.late_game,
            "key_items": self.key_items,
            "tips": self.tips,
            "win_rate": self.win_rate,
            "popularity": self.popularity,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LineupRecommendation:
        """从字典创建"""
        return cls(
            lineup_id=data["lineup_id"],
            name=data["name"],
            description=data["description"],
            difficulty=data.get("difficulty", 3),
            core_heroes=data.get("core_heroes", []),
            optional_heroes=data.get("optional_heroes", []),
            synergies=data.get("synergies", {}),
            play_style=data.get("play_style", "balanced"),
            early_game=data.get("early_game", []),
            mid_game=data.get("mid_game", []),
            late_game=data.get("late_game", []),
            key_items=data.get("key_items", []),
            tips=data.get("tips", []),
            win_rate=data.get("win_rate", 0.5),
            popularity=data.get("popularity", 0.5),
        )


@dataclass
class MatchHistoryItem:
    """
    对局历史记录

    用于AI教练分析玩家的历史对局数据。

    Attributes:
        match_id: 对局ID
        game_id: 游戏ID
        final_rank: 最终排名
        total_rounds: 总回合数
        duration_seconds: 对局时长
        final_lineup: 最终阵容
        final_synergies: 最终羁绊
        damage_dealt: 造成伤害
        damage_taken: 承受伤害
        gold_earned: 获得金币
        key_decisions: 关键决策
        analysis: 对局分析（如果有）
        played_at: 对局时间
    """

    match_id: str
    game_id: str
    final_rank: int
    total_rounds: int
    duration_seconds: int
    final_lineup: list[str] = field(default_factory=list)
    final_synergies: dict[str, int] = field(default_factory=dict)
    damage_dealt: int = 0
    damage_taken: int = 0
    gold_earned: int = 0
    key_decisions: list[str] = field(default_factory=list)
    analysis: CoachAnalysis | None = None
    played_at: int = field(default_factory=lambda: int(time.time() * 1000))

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "match_id": self.match_id,
            "game_id": self.game_id,
            "final_rank": self.final_rank,
            "total_rounds": self.total_rounds,
            "duration_seconds": self.duration_seconds,
            "final_lineup": self.final_lineup,
            "final_synergies": self.final_synergies,
            "damage_dealt": self.damage_dealt,
            "damage_taken": self.damage_taken,
            "gold_earned": self.gold_earned,
            "key_decisions": self.key_decisions,
            "analysis": self.analysis.to_dict() if self.analysis else None,
            "played_at": self.played_at,
        }

    @property
    def duration_minutes(self) -> float:
        """对局时长（分钟）"""
        return round(self.duration_seconds / 60, 1)

    @property
    def is_win(self) -> bool:
        """是否获胜（第一名）"""
        return self.final_rank == 1


@dataclass
class PlayerLearningStats:
    """
    玩家学习统计

    AI教练跟踪的玩家学习数据。

    Attributes:
        player_id: 玩家ID
        total_matches: 总对局数
        wins: 胜利次数
        top4_rate: 前4名率
        avg_rank: 平均排名
        favorite_synergies: 常用羁绊
        improvement_areas: 待改进领域
        recent_form: 最近状态趋势
        suggestions_followed: 采纳建议次数
        coaching_sessions: 教练会话次数
    """

    player_id: int
    total_matches: int = 0
    wins: int = 0
    top4_count: int = 0
    avg_rank: float = 4.0
    favorite_synergies: dict[str, int] = field(default_factory=dict)
    improvement_areas: list[str] = field(default_factory=list)
    recent_form: str = "stable"  # improving / declining / stable
    suggestions_followed: int = 0
    coaching_sessions: int = 0

    @property
    def win_rate(self) -> float:
        """胜率"""
        if self.total_matches == 0:
            return 0.0
        return round(self.wins / self.total_matches, 3)

    @property
    def top4_rate(self) -> float:
        """前4名率"""
        if self.total_matches == 0:
            return 0.0
        return round(self.top4_count / self.total_matches, 3)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "player_id": self.player_id,
            "total_matches": self.total_matches,
            "wins": self.wins,
            "top4_count": self.top4_count,
            "avg_rank": self.avg_rank,
            "win_rate": self.win_rate,
            "top4_rate": self.top4_rate,
            "favorite_synergies": self.favorite_synergies,
            "improvement_areas": self.improvement_areas,
            "recent_form": self.recent_form,
            "suggestions_followed": self.suggestions_followed,
            "coaching_sessions": self.coaching_sessions,
        }
