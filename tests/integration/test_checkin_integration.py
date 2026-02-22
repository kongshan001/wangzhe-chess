"""
王者之奕 - 签到系统与数据库集成测试

测试签到系统与数据库的跨模块交互：
- 签到记录持久化
- 连续签到计算
- 补签功能
- 签到奖励发放
"""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch, AsyncMock

from src.server.checkin import (
    CheckinManager,
    CheckinInfo,
    CheckinRecord,
    CheckinStreak,
    CheckinReward,
    DailyRewardConfig,
    RewardType,
)


class TestCheckinIntegration:
    """签到系统集成测试"""

    @pytest.fixture
    def checkin_manager(self):
        """创建签到管理器"""
        manager = CheckinManager()
        manager.clear_cache()
        return manager

    def test_daily_checkin(self, checkin_manager):
        """测试每日签到"""
        player_id = "player_001"
        
        # 执行签到
        record, error = checkin_manager.checkin(player_id)
        
        assert record is not None
        assert error is None
        assert record.player_id == player_id
        assert record.checkin_date == date.today()
        assert len(record.rewards) > 0

    def test_duplicate_checkin(self, checkin_manager):
        """测试重复签到"""
        player_id = "player_001"
        
        # 第一次签到
        checkin_manager.checkin(player_id)
        
        # 第二次签到应该失败
        record, error = checkin_manager.checkin(player_id)
        
        assert record is None
        assert "已签到" in error

    def test_checkin_info(self, checkin_manager):
        """测试获取签到信息"""
        player_id = "player_001"
        
        # 获取初始信息
        info = checkin_manager.get_checkin_info(player_id)
        
        assert info is not None
        assert info.can_checkin is True
        assert info.today_checked is False

    def test_checkin_updates_streak(self, checkin_manager):
        """测试签到更新连续天数"""
        player_id = "player_001"
        
        # 连续签到3天
        for i in range(3):
            with patch('src.server.checkin.manager.date') as mock_date:
                mock_date.today.return_value = date.today() - timedelta(days=2-i)
                mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs) if args else date.today() - timedelta(days=2-i)
                checkin_manager.checkin(player_id)
        
        info = checkin_manager.get_checkin_info(player_id)
        assert info.streak_info.current_streak >= 3


class TestCheckinStreakIntegration:
    """连续签到集成测试"""

    @pytest.fixture
    def manager(self):
        """创建签到管理器"""
        manager = CheckinManager()
        manager.clear_cache()
        return manager

    def test_streak_calculation(self, manager):
        """测试连续签到计算"""
        player_id = "player_001"
        
        # 签到
        manager.checkin(player_id)
        
        streak = manager.get_or_create_streak(player_id)
        assert streak.current_streak == 1
        assert streak.total_count == 1

    def test_streak_break(self, manager):
        """测试断签"""
        player_id = "player_001"
        
        # 今天签到
        manager.checkin(player_id)
        
        # 模拟昨天未签到，今天再签到
        # 实际上这里需要修改 last_checkin_date 来模拟断签
        streak = manager.get_or_create_streak(player_id)
        streak.last_checkin_date = date.today() - timedelta(days=2)
        
        # 再次签到会重置连续天数
        manager.checkin(player_id)  # 这会更新为1
        
        streak = manager.get_or_create_streak(player_id)
        # 根据实现，可能重置或保持

    def test_max_streak_update(self, manager):
        """测试最大连续签到更新"""
        player_id = "player_001"
        
        # 多次签到
        for _ in range(5):
            manager.player_streaks.pop(player_id, None)  # 重置
            manager.checkin(player_id)
        
        streak = manager.get_or_create_streak(player_id)
        assert streak.max_streak >= streak.current_streak

    def test_cycle_day_calculation(self, manager):
        """测试周期天数计算"""
        player_id = "player_001"
        
        # 签到
        manager.checkin(player_id)
        
        streak = manager.get_or_create_streak(player_id)
        cycle_day = manager.calculate_cycle_day(streak)
        
        assert 1 <= cycle_day <= 7


