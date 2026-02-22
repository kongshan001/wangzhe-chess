"""
王者之奕 - 自定义房间系统测试

测试自定义房间系统的核心功能：
- 房间创建
- 玩家加入/离开
- 房主踢人
- AI 填充
- 开始游戏
- 特殊规则

需求 #16: 自定义房间
"""

import asyncio
import pytest
from datetime import datetime

from src.server.custom_room import (
    custom_room_manager,
    CustomRoom,
    CustomRoomState,
    CustomRoomFilter,
    RoomPlayer,
    RoomPlayerState,
    RoomSettings,
    SpecialRuleType,
)
from src.server.custom_room.manager import CustomRoomManager


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def manager():
    """创建隔离的房间管理器实例"""
    # 重置全局实例
    CustomRoomManager.reset()
    return CustomRoomManager.get_instance()


@pytest.fixture
def room_settings():
    """默认房间设置"""
    return RoomSettings(
        max_players=8,
        password=None,
        special_rules=[],
    )


@pytest.fixture
def fast_mode_settings():
    """快速模式设置"""
    return RoomSettings(
        max_players=4,
        special_rules=[SpecialRuleType.FAST_MODE],
    )


@pytest.fixture
def double_economy_settings():
    """双倍经济设置"""
    return RoomSettings(
        max_players=8,
        special_rules=[SpecialRuleType.DOUBLE_ECONOMY],
    )


# ============================================================================
# RoomSettings 测试
# ============================================================================

class TestRoomSettings:
    """房间设置测试"""
    
    def test_default_settings(self):
        """测试默认设置"""
        settings = RoomSettings()
        
        assert settings.max_players == 8
        assert settings.password is None
        assert settings.special_rules == []
        assert settings.round_time == 30
        assert settings.prepare_time == 30
        assert settings.starting_gold == 10
        assert settings.starting_hp == 100
        assert settings.ai_fill is True
    
    def test_max_players_validation(self):
        """测试玩家数量验证"""
        # 有效范围
        settings = RoomSettings(max_players=2)
        assert settings.max_players == 2
        
        settings = RoomSettings(max_players=8)
        assert settings.max_players == 8
        
        # 无效范围
        with pytest.raises(ValueError):
            RoomSettings(max_players=1)
        
        with pytest.raises(ValueError):
            RoomSettings(max_players=9)
    
    def test_fast_mode_adjusts_times(self):
        """测试快速模式自动调整时间"""
        settings = RoomSettings(special_rules=[SpecialRuleType.FAST_MODE])
        
        assert settings.round_time == 15
        assert settings.prepare_time == 15
    
    def test_double_economy_doubles_gold(self):
        """测试双倍经济自动调整金币"""
        settings = RoomSettings(special_rules=[SpecialRuleType.DOUBLE_ECONOMY])
        
        assert settings.starting_gold == 20  # 10 * 2
    
    def test_has_rule(self):
        """测试检查规则是否存在"""
        settings = RoomSettings(
            special_rules=[SpecialRuleType.RANDOM_POOL, SpecialRuleType.FAST_MODE]
        )
        
        assert settings.has_rule(SpecialRuleType.RANDOM_POOL) is True
        assert settings.has_rule(SpecialRuleType.FAST_MODE) is True
        assert settings.has_rule(SpecialRuleType.DOUBLE_ECONOMY) is False
    
    def test_to_dict(self):
        """测试序列化"""
        settings = RoomSettings(
            max_players=4,
            password="secret",
            special_rules=[SpecialRuleType.FAST_MODE],
        )
        
        data = settings.to_dict()
        
        assert data["max_players"] == 4
        assert data["has_password"] is True
        assert data["special_rules"] == ["fast_mode"]
        assert data["round_time"] == 15
    
    def test_from_dict(self):
        """测试反序列化"""
        data = {
            "max_players": 6,
            "password": "test123",
            "special_rules": ["random_pool", "fast_mode"],
            "round_time": 20,
        }
        
        settings = RoomSettings.from_dict(data)
        
        assert settings.max_players == 6
        assert settings.password == "test123"
        assert len(settings.special_rules) == 2
        assert SpecialRuleType.RANDOM_POOL in settings.special_rules
        assert SpecialRuleType.FAST_MODE in settings.special_rules


# ============================================================================
# RoomPlayer 测试
# ============================================================================

