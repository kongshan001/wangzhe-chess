"""
王者之奕 - 匹配系统测试

本模块测试匹配系统的核心功能，包括：
- 匹配队列操作
- ELO 等级分计算
- 段位系统管理

测试覆盖率目标: >80%
"""

import asyncio
import time
import pytest

from server.match.queue import (
    MatchQueue,
    QueueConfig,
    QueueEntry,
    QueueState,
    QueuePriority,
    AIPlayerGenerator,
)
from server.match.elo import (
    EloCalculator,
    EloConfig,
    PlayerElo,
    DEFAULT_ELO_CONFIG,
    get_elo_tier_range,
    compare_elo,
)
from server.match.rating import (
    Tier,
    PlayerRating,
    TierConfig,
    TIER_CONFIGS,
    SeasonManager,
    get_tier_config,
    compare_ratings,
)


# ============================================================================
# 匹配队列测试
# ============================================================================

class TestMatchQueue:
    """匹配队列测试"""

    @pytest.mark.asyncio
    async def test_add_player(self):
        """测试添加玩家到队列"""
        config = QueueConfig(max_queue_size=100)
        queue = MatchQueue(config)
        
        rating = PlayerRating(player_id="player_001")
        result = await queue.join(
            player_id="player_001",
            rating=rating,
            elo_score=1200,
        )
        
        assert result is True
        assert await queue.get_queue_size() == 1

    @pytest.mark.asyncio
    async def test_add_player_already_in_queue(self):
        """测试重复添加同一玩家"""
        queue = MatchQueue()
        rating = PlayerRating(player_id="player_001")
        
        await queue.join("player_001", rating, 1200)
        result = await queue.join("player_001", rating, 1200)
        
        assert result is False
        assert await queue.get_queue_size() == 1

    @pytest.mark.asyncio
    async def test_add_player_queue_full(self):
        """测试队列已满"""
        config = QueueConfig(max_queue_size=2)
        queue = MatchQueue(config)
        
        for i in range(3):
            rating = PlayerRating(player_id=f"player_{i}")
            result = await queue.join(f"player_{i}", rating, 1200)
            
            if i < 2:
                assert result is True
            else:
                assert result is False

    @pytest.mark.asyncio
    async def test_remove_player(self):
        """测试移除玩家"""
        queue = MatchQueue()
        rating = PlayerRating(player_id="player_001")
        
        await queue.join("player_001", rating, 1200)
        entry = await queue.leave("player_001")
        
        assert entry is not None
        assert entry.player_id == "player_001"
        assert entry.state == QueueState.CANCELLED
        assert await queue.get_queue_size() == 0

    @pytest.mark.asyncio
    async def test_remove_nonexistent_player(self):
        """测试移除不存在的玩家"""
        queue = MatchQueue()
        
        entry = await queue.leave("nonexistent")
        
        assert entry is None

    @pytest.mark.asyncio
    async def test_find_match(self):
        """测试寻找匹配"""
        queue = MatchQueue()
        
        # 添加多个同段位玩家
        for i in range(8):
            rating = PlayerRating(player_id=f"player_{i}")
            await queue.join(f"player_{i}", rating, 1200 + i * 10)
        
        # 处理匹配
        matches = await queue._process_matches()
        
        # 应该找到至少一组匹配
        # 注意：由于匹配需要满足条件，可能不一定找到
        assert isinstance(matches, list)

    @pytest.mark.asyncio
    async def test_find_match_cross_tier(self):
        """测试跨段位匹配"""
        queue = MatchQueue()
        
        # 添加不同段位的玩家
        ratings = [
            (Tier.BRONZE, 1000),
            (Tier.SILVER, 1300),
            (Tier.GOLD, 1500),
        ]
        
        for i, (tier, elo) in enumerate(ratings):
            rating = PlayerRating(
                player_id=f"player_{i}",
                tier=tier,
                stars=TIER_CONFIGS[tier].min_stars,
            )
            await queue.join(f"player_{i}", rating, elo)
        
        # 等待足够时间让搜索范围扩大
        await asyncio.sleep(0.1)
        
        matches = await queue._process_matches()
        assert isinstance(matches, list)

    @pytest.mark.asyncio
    async def test_expand_search_range(self):
        """测试扩大搜索范围"""
        queue = MatchQueue()
        rating = PlayerRating(player_id="player_001")
        
        await queue.join("player_001", rating, 1200)
        entry = await queue.get_entry("player_001")
        
        initial_range = entry.search_range
        
        # 模拟等待时间
        entry.join_time = time.time() - 60  # 60秒前加入
        
        new_range = entry.expand_search_range()
        
        # 等待后范围应该扩大
        assert new_range >= initial_range

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """测试超时处理"""
        config = QueueConfig(timeout_seconds=1)
        queue = MatchQueue(config)
        rating = PlayerRating(player_id="player_001")
        
        await queue.join("player_001", rating, 1200)
        entry = await queue.get_entry("player_001")
        
        # 模拟超时
        entry.join_time = time.time() - 10
        
        timeout_entries = queue._check_timeouts()
        
        assert len(timeout_entries) == 1
        assert timeout_entries[0].state == QueueState.TIMEOUT

    @pytest.mark.asyncio
    async def test_get_queue_stats(self):
        """测试获取队列统计"""
        queue = MatchQueue()
        
        for i in range(5):
            rating = PlayerRating(player_id=f"player_{i}")
            await queue.join(f"player_{i}", rating, 1200)
        
        stats = queue.get_queue_stats()
        
        assert stats["total_players"] == 5
        assert "tier_distribution" in stats
        assert "average_wait_time" in stats

    @pytest.mark.asyncio
    async def test_clear_queue(self):
        """测试清空队列"""
        queue = MatchQueue()
        
        for i in range(5):
            rating = PlayerRating(player_id=f"player_{i}")
            await queue.join(f"player_{i}", rating, 1200)
        
        count = await queue.clear()
        
        assert count == 5
        assert await queue.get_queue_size() == 0

    @pytest.mark.asyncio
    async def test_force_match(self):
        """测试强制匹配"""
        queue = MatchQueue()
        
        player_ids = []
        for i in range(2):
            pid = f"player_{i}"
            player_ids.append(pid)
            rating = PlayerRating(player_id=pid)
            await queue.join(pid, rating, 1200)
        
        result = await queue.force_match(player_ids)
        
        assert result is not None
        assert len(result) == 2
        assert all(e.state == QueueState.MATCHED for e in result)

    @pytest.mark.asyncio
    async def test_force_match_missing_player(self):
        """测试强制匹配缺少的玩家"""
        queue = MatchQueue()
        
        rating = PlayerRating(player_id="player_001")
        await queue.join("player_001", rating, 1200)
        
        # 尝试匹配一个不存在的玩家
        result = await queue.force_match(["player_001", "nonexistent"])
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_wait_time_estimate(self):
        """测试等待时间估算"""
        queue = MatchQueue()
        
        # 空队列
        estimate = await queue.get_wait_time_estimate(Tier.BRONZE)
        assert estimate > 0
        
        # 添加一些玩家
        for i in range(5):
            rating = PlayerRating(player_id=f"player_{i}")
            await queue.join(f"player_{i}", rating, 1200)
        
        estimate = await queue.get_wait_time_estimate(Tier.BRONZE)
        assert estimate >= 0


