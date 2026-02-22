"""
王者之奕 - 自定义房间与匹配系统集成测试

测试自定义房间与匹配系统的跨模块交互：
- 房间创建与加入
- 特殊规则应用
- 匹配系统与房间联动
- 游戏开始流程
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch

from src.server.custom_room import (
    CustomRoomManager,
    CustomRoom,
    CustomRoomState,
    RoomPlayer,
    RoomPlayerState,
    RoomSettings,
    SpecialRuleType,
    custom_room_manager,
)


class TestCustomRoomIntegration:
    """自定义房间集成测试"""

    @pytest.fixture
    def room_manager(self):
        """创建房间管理器"""
        return CustomRoomManager()

    @pytest.fixture
    def default_settings(self) -> RoomSettings:
        """创建默认房间设置"""
        return RoomSettings(
            max_players=4,
            password=None,
            special_rules=[],
        )

    @pytest.mark.asyncio
    async def test_create_room(self, room_manager, default_settings):
        """测试创建房间"""
        room = await room_manager.create_room(
            host_id="player_001",
            host_name="玩家1",
            settings=default_settings,
        )
        
        assert room is not None
        assert room.host_id == "player_001"
        assert room.state == CustomRoomState.WAITING
        assert len(room.players) == 1

    @pytest.mark.asyncio
    async def test_join_room(self, room_manager, default_settings):
        """测试加入房间"""
        # 创建房间
        room = await room_manager.create_room(
            host_id="player_001",
            host_name="玩家1",
            settings=default_settings,
        )
        
        # 加入房间
        result = await room_manager.join_room(
            player_id="player_002",
            player_name="玩家2",
            room_id=room.room_id,
        )
        
        assert result is not None
        assert len(result.players) == 2

    @pytest.mark.asyncio
    async def test_room_is_full(self, room_manager):
        """测试房间满员状态"""
        settings = RoomSettings(max_players=2)
        
        # 创建房间
        room = await room_manager.create_room(
            host_id="player_001",
            host_name="玩家1",
            settings=settings,
        )
        
        # 第二个玩家加入
        await room_manager.join_room(
            player_id="player_002",
            player_name="玩家2",
            room_id=room.room_id,
        )
        
        # 验证房间已满
        room = await room_manager.get_room(room.room_id)
        assert room.is_full is True

    @pytest.mark.asyncio
    async def test_room_players_count(self, room_manager, default_settings):
        """测试房间玩家数量"""
        room = await room_manager.create_room(
            host_id="player_001",
            host_name="玩家1",
            settings=default_settings,
        )
        await room_manager.join_room(
            player_id="player_002",
            player_name="玩家2",
            room_id=room.room_id,
        )
        
        room = await room_manager.get_room(room.room_id)
        assert room.player_count == 2


class TestRoomPasswordIntegration:
    """房间密码集成测试"""

    @pytest.fixture
    def room_manager(self):
        """创建房间管理器"""
        return CustomRoomManager()

    @pytest.mark.asyncio
    async def test_password_protected_room(self, room_manager):
        """测试密码保护的房间"""
        settings = RoomSettings(
            password="secret123",
        )
        
        # 创建房间
        room = await room_manager.create_room(
            host_id="player_001",
            host_name="玩家1",
            settings=settings,
        )
        
        assert room.has_password is True

    @pytest.mark.asyncio
    async def test_join_with_wrong_password(self, room_manager):
        """测试使用错误密码加入"""
        settings = RoomSettings(password="correct")
        
        room = await room_manager.create_room(
            host_id="player_001",
            host_name="玩家1",
            settings=settings,
        )
        
        # 错误密码
        result = await room_manager.join_room(
            player_id="player_002",
            player_name="玩家2",
            room_id=room.room_id,
            password="wrong",
        )
        
        assert result is None


class TestSpecialRulesIntegration:
    """特殊规则集成测试"""

    @pytest.fixture
    def room_manager(self):
        """创建房间管理器"""
        return CustomRoomManager()

    @pytest.mark.asyncio
    async def test_fast_mode_rule(self, room_manager):
        """测试快速模式规则"""
        settings = RoomSettings(
            special_rules=[SpecialRuleType.FAST_MODE],
        )
        
        room = await room_manager.create_room(
            host_id="player_001",
            host_name="玩家1",
            settings=settings,
        )
        
        assert SpecialRuleType.FAST_MODE in room.settings.special_rules

    @pytest.mark.asyncio
    async def test_double_economy_rule(self, room_manager):
        """测试双倍经济规则"""
        settings = RoomSettings(
            special_rules=[SpecialRuleType.DOUBLE_ECONOMY],
        )
        
        room = await room_manager.create_room(
            host_id="player_001",
            host_name="玩家1",
            settings=settings,
        )
        
        assert SpecialRuleType.DOUBLE_ECONOMY in room.settings.special_rules

    @pytest.mark.asyncio
    async def test_random_pool_rule(self, room_manager):
        """测试随机英雄池规则"""
        settings = RoomSettings(
            special_rules=[SpecialRuleType.RANDOM_POOL],
        )
        
        room = await room_manager.create_room(
            host_id="player_001",
            host_name="玩家1",
            settings=settings,
        )
        
        assert SpecialRuleType.RANDOM_POOL in room.settings.special_rules

    @pytest.mark.asyncio
    async def test_multiple_rules(self, room_manager):
        """测试多个规则组合"""
        settings = RoomSettings(
            special_rules=[
                SpecialRuleType.FAST_MODE,
                SpecialRuleType.DOUBLE_ECONOMY,
            ],
        )
        
        room = await room_manager.create_room(
            host_id="player_001",
            host_name="玩家1",
            settings=settings,
        )
        
        assert len(room.settings.special_rules) == 2


class TestRoomStateIntegration:
    """房间状态集成测试"""

    @pytest.fixture
    def room_manager(self):
        """创建房间管理器"""
        return CustomRoomManager()

    @pytest.mark.asyncio
    async def test_room_waiting_state(self, room_manager):
        """测试房间等待状态"""
        settings = RoomSettings(max_players=4)
        
        room = await room_manager.create_room(
            host_id="player_001",
            host_name="玩家1",
            settings=settings,
        )
        
        assert room.state == CustomRoomState.WAITING

    @pytest.mark.asyncio
    async def test_can_start_check(self, room_manager):
        """测试是否可以开始游戏检查"""
        settings = RoomSettings(max_players=2)
        
        room = await room_manager.create_room(
            host_id="player_001",
            host_name="玩家1",
            settings=settings,
        )
        
        # 一人无法开始
        assert room.can_start is False
        
        # 加入第二个玩家
        await room_manager.join_room(
            player_id="player_002",
            player_name="玩家2",
            room_id=room.room_id,
        )
        
        room = await room_manager.get_room(room.room_id)
        
        # 设置准备后才能开始
        room.set_player_ready("player_001", True)
        room.set_player_ready("player_002", True)
        
        assert room.can_start is True

    @pytest.mark.asyncio
    async def test_only_host_can_start(self, room_manager):
        """测试只有房主可以开始"""
        settings = RoomSettings(max_players=2)
        
        room = await room_manager.create_room(
            host_id="player_001",
            host_name="玩家1",
            settings=settings,
        )
        
        await room_manager.join_room(
            player_id="player_002",
            player_name="玩家2",
            room_id=room.room_id,
        )
        
        # 非房主尝试开始
        result = await room_manager.start_game(room.room_id, "player_002")
        
        assert result is False


class TestRoomPlayerIntegration:
    """房间玩家集成测试"""

    @pytest.fixture
    def room_manager(self):
        """创建房间管理器"""
        return CustomRoomManager()

    @pytest.mark.asyncio
    async def test_player_state(self, room_manager):
        """测试玩家状态"""
        room = await room_manager.create_room(
            host_id="player_001",
            host_name="玩家1",
            settings=RoomSettings(),
        )
        
        # 检查玩家状态（默认未准备）
        player = room.get_player("player_001")
        assert player is not None
        assert player.state == RoomPlayerState.NOT_READY

    @pytest.mark.asyncio
    async def test_set_player_ready(self, room_manager):
        """测试设置玩家准备"""
        room = await room_manager.create_room(
            host_id="player_001",
            host_name="玩家1",
            settings=RoomSettings(),
        )
        
        # 设置准备
        room.set_player_ready("player_001", True)
        
        player = room.get_player("player_001")
        assert player.is_ready is True


class TestRoomSerialization:
    """房间序列化测试"""

    def test_room_settings_serialization(self):
        """测试房间设置序列化"""
        settings = RoomSettings(
            max_players=4,
            password="secret",
            special_rules=[SpecialRuleType.FAST_MODE],
        )
        
        data = settings.to_dict()
        assert data["max_players"] == 4
        
        loaded = RoomSettings.from_dict(data)
        assert loaded.max_players == 4
        assert SpecialRuleType.FAST_MODE in loaded.special_rules

    def test_room_player_serialization(self):
        """测试房间玩家序列化"""
        player = RoomPlayer(
            player_id="player_001",
            nickname="玩家1",
            is_host=True,
            is_ai=False,
        )
        
        data = player.to_dict()
        assert data["player_id"] == "player_001"
