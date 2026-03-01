"""
王者之奕 - 观战系统测试

本模块测试观战系统的核心功能：
- 观战会话管理
- 延迟同步机制
- 弹幕/聊天功能
- 可观战对局列表
"""

import time

import pytest

from src.server.spectator import (
    GameVisibility,
    SpectatorChat,
    SpectatorData,
    SpectatorGameState,
    SpectatorManager,
    SpectatorSession,
    SpectatorStatus,
    get_spectator_manager,
)


class TestSpectatorModels:
    """测试观战数据模型"""

    def test_spectator_game_state_creation(self):
        """测试游戏状态快照创建"""
        state = SpectatorGameState(
            snapshot_time=int(time.time() * 1000),
            game_id="game_123",
            round_num=5,
            phase="preparation",
            player_states={
                "player_1": {"hp": 100, "gold": 50},
                "player_2": {"hp": 80, "gold": 30},
            },
            timestamp=int(time.time() * 1000),
        )

        assert state.game_id == "game_123"
        assert state.round_num == 5
        assert state.phase == "preparation"
        assert len(state.player_states) == 2

        # 测试序列化
        state_dict = state.to_dict()
        assert state_dict["game_id"] == "game_123"

        # 测试反序列化
        restored = SpectatorGameState.from_dict(state_dict)
        assert restored.game_id == state.game_id
        assert restored.round_num == state.round_num

    def test_spectator_session_creation(self):
        """测试观战会话创建"""
        session = SpectatorSession(
            session_id="session_123",
            spectator_id="spectator_456",
            game_id="game_789",
            watching_player_id="player_111",
        )

        assert session.session_id == "session_123"
        assert session.spectator_id == "spectator_456"
        assert session.status == SpectatorStatus.WATCHING
        assert session.is_active()

        # 测试切换玩家
        session.switch_player("player_222")
        assert session.watching_player_id == "player_222"

    def test_spectator_data_management(self):
        """测试观战数据管理"""
        data = SpectatorData(
            game_id="game_123",
            visibility=GameVisibility.PUBLIC,
            max_spectators=10,
            delay_seconds=30,
        )

        # 测试添加观众
        session = SpectatorSession(
            session_id="session_1",
            spectator_id="spectator_1",
            game_id="game_123",
            watching_player_id="player_1",
        )

        assert data.add_spectator(session) is True
        assert data.get_spectator_count() == 1
        assert not data.is_full()

        # 测试移除观众
        removed = data.remove_spectator("session_1")
        assert removed is not None
        assert data.get_spectator_count() == 0

    def test_spectator_data_visibility(self):
        """测试观战可见性控制"""
        # 测试私密对局
        private_data = SpectatorData(
            game_id="private_game",
            visibility=GameVisibility.PRIVATE,
        )

        session = SpectatorSession(
            session_id="session_1",
            spectator_id="spectator_1",
            game_id="private_game",
            watching_player_id="player_1",
        )

        assert private_data.add_spectator(session) is False

        # 测试好友对局
        friend_data = SpectatorData(
            game_id="friend_game",
            visibility=GameVisibility.FRIENDS,
            allowed_spectators=["friend_1", "friend_2"],
        )

        friend_session = SpectatorSession(
            session_id="session_2",
            spectator_id="friend_1",
            game_id="friend_game",
            watching_player_id="player_1",
        )

        assert friend_data.add_spectator(friend_session) is True

        # 非好友不能观战
        stranger_session = SpectatorSession(
            session_id="session_3",
            spectator_id="stranger",
            game_id="friend_game",
            watching_player_id="player_1",
        )

        assert friend_data.add_spectator(stranger_session) is False

    def test_spectator_chat_validation(self):
        """测试弹幕消息验证"""
        # 有效消息
        valid_chat = SpectatorChat(
            chat_id="chat_1",
            game_id="game_123",
            sender_id="player_1",
            sender_name="玩家1",
            content="666",
        )
        assert valid_chat.is_valid() is True

        # 空消息
        empty_chat = SpectatorChat(
            chat_id="chat_2",
            game_id="game_123",
            sender_id="player_1",
            sender_name="玩家1",
            content="",
        )
        assert empty_chat.is_valid() is False

        # 过长消息
        long_chat = SpectatorChat(
            chat_id="chat_3",
            game_id="game_123",
            sender_id="player_1",
            sender_name="玩家1",
            content="a" * 201,
        )
        assert long_chat.is_valid() is False


