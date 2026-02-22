"""
王者之奕 - AI教练系统 WebSocket 处理器

本模块提供AI教练系统相关的 WebSocket 消息处理：
- 获取教练建议
- 分析阵容
- 获取阵容推荐
- 获取对局历史
- 获取装备建议
- 获取站位建议
- 获取回合策略
- 获取胜率预测

与主 WebSocket 处理器集成。
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Optional

from ..ai_coach import (
    AISuggestion,
    AICoachManager,
    CoachAnalysis,
    EquipmentAdvice,
    LineupRecommendation,
    MatchHistoryItem,
    PositionAdvice,
    RoundStrategy,
    WinRatePrediction,
    get_ai_coach_manager,
)
from ...shared.protocol import (
    BaseMessage,
    ErrorMessage,
    MessageType,
    GetCoachSuggestionsMessage,
    CoachSuggestionsMessage,
    AnalyzeLineupMessage,
    LineupAnalysisMessage,
    GetLineupRecommendationsMessage,
    LineupRecommendationsMessage,
    GetMatchHistoryMessage,
    MatchHistoryMessage,
    GetEquipmentAdviceMessage,
    EquipmentAdviceMessage,
    GetPositionAdviceMessage,
    PositionAdviceMessage,
    GetRoundStrategyMessage,
    RoundStrategyMessage,
    GetWinRatePredictionMessage,
    WinRatePredictionMessage,
    AISuggestionData,
    CoachAnalysisData,
    LineupRecommendationData,
    MatchHistoryItemData,
    EquipmentAdviceData,
    PositionAdviceData,
    RoundStrategyData,
    WinRatePredictionData,
)

if TYPE_CHECKING:
    from ..ws.handler import Session

logger = logging.getLogger(__name__)


class AICoachWSHandler:
    """
    AI教练系统 WebSocket 处理器
    
    处理所有AI教练相关的 WebSocket 消息。
    
    使用方式:
        handler = AICoachWSHandler()
        
        @ws_handler.on_message(MessageType.GET_COACH_SUGGESTIONS)
        async def handle_get_coach_suggestions(session, message):
            return await coach_handler.handle_get_coach_suggestions(session, message)
    """
    
    def __init__(self) -> None:
        """初始化处理器"""
        self._manager: Optional[AICoachManager] = None
    
    @property
    def manager(self) -> AICoachManager:
        """获取AI教练管理器"""
        if self._manager is None:
            self._manager = get_ai_coach_manager()
        return self._manager
    
    # ========================================================================
    # 消息处理
    # ========================================================================
    
    async def handle_get_coach_suggestions(
        self,
        session: "Session",
        message: GetCoachSuggestionsMessage,
    ) -> Optional[BaseMessage]:
        """
        处理获取教练建议请求
        
        Args:
            session: WebSocket 会话
            message: 获取教练建议消息
            
        Returns:
            响应消息
        """
        player_id = session.player_id
        
        try:
            # 获取游戏状态
            game_state = message.game_state or {}
            
            # 分析阵容获取建议
            analysis = self.manager.analyze_lineup(player_id, game_state)
            
            # 转换建议为消息格式
            suggestions_data = [
                AISuggestionData(
                    suggestion_id=s.suggestion_id,
                    suggestion_type=s.suggestion_type.value,
                    priority=s.priority.value,
                    title=s.title,
                    description=s.description,
                    reason=s.reason,
                    action=s.action,
                    expected_benefit=s.expected_benefit,
                    confidence=s.confidence,
                )
                for s in analysis.suggestions
            ]
            
            logger.debug(
                "获取教练建议",
                extra={
                    "player_id": player_id,
                    "suggestion_count": len(suggestions_data),
                }
            )
            
            return CoachSuggestionsMessage(
                suggestions=suggestions_data,
                overall_score=analysis.overall_score,
                seq=message.seq,
            )
        
        except Exception as e:
            logger.exception(
                "获取教练建议异常",
                extra={"player_id": player_id, "error": str(e)},
            )
            return ErrorMessage(
                code=7000,
                message="获取教练建议失败",
                details={"error": str(e)},
                seq=message.seq,
            )
    
    async def handle_analyze_lineup(
        self,
        session: "Session",
        message: AnalyzeLineupMessage,
    ) -> Optional[BaseMessage]:
        """
        处理分析阵容请求
        
        Args:
            session: WebSocket 会话
            message: 分析阵容消息
            
        Returns:
            响应消息
        """
        player_id = session.player_id
        
        try:
            # 获取游戏状态
            game_state = message.game_state or {}
            
            # 分析阵容
            analysis = self.manager.analyze_lineup(player_id, game_state)
            
            # 转换为消息格式
            analysis_data = self._convert_analysis_to_data(analysis)
            
            logger.info(
                "分析阵容",
                extra={
                    "player_id": player_id,
                    "overall_score": analysis.overall_score,
                    "round_num": analysis.round_num,
                }
            )
            
            return LineupAnalysisMessage(
                analysis=analysis_data,
                seq=message.seq,
            )
        
        except Exception as e:
            logger.exception(
                "分析阵容异常",
                extra={"player_id": player_id, "error": str(e)},
            )
            return ErrorMessage(
                code=7001,
                message="分析阵容失败",
                details={"error": str(e)},
                seq=message.seq,
            )
    
    async def handle_get_lineup_recommendations(
        self,
        session: "Session",
        message: GetLineupRecommendationsMessage,
    ) -> Optional[BaseMessage]:
        """
        处理获取阵容推荐请求
        
        Args:
            session: WebSocket 会话
            message: 获取阵容推荐消息
            
        Returns:
            响应消息
        """
        player_id = session.player_id
        
        try:
            # 获取当前英雄
            current_heroes = message.current_heroes or []
            
            # 获取推荐
            recommendations = self.manager.get_lineup_recommendations(
                player_id=player_id,
                current_heroes=current_heroes,
                limit=message.limit or 5,
            )
            
            # 转换为消息格式
            recommendations_data = [
                self._convert_lineup_to_data(r) for r in recommendations
            ]
            
            logger.debug(
                "获取阵容推荐",
                extra={
                    "player_id": player_id,
                    "recommendation_count": len(recommendations_data),
                }
            )
            
            return LineupRecommendationsMessage(
                recommendations=recommendations_data,
                seq=message.seq,
            )
        
        except Exception as e:
            logger.exception(
                "获取阵容推荐异常",
                extra={"player_id": player_id, "error": str(e)},
            )
            return ErrorMessage(
                code=7002,
                message="获取阵容推荐失败",
                details={"error": str(e)},
                seq=message.seq,
            )
    
    async def handle_get_match_history(
        self,
        session: "Session",
        message: GetMatchHistoryMessage,
    ) -> Optional[BaseMessage]:
        """
        处理获取对局历史请求
        
        Args:
            session: WebSocket 会话
            message: 获取对局历史消息
            
        Returns:
            响应消息
        """
        player_id = session.player_id
        
        try:
            # 获取历史记录
            history = self.manager.get_match_history(
                player_id=player_id,
                limit=message.limit or 20,
            )
            
            # 转换为消息格式
            history_data = [
                self._convert_match_history_to_data(h) for h in history
            ]
            
            # 获取玩家统计
            stats = self.manager.get_player_stats(player_id)
            
            logger.debug(
                "获取对局历史",
                extra={
                    "player_id": player_id,
                    "history_count": len(history_data),
                }
            )
            
            return MatchHistoryMessage(
                matches=history_data,
                total_matches=stats.total_matches,
                win_rate=stats.win_rate,
                avg_rank=stats.avg_rank,
                seq=message.seq,
            )
        
        except Exception as e:
            logger.exception(
                "获取对局历史异常",
                extra={"player_id": player_id, "error": str(e)},
            )
            return ErrorMessage(
                code=7003,
                message="获取对局历史失败",
                details={"error": str(e)},
                seq=message.seq,
            )
    
    async def handle_get_equipment_advice(
        self,
        session: "Session",
        message: GetEquipmentAdviceMessage,
    ) -> Optional[BaseMessage]:
        """
        处理获取装备建议请求
        
        Args:
            session: WebSocket 会话
            message: 获取装备建议消息
            
        Returns:
            响应消息
        """
        player_id = session.player_id
        
        try:
            # 获取装备建议
            advice_list = self.manager.get_equipment_advice(
                player_id=player_id,
                equipment=message.equipment or [],
                heroes=message.heroes or [],
            )
            
            # 转换为消息格式
            advice_data = [
                EquipmentAdviceData(
                    equipment_id=a.equipment_id,
                    equipment_name=a.equipment_name,
                    target_hero_id=a.target_hero_id,
                    reason=a.reason,
                    recipe=a.recipe,
                    priority=a.priority.value,
                    expected_stat_boost=a.expected_stat_boost,
                )
                for a in advice_list
            ]
            
            logger.debug(
                "获取装备建议",
                extra={
                    "player_id": player_id,
                    "advice_count": len(advice_data),
                }
            )
            
            return EquipmentAdviceMessage(
                advice=advice_data,
                seq=message.seq,
            )
        
        except Exception as e:
            logger.exception(
                "获取装备建议异常",
                extra={"player_id": player_id, "error": str(e)},
            )
            return ErrorMessage(
                code=7004,
                message="获取装备建议失败",
                details={"error": str(e)},
                seq=message.seq,
            )
    
    async def handle_get_position_advice(
        self,
        session: "Session",
        message: GetPositionAdviceMessage,
    ) -> Optional[BaseMessage]:
        """
        处理获取站位建议请求
        
        Args:
            session: WebSocket 会话
            message: 获取站位建议消息
            
        Returns:
            响应消息
        """
        player_id = session.player_id
        
        try:
            # 获取站位建议
            advice_list = self.manager.get_position_advice(
                player_id=player_id,
                board=message.board or {},
                heroes=message.heroes or [],
            )
            
            # 转换为消息格式
            advice_data = [
                PositionAdviceData(
                    hero_id=a.hero_id,
                    hero_name=a.hero_name,
                    current_position=a.current_position,
                    recommended_position=a.recommended_position,
                    reason=a.reason,
                    priority=a.priority.value,
                    tactical_role=a.tactical_role,
                )
                for a in advice_list
            ]
            
            logger.debug(
                "获取站位建议",
                extra={
                    "player_id": player_id,
                    "advice_count": len(advice_data),
                }
            )
            
            return PositionAdviceMessage(
                advice=advice_data,
                seq=message.seq,
            )
        
        except Exception as e:
            logger.exception(
                "获取站位建议异常",
                extra={"player_id": player_id, "error": str(e)},
            )
            return ErrorMessage(
                code=7005,
                message="获取站位建议失败",
                details={"error": str(e)},
                seq=message.seq,
            )
    
    async def handle_get_round_strategy(
        self,
        session: "Session",
        message: GetRoundStrategyMessage,
    ) -> Optional[BaseMessage]:
        """
        处理获取回合策略请求
        
        Args:
            session: WebSocket 会话
            message: 获取回合策略消息
            
        Returns:
            响应消息
        """
        player_id = session.player_id
        
        try:
            # 获取回合策略
            strategy = self.manager.get_round_strategy(
                player_id=player_id,
                round_num=message.round_num,
                game_state=message.game_state or {},
            )
            
            # 转换为消息格式
            strategy_data = RoundStrategyData(
                round_num=strategy.round_num,
                phase=strategy.phase.value,
                strategy_type=strategy.strategy_type,
                description=strategy.description,
                key_actions=strategy.key_actions,
                focus_synergies=strategy.focus_synergies,
                economy_advice=strategy.economy_advice,
                risk_level=strategy.risk_level,
                win_condition=strategy.win_condition,
            )
            
            logger.debug(
                "获取回合策略",
                extra={
                    "player_id": player_id,
                    "round_num": message.round_num,
                    "strategy_type": strategy.strategy_type,
                }
            )
            
            return RoundStrategyMessage(
                strategy=strategy_data,
                seq=message.seq,
            )
        
        except Exception as e:
            logger.exception(
                "获取回合策略异常",
                extra={"player_id": player_id, "error": str(e)},
            )
            return ErrorMessage(
                code=7006,
                message="获取回合策略失败",
                details={"error": str(e)},
                seq=message.seq,
            )
    
    async def handle_get_win_rate_prediction(
        self,
        session: "Session",
        message: GetWinRatePredictionMessage,
    ) -> Optional[BaseMessage]:
        """
        处理获取胜率预测请求
        
        Args:
            session: WebSocket 会话
            message: 获取胜率预测消息
            
        Returns:
            响应消息
        """
        player_id = session.player_id
        
        try:
            # 获取胜率预测
            prediction = self.manager.predict_win_rate(
                player_id=player_id,
                game_state=message.game_state or {},
            )
            
            # 转换为消息格式
            prediction_data = WinRatePredictionData(
                predicted_win_rate=prediction.predicted_win_rate,
                confidence=prediction.confidence,
                factors=prediction.factors,
                comparison_rank=prediction.comparison_rank,
                key_advantages=prediction.key_advantages,
                key_weaknesses=prediction.key_weaknesses,
                improvement_suggestions=prediction.improvement_suggestions,
            )
            
            logger.debug(
                "获取胜率预测",
                extra={
                    "player_id": player_id,
                    "win_rate": prediction.predicted_win_rate,
                    "confidence": prediction.confidence,
                }
            )
            
            return WinRatePredictionMessage(
                prediction=prediction_data,
                seq=message.seq,
            )
        
        except Exception as e:
            logger.exception(
                "获取胜率预测异常",
                extra={"player_id": player_id, "error": str(e)},
            )
            return ErrorMessage(
                code=7007,
                message="获取胜率预测失败",
                details={"error": str(e)},
                seq=message.seq,
            )
    
    # ========================================================================
    # 辅助方法
    # ========================================================================
    
    def _convert_analysis_to_data(
        self, analysis: CoachAnalysis
    ) -> CoachAnalysisData:
        """将 CoachAnalysis 转换为 CoachAnalysisData"""
        suggestions = [
            AISuggestionData(
                suggestion_id=s.suggestion_id,
                suggestion_type=s.suggestion_type.value,
                priority=s.priority.value,
                title=s.title,
                description=s.description,
                reason=s.reason,
                action=s.action,
                expected_benefit=s.expected_benefit,
                confidence=s.confidence,
            )
            for s in analysis.suggestions
        ]
        
        win_rate_data = None
        if analysis.win_rate_prediction:
            win_rate_data = WinRatePredictionData(
                predicted_win_rate=analysis.win_rate_prediction.predicted_win_rate,
                confidence=analysis.win_rate_prediction.confidence,
                factors=analysis.win_rate_prediction.factors,
                comparison_rank=analysis.win_rate_prediction.comparison_rank,
                key_advantages=analysis.win_rate_prediction.key_advantages,
                key_weaknesses=analysis.win_rate_prediction.key_weaknesses,
                improvement_suggestions=analysis.win_rate_prediction.improvement_suggestions,
            )
        
        return CoachAnalysisData(
            analysis_id=analysis.analysis_id,
            player_id=analysis.player_id,
            game_id=analysis.game_id,
            analysis_type=analysis.analysis_type.value,
            round_num=analysis.round_num,
            lineup_score=analysis.lineup_score,
            economy_score=analysis.economy_score,
            synergy_score=analysis.synergy_score,
            position_score=analysis.position_score,
            overall_score=analysis.overall_score,
            strengths=analysis.strengths,
            weaknesses=analysis.weaknesses,
            suggestions=suggestions,
            win_rate_prediction=win_rate_data,
            created_at=analysis.created_at,
        )
    
    def _convert_lineup_to_data(
        self, lineup: LineupRecommendation
    ) -> LineupRecommendationData:
        """将 LineupRecommendation 转换为 LineupRecommendationData"""
        return LineupRecommendationData(
            lineup_id=lineup.lineup_id,
            name=lineup.name,
            description=lineup.description,
            difficulty=lineup.difficulty,
            core_heroes=lineup.core_heroes,
            optional_heroes=lineup.optional_heroes,
            synergies=lineup.synergies,
            play_style=lineup.play_style,
            early_game=lineup.early_game,
            mid_game=lineup.mid_game,
            late_game=lineup.late_game,
            key_items=lineup.key_items,
            tips=lineup.tips,
            win_rate=lineup.win_rate,
            popularity=lineup.popularity,
        )
    
    def _convert_match_history_to_data(
        self, item: MatchHistoryItem
    ) -> MatchHistoryItemData:
        """将 MatchHistoryItem 转换为 MatchHistoryItemData"""
        analysis_data = None
        if item.analysis:
            analysis_data = self._convert_analysis_to_data(item.analysis)
        
        return MatchHistoryItemData(
            match_id=item.match_id,
            game_id=item.game_id,
            final_rank=item.final_rank,
            total_rounds=item.total_rounds,
            duration_seconds=item.duration_seconds,
            final_lineup=item.final_lineup,
            final_synergies=item.final_synergies,
            damage_dealt=item.damage_dealt,
            damage_taken=item.damage_taken,
            gold_earned=item.gold_earned,
            key_decisions=item.key_decisions,
            analysis=analysis_data,
            played_at=item.played_at,
        )


# 全局处理器实例
ai_coach_ws_handler = AICoachWSHandler()
