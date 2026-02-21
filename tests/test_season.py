"""
王者之奕 - 赛季系统测试

测试赛季系统的核心功能：
- Season 数据类
- SeasonReward 数据类
- PlayerSeasonData 数据类
- SeasonManager 管理器
"""

import pytest
from datetime import datetime, timedelta

from src.server.season.models import (
    Season,
    SeasonReward,
    SeasonStatus,
    PlayerSeasonData,
    Tier,
)
from src.server.season.manager import SeasonManager


# ============================================================================
# Tier 测试
# ============================================================================

class TestTier:
    """段位枚举测试"""

    def test_tier_values(self):
        """测试段位值"""
        assert Tier.BRONZE.value == 1
        assert Tier.SILVER.value == 2
        assert Tier.GOLD.value == 3
        assert Tier.PLATINUM.value == 4
        assert Tier.DIAMOND.value == 5
        assert Tier.MASTER.value == 6
        assert Tier.GRANDMASTER.value == 7
        assert Tier.KING.value == 8

    def test_tier_from_name(self):
        """测试从名称获取段位"""
        assert Tier.from_name("bronze") == Tier.BRONZE
        assert Tier.from_name("GOLD") == Tier.GOLD
        assert Tier.from_name("Diamond") == Tier.DIAMOND
        assert Tier.from_name("king") == Tier.KING
        assert Tier.from_name("unknown") == Tier.BRONZE

    def test_tier_display_name(self):
        """测试段位显示名称"""
        assert Tier.BRONZE.display_name == "青铜"
        assert Tier.GOLD.display_name == "黄金"
        assert Tier.KING.display_name == "王者"

    def test_tier_comparison(self):
        """测试段位比较"""
        assert Tier.GOLD > Tier.SILVER
        assert Tier.KING > Tier.GRANDMASTER
        assert Tier.BRONZE < Tier.DIAMOND


# ============================================================================
# SeasonReward 测试
# ============================================================================

class TestSeasonReward:
    """赛季奖励测试"""

    def test_reward_creation(self):
        """测试奖励创建"""
        reward = SeasonReward(
            tier=Tier.GOLD,
            gold=1200,
            exp=2000,
            title="黄金战士",
        )
        assert reward.tier == Tier.GOLD
        assert reward.gold == 1200
        assert reward.exp == 2000
        assert reward.title == "黄金战士"
        assert reward.avatar_frame is None
        assert reward.skin is None

    def test_reward_serialization(self):
        """测试奖励序列化"""
        reward = SeasonReward(
            tier=Tier.DIAMOND,
            gold=2500,
            exp=4500,
            avatar_frame="diamond_frame",
            skin="season_skin",
            title="钻石精英",
            items=[{"item_id": "chest", "quantity": 1}],
        )
        
        data = reward.to_dict()
        assert data["tier"] == 5
        assert data["tier_name"] == "钻石"
        assert data["gold"] == 2500
        assert data["avatar_frame"] == "diamond_frame"
        
        restored = SeasonReward.from_dict(data)
        assert restored.tier == Tier.DIAMOND
        assert restored.gold == reward.gold


# ============================================================================
# Season 测试
# ============================================================================

