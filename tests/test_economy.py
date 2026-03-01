"""
王者之奕 - 经济系统测试

测试经济系统的核心功能：
- 利息计算
- 连胜奖励
- 连败奖励
- 回合总收入
- 升级逻辑
- 购买经验
- 最高等级
"""

import pytest

from server.game.economy import (
    EconomyManager,
    EconomyState,
    create_economy_manager,
    get_income_table,
    get_level_table,
    get_streak_bonus_table,
)
from shared.constants import (
    BASE_INCOME_PER_ROUND,
    BUY_EXP_AMOUNT,
    BUY_EXP_COST,
    INTEREST_INCREMENT,
    LEVEL_UP_EXP,
    MAX_INTEREST_GOLD,
    MAX_LOSE_STREAK_BONUS,
    MAX_PLAYER_LEVEL,
    MAX_WIN_STREAK_BONUS,
    SHOP_REFRESH_COST,
)

# ============================================================================
# 测试 Fixtures
# ============================================================================


@pytest.fixture
def economy() -> EconomyManager:
    """创建默认经济管理器"""
    return EconomyManager()


@pytest.fixture
def economy_with_gold() -> EconomyManager:
    """创建带有金币的经济管理器"""
    return EconomyManager(initial_gold=50)


@pytest.fixture
def high_level_economy() -> EconomyManager:
    """创建高级经济管理器"""
    eco = EconomyManager(initial_gold=100)
    eco.state.level = 8
    eco.state.exp = 100
    return eco


# ============================================================================
# test_calculate_interest - 利息计算测试
# ============================================================================