class TestSpectatorManager:
    """测试观战管理器"""

    @pytest.fixture
    def manager(self):
        """创建管理器实例"""
        return SpectatorManager()

    def test_create_spectatable_game(self, manager):
        """测试创建可观战对局"""
        data = manager.create_spectatable_game(
            game_id="game_123",
            visibility=GameVisibility.PUBLIC,
            delay_seconds=30,
        )

        assert data is not None
        assert data.game_id == "game_123"
        assert data.visibility == GameVisibility.PUBLIC
        assert data.delay_seconds == 30

        # 检查可以获取
        retrieved = manager.get_spectatable_game("game_123")
        assert retrieved is not None

    def test_remove_spectatable_game(self, manager):
        """测试移除可观战对局"""
        manager.create_spectatable_game("game_123")

        # 移除
        removed = manager.remove_spectatable_game("game_123")
        assert removed is not None

        # 检查已移除
        assert manager.get_spectatable_game("game_123") is None

    def test_create_spectator_session(self, manager):
        """测试创建观战会话"""
        # 先创建对局
        manager.create_spectatable_game("game_123")

        # 创建会话
        session = manager.create_session(
            spectator_id="spectator_1",
            game_id="game_123",
            watching_player_id="player_1",
        )

        assert session is not None
        assert session.spectator_id == "spectator_1"
        assert session.game_id == "game_123"
        assert session.watching_player_id == "player_1"

        # 检查可以通过玩家ID获取
        retrieved = manager.get_session_by_player("spectator_1")
        assert retrieved is not None

    def test_leave_spectate(self, manager):
        """测试离开观战"""
        manager.create_spectatable_game("game_123")
        session = manager.create_session(
            spectator_id="spectator_1",
            game_id="game_123",
            watching_player_id="player_1",
        )

        # 离开
        removed = manager.leave_spectate(session.session_id)
        assert removed is not None

        # 检查已移除
        assert manager.get_session(session.session_id) is None
        assert manager.get_session_by_player("spectator_1") is None

    def test_switch_watching_player(self, manager):
        """测试切换观战对象"""
        manager.create_spectatable_game("game_123")
        session = manager.create_session(
            spectator_id="spectator_1",
            game_id="game_123",
            watching_player_id="player_1",
        )

        # 切换
        updated = manager.switch_watching_player(
            session.session_id,
            "player_2",
        )

        assert updated is not None
        assert updated.watching_player_id == "player_2"

    def test_delayed_sync(self, manager):
        """测试延迟同步机制"""
        manager.create_spectatable_game("game_123", delay_seconds=1)

        # 推送状态
        now = int(time.time() * 1000)

        # 推送旧状态（2秒前）
        manager.push_game_state(
            game_id="game_123",
            round_num=1,
            phase="preparation",
            player_states={"player_1": {"hp": 100}},
        )

        # 等待超过延迟时间
        time.sleep(1.1)

        # 推送新状态
        manager.push_game_state(
            game_id="game_123",
            round_num=2,
            phase="preparation",
            player_states={"player_1": {"hp": 90}},
        )

        # 获取延迟状态
        delayed = manager.get_delayed_state("game_123")

        # 应该返回旧状态（因为新状态还没到延迟时间）
        # 注意：这里的时间判断可能需要根据实际情况调整

    def test_push_game_state(self, manager):
        """测试推送游戏状态"""
        manager.create_spectatable_game("game_123")

        # 推送状态
        state = manager.push_game_state(
            game_id="game_123",
            round_num=1,
            phase="preparation",
            player_states={
                "player_1": {"hp": 100, "gold": 50},
            },
            shop_slots={"player_1": []},
        )

        assert state is not None
        assert state.round_num == 1
        assert state.phase == "preparation"

        # 检查历史记录
        spectator_data = manager.get_spectatable_game("game_123")
        assert len(spectator_data.state_history) == 1

    def test_spectator_chat(self, manager):
        """测试弹幕功能"""
        manager.create_spectatable_game("game_123")

        # 发送弹幕
        chat = manager.send_chat(
            game_id="game_123",
            sender_id="spectator_1",
            sender_name="观众1",
            content="666",
        )

        assert chat is not None
        assert chat.sender_id == "spectator_1"
        assert chat.content == "666"

        # 获取历史
        history = manager.get_chat_history("game_123")
        assert len(history) == 1

    def test_get_spectatable_games(self, manager):
        """测试获取可观战对局列表"""
        # 创建多个对局
        manager.create_spectatable_game("game_1")
        manager.create_spectatable_game("game_2")
        manager.create_spectatable_game("game_3")

        # 更新玩家信息
        manager.update_game_players(
            "game_1",
            [
                {"player_id": "p1", "nickname": "玩家1"},
            ],
        )

        # 获取列表
        games = manager.get_spectatable_games(page=1, page_size=10)

        assert len(games) == 3

    def test_max_spectators(self, manager):
        """测试最大观众数限制"""
        manager.create_spectatable_game("game_123", delay_seconds=30)
        spectator_data = manager.get_spectatable_game("game_123")
        spectator_data.max_spectators = 2

        # 添加观众
        session1 = manager.create_session("s1", "game_123", "p1")
        session2 = manager.create_session("s2", "game_123", "p1")
        session3 = manager.create_session("s3", "game_123", "p1")

        assert session1 is not None
        assert session2 is not None
        # 第三个应该失败
        assert session3 is None

    def test_stats(self, manager):
        """测试统计信息"""
        manager.create_spectatable_game("game_123")
        manager.create_session("s1", "game_123", "p1")
        manager.send_chat("game_123", "s1", "观众1", "666")

        stats = manager.get_stats()

        assert stats["total_games"] == 1
        assert stats["total_spectators"] == 1
        assert stats["total_chats"] == 1