class TestRoomPlayer:
    """房间玩家测试"""
    
    def test_create_player(self):
        """测试创建玩家"""
        player = RoomPlayer(
            player_id="player1",
            nickname="玩家1",
            slot=0,
        )
        
        assert player.player_id == "player1"
        assert player.nickname == "玩家1"
        assert player.slot == 0
        assert player.state == RoomPlayerState.NOT_READY
        assert player.is_host is False
        assert player.is_ai is False
        assert player.is_ready is False
        assert player.is_connected is True
    
    def test_set_ready(self):
        """测试设置准备状态"""
        player = RoomPlayer(player_id="p1", nickname="玩家1")
        
        player.set_ready(True)
        assert player.is_ready is True
        assert player.state == RoomPlayerState.READY
        assert player.ready_at is not None
        
        player.set_ready(False)
        assert player.is_ready is False
        assert player.state == RoomPlayerState.NOT_READY
        assert player.ready_at is None
    
    def test_set_playing(self):
        """测试设置游戏中状态"""
        player = RoomPlayer(player_id="p1", nickname="玩家1")
        player.set_playing()
        
        assert player.state == RoomPlayerState.PLAYING
    
    def test_set_disconnected(self):
        """测试断开连接"""
        player = RoomPlayer(player_id="p1", nickname="玩家1")
        player.set_disconnected()
        
        assert player.state == RoomPlayerState.DISCONNECTED
        assert player.is_connected is False
    
    def test_to_dict(self):
        """测试序列化"""
        player = RoomPlayer(
            player_id="p1",
            nickname="玩家1",
            slot=2,
            is_host=True,
        )
        player.set_ready(True)
        
        data = player.to_dict()
        
        assert data["player_id"] == "p1"
        assert data["nickname"] == "玩家1"
        assert data["slot"] == 2
        assert data["is_host"] is True
        assert data["state"] == "ready"


# ============================================================================
# CustomRoom 测试
# ============================================================================