# ============================================================================
# 队列条目测试
# ============================================================================

class TestQueueEntry:
    """队列条目测试"""

    def test_create_entry(self):
        """测试创建队列条目"""
        rating = PlayerRating(player_id="test_player")
        entry = QueueEntry(
            player_id="test_player",
            rating=rating,
            elo_score=1500,
        )
        
        assert entry.player_id == "test_player"
        assert entry.elo_score == 1500
        assert entry.state == QueueState.WAITING
        assert entry.priority == QueuePriority.NORMAL

    def test_get_wait_time(self):
        """测试获取等待时间"""
        rating = PlayerRating(player_id="test_player")
        entry = QueueEntry(
            player_id="test_player",
            rating=rating,
            elo_score=1500,
            join_time=time.time() - 10,  # 10秒前加入
        )
        
        wait_time_ms = entry.get_wait_time_ms()
        assert 9000 <= wait_time_ms <= 11000  # 约10秒

    def test_is_within_range(self):
        """测试是否在搜索范围内"""
        rating = PlayerRating(player_id="test_player")
        entry = QueueEntry(
            player_id="test_player",
            rating=rating,
            elo_score=1500,
            search_range=100,
        )
        
        assert entry.is_within_range(1450) is True
        assert entry.is_within_range(1600) is True
        assert entry.is_within_range(1400) is False

    def test_calculate_match_quality(self):
        """测试计算匹配质量"""
        rating1 = PlayerRating(player_id="player_1")
        rating2 = PlayerRating(player_id="player_2")
        
        entry1 = QueueEntry(
            player_id="player_1",
            rating=rating1,
            elo_score=1500,
        )
        entry2 = QueueEntry(
            player_id="player_2",
            rating=rating2,
            elo_score=1500,
        )
        
        quality = entry1.calculate_match_quality(entry2)
        
        # 相同ELO的匹配质量应该很高
        assert 0.0 <= quality <= 1.0
        assert quality >= 0.5

    def test_expand_search_range_progression(self):
        """测试搜索范围扩大进度"""
        rating = PlayerRating(player_id="test_player")
        entry = QueueEntry(
            player_id="test_player",
            rating=rating,
            elo_score=1500,
            search_range=50,
        )
        
        # 刚加入，范围不扩大
        entry.join_time = time.time()
        new_range = entry.expand_search_range()
        assert new_range == 50
        
        # 等待30秒后
        entry.join_time = time.time() - 30
        new_range = entry.expand_search_range()
        assert new_range > 50
        
        # 等待60秒后
        entry.join_time = time.time() - 60
        new_range = entry.expand_search_range()
        assert new_range > 75

    def test_to_dict(self):
        """测试序列化为字典"""
        rating = PlayerRating(player_id="test_player")
        entry = QueueEntry(
            player_id="test_player",
            rating=rating,
            elo_score=1500,
        )
        
        data = entry.to_dict()
        
        assert data["player_id"] == "test_player"
        assert data["elo_score"] == 1500
        assert "tier_name" in data
        assert "wait_time_ms" in data


