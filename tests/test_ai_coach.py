"""
王者之奕 - AI教练系统测试

测试AI教练系统的核心功能：
- 阵容分析
- 阵容推荐
- 装备建议
- 站位优化
- 回合策略
- 胜率预测
- 对局历史
"""

import pytest
from unittest.mock import Mock, patch

from src.server.ai_coach import (
    AISuggestion,
    AICoachManager,
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
    get_ai_coach_manager,
    META_LINEUPS,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def ai_coach_manager():
    """创建AI教练管理器实例"""
    return AICoachManager()


@pytest.fixture
def sample_game_state():
    """示例游戏状态"""
    return {
        "game_id": "test_game_001",
        "round_num": 15,
        "heroes": [
            {"hero_id": "hero_1", "name": "战士A", "cost": 3, "stars": 2, "race": "人族", "profession": "战士"},
            {"hero_id": "hero_2", "name": "法师B", "cost": 4, "stars": 2, "race": "人族", "profession": "法师"},
            {"hero_id": "hero_3", "name": "坦克C", "cost": 2, "stars": 2, "race": "神族", "profession": "坦克"},
            {"hero_id": "hero_4", "name": "射手D", "cost": 3, "stars": 1, "race": "精灵", "profession": "射手"},
            {"hero_id": "hero_5", "name": "辅助E", "cost": 2, "stars": 2, "race": "人族", "profession": "辅助"},
        ],
        "synergies": {"人族": 3, "法师": 1, "战士": 1},
        "gold": 40,
        "level": 6,
        "hp": 75,
        "board": {
            "1_3": {"hero_id": "hero_1", "name": "战士A", "profession": "战士"},
            "2_4": {"hero_id": "hero_3", "name": "坦克C", "profession": "坦克"},
            "3_1": {"hero_id": "hero_2", "name": "法师B", "profession": "法师"},
            "3_2": {"hero_id": "hero_4", "name": "射手D", "profession": "射手"},
            "3_3": {"hero_id": "hero_5", "name": "辅助E", "profession": "辅助"},
        },
        "bench": [],
    }


@pytest.fixture
def sample_equipment():
    """示例装备列表"""
    return [
        {"equipment_id": "equip_1", "name": "攻击剑", "type": "sword", "tier": 1, "stats": {"attack": 15}},
        {"equipment_id": "equip_2", "name": "法杖", "type": "staff", "tier": 1, "stats": {"spell_power": 20}},
        {"equipment_id": "equip_3", "name": "锁子甲", "type": "armor", "tier": 1, "stats": {"armor": 20}},
    ]


@pytest.fixture
def sample_heroes():
    """示例英雄列表"""
    return [
        {"hero_id": "hero_1", "name": "战士A", "profession": "战士", "cost": 3, "stars": 2},
        {"hero_id": "hero_2", "name": "法师B", "profession": "法师", "cost": 4, "stars": 2},
        {"hero_id": "hero_3", "name": "坦克C", "profession": "坦克", "cost": 2, "stars": 2},
        {"hero_id": "hero_4", "name": "射手D", "profession": "射手", "cost": 3, "stars": 1},
    ]


# ============================================================================
# 测试数据模型
# ============================================================================


class TestAISuggestion:
    """测试AI建议模型"""
    
    def test_create_suggestion(self):
        """测试创建建议"""
        suggestion = AISuggestion(
            suggestion_id="test_suggest_1",
            suggestion_type=SuggestionType.LINEUP,
            priority=Priority.HIGH,
            title="测试建议",
            description="这是一个测试建议",
            reason="测试原因",
            action={"focus": "upgrade"},
            expected_benefit="提升战力",
        )
        
        assert suggestion.suggestion_id == "test_suggest_1"
        assert suggestion.suggestion_type == SuggestionType.LINEUP
        assert suggestion.priority == Priority.HIGH
        assert suggestion.confidence == 0.8
        
    def test_suggestion_to_dict(self):
        """测试建议转换为字典"""
        suggestion = AISuggestion(
            suggestion_id="test_suggest_1",
            suggestion_type=SuggestionType.EQUIPMENT,
            priority=Priority.MEDIUM,
            title="测试建议",
            description="描述",
            reason="原因",
            action={},
            expected_benefit="收益",
        )
        
        data = suggestion.to_dict()
        
        assert data["suggestion_id"] == "test_suggest_1"
        assert data["suggestion_type"] == "equipment"
        assert data["priority"] == "medium"
        
    def test_suggestion_from_dict(self):
        """测试从字典创建建议"""
        data = {
            "suggestion_id": "test_suggest_1",
            "suggestion_type": "synergy",
            "priority": "high",
            "title": "完善羁绊",
            "description": "添加更多同羁绊英雄",
            "reason": "羁绊不完整",
            "action": {"synergy": "法师"},
            "expected_benefit": "获得羁绊加成",
        }
        
        suggestion = AISuggestion.from_dict(data)
        
        assert suggestion.suggestion_type == SuggestionType.SYNERGY
        assert suggestion.priority == Priority.HIGH


class TestCoachAnalysis:
    """测试对局分析模型"""
    
    def test_create_analysis(self):
        """测试创建分析"""
        analysis = CoachAnalysis(
            analysis_id="analysis_1",
            player_id=123,
            game_id="game_1",
            analysis_type=AnalysisType.MID_GAME,
            round_num=15,
            lineup_score=65.0,
            economy_score=70.0,
            synergy_score=55.0,
            position_score=60.0,
            overall_score=62.5,
        )
        
        assert analysis.analysis_id == "analysis_1"
        assert analysis.overall_score == 62.5
        assert analysis.analysis_type == AnalysisType.MID_GAME
        
    def test_analysis_to_dict(self):
        """测试分析转换为字典"""
        analysis = CoachAnalysis(
            analysis_id="analysis_1",
            player_id=123,
            game_id="game_1",
            analysis_type=AnalysisType.EARLY_GAME,
            round_num=5,
            strengths=["经济好"],
            weaknesses=["阵容弱"],
        )
        
        data = analysis.to_dict()
        
        assert data["analysis_id"] == "analysis_1"
        assert data["strengths"] == ["经济好"]
        assert data["weaknesses"] == ["阵容弱"]


class TestWinRatePrediction:
    """测试胜率预测模型"""
    
    def test_create_prediction(self):
        """测试创建预测"""
        prediction = WinRatePrediction(
            predicted_win_rate=0.25,
            confidence=0.7,
            factors={"lineup": 0.6, "economy": 0.8},
            comparison_rank=3,
            key_advantages=["经济健康"],
            key_weaknesses=["阵容不完整"],
            improvement_suggestions=["完善羁绊"],
        )
        
        assert prediction.predicted_win_rate == 0.25
        assert prediction.confidence == 0.7
        assert "经济健康" in prediction.key_advantages


class TestLineupRecommendation:
    """测试阵容推荐模型"""
    
    def test_create_lineup(self):
        """测试创建阵容推荐"""
        lineup = LineupRecommendation(
            lineup_id="meta_wizard",
            name="法师流",
            description="高爆发法术阵容",
            core_heroes=["法师A", "法师B"],
            synergies={"法师": 6},
            win_rate=0.52,
        )
        
        assert lineup.lineup_id == "meta_wizard"
        assert "法师A" in lineup.core_heroes
        assert lineup.win_rate == 0.52


class TestMatchHistoryItem:
    """测试对局历史记录模型"""
    
    def test_create_match_history(self):
        """测试创建对局历史"""
        match = MatchHistoryItem(
            match_id="match_1",
            game_id="game_1",
            final_rank=2,
            total_rounds=30,
            duration_seconds=1200,
            final_lineup=["hero_1", "hero_2"],
            final_synergies={"人族": 4},
        )
        
        assert match.match_id == "match_1"
        assert match.final_rank == 2
        assert match.is_win is False
        assert match.duration_minutes == 20.0


class TestPlayerLearningStats:
    """测试玩家学习统计模型"""
    
    def test_create_stats(self):
        """测试创建统计"""
        stats = PlayerLearningStats(
            player_id=123,
            total_matches=50,
            wins=10,
            top4_count=25,
            avg_rank=3.5,
        )
        
        assert stats.player_id == 123
        assert stats.win_rate == 0.2
        assert stats.top4_rate == 0.5


# ============================================================================
# 测试AI教练管理器
# ============================================================================


class TestAICoachManager:
    """测试AI教练管理器"""
    
    def test_get_manager_singleton(self):
        """测试获取管理器单例"""
        manager1 = get_ai_coach_manager()
        manager2 = get_ai_coach_manager()
        
        assert manager1 is manager2
    
    def test_analyze_lineup_early_game(self, ai_coach_manager, sample_game_state):
        """测试前期阵容分析"""
        sample_game_state["round_num"] = 5
        
        analysis = ai_coach_manager.analyze_lineup(123, sample_game_state)
        
        assert analysis.player_id == 123
        assert analysis.analysis_type == AnalysisType.EARLY_GAME
        assert 0 <= analysis.overall_score <= 100
        assert isinstance(analysis.suggestions, list)
    
    def test_analyze_lineup_mid_game(self, ai_coach_manager, sample_game_state):
        """测试中期阵容分析"""
        sample_game_state["round_num"] = 15
        
        analysis = ai_coach_manager.analyze_lineup(123, sample_game_state)
        
        assert analysis.analysis_type == AnalysisType.MID_GAME
        assert analysis.lineup_score >= 0
        assert analysis.economy_score >= 0
        assert analysis.synergy_score >= 0
        assert analysis.position_score >= 0
    
    def test_analyze_lineup_late_game(self, ai_coach_manager, sample_game_state):
        """测试后期阵容分析"""
        sample_game_state["round_num"] = 25
        
        analysis = ai_coach_manager.analyze_lineup(123, sample_game_state)
        
        assert analysis.analysis_type == AnalysisType.LATE_GAME
    
    def test_analyze_lineup_low_hp_suggestions(self, ai_coach_manager, sample_game_state):
        """测试低血量时的建议"""
        sample_game_state["hp"] = 20
        
        analysis = ai_coach_manager.analyze_lineup(123, sample_game_state)
        
        # 低血量应该触发紧急建议
        critical_suggestions = [
            s for s in analysis.suggestions
            if s.priority == Priority.CRITICAL
        ]
        assert len(critical_suggestions) > 0 or any("血量" in w for w in analysis.weaknesses)
    
    def test_get_lineup_recommendations(self, ai_coach_manager, sample_heroes):
        """测试获取阵容推荐"""
        recommendations = ai_coach_manager.get_lineup_recommendations(
            player_id=123,
            current_heroes=sample_heroes,
            limit=5,
        )
        
        assert len(recommendations) <= 5
        assert all(isinstance(r, LineupRecommendation) for r in recommendations)
        assert all(r.lineup_id for r in recommendations)
    
    def test_get_lineup_recommendations_match_scoring(self, ai_coach_manager):
        """测试阵容推荐匹配度评分"""
        # 提供与法师流匹配的英雄
        current_heroes = [
            {"hero_id": "h1", "race": "人族", "profession": "法师"},
            {"hero_id": "h2", "race": "人族", "profession": "法师"},
        ]
        
        recommendations = ai_coach_manager.get_lineup_recommendations(
            player_id=123,
            current_heroes=current_heroes,
        )
        
        # 应该返回推荐
        assert len(recommendations) > 0
    
    def test_get_equipment_advice(self, ai_coach_manager, sample_equipment, sample_heroes):
        """测试获取装备建议"""
        advice = ai_coach_manager.get_equipment_advice(
            player_id=123,
            equipment=sample_equipment,
            heroes=sample_heroes,
        )
        
        assert isinstance(advice, list)
        assert all(isinstance(a, EquipmentAdvice) for a in advice)
    
    def test_get_position_advice(self, ai_coach_manager, sample_game_state):
        """测试获取站位建议"""
        advice = ai_coach_manager.get_position_advice(
            player_id=123,
            board=sample_game_state["board"],
            heroes=sample_game_state["heroes"],
        )
        
        assert isinstance(advice, list)
        assert all(isinstance(a, PositionAdvice) for a in advice)
    
    def test_get_round_strategy_early(self, ai_coach_manager, sample_game_state):
        """测试前期回合策略"""
        strategy = ai_coach_manager.get_round_strategy(
            player_id=123,
            round_num=5,
            game_state=sample_game_state,
        )
        
        assert strategy.round_num == 5
        assert strategy.phase == AnalysisType.EARLY_GAME
        assert strategy.strategy_type in ["aggressive", "defensive", "balanced", "economic"]
    
    def test_get_round_strategy_mid(self, ai_coach_manager, sample_game_state):
        """测试中期回合策略"""
        strategy = ai_coach_manager.get_round_strategy(
            player_id=123,
            round_num=15,
            game_state=sample_game_state,
        )
        
        assert strategy.phase == AnalysisType.MID_GAME
    
    def test_get_round_strategy_late(self, ai_coach_manager, sample_game_state):
        """测试后期回合策略"""
        strategy = ai_coach_manager.get_round_strategy(
            player_id=123,
            round_num=25,
            game_state=sample_game_state,
        )
        
        assert strategy.phase == AnalysisType.LATE_GAME
    
    def test_predict_win_rate(self, ai_coach_manager, sample_game_state):
        """测试胜率预测"""
        prediction = ai_coach_manager.predict_win_rate(
            player_id=123,
            game_state=sample_game_state,
        )
        
        assert 0 <= prediction.predicted_win_rate <= 1
        assert 0 <= prediction.confidence <= 1
        assert 1 <= prediction.comparison_rank <= 8
        assert isinstance(prediction.factors, dict)
    
    def test_predict_win_rate_high_hp(self, ai_coach_manager, sample_game_state):
        """测试高血量时的胜率预测"""
        sample_game_state["hp"] = 100
        
        prediction = ai_coach_manager.predict_win_rate(123, sample_game_state)
        
        # 高血量应该有更高的胜率
        assert "血量健康" in prediction.key_advantages or prediction.factors.get("hp", 0) > 0.5
    
    def test_record_and_get_match_history(self, ai_coach_manager):
        """测试记录和获取对局历史"""
        match_data = {
            "match_id": "match_1",
            "game_id": "game_1",
            "final_rank": 2,
            "total_rounds": 30,
            "duration_seconds": 1200,
            "final_lineup": ["hero_1", "hero_2"],
            "final_synergies": {"人族": 4},
        }
        
        # 记录对局
        match = ai_coach_manager.record_match(123, match_data)
        
        assert match.match_id == "match_1"
        assert match.is_win is False
        
        # 获取历史
        history = ai_coach_manager.get_match_history(123, limit=10)
        
        assert len(history) > 0
        assert history[0].match_id == "match_1"
    
    def test_get_player_stats(self, ai_coach_manager):
        """测试获取玩家统计"""
        # 记录几局对局
        for rank in [1, 2, 3, 4]:
            ai_coach_manager.record_match(123, {
                "match_id": f"match_{rank}",
                "game_id": f"game_{rank}",
                "final_rank": rank,
                "total_rounds": 25,
                "duration_seconds": 1000,
            })
        
        stats = ai_coach_manager.get_player_stats(123)
        
        assert stats.total_matches == 4
        assert stats.wins == 1
        assert stats.top4_count == 4
        assert stats.win_rate == 0.25
    
    def test_get_stats(self, ai_coach_manager):
        """测试获取管理器统计"""
        stats = ai_coach_manager.get_stats()
        
        assert "total_players_tracked" in stats
        assert "total_matches_recorded" in stats
        assert "total_analyses" in stats


# ============================================================================
# 测试评分逻辑
# ============================================================================


class TestScoringLogic:
    """测试评分逻辑"""
    
    def test_lineup_score_empty(self, ai_coach_manager):
        """测试空阵容评分"""
        game_state = {
            "heroes": [],
            "level": 1,
            "round_num": 1,
            "synergies": {},
        }
        
        score = ai_coach_manager._calculate_lineup_score(game_state)
        
        # 空阵容应该有较低分数
        assert score < 50
    
    def test_lineup_score_with_heroes(self, ai_coach_manager, sample_game_state):
        """测试有英雄的阵容评分"""
        score = ai_coach_manager._calculate_lineup_score(sample_game_state)
        
        assert 0 <= score <= 100
    
    def test_economy_score_low_gold(self, ai_coach_manager):
        """测试低金币经济评分"""
        game_state = {
            "gold": 5,
            "round_num": 15,
            "hp": 80,
        }
        
        score = ai_coach_manager._calculate_economy_score(game_state)
        
        # 低金币应该有较低分数
        assert score < 60
    
    def test_economy_score_high_gold(self, ai_coach_manager):
        """测试高金币经济评分"""
        game_state = {
            "gold": 60,
            "round_num": 15,
            "hp": 80,
        }
        
        score = ai_coach_manager._calculate_economy_score(game_state)
        
        # 高金币应该有较高分数
        assert score > 60
    
    def test_synergy_score_no_synergies(self, ai_coach_manager):
        """测试无羁绊评分"""
        game_state = {
            "synergies": {},
            "heroes": [{"hero_id": "h1"}],
        }
        
        score = ai_coach_manager._calculate_synergy_score(game_state)
        
        # 无羁绊应该有较低分数
        assert score < 50
    
    def test_synergy_score_with_synergies(self, ai_coach_manager, sample_game_state):
        """测试有羁绊的评分"""
        score = ai_coach_manager._calculate_synergy_score(sample_game_state)
        
        assert 0 <= score <= 100


# ============================================================================
# 测试建议生成
# ============================================================================


class TestSuggestionGeneration:
    """测试建议生成"""
    
    def test_weakness_based_suggestions(self, ai_coach_manager, sample_game_state):
        """测试基于劣势的建议生成"""
        # 设置为低血量
        sample_game_state["hp"] = 25
        
        analysis = ai_coach_manager.analyze_lineup(123, sample_game_state)
        
        # 应该有与血量相关的建议或劣势
        has_hp_related = any(
            "血量" in w or "血量" in s.reason
            for w in analysis.weaknesses
            for s in analysis.suggestions
        ) or any("血量" in w for w in analysis.weaknesses)
        
        assert has_hp_related or len(analysis.weaknesses) > 0
    
    def test_phase_based_suggestions(self, ai_coach_manager, sample_game_state):
        """测试基于阶段的建议生成"""
        # 前期
        sample_game_state["round_num"] = 5
        early_analysis = ai_coach_manager.analyze_lineup(123, sample_game_state)
        
        # 后期
        sample_game_state["round_num"] = 25
        late_analysis = ai_coach_manager.analyze_lineup(123, sample_game_state)
        
        # 两个阶段的建议可能不同
        assert isinstance(early_analysis.suggestions, list)
        assert isinstance(late_analysis.suggestions, list)


# ============================================================================
# 测试预定义阵容
# ============================================================================


class TestMetaLineups:
    """测试预定义阵容"""
    
    def test_meta_lineups_exist(self):
        """测试预定义阵容存在"""
        assert len(META_LINEUPS) > 0
    
    def test_meta_lineups_structure(self):
        """测试预定义阵容结构"""
        for lineup in META_LINEUPS:
            assert "lineup_id" in lineup
            assert "name" in lineup
            assert "description" in lineup
            assert "core_heroes" in lineup
            assert "synergies" in lineup
            assert "win_rate" in lineup


# ============================================================================
# 集成测试
# ============================================================================


class TestIntegration:
    """集成测试"""
    
    def test_full_analysis_workflow(self, ai_coach_manager, sample_game_state):
        """测试完整分析流程"""
        # 1. 分析阵容
        analysis = ai_coach_manager.analyze_lineup(123, sample_game_state)
        
        # 2. 获取阵容推荐
        recommendations = ai_coach_manager.get_lineup_recommendations(
            123, sample_game_state["heroes"]
        )
        
        # 3. 预测胜率
        prediction = ai_coach_manager.predict_win_rate(123, sample_game_state)
        
        # 4. 获取回合策略
        strategy = ai_coach_manager.get_round_strategy(
            123, sample_game_state["round_num"], sample_game_state
        )
        
        # 验证所有结果都合理
        assert analysis.overall_score >= 0
        assert len(recommendations) > 0
        assert prediction.predicted_win_rate >= 0
        assert strategy.round_num == sample_game_state["round_num"]
    
    def test_match_history_tracking(self, ai_coach_manager):
        """测试对局历史追踪"""
        player_id = 999
        
        # 记录多局对局
        for i in range(5):
            ai_coach_manager.record_match(player_id, {
                "match_id": f"match_{i}",
                "game_id": f"game_{i}",
                "final_rank": i + 1,
                "total_rounds": 20 + i * 5,
                "duration_seconds": 1000 + i * 100,
            })
        
        # 获取统计
        stats = ai_coach_manager.get_player_stats(player_id)
        
        assert stats.total_matches == 5
        assert stats.wins == 1  # 第一名只有一次
        assert stats.top4_count == 4  # 前4名有4次


# ============================================================================
# 运行测试
# ============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
