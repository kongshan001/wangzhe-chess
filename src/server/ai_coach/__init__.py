"""
王者之奕 - AI教练系统

本模块提供AI教练功能，帮助玩家提升游戏水平：
- 阵容分析与建议
- 装备合成建议
- 站位优化
- 回合策略
- 胜率预测
- 历史对局分析

主要导出:
- AICoachManager: AI教练管理器
- 数据模型类
- 便捷函数
"""

from .manager import (
    META_LINEUPS,
    AICoachManager,
    get_ai_coach_manager,
)
from .models import (
    AISuggestion,
    AnalysisType,
    CoachAnalysis,
    EquipmentAdvice,
    LineupRecommendation,
    MatchHistoryItem,
    PlayerLearningStats,
    PositionAdvice,
    Priority,
    RoundStrategy,
    SuggestionType,
    WinRatePrediction,
)

__all__ = [
    # 管理器
    "AICoachManager",
    "get_ai_coach_manager",
    # 数据模型
    "AISuggestion",
    "AnalysisType",
    "CoachAnalysis",
    "EquipmentAdvice",
    "LineupRecommendation",
    "MatchHistoryItem",
    "PlayerLearningStats",
    "PositionAdvice",
    "Priority",
    "RoundStrategy",
    "SuggestionType",
    "WinRatePrediction",
    # 常量
    "META_LINEUPS",
]