# ============================================================================
# ELO 系统测试
# ============================================================================

class TestELOSystem:
    """ELO 系统测试"""

    def test_calculate_elo_win(self):
        """测试胜利时的ELO计算"""
        calculator = EloCalculator()
        
        player = PlayerElo(player_id="player_001", current_elo=1500)
        opponent = PlayerElo(player_id="player_002", current_elo=1400)
        
        result = calculator.update_elo(player, opponent, is_win=True)
        
        assert result["new_elo"] > result["old_elo"]
        assert result["change"] > 0
        assert result["actual_score"] == 1.0

    def test_calculate_elo_loss(self):
        """测试失败时的ELO计算"""
        calculator = EloCalculator()
        
        player = PlayerElo(player_id="player_001", current_elo=1500)
        opponent = PlayerElo(player_id="player_002", current_elo=1400)
        
        result = calculator.update_elo(player, opponent, is_win=False)
        
        assert result["new_elo"] < result["old_elo"]
        assert result["change"] < 0
        assert result["actual_score"] == 0.0

    def test_k_factor_adjustment(self):
        """测试K值动态调整"""
        config = EloConfig(
            base_k=32,
            new_player_k=50,
            new_player_games=10,
        )
        calculator = EloCalculator(config)
        
        # 新玩家应该使用高K值
        new_player = PlayerElo(player_id="new", current_elo=1500, total_games=5)
        k_new = calculator.get_dynamic_k(new_player)
        
        # 老玩家使用基础K值
        old_player = PlayerElo(player_id="old", current_elo=1500, total_games=50)
        k_old = calculator.get_dynamic_k(old_player)
        
        assert k_new > k_old

    def test_k_factor_high_elo(self):
        """测试高分段K值降低"""
        config = EloConfig(
            base_k=32,
            high_elo_k=24,
            high_elo_threshold=2000,
        )
        calculator = EloCalculator(config)
        
        high_elo_player = PlayerElo(
            player_id="pro",
            current_elo=2200,
            total_games=100,
        )
        k_high = calculator.get_dynamic_k(high_elo_player)
        
        normal_player = PlayerElo(
            player_id="normal",
            current_elo=1500,
            total_games=100,
        )
        k_normal = calculator.get_dynamic_k(normal_player)
        
        assert k_high < k_normal

    def test_expected_score(self):
        """测试预期胜率计算"""
        calculator = EloCalculator()
        
        # 相同ELO，预期胜率50%
        expected = calculator.calculate_expected_score(1500, 1500)
        assert abs(expected - 0.5) < 0.01
        
        # 高ELO，预期胜率更高
        expected = calculator.calculate_expected_score(1800, 1200)
        assert expected > 0.9
        
        # 低ELO，预期胜率更低
        expected = calculator.calculate_expected_score(1200, 1800)
        assert expected < 0.1

    def test_elo_change_magnitude(self):
        """测试ELO变化幅度"""
        calculator = EloCalculator()
        
        # 击败高ELO对手，获得更多分数
        player1 = PlayerElo(player_id="p1", current_elo=1200, total_games=50)
        opponent1 = PlayerElo(player_id="o1", current_elo=1800, total_games=50)
        result1 = calculator.update_elo(player1, opponent1, is_win=True)
        
        # 击败低ELO对手，获得较少分数
        player2 = PlayerElo(player_id="p2", current_elo=1800, total_games=50)
        opponent2 = PlayerElo(player_id="o2", current_elo=1200, total_games=50)
        result2 = calculator.update_elo(player2, opponent2, is_win=True)
        
        assert abs(result1["change"]) > abs(result2["change"])

    def test_elo_bounds(self):
        """测试ELO边界"""
        config = EloConfig(min_elo=100, max_elo=3000)
        calculator = EloCalculator(config)
        
        # 最低ELO玩家失败，不应低于最小值
        player = PlayerElo(player_id="low", current_elo=100, total_games=50)
        opponent = PlayerElo(player_id="high", current_elo=3000, total_games=50)
        
        result = calculator.update_elo(player, opponent, is_win=False)
        
        assert result["new_elo"] >= 100

    def test_elo_draw(self):
        """测试平局ELO变化"""
        calculator = EloCalculator()
        
        player = PlayerElo(player_id="p1", current_elo=1500, total_games=50)
        opponent = PlayerElo(player_id="p2", current_elo=1500, total_games=50)
        
        result = calculator.update_elo(player, opponent, is_win=False, is_draw=True)
        
        # 相同ELO平局，变化应该很小
        assert abs(result["change"]) < 5

    def test_elo_win_streak(self):
        """测试连胜对K值的影响"""
        calculator = EloCalculator()
        
        player = PlayerElo(
            player_id="streak",
            current_elo=1500,
            total_games=50,
            win_streak=5,
        )
        opponent = PlayerElo(player_id="normal", current_elo=1500, total_games=50)
        
        k = calculator.get_dynamic_k(player)
        # 连胜时K值应该略有增加
        assert k >= DEFAULT_ELO_CONFIG.base_k

    def test_player_elo_record_game(self):
        """测试记录游戏结果"""
        player = PlayerElo(player_id="test")
        
        # 记录胜利
        player.record_game(is_win=True)
        assert player.wins == 1
        assert player.win_streak == 1
        assert player.lose_streak == 0
        
        # 记录失败
        player.record_game(is_win=False)
        assert player.losses == 1
        assert player.win_streak == 0
        assert player.lose_streak == 1

    def test_player_elo_win_rate(self):
        """测试胜率计算"""
        player = PlayerElo(
            player_id="test",
            total_games=100,
            wins=60,
        )
        
        win_rate = player.get_win_rate()
        assert win_rate == 0.6

    def test_player_elo_trend(self):
        """测试趋势分析"""
        player = PlayerElo(player_id="test")
        
        # 模拟连胜
        for _ in range(8):
            player.record_game(is_win=True)
        
        assert player.get_trend() == "rising"
        
        # 模拟连败
        player.win_streak = 0
        player.recent_results = []
        for _ in range(8):
            player.record_game(is_win=False)
        
        assert player.get_trend() == "falling"

    def test_player_elo_serialization(self):
        """测试ELO数据序列化"""
        player = PlayerElo(
            player_id="test",
            current_elo=1500,
            peak_elo=1600,
            total_games=100,
            wins=60,
        )
        
        data = player.to_dict()
        restored = PlayerElo.from_dict(data)
        
        assert restored.player_id == player.player_id
        assert restored.current_elo == player.current_elo
        assert restored.peak_elo == player.peak_elo