class TestCalculateInterest:
    """利息计算测试"""

    def test_zero_gold_interest(self, economy: EconomyManager):
        """测试0金币时的利息"""
        interest = economy.calculate_interest(gold=0)
        assert interest == 0

    def test_below_interest_threshold(self, economy: EconomyManager):
        """测试低于利息阈值"""
        # 9金币 -> 0利息
        interest = economy.calculate_interest(gold=9)
        assert interest == 0

    def test_single_interest_unit(self, economy: EconomyManager):
        """测试单个利息单位（10金币）"""
        interest = economy.calculate_interest(gold=10)
        assert interest == 1

    def test_multiple_interest_units(self, economy: EconomyManager):
        """测试多个利息单位"""
        # 30金币 -> 3利息
        interest = economy.calculate_interest(gold=30)
        assert interest == 3

        # 40金币 -> 4利息
        interest = economy.calculate_interest(gold=40)
        assert interest == 4

    def test_interest_cap(self, economy: EconomyManager):
        """测试利息上限"""
        # 50金币 -> 5利息（上限）
        interest = economy.calculate_interest(gold=50)
        assert interest == 5

        # 60金币 -> 5利息（仍然上限）
        interest = economy.calculate_interest(gold=60)
        assert interest == 5

        # 100金币 -> 5利息（仍然上限）
        interest = economy.calculate_interest(gold=100)
        assert interest == 5

    def test_interest_boundary_values(self, economy: EconomyManager):
        """测试利息边界值"""
        # 恰好触发利息
        assert economy.calculate_interest(gold=10) == 1
        assert economy.calculate_interest(gold=19) == 1
        assert economy.calculate_interest(gold=20) == 2
        assert economy.calculate_interest(gold=49) == 4
        assert economy.calculate_interest(gold=50) == 5

    def test_interest_uses_current_gold(self, economy_with_gold: EconomyManager):
        """测试默认使用当前金币计算利息"""
        # economy_with_gold 有50金币
        interest = economy_with_gold.calculate_interest()
        assert interest == 5

    def test_interest_all_values(self, economy: EconomyManager):
        """测试所有金币值的利息"""
        for gold in range(0, 100):
            interest = economy.calculate_interest(gold=gold)
            expected = min(gold // INTEREST_INCREMENT, MAX_INTEREST_GOLD)
            assert interest == expected, f"Failed at gold={gold}"


# ============================================================================
# test_win_streak_bonus - 连胜奖励测试
# ============================================================================


class TestWinStreakBonus:
    """连胜奖励测试"""

    def test_no_streak_bonus(self, economy: EconomyManager):
        """测试无连胜时的奖励"""
        # 0-1连胜无奖励
        assert economy.calculate_win_streak_bonus(streak=0) == 0
        assert economy.calculate_win_streak_bonus(streak=1) == 0

    def test_2_3_win_streak(self, economy: EconomyManager):
        """测试2-3连胜奖励"""
        # 2-3连胜 -> +1金币
        assert economy.calculate_win_streak_bonus(streak=2) == 1
        assert economy.calculate_win_streak_bonus(streak=3) == 1

    def test_4_5_win_streak(self, economy: EconomyManager):
        """测试4-5连胜奖励"""
        # 4-5连胜 -> +2金币
        assert economy.calculate_win_streak_bonus(streak=4) == 2
        assert economy.calculate_win_streak_bonus(streak=5) == 2

    def test_6_plus_win_streak(self, economy: EconomyManager):
        """测试6+连胜奖励"""
        # 6+连胜 -> +3金币（上限）
        assert economy.calculate_win_streak_bonus(streak=6) == 3
        assert economy.calculate_win_streak_bonus(streak=7) == 3
        assert economy.calculate_win_streak_bonus(streak=10) == 3
        assert economy.calculate_win_streak_bonus(streak=20) == 3

    def test_win_streak_uses_current_streak(self, economy: EconomyManager):
        """测试使用当前连胜计算"""
        economy.record_win()  # 1连胜
        economy.record_win()  # 2连胜
        assert economy.calculate_win_streak_bonus() == 1

        economy.record_win()  # 3连胜
        economy.record_win()  # 4连胜
        assert economy.calculate_win_streak_bonus() == 2

    def test_win_streak_all_values(self, economy: EconomyManager):
        """测试所有连胜值的奖励"""
        for streak in range(0, 15):
            bonus = economy.calculate_win_streak_bonus(streak=streak)

            if streak < 2:
                expected = 0
            elif streak < 4:
                expected = 1
            elif streak < 6:
                expected = 2
            else:
                expected = 3

            assert bonus == expected, f"Failed at streak={streak}"


# ============================================================================
# test_lose_streak_bonus - 连败奖励测试
# ============================================================================


class TestLoseStreakBonus:
    """连败奖励测试"""

    def test_no_streak_bonus(self, economy: EconomyManager):
        """测试无连败时的奖励"""
        assert economy.calculate_lose_streak_bonus(streak=0) == 0
        assert economy.calculate_lose_streak_bonus(streak=1) == 0

    def test_2_3_lose_streak(self, economy: EconomyManager):
        """测试2-3连败奖励"""
        assert economy.calculate_lose_streak_bonus(streak=2) == 1
        assert economy.calculate_lose_streak_bonus(streak=3) == 1

    def test_4_5_lose_streak(self, economy: EconomyManager):
        """测试4-5连败奖励"""
        assert economy.calculate_lose_streak_bonus(streak=4) == 2
        assert economy.calculate_lose_streak_bonus(streak=5) == 2

    def test_6_plus_lose_streak(self, economy: EconomyManager):
        """测试6+连败奖励"""
        assert economy.calculate_lose_streak_bonus(streak=6) == 3
        assert economy.calculate_lose_streak_bonus(streak=7) == 3
        assert economy.calculate_lose_streak_bonus(streak=10) == 3

    def test_lose_streak_uses_current_streak(self, economy: EconomyManager):
        """测试使用当前连败计算"""
        economy.record_loss()  # 1连败
        economy.record_loss()  # 2连败
        assert economy.calculate_lose_streak_bonus() == 1

        economy.record_loss()  # 3连败
        economy.record_loss()  # 4连败
        assert economy.calculate_lose_streak_bonus() == 2

    def test_lose_streak_all_values(self, economy: EconomyManager):
        """测试所有连败值的奖励"""
        for streak in range(0, 15):
            bonus = economy.calculate_lose_streak_bonus(streak=streak)

            if streak < 2:
                expected = 0
            elif streak < 4:
                expected = 1
            elif streak < 6:
                expected = 2
            else:
                expected = 3

            assert bonus == expected, f"Failed at streak={streak}"

    def test_win_resets_lose_streak(self, economy: EconomyManager):
        """测试胜利重置连败"""
        economy.record_loss()  # 1连败
        economy.record_loss()  # 2连败
        economy.record_loss()  # 3连败

        assert economy.state.lose_streak == 3

        economy.record_win()  # 胜利

        assert economy.state.lose_streak == 0
        assert economy.state.win_streak == 1

    def test_loss_resets_win_streak(self, economy: EconomyManager):
        """测试失败重置连胜"""
        economy.record_win()  # 1连胜
        economy.record_win()  # 2连胜
        economy.record_win()  # 3连胜

        assert economy.state.win_streak == 3

        economy.record_loss()  # 失败

        assert economy.state.win_streak == 0
        assert economy.state.lose_streak == 1


# ============================================================================
# test_round_income - 回合总收入测试
# ============================================================================


class TestRoundIncome:
    """回合总收入测试"""

    def test_base_income_only(self, economy: EconomyManager):
        """测试仅有基础收入"""
        breakdown = economy.calculate_round_income(gold=0, win_streak=0, lose_streak=0)

        assert breakdown.base_income == BASE_INCOME_PER_ROUND
        assert breakdown.interest_income == 0
        assert breakdown.win_streak_income == 0
        assert breakdown.lose_streak_income == 0
        assert breakdown.total_income == BASE_INCOME_PER_ROUND

    def test_income_with_interest(self, economy: EconomyManager):
        """测试含利息的收入"""
        breakdown = economy.calculate_round_income(gold=30, win_streak=0, lose_streak=0)

        assert breakdown.base_income == BASE_INCOME_PER_ROUND
        assert breakdown.interest_income == 3  # 30/10 = 3
        assert breakdown.total_income == BASE_INCOME_PER_ROUND + 3

    def test_income_with_win_streak(self, economy: EconomyManager):
        """测试含连胜的收入"""
        breakdown = economy.calculate_round_income(gold=0, win_streak=4, lose_streak=0)

        assert breakdown.base_income == BASE_INCOME_PER_ROUND
        assert breakdown.win_streak_income == 2  # 4连胜
        assert breakdown.total_income == BASE_INCOME_PER_ROUND + 2

    def test_income_with_lose_streak(self, economy: EconomyManager):
        """测试含连败的收入"""
        breakdown = economy.calculate_round_income(gold=0, win_streak=0, lose_streak=4)

        assert breakdown.base_income == BASE_INCOME_PER_ROUND
        assert breakdown.lose_streak_income == 2  # 4连败
        assert breakdown.total_income == BASE_INCOME_PER_ROUND + 2

    def test_income_all_components(self, economy: EconomyManager):
        """测试所有收入组成部分"""
        breakdown = economy.calculate_round_income(gold=50, win_streak=6, lose_streak=0)

        assert breakdown.base_income == BASE_INCOME_PER_ROUND
        assert breakdown.interest_income == 5  # 上限
        assert breakdown.win_streak_income == 3  # 6连胜上限
        assert breakdown.total_income == BASE_INCOME_PER_ROUND + 5 + 3

    def test_win_vs_lose_streak_takes_higher(self, economy: EconomyManager):
        """测试连胜和连败取较大值"""
        # 连胜较高
        breakdown = economy.calculate_round_income(gold=0, win_streak=6, lose_streak=2)
        assert breakdown.win_streak_income == 3
        assert breakdown.lose_streak_income == 0

        # 连败较高
        breakdown = economy.calculate_round_income(gold=0, win_streak=2, lose_streak=6)
        assert breakdown.win_streak_income == 0
        assert breakdown.lose_streak_income == 3

    def test_apply_round_income(self, economy: EconomyManager):
        """测试应用回合收入"""
        economy.state.gold = 50
        economy.state.win_streak = 6

        initial_gold = economy.state.gold
        breakdown = economy.apply_round_income()

        assert economy.state.gold == initial_gold + breakdown.total_income
        assert breakdown.interest_income == 5
        assert breakdown.win_streak_income == 3

    def test_max_possible_income(self, economy: EconomyManager):
        """测试最大可能收入"""
        # 50金币 + 6连胜 = 5(基础) + 5(利息上限) + 3(连胜上限) = 13
        breakdown = economy.calculate_round_income(gold=50, win_streak=10, lose_streak=0)
        assert (
            breakdown.total_income
            == BASE_INCOME_PER_ROUND + MAX_INTEREST_GOLD + MAX_WIN_STREAK_BONUS
        )

    def test_income_breakdown_to_dict(self, economy: EconomyManager):
        """测试收入明细序列化"""
        breakdown = economy.calculate_round_income(gold=50, win_streak=6, lose_streak=0)
        data = breakdown.to_dict()

        assert "base_income" in data
        assert "interest_income" in data
        assert "win_streak_income" in data
        assert "lose_streak_income" in data
        assert "total_income" in data


# ============================================================================
# test_level_up - 升级逻辑测试
# ============================================================================


class TestLevelUp:
    """升级逻辑测试"""

    def test_initial_level(self, economy: EconomyManager):
        """测试初始等级"""
        assert economy.get_level() == 1
        assert economy.get_exp() == 0

    def test_add_exp_without_level_up(self, economy: EconomyManager):
        """测试增加经验但未升级"""
        result = economy.add_exp(1)

        assert result.success is False
        assert economy.get_level() == 1
        assert economy.get_exp() == 1

    def test_add_exp_with_level_up(self, economy: EconomyManager):
        """测试增加经验并升级"""
        # 升到2级需要2经验
        result = economy.add_exp(2)

        assert result.success is True
        assert result.old_level == 1
        assert result.new_level == 2
        assert economy.get_level() == 2

    def test_multiple_level_ups(self, economy: EconomyManager):
        """测试一次经验导致多次升级"""
        # 1->2: 2exp, 2->3: 2exp, 3->4: 6exp
        # 共需要 2+2+6=10exp 才能升到4级
        result = economy.add_exp(10)

        assert result.success is True
        assert economy.get_level() == 4

    def test_level_progression(self, economy: EconomyManager):
        """测试等级递进"""
        current_level = 1
        for target_level in range(2, MAX_PLAYER_LEVEL + 1):
            exp_needed = economy.get_exp_needed_for_next_level()
            result = economy.add_exp(exp_needed)

            assert economy.get_level() == target_level
            current_level = target_level

    def test_max_field_heroes(self, economy: EconomyManager):
        """测试最大上场数量"""
        # 等级 = 上场数量
        for level in range(1, MAX_PLAYER_LEVEL + 1):
            economy.state.level = level
            assert economy.get_max_field_heroes() == level

    def test_exp_for_next_level(self, economy: EconomyManager):
        """测试下一级所需经验"""
        # 升到2级总共需要2经验
        assert economy.get_exp_for_next_level(2) == 2

        # 升到3级总共需要2+2=4经验
        assert economy.get_exp_for_next_level(3) == 4

        # 升到4级总共需要2+2+6=10经验
        assert economy.get_exp_for_next_level(4) == 10

    def test_exp_for_max_level(self, economy: EconomyManager):
        """测试最高级经验需求"""
        # 超过最高级返回-1
        assert economy.get_exp_for_next_level(MAX_PLAYER_LEVEL + 1) == -1

    def test_exp_needed_for_next_level(self, economy: EconomyManager):
        """测试还需要多少经验"""
        economy.state.exp = 1
        economy.state.level = 1

        # 还需要1经验升到2级
        assert economy.get_exp_needed_for_next_level() == 1

    def test_level_up_result_serialization(self, economy: EconomyManager):
        """测试升级结果序列化"""
        result = economy.add_exp(2)
        data = result.to_dict()

        assert "success" in data
        assert "old_level" in data
        assert "new_level" in data


# ============================================================================
# test_buy_exp - 购买经验测试
# ============================================================================


class TestBuyExp:
    """购买经验测试"""

    def test_buy_exp_success(self, economy_with_gold: EconomyManager):
        """测试成功购买经验"""
        initial_gold = economy_with_gold.get_gold()
        result = economy_with_gold.buy_exp()

        assert result.success is True
        assert economy_with_gold.get_gold() == initial_gold - BUY_EXP_COST
        # 购买4经验，可能导致升级
        assert result.exp_gained == BUY_EXP_AMOUNT

    def test_buy_exp_insufficient_gold(self, economy: EconomyManager):
        """测试金币不足购买经验"""
        economy.state.gold = 2  # 少于 BUY_EXP_COST(4)
        result = economy.buy_exp()

        assert result.success is False
        assert result.cost == BUY_EXP_COST

    def test_buy_exp_exact_gold(self, economy: EconomyManager):
        """测试恰好够金币购买"""
        economy.state.gold = BUY_EXP_COST
        result = economy.buy_exp()

        assert result.success is True
        assert economy.get_gold() == 0

    def test_buy_exp_multiple_times(self, economy_with_gold: EconomyManager):
        """测试多次购买经验"""
        for _ in range(5):
            if economy_with_gold.can_afford(BUY_EXP_COST):
                result = economy_with_gold.buy_exp()
                assert result.success is True

    def test_buy_exp_at_max_level(self, high_level_economy: EconomyManager):
        """测试最高级购买经验"""
        high_level_economy.state.level = MAX_PLAYER_LEVEL
        high_level_economy.state.exp = 0

        result = high_level_economy.buy_exp()

        # 可以购买但不会升级
        assert result.new_level == MAX_PLAYER_LEVEL


# ============================================================================
# test_max_level - 最高等级测试
# ============================================================================


class TestMaxLevel:
    """最高等级测试"""

    def test_is_max_level_false(self, economy: EconomyManager):
        """测试未达最高等级"""
        assert economy.is_max_level() is False

    def test_is_max_level_true(self, high_level_economy: EconomyManager):
        """测试已达最高等级"""
        high_level_economy.state.level = MAX_PLAYER_LEVEL
        assert high_level_economy.is_max_level() is True

    def test_cannot_exceed_max_level(self, economy: EconomyManager):
        """测试不能超过最高等级"""
        economy.state.level = MAX_PLAYER_LEVEL
        economy.state.exp = 0

        # 添加大量经验
        result = economy.add_exp(1000)

        assert economy.get_level() == MAX_PLAYER_LEVEL
        assert economy.is_max_level() is True

    def test_max_level_constant(self):
        """测试最高等级常量"""
        assert MAX_PLAYER_LEVEL == 10

    def test_level_table(self):
        """测试等级表"""
        table = get_level_table()

        assert len(table) == MAX_PLAYER_LEVEL

        for i, entry in enumerate(table):
            assert entry["level"] == i + 1
            assert entry["max_heroes"] == i + 1

    def test_exp_requirements(self):
        """测试经验需求表"""
        for level in range(2, MAX_PLAYER_LEVEL + 1):
            assert level in LEVEL_UP_EXP
            assert LEVEL_UP_EXP[level] > 0


# ============================================================================
# 金币操作测试
# ============================================================================


class TestGoldOperations:
    """金币操作测试"""

    def test_get_gold(self, economy_with_gold: EconomyManager):
        """测试获取金币"""
        assert economy_with_gold.get_gold() == 50

    def test_can_afford(self, economy: EconomyManager):
        """测试能否支付"""
        economy.state.gold = 10

        assert economy.can_afford(5) is True
        assert economy.can_afford(10) is True
        assert economy.can_afford(11) is False

    def test_spend_gold_success(self, economy: EconomyManager):
        """测试成功花费金币"""
        economy.state.gold = 10
        result = economy.spend_gold(5)

        assert result is True
        assert economy.get_gold() == 5

    def test_spend_gold_failure(self, economy: EconomyManager):
        """测试花费金币失败"""
        economy.state.gold = 3
        result = economy.spend_gold(5)

        assert result is False
        assert economy.get_gold() == 3

    def test_earn_gold(self, economy: EconomyManager):
        """测试获得金币"""
        economy.state.gold = 10
        economy.earn_gold(5)

        assert economy.get_gold() == 15

    def test_total_gold_tracking(self, economy: EconomyManager):
        """测试金币累计统计"""
        economy.earn_gold(10)
        economy.earn_gold(5)
        economy.spend_gold(3)

        assert economy.state.total_gold_earned == 15
        assert economy.state.total_gold_spent == 3


# ============================================================================
# 商店相关经济测试
# ============================================================================


class TestShopEconomy:
    """商店相关经济测试"""

    def test_get_refresh_cost(self, economy: EconomyManager):
        """测试刷新费用"""
        assert economy.get_refresh_cost() == SHOP_REFRESH_COST

    def test_can_refresh_shop(self, economy: EconomyManager):
        """测试能否刷新商店"""
        economy.state.gold = SHOP_REFRESH_COST
        assert economy.can_refresh_shop() is True

        economy.state.gold = SHOP_REFRESH_COST - 1
        assert economy.can_refresh_shop() is False

    def test_pay_for_refresh(self, economy: EconomyManager):
        """测试支付刷新费用"""
        economy.state.gold = 10
        result = economy.pay_for_refresh()

        assert result is True
        assert economy.get_gold() == 10 - SHOP_REFRESH_COST

    def test_can_buy_hero(self, economy: EconomyManager):
        """测试能否购买英雄"""
        economy.state.gold = 5

        assert economy.can_buy_hero(3) is True  # 3费英雄
        assert economy.can_buy_hero(5) is True  # 5费英雄
        assert economy.can_buy_hero(6) is False  # 不够

    def test_pay_for_hero(self, economy: EconomyManager):
        """测试支付英雄费用"""
        economy.state.gold = 10
        result = economy.pay_for_hero(3)

        assert result is True
        assert economy.get_gold() == 7


# ============================================================================
# 状态管理测试
# ============================================================================


class TestStateManagement:
    """状态管理测试"""

    def test_get_state(self, economy_with_gold: EconomyManager):
        """测试获取状态"""
        state = economy_with_gold.get_state()

        assert isinstance(state, EconomyState)
        assert state.gold == 50

    def test_set_state(self, economy: EconomyManager):
        """测试设置状态"""
        new_state = EconomyState(
            gold=100,
            level=5,
            exp=10,
            win_streak=3,
        )
        economy.set_state(new_state)

        assert economy.get_gold() == 100
        assert economy.get_level() == 5
        assert economy.get_exp() == 10

    def test_reset(self, economy_with_gold: EconomyManager):
        """测试重置"""
        economy_with_gold.reset(initial_gold=20)

        assert economy_with_gold.get_gold() == 20
        assert economy_with_gold.get_level() == 1
        assert economy_with_gold.get_exp() == 0

    def test_to_dict(self, economy_with_gold: EconomyManager):
        """测试序列化为字典"""
        data = economy_with_gold.to_dict()

        assert "gold" in data
        assert "level" in data
        assert "exp" in data
        assert data["gold"] == 50

    def test_from_dict(self):
        """测试从字典反序列化"""
        data = {"gold": 30, "level": 3, "exp": 5}
        economy = EconomyManager.from_dict(data)

        assert economy.get_gold() == 30
        assert economy.get_level() == 3
        assert economy.get_exp() == 5

    def test_state_serialization(self):
        """测试状态序列化"""
        state = EconomyState(
            gold=50,
            level=5,
            exp=10,
            win_streak=3,
            lose_streak=0,
            total_gold_earned=100,
            total_gold_spent=50,
        )
        data = state.to_dict()

        assert data["gold"] == 50
        assert data["level"] == 5
        assert data["win_streak"] == 3


# ============================================================================
# 边界条件测试
# ============================================================================


class TestBoundaryConditions:
    """边界条件测试"""

    def test_zero_gold_operations(self, economy: EconomyManager):
        """测试零金币操作"""
        assert economy.calculate_interest(gold=0) == 0
        assert economy.can_afford(0) is True
        assert economy.spend_gold(0) is True

    def test_negative_gold_prevented(self, economy: EconomyManager):
        """测试防止负金币"""
        economy.state.gold = 5
        result = economy.spend_gold(10)

        assert result is False
        assert economy.get_gold() == 5  # 未改变

    def test_large_gold_amount(self, economy: EconomyManager):
        """测试大额金币"""
        economy.state.gold = 1000
        interest = economy.calculate_interest()

        assert interest == MAX_INTEREST_GOLD  # 仍然受限于上限

    def test_very_long_streak(self, economy: EconomyManager):
        """测试超长连胜"""
        bonus = economy.calculate_win_streak_bonus(streak=100)
        assert bonus == MAX_WIN_STREAK_BONUS

        bonus = economy.calculate_lose_streak_bonus(streak=100)
        assert bonus == MAX_LOSE_STREAK_BONUS

    def test_factory_function(self):
        """测试工厂函数"""
        economy = create_economy_manager(initial_gold=100)

        assert isinstance(economy, EconomyManager)
        assert economy.get_gold() == 100

    def test_income_table(self):
        """测试收入表"""
        table = get_income_table(gold_range=60)

        assert len(table) > 0
        for entry in table:
            assert "gold" in entry
            assert "interest" in entry
            assert entry["interest"] <= MAX_INTEREST_GOLD

    def test_streak_bonus_table(self):
        """测试连胜/连败奖励表"""
        table = get_streak_bonus_table()

        assert "win_streak" in table
        assert "lose_streak" in table
        assert "max_win_bonus" in table
        assert "max_lose_bonus" in table

    def test_consecutive_wins_and_losses(self, economy: EconomyManager):
        """测试连续胜负记录"""
        # 连胜
        for _ in range(5):
            economy.record_win()

        assert economy.state.win_streak == 5
        assert economy.state.lose_streak == 0

        # 连败
        for _ in range(3):
            economy.record_loss()

        assert economy.state.win_streak == 0
        assert economy.state.lose_streak == 3