class TestCustomRoom:
    """自定义房间测试"""
    
    def test_create_room(self):
        """测试创建房间"""
        room = CustomRoom(
            name="测试房间",
            host_id="host1",
        )
        
        assert room.room_id is not None
        assert room.name == "测试房间"
        assert room.host_id == "host1"
        assert room.state == CustomRoomState.WAITING
        assert room.player_count == 0
        assert room.is_empty is True
        assert room.is_full is False
    
    def test_room_auto_name(self):
        """测试自动生成房间名"""
        room = CustomRoom()
        
        assert room.name.startswith("房间-")
    
    def test_add_player(self):
        """测试添加玩家"""
        room = CustomRoom(host_id="host1")
        
        player = room.add_player(
            player_id="host1",
            nickname="房主",
            slot=0,
        )
        
        assert player is not None
        assert player.player_id == "host1"
        assert player.is_host is True
        assert room.player_count == 1
    
    def test_add_player_auto_slot(self):
        """测试自动分配位置"""
        room = CustomRoom()
        
        p1 = room.add_player(player_id="p1", nickname="玩家1")
        p2 = room.add_player(player_id="p2", nickname="玩家2")
        p3 = room.add_player(player_id="p3", nickname="玩家3")
        
        assert p1.slot == 0
        assert p2.slot == 1
        assert p3.slot == 2
    
    def test_add_player_already_in_room(self):
        """测试重复添加玩家"""
        room = CustomRoom()
        room.add_player(player_id="p1", nickname="玩家1")
        
        player = room.add_player(player_id="p1", nickname="玩家1")
        
        assert player is None
        assert room.player_count == 1
    
    def test_remove_player(self):
        """测试移除玩家"""
        room = CustomRoom(host_id="host1")
        room.add_player(player_id="host1", nickname="房主", slot=0)
        room.add_player(player_id="p2", nickname="玩家2", slot=1)
        
        removed = room.remove_player("p2")
        
        assert removed is not None
        assert removed.player_id == "p2"
        assert room.player_count == 1
    
    def test_remove_host_transfers_ownership(self):
        """测试房主离开后转让房主"""
        room = CustomRoom(host_id="host1")
        room.add_player(player_id="host1", nickname="房主", slot=0)
        room.add_player(player_id="p2", nickname="玩家2", slot=1)
        
        room.remove_player("host1")
        
        assert room.host_id == "p2"
        assert room.players["p2"].is_host is True
    
    def test_set_player_ready(self):
        """测试设置玩家准备状态"""
        room = CustomRoom()
        room.add_player(player_id="p1", nickname="玩家1")
        
        success = room.set_player_ready("p1", True)
        
        assert success is True
        assert room.players["p1"].is_ready is True
    
    def test_ai_player_auto_ready(self):
        """测试 AI 玩家自动准备"""
        room = CustomRoom()
        
        player = room.add_player(
            player_id="ai_1",
            nickname="AI-1",
            is_ai=True,
        )
        player.set_ready(True)
        
        assert player.is_ai is True
        assert player.is_ready is True
    
    def test_fill_with_ai(self):
        """测试 AI 填充"""
        room = CustomRoom(settings=RoomSettings(max_players=4))
        room.add_player(player_id="p1", nickname="玩家1")
        
        ai_players = room.fill_with_ai()
        
        assert len(ai_players) == 3  # 填满到4人
        assert room.player_count == 4
        assert room.ai_count == 3
        assert all(p.is_ai for p in ai_players)
        assert all(p.is_ready for p in ai_players)  # AI 自动准备
    
    def test_can_start(self):
        """测试是否可以开始游戏"""
        room = CustomRoom(settings=RoomSettings(max_players=4))
        
        # 没有玩家
        assert room.can_start is False
        
        # 只有一个玩家
        room.add_player(player_id="p1", nickname="玩家1")
        assert room.can_start is False
        
        # 两个玩家但未准备
        room.add_player(player_id="p2", nickname="玩家2")
        assert room.can_start is False
        
        # 一个准备
        room.set_player_ready("p1", True)
        assert room.can_start is False
        
        # 都准备了
        room.set_player_ready("p2", True)
        assert room.can_start is True
    
    def test_start_game(self):
        """测试开始游戏"""
        room = CustomRoom(settings=RoomSettings(max_players=4))
        room.add_player(player_id="p1", nickname="玩家1")
        room.add_player(player_id="p2", nickname="玩家2")
        room.set_player_ready("p1", True)
        room.set_player_ready("p2", True)
        
        success = room.start_game()
        
        assert success is True
        assert room.state == CustomRoomState.PLAYING
        assert room.game_started_at is not None
        assert all(p.state == RoomPlayerState.PLAYING for p in room.players.values())
    
    def test_start_game_not_ready(self):
        """测试未准备时开始游戏"""
        room = CustomRoom()
        room.add_player(player_id="p1", nickname="玩家1")
        room.add_player(player_id="p2", nickname="玩家2")
        # 未准备
        
        success = room.start_game()
        
        assert success is False
        assert room.state == CustomRoomState.WAITING
    
    def test_special_rules_random_pool(self):
        """测试随机英雄池规则"""
        room = CustomRoom(
            settings=RoomSettings(special_rules=[SpecialRuleType.RANDOM_POOL])
        )
        
        room.set_random_hero_pool(["hero1", "hero2", "hero3"])
        
        assert room.is_hero_available("hero1") is True
        assert room.is_hero_available("hero4") is False
    
    def test_to_dict(self):
        """测试房间序列化"""
        room = CustomRoom(name="测试房间", host_id="host1")
        room.add_player(player_id="host1", nickname="房主", slot=0)
        
        data = room.to_dict()
        
        assert data["name"] == "测试房间"
        assert data["host_id"] == "host1"
        assert data["player_count"] == 1
        assert len(data["players"]) == 1
    
    def test_to_summary(self):
        """测试房间简要信息"""
        room = CustomRoom(name="测试房间", host_id="host1")
        room.add_player(player_id="host1", nickname="房主", slot=0)
        
        summary = room.to_summary()
        
        assert summary["name"] == "测试房间"
        assert summary["host_name"] == "房主"
        assert summary["player_count"] == 1


# ============================================================================
# CustomRoomManager 测试
# ============================================================================

