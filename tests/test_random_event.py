"""
王者之奕 - 随机事件系统测试

测试随机事件管理器的各项功能。
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from src.server.random_event.models import (
    EventEffect,
    EventEffectType,
    EventHistoryEntry,
    EventRarity,
    EventTrigger,
    EventType,
    RandomEvent,
)
from src.server.random_event.manager import (
    ActiveEvent,
    RandomEventManager,
    create_random_event_manager,
    get_random_event_manager,
)


class TestEventModels:
    """测试事件数据模型"""
    
    def test_event_effect_creation(self):
        """测试事件效果创建"""
        effect = EventEffect(
            effect_type=EventEffectType.GIVE_GOLD_ALL,
            value=10,
            duration=0,
        )
        
        assert effect.effect_type == EventEffectType.GIVE_GOLD_ALL
        assert effect.value == 10
        assert effect.duration == 0
    
    def test_event_effect_to_dict(self):
        """测试事件效果序列化"""
        effect = EventEffect(
            effect_type=EventEffectType.DISCOUNT_HERO_COST,
            value=1,
            target="1",
            duration=1,
        )
        
        data = effect.to_dict()
        
        assert data["effect_type"] == "discount_hero_cost"
        assert data["value"] == 1
        assert data["target"] == "1"
        assert data["duration"] == 1
    
    def test_event_effect_from_dict(self):
        """测试事件效果反序列化"""
        data = {
            "effect_type": "give_gold_all",
            "value": 5,
            "target": "",
            "duration": 0,
        }
        
        effect = EventEffect.from_dict(data)
        
        assert effect.effect_type == EventEffectType.GIVE_GOLD_ALL
        assert effect.value == 5
    
    def test_event_trigger_creation(self):
        """测试触发条件创建"""
        trigger = EventTrigger(
            probability=0.05,
            fixed_rounds=[10, 20],
            min_round=1,
            max_round=100,
        )
        
        assert trigger.probability == 0.05
        assert trigger.fixed_rounds == [10, 20]
        assert trigger.min_round == 1
        assert trigger.max_round == 100
    
    def test_random_event_creation(self):
        """测试随机事件创建"""
        event = RandomEvent(
            event_id="test_event",
            name="测试事件",
            description="这是一个测试事件",
            event_type=EventType.GOLD_RAIN,
            rarity=EventRarity.COMMON,
            effects=[
                EventEffect(
                    effect_type=EventEffectType.GIVE_GOLD_ALL,
                    value=5,
                )
            ],
            trigger=EventTrigger(probability=0.05),
        )
        
        assert event.event_id == "test_event"
        assert event.name == "测试事件"
        assert event.event_type == EventType.GOLD_RAIN
        assert event.rarity == EventRarity.COMMON
        assert len(event.effects) == 1
        assert event.enabled is True
    
    def test_random_event_to_dict(self):
        """测试随机事件序列化"""
        event = RandomEvent(
            event_id="gold_rain",
            name="金币雨",
            description="所有玩家获得金币",
            event_type=EventType.GOLD_RAIN,
            rarity=EventRarity.COMMON,
            effects=[EventEffect(effect_type=EventEffectType.GIVE_GOLD_ALL, value=5)],
            trigger=EventTrigger(probability=0.05),
        )
        
        data = event.to_dict()
        
        assert data["event_id"] == "gold_rain"
        assert data["name"] == "金币雨"
        assert data["event_type"] == "gold_rain"
        assert data["rarity"] == "common"
        assert len(data["effects"]) == 1
    
    def test_random_event_from_dict(self):
        """测试随机事件反序列化"""
        data = {
            "event_id": "test_event",
            "name": "测试事件",
            "description": "测试描述",
            "event_type": "gold_rain",
            "rarity": "rare",
            "effects": [
                {
                    "effect_type": "give_gold_all",
                    "value": 10,
                    "target": "",
                    "duration": 0,
                }
            ],
            "trigger": {
                "probability": 0.03,
                "fixed_rounds": [],
                "min_round": 1,
                "max_round": 100,
            },
            "enabled": True,
        }
        
        event = RandomEvent.from_dict(data)
        
        assert event.event_id == "test_event"
        assert event.name == "测试事件"
        assert event.event_type == EventType.GOLD_RAIN
        assert event.rarity == EventRarity.RARE
        assert len(event.effects) == 1
        assert event.trigger.probability == 0.03
    
    def test_event_history_entry(self):
        """测试事件历史记录"""
        event = RandomEvent(
            event_id="test_event",
            name="测试事件",
            description="",
            event_type=EventType.GOLD_RAIN,
            rarity=EventRarity.COMMON,
        )
        
        entry = EventHistoryEntry(
            entry_id="entry_1",
            room_id="room_1",
            event=event,
            round_number=5,
            trigger_time=datetime.now(),
            affected_players=[1, 2, 3],
            effect_results=[{"effect_type": "give_gold_all", "value": 5}],
        )
        
        assert entry.entry_id == "entry_1"
        assert entry.room_id == "room_1"
        assert entry.round_number == 5
        assert len(entry.affected_players) == 3
        
        # 测试序列化
        data = entry.to_dict()
        assert data["entry_id"] == "entry_1"
        assert data["room_id"] == "room_1"


class TestEventManager:
    """测试事件管理器"""
    
    @pytest.fixture
    def manager(self):
        """创建事件管理器实例"""
        # 使用默认配置（不从文件加载）
        manager = RandomEventManager(config_path="/nonexistent/path.json")
        return manager
    
    def test_manager_initialization(self, manager):
        """测试管理器初始化"""
        assert manager is not None
        assert isinstance(manager.events, dict)
        assert len(manager.events) > 0  # 应该有默认事件
    
    def test_get_event(self, manager):
        """测试获取事件"""
        # 获取默认存在的金币雨事件
        event = manager.get_event("gold_rain")
        
        assert event is not None
        assert event.event_id == "gold_rain"
        assert event.name == "金币雨"
    
    def test_get_all_events(self, manager):
        """测试获取所有事件"""
        events = manager.get_all_events()
        
        assert len(events) > 0
        assert all(isinstance(e, RandomEvent) for e in events)
    
    def test_get_enabled_events(self, manager):
        """测试获取启用的事件"""
        # 先禁用一个事件
        manager.set_event_enabled("gold_rain", False)
        
        enabled = manager.get_enabled_events()
        
        assert all(e.enabled for e in enabled)
        assert "gold_rain" not in [e.event_id for e in enabled]
        
        # 恢复
        manager.set_event_enabled("gold_rain", True)
    
    def test_add_event(self, manager):
        """测试添加事件"""
        new_event = RandomEvent(
            event_id="custom_event",
            name="自定义事件",
            description="自定义事件描述",
            event_type=EventType.GOLD_RAIN,
            rarity=EventRarity.COMMON,
            effects=[EventEffect(effect_type=EventEffectType.GIVE_GOLD_ALL, value=20)],
            trigger=EventTrigger(probability=0.1),
        )
        
        manager.add_event(new_event)
        
        assert manager.get_event("custom_event") is not None
        assert manager.get_event("custom_event").name == "自定义事件"
    
    def test_set_event_probability(self, manager):
        """测试设置事件概率"""
        result = manager.set_event_probability("gold_rain", 0.1)
        
        assert result is True
        assert manager.get_event("gold_rain").trigger.probability == 0.1
        
        # 恢复
        manager.set_event_probability("gold_rain", 0.05)
    
    def test_check_events_fixed_round(self, manager):
        """测试固定回合触发"""
        # 创建一个固定在第5回合触发的事件
        event = RandomEvent(
            event_id="fixed_round_event",
            name="固定回合事件",
            description="",
            event_type=EventType.GOLD_RAIN,
            rarity=EventRarity.COMMON,
            effects=[EventEffect(effect_type=EventEffectType.GIVE_GOLD_ALL, value=5)],
            trigger=EventTrigger(probability=0, fixed_rounds=[5]),
        )
        manager.add_event(event)
        
        # 在第5回合应该触发
        triggered = manager.check_events("room_1", 5)
        assert any(e.event_id == "fixed_round_event" for e in triggered)
        
        # 在其他回合不应该触发（概率为0）
        triggered = manager.check_events("room_1", 4)
        assert not any(e.event_id == "fixed_round_event" for e in triggered)
    
    def test_check_events_round_range(self, manager):
        """测试回合范围限制"""
        # 创建一个只在3-10回合触发的事件
        event = RandomEvent(
            event_id="range_event",
            name="范围事件",
            description="",
            event_type=EventType.GOLD_RAIN,
            rarity=EventRarity.COMMON,
            effects=[EventEffect(effect_type=EventEffectType.GIVE_GOLD_ALL, value=5)],
            trigger=EventTrigger(probability=1.0, min_round=3, max_round=10),
        )
        manager.add_event(event)
        
        # 在范围内应该触发
        triggered = manager.check_events("room_1", 5)
        assert any(e.event_id == "range_event" for e in triggered)
        
        # 在范围外不应该触发
        triggered = manager.check_events("room_1", 2)
        assert not any(e.event_id == "range_event" for e in triggered)
        
        triggered = manager.check_events("room_1", 11)
        assert not any(e.event_id == "range_event" for e in triggered)
    
    def test_execute_event(self, manager):
        """测试执行事件"""
        event = manager.get_event("gold_rain")
        players = [
            {"player_id": 1, "gold": 50},
            {"player_id": 2, "gold": 30},
        ]
        
        result = manager.execute_event(
            room_id="room_1",
            event=event,
            round_number=1,
            players=players,
        )
        
        assert result["event_id"] == "gold_rain"
        assert len(result["effects"]) > 0
        assert len(result["affected_players"]) == 2
    
    def test_get_event_history(self, manager):
        """测试获取事件历史"""
        # 先执行一些事件
        event = manager.get_event("gold_rain")
        players = [{"player_id": 1}]
        
        manager.execute_event("room_1", event, 1, players)
        manager.execute_event("room_1", event, 2, players)
        
        history = manager.get_event_history("room_1")
        
        assert len(history) == 2
        assert all(isinstance(e, EventHistoryEntry) for e in history)
    
    def test_get_active_events(self, manager):
        """测试获取活跃事件"""
        # 执行一个持续效果的事件
        event = manager.get_event("free_refresh")
        if event:
            players = [{"player_id": 1}]
            manager.execute_event("room_1", event, 1, players)
            
            active = manager.get_active_events("room_1")
            assert len(active) > 0
    
    def test_get_hero_discount(self, manager):
        """测试获取英雄折扣"""
        # 执行一费英雄折扣事件
        event = manager.get_event("hero_discount_1")
        if event:
            players = [{"player_id": 1}]
            manager.execute_event("room_1", event, 1, players)
            
            discount = manager.get_hero_discount("room_1", 1, 1)
            assert discount == 1
            
            # 二费英雄不应该有折扣
            discount = manager.get_hero_discount("room_1", 1, 2)
            assert discount == 0
    
    def test_is_free_refresh(self, manager):
        """测试免费刷新检查"""
        event = manager.get_event("free_refresh")
        if event:
            players = [{"player_id": 1}]
            manager.execute_event("room_1", event, 1, players)
            
            assert manager.is_free_refresh("room_1", 1) is True
            assert manager.is_free_refresh("room_1", 999) is False
    
    def test_advance_round(self, manager):
        """测试推进回合"""
        # 执行一个持续1回合的事件（duration=1）
        event = manager.get_event("free_refresh")
        if event:
            players = [{"player_id": 1}]
            manager.execute_event("room_1", event, 1, players)
            
            # 初始有活跃事件，remaining_duration=0（duration-1）
            active = manager.get_active_events("room_1")
            assert len(active) > 0
            assert active[0].remaining_duration == 0
            
            # 推进回合后 remaining_duration=-1，过期
            expired = manager.advance_round("room_1")
            assert len(expired) > 0
            assert len(manager.get_active_events("room_1")) == 0
    
    def test_clear_active_events(self, manager):
        """测试清除活跃事件"""
        event = manager.get_event("free_refresh")
        if event:
            players = [{"player_id": 1}]
            manager.execute_event("room_1", event, 1, players)
            
            manager.clear_active_events("room_1")
            
            assert len(manager.get_active_events("room_1")) == 0
    
    def test_clear_event_history(self, manager):
        """测试清除事件历史"""
        event = manager.get_event("gold_rain")
        players = [{"player_id": 1}]
        manager.execute_event("room_1", event, 1, players)
        
        manager.clear_event_history("room_1")
        
        assert len(manager.get_event_history("room_1")) == 0


class TestEventManagerCallbacks:
    """测试事件管理器回调"""
    
    @pytest.fixture
    def manager(self):
        """创建事件管理器实例"""
        return RandomEventManager(config_path="/nonexistent/path.json")
    
    def test_on_event_triggered_callback(self, manager):
        """测试事件触发回调"""
        callback = Mock()
        manager.on_event_triggered(callback)
        
        event = manager.get_event("gold_rain")
        players = [{"player_id": 1}]
        
        manager.execute_event("room_1", event, 1, players)
        
        callback.assert_called_once()
        args = callback.call_args[0]
        assert args[0] == "room_1"
        assert args[1] == event
        assert args[2] == 1
    
    def test_on_effect_applied_callback(self, manager):
        """测试效果应用回调"""
        callback = Mock()
        manager.on_effect_applied(callback)
        
        event = manager.get_event("gold_rain")
        players = [{"player_id": 1}]
        
        manager.execute_event("room_1", event, 1, players)
        
        # 金币雨事件有1个效果
        assert callback.call_count >= 1


class TestEventType:
    """测试事件类型"""
    
    def test_event_type_display_name(self):
        """测试事件类型显示名称"""
        assert EventType.GOLD_RAIN.display_name == "金币雨"
        assert EventType.HERO_DISCOUNT.display_name == "英雄折扣"
        assert EventType.LUCKY_WHEEL.display_name == "幸运轮盘"
    
    def test_event_rarity_display_name(self):
        """测试事件稀有度显示名称"""
        assert EventRarity.COMMON.display_name == "普通"
        assert EventRarity.RARE.display_name == "稀有"
        assert EventRarity.EPIC.display_name == "史诗"
        assert EventRarity.LEGENDARY.display_name == "传说"
    
    def test_event_rarity_probability(self):
        """测试事件稀有度基础概率"""
        assert EventRarity.COMMON.base_probability == 0.05
        assert EventRarity.RARE.base_probability == 0.03
        assert EventRarity.EPIC.base_probability == 0.015
        assert EventRarity.LEGENDARY.base_probability == 0.005


class TestGlobalManager:
    """测试全局管理器"""
    
    def test_create_random_event_manager(self):
        """测试创建全局管理器"""
        manager = create_random_event_manager()
        
        assert manager is not None
        assert isinstance(manager, RandomEventManager)
    
    def test_get_random_event_manager(self):
        """测试获取全局管理器"""
        manager1 = get_random_event_manager()
        manager2 = get_random_event_manager()
        
        assert manager1 is manager2  # 应该是同一个实例


class TestActiveEvent:
    """测试活跃事件"""
    
    def test_active_event_creation(self):
        """测试活跃事件创建"""
        event = RandomEvent(
            event_id="test",
            name="测试",
            description="",
            event_type=EventType.GOLD_RAIN,
            rarity=EventRarity.COMMON,
        )
        
        active = ActiveEvent(
            event=event,
            start_round=1,
            remaining_duration=2,
            affected_players=[1, 2, 3],
        )
        
        assert active.event == event
        assert active.start_round == 1
        assert active.remaining_duration == 2
        assert len(active.affected_players) == 3
    
    def test_active_event_to_dict(self):
        """测试活跃事件序列化"""
        event = RandomEvent(
            event_id="test",
            name="测试",
            description="",
            event_type=EventType.GOLD_RAIN,
            rarity=EventRarity.COMMON,
        )
        
        active = ActiveEvent(
            event=event,
            start_round=1,
            remaining_duration=1,
            affected_players=[1],
        )
        
        data = active.to_dict()
        
        assert data["start_round"] == 1
        assert data["remaining_duration"] == 1
        assert "event" in data