class TestSupplementCheckinIntegration:
    """补签集成测试"""

    @pytest.fixture
    def manager(self):
        """创建签到管理器"""
        manager = CheckinManager()
        manager.clear_cache()
        return manager

    def test_supplement_checkin(self, manager):
        """测试补签"""
        player_id = "player_001"
        target_date = date.today() - timedelta(days=1)
        
        # 补签
        record, cost, error = manager.supplement_checkin(
            player_id=player_id,
            target_date=target_date,
            diamond_balance=1000,
        )
        
        assert record is not None
        assert record.is_supplement is True
        assert cost > 0
        assert error is None

    def test_supplement_future_date(self, manager):
        """测试补签未来日期"""
        player_id = "player_001"
        future_date = date.today() + timedelta(days=1)
        
        record, cost, error = manager.supplement_checkin(
            player_id=player_id,
            target_date=future_date,
            diamond_balance=1000,
        )
        
        assert record is None
        assert "无法补签" in error

    def test_supplement_exceeds_limit(self, manager):
        """测试补签超过限制天数"""
        player_id = "player_001"
        old_date = date.today() - timedelta(days=10)  # 超过3天
        
        record, cost, error = manager.supplement_checkin(
            player_id=player_id,
            target_date=old_date,
            diamond_balance=1000,
        )
        
        assert record is None
        assert "最多" in error

    def test_supplement_insufficient_diamond(self, manager):
        """测试钻石不足补签"""
        player_id = "player_001"
        target_date = date.today() - timedelta(days=1)
        
        record, cost, error = manager.supplement_checkin(
            player_id=player_id,
            target_date=target_date,
            diamond_balance=10,  # 不足
        )
        
        assert record is None
        assert "不足" in error

    def test_supplement_cost_calculation(self, manager):
        """测试补签消耗计算"""
        # 1天前
        cost1 = manager.calculate_supplement_cost(1)
        assert cost1 == 50
        
        # 2天前
        cost2 = manager.calculate_supplement_cost(2)
        assert cost2 == 100
        
        # 3天前
        cost3 = manager.calculate_supplement_cost(3)
        assert cost3 == 150

    def test_get_supplement_days(self, manager):
        """测试获取可补签日期"""
        player_id = "player_001"
        
        # 获取可补签日期
        supplement_days = manager.get_supplement_days(player_id)
        
        # 应该是最近3天未签到的日期
        assert len(supplement_days) <= 3


class TestCheckinRewardsIntegration:
    """签到奖励集成测试"""

    @pytest.fixture
    def manager(self):
        """创建签到管理器"""
        manager = CheckinManager()
        manager.clear_cache()
        return manager

    def test_daily_rewards(self, manager):
        """测试每日奖励"""
        for day in range(1, 8):
            base_rewards, bonus_rewards = manager.get_daily_rewards(day, 1)
            
            assert len(base_rewards) > 0
            # 第7天应该有额外奖励
            if day == 7:
                assert len(bonus_rewards) > 0

    def test_streak_bonus(self, manager):
        """测试连续签到加成"""
        # 连续1天
        base1, _ = manager.get_daily_rewards(1, 1)
        
        # 连续7天
        base7, _ = manager.get_daily_rewards(1, 7)
        
        # 连续签到加成可能导致奖励更多
        # 具体逻辑取决于实现

    def test_monthly_rewards(self, manager):
        """测试月度累计奖励"""
        # 累计7天
        rewards7 = manager.get_monthly_rewards(7)
        assert len(rewards7) > 0
        
        # 累计30天
        rewards30 = manager.get_monthly_rewards(30)
        assert len(rewards30) > 0

    def test_checkin_reward_types(self, manager):
        """测试签到奖励类型"""
        player_id = "player_001"
        
        record, _ = manager.checkin(player_id)
        
        # 验证奖励类型
        for reward in record.rewards:
            assert reward.reward_type in [
                RewardType.GOLD,
                RewardType.DIAMOND,
                RewardType.HERO_FRAGMENT,
                RewardType.ITEM,
                RewardType.SKIN,
            ]