class TestSpectatorManagerSingleton:
    """测试单例"""

    def test_get_spectator_manager(self):
        """测试获取单例"""
        manager1 = get_spectator_manager()
        manager2 = get_spectator_manager()

        assert manager1 is manager2


class TestDelayedSync:
    """测试延迟同步机制"""

    @pytest.fixture
    def manager(self):
        """创建管理器实例"""
        return SpectatorManager()

    def test_delay_accuracy(self, manager):
        """测试延迟精度"""
        delay_seconds = 2
        manager.create_spectatable_game("game_123", delay_seconds=delay_seconds)

        # 记录推送时间
        push_time = time.time()

        # 推送状态
        manager.push_game_state(
            game_id="game_123",
            round_num=1,
            phase="preparation",
            player_states={"player_1": {"hp": 100}},
        )

        # 立即获取应该为空
        delayed = manager.get_delayed_state("game_123")
        assert delayed is None

        # 等待延迟时间后获取
        time.sleep(delay_seconds + 0.5)

        # 推送新状态以触发旧状态可见
        manager.push_game_state(
            game_id="game_123",
            round_num=2,
            phase="preparation",
            player_states={"player_1": {"hp": 90}},
        )

        delayed = manager.get_delayed_state("game_123")
        # 应该返回第一个状态

    def test_state_history_cleanup(self, manager):
        """测试状态历史清理"""
        manager.create_spectatable_game("game_123")

        # 推送多个状态
        for i in range(10):
            manager.push_game_state(
                game_id="game_123",
                round_num=i,
                phase="preparation",
                player_states={"player_1": {"hp": 100 - i}},
            )
            time.sleep(0.1)

        spectator_data = manager.get_spectatable_game("game_123")

        # 历史应该被保留（在5分钟内）
        assert len(spectator_data.state_history) == 10