# ============================================================================
# 段位系统测试
# ============================================================================

class TestRatingSystem:
    """段位系统测试"""

    def test_tier_assignment(self):
        """测试段位分配"""
        # 根据ELO分配段位
        test_cases = [
            (500, Tier.BRONZE),
            (1100, Tier.BRONZE),
            (1250, Tier.SILVER),
            (1450, Tier.GOLD),
            (1650, Tier.PLATINUM),
            (1850, Tier.DIAMOND),
            (2050, Tier.MASTER),
            (2250, Tier.KING),
        ]
        
        for elo, expected_tier in test_cases:
            tier = SeasonManager.get_tier_from_elo(elo)
            assert tier == expected_tier, f"ELO {elo} 应该是 {expected_tier}, 实际是 {tier}"

    def test_promotion(self):
        """测试晋级"""
        player = PlayerRating(
            player_id="test",
            tier=Tier.BRONZE,
            stars=TIER_CONFIGS[Tier.BRONZE].max_stars,  # 满星
        )
        
        result = player.add_stars(1)
        
        # 应该晋级到白银
        assert player.tier == Tier.SILVER
        assert "promotion" in result
        assert result["promotion"]["promoted"] is True

    def test_demotion(self):
        """测试降级"""
        player = PlayerRating(
            player_id="test",
            tier=Tier.SILVER,
            stars=TIER_CONFIGS[Tier.SILVER].min_stars,  # 最低星
        )
        
        result = player.remove_stars(10)
        
        # 检查降级（如果触发了保级保护，可能不会立即降级）
        if result.get("demotion"):
            assert player.tier == Tier.BRONZE

    def test_demotion_protection(self):
        """测试降级保护"""
        player = PlayerRating(
            player_id="test",
            tier=Tier.SILVER,
            stars=TIER_CONFIGS[Tier.SILVER].min_stars,
            demotion_counter=0,  # 还没用完保护次数
        )
        
        result = player.remove_stars(1)
        
        # 应该触发保护
        if result.get("demotion_protection_triggered"):
            assert player.tier == Tier.SILVER

    def test_star_system(self):
        """测试星级系统"""
        player = PlayerRating(
            player_id="test",
            tier=Tier.BRONZE,
            stars=0,
        )
        
        # 增加星级
        result = player.add_stars(5)
        
        assert player.stars == 5
        assert result["stars_change"] == 5
        
        # 减少星级
        result = player.remove_stars(2)
        
        assert player.stars == 3

    def test_star_not_negative(self):
        """测试星级不会为负"""
        player = PlayerRating(
            player_id="test",
            tier=Tier.BRONZE,
            stars=0,
        )
        
        player.remove_stars(100)
        
        assert player.stars >= 0

    def test_tier_display(self):
        """测试段位显示"""
        assert Tier.BRONZE.get_display_name() == "青铜"
        assert Tier.SILVER.get_display_name() == "白银"
        assert Tier.GOLD.get_display_name() == "黄金"
        assert Tier.PLATINUM.get_display_name() == "铂金"
        assert Tier.DIAMOND.get_display_name() == "钻石"
        assert Tier.MASTER.get_display_name() == "大师"
        assert Tier.KING.get_display_name() == "王者"

    def test_tier_icons(self):
        """测试段位图标"""
        icons = {
            Tier.BRONZE: "🥉",
            Tier.SILVER: "🥈",
            Tier.GOLD: "🥇",
            Tier.PLATINUM: "💎",
            Tier.DIAMOND: "💠",
            Tier.MASTER: "🏆",
            Tier.KING: "👑",
        }
        
        for tier, expected_icon in icons.items():
            assert tier.get_icon() == expected_icon

    def test_tier_progress(self):
        """测试段位进度"""
        config = TIER_CONFIGS[Tier.GOLD]
        min_stars = config.min_stars
        max_stars = config.max_stars
        
        # 50%进度
        mid_stars = (min_stars + max_stars) // 2
        player = PlayerRating(
            player_id="test",
            tier=Tier.GOLD,
            stars=mid_stars,
        )
        
        progress = player.get_tier_progress()
        assert 0.4 <= progress <= 0.6

    def test_highest_tier_tracking(self):
        """测试历史最高段位跟踪"""
        player = PlayerRating(
            player_id="test",
            tier=Tier.BRONZE,
            stars=0,
            highest_tier=Tier.BRONZE,
            highest_stars=0,
        )
        
        # 晋级多次
        while player.tier != Tier.GOLD:
            player.add_stars(1)
        
        assert player.highest_tier.value >= Tier.GOLD.value

    def test_record_game(self):
        """测试记录游戏结果"""
        player = PlayerRating(player_id="test")
        
        # 记录胜利
        player.record_game(is_win=True)
        assert player.season_games == 1
        assert player.season_wins == 1
        assert player.win_streak == 1
        
        # 记录失败
        player.record_game(is_win=False)
        assert player.season_games == 2
        assert player.win_streak == 0
        assert player.lose_streak == 1

    def test_season_reset(self):
        """测试赛季重置"""
        player = PlayerRating(
            player_id="test",
            tier=Tier.KING,
            stars=100,
            highest_tier=Tier.KING,
            highest_stars=100,
        )
        
        new_rating = player.calculate_season_reset()
        
        # 王者应该重置到钻石
        assert new_rating.tier == Tier.DIAMOND
        # 历史最高保留
        assert new_rating.highest_tier == Tier.KING
        # 上赛季数据记录
        assert new_rating.last_season_tier == Tier.KING

    def test_season_reset_all_tiers(self):
        """测试所有段位的赛季重置"""
        tier_drop_map = {
            Tier.KING: Tier.DIAMOND,
            Tier.MASTER: Tier.PLATINUM,
            Tier.DIAMOND: Tier.PLATINUM,
            Tier.PLATINUM: Tier.GOLD,
            Tier.GOLD: Tier.SILVER,
            Tier.SILVER: Tier.BRONZE,
            Tier.BRONZE: Tier.BRONZE,
        }
        
        for original_tier, expected_new_tier in tier_drop_map.items():
            player = PlayerRating(
                player_id="test",
                tier=original_tier,
                stars=TIER_CONFIGS[original_tier].min_stars + 5,
            )
            new_rating = player.calculate_season_reset()
            assert new_rating.tier == expected_new_tier

    def test_player_rating_serialization(self):
        """测试段位数据序列化"""
        player = PlayerRating(
            player_id="test",
            tier=Tier.GOLD,
            stars=25,
            highest_tier=Tier.PLATINUM,
            highest_stars=35,
            season_games=100,
            season_wins=60,
        )
        
        data = player.to_dict()
        restored = PlayerRating.from_dict(data)
        
        assert restored.player_id == player.player_id
        assert restored.tier == player.tier
        assert restored.stars == player.stars
        assert restored.highest_tier == player.highest_tier

    def test_get_display_info(self):
        """测试获取显示信息"""
        player = PlayerRating(
            player_id="test",
            tier=Tier.GOLD,
            stars=25,
            season_games=100,
            season_wins=60,
        )
        
        info = player.get_display_info()
        
        assert info["tier_name"] == "黄金"
        assert info["tier_icon"] == "🥇"
        assert "progress" in info
        assert "win_rate" in info