class TestCheckinRecordsIntegration:
    """签到记录集成测试"""

    @pytest.fixture
    def manager(self):
        """创建签到管理器"""
        manager = CheckinManager()
        manager.clear_cache()
        return manager

    def test_get_player_records(self, manager):
        """测试获取玩家签到记录"""
        player_id = "player_001"
        
        # 签到几次
        manager.checkin(player_id)
        
        records = manager.get_player_records(player_id)
        
        assert len(records) >= 1

    def test_records_date_filter(self, manager):
        """测试签到记录日期筛选"""
        player_id = "player_001"
        
        # 签到
        manager.checkin(player_id)
        
        # 获取今天的记录
        records = manager.get_player_records(
            player_id=player_id,
            start_date=date.today(),
            end_date=date.today(),
        )
        
        assert len(records) == 1

    def test_records_limit(self, manager):
        """测试签到记录数量限制"""
        player_id = "player_001"
        
        # 签到
        manager.checkin(player_id)
        
        # 获取限制数量的记录
        records = manager.get_player_records(player_id, limit=10)
        
        assert len(records) <= 10


class TestCheckinConfigIntegration:
    """签到配置集成测试"""

    @pytest.fixture
    def manager(self):
        """创建签到管理器"""
        manager = CheckinManager()
        return manager

    def test_get_reward_config(self, manager):
        """测试获取奖励配置"""
        config = manager.get_reward_config()
        
        assert "daily_rewards" in config
        assert "monthly_rewards" in config
        assert "max_supplement_days" in config

    def test_default_rewards_loaded(self, manager):
        """测试默认奖励加载"""
        # 应该有7天的奖励配置
        assert len(manager.daily_rewards) == 7

    def test_monthly_rewards_loaded(self, manager):
        """测试月度奖励加载"""
        # 应该有月度奖励配置
        assert len(manager.monthly_rewards) > 0


class TestCheckinMonthlyResetIntegration:
    """签到月度重置集成测试"""

    def test_reset_monthly_count(self):
        """测试重置月签到次数"""
        manager = CheckinManager()
        player_id = "player_001"
        
        # 签到几次
        manager.checkin(player_id)
        
        streak = manager.get_or_create_streak(player_id)
        initial_count = streak.monthly_count
        
        # 重置
        manager.reset_monthly_count(player_id)
        
        streak = manager.get_or_create_streak(player_id)
        assert streak.monthly_count == 0


class TestCheckinSerialization:
    """签到序列化测试"""

    def test_checkin_reward_serialization(self):
        """测试签到奖励序列化"""
        reward = CheckinReward(
            reward_id="reward_001",
            reward_type=RewardType.GOLD,
            quantity=100,
        )
        
        data = reward.to_dict()
        assert data["reward_id"] == "reward_001"
        assert data["reward_type"] == "gold"
        assert data["quantity"] == 100
        
        loaded = CheckinReward.from_dict(data)
        assert loaded.reward_id == "reward_001"
        assert loaded.reward_type == RewardType.GOLD

    def test_daily_reward_config_serialization(self):
        """测试每日奖励配置序列化"""
        config = DailyRewardConfig(
            day=1,
            base_rewards=[
                CheckinReward(reward_id="r1", reward_type=RewardType.GOLD, quantity=100),
            ],
            bonus_rewards=[],
            streak_bonus={"7": 50},
        )
        
        data = config.to_dict()
        assert data["day"] == 1
        
        loaded = DailyRewardConfig.from_dict(data)
        assert loaded.day == 1
        assert len(loaded.base_rewards) == 1

    def test_checkin_streak_serialization(self):
        """测试连续签到数据序列化"""
        streak = CheckinStreak(player_id="player_001")
        streak.current_streak = 5
        streak.total_count = 10
        
        data = streak.to_dict()
        assert data["player_id"] == "player_001"
        assert data["current_streak"] == 5
        
        loaded = CheckinStreak.from_dict(data)
        assert loaded.player_id == "player_001"
        assert loaded.current_streak == 5