class TestCustomRoomManager:
    """自定义房间管理器测试"""
    
    @pytest.mark.asyncio
    async def test_create_room(self, manager):
        """测试创建房间"""
        room = await manager.create_room(
            host_id="host1",
            host_name="房主",
            name="测试房间",
        )
        
        assert room is not None
        assert room.host_id == "host1"
        assert room.name == "测试房间"
        assert room.player_count == 1  # 房主自动加入
        assert manager.is_player_in_room("host1")
    
    @pytest.mark.asyncio
    async def test_join_room(self, manager):
        """测试加入房间"""
        room = await manager.create_room(
            host_id="host1",
            host_name="房主",
        )
        
        joined_room = await manager.join_room(
            player_id="p2",
            player_name="玩家2",
            room_id=room.room_id,
        )
        
        assert joined_room is not None
        assert joined_room.room_id == room.room_id
        assert joined_room.player_count == 2
        assert manager.is_player_in_room("p2")
    
    @pytest.mark.asyncio
    async def test_join_room_with_password(self, manager):
        """测试密码房间"""
        settings = RoomSettings(password="secret123")
        room = await manager.create_room(
            host_id="host1",
            host_name="房主",
            settings=settings,
        )
        
        # 错误密码
        joined = await manager.join_room(
            player_id="p2",
            player_name="玩家2",
            room_id=room.room_id,
            password="wrong",
        )
        assert joined is None
        
        # 正确密码
        joined = await manager.join_room(
            player_id="p2",
            player_name="玩家2",
            room_id=room.room_id,
            password="secret123",
        )
        assert joined is not None
    
    @pytest.mark.asyncio
    async def test_join_full_room(self, manager):
        """测试加入已满房间"""
        settings = RoomSettings(max_players=2)
        room = await manager.create_room(
            host_id="host1",
            host_name="房主",
            settings=settings,
        )
        await manager.join_room(
            player_id="p2",
            player_name="玩家2",
            room_id=room.room_id,
        )
        
        # 房间已满
        joined = await manager.join_room(
            player_id="p3",
            player_name="玩家3",
            room_id=room.room_id,
        )
        assert joined is None
    
    @pytest.mark.asyncio
    async def test_leave_room(self, manager):
        """测试离开房间"""
        room = await manager.create_room(
            host_id="host1",
            host_name="房主",
        )
        await manager.join_room(
            player_id="p2",
            player_name="玩家2",
            room_id=room.room_id,
        )
        
        success = await manager.leave_room("p2")
        
        assert success is True
        assert not manager.is_player_in_room("p2")
        
        room = await manager.get_room(room.room_id)
        assert room.player_count == 1
    
    @pytest.mark.asyncio
    async def test_kick_player(self, manager):
        """测试踢出玩家"""
        room = await manager.create_room(
            host_id="host1",
            host_name="房主",
        )
        await manager.join_room(
            player_id="p2",
            player_name="玩家2",
            room_id=room.room_id,
        )
        
        # 非房主无法踢人
        success = await manager.kick_player(
            room_id=room.room_id,
            host_id="p2",
            target_id="host1",
        )
        assert success is False
        
        # 房主踢人
        success = await manager.kick_player(
            room_id=room.room_id,
            host_id="host1",
            target_id="p2",
        )
        assert success is True
        
        room = await manager.get_room(room.room_id)
        assert room.player_count == 1
    
    @pytest.mark.asyncio
    async def test_set_player_ready(self, manager):
        """测试设置准备状态"""
        room = await manager.create_room(
            host_id="host1",
            host_name="房主",
        )
        
        success = await manager.set_player_ready("host1", True)
        
        assert success is True
        
        room = await manager.get_room(room.room_id)
        assert room.players["host1"].is_ready is True
    
    @pytest.mark.asyncio
    async def test_fill_room_with_ai(self, manager):
        """测试 AI 填充房间"""
        settings = RoomSettings(max_players=4)
        room = await manager.create_room(
            host_id="host1",
            host_name="房主",
            settings=settings,
        )
        
        ai_players = await manager.fill_room_with_ai(room.room_id)
        
        assert len(ai_players) == 3
        
        room = await manager.get_room(room.room_id)
        assert room.player_count == 4
        assert room.ai_count == 3
    
    @pytest.mark.asyncio
    async def test_start_game(self, manager):
        """测试开始游戏"""
        room = await manager.create_room(
            host_id="host1",
            host_name="房主",
        )
        await manager.join_room(
            player_id="p2",
            player_name="玩家2",
            room_id=room.room_id,
        )
        await manager.set_player_ready("host1", True)
        await manager.set_player_ready("p2", True)
        
        success = await manager.start_game(
            room_id=room.room_id,
            host_id="host1",
        )
        
        assert success is True
        
        room = await manager.get_room(room.room_id)
        assert room.state == CustomRoomState.PLAYING
    
    @pytest.mark.asyncio
    async def test_start_game_not_all_ready(self, manager):
        """测试未全部准备时开始游戏"""
        room = await manager.create_room(
            host_id="host1",
            host_name="房主",
        )
        await manager.join_room(
            player_id="p2",
            player_name="玩家2",
            room_id=room.room_id,
        )
        await manager.set_player_ready("host1", True)
        # p2 未准备
        
        success = await manager.start_game(
            room_id=room.room_id,
            host_id="host1",
        )
        
        assert success is False
    
    @pytest.mark.asyncio
    async def test_destroy_room(self, manager):
        """测试销毁房间"""
        room = await manager.create_room(
            host_id="host1",
            host_name="房主",
        )
        
        success = await manager.destroy_room(room.room_id)
        
        assert success is True
        
        room = await manager.get_room(room.room_id)
        assert room is None
    
    @pytest.mark.asyncio
    async def test_find_rooms(self, manager):
        """测试查找房间"""
        # 创建多个房间
        await manager.create_room(host_id="h1", host_name="房主1")
        
        settings = RoomSettings(special_rules=[SpecialRuleType.FAST_MODE])
        await manager.create_room(
            host_id="h2",
            host_name="房主2",
            settings=settings,
        )
        
        # 查找所有等待中的房间
        filter_ = CustomRoomFilter(state=CustomRoomState.WAITING)
        rooms = await manager.find_rooms(filter_)
        
        assert len(rooms) == 2
    
    @pytest.mark.asyncio
    async def test_get_player_room(self, manager):
        """测试获取玩家所在房间"""
        room = await manager.create_room(
            host_id="host1",
            host_name="房主",
        )
        
        player_room = await manager.get_player_room("host1")
        
        assert player_room is not None
        assert player_room.room_id == room.room_id
    
    @pytest.mark.asyncio
    async def test_get_stats(self, manager):
        """测试获取统计信息"""
        await manager.create_room(host_id="h1", host_name="房主1")
        await manager.create_room(host_id="h2", host_name="房主2")
        
        stats = manager.get_stats()
        
        assert stats["total_rooms"] == 2
        assert stats["total_created"] == 2
        assert stats["state_distribution"]["waiting"] == 2