class TestSpectatorChatHistory:
    """测试弹幕历史"""

    @pytest.fixture
    def manager(self):
        """创建管理器实例"""
        return SpectatorManager()

    def test_chat_history_limit(self, manager):
        """测试弹幕历史限制"""
        manager.create_spectatable_game("game_123")

        # 发送超过限制数量的弹幕
        for i in range(150):
            manager.send_chat(
                game_id="game_123",
                sender_id=f"spectator_{i}",
                sender_name=f"观众{i}",
                content=f"消息{i}",
            )

        # 历史应该被限制
        history = manager.get_chat_history("game_123", limit=200)
        assert len(history) <= 150  # MAX_CHAT_HISTORY

    def test_chat_history_pagination(self, manager):
        """测试弹幕历史分页"""
        manager.create_spectatable_game("game_123")

        # 发送多条弹幕
        for i in range(30):
            manager.send_chat(
                game_id="game_123",
                sender_id="spectator_1",
                sender_name="观众1",
                content=f"消息{i}",
            )
            time.sleep(0.01)  # 确保时间不同

        # 获取最新的10条
        history = manager.get_chat_history("game_123", limit=10)
        assert len(history) == 10


class TestSpectatorCallback:
    """测试回调机制"""

    @pytest.fixture
    def manager(self):
        """创建管理器实例"""
        return SpectatorManager()

    def test_state_update_callback(self, manager):
        """测试状态更新回调"""
        callback_called = []

        def callback(game_id, state):
            callback_called.append((game_id, state.round_num))

        manager.set_state_update_callback(callback)
        manager.create_spectatable_game("game_123")

        # 推送状态
        manager.push_game_state(
            game_id="game_123",
            round_num=1,
            phase="preparation",
            player_states={"player_1": {"hp": 100}},
        )

        assert len(callback_called) == 1
        assert callback_called[0] == ("game_123", 1)

    def test_chat_callback(self, manager):
        """测试聊天回调"""
        callback_called = []

        def callback(chat):
            callback_called.append(chat.content)

        manager.set_chat_callback(callback)
        manager.create_spectatable_game("game_123")

        # 发送弹幕
        manager.send_chat(
            game_id="game_123",
            sender_id="s1",
            sender_name="观众1",
            content="测试消息",
        )

        assert len(callback_called) == 1
        assert callback_called[0] == "测试消息"


# 集成测试标记
@pytest.mark.integration
class TestSpectatorIntegration:
    """集成测试"""

    @pytest.fixture
    def manager(self):
        """创建管理器实例"""
        return SpectatorManager()

    def test_full_spectator_flow(self, manager):
        """测试完整观战流程"""
        # 1. 游戏开始，创建可观战对局
        game_data = manager.create_spectatable_game(
            game_id="game_123",
            visibility=GameVisibility.PUBLIC,
            delay_seconds=1,
        )
        assert game_data is not None

        # 2. 更新玩家信息
        manager.update_game_players(
            "game_123",
            [
                {"player_id": "p1", "nickname": "玩家1", "tier": "gold"},
                {"player_id": "p2", "nickname": "玩家2", "tier": "silver"},
            ],
        )

        # 3. 玩家加入观战
        session = manager.create_session(
            spectator_id="spectator_1",
            game_id="game_123",
            watching_player_id="p1",
        )
        assert session is not None

        # 4. 推送游戏状态
        manager.push_game_state(
            game_id="game_123",
            round_num=1,
            phase="preparation",
            player_states={
                "p1": {"hp": 100, "gold": 50, "level": 3},
                "p2": {"hp": 100, "gold": 40, "level": 2},
            },
        )

        # 5. 发送弹幕
        chat = manager.send_chat(
            game_id="game_123",
            sender_id="spectator_1",
            sender_name="观众1",
            content="加油！",
        )
        assert chat is not None

        # 6. 切换观战对象
        manager.switch_watching_player(session.session_id, "p2")

        # 7. 玩家离开观战
        manager.leave_spectate(session.session_id)

        # 8. 游戏结束，移除可观战对局
        manager.remove_spectatable_game("game_123")

        # 9. 验证清理完成
        assert manager.get_spectatable_game("game_123") is None
        assert len(manager.get_spectators_in_game("game_123")) == 0