class TestSeason:
    """赛季测试"""

    def test_season_creation(self):
        """测试赛季创建"""
        now = datetime.now()
        season = Season(
            season_id="S1",
            name="第一赛季",
            start_time=now,
            end_time=now + timedelta(days=28),
        )
        assert season.season_id == "S1"
        assert season.name == "第一赛季"
        assert season.is_active is True
        assert season.duration_days == 28

    def test_season_status_active(self):
        """测试赛季状态 - 进行中"""
        season = Season(
            season_id="S1",
            name="第一赛季",
            start_time=datetime.now() - timedelta(days=10),
            end_time=datetime.now() + timedelta(days=18),
        )
        assert season.status == SeasonStatus.ACTIVE
        # days_remaining 可能有1天的误差
        assert 17 <= season.days_remaining <= 18

    def test_season_status_ending(self):
        """测试赛季状态 - 即将结束"""
        season = Season(
            season_id="S1",
            name="第一赛季",
            start_time=datetime.now() - timedelta(days=26),
            end_time=datetime.now() + timedelta(days=2),
        )
        assert season.status == SeasonStatus.ENDING

    def test_season_status_ended(self):
        """测试赛季状态 - 已结束"""
        season = Season(
            season_id="S1",
            name="第一赛季",
            start_time=datetime.now() - timedelta(days=30),
            end_time=datetime.now() - timedelta(days=2),
        )
        assert season.status == SeasonStatus.ENDED
        assert season.days_remaining == 0

    def test_season_status_upcoming(self):
        """测试赛季状态 - 即将开始"""
        season = Season(
            season_id="S2",
            name="第二赛季",
            start_time=datetime.now() + timedelta(days=5),
            end_time=datetime.now() + timedelta(days=33),
        )
        assert season.status == SeasonStatus.UPCOMING

    def test_season_progress(self):
        """测试赛季进度"""
        season = Season(
            season_id="S1",
            name="第一赛季",
            start_time=datetime.now() - timedelta(days=14),
            end_time=datetime.now() + timedelta(days=14),
        )
        # 进度应约为50%
        assert 49 <= season.progress * 100 <= 51

    def test_season_get_reward(self):
        """测试获取段位奖励"""
        rewards = {
            Tier.GOLD.value: SeasonReward(tier=Tier.GOLD, gold=1200),
            Tier.DIAMOND.value: SeasonReward(tier=Tier.DIAMOND, gold=2500),
        }
        season = Season(
            season_id="S1",
            name="第一赛季",
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(days=28),
            rewards=rewards,
        )
        
        gold_reward = season.get_reward_for_tier(Tier.GOLD)
        assert gold_reward is not None
        assert gold_reward.gold == 1200
        
        bronze_reward = season.get_reward_for_tier(Tier.BRONZE)
        assert bronze_reward is None

    def test_season_serialization(self):
        """测试赛季序列化"""
        season = Season(
            season_id="S1",
            name="第一赛季",
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(days=28),
            description="新赛季测试",
            rewards={
                Tier.GOLD.value: SeasonReward(tier=Tier.GOLD, gold=1200),
            },
        )
        
        data = season.to_dict()
        assert data["season_id"] == "S1"
        assert data["name"] == "第一赛季"
        assert data["description"] == "新赛季测试"
        assert "rewards" in data
        
        restored = Season.from_dict(data)
        assert restored.season_id == season.season_id
        assert restored.name == season.name


# ============================================================================
# PlayerSeasonData 测试
# ============================================================================