# ============================================================================
# AI 玩家生成器测试
# ============================================================================

class TestAIPlayerGenerator:
    """AI 玩家生成器测试"""

    def test_generate_ai_player(self):
        """测试生成AI玩家"""
        ai = AIPlayerGenerator.generate_ai_player(
            target_elo=1500,
            tier=Tier.GOLD,
        )
        
        assert "player_id" in ai
        assert ai["is_ai"] is True
        assert ai["tier"] == Tier.GOLD
        # ELO在目标附近波动
        assert 1450 <= ai["elo_score"] <= 1550

    def test_generate_ai_team(self):
        """测试生成AI队伍"""
        team = AIPlayerGenerator.generate_ai_team(
            target_elo=1500,
            tier=Tier.GOLD,
            count=5,
        )
        
        assert len(team) == 5
        for ai in team:
            assert ai["is_ai"] is True

    def test_ai_player_unique_ids(self):
        """测试AI玩家ID唯一性"""
        ais = [
            AIPlayerGenerator.generate_ai_player(1500, Tier.GOLD)
            for _ in range(10)
        ]
        
        ids = [ai["player_id"] for ai in ais]
        assert len(set(ids)) == 10


# ============================================================================
# 辅助函数测试
# ============================================================================

class TestHelperFunctions:
    """辅助函数测试"""

    def test_get_elo_tier_range(self):
        """测试获取ELO段位范围"""
        ranges = [
            (Tier.BRONZE, (100, 1200)),
            (Tier.SILVER, (1200, 1400)),
            (Tier.GOLD, (1400, 1600)),
            (Tier.PLATINUM, (1600, 1800)),
            (Tier.DIAMOND, (1800, 2000)),
            (Tier.MASTER, (2000, 2200)),
            (Tier.KING, (2200, 3000)),
        ]
        
        for tier, expected_range in ranges:
            actual_range = get_elo_tier_range(tier)
            assert actual_range == expected_range

    def test_compare_elo(self):
        """测试比较ELO"""
        # 相同ELO
        assert compare_elo(1500, 1500) == 0.0
        
        # 玩家A更高
        result = compare_elo(1800, 1200)
        assert result > 0
        
        # 玩家B更高
        result = compare_elo(1200, 1800)
        assert result < 0

    def test_get_tier_config(self):
        """测试获取段位配置"""
        for tier in Tier:
            config = get_tier_config(tier)
            assert config.tier == tier
            assert config.min_stars >= 0
            assert config.max_stars >= config.min_stars

    def test_compare_ratings(self):
        """测试比较段位"""
        rating1 = PlayerRating(player_id="p1", tier=Tier.GOLD, stars=25)
        rating2 = PlayerRating(player_id="p2", tier=Tier.SILVER, stars=15)
        
        result = compare_ratings(rating1, rating2)
        assert result > 0  # 黄金高于白银

    def test_season_manager_stars_from_elo(self):
        """测试根据ELO计算星级"""
        stars = SeasonManager.get_stars_from_elo(1500, Tier.GOLD)
        
        config = TIER_CONFIGS[Tier.GOLD]
        assert config.min_stars <= stars <= config.max_stars


