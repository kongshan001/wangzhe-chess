"""
王者之奕 - 随机事件管理器

本模块实现随机事件的核心管理逻辑：
- 检查事件触发
- 执行事件效果
- 管理事件配置
- 记录事件历史
"""

from __future__ import annotations

import json
import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

import structlog

from .models import (
    EventEffect,
    EventEffectType,
    EventHistoryEntry,
    EventRarity,
    EventTrigger,
    EventType,
    RandomEvent,
)


logger = structlog.get_logger()


@dataclass
class ActiveEvent:
    """
    活跃事件
    
    跟踪当前激活的事件及其状态。
    
    Attributes:
        event: 事件对象
        start_round: 开始回合
        remaining_duration: 剩余持续回合
        affected_players: 受影响玩家
    """
    
    event: RandomEvent
    start_round: int
    remaining_duration: int
    affected_players: List[int] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "event": self.event.to_dict(),
            "start_round": self.start_round,
            "remaining_duration": self.remaining_duration,
            "affected_players": self.affected_players,
        }


class RandomEventManager:
    """
    随机事件管理器
    
    管理游戏中的随机事件系统。
    
    主要功能：
    1. 加载和管理事件配置
    2. 检查事件触发条件
    3. 执行事件效果
    4. 记录事件历史
    5. 管理活跃事件
    
    Attributes:
        events: 所有可能的事件
        event_history: 事件历史记录
        active_events: 当前活跃的事件
        config_path: 配置文件路径
    """
    
    def __init__(self, config_path: Optional[str] = None) -> None:
        """
        初始化事件管理器
        
        Args:
            config_path: 事件配置文件路径
        """
        self.events: Dict[str, RandomEvent] = {}
        self.event_history: Dict[str, List[EventHistoryEntry]] = {}  # room_id -> entries
        self.active_events: Dict[str, List[ActiveEvent]] = {}  # room_id -> active events
        self.config_path = config_path or "config/random-events.json"
        
        # 事件回调
        self._on_event_triggered: Optional[Callable[[str, RandomEvent, int, Dict], None]] = None
        self._on_effect_applied: Optional[Callable[[str, EventEffect, Dict], None]] = None
        
        # 加载配置
        self._load_config()
        
        logger.info(
            "随机事件管理器已初始化",
            events_count=len(self.events),
            config_path=self.config_path,
        )
    
    def _load_config(self) -> None:
        """加载事件配置文件"""
        config_file = Path(self.config_path)
        
        if not config_file.exists():
            logger.warning(
                "事件配置文件不存在，使用默认配置",
                path=self.config_path,
            )
            self._create_default_config()
            return
        
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            events_data = config.get("events", [])
            for event_data in events_data:
                event = RandomEvent.from_dict(event_data)
                self.events[event.event_id] = event
            
            logger.info(
                "事件配置加载成功",
                events_count=len(self.events),
            )
            
        except Exception as e:
            logger.error(
                "加载事件配置失败",
                error=str(e),
                path=self.config_path,
            )
            self._create_default_config()
    
    def _create_default_config(self) -> None:
        """创建默认事件配置"""
        default_events = self._get_default_events()
        for event in default_events:
            self.events[event.event_id] = event
        
        # 尝试保存默认配置
        try:
            self._save_config()
            logger.info("默认事件配置已创建")
        except Exception as e:
            logger.warning("无法保存默认配置", error=str(e))
    
    def _get_default_events(self) -> List[RandomEvent]:
        """获取默认事件列表"""
        return [
            # 金币雨 - 普通事件
            RandomEvent(
                event_id="gold_rain",
                name="金币雨",
                description="天降金币！所有玩家获得额外金币。",
                event_type=EventType.GOLD_RAIN,
                rarity=EventRarity.COMMON,
                effects=[
                    EventEffect(
                        effect_type=EventEffectType.GIVE_GOLD_ALL,
                        value=5,
                        duration=0,
                    )
                ],
                trigger=EventTrigger(
                    probability=0.05,
                    fixed_rounds=[],
                    min_round=1,
                    max_round=100,
                ),
                icon="gold_rain",
                animation="gold_rain",
                announcement="💰 金币雨来了！所有玩家获得 {value} 金币！",
            ),
            
            # 大金币雨 - 稀有事件
            RandomEvent(
                event_id="big_gold_rain",
                name="大金币雨",
                description="金币如雨般落下！所有玩家获得大量金币。",
                event_type=EventType.GOLD_RAIN,
                rarity=EventRarity.RARE,
                effects=[
                    EventEffect(
                        effect_type=EventEffectType.GIVE_GOLD_ALL,
                        value=10,
                        duration=0,
                    )
                ],
                trigger=EventTrigger(
                    probability=0.03,
                    fixed_rounds=[],
                    min_round=3,
                    max_round=100,
                ),
                icon="big_gold_rain",
                animation="big_gold_rain",
                announcement="💰💰 大金币雨！所有玩家获得 {value} 金币！",
            ),
            
            # 英雄折扣 - 普通事件
            RandomEvent(
                event_id="hero_discount_1",
                name="一费英雄折扣",
                description="商店的一费英雄正在打折！",
                event_type=EventType.HERO_DISCOUNT,
                rarity=EventRarity.COMMON,
                effects=[
                    EventEffect(
                        effect_type=EventEffectType.DISCOUNT_HERO_COST,
                        value=1,  # 折扣1金币
                        target="1",  # 一费英雄
                        duration=1,  # 持续1回合
                    )
                ],
                trigger=EventTrigger(
                    probability=0.05,
                    fixed_rounds=[],
                    min_round=1,
                    max_round=50,
                ),
                icon="discount",
                animation="discount",
                announcement="🏷️ 一费英雄大减价！本回合购买立减1金币！",
            ),
            
            # 二费英雄折扣 - 稀有事件
            RandomEvent(
                event_id="hero_discount_2",
                name="二费英雄折扣",
                description="商店的二费英雄正在打折！",
                event_type=EventType.HERO_DISCOUNT,
                rarity=EventRarity.RARE,
                effects=[
                    EventEffect(
                        effect_type=EventEffectType.DISCOUNT_HERO_COST,
                        value=1,
                        target="2",
                        duration=1,
                    )
                ],
                trigger=EventTrigger(
                    probability=0.03,
                    fixed_rounds=[],
                    min_round=3,
                    max_round=50,
                ),
                icon="discount",
                animation="discount",
                announcement="🏷️ 二费英雄大减价！本回合购买立减1金币！",
            ),
            
            # 三费英雄折扣 - 史诗事件
            RandomEvent(
                event_id="hero_discount_3",
                name="三费英雄折扣",
                description="商店的三费英雄正在打折！",
                event_type=EventType.HERO_DISCOUNT,
                rarity=EventRarity.EPIC,
                effects=[
                    EventEffect(
                        effect_type=EventEffectType.DISCOUNT_HERO_COST,
                        value=2,
                        target="3",
                        duration=1,
                    )
                ],
                trigger=EventTrigger(
                    probability=0.015,
                    fixed_rounds=[],
                    min_round=5,
                    max_round=50,
                ),
                icon="discount",
                animation="discount",
                announcement="🏷️ 三费英雄大减价！本回合购买立减2金币！",
            ),
            
            # 免费刷新 - 普通事件
            RandomEvent(
                event_id="free_refresh",
                name="免费刷新",
                description="本回合商店刷新免费！",
                event_type=EventType.SHOP_REFRESH_FREE,
                rarity=EventRarity.COMMON,
                effects=[
                    EventEffect(
                        effect_type=EventEffectType.FREE_REFRESH,
                        value=1,
                        duration=1,
                    )
                ],
                trigger=EventTrigger(
                    probability=0.05,
                    fixed_rounds=[],
                    min_round=1,
                    max_round=50,
                ),
                icon="free_refresh",
                animation="free_refresh",
                announcement="🔄 免费刷新！本回合商店刷新不消耗金币！",
            ),
            
            # 装备掉落 - 稀有事件
            RandomEvent(
                event_id="equipment_drop",
                name="装备掉落",
                description="野怪掉落额外装备！",
                event_type=EventType.EQUIPMENT_DROP,
                rarity=EventRarity.RARE,
                effects=[
                    EventEffect(
                        effect_type=EventEffectType.DROP_RATE_BOOST,
                        value=50,  # 掉落率提升50%
                        duration=1,
                    )
                ],
                trigger=EventTrigger(
                    probability=0.03,
                    fixed_rounds=[],
                    min_round=3,
                    max_round=100,
                ),
                icon="equipment",
                animation="equipment_drop",
                announcement="⚔️ 装备掉落率提升！本回合野怪掉落额外装备！",
            ),
            
            # 装备奖励 - 稀有事件
            RandomEvent(
                event_id="equipment_bonus",
                name="装备奖励",
                description="所有玩家获得一件随机装备！",
                event_type=EventType.EQUIPMENT_BONUS,
                rarity=EventRarity.RARE,
                effects=[
                    EventEffect(
                        effect_type=EventEffectType.GIVE_EQUIPMENT_ALL,
                        value=1,
                        duration=0,
                    )
                ],
                trigger=EventTrigger(
                    probability=0.025,
                    fixed_rounds=[],
                    min_round=5,
                    max_round=100,
                ),
                icon="equipment",
                animation="equipment_bonus",
                announcement="🎁 装备奖励！所有玩家获得一件随机装备！",
            ),
            
            # 羁绊祝福 - 史诗事件
            RandomEvent(
                event_id="synergy_blessing_warrior",
                name="战士祝福",
                description="本回合战士羁绊效果翻倍！",
                event_type=EventType.SYNERGY_BLESSING,
                rarity=EventRarity.EPIC,
                effects=[
                    EventEffect(
                        effect_type=EventEffectType.SYNERGY_BOOST,
                        value=100,  # 效果翻倍
                        target="warrior",
                        duration=1,
                    )
                ],
                trigger=EventTrigger(
                    probability=0.015,
                    fixed_rounds=[],
                    min_round=5,
                    max_round=100,
                ),
                icon="synergy_blessing",
                animation="synergy_blessing",
                announcement="⚔️ 战士祝福！本回合战士羁绊效果翻倍！",
            ),
            
            # 法师祝福
            RandomEvent(
                event_id="synergy_blessing_mage",
                name="法师祝福",
                description="本回合法师羁绊效果翻倍！",
                event_type=EventType.SYNERGY_BLESSING,
                rarity=EventRarity.EPIC,
                effects=[
                    EventEffect(
                        effect_type=EventEffectType.SYNERGY_BOOST,
                        value=100,
                        target="mage",
                        duration=1,
                    )
                ],
                trigger=EventTrigger(
                    probability=0.015,
                    fixed_rounds=[],
                    min_round=5,
                    max_round=100,
                ),
                icon="synergy_blessing",
                animation="synergy_blessing",
                announcement="✨ 法师祝福！本回合法师羁绊效果翻倍！",
            ),
            
            # 幸运轮盘 - 传说事件
            RandomEvent(
                event_id="lucky_wheel",
                name="幸运轮盘",
                description="所有玩家转动幸运轮盘，获得随机奖励！",
                event_type=EventType.LUCKY_WHEEL,
                rarity=EventRarity.LEGENDARY,
                effects=[
                    EventEffect(
                        effect_type=EventEffectType.RANDOM_REWARD,
                        value=1,
                        duration=0,
                        conditions={
                            "rewards": [
                                {"type": "gold", "min": 3, "max": 15},
                                {"type": "exp", "min": 2, "max": 8},
                                {"type": "equipment", "chance": 0.3},
                            ]
                        }
                    )
                ],
                trigger=EventTrigger(
                    probability=0.005,
                    fixed_rounds=[10, 20, 30],
                    min_round=5,
                    max_round=100,
                ),
                icon="lucky_wheel",
                animation="lucky_wheel",
                announcement="🎡 幸运轮盘！所有玩家获得随机奖励！",
            ),
            
            # 双倍经验 - 稀有事件
            RandomEvent(
                event_id="double_exp",
                name="双倍经验",
                description="本回合所有玩家获得的经验翻倍！",
                event_type=EventType.DOUBLE_EXP,
                rarity=EventRarity.RARE,
                effects=[
                    EventEffect(
                        effect_type=EventEffectType.GIVE_EXP_ALL,
                        value=4,  # 额外4点经验
                        duration=0,
                    )
                ],
                trigger=EventTrigger(
                    probability=0.03,
                    fixed_rounds=[],
                    min_round=3,
                    max_round=50,
                ),
                icon="double_exp",
                animation="double_exp",
                announcement="⬆️ 双倍经验！所有玩家获得额外4点经验！",
            ),
            
            # 免费升级 - 传说事件
            RandomEvent(
                event_id="free_level_up",
                name="免费升级",
                description="所有玩家立即升级！",
                event_type=EventType.LEVEL_UP_BONUS,
                rarity=EventRarity.LEGENDARY,
                effects=[
                    EventEffect(
                        effect_type=EventEffectType.FREE_LEVEL_UP,
                        value=1,
                        duration=0,
                    )
                ],
                trigger=EventTrigger(
                    probability=0.005,
                    fixed_rounds=[15, 25],
                    min_round=10,
                    max_round=50,
                ),
                icon="level_up",
                animation="level_up",
                announcement="🌟 免费升级！所有玩家立即提升一级！",
            ),
        ]
    
    def _save_config(self) -> None:
        """保存事件配置到文件"""
        config = {
            "version": "1.0",
            "events": [event.to_dict() for event in self.events.values()],
        }
        
        config_file = Path(self.config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    # ========================================================================
    # 事件配置管理
    # ========================================================================
    
    def get_event(self, event_id: str) -> Optional[RandomEvent]:
        """
        获取指定事件
        
        Args:
            event_id: 事件ID
            
        Returns:
            事件对象，不存在则返回None
        """
        return self.events.get(event_id)
    
    def get_all_events(self) -> List[RandomEvent]:
        """获取所有事件列表"""
        return list(self.events.values())
    
    def get_enabled_events(self) -> List[RandomEvent]:
        """获取所有启用的事件"""
        return [e for e in self.events.values() if e.enabled]
    
    def add_event(self, event: RandomEvent) -> None:
        """
        添加新事件
        
        Args:
            event: 事件对象
        """
        self.events[event.event_id] = event
        logger.info("添加新事件", event_id=event.event_id, name=event.name)
    
    def update_event(self, event_id: str, **kwargs) -> bool:
        """
        更新事件配置
        
        Args:
            event_id: 事件ID
            **kwargs: 要更新的属性
            
        Returns:
            是否成功更新
        """
        event = self.events.get(event_id)
        if not event:
            return False
        
        for key, value in kwargs.items():
            if hasattr(event, key):
                setattr(event, key, value)
        
        logger.info("更新事件配置", event_id=event_id, updates=kwargs)
        return True
    
    def set_event_enabled(self, event_id: str, enabled: bool) -> bool:
        """
        启用/禁用事件
        
        Args:
            event_id: 事件ID
            enabled: 是否启用
            
        Returns:
            是否成功
        """
        return self.update_event(event_id, enabled=enabled)
    
    def set_event_probability(self, event_id: str, probability: float) -> bool:
        """
        设置事件触发概率
        
        Args:
            event_id: 事件ID
            probability: 新的触发概率（0-1）
            
        Returns:
            是否成功
        """
        event = self.events.get(event_id)
        if not event:
            return False
        
        event.trigger.probability = max(0, min(1, probability))
        logger.info(
            "更新事件概率",
            event_id=event_id,
            probability=probability,
        )
        return True
    
    # ========================================================================
    # 事件触发检查
    # ========================================================================
    
    def check_events(
        self,
        room_id: str,
        round_number: int,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[RandomEvent]:
        """
        检查是否触发事件
        
        Args:
            room_id: 房间ID
            round_number: 当前回合
            context: 上下文信息（用于条件检查）
            
        Returns:
            触发的事件列表
        """
        triggered_events = []
        context = context or {}
        
        for event in self.get_enabled_events():
            if self._should_trigger(event, round_number, context):
                triggered_events.append(event)
                logger.info(
                    "事件触发",
                    room_id=room_id,
                    event_id=event.event_id,
                    event_name=event.name,
                    round=round_number,
                )
        
        return triggered_events
    
    def _should_trigger(
        self,
        event: RandomEvent,
        round_number: int,
        context: Dict[str, Any],
    ) -> bool:
        """
        判断事件是否应该触发
        
        Args:
            event: 事件对象
            round_number: 当前回合
            context: 上下文信息
            
        Returns:
            是否触发
        """
        trigger = event.trigger
        
        # 检查回合范围
        if round_number < trigger.min_round or round_number > trigger.max_round:
            return False
        
        # 检查固定触发回合
        if round_number in trigger.fixed_rounds:
            return True
        
        # 检查概率触发
        if random.random() < trigger.probability:
            return True
        
        return False
    
    # ========================================================================
    # 事件效果执行
    # ========================================================================
    
    def execute_event(
        self,
        room_id: str,
        event: RandomEvent,
        round_number: int,
        players: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        执行事件效果
        
        Args:
            room_id: 房间ID
            event: 事件对象
            round_number: 当前回合
            players: 玩家列表
            context: 上下文信息
            
        Returns:
            执行结果
        """
        context = context or {}
        results = {
            "event_id": event.event_id,
            "event_name": event.name,
            "round": round_number,
            "effects": [],
            "affected_players": [],
        }
        
        # 初始化房间活跃事件列表
        if room_id not in self.active_events:
            self.active_events[room_id] = []
        
        # 处理每个效果
        for effect in event.effects:
            effect_result = self._execute_effect(
                room_id, effect, players, round_number, context
            )
            results["effects"].append(effect_result)
            
            # 记录受影响玩家
            if effect_result.get("affected_players"):
                results["affected_players"].extend(effect_result["affected_players"])
        
        # 去重
        results["affected_players"] = list(set(results["affected_players"]))
        
        # 记录历史
        history_entry = EventHistoryEntry(
            entry_id=str(uuid.uuid4()),
            room_id=room_id,
            event=event,
            round_number=round_number,
            trigger_time=datetime.now(),
            affected_players=results["affected_players"],
            effect_results=results["effects"],
        )
        
        if room_id not in self.event_history:
            self.event_history[room_id] = []
        self.event_history[room_id].append(history_entry)
        
        # 触发回调
        if self._on_event_triggered:
            try:
                self._on_event_triggered(room_id, event, round_number, results)
            except Exception as e:
                logger.error("事件触发回调失败", error=str(e))
        
        logger.info(
            "事件执行完成",
            room_id=room_id,
            event_id=event.event_id,
            effects_count=len(results["effects"]),
            players_affected=len(results["affected_players"]),
        )
        
        return results
    
    def _execute_effect(
        self,
        room_id: str,
        effect: EventEffect,
        players: List[Dict[str, Any]],
        round_number: int,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        执行单个效果
        
        Args:
            room_id: 房间ID
            effect: 效果对象
            players: 玩家列表
            round_number: 当前回合
            context: 上下文信息
            
        Returns:
            效果执行结果
        """
        result = {
            "effect_type": effect.effect_type.value,
            "value": effect.value,
            "target": effect.target,
            "affected_players": [],
            "details": {},
        }
        
        player_ids = [p.get("player_id") for p in players if p.get("player_id")]
        
        if effect.effect_type == EventEffectType.GIVE_GOLD_ALL:
            # 所有人获得金币
            result["affected_players"] = player_ids
            result["details"]["gold_given"] = effect.value
            
        elif effect.effect_type == EventEffectType.GIVE_GOLD:
            # 特定玩家获得金币
            result["affected_players"] = player_ids
            result["details"]["gold_given"] = effect.value
            
        elif effect.effect_type == EventEffectType.DISCOUNT_HERO_COST:
            # 英雄折扣
            result["affected_players"] = player_ids
            result["details"]["cost_target"] = effect.target
            result["details"]["discount_amount"] = effect.value
            
            # 添加到活跃事件（duration=1表示当前回合有效，所以remaining_duration=duration-1）
            active_event = ActiveEvent(
                event=RandomEvent(
                    event_id=f"discount_{effect.target}",
                    name=f"{effect.target}费折扣",
                    description="",
                    event_type=EventType.HERO_DISCOUNT,
                    rarity=EventRarity.COMMON,
                    effects=[effect],
                ),
                start_round=round_number,
                remaining_duration=max(0, effect.duration - 1),
                affected_players=player_ids,
            )
            self.active_events[room_id].append(active_event)
            
        elif effect.effect_type == EventEffectType.FREE_REFRESH:
            # 免费刷新
            result["affected_players"] = player_ids
            result["details"]["free_refresh_count"] = effect.value
            
            active_event = ActiveEvent(
                event=RandomEvent(
                    event_id="free_refresh_active",
                    name="免费刷新",
                    description="",
                    event_type=EventType.SHOP_REFRESH_FREE,
                    rarity=EventRarity.COMMON,
                    effects=[effect],
                ),
                start_round=round_number,
                remaining_duration=max(0, effect.duration - 1),
                affected_players=player_ids,
            )
            self.active_events[room_id].append(active_event)
            
        elif effect.effect_type == EventEffectType.GIVE_EQUIPMENT_ALL:
            # 所有人获得装备
            result["affected_players"] = player_ids
            result["details"]["equipment_count"] = effect.value
            
        elif effect.effect_type == EventEffectType.DROP_RATE_BOOST:
            # 掉落率提升
            result["affected_players"] = player_ids
            result["details"]["drop_rate_boost"] = effect.value
            
            active_event = ActiveEvent(
                event=RandomEvent(
                    event_id="drop_rate_boost",
                    name="掉落率提升",
                    description="",
                    event_type=EventType.EQUIPMENT_DROP,
                    rarity=EventRarity.RARE,
                    effects=[effect],
                ),
                start_round=round_number,
                remaining_duration=max(0, effect.duration - 1),
                affected_players=player_ids,
            )
            self.active_events[room_id].append(active_event)
            
        elif effect.effect_type == EventEffectType.SYNERGY_BOOST:
            # 羁绊加成
            result["affected_players"] = player_ids
            result["details"]["synergy_target"] = effect.target
            result["details"]["boost_percent"] = effect.value
            
            active_event = ActiveEvent(
                event=RandomEvent(
                    event_id=f"synergy_boost_{effect.target}",
                    name=f"{effect.target}羁绊加成",
                    description="",
                    event_type=EventType.SYNERGY_BLESSING,
                    rarity=EventRarity.EPIC,
                    effects=[effect],
                ),
                start_round=round_number,
                remaining_duration=max(0, effect.duration - 1),
                affected_players=player_ids,
            )
            self.active_events[room_id].append(active_event)
            
        elif effect.effect_type == EventEffectType.GIVE_EXP_ALL:
            # 所有人获得经验
            result["affected_players"] = player_ids
            result["details"]["exp_given"] = effect.value
            
        elif effect.effect_type == EventEffectType.FREE_LEVEL_UP:
            # 免费升级
            result["affected_players"] = player_ids
            result["details"]["level_up_count"] = effect.value
            
        elif effect.effect_type == EventEffectType.RANDOM_REWARD:
            # 随机奖励
            result["affected_players"] = player_ids
            rewards_config = effect.conditions.get("rewards", [])
            rewards_given = []
            
            for player_id in player_ids:
                player_reward = self._generate_random_reward(rewards_config)
                rewards_given.append({
                    "player_id": player_id,
                    "reward": player_reward,
                })
            
            result["details"]["rewards"] = rewards_given
        
        # 触发效果回调
        if self._on_effect_applied:
            try:
                self._on_effect_applied(room_id, effect, result)
            except Exception as e:
                logger.error("效果应用回调失败", error=str(e))
        
        return result
    
    def _generate_random_reward(
        self,
        rewards_config: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        生成随机奖励
        
        Args:
            rewards_config: 奖励配置列表
            
        Returns:
            生成的奖励
        """
        # 计算总权重
        total_weight = 0
        weights = []
        
        for config in rewards_config:
            weight = 1
            if config.get("type") == "equipment":
                weight = config.get("chance", 0.3) * 10
            total_weight += weight
            weights.append(weight)
        
        # 随机选择奖励类型
        roll = random.random() * total_weight
        cumulative = 0
        
        for i, config in enumerate(rewards_config):
            cumulative += weights[i]
            if roll <= cumulative:
                reward_type = config.get("type", "gold")
                
                if reward_type == "gold":
                    return {
                        "type": "gold",
                        "amount": random.randint(
                            config.get("min", 3),
                            config.get("max", 15)
                        ),
                    }
                elif reward_type == "exp":
                    return {
                        "type": "exp",
                        "amount": random.randint(
                            config.get("min", 2),
                            config.get("max", 8)
                        ),
                    }
                elif reward_type == "equipment":
                    return {
                        "type": "equipment",
                        "equipment_id": random.choice([
                            "sword", "armor", "boots", "ring", "amulet"
                        ]),
                    }
        
        # 默认返回金币
        return {"type": "gold", "amount": 5}
    
    # ========================================================================
    # 活跃事件管理
    # ========================================================================
    
    def get_active_events(self, room_id: str) -> List[ActiveEvent]:
        """
        获取房间的活跃事件
        
        Args:
            room_id: 房间ID
            
        Returns:
            活跃事件列表
        """
        return self.active_events.get(room_id, [])
    
    def get_hero_discount(
        self,
        room_id: str,
        player_id: int,
        hero_cost: int,
    ) -> int:
        """
        获取英雄折扣金额
        
        Args:
            room_id: 房间ID
            player_id: 玩家ID
            hero_cost: 英雄费用
            
        Returns:
            折扣金额
        """
        total_discount = 0
        
        for active in self.active_events.get(room_id, []):
            for effect in active.event.effects:
                if effect.effect_type == EventEffectType.DISCOUNT_HERO_COST:
                    # 检查目标费用
                    if effect.target == str(hero_cost) or effect.target == "":
                        # 检查玩家是否受影响
                        if player_id in active.affected_players:
                            total_discount += effect.value
        
        return total_discount
    
    def is_free_refresh(
        self,
        room_id: str,
        player_id: int,
    ) -> bool:
        """
        检查是否有免费刷新
        
        Args:
            room_id: 房间ID
            player_id: 玩家ID
            
        Returns:
            是否免费
        """
        for active in self.active_events.get(room_id, []):
            for effect in active.event.effects:
                if effect.effect_type == EventEffectType.FREE_REFRESH:
                    if player_id in active.affected_players:
                        return True
        return False
    
    def get_synergy_boost(
        self,
        room_id: str,
        player_id: int,
        synergy_name: str,
    ) -> int:
        """
        获取羁绊加成百分比
        
        Args:
            room_id: 房间ID
            player_id: 玩家ID
            synergy_name: 羁绊名称
            
        Returns:
            加成百分比
        """
        total_boost = 0
        
        for active in self.active_events.get(room_id, []):
            for effect in active.event.effects:
                if effect.effect_type == EventEffectType.SYNERGY_BOOST:
                    if effect.target == synergy_name:
                        if player_id in active.affected_players:
                            total_boost += effect.value
        
        return total_boost
    
    def get_drop_rate_boost(
        self,
        room_id: str,
        player_id: int,
    ) -> int:
        """
        获取掉落率加成
        
        Args:
            room_id: 房间ID
            player_id: 玩家ID
            
        Returns:
            掉落率加成百分比
        """
        total_boost = 0
        
        for active in self.active_events.get(room_id, []):
            for effect in active.event.effects:
                if effect.effect_type == EventEffectType.DROP_RATE_BOOST:
                    if player_id in active.affected_players:
                        total_boost += effect.value
        
        return total_boost
    
    def advance_round(self, room_id: str) -> List[ActiveEvent]:
        """
        推进回合，更新活跃事件
        
        Args:
            room_id: 房间ID
            
        Returns:
            过期的事件列表
        """
        if room_id not in self.active_events:
            return []
        
        expired = []
        remaining = []
        
        for active in self.active_events[room_id]:
            active.remaining_duration -= 1
            if active.remaining_duration < 0:
                expired.append(active)
            else:
                remaining.append(active)
        
        self.active_events[room_id] = remaining
        
        if expired:
            logger.info(
                "活跃事件过期",
                room_id=room_id,
                expired_count=len(expired),
            )
        
        return expired
    
    def clear_active_events(self, room_id: str) -> None:
        """
        清除房间的所有活跃事件
        
        Args:
            room_id: 房间ID
        """
        self.active_events.pop(room_id, None)
    
    # ========================================================================
    # 事件历史
    # ========================================================================
    
    def get_event_history(
        self,
        room_id: str,
        limit: int = 50,
    ) -> List[EventHistoryEntry]:
        """
        获取事件历史记录
        
        Args:
            room_id: 房间ID
            limit: 最大返回数量
            
        Returns:
            历史记录列表
        """
        history = self.event_history.get(room_id, [])
        return history[-limit:] if limit else history
    
    def get_player_event_history(
        self,
        player_id: int,
        room_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[EventHistoryEntry]:
        """
        获取玩家相关的事件历史
        
        Args:
            player_id: 玩家ID
            room_id: 房间ID（可选）
            limit: 最大返回数量
            
        Returns:
            历史记录列表
        """
        results = []
        
        rooms = [room_id] if room_id else list(self.event_history.keys())
        
        for rid in rooms:
            for entry in self.event_history.get(rid, []):
                if player_id in entry.affected_players:
                    results.append(entry)
        
        return results[-limit:] if limit else results
    
    def clear_event_history(self, room_id: str) -> None:
        """
        清除房间的事件历史
        
        Args:
            room_id: 房间ID
        """
        self.event_history.pop(room_id, None)
    
    # ========================================================================
    # 回调设置
    # ========================================================================
    
    def on_event_triggered(
        self,
        callback: Callable[[str, RandomEvent, int, Dict], None],
    ) -> None:
        """
        设置事件触发回调
        
        Args:
            callback: 回调函数 (room_id, event, round_number, results)
        """
        self._on_event_triggered = callback
    
    def on_effect_applied(
        self,
        callback: Callable[[str, EventEffect, Dict], None],
    ) -> None:
        """
        设置效果应用回调
        
        Args:
            callback: 回调函数 (room_id, effect, result)
        """
        self._on_effect_applied = callback


# ============================================================================
# 全局实例管理
# ============================================================================

_random_event_manager: Optional[RandomEventManager] = None


def create_random_event_manager(
    config_path: Optional[str] = None,
) -> RandomEventManager:
    """
    创建随机事件管理器实例
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        管理器实例
    """
    global _random_event_manager
    _random_event_manager = RandomEventManager(config_path)
    return _random_event_manager


def get_random_event_manager() -> RandomEventManager:
    """
    获取全局随机事件管理器实例
    
    Returns:
        管理器实例
    """
    global _random_event_manager
    if _random_event_manager is None:
        _random_event_manager = RandomEventManager()
    return _random_event_manager
