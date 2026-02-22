"""
王者之奕 - 排行榜系统测试

本模块测试排行榜系统的核心功能：
- 排行榜管理器
- 排行榜数据更新
- 排行榜查询
- 排行榜奖励
- WebSocket 处理器
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.server.leaderboard import (
    LeaderboardManager,
    LeaderboardType,
    LeaderboardPeriod,
    LeaderboardEntry,
    LeaderboardReward,
    PlayerRankInfo,
    LeaderboardData,
    get_leaderboard_manager,
)


class TestLeaderboardModels:
    """测试排行榜数据模型"""
    
    def test_leaderboard_type_display_name(self):
        """测试排行榜类型显示名称"""
        assert LeaderboardType.TIER.display_name == "段位排行"
        assert LeaderboardType.WIN_RATE.display_name == "胜率排行"
        assert LeaderboardType.FIRST_PLACE.display_name == "吃鸡排行"
        assert LeaderboardType.DAMAGE.display_name == "伤害排行"
        assert LeaderboardType.WEALTH.display_name == "财富排行"
    
    def test_leaderboard_period_display_name(self):
        """测试排行榜周期显示名称"""
        assert LeaderboardPeriod.WEEKLY.display_name == "周榜"
        assert LeaderboardPeriod.MONTHLY.display_name == "月榜"
        assert LeaderboardPeriod.SEASON.display_name == "赛季榜"
    
    def test_leaderboard_reward_contains_rank(self):
        """测试排行榜奖励范围检查"""
        reward = LeaderboardReward(
            rank_start=1,
            rank_end=10,
            gold=1000,
            exp=500,
        )
        
        assert reward.contains_rank(1) is True
        assert reward.contains_rank(5) is True
        assert reward.contains_rank(10) is True
        assert reward.contains_rank(0) is False
        assert reward.contains_rank(11) is False
    
    def test_leaderboard_reward_to_dict(self):
        """测试排行榜奖励序列化"""
        reward = LeaderboardReward(
            rank_start=1,
            rank_end=3,
            gold=5000,
            exp=10000,
            title="荣耀王者",
            avatar_frame="rank_1_frame",
        )
        
        data = reward.to_dict()
        
        assert data["rank_start"] == 1
        assert data["rank_end"] == 3
        assert data["gold"] == 5000
        assert data["exp"] == 10000
        assert data["title"] == "荣耀王者"
        assert data["avatar_frame"] == "rank_1_frame"
    
    def test_leaderboard_reward_from_dict(self):
        """测试排行榜奖励反序列化"""
        data = {
            "rank_start": 4,
            "rank_end": 10,
            "gold": 2000,
            "exp": 4000,
        }
        
        reward = LeaderboardReward.from_dict(data)
        
        assert reward.rank_start == 4
        assert reward.rank_end == 10
        assert reward.gold == 2000
        assert reward.exp == 4000
    
    def test_leaderboard_entry_display_rank(self):
        """测试排行榜条目段位显示"""
        entry = LeaderboardEntry(
            player_id="player_1",
            nickname="测试玩家",
            avatar="avatar.png",
            rank=1,
            score=1000,
            tier="diamond",
            stars=3,
        )
        
        assert entry.display_rank == "钻石 3星"
    
    def test_leaderboard_entry_to_dict(self):
        """测试排行榜条目序列化"""
        entry = LeaderboardEntry(
            player_id="player_1",
            nickname="测试玩家",
            avatar="avatar.png",
            rank=1,
            score=1000,
            tier="gold",
            stars=2,
        )
        
        data = entry.to_dict()
        
        assert data["player_id"] == "player_1"
        assert data["nickname"] == "测试玩家"
        assert data["rank"] == 1
        assert data["score"] == 1000
        assert data["tier"] == "gold"
        assert data["display_rank"] == "黄金 2星"
    
    def test_player_rank_info_is_ranked(self):
        """测试玩家排名是否上榜"""
        ranked_info = PlayerRankInfo(
            player_id="player_1",
            leaderboard_type=LeaderboardType.TIER,
            period=LeaderboardPeriod.WEEKLY,
            rank=10,
        )
        
        unranked_info = PlayerRankInfo(
            player_id="player_2",
            leaderboard_type=LeaderboardType.TIER,
            period=LeaderboardPeriod.WEEKLY,
            rank=0,
        )
        
        assert ranked_info.is_ranked is True
        assert unranked_info.is_ranked is False
    
    def test_player_rank_info_rank_change_text(self):
        """测试排名变化文本"""
        # 新上榜
        info1 = PlayerRankInfo(
            player_id="player_1",
            leaderboard_type=LeaderboardType.TIER,
            period=LeaderboardPeriod.WEEKLY,
            rank=10,
            history_rank=0,
        )
        assert info1.rank_change_text == "新上榜"
        
        # 上升
        info2 = PlayerRankInfo(
            player_id="player_1",
            leaderboard_type=LeaderboardType.TIER,
            period=LeaderboardPeriod.WEEKLY,
            rank=5,
            history_rank=3,
        )
        assert info2.rank_change_text == "↑3"
        
        # 下降
        info3 = PlayerRankInfo(
            player_id="player_1",
            leaderboard_type=LeaderboardType.TIER,
            period=LeaderboardPeriod.WEEKLY,
            rank=15,
            history_rank=-5,
        )
        assert info3.rank_change_text == "↓5"
        
        # 不变
        info4 = PlayerRankInfo(
            player_id="player_1",
            leaderboard_type=LeaderboardType.TIER,
            period=LeaderboardPeriod.WEEKLY,
            rank=10,
            history_rank=0,
        )
        assert info4.rank_change_text == "新上榜"


class TestLeaderboardManager:
    """测试排行榜管理器"""
    
    @pytest.fixture
    def manager(self):
        """创建排行榜管理器"""
        return LeaderboardManager()
    
    def test_manager_initialization(self, manager):
        """测试管理器初始化"""
        assert manager is not None
    
    def test_update_player_data(self, manager):
        """测试更新玩家数据"""
        manager.update_player_data(
            player_id="player_1",
            nickname="测试玩家1",
            avatar="avatar1.png",
            tier="gold",
            stars=2,
            tier_score=1500,
            win_count=50,
            total_count=100,
            first_place_count=10,
            max_damage=5000,
            total_gold=10000,
        )
        
        # 验证段位榜数据
        key = f"{LeaderboardType.TIER.value}_{LeaderboardPeriod.WEEKLY.value}"
        assert key in manager._entries
        assert "player_1" in manager._entries[key]
        
        entry = manager._entries[key]["player_1"]
        assert entry["score"] == 1500
        assert entry["tier"] == "gold"
        assert entry["stars"] == 2
    
    def test_update_multiple_players(self, manager):
        """测试更新多个玩家数据"""
        for i in range(1, 11):
            manager.update_player_data(
                player_id=f"player_{i}",
                nickname=f"玩家{i}",
                avatar=f"avatar{i}.png",
                tier="gold",
                stars=i % 5,
                tier_score=1000 + i * 100,
                win_count=i * 10,
                total_count=i * 20,
                first_place_count=i,
                max_damage=1000 * i,
                total_gold=1000 * i,
            )
        
        # 验证段位榜数据
        key = f"{LeaderboardType.TIER.value}_{LeaderboardPeriod.WEEKLY.value}"
        assert len(manager._entries[key]) == 10
    
    def test_get_leaderboard(self, manager):
        """测试获取排行榜"""
        # 添加测试数据
        for i in range(1, 51):
            manager.update_player_data(
                player_id=f"player_{i}",
                nickname=f"玩家{i}",
                avatar=f"avatar{i}.png",
                tier="gold",
                stars=i % 5,
                tier_score=1000 + i * 10,
                win_count=i,
                total_count=100,
                first_place_count=i // 10,
                max_damage=100 * i,
                total_gold=100 * i,
            )
        
        # 获取第一页
        leaderboard = manager.get_leaderboard(
            leaderboard_type=LeaderboardType.TIER,
            period=LeaderboardPeriod.WEEKLY,
            page=1,
            page_size=10,
        )
        
        assert leaderboard.page == 1
        assert leaderboard.page_size == 10
        assert len(leaderboard.entries) == 10
        assert leaderboard.total_count == 50
        assert leaderboard.entries[0].rank == 1
        assert leaderboard.entries[0].score == 1500  # player_50
    
    def test_get_leaderboard_pagination(self, manager):
        """测试排行榜分页"""
        # 添加测试数据
        for i in range(1, 31):
            manager.update_player_data(
                player_id=f"player_{i}",
                nickname=f"玩家{i}",
                avatar=f"avatar{i}.png",
                tier="gold",
                stars=0,
                tier_score=i * 100,
                win_count=i,
                total_count=100,
                first_place_count=i // 10,
                max_damage=100 * i,
                total_gold=100 * i,
            )
        
        # 获取第二页
        leaderboard = manager.get_leaderboard(
            leaderboard_type=LeaderboardType.TIER,
            period=LeaderboardPeriod.WEEKLY,
            page=2,
            page_size=10,
        )
        
        assert leaderboard.page == 2
        assert len(leaderboard.entries) == 10
        assert leaderboard.entries[0].rank == 11
    
    def test_get_leaderboard_different_types(self, manager):
        """测试不同类型排行榜"""
        # 添加测试数据
        manager.update_player_data(
            player_id="player_1",
            nickname="玩家1",
            avatar="avatar1.png",
            tier="diamond",
            stars=3,
            tier_score=2000,
            win_count=80,
            total_count=100,
            first_place_count=20,
            max_damage=10000,
            total_gold=50000,
        )
        
        # 获取段位榜
        tier_board = manager.get_leaderboard(
            leaderboard_type=LeaderboardType.TIER,
            period=LeaderboardPeriod.WEEKLY,
        )
        assert tier_board.entries[0].score == 2000
        
        # 获取胜率榜
        win_rate_board = manager.get_leaderboard(
            leaderboard_type=LeaderboardType.WIN_RATE,
            period=LeaderboardPeriod.WEEKLY,
        )
        assert win_rate_board.entries[0].score == 80.0  # 80%
        
        # 获取吃鸡榜
        first_place_board = manager.get_leaderboard(
            leaderboard_type=LeaderboardType.FIRST_PLACE,
            period=LeaderboardPeriod.WEEKLY,
        )
        assert first_place_board.entries[0].score == 20
        
        # 获取伤害榜
        damage_board = manager.get_leaderboard(
            leaderboard_type=LeaderboardType.DAMAGE,
            period=LeaderboardPeriod.WEEKLY,
        )
        assert damage_board.entries[0].score == 10000
        
        # 获取财富榜
        wealth_board = manager.get_leaderboard(
            leaderboard_type=LeaderboardType.WEALTH,
            period=LeaderboardPeriod.WEEKLY,
        )
        assert wealth_board.entries[0].score == 50000
    
    def test_get_player_rank(self, manager):
        """测试获取玩家排名"""
        # 添加测试数据
        for i in range(1, 11):
            manager.update_player_data(
                player_id=f"player_{i}",
                nickname=f"玩家{i}",
                avatar=f"avatar{i}.png",
                tier="gold",
                stars=0,
                tier_score=i * 100,
                win_count=i,
                total_count=100,
                first_place_count=i // 2,
                max_damage=100 * i,
                total_gold=100 * i,
            )
        
        # 获取玩家5的排名
        rank_info = manager.get_player_rank(
            player_id="player_5",
            leaderboard_type=LeaderboardType.TIER,
            period=LeaderboardPeriod.WEEKLY,
        )
        
        assert rank_info.is_ranked is True
        assert rank_info.rank == 6  # 500分，排第6
        assert rank_info.total_players == 10
    
    def test_get_player_rank_unranked(self, manager):
        """测试获取未上榜玩家排名"""
        rank_info = manager.get_player_rank(
            player_id="unknown_player",
            leaderboard_type=LeaderboardType.TIER,
            period=LeaderboardPeriod.WEEKLY,
        )
        
        assert rank_info.is_ranked is False
        assert rank_info.rank == 0
    
    def test_get_player_all_ranks(self, manager):
        """测试获取玩家所有排名"""
        manager.update_player_data(
            player_id="player_1",
            nickname="玩家1",
            avatar="avatar1.png",
            tier="gold",
            stars=2,
            tier_score=1500,
            win_count=60,
            total_count=100,
            first_place_count=15,
            max_damage=8000,
            total_gold=30000,
        )
        
        all_ranks = manager.get_player_all_ranks("player_1")
        
        # 应该有5种类型 * 3种周期 = 15个排名信息
        assert len(all_ranks) == 15
    
    def test_get_leaderboard_list(self, manager):
        """测试获取排行榜列表"""
        # 添加测试数据
        for i in range(1, 6):
            manager.update_player_data(
                player_id=f"player_{i}",
                nickname=f"玩家{i}",
                avatar=f"avatar{i}.png",
                tier="gold",
                stars=0,
                tier_score=i * 100,
                win_count=i,
                total_count=100,
                first_place_count=i,
                max_damage=100 * i,
                total_gold=100 * i,
            )
        
        list_data = manager.get_leaderboard_list()
        
        assert "leaderboards" in list_data
        assert len(list_data["leaderboards"]) == 15  # 5 types * 3 periods
    
    def test_set_and_get_rewards(self, manager):
        """测试设置和获取奖励配置"""
        rewards = [
            LeaderboardReward(rank_start=1, rank_end=1, gold=10000, title="冠军"),
            LeaderboardReward(rank_start=2, rank_end=3, gold=5000, title="亚军"),
        ]
        
        manager.set_rewards(
            leaderboard_type=LeaderboardType.TIER,
            period=LeaderboardPeriod.WEEKLY,
            rewards=rewards,
        )
        
        stored_rewards = manager.get_rewards(
            leaderboard_type=LeaderboardType.TIER,
            period=LeaderboardPeriod.WEEKLY,
        )
        
        assert len(stored_rewards) == 2
        assert stored_rewards[0].gold == 10000
        assert stored_rewards[1].gold == 5000
    
    def test_get_player_reward(self, manager):
        """测试获取玩家可领取的奖励"""
        # 添加测试数据
        for i in range(1, 11):
            manager.update_player_data(
                player_id=f"player_{i}",
                nickname=f"玩家{i}",
                avatar=f"avatar{i}.png",
                tier="gold",
                stars=0,
                tier_score=i * 100,
                win_count=i,
                total_count=100,
                first_place_count=i,
                max_damage=100 * i,
                total_gold=100 * i,
            )
        
        # 第1名应该有奖励
        reward = manager.get_player_reward(
            player_id="player_10",  # 最高分
            leaderboard_type=LeaderboardType.TIER,
            period=LeaderboardPeriod.WEEKLY,
        )
        
        assert reward is not None
        assert reward.contains_rank(1)
    
    def test_claim_reward(self, manager):
        """测试领取奖励"""
        # 添加测试数据
        manager.update_player_data(
            player_id="player_1",
            nickname="玩家1",
            avatar="avatar1.png",
            tier="gold",
            stars=0,
            tier_score=2000,
            win_count=100,
            total_count=100,
            first_place_count=50,
            max_damage=10000,
            total_gold=50000,
        )
        
        # 领取奖励
        reward = manager.claim_reward(
            player_id="player_1",
            leaderboard_type=LeaderboardType.TIER,
            period=LeaderboardPeriod.WEEKLY,
        )
        
        assert reward is not None
        
        # 再次领取应该失败
        reward2 = manager.claim_reward(
            player_id="player_1",
            leaderboard_type=LeaderboardType.TIER,
            period=LeaderboardPeriod.WEEKLY,
        )
        
        assert reward2 is None
    
    def test_clear_period(self, manager):
        """测试清除周期数据"""
        # 添加测试数据
        manager.update_player_data(
            player_id="player_1",
            nickname="玩家1",
            avatar="avatar1.png",
            tier="gold",
            stars=0,
            tier_score=1000,
            win_count=50,
            total_count=100,
            first_place_count=10,
            max_damage=5000,
            total_gold=10000,
        )
        
        # 清除周榜
        manager.clear_period(LeaderboardPeriod.WEEKLY)
        
        # 验证数据已清除
        key = f"{LeaderboardType.TIER.value}_{LeaderboardPeriod.WEEKLY.value}"
        assert len(manager._entries[key]) == 0
    
    def test_remove_player(self, manager):
        """测试移除玩家"""
        # 添加测试数据
        manager.update_player_data(
            player_id="player_1",
            nickname="玩家1",
            avatar="avatar1.png",
            tier="gold",
            stars=0,
            tier_score=1000,
            win_count=50,
            total_count=100,
            first_place_count=10,
            max_damage=5000,
            total_gold=10000,
        )
        
        # 移除玩家
        manager.remove_player("player_1")
        
        # 验证玩家已移除
        for lb_type in LeaderboardType:
            for period in LeaderboardPeriod:
                key = f"{lb_type.value}_{period.value}"
                if key in manager._entries:
                    assert "player_1" not in manager._entries[key]
    
    def test_get_period_range(self, manager):
        """测试获取周期时间范围"""
        # 周榜
        start, end = manager._get_period_range(LeaderboardPeriod.WEEKLY)
        assert (end - start).days == 7
        
        # 月榜
        start, end = manager._get_period_range(LeaderboardPeriod.MONTHLY)
        assert start.day == 1
        
        # 赛季榜
        start, end = manager._get_period_range(LeaderboardPeriod.SEASON)
        assert start.day == 1
        assert start.month in [1, 4, 7, 10]


class TestGetLeaderboardManager:
    """测试获取排行榜管理器单例"""
    
    def test_get_singleton(self):
        """测试获取单例"""
        from src.server.leaderboard.manager import _leaderboard_manager
        
        # 清除现有单例
        import src.server.leaderboard.manager as module
        module._leaderboard_manager = None
        
        manager1 = get_leaderboard_manager()
        manager2 = get_leaderboard_manager()
        
        assert manager1 is manager2


class TestLeaderboardData:
    """测试排行榜数据类"""
    
    def test_leaderboard_data_to_dict(self):
        """测试排行榜数据序列化"""
        entries = [
            LeaderboardEntry(
                player_id="player_1",
                nickname="玩家1",
                avatar="avatar1.png",
                rank=1,
                score=2000,
                tier="diamond",
                stars=3,
            ),
            LeaderboardEntry(
                player_id="player_2",
                nickname="玩家2",
                avatar="avatar2.png",
                rank=2,
                score=1800,
                tier="diamond",
                stars=1,
            ),
        ]
        
        data = LeaderboardData(
            leaderboard_type=LeaderboardType.TIER,
            period=LeaderboardPeriod.WEEKLY,
            entries=entries,
            total_count=100,
            page=1,
            page_size=50,
            updated_at=datetime.now(),
        )
        
        result = data.to_dict()
        
        assert result["leaderboard_type"] == "tier"
        assert result["period"] == "weekly"
        assert len(result["entries"]) == 2
        assert result["total_count"] == 100
        assert result["page"] == 1
        assert result["page_size"] == 50
        assert result["total_pages"] == 2
    
    def test_leaderboard_data_from_dict(self):
        """测试排行榜数据反序列化"""
        data = {
            "leaderboard_type": "win_rate",
            "period": "monthly",
            "entries": [
                {
                    "player_id": "player_1",
                    "nickname": "玩家1",
                    "avatar": "avatar1.png",
                    "rank": 1,
                    "score": 95.5,
                    "tier": "gold",
                    "stars": 2,
                }
            ],
            "total_count": 50,
            "page": 2,
            "page_size": 20,
        }
        
        leaderboard = LeaderboardData.from_dict(data)
        
        assert leaderboard.leaderboard_type == LeaderboardType.WIN_RATE
        assert leaderboard.period == LeaderboardPeriod.MONTHLY
        assert len(leaderboard.entries) == 1
        assert leaderboard.page == 2


class TestLeaderboardWinRate:
    """测试胜率计算"""
    
    @pytest.fixture
    def manager(self):
        """创建排行榜管理器"""
        return LeaderboardManager()
    
    def test_win_rate_calculation(self, manager):
        """测试胜率计算"""
        # 80胜20负
        manager.update_player_data(
            player_id="player_1",
            nickname="高胜率玩家",
            avatar="avatar1.png",
            tier="gold",
            stars=2,
            tier_score=1500,
            win_count=80,
            total_count=100,
            first_place_count=20,
            max_damage=5000,
            total_gold=10000,
        )
        
        leaderboard = manager.get_leaderboard(
            leaderboard_type=LeaderboardType.WIN_RATE,
            period=LeaderboardPeriod.WEEKLY,
        )
        
        assert leaderboard.entries[0].score == 80.0
    
    def test_win_rate_zero_games(self, manager):
        """测试零场胜率"""
        manager.update_player_data(
            player_id="player_1",
            nickname="新玩家",
            avatar="avatar1.png",
            tier="bronze",
            stars=0,
            tier_score=0,
            win_count=0,
            total_count=0,
            first_place_count=0,
            max_damage=0,
            total_gold=0,
        )
        
        leaderboard = manager.get_leaderboard(
            leaderboard_type=LeaderboardType.WIN_RATE,
            period=LeaderboardPeriod.WEEKLY,
        )
        
        assert leaderboard.entries[0].score == 0


class TestLeaderboardSorting:
    """测试排行榜排序"""
    
    @pytest.fixture
    def manager(self):
        """创建排行榜管理器"""
        return LeaderboardManager()
    
    def test_sorting_by_score_descending(self, manager):
        """测试按分数降序排序"""
        # 故意添加乱序数据
        scores = [1500, 2000, 1000, 2500, 1800]
        for i, score in enumerate(scores):
            manager.update_player_data(
                player_id=f"player_{i}",
                nickname=f"玩家{i}",
                avatar=f"avatar{i}.png",
                tier="gold",
                stars=0,
                tier_score=score,
                win_count=10,
                total_count=100,
                first_place_count=1,
                max_damage=100,
                total_gold=100,
            )
        
        leaderboard = manager.get_leaderboard(
            leaderboard_type=LeaderboardType.TIER,
            period=LeaderboardPeriod.WEEKLY,
        )
        
        # 验证排序
        assert leaderboard.entries[0].score == 2500
        assert leaderboard.entries[1].score == 2000
        assert leaderboard.entries[2].score == 1800
        assert leaderboard.entries[3].score == 1500
        assert leaderboard.entries[4].score == 1000