# ============================================================================
# 集成测试
# ============================================================================

class TestCustomRoomIntegration:
    """自定义房间集成测试"""
    
    @pytest.mark.asyncio
    async def test_full_game_flow(self, manager):
        """测试完整游戏流程"""
        # 1. 房主创建房间
        room = await manager.create_room(
            host_id="host1",
            host_name="房主",
            name="快乐游戏",
            settings=RoomSettings(
                max_players=4,
                special_rules=[SpecialRuleType.FAST_MODE],
            ),
        )
        assert room is not None
        
        # 2. 其他玩家加入
        await manager.join_room(
            player_id="p2",
            player_name="玩家2",
            room_id=room.room_id,
        )
        
        # 3. AI 填充
        ai_players = await manager.fill_room_with_ai(room.room_id)
        assert len(ai_players) == 2
        
        # 4. 房主准备
        await manager.set_player_ready("host1", True)
        
        # 5. 玩家2准备
        await manager.set_player_ready("p2", True)
        
        # 6. 开始游戏
        success = await manager.start_game(
            room_id=room.room_id,
            host_id="host1",
        )
        assert success is True
        
        # 7. 验证游戏状态
        room = await manager.get_room(room.room_id)
        assert room.state == CustomRoomState.PLAYING
        assert room.player_count == 4
        assert room.ai_count == 2
    
    @pytest.mark.asyncio
    async def test_special_rules_effect(self, manager):
        """测试特殊规则效果"""
        # 快速模式
        fast_settings = RoomSettings(special_rules=[SpecialRuleType.FAST_MODE])
        room = await manager.create_room(
            host_id="h1",
            host_name="房主",
            settings=fast_settings,
        )
        
        assert room.settings.round_time == 15
        assert room.settings.prepare_time == 15
        
        # 双倍经济
        double_settings = RoomSettings(special_rules=[SpecialRuleType.DOUBLE_ECONOMY])
        room2 = await manager.create_room(
            host_id="h2",
            host_name="房主2",
            settings=double_settings,
        )
        
        assert room2.settings.starting_gold == 20


# ============================================================================
# 运行测试
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
