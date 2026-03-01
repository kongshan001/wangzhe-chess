"""
王者之奕 - 经济系统实现

本模块实现游戏的经济系统，包括：
- 回合收入计算（基础收入 + 连胜/连败奖励 + 利息）
- 经验升级逻辑
- 等级与上场数量关系

经济系统是自走棋游戏的核心机制之一，合理的经济管理是获胜的关键。
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.constants import (
    BASE_INCOME_PER_ROUND,
    BUY_EXP_AMOUNT,
    BUY_EXP_COST,
    INTEREST_INCREMENT,
    LEVEL_UP_EXP,
    LOSE_STREAK_BONUS,
    MAX_INTEREST_GOLD,
    MAX_LOSE_STREAK_BONUS,
    MAX_PLAYER_LEVEL,
    MAX_WIN_STREAK_BONUS,
    SHOP_REFRESH_COST,
    WIN_STREAK_BONUS,
)

# ============================================================================
# 数据类型定义
# ============================================================================


@dataclass
class IncomeBreakdown:
    """
    回合收入明细

    记录回合收入的各种来源。

    Attributes:
        base_income: 基础收入
        interest_income: 利息收入
        win_streak_income: 连胜奖励
        lose_streak_income: 连败奖励
        total_income: 总收入
    """

    base_income: int = 0
    interest_income: int = 0
    win_streak_income: int = 0
    lose_streak_income: int = 0
    total_income: int = 0

    def calculate_total(self) -> int:
        """计算总收入"""
        self.total_income = (
            self.base_income
            + self.interest_income
            + self.win_streak_income
            + self.lose_streak_income
        )
        return self.total_income

    def to_dict(self) -> dict:
        """序列化为字典"""
        return {
            "base_income": self.base_income,
            "interest_income": self.interest_income,
            "win_streak_income": self.win_streak_income,
            "lose_streak_income": self.lose_streak_income,
            "total_income": self.total_income,
        }


@dataclass
class LevelUpResult:
    """
    升级结果

    Attributes:
        success: 是否成功升级
        old_level: 原等级
        new_level: 新等级
        exp_gained: 获得的经验值
        exp_remaining: 升级后剩余经验值
        cost: 消耗的金币
    """

    success: bool
    old_level: int
    new_level: int
    exp_gained: int = 0
    exp_remaining: int = 0
    cost: int = 0

    def to_dict(self) -> dict:
        """序列化为字典"""
        return {
            "success": self.success,
            "old_level": self.old_level,
            "new_level": self.new_level,
            "exp_gained": self.exp_gained,
            "exp_remaining": self.exp_remaining,
            "cost": self.cost,
        }


@dataclass
class EconomyState:
    """
    玩家经济状态

    Attributes:
        gold: 当前金币
        level: 当前等级
        exp: 当前经验值
        win_streak: 连胜场次
        lose_streak: 连败场次
        total_gold_earned: 累计获得的金币
        total_gold_spent: 累计花费的金币
    """

    gold: int = 0
    level: int = 1
    exp: int = 0
    win_streak: int = 0
    lose_streak: int = 0
    total_gold_earned: int = 0
    total_gold_spent: int = 0

    def to_dict(self) -> dict:
        """序列化为字典"""
        return {
            "gold": self.gold,
            "level": self.level,
            "exp": self.exp,
            "win_streak": self.win_streak,
            "lose_streak": self.lose_streak,
            "total_gold_earned": self.total_gold_earned,
            "total_gold_spent": self.total_gold_spent,
        }


# ============================================================================
# 经济系统核心类
# ============================================================================


class EconomyManager:
    """
    经济管理器

    管理玩家的经济状态，包括收入计算、经验升级等。

    经济系统规则：
    1. 基础收入：每回合固定获得5金币
    2. 利息：每10金币获得1金币利息，上限5金币
    3. 连胜奖励：连续获胜获得额外金币
    4. 连败奖励：连续失败获得额外金币（保底机制）

    Attributes:
        state: 玩家经济状态
    """

    def __init__(
        self,
        initial_gold: int = 0,
        initial_level: int = 1,
        initial_exp: int = 0,
    ) -> None:
        """
        初始化经济管理器

        Args:
            initial_gold: 初始金币
            initial_level: 初始等级
            initial_exp: 初始经验值
        """
        self.state = EconomyState(
            gold=initial_gold,
            level=initial_level,
            exp=initial_exp,
        )

    # ========================================================================
    # 金币相关操作
    # ========================================================================

    def get_gold(self) -> int:
        """
        获取当前金币

        Returns:
            当前金币数量
        """
        return self.state.gold

    def can_afford(self, cost: int) -> bool:
        """
        检查是否有足够金币

        Args:
            cost: 需要的金币数量

        Returns:
            是否有足够金币
        """
        return self.state.gold >= cost

    def spend_gold(self, amount: int) -> bool:
        """
        花费金币

        Args:
            amount: 花费金额

        Returns:
            是否成功花费
        """
        if not self.can_afford(amount):
            return False
        self.state.gold -= amount
        self.state.total_gold_spent += amount
        return True

    def earn_gold(self, amount: int) -> None:
        """
        获得金币

        Args:
            amount: 获得的金币数量
        """
        self.state.gold += amount
        self.state.total_gold_earned += amount

    # ========================================================================
    # 收入计算
    # ========================================================================

    def calculate_interest(self, gold: int | None = None) -> int:
        """
        计算利息收入

        利息规则：每10金币获得1金币利息，上限5金币

        Args:
            gold: 计算利息的金币数（默认使用当前金币）

        Returns:
            利息收入
        """
        if gold is None:
            gold = self.state.gold

        # 每10金币获得1金币利息
        interest = gold // INTEREST_INCREMENT

        # 利息上限
        return min(interest, MAX_INTEREST_GOLD)

    def calculate_win_streak_bonus(self, streak: int | None = None) -> int:
        """
        计算连胜奖励

        连胜奖励规则：
        - 2-3连胜：+1金币
        - 4-5连胜：+2金币
        - 6+连胜：+3金币（上限）

        Args:
            streak: 连胜场次（默认使用当前连胜）

        Returns:
            连胜奖励
        """
        if streak is None:
            streak = self.state.win_streak

        if streak < 2:
            return 0

        # 查找对应的连胜奖励
        for required_streak, bonus in sorted(WIN_STREAK_BONUS.items(), reverse=True):
            if streak >= required_streak:
                return bonus

        return MAX_WIN_STREAK_BONUS

    def calculate_lose_streak_bonus(self, streak: int | None = None) -> int:
        """
        计算连败奖励

        连败奖励规则：
        - 2-3连败：+1金币
        - 4-5连败：+2金币
        - 6+连败：+3金币（上限）

        Args:
            streak: 连败场次（默认使用当前连败）

        Returns:
            连败奖励
        """
        if streak is None:
            streak = self.state.lose_streak

        if streak < 2:
            return 0

        # 查找对应的连败奖励
        for required_streak, bonus in sorted(LOSE_STREAK_BONUS.items(), reverse=True):
            if streak >= required_streak:
                return bonus

        return MAX_LOSE_STREAK_BONUS

    def calculate_round_income(
        self,
        gold: int | None = None,
        win_streak: int | None = None,
        lose_streak: int | None = None,
    ) -> IncomeBreakdown:
        """
        计算回合总收入

        收入组成：
        1. 基础收入：5金币
        2. 利息：根据金币数量计算
        3. 连胜/连败奖励：二选一，不会同时获得

        Args:
            gold: 用于计算利息的金币数
            win_streak: 连胜场次
            lose_streak: 连败场次

        Returns:
            收入明细
        """
        breakdown = IncomeBreakdown()

        # 基础收入
        breakdown.base_income = BASE_INCOME_PER_ROUND

        # 利息收入
        breakdown.interest_income = self.calculate_interest(gold)

        # 连胜/连败奖励（取较大值，不会同时获得）
        w_bonus = self.calculate_win_streak_bonus(win_streak)
        l_bonus = self.calculate_lose_streak_bonus(lose_streak)

        if w_bonus > l_bonus:
            breakdown.win_streak_income = w_bonus
        else:
            breakdown.lose_streak_income = l_bonus

        # 计算总收入
        breakdown.calculate_total()

        return breakdown

    def apply_round_income(self) -> IncomeBreakdown:
        """
        应用回合收入

        根据当前状态计算收入并加到金币上。

        Returns:
            收入明细
        """
        breakdown = self.calculate_round_income(
            gold=self.state.gold,
            win_streak=self.state.win_streak,
            lose_streak=self.state.lose_streak,
        )

        self.earn_gold(breakdown.total_income)

        return breakdown

    # ========================================================================
    # 连胜/连败管理
    # ========================================================================

    def record_win(self) -> int:
        """
        记录一场胜利

        重置连败计数，增加连胜计数。

        Returns:
            更新后的连胜场次
        """
        self.state.lose_streak = 0
        self.state.win_streak += 1
        return self.state.win_streak

    def record_loss(self) -> int:
        """
        记录一场失败

        重置连胜计数，增加连败计数。

        Returns:
            更新后的连败场次
        """
        self.state.win_streak = 0
        self.state.lose_streak += 1
        return self.state.lose_streak

    def reset_streaks(self) -> None:
        """重置连胜和连败计数"""
        self.state.win_streak = 0
        self.state.lose_streak = 0

    # ========================================================================
    # 等级和经验系统
    # ========================================================================

    def get_level(self) -> int:
        """
        获取当前等级

        Returns:
            当前等级
        """
        return self.state.level

    def get_exp(self) -> int:
        """
        获取当前经验值

        Returns:
            当前经验值
        """
        return self.state.exp

    def get_exp_for_next_level(self, level: int | None = None) -> int:
        """
        获取升到下一级所需的总经验值

        Args:
            level: 目标等级（默认使用当前等级+1）

        Returns:
            所需经验值，如果已达最高级返回-1
        """
        if level is None:
            level = self.state.level + 1

        if level > MAX_PLAYER_LEVEL:
            return -1

        # 计算从1级升到目标等级所需的总经验
        total_exp = 0
        for lvl in range(2, level + 1):
            total_exp += LEVEL_UP_EXP.get(lvl, 0)

        return total_exp

    def get_exp_needed_for_next_level(self) -> int:
        """
        获取升到下一级还需要多少经验值

        Returns:
            还需要的经验值，如果已达最高级返回-1
        """
        next_level = self.state.level + 1
        if next_level > MAX_PLAYER_LEVEL:
            return -1

        total_needed = self.get_exp_for_next_level(next_level)
        return total_needed - self.state.exp

    def get_max_field_heroes(self) -> int:
        """
        获取当前等级可上场的最大英雄数量

        等级 = 可上场数量

        Returns:
            最大上场数量
        """
        return self.state.level

    def add_exp(self, amount: int) -> LevelUpResult:
        """
        增加经验值（自动升级）

        增加经验后自动检查是否升级，可能会连续升级多级。

        Args:
            amount: 增加的经验值

        Returns:
            升级结果（包含可能的多次升级信息）
        """
        old_level = self.state.level
        self.state.exp += amount

        # 检查升级（可能连续升级）
        while self._check_level_up():
            pass

        new_level = self.state.level

        return LevelUpResult(
            success=new_level > old_level,
            old_level=old_level,
            new_level=new_level,
            exp_gained=amount,
            exp_remaining=self.state.exp,
        )

    def _check_level_up(self) -> bool:
        """
        检查并执行升级

        Returns:
            是否发生了升级
        """
        if self.state.level >= MAX_PLAYER_LEVEL:
            return False

        next_level = self.state.level + 1
        total_exp_needed = self.get_exp_for_next_level(next_level)

        if self.state.exp >= total_exp_needed:
            self.state.level = next_level
            return True

        return False

    def buy_exp(self) -> LevelUpResult:
        """
        购买经验

        花费金币购买经验值。

        Returns:
            升级结果（success=True 表示购买成功，不一定是升级成功）
        """
        old_level = self.state.level

        if not self.can_afford(BUY_EXP_COST):
            return LevelUpResult(
                success=False,
                old_level=old_level,
                new_level=old_level,
                cost=BUY_EXP_COST,
            )

        # 花费金币
        self.spend_gold(BUY_EXP_COST)

        # 增加经验
        result = self.add_exp(BUY_EXP_AMOUNT)
        result.cost = BUY_EXP_COST
        result.success = True  # 购买成功（不一定是升级成功）

        return result

    def is_max_level(self) -> bool:
        """
        检查是否已达最高等级

        Returns:
            是否已达最高等级
        """
        return self.state.level >= MAX_PLAYER_LEVEL

    # ========================================================================
    # 商店相关经济操作
    # ========================================================================

    def get_refresh_cost(self) -> int:
        """
        获取商店刷新费用

        Returns:
            刷新费用
        """
        return SHOP_REFRESH_COST

    def can_refresh_shop(self) -> bool:
        """
        检查是否有足够金币刷新商店

        Returns:
            是否可以刷新
        """
        return self.can_afford(SHOP_REFRESH_COST)

    def pay_for_refresh(self) -> bool:
        """
        支付商店刷新费用

        Returns:
            是否成功支付
        """
        return self.spend_gold(SHOP_REFRESH_COST)

    def can_buy_hero(self, cost: int) -> bool:
        """
        检查是否有足够金币购买英雄

        Args:
            cost: 英雄费用

        Returns:
            是否可以购买
        """
        return self.can_afford(cost)

    def pay_for_hero(self, cost: int) -> bool:
        """
        支付购买英雄的费用

        Args:
            cost: 英雄费用

        Returns:
            是否成功支付
        """
        return self.spend_gold(cost)

    # ========================================================================
    # 状态管理
    # ========================================================================

    def get_state(self) -> EconomyState:
        """
        获取当前经济状态

        Returns:
            经济状态的副本
        """
        return EconomyState(
            gold=self.state.gold,
            level=self.state.level,
            exp=self.state.exp,
            win_streak=self.state.win_streak,
            lose_streak=self.state.lose_streak,
            total_gold_earned=self.state.total_gold_earned,
            total_gold_spent=self.state.total_gold_spent,
        )

    def set_state(self, state: EconomyState) -> None:
        """
        设置经济状态

        Args:
            state: 新的经济状态
        """
        self.state = EconomyState(
            gold=state.gold,
            level=state.level,
            exp=state.exp,
            win_streak=state.win_streak,
            lose_streak=state.lose_streak,
            total_gold_earned=state.total_gold_earned,
            total_gold_spent=state.total_gold_spent,
        )

    def reset(self, initial_gold: int = 0) -> None:
        """
        重置经济状态

        Args:
            initial_gold: 初始金币
        """
        self.state = EconomyState(gold=initial_gold)

    def to_dict(self) -> dict:
        """
        序列化为字典

        Returns:
            状态字典
        """
        return self.state.to_dict()

    @classmethod
    def from_dict(cls, data: dict) -> EconomyManager:
        """
        从字典反序列化

        Args:
            data: 状态字典

        Returns:
            经济管理器实例
        """
        return cls(
            initial_gold=data.get("gold", 0),
            initial_level=data.get("level", 1),
            initial_exp=data.get("exp", 0),
        )


# ============================================================================
# 等级系统辅助函数
# ============================================================================


def get_level_table() -> list[dict]:
    """
    获取等级表

    返回所有等级的经验需求和可上场数量。

    Returns:
        等级表列表
    """
    table = []
    cumulative_exp = 0

    for level in range(1, MAX_PLAYER_LEVEL + 1):
        exp_for_level = LEVEL_UP_EXP.get(level + 1, 0) if level < MAX_PLAYER_LEVEL else 0
        cumulative_exp += exp_for_level

        table.append(
            {
                "level": level,
                "max_heroes": level,
                "exp_for_next_level": exp_for_level if level < MAX_PLAYER_LEVEL else 0,
                "total_exp_required": cumulative_exp,
            }
        )

    return table


def get_income_table(gold_range: int = 60) -> list[dict]:
    """
    获取收入表

    返回不同金币数量对应的利息收入。

    Args:
        gold_range: 金币范围上限

    Returns:
        收入表列表
    """
    table = []

    for gold in range(0, gold_range + 1, 5):
        interest = min(gold // 10, MAX_INTEREST_GOLD)
        table.append(
            {
                "gold": gold,
                "interest": interest,
                "base_income": BASE_INCOME_PER_ROUND,
                "total_base": BASE_INCOME_PER_ROUND + interest,
            }
        )

    return table


def get_streak_bonus_table() -> dict:
    """
    获取连胜/连败奖励表

    Returns:
        奖励表字典
    """
    return {
        "win_streak": WIN_STREAK_BONUS.copy(),
        "lose_streak": LOSE_STREAK_BONUS.copy(),
        "max_win_bonus": MAX_WIN_STREAK_BONUS,
        "max_lose_bonus": MAX_LOSE_STREAK_BONUS,
    }


# ============================================================================
# 工厂函数
# ============================================================================


def create_economy_manager(initial_gold: int = 0) -> EconomyManager:
    """
    创建经济管理器

    Args:
        initial_gold: 初始金币

    Returns:
        经济管理器实例
    """
    return EconomyManager(initial_gold=initial_gold)