class TestPlayerSeasonData:
    """玩家赛季数据测试"""

    def test_player_season_data_creation(self):
        """测试玩家赛季数据创建"""
        data = PlayerSeasonData(
            player_id="player_001",
            season_id="S1",
        )
        assert data.player_id == "player_001"
        assert data.season_id == "S1"
        assert data.highest_tier == Tier.BRONZE
        assert data.final_tier == Tier.BRONZE
        assert data.total_games == 0
        assert data.pass_level == 1

    def test_add_game_result(self):
        """测试添加对局结果"""
        data = PlayerSeasonData(
            player_id="player_001",
            season_id="S1",
        )
        
        # 添加第一名
        data.add_game_result(1)
        assert data.total_games == 1
        assert data.total_wins == 1
        assert data.first_place_count == 1
        assert data.total_top4 == 1
        
        # 添加第三名
        data.add_game_result(3)
        assert data.total_games == 2
        assert data.total_wins == 1
        assert data.total_top4 == 2
        
        # 添加第八名
        data.add_game_result(8)
        assert data.total_games == 3
        assert data.total_top4 == 2

    def test_win_rate(self):
        """测试胜率计算"""
        data = PlayerSeasonData(
            player_id="player_001",
            season_id="S1",
        )
        
        assert data.win_rate == 0.0
        
        data.add_game_result(1)
        data.add_game_result(1)
        data.add_game_result(2)
        data.add_game_result(3)
        
        assert data.win_rate == 50.0
        assert data.top4_rate == 100.0

    def test_pass_exp(self):
        """测试通行证经验"""
        data = PlayerSeasonData(
            player_id="player_001",
            season_id="S1",
        )
        
        new_level = data.add_pass_exp(50)
        assert data.pass_exp == 50
        assert new_level == 1
        assert data.pass_level == 1
        
        new_level = data.add_pass_exp(60)
        assert data.pass_exp == 110
        assert new_level == 2
        assert data.pass_level == 2

    def test_update_tier(self):
        """测试更新段位"""
        data = PlayerSeasonData(
            player_id="player_001",
            season_id="S1",
        )
        
        data.update_tier(Tier.GOLD)
        assert data.final_tier == Tier.GOLD
        assert data.highest_tier == Tier.GOLD
        
        data.update_tier(Tier.SILVER)
        assert data.final_tier == Tier.SILVER
        assert data.highest_tier == Tier.GOLD  # 最高段位保持不变

    def test_placement_matches(self):
        """测试定位赛"""
        data = PlayerSeasonData(
            player_id="player_001",
            season_id="S1",
        )
        
        for i in range(5):
            data.record_placement_match(won=True)
        
        assert data.placement_matches == 5
        assert data.placement_wins == 5
        assert data.placement_done is False
        
        for i in range(5):
            data.record_placement_match(won=False)
        
        assert data.placement_matches == 10
        assert data.placement_wins == 5
        assert data.placement_done is True

    def test_player_season_data_serialization(self):
        """测试玩家赛季数据序列化"""
        data = PlayerSeasonData(
            player_id="player_001",
            season_id="S1",
            highest_tier=Tier.DIAMOND,
            final_tier=Tier.GOLD,
            total_games=100,
            total_wins=25,
            pass_level=10,
            pass_premium=True,
        )
        
        serialized = data.to_dict()
        assert serialized["player_id"] == "player_001"
        assert serialized["highest_tier"] == 5
        assert serialized["highest_tier_name"] == "钻石"
        assert serialized["final_tier"] == 3
        assert serialized["pass_premium"] is True
        
        restored = PlayerSeasonData.from_dict(serialized)
        assert restored.player_id == data.player_id
        assert restored.highest_tier == data.highest_tier
        assert restored.final_tier == data.final_tier


# ============================================================================
# SeasonManager 测试
# ============================================================================