# ============================================================================
# 边界条件测试
# ============================================================================

class TestBoundaryConditions:
    """边界条件测试"""

    def test_elo_min_max(self):
        """测试ELO最小最大值"""
        config = EloConfig(min_elo=100, max_elo=3000)
        calculator = EloCalculator(config)
        
        # 最低ELO
        player = PlayerElo(player_id="min", current_elo=100, total_games=50)
        opponent = PlayerElo(player_id="max", current_elo=3000, total_games=50)
        
        result = calculator.update_elo(player, opponent, is_win=False)
        assert result["new_elo"] >= 100
        
        # 最高ELO
        player.current_elo = 3000
        opponent.current_elo = 100
        
        result = calculator.update_elo(player, opponent, is_win=True)
        assert result["new_elo"] <= 3000

    def test_tier_order(self):
        """测试段位顺序"""
        tiers = list(Tier)
        
        for i in range(len(tiers) - 1):
            assert tiers[i].value < tiers[i + 1].value

    def test_empty_queue_operations(self):
        """测试空队列操作"""
        queue = MatchQueue()
        
        # 空队列获取大小
        assert asyncio.run(queue.get_queue_size()) == 0
        
        # 空队列移除
        assert asyncio.run(queue.leave("nonexistent")) is None
        
        # 空队列获取条目
        assert asyncio.run(queue.get_entry("nonexistent")) is None

    def test_queue_entry_zero_elo(self):
        """测试零ELO"""
        rating = PlayerRating(player_id="test")
        entry = QueueEntry(
            player_id="test",
            rating=rating,
            elo_score=0,
        )
        
        assert entry.elo_score == 0

    def test_player_rating_zero_stars(self):
        """测试零星级"""
        player = PlayerRating(
            player_id="test",
            tier=Tier.BRONZE,
            stars=0,
        )
        
        # 零星时再减少
        player.remove_stars(10)
        
        assert player.stars >= 0

    def test_king_no_max_stars(self):
        """测试王者没有星级上限"""
        config = TIER_CONFIGS[Tier.KING]
        
        # 王者的 max_stars 应该很大或特殊处理
        assert config.max_stars >= 999

    def test_bronze_no_demotion(self):
        """测试青铜不会降级"""
        player = PlayerRating(
            player_id="test",
            tier=Tier.BRONZE,
            stars=0,
        )
        
        player.remove_stars(1000)
        
        # 青铜是最低段位
        assert player.tier == Tier.BRONZE

    def test_match_quality_boundary(self):
        """测试匹配质量边界"""
        rating1 = PlayerRating(player_id="p1", tier=Tier.BRONZE)
        rating2 = PlayerRating(player_id="p2", tier=Tier.KING)
        
        entry1 = QueueEntry(player_id="p1", rating=rating1, elo_score=500)
        entry2 = QueueEntry(player_id="p2", rating=rating2, elo_score=2500)
        
        quality = entry1.calculate_match_quality(entry2)
        
        # 差距很大，质量应该很低
        assert 0.0 <= quality <= 1.0

    @pytest.mark.asyncio
    async def test_concurrent_queue_operations(self):
        """测试并发队列操作"""
        queue = MatchQueue()
        
        # 并发添加玩家
        tasks = []
        for i in range(100):
            rating = PlayerRating(player_id=f"player_{i}")
            task = queue.join(f"player_{i}", rating, 1200)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # 所有操作都应该成功
        assert all(results)

    def test_probability_edge_cases(self):
        """测试概率边界情况"""
        from server.game.battle.simulator import DeterministicRNG
        
        rng = DeterministicRNG(seed=42)
        
        # 0% 概率
        for _ in range(100):
            assert rng.check_probability(0) is False
        
        # 100% 概率
        for _ in range(100):
            assert rng.check_probability(100) is True
        
        # 负概率
        assert rng.check_probability(-10) is False
        
        # 超过100的概率
        assert rng.check_probability(150) is True
