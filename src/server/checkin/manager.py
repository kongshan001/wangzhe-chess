"""
王者之奕 - 签到管理器

本模块提供签到系统的管理功能：
- CheckinManager: 签到管理器类
- 每日签到处理
- 签到奖励发放
- 连续签到计算
- 补签功能
- 签到配置加载
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .models import (
    CheckinInfo,
    CheckinRecord,
    CheckinReward,
    CheckinStreak,
    DailyRewardConfig,
    RewardType,
)

logger = logging.getLogger(__name__)


class CheckinManager:
    """
    签到管理器
    
    负责管理所有签到相关的操作：
    - 签到奖励配置
    - 每日签到处理
    - 连续签到计算
    - 补签功能
    - 签到记录查询
    
    Attributes:
        daily_rewards: 每日奖励配置 (day -> DailyRewardConfig)
        monthly_rewards: 月度累计奖励配置 (day -> DailyRewardConfig)
        player_streaks: 玩家连续签到数据 (player_id -> CheckinStreak)
        player_records: 玩家签到记录 (player_id -> List[CheckinRecord])
        config_path: 配置文件路径
    """
    
    # 补签最大天数
    MAX_SUPPLEMENT_DAYS = 3
    
    # 补签基础消耗（钻石）
    SUPPLEMENT_BASE_COST = 50
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化签到管理器
        
        Args:
            config_path: 签到配置文件路径
        """
        self.daily_rewards: Dict[int, DailyRewardConfig] = {}
        self.monthly_rewards: Dict[int, DailyRewardConfig] = {}
        self.player_streaks: Dict[str, CheckinStreak] = {}
        self.player_records: Dict[str, List[CheckinRecord]] = {}
        self.config_path = config_path
        
        # 加载配置
        if config_path:
            self.load_config(config_path)
        else:
            self._init_default_rewards()
        
        logger.info(f"CheckinManager initialized with {len(self.daily_rewards)} daily rewards")
    
    def _init_default_rewards(self) -> None:
        """初始化默认签到奖励配置"""
        # 7天循环奖励
        default_daily = [
            DailyRewardConfig(
                day=1,
                base_rewards=[
                    CheckinReward(reward_id="day1_gold", reward_type=RewardType.GOLD, quantity=100),
                ],
            ),
            DailyRewardConfig(
                day=2,
                base_rewards=[
                    CheckinReward(reward_id="day2_gold", reward_type=RewardType.GOLD, quantity=150),
                    CheckinReward(reward_id="day2_fragment", reward_type=RewardType.HERO_FRAGMENT, quantity=5),
                ],
            ),
            DailyRewardConfig(
                day=3,
                base_rewards=[
                    CheckinReward(reward_id="day3_gold", reward_type=RewardType.GOLD, quantity=200),
                ],
                bonus_rewards=[
                    CheckinReward(reward_id="day3_item", reward_type=RewardType.ITEM, item_id="exp_boost", quantity=1),
                ],
            ),
            DailyRewardConfig(
                day=4,
                base_rewards=[
                    CheckinReward(reward_id="day4_gold", reward_type=RewardType.GOLD, quantity=250),
                    CheckinReward(reward_id="day4_fragment", reward_type=RewardType.HERO_FRAGMENT, quantity=10),
                ],
            ),
            DailyRewardConfig(
                day=5,
                base_rewards=[
                    CheckinReward(reward_id="day5_gold", reward_type=RewardType.GOLD, quantity=300),
                ],
                bonus_rewards=[
                    CheckinReward(reward_id="day5_diamond", reward_type=RewardType.DIAMOND, quantity=10),
                ],
            ),
            DailyRewardConfig(
                day=6,
                base_rewards=[
                    CheckinReward(reward_id="day6_gold", reward_type=RewardType.GOLD, quantity=400),
                    CheckinReward(reward_id="day6_fragment", reward_type=RewardType.HERO_FRAGMENT, quantity=15),
                ],
            ),
            DailyRewardConfig(
                day=7,
                base_rewards=[
                    CheckinReward(reward_id="day7_gold", reward_type=RewardType.GOLD, quantity=500),
                ],
                bonus_rewards=[
                    CheckinReward(reward_id="day7_diamond", reward_type=RewardType.DIAMOND, quantity=30),
                    CheckinReward(reward_id="day7_skin", reward_type=RewardType.SKIN, item_id="random_skin_box", quantity=1),
                ],
            ),
        ]
        
        for config in default_daily:
            self.daily_rewards[config.day] = config
        
        # 月度累计奖励（7、14、21、30天）
        default_monthly = [
            DailyRewardConfig(
                day=7,
                day_type="monthly",
                base_rewards=[
                    CheckinReward(reward_id="month7_gold", reward_type=RewardType.GOLD, quantity=500),
                    CheckinReward(reward_id="month7_diamond", reward_type=RewardType.DIAMOND, quantity=20),
                ],
            ),
            DailyRewardConfig(
                day=14,
                day_type="monthly",
                base_rewards=[
                    CheckinReward(reward_id="month14_gold", reward_type=RewardType.GOLD, quantity=1000),
                    CheckinReward(reward_id="month14_fragment", reward_type=RewardType.HERO_FRAGMENT, quantity=30),
                ],
            ),
            DailyRewardConfig(
                day=21,
                day_type="monthly",
                base_rewards=[
                    CheckinReward(reward_id="month21_gold", reward_type=RewardType.GOLD, quantity=1500),
                    CheckinReward(reward_id="month21_diamond", reward_type=RewardType.DIAMOND, quantity=50),
                ],
            ),
            DailyRewardConfig(
                day=30,
                day_type="monthly",
                base_rewards=[
                    CheckinReward(reward_id="month30_gold", reward_type=RewardType.GOLD, quantity=3000),
                    CheckinReward(reward_id="month30_diamond", reward_type=RewardType.DIAMOND, quantity=100),
                    CheckinReward(reward_id="month30_skin", reward_type=RewardType.SKIN, item_id="month_skin_box", quantity=1),
                ],
            ),
        ]
        
        for config in default_monthly:
            self.monthly_rewards[config.day] = config
    
    def load_config(self, config_path: str) -> None:
        """
        从配置文件加载签到奖励
        
        Args:
            config_path: 配置文件路径
        """
        path = Path(config_path)
        if not path.exists():
            logger.warning(f"Checkin config file not found: {config_path}")
            self._init_default_rewards()
            return
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # 加载7天循环奖励
            daily_data = data.get("daily_rewards", [])
            for reward_data in daily_data:
                config = DailyRewardConfig.from_dict(reward_data)
                self.daily_rewards[config.day] = config
            
            # 加载月度累计奖励
            monthly_data = data.get("monthly_rewards", [])
            for reward_data in monthly_data:
                config = DailyRewardConfig.from_dict(reward_data)
                self.monthly_rewards[config.day] = config
            
            logger.info(f"Loaded checkin config from {config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load checkin config: {e}")
            self._init_default_rewards()
    
    def save_config(self, config_path: Optional[str] = None) -> None:
        """
        保存签到配置到文件
        
        Args:
            config_path: 配置文件路径
        """
        path = Path(config_path or self.config_path)
        if not path:
            logger.warning("No config path specified for saving")
            return
        
        try:
            data = {
                "version": "1.0.0",
                "last_updated": datetime.now().isoformat(),
                "daily_rewards": [r.to_dict() for r in self.daily_rewards.values()],
                "monthly_rewards": [r.to_dict() for r in self.monthly_rewards.values()],
            }
            
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved checkin config to {path}")
            
        except Exception as e:
            logger.error(f"Failed to save checkin config: {e}")
    
    def get_or_create_streak(self, player_id: str) -> CheckinStreak:
        """
        获取或创建玩家连续签到数据
        
        Args:
            player_id: 玩家ID
            
        Returns:
            玩家连续签到数据
        """
        if player_id not in self.player_streaks:
            self.player_streaks[player_id] = CheckinStreak(player_id=player_id)
        return self.player_streaks[player_id]
    
    def get_player_records(self, player_id: str, limit: int = 30) -> List[CheckinRecord]:
        """
        获取玩家签到记录
        
        Args:
            player_id: 玩家ID
            limit: 返回数量限制
            
        Returns:
            签到记录列表
        """
        records = self.player_records.get(player_id, [])
        return sorted(records, key=lambda r: r.checkin_date, reverse=True)[:limit]
    
    def has_checked_today(self, player_id: str) -> bool:
        """
        检查玩家今日是否已签到
        
        Args:
            player_id: 玩家ID
            
        Returns:
            是否已签到
        """
        today = date.today()
        records = self.player_records.get(player_id, [])
        for record in records:
            if record.checkin_date == today and not record.is_supplement:
                return True
        return False
    
    def calculate_cycle_day(self, streak: CheckinStreak) -> int:
        """
        计算当前在7天周期中的天数
        
        Args:
            streak: 玩家连续签到数据
            
        Returns:
            周期天数（1-7）
        """
        if streak.cycle_start_date is None:
            return 1
        
        today = date.today()
        days_since_start = (today - streak.cycle_start_date).days
        
        # 7天为一个周期
        return (days_since_start % 7) + 1
    
    def calculate_supplement_cost(self, days_ago: int) -> int:
        """
        计算补签消耗
        
        补签消耗随天数递增：
        - 1天前: 50 钻石
        - 2天前: 100 钻石
        - 3天前: 150 钻石
        
        Args:
            days_ago: 距今天数（1-3）
            
        Returns:
            补签消耗钻石数
        """
        if days_ago < 1 or days_ago > self.MAX_SUPPLEMENT_DAYS:
            return 0
        return self.SUPPLEMENT_BASE_COST * days_ago
    
    def get_supplement_days(self, player_id: str) -> List[date]:
        """
        获取可补签的日期列表
        
        Args:
            player_id: 玩家ID
            
        Returns:
            可补签日期列表
        """
        today = date.today()
        records = self.player_records.get(player_id, [])
        checked_dates = {r.checkin_date for r in records}
        
        supplement_days = []
        for i in range(1, self.MAX_SUPPLEMENT_DAYS + 1):
            check_date = today - timedelta(days=i)
            if check_date not in checked_dates:
                supplement_days.append(check_date)
        
        return supplement_days
    
    def get_daily_rewards(self, cycle_day: int, streak_days: int) -> Tuple[List[CheckinReward], List[CheckinReward]]:
        """
        获取指定天数的签到奖励
        
        Args:
            cycle_day: 周期天数（1-7）
            streak_days: 连续签到天数
            
        Returns:
            (基础奖励列表, 额外奖励列表)
        """
        config = self.daily_rewards.get(cycle_day, self.daily_rewards.get(1))
        if not config:
            return [], []
        
        base_rewards = config.base_rewards.copy()
        bonus_rewards = config.bonus_rewards.copy()
        
        # 连续签到加成
        for streak, bonus_percent in config.streak_bonus.items():
            if streak_days >= int(streak):
                # 应用加成
                for reward in base_rewards:
                    reward.quantity = int(reward.quantity * (1 + bonus_percent / 100))
        
        return base_rewards, bonus_rewards
    
    def get_monthly_rewards(self, monthly_count: int) -> List[CheckinReward]:
        """
        获取月度累计奖励
        
        Args:
            monthly_count: 本月签到次数
            
        Returns:
            月度奖励列表
        """
        config = self.monthly_rewards.get(monthly_count)
        if not config:
            return []
        
        return config.base_rewards.copy()
    
    def checkin(self, player_id: str) -> Tuple[Optional[CheckinRecord], Optional[str]]:
        """
        执行每日签到
        
        Args:
            player_id: 玩家ID
            
        Returns:
            (签到记录, 错误信息) - 成功时错误信息为None
        """
        # 检查今日是否已签到
        if self.has_checked_today(player_id):
            return None, "今日已签到"
        
        today = date.today()
        now = datetime.now()
        
        # 获取或创建连续签到数据
        streak = self.get_or_create_streak(player_id)
        
        # 更新连续签到（需要先处理断签情况）
        if streak.last_checkin_date is not None:
            days_diff = (today - streak.last_checkin_date).days
            if days_diff > 1:
                # 超过1天未签到，重新开始
                streak.current_streak = 0
                streak.cycle_start_date = today
        
        # 更新签到天数
        if streak.cycle_start_date is None:
            streak.cycle_start_date = today
        
        streak.current_streak += 1
        streak.last_checkin_date = today
        streak.total_count += 1
        
        # 更新月签到数
        if streak.last_checkin_date and streak.last_checkin_date.month != today.month:
            streak.monthly_count = 1
        else:
            streak.monthly_count += 1
        
        # 更新最大连续签到
        if streak.current_streak > streak.max_streak:
            streak.max_streak = streak.current_streak
        
        # 计算周期天数
        cycle_day = self.calculate_cycle_day(streak)
        
        # 获取奖励
        base_rewards, bonus_rewards = self.get_daily_rewards(cycle_day, streak.current_streak)
        all_rewards = base_rewards + bonus_rewards
        
        # 检查月度奖励
        monthly_rewards = self.get_monthly_rewards(streak.monthly_count)
        all_rewards.extend(monthly_rewards)
        
        # 创建签到记录
        record = CheckinRecord(
            record_id=f"checkin_{uuid.uuid4().hex[:16]}",
            player_id=player_id,
            checkin_date=today,
            checkin_time=now,
            day_in_cycle=cycle_day,
            streak_days=streak.current_streak,
            rewards=all_rewards,
        )
        
        # 保存记录
        if player_id not in self.player_records:
            self.player_records[player_id] = []
        self.player_records[player_id].append(record)
        
        logger.info(
            f"Player {player_id} checked in: day={cycle_day}, streak={streak.current_streak}, rewards={len(all_rewards)}"
        )
        
        return record, None
    
    def supplement_checkin(
        self,
        player_id: str,
        target_date: date,
        diamond_balance: int,
    ) -> Tuple[Optional[CheckinRecord], int, Optional[str]]:
        """
        执行补签
        
        Args:
            player_id: 玩家ID
            target_date: 补签日期
            diamond_balance: 当前钻石余额
            
        Returns:
            (签到记录, 消耗钻石, 错误信息) - 成功时错误信息为None
        """
        today = date.today()
        
        # 验证补签日期
        days_ago = (today - target_date).days
        if days_ago < 1:
            return None, 0, "无法补签今天或未来的日期"
        if days_ago > self.MAX_SUPPLEMENT_DAYS:
            return None, 0, f"最多只能补签{self.MAX_SUPPLEMENT_DAYS}天内"
        
        # 检查是否已补签或签到过
        records = self.player_records.get(player_id, [])
        for record in records:
            if record.checkin_date == target_date:
                return None, 0, "该日期已签到或补签"
        
        # 计算补签消耗
        cost = self.calculate_supplement_cost(days_ago)
        
        # 检查钻石余额
        if diamond_balance < cost:
            return None, 0, f"钻石不足，需要{cost}钻石"
        
        now = datetime.now()
        
        # 获取连续签到数据
        streak = self.get_or_create_streak(player_id)
        
        # 计算周期天数（补签不影响周期计算）
        cycle_day = ((target_date - (streak.cycle_start_date or target_date)).days % 7) + 1
        
        # 获取奖励（补签只获得基础奖励）
        base_rewards, _ = self.get_daily_rewards(cycle_day, 1)
        
        # 创建签到记录
        record = CheckinRecord(
            record_id=f"supplement_{uuid.uuid4().hex[:16]}",
            player_id=player_id,
            checkin_date=target_date,
            checkin_time=now,
            day_in_cycle=cycle_day,
            streak_days=1,
            rewards=base_rewards,
            is_supplement=True,
            supplement_cost=cost,
        )
        
        # 保存记录
        if player_id not in self.player_records:
            self.player_records[player_id] = []
        self.player_records[player_id].append(record)
        
        # 更新总签到数（补签不计入连续）
        streak.total_count += 1
        
        logger.info(
            f"Player {player_id} supplement checked in: date={target_date}, cost={cost}"
        )
        
        return record, cost, None
    
    def get_checkin_info(self, player_id: str) -> CheckinInfo:
        """
        获取玩家签到信息
        
        Args:
            player_id: 玩家ID
            
        Returns:
            签到信息
        """
        today = date.today()
        streak = self.get_or_create_streak(player_id)
        today_checked = self.has_checked_today(player_id)
        
        # 计算周期天数
        cycle_day = self.calculate_cycle_day(streak)
        
        # 获取今日奖励预览
        base_rewards, bonus_rewards = self.get_daily_rewards(cycle_day, streak.current_streak + 1)
        today_rewards = base_rewards + bonus_rewards
        
        # 计算下次签到时间
        next_checkin_time = None
        if today_checked:
            next_checkin_time = datetime.combine(today + timedelta(days=1), datetime.min.time())
        
        # 计算可补签天数
        supplement_dates = self.get_supplement_days(player_id)
        
        return CheckinInfo(
            can_checkin=not today_checked,
            today_checked=today_checked,
            streak_info=streak,
            today_rewards=today_rewards,
            cycle_day=cycle_day,
            monthly_count=streak.monthly_count,
            supplement_days=len(supplement_dates),
            next_checkin_time=next_checkin_time,
        )
    
    def get_checkin_records(
        self,
        player_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 30,
    ) -> List[CheckinRecord]:
        """
        获取玩家签到记录
        
        Args:
            player_id: 玩家ID
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回数量限制
            
        Returns:
            签到记录列表
        """
        records = self.player_records.get(player_id, [])
        
        # 筛选日期范围
        if start_date:
            records = [r for r in records if r.checkin_date >= start_date]
        if end_date:
            records = [r for r in records if r.checkin_date <= end_date]
        
        # 排序并限制数量
        return sorted(records, key=lambda r: r.checkin_date, reverse=True)[:limit]
    
    def get_reward_config(self) -> Dict[str, Any]:
        """
        获取签到奖励配置
        
        Returns:
            奖励配置字典
        """
        return {
            "daily_rewards": {day: config.to_dict() for day, config in self.daily_rewards.items()},
            "monthly_rewards": {day: config.to_dict() for day, config in self.monthly_rewards.items()},
            "max_supplement_days": self.MAX_SUPPLEMENT_DAYS,
            "supplement_base_cost": self.SUPPLEMENT_BASE_COST,
        }
    
    def reset_monthly_count(self, player_id: str) -> None:
        """
        重置月签到次数（月初调用）
        
        Args:
            player_id: 玩家ID
        """
        streak = self.player_streaks.get(player_id)
        if streak:
            streak.monthly_count = 0
            logger.info(f"Reset monthly checkin count for player {player_id}")
    
    def clear_cache(self, player_id: Optional[str] = None) -> None:
        """
        清除缓存
        
        Args:
            player_id: 玩家ID（None表示清除所有）
        """
        if player_id:
            self.player_streaks.pop(player_id, None)
            self.player_records.pop(player_id, None)
        else:
            self.player_streaks.clear()
            self.player_records.clear()


# 全局单例
_checkin_manager: Optional[CheckinManager] = None


def get_checkin_manager(config_path: Optional[str] = None) -> CheckinManager:
    """
    获取签到管理器单例
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        签到管理器实例
    """
    global _checkin_manager
    if _checkin_manager is None:
        _checkin_manager = CheckinManager(config_path)
    return _checkin_manager
