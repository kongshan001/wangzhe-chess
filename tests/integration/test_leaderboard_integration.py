"""
王者之奕 - 排行榜数据更新集成测试

测试排行榜数据更新的跨模块交互：
- 对局结束更新排行榜
- 排名计算与更新
- 排行榜奖励发放
- 周期切换与重置
"""

import pytest

from src.server.leaderboard import (
    LeaderboardManager,
    LeaderboardPeriod,
    LeaderboardType,
)


class TestLeaderboardIntegration:
    """排行榜集成测试"""

    @pytest.fixture
    def leaderboard_manager(self):
        """创建排行榜管理器"""
        return LeaderboardManager()

    @pytest.fixture
    def sample_players(self) -> list[dict]:
        """创建示例玩家数据"""
        return [
            {
                "player_id": f"player_{i:03d}",
                "nickname": f"玩家{i}",
                "avatar": f"avatar_{i}.png",
                "tier": ["bronze", "silver", "gold", "platinum", "diamond"][min(i // 2, 4)],
                "stars": i % 5,
                "tier_score": 1000 + i * 100,
                "win_count": 10 + i * 5,
                "total_count": 20 + i * 8,
                "first_place_count": i,
                "max_damage": 1000 + i * 200,
                "total_gold": 5000 + i * 500,
            }
            for i in range(10)
        ]

    def test_update_player_data(self, leaderboard_manager, sample_players):
        """测试更新玩家数据"""
        player = sample_players[0]

        leaderboard_manager.update_player_data(
            player_id=player["player_id"],
            nickname=player["nickname"],
            avatar=player["avatar"],
            tier=player["tier"],
            stars=player["stars"],
            tier_score=player["tier_score"],
            win_count=player["win_count"],
            total_count=player["total_count"],
            first_place_count=player["first_place_count"],
            max_damage=player["max_damage"],
            total_gold=player["total_gold"],
        )

        # 验证数据已更新
        rank_info = leaderboard_manager.get_player_rank(
            player_id=player["player_id"],
            leaderboard_type=LeaderboardType.TIER,
            period=LeaderboardPeriod.WEEKLY,
        )

        assert rank_info is not None

    def test_get_leaderboard(self, leaderboard_manager, sample_players):
        """测试获取排行榜"""
        # 添加所有玩家
        for player in sample_players:
            leaderboard_manager.update_player_data(
                player_id=player["player_id"],
                nickname=player["nickname"],
                avatar=player["avatar"],
                tier=player["tier"],
                stars=player["stars"],
                tier_score=player["tier_score"],
                win_count=player["win_count"],
                total_count=player["total_count"],
                first_place_count=player["first_place_count"],
                max_damage=player["max_damage"],
                total_gold=player["total_gold"],
            )

        # 获取段位排行榜
        data = leaderboard_manager.get_leaderboard(
            leaderboard_type=LeaderboardType.TIER,
            period=LeaderboardPeriod.WEEKLY,
            page=1,
            page_size=10,
        )

        assert data is not None
        assert data.total_count == 10
        assert len(data.entries) == 10

        # 验证排名顺序（段位积分高的在前）
        scores = [e.score for e in data.entries]
        assert scores == sorted(scores, reverse=True)

    def test_leaderboard_pagination(self, leaderboard_manager, sample_players):
        """测试排行榜分页"""
        # 添加玩家
        for player in sample_players:
            leaderboard_manager.update_player_data(
                player_id=player["player_id"],
                nickname=player["nickname"],
                avatar=player["avatar"],
                tier=player["tier"],
                stars=player["stars"],
                tier_score=player["tier_score"],
                win_count=player["win_count"],
                total_count=player["total_count"],
                first_place_count=player["first_place_count"],
                max_damage=player["max_damage"],
                total_gold=player["total_gold"],
            )

        # 获取第一页
        page1 = leaderboard_manager.get_leaderboard(
            leaderboard_type=LeaderboardType.TIER,
            period=LeaderboardPeriod.WEEKLY,
            page=1,
            page_size=5,
        )

        # 获取第二页
        page2 = leaderboard_manager.get_leaderboard(
            leaderboard_type=LeaderboardType.TIER,
            period=LeaderboardPeriod.WEEKLY,
            page=2,
            page_size=5,
        )

        assert len(page1.entries) == 5
        assert len(page2.entries) == 5

        # 验证两页没有重叠
        page1_ids = {e.player_id for e in page1.entries}
        page2_ids = {e.player_id for e in page2.entries}
        assert len(page1_ids & page2_ids) == 0


class TestLeaderboardTypesIntegration:
    """不同排行榜类型集成测试"""

    @pytest.fixture
    def manager_with_data(self):
        """创建带有数据的排行榜管理器"""
        manager = LeaderboardManager()

        # 添加测试玩家
        for i in range(5):
            manager.update_player_data(
                player_id=f"player_{i:03d}",
                nickname=f"玩家{i}",
                avatar="",
                tier="gold",
                stars=i,
                tier_score=1000 + i * 100,
                win_count=10 + i * 2,
                total_count=20 + i * 3,
                first_place_count=i,
                max_damage=1000 + i * 100,
                total_gold=5000 + i * 200,
            )

        return manager

    def test_tier_leaderboard(self, manager_with_data):
        """测试段位排行榜"""
        data = manager_with_data.get_leaderboard(
            leaderboard_type=LeaderboardType.TIER,
            period=LeaderboardPeriod.WEEKLY,
        )

        assert data.leaderboard_type == LeaderboardType.TIER
        assert len(data.entries) == 5

    def test_win_rate_leaderboard(self, manager_with_data):
        """测试胜率排行榜"""
        data = manager_with_data.get_leaderboard(
            leaderboard_type=LeaderboardType.WIN_RATE,
            period=LeaderboardPeriod.WEEKLY,
        )

        assert data.leaderboard_type == LeaderboardType.WIN_RATE

    def test_first_place_leaderboard(self, manager_with_data):
        """测试吃鸡排行榜"""
        data = manager_with_data.get_leaderboard(
            leaderboard_type=LeaderboardType.FIRST_PLACE,
            period=LeaderboardPeriod.WEEKLY,
        )

        assert data.leaderboard_type == LeaderboardType.FIRST_PLACE

        # 验证吃鸡次数排名
        entries = data.entries
        assert entries[0].score >= entries[-1].score

    def test_damage_leaderboard(self, manager_with_data):
        """测试伤害排行榜"""
        data = manager_with_data.get_leaderboard(
            leaderboard_type=LeaderboardType.DAMAGE,
            period=LeaderboardPeriod.WEEKLY,
        )

        assert data.leaderboard_type == LeaderboardType.DAMAGE

    def test_wealth_leaderboard(self, manager_with_data):
        """测试财富排行榜"""
        data = manager_with_data.get_leaderboard(
            leaderboard_type=LeaderboardType.WEALTH,
            period=LeaderboardPeriod.WEEKLY,
        )

        assert data.leaderboard_type == LeaderboardType.WEALTH


class TestLeaderboardPeriodsIntegration:
    """排行榜周期集成测试"""

    @pytest.fixture
    def manager(self):
        """创建排行榜管理器"""
        return LeaderboardManager()

    def test_weekly_leaderboard(self, manager):
        """测试周榜"""
        manager.update_player_data(
            player_id="player_001",
            nickname="玩家1",
            avatar="",
            tier="gold",
            stars=0,
            tier_score=1000,
            win_count=10,
            total_count=20,
            first_place_count=5,
            max_damage=2000,
            total_gold=10000,
        )

        data = manager.get_leaderboard(
            leaderboard_type=LeaderboardType.TIER,
            period=LeaderboardPeriod.WEEKLY,
        )

        assert data.period == LeaderboardPeriod.WEEKLY
        assert data.period_start is not None
        assert data.period_end is not None

    def test_monthly_leaderboard(self, manager):
        """测试月榜"""
        manager.update_player_data(
            player_id="player_001",
            nickname="玩家1",
            avatar="",
            tier="gold",
            stars=0,
            tier_score=1000,
            win_count=10,
            total_count=20,
            first_place_count=5,
            max_damage=2000,
            total_gold=10000,
        )

        data = manager.get_leaderboard(
            leaderboard_type=LeaderboardType.TIER,
            period=LeaderboardPeriod.MONTHLY,
        )

        assert data.period == LeaderboardPeriod.MONTHLY

    def test_season_leaderboard(self, manager):
        """测试赛季榜"""
        manager.update_player_data(
            player_id="player_001",
            nickname="玩家1",
            avatar="",
            tier="gold",
            stars=0,
            tier_score=1000,
            win_count=10,
            total_count=20,
            first_place_count=5,
            max_damage=2000,
            total_gold=10000,
        )

        data = manager.get_leaderboard(
            leaderboard_type=LeaderboardType.TIER,
            period=LeaderboardPeriod.SEASON,
        )

        assert data.period == LeaderboardPeriod.SEASON


class TestLeaderboardRewardsIntegration:
    """排行榜奖励集成测试"""

    @pytest.fixture
    def manager_with_rankings(self):
        """创建带有排名的排行榜"""
        manager = LeaderboardManager()

        # 添加玩家
        for i in range(10):
            manager.update_player_data(
                player_id=f"player_{i:03d}",
                nickname=f"玩家{i}",
                avatar="",
                tier="gold",
                stars=i,
                tier_score=1000 + i * 50,
                win_count=10 + i,
                total_count=20 + i,
                first_place_count=i,
                max_damage=1000 + i * 100,
                total_gold=5000 + i * 100,
            )

        return manager

    def test_get_player_reward(self, manager_with_rankings):
        """测试获取玩家奖励"""
        # 第一名应该有奖励
        reward = manager_with_rankings.get_player_reward(
            player_id="player_009",  # 积分最高
            leaderboard_type=LeaderboardType.TIER,
            period=LeaderboardPeriod.WEEKLY,
        )

        assert reward is not None
        assert reward.gold == 5000
        assert reward.title == "荣耀王者"

    def test_claim_reward(self, manager_with_rankings):
        """测试领取奖励"""
        reward = manager_with_rankings.claim_reward(
            player_id="player_009",
            leaderboard_type=LeaderboardType.TIER,
            period=LeaderboardPeriod.WEEKLY,
        )

        assert reward is not None
        assert reward.gold == 5000

    def test_claim_already_claimed_reward(self, manager_with_rankings):
        """测试重复领取奖励"""
        # 第一次领取
        manager_with_rankings.claim_reward(
            player_id="player_009",
            leaderboard_type=LeaderboardType.TIER,
            period=LeaderboardPeriod.WEEKLY,
        )

        # 第二次领取
        reward = manager_with_rankings.claim_reward(
            player_id="player_009",
            leaderboard_type=LeaderboardType.TIER,
            period=LeaderboardPeriod.WEEKLY,
        )

        assert reward is None

    def test_reward_tiers(self, manager_with_rankings):
        """测试奖励层级"""
        # 第1名
        reward1 = manager_with_rankings.get_player_reward(
            player_id="player_009",
            leaderboard_type=LeaderboardType.TIER,
            period=LeaderboardPeriod.WEEKLY,
        )

        # 第5名
        reward5 = manager_with_rankings.get_player_reward(
            player_id="player_005",
            leaderboard_type=LeaderboardType.TIER,
            period=LeaderboardPeriod.WEEKLY,
        )

        # 第10名
        reward10 = manager_with_rankings.get_player_reward(
            player_id="player_000",
            leaderboard_type=LeaderboardType.TIER,
            period=LeaderboardPeriod.WEEKLY,
        )

        # 第1名奖励应该最好
        if reward1 and reward5:
            assert reward1.gold >= reward5.gold


class TestLeaderboardResetIntegration:
    """排行榜重置集成测试"""

    def test_clear_period(self):
        """测试清除周期数据"""
        manager = LeaderboardManager()

        # 添加数据
        manager.update_player_data(
            player_id="player_001",
            nickname="玩家1",
            avatar="",
            tier="gold",
            stars=0,
            tier_score=1000,
            win_count=10,
            total_count=20,
            first_place_count=5,
            max_damage=2000,
            total_gold=10000,
        )

        # 清除周榜
        manager.clear_period(LeaderboardPeriod.WEEKLY)

        # 验证数据已清除
        data = manager.get_leaderboard(
            leaderboard_type=LeaderboardType.TIER,
            period=LeaderboardPeriod.WEEKLY,
        )

        assert data.total_count == 0

    def test_snapshot_ranks(self):
        """测试排名快照"""
        manager = LeaderboardManager()

        # 添加数据
        for i in range(5):
            manager.update_player_data(
                player_id=f"player_{i:03d}",
                nickname=f"玩家{i}",
                avatar="",
                tier="gold",
                stars=i,
                tier_score=1000 + i * 100,
                win_count=10 + i,
                total_count=20 + i,
                first_place_count=i,
                max_damage=1000 + i * 100,
                total_gold=5000 + i * 100,
            )

        # 快照排名
        manager.snapshot_current_ranks()

        # 更新数据改变排名
        manager.update_player_data(
            player_id="player_000",
            nickname="玩家0",
            avatar="",
            tier="gold",
            stars=0,
            tier_score=2000,  # 提升积分
            win_count=10,
            total_count=20,
            first_place_count=5,
            max_damage=1000,
            total_gold=5000,
        )

        # 验证排名变化（通过历史排名）
        rank_info = manager.get_player_rank(
            player_id="player_000",
            leaderboard_type=LeaderboardType.TIER,
            period=LeaderboardPeriod.WEEKLY,
        )

        # 历史排名应该为正数（排名上升）
        assert rank_info.history_rank >= 0


class TestPlayerRankInfoIntegration:
    """玩家排名信息集成测试"""

    def test_get_player_rank(self):
        """测试获取玩家排名"""
        manager = LeaderboardManager()

        manager.update_player_data(
            player_id="player_001",
            nickname="玩家1",
            avatar="",
            tier="gold",
            stars=3,
            tier_score=1500,
            win_count=15,
            total_count=25,
            first_place_count=5,
            max_damage=2000,
            total_gold=10000,
        )

        rank_info = manager.get_player_rank(
            player_id="player_001",
            leaderboard_type=LeaderboardType.TIER,
            period=LeaderboardPeriod.WEEKLY,
        )

        assert rank_info.player_id == "player_001"
        assert rank_info.rank == 1
        assert rank_info.score == 1500
        assert rank_info.total_players == 1

    def test_get_player_all_ranks(self):
        """测试获取玩家所有排名"""
        manager = LeaderboardManager()

        manager.update_player_data(
            player_id="player_001",
            nickname="玩家1",
            avatar="",
            tier="gold",
            stars=3,
            tier_score=1500,
            win_count=15,
            total_count=25,
            first_place_count=5,
            max_damage=2000,
            total_gold=10000,
        )

        all_ranks = manager.get_player_all_ranks("player_001")

        # 应该有多个排行榜类型和周期
        assert len(all_ranks) > 0

    def test_remove_player(self):
        """测试移除玩家"""
        manager = LeaderboardManager()

        manager.update_player_data(
            player_id="player_001",
            nickname="玩家1",
            avatar="",
            tier="gold",
            stars=3,
            tier_score=1500,
            win_count=15,
            total_count=25,
            first_place_count=5,
            max_damage=2000,
            total_gold=10000,
        )

        # 移除玩家
        manager.remove_player("player_001")

        # 验证已移除
        rank_info = manager.get_player_rank(
            player_id="player_001",
            leaderboard_type=LeaderboardType.TIER,
            period=LeaderboardPeriod.WEEKLY,
        )

        assert rank_info.rank == 0  # 未排名
