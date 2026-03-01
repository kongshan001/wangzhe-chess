"""
王者之奕 - 签到系统测试

测试签到系统的核心功能：
- 每日签到
- 连续签到计算
- 签到奖励获取
- 补签功能
- 签到记录查询
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

import pytest

from src.server.checkin.manager import CheckinManager
from src.server.checkin.models import (
    CheckinInfo,
    CheckinRecord,
    CheckinReward,
    CheckinStreak,
    RewardType,
)


class TestCheckinModels:
    """测试签到数据模型"""

    def test_checkin_reward_creation(self):
        """测试签到奖励创建"""
        reward = CheckinReward(
            reward_id="test_reward",
            reward_type=RewardType.GOLD,
            quantity=100,
        )

        assert reward.reward_id == "test_reward"
        assert reward.reward_type == RewardType.GOLD
        assert reward.quantity == 100

    def test_checkin_reward_to_dict(self):
        """测试签到奖励序列化"""
        reward = CheckinReward(
            reward_id="test_reward",
            reward_type=RewardType.GOLD,
            quantity=100,
            extra_data={"bonus": 10},
        )

        data = reward.to_dict()
        assert data["reward_id"] == "test_reward"
        assert data["reward_type"] == "gold"
        assert data["quantity"] == 100
        assert data["extra_data"]["bonus"] == 10

    def test_checkin_reward_from_dict(self):
        """测试签到奖励反序列化"""
        data = {
            "reward_id": "test_reward",
            "reward_type": "diamond",
            "quantity": 50,
            "item_id": "test_item",
        }

        reward = CheckinReward.from_dict(data)
        assert reward.reward_id == "test_reward"
        assert reward.reward_type == RewardType.DIAMOND
        assert reward.quantity == 50
        assert reward.item_id == "test_item"

    def test_checkin_streak_update(self):
        """测试连续签到更新"""
        streak = CheckinStreak(player_id="test_player")

        # 首次签到
        today = date.today()
        is_continuous = streak.update_streak(today)

        assert streak.current_streak == 1
        assert streak.total_count == 1
        assert streak.last_checkin_date == today
        assert is_continuous == False  # 首次签到不算连续

    def test_checkin_streak_continuous(self):
        """测试连续签到天数累加"""
        streak = CheckinStreak(player_id="test_player")
        today = date.today()

        # 第一天签到
        streak.update_streak(today)
        assert streak.current_streak == 1

        # 第二天签到
        tomorrow = today + timedelta(days=1)
        is_continuous = streak.update_streak(tomorrow)

        assert streak.current_streak == 2
        assert is_continuous == True

    def test_checkin_streak_broken(self):
        """测试签到中断后重新开始"""
        streak = CheckinStreak(player_id="test_player")
        today = date.today()

        # 第一天签到
        streak.update_streak(today)
        assert streak.current_streak == 1

        # 第三天签到（跳过一天）
        day3 = today + timedelta(days=2)
        streak.update_streak(day3)

        assert streak.current_streak == 1  # 重新开始
        assert streak.cycle_start_date == day3

    def test_checkin_record_creation(self):
        """测试签到记录创建"""
        today = date.today()
        now = datetime.now()

        record = CheckinRecord(
            record_id="test_record",
            player_id="test_player",
            checkin_date=today,
            checkin_time=now,
            day_in_cycle=1,
            streak_days=1,
            rewards=[
                CheckinReward(reward_id="gold", reward_type=RewardType.GOLD, quantity=100),
            ],
        )

        assert record.record_id == "test_record"
        assert record.checkin_date == today
        assert record.day_in_cycle == 1
        assert len(record.rewards) == 1
        assert record.is_supplement == False


class TestCheckinManager:
    """测试签到管理器"""

    @pytest.fixture
    def manager(self):
        """创建签到管理器"""
        return CheckinManager()

    def test_manager_initialization(self, manager):
        """测试管理器初始化"""
        assert len(manager.daily_rewards) == 7
        assert len(manager.monthly_rewards) == 4

    def test_get_or_create_streak(self, manager):
        """测试获取或创建连续签到数据"""
        streak1 = manager.get_or_create_streak("player1")
        assert streak1.player_id == "player1"
        assert streak1.current_streak == 0

        # 再次获取应该是同一个对象
        streak2 = manager.get_or_create_streak("player1")
        assert streak1 is streak2

    def test_has_checked_today(self, manager):
        """测试检查今日是否已签到"""
        player_id = "test_player"

        # 未签到
        assert manager.has_checked_today(player_id) == False

        # 执行签到
        manager.checkin(player_id)

        # 已签到
        assert manager.has_checked_today(player_id) == True

    def test_daily_checkin(self, manager):
        """测试每日签到"""
        player_id = "test_player"

        record, error = manager.checkin(player_id)

        assert record is not None
        assert error is None
        assert record.player_id == player_id
        assert len(record.rewards) > 0

    def test_duplicate_checkin(self, manager):
        """测试重复签到"""
        player_id = "test_player"

        # 第一次签到
        record1, error1 = manager.checkin(player_id)
        assert record1 is not None
        assert error1 is None

        # 重复签到
        record2, error2 = manager.checkin(player_id)
        assert record2 is None
        assert error2 == "今日已签到"

    def test_calculate_cycle_day(self, manager):
        """测试计算周期天数"""
        streak = CheckinStreak(player_id="test_player")
        today = date.today()

        # 首次签到，周期第1天
        streak.cycle_start_date = today
        assert manager.calculate_cycle_day(streak) == 1

        # 第3天
        streak.cycle_start_date = today - timedelta(days=2)
        assert manager.calculate_cycle_day(streak) == 3

        # 第8天（新周期第1天）
        streak.cycle_start_date = today - timedelta(days=7)
        assert manager.calculate_cycle_day(streak) == 1

    def test_calculate_supplement_cost(self, manager):
        """测试计算补签消耗"""
        assert manager.calculate_supplement_cost(1) == 50
        assert manager.calculate_supplement_cost(2) == 100
        assert manager.calculate_supplement_cost(3) == 150
        assert manager.calculate_supplement_cost(4) == 0  # 超出范围

    def test_get_supplement_days(self, manager):
        """测试获取可补签日期"""
        player_id = "test_player"

        # 先签到一天，确保有可补签的日期
        manager.checkin(player_id)

        supplement_days = manager.get_supplement_days(player_id)

        # 应该返回3个可补签日期（前3天）
        assert len(supplement_days) <= 3

        # 如果今天刚签到，应该有3天可补签
        if manager.has_checked_today(player_id):
            today = date.today()
            expected = [
                today - timedelta(days=1),
                today - timedelta(days=2),
                today - timedelta(days=3),
            ]
            assert supplement_days == expected

    def test_supplement_checkin_success(self, manager):
        """测试补签成功"""
        player_id = "test_player"
        target_date = date.today() - timedelta(days=1)

        # 钻石余额充足
        record, cost, error = manager.supplement_checkin(
            player_id, target_date, diamond_balance=100
        )

        assert record is not None
        assert cost == 50  # 1天前补签消耗50钻石
        assert error is None
        assert record.is_supplement == True
        assert record.supplement_cost == 50

    def test_supplement_checkin_insufficient_diamond(self, manager):
        """测试钻石不足补签失败"""
        player_id = "test_player2"
        target_date = date.today() - timedelta(days=1)

        # 钻石余额不足
        record, cost, error = manager.supplement_checkin(player_id, target_date, diamond_balance=10)

        assert record is None
        assert "钻石不足" in error

    def test_supplement_checkin_already_checked(self, manager):
        """测试已签到日期补签失败"""
        player_id = "test_player3"

        # 先签到
        manager.checkin(player_id)

        # 尝试补签今天
        record, cost, error = manager.supplement_checkin(
            player_id, date.today(), diamond_balance=100
        )

        assert record is None
        assert "未来的日期" in error or "无法补签" in error

    def test_supplement_checkin_too_far(self, manager):
        """测试补签日期太远"""
        player_id = "test_player4"
        target_date = date.today() - timedelta(days=5)

        record, cost, error = manager.supplement_checkin(
            player_id, target_date, diamond_balance=1000
        )

        assert record is None
        assert "最多只能补签3天" in error

    def test_get_checkin_info(self, manager):
        """测试获取签到信息"""
        player_id = "test_player"

        info = manager.get_checkin_info(player_id)

        assert isinstance(info, CheckinInfo)
        assert info.can_checkin == True  # 未签到
        assert info.today_checked == False
        assert info.streak_info is not None

    def test_get_checkin_info_after_checkin(self, manager):
        """测试签到后获取信息"""
        player_id = "test_player"

        # 执行签到
        manager.checkin(player_id)

        info = manager.get_checkin_info(player_id)

        assert info.can_checkin == False
        assert info.today_checked == True

    def test_get_checkin_records(self, manager):
        """测试获取签到记录"""
        player_id = "test_player"

        # 签到
        manager.checkin(player_id)

        records = manager.get_checkin_records(player_id)

        assert len(records) == 1
        assert records[0].player_id == player_id

    def test_get_reward_config(self, manager):
        """测试获取奖励配置"""
        config = manager.get_reward_config()

        assert "daily_rewards" in config
        assert "monthly_rewards" in config
        assert config["max_supplement_days"] == 3
        assert config["supplement_base_cost"] == 50

    def test_clear_cache(self, manager):
        """测试清除缓存"""
        player_id = "test_player"

        # 创建数据
        manager.checkin(player_id)

        # 清除指定玩家缓存
        manager.clear_cache(player_id)

        assert player_id not in manager.player_streaks
        assert player_id not in manager.player_records

    def test_clear_all_cache(self, manager):
        """测试清除所有缓存"""
        # 创建数据
        manager.checkin("player1")
        manager.checkin("player2")

        # 清除所有缓存
        manager.clear_cache()

        assert len(manager.player_streaks) == 0
        assert len(manager.player_records) == 0


class TestCheckinStreak:
    """测试连续签到逻辑"""

    def test_max_streak_update(self):
        """测试最大连续签到更新"""
        streak = CheckinStreak(player_id="test_player")
        today = date.today()

        for i in range(5):
            streak.update_streak(today + timedelta(days=i))

        assert streak.max_streak == 5

    def test_monthly_count_reset(self):
        """测试月签到计数"""
        streak = CheckinStreak(player_id="test_player")
        today = date.today()

        # 连续签到5天
        for i in range(5):
            streak.update_streak(today + timedelta(days=i))

        assert streak.monthly_count == 5

    def test_streak_after_break(self):
        """测试中断后连续签到重置"""
        streak = CheckinStreak(player_id="test_player")
        today = date.today()

        # 连续签到3天
        for i in range(3):
            streak.update_streak(today + timedelta(days=i))

        assert streak.current_streak == 3

        # 跳过2天后再签到
        streak.update_streak(today + timedelta(days=5))

        assert streak.current_streak == 1
        assert streak.max_streak == 3  # 历史最大保持不变


class TestDailyRewards:
    """测试每日奖励配置"""

    def test_default_rewards(self):
        """测试默认奖励配置"""
        manager = CheckinManager()

        # 验证7天循环奖励
        assert 1 in manager.daily_rewards
        assert 7 in manager.daily_rewards

        # 验证月度奖励
        assert 7 in manager.monthly_rewards
        assert 30 in manager.monthly_rewards

    def test_day_7_rewards(self):
        """测试第7天奖励"""
        manager = CheckinManager()

        day7 = manager.daily_rewards[7]
        assert day7.day == 7

        # 第7天应该有基础奖励和额外奖励
        assert len(day7.base_rewards) > 0
        assert len(day7.bonus_rewards) > 0

    def test_monthly_30_rewards(self):
        """测试30天月度奖励"""
        manager = CheckinManager()

        month30 = manager.monthly_rewards[30]
        assert month30.day == 30
        assert month30.day_type == "monthly"

        # 30天奖励应该更丰厚
        assert len(month30.base_rewards) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
