"""
王者之奕 - AI教练系统管理器

本模块提供AI教练系统的核心管理功能：
- AICoachManager: AI教练管理器类
- 分析当前阵容
- 推荐阵容
- 装备建议
- 站位优化
- 回合策略
- 预测胜率
- 对局历史分析

使用内存存储实现高性能，结合数据分析和规则引擎提供建议。
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import TYPE_CHECKING, Any

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

if TYPE_CHECKING:
    from ..db.database import Database

logger = logging.getLogger(__name__)


# ============================================================================
# 预定义阵容推荐
# ============================================================================

# 强势阵容数据（基于游戏平衡性设计）
META_LINEUPS: list[dict[str, Any]] = [
    {
        "lineup_id": "meta_wizard",
        "name": "法师流",
        "description": "以高爆发法术伤害为核心的阵容，适合中期发力",
        "difficulty": 3,
        "core_heroes": ["法师A", "法师B", "法师C"],
        "optional_heroes": ["辅助A", "坦克A"],
        "synergies": {"法师": 6, "人族": 4},
        "play_style": "aggressive",
        "early_game": ["低费法师", "低费人族"],
        "mid_game": ["3星法师核心", "2星人族前排"],
        "late_game": ["5费法师", "完整6法师羁绊"],
        "key_items": ["法杖", "蓝buff"],
        "tips": ["前期保血优先", "7级开始D牌", "注意站位防刺客"],
        "win_rate": 0.52,
        "popularity": 0.75,
    },
    {
        "lineup_id": "meta_tank",
        "name": "重装坦克流",
        "description": "高护甲高血量的肉盾阵容，后期转型灵活",
        "difficulty": 2,
        "core_heroes": ["坦克A", "坦克B", "坦克C"],
        "optional_heroes": ["辅助A", "射手A"],
        "synergies": {"坦克": 6, "战士": 4},
        "play_style": "defensive",
        "early_game": ["低费坦克", "低费战士"],
        "mid_game": ["3星坦克前排", "2星输出"],
        "late_game": ["5费大肉", "完整6坦克羁绊"],
        "key_items": ["锁子甲", "负极斗篷"],
        "tips": ["前期连胜经济", "中期稳血", "后期找C位"],
        "win_rate": 0.50,
        "popularity": 0.60,
    },
    {
        "lineup_id": "meta_assassin",
        "name": "刺客流",
        "description": "高爆发切后排阵容，需要精准的站位和时机",
        "difficulty": 4,
        "core_heroes": ["刺客A", "刺客B", "刺客C"],
        "optional_heroes": ["辅助A", "战士A"],
        "synergies": {"刺客": 6, "精灵": 4},
        "play_style": "aggressive",
        "early_game": ["低费刺客", "低费精灵"],
        "mid_game": ["3星刺客核心", "前排坦克"],
        "late_game": ["5费刺客", "完整6刺客羁绊"],
        "key_items": ["攻击剑", "无尽"],
        "tips": ["注意对手站位", "8级成型", "经济管理很重要"],
        "win_rate": 0.48,
        "popularity": 0.55,
    },
    {
        "lineup_id": "meta_ranger",
        "name": "射手流",
        "description": "远程物理输出阵容，需要良好的前排保护",
        "difficulty": 3,
        "core_heroes": ["射手A", "射手B", "辅助A"],
        "optional_heroes": ["坦克A", "坦克B"],
        "synergies": {"射手": 4, "辅助": 4, "人族": 4},
        "play_style": "balanced",
        "early_game": ["低费射手", "低费坦克"],
        "mid_game": ["3星射手核心", "2星坦克"],
        "late_game": ["5费射手", "完整羁绊"],
        "key_items": ["攻击剑", "暴击剑"],
        "tips": ["保护C位站位", "注意刺客", "中期锁血"],
        "win_rate": 0.51,
        "popularity": 0.65,
    },
    {
        "lineup_id": "meta_summoner",
        "name": "召唤流",
        "description": "通过召唤物压场的特殊阵容，需要特定英雄",
        "difficulty": 5,
        "core_heroes": ["召唤师A", "召唤师B", "辅助A"],
        "optional_heroes": ["坦克A", "法师A"],
        "synergies": {"召唤": 4, "法师": 4, "亡灵": 2},
        "play_style": "balanced",
        "early_game": ["低费召唤", "低费坦克"],
        "mid_game": ["3星召唤核心", "前排成型"],
        "late_game": ["5费召唤", "完整羁绊"],
        "key_items": ["法杖", "蓝buff"],
        "tips": ["特定英雄很重要", "经济要求高", "后期发力"],
        "win_rate": 0.53,
        "popularity": 0.40,
    },
]


class AICoachManager:
    """
    AI教练管理器

    提供AI教练的核心功能：
    - 阵容分析与建议
    - 装备合成建议
    - 站位优化
    - 回合策略
    - 胜率预测
    - 历史对局分析

    使用方式:
        manager = AICoachManager()

        # 分析当前阵容
        analysis = manager.analyze_lineup(player_id, game_state)

        # 获取推荐阵容
        recommendations = manager.get_lineup_recommendations(player_id, current_heroes)

        # 获取装备建议
        equipment_advice = manager.get_equipment_advice(player_id, equipment, heroes)

        # 预测胜率
        win_rate = manager.predict_win_rate(player_id, game_state)
    """

    # 评分权重
    SCORE_WEIGHTS = {
        "lineup": 0.30,
        "economy": 0.25,
        "synergy": 0.25,
        "position": 0.20,
    }

    # 阵容评分阈值
    LINEUP_QUALITY_THRESHOLDS = {
        "excellent": 85,
        "good": 70,
        "average": 55,
        "poor": 40,
    }

    def __init__(self, database: Database | None = None) -> None:
        """
        初始化AI教练管理器

        Args:
            database: 数据库实例
        """
        self._database = database
        # 玩家学习统计缓存
        self._player_stats: dict[int, PlayerLearningStats] = {}
        # 对局历史缓存（最近100局）
        self._match_history: dict[int, list[MatchHistoryItem]] = {}
        # 分析结果缓存
        self._analysis_cache: dict[str, CoachAnalysis] = {}
        # 计数器
        self._suggestion_counter = 0
        self._analysis_counter = 0

        logger.info("AICoachManager initialized")

    @property
    def database(self) -> Database:
        """获取数据库实例"""
        if self._database is None:
            from ..db.database import get_database

            self._database = get_database()
        return self._database

    # ========================================================================
    # ID生成
    # ========================================================================

    def _generate_suggestion_id(self) -> str:
        """生成建议ID"""
        self._suggestion_counter += 1
        return f"suggest_{int(time.time() * 1000)}_{self._suggestion_counter}"

    def _generate_analysis_id(self) -> str:
        """生成分析ID"""
        self._analysis_counter += 1
        return f"analysis_{int(time.time() * 1000)}_{self._analysis_counter}"

    # ========================================================================
    # 阵容分析
    # ========================================================================

    def analyze_lineup(
        self,
        player_id: int,
        game_state: dict[str, Any],
    ) -> CoachAnalysis:
        """
        分析当前阵容

        Args:
            player_id: 玩家ID
            game_state: 游戏状态数据，包含：
                - game_id: 对局ID
                - round_num: 当前回合
                - heroes: 英雄列表
                - synergies: 激活的羁绊
                - gold: 当前金币
                - level: 当前等级
                - hp: 当前血量
                - board: 棋盘状态
                - bench: 备战席

        Returns:
            阵容分析结果
        """
        game_id = game_state.get("game_id", str(uuid.uuid4()))
        round_num = game_state.get("round_num", 1)

        # 确定分析类型
        if round_num <= 10:
            analysis_type = AnalysisType.EARLY_GAME
        elif round_num <= 20:
            analysis_type = AnalysisType.MID_GAME
        else:
            analysis_type = AnalysisType.LATE_GAME

        # 计算各项评分
        lineup_score = self._calculate_lineup_score(game_state)
        economy_score = self._calculate_economy_score(game_state)
        synergy_score = self._calculate_synergy_score(game_state)
        position_score = self._calculate_position_score(game_state)

        # 计算综合评分
        overall_score = (
            lineup_score * self.SCORE_WEIGHTS["lineup"]
            + economy_score * self.SCORE_WEIGHTS["economy"]
            + synergy_score * self.SCORE_WEIGHTS["synergy"]
            + position_score * self.SCORE_WEIGHTS["position"]
        )

        # 识别优势和劣势
        strengths = self._identify_strengths(
            lineup_score, economy_score, synergy_score, position_score, game_state
        )
        weaknesses = self._identify_weaknesses(
            lineup_score, economy_score, synergy_score, position_score, game_state
        )

        # 生成建议
        suggestions = self._generate_suggestions(player_id, game_state, strengths, weaknesses)

        # 预测胜率
        win_rate_prediction = self.predict_win_rate(player_id, game_state)

        # 创建分析结果
        analysis = CoachAnalysis(
            analysis_id=self._generate_analysis_id(),
            player_id=player_id,
            game_id=game_id,
            analysis_type=analysis_type,
            round_num=round_num,
            lineup_score=lineup_score,
            economy_score=economy_score,
            synergy_score=synergy_score,
            position_score=position_score,
            overall_score=overall_score,
            strengths=strengths,
            weaknesses=weaknesses,
            suggestions=suggestions,
            win_rate_prediction=win_rate_prediction,
        )

        # 缓存分析结果
        self._analysis_cache[analysis.analysis_id] = analysis

        logger.debug(
            f"Analyzed lineup for player {player_id}",
            extra={
                "player_id": player_id,
                "overall_score": overall_score,
                "round_num": round_num,
            },
        )

        return analysis

    def _calculate_lineup_score(self, game_state: dict[str, Any]) -> float:
        """计算阵容评分"""
        heroes = game_state.get("heroes", [])
        level = game_state.get("level", 1)
        game_state.get("round_num", 1)

        if not heroes:
            return 30.0

        # 基础分：根据英雄数量与等级的比例
        hero_count = len(heroes)
        level_ratio = hero_count / max(level, 1)
        base_score = min(50, level_ratio * 25)  # 最多50分

        # 英雄质量分：星级和费用
        quality_score = 0.0
        for hero in heroes:
            stars = hero.get("stars", 1)
            cost = hero.get("cost", 1)
            quality_score += stars * cost * 2
        quality_score = min(30, quality_score)  # 最多30分

        # 羁绊完整性加成
        synergies = game_state.get("synergies", {})
        synergy_score = 0.0
        for _synergy_name, count in synergies.items():
            if count >= 4:
                synergy_score += 10
            elif count >= 2:
                synergy_score += 5
        synergy_score = min(20, synergy_score)  # 最多20分

        total_score = base_score + quality_score + synergy_score
        return round(min(100, total_score), 1)

    def _calculate_economy_score(self, game_state: dict[str, Any]) -> float:
        """计算经济评分"""
        gold = game_state.get("gold", 0)
        round_num = game_state.get("round_num", 1)
        hp = game_state.get("hp", 100)

        # 理想金币：根据回合数计算
        # 前期（1-10）：10-30金
        # 中期（11-20）：30-60金
        # 后期（21+）：50-80金
        if round_num <= 10:
            ideal_gold = 10 + round_num * 2
        elif round_num <= 20:
            ideal_gold = 30 + (round_num - 10) * 3
        else:
            ideal_gold = 60 + (round_num - 20) * 2

        ideal_gold = min(80, ideal_gold)

        # 计算经济分
        if gold >= ideal_gold:
            gold_score = 70 + min(30, (gold - ideal_gold))
        else:
            gold_score = max(30, 70 - (ideal_gold - gold) * 2)

        # 血量惩罚：血量过低需要更快花钱
        if hp < 30:
            gold_score -= 15
        elif hp < 50:
            gold_score -= 5

        return round(max(0, min(100, gold_score)), 1)

    def _calculate_synergy_score(self, game_state: dict[str, Any]) -> float:
        """计算羁绊评分"""
        synergies = game_state.get("synergies", {})
        heroes = game_state.get("heroes", [])

        if not synergies:
            return 30.0

        # 计算激活的羁绊数量和质量
        active_count = 0
        strong_count = 0
        total_count = sum(synergies.values())

        for _synergy_name, count in synergies.items():
            if count >= 2:
                active_count += 1
            if count >= 4:
                strong_count += 1

        # 羁绊多样性（2-4个最佳）
        diversity_score = 0
        if 2 <= active_count <= 4:
            diversity_score = 30
        elif active_count == 1 or active_count == 5:
            diversity_score = 20
        else:
            diversity_score = 10

        # 羁绊强度
        strength_score = min(40, strong_count * 15 + active_count * 5)

        # 羁绊利用效率
        efficiency = 0
        if heroes:
            hero_count = len(heroes)
            efficiency = min(30, (total_count / hero_count) * 15)

        total_score = diversity_score + strength_score + efficiency
        return round(min(100, total_score), 1)

    def _calculate_position_score(self, game_state: dict[str, Any]) -> float:
        """计算站位评分"""
        board = game_state.get("board", {})
        heroes = game_state.get("heroes", [])

        if not heroes or not board:
            return 50.0

        # 简化的站位评分逻辑
        score = 50.0

        # 检查前排和后排分布
        front_row_count = 0
        back_row_count = 0

        for pos_str, hero in board.items():
            if isinstance(pos_str, str):
                # 假设位置格式为 "row_col"
                parts = pos_str.split("_")
                if len(parts) == 2:
                    row = int(parts[0])
                    if row <= 2:  # 前排
                        front_row_count += 1
                    else:  # 后排
                        back_row_count += 1

        total_placed = front_row_count + back_row_count
        if total_placed > 0:
            # 理想比例：前排30-50%，后排50-70%
            front_ratio = front_row_count / total_placed
            if 0.3 <= front_ratio <= 0.5:
                score += 20
            elif 0.2 <= front_ratio <= 0.6:
                score += 10
            else:
                score -= 10

        # 检查核心英雄保护
        # 简化处理：假设费用高的英雄是核心
        core_heroes = [h for h in heroes if h.get("cost", 1) >= 4]
        protected_count = 0
        for hero in core_heroes:
            hero_id = hero.get("hero_id")
            for pos_str, board_hero in board.items():
                if isinstance(board_hero, dict) and board_hero.get("hero_id") == hero_id:
                    parts = pos_str.split("_")
                    if len(parts) == 2 and int(parts[0]) > 2:  # 在后排
                        protected_count += 1
                    break

        if core_heroes:
            protection_ratio = protected_count / len(core_heroes)
            score += protection_ratio * 20

        return round(max(0, min(100, score)), 1)

    def _identify_strengths(
        self,
        lineup_score: float,
        economy_score: float,
        synergy_score: float,
        position_score: float,
        game_state: dict[str, Any],
    ) -> list[str]:
        """识别优势"""
        strengths = []

        if lineup_score >= 70:
            strengths.append("阵容质量高，核心英雄星级充足")
        if economy_score >= 70:
            strengths.append("经济健康，有充足的运营空间")
        if synergy_score >= 70:
            strengths.append("羁绊完整，阵容协同效应强")
        if position_score >= 70:
            strengths.append("站位合理，核心输出得到保护")

        synergies = game_state.get("synergies", {})
        for syn_name, count in synergies.items():
            if count >= 6:
                strengths.append(f"{syn_name}羁绊满层，效果显著")
            elif count >= 4:
                strengths.append(f"{syn_name}羁绊成型，中期强势")

        hp = game_state.get("hp", 100)
        if hp >= 80:
            strengths.append("血量健康，容错率高")

        return strengths[:5]  # 最多返回5个

    def _identify_weaknesses(
        self,
        lineup_score: float,
        economy_score: float,
        synergy_score: float,
        position_score: float,
        game_state: dict[str, Any],
    ) -> list[str]:
        """识别劣势"""
        weaknesses = []

        if lineup_score < 50:
            weaknesses.append("阵容质量不足，需要提升英雄星级")
        if economy_score < 50:
            weaknesses.append("经济压力较大，需要调整运营策略")
        if synergy_score < 50:
            weaknesses.append("羁绊不完整，阵容缺乏协同")
        if position_score < 50:
            weaknesses.append("站位存在问题，核心英雄容易受到威胁")

        synergies = game_state.get("synergies", {})
        if not synergies or all(count < 2 for count in synergies.values()):
            weaknesses.append("没有激活任何有效羁绊")

        hp = game_state.get("hp", 100)
        if hp < 30:
            weaknesses.append("血量危急，需要立即提升战力")
        elif hp < 50:
            weaknesses.append("血量偏低，需要注意保血")

        level = game_state.get("level", 1)
        round_num = game_state.get("round_num", 1)
        expected_level = min(8, 2 + round_num // 3)
        if level < expected_level - 1:
            weaknesses.append("等级落后，可能影响高费英雄获取")

        return weaknesses[:5]  # 最多返回5个

    def _generate_suggestions(
        self,
        player_id: int,
        game_state: dict[str, Any],
        strengths: list[str],
        weaknesses: list[str],
    ) -> list[AISuggestion]:
        """生成建议"""
        suggestions = []

        # 基于劣势生成针对性建议
        for weakness in weaknesses:
            suggestion = self._create_suggestion_for_weakness(player_id, game_state, weakness)
            if suggestion:
                suggestions.append(suggestion)

        # 基于游戏阶段添加通用建议
        round_num = game_state.get("round_num", 1)
        if round_num <= 10:
            suggestions.extend(self._get_early_game_suggestions(game_state))
        elif round_num <= 20:
            suggestions.extend(self._get_mid_game_suggestions(game_state))
        else:
            suggestions.extend(self._get_late_game_suggestions(game_state))

        # 按优先级排序
        priority_order = {
            Priority.CRITICAL: 0,
            Priority.HIGH: 1,
            Priority.MEDIUM: 2,
            Priority.LOW: 3,
        }
        suggestions.sort(key=lambda s: priority_order.get(s.priority, 2))

        return suggestions[:10]  # 最多返回10个建议

    def _create_suggestion_for_weakness(
        self,
        player_id: int,
        game_state: dict[str, Any],
        weakness: str,
    ) -> AISuggestion | None:
        """为特定劣势创建建议"""
        suggestion_type = SuggestionType.LINEUP
        priority = Priority.MEDIUM
        title = ""
        description = ""
        reason = weakness
        action = {}
        expected_benefit = ""

        if "阵容质量不足" in weakness:
            suggestion_type = SuggestionType.HERO_BUY
            priority = Priority.HIGH
            title = "提升英雄星级"
            description = "建议优先升级核心英雄到2星或3星"
            action = {"focus": "upgrade_core_heroes"}
            expected_benefit = "显著提升阵容战斗力"

        elif "经济压力" in weakness:
            suggestion_type = SuggestionType.ECONOMY
            priority = Priority.HIGH
            title = "调整经济运营"
            description = "建议控制花费，优先积累金币利息"
            action = {"focus": "save_gold", "target_gold": 50}
            expected_benefit = "获得更多金币利息，后期有更多经济优势"

        elif "羁绊不完整" in weakness or "没有激活" in weakness:
            suggestion_type = SuggestionType.SYNERGY
            priority = Priority.HIGH
            title = "完善羁绊组合"
            description = "建议购买特定英雄激活羁绊效果"
            action = {"focus": "complete_synergies"}
            expected_benefit = "激活羁绊效果，获得属性加成"

        elif "站位存在" in weakness:
            suggestion_type = SuggestionType.POSITION
            priority = Priority.MEDIUM
            title = "优化站位布局"
            description = "建议调整英雄站位，保护核心输出"
            action = {"focus": "optimize_position"}
            expected_benefit = "核心英雄存活更久，输出更高"

        elif "血量危急" in weakness:
            suggestion_type = SuggestionType.LINEUP
            priority = Priority.CRITICAL
            title = "紧急提升战力"
            description = "血量危急，建议立即升级英雄或购买关键装备"
            action = {"focus": "emergency_power"}
            expected_benefit = "避免被淘汰，保住排名"

        elif "血量偏低" in weakness:
            suggestion_type = SuggestionType.LINEUP
            priority = Priority.HIGH
            title = "注意保血"
            description = "建议在保持经济的同时适度提升战力"
            action = {"focus": "balance_power"}
            expected_benefit = "稳定血量，避免后期压力"

        elif "等级落后" in weakness:
            suggestion_type = SuggestionType.LEVEL_UP
            priority = Priority.HIGH
            title = "提升玩家等级"
            description = "建议购买经验提升等级，增加上场英雄数量"
            action = {"focus": "buy_exp"}
            expected_benefit = "可以上场更多英雄，激活更多羁绊"

        else:
            return None

        return AISuggestion(
            suggestion_id=self._generate_suggestion_id(),
            suggestion_type=suggestion_type,
            priority=priority,
            title=title,
            description=description,
            reason=reason,
            action=action,
            expected_benefit=expected_benefit,
        )

    def _get_early_game_suggestions(self, game_state: dict[str, Any]) -> list[AISuggestion]:
        """获取前期建议"""
        suggestions = []
        gold = game_state.get("gold", 0)
        level = game_state.get("level", 1)

        # 前期经济建议
        if gold < 20:
            suggestions.append(
                AISuggestion(
                    suggestion_id=self._generate_suggestion_id(),
                    suggestion_type=SuggestionType.ECONOMY,
                    priority=Priority.MEDIUM,
                    title="积累经济基础",
                    description="前期优先保经济，为中期做准备",
                    reason="前期经济基础决定后期上限",
                    action={"save_gold": True},
                    expected_benefit="获得利息收入，中期更强",
                )
            )

        # 等级建议
        if level < 4:
            suggestions.append(
                AISuggestion(
                    suggestion_id=self._generate_suggestion_id(),
                    suggestion_type=SuggestionType.LEVEL_UP,
                    priority=Priority.LOW,
                    title="适度升级",
                    description="前期适度升级到4级，增加上场英雄",
                    reason="4级可以多上一个英雄，有助于保持连胜或连败",
                    action={"target_level": 4},
                    expected_benefit="阵容更完整，战力提升",
                )
            )

        return suggestions

    def _get_mid_game_suggestions(self, game_state: dict[str, Any]) -> list[AISuggestion]:
        """获取中期建议"""
        suggestions = []
        gold = game_state.get("gold", 0)
        level = game_state.get("level", 1)
        hp = game_state.get("hp", 100)

        # 中期关键等级
        if level < 6:
            suggestions.append(
                AISuggestion(
                    suggestion_id=self._generate_suggestion_id(),
                    suggestion_type=SuggestionType.LEVEL_UP,
                    priority=Priority.HIGH,
                    title="提升到6级",
                    description="中期6级是关键节点，应该尽快到达",
                    reason="6级可以开始D牌找3星核心",
                    action={"target_level": 6},
                    expected_benefit="阵容成型更快，战力稳定提升",
                )
            )

        # 血量与经济平衡
        if hp < 50 and gold > 30:
            suggestions.append(
                AISuggestion(
                    suggestion_id=self._generate_suggestion_id(),
                    suggestion_type=SuggestionType.ECONOMY,
                    priority=Priority.HIGH,
                    title="血量偏低，适度花钱",
                    description="血量不足时应该花钱提升战力保血",
                    reason="保血比存钱更重要",
                    action={"spend_gold": gold * 0.5},
                    expected_benefit="稳定血量，保证后期运营空间",
                )
            )

        return suggestions

    def _get_late_game_suggestions(self, game_state: dict[str, Any]) -> list[AISuggestion]:
        """获取后期建议"""
        suggestions = []
        gold = game_state.get("gold", 0)
        level = game_state.get("level", 1)

        # 后期关键等级
        if level < 8:
            suggestions.append(
                AISuggestion(
                    suggestion_id=self._generate_suggestion_id(),
                    suggestion_type=SuggestionType.LEVEL_UP,
                    priority=Priority.HIGH,
                    title="冲击8级",
                    description="后期8级是标准配置，可以获得5费英雄",
                    reason="8级有更高概率获得5费核心英雄",
                    action={"target_level": 8},
                    expected_benefit="阵容上限提升，可以找到最终核心",
                )
            )

        # 后期全力提升
        if gold > 50:
            suggestions.append(
                AISuggestion(
                    suggestion_id=self._generate_suggestion_id(),
                    suggestion_type=SuggestionType.LINEUP,
                    priority=Priority.HIGH,
                    title="全力提升阵容",
                    description="后期应该花钱提升阵容质量",
                    reason="后期每一回合都很关键",
                    action={"spend_all": True},
                    expected_benefit="阵容质量最大化，提高吃鸡概率",
                )
            )

        return suggestions

    # ========================================================================
    # 阵容推荐
    # ========================================================================

    def get_lineup_recommendations(
        self,
        player_id: int,
        current_heroes: list[dict[str, Any]],
        limit: int = 5,
    ) -> list[LineupRecommendation]:
        """
        获取阵容推荐

        Args:
            player_id: 玩家ID
            current_heroes: 当前拥有的英雄
            limit: 返回数量限制

        Returns:
            推荐阵容列表
        """
        recommendations = []

        # 提取当前英雄的羁绊信息
        current_synergies: dict[str, int] = {}
        current_hero_ids = set()
        for hero in current_heroes:
            hero_id = hero.get("hero_id", "")
            current_hero_ids.add(hero_id)
            race = hero.get("race", "")
            profession = hero.get("profession", "")
            if race:
                current_synergies[race] = current_synergies.get(race, 0) + 1
            if profession:
                current_synergies[profession] = current_synergies.get(profession, 0) + 1

        # 计算每个阵容的匹配度
        lineup_scores = []
        for lineup_data in META_LINEUPS:
            score = self._calculate_lineup_match_score(
                lineup_data, current_hero_ids, current_synergies
            )
            lineup_scores.append((score, lineup_data))

        # 按匹配度排序
        lineup_scores.sort(key=lambda x: x[0], reverse=True)

        # 创建推荐对象
        for score, lineup_data in lineup_scores[:limit]:
            lineup = LineupRecommendation(
                lineup_id=lineup_data["lineup_id"],
                name=lineup_data["name"],
                description=lineup_data["description"],
                difficulty=lineup_data.get("difficulty", 3),
                core_heroes=lineup_data.get("core_heroes", []),
                optional_heroes=lineup_data.get("optional_heroes", []),
                synergies=lineup_data.get("synergies", {}),
                play_style=lineup_data.get("play_style", "balanced"),
                early_game=lineup_data.get("early_game", []),
                mid_game=lineup_data.get("mid_game", []),
                late_game=lineup_data.get("late_game", []),
                key_items=lineup_data.get("key_items", []),
                tips=lineup_data.get("tips", []),
                win_rate=lineup_data.get("win_rate", 0.5),
                popularity=lineup_data.get("popularity", 0.5),
            )

            # 添加匹配度信息到元数据
            lineup.metadata = {"match_score": score}  # type: ignore
            recommendations.append(lineup)

        return recommendations

    def _calculate_lineup_match_score(
        self,
        lineup_data: dict[str, Any],
        current_hero_ids: set,
        current_synergies: dict[str, int],
    ) -> float:
        """计算阵容匹配度"""
        score = 0.0

        # 核心英雄匹配
        core_heroes = set(lineup_data.get("core_heroes", []))
        core_match = len(current_hero_ids & core_heroes) / max(len(core_heroes), 1)
        score += core_match * 40

        # 羁绊匹配
        lineup_synergies = lineup_data.get("synergies", {})
        synergy_match = 0.0
        for syn_name, required_count in lineup_synergies.items():
            current_count = current_synergies.get(syn_name, 0)
            if current_count >= required_count:
                synergy_match += 1
            elif current_count > 0:
                synergy_match += current_count / required_count
        if lineup_synergies:
            synergy_match /= len(lineup_synergies)
        score += synergy_match * 40

        # 阵容强度和流行度
        score += lineup_data.get("win_rate", 0.5) * 10
        score += lineup_data.get("popularity", 0.5) * 10

        return round(score, 2)

    # ========================================================================
    # 装备建议
    # ========================================================================

    def get_equipment_advice(
        self,
        player_id: int,
        equipment: list[dict[str, Any]],
        heroes: list[dict[str, Any]],
    ) -> list[EquipmentAdvice]:
        """
        获取装备建议

        Args:
            player_id: 玩家ID
            equipment: 当前装备列表
            heroes: 当前英雄列表

        Returns:
            装备建议列表
        """
        advice_list = []

        # 识别核心英雄（高费用、高星级）
        core_heroes = sorted(
            [h for h in heroes if h.get("cost", 1) >= 3],
            key=lambda h: h.get("stars", 1) * h.get("cost", 1),
            reverse=True,
        )

        # 基础装备和成品装备分离
        base_equipment = [e for e in equipment if e.get("tier", 1) == 1]
        advanced_equipment = [e for e in equipment if e.get("tier", 1) >= 2]

        # 装备分配建议
        for hero in core_heroes[:3]:  # 只考虑前3个核心英雄
            hero_id = hero.get("hero_id")
            hero_name = hero.get("name", "Unknown")
            hero_type = hero.get("profession", "fighter")

            # 根据英雄类型推荐装备
            recommended_equips = self._get_recommended_equipment_for_hero(
                hero_type, base_equipment, advanced_equipment
            )

            for equip in recommended_equips:
                advice = EquipmentAdvice(
                    equipment_id=equip.get("equipment_id", ""),
                    equipment_name=equip.get("name", ""),
                    target_hero_id=hero_id,
                    reason=f"为{hero_name}提供适合的属性加成",
                    recipe=equip.get("recipe"),
                    priority=Priority.HIGH if hero == core_heroes[0] else Priority.MEDIUM,
                    expected_stat_boost=equip.get("stats", {}),
                )
                advice_list.append(advice)

        # 装备合成建议
        for base_equip in base_equipment:
            # 检查是否可以合成
            craft_recipe = self._find_craft_recipe(base_equip, base_equipment)
            if craft_recipe:
                advice = EquipmentAdvice(
                    equipment_id=craft_recipe["result_id"],
                    equipment_name=craft_recipe["result_name"],
                    target_hero_id=None,
                    reason="合成高级装备提升整体战力",
                    recipe=craft_recipe["ingredients"],
                    priority=Priority.MEDIUM,
                    expected_stat_boost=craft_recipe.get("stats", {}),
                )
                advice_list.append(advice)

        return advice_list[:10]

    def _get_recommended_equipment_for_hero(
        self,
        hero_type: str,
        base_equipment: list[dict[str, Any]],
        advanced_equipment: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """获取英雄的推荐装备"""
        recommendations = []

        # 根据英雄类型推荐
        if hero_type in ["法师", "术士"]:
            # 法术型：法强、蓝量
            for equip in advanced_equipment:
                if "spell_power" in equip.get("stats", {}):
                    recommendations.append(equip)
                    break
            for equip in base_equipment:
                if equip.get("type") == "staff":
                    recommendations.append(equip)

        elif hero_type in ["射手", "刺客"]:
            # 物理型：攻击、暴击、攻速
            for equip in advanced_equipment:
                stats = equip.get("stats", {})
                if "attack" in stats or "crit" in stats:
                    recommendations.append(equip)
                    break
            for equip in base_equipment:
                if equip.get("type") == "sword":
                    recommendations.append(equip)

        elif hero_type in ["坦克", "战士"]:
            # 防御型：护甲、血量
            for equip in advanced_equipment:
                stats = equip.get("stats", {})
                if "armor" in stats or "hp" in stats:
                    recommendations.append(equip)
                    break
            for equip in base_equipment:
                if equip.get("type") in ["armor", "cloak"]:
                    recommendations.append(equip)

        return recommendations[:3]

    def _find_craft_recipe(
        self,
        base_equip: dict[str, Any],
        all_base_equipment: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        """查找合成配方"""
        # 简化的合成配方查找
        equip_type = base_equip.get("type", "")
        equip_id = base_equip.get("equipment_id", "")

        # 检查是否有同类型的装备可以合成
        for other_equip in all_base_equipment:
            if other_equip.get("equipment_id") == equip_id:
                continue
            if other_equip.get("type") == equip_type:
                # 可以合成
                return {
                    "result_id": f"advanced_{equip_type}",
                    "result_name": f"高级{equip_type}",
                    "ingredients": [equip_id, other_equip.get("equipment_id")],
                    "stats": {"upgrade": 2},
                }

        return None

    # ========================================================================
    # 站位优化
    # ========================================================================

    def get_position_advice(
        self,
        player_id: int,
        board: dict[str, Any],
        heroes: list[dict[str, Any]],
    ) -> list[PositionAdvice]:
        """
        获取站位建议

        Args:
            player_id: 玩家ID
            board: 当前棋盘状态
            heroes: 当前英雄列表

        Returns:
            站位建议列表
        """
        advice_list = []

        # 识别英雄类型
        tanks = []
        dps = []
        supports = []

        for hero in heroes:
            profession = hero.get("profession", "")
            if profession in ["坦克", "战士"]:
                tanks.append(hero)
            elif profession in ["射手", "法师", "刺客"]:
                dps.append(hero)
            else:
                supports.append(hero)

        # 检查当前站位
        for pos_str, hero_data in board.items():
            if not isinstance(hero_data, dict):
                continue

            hero_id = hero_data.get("hero_id")
            hero_name = hero_data.get("name", "Unknown")

            # 解析当前位置
            parts = pos_str.split("_")
            if len(parts) != 2:
                continue
            current_row = int(parts[0])
            current_col = int(parts[1])

            # 判断英雄类型并给出建议
            profession = hero_data.get("profession", "")

            # 坦克应该在前排
            if hero_data in [h.get("hero_id") for h in tanks]:
                if current_row > 2:
                    # 坦克在后排，建议前移
                    advice = PositionAdvice(
                        hero_id=hero_id,
                        hero_name=hero_name,
                        current_position={"row": current_row, "col": current_col},
                        recommended_position={"row": 1, "col": current_col},
                        reason="坦克英雄应该站在前排吸收伤害",
                        priority=Priority.HIGH,
                        tactical_role="tank",
                    )
                    advice_list.append(advice)

            # 输出应该在后排
            elif hero_data in [h.get("hero_id") for h in dps]:
                if current_row <= 2:
                    # 输出在前排，建议后移
                    advice = PositionAdvice(
                        hero_id=hero_id,
                        hero_name=hero_name,
                        current_position={"row": current_row, "col": current_col},
                        recommended_position={"row": 3, "col": current_col},
                        reason="输出英雄应该在后排安全位置",
                        priority=Priority.HIGH,
                        tactical_role="dps",
                    )
                    advice_list.append(advice)

        return advice_list[:8]

    # ========================================================================
    # 回合策略
    # ========================================================================

    def get_round_strategy(
        self,
        player_id: int,
        round_num: int,
        game_state: dict[str, Any],
    ) -> RoundStrategy:
        """
        获取回合策略

        Args:
            player_id: 玩家ID
            round_num: 当前回合
            game_state: 游戏状态

        Returns:
            回合策略
        """
        # 确定游戏阶段
        if round_num <= 10:
            phase = AnalysisType.EARLY_GAME
            strategy_type = "economic"  # 前期经济优先
            description = "前期积累经济，适度保血"
            key_actions = [
                "积累金币到20-30",
                "购买低费英雄保持战力",
                "观察对手阵容方向",
            ]
            focus_synergies = ["人族", "战士"]  # 通用前期羁绊
            economy_advice = "优先存钱，保持连胜或连败"
            risk_level = "low"
            win_condition = "健康经济进入中期"

        elif round_num <= 20:
            phase = AnalysisType.MID_GAME
            strategy_type = "balanced"  # 中期平衡发展
            description = "中期确立阵容方向，开始D牌"
            key_actions = [
                "确定最终阵容方向",
                "提升核心英雄到2星",
                "达到6-7级",
            ]
            focus_synergies = list(game_state.get("synergies", {}).keys())[:3]
            economy_advice = "适度花钱，保留30金币基础"
            risk_level = "medium"
            win_condition = "阵容成型，血量健康"

        else:
            phase = AnalysisType.LATE_GAME
            strategy_type = "aggressive"  # 后期全力提升
            description = "后期全力提升阵容质量"
            key_actions = [
                "提升核心英雄到3星",
                "达到8级寻找5费英雄",
                "优化装备分配",
            ]
            focus_synergies = list(game_state.get("synergies", {}).keys())[:3]
            economy_advice = "全力花钱，无需保留金币"
            risk_level = "high"
            win_condition = "阵容达到上限，争取前3"

        # 根据实际状态调整
        hp = game_state.get("hp", 100)
        if hp < 30:
            strategy_type = "aggressive"
            risk_level = "high"
            economy_advice = "紧急花钱保血，否则会被淘汰"

        return RoundStrategy(
            round_num=round_num,
            phase=phase,
            strategy_type=strategy_type,
            description=description,
            key_actions=key_actions,
            focus_synergies=focus_synergies,
            economy_advice=economy_advice,
            risk_level=risk_level,
            win_condition=win_condition,
        )

    # ========================================================================
    # 胜率预测
    # ========================================================================

    def predict_win_rate(
        self,
        player_id: int,
        game_state: dict[str, Any],
    ) -> WinRatePrediction:
        """
        预测胜率

        Args:
            player_id: 玩家ID
            game_state: 游戏状态

        Returns:
            胜率预测
        """
        # 计算各项影响因素
        factors: dict[str, float] = {}

        # 阵容强度因素
        lineup_score = self._calculate_lineup_score(game_state)
        factors["lineup_strength"] = lineup_score / 100

        # 经济因素
        gold = game_state.get("gold", 0)
        round_num = game_state.get("round_num", 1)
        if round_num <= 10:
            ideal_gold = 20
        elif round_num <= 20:
            ideal_gold = 40
        else:
            ideal_gold = 60
        factors["economy"] = min(1.0, gold / ideal_gold)

        # 血量因素
        hp = game_state.get("hp", 100)
        factors["hp"] = hp / 100

        # 羁绊因素
        synergies = game_state.get("synergies", {})
        active_synergies = sum(1 for c in synergies.values() if c >= 2)
        factors["synergy"] = min(1.0, active_synergies / 4)

        # 等级因素
        level = game_state.get("level", 1)
        expected_level = min(8, 2 + round_num // 3)
        factors["level"] = min(1.0, level / expected_level)

        # 计算综合胜率

        # 各因素权重
        weights = {
            "lineup_strength": 0.30,
            "economy": 0.15,
            "hp": 0.25,
            "synergy": 0.20,
            "level": 0.10,
        }

        weighted_score = sum(factors[key] * weights.get(key, 0.2) for key in factors)

        # 将分数映射到胜率范围
        # 分数0-1，胜率5%-80%
        predicted_rate = 0.05 + weighted_score * 0.75

        # 置信度计算（基于回合数，后期更确定）
        confidence = min(0.9, 0.5 + round_num * 0.02)

        # 计算排名预测
        rank_score = (1 - weighted_score) * 7 + 1
        comparison_rank = int(max(1, min(8, rank_score)))

        # 识别关键优势和劣势
        key_advantages = []
        key_weaknesses = []

        if factors["lineup_strength"] > 0.7:
            key_advantages.append("阵容强度高")
        if factors["economy"] > 0.7:
            key_advantages.append("经济充裕")
        if factors["hp"] > 0.7:
            key_advantages.append("血量健康")

        if factors["lineup_strength"] < 0.5:
            key_weaknesses.append("阵容强度不足")
        if factors["economy"] < 0.5:
            key_weaknesses.append("经济压力大")
        if factors["hp"] < 0.5:
            key_weaknesses.append("血量偏低")

        # 改进建议
        improvement_suggestions = []
        if factors["lineup_strength"] < 0.6:
            improvement_suggestions.append("提升英雄星级和阵容质量")
        if factors["economy"] < 0.6 and round_num <= 15:
            improvement_suggestions.append("优化经济运营")
        if factors["hp"] < 0.5:
            improvement_suggestions.append("优先保血，适度花钱")
        if factors["synergy"] < 0.5:
            improvement_suggestions.append("完善羁绊组合")

        return WinRatePrediction(
            predicted_win_rate=round(predicted_rate, 3),
            confidence=round(confidence, 2),
            factors=factors,
            comparison_rank=comparison_rank,
            key_advantages=key_advantages,
            key_weaknesses=key_weaknesses,
            improvement_suggestions=improvement_suggestions,
        )

    # ========================================================================
    # 对局历史
    # ========================================================================

    def get_match_history(
        self,
        player_id: int,
        limit: int = 20,
    ) -> list[MatchHistoryItem]:
        """
        获取对局历史

        Args:
            player_id: 玩家ID
            limit: 返回数量限制

        Returns:
            对局历史列表
        """
        # 从缓存获取
        history = self._match_history.get(player_id, [])

        # 如果缓存不足，尝试从数据库加载
        if len(history) < limit:
            # TODO: 从数据库加载历史记录
            pass

        return history[:limit]

    def record_match(
        self,
        player_id: int,
        match_data: dict[str, Any],
    ) -> MatchHistoryItem:
        """
        记录对局结果

        Args:
            player_id: 玩家ID
            match_data: 对局数据

        Returns:
            对局历史记录
        """
        match_item = MatchHistoryItem(
            match_id=match_data.get("match_id", str(uuid.uuid4())),
            game_id=match_data.get("game_id", ""),
            final_rank=match_data.get("final_rank", 8),
            total_rounds=match_data.get("total_rounds", 0),
            duration_seconds=match_data.get("duration_seconds", 0),
            final_lineup=match_data.get("final_lineup", []),
            final_synergies=match_data.get("final_synergies", {}),
            damage_dealt=match_data.get("damage_dealt", 0),
            damage_taken=match_data.get("damage_taken", 0),
            gold_earned=match_data.get("gold_earned", 0),
            key_decisions=match_data.get("key_decisions", []),
        )

        # 更新缓存
        if player_id not in self._match_history:
            self._match_history[player_id] = []
        self._match_history[player_id].insert(0, match_item)

        # 限制缓存大小
        if len(self._match_history[player_id]) > 100:
            self._match_history[player_id] = self._match_history[player_id][:100]

        # 更新玩家统计
        self._update_player_stats(player_id, match_item)

        return match_item

    def _update_player_stats(
        self,
        player_id: int,
        match_item: MatchHistoryItem,
    ) -> None:
        """更新玩家学习统计"""
        if player_id not in self._player_stats:
            self._player_stats[player_id] = PlayerLearningStats(player_id=player_id)

        stats = self._player_stats[player_id]
        stats.total_matches += 1

        if match_item.is_win:
            stats.wins += 1

        if match_item.final_rank <= 4:
            stats.top4_count += 1

        # 更新平均排名
        total_matches = stats.total_matches
        stats.avg_rank = (
            stats.avg_rank * (total_matches - 1) + match_item.final_rank
        ) / total_matches

        # 更新常用羁绊
        for syn_name in match_item.final_synergies:
            stats.favorite_synergies[syn_name] = stats.favorite_synergies.get(syn_name, 0) + 1

    def get_player_stats(self, player_id: int) -> PlayerLearningStats:
        """
        获取玩家学习统计

        Args:
            player_id: 玩家ID

        Returns:
            玩家学习统计
        """
        if player_id not in self._player_stats:
            self._player_stats[player_id] = PlayerLearningStats(player_id=player_id)
        return self._player_stats[player_id]

    # ========================================================================
    # 统计信息
    # ========================================================================

    def get_stats(self) -> dict[str, Any]:
        """
        获取管理器统计信息

        Returns:
            统计信息
        """
        return {
            "total_players_tracked": len(self._player_stats),
            "total_matches_recorded": sum(len(history) for history in self._match_history.values()),
            "total_analyses": len(self._analysis_cache),
            "suggestion_counter": self._suggestion_counter,
            "analysis_counter": self._analysis_counter,
        }


# ========================================================================
# 全局单例
# ========================================================================

_ai_coach_manager: AICoachManager | None = None


def get_ai_coach_manager() -> AICoachManager:
    """
    获取AI教练管理器单例

    Returns:
        AI教练管理器实例
    """
    global _ai_coach_manager
    if _ai_coach_manager is None:
        _ai_coach_manager = AICoachManager()
    return _ai_coach_manager