class TestSeasonManager:
    """赛季管理器测试"""

    @pytest.fixture
    def manager(self):
        """创建管理器实例"""
        return SeasonManager()

    def test_manager_initialization(self, manager):
        """测试管理器初始化"""
        assert manager is not None
        assert manager.current_season_id is None

    def test_create_season(self, manager):
        """测试创建赛季"""
        season = manager.create_season(
            season_id="S1",
            name="第一赛季",
            duration_days=28,
        )
        
        assert season is not None
        assert season.season_id == "S1"
        assert season.name == "第一赛季"
        assert manager.current_season_id == "S1"

    def test_get_current_season(self, manager):
        """测试获取当前赛季"""
        manager.create_season("S1", "第一赛季")
        
        current = manager.get_current_season()
        assert current is not None
        assert current.season_id == "S1"

    def test_end_season(self, manager):
        """测试结束赛季"""
        manager.create_season("S1", "第一赛季")
        
        result = manager.end_season("S1")
        assert result is True
        assert manager.current_season_id is None

    def test_soft_reset_tier(self, manager):
        """测试段位软重置"""
        # 青铜保持青铜
        assert manager.soft_reset_tier(Tier.BRONZE) == Tier.BRONZE
        
        # 白银软重置: ceil((2+1)/2)=ceil(1.5)=2 -> 白银
        assert manager.soft_reset_tier(Tier.SILVER) == Tier.SILVER
        
        # 黄金软重置: ceil((3+1)/2)=ceil(2)=2 -> 白银
        assert manager.soft_reset_tier(Tier.GOLD) == Tier.SILVER
        
        # 王者软重置: ceil((8+1)/2)=ceil(4.5)=5 -> 钻石
        assert manager.soft_reset_tier(Tier.KING) == Tier.DIAMOND

    def test_calculate_season_reward(self, manager):
        """测试计算赛季奖励"""
        manager.create_season("S1", "第一赛季")
        
        # 创建玩家赛季数据
        player_data = manager.get_or_create_player_season_data("player_001")
        player_data.update_tier(Tier.GOLD)
        
        reward = manager.calculate_season_reward("player_001")
        assert reward is not None
        assert reward.tier == Tier.GOLD
        assert reward.gold == 1200

    def test_record_game_result(self, manager):
        """测试记录对局结果"""
        manager.create_season("S1", "第一赛季")
        
        data = manager.record_game_result("player_001", rank=1)
        assert data.total_games == 1
        assert data.total_wins == 1
        
        data = manager.record_game_result("player_001", rank=3)
        assert data.total_games == 2
        assert data.total_top4 == 2

    def test_start_new_season_for_player(self, manager):
        """测试玩家开始新赛季"""
        # 第一赛季
        manager.create_season("S1", "第一赛季")
        player_data = manager.get_or_create_player_season_data("player_001")
        player_data.update_tier(Tier.DIAMOND)
        
        # 创建第二赛季
        manager.create_season("S2", "第二赛季")
        new_data = manager.start_new_season_for_player("player_001", "S2")
        
        # 钻石软重置后应为黄金 (5+1)/2 = 3
        assert new_data.final_tier == Tier.GOLD
        assert new_data.season_id == "S2"

    def test_get_season_ranking(self, manager):
        """测试赛季排行榜"""
        manager.create_season("S1", "第一赛季")
        
        # 创建多个玩家数据
        for i in range(5):
            data = manager.get_or_create_player_season_data(f"player_{i}")
            data.update_tier(Tier(i + 2))  # 白银到大师
            data.add_game_result(1)
        
        ranking = manager.get_season_ranking(limit=10)
        assert len(ranking) == 5
        # 最高段位应该在第一位 (player_4 是大师=6)
        assert ranking[0]["tier"] == Tier.MASTER.value

    def test_add_pass_exp(self, manager):
        """测试添加通行证经验"""
        manager.create_season("S1", "第一赛季")
        
        new_level = manager.add_pass_exp("player_001", 150)
        assert new_level == 2
        
        player_data = manager.get_player_season_data("player_001")
        assert player_data.pass_level == 2
        assert player_data.pass_exp == 150


# ============================================================================
# 边界条件测试
# ============================================================================

class TestBoundaryConditions:
    """边界条件测试"""

    def test_zero_games_stats(self):
        """测试零对局时的统计"""
        data = PlayerSeasonData(
            player_id="player_001",
            season_id="S1",
        )
        
        assert data.win_rate == 0.0
        assert data.top4_rate == 0.0
        assert data.avg_rank == 0.0

    def test_tier_boundary(self):
        """测试段位边界值"""
        # 最低和最高段位
        assert Tier.BRONZE.value == 1
        assert Tier.KING.value == 8

    def test_season_zero_duration(self):
        """测试零持续时间赛季"""
        now = datetime.now()
        season = Season(
            season_id="S1",
            name="测试赛季",
            start_time=now,
            end_time=now,
        )
        assert season.duration_days == 0
        # 零持续时间应返回1.0表示已完成
        assert season.progress == 1.0

    def test_manager_empty_ranking(self):
        """测试空排行榜"""
        manager = SeasonManager()
        manager.create_season("S1", "第一赛季")
        
        ranking = manager.get_season_ranking()
        assert ranking == []

    def test_nonexistent_season(self):
        """测试不存在的赛季"""
        manager = SeasonManager()
        
        season = manager.get_season("NONEXISTENT")
        assert season is None
        
        reward = manager.calculate_season_reward("player_001", "NONEXISTENT")
        assert reward is None
